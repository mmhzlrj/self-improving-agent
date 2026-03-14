# MiniMax MCP Server

一个基于 Model Context Protocol (MCP) 的服务器，集成 MiniMax API 提供网页搜索和图片理解功能。

## 功能

- **web_search**: 使用 Brave Search API 进行网页搜索
- **understand_image**: 使用 MiniMax Vision API 分析图片内容

## 环境要求

- Node.js >= 18.0.0

## 安装

```bash
cd minimax-mcp
npm install
```

## 配置

需要设置以下环境变量：

### 方式 1: 使用 .env 文件

创建 `.env` 文件：

```bash
# Brave Search API (免费额度: 每月 2000 次)
# 申请地址: https://brave.com/search/api/
BRAVE_SEARCH_API_KEY=your_brave_api_key

# MiniMax API
# 申请地址: https://platform.minimaxi.com/
MINIMAX_API_KEY=your_minimax_api_key
MINIMAX_GROUP_ID=your_minimax_group_id
```

### 方式 2: 环境变量

```bash
export BRAVE_SEARCH_API_KEY=your_brave_api_key
export MINIMAX_API_KEY=your_minimax_api_key
export MINIMAX_GROUP_ID=your_minimax_group_id
```

## API 密钥获取

### Brave Search API

1. 访问 [Brave Search API](https://brave.com/search/api/)
2. 注册账号
3. 免费额度: 每月 2000 次搜索

### MiniMax API

1. 访问 [MiniMax 开放平台](https://platform.minimaxi.com/)
2. 注册并完成认证
3. 创建 API Key 和 Group ID

## 运行

### 开发模式

```bash
npm run dev
```

### 生产模式

```bash
npm run build
npm start
```

## 在 OpenClaw 中使用

在 OpenClaw 配置中添加：

```json
{
  "mcpServers": {
    "minimax": {
      "command": "node",
      "args": ["/path/to/minimax-mcp/dist/index.js"],
      "env": {
        "BRAVE_SEARCH_API_KEY": "your_key",
        "MINIMAX_API_KEY": "your_key",
        "MINIMAX_GROUP_ID": "your_group_id"
      }
    }
  }
}
```

## 使用示例

### web_search

```json
{
  "name": "web_search",
  "arguments": {
    "query": "MiniMax API 文档",
    "count": 10
  }
}
```

### understand_image

```json
{
  "name": "understand_image",
  "arguments": {
    "image": "https://example.com/image.jpg",
    "prompt": "请描述这张图片的内容"
  }
}
```

或者使用 base64 图片：

```json
{
  "name": "understand_image",
  "arguments": {
    "image": "data:image/png;base64,iVBORw0KGgo...",
    "prompt": "图中有哪些文字?"
  }
}
```

## 注意事项

- `web_search` 功能需要 Brave Search API 密钥（免费额度足够个人使用）
- `understand_image` 功能需要 MiniMax API 密钥
- 图片支持 URL 和 base64 格式

## 许可证

MIT
