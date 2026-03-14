# 智库平台问答测试SOP - 问题同步与回复回收

## 测试日期：2026-03-14

## 测试目标
将问题同步到多个AI网页平台（DeepSeek、智谱、千问、豆包、Kimi），获取AI回复后保存为MD文档，并总结方案输出到OpenClaw聊天页面。

---

## 一、平台配置检查

### 1.1 DeepSeek 配置检查
- **深度思考**：已开启
- **智能搜索**：已开启

### 1.2 智谱配置检查
- **思考**：已开启
- **联网**：已开启

### 1.3 千问配置检查
- **默认配置**：保持不变

### 1.4 豆包配置检查
- **专家模式**：已开启

### 1.5 Kimi 配置检查
- **K2.5思考**：已开启

---

## 二、问题同步到各平台

### 测试问题
```
请用一句话解释什么是人工智能？
```

### 2.1 DeepSeek 操作流程

#### Step A: 找到聊天输入框
```python
import websocket
import json

page_id = "DeepSeek页面ID"
ws = websocket.create_connection(f"ws://127.0.0.1:18800/devtools/page/{page_id}", timeout=10)

# 找到聊天输入框
cmd = {"method": "Runtime.evaluate", "params": {"expression": """
(function(){
    // 尝试多种可能的输入框选择器
    var selectors = [
        'textarea[placeholder*="输入"]',
        'textarea[placeholder*="essage"]',
        'div[contenteditable="true"]',
        'input[type="text"]'
    ];
    
    for(var s=0; s<selectors.length; s++) {
        var el = document.querySelector(selectors[s]);
        if(el) {
            return '找到输入框: ' + selectors[s];
        }
    }
    
    // 备选：遍历所有 textarea
    var allTextarea = document.querySelectorAll('textarea');
    for(var i=0; i<allTextarea.length; i++) {
        if(allTextarea[i].clientWidth > 100) {
            return '找到输入框 (备选): textarea #' + i;
        }
    }
    
    return '未找到输入框';
})();
""", "returnByValue": True}}

ws.send(json.dumps(cmd))
result = json.loads(ws.recv())
print(result['result']['result']['value'])
ws.close()
```

#### Step B: 输入问题
```python
# 输入问题
cmd = {"method": "Runtime.evaluate", "params": {"expression": """
(function(){
    var textarea = document.querySelector('textarea');
    if(textarea) {
        textarea.value = '请用一句话解释什么是人工智能？';
        textarea.dispatchEvent(new Event('input', {bubbles: true}));
        textarea.dispatchEvent(new Event('change', {bubbles: true}));
        return '问题已输入';
    }
    return '未找到输入框';
})();
""", "returnByValue": True}}
```

#### Step C: 找到发送按钮
```python
# 找到发送按钮
cmd = {"method": "Runtime.evaluate", "params": {"expression": """
(function(){
    // 查找包含"发送"或"Submit"或"→"的按钮
    var all = document.querySelectorAll('*');
    for(var i=0; i<all.length; i++) {
        var text = all[i].textContent.trim();
        if(text === '发送' || text === 'Send' || text === '→') {
            var rect = all[i].getBoundingClientRect();
            if(rect.width > 0 && rect.height > 0) {
                return '找到发送按钮, 位置: (' + rect.x + ', ' + rect.y + ')';
            }
        }
    }
    
    // 备选：找带箭头的按钮
    var buttons = document.querySelectorAll('button, div[role="button"]');
    for(var i=0; i<buttons.length; i++) {
        var svg = buttons[i].querySelector('svg');
        if(svg && buttons[i].clientWidth > 0) {
            var rect = buttons[i].getBoundingClientRect();
            return '找到发送按钮(备选), 位置: (' + rect.x + ', ' + rect.y + ')';
        }
    }
    
    return '未找到发送按钮';
})();
""", "returnByValue": True}}
```

#### Step D: 点击发送
```python
# 点击发送按钮
cmd = {"method": "Runtime.evaluate", "params": {"expression": """
(function(){
    var all = document.querySelectorAll('*');
    for(var i=0; i<all.length; i++) {
        var text = all[i].textContent.trim();
        if(text === '发送' || text === 'Send' || text === '→') {
            var rect = all[i].getBoundingClientRect();
            if(rect.width > 0 && rect.height > 0) {
                all[i].click();
                return '已点击发送';
            }
        }
    }
    return '未找到发送按钮';
})();
""", "returnByValue": True}}
```

---

## 三、监控AI回复状态

### 3.1 检查是否正在生成

#### Step A: 检查生成状态
```python
# 检查是否有加载动画或生成中的标志
cmd = {"method": "Runtime.evaluate", "params": {"expression": """
(function(){
    // 检查是否有"思考中"、"生成中"、"loading"等元素
    var all = document.querySelectorAll('*');
    for(var i=0; i<all.length; i++) {
        var text = all[i].textContent.trim();
        if(text.indexOf('思考中') !== -1 || 
           text.indexOf('生成中') !== -1 || 
           text.indexOf('loading') !== -1 ||
           text.indexOf('Loading') !== -1) {
            return '正在生成中...';
        }
    }
    
    // 检查发送按钮是否禁用
    var buttons = document.querySelectorAll('button');
    for(var i=0; i<buttons.length; i++) {
        if(buttons[i].disabled || buttons[i].getAttribute('disabled') !== null) {
            return '等待生成完成...';
        }
    }
    
    return '生成完成';
})();
""", "returnByValue": True}}
```

#### Step B: 轮询等待生成完成
```python
# 每3秒检查一次，最多等待60秒
import time

max_wait = 60
interval = 3
elapsed = 0

while elapsed < max_wait:
    cmd = {"method": "Runtime.evaluate", "params": {"expression": """
    (function(){
        var all = document.querySelectorAll('*');
        for(var i=0; i<all.length; i++) {
            var text = all[i].textContent.trim();
            if(text.indexOf('思考中') !== -1 || 
               text.indexOf('生成中') !== -1 || 
               text.indexOf('loading') !== -1) {
                return '生成中';
            }
        }
        
        // 检查发送按钮
        var buttons = document.querySelectorAll('button');
        for(var i=0; i<buttons.length; i++) {
            if(buttons[i].disabled) {
                return '生成中';
            }
        }
        
        return '完成';
    })();
    """, "returnByValue": True}}
    
    ws.send(json.dumps(cmd))
    result = json.loads(ws.recv())
    status = result['result']['result']['value']
    
    if status == '完成':
        print('✅ AI回复生成完成')
        break
    
    print(f'等待生成中... ({elapsed}s)')
    time.sleep(interval)
    elapsed += interval
```

---

## 四、获取回复内容

### 4.1 提取AI回复

#### Step A: 找到回复容器
```python
# 获取AI回复内容
cmd = {"method": "Runtime.evaluate", "params": {"expression": """
(function(){
    // 尝试多种选择器获取回复内容
    var selectors = [
        'div[class*="message"]',
        'div[class*="response"]',
        'div[class*="answer"]',
        'div[class*="content"]'
    ];
    
    for(var s=0; s<selectors.length; s++) {
        var els = document.querySelectorAll(selectors[s]);
        for(var i=0; i<els.length; i++) {
            var text = els[i].textContent.trim();
            if(text.length > 10) {
                return '回复内容: ' + text.substring(0, 500);
            }
        }
    }
    
    return '未找到回复内容';
})();
""", "returnByValue": True}}
```

---

## 五、保存回复到MD文件

### 5.1 文件保存路径
- **保存目录**：`~/.openclaw/workspace/ai-responses/`
- **文件命名**：`{平台名}_{时间戳}.md`

### 5.2 保存格式
```markdown
# {平台名} AI回复

## 原始问题
请用一句话解释什么是人工智能？

## 回复时间
2026-03-14 12:10:00

## 回复内容
[AI回复的完整内容]

## 平台信息
- 平台：DeepSeek
- 模型：DeepSeek-Chat
- 配置：深度思考 + 智能搜索
```

---

## 六、汇总输出到OpenClaw

### 6.1 读取所有回复文件
```python
import os
import glob

response_dir = '~/.openclaw/workspace/ai-responses/'
files = glob.glob(os.path.join(response_dir, '*.md'))

responses = []
for f in sorted(files):
    with open(f, 'r') as fp:
        responses.append(fp.read())
```

### 6.2 生成汇总报告
```markdown
# AI问答汇总报告

## 问题
请用一句话解释什么是人工智能？

## 各平台回复

### DeepSeek
[回复内容]

### 智谱
[回复内容]

### 千问
[回复内容]

### 豆包
[回复内容]

### Kimi
[回复内容]

## 综合分析
[根据各平台回复，总结出详细方案]
```

---

## 七、完整测试流程

### 7.1 测试清单
| 步骤 | 操作 | 状态 |
|------|------|------|
| 1 | 检查各平台配置 | ⬜ |
| 2 | 打开各平台网页 | ⬜ |
| 3 | 输入测试问题 | ⬜ |
| 4 | 点击发送 | ⬜ |
| 5 | 等待回复完成 | ⬜ |
| 6 | 保存回复到MD | ⬜ |
| 7 | 汇总输出到OpenClaw | ⬜ |

### 7.2 预期结果
- 各平台能正常发送问题
- 各平台能正常接收AI回复
- 回复内容正确保存到MD文件
- 汇总报告能展示所有回复
