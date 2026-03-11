# AI Platform Setup Skill

## 介绍
自动设置各大 AI 网页平台的模型模式（深度思考、专家模式等）。

## 使用方式

### 设置单个平台
```
/ai-platform-setup deepseek   # DeepSeek: 深度-platform-setup doubao思考
/ai     # 豆包: 专家模式
/ai-platform-setup qwen       # 千问: 思考模式
/ai-platform-setup glm        # 智谱: 思考+联网
/ai-platform-setup kimi      # Kimi: 思考模式
```

### 设置所有平台
```
/ai-platform-setup all
```

## 脚本位置
- 主脚本：`~/.openclaw/workspace/scripts/cdp-setup-v3.sh`

## 各平台功能对照

| 平台 | 设置的功能 | URL |
|------|-----------|-----|
| DeepSeek | 深度思考 | https://chat.deepseek.com/ |
| 豆包 | 专家模式 | https://www.doubao.com/chat/38416305792801026 |
| 千问 | 思考模式 | https://chat.qwen.ai/ |
| 智谱 | 思考+联网 | https://chatglm.cn/ |
| Kimi | 思考模式 | https://kimi.moonshot.cn/ |

## 技术原理

1. **Browser Relay CDP**：端口 18800 = Chrome DevTools Protocol 端口
2. **动态获取 ref**：用 `openclaw browser snapshot` 获取页面元素 ref
3. **点击设置**：解析 ref 后用 `openclaw browser click` 点击按钮
4. **自动导航**：all 模式下自动导航到各平台页面

## 依赖
- OpenClaw Gateway 运行中
- Browser Relay 插件已连接
- 各平台已登录
