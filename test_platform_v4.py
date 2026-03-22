#!/usr/bin/env python3
"""智库平台问答测试 - AI调试版v2 测试"""
import time
import os
from datetime import datetime
from playwright.sync_api import sync_playwright

QUESTION = "请用一句话解释什么是人工智能？"
QUESTION_KEYWORD = QUESTION[:20]  # 用于验证

class PlatformTask:
    def __init__(self, name, page, question_keyword):
        self.name = name
        self.page = page
        self.question_keyword = question_keyword
        self.status = "pending"
        self.reply_text = ""
        self.start_time = datetime.now()
        self.last_ask_time = None
        self.hook = None

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
    print(f"[{platform_name}] 发送问题...")
    
    try:
        # 豆包：滚动到底部
        if platform_name == "豆包":
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(0.5)
            # 点击新对话
            try:
                new_btn = page.get_by_text("新对话").or_(page.get_by_text("+"))
                if new_btn.count() > 0:
                    new_btn.first.click()
                    time.sleep(1)
            except:
                pass
        
        # 千问：先获取焦点
        if platform_name == "千问":
            page.click("body")
            time.sleep(0.5)
        
        # Kimi：新会话
        if platform_name == "Kimi":
            page.goto("https://www.kimi.com/?chat_enter_method=new_chat")
            time.sleep(3)
        
        # 等待输入框
        try:
            page.wait_for_selector("textarea", timeout=5000)
        except:
            page.get_by_role("textbox").first.click()
            time.sleep(0.5)
        
        page.click("textarea")
        time.sleep(0.3)
        
        # 输入并发送
        page.keyboard.type(question, delay=50)
        time.sleep(0.3)
        page.keyboard.press("Enter")
        
        print(f"[{platform_name}] ✅ 问题已发送")
        return True
    except Exception as e:
        print(f"[{platform_name}] ❌ 发送失败: {str(e)[:80]}")
        return False

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
                # 二次确认：检查是否包含问题关键词
                if task.question_keyword not in reply:
                    print(f"[{task.name}] ⚠️ 回复可能不是新问题的回答，重新获取")
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
            print("\n所有平台回复已完成")
            break
        
        time.sleep(check_interval)

def main():
    print("=" * 50)
    print("智库平台问答测试 - AI调试版v2")
    print("=" * 50)
    print(f"问题: {QUESTION}\n")
    
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:18800")
        
        tasks = []
        
        # 遍历所有页面找5个平台
        for page in browser.contexts[0].pages:
            url = page.url.lower()
            
            if "deepseek" in url:
                tasks.append(PlatformTask("DeepSeek", page, QUESTION_KEYWORD))
                print("找到 DeepSeek")
            elif "chatglm" in url:
                tasks.append(PlatformTask("智谱", page, QUESTION_KEYWORD))
                print("找到 智谱")
            elif "qwen" in url:
                tasks.append(PlatformTask("千问", page, QUESTION_KEYWORD))
                print("找到 千问")
            elif "doubao" in url and "sharedworker" not in url:
                tasks.append(PlatformTask("豆包", page, QUESTION_KEYWORD))
                print("找到 豆包")
            elif "kimi" in url and "chat" in url:
                tasks.append(PlatformTask("Kimi", page, QUESTION_KEYWORD))
                print("找到 Kimi")
        
        print(f"\n共找到 {len(tasks)} 个平台\n")
        
        # 创建hook
        for task in tasks:
            task.hook = create_hook(task.page, task.question_keyword)
        
        # 发送问题
        print("=== 发送问题 ===")
        for task in tasks:
            send_question(task.page, task.name, QUESTION)
        
        # 等待完成
        yield_manager(tasks, global_timeout=120, check_interval=5)
        
        # 汇总结果
        print("\n" + "=" * 50)
        print("=== 测试结果 ===")
        print("=" * 50)
        
        for task in tasks:
            status = "✅" if task.status == "completed" else "⏸️"
            # 检查是否包含问题关键词
            has_keyword = QUESTION_KEYWORD in task.reply_text if task.reply_text else False
            keyword_status = "✓含关键词" if has_keyword else "✗无关键词"
            
            preview = task.reply_text[:60].replace('\n', ' ') if task.reply_text else "(无)"
            print(f"{status} {task.name}: {keyword_status}")
            print(f"   内容: {preview}...")
            
            # 保存到文件
            if task.reply_text:
                filename = os.path.expanduser(f"~/.openclaw/workspace/memory/test-v2-{task.name}.txt")
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(task.reply_text)
                print(f"   → 已保存")

if __name__ == "__main__":
    main()
