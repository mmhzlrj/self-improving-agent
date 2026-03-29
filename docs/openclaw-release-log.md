# OpenClaw Release Log

> 当前安装版本：**2026.3.24** (cff6dc9)
> 最新版本：**2026.3.28** (2026-03-29)
> 源码：https://github.com/openclaw/openclaw/releases

---

## 2026.3.28 (2026-03-29)

### Breaking

- **Qwen**: 移除已废弃的 `qwen-portal-auth` OAuth 集成，迁移到 Model Studio（`openclaw onboard --auth-choice modelstudio-api-key`）
- **Config/Doctor**: 放弃两个月前的自动配置迁移，很旧的 legacy key 现在会验证失败而不是被重写

### Changes（新功能）

- **xAI**: 切换到 Responses API，新增 `x_search`，自动启用 xAI 插件（无需手动 toggle）
- **MiniMax**: 新增图片生成 provider（image-01 模型），支持生成和图片编辑，支持宽高比控制
- **MiniMax**: 模型目录精简为仅 M2.7，移除 M2、M2.1、M2.5、VL-01
- **Plugins/Hooks**: 新增 `before_tool_call` 的 `requireApproval`，允许插件暂停工具执行并提示用户审批（exec overlay、Telegram 按钮、Discord 交互、/approve 命令）
- **ACP/Channels**: 新增当前对话 ACP 绑定（Discord/BlueBubbles/iMessage），`/acp spawn codex --bind here` 可将当前聊天转为 Codex 工作区
- **OpenAI**: 默认启用 `apply_patch`，对齐 sandbox 权限
- **CLI backends**: 新增 Gemini CLI 后端支持，`--claude-cli-logs` 改为通用 `--cli-backend-logs`
- **Podman**: 简化容器设置，安装到 `~/.local/bin`
- **Slack**: 新增显式 `upload-file` 动作，支持文件名/标题/评论
- **Matrix TTS**: 自动 TTS 回复改为原生语音气泡
- **CLI**: 新增 `openclaw config schema` 命令
- **Memory**: pre-compaction memory flush 交给 memory-core 插件管理
- **Plugins**: 暴露 `runHeartbeatOnce`，插件可触发单次心跳
- **Tavily**: 标记 `X-Client-Source: openclaw`
- **Compaction**: 保留 stale-usage 压缩后的 AGENTS 刷新；`/compact` 无操作时显示"skipped"而非"failed"

### Fixes（修复）

- **Anthropic**: 未处理的 provider stop reason（如 sensitive）不再崩溃 agent run
- **Google**: Gemini 3.1 pro/flash/flash-lite 解析修复
- **OpenAI Codex**: 图片工具注册修复，不再因缺少 provider 而失败
- **image tool**: 恢复 generic fallback，openrouter/minimax-portal 图片分析修复
- **WhatsApp**: 修复自聊 DM 模式的无限回声循环
- **Telegram**: 长消息按词边界拆分；空文本回复不再触发 GrammyError 400；replyToMessageId 验证修复
- **Mistral**: 修复 422 错误
- **Control UI**: 敏感配置默认隐藏，需显式点击才能编辑
- **Discord**: 重连时清理旧 socket，不再循环重连
- **iMessage**: 不再泄露 `[[reply_to:...]]` 标签到发送文本
- **Feishu**: WebSocket 连接关闭修复；使用原始 create_time 而非 Date.now()
- **Heartbeat**: 保证定时器在异常后重新启动，心跳不再静默停止
- **Memory search**: 修复跨插件运行时的 unknown provider 错误
- **Agents/sandbox**: 尊重 `alsoAllow`，工具策略对齐
- **Cooldowns**: 按模型限流，30s/1min/5min 阶梯，不再一个 429 阻塞所有模型

---

## 2026.3.24 (2026-03-25) ← 当前安装版本

### Breaking

无

### Changes（新功能）

- **Gateway/OpenAI 兼容**: 新增 `/v1/models` 和 `/v1/embeddings`，`/v1/chat/completions` 和 `/v1/responses` 支持模型覆盖
- **Agents/tools**: `/tools` 命令显示当前可用工具，Control UI 新增 "Available Right Now" 区域
- **Microsoft Teams**: 迁移到官方 SDK，支持流式回复、欢迎卡片、反馈、状态更新
- **Teams**: 新增消息编辑和删除支持
- **Skills**: 打包技能新增一键安装（coding-agent、gh-issues、whisper 等）
- **Control UI/Skills**: 状态过滤标签（All/Ready/Needs Setup/Disabled）
- **Slack**: 恢复富文本回复，Options 行自动渲染为按钮
- **CLI/Containers**: 新增 `--container` 和 `OPENCLAW_CONTAINER` 在 Docker/Podman 内运行
- **Discord**: 可选 `autoThreadName: "generated"` 自动命名
- **Plugins/hooks**: 新增 `before_dispatch`
- **Control UI**: Agent 工作区文件支持展开和 markdown 预览

### Fixes（修复）

- **Agents**: image tool 恢复 generic fallback（openrouter/minimax-portal）
- **Agents**: 429/overload 中途失败现在会暴露给用户
- **Agents**: cooldown 按模型限流（30s/1min/5min 阶梯）
- **Agents**: compaction 超时恢复，不再重复过大请求
- **Feishu**: WebSocket 关闭修复；时间戳修复
- **Discord**: 重连修复，不再循环
- **Memory search**: 跨插件运行时修复
- **CLI**: 更新检查显示 "up to date"

---

## 历史版本索引

| 版本 | 日期 | 类型 |
|------|------|------|
| 2026.3.28 | 2026-03-29 | 正式 |
| 2026.3.24 | 2026-03-25 | 正式 ← 当前安装 |
| 2026.3.23 | 2026-03-23 | 正式 |
| 2026.3.22 | 2026-03-23 | 正式 |
| 2026.3.13 | 2026-03-14 | 正式 |
| 2026.3.12 | 2026-03-13 | 正式 |
| 2026.3.11 | 2026-03-12 | 正式 |
| 2026.3.8 | 2026-03-09 | 正式 |
| 2026.3.7 | 2026-03-08 | 正式 |
| 2026.3.2 | 2026-03-03 | 正式 |
| 2026.3.1 | 2026-03-02 | 正式 |

> 注：历史版本详细内容待补充。如需查看某个版本的完整 changelog，访问 https://github.com/openclaw/openclaw/releases/tag/v{版本号}
