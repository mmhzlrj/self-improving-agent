# OpenClaw 更新功能 → 0-1 机器人项目落地详细分析

> 基于版本 2026.3.8 ~ 2026.3.28 的 changelog（含 gh api 原始 release notes），对照 0-1 项目 Phase 0-6+ 各阶段技术需求，逐阶段分析可用功能和配置方法。
>
> 文档版本：v1.0
> 生成日期：2026-03-29
> 信息来源：gh api release notes（v2026.3.8/11/12/22/23/24/28）+ ROBOT-SOP.md Phase 0-6+

---

## 目录

- [Phase 0：Ubuntu 台式机对接 Gateway](#phase-0ubuntu-台式机对接-gateway)
- [Phase 1：语音陪伴模块](#phase-1语音陪伴模块)
- [Phase 2：视觉记录模块（ESP32-Cam）](#phase-2视觉记录模块esp32-cam)
- [Phase 3：iPhone 感知前端](#phase-3iphone-感知前端)
- [Phase 4：运动控制模块](#phase-4运动控制模块)
- [Phase 5：面部表情系统](#phase-5面部表情系统)
- [Phase 6：室内移动与智能家居硬件拓展](#phase-6室内移动与智能家居硬件拓展)
- [跨 Phase 通用能力](#跨-phase-通用能力)
- [升级优先级建议](#升级优先级建议)

---

## Phase 0：Ubuntu 台式机对接 Gateway

### 阶段需求
- Ubuntu 节点（5600G+RTX 2060）通过 OpenClaw Node 协议连接 Mac Gateway
- 节点发现 → 配对 → 执行链路跑通
- GPU 任务默认路由到该节点

### 可用 OpenClaw 功能

#### 1. SSH Sandbox 后端（2026.3.22）
**具体用途**：通过 SSH 安全地远程操作 Jetson Nano，执行代码、传输文件
- 新增核心 SSH sandbox 后端，支持 secret-backed key/certificate
- 替代直接 SSH 命令执行，提供更安全的隔离环境
- **对 Phase 0 的价值**：Ubuntu GPU 节点可通过 SSH sandbox 后端安全接入，无需直接在主机上运行命令

**配置方法**：
```bash
# 在 openclaw.json 中配置
{
  "sandbox": {
    "backend": "ssh",
    "ssh": {
      "target": "ubuntu-gpu-node",
      "host": "192.168.x.x",
      "user": "nvidia",
      "auth": "key"
    }
  }
}
```

#### 2. 设备配对安全升级（2026.3.22 Breaking）
**具体用途**：设备 pairing 改用短效 bootstrap token，不再在 QR 码中嵌入共享 gateway 凭证
- **安全性大幅提升**：旧版 /pair 和 openclaw qr 的 setup codes 含共享凭证，有被盗用风险
- 新版 token 有时效性，过期自动作废
- **对 Phase 0 的价值**：Ubuntu 节点配对到 Gateway 时更安全

#### 3. Gateway/WebSocket 安全加固（2026.3.28）
**具体用途**：browser origin 验证，防止跨站 WebSocket 劫持
- 即使在 trusted-proxy 模式下也会验证 origin，防止恶意网页获取 operator.admin 权限
- **对 Phase 0 的价值**：Ubuntu 节点连接 Gateway 时的通信安全有保障

#### 4. Node pending work queue（2026.3.11）
**具体用途**：休眠节点的任务队列
- `node.pending.enqueue` / `node.pending.drain`
- 向离线/休眠的节点发送任务，上线后自动执行
- **对 Phase 0 的价值**：Ubuntu 节点在睡眠/休眠后，积累的任务可自动恢复执行

#### 5. sessions_yield（2026.3.12）
**具体用途**：subagent 可主动结束当前轮次
- 编排器可立即结束当前轮次，跳过排队的工具工作
- **对 Phase 0 的价值**：Ubuntu GPU 节点的长任务（如 YOLO TensorRT 编译）可分段 yield，不阻塞主会话

---

## Phase 1：语音陪伴模块

### 阶段需求
- 麦克风 → Whisper 语音识别 → OpenClaw → Edge-TTS → 扬声器
- 跑通"数字大脑→Cyber Bricks"的第一次物理输出
- 语音延迟要低（实时对话体验）

### 可用 OpenClaw 功能

#### 1. Fast Mode /fast 命令（2026.3.22）
**具体用途**：简单问答/快速响应场景用高速模型
- `/fast` 映射到 MiniMax `-highspeed` 模型
- 延迟大幅降低，适合语音对话的快速确认场景
- **对 Phase 1 的价值**：语音交互的确认回复（"好的"/"收到"）用 fast mode，节省延迟

**配置方法**：
```bash
# 启用 fast 模式
openclaw config set models.default.fastModel "minimax/highspeed"
# 使用时：/fast
```

#### 2. Per-Model Cooldowns 阶梯限流（2026.3.24/28）
**具体用途**：一个模型 429 不再阻塞所有模型
- 30s/1min/5min 阶梯限流
- MiniMax 限流时可以自动 fallback 到 GLM/Qwen
- **对 Phase 1 的价值**：语音对话中主模型限流时，fallback 模型自动接管，不中断对话

**配置方法**：
```bash
# 配置 fallback 模型链
openclaw config set models.fallback["minimax"] "glm-4-plus"
openclaw config set models.fallback["glm-4-plus"] "qwen-plus"
```

#### 3. MCP/Channels Bridge（2026.3.11）
**具体用途**：Gateway-backed channel MCP bridge
- Codex/Claude-facing conversation tools
- Claude channel notifications
- **对 Phase 1 的价值**：用 MCP 协议桥接 Jetson Nano 上的语音处理模块

#### 4. before_dispatch Hook（2026.3.11/23）
**具体用途**：在消息 dispatch 之前插入自定义逻辑
- 可用于语音命令的预处理（如降噪级别判断、唤醒词检测）
- canonical inbound metadata 可访问
- **对 Phase 1 的价值**：在语音命令进入 AI 前，先判断是否需要触发物理动作

#### 5. exec Overlay + before_tool_call requireApproval（2026.3.28）
**具体用途**：工具执行前需要用户审批
- `before_tool_call` hooks 可暂停工具执行，提示用户审批
- 支持 exec overlay、Telegram 按钮、Discord 交互、/approve 命令
- **对 Phase 1 的价值**：语音控制 Cyber Bricks 动作时，可设置审批确认（防止误触发）

**配置方法**：
```javascript
// plugins/phase1-voice-approval/index.js
module.exports = {
  before_tool_call: async ({ toolName, params, context }) => {
    if (toolName === 'exec' && params.command?.includes('cyberbrick')) {
      return { requireApproval: true };
    }
  }
};
```

#### 6. runHeartbeatOnce（2026.3.28）
**具体用途**：插件可触发单次心跳
- `runHeartbeatOnce` 可精确触发检查任务
- 支持显式 delivery target 覆盖
- **对 Phase 1 的价值**：语音交互时，触发定时器检查（如：超时提醒）

---

## Phase 2：视觉记录模块（ESP32-Cam）

### 阶段需求
- ESP32-Cam 采集 → RTSP 流 → Jetson Nano 处理
- AI 理解画面内容（目标检测/人体姿态）
- 本地处理不传云端

### 可用 OpenClaw 功能

#### 1. Image Tool Generic Fallback 修复（2026.3.22/24）
**具体用途**：ESP32-Cam 拍摄的照片可被 MiniMax/OpenRouter 分析
- 恢复了 generic image-runtime fallback
- openrouter/minimax-portal 图片分析修复
- **对 Phase 2 的价值**：用 MiniMax M2.7 分析 ESP32-Cam 的 RTSP 截帧，无需担心 provider 缺失

**配置方法**：无需额外配置，已默认启用（2026.3.24 已修复）

#### 2. MCP/Channels Bridge（2026.3.11）
**具体用途**：将 Jetson Nano 的视觉处理结果通过 MCP 传回 Gateway
- 为 Jetson Nano 上的 YOLO/MediaPipe 推理结果建立标准化通道
- **对 Phase 2 的价值**：视觉检测结果（物体类别/bounding box/人体关键点）可结构化传回贵庚

#### 3. Gemini Multimodal Embedding（2026.3.11）
**具体用途**：图片和音频的向量索引
- `gemini-embedding-2-preview` 支持图片和音频索引
- `memorySearch.extraPaths` 支持多模态索引
- **对 Phase 2 的价值**：ESP32-Cam 录像的关键帧自动索引到记忆系统，未来可检索"上次看到这个物体是什么时候"

**配置方法**：
```bash
# 在 memory 配置中启用
openclaw config set memory.search.provider "gemini"
openclaw config set memory.search.gemini.embeddingModel "gemini-embedding-2-preview"
openclaw config set memory.search.extraPaths ["/path/to/esp32-frames"]
```

#### 4. MiniMax 图片生成（2026.3.28）
**具体用途**：为 Phase 5 面部表情系统生成素材
- `image-01` 模型支持图片生成和图片编辑
- 支持宽高比控制
- **对 Phase 2 的价值**：间接——生成测试用仿真图像用于 YOLO 模型测试

#### 5. Memory Plugins 化（2026.3.28）
**具体用途**：记忆 flush 交给 memory-core 插件管理
- 插件可注册自定义 system-prompt section
- **对 Phase 2 的价值**：ESP32-Cam 采集的视觉事件可定制为独立的 memory 插件，自动写入 NAS

---

## Phase 3：iPhone 感知前端

### 阶段需求
- iPhone 16 Pro 通过 OpenClaw Node 协议接入，成为分布式感知网络
- 高质量视觉（LiDAR/摄像头）、传感器数据（IMU/UWB）
- 室内移动时无缝切换

### 可用 OpenClaw 功能

#### 1. Node Pending Work Queue（2026.3.11）⭐⭐⭐⭐⭐
**具体用途**：Jetson Nano 等休眠节点的任务队列
- `node.pending.enqueue` / `node.pending.drain`
- 向离线/休眠的 iPhone Node 发送任务，上线后自动执行
- **对 Phase 3 的价值**：iPhone 移动时网络切换，旧任务缓存，新任务排队，切换完成后自动 drain

**配置方法**：
```javascript
// 向 iPhone 节点发送任务
await openclaw.node.pending.enqueue({
  nodeId: "iphone-16-pro",
  task: { type: "capture", params: { resolution: "high" } },
  expiresIn: "5m"
});

// iPhone 重新连接时自动 drain
const tasks = await openclaw.node.pending.drain("iphone-16-pro");
```

#### 2. MCP/Channels Bridge（2026.3.11）
**具体用途**：iPhone（Swift + ARKit）通过 MCP 与 Jetson Nano/ROS 2 桥接
- WebSocket 传输，标准化接口
- **对 Phase 3 的价值**：替代自定义 rosbridge JSON 协议，用原生 MCP 通信

#### 3. ACP Current-Conversation Bind（2026.3.28）
**具体用途**：当前对话 ACP 绑定（Discord/BlueBubbles/iMessage）
- `/acp spawn codex --bind here` 可将当前聊天转为 Codex 工作区
- **对 Phase 3 的价值**：iPhone 上的对话可无缝切换到 Codex subagent 处理复杂视觉分析

#### 4. before_dispatch Hook（2026.3.11/23）
**具体用途**：iPhone 传感器数据的预处理
- IMU 数据到达 Gateway 前可做过滤/聚合
- **对 Phase 3 的价值**：减少无效传感器数据的处理开销

#### 5. sessions_yield + Resume（2026.3.11/12）
**具体用途**：iPhone 发起的视觉分析任务可中断恢复
- `sessions_spawn` 支持 `resumeSessionId` 参数
- **对 Phase 3 的价值**：iPhone 拍摄的长视频分析可分段进行，中途网络切换自动恢复

#### 6. ACP Sessions Resume（2026.3.11）
**具体用途**：Codex/Claude 长任务持续
- 已有 ACP session 可 resume，不从头开始
- **对 Phase 3 的价值**：iPhone 侧的复杂场景理解任务（如：分析整个室内环境）可跨会话恢复

---

## Phase 4：运动控制模块

### 阶段需求
- OpenClaw Gateway → MQTT → Jetson Nano → UART → Cyber Bricks
- GPIO 应急停止（<1ms）
- 电机/舵机执行物理动作

### 可用 OpenClaw 功能

#### 1. before_tool_call requireApproval + exec Overlay（2026.3.28）⭐⭐⭐⭐⭐
**具体用途**：Cyber Bricks 动作执行前需要用户审批
- 插件可暂停工具执行，弹出审批 UI
- 支持 Telegram 按钮、Discord 交互、/approve 命令
- **对 Phase 4 的价值**：最关键功能！语音命令触发运动前，必须经过审批，防止误触发危险动作（如机械臂撞人）

**配置方法**：
```javascript
// openclaw.json plugins 配置
{
  "plugins": {
    "entries": {
      "cyberbrick-approval": {
        "enabled": true
      }
    }
  }
}

// 对应插件代码（伪代码）
const cyberbrickApproval = {
  before_tool_call: async ({ toolName, params }) => {
    if (toolName === 'exec' && isCyberbrickCommand(params.command)) {
      return { requireApproval: true };
    }
  }
};
```

#### 2. before_dispatch Hook（2026.3.11/23）
**具体用途**：MQTT 命令发出前的拦截
- 判断是否是危险动作（高速/大幅度），是则 requireApproval
- **对 Phase 4 的价值**：在 exec 之前就拦截，不需要等到具体命令执行

#### 3. runHeartbeatOnce（2026.3.28）
**具体用途**：定期检查 Cyber Bricks 状态
- 插件可触发单次心跳，检查执行器状态
- **对 Phase 4 的价值**：无需等待用户查询，定时检查电机温度/位置是否正常

**配置方法**：
```javascript
// 定期检查 Cyber Bricks 状态
setInterval(async () => {
  await openclaw.runHeartbeatOnce({ target: "cyberbrick-monitor" });
}, 60000); // 每分钟一次
```

#### 4. Gateway Health Monitoring（2026.3.22）
**具体用途**：系统稳定性监控
- 可配置的 stale-event 阈值和重启限制
- 每通道/每账户独立控制
- **对 Phase 4 的价值**：监控 MQTT 连接健康状态，Jetson Nano 断连时自动告警

**配置方法**：
```bash
openclaw config set gateway.health.staleEventThreshold 30000  # 30秒无响应则告警
openclaw config set gateway.health.restartLimit 3  # 最多重启3次
```

#### 5. ACP Direct Chats（2026.3.28）
**具体用途**：TTS 回复在无音频时也发送最终 ACP 结果
- ACP 结果 delivery 保证
- **对 Phase 4 的价值**：Cyber Bricks 执行结果的确认消息不丢失

---

## Phase 5：面部表情系统

### 阶段需求
- 面部「0」「-」「1」三个元素
- NeoPixel 灯光带 + OLED 眼睛屏幕
- MQTT 接收表情指令

### 可用 OpenClaw 功能

#### 1. MiniMax 图片生成（2026.3.28）⭐⭐⭐⭐⭐
**具体用途**：AI 生成表情素材
- `image-01` 模型支持图片生成和图片编辑
- 支持宽高比控制（方形/16:9/9:16）
- **对 Phase 5 的价值**：
  - 生成「0」眼睛的眨眼动画帧（生成后转 GIF）
  - 为不同情绪状态生成概念图（happy/sad/alert）
  - 生成 3D 打印预览概念图

**配置方法**：
```javascript
// 调用 MiniMax 图片生成
const result = await openclaw.minimax.generateImage({
  model: "image-01",
  prompt: "A cute robot face showing '0-1' expression, digital art style, square format",
  aspectRatio: "1:1"
});
```

#### 2. MiniMax 图片编辑（2026.3.28）
**具体用途**：在已有素材上编辑
- image-to-image 编辑能力
- **对 Phase 5 的价值**：在基础表情图上微调（换颜色/表情细节），不用每次从头生成

#### 3. NeoPixel / Matrix TTS 语音气泡（2026.3.28）
**具体用途**：Matrix 语音消息改为原生语音气泡
- **对 Phase 5 的价值**：参考——语音气泡 UI 设计可借鉴到面部表情系统

#### 4. before_tool_call requireApproval（2026.3.28）
**具体用途**：表情切换审批
- 某些特殊表情（alert/emergency）需要确认才切换
- **对 Phase 5 的价值**：防止误触发吓人的表情

---

## Phase 6：室内移动与智能家居硬件拓展

### 阶段需求
- 室内自主导航（RGB-D SLAM/视觉）
- IoT 控制（HomeAssistant/米家）
- 星闪通信模块（BearPi-Pico H3863）
- 拓竹生态扩展

### 可用 OpenClaw 功能

#### 1. Tavily / Exa / Firecrawl 搜索插件（2026.3.22）⭐⭐⭐⭐⭐
**具体用途**：更丰富的搜索来源
- Tavily：结构化搜索结果，带 `tavily_extract` 抓取完整网页
- Exa：语义搜索，支持网页内容提取
- Firecrawl：整站抓取，适合调研智能家居设备规格
- **对 Phase 6 的价值**：
  - 调研 HomeAssistant 集成方案时快速获取官方文档
  - 拓竹 H2C 参数问题直接抓取官方规格表
  - 调研 H3863 星闪模块技术规格

**配置方法**：
```bash
# 安装 Tavily 插件
openclaw plugins install tavily
# 配置 API key
openclaw config set plugins.tavily.apiKey "tvly-xxx"

# 使用搜索
/open tavily what's new in HomeAssistant 2026
```

#### 2. Gateway/OpenAI 兼容性（2026.3.23/24）
**具体用途**：`/v1/models` 和 `/v1/embeddings` 接口
- RAG 兼容性大幅提升
- **对 Phase 6 的价值**：Jetson Nano 上的本地 embedding 服务可接入 OpenClaw 的 RAG pipeline

#### 3. MCP/Channels Bridge（2026.3.11）
**具体用途**：连接 HomeAssistant 的 MCP 接口
- HomeAssistant 已支持 MCP 协议（2025年底新特性）
- **对 Phase 6 的价值**：用 MCP 而非 MQTT 更标准化

#### 4. Podman 容器支持（2026.3.24/28）
**具体用途**：客户设备快速部署
- 简化 rootless Podman 设置
- `openclaw --container <name> ...` 在容器内运行命令
- **对 Phase 6 的价值**：给客户部署时，HomeAssistant + OpenClaw 可打包为 Podman 容器，一键部署

**配置方法**：
```bash
# 在客户设备上
podman pull openclaw/openclaw:latest
openclaw --container openclaw-01 run
```

#### 5. Kubernetes 支持（2026.3.12）
**具体用途**：企业级/多节点部署
- K8s manifest + Kind 安装文档
- **对 Phase 6 的价值**：未来多台机器人协同时，可用 K8s 统一管理多个 OpenClaw 实例

#### 6. Gemini CLI Backend（2026.3.28）
**具体用途**：新增 Gemini CLI 后端
- 替代 `gateway run --claude-cli-logs` 为通用 `--cli-backend-logs`
- **对 Phase 6 的价值**：在 Jetson Nano 上用 Gemini CLI 做本地推理，与 OpenClaw 集成

#### 7. Memory Plugins 化（2026.3.28）
**具体用途**：贵庚记忆系统定制
- memory flush 交给 memory-core 插件管理
- 插件可注册自定义 system-prompt section
- **对 Phase 6 的价值**：IoT 设备状态（灯光/门锁/温度）可写入贵庚记忆，未来可检索"上次关灯是什么时候"

---

## 跨 Phase 通用能力

### 安全相关

#### 1. 设备 Pairing Token 安全（2026.3.22）
**具体用途**：短效 bootstrap token 替代永久凭证
- /pair 和 QR 码不再嵌入共享 gateway 凭证
- token 有时效性，过期作废
- **对所有 Phase 的价值**：0-1 机器人的节点配对不会被中间人攻击

#### 2. Browser Profile 安全隔离（2026.3.22 Breaking）
**具体用途**：托管浏览器使用独立 profile
- `driver: "extension"` 已被移除，改为内置 CDP 直连
- **对所有 Phase 的价值**：自动化测试和手动浏览完全隔离，不会互相影响

#### 3. Security WebSocket Origin 验证（2026.3.28）
**具体用途**：防止跨站 WebSocket 劫持
- **对所有 Phase 的价值**：Gateway 暴露在公网时，防止恶意网页劫持 session

#### 4. Security Exec Approvals（2026.3.8~28 多处修复）
**具体用途**：命令执行安全
- 零宽字符/Unicode 格式字符检测防止欺骗
- 路径遍历防护
- **对所有 Phase 的价值**：防止通过语音命令注入恶意指令

### Agent / Subagent 相关

#### 5. Agent 超时 48h（2026.3.22）
**具体用途**：长时间运行的 subagent 任务不再超时
- 从 600s 提升到 48h
- **对所有 Phase 的价值**：FramePack 视频生成、YOLO 训练等长任务不中断

#### 6. sessions_yield（2026.3.12）
**具体用途**：编排器主动结束当前轮次
- **对所有 Phase 的价值**：主 agent 派发子任务后主动 yield，子任务完成后主动汇报

#### 7. ACP Resume Session（2026.3.11）
**具体用途**：已有 ACP session 可 resume
- `sessions_spawn` 支持 `resumeSessionId`
- **对所有 Phase 的价值**：长对话跨节点切换不丢上下文

#### 8. Subagent Completion Announce（2026.3.24）
**具体用途**：subagent 完成通知扩展到 extension channels
- BlueBubbles 等渠道也能收到完成通知
- **对所有 Phase 的价值**：跨渠道（飞书/Telegram）控制机器人，完成后多渠道确认

### Memory / Context 相关

#### 9. Memory Multimodal Indexing（2026.3.11）
**具体用途**：Gemini embedding-2 支持图片和音频索引
- **对所有 Phase 的价值**：0-1 积累的所有媒体类型（图片/语音/视频）都可索引检索

#### 10. Memory Plugins 化（2026.3.28）
**具体用途**：记忆 flush 交给插件管理
- **对所有 Phase 的价值**：贵庚记忆系统可作为独立插件，定制 flush 策略（何时写入 NAS）

#### 11. Compact Preserved AGENTS 刷新（2026.3.24/28）
**具体用途**：压缩后保留 AGENTS 刷新
- stale-usage 预压缩也保留
- **对所有 Phase 的价值**：对话历史压缩时不忘刷新 AGENTS.md，保持上下文一致

### 网络 / 通信相关

#### 12. Node Pending Work Queue（2026.3.11）
**具体用途**：休眠节点任务队列
- `node.pending.enqueue` / `node.pending.drain`
- **对所有 Phase 的价值**：任何节点（Jetson/iPhone/ESP32）休眠时任务自动排队

#### 13. Gateway Health Monitoring（2026.3.22）
**具体用途**：Gateway 健康检查 + 自动重启限制
- **对所有 Phase 的价值**：Mac Gateway 异常崩溃后自动恢复，0-1 不失联

#### 14. Per-Model Cooldowns（2026.3.24/28）
**具体用途**：按模型限流
- 30s/1min/5min 阶梯
- **对所有 Phase 的价值**：MiniMax 限流时 GLM/Qwen 自动接管，不影响 0-1 实时响应

#### 15. Heartbeat Guaranteed（2026.3.28）
**具体用途**：心跳定时器在异常后保证重启
- **对所有 Phase 的价值**：定时检查（电池/温度/传感器状态）不再静默停止

### MCP / 插件相关

#### 16. MCP/Channels Bridge（2026.3.11）
**具体用途**：Gateway-backed MCP bridge
- Codex/Claude-facing conversation tools
- safer stdio bridge lifecycle
- **对所有 Phase 的价值**：Jetson Nano/iPhone/ESP32 都可通过 MCP 接入，标准化接口

#### 17. before_dispatch Hook（2026.3.11/23）
**具体用途**：dispatch 前的拦截
- canonical inbound metadata
- **对所有 Phase 的价值**：消息路由前可做过滤/审批/日志

#### 18. before_tool_call requireApproval（2026.3.28）
**具体用途**：工具执行前审批
- exec overlay / Telegram 按钮 / Discord 交互 / /approve
- **对所有 Phase 的价值**：任何危险操作（运动/删除/外发消息）都需确认

### 搜索 / 调研相关

#### 19. Tavily / Exa / Firecrawl 内置搜索（2026.3.22）
**具体用途**：丰富搜索来源
- Tavily：`X-Client-Source: openclaw` 标识
- **对所有 Phase 的价值**：调研智能家居方案/机器人技术时快速获取准确信息

### 调试 / 诊断相关

#### 20. /tools 命令（2026.3.23）
**具体用途**：显示当前可用工具
- Control UI 新增 "Available Right Now" 区域
- **对所有 Phase 的价值**：开发阶段快速确认哪些工具可用

#### 21. Control UI Improvements（2026.3.23/24）
**具体用途**：Agent 工作区文件支持展开和 markdown 预览
- **对所有 Phase 的价值**：调试 Phase 4/5/6 的控制脚本时直接在 UI 预览

#### 22. openclaw config schema（2026.3.28）
**具体用途**：打印 JSON schema
- **对所有 Phase 的价值**：开发插件时快速查配置项结构

---

## 升级优先级建议

### 🔴 P0（立即升级，高优先级）

| 功能 | 原因 | 影响 Phase |
|------|------|-----------|
| **Agent 超时 48h** | FramePack 视频生成等长任务不再中断 | Phase 2, 3 |
| **Per-Model Cooldowns** | MiniMax 限流不影响其他模型，实时响应不中断 | Phase 1, 2, 3, 4 |
| **before_tool_call requireApproval** | Phase 4 运动控制安全的关键保障 | Phase 4 |
| **Node Pending Work Queue** | iPhone/Jetson 休眠恢复的核心机制 | Phase 3 |
| **Memory Multimodal Indexing** | ESP32-Cam 视觉记录索引，Phase 2 核心 | Phase 2 |

### 🟡 P1（近期升级，中优先级）

| 功能 | 原因 | 影响 Phase |
|------|------|-----------|
| **runHeartbeatOnce** | 定期检查 Cyber Bricks 状态，Phase 4 稳定运行 | Phase 4 |
| **ACP Resume Session** | iPhone 移动切换不丢上下文 | Phase 3 |
| **sessions_yield** | 编排器主动控制轮次，子任务管理更灵活 | Phase 3, 4 |
| **MiniMax Image Generation** | Phase 5 表情素材生成 | Phase 5 |
| **Tavily/Exa/Firecrawl 搜索** | 调研拓竹/H3863/智能家居规格 | Phase 6 |
| **Gateway Health Monitoring** | 系统稳定性监控，Mac 重启后自动恢复 | Phase 4, 6 |

### 🟢 P2（后续升级，低优先级）

| 功能 | 原因 | 影响 Phase |
|------|------|-----------|
| **SSH Sandbox Backend** | 远程管理 Jetson Nano（当前手动 SSH 够用）| Phase 0 |
| **Podman 容器支持** | 客户部署（当前还没到交付阶段）| Phase 6 |
| **Kubernetes 支持** | 企业级多节点（当前单节点够用）| Phase 6 |
| **Gemini CLI Backend** | 本地推理备选（当前 MiniMax 够用）| Phase 6 |
| **MCP/Channels Bridge** | Jetson/iPhone 标准化接入（Phase 3 中已有替代方案）| Phase 3 |
| **Memory Plugins** | 贵庚定制（Phase 1 日志式够用）| 全部 |

### ⚠️ 升级注意事项

1. **Chrome 扩展 relay 已移除**（2026.3.22 Breaking）：`driver: "extension"` 被移除，但我们已切换到 `openclaw` 托管浏览器，不受影响
2. **Qwen OAuth 迁移**（2026.3.28 Breaking）：已废弃 `qwen-portal-auth`，我们的 Qwen 用的是 webauth MCP，不受影响
3. **Config Doctor 迁移校验**（2026.3.28 Breaking）：两个月前的 legacy key 现在会验证失败，`openclaw doctor` 检查一下现有配置
4. **Node 22 最低版本**（2026.3.23）：需 Node 22.14+，确认 Jetson Nano 上的 Node 版本

---

## 功能 × Phase 矩阵汇总

| 功能 | P0 | P1 | P2 | P3 | P4 | P5 | P6 |
|------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| SSH Sandbox Backend | ✅ | | | | | | |
| Device Pairing Token 安全 | ✅ | | | | | | |
| Agent 超时 48h | 🔴 | | | ✅ | | | |
| Per-Model Cooldowns | 🔴 | | | ✅ | ✅ | | |
| before_tool_call requireApproval | | 🔴 | | | | ✅ | |
| Node Pending Work Queue | 🔴 | | | | | | |
| Memory Multimodal Indexing | 🔴 | | | | | | |
| runHeartbeatOnce | | 🟡 | | | ✅ | | |
| ACP Resume Session | | 🟡 | | | | | |
| sessions_yield | | 🟡 | | ✅ | | | |
| MiniMax Image Generation | | 🟡 | | | | ✅ | |
| Tavily/Exa/Firecrawl | | 🟡 | | | | | ✅ |
| Gateway Health Monitoring | | 🟡 | | | ✅ | | ✅ |
| Image Tool Fallback 修复 | ✅ | | | | | | |
| MCP/Channels Bridge | | | 🟢 | ✅ | | | ✅ |
| Podman 支持 | | | 🟢 | | | | ✅ |
| Kubernetes 支持 | | | 🟢 | | | | ✅ |
| Memory Plugins | | | 🟢 | | | | ✅ |
| Gemini CLI Backend | | | 🟢 | | | | ✅ |
| ACP Current-Conversation Bind | | | 🟢 | ✅ | | | |
| /tools 命令 | | | 🟢 | | | | |
| OpenAI apply_patch 默认 | | | 🟢 | | | | |

---

> 📝 **生成说明**：本分析基于 gh api 获取的原始 release notes（v2026.3.8/11/12/22/23/24/28）和 ROBOT-SOP.md Phase 0-6+ 章节。v2026.3.13 版本在 GitHub 上未找到（404），可能尚未发布或标签名称不同。如需补充该版本内容，请访问 https://github.com/openclaw/openclaw/releases 手动查看。
