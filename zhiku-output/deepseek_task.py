#!/usr/bin/env python3
"""DeepSeek Automation - Continue with existing session"""
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        # 使用已有的浏览器上下文
        context = await p.chromium.launch_persistent_context(
            user_data_dir="/tmp/playwright-deepseek",
            headless=False
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        # 刷新页面检查登录状态
        print("检查登录状态...")
        await page.goto("https://chat.deepseek.com/")
        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(3)
        
        await page.screenshot(path="/tmp/deepseek-check.png")
        
        page_text = await page.evaluate('() => document.body.innerText')
        
        if "登录" in page_text and "手机号" in page_text:
            print("仍然需要登录")
            print("请在弹出的浏览器窗口中完成登录")
            print("完成后等待...")
            await asyncio.sleep(60)  # 等待用户手动登录
        else:
            print("已登录")
        
        # 查找输入框
        print("查找输入框...")
        selectors = ['textarea', 'div[contenteditable="true"]', '[contenteditable="true"]']
        
        input_box = None
        for sel in selectors:
            try:
                el = page.locator(sel).first
                if await el.is_visible():
                    print(f"找到: {sel}")
                    input_box = el
                    break
            except:
                continue
        
        if input_box:
            await input_box.click()
            await input_box.fill("用一句话介绍深圳")
            await asyncio.sleep(1)
            await input_box.press("Enter")
            print("已发送问题")
            
            # 等待回复
            print("等待回复...")
            for _ in range(40):  # 最多等待120秒
                await asyncio.sleep(3)
                
                # 检查停止按钮
                try:
                    stop = page.locator('button:has-text("停止")').first
                    if await stop.is_visible():
                        print("正在生成...")
                        continue
                except: pass
                
                # 检查思考中
                try:
                    think = page.locator('text=思考中').first
                    if await think.is_visible():
                        continue
                except: pass
                
                print("完成，提取内容...")
                break
            
            # 提取内容
            content = await page.evaluate('''() => {
                const msgs = document.querySelectorAll('[class*="message"], [role="article"]');
                let text = '';
                msgs.forEach(m => text += m.innerText + '\\n=====\\n');
                return text || document.body.innerText;
            }''')
            
            output_path = "/Users/lr/.openclaw/workspace/zhiku-output/agent3-DeepSeek.md"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"# DeepSeek 回复\n\n**问题**: 用一句话介绍深圳\n\n**回复**:\n\n{content}")
            
            print(f"已保存: {output_path}")
        else:
            print("未找到输入框")
        
        await context.close()

asyncio.run(main())
