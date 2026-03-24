---
name: git-retry-push
description: 当 git push 因网络问题失败时，创建定时任务自动重试，push 成功后自动删除定时任务。适用于 GitHub 等远程仓库连接超时的场景。
metadata:
  {
    "openclaw": {
      "requires": { "env": [] },
    }
  }
---

# Git Retry Push Skill

> 当 `git push` 因网络问题失败时，用此 skill 创建定时重试任务，push 成功后自动清理。

## 适用场景

- `git push` 失败，报错类似 `Failed to connect to github.com port 443`
- 网络不稳定，需要等待恢复
- 不想手动反复尝试 push

## 使用方法

### 一条指令调用

用户说"push 失败了，帮我重试"或类似的话时，直接执行以下步骤。

### Step 1: 确认当前状态

```bash
cd ~/.openclaw/workspace
git status --short
git log --oneline -1
```

确认有待 push 的 commit。

### Step 2: 创建定时任务

使用 `cron` 工具创建一个 `every` 类型的定时任务：

```json
{
  "name": "git-retry-push",
  "schedule": { "kind": "every", "everyMs": 300000 },
  "payload": {
    "kind": "agentTurn",
    "message": "执行 cd ~/.openclaw/workspace && git push origin main，如果 push 成功（exit code 0），就用 cron remove 删除自己这个 job（jobId: git-retry-push）。如果失败就不管，等下次自动重试。不要通知用户，静默完成即可。",
    "timeoutSeconds": 60
  },
  "delivery": { "mode": "none" },
  "sessionTarget": "isolated",
  "enabled": true
}
```

### Step 3: 告知用户

```
已创建定时重试任务 git-retry-push：
- 每 5 分钟尝试一次 push
- push 成功后自动删除任务
- 网络恢复后会自动完成
```

### Step 4: 如果需要立即尝试

先手动 push 一次，如果成功就不需要创建定时任务：

```bash
cd ~/.openclaw/workspace && git push origin main
```

如果失败再走 Step 2。

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `everyMs` | 300000 (5分钟) | 重试间隔，可根据网络情况调整 |
| `timeoutSeconds` | 60 | 单次 push 超时时间 |
| 仓库路径 | `~/.openclaw/workspace` | 可根据需要修改 |
| 远程分支 | `origin main` | 可根据需要修改 |

## 自定义用法

如果用户指定了不同的仓库或分支：

```
用户："帮我重试 push ~/Projects/myapp 到 origin dev"
```

修改 payload 中的命令为：
```bash
cd ~/Projects/myapp && git push origin dev
```

## 注意事项

1. **任务名称固定为 `git-retry-push`**，确保 subagent 能用 `cron remove` 删除自己
2. **delivery 设为 none**，不需要通知用户
3. **sessionTarget 必须是 isolated**，不能在主会话里跑
4. 如果手动解决了网络问题并 push 成功，记得手动删除定时任务：`cron remove git-retry-push`
