# OpenClaw 关键配置文档

本文档记录 OpenClaw 系统的重要配置信息，用于快速查阅。

## 端口配置

| 服务 | 端口 | 说明 |
|------|------|------|
| Gateway HTTP | 18789 | OpenClaw 控制面板 |
| Browser Relay CDP | 18792 | Chrome 调试端口（需要认证） |

## 地址

| 服务 | 地址 |
|------|------|
| Gateway | http://127.0.0.1:18789 |
| Control UI | http://127.0.0.1:18789/chat?session=agent%3Amain%3Amain |
| Browser Relay | http://127.0.0.1:18792/ |

## Chrome 调试端口启动命令

```bash
# 方式1：通过启动参数
open -a "Google Chrome" --args --remote-debugging-port=18792

# 方式2：检查现有端口
lsof -i :18792
curl http://127.0.0.1:18792/json
```

## 关键文件路径

- 扩展目录：`~/.openclaw/browser/chrome-extension/`
- 配置文件：`~/.openclaw/openclaw.json`
- 日志文件：`/tmp/openclaw/openclaw-YYYY-MM-DD.log`

## 更新日志

- 2026-03-10：初始版本，记录端口 18789 (Gateway) 和 18792 (Browser)
 Relay CDP