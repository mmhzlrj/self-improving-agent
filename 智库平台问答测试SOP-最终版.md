# 智库平台问答测试 SOP（最终版）

## 测试目标
将问题同步到多个 AI 网页平台（DeepSeek、智谱、千问、豆包、Kimi），获取 AI 回复后保存为 MD 文档。

---

## 一、测试问题
```
请用一句话解释什么是人工智能？
```

---

## 二、平台配置

| 平台 | 需要配置 | 说明 |
|------|----------|------|
| DeepSeek | 深度思考 + 智能搜索 | 两个都有 |
| 智谱 | 思考 + 联网 | 两个都有 |
| 千问 | 默认 | 不需要操作 |
| 豆包 | 专家模式 | 只有这个，没有联网 |
| Kimi | K2.5 思考 | 只有这个，没有联网 |

---

## 三、测试流程

### 3.1 Step A: 确认页面状态

**执行命令**:
```bash
curl -s http://127.0.0.1:18800/json | python3 -c "
import json,sys
data=json.load(sys.stdin)
for p in data:
    if '平台名' in p['title']:
        print(f\"ID: {p['id']}\")
        print(f\"URL: {p['url']}\")
"
```

### 3.2 Step B: 使用 Playwright 测试（通用方法）

**核心代码**:
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:18800")
    
    for page in browser.contexts[0].pages:
        if "平台关键字" in page.url.lower():
            # 预处理（根据平台选择）
            # ...
            
            # 找到输入框并输入
            page.wait_for_selector("textarea", timeout=5000)
            page.click("textarea")
            page.keyboard.type("问题内容", delay=100)
            
            # 发送
            page.keyboard.press("Enter")
            
            # 等待回复
            page.wait_for_load_state("networkidle", timeout=15000)
            
            # 获取回复
            content = page.inner_text("body")
            break
```

### 3.3 Step C: 各平台详细操作

#### DeepSeek
```python
# 无需预处理
page.keyboard.type("问题", delay=100)
page.keyboard.press("Enter")
```

#### 智谱
```python
# 无需预处理（CDP会失败，必须用Playwright）
page.keyboard.type("问题", delay=100)
page.keyboard.press("Enter")
```

#### 千问
```python
# 无需预处理（CDP会失败，必须用Playwright）
page.keyboard.type("问题", delay=100)
page.keyboard.press("Enter")
```

#### 豆包
```python
# 需要先滚动到页面底部
page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
page.wait_for_timeout(1000)

page.keyboard.type("问题", delay=100)
page.keyboard.press("Enter")
```

#### Kimi
```python
# 需要先点击"问点难的"进入聊天
# 或者导航到 /chat

# 方法1：点击按钮
page.evaluate("""
    var all = document.querySelectorAll("*");
    for(var i=0; i<all.length; i++) {
        if(all[i].textContent.indexOf("问点难的") !== -1) {
            all[i].click();
            return;
        }
    }
""")

# 方法2：直接导航
page.goto("https://kimi.com/chat")

# 然后找到输入元素
inputs = page.query_selector_all("input, textarea")
if inputs:
    inputs[0].fill("问题")
    page.keyboard.press("Enter")
```

---

## 四、等待回复

### 4.1 使用 Playwright 灵活等待（推荐）

```python
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:18800")
    
    for page in browser.contexts[0].pages:
        if "目标平台" in page.url.lower():
            # 方法1：等待输入框被清空（消息已发送）
            # 适用于：发送后输入框会清空的平台
            try:
                page.wait_for_function(
                    """() => document.querySelector("textarea").value === """"",
                    timeout=60000
                )
                print("✅ 消息已发送")
            except:
                print("⚠️ 等待超时")
            
            # 方法2：等待加载动画消失
            # 适用于：有加载动画的平台
            try:
                page.wait_for_selector(
                    "[class*='loading'], [class*='spinner']",
                    state="hidden",
                    timeout=60000
                )
                print("✅ 加载完成")
            except:
                print("⚠️ 等待加载超时")
            
            # 方法3：等待回复内容出现（最通用）
            # 适用于：所有平台
            try:
                # 等待页面出现新内容（回复通常在用户问题之后）
                page.wait_for_function(
                    """() => {
                        const texts = document.body.innerText;
                        // 检查是否有 AI 回复的迹象
                        // - 包含"完成思考"
                        // - 包含"内容由AI生成"
                        // - 有新的段落出现
                        return texts.includes("完成") || 
                               texts.includes("内容由") ||
                               texts.length > 500;
                    }""",
                    timeout=60000
                )
                print("✅ AI 回复已生成")
            except Exception as e:
                print(f"⚠️ 等待回复超时: {e}")
            
            # 方法4：等待某个元素出现
            # 适用于：知道回复容器选择器的平台
            try:
                page.wait_for_selector(
                    "div[class*='message'], div[class*='response']",
                    state="visible",
                    timeout=60000
                )
                print("✅ 回复容器已出现")
            except:
                print("⚠️ 等待超时")
            
            # 获取最终页面内容
            content = page.inner_text("body")
            print("页面内容:", content[:200])
            
            break
    
    browser.close()
```

### 4.2 高级：动态检测生成完成

```python
# 更智能的检测：等待回复区域稳定
page.wait_for_function(
    """() => {
        // 检查是否还在生成
        const body = document.body.innerText;
        
        // 生成中的标志
        const generating = [
            "思考中", "生成中", "loading", 
            "正在思考", "正在生成", "Stop"
        ];
        
        for (const text of generating) {
            if (body.includes(text)) {
                return false; // 还在生成
            }
        }
        
        // 检查是否有有效回复内容（长度 > 100 字符）
        return body.length > 100;
    }""",
    timeout=120000,  # 2分钟超时
    polling=1000    # 每秒检查一次
)
print("✅ 生成完成")
```

---

## 五、保存回复到 MD 文件

### 5.1 文件命名规则
```python
def simplify_question(q, max_len=20):
    """精简问题到指定长度"""
    q = q.strip()
    if len(q) <= max_len:
        return q
    return q[:max_len] + "..."

# 文件名: 平台_问题_日期时间.md
# 示例: DeepSeek_请用一句话解释什么是人工智能？_20260314_172537.md
```

### 5.2 保存格式
```markdown
# {平台名} AI回复

## 原始问题
{问题内容}

## 回复时间
{时间}

## 回复内容
{AI回复内容}

## 平台信息
- 平台：{平台名}
- 模型：{模型名}
- 配置：{配置信息}
```

### 5.3 保存代码
```python
from datetime import datetime
import os

question = "请用一句话解释什么是人工智能？"
reply = "AI回复内容"
platform = "DeepSeek"
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
simplified_q = simplify_question(question)

content = f'''# {platform} AI回复

## 原始问题
{question}

## 回复时间
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 回复内容
{reply}

## 平台信息
- 平台：{platform}
- 模型：xxx
- 配置：xxx
'''

os.makedirs('ai-responses', exist_ok=True)
filename = f'ai-responses/{platform}_{simplified_q}_{timestamp}.md'
with open(filename, 'w', encoding='utf-8') as f:
    f.write(content)
```

---

## 六、测试清单

| 步骤 | 操作 | DeepSeek | 智谱 | 千问 | 豆包 | Kimi |
|------|------|----------|------|------|------|------|
| 1 | 配置检查 | ✅ | ✅ | ⏭️ | ✅ | ✅ |
| 2 | 打开网页 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 3 | 输入问题 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 4 | 发送 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 5 | 等待回复 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 6 | 保存MD | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 七、常见错误及解决

### 7.1 CDP 发送失败
- **原因**：智谱、千问等平台有反自动化检测
- **解决**：改用 Playwright 的 keyboard.type

### 7.2 输入框找不到
- **豆包**：需要滚动到页面底部
- **Kimi**：需要先进入聊天界面

### 7.3 元素不在视口内
- **解决**：`page.evaluate("window.scrollTo(0, document.body.scrollHeight)")`

---

## 八、经验总结

1. **Playwright 连接已登录 Chrome 是通用解决方案**
2. **CDP 原生接口容易被反自动化检测拦截**
3. **各平台需要不同的预处理**
4. **测试过程要实时记录日志**

---

## 版本信息
- **创建日期**：2026-03-14
- **版本**：v1.0
- **测试平台**：DeepSeek、智谱、千问、豆包、Kimi
