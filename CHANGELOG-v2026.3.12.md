# v2026.3.12 版本更新记录

**发布日期**: 2026-03-13
**更新时间**: 13:12 GMT+8

## 🎯 新增功能

### MCP Client 浏览器控制 (重大更新)
- **插件**: openclaw-mcp-adapter (来自 https://github.com/androidStern-personal/openclaw-mcp-adapter)
- **版本**: 0.1.1
- **MCP 服务器**: @playwright/mcp
- **安装方式**: 本地安装 (openclaw plugins install /tmp/package)

#### 新增工具 (11个)
| 工具名 | 功能 |
|--------|------|
| playwright_browser_navigate | 导航到URL |
| playwright_browser_snapshot | 获取页面快照 |
| playwright_browser_click | 点击元素 |
| playwright_browser_type | 输入文本 |
| playwright_browser_select_option | 选择下拉框 |
| playwright_browser_hover | 悬停元素 |
| playwright_browser_drag | 拖拽元素 |
| playwright_browser_take_screenshot | 截屏 |
| playwright_browser_network_requests | 网络请求 |
| playwright_browser_run_code | 运行代码 |
| playwright_browser_tabs | 管理标签页 |
| playwright_browser_wait_for | 等待元素 |

#### 配置内容
```json
{
  "plugins": {
    "entries": {
      "openclaw-mcp-adapter": {
        "enabled": true,
        "config": {
          "servers": [
            {
              "name": "playwright",
              "transport": "stdio",
              "command": "npx",
              "args": ["-y", "@playwright/mcp"]
            }
          ]
        }
      }
    }
  }
}
```

## 🔧 其他更新

- 清理了 stale 的 openclaw-mcp 配置项

## ⚠️ 注意事项

- MCP 适配器通过 stdio 启动 npx @playwright/mcp
- Playwright MCP 会启动独立的 Chrome 实例（不是用现有的 Browser Relay）
- Gateway 必须重启才能加载新插件

## 📝 备份记录

关键配置文件位置:
- `~/.openclaw/openclaw.json` - 主配置
- `~/.openclaw/extensions/openclaw-mcp-adapter/` - 插件源码
- `~/.openclaw/backup/golden/openclaw.json` - Golden 备份
