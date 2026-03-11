
# Browser Relay 修复计划（豆包提供）

## 核心问题复盘

| 问题类型 | 影响程度 | 优先级 |
|-------------------------|----------|--------|
| 无 CDP 请求/标签页日志 | 无法定位失败原因 | 最高 |
| 标签页查询仅返回活动页 | 列表不完整 | 高 |
| Target.createTarget 失败 | 核心功能异常 | 高 |
| 不支持 HTTP /json API | 兼容性问题 | 中 |

---

## 下一步行动

### 🔴 第一步：补充日志（最高优先级）

需要在扩展代码中添加日志：

1. **handleForwardCdpCommand 函数**（Target.createTarget 分支，约第 439-448 行）：
```javascript
if (method === 'Target.createTarget') {
  console.log('[CDP] 收到创建标签页请求：', { method, params });
  try {
    const url = typeof params?.url === 'string' ? params.url : 'about:blank'
    const tab = await chrome.tabs.create({ url, active: false })
    console.log('[CDP] 标签页创建结果：', tab);
    if (!tab.id) throw new Error('tab.id 为空，创建失败')
    
    await new Promise((r) => setTimeout(r, 100))
    const attached = await attachTab(tab.id)
    console.log('[CDP] 标签页连接结果：', attached);
    return { targetId: attached.targetId }
  } catch (e) {
    console.error('[CDP] 创建/连接标签页失败：', e.message, e.stack);
    throw e;
  }
}
```

2. **connectOrToggleForActiveTab 函数**（约第 357 行）：
```javascript
console.log('[TabQuery] 开始查询标签页（当前窗口+活动页）');
const [active] = await chrome.tabs.query({ active: true, currentWindow: true })
console.log('[TabQuery] 查询结果：', active);
```

### 🟠 第二步：修复标签页查询逻辑

```javascript
// 原代码（仅查活动页）
const [active] = await chrome.tabs.query({ active: true, currentWindow: true })

// 方案1：查询当前窗口所有标签页（推荐）
const allTabsInCurrentWindow = await chrome.tabs.query({ currentWindow: true });

// 方案2：查询所有窗口的所有标签页
const allTabs = await chrome.tabs.query({});
```

### 🟡 第三步：排查 Target.createTarget 失败问题

1. 若 tab.id 为空：检查 URL 参数合法性
2. 若 attachTab 失败：检查权限和连接逻辑
3. 确认 manifest.json 包含权限：
```json
{
  "permissions": ["tabs", "debugger", "activeTab", "scripting"]
}
```

### 🟢 第四步：（可选）支持 HTTP /json API

### 🟣 第五步：回归测试

---

## 相关文件
- `/Users/lr/.openclaw/browser/chrome-extension/background.js` - 扩展代码
