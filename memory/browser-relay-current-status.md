
# Browser Relay 当前状态报告

## 调试时间
2026-03-10

## 当前状态

### 1. Browser Relay 扩展状态
- ✅ Browser Relay 已切换到 On 状态
- ✅ Chrome 提示"Openclaw Browser Relay 已经开始调试此浏览器"
- ✅ 扩展已连接到 Gateway

### 2. CDP 端点测试

#### 测试 2.1: 获取标签页列表
```bash
curl "http://127.0.0.1:18792/json?token=235bf68c2288bfde322b8567509fb0e4d8eb368ec3c70000"
```

**结果**：⚠️ 部分成功
```json
[{
  "id": "B1B8C07160D4FD846671B5D0D8EF4934",
  "type": "page",
  "title": "OpenClaw Control",
  "description": "OpenClaw Control",
  "url": "http://127.0.0.1:18789/chat?session=agent%3Amain%3Amain",
  "webSocketDebuggerUrl": "ws://127.0.0.1:18792/cdp",
  "devtoolsFrontendUrl": "/devtools/inspector.html?ws=127.0.0.1:18792/cdp"
}]
```

**问题**：只返回 1 个标签页，但实际 Chrome 有 2 个标签页：
1. OpenClaw Control
2. 豆包

#### 测试 2.2: 创建新标签页
```bash
curl "http://127.0.0.1:18792/json?token=235bf68c2288bfde322b8567509fb0e4d8eb368ec3c70000" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"id":1,"method":"Target.createTarget","params":{"url":"https://www.baidu.com"}}'
```

**结果**：❌ 返回 "not found"

### 3. 连接状态
```
lsof -i :18792

COMMAND  PID   USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
node    20584  lr    30u  IPv4 0x1c76c1ae38bc10c1  0t0  TCP localhost:18792->localhost:58855 (ESTABLISHED)
Google  25122  lr    41u  IPv4 0x1c76c1ae38bdc619  0t0  TCP localhost:58855->localhost:18792 (ESTABLISHED)
```

## 问题总结

| 功能 | 状态 | 说明 |
|------|------|------|
| 扩展连接 | ✅ 正常 | On 状态，已连接 |
| 获取标签页 | ⚠️ 部分 | 只返回 1 个标签页，遗漏其他标签页 |
| 创建标签页 | ❌ 失败 | 返回 "not found" |
| 读取页面内容 | ❌ 未测试 | - |

## 已验证的事实

1. **Query 参数认证方式有效**：
   - `?token=xxx` 方式可以认证成功
   - Bearer Header 和 Basic 认证返回 401

2. **扩展转发部分工作**：
   - CDP 端点可以访问
   - 但返回的标签页列表不完整

## 可能的根因

1. Browser Relay 扩展只代理了当前活动标签页
2. 扩展的 CDP 转发逻辑可能有 bug
3. 需要检查扩展的日志

## 待排查

- [ ] 为什么只返回 1 个标签页？
- [ ] 为什么创建新标签页返回 "not found"？
- [ ] 扩展的 CDP 转发逻辑是否有问题？
- [ ] 是否需要重新安装或更新扩展？

## 相关文件
- `memory/browser-relay-debug-log.md` - 完整调试记录
- `memory/browser-relay-issue-summary.md` - 问题总结
- `memory/browser-relay-error.md` - 错误记录
