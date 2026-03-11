
# Browser Relay 问题总结

## 问题描述
通过 Browser Relay 无法控制用户的 Chrome 浏览器。

## 当前状态

### 1. 扩展状态
- ✅ Browser Relay 插件已切换到 On 状态
- ✅ Chrome 提示"Openclaw Browser Relay 已经开始调试此浏览器"
- ✅ Chrome 已连接到 Gateway (端口 18792)

### 2. 连接状态
- Chrome (PID 6231) → 18792: ESTABLISHED ✅
- Gateway (PID 20584) → 18792: ESTABLISHED ✅

### 3. CDP 端点测试
- `curl http://127.0.0.1:18792/json` → 返回 "Unauthorized" ❌
- 认证后 WebSocket 无响应 ❌

## 测试过的方法

1. ❌ 直接访问 CDP (curl 18792/json) - 返回 401
2. ❌ Gateway WebSocket /extension 认证 - 认证成功但无响应
3. ❌ osascript + JavaScript - 需要开启 AppleScript JavaScript 功能

## 需要排查的方向

1. Browser Relay 扩展的 CDP 代理功能是否正常工作？
2. CDP 认证机制是否正确？
3. Gateway 的 /extension 端点认证是否有问题？

## 环境信息
- Chrome: 带插件的版本 (PID 6231)
- Gateway: 18789
- Browser Relay CDP: 18792
- Token: 235bf68c2288bfde322b8567509fb0e4d8eb368ec3c70000
