
# Browser Relay 问题分析 - Target.createTarget

## 时间
2026-03-10

## 测试

### HTTP POST 测试
```bash
curl "http://127.0.0.1:18792/json?token=xxx" -X POST -d '{"method":"Target.createTarget","params":{"url":"https://www.baidu.com"}}'
```
**结果**：404 Not Found

### 分析
通过检查 Gateway 源码，发现：
- Gateway 只处理 `/json/activate/` 和 `/json/close/`
- **没有处理 `/json/new` 或 POST 到 `/json`**

扩展使用 **WebSocket** 与 Gateway 通信，而不是 HTTP API。

## 问题
Browser Relay 的 HTTP /json 接口**不完整**：
- GET `/json` 可以获取标签页列表
- POST `/json` 创建标签页返回 404

## 待确认
- 扩展是否需要通过 WebSocket 发送 CDP 命令？
- Gateway 的 WebSocket 端点是否正确转发 CDP 命令？

## 待测试
- 通过 WebSocket 发送 Target.createTarget 命令
