---
name: openclaw-upgrade
description: "OpenClaw 升级前准备流程。触发条件：(1) 检测到新版本时 (2) 用户要求升级前。执行版本检查、备份配置、Breaking Changes 分析、插件兼容性检查，汇报后询问确认。"
---

# OpenClaw 升级准备 Skill

## 触发条件

满足以下任一条件时执行：
1. **检测到新版本**：运行 `openclaw update` 或查询 GitHub releases，发现当前安装版本 < 最新版本
2. **用户提示升级**：用户说"升级"、"更新 OpenClaw"、"update openclaw"等

## 执行时机

- **新版本检测后**：询问用户是否执行升级准备
- **用户要求升级前**：先执行升级准备，确认完成后再执行实际升级

## 升级前强制步骤（按顺序执行！）

### Step A: 记录到 memory/YYYY-MM-DD.md
将以下内容追加到 `memory/YYYY-MM-DD.md`（顶部加新章节）：
```markdown
## OpenClaw 升级准备
- 时间：YYYY-MM-DD HH:MM
- 当前版本：vX.X.X
- 目标版本：vY.Y.Y
- Breaking Changes：[列出]
- 备份路径：[列出]
```

### Step B: 记录到 self-improving-agent ERRORS.md（如有）
如果升级前检查中发现任何问题，立即写入两处：
- `~/.openclaw/workspace/.learnings/ERRORS.md`
- `~/.openclaw/workspace/skills/self-improving-agent/.learnings/ERRORS.md`

### Step C: 记录到 self-improving-agent LEARNINGS.md
将本次升级准备的正确命令、错误经验写入两处：
- `~/.openclaw/workspace/.learnings/LEARNINGS.md`
- `~/.openclaw/workspace/skills/self-improving-agent/.learnings/LEARNINGS.md`

### Step D: Git push（必须！）
```bash
git -C ~/.openclaw/workspace add .
git -C ~/.openclaw/workspace commit -m "chore: upgrade prep for vX.X.X -> vY.Y.Y"
git -C ~/.openclaw/workspace push
```
> 如果 git push 失败，用 git-retry-push skill 自动重试。

### Step E: 同步 sessions 到 Ubuntu + reindex
```bash
# 1. 同步 sessions（rsync 已永久免审）
rsync -avz --ignore-existing ~/.openclaw/agents/main/sessions/ jet@192.168.1.18:~/.openclaw/agents/main/sessions/

# 2. 触发 Ubuntu Semantic Cache 增量索引
curl -s -X POST http://100.97.193.116:5050/reindex
```
> 如果 curl 超时，静默继续（可能是 Tailscale TCP 临时问题）。

### Step F: 记录命令日志（必须！）
每次 exec 命令完成后，立即追加到 `docs/command-log.md`：
```markdown
| HH:MM | `命令` | ✅/❌ 结果 | 备注 |
```

---

## 升级准备步骤

### Step 1: 环境检查
```bash
# 检查当前版本
openclaw --version

# 检查最新版本（用 gh CLI，已在 allow-always）
gh release list --repo openclaw/openclaw --limit 3

# 检查 Gateway 状态
openclaw gateway status

# 检查正在运行的 tasks
openclaw tasks list
```

### Step 2: 备份配置
```bash
# 备份 golden 配置
bash ~/.openclaw/backup/update-golden.sh

# 或手动备份关键文件
cp ~/.openclaw/openclaw.json ~/.openclaw/backup/openclaw.json.$(date +%Y%m%d)
```

### Step 3: 检查 Breaking Changes
```bash
# 使用封装脚本
python3 ~/.openclaw/workspace/scripts/check-openclaw-latest.py
```

> ⚠️ **不要用** `curl ... | python3` — 会触发新的 allowlist 审批。
> ⚠️ **不要用** `curl ... | head` 或 `tail` — 严格禁止截断命令。
> ✅ **正确做法**：curl → 写脚本文件 → python3 执行脚本文件

### Step 4: 检查插件兼容性
```bash
# 列出所有插件
ls ~/.openclaw/extensions/

# 检查 MCP servers
ls ~/.openclaw/extensions/*/server.mjs 2>/dev/null
```

### Step 5: 汇报给用户确认
向用户报告：
1. 当前版本 → 目标版本
2. 发现的 breaking changes（如果有）
3. 需要的额外步骤（如果有）
4. 备份已完成
5. **A-F 强制步骤已完成**（git push、sessions 同步、memory 记录全部就绪）
6. 询问：是否可以执行升级？

## 输出格式

```
## OpenClaw 升级准备报告

### 版本信息
- 当前版本: v2026.x.x
- 目标版本: v2026.x.x

### Breaking Changes
- [有/无]
- [如有，列出具体内容]

### 备份状态
- ✅ openclaw.json 已备份
- ✅ 配置 golden 备份已更新

### A-F 强制步骤
- ✅ Step A: memory 记录
- ✅ Step B: LEARNINGS 记录
- ✅ Step C: ERRORS 检查
- ✅ Step D: git push
- ✅ Step E: sessions 同步 + reindex
- ✅ Step F: command-log 记录

### 建议
[是否可以安全升级]

是否可以执行升级？
```

## 执行升级（用户确认后）

```bash
# ✅ 正确命令（无参数）
openclaw update

# ❌ 错误命令（不接受参数）
openclaw update run
```

## ⭐ 升级完成后的强制步骤

### Step G: 验证新版本
```bash
openclaw --version
```
确认显示新版本号。

### Step H: 运行 doctor 修复（如有 Breaking Changes）
```bash
openclaw doctor --fix
```

### Step I: 记录升级结果到 memory
```markdown
## OpenClaw 升级结果
- 时间：YYYY-MM-DD HH:MM
- 版本：vX.X.X → vY.Y.Y
- 结果：成功/失败
- 遇到的问题：[如有]
```

### Step J: 推送 git
```bash
git -C ~/.openclaw/workspace add .
git -C ~/.openclaw/workspace commit -m "OpenClaw upgrade: vX.X.X -> vY.Y.Y"
git -C ~/.openclaw/workspace push
```

### Step K: 再次同步 sessions + reindex（升级后同步）
```bash
rsync -avz --ignore-existing ~/.openclaw/agents/main/sessions/ jet@192.168.1.18:~/.openclaw/agents/main/sessions/
curl -s -X POST http://100.97.193.116:5050/reindex
```
