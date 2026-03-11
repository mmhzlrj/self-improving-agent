
# Browser Relay 扩展日志分析

## 时间
2026-03-10

## 日志内容

```
background.js:575 [TabQuery] 开始查询标签页（当前窗口+活动页）
background.js:577 [TabQuery] 查询结果： Object
background.js:624 attach failed Cannot access a chrome:// URL Error
  at nowStack (chrome-extension://mgemdfpfjcjhmaoakndbhehmjpaphncj/background.js:46:12)
  at connectOrToggleForActiveTab (chrome-extension://mgemdfpfjcjhmaoakndbhehmjpaphncj/background.js:624:46)
```

## 问题分析

### 问题1：标签页查询结果为空
```
查询结果： Object
```
- `chrome.tabs.query` 返回的是空对象或未定义的 tab 对象

### 问题2：无法访问 chrome:// URL
```
attach failed Cannot access a chrome:// URL Error
```

**根因**：
1. 当前活动的标签页可能是 "chrome://" 开头的 URL（如 chrome://newtab）
2. Chrome 扩展**没有权限**访问 chrome:// URL
3. 这是一个 Chrome 扩展的权限限制，不是代码 bug

## 解决方案

### 方案1：切换到非 chrome:// URL 的标签页
- 让用户切换到普通网页（如百度）作为活动标签页
- 然后再尝试连接

### 方案2：修改扩展代码
- 在 `attachTab` 之前检查 URL 是否为 chrome://
- 如果是，跳过或提示用户

### 方案3：使用其他方式
- 使用 osascript + CDP 结合的方式
