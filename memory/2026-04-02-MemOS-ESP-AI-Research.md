# 调研报告：MemOS + ESP-AI 对 0-1 项目的价值分析

> **调研时间**: 2026-04-02
> **调研人**: 主 Agent
> **工具1**: MemOS（memos-claw / MemOS-Cloud-OpenClaw-Plugin）
> **工具2**: ESP-AI（wangzongming/esp-ai）

---

## 一、MemOS（memos-claw）调研

### 1.1 是什么

MemOS 是 MemTensor 开发的 AI 记忆操作系统，有两个 OpenClaw 相关产品：

| 产品 | 类型 | 定位 |
|------|------|------|
| **MemOS-Cloud-OpenClaw-Plugin** | 云服务插件 | OpenClaw 生命周期插件，自动 recall/add |
| **MemOS Local (memos-local)** | 本地插件 | 完全本地化，SQLite 存储，零云依赖 |

**核心数字**：
- Token 节省：72% vs 加载完整对话历史
- 准确率：+43.70% vs OpenAI Memory（Benchmark）
- 多智能体共享：同一 user_id 跨实例共享记忆

### 1.2 核心功能

| 功能 | 说明 | 对应 0-1 已有能力 |
|------|------|------------------|
| 全量写入（Full-Write） | 每次对话自动语义分片持久化 | Semantic Cache（部分重叠） |
| 任务总结（Tasks） | 碎片对话归纳为结构化任务 | 无 |
| 技能进化（Skill Evolution） | 任务提炼为可复用技能并持续升级 | 无 |
| 混合检索（Hybrid Search） | 向量 + BM25 混合召回 | Semantic Cache（重叠） |
| 多智能体记忆共享 | 同 user_id 跨实例共享 | 无（Semantic Cache 仅本地） |
| 分级模型配置 | embedding/summarizer/recall 可用不同模型 | 部分（当前 embedding 在 Ubuntu） |

### 1.3 安装方式

**MemOS Cloud 插件**：
```bash
openclaw plugins install github:MemTensor/MemOS-Cloud-OpenClaw-Plugin
```
配置 `memosApiUrl` + API Key 即可。

**MemOS Local**：
```bash
openclaw plugins install github:MemTensor/memos-local
```
本地 SQLite Viewer 监听 `127.0.0.1:18799`。

### 1.4 与现有 Semantic Memory 的关系

**重叠部分**：
- 语义存储 + 检索（FAISS vs 向量数据库）
- 会话历史持久化
- 跨 session 上下文注入

**MemOS 多出的能力**：
- 技能进化（从对话中提炼可复用技能）
- 任务归纳（碎片 → 结构化任务）
- 多智能体共享（一个 user_id，多个 agent 实例共享）
- 更成熟的 Viewer UI（网页面板）

**当前 0-1 Semantic Memory 架构**：
```
MacBook Gateway
  └── Smart Context Hook（session 前注入语义上下文）
        └── curl → Ubuntu:5050 Semantic Cache
              └── sentence-transformers + FAISS
```

**结论**：MemOS Local 可以作为 Semantic Cache 的**替代方案**，也可以作为**冗余备份**（Ubuntu 离线时的 fallback）。两者的核心能力高度重叠，不建议同时运行。

---

## 二、ESP-AI 调研

### 2.1 是什么

ESP-AI 是 wangzongming 开发的开源 AIoT 开发平台，GitHub: `wangzongming/esp-ai`（⭐ 6.9k）。

**核心理念**：为硬件设备注入 AI 灵魂，最低成本、最简单方案。

**技术栈**：
- 服务端：Node.js（`esp-ai` npm 包）
- 客户端：Arduino / ESP-IDF（烧录到 ESP32）
- 支持芯片：ESP32-S3、ESP32-C3、XIAO ESP32-S3

### 2.2 核心功能

| 模块 | 支持服务 | 说明 |
|------|---------|------|
| **ASR（语音识别）** | 火山引擎（免费额度）、阿里云 | 唤醒词检测 + 语音转文字 |
| **LLM（大模型）** | 豆包、DeepSeek-R1 等 | 云端推理 |
| **TTS（语音合成）** | 火山引擎（免费额度）、阿里云 | 文字转语音 |
| **NLP（语义判断）** | — | 相同语义判断 |
| **知识库 RAG** | — | 知识库检索 |
| **自定义插件** | NPM 插件市场 | 扩展 ASR/LLM/TTS |

### 2.3 硬件要求

| 组件 | 推荐型号 | 成本 |
|------|---------|------|
| 主芯片 | ESP32-S3（带 PSRAM）| ~¥30-50 |
| 麦克风阵列 | 天问 ASR Pro（唤醒模块）| ~¥50-80 |
| 或 | I2S 数字麦克风（直接连接）| ~¥10-20 |
| **总计** | | **¥40-130** |

**对比当前 0-1 方案**：

| 方案 | 组件 | 成本 | 复杂度 |
|------|------|------|--------|
| **现有方案** | Jetson Nano + USB 麦克风 + Python 语音链 | ¥2000+ | 高（需自己写 ASR/TTS 链路） |
| **ESP-AI 方案** | ESP32-S3 + 天问 ASR + 云端 LLM | ¥80-130 | 低（几行代码接入） |

### 2.4 代码示例（对话功能）

**Node.js 服务端**（最简）：
```javascript
const ESP = require('esp-ai')
ESP.start({
  // 火山引擎 ASR
  iat_config: { api_key: 'xxx', voice: 'zh_female' },
  // 豆包 LLM
  llm_config: { api_key: 'xxx', model: 'doubao-pro' },
  // TTS
  tts_config: { api_key: 'xxx', voice: 'zh_male' },
  onLLMText: (text) => console.log('LLM 说:', text),
  onTTSEnd: () => console.log('TTS 播放完成')
})
```

**Arduino 客户端**（最简）：
```cpp
#include <esp-ai.h>
void setup() {
  ESP_AI.begin();
}
void loop() {
  ESP_AI.update();
}
```

### 2.5 与 0-1 项目的关联

**Phase 0-1（语音陪伴）**需求：
- 唤醒词检测（关键词触发）
- 语音转文字（ASR）
- 大模型对话（LLM）
- 文字转语音（TTS）

**ESP-AI 能做到**：
- ✅ 唤醒词检测（天问 ASR Pro 模块，支持引脚/串口唤醒）
- ✅ ASR（火山引擎免费额度，1 额度/次）
- ✅ LLM（豆包、DeepSeek-R1 等）
- ✅ TTS（支持克隆自定义音色，15秒音频即可）
- ✅ 本地处理部分逻辑（ESP32 固件）

**ESP-AI 不能做到**（需要 Jetson Nano 处理）：
- 本地视觉处理
- 实时视频流
- 重计算量 AI 推理

**结论**：ESP-AI 是 Phase 0-1 语音模块的**最佳性价比选择**。低成本、低门槛、快速验证。

---

## 三、对比总结

### 3.1 功能重叠分析

| vs 现有工具 | MemOS | ESP-AI |
|------------|-------|--------|
| Semantic Cache | ⚠️ 重叠（可替代或互补）| ❌ 不重叠 |
| Smart Context Hook | ⚠️ 功能类似（可整合）| ❌ 不重叠 |
| Phase 0-1 语音 | ❌ 不重叠 | ✅ **直接满足** |
| Jetson Nano 视觉 | ❌ 不重叠 | ❌ 不重叠 |

### 3.2 推荐决策

| 工具 | 建议 | 理由 |
|------|------|------|
| **MemOS Local** | ⭐ **可引入，评估后决定是否替换 Semantic Cache** | 功能比 Semantic Cache 更完整，Viewer UI 好，但需要评估稳定性 |
| **MemOS Cloud** | ❌ 暂不引入 | 云服务有隐私风险，0-1 数据本地优先 |
| **ESP-AI** | ✅ **Phase 0-1 语音推荐方案** | 成本极低（¥80-130），代码量少，托管在 GitHub 活跃维护 |

---

## 四、A 序列任务建议

建议拆分为两个 A 序列任务：

### Task A19：MemOS Local 评估与集成测试
**目标**：评估 MemOS Local 能否替代或增强现有 Semantic Cache
**验收标准**：
1. MemOS Local 安装成功，Viewer 可访问
2. 对比测试：相同 query 下 MemOS vs Semantic Cache 的召回质量
3. Skill Evolution 功能验证
4. 决定是否替换现有 Semantic Cache

### Task A20：ESP-AI 语音模块接入 Phase 0-1
**目标**：用 ESP-AI 实现 Phase 0-1 语音对话能力
**验收标准**：
1. ESP32-S3 + 天问 ASR 固件烧录成功
2. Node.js 服务端启动成功
3. 唤醒词触发 → ASR → LLM → TTS 全链路测试通过
4. 与 Jetson Nano 的通信接口定义（UART/I2C 待定）

---

## 五、参考链接

| 资源 | 链接 |
|------|------|
| MemOS GitHub | https://github.com/MemTensor/MemOS |
| MemOS-Cloud OpenClaw Plugin | https://github.com/MemTensor/MemOS-Cloud-OpenClaw-Plugin |
| memos-local 安装文档 | https://memos-claw.openmem.net/docs/index.html |
| ESP-AI GitHub | https://github.com/wangzongming/esp-ai |
| ESP-AI 开放平台 | https://espai.fun |
| ESP-AI 升级日志 | https://espai2.fun/change-logs/ |
