# 智库 5 平台配置 SOP

## 背景
配置 5 个 AI 平台的思考/推理模型和联网功能，实现自动化操作。

## 配置清单

| 平台 | 需要开启 | 注意事项 |
|------|----------|----------|
| Kimi | K2.5快速→K2.5思考 | 只有这个，没有联网 |
| DeepSeek | 深度思考、智能搜索 | 两个都有 |
| 智谱 | 联网和思考 | 两个都有 |
| 千问 | 保持默认 | 不需要操作 |
| 豆包 | 快速→专家模式 | 只有这个，没有联网 |

---

## 完整操作流程

### 准备工作

**1. 检查 CDP 连接**
```bash
curl http://127.0.0.1:18800/json
```

**2. 获取页面 ID**
```
Kimi: 64DB20B19E8ACADB8EABBB4B60424CE1
DeepSeek: 56C6284264CE26AEC4AD0E737364C4E4
智谱: 1A4761E78836289D0F7A0254AAE62FFC
千问: 6C0A51B4C2D1BD551F3CB50E18C2A1AA
豆包: EB57129E223F493E25ACC1A26F7878D7
```

**3. 建立 WebSocket 连接**
```python
ws = websocket.create_connection(f"ws://127.0.0.1:18800/devtools/page/{page_id}")
```

---

### DeepSeek - 深度思考

**Step A: 用 XPath 找到按钮**
```python
cmd = {"id": 1, "method": "Runtime.evaluate", "params": {"expression": """
    const result = document.evaluate(
        '//*[contains(text(), "深度思考")]',
        document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
    );
    const btn = result.singleNodeValue;
    btn ? '找到按钮' : '未找到';
"""}}
```

**Step B: 检查当前状态**
```python
cmd = {"id": 1, "method": "Runtime.evaluate", "params": {"expression": """
    const result = document.evaluate(
        '//*[contains(text(), "深度思考")]',
        document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
    );
    const btn = result.singleNodeValue;
    let parent = btn.parentElement;
    let isActive = false;
    for (let i = 0; i < 5; i++) {
        if (parent && parent.className && parent.className.includes('active')) {
            isActive = true;
            break;
        }
        parent = parent.parentElement;
    }
    isActive ? '已开启' : '已关闭';
"""}}
```

**Step C: 只在关闭状态时才点击**
```python
cmd = {"id": 1, "method": "Runtime.evaluate", "params": {"expression": """
    const result = document.evaluate(
        '//*[contains(text(), "深度思考")]',
        document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
    );
    const btn = result.singleNodeValue;
    let parent = btn.parentElement;
    let isActive = false;
    for (let i = 0; i < 5; i++) {
        if (parent && parent.className && parent.className.includes('active')) {
            isActive = true;
            break;
        }
        parent = parent.parentElement;
    }
    if (!isActive) {
        btn.click();
        '已点击开启';
    } else {
        '无需点击，已开启';
    }
"""}}
```

**Step D: 验证结果**
```python
cmd = {"id": 1, "method": "Runtime.evaluate", "params": {"expression": """
    const start = Date.now();
    while (Date.now() - start < 1000) {}
    
    const result = document.evaluate(
        '//*[contains(text(), "深度思考")]',
        document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
    );
    const btn = result.singleNodeValue;
    let parent = btn.parentElement;
    let isActive = false;
    for (let i = 0; i < 5; i++) {
        if (parent && parent.className && parent.className.includes('active')) {
            isActive = true;
            break;
        }
        parent = parent.parentElement;
    }
    isActive ? '✅ 已开启成功' : '❌ 开启失败';
"""}}
```

---

### DeepSeek - 智能搜索

**Step A: 用 XPath 找到按钮**
```python
cmd = {"id": 1, "method": "Runtime.evaluate", "params": {"expression": """
    const result = document.evaluate(
        '//*[contains(text(), "智能搜索")]',
        document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
    );
    const btn = result.singleNodeValue;
    btn ? '找到按钮' : '未找到';
"""}}
```

**Step B: 检查当前状态**
```python
cmd = {"id": 1, "method": "Runtime.evaluate", "params": {"expression": """
    const result = document.evaluate(
        '//*[contains(text(), "智能搜索")]',
        document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
    );
    const btn = result.singleNodeValue;
    let parent = btn.parentElement;
    let isActive = false;
    for (let i = 0; i < 5; i++) {
        if (parent && parent.className && parent.className.includes('active')) {
            isActive = true;
            break;
        }
        parent = parent.parentElement;
    }
    isActive ? '已开启' : '已关闭';
"""}}
```

**Step C: 只在关闭状态时才点击**
```python
cmd = {"id": 1, "method": "Runtime.evaluate", "params": {"expression": """
    const result = document.evaluate(
        '//*[contains(text(), "智能搜索")]',
        document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
    );
    const btn = result.singleNodeValue;
    let parent = btn.parentElement;
    let isActive = false;
    for (let i = 0; i < 5; i++) {
        if (parent && parent.className && parent.className.includes('active')) {
            isActive = true;
            break;
        }
        parent = parent.parentElement;
    }
    if (!isActive) {
        btn.click();
        '已点击开启';
    } else {
        '无需点击，已开启';
    }
"""}}
```

**Step D: 验证结果**
```python
cmd = {"id": 1, "method": "Runtime.evaluate", "params": {"expression": """
    const start = Date.now();
    while (Date.now() - start < 1000) {}
    
    const result = document.evaluate(
        '//*[contains(text(), "智能搜索")]',
        document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
    );
    const btn = result.singleNodeValue;
    let parent = btn.parentElement;
    let isActive = false;
    for (let i = 0; i < 5; i++) {
        if (parent && parent.className && parent.className.includes('active')) {
            isActive = true;
            break;
        }
        parent = parent.parentElement;
    }
    isActive ? '✅ 已开启成功' : '❌ 开启失败';
"""}}
```

---

### 智谱 - 思考

**Step A: 用 XPath 找到按钮**
```python
cmd = {"id": 1, "method": "Runtime.evaluate", "params": {"expression": """
    const result = document.evaluate(
        '//*[contains(text(), "思考")]',
        document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
    );
    const btn = result.singleNodeValue;
    btn ? '找到按钮' : '未找到';
"""}}
```

**Step B: 检查当前状态**
```python
cmd = {"id": 1, "method": "Runtime.evaluate", "params": {"expression": """
    const result = document.evaluate(
        '//*[contains(text(), "思考")]',
        document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
    );
    const btn = result.singleNodeValue;
    let parent = btn.parentElement;
    let isActive = false;
    for (let i = 0; i < 5; i++) {
        if (parent && parent.className && parent.className.includes('active')) {
            isActive = true;
            break;
        }
        parent = parent.parentElement;
    }
    isActive ? '已开启' : '已关闭';
"""}}
```

**Step C: 只在关闭状态时才点击**
```python
cmd = {"id": 1, "method": "Runtime.evaluate", "params": {"expression": """
    const result = document.evaluate(
        '//*[contains(text(), "思考")]',
        document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
    );
    const btn = result.singleNodeValue;
    let parent = btn.parentElement;
    let isActive = false;
    for (let i = 0; i < 5; i++) {
        if (parent && parent.className && parent.className.includes('active')) {
            isActive = true;
            break;
        }
        parent = parent.parentElement;
    }
    if (!isActive) {
        btn.click();
        '已点击开启';
    } else {
        '无需点击，已开启';
    }
"""}}
```

**Step D: 验证结果**
```python
cmd = {"id": 1, "method": "Runtime.evaluate", "params": {"expression": """
    const start = Date.now();
    while (Date.now() - start < 1000) {}
    
    const result = document.evaluate(
        '//*[contains(text(), "思考")]',
        document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
    );
    const btn = result.singleNodeValue;
    let parent = btn.parentElement;
    let isActive = false;
    for (let i = 0; i < 5; i++) {
        if (parent && parent.className && parent.className.includes('active')) {
            isActive = true;
            break;
        }
        parent = parent.parentElement;
    }
    isActive ? '✅ 已开启成功' : '❌ 开启失败';
"""}}
```

---

### 智谱 - 联网

**Step A: 用 XPath 找到按钮**
```python
cmd = {"id": 1, "method": "Runtime.evaluate", "params": {"expression": """
    const result = document.evaluate(
        '//*[contains(text(), "联网")]',
        document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
    );
    const btn = result.singleNodeValue;
    btn ? '找到按钮' : '未找到';
"""}}
```

**Step B: 检查当前状态**
```python
cmd = {"id": 1, "method": "Runtime.evaluate", "params": {"expression": """
    const result = document.evaluate(
        '//*[contains(text(), "联网")]',
        document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
    );
    const btn = result.singleNodeValue;
    let parent = btn.parentElement;
    let isActive = false;
    for (let i = 0; i < 5; i++) {
        if (parent && parent.className && parent.className.includes('active')) {
            isActive = true;
            break;
        }
        parent = parent.parentElement;
    }
    isActive ? '已开启' : '已关闭';
"""}}
```

**Step C: 只在关闭状态时才点击**
```python
cmd = {"id": 1, "method": "Runtime.evaluate", "params": {"expression": """
    const result = document.evaluate(
        '//*[contains(text(), "联网")]',
        document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
    );
    const btn = result.singleNodeValue;
    let parent = btn.parentElement;
    let isActive = false;
    for (let i = 0; i < 5; i++) {
        if (parent && parent.className && parent.className.includes('active')) {
            isActive = true;
            break;
        }
        parent = parent.parentElement;
    }
    if (!isActive) {
        btn.click();
        '已点击开启';
    } else {
        '无需点击，已开启';
    }
"""}}
```

**Step D: 验证结果**
```python
cmd = {"id": 1, "method": "Runtime.evaluate", "params": {"expression": """
    const start = Date.now();
    while (Date.now() - start < 1000) {}
    
    const result = document.evaluate(
        '//*[contains(text(), "联网")]',
        document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
    );
    const btn = result.singleNodeValue;
    let parent = btn.parentElement;
    let isActive = false;
    for (let i = 0; i < 5; i++) {
        if (parent && parent.className && parent.className.includes('active')) {
            isActive = true;
            break;
        }
        parent = parent.parentElement;
    }
    isActive ? '✅ 已开启成功' : '❌ 开启失败';
"""}}
```

---

### 豆包 - 快速 → 专家

**Step A: 点击"快速"按钮**
```python
cmd = {"id": 1, "method": "Runtime.evaluate", "params": {"expression": """
    const fastBtn = document.evaluate(
        '//*[contains(text(), "快速")]',
        document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
    ).singleNodeValue;
    fastBtn.click();
    '已点击快速';
"""}}
```

**Step B: 等待菜单出现**
```python
cmd = {"id": 1, "method": "Runtime.evaluate", "params": {"expression": """
    const start = Date.now();
    while (Date.now() - start < 500) {}
    '已等待500ms';
"""}}
```

**Step C: 点击"专家"**
```python
cmd = {"id": 1, "method": "Runtime.evaluate", "params": {"expression": """
    const proBtn = document.evaluate(
        '//*[contains(text(), "专家")]',
        document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
    ).singleNodeValue;
    proBtn.click();
    '已点击专家';
"""}}
```

**Step D: 验证结果**
```python
cmd = {"id": 1, "method": "Runtime.evaluate", "params": {"expression": """
    const start = Date.now();
    while (Date.now() - start < 1000) {}
    
    const current = document.evaluate(
        '//*[contains(text(), "快速")] | //*[contains(text(), "专家")]',
        document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
    ).singleNodeValue.textContent.trim();
    
    current === '专家' ? '✅ 已切换成功' : '❌ 切换失败';
"""}}
```

---

### Kimi - K2.5思考

**Step A: 用 XPath 找到按钮**
```python
cmd = {"id": 1, "method": "Runtime.evaluate", "params": {"expression": """
    const result = document.evaluate(
        '//*[contains(text(), "K2.5")]',
        document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
    );
    const btn = result.singleNodeValue;
    btn ? '找到按钮' : '未找到';
"""}}
```

**Step B: 检查当前状态**
```python
cmd = {"id": 1, "method": "Runtime.evaluate", "params": {"expression": """
    const result = document.evaluate(
        '//*[contains(text(), "K2.5")]',
        document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
    );
    const btn = result.singleNodeValue;
    let parent = btn.parentElement;
    let isActive = false;
    for (let i = 0; i < 5; i++) {
        if (parent && parent.className && parent.className.includes('active')) {
            isActive = true;
            break;
        }
        parent = parent.parentElement;
    }
    isActive ? '已开启' : '已关闭';
"""}}
```

**Step C: 只在关闭状态时才点击**
```python
cmd = {"id": 1, "method": "Runtime.evaluate", "params": {"expression": """
    const result = document.evaluate(
        '//*[contains(text(), "K2.5")]',
        document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
    );
    const btn = result.singleNodeValue;
    let parent = btn.parentElement;
    let isActive = false;
    for (let i = 0; i < 5; i++) {
        if (parent && parent.className && parent.className.includes('active')) {
            isActive = true;
            break;
        }
        parent = parent.parentElement;
    }
    if (!isActive) {
        btn.click();
        '已点击开启';
    } else {
        '无需点击，已开启';
    }
"""}}
```

**Step D: 验证结果**
```python
cmd = {"id": 1, "method": "Runtime.evaluate", "params": {"expression": """
    const start = Date.now();
    while (Date.now() - start < 1000) {}
    
    const result = document.evaluate(
        '//*[contains(text(), "K2.5")]',
        document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
    );
    const btn = result.singleNodeValue;
    let parent = btn.parentElement;
    let isActive = false;
    for (let i = 0; i < 5; i++) {
        if (parent && parent.className && parent.className.includes('active')) {
            isActive = true;
            break;
        }
        parent = parent.parentElement;
    }
    isActive ? '✅ 已开启成功' : '❌ 开启失败';
"""}}
```

---

## 重要原则

1. **严格按照 SOP 执行** - 每一步都不能省略
2. **先检查状态再点击** - 只在关闭状态时才点击
3. **必须验证结果** - 点击后等待1秒重新检查状态
4. **禁止自由发挥** - 按 SOP 写的步骤执行
