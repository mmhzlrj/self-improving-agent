---
name: mdview
description: 快速查看 Markdown 文件 - 用浏览器打开 MD 文件，效果类似 GitHub
---

# MDView Skill

用浏览器快速查看 Markdown 文件，效果类似 GitHub 预览。

## 安装

```bash
# 安装依赖
pip3 install markdown

# 添加到 PATH（可选）
echo 'export PATH="$HOME/.openclaw/workspace/tools:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

## 使用方式

### 方式1：命令行

```bash
python3 ~/.openclaw/workspace/tools/mdview.py ~/.openclaw/workspace/harness/aigc-workflow/README.md
```

### 方式2：作为 Skill 使用

当用户要求查看 .md 文件时，使用此 Skill：

```bash
python3 ~/.openclaw/workspace/tools/mdview.py <文件路径>
```

## 功能

- ✅ 用浏览器打开 Markdown 文件
- ✅ 代码高亮
- ✅ 表格样式
- ✅ 类似 GitHub 的预览效果
- ✅ 支持中文

## 示例文件

查看调研报告：
```bash
python3 ~/.openclaw/workspace/tools/mdview.py ~/.openclaw/workspace/harness/aigc-workflow/README.md
```
