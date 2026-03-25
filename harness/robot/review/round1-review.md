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

---

### 2. AMD AI Halo "1 PFLOPS" 严重夸大
**问题**：SOP 写"1 PFLOPS 算力"，实际最强消费级 RTX 4090 才 80-90 TFLOPS。

**修正方案**：改为"预估 GPU 算力约 30-50 TFLOPS（INT4/INT8 稀疏算力可能更高，需实测确认）"。

**来源**：Agent 2 核实

---

## 🟡 中优先级修正

### 3. 星闪"三模"不准确
**问题**：SOP 称星闪为"三模"，不够准确。

**修正方案**：改为"SLE+SLB 双模式"或"某些模组同时集成 BLE+星闪+WiFi 三芯片"。

**来源**：Agent 2

---

### 4. Jetson "2070 TFLOPS" 单位错误
**问题**：Jetson "2070 TFLOPS" 实际是 INT8 TOPS，不是 TFLOPS。

**修正方案**：改为"INT8 TOPS（稀疏算力）"或直接写"TOPS"而非"TFLOPS"。

**来源**：Agent 2

---

### 5. SSD 2280 16TB 不存在
**问题**：消费级 2280 16TB SSD 基本不存在。

**修正方案**：改为"工业级 15.36TB"并注明消费级基本不存在。

**来源**：Agent 2

---

### 6. Project Silica 容量数据过时
**问题**：SOP 写 100GB/片，为 2022 POC 早期数据；2023年已达 7TB。

**修正方案**：改为"实验室最新 7TB（2023年），100GB 为 2022 POC 早期数据"。

**来源**：Agent 1

---

### 7. screenray.exe 名称不准确
**问题**：SOP 写 screenray.exe，实际应为 Snapshot Service（微软官方名称）。

**修正方案**：改为"Snapshot Service"（微软官方名称）。

**来源**：Agent 1

---

### 8. Recall 向量引擎推测错误
**问题**：SOP 称 Recall 使用 Faiss，实际可能使用微软自研 DiskANN。

**修正方案**：改为"推测使用 DiskANN（微软自研），待核实"。

**来源**：Agent 1

---

### 9. Recall Phi-3.5-mini 型号未确认
**问题**：SOP 指定了 Phi-3.5-mini，但该型号未被官方确认。

**修正方案**：改为"使用轻量级交叉编码器"（不指定型号）。

**来源**：Agent 3

---

### 10. RynnBrain GRPO β=0.02 参数无法核实
**问题**：该参数来源无法核实。

**修正方案**：删除此参数。

**来源**：Agent 1

---

### 11. RynnBrain 94% 保留率数据无法核实
**问题**：该数据来源无法核实。

**修正方案**：删除此数据。

**来源**：Agent 1

---

### 12. Neo4j TimeTree 插件状态待确认
**问题**：TimeTree 插件状态待官方确认。

**修正方案**：改为"可用 Neo4j 内置时间属性替代，TimeTree 插件状态待确认"。

**来源**：Agent 3

---

## ✅ 确认无误

以下技术点经核查属实，无需修改：

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

1. **立即修正**：GRPO 参数从 RynnBrain 章节移至 OpenClaw RL；AMD AI Halo 算力数据修正
2. **第二轮修正**：其余 10 项中低优先级问题
3. **待用户确认**：部分描述的修正方向是否正确
