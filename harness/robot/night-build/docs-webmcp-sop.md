# SOP: docs.0-1.ai WebMCP 集成实施

> **版本**: v1.0
> **创建日期**: 2026-04-01
> **源码文件**: `/Users/lr/.openclaw/workspace/tools/docs-server.py`
> **参考文档**:
>   - `/Users/lr/.openclaw/workspace/webmcp.md`（WebMCP 概述与仓库链接）
>   - `/Users/lr/.openclaw/workspace/docs/docs.openclaw.ai-sop.md`（docs 站点技术 SOP）
>   - https://webmachinelearning.github.io/webmcp（W3C WebMCP 规范）
>   - https://github.com/webmachinelearning/webmcp（官方仓库）
>   - https://bug0.com/blog/webmcp-chrome-146-guide（Chrome 146 WebMCP 指南）

---

## 一、背景

### 1.1 什么是 WebMCP

WebMCP（Web Model Context Protocol）是 W3C Web Machine Learning Community Group 孵化的 Web 标准，2026年2月发布草案，Chrome 146 开始支持早期预览。

**核心原理**：网页通过 `navigator.modelContext` API 注册"工具"（JavaScript 函数），AI Agent（如 Gemini）可以直接调用这些工具，无需 DOM 抓取或模拟点击。

**两种注册方式**：
1. **Imperative（命令式）**：JavaScript 代码 `navigator.modelContext.registerTool({...})`
2. **Declarative（声明式）**：HTML `<form>` 元素加 `webmcp` 属性（仍在草案阶段，可用 Polyfill）

**与 docs.0-1.ai 的关系**：当前站点已具备搜索、审阅、模块管理等功能，但 AI Agent 无法直接调用。WebMCP 集成后，AI Agent 可以：
- 搜索 SOP 文档内容
- 提交/查询调研报告
- 查询模块状态
- 读取特定章节内容

### 1.2 为什么需要这个

| 不集成 WebMCP | 集成 WebMCP |
|--------------|------------|
| AI 只能通过视觉模型"看"网页 | AI 直接调用结构化 API |
| 每步操作 2-5 秒延迟 | 每步 10-50ms |
| UI 改版就失效 | Schema 即合约，不受 UI 影响 |
| 需要 GPU 视觉推理 | 节省 67% 计算量 |

### 1.3 当前 docs-server.py 状态

**已有 API 端点**（基于 Python http.server）：
- `GET /api/search?q=keyword` — 模糊搜索（Fuse.js 客户端 + Python 服务端）
- `POST /api/review` — 审阅批注提交
- `POST /api/reports/submit` — 调研报告提交
- `GET /api/docs/get?file=xxx` — Markdown 文件读取
- `GET /api/export/sop-pdf` — SOP PDF 导出
- `POST /api/modules/update` — 模块数据更新

**已有页面**：
- `/` — 首页 Dashboard
- `/sop/chapter-{0-10}.html` — SOP 各章节
- `/modules/` — 模块列表
- `/board/` — 看板
- `/tools/mcp.html` — MCP 工具配置页（仅展示）

---

## 二、技术方案

### 2.1 方案选择

**采用 Imperative API（命令式注册）**，原因：
1. Declarative（声明式）仍在 W3C 草案 TODO 阶段
2. Imperative 已在 Chrome 146 早期预览可用
3. 可以精细控制每个 tool 的行为和权限

### 2.2 工具清单（MVP 8 个）

| # | Tool Name | Description | readOnlyHint | 对应已有 API |
|---|-----------|-------------|:------------:|-------------|
| 1 | `search_docs` | 搜索文档内容，支持模糊匹配 | ✅ | `/api/search` |
| 2 | `get_chapter` | 读取 SOP 指定章节的完整内容 | ✅ | `章节 HTML` |
| 3 | `get_module_info` | 获取指定模块的详细信息 | ✅ | `/modules/{slug}.html` |
| 4 | `list_modules` | 列出所有模块及其状态 | ✅ | 模块数据 |
| 5 | `get_toc` | 获取 SOP 目录结构 | ✅ | 侧边栏数据 |
| 6 | `submit_review` | 对文档段落提交审阅意见 | ❌ | `/api/review` |
| 7 | `get_report` | 获取指定调研报告内容 | ✅ | 报告 HTML |
| 8 | `get_board_status` | 获取项目看板状态 | ✅ | 看板数据 |

### 2.3 架构设计

```
Chrome 浏览器
  └── navigator.modelContext
       └── registerTool() × 8
            ├── search_docs    → fetch('/api/search?q=' + input.query)
            ├── get_chapter    → fetch('/sop/chapter-' + input.chapter + '.html')
            ├── get_module_info→ fetch('/modules/' + input.slug + '.html')  
            ├── list_modules   → 从页面内嵌数据读取
            ├── get_toc        → 从页面内嵌 NAV_DATA 读取
            ├── submit_review  → fetch('/api/review', {method:'POST'})
            ├── get_report     → fetch('/reports/' + input.slug + '.html')
            └── get_board_status→ fetch('/board/') 解析 HTML
```

**关键设计决策**：
- Tool 注册代码嵌入每个 HTML 页面的 `<script>` 中（因为 WebMCP 是客户端 API）
- 每个 tool 通过 `fetch()` 调用已有的后端 API
- 纯只读操作（readOnlyHint=true）不需要用户确认即可执行
- 写操作（submit_review）会触发浏览器的用户确认弹窗

---

## 三、实施步骤（严格按顺序执行）

### Step 1：在 docs-server.py 中添加 WebMCP 工具注册函数

**位置**: 在 `/Users/lr/.openclaw/workspace/tools/docs-server.py` 中，找到生成 HTML 页面的函数区域（约 line 400-500 附近，`_build_page_shell` 或类似的模板函数），添加一个 Python 函数生成 WebMCP JS 代码。

**函数定义**：

```python
def _make_webmcp_js():
    """生成 WebMCP 工具注册的 JavaScript 代码块"""
    return '''
<script>
// WebMCP: 让 AI Agent 可以直接调用站点功能
// 规范: https://webmachinelearning.github.io/webmcp
// 需要 Chrome 146+ 的 navigator.modelContext API
(function initWebMCP() {
    if (!('modelContext' in navigator)) {
        console.log('[WebMCP] navigator.modelContext not available (requires Chrome 146+)');
        return;
    }

    const SCRIPT_PREFIX = '/docs.0-1.ai';
    
    // 工具 1: 搜索文档
    navigator.modelContext.registerTool({
        name: 'search_docs',
        description: '搜索 docs.0-1.ai 文档站的全部内容，包括 SOP 实施指南、调研报告、模块文档。返回匹配的文档标题、摘要和链接。',
        inputSchema: {
            type: 'object',
            properties: {
                query: { type: 'string', description: '搜索关键词' },
                limit: { type: 'number', description: '返回结果数量上限，默认 5' }
            },
            required: ['query']
        },
        annotations: { readOnlyHint: true },
        handler: async ({ query, limit = 5 }) => {
            const res = await fetch(SCRIPT_PREFIX + '/api/search?q=' + encodeURIComponent(query));
            const data = await res.json();
            return {
                results: data.results ? data.results.slice(0, limit) : [],
                total: data.results ? data.results.length : 0
            };
        }
    });

    // 工具 2: 获取 SOP 章节
    navigator.modelContext.registerTool({
        name: 'get_chapter',
        description: '获取 SOP 实施指南的指定章节内容。章节编号: 0=目录, 1=快速开始, 2=概念与愿景, 3=硬件体系, 4=系统架构, 5=实施阶段, 6=贵庚系统, 7=训练方案, 8=部署运维, 9=安全体系, 10=术语表。',
        inputSchema: {
            type: 'object',
            properties: {
                chapter: { type: 'number', description: '章节编号 (0-10)' }
            },
            required: ['chapter']
        },
        annotations: { readOnlyHint: true },
        handler: async ({ chapter }) => {
            const res = await fetch(SCRIPT_PREFIX + '/sop/chapter-' + chapter + '.html');
            const html = await res.text();
            // 提取正文内容（去除导航、侧边栏等）
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const content = doc.querySelector('.prose, .sop-content, main article, #content');
            return {
                chapter: chapter,
                title: doc.title,
                content: content ? content.innerText.substring(0, 8000) : html.substring(0, 8000),
                url: SCRIPT_PREFIX + '/sop/chapter-' + chapter + '.html'
            };
        }
    });

    // 工具 3: 获取模块详情
    navigator.modelContext.registerTool({
        name: 'get_module_info',
        description: '获取 0-1 项目指定模块的详细信息。可用模块: lewm(LeWM世界模型), gui-geng(贵庚记忆系统), vision(视觉系统), motor(运动控制), comm(通信模块), power(电源管理)。',
        inputSchema: {
            type: 'object',
            properties: {
                slug: { type: 'string', description: '模块标识 (如 lewm, gui-geng, vision)' }
            },
            required: ['slug']
        },
        annotations: { readOnlyHint: true },
        handler: async ({ slug }) => {
            const res = await fetch(SCRIPT_PREFIX + '/modules/' + slug + '.html');
            if (!res.ok) return { error: 'Module not found: ' + slug };
            const html = await res.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const content = doc.querySelector('.prose, .module-content, main article, #content');
            return {
                slug: slug,
                title: doc.title,
                content: content ? content.innerText.substring(0, 8000) : html.substring(0, 8000),
                url: SCRIPT_PREFIX + '/modules/' + slug + '.html'
            };
        }
    });

    // 工具 4: 列出所有模块
    navigator.modelContext.registerTool({
        name: 'list_modules',
        description: '列出 0-1 项目的所有模块及其状态摘要，包括 LeWM 世界模型、贵庚记忆系统、视觉系统、运动控制等。',
        inputSchema: { type: 'object', properties: {} },
        annotations: { readOnlyHint: true },
        handler: async () => {
            const res = await fetch(SCRIPT_PREFIX + '/modules/');
            const html = await res.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const cards = doc.querySelectorAll('.module-card, .card');
            const modules = [];
            cards.forEach(card => {
                const title = card.querySelector('h3, h2, .title, .card-title');
                const desc = card.querySelector('p, .desc, .card-desc');
                if (title) {
                    modules.push({
                        name: title.innerText.trim(),
                        description: desc ? desc.innerText.trim().substring(0, 200) : ''
                    });
                }
            });
            return { modules: modules, total: modules.length };
        }
    });

    // 工具 5: 获取 SOP 目录
    navigator.modelContext.registerTool({
        name: 'get_toc',
        description: '获取 SOP 实施指南的完整目录结构，包含所有章节和小节。',
        inputSchema: { type: 'object', properties: {} },
        annotations: { readOnlyHint: true },
        handler: () => {
            // 从页面内嵌的 NAV_DATA 读取（如果存在）
            if (typeof NAV_DATA !== 'undefined') {
                return { toc: NAV_DATA, source: 'embedded' };
            }
            // 降级: 抓取目录页
            return { toc: 'See ' + SCRIPT_PREFIX + '/sop/chapter-1.html for full TOC', source: 'fallback' };
        }
    });

    // 工具 6: 提交审阅意见
    navigator.modelContext.registerTool({
        name: 'submit_review',
        description: '对文档的某个段落提交审阅意见（采纳/拒绝/备注）。用于审阅调研报告或 SOP 修改建议。',
        inputSchema: {
            type: 'object',
            properties: {
                paragraph_id: { type: 'number', description: '段落编号' },
                action: { type: 'string', enum: ['approve', 'reject', 'comment'], description: '审阅动作' },
                comment: { type: 'string', description: '审阅备注' }
            },
            required: ['paragraph_id', 'action']
        },
        annotations: { readOnlyHint: false },
        handler: async ({ paragraph_id, action, comment = '' }) => {
            const res = await fetch(SCRIPT_PREFIX + '/api/review', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ paragraph_id, action, comment })
            });
            return await res.json();
        }
    });

    // 工具 7: 获取调研报告
    navigator.modelContext.registerTool({
        name: 'get_report',
        description: '获取指定调研报告的内容。可用的报告 slug 需要先通过 list_reports 获取。',
        inputSchema: {
            type: 'object',
            properties: {
                slug: { type: 'string', description: '报告标识' }
            },
            required: ['slug']
        },
        annotations: { readOnlyHint: true },
        handler: async ({ slug }) => {
            const res = await fetch(SCRIPT_PREFIX + '/reports/' + slug + '.html');
            if (!res.ok) return { error: 'Report not found: ' + slug };
            const html = await res.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const content = doc.querySelector('.prose, .report-content, main article, #content');
            return {
                slug: slug,
                title: doc.title,
                content: content ? content.innerText.substring(0, 8000) : html.substring(0, 8000)
            };
        }
    });

    // 工具 8: 获取看板状态
    navigator.modelContext.registerTool({
        name: 'get_board_status',
        description: '获取 0-1 项目的项目看板，包含各任务的状态（待办/进行中/已完成）。',
        inputSchema: { type: 'object', properties: {} },
        annotations: { readOnlyHint: true },
        handler: async () => {
            const res = await fetch(SCRIPT_PREFIX + '/board/');
            const html = await res.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const columns = doc.querySelectorAll('.kanban-column, .column, .board-column');
            const board = {};
            columns.forEach(col => {
                const header = col.querySelector('h2, h3, .column-title');
                const cards = col.querySelectorAll('.kanban-card, .card, .task-card');
                if (header) {
                    const tasks = [];
                    cards.forEach(card => {
                        tasks.push(card.innerText.trim().substring(0, 200));
                    });
                    board[header.innerText.trim()] = tasks;
                }
            });
            return { board: board };
        }
    });

    console.log('[WebMCP] Registered 8 tools: search_docs, get_chapter, get_module_info, list_modules, get_toc, submit_review, get_report, get_board_status');
})();
</script>
'''.strip()
```

**注意**：
- 函数返回一个完整的 `<script>` 标签字符串
- `SCRIPT_PREFIX` 使用 `/docs.0-1.ai`（与现有代码中的 `SCRIPT_PREFIX` 变量保持一致）
- 每个 tool 都有清晰的 description，让 AI 能理解何时调用

### Step 2：在页面模板中注入 WebMCP JS

**位置**: 找到 docs-server.py 中生成 `<head>` 或 `</body>` 的位置（搜索 `</head>` 或 `</body>`），在每个页面底部（`</body>` 之前）插入 WebMCP JS。

**具体方法**：
1. 找到 `send_html` 函数或页面生成函数
2. 在 `html.replace('</body>', _make_webmcp_js() + '</body>')` 处注入

**如果找不到统一的注入点**，在每个 `return self.send_html(make_xxx())` 之前，先获取 HTML 字符串，再手动拼接：

```python
html = make_xxx()
html = html.replace('</body>', _make_webmcp_js() + '\n</body>')
return self.send_html(html)
```

**⚠️ 必须注入到所有页面**：首页、SOP 各章节、模块页、报告页、看板页、工具页。

### Step 3：验证 SCRIPT_PREFIX 一致性

**检查**：
```bash
grep -n "SCRIPT_PREFIX" /Users/lr/.openclaw/workspace/tools/docs-server.py | head -10
```

**确认**：WebMCP JS 中的 `SCRIPT_PREFIX` 值必须与 docs-server.py 中其他 JS 代码使用的值完全一致。如果不一致，API 调用会 404。

### Step 4：语法检查

**必须执行**：
```bash
python3 -c "import py_compile; py_compile.compile('/Users/lr/.openclaw/workspace/tools/docs-server.py', doraise=True)"
```

如果有 SyntaxError，立即修复后再继续。

### Step 5：重启 docs-server

**必须执行的步骤**：
1. 找到并杀掉旧进程：`ps aux | grep docs-server | grep -v grep`
2. 启动新进程：`nohup python3 /Users/lr/.openclaw/workspace/tools/docs-server.py > /tmp/docs-server.log 2>&1 &`
3. 验证启动成功：`curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://127.0.0.1:18998/docs.0-1.ai/`
4. 期望返回 `200`

### Step 6：功能验证

**验证 WebMCP JS 已注入**：
```bash
curl -s http://127.0.0.1:18998/docs.0-1.ai/ | grep -c "navigator.modelContext"
```
期望输出 ≥ 1。

**验证 API 端点正常**：
```bash
curl -s http://127.0.0.1:18998/docs.0-1.ai/api/search?q=贵庚 | head -200
```
期望返回 JSON 格式的搜索结果。

**验证章节页正常**：
```bash
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:18998/docs.0-1.ai/sop/chapter-2.html
```
期望返回 `200`。

### Step 7：（可选但推荐）添加 WebMCP 状态指示器

在页面底部（footer 区域）添加一个小标识，显示 WebMCP 工具数量：

```javascript
// 在 WebMCP 初始化代码末尾添加
if ('modelContext' in navigator) {
    const badge = document.createElement('div');
    badge.id = 'webmcp-badge';
    badge.style.cssText = 'position:fixed;bottom:8px;right:8px;background:#10b981;color:white;padding:2px 8px;border-radius:12px;font-size:11px;z-index:9999;opacity:0.6;cursor:default;';
    badge.textContent = '🤖 WebMCP: 8 tools';
    document.body.appendChild(badge);
}
```

---

## 四、验证 Checklist

完成后逐项确认：

| # | 检查项 | 验证方法 | 期望结果 |
|---|--------|---------|---------|
| 1 | Python 语法正确 | `py_compile` | 无报错 |
| 2 | Server 启动成功 | `curl` 返回 HTTP 200 | ✅ |
| 3 | WebMCP JS 已注入 | `grep navigator.modelContext` | ≥ 1 匹配 |
| 4 | search_docs tool 可调用 | Chrome DevTools Console 执行 tool 调用 | 返回搜索结果 |
| 5 | get_chapter tool 可调用 | 查询章节 2 | 返回概念与愿景内容 |
| 6 | list_modules tool 可调用 | 列出模块 | 返回模块列表 |
| 7 | 非 Chrome 浏览器不报错 | Firefox/Safari 打开 | 无 console 错误 |
| 8 | 所有页面都有 WebMCP | 检查 5+ 个页面 | 每页都有 script |

---

## 五、注意事项与风险

### 5.1 浏览器兼容性
- WebMCP 仅在 Chrome 146+ 支持（2026 年 5 月左右发布稳定版）
- 其他浏览器（Firefox、Safari）目前不支持，必须有降级处理（`if (!('modelContext' in navigator)) return;`）
- localhost 自动是 Secure Context，生产环境需要 HTTPS

### 5.2 安全考虑
- `submit_review` 是唯一的写操作，`readOnlyHint: false`，浏览器会要求用户确认
- 所有读操作都是 `readOnlyHint: true`，Agent 可以自由调用
- 内容截断到 8000 字符，防止过大响应

### 5.3 已知限制
- WebMCP Declarative（声明式 `<form webmcp>`）仍是 TODO
- 没有跨域工具发现机制（`.well-known/webmcp` 尚未标准化）
- Agent 必须先导航到站点页面才能发现工具

### 5.4 未来扩展方向（本次不实施）
- 添加 `.well-known/webmcp.json` 发现文件（等规范稳定）
- 支持 OAuth 2.1 认证的写操作
- 添加 `llms.txt` 标准文件提升 GEO（Agent 可发现性）
- 工具版本管理（与 Q3 版本号系统整合）

---

## 六、回滚方案

如果 WebMCP 注入导致页面异常：
1. 删除 `_make_webmcp_js()` 函数
2. 删除所有 `html.replace('</body>', ...)` 注入行
3. 重启 docs-server
4. 验证页面恢复正常

---

## 七、参考资料

| 资料 | 链接/路径 |
|------|----------|
| W3C WebMCP 规范 | https://webmachinelearning.github.io/webmcp |
| WebMCP GitHub 仓库 | https://github.com/webmachinelearning/webmcp |
| Chrome 146 WebMCP 指南 | https://bug0.com/blog/webmcp-chrome-146-guide |
| WebMCP 详解 | https://atalupadhyay.wordpress.com/2026/03/06/webmcp-guide/ |
| MCP 官方协议 | https://github.com/modelcontextprotocol/modelcontextprotocol |
| 本地 WebMCP 概述 | `/Users/lr/.openclaw/workspace/webmcp.md` |
| docs 站点 SOP | `/Users/lr/.openclaw/workspace/docs/docs.openclaw.ai-sop.md` |
| 源码文件 | `/Users/lr/.openclaw/workspace/tools/docs-server.py` |
