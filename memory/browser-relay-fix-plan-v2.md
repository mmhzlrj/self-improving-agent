
# Browser Relay + 豆包 Skill 修复计划

## 核心目标
让豆包 Skill 通过 Browser Relay 稳定操控豆包网页版

## 当前状态

| 状态 | 问题/事实 | 影响程度 |
|------------|---------------------------------------------------------------------------|----------------|
| ✅ 已解决 | 获取标签页（切换至普通页面后正常）| 无阻断 |
| ❌ 阻断性 | 创建新标签页失败（POST /json 404）| 高 |
| ❌ 关键适配 | HTTP /json接口不完整，扩展底层依赖WebSocket+CDP协议 | 高 |
| ❓ 待验证 | 豆包Skill核心操作能否通过WebSocket+CDP正常执行 | 核心 |

---

## 下一步行动

### 阶段1：紧急验证（高优先级）

**目标**：在手动打开的豆包标签页下，通过 WebSocket + CDP 完成 Skill 核心操作

**需要验证的 CDP 命令**：

| 原 Skill 操作 | 对应 CDP 命令 |
|---------------|---------------|
| 聚焦输入框 | `Runtime.evaluate` + `{"expression": "document.querySelector('div[role=\"textbox\"]')?.focus()"}` |
| 输入文字 | `Runtime.evaluate` + `{"expression": "document.execCommand('insertText', false, '测试问题')"}` |
| 发送消息 | `Input.dispatchKeyEvent` + `{"type": "keyDown", "key": "Enter"}` + `{"type": "keyUp", "key": "Enter"}` |
| 获取回答 | `Page.captureSnapshot` 或 `Runtime.evaluate` 抓取 DOM |

**步骤**：
1. 找到 Browser Relay 的 CDP WebSocket 端点
2. 通过 WebSocket 发送 CDP 命令
3. 验证结果

---

### 阶段2：解决创建新标签页问题

**目标**：通过 WebSocket 调用 CDP 的 `Target.createTarget`

### 阶段3：适配豆包 Skill 调用逻辑

**目标**：将 Skill 中基于 HTTP 的 browser action 调用改造为基于 WebSocket 的 CDP 命令

### 阶段4：闭环验证与优化

---

## 相关文件
- `/Users/lr/.openclaw/workspace/skills/doubao-chat/SKILL.md` - 豆包 Skill
- `/Users/lr/.openclaw/workspace/memory/browser-relay-debug-log.md` - 已过时
