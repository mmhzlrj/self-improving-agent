# AMI Labs深度研究报告：Yann LeCun的$1B创业公司及0-1项目可借鉴内容

> **研究日期**: 2026-03-30
> **研究主题**: AMI Labs技术架构、JEPA进展、以及0-1个人机器人项目的实际借鉴路径

---

## 一、AMI Labs概况：已知信息汇总

### 1.1 公司基本信息

| 项目 | 内容 |
|------|------|
| **全称** | Advanced Machine Intelligence (AMI) |
| **创始人** | Yann LeCun（图灵奖得主，前Meta FAIR负责人） |
| **成立时间** | 2025年11月（LeCun离开Meta后） |
| **总部** | 法国巴黎 |
| **其他办公室** | 纽约、蒙特利尔、新加坡 |
| **融资规模** | **$1.03B**（约€890M）种子轮 |
| **Pre-money估值** | **$3.5B** |
| **领投方** | Cathay Innovation、Greycroft、Hiro Capital、HV Capital、Bezos Expeditions |
| **战略投资者** | Toyota Ventures、NVIDIA、Mark Cuban、Temasek、Samsung等 |
| **CEO** | Alexandre LeBrun（此前创立Wit.ai，后被Meta收购） |
| **COO** | Laurent Solly（前Meta欧洲VP） |

**官方网址**: https://amilabs.xyz/

### 1.2 核心使命声明

AMI Labs官网明确表述：

> *"Real intelligence does not start in language. It starts in the world."*
> （真正的智能不是从语言开始的，是从世界开始的。）

> *"Generative architectures trained by self-supervised learning to predict the future have been astonishingly successful for language understanding and generation. But much of real-world sensor data is unpredictable, and generative approaches do not work well."*
> （生成式架构在语言理解和生成上非常成功。但大多数真实传感器数据是不可预测的，生成式方法效果不好。）

**AMI的技术路线**：开发世界模型，学习真实世界传感器数据的抽象表征，忽略不可预测的细节，在表征空间（representation space）中进行预测。

---

## 二、技术架构：AMI Labs实际在建造什么？

### 2.1 核心技术栈：JEPA（联合嵌入预测架构）

AMI Labs的技术根基是**JEPA（Joint Embedding Predictive Architecture）**——LeCun在2022年提出的替代自回归LLM的架构范式。

**JEPA的核心思想**：

```
传统LLM: 预测下一个token（离散符号）
JEPA: 预测下一个表征向量（在连续潜在空间中）
```

关键区别：
- **生成式方法**（LLM/Sora）：在像素空间或token空间预测未来 → 对于复杂、不可预测的真实世界传感器数据效果差
- **JEPA**：先编码到紧凑潜在空间，在表征空间预测 → 只预测"重要的高层结构"，忽略不可预测的细节

### 2.2 VL-JEPA：多模态扩展

在Meta期间，LeCun团队开发了**VL-JEPA**（Vision-Language JEPA），将JEPA扩展到视觉-语言多模态。

**两阶段训练**：
1. **视觉编码器**：通过JEPA目标在视频数据上预训练，学习世界表征
2. **语言对齐**：将视觉表征与语言关联

### 2.3 LeWorldModel（LeWM）：JEPA的工程突破

**发布信息**：
- **论文**: arXiv:2603.19312（2026年3月，v2版本2026年3月24日）
- **作者**: Lucas Maes, Quentin Le Lidec, Damien Scieur, Yann LeCun, Randall Balestriero
- **GitHub**: https://github.com/lucas-maes/le-wm
- **官网**: https://le-wm.github.io/

**核心突破**：

| 指标 | 数值 |
|------|------|
| **参数量** | ~15M |
| **训练硬件** | 单GPU，训练数小时 |
| **推理速度** | 比foundation-model-based世界模型快**48倍** |
| **损失函数项** | 仅**2个**（next-embedding预测损失 + 高斯分布正则化SIGReg） |
| **之前方法** | 需要6个超参数调优（多目标损失、EMA、预训练编码器、辅助监督等） |

**架构细节**：
```
图像观测 → 编码器(Encoder) → 潜在表征z^t
                                        ↓
                              预测器(Predictor)
                                        ↓
                              预测下一时刻表征ẑ^(t+1)
                                    
潜在表征z^t + 动作a^t → 预测器 → ẑ^(t+1)
                                    ↓
                    对比损失（确保预测与实际表征一致）
```

**关键创新 - SIGReg（高斯正则化）**：
- LeWM通过一个简单的正则化项强制潜在表征服从高斯分布
- 这自动防止了"表征崩溃"（representation collapse）问题
- 不需要之前JEPA方法中的复杂启发式技巧

**物理探测结果**：
- LeWM的潜在空间编码了有意义的物理结构
- 可以探测性地预测物理量（速度、位置等）
- 对"物理上不合理的事件"能可靠检测（surprise evaluation）

### 2.4 LeJEPA：理论框架

**论文**: "LeJEPA: Provable and Scalable Self-Supervised Learning Without the Heuristics" (arXiv:2511.08544, 2025年11月)
**作者**: Randall Balestriero & Yann LeCun

这是JEPA的理论升级版，提供了：
- 更严格的数学证明框架
- 证明为什么JEPA可以在没有启发式技巧的情况下稳定训练
- 可扩展性证明

### 2.5 SAI：重新定义AGI目标

**论文**: arXiv:2602.23643v1（2026年2月/3月）
**标题**: 提出了SAI（Superhuman Adaptable Intelligence）替代AGI

**核心论点**：
- **AGI不是一个精确定义的目标**：不同人对AGI的定义不一致，无法作为可靠的科研目标
- **人类智能并非"通用"**：人类只是在进化塑造的任务分布内表现好，超出这个范围能力有限
- **真正重要的是适应速度（Adaptation Speed）**：系统学习新任务、多快能专业化
- **SAI = 超人类适应性智能**：能适应任何人类能做的任务，且能适应人类领域之外的有用任务

**SAI对世界模型的启示**：
> "Strong adaptation likely benefits from world models. What matters is learning compact representations that capture system dynamics. A world model supports simulation and planning, which in turn support zero-shot and few-shot adaptation."

---

## 三、竞争格局：世界模型五条路线

| 公司/团队 | 方法 | 核心技术 | 融资/资源 |
|-----------|------|----------|-----------|
| **AMI Labs** (LeCun) | JEPA/VL-JEPA | 潜在空间预测 + 自监督 | $1.03B |
| **World Labs** (Fei-Fei Li) | Marble | 生成式3D世界 + Gaussian Splatting | $1B+ |
| **Google DeepMind** | Genie 3 + SIMA 2 | Transformer + 视频生成 | Google内部 |
| **Verses.ai** (Karl Friston) | AXIOM | 主动推理 + 对象组合 | 未公开 |
| **xAI** (Musk) | Grok | 多模态 + FSD数据 | xAI生态 |

**各路线对比**：
- **生成式**（Marble/Genie 3）：预测像素/视频流 → 计算量大，难以精确控制
- **JEPA路线**：预测潜在表征 → 更紧凑、可控，但需要解决表征崩溃
- **主动推理路线**（AXIOM）：基于变分推断的主动更新

---

## 四、AMI Labs与Nabla合作：医疗健康应用

### 4.1 Nabla是谁

Nabla（https://www.nabla.com）是一家数字健康AI公司，其ambient AI助手已在美国数百家医疗系统中使用，帮助医生自动生成临床文档。

LeCun目前担任Nabla的**董事长**。

### 4.2 合作内容

Nabla官方博客（2026年3月）明确表述：

**为什么医疗需要世界模型**：
- **LLM的局限性**：基于概率的系统，在确定性推理、连续多模态数据适应、复杂环境演化模拟方面有根本限制
- **医疗的复杂性**：临床环境涉及多团队协作、碎片化技术基础设施、持续变化的患者状况

**世界模型在医疗中的具体应用**：
1. **安全和可审计的决策**：能在潜在空间做"what-if"模拟分析
2. **多模态医疗信号处理**：音频、医学影像、生理数据
3. **自主代理系统的可信监管路径**：这是关键！SAI paper中提到的安全guardrails在这里体现
4. **工作流理解**：超越文档，理解和协调临床工作流

**AMI Labs的承诺**：
> *"AMI's research focuses on developing world models that can maintain persistent memory, reason about evolving situations, and plan actions under real-world constraints, with safety, reliability, and controllability as core design principles."*
> （AMI的研究专注于开发能保持持久记忆、在现实约束下推理和规划行动的世界模型，以安全、可靠和可控为核心设计原则。）

---

## 五、JEPA在真实机器人部署的现状与挑战

### 5.1 LeWM已经做到什么

LeWM已在以下任务上验证：
- **2D控制任务**（Push-T等）
- **3D控制任务**
- 完整规划（full planning）**不到1秒**

但这些都是**模拟环境**中的控制任务。

### 5.2 关键未解决挑战

#### 挑战1：表征崩溃（Representation Collapse）

这是JEPA训练的核心问题——如果预测器和编码器太弱，模型可能学到"平凡解"（所有输入映射到同一表征）。

**LeWM的解决方案**：SIGReg（高斯正则化），但这仍是学术环境下的验证。

#### 挑战2：Sim-to-Real Gap（模拟到真实差距）

**这是90%机器人创业公司死亡的地点。**

模拟环境与真实世界的差异包括：
- 物理参数不准确（摩擦力、质量、弹性等）
- 传感器噪声分布不同
- 光照、纹理、视角变化

**当前解决思路**：
- Domain Randomization：在模拟中随机化各种参数
- 使用真实数据fine-tune
- World Models允许在"想象中"探索失败场景

#### 挑战3：Latent Space Planning（潜在空间规划）

在潜在空间中进行规划是JePA的核心优势，但存在：
- 潜在表征可能不编码所有关键信息
- 规划空间与实际动作空间的对应关系
- 长视野规划中的误差累积

#### 挑战4：连续真实世界数据

> *"Real-world data is continuous, high-dimensional, and noisy."*
> （真实世界数据是连续的、高维的、有噪声的。）

从连续传感器流中提取有效表征本身就是难题。

---

## 六、LeCun三篇2026年3月论文的实质关系

### 6.1 三篇论文一览

| 论文 | arXiv编号 | 时间 | 内容 |
|------|-----------|------|------|
| **LeWorldModel (LeWM)** | 2603.19312 | 2026年3月13日 | JEPA工程实现突破，15M参数，单GPU训练 |
| **SAI** | 2602.23643 | 2026年2月 | 重新定义AGI→SAI，世界模型作为核心组件 |
| **LeJEPA** | 2511.08544 | 2025年11月 | JEPA理论框架，证明无启发式可扩展 |

**还有相关论文**：
- **Value-guided action planning with JEPA world models** (arXiv:2601.00844) - JEPA在规划中的应用

### 6.2 与AMI Labs的实际关系

**重要区分**：

1. **这些论文主要是学术研究**，发布在arXiv上，由NYU和其他学术机构的研究者完成
2. **LeCun作为共同作者参与**，但论文本身不代表AMI Labs的产品路线
3. **AMI Labs将这些学术成果作为技术基础**来开发商业应用
4. **AMI Labs与Meta是分开的实体**：LeCun离开Meta后创立AMI，这些论文是他学术生涯的延续，但技术方向与AMI的商业目标一致

**可以合理推断**：
- **LeWM的工程思路**（单GPU、15M参数）是AMI Labs"可负担的世界模型"路线的基础
- **SAI论文**代表了LeCun/AMI对智能目标的哲学框架
- **LeJEPA**为大规模训练提供了理论基础

---

## 七、0-1项目架构原则借鉴

### 7.1 AMI Labs的核心设计原则（可移植到0-1）

1. **表征优于重建**：学习抽象表征，在表征空间预测，而非像素级生成
2. **自监督学习**：减少对标注数据的依赖
3. **持久记忆**：AMI Labs明确强调"persistent memory"——这正是0-1用贵庚语义缓存试图解决的核心问题
4. **安全guardrails**：在潜在空间中操作，行为可预测和可控
5. **小而专注**：LeWM用15M参数做到了在单GPU上可训练可推理

### 7.2 AMI Labs架构 vs 0-1现状对比

| 维度 | AMI Labs目标 | 0-1项目现状 | 差距分析 |
|------|-------------|-----------|---------|
| **世界模型** | JEPA，在表征空间预测 | 贵庚：sentence-transformers + FAISS（纯检索） | **根本范式差距**：检索≠预测 |
| **持久记忆** | 持久、适应性强的记忆系统 | FAISS语义缓存（基于历史对话） | AMI的persistent memory是动态演化的；0-1是静态检索 |
| **多模态** | 视觉+语言+动作统一表征 | 主要文本，少量图像理解 | 差距巨大 |
| **推理架构** | 潜在空间规划 | 纯LLM调用 | 0-1完全依赖LLM，缺少世界模型层 |
| **硬件** | 多GPU集群 | Jetson Nano 2GB + ESP32-Cam | 计算能力差距~1000x |
| **训练方式** | 自监督 | 预训练模型fine-tune | 0-1不能训练自己的模型 |
| **应用场景** | 企业级（医疗、工业） | 个人陪伴机器人 | 规模完全不同 |
| **安全guardrails** | 核心设计原则 | 无 | 0-1没有显式安全层 |

---

## 八、最小可行世界模型（Minimum Viable World Model）

### 8.1 什么是"最小可行世界模型"

基于LeWM的启示，对于嵌入式个人机器人，最小可行世界模型应该：

```
输入：摄像头图像（或低分辨率帧）
    ↓
编码器：轻量级CNN/ViT → 潜在向量z（维度~64-256）
    ↓
预测器：根据当前z + 动作a → 预测下一时刻z'
    ↓
动作选择：在潜在空间搜索最佳动作序列
```

### 8.2 0-1约束下的可行性分析

**Jetson Nano 2GB的实际情况**：
- GPU: Maxwell架构，128 CUDA核心，4GB RAM（系统2GB可用）
- **可以运行**：轻量级CNN推理（~10-30 FPS）
- **不能训练**：无法训练LeWM那样15M参数的模型
- **ESP32-Cam**：只有240MHz Xtensa CPU，无AI能力，只能传输图像

**现实评估**：

| 方案 | 可行性 | 说明 |
|------|--------|------|
| 在Jetson Nano上运行预训练世界模型 | ⚠️ 可行但受限 | LeWM 15M参数≈60MB，Nano可以加载但推理较慢 |
| 在云端运行世界模型，本地推理 | ✅ 合理 | 本地做感知编码，上云做世界模型预测 |
| 用LLM模拟"世界模型" | ⚠️ 伪方案 | 纯语言不能建模物理世界，但可以处理语义上下文 |
| 保持当前贵庚架构 + 添加简单预测层 | ✅ **推荐路径** | 渐进式升级，不推倒重来 |

---

## 九、渐进式升级路径：从语义缓存到世界模型

### 阶段1：巩固语义缓存（当前状态，优化而非革命）

**改进方向**：
- 将FAISS升级到更快的向量索引（如HNSW）
- 使用更小的embedding模型（如E5-Mini而非Full E5）
- 增加时间衰减权重（新记忆更重要）
- 显式存储"机器人-用户交互序列"而不仅是问答对

**具体可执行改进**：
```
当前: 贵庚 = 语义缓存（sentence-transformer + FAISS）
       ↓ 仅检索
     LLM回复

改进: 贵庚 = 语义缓存 + 时间加权 + 交互状态机
       ↓ 检索 + 状态推断
     LLM回复
```

### 阶段2：轻量级潜在空间（1-3个月）

**目标**：在Jetson Nano上添加一个轻量级预测层

**技术方案A - 动作条件预测**：
- 使用一个小型CNN（~1-3M参数）将图像编码为z向量
- 使用另一个小型网络预测：`z' = f(z, a)`（z'是预测的下一帧表征）
- 在本地"想象"几个动作序列，选择最好的

**技术方案B - 语义预测（更务实）**：
- 不做图像潜在空间，而是做"语义状态预测"
- 用LLM维护一个"世界状态描述"，预测状态变化
- 优点：完全在语言层面，不需要感知编码器

**LeWM论文的关键启示**：
> *"LeWM plans up to 48× faster than foundation-model-based world models"*
> （LeWM比基于foundation model的世界模型规划速度快48倍）

→ 这说明轻量级世界模型不仅可行，而且效率远超高配方案。

### 阶段3：多模态感知编码（3-6个月）

**引入视觉编码器**：
- 使用MobileNet或EfficientNet-Lite作为视觉编码器
- 将图像压缩为固定长度的向量
- 这个编码器可以在桌面GPU上预训练，再部署到Jetson Nano

**开源参考实现**：
- LeWM GitHub: https://github.com/lucas-maes/le-wm
- VLA-JEPA: arXiv:2602.10098 - 视觉-语言-动作的JEPA扩展

### 阶段4：云端世界模型（6-12个月）

**架构**：
```
本地（Jetson Nano）:
  ESP32-Cam图像 → MobileNet编码 → z向量 → 压缩 → 发送到云端

云端（你的服务器）:
  接收z向量 → 世界模型预测 → 最佳动作建议 → 返回本地

本地:
  接收动作建议 → 执行 → 反馈结果 → 更新模型
```

**这个架构的优势**：
- 计算密集的世界模型推理在云端
- 本地只做轻量级感知编码
- 可以迭代升级云端模型而不影响硬件

### 阶段5：持续学习和适应（长期目标）

**参考AMI Labs的"persistent memory"**：
- 世界模型不是一次性训练的
- 持续从交互中学习新对象、新场景
- 使用自监督学习，不需要人工标注

---

## 十、世界模型 vs 语义检索：根本区别

### 10.1 语义检索（贵庚当前做法）

```
用户说: "我今天头疼"
     ↓
检索: 在FAISS中找最相似的历史记忆
     ↓
找到: "用户上周也提到过头疼"
     ↓
LLM回复: "您上周也有类似症状，建议..."
```

**问题**：这只是"记得以前说过什么"，不是"理解头疼意味着什么"。

### 10.2 世界模型（JEPA做法）

```
当前状态感知: 图像+语言 → z向量
     ↓
世界模型: 根据动作预测下一状态
  "如果我建议用户休息，ta的状态会如何变化？"
  "如果我询问症状细节，能获得什么信息？"
     ↓
在潜在空间中选择最佳动作序列
     ↓
执行动作 → 观察新状态 → 更新模型
```

**核心区别**：

| 维度 | 语义检索（贵庚） | 世界模型（JEPA） |
|------|----------------|----------------|
| **记忆形式** | 历史问答对 | 环境动态模型 |
| **预测能力** | 无，只能匹配 | 可以模拟"如果...会怎样" |
| **泛化能力** | 受限于见过哪些话 | 可以推理未见过的情况 |
| **计算需求** | 低（向量检索） | 高（需要训练和推理） |
| **对0-1的适用性** | 实用，当前可用 | 长期目标 |

### 10.3 0-1的务实选择

**不是"世界模型 vs 语义检索"，而是"两者结合"**：

```
短期（当前）:
  语义检索提供即时可用的上下文
  
中期（6-12个月）:
  添加轻量级世界模型层，在语义层面做简单预测
  例: "用户今天说了X，根据历史模型，ta可能在Y方面有困扰"
  
长期（1-2年）:
  逐步引入视觉潜在空间，实现真正的多模态世界模型
```

---

## 十一、医疗/陪伴场景的具体借鉴

### 11.1 Nabla世界模型对0-1的启示

**Nabla关注的医疗AI核心需求**（0-1陪伴机器人可类比）：

1. **持续上下文理解**：不是单次问答，而是跨时间的连续理解
   - 0-1可借鉴：追踪用户的情绪状态、作息规律、偏好变化

2. **多模态信号处理**：不只是文字，还有语音语调、面部表情
   - 0-1可借鉴：ESP32-Cam的图像流 + 麦克风音频 → 综合判断情绪

3. **确定性 vs 概率性**：医疗需要可靠的可审计决策
   - 0-1可借鉴：对于安全相关建议（如药物提醒），需要确定性而非LLM的随机输出

4. **"What-if"推理能力**：
   - *"If I ask about their sleep, what might I learn about their stress level?"*
   - 这个能力对0-1的"个性化陪伴"至关重要

### 11.2 0-1具体可实现的功能

基于AMI Labs思路，0-1在个人陪伴场景可以：

**已可行的**（改进语义缓存）：
- 记住用户的长期偏好和习惯
- 根据历史交互推断当前情绪状态
- 主动询问（而非被动响应）

**6-12个月内可行的**（加轻量预测层）：
- 在语言层面做"如果-那么"推理
- 预测用户可能需要什么（基于世界状态模型）
- 主动建议而非被动回答

**1-2年可能可行的**（加视觉编码器）：
- 识别用户表情、姿态、眼神
- 在视觉潜在空间中建模用户情绪
- 实现真正的"共情陪伴"

---

## 十二、关键结论和行动建议

### 12.1 核心结论

1. **AMI Labs的$1B融资**证明了世界模型不仅是学术方向，也是产业资本认可的方向
2. **JEPA路线**（LeWM展示的15M参数、单GPU、48倍加速）是可负担得起的世界模型实现路径
3. **LeWM的开源代码**（github.com/lucas-maes/le-wm）是目前最接近0-1约束的世界模型参考实现
4. **0-1不需要"追赶"AMI Labs**，而是需要借鉴其核心原则：学习表征、在潜在空间预测、持久记忆
5. **语义检索和世界模型不是互斥的**：0-1可以先优化当前的贵庚语义缓存，同时逐步引入世界模型层

### 12.2 0-1的3个月行动计划

```
Month 1:
  ├── 优化语义缓存：HNSW索引替换FAISS
  ├── 添加时间衰减权重
  └── 实现交互状态机（追踪"会话状态"）

Month 2:
  ├── 研究LeWM代码仓库（github.com/lucas-maes/le-wm）
  ├── 设计适合0-1的"简化版JEPA"
  └── 在服务器上尝试预训练小世界模型

Month 3:
  ├── 部署轻量级预测层到Jetson Nano
  ├── 实现基本的"what-if"推理
  └── 测试ESP32-Cam → Nano → 云端世界模型管道
```

### 12.3 最重要的借鉴：不要重新发明轮子

AMI Labs花费$1B解决的根本问题，0-1可以用以下方式利用：

1. **直接使用LeWM**：作为预训练世界模型，fine-tune到0-1的具体场景
2. **使用VL-JEPA的多模态编码思路**：但用更小的模型（如MobileNet）
3. **借鉴"persistent memory"概念**：但用更务实的方式实现（扩展语义缓存而非完整世界模型）
4. **学习SAI的设计原则**：专注于"适应速度"而非"知识广度"——0-1不需要知道一切，只需要对特定用户越来越了解

---

## 十三、引用来源

### AMI Labs官方

1. AMI Labs官网: https://amilabs.xyz/
2. AMI Labs Updates: https://amilabs.xyz/updates
3. Nabla + AMI Partnership Announcement: https://www.nabla.com/blog/ami-raises-1-03b-to-build-world-models----powering-the-next-generation-of-healthcare-ai-with-nabla

### 新闻报道

4. TechCrunch: "Yann LeCun's AMI Labs raises $1.03B to build world models" (2026-03-09): https://techcrunch.com/2026/03/09/yann-lecuns-ami-labs-raises-1-03-billion-to-build-world-models/
5. MIT Technology Review: "Yann LeCun's new venture is a contrarian bet against large language models" (2026-01-22): https://www.technologyreview.com/2026/01/22/1131661/yann-lecuns-new-venture-ami-labs/
6. HPC Wire: "Yann LeCun's AMI Secures $1B Seed to Develop AI World Models" (2026-03-11): https://www.hpcwire.com/aiwire/2026/03/11/yann-lecuns-ami-secures-1b-seed-to-develop-ai-world-models/
7. Venture Beat/WIRED相关报道

### 学术论文

8. **LeWorldModel (LeWM)**: arXiv:2603.19312 (2026-03-13): https://arxiv.org/abs/2603.19312 | https://le-wm.github.io/
9. **SAI**: arXiv:2602.23643v1: https://arxiv.org/pdf/2602.23643v1
10. **LeJEPA**: arXiv:2511.08544 (2025-11): https://arxiv.org/abs/2511.08544
11. **Value-guided action planning with JEPA world models**: arXiv:2601.00844: https://arxiv.org/abs/2601.00844
12. **VLA-JEPA**: arXiv:2602.10098: https://arxiv.org/abs/2602.10098

### 技术分析

13. Themesis: "World Models: Five Competing Approaches" (2026-01-07): https://themesis.com/2026/01/07/world-models-five-competing-approaches/
14. MarkTechPost: "Yann LeCun's New AI Paper Argues AGI Is Misdefined and Introduces Superhuman Adaptable Intelligence (SAI) Instead" (2026-03-07): https://www.marktechpost.com/2026/03/07/yann-lecuns-new-ai-paper-argues-agi-is-misdefined-and-introduces-superhuman-adaptable-intelligence-sai-instead/
15. Analytics India Mag: "Yann LeCun Builds a World Model That Runs on a Single GPU": https://analyticsindiamag.com/ai-news/yann-lecun-builds-a-world-model-that-runs-on-a-single-gpu
16. evoai labs: "LeWorldModel: 15 Million Parameters to Map the World": https://evoailabs.medium.com/leworldmodel-15-million-parameters-to-map-the-world-9a0b37581279
17. SignalFire: "The missing piece in robotics: A model of the world": https://www.signalfire.com/blog/missing-piece-in-robotics-a-world-model
18. LeWM GitHub: https://github.com/lucas-maes/le-wm

---

*报告完成于 2026-03-30*
*主要研究工具: Tavily Web Search, Web Fetch*
*研究覆盖范围: AMI Labs官方信息、TechCrunch/VentureBeat/WIRED/mittechreview新闻报道、arXiv学术论文、技术分析博客*
