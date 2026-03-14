# Learnings Log

Captured learnings, corrections, and discoveries. Review before major tasks.

---

## LRN-20260314-002 SOP 编写规范模板

**Logged**: 2026-03-14T10:43:00+08:00
**Priority**: high
**Status**: pending
**Area**: workflow

### Summary
未来写任何 SOP 都要参考"智库平台配置SOP"的详细程度，禁止用"其他步骤同上"简化

### Details
SOP 模板规范（来自智库平台配置SOP.md）：

**必须包含的要素：**
1. **背景** - 说明这个 SOP 要解决什么问题
2. **配置清单** - 表格形式，列出所有平台和需要开启的功能
3. **完整操作流程** - 每个步骤都要详细写出，不能省略
4. **重要原则** - 强调必须严格按照 SOP 执行

**每个操作的 Step 规范（4步法）：**
- Step A: 用 XPath/选择器找到目标元素
- Step B: 检查当前状态（是否已开启）
- Step C: 只在关闭状态时才执行操作
- Step D: 验证结果

**禁止出现的描述：**
- ❌ "其他步骤同上"
- ❌ "类似操作"
- ❌ "参考上面"

**正确做法：**
- ✅ 每个操作都要完整写出 4 个 Step
- ✅ 每个 Step 都要有具体的代码/命令
- ✅ XPath/选择器要明确写出

### Metadata
- Source: user_feedback
- Related Files: ~/.openclaw/workspace/智库平台配置SOP.md
- Tags: sop, template, best_practice

---
