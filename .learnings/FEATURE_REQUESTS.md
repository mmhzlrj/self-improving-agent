# FEATURE_REQUESTS.md - 功能请求

> 记录用户请求的功能和能力，作为待实现清单。

---

## 豆包对话 Skill（已实现）

- **Status**: done
- **实现日期**: 2026-03-11

### 请求内容
- 无需 API Key 调用豆包网页版
- 默认使用"专家"模式

### 实现方案
- 使用 Browser Relay + CSS 选择器
- 零窗口跳动

---

## 小程序自动化（待实现）

- **Status**: pending

### 请求内容
- 微信/支付宝小程序自动化
- 需要能够操作小程序界面

### 复杂度 Estimate
- complex
- 需要深入研究小程序技术架构

---

## P2P 跨网络连接（进行中）

- **Status**: in_progress

### 请求内容
- 小龙虾 P2P 跨网络连接
- 需要 IPv6 或中继方案

### 相关文件
- `~/.openclaw/workspace/skills/lobster-p2p/`

## 2026-03-19

### Chrome 调试端口开机自启
- 当前手动启动，开机后需重新运行 Chrome 调试
- 考虑用 launchd 或自启动脚本

### Qwen parent_id 状态管理
- 当前方案：每次调用新建 chat，避免 parent_id 维护
- 如需多轮对话上下文：需要管理 parent_id 和消息历史
