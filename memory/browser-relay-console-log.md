
# Browser Relay 扩展日志

## 获取时间
2026-03-10

## Console 日志内容

```
background.js:1055 [Keepalive] Alarm triggered, SW refreshed
background.js:1028 [Keepalive] WebSocket ping sent
background.js:1055 [Keepalive] Alarm triggered, SW refreshed
background.js:1028 [Keepalive] WebSocket ping sent
... (重复多次)
```

## 分析

**问题**：日志只显示了 Keepalive 心跳日志，没有显示 CDP 请求处理日志

**可能原因**：
1. 扩展没有为 CDP 请求输出 Console 日志
2. 日志被过滤了
3. 需要开启更详细的日志级别

## 豆包建议的下一步

根据豆包的排查计划，需要：
1. 检查是否有其他日志来源（如 Network 标签）
2. 检查扩展代码中是否有 Console.log 输出
3. 可能需要在扩展代码中添加调试日志

## 待确认
- 是否有 Network 标签的请求日志？
- 扩展代码中是否有处理 /json 和 Target.createTarget 的日志输出？
