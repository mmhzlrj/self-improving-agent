---
name: agent-reach
description: 给 AI Agent 装上互联网能力 - 读取 Twitter、YouTube、B站、小红书、GitHub、Reddit 等
---

# Agent Reach Skill

让 AI Agent 可以读取和搜索各大平台。

## 已安装 ✅

- Python 3.11 + agent-reach
- gh CLI (GitHub)
- mcporter + Exa (全网搜索)

## 当前可用功能

| 状态 | 平台/功能 |
|------|----------|
| ✅ | YouTube 视频和字幕 |
| ✅ | RSS/Atom 订阅源 |
| ✅ | 任意网页（Jina Reader） |
| ✅ | 全网搜索（Exa） |
| ⚠️ | Twitter/X（需要 Cookie 配置） |
| ⚠️ | GitHub（需要 gh auth login） |
| ⚠️ | B站（本地可用，服务器需代理） |
| ⚠️ | 小红书（需要 Docker + MCP） |
| ⚠️ | 抖音（需要 Python 3.12） |
| ⚠️ | LinkedIn（需要 MCP 服务） |
| ⚠️ | Boss直聘（需要 MCP 服务） |

## 当前状态

```
mcporter 0.7.3 — Listing 4 server(s)
- exa (online ✅)
- xiaohongshu (offline - 需要 Docker)
- douyin (offline - 需要 Python 3.12)
- linkedin (offline - 需要 MCP 服务)
```

## 使用方式

### 读取任意网页
```bash
curl -s https://r.jina.ai/<URL>
```

### YouTube/B站 字幕
```bash
/Library/Frameworks/Python.framework/Versions/3.11/bin/yt-dlp --write-sub --skip-download "<视频URL>"
```

### 全网搜索（Exa）
```bash
mcporter call 'exa.search(query: "关键词", num_results: 5)'
```

## 待完成

1. **安装 Docker Desktop** - 需要手动安装
2. **运行 gh auth login** - 授权 GitHub
3. **配置 Twitter Cookie** - 可选

## 快捷命令

- `agent-reach` → `/Library/Frameworks/Python.framework/Versions/3.11/bin/agent-reach`
- `yt-dlp` → `/Library/Frameworks/Python.framework/Versions/3.11/bin/yt-dlp`
- `mcporter` → `/Users/lr/.nvm/versions/node/v22.22.0/bin/mcporter`

## 官方文档

- GitHub: https://github.com/Panniantong/agent-reach
