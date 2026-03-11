# OpenClaw 落地场景与本地大模型部署追踪

> 记录 OpenClaw 实际落地的新场景、本地部署大模型进展、硬件更新、商用平台等

---

## 📌 核心关注点

### 1. OpenClaw 落地新场景
- 记录发现的每个新场景
- 包含：场景描述、实现方式、所需工具/技能

### 2. 本地部署大模型
- 国产模型：Step 3.5 Flash, DeepSeek V4, Qwen, Yi, etc.
- 硬件要求：Apple M系列, AMD AI Max 395, Medusa Halo, etc.
- 性能实测数据

### 3. 硬件更新
- LPDDR6 / LPCAMM2
- PCIe 6.0 SSD
- AMD AM6/AM7
- 其他有利于本地部署的硬件

### 4. 软件/API 对接
- 积极对接 OpenClaw 的服务
- 商用平台/软件

### 5. 商用孵化
- 基于 OpenClaw 的商业产品
- 成功案例

---

## 📰 每日更新记录

### 2026-03-06

#### 用户需求确认
- 目标：每天在 QQ 群展示 1-2 个热门新场景
- 关注国产本地大模型：Step 3.5 Flash, DeepSeek V4
- 关注硬件架构：Apple M系列, AMD AI Max 395, Medusa Halo, LPDDR6, LPCAMM2, PCIe 6.0 SSD

### 2026-03-06 更新

#### Step 3.5 Flash - 重大发现！

| 项目 | 内容 |
|------|------|
| **总参数** | 196B (MoE) |
| **激活参数** | 11B |
| **本地部署** | 支持！ |
| **推荐硬件** | Mac Studio M4 Max, NVIDIA DGX Spark |
| **最低VRAM** | 24GB (RTX 4090) |
| **推荐内存** | 128GB 统一内存 |
| **推理速度** | ~350 token/s |
| **上下文** | 256K |
| **量化版本** | FP8/Int4 |
| **已适配** | 华为昇腾、沐、壁仞等国产芯片 |
| **支持框架** | vLLM, SGLang, Transformers, llama.cpp |
| **特点** | 活跃参数规模(11B)与消费级硬件门槛匹配 |

#### DeepSeek V4
- 待查

#### 硬件架构
- Apple M4 Max: 128GB统一内存，适合
- AMD AI Max 395: 128GB，适合
- 待查更多

---

## 🛠️ 已知的本地部署方案

### 模型
| 模型 | 参数量 | 适合场景 | 备注 |
|------|--------|----------|------|
| Qwen | 7B-72B | 通用对话 | 阿里 |
| Yi | 6B-34B | 通用对话 | 零一万物 |
| DeepSeek | 7B-67B | 代码/推理 | 深度求索 |
| Step | - | 通用对话 | 阶跃星辰 |

### 硬件
| 硬件 | 内存 | 适用模型 |
|------|------|----------|
| Apple M3 Max | 64GB/128GB | 7B-14B |
| Apple M4 Max | 64GB/128GB | 7B-14B |
| AMD AI Max 395 | 128GB | 7B-34B? |
| NVIDIA RTX 4090 | 24GB | 7B-14B |
| NVIDIA A100 | 40GB/80B | 14B-34B |

---

## 🔗 对接中的服务

(待记录)

---

## 💡 想法/推理

(记录从现有信息推理出的实现方式)
