
# Browser Relay 当前问题汇总

## 调试时间
2026-03-10

## 当前状态

### 1. Browser Relay 扩展状态
- ✅ Browser Relay 已切换到 On 状态
- ✅ 扩展已连接到 Gateway

### 2. CDP 端点测试结果

#### 测试1: 获取标签页列表
```bash
curl "http://127.0.0.1:18792/json?token=235bf68c2288bfde322b8567509fb0e4d8eb368ec3c70000"
```
**结果**：⚠️ 只返回 1 个标签页
```json
[{
  "id": "B1B8C07160D4FD846671B5D0D8EF4934",
  "title": "OpenClaw Control",
  "url": "http://127.0.0.1:18789/chat?session=agent%3Amain%3Amain"
}]
```

**实际 Chrome 有 4 个标签页**：
1. OpenClaw Control
2. 豆包
3. Coding Plan
4. 百度一下

#### 测试2: 创建新标签页
```bash
curl "http://127.0.0.1:18792/json?token=xxx" -X POST -d '{"method":"Target.createTarget","params":{"url":"https://www.taobao.com"}}'
```
**结果**：❌ 返回 "not found"

### 3. 扩展 Console 日志

**日志内容**：
```
background.js:1055 [Keepalive] Alarm triggered, SW refreshed
background.js:1028 [Keepalive] WebSocket ping sent
background.js:1055 [Keepalive] Alarm triggered, SW refreshed
... (重复多次)
```

**问题**：只显示 Keepalive 心跳日志，**没有 CDP 请求处理日志**

### 4. 扩展 Network 标签
- ❌ 没有任何请求记录

## 问题分析

1. **标签页列表不完整**：扩展只返回 1 个标签页，可能只代理了活动标签页
2. **创建标签页失败**：返回 "not found"，可能是接口路由错误
3. **没有请求日志**：扩展没有为 CDP 请求输出 Console 日志，也没有 Network 请求记录

## 已验证的事实

1. ✅ Query 参数认证有效：`?token=xxx`
2. ✅ Chrome 原生 CDP (9222) 正常工作
3. ✅ 扩展的 Keepalive 心跳正常工作
4. ❌ 扩展的 CDP 转发不完整

## 待排查

1. 扩展代码中 /json 接口是如何处理的？
2. 扩展代码中 Target.createTarget 是如何处理的？
3. 为什么没有 CDP 请求的日志？

## 代码分析结果（Subagent）

### 关键发现
1. **只查询活动标签页**：`chrome.tabs.query({ active: true, currentWindow: true })`
   - 这就是为什么只返回 1 个标签页的原因！

2. **HTTP /json 未实现**：扩展使用 WebSocket，不支持 HTTP /json API

3. **没有调试日志**：开发者没有添加 CDP 请求的 console.log

## 相关文件
- `/Users/lr/.openclaw/workspace/memory/browser-relay-debug-log.md` - 完整调试记录
- `/Users/lr/.openclaw/workspace/memory/browser-relay-console-log.md` - Console 日志
