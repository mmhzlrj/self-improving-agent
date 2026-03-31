# A-0004: NLAH格式 → OpenClaw Skills 编写规范更新

## 来源
- 调研报告: `memory/2026-03-30-NLAH-Research-Report.md`
- 论文: arXiv:2603.25723 | 清华+哈工大 | 2026年3月
- 任务: 将NLAH格式融入OpenClaw Skills编写规范

---

## 一、现有OpenClaw Skills与NLAH组件对应关系

| NLAH组件 | OpenClaw已有 | 状态 |
|---------|-------------|------|
| Contracts | SKILL.md 的 description + 参数说明 | ✅ 部分覆盖 |
| Roles | prompt 指令 | ✅ 已有 |
| Stage Structure | 无（线性执行） | ❌ 缺失 |
| Failure Taxonomy | 无 | ❌ 缺失 |
| Evidence-backed closure | 无 | ❌ 缺失 |
| Runtime Charter | 无 | ❌ 缺失 |

**结论**: OpenClaw Skills 已有 Contracts 和 Roles 的雏形，但缺少:
1. 正式的 Stage Structure（DAG拓扑）
2. Failure Taxonomy（标准化失败分类）
3. Evidence-backed closure（产出验证）
4. Runtime Charter（全局策略分离）

---

## 二、NLAH格式 Skill 模板（推荐新格式）

```markdown
# Skill: [技能名称]

## Contracts（契约）
- **Input**: [具体输入格式，JSON schema或自然语言描述]
- **Output**: [具体输出格式，文件路径或返回值]
- **Validation Gate**: [必须通过的验证项列表]
- **Stop Conditions**: [明确何时停止执行的条件]

## Roles（角色）
- **Orchestrator**: [负责调度整个Skill流程的角色描述]
- **Solver**: [负责实际执行任务的角色描述]
- **Verifier**: [负责验证结果的角色描述]

## Stage Structure（阶段结构）
1. **Plan**: [规划阶段 - 分析输入、分解任务]
2. **Execute**: [执行阶段 - 调用工具、完成具体操作]
3. **Verify**: [验证阶段 - 检查输出是否符合Validation Gate]
4. **Repair**: [修复阶段 - 失败时的恢复策略]

## Failure Taxonomy（失败分类）
| 失败代码 | 描述 | 恢复方法 |
|---------|------|---------|
| `ERR_FILE_NOT_FOUND` | 输入文件不存在 | 检查路径、提示用户确认 |
| `ERR_API_RATE_LIMIT` | API调用超限 | 等待后重试、使用备用API |
| `ERR_TIMEOUT` | 操作超时 | 减少任务规模、增加超时时间 |
| `ERR_PARSE` | 解析失败 | 检查输入格式、启用宽松模式 |

## Evidence-backed Closure（证据闭包）
- **Artifact**: [Skill执行后必须生成的产物]
- **Verification**: [如何验证产物正确性]
- **Sign-off**: [谁/什么确认完成]

## Adapters（适配器）
- `test_hook`: [确定性测试命令]
- `verify_hook`: [验证脚本]
- `cleanup_hook`: [清理脚本]

## Runtime Charter（运行时宪章）
- **Global Policy**: [适用于所有Skill的全局规则]
- **Local Policy**: [本Skill特有的规则]
```

---

## 三、对现有Skills的具体修改建议

### 3.1 更新所有 SKILL.md 添加 Contracts

示例 - 更新 `feishu-doc/SKILL.md`:

```markdown
## Contracts
- **Input**: 飞书文档链接（URL格式: https://[domain]/docs/[docId]）
- **Output**: 文档内容（markdown格式）或写入结果
- **Validation Gate**:
  - URL必须可访问
  - docId必须有效
  - 写入内容不超过飞书API限制
- **Stop Conditions**:
  - 连续失败3次 → 停止并报告
  - 单次操作超过30秒 → 超时停止
```

### 3.2 添加 Stage Structure 到复杂Skills

对于多步骤Skill（如 `deep-research`），添加:

```markdown
## Stage Structure
1. **Plan**: 并行调用5平台搜索 + Tavily + web_fetch
2. **Execute**: 收集所有搜索结果
3. **Verify**: 检查是否有有效结果（>0条）
4. **Repair**: 如果全部失败，尝试备选搜索关键词
```

### 3.3 添加 Failure Taxonomy

在 `self-improving-agent/SKILL.md` 中添加:

```markdown
## Failure Taxonomy
| 失败代码 | 描述 | 恢复方法 |
|---------|------|---------|
| `ERR_FILE_WRITE` | 写入文件失败 | 检查文件权限、磁盘空间 |
| `ERR_GIT_PUSH` | Git推送失败 | 检查网络、重试3次 |
| `ERR_MEMORY_UPDATE` | 记忆更新失败 | 写入备用文件、稍后重试 |
```

### 3.4 添加 Evidence-backed Closure

对于所有Skills，添加:

```markdown
## Evidence-backed Closure
- **Artifact**: [具体产物，如更新的文件路径]
- **Verification**: `grep -c "实际内容" [文件路径]` ≥ 1
- **Sign-off**: 写入 memory/YYYY-MM-DD.md
```

---

## 四、NLAH vs 现有Skills 格式对比

### 现有格式（简化）:
```markdown
# Skill: xxx
[描述]
## 使用方法
[步骤]
```

### NLAH格式（完整）:
```markdown
# Skill: xxx

## Contracts
[输入/输出/验证/停止条件]

## Roles
[Orchestrator/Solver/Verifier]

## Stage Structure
1. Plan
2. Execute
3. Verify
4. Repair

## Failure Taxonomy
[表格：失败代码/描述/恢复]

## Evidence-backed Closure
[产物/验证/确认]

## Adapters
[钩子脚本]
```

---

## 五、迁移计划

### Phase 1: 创建模板（本周）
- [ ] 创建 `skills/nLAH-template/SKILL.md` 标准模板
- [ ] 更新 `skill-creator/SKILL.md` 使用新模板

### Phase 2: 更新核心Skills（本周）
- [ ] 更新 `deep-research/SKILL.md`
- [ ] 更新 `feishu-doc/SKILL.md`
- [ ] 更新 `self-improving-agent/SKILL.md`

### Phase 3: 全面审查（下周）
- [ ] 审查所有Skills，添加 Failure Taxonomy
- [ ] 添加 Evidence-backed Closure 到所有Skills
- [ ] 验证 Runtime Charter 全局策略

---

## 六、Runtime Charter 全局策略（待实现）

建议在 `AGENTS.md` 或单独文件中定义:

```markdown
# Runtime Charter - 全局策略

## 全局规则（所有Skills必须遵守）
1. 不执行破坏性操作（rm -rf /, pkill chrome等）除非显式授权
2. 所有外部操作（发邮件、发消息）必须先确认
3. 敏感数据不写入日志文件
4. 所有操作必须记录到 memory/YYYY-MM-DD.md

## Skill间协调
1. Skills之间通过文件系统协调（无共享内存）
2. 失败时返回标准错误码，不抛异常
3. 超时统一设置为300秒（可覆盖）
```

---

*生成时间: 2026-03-30 15:12 GMT+8*
*来源: memory/2026-03-30-NLAH-Research-Report.md*
