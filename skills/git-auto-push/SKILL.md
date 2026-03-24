---
name: git-auto-push
description: Git 自动推送 - 当 git push 因网络问题失败时，自动重试推送
---

# Git Auto Push Skill

当 `git push` 因网络问题失败时，用此 skill 自动重试或设置定时推送。

## 适用场景

- `git push` 报错：`Error in the HTTP2 framing layer`、`Connection refused`、`SSL error` 等
- 网络不稳定导致 push 失败
- 需要确保 workspace 代码同步到 GitHub 远程仓库

## 使用方式

### 方式1：立即重试（降级 HTTP/1.1）

```bash
# 强制使用 HTTP/1.1（解决 HTTP2 framing layer 错误）
cd ~/.openclaw/workspace && git -c http.version=HTTP/1.1 push
```

### 方式2：检查待推送的 commit

```bash
# 查看本地领先远程多少个 commit
cd ~/.openclaw/workspace && git log --oneline @{upstream}..HEAD
```

### 方式3：设置 cron 定时重试

```bash
# 每 30 分钟自动重试 push
openclaw cron add --job '{
  "name": "git-auto-push",
  "schedule": { "kind": "every", "everyMs": 1800000 },
  "payload": { "kind": "agentTurn", "message": "执行 git push，如果失败则等下次重试。命令：cd ~/.openclaw/workspace && git -c http.version=HTTP/1.1 push。成功后删除这个 cron job。" },
  "sessionTarget": "isolated",
  "enabled": true
}'
```

成功后手动删除 cron：
```bash
# 查看所有 cron jobs
openclaw cron list
# 删除（用实际的 jobId）
openclaw cron remove --jobId <jobId>
```

## 故障排除

| 错误 | 解决方案 |
|------|---------|
| `Error in the HTTP2 framing layer` | 降级 HTTP/1.1：`git -c http.version=HTTP/1.1 push` |
| `Connection refused` | 检查网络/代理，等网络恢复后重试 |
| `Authentication failed` | 检查 GitHub token 是否过期 |
| `push timeout` | 增大超时：`git config --global http.postBuffer 524288000` |

## 注意事项

- 本地 commit 不会丢失，push 失败不影响 subagent 读本地文件
- 远程仓库 `https://github.com/mmhzlrj/openclaw-workspace-backup.git` 仅作备份
- subagent 继承 workspace 目录，读到的是**本地文件**，不依赖 GitHub
- 如果连续失败 3 次以上，通知用户检查网络环境
