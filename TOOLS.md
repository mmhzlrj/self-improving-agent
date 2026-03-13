# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

### 飞书图片存储

- 路径: `~/.openclaw/workspace/feishu-images/`
- 命名规则: 精确到秒 (YYYY-MM-DD-HH-mm-ss.png)

### AI 平台设置脚本

- **位置**: `~/.openclaw/workspace/scripts/cdp-setup-v3.sh`
- **用途**: 设置 AI 网页版的模型模式
- **使用**: 
  - 单平台: `~/.openclaw/workspace/scripts/cdp-setup-v3.sh deepseek`
  - 全部: `~/.openclaw/workspace/scripts/cdp-setup-v3.sh all`

### 图片分析

- **工具**: `~/.openclaw/workspace/skills/minimax-tools/minimax.py`
- **用法**: 
  ```bash
  python3 ~/.openclaw/workspace/skills/minimax-tools/minimax.py image "问题" "图片路径"
  ```
- **注意**: 输出为空时可能是用错工具了

### 经验教训目录

- **路径**: `~/.openclaw/workspace/.learnings/`
- **内容**:
  - `LEARNINGS.md` - 经验教训
  - `ERRORS.md` - 错误记录
  - `FEATURE_REQUESTS.md` - 功能请求
- **注意**: 不要放到 skill 目录下的 .learnings，要统一放到 workspace 根目录

### 查看 Markdown 文件

- **Skill**: mdview
- **用途**: 用浏览器打开 MD 文件，效果类似 GitHub
- **路径**: `~/.openclaw/workspace/skills/mdview/`
- **命令**: 
  ```bash
  python3 ~/.openclaw/workspace/tools/mdview.py <文件路径>
  ```
- **教训**: 2026-03-12 用错skill，直接用exec打开而非mdview

---

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.
