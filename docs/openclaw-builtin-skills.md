# OpenClaw 内置 Skills / Agents 完整列表

> 版本：2026.3.24 | 更新时间：2026-03-29
> 路径：`~/.nvm/versions/node/v22.22.0/lib/node_modules/openclaw/skills/`
> 注：以下为当前版本内置的 Skills，新版本可能已有更新

---

## 🤖 Coding / ACP Agents（编码代理）

| Skill | 说明 |
|-------|------|
| **coding-agent** | 委托编码任务给 Codex、Claude Code 或 Pi agents。构建新功能、审查 PR、重构代码、迭代开发 |
| **gh-issues** | 自动修复 GitHub issues：抓取 issue → subagent 实现 → 开 PR → 监控 review |

## 💬 通讯 / 社交平台

| Skill | 说明 |
|-------|------|
| **discord** | Discord 消息操作 |
| **slack** | Slack 消息、表情、置顶 |
| **bluebubbles** | iMessage 收发（通过 BlueBubbles） |
| **imsg** | iMessage/SMS 本地 CLI |
| **wacli** | WhatsApp 消息发送和聊天记录搜索 |
| **xurl** | X (Twitter) API 完整操作（发推、回复、搜索、DM、媒体上传） |

## 📝 笔记 / 知识管理

| Skill | 说明 |
|-------|------|
| **apple-notes** | Apple Notes 管理（创建、搜索、编辑、删除） |
| **apple-reminders** | Apple Reminders 管理（列表、添加、完成、删除） |
| **bear-notes** | Bear 笔记管理 |
| **obsidian** | Obsidian Vault 操作（Markdown 笔记自动化） |
| **notion** | Notion API（页面、数据库、blocks） |
| **trello** | Trello 看板管理（boards、lists、cards） |

## 📧 邮件 / 日历

| Skill | 说明 |
|-------|------|
| **himalaya** | IMAP/SMTP 邮件 CLI（列表、读取、回复、搜索） |
| **gog** | Google Workspace CLI（Gmail、Calendar、Drive、Contacts、Sheets、Docs） |

## 🔐 密码 / 安全

| Skill | 说明 |
|-------|------|
| **1password** | 1Password CLI 集成（读取、注入、运行密钥） |
| **healthcheck** | 主机安全加固和风险配置（防火墙、SSH、更新、漏洞检查） |

## 🎤 语音 / 音频

| Skill | 说明 |
|-------|------|
| **sag** | ElevenLabs TTS（文本转语音） |
| **sherpa-onnx-tts** | 本地离线 TTS（sherpa-onnx，无需云端） |
| **openai-whisper** | 本地语音转文字（Whisper CLI） |
| **openai-whisper-api** | OpenAI Whisper API 语音转文字 |
| **songsee** | 音频频谱图和特征可视化 |
| **voice-call** | 语音通话 |

## 📷 图片 / 视频 / 摄像头

| Skill | 说明 |
|-------|------|
| **image** (内置工具) | 图片分析（多 provider 支持） |
| **video-frames** | ffmpeg 提取视频帧或短视频 |
| **camsnap** | RTSP/ONVIF 摄像头抓帧或录像 |
| **gifgrep** | GIF 搜索、下载、提取静态帧 |
| **nano-pdf** | 自然语言编辑 PDF |
| **peekaboo** | macOS UI 截屏和自动化 |

## 🏠 智能家居 / IoT

| Skill | 说明 |
|-------|------|
| **openhue** | Philips Hue 灯光和场景控制 |
| **eightctl** | Eight Sleep 床垫控制（温度、闹钟、日程） |
| **blucli** | BluOS 音箱控制（播放、分组、音量） |
| **sonoscli** | Sonos 音箱控制 |

## 🎵 音乐

| Skill | 说明 |
|-------|------|
| **spotify-player** | Spotify 播放和搜索 |
| **songsee** | 音频可视化 |

## 🔧 开发工具

| Skill | 说明 |
|-------|------|
| **github** | GitHub CLI 操作（issues、PRs、CI、code review） |
| **gemini** | Gemini CLI 一次性问答 |
| **node-connect** | Node 连接和配对故障诊断 |
| **mcporter** | MCP Server 工具调用（HTTP 或 stdio） |
| **oracle** | Oracle CLI 最佳实践（prompt、session、文件附件） |
| **tmux** | tmux 会话远程控制（发送按键、读取输出） |
| **model-usage** | CodexBar 本地成本/用量统计 |
| **session-logs** | 搜索和分析历史会话日志 |
| **skill-creator** | 创建、编辑、审查 AgentSkills |

## 🌐 网络 / 内容

| Skill | 说明 |
|-------|------|
| **weather** | 天气和预报（wttr.in / Open-Meteo） |
| **summarize** | URL / 播客 / 文件摘要提取 |
| **blogwatcher** | 博客和 RSS/Atom 订阅监控 |
| **goplaces** | Google Places API 地点搜索 |
| **clawhub** | ClawHub Skill 搜索、安装、更新、发布 |
| **canvas** | Canvas 画布 |

## 🍔 其他

| Skill | 说明 |
|-------|------|
| **things-mac** | Things 3 任务管理 |
| **ordercli** | Foodora 外卖订单查询 |

---

## ⚠️ 注意
- 以上是 **2026.3.24** 版本的 Skills 列表
- **2026.3.28** 可能新增了更多 Skills（需升级后查看）
- 你当前已覆盖的 Skills：`weather`, `gh-issues`, `github`, `healthcheck`, `mcporter`, `node-connect`, `skill-creator`, `1password` 等
- 一些 Skills 需要额外安装 CLI 工具（如 `himalaya`, `gog`, `grizzly` 等）
- `coding-agent` 支持的后端：Codex、Claude Code、Gemini CLI、Pi
