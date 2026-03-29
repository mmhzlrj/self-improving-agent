# OpenClaw 更新功能 → 0-1 机器人项目落地分析

> 基于版本 2026.3.8 ~ 2026.3.28 的 changelog，对照 0-1 项目各阶段需求

---

## 🎯 直接可用的新功能

### 1. OpenClaw 托管浏览器（2026.3.22 Breaking）
**对应需求：** AI Chat 工具集成、浏览器自动化
- ✅ **已在使用**：`openclaw browser --browser-profile openclaw start`（端口 18800）
- 移除了 Chrome 扩展 relay 路径，改为内置 CDP 直连
- **好处**：不需要折腾 Chrome 扩展加载，隔离的浏览器 profile 不会影响主 Chrome
- **注意**：`driver: "extension"` 和 `browser.relayBindHost` 已被移除

### 2. MiniMax 图片生成（2026.3.28）
**对应需求：** 0-1 视觉系统、表情生成、3D打印预览
- 新增 `image-01` 模型，支持图片生成和图片编辑
- 支持宽高比控制
- MiniMax 模型精简为仅 M2.7
- **用途**：
  - Phase 5（面部表情）：AI 生成表情素材
  - 3D 打印预览：生成概念图
  - 社交媒体内容：为小红书生成配图

### 3. MiniMax Fast Mode（2026.3.22）
**对应需求：** 减少响应延迟、节省 Coding Plan 配额
- `/fast` 命令映射到 MiniMax `-highspeed` 模型
- **用途**：简单问答、快速响应场景用高速模式，复杂任务用完整模型

### 4. Agent 默认超时 48h（2026.3.22）
**对应需求：** 长时间运行的 subagent 任务
- 从 600s 提升到 48h
- **用途**：FramePack 视频生成等长时间任务不再超时中断

### 5. 按模型限流（2026.3.28）
**对应需求：** MiniMax Coding Plan 配额管理
- 一个模型 429 不再阻塞所有模型
- 30s/1min/5min 阶梯限流
- **用途**：MiniMax 限流时可以自动 fallback 到 GLM 或其他模型

### 6. image tool fallback 修复（2026.3.28）
**对应需求：** ESP32-Cam 图片分析、Jetson Nano 视觉
- 恢复了 generic image-runtime fallback
- openrouter/minimax-portal 图片分析修复
- **用途**：用 MiniMax 或其他模型分析 ESP32-Cam 拍摄的照片

### 7. OpenAI apply_patch 默认启用（2026.3.28）
**对应需求：** subagent 代码编辑能力
- OpenAI 和 Codex 模型默认支持 patch 格式编辑
- **用途**：Codex subagent 编辑代码更高效

---

## 🔧 有用但需要配置的功能

### 8. SSH Sandbox 后端（2026.3.22）
**对应需求：** 远程管理 Jetson Nano、Ubuntu 节点
- 新增核心 SSH sandbox 后端，支持 secret-backed key/certificate
- **用途**：通过 SSH 安全地远程操作 Jetson Nano，执行代码、传输文件
- **配置**：需要配置 `sandbox.backend: "ssh"` + SSH 密钥

### 9. Gateway 健康监控（2026.3.22）
**对应需求：** 0-1 系统稳定性监控
- 可配置的 stale-event 阈值和重启限制
- 每通道/每账户独立控制
- **用途**：监控 OpenClaw Gateway 健康状态，自动检测和处理异常

### 10. Heartbeat 单次触发（2026.3.28）
**对应需求：** 定时任务调度
- 插件可调用 `runHeartbeatOnce` 触发单次心跳
- 支持显式 delivery target 覆盖
- **用途**：在 Hook 或插件中精确触发检查任务

### 11. Memory 多模态索引（2026.3.11）
**对应需求：** 视觉记忆系统
- Gemini `gemini-embedding-2-preview` 支持图片和音频索引
- **用途**：未来 0-1 机器人拍的照片可以自动索引到记忆系统

### 12. ACP resume session（2026.3.11）
**对应需求：** Codex/Claude 长任务持续
- `sessions_spawn` 支持 `resumeSessionId` 参数
- **用途**：长时间 coding 任务可以在中断后恢复

### 13. Memory 插件化（2026.3.28）
**对应需求：** 贵庚记忆系统定制
- memory flush 交给 memory-core 插件管理
- 插件可注册自定义 system-prompt section
- **用途**：可以为贵庚定制专用的记忆管理逻辑

### 14. Web 搜索工具增强（2026.3.22）
**对应需求：** 调研能力
- 新增 Exa、Tavily、Firecrawl 作为内置搜索插件
- **用途**：更丰富的搜索来源，特别是 Tavily 的 `tavily_extract` 可以抓取完整网页内容

---

## 📱 硬件/Node 相关

### 15. Android callLog.search（2026.3.22）
**对应需求：** iPhone 感知前端
- Android node 可以搜索通话记录
- **用途**：如果用 Android 手机作为感知前端，可以获取通话记录

### 16. Android sms.search（2026.3.22）
**对应需求：** iPhone 感知前端
- Android node 可以搜索短信
- **用途**：获取短信内容作为上下文

### 17. Node pending work queue（2026.3.11）
**对应需求：** Jetson Nano 等休眠节点的任务队列
- 新增 `node.pending.enqueue` / `node.pending.drain`
- **用途**：向离线/休眠的 node 发送任务，上线后自动执行

### 18. Gateway 冷启动优化（2026.3.22 多处）
**对应需求：** 系统启动速度
- Gateway 启动预热主模型
- 懒加载 channel 插件
- **用途**：MacBook 重启后 OpenClaw 更快可用

---

## 🐳 容器化部署

### 19. Podman 支持（2026.3.28）
**对应需求：** 客户设备快速部署
- 简化 rootless Podman 设置
- `openclaw --container ...` 在容器内运行命令
- **用途**：给客户设备一键部署 OpenClaw（不需要 Docker，用 Podman）

### 20. Kubernetes 支持（2026.3.12）
**对应需求：** 企业级部署
- 添加了 K8s 安装文档和 manifest
- **用途**：未来企业客户批量部署时可用

---

## ⚡ 建议优先升级的理由

| 优先级 | 理由 |
|--------|------|
| 🔴 高 | Agent 超时 48h → FramePack 等长任务不再中断 |
| 🔴 高 | 按模型限流 → MiniMax 限流不影响其他模型 |
| 🟡 中 | MiniMax 图片生成 → 表情系统素材生成 |
| 🟡 中 | 托管浏览器 → 不再依赖 Chrome 扩展（已手动解决） |
| 🟡 中 | image tool fallback → ESP32-Cam 图片分析 |
| 🟢 低 | SSH sandbox → 远程管理 Jetson（当前手动 SSH 够用） |
| 🟢 低 | Podman → 客户部署（当前还没到交付阶段） |

---

## ⚠️ 升级注意事项

1. **Chrome 扩展 relay 已移除**：`driver: "extension"` 被移除，但我们已经切换到 `openclaw` 托管浏览器，不受影响
2. **Qwen OAuth 迁移**：已废弃 `qwen-portal-auth`，但我们的 Qwen 用的是 webauth MCP（直接控制网页），不受影响
3. **image tool 变更**：`nano-banana-pro` skill 被移除，但我们的 MiniMax MCP 是独立实现
4. **插件 SDK 变更**：`openclaw/extension-api` 被移除，我们的自定义扩展（webauth-mcp 等）用的是 `@modelcontextprotocol/sdk`，不受影响
