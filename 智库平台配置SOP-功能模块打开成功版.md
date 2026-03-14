# 智库平台配置SOP-功能模块打开成功版

## 测试日期：2026-03-14

---

## 一、DeepSeek 配置

### 目标：开启「深度思考」和「智能搜索」

#### 成功方法

```python
import websocket
import json

page_id = "DeepSeek页面ID"
ws = websocket.create_connection(f"ws://127.0.0.1:18800/devtools/page/{page_id}", timeout=10)

# Step A: 找到按钮
cmd = {"method": "Runtime.evaluate", "params": {"expression": """
(function(){
    var all = document.querySelectorAll('*');
    for(var i=0; i<all.length; i++) {
        if(all[i].textContent && all[i].textContent.trim() === '深度思考') {
            return '找到按钮';
        }
    }
    return '未找到';
})();
""", "returnByValue": True}}

# Step B: 检查状态（检查按钮自身的 selected class）
cmd = {"method": "Runtime.evaluate", "params": {"expression": """
(function(){
    var all = document.querySelectorAll('*');
    for(var i=0; i<all.length; i++) {
        if(all[i].textContent && all[i].textContent.trim() === '深度思考') {
            var isActive = all[i].className && all[i].className.indexOf('selected') !== -1;
            return isActive ? '已开启' : '已关闭';
        }
    }
    return '未找到';
})();
""", "returnByValue": True}}

# Step C: 点击开启
cmd = {"method": "Runtime.evaluate", "params": {"expression": """
(function(){
    var all = document.querySelectorAll('*');
    for(var i=0; i<all.length; i++) {
        if(all[i].textContent && all[i].textContent.trim() === '深度思考') {
            var isActive = all[i].className && all[i].className.indexOf('selected') !== -1;
            if(!isActive) {
                all[i].click();
                return '已点击开启';
            }
            return '无需点击';
        }
    }
    return '未找到';
})();
""", "returnByValue": True}}

# Step D: 验证（等待1秒后检查）
cmd = {"method": "Runtime.evaluate", "params": {"expression": """
(function(){
    var start = Date.now();
    while(Date.now() - start < 1000) {}
    
    var all = document.querySelectorAll('*');
    for(var i=0; i<all.length; i++) {
        if(all[i].textContent && all[i].textContent.trim() === '深度思考') {
            var isActive = all[i].className && all[i].className.indexOf('selected') !== -1;
            return isActive ? '✅ 已开启成功' : '❌ 开启失败';
        }
    }
    return '未找到';
})();
""", "returnByValue": True}}
```

#### 关键点
- 选择器：用 `querySelectorAll('*')` 遍历所有元素
- 文本匹配：用 `textContent.trim() === '深度思考'`
- 状态判断：检查按钮自身的 class 是否包含 `selected`
- 智能搜索同理，把文本改成 `智能搜索` 即可

---

## 二、智谱配置

### 目标：开启「思考」和「联网」

#### 成功方法

与 DeepSeek 相同的方法：
```javascript
// 检查按钮自身的 class 是否包含 selected
var isActive = target.className && target.className.indexOf('selected') !== -1;
```

#### 关键点
- 选择器：`textContent.trim() === '思考'`
- 选择器：`textContent.trim() === '联网'`
- 状态判断：检查按钮自身的 `selected` class

---

## 三、豆包配置

### 目标：从「快速」切换到「专家」

#### 成功方法

```python
import websocket
import json
import time

page_id = "豆包页面ID"
ws = websocket.create_connection(f"ws://127.0.0.1:18800/devtools/page/{page_id}", timeout=10)

# Step A: 找到按钮 ID（按钮 ID 可能变化，如 radix-:rm: 或 radix-:rp:）
cmd = {"method": "Runtime.evaluate", "params": {"expression": """
(function(){
    var es = document.querySelectorAll('button,div');
    for(var i=0; i<es.length; i++) {
        if(es[i].textContent && es[i].textContent.trim() === '快速') {
            return 'id:' + es[i].id;
        }
    }
    return 'not found';
})();
""", "returnByValue": True}}

# Step B: 打开菜单（必须用空格键）
cmd = {"method": "Runtime.evaluate", "params": {"expression": """
(function(){
    var btn = document.getElementById('radix-:rm:');
    if(btn) {
        btn.focus();
        var event = new KeyboardEvent('keydown', {
            key: ' ',
            code: 'Space',
            bubbles: true
        });
        btn.dispatchEvent(event);
        return '已打开菜单';
    }
    return '未找到';
})();
""", "returnByValue": True}}

# Step C: 等待菜单展开
time.sleep(1)

# Step D: 点击"专家"选项
cmd = {"method": "Runtime.evaluate", "params": {"expression": """
(function(){
    var all = document.getElementsByTagName('*');
    for(var i=0; i<all.length; i++) {
        if(all[i].textContent.trim() === '专家') {
            all[i].click();
            return '已点击专家';
        }
    }
    return '未找到';
})();
""", "returnByValue": True}}

# Step E: 验证
time.sleep(1)
cmd = {"method": "Runtime.evaluate", "params": {"expression": """
(function(){
    var btn = document.getElementById('radix-:rm:');
    if(btn) {
        var text = btn.textContent.trim();
        return text.startsWith('专家') ? '✅ 已切换到专家' : '❌ 当前: ' + text;
    }
    return '❌ 未找到按钮';
})();
""", "returnByValue": True}}
```

#### 关键点
1. **Radix UI 下拉框必须用空格键打开**：不能用 click 事件
2. **按钮 ID 可能变化**：需要先查找当前按钮 ID（可能是 `radix-:rm:` 或 `radix-:rp:` 等）
3. **菜单打开后才能操作**：aria-expanded 变为 true 后才能点击选项
4. **用 textContent 精确匹配**：`=== '专家'` 而非 includes

#### 失败尝试记录
- ❌ btn.click() - 无效
- ❌ MouseEvent 模拟 - 无效
- ❌ Input.dispatchMouseEvent 坐标点击 - 无效
- ❌ ArrowDown + Enter - 无效（菜单未打开）

---

## 四、Kimi 配置

### 目标：从「K2.5 快速」切换到「K2.5 思考」

#### 成功方法

```python
import websocket
import json
import time

page_id = "Kimi页面ID"
ws = websocket.create_connection(f"ws://127.0.0.1:18800/devtools/page/{page_id}", timeout=10)

# Step A: 先导航到对话页面
cmd = {"method": "Page.navigate", "params": {"url": "https://www.kimi.com/?chat_enter_method=new_chat"}}
ws.send(json.dumps(cmd))
time.sleep(4)

# Step B: 点击 "K2.5 快速" 按钮打开菜单
cmd = {"method": "Runtime.evaluate", "params": {"expression": """
(function(){
    var es = document.querySelectorAll('*');
    for(var i=0; i<es.length; i++) {
        if(es[i].textContent === 'K2.5 快速') {
            es[i].click();
            return '已点击K2.5快速';
        }
    }
    return '未找到';
})();
""", "returnByValue": True}}

time.sleep(1)

# Step C: 在菜单中选择 "K2.5 思考"
cmd = {"method": "Runtime.evaluate", "params": {"expression": """
(function(){
    var es = document.querySelectorAll('*');
    for(var i=0; i<es.length; i++) {
        if(es[i].textContent === 'K2.5 思考') {
            es[i].click();
            return '已点击K2.5思考';
        }
    }
    return '未找到';
})();
""", "returnByValue": True}}

time.sleep(1)

# Step D: 验证
cmd = {"method": "Runtime.evaluate", "params": {"expression": """
(function(){
    var t = document.body.innerText;
    var p = t.indexOf('K2.5');
    if(p >= 0) {
        var mode = t.substring(p, p + 20);
        if(mode.includes('思考')) {
            return '✅ 已切换到K2.5思考';
        }
    }
    return '❌ 切换失败';
})();
""", "returnByValue": True}}
```

#### 关键点
1. **必须先导航到对话页面**：用 `?chat_enter_method=new_chat` 参数
2. **按钮是 SPAN 元素**：`<SPAN class="name">K2.5 快速</SPAN>`
3. **需要两步点击**：先点击当前模式打开菜单，再点击目标选项
4. **验证方式**：检查页面文本是否包含 "K2.5 思考"

#### 失败尝试记录
- ❌ 用 querySelector('[class*="model"]') - 无效
- ❌ 页面在官网而非对话页面 - 需要导航
- ❌ 检查父级 active/selected class - 验证方式不对

---

## 五、千问配置

### 目标：保持默认（无需操作）

---

## 六、配置清单汇总

| 平台 | 需要开启 | 选择器 | 状态判断 |
|------|----------|--------|----------|
| DeepSeek | 深度思考 | textContent === '深度思考' | class includes 'selected' |
| DeepSeek | 智能搜索 | textContent === '智能搜索' | class includes 'selected' |
| 智谱 | 思考 | textContent === '思考' | class includes 'selected' |
| 智谱 | 联网 | textContent === '联网' | class includes 'selected' |
| 豆包 | 快速→专家 | getElementById('radix-:rm:') + 空格键 | text.startsWith('专家') |
| Kimi | K2.5思考 | textContent === 'K2.5 快速/思考' | 页面文本检查 |
| 千问 | 保持默认 | - | - |

---

## 七、重要教训

1. **Radix UI 下拉框必须用键盘事件触发**：空格键 `key: ' '`
2. **菜单未打开时所有操作无效**：必须先验证 aria-expanded 为 true
3. **选择器要用精确匹配**：用 `===` 而非 `includes`
4. **状态判断因平台而异**：有的看按钮 class，有的看父级 class，有的看页面文本
5. **页面可能需要导航**：Kimi 需要导航到对话页面才能找到模型选择器
6. **按钮 ID 可能变化**：豆包的 radix ID 可能会变化，需要先查找
