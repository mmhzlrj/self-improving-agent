# 🌙 0-1 Night Build — MiniMax Coding Plan 夜间自动化方案

**创建日期**: 2026-03-26
**状态**: 待确认

---

## 一、核心理念

> 在你睡觉的 14 小时里（20:00-10:00），MiniMax 1800 次调用额度几乎没用。
> 让 MiniMax subagent 在夜间以"短小快"的小任务模式，自动推进 0-1 项目。
> 早上起来你和我一起审核，把好的合并，坏的丢掉。

### 设计原则

1. **工作目录隔离**：所有夜间产出到 `harness/robot/night-build/`，不影响原始 `ROBOT-SOP.md`
2. **短小快任务**：每个 subagent 任务控制在 3-5 分钟内，单次调用不超过 50k tokens
3. **流水线式编排**：3 个 subagent 轮转执行，每个完成后自动启动下一个
4. **晨间审核机制**：早上 9:50 自动生成夜间工作摘要，等你审核决定合并什么

---

## 二、额度感知调度（核心机制）

### ⚠️ 核心原则：不写死任务数，基于实时额度动态调度

**问题场景**：你某天晚上 10 点还在用 MiniMax，20:00-24:00 的 600 次可能已用掉 300 次。
如果按写死的 12 个任务去调度，剩余 300 次只够 10 个任务，最后 2 个会失败。
更糟的是，失败可能产生错误产出或浪费额度。

### 额度 API

```bash
curl -s -X GET "https://www.minimaxi.com/v1/api/openplatform/coding_plan/remains" \
  -H "Authorization: Bearer sk-cp-..."
```

返回 `current_interval_usage_count`（剩余次数）和 `current_interval_total_count`（总量）。

### 调度决策矩阵

每次 orchestrator 触发时，先查 API 获取**真实剩余次数**，然后按以下矩阵决策：

| 剩余额度 | 决策 | 可派 subagent 数 | 任务类型 |
|---------|------|-----------------|---------|
| ≥ 450 | 全力运行 | 3 个并行 | 所有任务类型 |
| 300-449 | 正常运行 | 2 个并行 | 调研+编写（禁优化） |
| 150-299 | 保守运行 | 1 个 | 仅轻量任务（审核+调研） |
| 60-149 | 降速模式 | 1 个 | 仅审核任务（最快完成） |
| 30-59 | 即将耗尽 | 0 个 | **停止派任务，生成中期总结** |
| < 30 | 紧急停止 | 0 个 | **停止一切，写紧急日志** |

### 任务调用预算（按类型）

| 任务类型 | 单次预估调用次数 | 安全阈值 |
|---------|----------------|---------|
| 调研（搜索+整理） | 15-25 次 | ≥ 30 才派 |
| 编写（读+写文件） | 20-35 次 | ≥ 40 才派 |
| 审核（读+检查） | 10-20 次 | ≥ 20 才派 |
| 优化（读+重写） | 25-40 次 | ≥ 45 才派 |

**调度公式**：`可派任务数 = floor(剩余额度 / 单任务安全阈值)`
**安全余量**：始终保留 30 次额度作为缓冲，防止最后一个任务意外超支

### 时间段与并发策略（仅作参考基线，实际以额度为准）

| 时间段 | 预期剩余（无人工使用时） | 默认并发 | 说明 |
|--------|---------------------|---------|------|
| 20:00-24:00 | ~600（但你可能在使用） | 动态判断 | 高峰过渡期，你可能在用 |
| 00:00-05:00 | ~600（你在睡觉） | 3 个并行 | 最稳定时段 |
| 05:00-10:00 | ~600（你可能快醒了） | 3→1 递减 | 接近起床逐渐降速 |

### 心跳辅助监控

主 session 心跳（每 30 分钟）顺带检查额度并记录到 `night-build/night-summary.json`。
如果发现某个时间段额度消耗异常快（>80%/小时），在日志中标注 warning。
**注意**：心跳只做监控记录，不做调度决策。调度决策完全由 orchestrator cron 负责。

### 失败隔离机制

**关键**：任务之间完全独立，不做链式依赖。

```
任务 A 失败 → 记录失败原因 → 标记 skip → 继续调度任务 B
```

- 任务 A 失败**不会**影响任务 B 的调度
- 连续 3 次失败 → 触发"降级模式"：只派最轻量的审核任务
- 全部失败 → 生成错误总结，停止调度，等早上审核

---

## 三、工作目录结构

```
harness/robot/night-build/
├── README.md                    # 夜间构建总览（自动生成）
├── tasks/                       # 任务定义（预定义）
│   ├── 01-xxx.md               # 每个文件 = 一个任务
│   ├── 02-xxx.md
│   └── ...
├── output/                      # 当晚产出
│   ├── 2026-03-26/             # 按日期隔离
│   │   ├── task-01/            # 单个任务产出
│   │   │   ├── result.md       # 任务结果
│   │   │   ├── diff.patch      # 如果有文件修改
│   │   │   └── log.txt         # 执行日志
│   │   ├── task-02/
│   │   └── ...
│   └── 2026-03-27/
├── reviews/                     # 审核结果
│   ├── 2026-03-26-review.md    # 晨间审核文档
│   └── merged/                 # 已合并的任务
├── task-queue.json              # 当前任务队列
└── night-summary.json           # 夜间总结
```

---

## 四、任务分类与定义

### 任务类型

| 类型 | 描述 | 预计耗时 | Token 预算 |
|------|------|---------|-----------|
| **调研** | 搜索最新技术/硬件/论文信息 | 3-5分钟 | 40k tokens |
| **编写** | 基于现有章节，写新内容或补充细节 | 3-5分钟 | 50k tokens |
| **审核** | 检查已有章节的逻辑、数据、交叉引用 | 2-3分钟 | 30k tokens |
| **优化** | 重写、精简、结构调整 | 3-5分钟 | 40k tokens |

### 预定义任务池（按优先级排序）

#### 🔴 高优先级（直接推进项目落地）

| ID | 任务 | 类型 | 输入 | 输出 |
|----|------|------|------|------|
| T01 | Phase 0 详细实施步骤 | 编写 | §Phase 0 概述 | 完整的 Phase 0 SOP（命令级） |
| T02 | Phase 1 语音模块：设备选型对比表 | 调研 | §4 Phase 1 | 麦克风/扬声器/ADC 选型表 |
| T03 | Phase 1 Whisper 离线部署方案 | 编写 | §6.2 NemoClaw + §A.2 | 逐步安装+配置脚本 |
| T04 | Phase 1 TTS 部署方案（本地） | 编写 | §A.2 TTS 推荐 | Piper/TTS 逐步部署 |
| T05 | Phase 2 视觉模块：ESP32-CAM 完整配置 | 编写 | §3.4.2 + §A.3 | 烧录+连接+测试全流程 |
| T06 | Phase 0 台式机对接 Gateway 实战脚本 | 编写 | §4 Phase 0 | 可执行的 shell 脚本 |

#### 🟡 中优先级（完善现有文档）

| ID | 任务 | 类型 | 输入 | 输出 |
|----|------|------|------|------|
| T07 | 贵庚记忆系统数据流图（文本版） | 优化 | §1.2 全部 | ASCII/Mermaid 流程图 |
| T08 | 通信协议选型决策矩阵 | 优化 | §3.3 | 对比表+推荐结论 |
| T09 | ROS 2 vs 替代框架对比表 | 审核 | §3.4 | 结构化对比+推荐 |
| T10 | 采购清单价格核实与更新 | 调研 | §2.2 + §2.4 | 最新价格表+购买链接 |
| T11 | 电源方案详细电路图描述 | 编写 | §2.3 | 详细文字版电路方案 |
| T12 | 网络断连分级应对策略审核 | 审核 | §网络断连 | 优化建议 |

#### 🟢 低优先级（锦上添花）

| ID | 任务 | 类型 | 输入 | 输出 |
|----|------|------|------|------|
| T13 | 术语表自动补全与排序 | 优化 | §术语表 | 补全缺失术语 |
| T14 | 交叉引用完整性检查 | 审核 | 全文 | 断链+错误引用列表 |
| T15 | 各 Phase 间依赖关系图 | 优化 | §4 全部 | Mermaid 依赖图 |
| T16 | 安全模块实施脚本 | 编写 | §8 全部 | 可执行脚本 |
| T17 | 日常维护自动化脚本 | 编写 | §8.4 | bash 一键检查脚本 |
| T18 | 最新开源项目调研补充 | 调研 | §A.1 | 新项目推荐 |

---

## 五、任务编排机制

### 方案：Cron Job + Isolated Session 流水线

#### 核心架构

```
┌─────────────────────────────────────────────┐
│              Gateway Cron Scheduler          │
│                                             │
│  ┌─────────────┐  ┌──────────────────────┐  │
│  │ 定时触发器   │→ │ Night Orchestrator   │  │
│  │ (每30分钟)  │  │ (isolated session)   │  │
│  └─────────────┘  │                      │  │
│                   │  1. 检查额度          │  │
│                   │  2. 选下一个任务       │  │
│                   │  3. 检查已有产出       │  │
│                   │  4. 派 subagent       │  │
│                   │  5. 记录结果          │  │
│                   └──────────┬───────────┘  │
│                              │              │
│                   ┌──────────▼───────────┐  │
│                   │  MiniMax Subagent     │  │
│                   │  (3-5分钟超时)        │  │
│                   │                      │  │
│                   │  - 读取输入文件       │  │
│                   │  - 执行任务           │  │
│                   │  - 写入产出文件       │  │
│                   └──────────────────────┘  │
└─────────────────────────────────────────────┘
```

#### Cron Job 设计

**Job 1: Night Orchestrator（夜间编排器）**

```json
{
  "name": "0-1 Night Build Orchestrator",
  "schedule": { "kind": "cron", "expr": "*/30 20-23,0-9 * * *", "tz": "Asia/Shanghai" },
  "sessionTarget": "isolated",
  "payload": {
    "kind": "agentTurn",
    "message": "你是 0-1 项目的夜间编排器。\n\n## 第一步：查实时额度（必须先执行）\n\n用 curl 查询 MiniMax Coding Plan 额度：\ncurl -s -X GET 'https://www.minimaxi.com/v1/api/openplatform/coding_plan/remains' -H 'Authorization: Bearer sk-cp-Zosvx8d6zR6EI34fzFEWopC1kvtXdtzpMPWObv8goBG4MyNJTzK-vuniGGQV5TPOcICyJP-qIjWQ66KlY5mtOm6Z1oAVA1lugbkRDjE1QyMFX6phXsGVOPA'\n\n获取 current_interval_usage_count（剩余次数）。\n\n## 第二步：调度决策（基于实时额度）\n\n决策矩阵：\n- 剩余 ≥ 450: 派 3 个 subagent 并行（用 sessions_spawn）\n- 剩余 300-449: 派 2 个并行\n- 剩余 150-299: 派 1 个\n- 剩余 60-149: 派 1 个（仅审核类轻量任务）\n- 剩余 30-59: **停止**，生成中期总结\n- 剩余 < 30: **紧急停止**，记录日志\n\n任务调用预算：调研15-25次、编写20-35次、审核10-20次、优化25-40次\n安全余量：始终保留30次\n\n## 第三步：取任务并派 subagent\n\n1. 读取 night-build/task-queue.json 获取 pending 任务\n2. 根据剩余额度和任务类型预算，决定能派几个\n3. 对每个任务：\n   a. 读取 tasks/XX-xxx.md 获取任务定义\n   b. 读取 ROBOT-SOP.md 相关章节（用 offset/limit，不要读全文）\n   c. sessions_spawn 派 MiniMax subagent（timeout 300秒）\n   d. 等待完成后将结果写入 output/YYYY-MM-DD/task-XX/\n   e. 更新 task-queue.json\n4. 失败隔离：单任务失败不影响后续任务调度\n5. 连续3次失败→降级为仅审核任务\n\n## 绝对规则\n- 工作目录: harness/robot/night-build/\n- ROBOT-SOP.md 只读，绝不修改\n- 所有产出写入隔离目录\n- 每次必须先查额度再调度，不能假设额度充足",
    "model": "minimax/MiniMax-M2.7",
    "timeoutSeconds": 480
  },
  "delivery": { "mode": "none" },
  "enabled": true
}
```

**Job 2: Morning Summary（晨间总结）**

```json
{
  "name": "0-1 Night Build Summary",
  "schedule": { "kind": "cron", "expr": "50 9 * * *", "tz": "Asia/Shanghai" },
  "sessionTarget": "isolated",
  "payload": {
    "kind": "agentTurn",
    "message": "你是 0-1 项目的晨间审核助手。请执行：\n1. 读取 harness/robot/night-build/output/ 昨晚的产出目录\n2. 汇总每个任务的执行状态（成功/失败/部分完成）\n3. 为每个成功的产出生成简短摘要\n4. 生成审核文档到 night-build/reviews/YYYY-MM-DD-review.md\n5. 用 mdview 打开审核文档供用户查看\n6. 发送通知告知用户夜间工作完成",
    "model": "minimax/MiniMax-M2.7",
    "timeoutSeconds": 300
  },
  "delivery": { "mode": "announce" },
  "enabled": true
}
```

**Job 3: Night Build Start（夜间启动器）**

```json
{
  "name": "0-1 Night Build Start",
  "schedule": { "kind": "cron", "expr": "5 20 * * *", "tz": "Asia/Shanghai" },
  "sessionTarget": "isolated",
  "payload": {
    "kind": "agentTurn",
    "message": "0-1 夜间构建启动。请执行：\n1. 创建今晚的产出目录 night-build/output/YYYY-MM-DD/\n2. 重置 task-queue.json（将所有任务标记为 pending）\n3. 复制最新 ROBOT-SOP.md 到 night-build/reference/（作为只读参考）\n4. 检查 MiniMax 额度\n5. 立即启动第一个任务（Phase 0 实施步骤）",
    "model": "minimax/MiniMax-M2.7",
    "timeoutSeconds": 300
  },
  "delivery": { "mode": "none" },
  "enabled": true
}
```

---

## 六、Subagent 提示词模板

### 通用约束（每个 subagent 必须遵守）

```
## 绝对规则

1. **只读取，不修改原始文档**：ROBOT-SOP.md 是只读的
2. **所有产出写入指定目录**：night-build/output/YYYY-MM-DD/task-XX/
3. **文件大小限制**：单个产出文件不超过 5000 行
4. **超时硬限制**：5 分钟内必须完成并写入结果
5. **失败处理**：如果无法完成，写入失败原因到 result.md，不要留空
6. **格式要求**：结果使用 Markdown 格式
7. **数据来源**：所有数据必须标注来源，不确定的标注 [待核实]

## 任务模板

你是 0-1 项目的夜间助手。请完成以下任务：

### 任务：{task_name}
### 任务 ID：{task_id}
### 类型：{task_type}

### 输入文件
- {input_file_path}: 描述

### 上下文
- ROBOT-SOP.md {section_range}: 相关章节

### 要求
1. {requirement_1}
2. {requirement_2}
3. ...

### 输出
- 写入：{output_path}/result.md
- 如果涉及文件修改，写入：{output_path}/diff.patch

### 完成后
- 在 {output_path}/result.md 末尾添加执行总结（耗时、遇到的问题、数据来源）
```

---

## 七、晨间审核流程

### 每天早上 9:50

1. **自动生成审核文档**（Cron Job 2）
2. **mdview 打开审核文档**
3. **通知用户**："昨晚 Night Build 完成，共执行 X 个任务"

### 审核方式

用户在审核文档中对每个任务标记：
- ✅ **合并**：将产出合并到 ROBOT-SOP.md
- ❌ **丢弃**：产出不合格
- 🔄 **返工**：需要修改，重新加入今晚任务队列

### 合并策略

- 合并操作由 GLM（我）在白天执行，不在夜间自动合并
- 合并前用 mdview 展示 diff 供用户确认
- 合并后 git commit + 记录到日志

---

## 八、防错机制

### 已知风险与对策

| 风险 | 概率 | 对策 |
|------|------|------|
| Subagent 超时 | 高 | 5分钟硬限制 + 自动记录失败 |
| Subagent 修改原始文件 | 中 | 工作目录隔离 + 提示词强调只读 |
| 内容质量差 | 高 | 晨间审核 + 返工机制 |
| 上下文太长导致混乱 | 高 | 每个任务只读取相关章节，不读全文 |
| 额度耗尽 | 中 | 实时监控 + 自动降速 |
| 3个并行导致限流 | 中 | 00:00-05:00 和 05:00-10:00 用3个，20:00-24:00 用1个 |
| 产出文件格式混乱 | 中 | 严格模板 + 自动校验 |
| Git push 失败 | 低 | 晨间手动处理 |

### Subagent 常犯错误（已知）

根据之前的经验记录：

1. **大文件操作超时**：ROBOT-SOP.md 有 4917 行/213KB，不能让 subagent 一次性读取全文
   - 对策：只读相关章节（用 `read` 的 offset/limit）
   
2. **edit 操作只改编号不改内容**：Phase 顺序调整时犯过
   - 对策：物理操作用 python 脚本，不依赖 edit 工具

3. **删除不该删的内容**：目录补全时误删正文
   - 对策：所有产出写入隔离目录，不碰原文件

4. **上下文丢失**：subagent 是新 session，没有之前的对话历史
   - 对策：任务定义文件必须自包含所有必要信息

---

## 九、实施步骤

### Step 1：创建目录结构 ✅（确认后执行）

```bash
mkdir -p harness/robot/night-build/{tasks,output,reviews}
```

### Step 2：创建任务定义文件 ✅（确认后执行）

为每个预定义任务创建 `tasks/XX-xxx.md`

### Step 3：创建任务队列文件 ✅（确认后执行）

`task-queue.json` 包含所有任务的状态

### Step 4：注册 Cron Jobs ✅（确认后执行）

通过 OpenClaw cron API 注册 3 个定时任务

### Step 5：首次测试 ✅（确认后执行）

手动触发一次 orchestrator 测试流程

### Step 6：晨间审核流程确认 ✅（确认后执行）

确认 mdview + 通知链路正常

---

## 十、监控与日志

### 日志文件

- `night-build/output/YYYY-MM-DD/` — 每晚产出
- `night-build/reviews/YYYY-MM-DD-review.md` — 每日审核
- `memory/YYYY-MM-DD.md` — 主日志中记录夜间工作状态

### 额度追踪

每次 orchestrator 运行时检查额度，记录到：
- `night-build/night-summary.json`

```json
{
  "date": "2026-03-26",
  "tasks_completed": 12,
  "tasks_failed": 2,
  "total_calls_used": 380,
  "calls_remaining": 420,
  "summary": "..."
}
```

---

## 十一、待确认事项

1. **时间段划分**：20:00-24:00 用 1 个 subagent，00:00-05:00 和 05:00-10:00 用 3 个 — 你觉得可以吗？
2. **任务优先级**：上面列的 18 个任务，你有没有想调整顺序的？
3. **晨间通知方式**：目前走 webchat announce，你需要同时发飞书/钉钉/QQ 吗？
4. **周末策略**：周末也要运行吗？还是只在周一到周五？
5. **首次启动时间**：今晚 20:05 开始第一次运行？

---

*方案版本: v1.0 | 等待用户确认后实施*
