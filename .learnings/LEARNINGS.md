# LEARNINGS.md - 经验教训记录

> 重要：所有错误和经验教训都应该记录在这里，方便下次遇到同样问题时查阅。

---

## 2026-03-11

### 主题：豆包网页版自动化对话

#### 失败的尝试

**1. 直接 API 调用**
- 方法：`curl` 直接调用豆包 API
- 结果：❌ 失败，需要 `a_bogus` 签名参数
- 原因：豆包 API 需要动态生成的防爬虫签名

**2. osascript 激活窗口输入**
- 方法：`osascript` 激活 Chrome → 输入 → 发送
- 结果：⚠️ 窗口会跳到最前面，打扰用户
- 原因：每次操作都需要激活目标应用

**3. JavaScript 键盘事件模拟**
- 方法：`dispatchEvent(new KeyboardEvent("keydown", {key: "Enter"}))`
- 结果：❌ 不稳定，豆包页面检测到是自动化操作
- 原因：豆包有反自动化机制，JavaScript 模拟的键盘事件被拦截

**4. DOM 点击发送按钮（第一次尝试）**
- 方法：`document.querySelector('button').click()`
- 结果：❌ 不触发发送
- 原因：豆包使用 React + 自定义事件处理，简单的 click() 不够

#### 成功的方案

**最终方案：纯 Browser Relay + CSS 选择器遍历父容器**
- 方法：
  1. `document.querySelector('textarea')` 找到输入框
  2. 设置 `value` 并触发 `input` 事件
  3. **遍历父容器**，找到带 SVG 的按钮并点击
  4. 使用 `openclaw browser evaluate` 执行 JavaScript
- 结果：✅ 成功，零窗口跳动
- 关键代码：
  ```javascript
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
  ```

---

## 2026-03-10

### Browser Relay 调试经验

#### 错误记录

**ERR-20260310-001**: 消息缓冲机制问题
- 问题：用户说"停下来"后消息仍在队列中执行
- 解决：**执行交给 subagents，我负责终止**

**ERR-20260310-004**: Browser Relay 连接失败
- 问题：使用了错误方法 `openclaw browser start`
- 教训：**禁止使用 openclaw browser 命令**，这些命令会创建新 Chrome 进程

**ERR-20260310-005**: 没用 subagents 自己执行任务
- 问题：调试时自己执行了任务
- 教训：按照 SOUL.md 规则，执行交给 subagents

**ERR-20260310-007, ERR-20260310-008**: 使用 openclaw browser 命令错误
- 解决：用 osascript 代替

#### 重要规则

1. **禁止自己执行任务**，交给 subagents
2. **指令不明确时**，先列出可能性让用户选择
3. **Browser Relay 问题**：用 osascript 代替 openclaw browser 命令

---

## 2026-03-09

### 微信公众号文章获取

#### 失败的尝试
1. **curl 直接请求** → 返回"环境异常"验证页面
2. **jina.ai 服务** → 请求超时

#### 成功方法
- 使用 `openclaw browser open "链接"` 打开页面
- 使用 `openclaw browser snapshot --json` 获取内容
- 关键：**微信公众号需要登录态，OpenClaw Browser 可以保持登录**

#### 重要要点
1. 微信公众号文章需要登录态
2. 不要用 curl/网络请求工具直接抓取
3. 优先使用 OpenClaw 自带浏览器

---

## 2026-03-09

### 豆包自动化输入技术

#### 问题
豆包页面使用 React 动态渲染，aria-ref 不稳定

#### 解决
使用 JavaScript 注入直接操作 DOM：
1. `document.querySelector('div[role="textbox"]')?.focus()` 聚焦
2. `document.execCommand('insertText', false, '文字')` 输入

---

## 2026-03-09

### Homebrew Node 安装问题

#### 问题
VPN 代理配置未清理导致 brew 无法连接

#### 解决
```bash
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy ALL_PROXY
```

---

## 2026-03-08

### MiniMax Tools 调试

#### 问题
必须添加 model 参数，图片 URL 必须是字符串格式

---

## 2026-03-07

### 子Agent任务经验

#### Agent 1: OpenClaw Lite 调研
- 结论：存在社区轻量版（nanobot, nanoclaw, clawlet），但它们是独立实现，**不支持连接 Gateway**

#### Agent 2: Cyber Bricks 调研
- 接入方案：WiFi HTTP / MQTT / WebSocket

#### Agent 3: Ubuntu 台式机对接 Gateway
- 命令：`openclaw node run --host <Gateway-IP> --port 18789`

---

## 2026-03-06

### QQ 机器人配置

#### 关键教训
- **OCR 识别容易把字母 O 和数字 0 混淆**
- 识别结果：`KU03...` → 正确：`KUO3...`
- **配置完成后务必核对原始图片中的字符**

---

## 2026-03-06

### 图片管理优化

#### 解决方案
创建各平台专用目录：
- 飞书：`~/.openclaw/workspace/feishu-images/`
- Telegram：`~/.openclaw/workspace/telegram-images/`
- Discord：`~/.openclaw/workspace/discord-images/`
- WhatsApp：`~/.openclaw/workspace/whatsapp-images/`
- Signal：`~/.openclaw/workspace/signal-images/`
- WeChat：`~/.openclaw/workspace/wechat-images/`

#### 命名规则
精确到秒：`YYYY-MM-DD-HH-mm-ss.png`

---

## 重要安全规则

1. **危险命令必须先确认**：删除、移动等操作前先问用户
2. **rm -rf 不能随便用**：删除前先检查内容，问用户确认
3. **不要在没确认的情况下合并目录**：先检查有没有重要数据

---

## 相关文件

- Skill: `~/.openclaw/workspace/skills/doubao-osascript/`
- 日志: `~/.openclaw/workspace/memory/2026-03-*.md`
- Browser Relay: `~/.openclaw/workspace/memory/browser-relay-*.md`

---

## 重要规则（必须遵守）- 2026-03-11

### 1. 图片分析必须用 minimax-tools
- ❌ 禁止用 exec + read 命令读取图片
- ✅ 必须用 `python3 ~/.openclaw/workspace/skills/minimax-tools/minimax.py image` 命令
- ⚠️ 工具输出为空时，很可能是用错工具了

### 2. 测试时必须等待用户指示
- 用户说执行哪步就执行哪步
- ❌ 禁止自动执行后续步骤
- ✅ 等用户明确指示后再继续

### 3. DeepSeek 自动化要点
- JavaScript 设置 value 无效（页面不显示）
- 必须用 osascript + 键盘输入
- 用 cliclick 点击坐标激活输入框
- 然后用 osascript 逐字输入
- **重要**：osascript 命令要**合并成一次执行**，不能分多次（会内容连在一起）

### 4. DeepSeek 截图要点
- 截图前必须先确认窗口是否正确
- 不要假设页面是对的，必须先验证
- 用 minimax.py 分析整个 Chrome 窗口，确认是哪个页面

### 5. DeepSeek 发送要点
- 发送前必须确保窗口激活
- 先 `osascript -e 'tell application "Google Chrome" to activate'`
- 然后再按回车发送
