# OpenClaw 升级准备 Skill

## 触发条件

满足以下任一条件时执行：
1. **检测到新版本**：运行 `openclaw update check` 或查询 GitHub releases，发现当前安装版本 < 最新版本
2. **用户提示升级**：用户说"升级"、"更新 OpenClaw"、"update openclaw"等

## 执行时机

- **新版本检测后**：询问用户是否执行升级准备
- **用户要求升级前**：先执行升级准备，确认完成后再执行实际升级

## 升级准备步骤

### Step 1: 环境检查
```bash
# 检查当前版本
openclaw --version

# 检查最新版本
curl -s "https://api.github.com/repos/openclaw/openclaw/releases/latest" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['tag_name'])"

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
# 阅读 release notes，查找以下关键词
# - breaking
# - migration
# - 需要手动干预
# - 配置变更
curl -s "https://api.github.com/repos/openclaw/openclaw/releases/latest" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print('版本:', d['tag_name'])
print('发布日期:', d['published_at'])
print()
body = d.get('body', '')
# 高亮 breaking change
for line in body.split('\n'):
    if any(k in line.lower() for k in ['breaking', 'migration', '需要手动', 'manual']):
        print('⚠️', line)
"
```

### Step 4: 检查插件兼容性
```bash
# 列出所有插件
ls ~/.openclaw/extensions/

# 检查 MCP servers
ps aux | grep -E "mcp|server.mjs" | grep -v grep | awk '{print $1,$2,$11}' | head -10
```

### Step 5: 记录准备状态
将以下信息写入 memory/YYYY-MM-DD.md：
- 当前版本
- 目标版本
- 发现的 breaking changes
- 需要的额外步骤
- 备份路径

### Step 6: 询问用户确认
向用户报告：
1. 当前版本 → 目标版本
2. 发现的 breaking changes（如果有）
3. 需要的额外步骤（如果有）
4. 备份已完成
5. 询问：是否可以执行升级？

## 输出格式

```
## OpenClaw 升级准备报告

### 版本信息
- 当前版本: v2026.3.28
- 最新版本: v2026.4.1
- 更新内容: [主要新功能列表]

### Breaking Changes
- [有/无]
- [如有，列出具体内容]

### 额外步骤
- [有/无需要手动干预的步骤]

### 备份状态
- ✅ openclaw.json 已备份
- ✅ 配置 golden 备份已更新

### 建议
[是否可以安全升级 / 需要注意的事项]

是否可以执行升级？
```
