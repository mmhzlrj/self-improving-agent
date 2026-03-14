#!/usr/bin/env python3
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        # 连接到现有的浏览器通过 CDP
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:18800")
        
        # 获取所有上下文
        contexts = browser.contexts
        
        # 尝试找到 kimi.com 页面
        kimi_page = None
        for ctx in contexts:
            for page in ctx.pages:
                if "kimi.com" in page.url:
                    kimi_page = page
                    print(f"找到 Kimi 页面: {page.url}")
                    break
            if kimi_page:
                break
        
        # 如果没有找到 Kimi 页面，打开新标签页
        if not kimi_page:
            print("未找到 Kimi 页面，正在打开新标签页...")
            if contexts:
                kimi_page = await contexts[0].new_page()
            else:
                ctx = await browser.new_context()
                kimi_page = await ctx.new_page()
            
            await kimi_page.goto("https://kimi.com")
            print(f"已打开 Kimi: {kimi_page.url}")
        
        # 等待页面加载完成
        await kimi_page.wait_for_load_state("networkidle")
        await asyncio.sleep(3)
        
        # 点击新建会话按钮以确保输入框可见
        try:
            new_chat_btn = await kimi_page.query_selector("text=新建会话")
            if new_chat_btn:
                await new_chat_btn.click()
                print("已点击新建会话")
                await asyncio.sleep(2)
        except Exception as e:
            print(f"点击新建会话失败: {e}")
        
        print("正在查找输入框...")
        
        # 尝试多种选择器找到输入框
        input_selectors = [
            "textarea",
            "div[contenteditable='true']",
            "input[type='text']",
            ".chat-input textarea",
            "[class*='input']",
            "[class*='Input']",
        ]
        
        input_box = None
        for selector in input_selectors:
            try:
                input_box = await kimi_page.query_selector(selector)
                if input_box:
                    print(f"找到输入框: {selector}")
                    break
            except:
                continue
        
        if input_box:
            await input_box.fill("什么是AI")
            print("已输入问题: 什么是AI")
            
            # 发送消息
            try:
                # 尝试按 Enter 发送
                await input_box.press("Enter")
                print("已发送消息")
            except Exception as e:
                print(f"按 Enter 发送失败: {e}")
                # 尝试点击发送按钮
                try:
                    send_btn = await kimi_page.query_selector("button:has-text('发送')")
                    if send_btn:
                        await send_btn.click()
                        print("已点击发送按钮")
                except:
                    pass
        else:
            # 如果找不到输入框，尝试截图查看页面结构
            await kimi_page.screenshot(path="/Users/lr/.openclaw/workspace/kimi_page.png")
            print("已截图到 kimi_page.png")
            
            # 打印页面中的按钮和输入元素
            textareas = await kimi_page.query_selector_all("textarea")
            print(f"找到 {len(textareas)} 个 textarea")
            
            inputs = await kimi_page.query_selector_all("input")
            print(f"找到 {len(inputs)} 个 input")
            
            buttons = await kimi_page.query_selector_all("button")
            print(f"找到 {len(buttons)} 个 button")
            for btn in buttons[:5]:
                text = await btn.text_content()
                print(f"  按钮: {text[:50] if text else 'None'}")
        
        # 等待 15 秒让 AI 生成回复
        print("\n等待 15 秒让 AI 生成回复...")
        await asyncio.sleep(15)
        
        # 获取回复内容
        print("正在获取回复...")
        
        # 尝试多种方式获取回复
        # 首先尝试获取整个对话内容
        try:
            # 查找所有消息内容
            message_containers = await kimi_page.query_selector_all("[class*='message'], [class*='Message'], .markdown-body")
            print(f"找到 {len(message_containers)} 个消息容器")
            
            for elem in reversed(message_containers):
                text = await elem.text_content()
                if text and len(text) > 100:  # 找到较长的回复
                    print(f"\n=== Kimi 回复 ===\n{text[:3000]}")
                    break
        except Exception as e:
            print(f"获取回复失败: {e}")
        
        # 如果上面的方法不行，获取整个页面的文本
        try:
            body = await kimi_page.query_selector("body")
            if body:
                full_text = await body.text_content()
                # 找到 "什么是AI" 之后的文本
                if "什么是AI" in full_text:
                    idx = full_text.index("什么是AI")
                    response = full_text[idx + len("什么是AI"):]
                    if len(response) > 50:
                        print(f"\n=== Kimi 回复 ===\n{response[:3000]}")
        except Exception as e:
            print(f"获取完整文本失败: {e}")
        
        await browser.close()
        print("\n任务完成")

if __name__ == "__main__":
    asyncio.run(main())
