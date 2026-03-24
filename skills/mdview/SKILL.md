---
name: mdview
description: 快速查看 Markdown 文件 - 用浏览器打开 MD 文件，支持普通预览和审批模式
---

# MDView Skill

用浏览器快速查看 Markdown 文件，支持普通预览和审批模式（采纳/拒绝/备注）。

## 安装

```bash
pip3 install markdown
```

## 使用方式

### 普通预览

```bash
python3 ~/.openclaw/workspace/tools/mdview.py <文件路径>
```

### 审批模式（带采纳/拒绝按钮）

```bash
python3 ~/.openclaw/workspace/tools/mdview.py --review <文件路径>
# 简写
python3 ~/.openclaw/workspace/tools/mdview.py -r <文件路径>
```

审批模式会将 Markdown 按 `### 数字.` 拆分为条目，每个条目显示：
- 📄 原文 / ✏️ 建议（如果有 `**原文**` 和 `**建议改为**` 字段）
- 采纳 / 拒绝按钮
- 备注输入框
- 优先级标签（如果有 `**优先级**` 字段）

顶部工具栏：全部采纳、重置、导出 JSON 结果
审批结果自动保存到浏览器 localStorage。

### 读取审批结果

```bash
# 自动检测（优先 CDP localStorage → ~/Downloads 导出文件）
python3 ~/.openclaw/workspace/tools/read-review-results.py

# 读取指定文件
python3 ~/.openclaw/workspace/tools/read-review-results.py ~/Downloads/review-results-2026-03-24.json
```

读取结果会自动保存到 `~/.openclaw/workspace/.review/review-results.json`。

## 功能

- ✅ 用浏览器打开 Markdown 文件（HTTP Server，非临时文件）
- ✅ 代码高亮、表格、引用、中文支持
- ✅ 审批模式：逐条采纳/拒绝，支持备注
- ✅ 审批结果导出为 JSON
- ✅ 通过 CDP 或导出文件读取审批结果

## 注意事项

- **打开 Markdown 文件用这个命令**，不要用 `open` 或 `exec + openclaw browser`
- 服务端口固定为 `18999`（`http://127.0.0.1:18999/index.html`）
- 审批结果存在浏览器 localStorage，刷新页面数据不丢失
- 导出的 JSON 文件默认下载到 `~/Downloads/`

## 示例

```bash
# 预览 README
python3 ~/.openclaw/workspace/tools/mdview.py ~/.openclaw/workspace/README.md

# 审批修改意见
python3 ~/.openclaw/workspace/tools/mdview.py -r ~/.openclaw/workspace/.review/2026-03-24-review.md

# 读取审批结果
python3 ~/.openclaw/workspace/tools/read-review-results.py
```
