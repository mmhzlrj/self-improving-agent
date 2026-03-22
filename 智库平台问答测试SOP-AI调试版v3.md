# 智库平台问答测试 SOP（AI调试版 v3）

基于：人工测试 + 豆包AI建议 + 智谱AI建议（部分）

---

## 一、核心问题

**如何验证获取到的是新问题的回答而不是历史内容？**

---

## 二、AI建议汇总

### 方案1：检查页面元素变化
- 新回复会有新的消息容器
- 检查是否有新生成的元素

### 方案2：记录发送前后的内容差异
- 发送问题前保存内容
- 发送后对比新增内容

### 方案3：检查"思考中"状态消失
- 等待"思考中"/"处理中"消失
- 然后检查内容变化

### 方案4：时间戳验证
- 记录发送问题的时间
- 检查内容中是否有比这个时间更晚的内容

---

## 三、改进后的代码

### 核心改进：随机字符串验证

**智谱AI建议**：在问题中加入随机字符串，检查回答中是否包含

```python
import time
import random
from datetime import datetime
from playwright.sync_api import sync_playwright

# 生成随机验证字符串
VERIFY_CODE = f"X{random.randint(10000,99999)}"
QUESTION = f"请用一句话解释什么是人工智能？回复末尾请加上验证码 {VERIFY_CODE}"


class PlatformTask:
    def __init__(self, name, page):
        self.name = name
        self.page = page
        self.status = "pending"
        self.reply_text = ""
        self.send_time = datetime.now()  # 记录发送时间
        self.content_before = ""  # 发送前的内容
        self.start_time = datetime.now()
        self.last_ask_time = None


def create_hook(page, content_before, verify_code):
    """检测回复是否完成，检查是否包含验证代码"""
    
    def hook(page):
        # 方法1：检测复制按钮
        try:
            for loc in [page.get_by_text("复制"), page.get_by_text("Copy")]:
                if loc.count() > 0 and loc.first.is_visible(timeout=2000):
                    content_after = page.evaluate("() => document.body.innerText")
                    # 检查是否包含验证码
                    if verify_code in content_after:
                        return True, content_after[:2000]
        except:
            pass
        
        # 方法2：检查验证码
        content_after = page.evaluate("() => document.body.innerText")
        if verify_code in content_after:
            return True, content_after[:2000]
        
        return False, ""
    
    return hook


def send_question(page, platform_name, question):
    """发送问题，返回发送前的内容"""
    print(f"[{platform_name}] 发送问题...")
    
    # 保存发送前的内容
    content_before = page.evaluate("() => document.body.innerText")
    
    try:
        if platform_name == "豆包":
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(0.5)
            try:
                new_btn = page.get_by_text("新对话").or_(page.get_by_text("+"))
                if new_btn.count() > 0:
                    new_btn.first.click()
                    time.sleep(1)
            except:
                pass
        
        if platform_name == "千问":
            page.click("body")
            time.sleep(0.5)
        
        if platform_name == "Kimi":
            page.goto("https://www.kimi.com/?chat_enter_method=new_chat")
            time.sleep(3)
        
        # 发送问题
        try:
            page.wait_for_selector("textarea", timeout=5000)
        except:
            page.get_by_role("textbox").first.click()
            time.sleep(0.5)
        
        page.click("textarea")
        time.sleep(0.3)
        page.keyboard.type(question, delay=50)
        time.sleep(0.3)
        page.keyboard.press("Enter")
        
        print(f"[{platform_name}] ✅ 问题已发送")
        return content_before
    except Exception as e:
        print(f"[{platform_name}] ❌ 发送失败: {str(e)[:80]}")
        return content_before


def yield_manager(tasks, global_timeout=120, check_interval=5):
    """主循环"""
    print("\n=== 启动 yield_manager ===")
    
    while True:
        all_completed = True
        now = datetime.now()
        
        for task in tasks:
            if task.status != "pending":
                continue
            
            all_completed = False
            
            # 调用 Hook 检测
            completed, reply = task.hook(task.page)
            
            if completed:
                # 二次确认：对比发送前后的内容
                content_after = task.page.evaluate("() => document.body.innerText")
                new_content = content_after[len(task.content_before):]
                
                if len(new_content) < 50:
                    print(f"[{task.name}] ⚠️ 没有新增内容，可能还在处理中")
                    continue
                
                task.status = "completed"
                task.reply_text = reply
                print(f"[{task.name}] ✅ 回复完成 (新增{len(new_content)}字符)")
                continue
            
            # 检查超时
            elapsed = (now - task.start_time).total_seconds()
            if elapsed > global_timeout:
                if task.last_ask_time is None or (now - task.last_ask_time).total_seconds() > 60:
                    print(f"[{task.name}] ⏰ 已超过2分钟")
                    task.last_ask_time = now
                    task.start_time = now
        
        if all_completed:
            print("\n所有平台回复已完成")
            break
        
        time.sleep(check_interval)


def main():
    print("=" * 50)
    print("智库平台问答测试 - AI调试版v3")
    print("=" * 50)
    print(f"问题: {QUESTION}\n")
    
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:18800")
        
        tasks = []
        
        # 遍历所有页面找5个平台
        for page in browser.contexts[0].pages:
            url = page.url.lower()
            
            if "deepseek" in url:
                tasks.append(PlatformTask("DeepSeek", page))
            elif "chatglm" in url:
                tasks.append(PlatformTask("智谱", page))
            elif "qwen" in url:
                tasks.append(PlatformTask("千问", page))
            elif "doubao" in url and "sharedworker" not in url:
                tasks.append(PlatformTask("豆包", page))
            elif "kimi" in url and "chat" in url:
                tasks.append(PlatformTask("Kimi", page))
        
        print(f"共找到 {len(tasks)} 个平台\n")
        
        # 发送问题并保存发送前的内容
        print("=== 发送问题 ===")
        for task in tasks:
            task.content_before = send_question(task.page, task.name, QUESTION)
            task.hook = create_hook(task.page, task.content_before)
        
        # 等待完成
        yield_manager(tasks, global_timeout=120, check_interval=5)
        
        # 汇总结果
        print("\n=== 测试结果 ===")
        for task in tasks:
            status = "✅" if task.status == "completed" else "⏸️"
            print(f"{status} {task.name}: {task.reply_text[:60]}...")


if __name__ == "__main__":
    main()
```

---

## 四、版本信息

- **版本**：v3.0（AI调试版）
- **创建日期**：2026-03-17
- **核心改进**：对比发送前后的内容差异来验证新回复
