# NLAH（自然语言Agent Harness）调研报告

**调研时间**：2026-03-30
**论文来源**：arXiv:2603.25723 | 清华+哈工大
**关键词**：#HarnessEngineering #NLAH #OSWorld #IHR

---

## 一、核心思想

### 问题
传统agent的harness（编排层）逻辑散落在controller代码里：
- 难以跨runtime迁移
- 难以公平比较
- 难以做ablation分析

### 解决方案
把harness控制逻辑从代码里抽出来，写成**自然语言文件**，由共享运行时（IHR）解释执行。

```
传统做法（代码写死）：
  harness逻辑 → 散落在controller代码里

NLAH做法（自然语言外置）：
  harness逻辑 → 写成自然语言文件 → IHR运行时解释执行
```

---

## 二、核心组件

| 组件 | 作用 |
|------|------|
| **Contracts（契约）** | 输入输出格式、验证门、停止条件 |
| **Roles（角色）** | solver/verifier/orchestrator的prompt和职责 |
| **Stage Structure（阶段结构）** | plan→execute→verify→repair 的DAG拓扑 |
| **Adapters & Scripts（适配器）** | 测试/linter/验证器的确定性钩子 |
| **State Semantics（状态语义）** | 文件持久化、跨步继承、truncation存活 |
| **Failure Taxonomy（失败分类）** | 命名失败模式 → 自动恢复路径 |

---

## 三、实验结果

### OSWorld benchmark
```
原生Python harness (OS-Symphony): 30.4%
NLAH迁移后: 47.2%  (+16.8%，55%相对提升)
```

**关键洞察**：NLAH不是改进了底层模型，而是改变了可靠性来源：
- 原生：GUI截图修复 → 脆弱
- NLAH：文件+artifact验证 → deterministic closure

### 模块ablation发现
| 模块 | 效果 |
|------|------|
| File-backed state | 提升auditability和recovery |
| Evidence-backed answering | 强化验证，关闭更可靠 |
| Self-evolution | 最强收益，强制acceptance-gated retry |
| Verifier | 可能和benchmark acceptance冲突 |
| Multi-candidate search | overhead太大，收益不明显 |

---

## 四、OpenClaw对比

| NLAH概念 | OpenClaw对应 |
|---------|-------------|
| NLAH文件 | `SOUL.md`, `AGENTS.md`, skills/*.md |
| IHR运行时 | OpenClaw Gateway |
| Runtime Charter | openclaw.json（全局策略） |
| Contracts | tool schema + input/output定义 |
| Roles | SOUL.md人格定义 |
| Stage Structure | skill流程/SOP |
| File-backed state | memory/会话状态 |
| Failure taxonomy | error handling规范 |
| Adapters/scripts | skill脚本 + hook系统 |

**结论**：OpenClaw架构天然契合NLAH思想，已经是"自然语言harness"系统。

---

## 五、OpenClaw落地建议

### 需要补的薄弱环节

| NLAH强调 | OpenClaw现状 | 建议 |
|---------|------------|------|
| **Contracts** | tool定义但缺验证门 | 给每个skill加明确的"完成条件"和"验证方法" |
| **Failure Taxonomy** | 分散 | 建立标准化的失败分类体系 |
| **Evidence-backed closure** | 弱 | skill执行完要有artifact验证 |
| **Runtime Charter分离** | 部分做到 | 全局策略和任务harness更清晰分离 |

### NLAH格式Skill模板

```markdown
# Skill: [任务名称]

## Contracts
- **Input**: [具体输入格式]
- **Output**: [具体输出格式]
- **Validation Gate**: [必须通过的验证项]
- **Stop Conditions**: [何时停止]

## Roles
- **Orchestrator**: [负责调度]
- **Solver**: [负责执行]
- **Verifier**: [负责验证]

## Stage Structure
1. **Plan**: [规划阶段]
2. **Execute**: [执行阶段]
3. **Verify**: [验证阶段]
4. **Repair**: [失败恢复]

## State Semantics
- **Persists**: [持久化状态]
- **Artifact paths**: [产出文件路径]
- **Recovery**: [checkpoint恢复方法]

## Failure Taxonomy
- **ERROR_A**: [失败模式] → [恢复方法]
- **ERROR_B**: [失败模式] → [恢复方法]

## Adapters
- **test_hook**: [确定性测试]
- **verify_hook**: [验证脚本]
- **cleanup_hook**: [清理脚本]
```

---

## 六、参考来源

| 来源 | 链接 |
|------|------|
| 论文arXiv | https://arxiv.org/abs/2603.25723 |
| NLAH GitHub | 待补充 |
| OS-Symphony | https://github.com/OS-Copilot/OS-Symphony |
| OpenClaw引用 | 论文Section 6引用 |

---

*报告生成于 2026-03-30*
