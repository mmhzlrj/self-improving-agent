# 智库平台问答测试 - AI调试版准备

## 当前版本
- 人工调试版-v1: `智库平台问答测试SOP-人工调试版-v1.md`

## 需要改进的问题

### 问题1：获取到历史内容
**原因**：hook只检查内容长度>200，没有验证是否是新问题回答
**改进**：hook添加验证，检查回复是否包含新问题关键词

### 问题2：Kimi发送失败
**原因**：选择器不对
**改进**：使用配置SOP中的方法，导航到 `?chat_enter_method=new_chat`

### 问题3：千问发送失败
**原因**：代码编辑器阻挡
**改进**：先点击body获取焦点

### 问题4：二次确认逻辑
**原因**：用长度对比不准确
**改进**：检查是否包含新问题关键词

---

## AI调试版改进计划

### 1. 新建窗口问问题
不是用现有页面，而是用 `page.goto()` 打开各平台的新会话URL

### 2. hook改进
```python
def create_hook(page, question):
    def hook(page):
        # 检测复制按钮
        try:
            for loc in [page.get_by_text("复制"), page.get_by_text("Copy")]:
                if loc.count() > 0 and loc.first.is_visible(timeout=2000):
                    content = page.evaluate("() => document.body.innerText")
                    # 验证是否包含问题关键词
                    if question[:20] in content or len(content) > 500:
                        return True, content[:2000]
        except:
            pass
        
        # 备选：检查内容长度
        content = page.evaluate("() => document.body.innerText")
        if len(content) > 500:
            return True, content[:2000]
        
        return False, ""
    return hook
```

### 3. 发送流程改进
- DeepSeek: `page.goto("https://chat.deepseek.com/")` + 等待 + 发送
- 智谱: `page.goto("https://chatglm.cn/")` + 等待 + 发送
- 千问: `page.goto("https://chat.qwen.ai/")` + 等待 + 发送
- 豆包: `page.goto("https://www.doubao.com/chat/")` + 切换专家 + 发送
- Kimi: `page.goto("https://www.kimi.com/?chat_enter_method=new_chat")` + 发送

---

## 测试问题（待定）
准备一个通用问题，用于测试
