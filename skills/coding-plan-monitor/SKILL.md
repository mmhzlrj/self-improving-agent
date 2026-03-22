---
name: coding-plan-monitor
description: MiniMax Coding Plan 额度监控 - 自动检测用量并控制任务节奏
---

# Coding Plan Monitor Skill

监控 MiniMax Coding Plan 使用量，自动控制任务节奏。

## 功能

### 1. 检查当前用量

```bash
python3 ~/.openclaw/workspace/skills/coding-plan-monitor/monitor.py check
```

输出：
```
模型: MiniMax-M2.5
周期: 20:00 - 00:00
剩余: 292 (48.7%)
已用: 308 (51.3%)
重置: 1小时37分钟后
```

### 2. 任务控制逻辑

| 用量 | 操作 |
|------|------|
| < 90% | 正常执行 |
| ≥ 90% | 减缓任务（减少并发） |
| ≥ 95% | 暂停任务，记录进度 |
| 重置后 | 继续执行 |

### 3. 在任务中调用

在执行消耗 API 的任务前，先调用：

```python
import subprocess
result = subprocess.run(
    ['python3', '~/.openclaw/workspace/skills/coding-plan-monitor/monitor.py', 'check'],
    capture_output=True, text=True
)
# 检查输出中的已用比例
```

---

## 额度阈值

| 阈值 | 剩余 | 状态 | 操作 |
|------|------|------|------|
| 90% | < 60 | ⚠️ 紧张 | 减缓任务 |
| 95% | < 30 | 🔴 暂停 | 记录进度，等待重置 |

---

## 重置周期

- 周期：每 5 小时滚动
- 时间：20:00 - 00:00 (UTC+8)
- 最后周期：4 小时

---

## API Key

已配置：
```
sk-cp-Zosvx8d6zR6EI34fzFEWopC1kvtXdtzpMPWObv8goBG4MyNJTzK-vuniGGQV5TPOcICyJP-qIjWQ66KlY5mtOm6Z1oAVA1lugbkRDjE1QyMFX6phXsGVOPA
```
