# docs.0-1.ai 本地文档站 - 规格说明书

## 1. 概述

- **目标**：构建本地文档网站，托管在 `http://127.0.0.1:18998/`
- **定位**：0-1 私人 AI 机器人项目的完整知识库
- **参考**：docs.openclaw.ai 的 Mintlify 风格

## 2. 导航结构

```
docs.0-1.ai/
├── 首页 (index.html)              # 项目总览 + 快速入口
├── SOP/                          # 0-1 实施指南
│   ├── 第0章：启动与配置
│   ├── 第1章：概念与愿景
│   ├── 第2章：硬件体系
│   ├── 第3章：软件架构
│   ├── 第4章：实施阶段
│   ├── 第5章：安全系统
│   └── 第6章：数据管理
├── 模块文档/
│   ├── 贵庚记忆系统/
│   ├── LeWM世界模型/
│   ├── 机械臂模块/
│   ├── 视觉识别/
│   ├── 吸盘抓手/
│   ├── 移动模块/
│   └── 面部模块/
├── 调研报告/
│   ├── 待审批/
│   └── 已发布/
├── 版本变更/
│   ├── OpenClaw核心/
│   ├── 各模块版本/
│   └── 变更日志/
├── 工具配置/
│   └── MCP工具/
├── 参考/
│   ├── dashboard (→18999/dashboard.html)
│   └── world (→18999/world.html)
└── 关于
```

## 3. 内容来源

### SOP 内容
- 主文件：`harness/robot/ROBOT-SOP.md`（~2100行）
- 切割成章节 HTML，按目录结构展示

### 研究报告
- 位置：`harness/robot/night-build/reports/*.md`
- 列表页：`reports/INDEX.md` 已有的索引
- 展示：按日期+类型（A/B/C/D序列）分类

### 模块文档
- 各模块 README 或 Markdown 散落在 workspace 中
- 需要从 skills/ 和 memory/ 中提取

### 版本变更
- OpenClaw：`docs/openclaw-release-log.md`
- 自定义模块：在 `.learnings/` 和 `memory/` 中追踪

## 4. 服务器架构

**端口分配**：
- `18999`：dashboard + world + 现有静态文件（MCP server 已占用）
- `18998`：**docs.0-1.ai 新站点**（新建 Python HTTP server）

**服务器脚本**：`~/.openclaw/workspace/tools/docs-server.py`

**核心功能**：
- 静态文件服务（HTML/CSS/JS）
- Markdown → HTML 渲染（python-markdown）
- 模板系统（Jinja2 风格纯 Python）
- 路由：基于路径映射到内容文件

## 5. 模板设计

### 整体布局
```
┌─────────────────────────────────────────────┐
│  🦞 docs.0-1.ai          [搜索] [版本]      │
├──────────┬──────────────────────────────────┤
│ 侧边导航  │ 内容区                           │
│          │                                  │
│ SOP      │ # 标题                           │
│ ├─ 第0章 │ 内容...                          │
│ ├─ 第1章 │                                  │
│ 模块     │                                  │
│ ├─ 贵庚  │                                  │
│ ├─ LeWM  │                                  │
│ 报告     │                                  │
│ ├─ 待审批│                                  │
│ └─ 已发布│                                  │
└──────────┴──────────────────────────────────┘
```

### 配色方案
- 主色：#ff6b35（橙色，呼应小龙虾）
- 背景：#0a0a0f（深色）
- 侧边：#12121a
- 强调：#70a1ff（蓝色）
- 成功：#2ed573
- 警告：#ffa502

### 字体
- 标题：DM Sans / 系统无衬线
- 代码：Fragment Mono
- 正文：DM Sans

## 6. 版本追踪系统

### 版本文件格式（JSON）
```json
{
  "openclaw": {
    "version": "2026.03.31",
    "changes": [
      {"date": "2026-03-31", "type": "modified", "detail": "alsoAllow移到tools级别，profile改为full"}
    ]
  },
  "gui-geng": {
    "version": "0.1.0",
    "changes": [...]
  },
  "lewm": {
    "version": "0.1.0",
    "changes": [...]
  }
}
```

### 版本文件位置
- 主版本文件：`~/.openclaw/workspace/docs/.versions/versions.json`
- 各模块可独立维护 changelog

## 7. 研究报告审批流程

### 状态
- `pending`：刚调研完，用户未审批
- `approved`：用户同意发布到 docs
- `rejected`：用户不同意，不展示

### 审批操作
- mdview --review 模式审批
- 审批结果保存到 JSON：`~/.openclaw/workspace/docs/.reports/status.json`
- 审批后可一键复制到对应章节目录

## 8. 实现计划

### Phase 1：基础设施（优先）
1. 创建 docs-server.py（Python HTTP server）
2. 基础 HTML 模板（侧边导航 + 内容区）
3. 路由系统（静态文件 + Markdown 渲染）

### Phase 2：SOP 内容填充
4. 读取 ROBOT-SOP.md，切割为章节
5. 实现侧边栏自动生成（扫描所有内容文件）

### Phase 3：研究报告中控
6. 扫描 night-build/reports/，按状态分类
7. 审批流程集成

### Phase 4：版本追踪
8. versions.json 生成脚本
9. OpenClaw release log 解析
10. 各模块 changelog 集成

### Phase 5：细节打磨
11. 搜索功能
12. 暗色主题完整适配
13. 响应式布局

## 9. 技术选型

- **服务器**：Python 标准库 http.server（无额外依赖）
- **Markdown**：python-markdown（pip install markdown）
- **模板**：纯 Python 字符串模板（避免 Jinja2 依赖）
- **静态资源**：CSS 内联 + 无外部图片依赖
- **搜索**：页面内 JavaScript 搜索（无需后端）

## 10. 文件结构

```
~/.openclaw/workspace/docs/
├── docs-server.py              # HTTP 服务器
├── index.html                  # 首页
├── styles.css                  # 全局样式
├── app.js                      # 前端 JS
├── versions.json                # 版本数据
├── reports/
│   └── status.json             # 报告审批状态
├── modules/                    # 各模块文档
│   ├── gui-geng/
│   ├── lewm/
│   ├── arm/
│   ├── vision/
│   ├── suction/
│   ├── locomotion/
│   └── face/
├── sop/                       # SOP 各章节
│   ├── chapter-0.html
│   ├── chapter-1.html
│   └── ...
└── changelog/
    └── openclaw.html
```
