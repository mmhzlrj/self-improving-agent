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

**优先使用 MCP 工具**：
```python
import minimax_mcp.server as s
result = s.understand_image(
    prompt='问题内容',
    image_source='/tmp/图片路径.jpg'  # 参数名是 image_source，不是 image_url
)
# 需要设置环境变量: MINIMAX_API_KEY, MINIMAX_API_HOST
```

**备选 minimax.py**：
```bash
python3 ~/.openclaw/workspace/skills/minimax-tools/minimax.py image "问题" "图片路径"
```

**优先级**：
1. 先尝试 MCP 工具 `minimax_understand_image`（更稳定）
2. 如果失败（返回 "image sensitive" 或 "output sensitive"），再尝试 minimax.py
3. 图片路径从 `/tmp/` 目录获取（如 `/tmp/test_image*.jpg`）

**注意事项**：
- 输出为空时可能是用错工具了
- MiniMax API 会过滤敏感内容（返回 1026/1027 错误）

### Playwright API 参考

- **路径**: `~/.openclaw/workspace/skills/playwright-api/SKILL.md`
- **用途**: Playwright 完整 API 参考文档（500+ 方法），从源码提取
- **使用**: 需要用 Playwright 时先读此文档，找对 API 再执行

### 经验教训目录

- **Workspace 本地**: `~/.openclaw/workspace/.learnings/`
  - `LEARNINGS.md` - 经验教训
  - `ERRORS.md` - 错误记录
  - `FEATURE_REQUESTS.md` - 功能请求
- **self-improving-agent**: `~/.openclaw/workspace/skills/self-improving-agent/.learnings/`
  - 每次记录错误经验时，**必须同步更新**这两个地方的 ERRORS.md 和 LEARNINGS.md
  - 记录完成后分别 push 到各自 remote
  - **这条规则由 2026-03-28 教训总结而来：已两次忘记同步。**

### 查看 Markdown 文件

- **Skill**: mdview
- **用途**: 用浏览器打开 MD 文件，效果类似 GitHub
- **mdview.py 路径**: `~/.openclaw/workspace/tools/mdview.py`（不是 skills/mdview/ 下）
- **SKILL.md 路径**: `~/.openclaw/workspace/skills/mdview/SKILL.md`
- **命令**: 
  ```bash
  # 普通预览
  python3 ~/.openclaw/workspace/tools/mdview.py <文件路径>
  # 审批模式（带采纳/不采纳/备注按钮）
  python3 ~/.openclaw/workspace/tools/mdview.py --review <文件路径>
  ```
- **审批模式功能**：
  - 每个修改意见有 ✅采纳 / ❌拒绝 按钮
  - 备注栏可写审批意见
  - 顶部工具栏：全部采纳、重置、导出结果
  - 底部工具栏：导出 JSON 结果
  - 审批状态自动保存到浏览器本地存储
  - 导出的 JSON 包含每条的状态（approved/rejected/pending）和备注
- **读取审批结果**：
  ```bash
  # 自动检测（CDP → ~/Downloads）
  python3 ~/.openclaw/workspace/tools/read-review-results.py
  # 指定文件
  python3 ~/.openclaw/workspace/tools/read-review-results.py /path/to/results.json
  ```
  读取后自动保存到 `~/.openclaw/workspace/.review/review-results.json`
- **教训**: 2026-03-12 用错skill；2026-03-23 路径记错，mdview.py 在 tools/ 而非 skills/mdview/ 下
- **重要**：mdview 的 `preprocess_toc()` 把三级目录（`| | | 标题 |`格式）整体转成 HTML `<table>`，解决 Python markdown 库只认前2列丢内容的问题

### Git Push 失败处理

- **Skill**: git-auto-push
- **常见错误**: `Error in the HTTP2 framing layer`
- **立即修复**: `git -c http.version=HTTP/1.1 push`
- **详情**: `skills/git-auto-push/SKILL.md`

### Web Fetch 使用规范

- **禁止带 maxChars 参数**：如果 AI 给的命令包含 `(max XXX chars)`，必须去掉括号
- ✅ 正确：`web_fetch({ url: "https://..." })`
- ❌ 错误：`web_fetch({ url: "https://...", maxChars: 15000 })`
- 原因：限制字数会导致内容被截断或请求失败

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.
