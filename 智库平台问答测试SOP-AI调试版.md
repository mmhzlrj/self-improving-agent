# 智库平台问答测试 SOP（AI调试版 v2）

基于人工测试问题和豆包AI建议整合

---

## 一、已成功经验

### 平台配置
| 平台 | 配置 |
|------|------|
| DeepSeek | 深度思考 + 智能搜索 |
| 智谱 | 思考 + 联网 |
| 千问 | 默认 |
| 豆包 | 专家模式 |
| Kimi | K2.5思考 |

---

## 二、测试问题

### 问题1：获取到历史内容而非新问题回答
- **原因**：hook只检查内容长度>200，页面有历史对话导致误判
- **影响**：4/5平台获取到历史内容

### 问题2：Kimi发送失败
- **原因**：选择器不对

### 问题3：千问发送失败
- **原因**：Monaco代码编辑器阻挡输入框

### 问题4：二次确认逻辑
- **原因**：对比长度不准确

---

## 三、AI建议（豆包回复）

### 3.1 hook验证改进
```python
def create_hook(page, question_keyword):
    """检测回复是否完成，并验证是新问题的回答"""
    
    def hook(page):
        # 方法1：检测复制按钮
        try:
            for loc in [page.get_by_text("复制"), page.get_by_text("Copy")]:
                if loc.count() > 0 and loc.first.is_visible(timeout=2000):
                    content = page.evaluate("() => document.body.innerText")
                    # 验证：检查是否包含问题关键词
                    if question_keyword in content or len(content) > 500:
                        return True, content[:2000]
        except:
            pass
        
        # 方法2：检查内容长度
        content = page.evaluate("() => document.body.innerText")
        if len(content) > 500:
            return True, content[:2000]
        
        return False, ""
    
    return hook
```

### 3.2 按钮检测优化
```python
# 多维度定位"复制"按钮
copy_locators = [
    page.get_by_text("复制", exact=False),
    page.locator("[aria-label*='复制'], [aria-label*='copy']"),
    page.locator("[title*='复制'], [title*='copy']"),
    page.locator("[class*='copy'], [class*='btn-copy']"),
]

# 等待元素可见且可点击
for locator in copy_locators:
    try:
        locator.first.wait_for(state="visible", timeout=3000)
        if locator.first.is_visible():
            return True, content
    except:
        continue
```

### 3.3 千问处理
- 先点击 body 获取焦点
- 等待页面稳定后再操作

---

## 四、改进后的代码框架

```python
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

QUESTION = "请用一句话解释什么是人工智能？"

class PlatformTask:
    def __init__(self, name, page, question_keyword):
        self.name = name
        self.page = page
        self.question_keyword = question_keyword  # 问题关键词
        self.status = "pending"
        self.reply_text = ""
        self.start_time = datetime.now()
        self.last_ask_time = None


def create_hook(page, question_keyword):
    """检测回复是否完成，并验证是新问题的回答"""
    
    def hook(page):
        # 方法1：检测复制按钮
        try:
            strategies = [
                page.get_by_text("复制", exact=False),
                page.get_by_text("Copy", exact=False),
                page.locator("[aria-label*='复制']"),
                page.locator("[title*='复制']"),
            ]
            
            for loc in strategies:
                if loc.count() > 0:
                    try:
                        if loc.first.is_visible(timeout=2000):
                            content = page.evaluate("() => document.body.innerText")
                            # 验证：检查是否包含问题关键词
                            if question_keyword in content or len(content) > 500:
                                return True, content[:2000]
                    except:
                        pass
        except:
            pass
        
        # 方法2：检查内容长度（需要足够长）
        content = page.evaluate("() => document.body.innerText")
        if len(content) > 500:
            # 额外验证：检查是否包含问题关键词
            if question_keyword in content:
                return True, content[:2000]
        
        return False, ""
    
    return hook


def send_question(page, platform_name, question):
    """发送问题"""
    
    # 新建窗口方式发送
    if platform_name == "Kimi":
        page.goto("https://www.kimi.com/?chat_enter_method=new_chat")
        page.wait_for_timeout(3000)
    elif platform_name == "豆包":
        page.goto("https://www.doubao.com/chat/")
        page.wait_for_timeout(2000)
        # 切换专家模式
        # ...
    else:
        page.goto(f"https://chat.{platform_name}.com/")
        page.wait_for_timeout(2000)
    
    # 发送问题
    page.wait_for_selector("textarea", timeout=5000)
    page.click("textarea")
    page.keyboard.type(question, delay=50)
    page.keyboard.press("Enter")


def yield_manager(tasks, global_timeout=120, check_interval=5):
    """主循环"""
    
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
                # 二次确认：检查是否包含问题关键词
                if task.question_keyword not in reply:
                    print(f"[{task.name}] 警告：回复可能不是新问题的回答")
                    reply = task.page.evaluate("() => document.body.innerText")[:2000]
                
                task.status = "completed"
                task.reply_text = reply
                print(f"[{task.name}] ✅ 回复完成")
                continue
            
            # 检查超时
            elapsed = (now - task.start_time).total_seconds()
            if elapsed > global_timeout:
                if task.last_ask_time is None or (now - task.last_ask_time).total_seconds() > 60:
                    print(f"[{task.name}] ⏰ 已超过2分钟")
                    task.last_ask_time = now
                    task.start_time = now
        
        if all_completed:
            break
        
        time.sleep(check_interval)


def main():
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:18800")
        
        # 平台配置
        platforms = [
            ("DeepSeek", "deepseek", "已思考"),
            ("智谱", "chatglm", "思考结束"),
            ("千问", "qwen", "已经完成思考"),
            ("豆包", "doubao", "就是让机器模拟"),
            ("Kimi", "kimi", "编辑"),
        ]
        
        tasks = []
        
        # 为每个平台创建任务
        for page in browser.contexts[0].pages:
            url = page.url.lower()
            for name, key, keyword in platforms:
                if key in url:
                    # 用问题关键词作为验证
                    question_keyword = QUESTION[:20]
                    tasks.append(PlatformTask(name, page, question_keyword))
                    tasks[-1].hook = create_hook(page, question_keyword)
                    break
        
        # 发送问题
        for task in tasks:
            send_question(task.page, task.name, QUESTION)
        
        # 等待完成
        yield_manager(tasks)


if __name__ == "__main__":
    main()
```

---

## 五、版本信息

- **版本**：v2.0（AI调试版）
- **创建日期**：2026-03-17
- **基于**：人工测试 + 豆包AI建议
