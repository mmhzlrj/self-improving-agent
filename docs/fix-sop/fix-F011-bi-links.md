# F-011: 双向链接系统

## 问题描述
模块文档和 SOP 章节之间没有互相链接。比如 arm.md 提到"Phase 4"但没有链接到 SOP 第四章，SOP 提到 Cyber Bricks 也没有链接到 arm.md。

## 文件
- `/Users/lr/.openclaw/workspace/tools/docs-server.py`
- 修改 `render_markdown` 函数或新增后处理步骤

## 修复步骤

### Step 1：定义关键词→链接映射表

在 docs-server.py 中（MODULE_DATA 附近）添加：

```python
# 双向链接关键词映射
BI_LINKS = [
    # 模块关键词 → 模块页面
    (r'\bCyber Bricks\b', f'{SCRIPT_PREFIX}/modules/arm.html'),
    (r'\b机械臂\b', f'{SCRIPT_PREFIX}/modules/arm.html'),
    (r'\bESP32-Cam\b', f'{SCRIPT_PREFIX}/modules/vision.html'),
    (r'\b视觉识别\b', f'{SCRIPT_PREFIX}/modules/vision.html'),
    (r'\bYOLO\b', f'{SCRIPT_PREFIX}/modules/vision.html'),
    (r'\b贵庚\b', f'{SCRIPT_PREFIX}/modules/gui-geng.html'),
    (r'\bSemantic Cache\b', f'{SCRIPT_PREFIX}/modules/gui-geng.html'),
    (r'\bLeWM\b', f'{SCRIPT_PREFIX}/modules/lewm.html'),
    (r'\b世界模型\b', f'{SCRIPT_PREFIX}/modules/lewm.html'),
    (r'\b吸盘\b', f'{SCRIPT_PREFIX}/modules/suction.html'),
    (r'\b面部表情\b', f'{SCRIPT_PREFIX}/modules/face.html'),
    (r'\b0-1.*三元素\b', f'{SCRIPT_PREFIX}/modules/face.html'),
    (r'\b移动模块\b', f'{SCRIPT_PREFIX}/modules/locomotion.html'),
    (r'\bROS 2\b', f'{SCRIPT_PREFIX}/modules/locomotion.html'),
    # SOP 章节关键词 → SOP 章节页面
    (r'\bPhase 0\b', f'{SCRIPT_PREFIX}/sop/chapter-4.html#phase-0'),
    (r'\bPhase 1\b', f'{SCRIPT_PREFIX}/sop/chapter-4.html#phase-1'),
    (r'\bPhase 2\b', f'{SCRIPT_PREFIX}/sop/chapter-4.html#phase-2'),
    (r'\bPhase 3\b', f'{SCRIPT_PREFIX}/sop/chapter-4.html#phase-3'),
    (r'\bPhase 4\b', f'{SCRIPT_PREFIX}/sop/chapter-4.html#phase-4'),
    (r'\bPhase 5\b', f'{SCRIPT_PREFIX}/sop/chapter-4.html#phase-5'),
    (r'\bPhase 6\b', f'{SCRIPT_PREFIX}/sop/chapter-4.html#phase-6'),
    (r'\bJetson Nano\b', f'{SCRIPT_PREFIX}/sop/chapter-2.html'),
    (r'\b星闪\b', f'{SCRIPT_PREFIX}/sop/chapter-2.html'),
    (r'\b拓竹 H2C\b', f'{SCRIPT_PREFIX}/sop/chapter-2.html'),
]
```

### Step 2：创建双向链接处理函数

```python
def apply_bi_links(html_text):
    """Apply bidirectional links to HTML content"""
    for pattern, url in BI_LINKS:
        # 只替换不在 <a> 标签内的匹配
        html_text = re.sub(
            f'(?<![">/])({pattern})(?![^<]*</a>)',
            f'<a href="{url}" style="color:var(--accent2);border-bottom:1px dotted var(--accent2)" title="查看相关文档">\\1</a>',
            html_text
        )
    return html_text
```

### Step 3：在渲染后应用双向链接

找到 `render_markdown` 的调用处，在返回 HTML 前套用 `apply_bi_links`。

最简单的方法：修改 `render_markdown` 函数本身，在末尾添加：
```python
    return apply_bi_links(html)
```

或者如果不想改 render_markdown，在各个 make_* 函数中，对最终 HTML 调用 `apply_bi_links`。

### Step 4：重启并验证

## 验证标准
- [ ] SOP 中 "Cyber Bricks" 文字变成可点击链接
- [ ] 模块文档中 "Phase 4" 变成可点击链接，跳转到 SOP 第四章
- [ ] 链接不会破坏已有 Markdown 链接
- [ ] 已有 <a> 标签内的文字不会被重复加链接
