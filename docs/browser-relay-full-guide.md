
# Browser Relay 从0到1安装配置指南

本文档详细记录 OpenClaw Browser Relay 的完整安装、配置和调优过程。

---

## 一、什么是 Browser Relay

Browser Relay 是一个 Chrome 扩展，允许 OpenClaw 控制用户已有的 Chrome 浏览器标签页。

**与 OpenClaw Browser 的区别：**
- Browser Relay：控制用户已有的 Chrome（需要安装扩展）
- OpenClaw Browser：OpenClaw 自带的专用浏览器

---

## 二、安装步骤

### 步骤1：安装扩展到稳定路径

```bash
npx openclaw browser extension install
npx openclaw browser extension path
```

输出路径：`~/.openclaw/browser/chrome-extension/`

### 步骤2：Chrome 加载扩展

1. 打开 Chrome → `chrome://extensions`
2. 启用 "Developer mode"（开发者模式）
3. 点击 "Load unpacked"（加载已解压的扩展）
4. 选择路径：`~/.openclaw/browser/chrome-extension/`
5. 固定扩展到工具栏

### 步骤3：启动 Chrome 并开启调试端口

**方法A：命令行启动**
```bash
open -a "Google Chrome" --args --remote-debugging-port=18792
```

**方法B：已有 Chrome 添加端口**
需要重启 Chrome 并添加启动参数

### 步骤4：操作用户的 Chrome（重要！）

**不要用 openclaw browser 命令！**

1. 先找到用户正在运行的 Chrome PID：
```bash
ps aux | grep "Google Chrome" | grep -v grep
```

2. 使用 osascript 操作用户当前已打开的 Chrome：
```bash
osascript -e 'tell application "Google Chrome" to open location "https://..."'
```

**为什么不用 openclaw browser**：
- openclaw browser 会创建新的 Chrome 进程（没有插件）
- 会遮挡用户窗口
- 没有 OpenClaw Browser Relay 插件

### 步骤5：配置扩展

1. 点击扩展图标 → 右键 → 选项 / Options
2. 填写配置：
   - **Gateway URL**: `http://127.0.0.1:18789`
   - **Gateway Token**: `235bf68c2288bfde322b8567509fb0e4d8eb368ec3c70000`
   - **Relay Port**: `18792`
3. 保存并刷新扩展

### 步骤5：连接测试

1. 点击扩展图标 → 应该显示 "Connected" 或绿色状态
2. 验证 CDP 可访问：
```bash
curl -s http://127.0.0.1:18792/json
```

---

## 三、关键配置信息

### 端口

| 服务 | 端口 | 说明 |
|------|------|------|
| Gateway HTTP | 18789 | OpenClaw 控制面板 |
| Browser Relay CDP | 18792 | Chrome 调试端口（需要认证） |

### Gateway Token

```
235bf68c2288bfde322b8567509fb0e4d8eb368ec3c70000
```

获取命令：`openclaw config get gateway.auth.token`

---

## 四、调优记录

### 问题1：MV3 Service Worker 30秒休眠

**问题描述：**
Chrome 扩展的 Service Worker (MV3) 在空闲 30 秒后会休眠，导致连接断开。

**解决方案：**
alarms (30秒) + WebSocket心跳 (25秒) 混合机制

**代码位置：**
`~/.openclaw/browser/chrome-extension/background.js`

**文档：**
`docs/browser-relay-keepalive.md`

---

## 五、故障排查

### 问题：/json 返回 Unauthorized

**原因**：Token 无效或过期

**解决**：
1. 打开扩展设置
2. 确认 Gateway Token 正确
3. 重新保存配置
4. 刷新扩展

### 问题：连接断开频繁

**解决**：
- 参考 `browser-relay-keepalive.md` 添加 keepalive 代码

---

## 六、验证命令

```bash
# 检查端口监听
lsof -i :18792

# 测试 HTTP 端点
curl -s http://127.0.0.1:18792/json

# 测试 Gateway
curl -s http://127.0.0.1:18789/

# 检查扩展连接状态
lsof -i :18792 | grep -v LISTEN
```

---

## 七、文件位置

- 扩展目录：`~/.openclaw/browser/chrome-extension/`
- Gateway 配置：`~/.openclaw/openclaw.json`
- 日志：`/tmp/openclaw/openclaw-YYYY-MM-DD.log`

---

## 八、相关文档

- `docs/browser-relay-config.md` - 配置指南
- `docs/browser-relay-keepalive.md` - Keepalive 优化方案
- `memory/2026-03-09.md` - 安装当天的工作日志

---

*最后更新：2026-03-10*
