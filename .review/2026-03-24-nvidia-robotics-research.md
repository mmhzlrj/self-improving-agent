# NVIDIA 机器人开源核心技术调研报告 — 0-1 应用价值分析

**调研时间**：2026-03-24
**来源**：NVIDIA 官方博客 + Hugging Face + GitHub + 多源搜索验证

---

## 一、四大核心技术概览

| 方案 | 定位 | 开源平台 | 对 0-1 价值 |
|------|------|---------|-------------|
| **Newton 物理引擎** | 高精度物理仿真 | GitHub + Isaac Lab | ⭐⭐⭐⭐⭐ |
| **Isaac GR00T N1.6** | 视觉-语言-动作基础模型 | Hugging Face | ⭐⭐⭐⭐⭐ |
| **Cosmos 世界基础模型** | 合成数据生成 | Hugging Face | ⭐⭐⭐⭐ |
| **Isaac Lab-Arena** | 仿真评估框架 | GitHub + LeRobot | ⭐⭐⭐⭐ |

---

## 二、Newton 物理引擎 ⭐⭐⭐⭐⭐

**发布时间**：2025-03-18（NVIDIA GTC）
**合作方**：NVIDIA + Google DeepMind + Disney Research，Linux Foundation 管理
**GitHub**：https://github.com/newton-physics/newton
**集成**：已集成至 NVIDIA Isaac Lab

### 核心技术架构

Newton = Disney 物理引擎技术 + DeepMind MuJoCo + NVIDIA Warp 的结合：

| 底层技术 | 说明 |
|---------|------|
| **NVIDIA Warp** | Python 框架，构建和加速仿真/空间计算，CUDA 级别性能 |
| **OpenUSD** | 聚合机器人及环境数据的描述框架 |
| **MuJoCo Warp** | NVIDIA GPU 优化版 MuJoCo（Newton 的核心求解器）|
| **GPU 加速** | 仿真从"天"加速到"分钟"级别 |

### 关键特性

| 特性 | 说明 |
|------|------|
| **GPU 加速** | CUDA 级别性能，无需底层编码 |
| **可微分** | 支持梯度计算，加速训练、设计优化、系统识别 |
| **可扩展** | 通过插件支持多物理场仿真 |
| **与 Isaac Lab 兼容** | 可直接替换 Isaac Sim 中的仿真后端 |
| **与 MuJoCo Playground 兼容** | DeepMind 的 MuJoCo 强化学习环境可直接用 Newton |

### 与 Genesis 的关系

> ⚠️ **重要区分**：此前 ROBOT-SOP 记录了 Genesis（applecartn/Genesis），这是苹果团队开源的独立物理引擎。**Newton 是 NVIDIA + DeepMind + Disney 联合开发的另一套引擎**，两者是**不同的独立项目**。

| 对比项 | **Newton** | **Genesis** |
|--------|-----------|-------------|
| 开发者 | NVIDIA + DeepMind + Disney | Apple |
| 发布时间 | 2025-03 GTC | 2025-02 |
| 基础 | Disney 引擎 + MuJoCo Warp | 自研 |
| 生态 | Isaac Lab 官方集成 | 独立开源 |
| 定位 | 工业/人形机器人仿真 | 通用物理引擎 |
| 资源需求 | RTX 3060+ | GTX 1080 6GB |

### 对 0-1 的价值

```
Genesis（已记录）：低成本入门仿真，GTX 1080 可跑
Newton（新增）：高精度工业仿真，与 Isaac Lab 官方生态集成

建议：
- 阶段一：用 Genesis 做基础仿真（资源门槛低）
- 阶段二/中期：用 Newton 替换，获得更高保真度和 Isaac Lab 生态
```

---

## 三、Isaac GR00T N1.6 ⭐⭐⭐⭐⭐

**发布**：2026 年最新版本
**开源**：Hugging Face（已上线）
**GitHub**：https://github.com/NVIDIA/Isaac-GR00T

### 模型架构

| 组件 | 说明 |
|------|------|
| **Base VLM** | NVIDIA Cosmos-2B 变体，支持灵活分辨率，原生长宽比无 padding |
| **DiT** | 32 层（比 N1.5 的 16 层大一倍），去除了 N1.5 的 post-VLM 4 层适配器 |
| **动作预测** | 状态相对动作分块（state-relative action chunk），而非绝对关节角度 |

### 预训练数据（300K steps，batch size 16384）

新增数据来源：
- Bimanual YAM 双臂遥操作数据
- **智元机器人 AgiBot Genie-1**（稚晖君的公司）
- Simulated Galaxea R1 Pro（BEHAVIOR 套件）
- **宇树 G1 全身运动操作数据**

### 支持的机器人平台

| 机器人 | 验证类型 |
|--------|---------|
| **宇树 G1** | 全身运动操作（locomanipulation）✅ |
| **智元 Genie-1** | 双手操作 ✅ |
| **Bimanual YAM** | 双手操作 ✅ |
| GR00T 家族 | N1.5 支持 Franka / 1x / Fourier 等 |

### 对 0-1 的价值

**GR00T N1.6 在真实机器人上验证过宇树 G1**，这意味着：
1. 宇树 G1 的动作数据已包含在预训练中
2. Cyber Bricks 作为宇树同源架构，动作空间可能兼容
3. 用 GR00T 做任务规划，Cyber Bricks 做执行——分层架构可行

```
0-1 建议架构（整合 GR00T）：
├─ GR00T N1.6（任务规划 + 视觉理解 + 全身协调）
├─ Cyber Bricks（执行层，电机控制）
└─ RynnBrain（记忆 + 对话管理）
```

**硬件需求**：预训练需要高端 GPU，但微调和推理可以在 AGX Orin 64G 上做。

---

## 四、Cosmos 世界基础模型 ⭐⭐⭐⭐

**发布时间**：CES 2025，2025-03 重大更新
**开源**：Hugging Face（下载量超 300 万次）
**官网**：https://cosmos下水.com/

### 核心能力

| 模型 | 功能 |
|------|------|
| **Cosmos Predict** | 给定当前状态，预测未来视频/物理结果 |
| **Cosmos Transfer** | 跨域迁移（从仿真到真实、从一类物体到另一类）|
| **Cosmos Reason** | 视觉语言模型，推理物理世界（集成到 GR00T）|

### Cosmos Predict 2.5（2025-08 更新）

- 整合三模型为一，体积缩小至 **1/3.5**，效率大幅提升
- 支持 30 秒视频生成，多视角输出
- 与 Isaac Lab 集成：从仿真环境直接生成合成数据

### 对 0-1 的价值

Cosmos = 不用拍摄真实机器人，直接**生成**大量合成训练数据：
```
传统数据采集：雇人遥操作 → 成本极高
Cosmos 生成：仿真环境 → 无限量合成数据 → 训练机器人
```

结合 RoboGSim（3DGS）可以：
- RoboGSim 重建真实场景（真实纹理）
- Cosmos 生成多样化的合成动作数据（无限变体）
- 两者结合 = 最高质量的仿真训练

---

## 五、Isaac Lab-Arena ⭐⭐⭐⭐

**发布**：2025-03 GTC
**开源**：GitHub + Hugging Face LeRobot EnvHub
**合作**：与 Lightwheel 联合开发

### 定位

Isaac Lab = Isaac Sim 中的机器人学习框架（训练用）
Isaac Lab-Arena = 在 Isaac Lab 基础上构建的**评估框架**（测试用）

### 核心能力

| 能力 | 说明 |
|------|------|
| **模块化任务 API** | 快速创建新任务和环境 |
| **GPU 加速仿真** | 比 CPU 仿真快 100 倍 |
| **大规模策略评估** | 同时评估数千个策略变体 |
| **Isaac Lab 兼容** | 直接复用 Isaac Lab 的仿真环境 |
| **LeRobot 集成** | Hugging Face LeRobot 环境中心直接调用 |

### 与 LeRobot 的关系

LeRobot（Hugging Face 开源机器人框架）：
- 提供标准化的数据集格式和训练循环
- Isaac Lab-Arena 作为仿真后端
- **GR00T N1.6 可以通过 LeRobot 微调** → 在 Isaac Lab-Arena 中评估

### 对 0-1 的价值

0-1 的 Cyber Bricks 目前没有标准化评估体系。
Isaac Lab-Arena 提供了：
- 仿真中大规模测试机器人策略
- 与 GR00T 生态无缝衔接
- Hugging Face 社区共享策略权重

---

## 六、物理 AI 数据集（15TB）⭐⭐⭐⭐⭐

**发布**：2025-03 GTC
**开源**：Hugging Face（下载量 480 万次）
**链接**：https://huggingface.co/collections/nvidia/physical-ai-67c643edbb024053dcbcd6d8

### 数据规模

| 指标 | 数量 |
|------|------|
| 总规模 | **15 TB** |
| 机器人轨迹 | **32 万+ 条** |
| OpenUSD 场景 | **1000+ 个** |
| SimReady 资产 | 涵盖常见物体材质/物理属性 |

### 数据内容

- 真实机器人遥操作数据（多种机器人平台）
- Isaac Lab 仿真数据
- Cosmos 生成的合成数据
- 覆盖：家庭、工业、物流等场景

### 对 0-1 的价值

**15TB 数据是目前机器人领域最大的开源数据集**：
- Cyber Bricks 可以直接用这些数据做预训练或微调
- 宇树 G1 的数据在预训练中 → Cyber Bricks 作为低成本替代可受益
- 这是 0-1 从"自己采集"到"利用开源数据"的关键资源

---

## 七、对 0-1 的综合价值排序

### 🔴 最高优先级（立即可用的）

| 技术 | 原因 |
|------|------|
| **GR00T N1.6** | 已在宇树 G1 上验证，Cyber Bricks 可能兼容；微调后可用作 0-1 的任务规划大脑 |
| **物理 AI 数据集（15TB）** | 32 万条轨迹，0-1 训练数据来源 |
| **Newton 物理引擎** | GPU 加速仿真，比 Genesis 精度更高；与 Isaac Lab 集成 |

### 🟡 中优先级（中期整合）

| 技术 | 原因 |
|------|------|
| **Cosmos Predict 2.5** | 生成无限合成数据，解决数据不足 |
| **Isaac Lab-Arena** | 大规模策略评估，与 GR00T/LeRobot 生态衔接 |

---

## 八、0-1 整合路线图（基于 NVIDIA 生态）

```
当前（阶段一）：
  Genesis（¥0）
  └─ 基础运动仿真

中期（GR00T 整合）：
  GR00T N1.6（任务规划）
  + Newton（高精度仿真）
  + 15TB 数据集（预训练）
  + Cyber Bricks（执行层）

远期：
  Cosmos Predict 2.5（无限合成数据）
  + Isaac Lab-Arena（大规模评估）
  + LeRobot（社区策略共享）
```

---

## 九、关键链接汇总

| 资源 | 链接 |
|------|------|
| Newton GitHub | https://github.com/newton-physics/newton |
| Newton in Isaac Lab | https://github.com/isaac-sim/IsaacLab/tree/feature/newton |
| Isaac GR00T GitHub | https://github.com/NVIDIA/Isaac-GR00T |
| GR00T N1.6 Hugging Face | https://huggingface.co/nvidia/GR00T-N1.6-3B |
| Cosmos Hugging Face | https://huggingface.co/blog/nvidia/cosmos-predict-and-transfer2-5 |
| Isaac Lab-Arena | https://developer.nvidia.com/blog/simplify-generalist-robot-policy-evaluation-in-simulation-with-nvidia-isaac-lab-arena/ |
| 物理 AI 数据集 | https://huggingface.co/collections/nvidia/physical-ai-67c643edbb024053dcbcd6d8 |
| Isaac Lab | https://developer.nvidia.com/isaac/lab |
| LeRobot（Hugging Face）| https://github.com/huggingface/lerobot |

---

## 十、与现有 ROBOT-SOP 的衔接

### 已记录 vs 新发现

| 已记录（v3.4）| 更新说明 |
|--------------|--------|
| Genesis 物理引擎 | Newton ≠ Genesis，Newton 是另一套独立引擎 |
| 宇树 G1 数据 | GR00T N1.6 预训练已包含宇树 G1 全身数据 |
| RoboGSim | 补充：Cosmos 可与 RoboGSim 协同（真实纹理 + 合成变体） |
| 具身大脑基模 | GR00T N1.6 可作为 RynnBrain 之外的任务规划补充 |

### 需要更新的内容

1. **Genesis vs Newton**：Newton 不是 Genesis 的替代，是 NVIDIA 官方生态的另一个引擎
2. **GR00T N1.6**：宇树 G1 已在预训练中 → Cyber Bricks 潜在兼容
3. **15TB 数据集**：应作为 0-1 训练数据的首选来源
