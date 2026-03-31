# MiniMax Subagent 最佳实践

> 持续更新，每晚迭代。每次 Night Build 后根据结果更新此文件。
>
> **Harness Engineering Skill（必须遵循）**：`../../skills/harness-engineering/SKILL.md`
>
> **用户做事风格 Contracts**：`../../skills/harness-engineering/contracts.md`

---

## 已知事实（来自白天手动测试）

### 模型能力边界
- MiniMax 处理 500 行输入：⚠️ 后半段信息丢失
- MiniMax 处理 300 行输入：✅ 稳定（代码密集区除外）
- MiniMax 处理 1000 行输入：❌ 不可靠
- MiniMax 多步指令（标题提取类）：❌ 几乎必然跳步
- MiniMax 多步指令（审核类，每步独立输出文件）：✅ 3/3 成功
- MiniMax 单动词任务：✅ 成功率 >90%
- 硬超时：10 分钟，超时后直接中断

### read 工具已知问题
- **offset=1 时行号偏移 7-14 行**，offset>1000 时行号正确
- **代码密集区域截断**：300 行的 limit 可能只返回 224 行
- **截断原因**：按字符数截断，非按行数。代码块行更长
- **结论：不要用 read 工具做精确内容提取**

### JSON 输出已知问题
- MiniMax 可能在 JSON 字符串中嵌入未转义引号（`"这4行"第5列空""`）
- **解决方案**：prompt 中明确要求"JSON 字符串中禁止使用双引号，用「」替代"
- 或：让输出为纯文本/Markdown，由另一个脚本解析

### 已验证的失败模式
- 给"先A再B"指令 → 只执行 B（2026-03-25 目录补全）
- 改编号不改内容 → 只改标题行不移动正文（2026-03-25 Phase 排序）
- 大文件 read + 多处 edit → 超时 9m59s（2026-03-25）
- 高峰期 3 个 subagent 并行 → 限流排队/超时（2026-03-24）
- read 工具 + 行号报告 → 行号偏移不固定（2026-03-26）
- read 工具 + 代码密集区 → 内容截断（2026-03-26）
- 脚本+人工混合模式 → 漏掉 high severity 问题（2026-03-26）

### 已验证的成功模式
- exec + grep/sed/awk 精确提取 → 100% 准确
- exec + sed 按行号读取 → 内容完整，不截断
- JSON 模板约束输出 → 格式一致（注意引号问题）
- 多步审核（每步独立输出文件）→ 3/3 完成，0 幻觉
- 单任务只读不写 → 安全不出错

---

## 任务类型 → 最佳策略映射

| 任务类型 | 最佳策略 | 准确率 | 备注 |
|---------|---------|--------|------|
| **文本提取**（标题/链接/代码） | exec + grep/sed/awk | 100% | 绝对不要用 read 工具 |
| **内容审核**（找逻辑问题） | R 组：exec+sed 多步 | 9 high/27 total | 每步独立输出文件 |
| **章节重写/补充** | A 组：原子任务（待测） | — | 预计更安全 |
| **脚本辅助审核** | 不推荐 | 0 high | 过滤误报时漏掉真实问题 |
| **混合任务**（提取+审核） | 拆成两个 subagent | — | 各自做擅长的事 |

---

## A/B 测试记录

### 2026-03-26 白天迭代测试（6 轮）

#### 测试 1：标题提取 v1（500行/段）→ ❌ 失败
- A01: 13/20 标题，行号全错，后 100 行丢失
- 结论：500行太长，行号不可信

#### 测试 2：标题提取 v2（300行/段 + 行号公式）→ ⚠️ 部分成功
- A01(开头): 11/11 文字匹配，行号错(偏7-14行)
- A08(中间): 24/24 完美匹配 ✅
- A14(尾部): 12/20 文字匹配，read 截断(224/300行)
- 结论：中间段可靠，开头行号偏移，代码区截断

#### 测试 3：grep 命令提取 → ✅ 完美
- exec + `grep -n '^#'` = 347/347 标题，100% 准确
- 结论：文本提取任务应用 exec/bash，不用 read 工具

#### 测试 4：内容审核（A组 vs B组）→ ✅ 两方案都可用

| 组 | 任务 | 章节 | 总问题 | 🔴 High | 幻觉 | 耗时 | tokens |
|----|------|------|--------|---------|------|------|--------|
| AR01 | 原子 | §2.7 | 3 | 1 | 0 | 43s | 5.9k |
| BR01 | 多步read | §2.6+2.7+2.8 | 18 | 3 | 0 | 2m30s | 54.2k |

- B 组多步在审核任务上成功（3/3，0 跳步）
- B 组发现更多 high severity 问题

#### 测试 5：exec+sed 多步审核 vs 脚本+人工混合 → ✅ R 组胜出

| 组 | 方法 | 章节 | 总问题 | 🔴 High | 幻觉 | 耗时 | tokens |
|----|------|------|--------|---------|------|------|--------|
| BR01 | 多步 read | 3章 | 18 | 3 | 0 | 2m30s | 54.2k |
| R01 | 多步 exec+sed | 3章 | **27** | **9** | 0 | 2m55s | 48.6k |
| H01 | 脚本+人工 | §2.7 | 11 | **0** | 0 | 1m53s | 37.1k |

**R01 vs BR01 关键差异**：
- R01 发现 **9 个 high** vs BR01 的 3 个（+200%）
- R01 总问题 27 vs BR01 的 18（+50%）
- R01 tokens 更少（48.6k vs 54.2k）——exec+sed 内容更精确
- **原因**：exec+sed 返回完整内容，read 工具在某些区域截断

**R01 发现的重要文档错误**（BR01 漏掉的）：
- Qwen3.5 系列可能不存在（应为 Qwen3 或 Qwen2.5）
- Ryzen AI Max+ 392 型号可能不存在（只有 385/395）
- RDNA 5/Zen 6/2nm 混在正式规格中未区分
- AI 算力 4-10x vs 2-3x 同一指标矛盾
- Genesis 43M FPS 数值异常
- LD-2209 舵机型号无法核实

**H01 失败原因分析**：
- 脚本产生 39 个"问题"，28 个是 markdown 表格误报
- MiniMax 过滤误报时过于激进，把注意力花在误报上
- **结果**：漏掉了所有 high severity 问题
- **教训**：脚本辅助审核不如纯人工审核效果好

**JSON 输出错误**：
- H01 生成的 JSON 包含未转义引号 → 解析失败
- 这意味着需要 prompt 约束或输出验证步骤

---

## 当前最优策略：R 组（exec+sed 多步审核）

### 核心原则
1. **永远用 exec + sed 读取内容**，不用 read 工具
2. **每步独立输出文件**，确保多步不跳步
3. **JSON 字符串中禁止双引号**，用「」或单引号替代
4. **不要编造问题**——prompt 中明确要求 0 幻觉

### R 组 Prompt 模板（v3，已验证）

```
你要审核 ROBOT-SOP.md 中的 N 个章节。

**第一步**：用 exec 执行以下命令读取 §X.X 章节名（起始行-结束行）：

sed -n '起始,结束p' harness/robot/night-build/reference/ROBOT-SOP.md

审核这段内容，找出问题（数据缺失、逻辑矛盾、重复内容、来源缺失、格式问题）。
写入 {output_dir}/sX.X.json

**第二步**：[重复上述模式]

...

**最后一步**：读取所有 section 文件，合并写入 result.json

每个 section 文件格式：
{"section": "章节名", "line_range": "起-止", "issues_found": 0, "issues": [...]}

result.json 格式：
{"task_id": "T-XX-RNN", "group": "R", "version": 3, "total_sections": N, "sections_completed": 0, "total_issues": 0, "section_results": []}

JSON 字符串中禁止使用双引号，用「」替代中文引号。
每完成一步必须写入文件再继续。不要编造问题。如果无问题写 issues_found: 0。
```

### 性能预期（基于实测）
- 3 章节审核：~3 分钟，~50k tokens，9 high / 27 total issues
- 幻觉率：0%
- 多步完成率：100%（3/3）
- 单章节范围建议：50-150 行（确保内容完整）

---

## 全文审核结果（2026-03-26 12:01）

### 规模
- 4917 行 / 20 个 MiniMax subagent / R 组 v3 策略
- 发现 187 个问题：42 high / 96 medium / 49 low
- 覆盖率 100%，完成率 100%，幻觉率 0%

### 交叉验证（12 个事实声明）
- 方法：MiniMax subagent 用 web_search 交叉验证
- 结果：8 confirmed / 2 rejected / 2 partially_confirmed
- **审核事实判断准确率: 83.3%**
- **误报率: 16.7%**（MiniMax 倾向于"纠正"文档中已正确的信息）

### 误报案例
1. V04: Hi3863V100 Flash 审核说 2MB，实际是 4MB（文档是对的）
2. V12: OpenClaw GitHub 审核说不是 openclaw/openclaw，实际就是

### 交叉验证策略经验
1. **web_search > web_fetch**: fetch 容易超时，search 更稳定
2. 中英文各搜一次能覆盖更多来源
3. 每个声明 2-3 次搜索足够

---

## 两步法工作流（审核 + 交叉验证）

### 第一步：MiniMax Subagent 审核
- 用 R 组 v3 策略（exec+sed 读取 + 多步独立输出文件）
- 输出: 各段 result.json

### 第二步：交叉验证（两种方式）

#### 方式 A：MiniMax Subagent 验证（v1，已测试）
- MiniMax subagent 用 web_search 验证事实性声明
- 优点: 不消耗主 session tokens
- 缺点: web_fetch 容易超时，搜索质量有限

#### 方式 B：五平台 + Tavily 验证（v2，推荐）
- GLM 主 agent 调用 deepseek_chat / doubao_chat / kimi_chat / qwen_chat / glm_chat / tavily_search
- 五平台并行，每个验证一个问题
- 优点: 搜索质量更高，各平台有联网搜索能力
- 缺点: 消耗主 session tokens（但每个调用很快）

#### 方式 B 的执行方式
不需要 subagent，GLM 直接并行调用 5 个聊天工具：
```
V01 验证 → deepseek_chat("Qwen3.5 是否存在？阿里官方发布过吗？")
V01 验证 → doubao_chat("Qwen3.5 是否存在？")
V01 验证 → kimi_chat("Qwen3.5 是否存在？")
...
```
每个平台独立给出判断，5 个结果交叉对比 → 最终结论

### 修正后 High 问题数
- 原 42 个 → 去掉 2 个误报 → 修正后 ~40 个

---

## Prompt 模板库

### R 组审核模板（v3，已验证 ✅）
见上方"R 组 Prompt 模板"

### E 组提取模板（已验证 ✅）
```
执行以下命令：
grep -n '^#' harness/robot/night-build/reference/ROBOT-SOP.md | python3 -c "
import json, sys, re
results = []
for line in sys.stdin:
    m = re.match(r'^(\d+):\s*(#+)\s*(.+)', line.strip())
    if m:
        results.append({'line': int(m.group(1)), 'level': len(m.group(2)), 'heading': m.group(3).strip()})
json.dump(results, sys.stdout, ensure_ascii=False, indent=2)
" > {output_path}
```

### 废弃模板（测试失败）
- ~~原子读任务模板~~ → read 工具行号不可靠
- ~~多步读任务模板 v1/v2/v3~~ → 标题提取用 grep 更好
- ~~脚本辅助审核模板~~ → 过滤误报时漏掉 high

---

## 更新日志

- 2026-03-27 21:55 v0.6：补充 N-01～N-06 经验（subagent 状态管理、任务描述粒度、read 限制、额度消耗效率）
- 2026-03-26 12:28 v0.5：三步法策略 v2（审核→五平台验证→修正建议），策略文件 NIGHT-BUILD-STRATEGY-v2.md
- 2026-03-26 12:19 v0.4：全文审核完成（187问题），交叉验证（83%准确率），五平台验证方案设计
- 2026-03-26 11:35 v0.3：6 轮测试完成，确立 R 组为最优策略
- 2026-03-26 11:00 v0.2：新增审核测试，发现多步审核可行
- 2026-03-26 v0.1：初始版本，标题提取测试

---

## 2026-03-27 N-01～N-06 经验补充

### subagent 任务状态管理（重要）

**问题**：N-03 subagent 完成后没有更新 task-queue.json 的状态（仍为 pending），N-04 subagent 正确更新了自己的状态。

**原因**：subagent prompt 里没有明确要求"完成后更新 task-queue.json"。N-04 的 prompt 提到了，N-03 没有。

**规则**：**每个 subagent prompt 必须包含**：
1. 完成后更新 task-queue.json 对应任务 status → success/failed
2. 写入 orchestrator-log.jsonl 记录操作
3. 用 `python3 -c "import json; ..."` 更新，不用 read+edit（避免浪费调用次数）

### 任务描述粒度影响效率（重要）

**对比**：

| 任务 | 描述详细度 | 耗时 | 效果 |
|------|-----------|------|------|
| N-01 | 简短（1句话） | ~5m | 完成但产出一般 |
| N-03 | 中等（步骤列表） | 1m44s | 完成度高，三份报告都更新了 |
| N-06 | 非常详细（7步+具体参数+验证方法） | 3m | 效果最好，LED/NPC/性能都处理了 |

**结论**：
- **任务描述越详细，subagent 效果越好**
- 应该包含：输入文件路径、输出文件路径、具体步骤、验证方法、注意事项
- 避免"分析并改进"这种模糊指令，改为"执行以下 5 个步骤"

### subagent 不应该用 read 工具（重要）

**N-03 经验**：subagent 用 read 读取了 3 个报告文件 + 验证报告，每个 read 消耗 1 次调用。如果改用 exec+grep/sed 提取关键内容，可以节省调用次数。

**N-04 经验**：subagent 用 read 扫描了多个目录和文件，消耗了不少调用次数。如果用 `find + head` 或 `ls` 预处理，效率更高。

**规则**：subagent prompt 里应明确指定：
- 用 `exec` + `grep`/`sed`/`awk` 读取文件内容，**不要用 read 工具**
- 如果必须读完整文件（如生成索引），一次性读完，不要分段 read

### MiniMax subagent 额度消耗效率分析

**今晚统计**：
- N-01: ~5m, 估计 15-20 次调用
- N-02: ~5m, 估计 20-25 次调用（重做映射报告，大文件操作）
- N-03: 1m44s, 184.3k tokens（in 180.7k / out 3.6k），估计 10-12 次调用
- N-04: 3m37s, 156.8k tokens（in 149.8k / out 7.0k），估计 15-18 次调用
- N-05: 5m, 估计 15-20 次调用（五平台 webauth 超时，subagent 内部重试）
- N-06: 3m, 估计 12-15 次调用

**总计**：6 个 subagent ≈ 87-110 次调用，5 小时周期 600 次 = **仅消耗 15-18% 的配额**

**浪费分析**：
- subagent 之间的间隔（主 session 分析 + 手动派发）：每次 3-10 分钟，这段时间额度空转
- 简单任务完成太快：N-03 只用了 1m44s，但调度间隔远大于此
- 主 session（GLM）也在消耗额度：对话中的 thinking + tool calls

**改进方向**：
1. cron 自动调度，消除间隔
2. 任务粒度更大，每个任务消耗 30-50 次调用
3. 用 attachments 传入文件内容，减少 subagent 的 read 调用
4. 让 subagent 用 exec+sed 而非 read

### subagent 完成后的状态汇报

**问题**：N-04 subagent 在完成汇报中说"N-03 pending"，但实际上 N-03 已经在它之前完成了。N-04 读的是旧版 task-queue.json。

**规则**：subagent 完成后应最后再读一次 task-queue.json 确认最新状态，避免汇报过期信息。

### N-06 的详细任务描述模板（推荐参考）

N-06 的任务描述是迄今为止效果最好的 subagent prompt，关键特征：
1. **验证先行**：先检查当前状态
2. **具体参数**：给出了 y 值、尺寸、颜色等精确数字
3. **步骤编号**：7 个步骤，每步有明确的操作和验证
4. **性能约束**：列出了 MacBook 硬件限制和优化要求
5. **语法验证**：`node --check` 确保不破坏文件
6. **视觉验证**：Playwright 截图 + AI 分析

**模板**：
```
你是 [角色]。执行以下任务。

## 第一步：验证
[检查当前状态]

## 第二步-N：具体操作
[每步给出文件路径、具体参数、代码片段]

## 验证方法
[如何确认修改正确]

## 注意事项
[硬件限制、已知问题、性能约束]

## 完成后
1. 更新 task-queue.json 状态
2. 汇报修改内容
```

### 新发现的失败模式

- **subagent 不更新 task-queue.json**：prompt 没要求 → 主 session 以为未完成（2026-03-27 N-03）
- **subagent 汇报过期状态**：读旧版 task-queue.json → 报告"pending"但已完成（2026-03-27 N-04）
- **额度消耗效率低**：6 个 subagent 仅用 15-18% 配额，间隔浪费严重（2026-03-27）
- **主 session 理解偏差**：用户说"路灯"= PointLight，主 session 改了 AmbientLight（2026-03-27）
