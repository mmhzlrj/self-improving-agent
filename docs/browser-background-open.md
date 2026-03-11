
# 浏览器操作规范

## 在后台打开新标签页（不抢当前标签）

### 核心命令
```bash
osascript -e 'tell application "Google Chrome" to tell window 1 to set oldTab to active tab index' -e 'tell application "Google Chrome" to tell window 1 to make new tab with properties {URL:"URL"}' -e 'tell application "Google Chrome" to tell window 1 to set active tab index to oldTab'
```

### 三步逻辑
1. **记录当前标签页索引**：`set oldTab to active tab index`
2. **打开新标签页**：`make new tab with properties {URL:"..."}`
3. **切回原标签页**：`set active tab index to oldTab`

### 结果
- 新标签页在后台默默加载
- 当前屏幕视线仍然停留在当前页面
- 不会抢夺当前聊天标签

### 示例：打开豆包
```bash
osascript -e 'tell application "Google Chrome" to tell window 1 to set oldTab to active tab index' -e 'tell application "Google Chrome" to tell window 1 to make new tab with properties {URL:"https://www.doubao.com/chat/"}' -e 'tell application "Google Chrome" to tell window 1 to set active tab index to oldTab'
```

### 相关文件
- `/Users/lr/.openclaw/workspace/skills/rpa-automation/SKILL.md` - RPA 自动化技能
- `/Users/lr/.openclaw/workspace/SOUL.md` - 行为准则
