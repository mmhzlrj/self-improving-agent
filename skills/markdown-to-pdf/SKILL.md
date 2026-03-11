---
name: markdown-to-pdf
description: "将 Markdown 文件转换为 PDF。支持自定义样式、页眉页脚、页码等功能。"
metadata: { "openclaw": { "emoji": "📄", "requires": {} } }
---

# Markdown 转 PDF Skill

将 Markdown 文件转换为 PDF 文档。

## 功能

- 📄 Markdown 转 PDF
- 🎨 自定义样式
- 📑 页眉页脚
- 🔢 页码设置
- 📐 页面大小设置

## 使用方法

### 基本命令

| 命令 | 说明 |
|------|------|
| `PDF 文件路径` | 将 Markdown 转换为 PDF |
| `PDF 文件路径 --title 标题` | 设置文档标题 |
| `PDF 文件路径 --landscape` | 横版布局 |

### 示例

```
PDF ~/Desktop/readme.md
PDF ~/Documents/report.md --title "我的报告"
PDF ~/Desktop/test.md --landscape
```

## 安装依赖

首次使用需要安装依赖：

```bash
npm install -g markdown-pdf
```

或使用 puppeteer（更美观）：

```bash
npm install -g puppeteer markdown-pdf
```

## 选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--title` | 文档标题 | 文件名 |
| `--landscape` | 横版布局 | false |
| `--format` | 页面格式 | A4 |
| `--margin` | 边距 | 10mm |

## 示例输出

转换后的 PDF 会保存在原文件同目录，扩展名为 .pdf。
