
# 阶段1验证 - 下一步计划（豆包提供）

## 时间
2026-03-10 20:38

## 核心问题

1. 直接连接 CDP WebSocket 端点返回 403
2. 通过 Gateway WebSocket 发送命令无响应
3. 可能原因：命令格式错误、缺失 sessionId、Gateway 转发异常

---

## 下一步计划

### 步骤1：收集日志
- 提取 Gateway 服务日志
- 提取浏览器扩展日志

### 步骤2：验证 CDP.forward 命令格式
- 参考 CDP 官方文档确认标准参数结构
- 重构标准化命令

### 步骤3：补充 sessionId 专项测试
- 先获取有效 sessionId
- 多场景测试

### 步骤4：验证 Gateway 转发逻辑
- 抓包验证
- 绕过 Gateway 测试

### 步骤5：对照组测试
- 确认是 CDP.forward 特有还是整体异常

---

## 相关文件
- `/Users/lr/.openclaw/workspace/memory/browser-relay-stage1-test.md`
