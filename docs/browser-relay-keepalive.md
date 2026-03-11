# OpenClaw Browser Relay Keepalive 优化方案

## 问题背景

OpenClaw Browser Relay 使用 Chrome 扩展的 Service Worker (MV3) 来维护 WebSocket 连接。MV3 Service Worker 在空闲 30 秒后会休眠，导致连接断开。

**症状**：每 30-60 秒连接断开，需要重新点击扩展图标连接。

## 调研过程

### 1. 问豆包讨论方案

向豆包咨询：
- chrome.alarms 实际精度和 MV3 最小间隔
- 更稳定的 keepalive 方案
- OpenClaw Gateway 是否有内置 heartbeat

**豆包回复要点**：
- Chrome 120+：alarms 最小间隔 30 秒
- Chrome 稳定版：alarms 最小间隔 1 分钟
- 建议使用混合方案：alarms + WebSocket 心跳 + 状态持久化
- OpenClaw Gateway 无内置 heartbeat

### 2. 验证方案

测试发现的问题：
- 原始代码用 `fetch` 发送心跳 → CORS 错误（Service Worker 不能用 fetch）
- 改为 chrome.alarms 后仍会断开

## 解决方案

### 最终方案：alarms + WebSocket 心跳混合

| 机制 | 间隔 | 作用 |
|------|------|------|
| chrome.alarms | 30 秒 | 兜底唤醒 Service Worker |
| WebSocket ping | 25 秒 | 保持连接活跃 + 唤醒 SW |

### 代码修改

文件：`~/.openclaw/browser/chrome-extension/background.js`

在文件末尾添加：

```javascript
// ========== Service Worker Keepalive (MV3) ==========
// Keep the service worker alive using chrome.alarms + WebSocket heartbeat.
// MV3 service workers timeout after 30 seconds of inactivity.

const KEEPALIVE_ALARM_NAME = 'relay-keepalive'
const KEEPALIVE_INTERVAL_SEC = 30 // 30 seconds (Chrome 120+ minimum)
const WS_HEARTBEAT_INTERVAL_MS = 25000 // 25 seconds (less than 30s SW threshold)

let heartbeatInterval = null

function startKeepalive() {
  // 1. Create/update the alarm (triggers every 30 seconds)
  chrome.alarms.create(KEEPALIVE_ALARM_NAME, {
    delayInMinutes: KEEPALIVE_INTERVAL_SEC / 60,
    periodInMinutes: KEEPALIVE_INTERVAL_SEC / 60
  })
  
  // 2. Start WebSocket heartbeat if connected
  startWsHeartbeat()
}

function stopKeepalive() {
  chrome.alarms.get(KEEPALIVE_ALARM_NAME, (alarm) => {
    if (alarm) {
      chrome.alarms.clear(KEEPALIVE_ALARM_NAME)
    }
  })
  stopWsHeartbeat()
}

function startWsHeartbeat() {
  if (heartbeatInterval) {
    clearInterval(heartbeatInterval)
  }
  
  heartbeatInterval = setInterval(() => {
    if (relayWs && relayWs.readyState === WebSocket.OPEN) {
      try {
        relayWs.send(JSON.stringify({ method: 'ping' }))
        console.log('[Keepalive] WebSocket ping sent')
      } catch (err) {
        console.warn('[Keepalive] WebSocket ping failed:', err)
      }
    }
  }, WS_HEARTBEAT_INTERVAL_MS)
}

function stopWsHeartbeat() {
  if (heartbeatInterval) {
    clearInterval(heartbeatInterval)
    heartbeatInterval = null
  }
}

// Handle the alarm - this wakes up the service worker
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name !== KEEPALIVE_ALARM_NAME) return
  
  // Refresh badges to keep UI in sync
  for (const [tabId, tab] of tabs.entries()) {
    if (tab.state === 'connected') {
      const isConnected = relayWs && relayWs.readyState === WebSocket.OPEN
      setBadge(tabId, isConnected ? 'on' : 'connecting')
    }
  }
  
  console.log('[Keepalive] Alarm triggered, SW refreshed')
})

// Start keepalive when service worker starts
startKeepalive()

// Stop keepalive on shutdown
chrome.runtime.onSuspend.addListener(() => {
  stopKeepalive()
})
```

## 部署步骤（新 OpenClaw 环境复现）

### 1. 备份原文件
```bash
cp ~/.openclaw/browser/chrome-extension/background.js ~/.openclaw/browser/chrome-extension/background.js.bak
```

### 2. 编辑 background.js
```bash
# 使用任何编辑器打开文件
nano ~/.openclaw/browser/chrome-extension/background.js
# 或
vim ~/.openclaw/browser/chrome-extension/background.js
```

### 3. 在文件末尾添加 keepalive 代码
找到文件最后的 `return true` 后添加上面的代码。

### 4. 刷新 Chrome 扩展
1. 打开 Chrome → `chrome://extensions`
2. 找到 OpenClaw Browser Relay 扩展
3. 点击 **刷新按钮** 🔄

### 5. 测试验证
```bash
# 测试连接是否稳定（等待 60+ 秒）
sleep 60

# 用 browser 工具测试
browser(action=tabs, profile="chrome")
```

## 关键原理

### 为什么需要双重机制？

1. **chrome.alarms**
   - Chrome 120+ 最小精度约 30 秒
   - 只能保证"在指定时间附近"触发
   - 作为兜底机制

2. **WebSocket 心跳**
   - 每 25 秒发送一次 ping
   - 小于 SW 30 秒空闲阈值
   - 发送和接收消息都能唤醒 SW

### 为什么 30 秒 + 25 秒？

- SW 空闲 30 秒后休眠
- alarms 30 秒触发，但可能有延迟
- WebSocket 25 秒心跳作为双重保险

## 测试结果

| 测试 | 结果 |
|------|------|
| 35 秒后连接 | ✅ 稳定 |
| 60 秒后连接 | ✅ 稳定 |
| 发送消息 | ✅ 正常 |
| 豆包回复 | ✅ 正常 |

## 相关文件

- 扩展目录：`~/.openclaw/browser/chrome-extension/`
- 核心文件：`background.js`
- 备份：`background.js.bak.20260309`

## 参考资料

- Chrome MV3 Service Worker 文档
- 豆包 AI 搜索结果（2026-03-09）
- OpenClaw 源码分析

## 更新日志

- **2026-03-09**：初始版本，添加 alarms + WebSocket 心跳混合方案
