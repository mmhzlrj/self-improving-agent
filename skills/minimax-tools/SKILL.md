---
name: minimax-tools
description: MiniMax 工具集 - 网络搜索和图片理解（模拟 MiniMax Coding Plan MCP）
---

# MiniMax Tools Skill

直接调用 MiniMax Coding Plan API 实现网络搜索和图片理解功能。

## 功能

### 1. web_search（网络搜索）

```bash
python3 ~/.openclaw/workspace/skills/minimax-tools/minimax.py search "<关键词>"
```

示例：
```bash
python3 ~/.openclaw/workspace/skills/minimax-tools/minimax.py search "AI 最新新闻"
python3 ~/.openclaw/workspace/skills/minimax-tools/minimax.py search "Python 教程"
```

### 2. understand_image（图片理解）

```bash
python3 ~/.openclaw/workspace/skills/minimax-tools/minimax.py image "<问题>" "<图片路径或URL>"
```

示例：
```bash
python3 ~/.openclaw/workspace/skills/minimax-tools/minimax.py image "这张图片是什么？" "https://example.com/image.jpg"
python3 ~/.openclaw/workspace/skills/minimax-tools/minimax.py image "描述这张图片" "/path/to/photo.png"
```

## API 信息

- API Key: sk-cp-Zosvx8d6zR6EI34fzFEWopC1kvtXdtzpMPWObv8goBG4MyNJTzK-vuniGGQV5TPOcICyJP-qIjWQ66KlY5mtOm6Z1oAVA1lugbkRDjE1QyMFX6phXsGVOPA
- API Host: https://api.minimaxi.com

## 优势

- ✅ 无需 MCP 客户端
- ✅ 直接调用 MiniMax API
- ✅ 支持网络搜索和图片理解
- ✅ 可以配合 Tavily 使用

## 使用场景

当需要 MiniMax 的网络搜索或图片理解功能时，可以使用这个脚本。

注意：此脚本使用的是 MiniMax Coding Plan 的 API，使用会消耗套餐额度。
