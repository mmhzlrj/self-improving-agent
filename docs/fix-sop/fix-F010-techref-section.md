# F-010: 旧文档归类（技术参考栏目）

## 问题描述
`docs/` 根目录下有 18 个旧 md 文件（browser-relay-keepalive.md、comfyui-6gb-research.md 等），散落无组织，没有进入侧边栏导航，但搜索能搜到。应该归类到"技术参考"栏目下。

## 文件
- `/Users/lr/.openclaw/workspace/tools/docs-server.py`
- 18 个 `docs/*.md` 文件（不动文件位置，只添加导航）

## 修复步骤

### Step 1：列出所有 docs/*.md 文件
```bash
ls /Users/lr/.openclaw/workspace/docs/*.md
```

当前文件列表：
- SPEC.md
- before_tool_call-example.md
- blender-robot-test.md
- browser-background-open.md
- browser-relay-config.md
- browser-relay-full-guide.md
- browser-relay-keepalive.md
- chat-export-for-rl.md
- comfyui-6gb-research.md
- docs.openclaw.ai-sop.md
- jetson-nano-opensclaw-video-stream.md
- node-pairing-sop.md
- openclaw-builtin-skills.md
- openclaw-release-log.md
- openclaw-update-analysis-for-01-detailed.md
- openclaw-update-analysis-for-01.md
- post-upgrade-20260329.md
- video-generation-research.md

### Step 2：按主题分类

| 分类 | 文件 |
|------|------|
| 浏览器/Browser Relay | browser-relay-config.md, browser-relay-full-guide.md, browser-relay-keepalive.md, browser-background-open.md |
| OpenClaw | openclaw-builtin-skills.md, openclaw-release-log.md, openclaw-update-analysis-for-01.md, openclaw-update-analysis-for-01-detailed.md, post-upgrade-20260329.md, docs.openclaw.ai-sop.md |
| 硬件 | jetson-nano-opensclaw-video-stream.md, node-pairing-sop.md |
| 调研 | comfyui-6gb-research.md, video-generation-research.md |
| 其他 | SPEC.md, before_tool_call-example.md, blender-robot-test.md, chat-export-for-rl.md |

### Step 3：在 NAV_CONFIG 中添加"技术参考"栏目

在"参考链接"之前，添加新的导航项：

```python
    {"id": "techref",  "label": "技术参考",   "icon": "📚", "path": "/techref/",
     "children": [
        {"id": "tr-browser", "label": "Browser Relay",   "path": "/techref/browser-relay.html"},
        {"id": "tr-openclaw", "label": "OpenClaw 更新",   "path": "/techref/openclaw-updates.html"},
        {"id": "tr-hardware", "label": "硬件参考",        "path": "/techref/hardware.html"},
        {"id": "tr-research", "label": "调研资料",        "path": "/techref/research.html"},
        {"id": "tr-misc",     "label": "其他文档",        "path": "/techref/misc.html"},
     ]},
```

### Step 4：添加路由处理

在 Handler.do_GET 中，添加技术参考页面的路由。每个分类页面列出该分类下的文档，点击可查看：

```python
        # Tech reference pages
        if path.startswith("/techref/"):
            techref_dir = path[len("/techref/"):]
            category_map = {
                "browser-relay.html": ["browser-relay-config.md", "browser-relay-full-guide.md", "browser-relay-keepalive.md", "browser-background-open.md"],
                "openclaw-updates.html": ["openclaw-builtin-skills.md", "openclaw-release-log.md", "openclaw-update-analysis-for-01.md", "openclaw-update-analysis-for-01-detailed.md", "post-upgrade-20260329.md", "docs.openclaw.ai-sop.md"],
                "hardware.html": ["jetson-nano-opensclaw-video-stream.md", "node-pairing-sop.md"],
                "research.html": ["comfyui-6gb-research.md", "video-generation-research.md"],
                "misc.html": ["SPEC.md", "before_tool_call-example.md", "blender-robot-test.md", "chat-export-for-rl.md"],
            }

            if techref_dir in category_map:
                files = category_map[techref_dir]
                category_title = {
                    "browser-relay.html": "Browser Relay",
                    "openclaw-updates.html": "OpenClaw 更新",
                    "hardware.html": "硬件参考",
                    "research.html": "调研资料",
                    "misc.html": "其他文档",
                }.get(techref_dir, "技术参考")

                items_html = ""
                for fname in files:
                    f = DOCS_ROOT / fname
                    if f.exists():
                        text = f.read_text(encoding='utf-8')
                        title_m = re.match(r'^#\s+(.+)$', text)
                        title = title_m.group(1).strip() if title_m else fname
                        size_kb = len(text) / 1024
                        items_html += f"""
                        <div class="report-item">
                            <div class="report-item-title">📄 {title}</div>
                            <div class="report-item-meta">{fname} · {size_kb:.1f} KB</div>
                            <div style="margin-top:8px">
                                <a href="{SCRIPT_PREFIX}/{fname.replace('.md','.html')}" class="btn btn-outline" style="font-size:12px;padding:4px 12px">📖 查看</a>
                            </div>
                        </div>"""

                page_title = f"📚 {category_title}"
                return self.send_html(make_page("techref", page_title, f"""
                <div class="content-header">
                    <h1>{page_title}</h1>
                    <div class="content-meta">{len(files)} 个文档</div>
                </div>
                {items_html}
                """))
            elif techref_dir == "" or techref_dir == "index.html":
                # Tech reference index
                return self.send_html(make_page("techref", "📚 技术参考", "<p>请从左侧导航选择分类。</p>"))
            else:
                # Try to serve as individual doc
                doc_name = techref_dir.replace('.html', '.md')
                f = DOCS_ROOT / doc_name
                if f.exists():
                    content = f.read_text(encoding='utf-8')
                    html = render_markdown(content)
                    title_m = re.match(r'^#\s+(.+)$', content)
                    title = title_m.group(1).strip() if title_m else doc_name
                    return self.send_html(make_page("techref", title, f"""
                    <div class="content-header"><h1>{title}</h1><div class="content-meta">{doc_name}</div></div>
                    {html}
                    """))
```

### Step 5：重启并验证

## 验证标准
- [ ] 侧边栏显示"技术参考"栏目，有 5 个子分类
- [ ] 点击各分类能看到对应的文档列表
- [ ] 点击文档能查看内容
