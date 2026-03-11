# OpenClaw Browser Relay 配置指南

本文档详细记录 OpenClaw Browser Relay 的配置方法。

## 概述

Browser Relay 让你通过 Chrome 扩展控制你的浏览器标签页，让我能读取网页内容、操作浏览器等。

## 关键配置信息

### 端口

| 服务 | 端口 | 说明 |
|------|------|------|
| Gateway HTTP | 18789 | OpenClaw 控制面板 |
| Browser Relay CDP | 18792 | Chrome 调试端口（需要认证） |

### Gateway Token

```
235bf68c2288bfde322b8567509fb0e4d8eb368ec3c70000
```

**位置**：`~/.openclaw/openclaw.json` 中的 `auth.profiles[0].token`

## 配置步骤

### 0. 检查 Browser Relay 状态（重要！）
每次使用前必须确认：
1. Browser Relay 插件有没有切换到 On 的状态？
   - 有时候 Chrome 提示"Openclaw Browser Relay 已经开始调试此浏览器"，这不是 On 的状态
2. Chrome 浏览器有没有提示"Openclaw Browser Relay 已经开始调试此浏览器"？

### 1. 操作用户的 Chrome（重要！）

**不要用 openclaw browser 命令！**

1. 先找到用户正在运行的 Chrome PID：
```bash
ps aux | grep "Google Chrome" | grep -v grep
```

2. 使用 osascript 操作用户当前已打开的 Chrome：
```bash
osascript -e 'tell application "Google Chrome" to open location "https://..."'
```

### 2. Chrome 启动参数（开启调试端口）

```bash
open -a "Google Chrome" --args --remote-debugging-port=18792
```

或者在 Chrome 启动后通过命令添加端口：
```bash
# 检查 Chrome 进程并添加端口（需要重启）
```

### 2. 配置扩展

1. 打开 Chrome → 右上角点击扩展图标
2. 右键 Openclaw Browser Relay → 选项 / Options
3. 填写配置：
   - **Gateway URL**: `http://127.0.0.1:18789`
   - **Gateway Token**: `235bf68c2288bfde322b8567509fb0e4d8eb368ec3c70000`
   - **Relay Port**: `18792`
4. 保存并刷新扩展

### 3. 连接测试

1. 点击扩展图标 → 应该显示 "Connected" 或绿色状态
2. 验证 CDP 可访问：
```bash
curl -s http://127.0.0.1:18792/json
```

## 故障排查

### 问题：/json 返回 Unauthorized

**原因**：Token 无效或过期

**解决**：
1. 打开扩展设置
2. 确认 Gateway Token 正确（见上文）
3. 重新保存配置
4. 刷新扩展

### 问题：连接断开频繁

**原因**：MV3 Service Worker 30秒休眠

**解决**：
- 参考 `browser-relay-keepalive.md` 添加 keepalive 代码

## 验证连接

```bash
# 检查端口监听
lsof -i :18792

# 测试 HTTP 端点
curl -s http://127.0.0.1:18792/json

# 测试 Gateway
curl -s http://127.0.0.1:18789/
```

## 文件位置

- 扩展目录：`~/.openclaw/browser/chrome-extension/`
- 扩展配置：`~/.openclaw/browser/chrome-extension/background.js`
- Gateway 配置：`~/.openclaw/openclaw.json`
- 日志：`/tmp/openclaw/openclaw-YYYY-MM-DD.log`

## 更新日志

- 2026-03-10：初始版本，记录完整配置流程和 Gateway Token
