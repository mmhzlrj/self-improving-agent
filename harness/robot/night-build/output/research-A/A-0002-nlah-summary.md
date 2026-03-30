# NLAH（自然语言Agent Harness）落地OpenClaw - 执行摘要

**生成时间**：2026-03-30
**来源报告**：`memory/2026-03-30-NLAH-Research-Report.md`

---

## 核心思想

把agent的harness控制逻辑从代码里抽出来，写成**自然语言文件**，由共享运行时（IHR）解释执行。

```
传统做法（代码写死）：
  harness逻辑 → 散落在controller代码里

NLAH做法（自然语言外置）：
  harness逻辑 → 写成自然语言文件 → IHR运行时解释执行
```

**OSWorld结果**：30.4% → 47.2%（+55%相对提升）

---

## NLAH vs OpenClaw 对应关系

| NLAH组件 | OpenClaw对应 |
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

## OpenClaw需要补的薄弱环节

| NLAH强调 | OpenClaw现状 | 建议 |
|---------|------------|------|
| **Contracts** | tool定义但缺验证门 | 给每个skill加明确的"完成条件"和"验证方法" |
| **Failure Taxonomy** | 分散 | 建立标准化的失败分类体系 |
| **Evidence-backed closure** | 弱 | skill执行完要有artifact验证 |
| **Runtime Charter分离** | 部分做到 | 全局策略和任务harness更清晰分离 |

---

## 参考来源

| 来源 | 链接 |
|------|------|
| 论文arXiv | https://arxiv.org/abs/2603.25723 |
| OS-Symphony | https://github.com/OS-Copilot/OS-Symphony |
