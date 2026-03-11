
# Browser Relay + 豆包 Skill 当前问题汇总

## 时间
2026-03-10 18:22

## 背景

### 1. 豆包 Skill 介绍
豆包 Skill 一开始就是为了打通 OpenClaw 和豆包网页版聊天才创建的。使用方式：

```bash
# 检查豆包标签页
browser(action=tabs, profile="chrome")

# 打开豆包
browser(action=open, profile="chrome", url="https://www.doubao.com/chat/")

# 聚焦输入框
browser(action=act, profile="chrome", request={
  "fn": "document.querySelector('div[role=\"textbox\"]')?.focus()",
  "kind": "evaluate"
})

# 输入文字
browser(action=act, profile="chrome", request={
  "fn": "document.execCommand('insertText', false, '问题')",
  "kind": "evaluate"
})

# 发送
browser(action=act, profile="chrome", request={"kind": "press", "key": "Enter"})

# 获取回答
browser(action=snapshot, profile="chrome")
```

### 2. Browser Relay 扩展
Browser Relay 扩展通过 CDP (Chrome DevTools Protocol) 控制浏览器。

---

## 当前问题

### 问题1：获取标签页 ✅ 已解决
- 切换到普通页面（非 chrome://）后正常工作

### 问题2：创建新标签页 ❌ 待排查
- HTTP POST /json 返回 404
- Gateway 只处理 /json/activate 和 /json/close
- 没有 /json/new 实现

### 问题3：HTTP /json 接口不完整
- GET /json ✅
- POST /json ❌ (404)
- 扩展使用 WebSocket，可能需要通过 WebSocket 发送命令

---

## 已验证事实

1. ✅ Chrome 原生 CDP (9222) 正常工作
2. ✅ Browser Relay 扩展连接正常
3. ✅ 标签页列表获取正常（切换到普通页面后）
4. ❌ 创建新标签页失败（返回 404）

---

## 待排查

1. 豆包 Skill 能否通过 Browser Relay 正常操作豆包网页版？
2. HTTP /json 接口不完整是否影响豆包 Skill 使用？
3. 是否需要通过 WebSocket 发送 CDP 命令？

---

## 相关文件
- `/Users/lr/.openclaw/workspace/skills/doubao-chat/SKILL.md` - 豆包 Skill 文档
- `/Users/lr/.openclaw/workspace/memory/browser-relay-debug-log.md` - 已过时
- `/Users/lr/.openclaw/workspace/memory/browser-relay-log-analysis.md` - 日志分析
- `/Users/lr/.openclaw/workspace/memory/browser-relay-fix-update.md` - 修复进展
- `/Users/lr/.openclaw/workspace/memory/browser-relay-target-create-analysis.md` - Target.createTarget 分析
