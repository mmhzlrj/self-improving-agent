# 第一轮核查报告：SOP v3.12-v3.20 新增内容

**调研时间**：2026-03-24 22:35-22:40
**调研方式**：3 个 subagent 并行，web_search + web_fetch 验证
**限速情况**：未触发

---

## 🔴 高优先级修正（需立即修正）

### 1. GRPO 与 RynnBrain 混淆
**问题**：SOP 在 RynnBrain 的"记忆更新机制"段落里写了 GRPO 训练参数（Group size G=5、KL β=0.02 等），但 RynnBrain 是具身智能模型，GRPO 是强化学习训练方法，两者**完全无关**。

**修正方案**：把这些 GRPO 参数移至 OpenClaw RL 部分，RynnBrain 章节删除这些内容。

**来源**：Agent 1 + Agent 3 独立核实

**用户审批结果**：❌ 拒绝

**用户备注**：
> 不能这样乱移动。OpenClaw RL 是单独开源的 skill，你为什么要这样随便移动？
> RynnBrain GRPO 训练参数均来自阿里达摩院官方技术报告（arXiv:2602.14979v1），是 RynnBrain-CoP 模型对齐训练使用的官方 GRPO 配置：
> - 组大小 G=5，KL β=0.02，clip_range [0.2, 0.28]
> - 训练轮次 10，batch size 128，max_context 16384 tokens
> - 学习率余弦调度，warmup 3%，SGLang Rollout
> - DeepSpeed ZeRO-1（2B/8B）/ ZeRO-2+EP（30B MoE）
> - 奖励函数：弗雷歇距离/Chamfer距离空间精度奖励 + 格式合规奖励 + KL约束奖励

**结论**：GRPO 参数保留在 RynnBrain 章节，SOP 无需修改。

---

### 2. AMD AI Halo "1 PFLOPS" 严重夸大
**问题**：SOP 写"1 PFLOPS 算力"，实际最强消费级 RTX 4090 才 80-90 TFLOPS。

**修正方案**：改为"预估 GPU 算力约 30-50 TFLOPS（INT4/INT8 稀疏算力可能更高，需实测确认）"。

**来源**：Agent 2 核实

**用户审批结果**：❌ 拒绝

**用户备注**：
> 最强消费级 RTX 4090 已经是过去式，它不是 AI 专用显卡。现在最新是 RTX 5090，5090Ti 也即将发布。AMD AI Halo 官方参数请查阅官方页面。

**AMD Ryzen AI Max+ 395（Strix Halo）官方参数（2026-03-25 查证）**：

| 指标 | 数值 | 说明 |
|------|------|------|
| NPU TOPS | 最高 50 TOPS | XDNA 2 架构 |
| Total Platform AI TOPS | 最高 126 TOPS | NPU + GPU 合计 |
| GPU FP32 | ~14.85 TFLOPS | RDNA 3.5，40 CU，2900 MHz |
| GPU FP16/BF16 | ~29.70 TFLOPS | FP32 的 2 倍 |
| INT8 稀疏 | 支持 | XDNA 2 NPU 原生支持 |
| INT4 稀疏 | 支持（软件层） | ONNX-GenAI / Vulkan llama.cpp |

**结论**：修正为官方参数，删除"1 PFLOPS"错误描述。

---

## 🟡 中优先级修正

### 3. 星闪"三模"不准确
**问题**：SOP 称星闪为"三模"，不够准确。

**修正方案**：改为"SLE+SLB 双模式"或"某些模组同时集成 BLE+星闪+WiFi 三芯片"。

**来源**：Agent 2

**用户审批结果**：❌ 拒绝

**用户建议修正方案**：
> 改为：小熊派WS63星闪开发板BearPi-Pico H3863 芯片WiFi6 BLE SLE模组

**结论**：按用户建议修改 SOP 描述。

---

### 4. Jetson "2070 TFLOPS" 单位错误
**问题**：Jetson "2070 TFLOPS" 实际是 INT8 TOPS，不是 TFLOPS。

**修正方案**：改为"INT8 TOPS（稀疏算力）"或直接写"TOPS"而非"TFLOPS"。

**来源**：Agent 2

**用户审批结果**：❌ 拒绝

**用户备注**：
> 把不同的情况下的算力都找到然后写清楚。

**待补充**：Jetson AGX Thor 各精度真实算力数据（FP16/BF16/INT8/TOPS），需进一步调研。

**结论**：待获取完整数据后更新 SOP。

---

### 5. SSD 2280 16TB 不存在
**问题**：消费级 2280 16TB SSD 基本不存在。

**修正方案**：改为"工业级 15.36TB"并注明消费级基本不存在。

**来源**：Agent 2

**用户审批结果**：❌ 拒绝

**用户备注**：
> 我又没有说是消费级 SSD 2280 16TB，而且工业级都出来了，消费级还会远吗，我又不是现在采购。

**结论**：SOP 无需修改，保持原描述。

---

### 6. Project Silica 容量数据过时
**问题**：SOP 写 100GB/片，为 2022 POC 早期数据；2023年已达 7TB。

**修正方案**：改为"实验室最新 7TB（2023年），100GB 为 2022 POC 早期数据"。

**来源**：Agent 1

**用户审批结果**：❌ 拒绝

**用户备注**：
> 除了补充最新的数据，还要补充国产的数据。国产的也有了。

**待补充**：Project Silica 最新容量数据 + 国产玻璃光学存储数据。

**结论**：待获取完整数据后更新 SOP。

---

### 7. screenray.exe 名称不准确 ✅ 已采纳
**问题**：SOP 写 screenray.exe，实际应为 Snapshot Service（微软官方名称）。

**修正方案**：改为"Snapshot Service"（微软官方名称）。

**来源**：Agent 1

**用户审批结果**：✅ 采纳

**SOP 修改**：screenray.exe → Snapshot Service（微软官方名称）

---

### 8. Recall 向量引擎推测错误
**问题**：SOP 称 Recall 使用 Faiss，实际可能使用微软自研 DiskANN。

**修正方案**：改为"推测使用 DiskANN（微软自研），待核实"。

**来源**：Agent 1

**用户审批结果**：❌ 拒绝

**用户备注**：
> 这里应该两个都记录上，然后写待核实。

**结论**：同时记录 Faiss 和 DiskANN 两种可能，注明"待核实"。

---

### 9. Recall Phi-3.5-mini 型号未确认
**问题**：SOP 指定了 Phi-3.5-mini，但该型号未被官方确认。

**修正方案**：改为"使用轻量级交叉编码器"（不指定型号）。

**来源**：Agent 3

**用户审批结果**：❌ 拒绝

**用户备注**：
> 如果都是没有准确的答案的情况下，SOP 指定了 Phi-3.5-mini，但该型号未被官方确认。这样的描述比"使用轻量级交叉编码器"（不指定型号）描述更好。因为如果是知道错的人，会直接说出来他知道对的型号。而不知道的人，会觉得有型号会比没型号做的更专业。而且这个型号也代表了轻量级交叉编码器的意思。

**结论**：保持 Phi-3.5-mini 描述，SOP 无需修改。

---

### 10. RynnBrain GRPO β=0.02 参数无法核实
**问题**：该参数来源无法核实。

**修正方案**：删除此参数。

**来源**：Agent 1

**用户审批结果**：❌ 拒绝

**用户备注**：
> RynnBrain GRPO 训练参数均来自阿里达摩院官方技术报告（arXiv:2602.14979v1），是 RynnBrain-CoP 模型官方 GRPO 配置（见 item-1 完整参数列表）。

**结论**：GRPO 参数保留，来源标注为"阿里达摩院官方技术报告 arXiv:2602.14979v1"。

---

### 11. RynnBrain 94% 保留率数据无法核实
**问题**：该数据来源无法核实。

**修正方案**：删除此数据。

**来源**：Agent 1

**用户审批结果**：❌ 拒绝

**用户备注**：
> 该数据最早由阿里达摩院 RynnBrain 官方团队在 2026 年 2 月模型开源发布时同步披露，来自《阿里 RynnBrain 具身智能开源登顶!30B MoE 时空记忆架构，16 项评测超谷歌 Gemini》权威技术解读，以及 arXiv:2602.14979v1 论文附录、官方发布会。

**结论**：94% 保留率数据保留，来源标注为"阿里达摩院官方发布（2026年2月）"。

---

### 12. Neo4j TimeTree 插件状态待确认
**问题**：TimeTree 插件状态待官方确认。

**修正方案**：改为"可用 Neo4j 内置时间属性替代，TimeTree 插件状态待确认"。

**来源**：Agent 3

**用户审批结果**：❌ 拒绝

**用户备注**：
> 该插件已正式退役（RETIRED），官方仓库已于 2021 年 5 月归档，最终版本 3.5.14.58.29 仅兼容 Neo4j 3.5.x，不支持 4.x/5.x。推荐替代方案：原生 Cypher 时间函数+索引、APOC 扩展库、手动构建时间树模型、Neo4j GDS 图数据科学库。

**结论**：修正为"已退役（RETIRED），推荐使用原生 Cypher 时间函数 或 APOC 扩展"。

---

## ✅ 确认无误（无需修改）

以下技术点经核查属实，无需修改 SOP：

- RynnBrain 存在、2B/8B/30B 版本、Apache 2.0
- RynnBrain 基于 Qwen3-VL、CoP 推理机制
- Mem0 Graph+Vector 支持、本地部署
- Windows Recall VBS Enclave + TPM 架构
- OpenClaw RL 真实存在、GRPO/OPD/Combination 三方法
- Whisper large-v3、支持中文方言
- H.266 比 H.265 省 20-50% 码率
- Project Silica 石英玻璃、300年+ 存储年限
- Qwen3-VL 开源、Apache 2.0
- Jetson AGX Thor $3,499、Blackwell 架构
- 星闪 SLE 2Mbps、低延迟 <20μs

---

## 修正优先级排序

1. **✅ 已完成**：screenray.exe → Snapshot Service
2. **待修正（需额外调研）**：Jetson 算力数据、Project Silica 最新+国产数据
3. **按用户指示修正**：AMD AI Halo（官方参数）、星闪（具体型号名）
4. **无需修改**：GRPO 参数、94% 保留率、SSD、工业级说明、Phi-3.5-mini 描述
5. **需补充**：Recall 向量引擎（Faiss + DiskANN 双记录）、TimeTree 替代方案
