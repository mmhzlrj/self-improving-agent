# F-004: 版本系统初始化

## 问题描述
`docs-server.py` 中已有 `load_versions()`、`bump_module_version()` 函数和版本页面路由，但 `docs/.versions/` 目录和 `versions.json` 文件不存在，版本系统是空转。

## 文件
- `/Users/lr/.openclaw/workspace/docs/.versions/versions.json`（需创建）

## 实现步骤

### Step 1: 创建 .versions 目录
```bash
mkdir -p /Users/lr/.openclaw/workspace/docs/.versions
```

### Step 2: 创建初始 versions.json
创建 `/Users/lr/.openclaw/workspace/docs/.versions/versions.json`：

```json
{
  "openclaw": {
    "version": "v0.1.0",
    "changes": [
      {
        "type": "added",
        "detail": "docs.0-1.ai 站点搭建：SOP 文档展示 + 模块文档 + 调研报告",
        "date": "2026-04-01"
      },
      {
        "type": "added",
        "detail": "暗黑/亮色主题切换",
        "date": "2026-04-01"
      },
      {
        "type": "added",
        "detail": "Prism.js 代码高亮 + Fuse.js 模糊搜索",
        "date": "2026-04-01"
      }
    ]
  },
  "lewm": {
    "version": "v0.1.0",
    "changes": [
      {
        "type": "added",
        "detail": "LeWM 世界模型文档初始化",
        "date": "2026-04-01"
      }
    ]
  },
  "gui-geng": {
    "version": "v0.1.0",
    "changes": [
      {
        "type": "added",
        "detail": "贵庚记忆系统文档初始化",
        "date": "2026-04-01"
      }
    ]
  },
  "arm": {
    "version": "v0.1.0",
    "changes": [
      {
        "type": "added",
        "detail": "机械臂模块文档初始化",
        "date": "2026-04-01"
      }
    ]
  },
  "vision": {
    "version": "v0.1.0",
    "changes": [
      {
        "type": "added",
        "detail": "视觉识别模块文档初始化",
        "date": "2026-04-01"
      }
    ]
  },
  "suction": {
    "version": "v0.1.0",
    "changes": [
      {
        "type": "added",
        "detail": "吸盘抓手模块文档初始化",
        "date": "2026-04-01"
      }
    ]
  },
  "locomotion": {
    "version": "v0.1.0",
    "changes": [
      {
        "type": "added",
        "detail": "移动模块文档初始化",
        "date": "2026-04-01"
      }
    ]
  },
  "face": {
    "version": "v0.1.0",
    "changes": [
      {
        "type": "added",
        "detail": "面部模块文档初始化",
        "date": "2026-04-01"
      }
    ]
  }
}
```

### Step 3: 重启服务并验证版本页面
```bash
lsof -ti:18998 | xargs kill -9 2>/dev/null
cd /Users/lr/.openclaw/workspace && nohup python3 tools/docs-server.py > /tmp/docs-server.log 2>&1 &
sleep 2
```

访问版本变更页面，确认内容正确显示。

### Step 4: 验证版本数据可读取
```bash
python3 -c "
import json
with open('/Users/lr/.openclaw/workspace/docs/.versions/versions.json') as f:
    d = json.load(f)
print(f'模块数: {len(d)}')
for k, v in d.items():
    print(f'  {k}: {v[\"version\"]} ({len(v[\"changes\"])} changes)')
"
```

## 验证标准
- [ ] `docs/.versions/versions.json` 存在
- [ ] JSON 格式合法（python3 能解析）
- [ ] 所有 8 个模块都有初始版本记录
- [ ] OpenClaw 有 3 条初始变更记录
- [ ] 版本页面正常显示（不报错）
