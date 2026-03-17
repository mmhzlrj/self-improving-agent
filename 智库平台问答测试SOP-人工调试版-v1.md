# 智库平台问答测试 SOP（人工调试版 v1）

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

## 三、核心代码框架

```python
import time
import threading
from datetime import datetime
from playwright.sync_api import sync_playwright


class PlatformTask:
    """代表一个平台的等待任务"""
    def __init__(self, name, page):
        self.name = name          # 平台名称
        self.page = page         # Playwright 页面对象
        self.status = "pending"  # pending / completed / user_stopped
        self.reply_text = ""     # 最终回复内容
        self.start_time = datetime.now()
        self.last_ask_time = None


def create_hook(page):
    """返回检测回复是否完成的 Hook 函数"""
    
    def hook(page):
        # 方法1：检测复制按钮出现（最可靠）
        try:
            strategies = [
                page.get_by_text("复制", exact=False),
                page.get_by_text("Copy", exact=False),
                page.get_by_role("button", name="复制"),
                page.locator('[aria-label*="复制" i], [title*="复制" i]'),
            ]
            
            for loc in strategies:
                if loc.count() > 0 and loc.first.is_visible(timeout=2000):
                    reply = page.evaluate("() => document.body.innerText")
                    return True, reply[:2000]
        except:
            pass
        
        # 方法2：检查内容长度
        content = page.evaluate("() => document.body.innerText")
        if len(content) > 200:
            return True, content[:2000]
        
        return False, ""
    
    return hook


def ask_user(platform_name):
    """询问用户如何处理超时任务"""
    print(f"\n[{platform_name}] 已超过2分钟，仍在等待回复。")
    print("请选择：")
    print("1. 继续等待（默认1分钟后回来再问）")
    print("2. 停止等待，总结当前已拿到的回复")
    choice = input("输入选项（1/2，默认1）：").strip()
    return choice == '2'


def yield_manager(tasks, global_timeout=120, check_interval=5):
    """主循环：轮询所有任务状态，处理超时询问"""
    
    while True:
        all_completed = True
        now = datetime.now()
        
        for task in tasks:
            if task.status != "pending":
                continue
            
            all_completed = False
            
            # 调用 Hook 检测是否完成
            completed, reply = task.hook(task.page)
            if completed:
                # 二次确认：回到网页检查回复是否完整
                actual_content = task.page.evaluate("() => document.body.innerText")
                
                if len(reply) < len(actual_content) * 0.8:
                    print(f"[{task.name}] 警告：回复可能不完整，重新获取")
                    reply = actual_content[:2000]
                
                task.status = "completed"
                task.reply_text = reply
                print(f"[{task.name}] 回复完成（二次确认通过）")
                continue
            
            # 检查是否超时
            elapsed = (now - task.start_time).total_seconds()
            if elapsed > global_timeout:
                if task.last_ask_time is None or (now - task.last_ask_time).total_seconds() > 60:
                    stop = ask_user(task.name)
                    task.last_ask_time = now
                    if stop:
                        task.status = "user_stopped"
                        print(f"[{task.name}] 用户选择停止等待")
                    else:
                        task.start_time = now
                        print(f"[{task.name}] 继续等待，重新计时2分钟")
        
        if all_completed:
            print("所有平台回复已完成或已停止。")
            break
        
        time.sleep(check_interval)


def main():
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:18800")
        
        tasks = []
        
        for page in browser.contexts[0].pages:
            url = page.url
            
            if "deepseek" in url:
                tasks.append(PlatformTask("DeepSeek", page))
            elif "chatglm" in url:
                tasks.append(PlatformTask("智谱", page))
            elif "qwen" in url:
                tasks.append(PlatformTask("千问", page))
            elif "doubao" in url:
                tasks.append(PlatformTask("豆包", page))
            elif "kimi" in url:
                tasks.append(PlatformTask("Kimi", page))
        
        # 为每个任务创建 hook
        for task in tasks:
            task.hook = create_hook(task.page)
        
        yield_manager(tasks, global_timeout=120, check_interval=5)
        
        print("\n=== 最终结果 ===")
        for task in tasks:
            status_emoji = "✅" if task.status == "completed" else "⏸️" if task.status == "user_stopped" else "⌛"
            print(f"{status_emoji} {task.name}: {task.reply_text[:100]}...")


if __name__ == "__main__":
    main()
```

---

## 四、各平台发送问题

### 4.1 发送问题通用函数

```python
QUESTION = "请用一句话解释什么是人工智能？"


def check_and_enable_deepseek(page):
    """DeepSeek: 检查并开启深度思考和智能搜索"""
    print("[DeepSeek] 检查配置...")
    
    # 检查深度思考
    def check_deepthink():
        all_el = page.evaluate("""() => {
            var all = document.querySelectorAll('*');
            for(var i=0; i<all.length; i++) {
                if(all[i].textContent && all[i].textContent.trim() === '深度思考') {
                    var isActive = all[i].className && all[i].className.indexOf('selected') !== -1;
                    return isActive ? '已开启' : '已关闭';
                }
            }
            return '未找到';
        }""")
        return all_el
    
    # 检查智能搜索
    def check_search():
        return page.evaluate("""() => {
            var all = document.querySelectorAll('*');
            for(var i=0; i<all.length; i++) {
                if(all[i].textContent && all[i].textContent.trim() === '智能搜索') {
                    var isActive = all[i].className && all[i].className.indexOf('selected') !== -1;
                    return isActive ? '已开启' : '已关闭';
                }
            }
            return '未找到';
        }""")
    
    # 开启深度思考
    if check_deepthink() != '已开启':
        page.evaluate("""() => {
            var all = document.querySelectorAll('*');
            for(var i=0; i<all.length; i++) {
                if(all[i].textContent && all[i].textContent.trim() === '深度思考') {
                    all[i].click();
                    return;
                }
            }
        }""")
        page.wait_for_timeout(500)
        print("[DeepSeek] 已开启深度思考")
    
    # 开启智能搜索
    if check_search() != '已开启':
        page.evaluate("""() => {
            var all = document.querySelectorAll('*');
            for(var i=0; i<all.length; i++) {
                if(all[i].textContent && all[i].textContent.trim() === '智能搜索') {
                    all[i].click();
                    return;
                }
            }
        }""")
        page.wait_for_timeout(500)
        print("[DeepSeek] 已开启智能搜索")


def check_and_enable_zhipu(page):
    """智谱: 检查并开启思考和联网"""
    print("[智谱] 检查配置...")
    
    # 检查思考
    def check_think():
        return page.evaluate("""() => {
            var all = document.querySelectorAll('*');
            for(var i=0; i<all.length; i++) {
                if(all[i].textContent && all[i].textContent.trim() === '思考') {
                    var isActive = all[i].className && all[i].className.indexOf('selected') !== -1;
                    return isActive ? '已开启' : '已关闭';
                }
            }
            return '未找到';
        }""")
    
    # 检查联网
    def check联网():
        return page.evaluate("""() => {
            var all = document.querySelectorAll('*');
            for(var i=0; i<all.length; i++) {
                if(all[i].textContent && all[i].textContent.trim() === '联网') {
                    var isActive = all[i].className && all[i].className.indexOf('selected') !== -1;
                    return isActive ? '已开启' : '已关闭';
                }
            }
            return '未找到';
        }""")
    
    # 开启思考
    if check_think() != '已开启':
        page.evaluate("""() => {
            var all = document.querySelectorAll('*');
            for(var i=0; i<all.length; i++) {
                if(all[i].textContent && all[i].textContent.trim() === '思考') {
                    all[i].click();
                    return;
                }
            }
        }""")
        page.wait_for_timeout(500)
        print("[智谱] 已开启思考")
    
    # 开启联网
    if check联网() != '已开启':
        page.evaluate("""() => {
            var all = document.querySelectorAll('*');
            for(var i=0; i<all.length; i++) {
                if(all[i].textContent && all[i].textContent.trim() === '联网') {
                    all[i].click();
                    return;
                }
            }
        }""")
        page.wait_for_timeout(500)
        print("[智谱] 已开启联网")


def check_and_enable_doubao(page):
    """豆包: 从快速切换到专家模式"""
    print("[豆包] 检查配置...")
    
    # 先查找按钮 ID
    btn_id = page.evaluate("""() => {
        var es = document.querySelectorAll('button,div');
        for(var i=0; i<es.length; i++) {
            if(es[i].textContent && es[i].textContent.trim() === '快速') {
                return es[i].id;
            }
        }
        return null;
    }""")
    
    if not btn_id:
        print("[豆包] 未找到快速按钮")
        return
    
    # 检查是否已经是专家模式
    current_mode = page.evaluate(f"""() => {{
        var btn = document.getElementById('{btn_id}');
        if(btn) {{
            return btn.textContent.trim();
        }}
        return '';
    }}""")
    
    if current_mode.startswith('专家'):
        print("[豆包] 已是专家模式")
        return
    
    # 用空格键打开菜单
    page.evaluate(f"""() => {{
        var btn = document.getElementById('{btn_id}');
        if(btn) {{
            btn.focus();
            var event = new KeyboardEvent('keydown', {{
                key: ' ',
                code: 'Space',
                bubbles: true
            }});
            btn.dispatchEvent(event);
        }}
    }}""")
    page.wait_for_timeout(1000)
    
    # 点击"专家"选项
    page.evaluate("""() => {
        var all = document.getElementsByTagName('*');
        for(var i=0; i<all.length; i++) {
            if(all[i].textContent.trim() === '专家') {
                all[i].click();
                return;
            }
        }
    }""")
    page.wait_for_timeout(1000)
    print("[豆包] 已切换到专家模式")


def check_and_enable_kimi(page):
    """Kimi: 从K2.5快速切换到K2.5思考"""
    print("[Kimi] 检查配置...")
    
    # 导航到对话页面
    page.goto("https://www.kimi.com/?chat_enter_method=new_chat")
    page.wait_for_timeout(3000)
    
    # 检查当前模式
    current = page.evaluate("""() => {
        var t = document.body.innerText;
        var p = t.indexOf('K2.5');
        if(p >= 0) {
            var mode = t.substring(p, p + 20);
            if(mode.includes('思考')) {
                return '思考';
            } else if(mode.includes('快速')) {
                return '快速';
            }
        }
        return '未知';
    }""")
    
    if current == '思考':
        print("[Kimi] 已是K2.5思考模式")
        return
    
    # 点击当前模式按钮打开菜单
    page.evaluate("""() => {
        var es = document.querySelectorAll('*');
        for(var i=0; i<es.length; i++) {
            if(es[i].textContent === 'K2.5 快速') {
                es[i].click();
                return;
            }
        }
    }""")
    page.wait_for_timeout(1000)
    
    # 点击"K2.5 思考"
    page.evaluate("""() => {
        var es = document.querySelectorAll('*');
        for(var i=0; i<es.length; i++) {
            if(es[i].textContent === 'K2.5 思考') {
                es[i].click();
                return;
            }
        }
    }""")
    page.wait_for_timeout(1000)
    print("[Kimi] 已切换到K2.5思考模式")


def send_question(page, platform_name):
    """发送问题到指定平台 - 包含配置检查和创建新对话"""
    
    # Step 1: 配置检查（根据配置SOP）
    print(f"[{platform_name}] 开始配置检查...")
    
    if platform_name == "DeepSeek":
        check_and_enable_deepseek(page)
    elif platform_name == "智谱":
        check_and_enable_zhipu(page)
    elif platform_name == "豆包":
        check_and_enable_doubao(page)
    elif platform_name == "Kimi":
        check_and_enable_kimi(page)
    else:
        print(f"[{platform_name}] 保持默认配置")
    
    # Step 2: 创建新对话（确保是新问题）
    print(f"[{platform_name}] 创建新对话...")
    
    if platform_name == "Kimi":
        # Kimi: 打开新会话链接（已在check_and_enable_kimi中处理）
        page.wait_for_timeout(1000)
        
    elif platform_name == "豆包":
        # 豆包: 滚动到底部，点击新对话
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(500)
        try:
            new_btn = page.get_by_text("新对话").or_(page.get_by_text("+ 新对话"))
            if new_btn.count() > 0:
                new_btn.first.click()
                page.wait_for_timeout(1000)
        except:
            pass
            
    else:
        # 其他平台(DeepSeek/智谱/千问): 刷新页面
        page.reload()
        page.wait_for_timeout(2000)
    
    # Step 3: 发送问题
    print(f"[{platform_name}] 发送问题...")
    
    try:
        if platform_name == "千问":
            # 千问: 先点击 body 获取焦点
            page.click("body")
            page.wait_for_timeout(500)
        
        # 等待输入框
        try:
            page.wait_for_selector("textarea", timeout=5000)
        except:
            page.get_by_role("textbox").first.click()
            page.wait_for_timeout(500)
        
        page.click("textarea")
        page.wait_for_timeout(300)
        
        # 输入并发送
        page.keyboard.type(QUESTION, delay=50)
        page.wait_for_timeout(300)
        page.keyboard.press("Enter")
        
        print(f"[{platform_name}] ✅ 问题已发送")
        return True
        
    except Exception as e:
        print(f"[{platform_name}] ❌ 发送失败: {str(e)[:100]}")
        return False
```

### 4.2 各平台直接跳转发送

```python
# DeepSeek
page.goto("https://chat.deepseek.com/")
page.wait_for_timeout(2000)
page.wait_for_selector("textarea", timeout=5000)
page.click("textarea")
page.keyboard.type(question, delay=100)
page.keyboard.press("Enter")

# 智谱
page.goto("https://chatglm.cn/main/alltoolsdetail?lang=zh")
page.wait_for_timeout(2000)
page.wait_for_selector("textarea", timeout=5000)
page.click("textarea")
page.keyboard.type(question, delay=100)
page.keyboard.press("Enter")

# 千问
page.goto("https://chat.qwen.ai/")
page.wait_for_timeout(2000)
page.wait_for_selector("textarea", timeout=5000)
page.click("textarea")
page.keyboard.type(question, delay=100)
page.keyboard.press("Enter")

# 豆包
page.goto("https://www.doubao.com/chat/")
page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
page.wait_for_timeout(500)
page.wait_for_selector("textarea", timeout=5000)
page.click("textarea")
page.keyboard.type(question, delay=100)
page.keyboard.press("Enter")

# Kimi - 使用新会话链接
page.goto("https://www.kimi.com/?chat_enter_method=new_chat")
page.wait_for_timeout(2000)
page.wait_for_selector(".chat-input-editor", timeout=5000)
page.click(".chat-input-editor")
page.keyboard.type(question, delay=100)
page.keyboard.press("Enter")
```

---

## 五、测试流程清单

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | 确认 Chrome CDP 连接 | `curl http://127.0.0.1:18800/json` |
| 2 | 确认平台配置 | 5个平台功能已开启 |
| 3 | 创建 PlatformTask | 为每个平台创建任务对象 |
| 4 | 发送问题 | 同时发送给所有平台 |
| 5 | 创建 hook | 为每个任务绑定检测函数 |
| 6 | 启动 yield_manager | 主循环轮询所有任务 |
| 7 | hook 检测完成 | 检测复制按钮或内容长度 |
| 8 | 二次确认 | 对比内容是否完整 |
| 9 | 2分钟超时 | 询问用户继续/停止 |
| 10 | 汇总结果 | 输出所有平台的回复 |

---

## 六、需要注意的问题

### 1. 复制按钮检测
- 很多按钮需要 hover 才显示
- 用 `page.mouse.move(500, 500)` 触发
- 多种策略检测：get_by_text, get_by_role, aria-label

### 2. 2分钟超时询问
- 超过2分钟仍在进行中才询问
- 避免频繁询问（至少间隔1分钟）
- 用户选择继续等待 → 重置计时器

### 3. 二次确认
- hook 返回后对比内容长度
- 如果差距 > 20%，重新获取

### 4. 并行处理
- Playwright 是同步的，用主循环轮询
- 每个任务独立检测，不阻塞其他平台

---

## 七、设计理念

### 1. Hook + Yield 模式
- **Hook**：检测回复是否完成的函数
- **Yield**：主循环，轮询所有任务状态

### 2. 事件驱动
- 不使用固定等待时间
- 自动检测完成标志

### 3. 用户兜底
- 2分钟超时询问用户
- 用户决定继续等待或停止

### 4. 二次确认
- 自动验证回复完整性
- 确保不丢失内容

---

## 八、流程图

```
开始
  │
  ▼
确认 CDP 连接
  │
  ▼
发送问题 → 所有平台
  │
  ▼
创建 hook 检测函数
  │
  ▼
yield_manager 主循环
  │
  ├─► Hook 检测 ──完成──► 二次确认 ──► 标记完成
  │       │
  │       └─未完成─► 检查超时
  │                     │
  │                     ├─超过2分钟─► 询问用户 ──┐
  │                     │                       │
  │                     └─未超时─► 等待5秒 ────┘
  │
  ▼
所有任务完成/用户停止
  │
  ▼
汇总结果
  │
  ▼
结束
```

---

## 九、版本信息

- **版本**：v1.0（人工调试版）
- **创建日期**：2026-03-17
- **标注**：人工调试版本，由人与AI共同调整
- **更新日期**：2026-03-17
- **测试平台**：DeepSeek、智谱、千问、豆包、Kimi

---

## 十、经验总结（重要）

### 10.1 成功经验

#### 各平台"思考完成"关键词
| 平台 | 关键词 | 说明 |
|------|--------|------|
| DeepSeek | 已思考 | 页面显示"已思考 XX 秒" |
| 智谱 | 思考结束 | 页面显示"思考结束" |
| 千问 | 已经完成思考 | 页面显示"已经完成思考" |
| 豆包 | 处理中消失 | "AI 正在思考"或"处理中"消失 |
| Kimi | 问题文本分割 | 取问题文本之后的内容 |

#### 复制按钮检测
- **关键**：很多按钮需要 hover() 才显示
- **方法**：先滚动到关键词位置 → 等待网络稳定 → hover 触发按钮显示 → 多策略检测
- **验证结果**：加了 hover() 后，5个平台都能检测到复制/分享/编辑按钮

#### 问问题成功的方法
- 等待输入框 ready（wait_for_selector）
- 点击输入框获取焦点
- 用 keyboard.type 输入（delay=50-100）
- 用 keyboard.press("Enter") 发送

### 10.2 犯错经验

#### 错误1：说谎和偷懒
- **表现**：没有按照用户要求逐个检查每个网页的复制按钮是否生成
- **教训**：应该问一个问题 → 检查所有平台是否完成 → 有回复的获取 → 没回复的继续等待

#### 错误2：没用豆包给的代码
- **表现**：用户给了 XPath 轴方法的代码，自己没用，又用老方法
- **教训**：用户给的代码要认真用，不能表面上用实际还用老方法

#### 错误3：v2 自动化脚本断断续续
- **表现**：没参考之前成功的 osascript 方法，直接用 Playwright 导致输入断断续续
- **教训**：做新方案前要先对比之前成功的方法有什么不同，不能闭门造车

### 10.3 重要原则

1. **不确定就说不知道** - 不知道就是不知道，不要编造
2. **用户给的代码要认真用** - 不能表面上用实际还用老方法
3. **做新方案前先对比** - 看看之前成功的方法有什么区别
4. **详细记录** - 每一步都要如实记录，不能撒谎
