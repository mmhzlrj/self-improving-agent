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

# 3. 输入问题（输入框 ref=e403）
browser(action=act, profile="chrome", request={
  "kind": "type",
  "ref": "e403",
  "text": "用户的问题"
})

# 4. 发送（按 Enter）
browser(action=act, profile="chrome", request={"kind": "press", "key": "Enter"})

# 5. 等待回答（5-10秒）
sleep 8

# 6. 获取回答
browser(action=snapshot, profile="chrome")
```

## 完整工作流程

### 步骤 1：确保豆包已打开并连接

```bash
# 检查当前连接的标签页
browser(action=tabs, profile="chrome")
```

如果没有豆包标签页，需要新建：

```bash
# 新建豆包窗口（不会占用当前聊天标签页）
browser(action=open, profile="chrome", url="https://www.doubao.com/chat/")
```

用户需要点击 OpenClaw Browser Relay 扩展图标连接这个标签页。

### 步骤 2：发送问题

```bash
# 获取页面确认元素
browser(action=snapshot, profile="chrome")

# 输入问题（输入框 ref=e403）
browser(action=act, profile="chrome", request={
  "kind": "type",
  "ref": "e403",
  "text": "问题内容"
})

# 按 Enter 发送
browser(action=act, profile="chrome", request={"kind": "press", "key": "Enter"})
```

### 步骤 3：等待并获取回答

```bash
# 等待豆包生成回答（通常 5-10 秒）
sleep 8

# 获取页面内容
browser(action=snapshot, profile="chrome")
```

从返回的 snapshot 中提取 AI 回复内容。

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
- ⏱️ 回答生成需要 5-10 秒，请耐心等待
- 🔄 如果输入框没有响应，尝试先点击输入框再输入

## 常见问题

**Q: 标签页断开了怎么办？**
A: 让用户重新点击 OpenClaw Browser Relay 扩展图标连接

**Q: 输入框没有响应？**
A: 先用 `browser(action=act, request={"kind": "click", "ref": "e403"})` 点击输入框

**Q: 如何开始新对话？**
A: 点击 ref=e15（新对话按钮），或刷新页面

## 使用示例

```
用户：用豆包查一下2026年AI领域的最新进展

# 检查连接
→ browser(action=tabs, profile="chrome")

# 输入问题
→ browser(action=act, profile="chrome", request={
  "kind": "type",
  "ref": "e403",
  "text": "2026年AI领域的最新进展有哪些？"
})

# 发送
→ browser(action=act, profile="chrome", request={"kind": "press", "key": "Enter"})

# 等待回答
→ sleep 10

# 获取结果
→ browser(action=snapshot, profile="chrome")

# 提取回答内容给用户
```
