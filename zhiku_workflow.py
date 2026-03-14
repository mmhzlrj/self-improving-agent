#!/usr/bin/env python3
"""
智库工作流 - 使用websocket-client直接发送CDP命令
"""
import json
import time
from urllib.request import urlopen
import websocket

class CDPBrowser:
    def __init__(self, ws_url):
        self.ws_url = ws_url
        self.ws = None
        self.msg_id = 0
        
    def connect(self):
        self.ws = websocket.WebSocket()
        self.ws.connect(self.ws_url)
        print("已连接到CDP")
        
    def send(self, method, params=None):
        self.msg_id += 1
        msg = {"id": self.msg_id, "method": method}
        if params:
            msg["params"] = params
        self.ws.send(json.dumps(msg))
        
        # 接收响应
        response = self.ws.recv()
        return json.loads(response)
    
    def navigate(self, url):
        # 使用Page.navigate命令
        result = self.send("Page.navigate", {"url": url})
        # 等待页面加载
        time.sleep(3)
        return result
    
    def fill_and_submit(self, selector, text):
        # 使用Runtime.evaluate执行JS来填写表单
        js_result = self.send("Runtime.evaluate", {
            "expression": f"""
                const el = document.querySelector('{selector}');
                if(el) {{ el.value = '{text}'; el.dispatchEvent(new Event('input')); }}
            """
        })
        
        # 按Enter
        self.send("Runtime.evaluate", {
            "expression": """
                const el = document.querySelector('textarea');
                if(el) { el.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', code: 'Enter'})); }
            """
        })
        
        return True
    
    def get_page_text(self):
        # 获取页面文本
        result = self.send("Runtime.evaluate", {
            "expression": "document.body.innerText.substring(0, 500)"
        })
        if "result" in result and "result" in result["result"]:
            return result["result"]["result"]["value"]
        return ""
    
    def close(self):
        if self.ws:
            self.ws.close()

def main():
    result = {}
    
    # 获取CDP端点
    with urlopen("http://127.0.0.1:18800/json") as response:
        targets = json.loads(response.read())
    
    if not targets:
        print("没有可用的CDP目标")
        return result
    
    page_target = None
    for t in targets:
        if t.get("type") == "page":
            page_target = t
            break
    if not page_target:
        page_target = targets[0]
    
    ws_url = page_target["webSocketDebuggerUrl"]
    print(f"连接CDP: {ws_url}")
    
    browser = CDPBrowser(ws_url)
    browser.connect()
    
    question = "用一句话介绍深圳"
    
    # 时间点1: 千问
    print("\n时间点1: 打开千问...")
    browser.navigate("https://chat.qwen.ai/")
    time.sleep(2)
    browser.fill_and_submit("textarea", question)
    print("千问已提问")
    
    # 时间点2: 智谱
    print("\n时间点2: 打开智谱...")
    browser.navigate("https://chatglm.cn/")
    time.sleep(2)
    browser.fill_and_submit("textarea", question)
    print("智谱已提问")
    
    # 时间点3: Kimi
    print("\n时间点3: 打开Kimi...")
    browser.navigate("https://www.kimi.com/")
    time.sleep(2)
    browser.fill_and_submit("textarea", question)
    print("Kimi已提问")
    
    # 等待回复
    print("\n等待回复 (20秒)...")
    time.sleep(20)
    
    # 时间点4: 豆包
    print("\n时间点4: 打开豆包...")
    browser.navigate("https://www.doubao.com/chat/")
    time.sleep(2)
    browser.fill_and_submit("textarea", question)
    print("豆包已提问")
    
    time.sleep(12)
    
    # 时间点5: DeepSeek
    print("\n时间点5: 打开DeepSeek...")
    browser.navigate("https://chat.deepseek.com/")
    time.sleep(2)
    browser.fill_and_submit("textarea", question)
    print("DeepSeek已提问")
    
    time.sleep(12)
    
    # 时间点6: 收集回复
    print("\n时间点6: 收集回复...")
    
    result["千问"] = browser.get_page_text()
    print(f"千问['千问']: {len(result)} chars")
    
    browser.navigate("https://chatglm.cn/")
    time.sleep(2)
    result["智谱"] = browser.get_page_text()
    print(f"智谱: {len(result['智谱'])} chars")
    
    browser.navigate("https://www.kimi.com/")
    time.sleep(2)
    result["Kimi"] = browser.get_page_text()
    print(f"Kimi: {len(result['Kimi'])} chars")
    
    browser.navigate("https://www.doubao.com/chat/")
    time.sleep(2)
    result["豆包"] = browser.get_page_text()
    print(f"豆包: {len(result['豆包'])} chars")
    
    browser.navigate("https://chat.deepseek.com/")
    time.sleep(2)
    result["DeepSeek"] = browser.get_page_text()
    print(f"DeepSeek: {len(result['DeepSeek'])} chars")
    
    browser.close()
    
    print("\n" + "="*50)
    print("最终结果:")
    for k, v in result.items():
        print(f"\n【{k}】\n{v[:200]}...")
    
    return result

if __name__ == "__main__":
    main()
