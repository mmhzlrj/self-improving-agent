
# Browser Relay 当前问题汇总

## 时间
2026-03-10 18:06

## 问题1：获取标签页 ✅ 已解决
- 切换到普通页面（非 chrome://）后正常工作

## 问题2：创建新标签页 ❌ 待排查
- HTTP POST 返回 404
- Gateway 只处理 /json/activate 和 /json/close
- 没有 /json/new 实现

## 问题3：HTTP /json 接口不完整
- GET /json ✅
- POST /json ❌ (404)
- 扩展使用 WebSocket，可能需要通过 WebSocket 发送命令

## 已验证
- Chrome 原生 CDP (9222) 正常工作
- Browser Relay 扩展连接正常
- 标签页列表获取正常（切换到普通页面后）

## 待测试
- 通过 WebSocket 发送 Target.createTarget 命令
