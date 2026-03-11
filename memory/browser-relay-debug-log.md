
# Browser Relay 调试完整记录

> **⚠️ 本文已过时，请查看最新文档：**
> - `/Users/lr/.openclaw/workspace/memory/browser-relay-fix-update.md` - 问题分析和修复进展
> - `/Users/lr/.openclaw/workspace/memory/browser-relay-log-analysis.md` - 日志分析

## 调试时间
2026-03-10

## 问题描述
Browser Relay 扩展无法控制用户的 Chrome 浏览器

---

## 一、问题核心分析

从现状来看，**TCP 连接层已打通（端口 18792 双向 ESTABLISHED），但应用层（CDP 协议+鉴权）存在核心故障**，具体可拆解为 3 个关键维度：

1. **CDP 代理链路异常**：Browser Relay 扩展未正确转发 Chrome 原生 CDP 指令/响应
2. **鉴权机制不匹配**：CDP 端点的 Token 鉴权方式（如参数位置、格式）与实际请求不一致，导致 401 Unauthorized
3. **Gateway 数据转发阻塞**：/extension WebSocket 端点虽认证成功，但未正确转发/解析 CDP 数据

---

## 二、详细解决步骤

### 阶段 1：验证基础通路

#### 步骤 1.1 绕过 Relay，验证 Chrome 原生 CDP 可用性

**操作**：
```bash
# 关闭当前 Chrome
pkill -9 -f "Google Chrome"

# 重启 Chrome 并开启原生 CDP 调试（使用临时 profile 测试）
open -a "Google Chrome" --args --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug

# 测试原生 CDP 端点
curl http://127.0.0.1:9222/json
```

**结果**：✅ 成功
```json
[{
  "description": "",
  "devtoolsFrontendUrl": "https://chrome-devtools-frontend.appspot.com/...",
  "id": "F607604DC05EA51E3317E716D75FB035",
  "title": "新标签页",
  "type": "page",
  "url": "chrome://newtab/",
  "webSocketDebuggerUrl": "ws://127.0.0.1:9222/devtools/page/F607604DC05EA51E3317E716D75FB035"
}]
```

**结论**：Chrome 自身 CDP 配置正常

---

#### 步骤 1.2 验证 Token 有效性与鉴权方式

**测试命令与结果**：

| 鉴权方式 | 命令 | 结果 |
|----------|------|------|
| Query 参数 | `curl http://127.0.0.1:18792/json?token=235bf68c2288bfde322b8567509fb0e4d8eb368ec3c70000` | ✅ 返回 `[]` (认证成功) |
| Bearer Header | `curl -H "Authorization: Bearer <token>"` | ❌ 401 Unauthorized |
| Basic 认证 | `curl -u token:<token>` | ❌ 401 Unauthorized |

**结论**：Query 参数方式认证成功

---

### 阶段 2：关键发现

#### 发现 1：Chrome 原生 CDP 端口未开启

- 问题：Browser Relay 需要 Chrome 原生 CDP (9222) 才能工作
- 解决：启动 Chrome 时需要同时开启 9222 和 18792 端口

#### 发现 2：使用默认 profile + 扩展时的问题

- 测试时用临时 profile 没有 Browser Relay 扩展
- 需要使用默认 profile 并确保扩展已安装

---

### 阶段 3：最终解决方案

#### 操作步骤

1. **关闭当前 Chrome**
```bash
pkill -9 -f "Google Chrome"
```

2. **用默认 profile 重启 Chrome**
```bash
open -a "Google Chrome"
```

3. **确保 Browser Relay 扩展已安装并切换到 On**

4. **测试 CDP 端点**
```bash
curl "http://127.0.0.1:18792/json?token=235bf68c2288bfde322b8567509fb0e4d8eb368ec3c70000"
```

#### 最终结果 ✅

```json
[{
  "id": "B1B8C07160D4FD846671B5D0D8EF4934",
  "type": "page",
  "title": "OpenClaw Control",
  "description": "OpenClaw Control",
  "url": "http://127.0.0.1:18789/chat?session=agent%3Amain%3Amain",
  "webSocketDebuggerUrl": "ws://127.0.0.1:18792/cdp",
  "devtoolsFrontendUrl": "/devtools/inspector.html?ws=127.0.0.1:18792/cdp"
}]
```

**Browser Relay 可以正常工作了！**

---

## 三、根因分析

**问题根源**：

1. Chrome 启动时需要开启原生 CDP 端口 (9222)
2. Browser Relay 扩展依赖 Chrome 原生 CDP 来代理请求
3. 如果只开启 18792 端口，扩展无法正常工作

**解决方案**：

在默认 profile 中使用 Browser Relay 扩展时，需要：
1. 确保扩展已安装并切换到 On
2. Chrome 会自动开启必要的 CDP 端口

---

## 四、预防措施

1. **不要使用 openclaw browser 命令**：会创建没有插件的新 Chrome
2. **使用 osascript 操作用户的 Chrome**：先找到 Chrome PID，再用 osascript
3. **确认 Browser Relay 状态**：每次使用前确认扩展已切换到 On
4. **记录关键端口**：
   - 18789: Gateway
   - 18792: Browser Relay CDP (需要认证)
   - 9222: Chrome 原生 CDP (临时测试用)

---

## 五、相关文件

- `docs/browser-relay-config.md` - 配置指南
- `docs/browser-relay-full-guide.md` - 从0到1完整指南
- `memory/browser-relay-issue-summary.md` - 问题总结
- `memory/browser-relay-debug-log.md` - 调试日志
- `memory/browser-relay-error.md` - 错误记录

---

## 六、后续工作

- [ ] 测试通过 Browser Relay 创建新标签页
- [ ] 测试通过 Browser Relay 读取网页内容
- [ ] 测试通过 Browser Relay 执行 JavaScript
- [ ] 记录完整的操作流程到文档
