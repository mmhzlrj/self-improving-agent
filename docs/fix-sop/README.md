# docs.0-1.ai 修复 SOP 总览

**日期**：2026-04-01
**背景**：MiniMax subagent 声称完成了 A-001~A-008 共 8 个任务，经审计只有 3 个真正完成。
**策略**：逐个修复，每次派 1 个 MiniMax subagent，严格按 SOP 步骤执行。

## 第一轮修复（已完成）

| # | SOP 文件 | 问题 | 状态 |
|---|---------|------|------|
| F-001 | fix-F001-css-theme-bug.md | 代码块亮色模式 CSS 硬编码 bug | ✅ 完成 |
| F-002 | fix-F002-module-docs.md | 5 个模块文档内容空壳 | ✅ 完成 |
| F-003 | fix-F003-review-workflow.md | Reports 审阅工作流缺失 | ✅ 完成 |
| F-004 | fix-F004-version-init.md | 版本系统初始化 | ✅ 完成 |
| F-005 | fix-F005-header-light-theme.md | header 亮色模式（合并到 F-001）| ✅ 完成 |

## 第二轮修复（待执行）

| # | SOP 文件 | 问题 | 优先级 | 状态 |
|---|---------|------|--------|------|
| F-006 | fix-F006-sop-chapter-routing.md | SOP 章节路由"章节未找到"bug | 🔴 P0 | ⏳ |
| F-007 | fix-F007-search-index-extend.md | 搜索索引扩展（模块+报告） | 🔴 P0 | ⏳ |
| F-008 | fix-F008-ai-write-api.md | AI 写入 API（提交报告/更新文档）| 🔴 P0 | ⏳ |
| F-009 | fix-F009-homepage-dashboard.md | 首页改版（仪表盘风格） | 🟡 P1 | ⏳ |
| F-010 | fix-F010-techref-section.md | 旧文档归类（技术参考栏目） | 🟡 P1 | ⏳ |
| F-011 | fix-F011-bi-links.md | 双向链接系统 | 🟡 P1 | ⏳ |
| F-012 | fix-F012-kanban-board.md | 任务看板页面 | 🟢 P2 | ⏳ |
| F-013 | fix-F013-ai-search-api.md | AI 搜索 API | 🟢 P2 | ⏳ |
