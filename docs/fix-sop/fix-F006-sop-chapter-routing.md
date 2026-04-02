# F-006: 修复 SOP 章节路由"章节未找到"Bug

## 问题描述
访问 http://127.0.0.1:18998/docs.0-1.ai/sop/chapter-0.html 等页面显示"章节未找到"。

## 根因分析

### 问题 1：chapter_names 与 SOP 实际标题不匹配
`make_sop_chapter()` 中的 `chapter_names` 字典：
```python
chapter_names = {
    0: "第0章：启动与配置",    # ❌ SOP 里没有这个标题
    1: "第一章：概念与愿景",    # ✅ 匹配
    2: "第二章：硬件体系",      # ✅ 匹配
    3: "第3章：软件架构",      # ❌ 实际是 "第三章：系统架构"
    4: "第四章：实施阶段",      # ✅ 匹配
    5: "第5章：安全系统",      # ❌ 实际是 "第五章：AI 与感知"
    6: "第6章：数据管理",      # ❌ 实际是 "第六章：本地 LLM 推理"
}
```

### 问题 2：SOP 有 10 章，导航只显示 0-6
实际 H1 标题（ROBOT-SOP.md）：
- Line 0: `🤖 0-1 私人 AI 机器人完整实施指南`（标题，不是章节）
- Line 15: `目录`（不是章节）
- Line 234: `第一章：概念与愿景`
- Line 1870: `第二章：硬件体系`
- Line 2435: `第三章：系统架构`
- Line 2810: `第四章：实施阶段`
- Line 3453: `第五章：AI 与感知`
- Line 4166: `第六章：本地 LLM 推理`
- Line 4302: `第七章：附录`
- Line 4464: `第八章：安全与维护`
- Line 4670: `第九章：风险与合规`
- Line 4699: `第十章：调研更新记录`
- Line 4926: `术语表（Glossary）`

### 问题 3：非章节 H1 标题打断解析
SOP 内部有 `# 1. 配置 locale` 等步骤标题，它们被 `parse_sop_chapters()` 当作新章节处理，导致内容被截断。

## 修复方案

### Step 1：用 Python 脚本动态提取章节标题（最可靠）
在 `make_sop_chapter()` 函数中，不再用硬编码的 `chapter_names`，而是从 `chapters` 字典中按索引查找。

修改 `make_sop_chapter()` 函数（约第 622 行）：

**替换前（第 622-638 行附近）：**
```python
def make_sop_chapter(chapter_num, active_id):
    """Render a SOP chapter — 显示完整章节内容，无截断"""
    chapters = load_sop_content()
    chapter_names = {
        0: "第0章：启动与配置",
        1: "第一章：概念与愿景",
        2: "第二章：硬件体系",
        3: "第3章：软件架构",
        4: "第四章：实施阶段",
        5: "第5章：安全系统",
        6: "第6章：数据管理",
    }
    ch_name = chapter_names.get(chapter_num, "")
    ch = chapters.get(ch_name, {})

    if not ch:
        return make_page(active_id, f"第{chapter_num}章", "<p>章节未找到。</p>")
```

**替换后：**
```python
def make_sop_chapter(chapter_num, active_id):
    """Render a SOP chapter — 显示完整章节内容，无截断"""
    chapters = load_sop_content()
    # 按文件出现顺序排序章节标题（跳过非章节标题）
    chapter_order = [
        "🤖 0-1 私人 AI 机器人完整实施指南",
        "目录",
        "第一章：概念与愿景",
        "第二章：硬件体系",
        "第三章：系统架构",
        "第四章：实施阶段",
        "第五章：AI 与感知",
        "第六章：本地 LLM 推理",
        "第七章：附录",
        "第八章：安全与维护",
        "第九章：风险与合规",
        "第十章：调研更新记录",
        "术语表（Glossary）",
    ]
    # 尝试用列表中的标题匹配，也尝试匹配已解析的章节 key
    ch_key = chapter_order[chapter_num] if chapter_num < len(chapter_order) else ""
    ch = chapters.get(ch_key, {})
    # 如果精确匹配失败，用模糊匹配（章节号）
    if not ch:
        import re as _re
        pat = _re.compile(r'第([一二三四五六七八九十\d]+)章')
        for k, v in chapters.items():
            m = pat.search(k)
            if m:
                cn = m.group(1)
                num_map = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}
                if num_map.get(cn, int(cn) if cn.isdigit() else -1) == chapter_num:
                    ch = v
                    ch_key = k
                    break
    # chapter_num=0 对应前言/目录
    if chapter_num == 0 and not ch:
        # 取前两个 H1 合并（标题+目录）
        keys = list(chapters.keys())
        if len(keys) >= 2:
            ch = dict(chapters[keys[0]])
            ch['content'] = chapters[keys[0]].get('content','') + '\n' + chapters[keys[1]].get('content','')
            ch['subsections'] = chapters[keys[0]].get('subsections',[]) + chapters[keys[1]].get('subsections',[])
            ch['title'] = "前言与目录"

    if not ch:
        return make_page(active_id, f"第{chapter_num}章", f"<p>章节未找到。可用章节：</p><ul>{''.join(f'<li><a href=\"{SCRIPT_PREFIX}/sop/chapter-{i}.html\">{chapter_order[i] if i < len(chapter_order) else \"?\"}</a></li>' for i in range(len(chapter_order)))}</ul>")
```

### Step 2：更新侧边栏导航（NAV_CONFIG）
将 SOP 章节导航从 0-6 扩展到 0-10：

**替换前（约第 41-49 行）：**
```python
    {"id": "sop-ch0", "label": "第0章：启动与配置", "path": "/sop/chapter-0.html"},
    {"id": "sop-ch1", "label": "第1章：概念与愿景", "path": "/sop/chapter-1.html"},
    {"id": "sop-ch2", "label": "第2章：硬件体系",   "path": "/sop/chapter-2.html"},
    {"id": "sop-ch3", "label": "第3章：软件架构",   "path": "/sop/chapter-3.html"},
    {"id": "sop-ch4", "label": "第4章：实施阶段",   "path": "/sop/chapter-4.html"},
    {"id": "sop-ch5", "label": "第5章：安全系统",   "path": "/sop/chapter-5.html"},
    {"id": "sop-ch6", "label": "第6章：数据管理",   "path": "/sop/chapter-6.html"},
    {"id": "sop-ch7", "label": "完整 SOP",          "path": "/sop/full.html"},
```

**替换后：**
```python
    {"id": "sop-ch0", "label": "前言与目录",       "path": "/sop/chapter-0.html"},
    {"id": "sop-ch1", "label": "第一章：概念与愿景", "path": "/sop/chapter-1.html"},
    {"id": "sop-ch2", "label": "第二章：硬件体系",   "path": "/sop/chapter-2.html"},
    {"id": "sop-ch3", "label": "第三章：系统架构",   "path": "/sop/chapter-3.html"},
    {"id": "sop-ch4", "label": "第四章：实施阶段",   "path": "/sop/chapter-4.html"},
    {"id": "sop-ch5", "label": "第五章：AI 与感知",  "path": "/sop/chapter-5.html"},
    {"id": "sop-ch6", "label": "第六章：本地 LLM 推理","path": "/sop/chapter-6.html"},
    {"id": "sop-ch7", "label": "第七章：附录",       "path": "/sop/chapter-7.html"},
    {"id": "sop-ch8", "label": "第八章：安全与维护", "path": "/sop/chapter-8.html"},
    {"id": "sop-ch9", "label": "第九章：风险与合规", "path": "/sop/chapter-9.html"},
    {"id": "sop-ch10", "label": "第十章：调研记录",  "path": "/sop/chapter-10.html"},
    {"id": "sop-full", "label": "完整 SOP",          "path": "/sop/full.html"},
```

### Step 3：修复 parse_sop_chapters 的 H1 拦截问题
在 `parse_sop_chapters()` 中，不要把 `# 数字.` 开头的行当作新章节：

在 `for line in lines:` 循环中，修改 `if line.startswith('# '):` 的判断：

**替换前：**
```python
        if line.startswith('# '):
            if current['title']:
                save_subsection()
                chapters[current_h1] = dict(current)
            current = {'title': line[2:].strip(), 'content': '', 'subsections': []}
            current_h1 = current['title']
```

**替换后：**
```python
        if line.startswith('# ') and not re.match(r'^# \d+\.', line):
            if current['title']:
                save_subsection()
                chapters[current_h1] = dict(current)
            current = {'title': line[2:].strip(), 'content': '', 'subsections': []}
            current_h1 = current['title']
```

这样 `# 1. 配置 locale` 之类的步骤标题不会被当作新章节。

### Step 4：删除 SOP 缓存（强制重新解析）
```bash
rm -f /Users/lr/.openclaw/workspace/docs/.sop_cache.json
```

### Step 5：重启并验证
```bash
lsof -ti:18998 | xargs kill -9 2>/dev/null; sleep 1; cd /Users/lr/.openclaw/workspace && nohup python3 tools/docs-server.py > /tmp/docs-server.log 2>&1 & sleep 2; curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:18998/docs.0-1.ai/sop/chapter-0.html
```

### Step 6：逐个验证每个章节
用浏览器或 curl 验证以下 URL 都返回 200 且有内容（不是"章节未找到"）：
- `/sop/chapter-0.html`（前言与目录）
- `/sop/chapter-1.html`（第一章）
- `/sop/chapter-2.html`（第二章）
- `/sop/chapter-3.html`（第三章）
- `/sop/chapter-4.html`（第四章）
- `/sop/chapter-5.html`（第五章）
- `/sop/chapter-6.html`（第六章）
- `/sop/chapter-7.html`（第七章）
- `/sop/chapter-8.html`（第八章）
- `/sop/chapter-9.html`（第九章）
- `/sop/chapter-10.html`（第十章）

## 验证标准
- [ ] 11 个章节 URL 全部返回 200 且有实际内容
- [ ] 侧边栏显示所有 11 个章节 + 完整 SOP
- [ ] 每个"第X章"页面显示正确的标题（与 SOP 一致）
- [ ] `.sop_cache.json` 已删除（首次访问时重建）
