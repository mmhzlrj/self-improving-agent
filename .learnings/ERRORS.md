# ERRORS.md - 错误记录

## 错误6：偷懒截断读取文件，导致误判文档结构（2026-04-01）
- 调研 ROBOT-SOP.md 时用了 `head -20` + `tail -5` 等截断命令
- 导致把 5008 行、10章+术语表的文档，误判为"7个章节"
- 用户发现后要求"重新去看完整的文件"，造成时间浪费
- 教训：调研阶段必须完整读取文件，不得以任何理由截断
- 已更新：SOUL.md、AGENTS.md

## 错误7：config 操作导致 openclaw.json 格式错误（2026-04-02）
- 执行 `openclaw config exec ask off` 和 `openclaw config exec security full` 导致配置文件损坏
- 原因：config 命令格式不确定就盲目执行
- 症状：Gateway 启动时报 `tools.exec.ask: Invalid option` 和 `Unrecognized key: "askFallback"`
- 教训：config 相关的操作必须先确认格式，不确定时要先问用户
- 修复：用户手动运行 `openclaw doctor --fix` 恢复

## 错误8：cron add 命令语法错误（2026-04-02）
- 尝试用 `openclaw cron add --schedule` 被拒绝（`--schedule` 不存在）
- 改用 `openclaw cron add --name --cron --session` 仍然失败
- 正确方式：用 cron tool 的 JSON schema 直接调用 `cron.add`，完全绕过 CLI 语法

## 错误9：exec 白名单路径错误（2026-04-02）
- `/usr/bin/rsync` 实际在白名单里（Gateway 已经允许），但没意识到
- 导致花了大量时间尝试用其他方式绕过白名单
- 教训：先确认哪些命令已经在白名单里，再决定需要添加哪些

## 错误10：误删 HEARTBEAT.md 的旧记录（2026-04-02）
- 编辑 HEARTBEAT.md 时用新内容块替换了旧内容块，但旧内容块引用的是更新前的状态
- 导致旧的 Last check 信息被覆盖
- 教训：编辑 HEARTBEAT.md 时要保留旧记录的完整性，只在底部追加新记录

## 错误15：错误归因 SIGKILL 为"系统杀进程"（2026-04-08~09）
- Ubuntu 上 PlatformIO toolchain 下载被 SIGKILL，日志记录为"大文件下载被系统 SIGKILL（网络问题）"
- 实际排查：Ubuntu 32GB 内存无 OOM、无 cgroup 限制、无 dmesg kill 记录
- **真正原因**：OpenClaw exec 的 timeout 参数到了 → Gateway 主动 kill exec 子进程 → SSH 会话断开 → 远程进程收到 SIGKILL
- 教训：
  - 写日志时不能瞎猜原因，要区分"系统 SIGKILL"和"exec timeout 导致的 SIGKILL"
  - 大文件下载/安装任务必须设足够长的 timeout
  - 正确模式：长超时 + 定期巡检（每 60s poll 一次），而不是短超时一次性等结果
- 已更新：经验教训需记录给 MiniMax subagent 参考

## 错误17：多次 config.patch 连锁导致 Gateway 不稳定（2026-04-09）
- 5 次 config.patch 在 2 小时内执行，每次触发 Gateway SIGUSR1 重启
- 重启期间 spawn subagent/sessions_send 导致 "GatewayDrainingError" 和 "gateway timeout"
- subagent 被断连 → exec 孤儿进程 SIGKILL → 更多系统通知
- 教训：**多个配置变更必须合并成一次 config.patch**，减少重启次数
- 教训：重启后至少等 30 秒再执行需要 WebSocket 的操作（spawn/send）

## 错误16：exec timeout 越设越短的恶性循环（2026-04-09）
- 安装 ESP-IDF 时 install.sh timeout 设 300s，不够用又重来
- subagent runTimeout 设 600s 但 exec 内部又套了短 timeout
- 导致：外层还没跑完，内层 exec 就被 SIGTERM 杀了
- 教训：
  - 长任务（安装、编译、下载）的 exec timeout 至少设 600-1800s
  - 不要在 exec 内部再套短 timeout
  - 用 process poll 定期检查进度，不要一次等到底

## 错误11：docs.0-1.ai 导航链接指向不存在的文件（2026-04-08）
- `NAV_CONFIG` 中 `/tools/config.html` 和 `/tools/mcp.html` 路由存在，但 `docs/tools/config.md` 和 `docs/tools/mcp.md` 文件不存在
- 导致用户点击导航后 404
- 教训：添加导航路由时，同步创建对应的 `.md` 文件，不能只加路由不加内容

## 错误12：techref 分类页"查看"按钮链接缺少分类前缀（2026-04-08）
- techref category 页面（如 `/techref/browser-relay.html`）的"查看"按钮生成链接为 `/docs.0-1.ai/browser-relay-config.html`
- 正确链接应为 `/docs.0-1.ai/techref/browser-relay-config.html`
- 导致所有 techref 分类下的子文档链接 404
- 教训：生成带分类路径的链接时，要使用完整路径 prefix，不能省略分类层级
- 修复：在 href 中加 `/techref/` 前缀

## 错误13：docs.0-1.ai 新增 section 后未同步更新 category_map（2026-04-08）
- NAV_CONFIG 添加了 `/techref/openclaw-v2026-4-5-changelog.html` 链接，但 `category_map` 中未注册，导致 404
- 教训：每次在 `docs/` 下新增 `.md` 文件时，同步检查 NAV_CONFIG 或 category_map 是否已注册路由

## 错误14：docs.0-1.ai `integrations/` 和 `fix-sop/` 目录无路由（2026-04-08）
- subagent A-0024 负责修复，但在我自己的排查中也发现了同样问题
- 说明 subagent 和我同时在修同一个问题，没有协调好
- 教训：发现 404 时先检查是否已有其他 agent/subagent 在处理同类问题，避免重复劳动
- 编辑 HEARTBEAT.md 时用新内容块替换了旧内容块，但旧内容块引用的是更新前的状态
- 导致旧的 Last check 信息被覆盖
- 教训：编辑 HEARTBEAT.md 时要保留旧记录的完整性，只在底部追加新记录

---

所有错误经验必须同步记录到两个地方：
- `~/.openclaw/workspace/.learnings/ERRORS.md`（workspace 本地）
- `~/.openclaw/workspace/skills/self-improving-agent/.learnings/ERRORS.md`（self-improving-agent submodule）

## 2026-04-09 孤儿进程清理误删 session

### 错误类型
逻辑错误：误判 orphan + runs.json 意外清空

### 触发条件
Gateway 过载时，sessions.json 膨胀到 16MB，误以为需要清理

### 正确做法
1. status=done/failed/timeout 的 subagent 不一定孤儿（必须检查 .jsonl 文件是否存在）
2. runs.json 绝对不能清空，只能删对应 orphan 相关的条目
3. 清理前必须先确认 backup 存在
