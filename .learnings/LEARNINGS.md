# Learnings Log

Captured learnings, corrections, and discoveries. Review before major tasks.

---

## LRN-20260314-004 智库5平台复杂问题测试

**Logged**: 2026-03-14T18:05:00+08:00
**Priority**: high
**Status**: complete
**Area**: automation

### Summary
测试"openclaw是什么"复杂问题，验证 wait_for_function 灵活等待方法

### Details
**测试结果**：
| 平台 | 结果 |
|------|------|
| DeepSeek | ✅ |
| 智谱 | ✅ |
| 千问 | ❌ (无联网) |
| 豆包 | ✅ |
| Kimi | ❌ (页面结构特殊) |

### Pattern-Key
复杂问题测试, wait_for_function, 联网搜索

---

## LRN-20260314-003 智库5平台问答自动化测试

**Logged**: 2026-03-14T17:40:00+08:00
**Priority**: high
**Status**: complete
**Area**: automation

### Summary
5个AI平台（DeepSeek、智谱、千问、豆包、Kimi）问答自动化测试经验总结

### Details
**测试平台结果：**
| 平台 | 结果 | 关键经验 |
|------|------|----------|
| DeepSeek | ✅ | Playwright + keyboard.type |
| 智谱 | ✅ | CDP失败，Playwright成功 |
| 千问 | ✅ | CDP失败，Playwright成功 |
| 豆包 | ✅ | 需滚动到页面底部 |
| Kimi | ✅ | 需点击"问点难的"进入聊天 |

**核心发现：**
1. CDP 原生接口（WebSocket）容易被各平台反自动化检测拦截
2. Playwright 连接已登录 Chrome + keyboard.type 是通用解决方案
3. 各平台预处理：
   - 智谱/千问：直接用 Playwright
   - 豆包：先滚动到页面底部
   - Kimi：先点击按钮进入聊天界面

### Pattern-Key
智库平台自动化, CDP反自动化, Playwright绕过

### See Also
- `智库平台问答测试SOP.md`
- `智谱问答测试执行日志.md`
- `千问问答测试执行日志.md`
- `豆包问答测试执行日志.md`
- `Kimi问答测试执行日志.md`

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

## 2026-03-14（续）

### 主题：Playwright 连接已登录 Chrome 解决 DeepSeek 输入问题

#### 背景
- **问题**：DeepSeek 网页版有反自动化检测，CDP 脚本输入被识别
- **已有条件**：Google Chrome 已登录 DeepSeek（通过 Browser Relay）
- **解决方案**：用 Playwright 连接已有 Chrome，绕过反自动化检测

#### 成功方法

**Step A: 连接已有 Chrome（CDP）**
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:18800")
```
- 使用 `connect_over_cdp` 连接已有 Chrome
- 无需启动新浏览器，直接复用已有登录状态

**Step B: 获取 DeepSeek 页面**
```python
context = browser.contexts[0]
for page in context.pages:
    if "deepseek" in page.url.lower():
        deepseek_page = page
        break
```

**Step C: 验证登录状态**
```python
deepseek_page.wait_for_load_state("networkidle", timeout=10000)
page_text = deepseek_page.inner_text("body")
if "登录" in page_text:
    raise Exception("Not logged in")
```

**Step D-F: 聚焦输入框 + 模拟打字 + 发送**
```python
input_box = deepseek_page.locator("textarea").first
input_box.click()
deepseek_page.keyboard.type("Explain what AI is in one sentence.", delay=100)
deepseek_page.keyboard.press("Enter")
```

**Step G-H: 等待并获取回复**
```python
deepseek_page.wait_for_timeout(15000)  # 或轮询检查
response_text = deepseek_page.locator("div[class*='message']").last.inner_text()
```

#### 核心突破
- `keyboard.type(delay=100)` 模拟真实打字速度，成功绕过 DeepSeek 反自动化
- `connect_over_cdp` 复用已有登录状态，无需重新登录

#### 关键教训
1. Playwright 连接已有 Chrome 用 `connect_over_cdp` 而非 `launch`
2. 必须先验证登录状态，未登录不执行后续操作
3. `keyboard.type` 带 delay 参数模拟人类打字
4. 选择器 `div[class*='message']` 可获取 AI 回复

#### Metadata
- Source: test_result
- Related Files: 
  - ~/.openclaw/workspace/Playwright 连接已登录 Chrome 解决 DeepSeek 输入问题 SOP.md
  - ~/.openclaw/workspace/Playwright_Chrome_执行日志.md
- Tags: playwright, deepseek, automation, cdp

---

## LRN-20260317-001 智库5平台"一句话"简单问题测试

**Logged**: 2026-03-17T21:00:00+08:00
**Priority**: high
**Status**: complete
**Area**: automation

### Summary
测试"请用一句话解释什么是人工智能？"简单问题，获取5个平台回复

### Details
**测试结果**：
| 平台 | 结果 | 回复内容 |
|------|------|----------|
| DeepSeek | ✅ | 人工智能是让计算机系统模拟人类智能... |
| 智谱 | ✅ | 人工智能是指由计算机系统所表现出的智能... |
| 千问 | ✅ | 人工智能是让机器模拟、延伸和扩展人类智能... |
| 豆包 | ✅ | 人工智能，就是让机器模拟、延伸甚至超越人类... |
| Kimi | ✅ | 人工智能是让计算机系统能够模拟人类智能行为... |

### 成功经验

**各平台"思考完成"关键词**：
| 平台 | 关键词 | 说明 |
|------|--------|------|
| DeepSeek | 已思考 | 页面显示"已思考 XX 秒" |
| 智谱 | 思考结束 | 页面显示"思考结束" |
| 千问 | 已经完成思考 | 页面显示"已经完成思考" |
| 豆包 | 处理中消失 | "AI 正在思考"或"处理中"消失 |
| Kimi | 问题文本分割 | 取问题文本之后的内容 |

**复制按钮检测**：
- 关键：很多按钮需要 hover() 才显示
- 方法：滚动到关键词位置 → 等待网络稳定 → hover() 触发 → 多策略检测

### Pattern-Key
智库平台, 思考完成关键词, 复制按钮检测, hover()

---
