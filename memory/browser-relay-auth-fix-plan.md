
# Browser Relay /extension 认证问题修复 Plan

## 问题描述

- Gateway 的 `/extension` WebSocket 端点认证失败
- 日志显示："invalid request frame"
- 扩展显示"已开始调试"，但实际连接有问题

## 调试步骤

### 步骤1：理解认证机制
1. 查看 Gateway 源码中 /extension 端点的实现
2. 理解正确的认证格式
3. 对比当前发送的认证格式

### 步骤2：修复认证
1. 根据源码修复认证格式
2. 或者配置 Gateway 开启/关闭某些认证选项

### 步骤3：验证
1. 重新连接扩展
2. 测试创建标签页功能

---

## 待确认

1. 是否继续排查 Gateway 源码？
2. 还是临时用其他方案（osascript）先实现读取网页内容？
