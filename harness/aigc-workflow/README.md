# AIGC 漫剧多智能体集群 - 完整技术调研报告

## 背景

参考图片中的"AIGC 漫剧多智能体集群协同"架构，设计一套自动化生成漫剧/短视频的 AI 工作流。

---

## 一、方案对比

### 1. 纯 API 方案（推荐）

| 功能 | API | 价格 | 状态 |
|------|-----|------|------|
| 对话/LLM | MiniMax Coding Plan | 40 prompts/5h | ✅ 已订阅 |
| 文生图 | 通义万相 | ¥0.16/张 | ✅ 可用 |
| 图生视频 | MiniMax Video | ~$0.08/秒 | ✅ 可用 |
| 图生视频 | Seedance 2.0 | ¥1/秒 | ⚠️ 更贵 |

**成本估算**：生成 30 秒视频 ≈ ¥18-20

### 2. 本地部署方案（6GB 显存优化）

#### ✅ 可行的 6GB 显存方案

| 方案 | 显存要求 | 状态 |
|------|----------|------|
| **Stable Video Diffusion (SVD)** | 6GB ✅ | 可行 |
| **SD 1.5 / SD 2.1** | 4-6GB | 可行 |
| **SDXL + 优化** | 8GB+ | ⚠️ 需优化 |
| **LCM 加速** | 4GB | 可行 |

**优化技巧**：
- 降低 batch size
- 降低分辨率
- 使用 tile 模式
- 关闭 VAE 缓存

#### 你的台式机配置

| 配置 | 状态 |
|------|------|
| CPU: 5600g | ✅ |
| RAM: 32GB | ✅ |
| GPU: RTX 2060 6GB | ✅ 可行 |

---

## 二、Ubuntu 远程部署方案

### 1. ComfyUI + Stable Video Diffusion

```
本地 Mac → SSH → Ubuntu (RTX 2060) → ComfyUI API
```

**安装步骤**：
```bash
# 1. 安装依赖
sudo apt update
sudo apt install python3.11 python3-pip git wget

# 2. 克隆 ComfyUI
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI

# 3. 安装 Python 依赖
pip install -r requirements.txt

# 4. 下载模型（SVD - 6GB 显存可运行）
# 从 HuggingFace 下载 stable-video-diffusion

# 5. 启动
python main.py
```

### 2. 云 GPU 租用（备选）

| 服务商 | GPU | 价格 |
|--------|-----|------|
| RunPod | RTX 4090 | ~$0.5/小时 |
| Paperspace | RTX A5000 | ~$0.4/小时 |

---

## 三、Stable Video Diffusion 方案

### SVD 模型对比

| 模型 | 显存 | 生成时间 | 质量 |
|------|------|----------|------|
| SVD | 6GB | 30-60秒 | 中 |
| SVD XT | 8GB | 60-90秒 | 高 |
| Stable Video Diffusion + | 12GB | 90秒 | 最高 |

### 工作流

```
图片 → SVD (ComfyUI) → 视频
```

### 6GB 显存配置

在 ComfyUI 中设置：
- 帧数：14-24
- 分辨率：512x512 或 576x1024
- motion bucket：127

---

## 四、OpenClaw 集成方式

### 方案 A：直接 API 调用（推荐）

```
OpenClaw (exec) → API → 返回结果
```

### 方案 B：SSH 到本地/云端 Ubuntu

```
OpenClaw (exec SSH) → Ubuntu (ComfyUI) → 生成视频
```

```bash
# SSH 到 Ubuntu
ssh user@192.168.x.x "cd ComfyUI && python main.py &"

# 调用 ComfyUI API
curl -X POST "http://192.168.x.x:8188/prompt" -d '{"prompt": {...}}'
```

---

## 五、架构设计

### 多 Agent 工作流

```
用户需求
    ↓
┌─────────────────────────────────────────┐
│           OpenClaw 主 Agent              │
│         (调度枢纽 + 任务分发)            │
└─────────────────────────────────────────┘
    ↓
┌──────────┐  ┌──────────┐  ┌──────────┐
│  编剧    │  │  绘画    │  │ Prompt   │
│  Agent   │  │  Agent   │  │ Agent    │
└──────────┘  └──────────┘  └──────────┘
    ↓          ↓            ↓
┌─────────────────────────────────────────┐
│           人工审核 (飞书/微信)            │
└─────────────────────────────────────────┘
    ↓
┌──────────┐  ┌──────────┐
│ 文生图    │  │ 视频合成  │
│ Agent    │  │ Agent    │
└──────────┘  └──────────┘
    ↓
┌─────────────────────────────────────────┐
│              最终输出                     │
└─────────────────────────────────────────┘
```

---

## 六、推荐方案

### 方案 1：纯 API（当前推荐）

- ✅ 无需额外硬件
- ✅ 成本可控
- ✅ 稳定可靠

### 方案 2：本地 Ubuntu + RTX 2060 6GB

| 组件 | 方案 |
|------|------|
| 文生图 | 通义万相 API 或 SD 1.5 |
| 图生视频 | Stable Video Diffusion |
| 成本 | 电费 |

### 方案 3：云 GPU（按需）

- 成本：~$0.5/小时
- 优点：高性能、随用随付

---

## 七、下一步计划

1. ✅ 确定方案
2. ⏳ 在 Ubuntu 台式机安装 ComfyUI + SVD
3. ⏳ 配置 SSH 访问
4. ⏳ 集成测试

---

## 七、AMD AI Halo 方案（2026 年 618 采购）

### 🎉 革命性硬件：Ryzen AI Max+ 395

| 规格 | 参数 |
|------|------|
| **CPU** | 16 核 Zen 5 |
| **GPU** | RDNA 3.5 集成显卡 |
| **统一内存** | 128GB LPDDR5X |
| **GPU 可用** | 最高 112GB |
| **NPU** | 50 TOPS |
| **发布时间** | 2026 年 Q2 |
| **预计价格** | ¥10,000-15,000 |

### 为什么强大

1. **统一内存架构** - GPU 直接访问系统内存，无需显存
2. **128GB 大内存** - 可加载超大模型
3. **Mini PC 体积** - 手掌大小，便携
4. **对标 Nvidia DGX Spark** - AMD 官方定位

### 可运行模型

| 模型 | 内存要求 | 状态 |
|------|----------|------|
| Stable Diffusion XL | 8-12GB | ✅ |
| Stable Video Diffusion | 8-12GB | ✅ |
| Llama 70B | 140GB | ⚠️ 需优化 |
| Qwen 72B | 144GB | ⚠️ 需优化 |
| 小模型 + LoRA | 32-64GB | ✅ |

### 推荐配置（2026 618 后）

```yaml
# AMD AI Halo 配置
硬件: AMD Ryzen AI Max+ 395 (128GB)
存储: 2TB NVMe SSD
系统: Ubuntu 24.04 / Windows 11

# 可运行
- ComfyUI + Stable Diffusion XL
- ComfyUI + Stable Video Diffusion
- 本地 LLM (32-70B)
- OpenClaw Node
```

### 预期成本

- 整机：¥10,000-15,000
- 优点：无需显卡、无需服务器、功耗低

---

## 八、相关文档

- 工作流目录：`~/.openclaw/workspace/harness/aigc-workflow/`
- MiniMax Tools：`~/.openclaw/workspace/skills/minimax-tools/`
- 额度监控：`~/.openclaw/workspace/skills/coding-plan-monitor/`
- MDView：`~/.openclaw/workspace/tools/mdview.py`
