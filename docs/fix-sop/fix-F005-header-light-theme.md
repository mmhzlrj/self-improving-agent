# F-005: Header 亮色模式适配

## 问题描述
`docs-server.py` 中 header 的背景色硬编码为 `rgba(10,10,15,0.95)`（深色），切到亮色主题后 header 仍是黑色，与浅色内容不协调。

> 注意：这个修复已合并到 F-001 中。如果 F-001 已完成，此任务自动完成。
> 如果 F-001 中的 Step 3 没有执行，则单独执行此 SOP。

## 文件
- `/Users/lr/.openclaw/workspace/tools/docs-server.py`

## 修复步骤

### Step 1: 检查 F-001 是否已修复 header
```bash
grep "background:var(--surface)" /Users/lr/.openclaw/workspace/tools/docs-server.py | head -1
```
如果已有输出（找到 `var(--surface)` 在 header 行），则此任务已完成。

### Step 2: 如果未修复，执行替换
找到：
```css
.header{{position:fixed;top:0;left:0;right:0;height:var(--header-h);background:rgba(10,10,15,0.95);border-bottom:1px solid var(--border);display:flex;align-items:center;padding:0 20px;z-index:100; backdrop-filter:blur(10px)}}
```

替换为：
```css
.header{{position:fixed;top:0;left:0;right:0;height:var(--header-h);background:var(--surface);border-bottom:1px solid var(--border);display:flex;align-items:center;padding:0 20px;z-index:100; backdrop-filter:blur(10px)}}
```

### Step 3: 重启验证
```bash
lsof -ti:18998 | xargs kill -9 2>/dev/null
cd /Users/lr/.openclaw/workspace && nohup python3 tools/docs-server.py > /tmp/docs-server.log 2>&1 &
sleep 2
```

## 验证标准
- [ ] 暗色模式 header 正常
- [ ] 亮色模式 header 为浅色背景
