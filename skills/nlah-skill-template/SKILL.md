---
name: nlah-skill-template
description: "基于 NLAH（Natural-Language Agent Harnesses）格式的 Skill 模板。每次创建新 Skill 时使用此模板。源自 arXiv:2603.25723 清华+哈工大论文。"
metadata:
  version: 1.0
  date: 2026-03-30
  paper: arXiv:2603.25723
---

# NLAH Skill 模板

> 基于 Natural-Language Agent Harnesses (NLAH) 格式，每次创建新 Skill 时使用此模板。

## 什么是 NLAH

NLAH 把 agent 的 harness 控制逻辑从代码里抽出来，写成自然语言文件，由运行时解释执行。

| NLAH 组件 | OpenClaw Skill 对应 |
|-----------|-------------------|
| Contracts | description + 验证门 |
| Roles | prompt / SOUL.md |
| Stage Structure | 多步骤执行流程 |
| Failure Taxonomy | 失败分类 |
| Evidence-backed closure | 产物验证 |

---

## Skill 文件结构

```
skills/
└── {skill-name}/
    ├── SKILL.md           # 本文件（NLAH 格式）
    ├── contracts.md        # 契约定义（可选）
    ├── roles.md           # 角色定义（可选）
    ├── failures.md        # 失败分类（可选）
    └── scripts/           # 确定性钩子
        ├── test.sh        # 测试脚本
        ├── verify.sh      # 验证脚本
        └── cleanup.sh     # 清理脚本
```

---

## SKILL.md 必须包含的章节

### 1. Contracts（契约）

```markdown
## Contracts

- **Trigger**: 什么情况下触发这个 Skill
- **Input**: 输入格式（文件路径、参数等）
- **Output**: 输出产物
- **Validation Gate**: 必须通过的验证项
- **Stop Conditions**: 何时停止执行
```

### 2. Roles（角色）

```markdown
## Roles

- **Orchestrator**: 谁负责调度整个流程
- **Solver**: 谁负责实际执行
- **Verifier**: 谁负责验证结果
```

### 3. Stage Structure（阶段结构）

```markdown
## Stage Structure

1. **Plan**: 分析输入，分解任务
2. **Execute**: 调用工具，执行操作
3. **Verify**: 检查输出是否符合 Validation Gate
4. **Repair**: 失败时的恢复策略
```

### 4. Failure Taxonomy（失败分类）

```markdown
## Failure Taxonomy

| 代码 | 描述 | 恢复方法 |
|------|------|---------|
| `ERR_FILE_NOT_FOUND` | 文件不存在 | 检查路径，提示用户确认 |
| `ERR_API_RATE_LIMIT` | API 超限 | 等待后重试 |
| `ERR_TIMEOUT` | 操作超时 | 减少任务规模 |
| `ERR_PARSE` | 解析失败 | 检查输入格式 |
```

### 5. Evidence-backed Closure（证据闭包）

```markdown
## Evidence-backed Closure

- **Artifact**: Skill 执行后必须生成的产物
- **Verification**: 如何验证产物正确性
- **Sign-off**: 确认完成的标志
```

---

## 示例：创建新 Skill

### Step 1: 创建目录结构

```bash
mkdir -p skills/my-new-skill/scripts
```

### Step 2: 编写 SKILL.md

```markdown
---
name: my-new-skill
description: "简短描述这个 Skill 做什么"
---

# My New Skill

## Contracts
- **Trigger**: 用户要求 [具体场景]
- **Input**: [格式]
- **Output**: [产物路径]
- **Validation Gate**: [验证项列表]
- **Stop Conditions**: [停止条件]

## Roles
- **Orchestrator**: [调度者描述]
- **Solver**: [执行者描述]
- **Verifier**: [验证者描述]

## Stage Structure
1. **Plan**: [规划阶段]
2. **Execute**: [执行阶段]
3. **Verify**: [验证阶段]
4. **Repair**: [修复阶段]

## Failure Taxonomy
| 代码 | 描述 | 恢复 |
|------|------|------|
| `ERR_XXX` | [描述] | [方法] |

## Evidence-backed Closure
- **Artifact**: [产物]
- **Verification**: [验证方法]
```

### Step 3: 添加确定性钩子（可选）

```bash
# scripts/test.sh
#!/bin/bash
echo "Running tests..."
# 测试命令

# scripts/verify.sh
#!/bin/bash
echo "Verifying output..."
# 验证命令
```

---

## NLAH vs 传统 Skill 对比

| 维度 | 传统格式 | NLAH 格式 |
|------|---------|-----------|
| 验证 | 依赖代码 | 自然语言定义 + 确定性钩子 |
| 失败处理 | try/catch | 命名失败模式 + 自动恢复 |
| 扩展性 | 修改代码 | 添加自然语言描述 |
| 可解释性 | 低 | 高 |

---

## 参考

- 论文: [arXiv:2603.25723](https://arxiv.org/abs/2603.25723)
- NLAH 调研报告: `memory/2026-03-30-NLAH-Research-Report.md`
