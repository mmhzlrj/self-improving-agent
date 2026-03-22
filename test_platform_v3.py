#!/usr/bin/env python3
"""智库平台问答测试 - 第1次测试"""
import time
import json
import os
from datetime import datetime
from playwright.sync_api import sync_playwright

QUESTION = "请用一句话解释什么是人工智能？"

class PlatformTask:
    def __init__(self, name, page):
        self.name = name
        self.page = page
        self.status = "pending"
        self.reply_text = ""
        self.start_time = datetime.now()
        self.last_ask_time = None
        self.hook = None

def create_hook(page):
    def hook(page):
        # 方法1：检测复制按钮出现
        try:
            strategies = [
                page.get_by_text("复制", exact=False),
                page.get_by_text("Copy", exact=False),
                page.get_by_role("button", name="复制"),
            ]
            for loc in strategies:
                if loc.count() > 0 and loc.first.is_visible(timeout=2000):
                    reply = page.evaluate("() => document.body.innerText")
                    return True, reply[:2000]
        except Exception as e:
            pass
        
        # 方法2：检查内容长度
        content = page.evaluate("() => document.body.innerText")
        if len(content) > 200:
            return True, content[:2000]
        
        return False, ""
    return hook

def send_question(page, platform_name):
    """发送问题到指定平台"""
    print(f"[{platform_name}] 发送问题...")
    
    try:
        # 豆包：滚动到底部
        if platform_name == "豆包":
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(500)
        
        # 千问：先获取焦点
        if platform_name == "千问":
            page.click("body")
            page.wait_for_timeout(300)
        
        # Kimi：新建会话
        if platform_name == "Kimi":
            try:
                new_btn = page.get_by_text("新建会话").or_(page.get_by_text("+"))
                if new_btn.count() > 0:
                    new_btn.first.click()
                    page.wait_for_timeout(1000)
            except:
                pass
        
        # 等待输入框
        try:
            page.wait_for_selector("textarea", timeout=3000)
        except:
            page.get_by_role("textbox").first.click()
            page.wait_for_timeout(500)
        
        page.click("textarea")
        page.wait_for_timeout(300)
        
        # 输入并发送
        page.keyboard.type(QUESTION, delay=50)
        page.wait_for_timeout(300)
        page.keyboard.press("Enter")
        
        print(f"[{platform_name}] ✅ 问题已发送")
        return True
    except Exception as e:
        print(f"[{platform_name}] ❌ 发送失败: {str(e)[:100]}")
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
            elapsed = (now - task.start_time).total_seconds()
            
            # 调用 Hook 检测
            completed, reply = task.hook(task.page)
            
            if completed:
                # 二次确认
                actual_content = task.page.evaluate("() => document.body.innerText")
                
                if len(reply) < len(actual_content) * 0.8:
                    print(f"[{task.name}] ⚠️ 回复不完整，重新获取")
                    reply = actual_content[:2000]
                
                task.status = "completed"
                task.reply_text = reply
                print(f"[{task.name}] ✅ 回复完成（二次确认通过）")
                continue
            
            # 检查超时
            if elapsed > global_timeout:
                if task.last_ask_time is None or (now - task.last_ask_time).total_seconds() > 60:
                    print(f"\n[{task.name}] ⏰ 已超过2分钟，仍在等待")
                    task.last_ask_time = now
                    task.start_time = now
                    print(f"[{task.name}] 继续等待...")
        
        if all_completed:
            print("\n所有平台回复已完成")
            break
        
        time.sleep(check_interval)

def main():
    print("=" * 50)
    print("智库平台问答测试 - 第1次测试")
    print("=" * 50)
    print(f"问题: {QUESTION}\n")
    
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:18800")
        
        tasks = []
        
        # 遍历所有页面
        for page in browser.contexts[0].pages:
            url = page.url.lower()
            
            if "deepseek" in url:
                tasks.append(PlatformTask("DeepSeek", page))
                print("找到 DeepSeek")
            elif "chatglm" in url:
                tasks.append(PlatformTask("智谱", page))
                print("找到 智谱")
            elif "qwen" in url:
                tasks.append(PlatformTask("千问", page))
                print("找到 千问")
            elif "doubao" in url:
                tasks.append(PlatformTask("豆包", page))
                print("找到 豆包")
            elif "kimi" in url:
                tasks.append(PlatformTask("Kimi", page))
                print("找到 Kimi")
        
        print(f"\n共找到 {len(tasks)} 个平台\n")
        
        # 创建 hook
        for task in tasks:
            task.hook = create_hook(task.page)
        
        # 发送问题
        print("=== 发送问题 ===")
        for task in tasks:
            send_question(task.page, task.name)
        
        # 启动 yield_manager
        yield_manager(tasks, global_timeout=120, check_interval=5)
        
        # 汇总结果
        print("\n" + "=" * 50)
        print("=== 最终结果 ===")
        print("=" * 50)
        
        for task in tasks:
            status = "✅" if task.status == "completed" else "⏸️"
            reply_preview = task.reply_text[:80].replace('\n', ' ') if task.reply_text else "(无回复)"
            print(f"{status} {task.name}: {reply_preview}...")
            
            # 保存到文件
            if task.reply_text:
                filename = os.path.expanduser(f"~/.openclaw/workspace/memory/test-{task.name}.txt")
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(task.reply_text)
                print(f"   → 已保存到 {filename}")
        
        browser.close()

if __name__ == "__main__":
    main()
