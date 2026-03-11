# 豆包对话 Skill (osascript 版) - 完整安装指南

通过 macOS Browser Relay + CSS 选择器调用豆包网页版进行对话。无需 API Key，完全后台运行，零窗口跳动。

## 功能

- ✅ 自动在豆包页面输入问题
- ✅ 自动发送消息
- ✅ 自动提取 AI 回答
- ✅ 无需 API Key
- ✅ 支持中文对话
- ✅ 默认使用"专家"模式
- ✅ **零窗口跳动**（后台运行）

---

## 完整安装步骤（从零开始）

### 步骤 1：安装依赖工具

```bash
# 安装 cliclick (鼠标点击工具)
brew install cliclick
```

### 步骤 2：登录豆包账号

1. 打开 Chrome 浏览器
2. 访问 https://www.doubao.com/chat/
3. 登录你的豆包账号
4. **保持登录状态，不要退出**

### 步骤 3：确保 Browser Relay 运行

```bash
# 启动 Browser Relay
openclaw browser start
```

### 步骤 4：创建 Skill 目录

```bash
mkdir -p ~/.openclaw/workspace/skills/doubao-osascript/scripts
```

### 步骤 5：下载脚本

将 `send-message.sh` 保存到 `~/.openclaw/workspace/skills/doubao-osascript/scripts/`

### 步骤 6：添加执行权限

```bash
chmod +x ~/.openclaw/workspace/skills/doubao-osascript/scripts/send-message.sh
```

---

## 使用方法

### 基本对话

直接对你的 OpenClaw 说：
```
问豆包：你好，请介绍一下你自己
```

### 带模型选择

```
问豆包(思考)：你好
问豆包(快速)：你好
```

---

## 技术原理

### 1. 导航和模型切换

通过 OpenClaw Browser Relay 获取页面快照，动态获取按钮 ref：
```bash
openclaw browser snapshot  # 获取页面元素 ref
openclaw browser click e1234  # 点击按钮
```

### 2. 输入和发送（零窗口跳动核心）

使用 **CSS 选择器 API** 在后台操作：

```javascript
// 找到输入框
var textarea = document.querySelector('textarea');

// 输入文字
textarea.value = '问题内容';
textarea.dispatchEvent(new Event('input', {bubbles: true}));

// 找到发送按钮（遍历父容器，找最后一个带 SVG 的按钮）
var parent = textarea.parentElement;
while (parent) {
    var btns = parent.querySelectorAll('button');
    for (var i = btns.length - 1; i >= 0; i--) {
        if (btns[i].querySelector('svg')) {
            btns[i].click();  // 点击发送
            break;
        }
    }
    parent = parent.parentElement;
}
```

### 3. 获取回答

```javascript
// 获取页面所有文本
document.body.innerText
```

---

## 关键代码片段

### 发送消息脚本 (send-message.sh)

```bash
#!/bin/bash
MESSAGE="$1"
MODEL="${2:-专家}"  # 默认专家模式

# 1. 导航
openclaw browser navigate "https://www.doubao.com/chat/38416305792801026"
sleep 3

# 2. 切换模型（通过快照获取 ref）
openclaw browser click "$MODEL_BTN_REF"
sleep 1
openclaw browser click "$MODEL_ITEM_REF"
sleep 1

# 3. 用 CSS 选择器输入并发送（零窗口跳动）
openclaw browser evaluate --fn "
(function() {
    var textarea = document.querySelector('textarea');
    textarea.value = '$MESSAGE';
    textarea.dispatchEvent(new Event('input', {bubbles: true}));
    
    // 找到发送按钮并点击
    var parent = textarea.parentElement;
    while (parent && parent.tagName !== 'BODY') {
        var btns = parent.querySelectorAll('button');
        for (var i = btns.length - 1; i >= 0; i--) {
            if (btns[i].querySelector('svg')) {
                btns[i].click();
                return 'sent';
            }
        }
        parent = parent.parentElement;
    }
    return 'fallback';
})()
"

# 4. 等待响应
sleep 20

# 5. 获取回答
openclaw browser evaluate --fn 'document.body.innerText'
```

---

## 故障排除

### 问题：发送失败

**可能原因**：页面结构变化，CSS 选择器失效

**解决方法**：检查豆包页面是否更新了布局

### 问题：模型切换失败

**可能原因**：ref 变化

**解决方法**：重新获取页面快照，找到正确的 ref

---

## 文件结构

```
doubao-osascript/
├── SKILL.md                 # 本文件
├── README.md                # 简要说明
└── scripts/
    └── send-message.sh      # 发送消息脚本
```

---

## 依赖清单

| 工具 | 安装方式 | 用途 |
|------|----------|------|
| openclaw | 已有 | Browser Relay 控制 |
| Chrome | 已有 | 豆包网页版 |

---

## 更新日志

- **2026-03-11**: 创建 Skill，使用纯 Browser Relay + CSS 选择器实现零窗口跳动
