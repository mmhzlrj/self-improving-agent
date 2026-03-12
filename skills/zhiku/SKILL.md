# 智库 Skill

## 介绍
通过 CDP 后台模式同时向 5 个国产 AI 平台提问并收集回复。

## 脚本位置

| 脚本 | 功能 |
|------|------|
| `scripts/zhiku-s1-v2.js` | subagent1：提问智谱、千问、Kimi |
| `scripts/zhiku-s2-v2.js` | subagent2：提问豆包、DeepSeek，收集智谱 |

## 使用方式

```bash
# 先运行 s1（先提问智谱）
node ~/.openclaw/workspace/scripts/zhiku-s1-v2.js "问题" &

# 3秒后运行 s2
sleep 3 && node ~/.openclaw/workspace/scripts/zhiku-s2-v2.js "问题"
```

## 各平台高级模式

| 平台 | 高级模式 | 新建对话方式 |
|------|----------|--------------|
| 豆包 | 专家模式 | Command+K |
| Kimi | 思考模式 | Command+K |
| DeepSeek | 深度思考 + 智能搜索 | page.goto() |
| 千问 | 默认 | page.goto() |
| 智谱 | 思考 + 联网 | page.goto() |

## 提问顺序

**s1 (先启动)**：
1. 提问智谱（不用等回复，立刻继续）
2. 提问千问
3. 提问 Kimi
4. 收集豆包回复
5. 收集 DeepSeek 回复

**s2 (后启动)**：
1. 提问豆包
2. 提问 DeepSeek
3. 收集千问回复
4. 收集 Kimi 回复
5. 收集智谱回复（等回复时间最长，放最后）

## 等待策略

- 轮询等待：每 10 秒检查一次
- 最大等待：60 秒（6 次轮询）
- **检测完成：检查页面是否有复制按钮出现，有则代表回答完成**

## 工作流程

1. CDP 连接 Browser Relay (`http://127.0.0.1:18800`)
2. 复用已有页面，不打开新窗口
3. 创建新对话避免缓存
4. 提问并等待回复
5. 用复制按钮或 innerText 获取内容

## 注意事项

- CDP 连接正常时不要改用非 headless 模式
- 遇到问题先问用户有没有手动干预
- 确保页面加载完成后再提问
