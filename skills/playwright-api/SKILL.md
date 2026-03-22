# Playwright 完整 API 参考

> 本文档从 Playwright v1.57 源码提取，涵盖 **500+ 个 API 方法**，按功能模块分类整理。
> 
> **当你需要用 Playwright 时，先读这个文档找到正确的 API，再去执行。**
> 
> 文档路径：`~/.openclaw/workspace/skills/playwright-api/SKILL.md`
> Playwright 源码：`~/.openclaw/extensions/playwright-mcp-server/node_modules/playwright-core/types/types.d.ts`

---

## ⚡ 快速索引

| 需求 | 用这个类 | 关键方法 |
|------|---------|---------|
| 打开网页 | `Page` | `goto()`, `setContent()` |
| 等待元素 | `Page` / `Locator` | `waitForSelector()`, `waitForLoadState()` |
| 点击/填表 | `Locator` | `click()`, `fill()`, `type()`, `select()` |
| 执行 JS | `Page` / `Frame` | `evaluate()` |
| 截屏/导出 | `Page` | `screenshot()`, `pdf()`, `saveAsPDF()` |
| 监听事件 | `Page` | `on()`, `once()`, `addListener()` |
| 操作 Cookie | `BrowserContext` | `cookies()`, `addCookies()`, `clearCookies()` |
| 拦截请求 | `BrowserContext` | `route()`, `unroute()` |
| 网络请求 | `APIRequestContext` | `get()`, `post()`, `fetch()` |
| 键盘/鼠标 | `Keyboard`, `Mouse` | `press()`, `click()`, `type()` |
| 截图元素 | `Locator` | `screenshot()` |
| iframe 操作 | `FrameLocator` | `frameLocator()` |
| 等待时间 | `Page` | `waitForTimeout()` |
| 弹窗处理 | `Dialog` | `accept()`, `dismiss()` |
| 文件上传 | `Page` | `setInputFiles()` |
| 文件下载 | `Download` | `path()`, `saveAs()` |

---

## 🧭 Playwright 启动与连接

### 连接已有 Chrome（CDP）

```javascript
// 通过 WS URL 连接
const { chromium } = require('playwright');
const browser = await chromium.connectOverCDP('ws://127.0.0.1:9223/devtools/browser/...');

// 获取页面
const page = browser.contexts()[0].pages()[0];
```

### 启动新浏览器

```javascript
const browser = await chromium.launch({ headless: false });
const page = await browser.newPage();
```

---

## 一、Page 类（544 个方法）

> 页面操作的核心类。几乎所有页面交互都通过 Page 对象。

### 页面导航

```javascript
page.goto(url, options)           // 导航到 URL
page.reload(options)              // 刷新页面
page.goBack(options)              // 后退
page.goForward(options)           // 前进
page.setContent(html)            // 直接设置 HTML 内容
page.close()                     // 关闭页面
```

### 等待

```javascript
page.waitForSelector(selector, options)         // 等待元素出现
page.waitForLoadState(state, options)            // 等待加载状态 ('load'|'domcontentloaded'|'networkidle')
page.waitForURL(url, options)                    // 等待 URL 变化
page.waitForFunction(fn, arg, options)           // 等待函数返回 true
page.waitForTimeout(ms)                          // 等待固定时间
page.waitForRequest(url, options)                // 等待请求
page.waitForResponse(url, options)               // 等待响应
page.waitForEvent(event)                         // 等待事件
```

### 元素查询

```javascript
page.locator(selector)              // 获取定位器（推荐）
page.$(selector)                     // 查询单个元素（ElementHandle）
page.$$(selector)                    // 查询所有元素
page.getByRole(role, options)        // 按 ARIA role 查找
page.getByText(text, options)        // 按文本查找
page.getByLabel(text, options)       // 按 label 查找
page.getByPlaceholder(text)          // 按 placeholder 查找
page.getByTestId(testId)             // 按 testId 查找
page.frame(nameOrFrame)              // 获取 iframe
page.frameLocator(selector)          // 获取 FrameLocator
```

### 元素操作

```javascript
page.click(selector, options)                 // 点击
page.dblclick(selector, options)              // 双击
page.rightClick(selector, options)           // 右键
page.fill(selector, value, options)           // 填充输入框
page.type(selector, text, options)            // 逐字输入
page.press(selector, key, options)            // 按键
page.check(selector, options)                 // 勾选 checkbox
page.uncheck(selector, options)               // 取消勾选
page.selectOption(selector, values, options)   // 下拉选择
page.setInputFiles(selector, files, options)    // 文件上传
page.focus(selector, options)                 // 聚焦
page.blur(selector, options)                  // 失焦
page.hover(selector, options)                 // 悬停
page.tap(selector, options)                   // 触屏 tap
page.dragAndDrop(from, to, options)           // 拖拽
```

### JavaScript 执行

```javascript
page.evaluate(fn, arg)              // 在页面执行 JS，返回结果
page.evaluateHandle(fn, arg)         // 执行 JS，返回 JSHandle
page.addScriptTag(content)          // 注入 script 标签
page.addStyleTag(content)           // 注入 style 标签
page.exposeFunction(name, fn)       // 暴露函数到 window
page.exposeBinding(name, fn)        // 暴露 binding 到 window
```

### 截图/导出

```javascript
page.screenshot(options)             // 截屏
page.saveAsPDF(options)             // 保存为 PDF
page.pdf(options)                    // 生成 PDF（返回 Buffer）
page.fullPageScreenshot()            // 整页截图（旧 API）
```

### 内容获取

```javascript
page.title()                         // 获取标题
page.url()                           // 获取 URL
page.content()                        // 获取完整 HTML
page.innerText(selector)             // 获取元素内文本
page.innerHTML(selector)             // 获取元素内 HTML
page.textContent(selector)           // 获取文本内容
page.getAttribute(selector, name)    // 获取属性
page.inputValue(selector)            // 获取输入框值
```

### 元素状态判断

```javascript
page.isChecked(selector)            // checkbox 是否勾选
page.isDisabled(selector)            // 是否禁用
page.isEditable(selector)            // 是否可编辑
page.isEnabled(selector)             // 是否启用
page.isHidden(selector)              // 是否隐藏
page.isVisible(selector)            // 是否可见
```

### 键盘操作

```javascript
page.keyboard.down(key)             // 按下键
page.keyboard.up(key)               // 松开键
page.keyboard.press(key)            // 按一次
page.keyboard.type(text)            // 输入文本
page.keyboard.insertText(text)      // 插入文本（绕过输入法）
```

### 鼠标操作

```javascript
page.mouse.click(x, y, options)      // 点击
page.mouse.dblclick(x, y, options)  // 双击
page.mouse.move(x, y, options)       // 移动
page.mouse.down(options)             // 按下
page.mouse.up(options)               // 松开
page.mouse.wheel(deltaX, deltaY)    // 滚轮
```

### 触屏操作

```javascript
page.touchscreen.tap(x, y)          // 触屏点击
```

### 弹窗/文件选择

```javascript
page.on('dialog', async dialog => {   // 监听对话框
  await dialog.accept(text)          // 接受
  await dialog.dismiss()             // 拒绝
  await dialog.message()             // 获取消息
  await dialog.defaultValue()        // 获取默认值
})

page.on('filechooser', async chooser => {
  await chooser.setFiles(files)      // 选择文件
})

page.on('popup', async page => {      // 监听弹窗
  await page.goto('...')
})
```

### 请求拦截

```javascript
page.route(url, handler)             // 拦截请求
page.routeFromHar(har)               // 从 HAR 重放
page.unroute(url, handler)            // 取消拦截
page.request                          // APIRequestContext 实例
```

### 网络响应

```javascript
page.on('request', req => {})         // 请求发出
page.on('response', res => {})         // 收到响应
page.on('requestfinished', req => {})  // 请求完成
page.on('requestfailed', req => {})   // 请求失败
```

### 事件监听

```javascript
page.on(event, handler)               // 监听事件
page.once(event, handler)            // 只监听一次
page.addListener(event, handler)      // 添加监听
page.removeListener(event, handler)   // 移除监听
page.removeAllListeners()             // 移除所有监听
```

**常用 Page 事件：**
```
'close' | 'console' | 'crash' | 'dialog' | 'domcontentloaded'
'download' | 'filechooser' | 'frameattached' | 'framedetached'
'framenavigated' | 'load' | 'pageerror' | 'popup' | 'request'
'requestfailed' | 'requestfinished' | 'response' | 'websocket' | 'worker'
```

---

## 二、Locator 类（220 个方法）

> 元素定位器，是新版 Playwright 推荐的主要交互方式。
> Locator 会自动等待元素就绪，比 ElementHandle 更可靠。

### 创建

```javascript
page.locator(selector)               // CSS/XPath 选择器
page.getByRole(role, options)        // ARIA role
page.getByText(text, options)         // 文本
page.getByLabel(text, options)        // label
page.getByPlaceholder(text)           // placeholder
page.getByAltText(text)              // alt 属性
page.getByTitle(text)                // title 属性
page.getByTestId(testId)             // data-testid
```

### 链式查询

```javascript
locator.filter(options)             // 过滤
locator.and(locator)                 // 同时满足
locator.or(locator)                  // 满足任一
locator.frameLocator(selector)       // 在 locator 内找 iframe
locator.nth(index)                   // 第 N 个
locator.first()                      // 第一个
locator.last()                       // 最后一个
```

### 操作方法

```javascript
locator.click(options)               // 点击
locator.dblclick(options)             // 双击
locator.rightClick(options)          // 右键
locator.fill(value)                  // 填入
locator.type(text, options)          // 逐字输入
locator.press(key, options)          // 按键
locator.check(options)               // 勾选
locator.uncheck(options)             // 取消勾选
locator.selectOption(values, options) // 选择
locator.setInputFiles(files, options)// 文件
locator.focus()                      // 聚焦
locator.blur()                       // 失焦
locator.hover(options)               // 悬停
locator.tap(options)                 // 触屏
locator.scrollIntoViewIfNeeded()     // 滚动到可见
```

### 等待方法

```javascript
locator.waitFor(options)             // 等待元素
locator.isVisible(options)            // 是否可见
locator.isHidden(options)             // 是否隐藏
locator.isEnabled(options)            // 是否启用
locator.isDisabled(options)           // 是否禁用
locator.isChecked(options)            // 是否勾选
locator.isEditable(options)           // 是否可编辑
locator.isFocused(options)            // 是否聚焦
```

### 内容获取

```javascript
locator.textContent(options)         // 文本内容
locator.innerText(options)           // 内联文本
locator.innerHTML(options)           // 内 HTML
locator.getAttribute(name, options)   // 属性值
locator.inputValue(options)          // 输入值
locator.allTextContents()            // 所有文本（含隐藏）
locator.allInnerTexts()             // 所有内联文本
```

### 断言辅助

```javascript
locator.toBeVisible()                 // 可见
locator.toBeHidden()                  // 隐藏
locator.toBeEnabled()                 // 启用
locator.toBeDisabled()                // 禁用
locator.toBeChecked()                 // 勾选
locator.toHaveText(text)              // 有某文本
locator.toHaveCount(count)            // 数量
locator.toHaveValue(value)             // 有某值
```

---

## 三、BrowserContext 类（365 个方法）

> 浏览器上下文，类似于独立的浏览器配置。
> 每个 Context 有独立的 Cookie、存储、代理设置。

### 创建

```javascript
const context = await browser.newContext(options)
const page = await context.newPage()
```

### Cookie 管理

```javascript
context.cookies(urls)                 // 获取 cookies
context.addCookies(cookies)           // 添加 cookies
context.clearCookies()                // 清除 cookies
context.addInitScript(script)         // 注入初始化脚本
```

### 权限/地理位置

```javascript
context.grantPermissions(permissions, options)  // 授予权限
context.clearPermissions()             // 清除权限
context.setGeolocation(geolocation)    // 设置地理位置
context.setExtraHTTPHeaders(headers)   // 设置请求头
context.setOffline(offline)            // 设置离线模式
```

### 请求拦截

```javascript
context.route(url, handler)            // 拦截请求
context.routeFromHar(har)             // 从 HAR 重放
context.unroute(url, handler)          // 取消拦截
```

### 页面管理

```javascript
context.newPage()                      // 新建页面
context.pages()                        // 所有页面
context.close()                        // 关闭上下文
context.browser()                      // 所属 browser
```

### CDP 会话

```javascript
context.newCDPSession(page)            // 创建 CDP 会话
context.newBrowserCDPSession()         // 浏览器级 CDP
```

### 存储

```javascript
context.storageState()                 // 获取存储状态
context.addInitScript(script)         // 初始化脚本
context.rectangle()                   // 窗口矩形
```

---

## 四、Browser 类（270 个方法）

> 浏览器实例管理。

### 创建

```javascript
await chromium.launch(options)         // 启动
await chromium.connect(wsEndpoint)    // 连接已有
await chromium.connectOverCDP(cdpUrl) // CDP 连接
```

### 上下文

```javascript
browser.newContext(options)            // 新建上下文
browser.contexts()                      // 所有上下文
browser.browserType()                  // 浏览器类型
```

### 其他

```javascript
browser.close()                        // 关闭
browser.isConnected()                   // 是否连接
browser.version()                      // 版本
browser.stopTracing()                  // 停止追踪
```

---

## 五、Frame 类（379 个方法）

> iframe 操作。与 Page API 基本一致。

```javascript
frame.goto(url, options)              // 导航
frame.locator(selector)               // 定位器
frame.$(selector)                     // 查询元素
frame.$$(selector)                    // 查询所有
frame.evaluate(fn, arg)              // 执行 JS
frame.content()                        // 获取 HTML
frame.title()                         // 标题
frame.url()                           // URL
frame.parentFrame()                   // 父 frame
frame.childFrames()                  // 子 frames
frame.waitForSelector(selector)       // 等待
frame.waitForTimeout(ms)              // 等待
frame.isDetached()                   // 是否已分离
```

---

## 六、APIRequestContext 类（115 个方法）

> HTTP API 测试，不需要浏览器。

### 请求方法

```javascript
context.get(url, options)             // GET 请求
context.post(url, options)            // POST 请求
context.put(url, options)            // PUT 请求
context.patch(url, options)          // PATCH 请求
context.delete(url, options)          // DELETE 请求
context.fetch(url, options)          // 通用 fetch
```

### 响应

```javascript
response.ok()                        // 是否成功
response.status()                     // 状态码
response.statusText()                 // 状态文本
response.headers()                    // 响应头
response.headerValue(name)            // 特定头
response.body()                       // 响应体（Buffer）
response.text()                       // 响应体（文本）
response.json()                      // 响应体（JSON）
response.url()                        // 请求 URL
```

### 请求配置

```javascript
// options 常用参数
{
  headers: {},         // 请求头
  params: {},          // URL 参数
  data: {},            // POST 数据
  json: {},            // JSON 数据
  formData: {},        // 表单数据
  timeout: 30000,      // 超时
  ignoreHTTPSErrors: true  // 忽略证书错误
}
```

---

## 七、Keyboard 类

```javascript
keyboard.down(key)                   // 按下
keyboard.up(key)                     // 松开
keyboard.press(key)                  // 按一次
keyboard.type(text)                   // 输入
keyboard.insertText(text)            // 插入（绕过输入法）
```

---

## 八、Mouse 类

```javascript
mouse.click(x, y, options)           // 点击
mouse.dblclick(x, y, options)       // 双击
mouse.move(x, y, options)            // 移动
mouse.down(options)                   // 按下
mouse.up(options)                     // 松开
mouse.wheel(deltaX, deltaY)         // 滚轮
```

---

## 九、其他重要 API

### Dialog 对话框

```javascript
dialog.accept(promptText)            // 接受（可填提示文本）
dialog.dismiss()                      // 拒绝
dialog.message()                      // 消息文本
dialog.defaultValue()                 // 默认值
dialog.type()                         // 类型
```

### Download 下载

```javascript
download.path()                       // 文件路径（下载完成后）
download.saveAs(path)                 // 保存到
download.cancel()                      // 取消
download.delete()                     // 删除
download.url()                        // 下载 URL
download.suggestedFilename()          // 建议文件名
download.failure()                    // 失败原因
download.createReadStream()           // 流式读取
```

### FileChooser 文件选择

```javascript
chooser.setFiles(files, options)     // 设置文件
chooser.element()                     // 对应元素
chooser.isMultiple()                  // 是否多选
```

### ConsoleMessage 控制台

```javascript
msg.type()                           // 类型
msg.text()                           // 文本
msg.args()                           // 参数
msg.location()                       // 位置
```

### WebSocket

```javascript
ws.waitForEvent(event)               // 等待事件
ws.url()                             // URL
ws.isClosed()                        // 是否关闭
```

### Worker

```javascript
worker.evaluate(fn)                   // 执行 JS
worker.url()                         // URL
```

---

## 🔧 常用场景模板

### 连接 Chrome 并操作

```javascript
const { chromium } = require('playwright');

// 找到 Chrome WS URL
// curl http://127.0.0.1:9223/json/version

const browser = await chromium.connectOverCDP('ws://127.0.0.1:9223/...');
const page = browser.contexts()[0].pages().find(p => p.url().includes('target'));

// 操作
await page.goto('https://example.com');
await page.locator('input[name="q"]').fill('search term');
await page.keyboard.press('Enter');
```

### 截取页面元素

```javascript
const element = page.locator('#my-element');
const screenshot = await element.screenshot({ path: 'element.png' });
```

### 等待网络请求

```javascript
const [response] = await Promise.all([
  page.waitForResponse('**/api/data'),
  page.click('#load-data-btn')
]);
const json = await response.json();
```

### 文件上传

```javascript
await page.setInputFiles('input[type="file"]', '/path/to/file.pdf');
```

### 拦截并修改响应

```javascript
await page.route('**/api/**', async route => {
  const response = await route.fetch();
  const body = await response.json();
  body.modified = true;
  await route.fulfill({ response, body: JSON.stringify(body) });
});
```

### 新标签页操作

```javascript
const [popup] = await Promise.all([
  page.waitForEvent('popup'),
  page.click('a[target="_blank"]')
]);
await popup.goto('...');
```

---

## ⚠️ 重要原则

1. **用 Locator 而不是 ElementHandle** — Locator 自动等待，更可靠
2. **用 `page.locator().click()` 而不是 `page.click()`** — 前者更稳定
3. **连接已有 Chrome 用 CDP** — 不要 launch 新浏览器
4. **先等待再操作** — 用 `waitForSelector` 确保元素存在
5. **断开后记得关闭** — `browser.close()`
6. **跨域用 `page.evaluate`** — 浏览器内的 JS 才能跨域

---

*本文档从 Playwright v1.57 源码自动提取*
*Source: `~/.openclaw/extensions/playwright-mcp-server/node_modules/playwright-core/types/types.d.ts`*
