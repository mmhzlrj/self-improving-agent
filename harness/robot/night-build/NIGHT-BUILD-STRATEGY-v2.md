# Night Build 两步法策略 v2

> 2026-03-26 12:28 基于 6 轮白天测试 + 全文审核 + 交叉验证的经验总结

---

## 核心发现

### MiniMax 审核的能力边界
- ✅ 找问题能力强（幻觉率 0%，不会编造）
- ⚠️ 事实判断准确率 75%（17% 误报率）
- ❌ 知识过时（Qwen3.5 2026年2月发布，MiniMax 不知道）
- ❌ 自我验证有盲区（用自己的知识验证自己的判断 = 循环论证）

### 五平台验证的能力
| 平台 | 擅长 | 发现 |
|------|------|------|
| DeepSeek | 最新信息、AI 模型版本 | 发现 MiniMax 漏判的 Qwen3.5 |
| 豆包 | 技术规格、芯片 datasheet | Hi3863V100 Flash、ROS2 支持平台 |
| Kimi | 学术事实、开源项目 | DOF、Whisper 模型、GitHub 组织名 |
| GLM | 产品信息、发布日期 | Jetson Thor、Phi-3.5 架构 |
| 千问 | 通用 | 可能超时，作为降级备选 |

### 误报的 3 种模式
1. **知识过时**: V01 — Qwen3.5 存在但 MiniMax 不知道
2. **反向误判**: V04 — 文档写的 4MB 是对的，MiniMax 说 2MB
3. **过度质疑**: V12 — 正确的 GitHub 地址被怀疑

---

## 三步法工作流

### 第一步：MiniMax Subagent 审核

**目标**: 找出所有潜在问题

**分段策略（改进）**:
- 基于标题结构分段（用 ground-truth-headings.json）
- 每段 200-300 行（避免 500 行段 tokens 爆炸）
- 分段时记录实际标题名，确保 subagent 任务描述准确

**Prompt 改进点**:
```
问题类型限定（英文枚举）:
- factual_error: 事实性错误（数据、规格、版本号）
- missing_source: 来源缺失
- data_missing: 数据缺失
- logic_contradiction: 逻辑矛盾
- format_issue: 格式问题
- incomplete: 内容不完整
- duplicate: 重复内容
- other: 其他

line_approx: 整数或 null，禁止使用范围值

重要指令:
「如果不确定某条是否真的是问题，不要报。宁可漏报也不要误报。」
「事实性声明只在你确信正确的情况下才报告为 factual_error。」
「如果需要联网验证才能确认，标记为 needs_verification 而不是 factual_error。」

JSON 验证:
写入文件后执行: python3 -c "import json; json.load(open('文件路径'))"
如果报错，修复后重新写入。
```

**并发控制**:
- OpenClaw 限制: 最多 5 个并发 subagent
- 流水线: 完成 1 个补派 1 个
- 20:00-01:00（非高峰）: 最多 3 个 MiniMax 并发
- 01:00-06:00（高峰）: 最多 1 个

**预期输出**: 每段 result.json + 问题汇总

---

### 第二步：五平台交叉验证

**目标**: 验证事实性声明，排除误报

**筛选规则**:
- 只验证 severity=high 中的事实性声明
- 排除: 纯逻辑矛盾、格式问题（这些不需要联网验证）
- 保留: factual_error、missing_source、data_missing、URL 错误

**平台分工**:
```python
platform_assignment = {
    "AI 模型版本/发布": "deepseek",      # Qwen3.5、GPT-5 等
    "芯片/硬件规格": "doubao",            # Hi3863V100、Jetson 等
    "开源项目/GitHub": "kimi",            # Genesis、GO-1 等
    "软件/框架能力": "glm",               # ROS2、Whisper、Phi-3.5 等
    "通用/其他": "deepseek",              # 默认用 DeepSeek
    "降级备选": "qwen",                   # 其他平台超时时用
}
```

**执行方式**:
- GLM 主 agent 直接调用（不用 MiniMax subagent）
- 并行调用 4-5 个平台
- 每个声明 1 个平台验证即可（不需要全平台验证）
- 如果超时，自动用降级平台补位

**验证输出**:
```json
{
    "verdict": "verified | false_alarm | needs_attention | inconclusive",
    "platform": "deepseek",
    "evidence": "关键证据",
    "source_url": "https://...",
    "correct_info": "正确信息（如果误报）"
}
```

---

### 第三步：修正建议生成（新增）

**目标**: 对 verified 的问题生成可执行的修正方案

**触发条件**: 第二步验证完成后

**修正范围**:
- verified → 生成修正建议
- false_alarm → 标注为「审核误报」，不修正
- needs_attention → 标注，等用户决定
- inconclusive → 不修正

**修正建议格式**:
```json
{
    "issue_id": "S18-H03",
    "type": "factual_error",
    "location": "第 4243 行",
    "original": "github.com/applecartn/genesis",
    "suggested": "https://github.com/Genesis-Embodied-AI/Genesis",
    "reason": "原 URL 返回 404，正确仓库地址为 Genesis-Embodied-AI 组织",
    "source": "https://github.com/Genesis-Embodied-AI/Genesis",
    "verified_by": "deepseek + kimi"
}
```

**写入位置**: `night-build/output/{date}/fixes/fix-SS-HNN.json`
**绝不修改原始 ROBOT-SOP.md**

---

## 额度消耗

| 步骤 | MiniMax 额度 | 其他额度 |
|------|-------------|---------|
| 第一步审核 | ~40 次 | — |
| 第二步验证 | 0 次 | 各平台 ~50 次聊天 |
| 第三步修正 | 0 次 | — |
| **总计** | **~40 次** | — |

**远低于 1800 次上限**，剩余额度可用于其他任务。

---

## Orchestrator 时间线（今晚）

| 时间 | 动作 |
|------|------|
| 20:05 | 开始审核（20 段，流水线派发） |
| 20:05-21:00 | 审核进行中（预计 40-60 分钟） |
| 21:00 | 审核完成，开始交叉验证 |
| 21:00-21:30 | 五平台验证（预计 20-30 分钟） |
| 21:30-22:00 | 生成修正建议 |
| 09:50 | 向用户汇报（summary + 修正建议） |

---

## 已知局限

1. **五平台验证非全自动**: 需要主 agent 介入调度，不能完全无人值守
2. **千问不稳定**: 经常超时，不能作为主要验证平台
3. **部分声明难以验证**: 比如文档内部的逻辑矛盾，需要人工判断
4. **修正建议需要人工审核**: 不自动应用修正

## 迭代计划

- **今晚**: 首次用 v2 策略运行完整三步法
- **明早**: 根据结果优化 prompt 和分段策略
- **后续**: 逐步实现全自动 orchestrator（cron 任务触发）
