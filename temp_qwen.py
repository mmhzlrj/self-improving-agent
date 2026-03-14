#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import time

def main():
    with sync_playwright() as p:
        # 连接到 CDP 浏览器
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:18800")
        
        # 获取所有上下文和页面
        contexts = browser.contexts
        page = None
        
        # 尝试找到千问页面
        for ctx in contexts:
            for p in ctx.pages:
                if "chat.qwen.ai" in p.url:
                    page = p
                    print(f"找到已有页面: {p.url}")
                    break
            if page:
                break
        
        # 如果没有找到，打开新标签页
        if not page:
            if contexts:
                ctx = contexts[0]
            else:
                ctx = browser.new_context()
            page = ctx.new_page()
            page.goto("https://chat.qwen.ai")
            print("已打开新标签页: chat.qwen.ai")
        
        # 等待 DOM 加载完成而不是 networkidle
        page.wait_for_load_state("domcontentloaded")
        time.sleep(5)  # 额外等待让页面完全渲染
        
        # 点击页面底部激活输入框
        # 先获取页面大小
        viewport = page.viewport_size
        if viewport:
            # 点击页面底部中央位置（通常是输入框位置）
            page.mouse.click(viewport['width'] // 2, viewport['height'] - 100)
            time.sleep(1)
        
        # 输入问题
        page.keyboard.type("什么是AI", delay=30)
        time.sleep(0.5)
        
        # 发送 - 按 Enter
        page.keyboard.press("Enter")
        
        print("已发送问题: 什么是AI")
        
        # 等待15秒让AI生成回复
        print("等待15秒...")
        time.sleep(15)
        
        # 获取回复内容 - 获取整个页面的文本
        response_text = page.locator("body").inner_text()
        
        # 清理文本，提取回答部分
        if "什么是AI" in response_text:
            idx = response_text.find("什么是AI")
            # 找到问题的下一个部分
            response_text = response_text[idx:]
        
        print("\n" + "=" * 60)
        print("【千问】" + response_text[:1500])
        print("=" * 60)
        
        browser.close()

if __name__ == "__main__":
    main()
