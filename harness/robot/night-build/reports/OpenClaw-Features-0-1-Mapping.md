# OpenClaw 原生功能 × 0-1 项目落地映射报告（v2）

> **报告版本**：v2（百科全书级）
> **生成日期**：2026-03-27
> **覆盖范围**：46 个 OpenClaw 文档页面 + ROBOT-SOP 全文（~4969 行）
> **质量原则**：所有结论注明来源页面，不确定处标注"需进一步验证"

---

## 一、0-1 项目概述

### 1.1 项目愿景

**0-1** —— 不是一台机器，是你人生的另一面。

| 层含义 | 说明 |
|--------|------|
| **机器层** | 二进制的起点，代表硅基生命的底层语言 |
| **制造层** | 第一次「从零到一」用 3D 打印制造一个完整的机器人 |
| **生命层** | 人一生的「0 到 1」——从出生到结束，机器的记忆就是我的人生存档 |

0-1 不是固定产品，而是一个随 AI 能力共同进化的陪伴者。10 年分五阶段，能力与期望共同成长。

### 1.2 核心系统：贵庚

**贵庚** 是 0-1 的记忆系统，专为保存一个人完整的一生而设计：
- **贵** = 粤语里对他人的敬称，暗含"珍贵"
- **庚** = 天干第七位，对应时间、年龄、周期——记忆本质是时间的切片
- **贵庚** 在粤语里是问老人家年龄的敬语，带着对岁月沉淀的敬畏

> 贵庚存的不是数据，是一个人的年龄和尊严。

### 1.3 硬件体系（来源：ROBOT-SOP 第二章）

| 设备 | 规格 | 角色 |
|------|------|------|
| **MacBook Pro** | OpenClaw Gateway | 主 AI 大脑、贵庚记忆、任务调度 |
| **Ubuntu 台式机** | 5600G + 32GB + RTX 2060 | GPU 节点，图像理解、GPU 密集任务 |
| **Jetson Nano 2GB** | Maxwell 128-core，2GB LPDDR4 | 边缘节点：语音交互、视频处理、运动控制（现阶段只用其中一个功能） |
| **ESP32-Cam ×2** | OV2640，RTSP 流 | 视觉节点，视频采集、室内建模 |
| **Cyber Bricks ×2** | ESP32-C3 + 电机 + 舵机 | 运动节点，电机控制、动作执行（拓竹赠送） |
| **星闪 H3863 ×2** | BearPi-Pico H3863（海思 WS63，WiFi6+BLE+SLE三模）| 低延迟通信网关、感知前处理、低功耗传感 hub |
| **拓竹 H2C** | 3D 打印机 | 个人制造工具链 |
| **iPhone 16 Pro** | A18 Pro + LiDAR + 4800万摄像 | 分布式感知前端，高质量感知、LLM 辅助推理、LiDAR 建模 |

### 1.4 实施 Phase 0-6

| Phase | 内容 | 对应年份 |
|-------|------|---------|
| Phase 0 | Ubuntu 台式机对接 Gateway | 阶段一前置 |
| Phase 1 | 语音陪伴（OpenClaw + Cyber Bricks 首次联动）| 阶段一 |
| Phase 2 | 视觉记录（ESP32-Cam + Jetson Nano）| 阶段一 |
| Phase 3 | iPhone 感知前端接入（分布式感知网络）| 阶段二 |
| Phase 4 | 运动控制（Cyber Bricks + MQTT）| 阶段一 |
| Phase 5 | 面部表情系统 | 阶段一 |
| Phase 6 | 室内移动 + 智能家居硬件拓展 kit | 阶段二 |

### 1.5 贵庚记忆系统架构（来源：ROBOT-SOP §1.2）

三层索引结构：

| 层级 | 类型 | 解决的问题 | 工具选型 |
|------|------|-----------|---------|
| **Layer 1** | 向量索引（语义检索）| "有没有说过类似的话" | Chroma / PGVector |
| **Layer 2** | 知识图谱（实体关系）| "提到了哪些人/地点/概念" | Mem0 OSS + Neo4j 5.x |
| **Layer 3** | 时序索引（时间线）| "上次是什么时候" | Neo4j 5.x + APOC |

发展阶段：

| 阶段 | 时间 | 数据来源 | 核心能力 |
|------|------|---------|---------|
| **前期** | 阶段一（1-2年）| 文本对话 + 语音 | 学语言习惯、记住重要内容 |
| **中期** | 阶段二（3-4年）| 全景摄像头 7×24 小时录像 | AI 分析标注视频，建立生活行为时间线 |
| **长期** | 阶段三+（5年+）| 持续扩展数据源 | 多模态理解、因果推理、个性化生成 |

模型路线：阶段一用 RAG 过渡 → 阶段二换边权重实例型大模型（OpenClaw RL GRPO+OPD）。

---

## 二、OpenClaw 功能全景

### 2.1 Gateway 核心（来源：gateway/index.md, gateway/configuration.md）

Gateway 是 OpenClaw 的核心守护进程，负责 AI Agent 运行时、节点管理、消息路由和工具调度。

**关键能力**：
- JSON5 配置文件 `~/.openclaw/openclaw.json`，热重载（默认 hybrid 模式）
- Config RPC：`config.apply`（全量替换）、`config.patch`（部分更新），带 baseHash 校验
- 环境变量：`.env` 文件 + `~/.openclaw/.env` 全局覆盖 + `${VAR}` 插值
- SecretRef：`env`/`file`/`exec` 三种密钥来源
- `$include` 配置分文件：deep-merge 数组覆盖
- 多 Agent 路由：`agents.list[]` + `bindings[]` 按 channel/account 绑定不同 Agent

**热重载能力表**（来源：gateway/configuration.md）：

| 字段类别 | 热重载 | 需重启 |
|---------|-------|--------|
| Channels | ✅ | ❌ |
| Agents & models | ✅ | ❌ |
| Automation (hooks/cron/heartbeat) | ✅ | ❌ |
| Sessions & messages | ✅ | ❌ |
| Tools & media | ✅ | ❌ |
| Gateway server (port/bind/auth/TLS) | ❌ | ✅ |
| Infrastructure (discovery/canvasHost/plugins) | ❌ | ✅ |

### 2.2 节点接入系统（来源：nodes/index.md, cli/node.md, gateway/heartbeat.md）

OpenClaw Node 是部署在远程设备上的轻量守护进程，通过 WebSocket 连接到 Gateway。

**发现与配对**：
- **mDNS/NSD（Bonjour）**：同一局域网自动发现（来源：gateway/bonjour.md）
- **Tailscale 跨网络发现**：Wide-Area Bonjour / unicast DNS-SD（来源：gateway/tailscale.md）
- **手动指定**：`OPENCLAW_GATEWAY_URL` 环境变量
- **配对流程**：Node 发起配对请求 → Gateway admin 执行 `openclaw devices approve <requestId>`（来源：channels/pairing.md）

**节点工具全家桶**（每个节点自动暴露，来源：nodes/index.md）：

| 工具 | 功能 |
|------|------|
| `camera.snap` | 拍摄 JPG 照片 |
| `camera.clip` | 录制 MP4 视频 |
| `canvas.*` | HTML/CSS/JS 内容推送（到节点屏幕）|
| `audio.*` | 音频录制（节点麦克风）|
| `talk.*` | 节点本地 TTS 播放 |
| `device.*` | 设备状态/健康检查 |
| `photos.latest` | 读取节点相册最新照片 |
| `notifications.*` | 读取/操作系统通知 |
| `contacts.*` / `calendar.*` / `callLog.*` / `sms.*` | iOS/Android 专属数据访问 |
| `motion.*` | IMU/计步数据 |
| `location.*` | GPS 位置 |
| `exec` | **SSH 远程命令执行**（来源：cli/exec.md）|

**心跳机制**（来源：gateway/heartbeat.md）：
- 配置：`agents.defaults.heartbeat.every`（duration string，如 `"30m"`）+ `target`（`"last"`/`"whatsapp"`/具体 channel）
- 作用：定期向指定 channel 发送运行状态消息，防止 Gateway 和外界失联
- 与 cron 的区别：Heartbeat 是轻量状态通知，cron 是完整任务执行（来源：automation/cron-vs-heartbeat.md）

### 2.3 工具系统（来源：tools/exec.md, tools/subagents.md, tools/skills.md）

**exec 工具**：
- 在 Node 上通过 SSH 执行远程命令（`exec` tool with `host: "node"` + `node: "<nodeId>"`）
- 来源：cli/exec.md，原理同 SSH exec，在远程机器上执行 shell 命令
- **重要**：Node exec 需要 Node 处于 `online` 状态

**子 Agent（subagents）**：
- 通过 `sessions_spawn` 派生子 Agent 并行处理任务
- 子 Agent 结果自动推送回主 session（push-based，非 poll）
- 支持 thread 模式（为 Discord 论坛 thread 专门设计，来源：channels/discord.md threadBindings）
- 来源：tools/subagents.md

**Skills 系统**：
- 三个加载位置（优先级从低到高）：bundled → `~/.openclaw/skills` → `<workspace>/skills`
- SKILL.md 是指令文件，描述工具的使用方式
- Skill 可以声明对外部工具的依赖（如 Tavily API、MiniMax 等）
- Skill 执行时可使用 `read`/`exec`/`write`/`edit` 等工具
- 创建步骤：编写 SKILL.md → 放入 `~/.openclaw/skills/` 或 workspace skills 目录
- 来源：tools/skills.md, tools/creating-skills.md

### 2.4 多 Agent 路由（来源：concepts/multi-agent.md）

多 Agent 支持隔离工作区 + 独立会话：

```json5
{
  agents: {
    list: [
      { id: "home", default: true, workspace: "~/.openclaw/workspace-home" },
      { id: "work", workspace: "~/.openclaw/workspace-work" },
    ],
  },
  bindings: [
    { agentId: "home", match: { channel: "whatsapp", accountId: "personal" } },
    { agentId: "work", match: { channel: "whatsapp", accountId: "biz" } },
  ],
}
```

- 每个 Agent 有独立工作区、独立会话历史
- 通过 channel + accountId routing 区分不同 Agent

### 2.5 记忆系统（来源：concepts/memory.md）

**记忆机制**：
- 每次 session 结束后，OpenClaw 将对话历史写入 `<workspace>/memory/YYYY-MM-DD.md`
- **HEARTBEAT.md**：心跳检查清单文件，每次 heartbeat poll 时读取并执行
- **MEMORY.md**：长期记忆文件，由 Agent 自己维护（在 main session 中）
- **Compaction（压缩）**：对话历史过长时自动压缩，保留关键决策和上下文摘要，来源：concepts/compaction.md

**Bootstrap 文件**（每个 session 自动注入）：
- `AGENTS.md` — 操作指令 + memory
- `SOUL.md` — persona、边界、语气
- `TOOLS.md` — 用户维护的工具笔记
- `IDENTITY.md` — Agent 名字/vibe/emoji
- `USER.md` — 用户画像
- `HEARTBEAT.md` — 心跳检查清单
- `BOOTSTRAP.md` — 一次性初始化 ritual（完成后删除）

### 2.6 自动化系统（来源：automation/cron-jobs.md, automation/standing-orders.md）

**Cron Jobs**：
- 调度三种类型：`at`（一次性）、`every`（固定间隔）、`cron`（crontab 表达式）
- 执行风格：`main`（心跳系统事件）、`isolated`（独立 cron session）、`current`（当前 session）、`session:xxx`（持久化命名 session）
- 投递模式：`announce`（channel 投递）、`webhook`（HTTP POST）、`none`（仅内部）
- 模型覆盖：`model` + `thinking` 参数可覆盖 job 级别模型
- 存储：`~/.openclaw/cron/jobs.json`（job 定义）+ `~/.openclaw/cron/runs/<jobId>.jsonl`（运行历史）
- 重试策略：瞬时错误（rate limit/network/5xx）指数退避，永久错误（auth/validation）立即禁用

**Standing Orders（常驻指令）**：
- 定义在 `AGENTS.md` 或独立 `standing-orders.md` 文件中
- 包含：Scope（权限范围）+ Triggers（触发条件）+ Approval Gates（审批门槛）+ Escalation Rules（升级规则）
- 与 Cron 的配合：Standing Order 定义"做什么"，Cron 定义"什么时候做"
- 核心原则：Execute-Verify-Report 循环，每次任务都要执行→验证→汇报

### 2.7 浏览器自动化（来源：tools/browser.md）

- **openclaw profile**：隔离的 agent 专用浏览器，与个人 Chrome 完全分开
- **user profile**：通过 Chrome DevTools MCP 附加到真实登录态的 Chrome
- 支持 Playwright 高级操作（click/type/drag/screenshot/PDF/navigate）
- 多 profile 支持：`openclaw`/`work`/`remote`/任意自定义 profile
- Node 浏览器代理：Node host 暴露本地浏览器控制服务，Gateway 自动代理（零配置）
- 远程 CDP：Browserless/Browserbase 远程浏览器服务，配置 `cdpUrl` 即可
- 安全：SSRF 保护（`ssrfPolicy`），默认允许私有网络，strict 模式需 hostname  allowlist

### 2.8 语音合成（来源：tools/tts.md）

- **ElevenLabs**（需 API Key）：多语言，`voiceId` + `modelId` + `voiceSettings`（stability/similarity/style/speed）
- **Microsoft Edge TTS**（无需 API Key）：使用 Edge 在线 neural TTS 服务，免费但无 SLA
- **OpenAI TTS**（需 API Key）：`gpt-4o-mini-tts`，`voice` 参数
- Auto-TTS 模式：`off`/`always`/`inbound`/`tagged`
- 模型驱动覆盖：模型可 emit `[[tts:voiceId=xxx]]` 指令覆盖单次回复的语音
- Per-user preferences：`~/.openclaw/settings/tts.json`，slash command 写入
- Feishu/Matrix/Telegram/WhatsApp：Opus 格式；其他 channel：MP3 格式

### 2.9 远程访问（来源：gateway/remote.md, gateway/tailscale.md）

- **SSH 隧道**：最通用方案，`ssh -N -L 18789:127.0.0.1:18789 user@host`
- **Tailscale Serve**：通过 Tailscale 尾网提供 HTTPS，Gateway 保持 loopback
- **Tailscale Funnel**：公网 HTTPS，需共享密码认证
- **OpenShell**：托管安全沙箱后端，支持 `mirror`（本地 canonical）和 `remote`（远程 canonical）两种 workspace 模式
- **Node 浏览器代理**：Gateway 代理浏览器控制到 Node，无需暴露额外端口

### 2.10 沙箱系统（来源：gateway/sandboxing.md）

- **模式**：`off`/`non-main`（默认，仅非 main session 沙箱化）/`all`
- **Scope**：`session`（每 session 一个容器）/`agent`（每 agent 一个容器）/`shared`（共享容器）
- **后端**：Docker（默认，本地容器）、SSH（远程机器）、OpenShell（托管安全沙箱）
- **Workspace 访问**：`none`（只看沙箱目录）/`ro`（只读 agent workspace）/`rw`（读写 agent workspace）
- **浏览器沙箱**：可选，Docker 镜像 `openclaw-sandbox-browser:bookworm-slim`
- **工具策略叠加**：Tool deny policy > sandbox，elevated 是 sandbox 的例外出口

### 2.11 提权模式（来源：tools/elevated.md）

- 沙箱 session 中通过 `/elevated on/ask/full/off` 指令切换到 host 执行
- `/elevated full`：host 执行 + 跳过 exec approvals
- 需要 `tools.elevated.enabled: true` + sender 在 `allowFrom` allowlist 中
- **注意**：Tool policy 拒绝 exec 时 elevated 无法覆盖

### 2.12 Web 搜索与抓取（来源：tools/web-fetch.md, tools/web.md）

- **web_fetch**：HTTP GET + Readability 内容提取，HTML → markdown/text，缓存 15 分钟
- **web_search**：Brave Search API，多语言/地区/时间过滤
- **Firecrawl 后备**：Readability 失败时自动重试 Firecrawl API（需 `FIRECRAWL_API_KEY`）
- 工具 profiles：`allow: ["web_fetch"]` 或 `allow: ["group:web"]`

---

## 三、硬件体系映射

### 3.1 MacBook Pro（Gateway 大脑）

**OpenClaw 能做什么**：

| 功能 | OpenClaw 支持方式 | 文档来源 |
|------|-----------------|---------|
| 主 Gateway 运行 | `openclaw gateway` 守护进程 | gateway/index.md |
| AI Agent 运行时 | 嵌入式 Pi agent core，单 session 串行 | concepts/agent-loop.md |
| 任务调度 | `cron` 工具（定时任务）| automation/cron-jobs.md |
| 心跳检查 | `heartbeat` 系统（periodic status ping）| gateway/heartbeat.md |
| 远程访问控制 | Tailscale Serve/Funnel 或 SSH 隧道 | gateway/tailscale.md |
| 浏览器控制 | `browser` 工具（本地 Chrome/Brave）| tools/browser.md |
| TTS 语音合成 | ElevenLabs/Microsoft/OpenAI | tools/tts.md |
| 文件管理 | `read`/`write`/`edit` 工具 | tools/exec.md |
| 多 Agent 路由 | `agents.list[]` + `bindings[]` | concepts/multi-agent.md |
| 记忆存储 | MEMORY.md + 每日日志 + Compaction | concepts/memory.md |
| Skills 加载 | bundled/local/workspace 三层 | tools/skills.md |
| 沙箱执行 | Docker/SSH/OpenShell 后端 | gateway/sandboxing.md |
| Web 搜索/抓取 | `web_search`/`web_fetch` | tools/web.md, tools/web-fetch.md |

**怎么做**：
1. 安装：`curl -fsSL https://openclaw.ai/install.sh | bash`
2. 启动：`openclaw gateway --port 18789`
3. 配置 token：`openclaw onboard` 或编辑 `~/.openclaw/openclaw.json`

**已知限制**：
- Gateway 本身不直接控制 GPIO/串口硬件（需要通过 Node exec 或外部脚本）
- TTS auto 模式默认关闭，需手动启用 `messages.tts.auto`
- 沙箱 browser 需要 Playwright（`npm install playwright` 后重启 Gateway）

---

### 3.2 Ubuntu 台式机（5600G + RTX 2060）

**OpenClaw 能做什么**：

| 功能 | OpenClaw 支持方式 | 文档来源 |
|------|-----------------|---------|
| GPU 推理节点 | 作为 Node 接入 Gateway，`exec` 远程跑 AI 推理命令 | cli/exec.md, nodes/index.md |
| vLLM/Ollama 服务 | Node exec 调用本地模型 API | tools/exec.md |
| YOLO/视觉处理 | Node exec SSH 跑 Python 脚本 | cli/exec.md |
| Genesis/Newton 仿真 | Node exec 跑物理仿真 | tools/exec.md |
| 存储节点 | `exec` + `read`/`write` 访问本地文件系统 | tools/exec.md |

**怎么做**：
1. 在 Ubuntu 上安装 OpenClaw Node：`curl -fsSL https://openclaw.ai/install.sh | bash`
2. 获取 Mac Gateway token：`cat ~/.openclaw/openclaw.json | python3 -c "..."`（来源：ROBOT-SOP Phase 0）
3. 启动 Node：`export OPENCLAW_GATEWAY_TOKEN="<token>" && openclaw node run --host <mac-ip> --port 18789`
4. Mac 上审批配对：`openclaw devices list` → `openclaw devices approve <requestId>`
5. 验证：`openclaw devices list` 显示 online

**关键配置**（来源：ROBOT-SOP Phase 0）：
```bash
# GPU 任务默认路由到该节点
openclaw config set tools.exec.host node
openclaw config set tools.exec.node "Ubuntu-GPU-Node"
```

**已知限制**：
- RTX 2060 6GB 只能跑 Q4_K_M 量化的 7B 模型（Qwen2.5-7B Q4_K_M ~4.5GB）
- Node exec 依赖 SSH 连通性（需同一局域网或 VPN）
- 不支持 GPU 透传（exec 在远程跑命令，不是 GPU 直接调用）

---

### 3.3 Jetson Nano 2GB（视觉处理节点）

**OpenClaw 能做什么**：

| 功能 | OpenClaw 支持方式 | 文档来源 |
|------|-----------------|---------|
| RTSP 摄像头接入 | `camera.clip` + `camera.snap` 工具（节点暴露）| nodes/camera.md |
| 音频录制 | `audio.record` 工具（节点麦克风）| nodes/audio.md |
| 远程命令执行 | `exec` tool with `host: "node"`, SSH 到 Nano | cli/exec.md |
| 语音交互 | `talk.*` 工具（节点 TTS）+ 自写 Whisper 脚本通过 exec 调用 | nodes/talk.md |
| 媒体理解 | `media.understand` 工具（节点视觉 AI）| nodes/media-understanding.md |
| 节点状态监控 | `device.status/info/health` | nodes/index.md |
| 文件传输 | `read`/`write` 访问 Nano 文件系统 | tools/exec.md |
| GPIO 控制 | `exec` SSH 跑 `sys/class/gpio` 命令 | tools/exec.md |

**怎么做**：
1. 安装 JetPack 5.x（L4T 35.x），参考 ROBOT-SOP Phase 1/2
2. 安装 OpenClaw Node（同 Ubuntu 台式机）
3. RTSP 流接收：用 GStreamer `rtspsrc` + `decodebin`（ROBOT-SOP §Phase 2）
4. YOLO 部署：TensorRT FP16（Maxwell 不支持 INT8），DeepStream 6.x 配置 FP16 模式（来源：ROBOT-SOP §5.1）
5. MediaPipe：GPU 加速不成熟，建议 CPU 版或用 TensorRT 替代（来源：ROBOT-SOP §5.1）

**已知限制**：
- 2GB 内存必须开 swap 才能同时跑 YOLO + MediaPipe
- **FP16 是唯一有效 GPU 加速**（Maxwell 不支持 INT8）
- YOLOv8n @ 640×640 约 13-16 FPS；降分辨率到 320×320 可达 35-45 FPS
- MediaPipe GPU 方案不成熟，不推荐在 Nano 上跑 MediaPipe GPU
- ESP32-Cam UART 通信：波特率 115200，电平 3.3V TTL 直接互连，不需要电平转换

---

### 3.4 ESP32-Cam（RTSP 摄像头）

**OpenClaw 能做什么**：

| 功能 | OpenClaw 支持方式 | 文档来源 |
|------|-----------------|---------|
| RTSP 视频流 | 作为 Camera Node 接入，`camera.clip` 录制视频 | nodes/camera.md |
| 静态图片拍摄 | `camera.snap` 拍摄 JPG | nodes/camera.md |
| JPEG 流获取 | 通过 `images.get` 工具获取最新帧 | nodes/images.md |

**怎么做**：
1. 烧录 CameraWebServer 固件（ESP32 v3.0.7 + AI Thinker Configuration，来源：ROBOT-SOP §A.3）
2. 配置静态 IP（在 camera_config_t 设置 WIFI_MODE_STA + 静态 IP）
3. 硬件连接：USB-TTL（烧录时 GPIO0 → GND 进入烧录模式）
4. OpenClaw Node 发现：同一局域网 mDNS 自动发现，或手动指定 `OPENCLAW_GATEWAY_URL`
5. 配对：`openclaw devices approve <requestId>`

**RTSP 流接收（Jetson Nano）**：
```bash
# GStreamer pipeline
gst-launch-1.0 rtspsrc location=rtsp://<esp32-ip>:8554/stream \
  ! decodebin ! videoconvert ! autovideosink
```

**已知限制**：
- OV2640 JPEG 压缩，320×240 @ 5-10 FPS 避免内存溢出
- 520KB SRAM，无法跑 micro-ROS 完整节点（只能跑 micro-ROS agent 或 HTTP/MJPEG 流）
- ESP-IDF 分区表需调整以支持 OTA

---

### 3.5 星闪 H3863（低延迟通信）

**OpenClaw 能做什么**：

| 功能 | OpenClaw 支持方式 | 文档来源 |
|------|-----------------|---------|
| 无线通信网关 | 作为 OpenClaw Node，SLE 12Mbps / WiFi6 114.7Mbps | nodes/index.md |
| UART 透传 | `exec` 通过 Node SSH 访问 H3863 串口 | cli/exec.md |
| MQTT 中枢 | H3863 作为 MQTT broker，Node exec 调用 `mosquitto_pub` | tools/exec.md |
| 传感器 hub | H3863 通过 I2C/SPI 聚合传感器，`exec` 读取数据 | tools/exec.md |

**关键发现（来源：ROBOT-SOP §2.5）**：
- H3863 **不适合跑 YOLO 目标检测**（240MHz RISC-V，606KB SRAM，约 0.24 GFLOPS）
- H3863 最佳角色：**感知前处理器 + 低功耗传感 hub + 星闪网关**
- 星闪 SLE 端到端延迟 ≤1ms，可传 YOLO 检测结果（~200B）
- 功耗：H3863 值守 0.3W vs Nano 单独运行 7.5W，续航提升约 5 倍

**怎么做**：
1. 两块成对购买（SLE 收发测试需要）
2. 搭建 Hi3863 开发环境（RISC-V 工具链 + 小熊派 SDK）
3. 通过 UART 与 Jetson Nano 连接（4Mbps 波特率）
4. 在 Nano 上安装 OpenClaw Node 作为主控
5. H3863 通过 SLE 无线接收上位机指令

**已知限制**：
- Hi3863 无 MMU，无法跑标准 Linux，需要 FreeRTOS 编程
- 无官方 micro-ROS 包，需自行移植
- 星闪 SLE 开发学习曲线较高（中等难度，7/10）

---

### 3.6 Cyber Bricks（运动控制）

**OpenClaw 能做什么**：

| 功能 | OpenClaw 支持方式 | 文档来源 |
|------|-----------------|---------|
| 电机/舵机控制 | `exec` SSH 到 Jetson Nano，Nano UART 发指令到 Cyber Bricks | tools/exec.md |
| MicroPython 固件 | Cyber Bricks 接收 MQTT 消息执行动作 | tools/exec.md |
| 应急停止 | `exec` 通过 GPIO 硬件中断（有线优先）| tools/exec.md |
| 状态查询 | `exec` 通过 UART 读取 Cyber Bricks 回传状态 | tools/exec.md |
| 多 Cyber Bricks 协同 | 分别订阅不同 MQTT topic（`0-1/cyberbrick1`、`0-1/cyberbrick2`）| tools/exec.md |

**怎么做**（来源：ROBOT-SOP Phase 4）：
1. Cyber Bricks 运行 MicroPython MQTT client（订阅 `0-1/cyberbrick1`）
2. Jetson Nano 作为 MQTT broker（安装 `mosquitto`）
3. OpenClaw 通过 Node exec 在 Nano 上调用 `mosquitto_pub` 发送指令
4. 指令格式：`{"action":"forward","speed":50}` 或 `{"type":"servo","angle":45}`
5. GPIO 应急停止：Nano GPIO Pin 29 发 `echo 0 > /sys/class/gpio/gpio29/value` 断开继电器

**OpenClaw Skill 示例**（发送指令）：
```
用户："让 Cyber Brick 往前走"
→ 调用 exec → python3 cyberbrick_control.py forward
```

**已知限制**：
- Cyber Bricks 只有 ESP32-C3（无外设接口），需要通过 UART 与 Nano 通信
- 无 OpenClaw 原生 MQTT 支持，所有 MQTT 操作通过 `exec` 调用外部工具
- 精细操作受限（无触觉传感，只能做基础动作）
- GPIO 应急停止 <1ms，无线 WiFi >100ms

---

### 3.7 iPhone 16 Pro（分布式感知）

**OpenClaw 能做什么**：

| 功能 | OpenClaw 支持方式 | 文档来源 |
|------|-----------------|---------|
| 摄像头视频流 | `camera.clip` + `camera.snap`（4800万主摄/LiDAR）| nodes/camera.md |
| 音频录制 | `audio.*` 工具（四麦克风阵列，远场语音）| nodes/audio.md |
| TTS 播放 | `talk.*` 工具（本地语音输出）| nodes/talk.md |
| 设备状态 | `device.status/info/health` | nodes/index.md |
| 通知读取 | `notifications.list/actions` | nodes/index.md |
| 相册读取 | `photos.latest` | nodes/index.md |
| 联系人/日历 | `contacts.search/add`、`calendar.events/add` | nodes/index.md |
| 通话记录/短信 | `callLog.search`、`sms.search` | nodes/index.md |
| IMU/计步 | `motion.activity`、`motion.pedometer` | nodes/index.md |
| GPS 位置 | `location.*` | nodes/index.md |
| 本地 LLM 推理 | 通过 Node 暴露的 exec 运行 Core ML 模型 | nodes/index.md, cli/exec.md |
| Canvas 推送 | `canvas.*` 推 HTML/CSS/JS 到 iPhone 屏幕 | nodes/index.md |

**怎么做**：
1. iPhone 安装 OpenClaw App（未公开发布，需从 GitHub 源码构建，来源：platforms/ios.md）
2. App 通过 mDNS/NSD 自动发现同一局域网的 Gateway
3. 或通过 Tailscale tailnet 发现（跨网络场景）
4. 或手动指定 Gateway URL + token
5. Gateway 审批配对：`openclaw devices list` → `openclaw devices approve <requestId>`
6. iPhone App 前台运行时自动保持 Gateway 连接（foreground service）

**Relay 推送（官方 iOS build）**：
- 需要配置 `gateway.push.apns.relay.baseUrl`（官方 build 自带 relay URL）
- App Attest + app receipt 注册 relay 凭证
- 用途：push 通知唤醒 App（即使 App 在后台）

**已知限制**：
- 官方 iOS App 未公开发布，需自行从源码构建（Java 17 + Android SDK，来源：platforms/ios.md）
- Voice wake/talk-mode toggle 已从 Android 移除（来源：platforms/android.md），iOS 情况待确认
- iPhone 作为 OpenClaw Node 时，相机权限需要用户在 App 内授权

---

### 3.8 拓竹 H2C（3D 打印）

**OpenClaw 能做什么**：

| 功能 | OpenClaw 支持方式 | 文档来源 |
|------|-----------------|---------|
| 打印任务触发 | `exec` SSH 跑 Bambu Studio / CyberBrick 桌面端命令 | tools/exec.md |
| 打印状态监控 | `exec` 跑拓竹农场管家 CLI 或 HTTP API | tools/exec.md |
| 制造执行记录 | 打印历史写入 MEMORY.md + 日志 | concepts/memory.md |
| 设计文件管理 | `read`/`write`/`edit` 操作 CAD/STL 文件 | tools/exec.md |

**怎么做**：
1. 拓竹 H2C 通过 WiFi 连接局域网
2. 拓竹农场管家（Windows）管理多台打印机，本地 MQTT / HTTP API
3. OpenClaw Node exec 调用 `curl` 或 Python 脚本向拓竹生态发指令
4. Bambu Suite 激光切割/刀切：通过 `exec` 在桌面端触发

**已知限制**：
- 无 OpenClaw 原生拓竹集成，所有操作通过 exec 调用外部工具
- 拓竹生态（CyberBrick/Bambu Suite/拓竹农场管家）主要是桌面端工具
- iOS 端 Bambu Handy 用于移动监控，但 OpenClaw iPhone Node 不能直接控制打印机

---

## 四、Phase 落地路径

### Phase 0: Ubuntu 台式机对接 Gateway

**目标**：让 Ubuntu 台式机（5600G + RTX 2060）作为 GPU 节点接入 Mac Gateway，跑通发现→配对→执行链路。

**OpenClaw 哪些功能直接可用**：

| 功能 | 方式 | 文档