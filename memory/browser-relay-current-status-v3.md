
# Browser Relay 当前问题汇总

## 时间
2026-03-10 18:17

## 背景
Browser Relay 扩展一开始就是为了打通 OpenClaw 和豆包网页版聊天才创建的。

## 问题1：获取标签页 ✅ 已解决
- 切换到普通页面（非 chrome://）后正常工作

## 问题2：创建新标签页 ❌ 待排查
- HTTP POST 返回 404
- Gateway 只处理 /json/activate 和 /json/close
- 没有 /json/new 实现

## 问题3：HTTP /json 接口不完整
- GET /json ✅
- POST /json ❌ (404)

## 已验证
- Chrome 原生 CDP (9222) 正常工作
- Browser Relay 扩展连接正常
- 标签页列表获取正常（切换到普通页面后）

## 待测试
- 通过 WebSocket 发送 Target.createTarget 命令
- 豆包 skill 能否通过 Browser Relay 正常操作豆包网页版

## 相关文件
- `/Users/lr/.openclaw/workspace/memory/browser-relay-debug-log.md` - 已过时
- `/Users/lr/.openclaw/workspace/memory/browser-relay-log-analysis.md` - 日志分析
- `/Users/lr/.openclaw/workspace/memory/browser-relay-fix-update.md` - 修复进展
- `/Users/lr/.openclaw/workspace/memory/browser-relay-target-create-analysis.md` - Target.createTarget 分析
