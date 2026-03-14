# Playwright 连接已登录 Chrome 解决 DeepSeek 输入问题 SOP

## 背景

- **问题**：DeepSeek 网页版有反自动化检测，CDP 脚本输入被识别
- **已有条件**：Google Chrome 已登录 DeepSeek（通过 Browser Relay）
- **解决方案**：用 Playwright 连接已有 Chrome，绕过反自动化检测

---

## 配置清单

| 项目 | 值 |
|------|-----|
| Playwright | 1.58.0（已安装）|
| Chrome CDP | 127.0.0.1:18800 |
| 目标页面 | https://chat.deepseek.com/ |

---

## 完整操作流程

### Step A: 连接已有 Chrome（CDP）

```python
from playwright.sync_api import sync_playwright

# Step A: 通过 CDP 连接已有 Chrome
with sync_playwright() as p:
    try:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:18800")
        print("✅ 已连接 Chrome")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        raise
```

### Step B: 获取 DeepSeek 页面

```python
    # Step B: 获取已登录的上下文
    if len(browser.contexts) == 0:
        print("❌ 没有找到浏览器上下文")
        raise Exception("No browser context")
    
    context = browser.contexts[0]
    
    # 查找已打开的 DeepSeek 页面
    deepseek_page = None
    for page in context.pages:
        if "deepseek" in page.url.lower():
            deepseek_page = page
            print(f"✅ 找到 DeepSeek 页面: {page.url}")
            break
    
    # 如果没有 DeepSeek 页面，则新建
    if not deepseek_page:
        deepseek_page = context.new_page()
        deepseek_page.goto("https://chat.deepseek.com/")
        print("✅ 已打开 DeepSeek 页面")
```

### Step C: 验证登录状态

```python
    # Step C: 等待页面加载并检查登录状态
    deepseek_page.wait_for_load_state("networkidle", timeout=10000)
    page_text = deepseek_page.inner_text("body")
    
    if "登录" in page_text or "Sign in" in page_text:
        print("❌ 未登录，请先在 Chrome 中登录 DeepSeek")
        raise Exception("Not logged in")
    else:
        print("✅ 已登录")
```

### Step D: 找到并聚焦输入框

```python
    # Step D: 等待输入框出现
    deepseek_page.wait_for_selector("textarea", timeout=5000)
    
    # 找到输入框
    input_box = deepseek_page.locator("textarea").first
    
    # 检查输入框是否可见
    if not input_box.is_visible():
        print("❌ 输入框不可见")
        raise Exception("Input box not visible")
    
    # 点击聚焦输入框
    input_box.click()
    print("✅ 已聚焦输入框")
```

### Step E: 模拟打字输入（关键步骤）

```python
    # Step E: 模拟真实打字（关键：绕过反自动化）
    question = "Explain what AI is in one sentence."
    
    # 使用 keyboard.type 带 delay 参数，模拟人类打字速度
    # delay=50-100ms 是比较真实的速度
    deepseek_page.keyboard.type(question, delay=100)
    print(f"✅ 已输入: {question}")
    
    # 验证输入成功
    input_value = input_box.input_value()
    print(f"输入框内容: {input_value}")
```

### Step F: 发送问题

```python
    # Step F: 发送问题
    # 方式1: 按 Enter
    deepseek_page.keyboard.press("Enter")
    print("✅ 已按 Enter 发送")
    
    # 等待一小段时间
    deepseek_page.wait_for_timeout(1000)
```

### Step G: 等待 AI 回复

```python
    # Step G: 等待回复生成
    # 方式1: 等待固定时间（简单粗暴）
    print("等待 AI 回复...")
    deepseek_page.wait_for_timeout(15000)  # 等待15秒
    
    # 方式2: 轮询检查加载状态（更智能）
    max_wait = 60
    interval = 3
    elapsed = 0
    
    while elapsed < max_wait:
        # 检查是否有"思考中"等加载提示
        loading = deepseek_page.locator("text=思考中, text=生成中, text=loading").count()
        if loading == 0:
            print("✅ AI 回复完成")
            break
        print(f"等待中... ({elapsed}s)")
        deepseek_page.wait_for_timeout(interval)
        elapsed += interval
```

### Step H: 获取回复内容

```python
    # Step H: 获取 AI 回复
    # 查找消息容器（需要根据实际 DOM结构调整）
    
    # 尝试多种选择器
    selectors = [
        "div[class*='message']",
        "div[class*='response']", 
        "div[class*='content']",
        ".ds-markdown"
    ]
    
    response_text = ""
    for selector in selectors:
        elements = deepseek_page.locator(selector).all()
        for elem in elements[-3:]:  # 取最后几条
            text = elem.inner_text()
            if len(text) > 50:  # 过滤掉短文本
                response_text = text
                break
        if response_text:
            break
    
    if response_text:
        print(f"✅ 获取到回复 ({len(response_text)} 字符):")
        print(response_text[:500])
    else:
        print("❌ 未获取到回复")
        # 截图调试
        deepseek_page.screenshot(path="/tmp/deepseek-response.png")
        print("截图已保存到 /tmp/deepseek-response.png")
```

---

## 完整代码

```python
#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import sys

def main():
    with sync_playwright() as p:
        # Step A: 连接已有 Chrome
        try:
            browser = p.chromium.connect_over_cdp("http://127.0.0.1:18800")
            print("✅ 已连接 Chrome")
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            sys.exit(1)
        
        # Step B: 获取 DeepSeek 页面
        if len(browser.contexts) == 0:
            print("❌ 没有浏览器上下文")
            sys.exit(1)
        
        context = browser.contexts[0]
        deepseek_page = None
        
        for page in context.pages:
            if "deepseek" in page.url.lower():
                deepseek_page = page
                print(f"✅ 找到 DeepSeek: {page.url}")
                break
        
        if not deepseek_page:
            deepseek_page = context.new_page()
            deepseek_page.goto("https://chat.deepseek.com/")
        
        # Step C: 验证登录
        deepseek_page.wait_for_load_state("networkidle", timeout=10000)
        if "登录" in deepseek_page.inner_text("body"):
            print("❌ 未登录")
            sys.exit(1)
        print("✅ 已登录")
        
        # Step D-F: 输入并发送
        deepseek_page.wait_for_selector("textarea", timeout=5000)
        input_box = deepseek_page.locator("textarea").first
        input_box.click()
        
        question = "Explain what AI is in one sentence."
        deepseek_page.keyboard.type(question, delay=100)
        deepseek_page.keyboard.press("Enter")
        
        # Step G: 等待回复
        deepseek_page.wait_for_timeout(15000)
        
        # Step H: 获取回复
        # (省略获取逻辑，见上文)
        
        browser.close()

if __name__ == "__main__":
    main()
```

---

## 重要原则

1. **连接已有 Chrome** - 不启动新浏览器，复用登录状态
2. **type 带 delay** - 模拟真实打字速度（50-100ms）
3. **先验证登录** - 未登录不执行后续操作
4. **异常处理** - 每步都要 try-except
5. **严格按照 SOP 执行** - 必须严格按照 SOP 的步骤和脚本执行，禁止跳步或省略
6. **记录执行经验** - 每次执行一个步骤后，都要记录犯错或成功的经验到执行日志文档

---

## 测试清单

| 步骤 | 操作 | 状态 |
|------|------|------|
| 1 | 连接已有 Chrome（CDP） | ⬜ |
| 2 | 获取 DeepSeek 页面 | ⬜ |
| 3 | 验证登录状态 | ⬜ |
| 4 | 找到并聚焦输入框 | ⬜ |
| 5 | 模拟打字输入 | ⬜ |
| 6 | 发送问题 | ⬜ |
| 7 | 等待 AI 回复 | ⬜ |
| 8 | 获取回复内容 | ⬜ |
