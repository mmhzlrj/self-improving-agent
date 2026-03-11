
# Browser Relay 最新测试报错

## 测试环境
- Chrome PID: 25037
- 使用临时 profile: /tmp/chrome-debug
- 启动命令: `open -a "Google Chrome" --args --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug`

## 测试结果

### 1. Chrome 原生 CDP (9222) - 成功
```bash
curl http://127.0.0.1:9222/json
```
返回:
```json
[{
  "description": "",
  "devtoolsFrontendUrl": "https://chrome-devtools-frontend.appspot.com/serve_rev/@662e0d7961bd91ebe77fe6c52f369e45647af51c/inspector.html?ws=127.0.0.1:9222/devtools/page/F607604DC05EA51E3317E716D75FB035",
  "id": "F607604DC05EA51E3317E716D75FB035",
  "title": "新标签页",
  "type": "page",
  "url": "chrome://newtab/",
  "webSocketDebuggerUrl": "ws://127.0.0.1:9222/devtools/page/F607604DC05EA51E3317E716D75FB035"
}]
```
✅ 正常工作

### 2. Browser Relay (18792) - 失败
```bash
curl http://127.0.0.1:18792/json?token=235bf68c2288bfde322b8567509fb0e4d8eb368ec3c70000
```
返回:
```
[]
```
❌ 返回空数组，没有返回标签页

### 3. 之前的测试（使用默认 profile + Browser Relay 扩展）
- 端口 18792 认证成功（Query 参数方式）
- 但 CDP 返回空数组

## 问题
Browser Relay 扩展已安装并连接，但 CDP 代理返回空数组，无法获取标签页列表。

## 之前成功的测试
- Query 参数认证: ✅ 成功（返回 `[]`，不是 401）
- Bearer Header: ❌ 401
- Basic 认证: ❌ 401
