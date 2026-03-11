---
name: doubao-chat
description: 豆包网页版 AI 对话助手。通过 Browser Relay 控制豆包标签页进行联网搜索和图片识别。当用户要求使用豆包进行搜索、问答、联网查询、或图片识别时触发此 Skill。
---

# doubao-chat

控制豆包网页版进行 AI 对话和联网搜索。

## 快速使用

当用户要求用豆包搜索或问答时：

```bash
# 1. 检查豆包标签页是否已连接
browser(action=tabs, profile="chrome")

# 2. 如果没有连接，新建豆包窗口
browser(action=open, profile="chrome", url="https://www.doubao.com/chat/")
```

## ⚠️ 重要：输入方法（2026-03-09 更新）

**不要使用 aria-ref 输入方法**，豆包页面使用 React 动态渲染，ref 不稳定。

**必须使用 JavaScript 注入方法**：

```bash
# 3. 聚焦输入框（使用 JavaScript）
browser(action=act, profile="chrome", request={
  "fn": "document.querySelector('div[role=\"textbox\"]')?.focus()",
  "kind": "evaluate"
})

# 4. 输入文字（使用 JavaScript）
browser(action=act, profile="chrome", request={
  "fn": "document.execCommand('insertText', false, '你的问题')",
  "kind": "evaluate"
})

# 5. 发送
browser(action=act, profile="chrome", request={"kind": "press", "key": "Enter"})

# 6. 等待回答（10-15秒）
sleep 15

# 7. 获取回答
browser(action=snapshot, profile="chrome")
```

**为什么不用 aria-ref**：豆包使用 React 动态渲染，aria-ref 每次都变，导致定位失败。

**JavaScript 方法优点**：直接操作 DOM，不依赖 aria-ref，稳定可靠。
```

## 完整工作流程

### 步骤 1：确保豆包已打开并连接

**重要：先确认 Browser Relay 状态！**
1. Browser Relay 插件有没有切换到 On 的状态？
   - 有时候 Chrome 提示"Openclaw Browser Relay 已经开始调试此浏览器"，这不是 On 的状态
2. Chrome 浏览器有没有提示"Openclaw Browser Relay 已经开始调试此浏览器"？

**不要擅自操作，先确认状态！**

```当前连接的标签页bash
# 检查
browser(action=tabs, profile="chrome")
```

```当前连接的标签页bash
# 检查
browser(action=tabs, profile="chrome")
```

如果没有豆包标签页，需要新建：

```bash
# 新建豆包窗口（不会占用当前聊天标签页）
browser(action=open, profile="chrome", url="https://www.doubao.com/chat/")
```

用户需要点击 OpenClaw Browser Relay 扩展图标连接这个标签页。

### 步骤 2：切换到专家模式（推荐）

豆包有三种模式：
- **快速**：适用于简单问题
- **思考**：适用于复杂问题
- **专家**：研究级智能模型，适用于高质量答案

```bash
# 2.1 点击模型选择按钮（"快速"按钮）
browser(action=act, profile="chrome", request={
  "kind": "click",
  "ref": "e347"
})
sleep 1

# 2.2 选择"专家"模式
browser(action=act, profile="chrome", request={
  "kind": "click",
  "ref": "e458"
})
sleep 1
```

### 步骤 3：检查并处理断线/新对话

**断线自动检测逻辑**：
```bash
# 获取页面快照
browser(action=snapshot, profile="chrome")

# 检查是否断线或需要新对话的标志：
# - 页面显示"未连接"或登录状态
# - 输入框 ref=e403 不存在
# - 出现新对话提示
```

**使用 command+K 创建新对话**：
```bash
# 方法1：使用快捷键 command+K（或 Ctrl+K）
browser(action=act, profile="chrome", request={
  "kind": "press",
  "key": "Meta+k"
})

# 方法2：点击新对话按钮
browser(action=act, profile="chrome", request={
  "kind": "click",
  "ref": "e15"
})

# 方法3：刷新页面创建全新会话
browser(action=act, profile="chrome", request={
  "kind": "press",
  "key": "Meta+r"
})
```

### 步骤 4：发送问题

**先检查页面状态**：
```bash
# 确保输入框可用
browser(action=snapshot, profile="chrome")
```

**输入问题**：
```bash
# 输入框 ref=e403
browser(action=act, profile="chrome", request={
  "kind": "type",
  "ref": "e403",
  "text": "问题内容"
})

# 按 Enter 发送
browser(action=act, profile="chrome", request={"kind": "press", "key": "Enter"})
```

### 步骤 5：等待并获取回答

```bash
# 等待豆包生成回答（专家模式较慢，通常 10-20 秒）
sleep 15

# 获取页面内容
browser(action=snapshot, profile="chrome")
```

从返回的 snapshot 中提取 AI 回复内容。

---

## 提问模板（让豆包回答更准确）

### 为什么需要详细提问？

模糊的问题 → 模糊的回答
详细的问题 → 精准的答案

**原始问题**："OpenClaw 发展趋势"
**优化后**："我需要了解 OpenClaw 在中国2026年的发展趋势，包括市场现状、政策支持、主要玩家、挑战和机会。请从技术、商业、生态三个角度分析。"

### 提问公式

```
[背景] + [需求] + [范围] + [角度] + [格式]
```

### 常见场景模板

#### 1. 调研类问题
```
我正在研究 [主题]，需要了解：
- 当前市场现状和主要数据
- 行业趋势和发展方向
- 主要玩家和竞争格局
- 潜在机会和风险
请提供最新信息，并用表格汇总关键数据。
```

#### 2. 技术类问题
```
我需要解决 [具体问题]：
- 技术背景：[使用的技术栈/工具]
- 遇到的问题：[具体错误或需求]
- 尝试过的方法：[已有的解决方案]
请提供具体的解决步骤和代码示例。
```

#### 3. 学习类问题
```
我想学习 [主题]，目标是 [学习目标]：
- 当前基础：[已掌握的知识]
- 学习时间：[每天可用时间]
- 学习方式：[理论为主/实践为主]
请推荐学习路线和资源。
```

#### 4. 商业分析类问题
```
分析 [公司/产品] 在 [市场] 的竞争地位：
- 核心优势和差异化
- 主要竞争对手
- 商业模式和盈利情况
- 未来发展预测
```

#### 5. 生活决策类问题
```
我面临 [决策]，具体情况是：
- 选项A：[优缺点]
- 选项B：[优缺点]
- 我的优先级：[最看重的因素]
请帮我分析并给出建议。
```

### 更多示例见 `prompts.md`

---

## 断线自动恢复流程

```python
# 伪代码逻辑

def send_to_doubao(question):
    # 1. 检查标签页状态
    tabs = browser(action=tabs, profile="chrome")
    
    if not has_doubao_connected(tabs):
        # 2. 打开豆包
        browser(action=open, url="https://www.doubao.com/chat/", profile="chrome")
        wait_for_user_connect()
    
    # 3. 获取页面快照检查状态
    snapshot = browser(action=snapshot, profile="chrome")
    
    if is_disconnected(snapshot) or needs_new_conversation(snapshot):
        # 4. 使用 command+K 创建新对话
        browser(action=act, request={"kind": "press", "key": "Meta+k"}, profile="chrome")
        sleep 2
    
    # 5. 输入问题
    browser(action=act, request={
        "kind": "type",
        "ref": "e403",
        "text": question
    }, profile="chrome")
    
    # 6. 发送
    browser(action=act, request={"kind": "press", "key": "Enter"}, profile="chrome")
    
    # 7. 等待回答
    sleep 10
    
    # 8. 返回结果
    return browser(action=snapshot, profile="chrome")
```

---

## 页面元素参考

| 元素 | ref | 说明 |
|------|-----|------|
| 输入框 | e403 | 豆包主输入框 |
| 发送 | Enter | 按回车键发送 |
| 新对话按钮 | e15 | 开始新对话 |
| 快速模式 | e347 | 快速回答模式 |
| 编程模式 | e360 | 编程专用模式 |

## 多标签页管理

当前可用的标签页：
- **OpenClaw Control**：用于和你聊天
- **豆包**：用于搜索问答

确保操作时使用正确的 `targetId`。

## 注意事项

- ❌ 图片识别暂不实现（页面交互复杂）
- ✅ 联网搜索：豆包会自动联网搜索最新信息
- ⏱️ 回答生成需要 5-15 秒，请耐心等待
- 🔄 如果输入框没有响应，尝试先点击输入框再输入
- ⌨️ 使用 command+K 可以快速创建新对话

---

## 使用示例

### 示例1：调研问题
```
用户：用豆包查一下2026年AI领域的最新进展

→ browser(action=tabs, profile="chrome")
→ browser(action=open, profile="chrome", url="https://www.doubao.com/chat/")

# 检查是否需要新对话
→ browser(action=snapshot, profile="chrome")
# 如果页面显示断线或旧对话，按 command+K

# 输入优化后的问题
→ browser(action=act, profile="chrome", request={
  "kind": "type",
  "ref": "e403",
  "text": "我需要了解2026年AI领域的最新进展，包括：1) 生成式AI的最新突破；2) 大模型发展趋势；3) AI在各行业的应用落地情况；4) 主要玩家动态。请提供最新信息并附带数据来源。"
})

→ browser(action=act, profile="chrome", request={"kind": "press", "key": "Enter"})
→ sleep 12
→ browser(action=snapshot, profile="chrome")
```

### 示例2：断线恢复
```
# 检测到断线
→ browser(action=snapshot, profile="chrome")
# 返回结果显示需要登录或会话过期

# 使用 command+K 创建新对话
→ browser(action=act, profile="chrome", request={
  "kind": "press",
  "key": "Meta+k"
})
sleep 2

# 继续正常流程...
```

---

## 微信公众号文章获取（2026-03-09 新增）

### 问题
微信公众号文章有验证码保护，curl 直接请求会被拦截。

### 成功方法

**方法1：OpenClaw 自带浏览器（推荐）**

```bash
# 打开文章
openclaw browser open "https://mp.weixin.qq.com/s/xxx"

# 获取内容
openclaw browser snapshot --json
```

**方法2：通过豆包发送链接**
- 直接把微信文章链接发给豆包，让豆包读取并总结

### 失败的方法
- curl 直接请求 → 返回"环境异常"验证页面
- jina.ai 等在线服务 → 请求超时

### 关键要点
1. 微信公众号需要登录态，OpenClaw Browser 可以保持登录
2. 不要用 curl/网络请求工具直接抓取
3. 优先使用 OpenClaw 自带浏览器
