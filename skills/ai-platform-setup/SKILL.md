# AI Platform Setup Skill

## 介绍
自动设置各大 AI 网页平台的模型模式，并支持一键群发问题。

## 使用方式

### 方式一：设置模式（不发送问题）

```bash
# 设置单个平台
~/.openclaw/workspace/scripts/cdp-setup-v3.sh deepseek   # 深度思考
~/.openclaw/workspace/scripts/cdp-setup-v3.sh doubao     # 专家模式
~/.openclaw/workspace/scripts/cdp-setup-v3.sh qwen       # 思考模式
~/.openclaw/workspace/scripts/cdp-setup-v3.sh glm        # 思考+联网
~/.openclaw/workspace/scripts/cdp-setup-v3.sh kimi       # 思考模式

# 设置所有平台
~/.openclaw/workspace/scripts/cdp-setup-v3.sh all
```

### 方式二：智库问答（设置 + 群发）

```bash
~/.openclaw/workspace/scripts/zhiku.sh "你的问题"
```

**示例**：
```bash
~/.openclaw/workspace/scripts/zhiku.sh "什么是openclaw？"
```

**工作流程**：
1. 自动设置所有平台的模式（深度思考/专家/思考等）
2. 自动向 5 个平台发送问题
3. 显示平台列表，供你查看回复

## 各平台功能对照

| 平台 | 高级模式 | URL |
|------|----------|-----|
| DeepSeek | 深度思考 + 智能搜索 | https://chat.deepseek.com/ |
| 豆包 | 专家模式 | https://www.doubao.com/chat/ |
| 千问 | 默认 | https://chat.qwen.ai/ |
| 智谱 | 思考 + 联网 | https://chatglm.cn/ |
| Kimi | 思考模式 | https://www.kimi.com/ |

## 脚本位置

| 脚本 | 功能 |
|------|------|
| `cdp-setup-v3.sh` | 设置平台模式 |
| `cdp-broadcast.sh` | 群发问题 |
| `zhiku.sh` | 智库问答（设置+群发）|

## 前置条件

1. **Gateway 运行中**：确保 OpenClaw Gateway 正常运行
2. **Browser Relay 已连接**：Chrome 插件已连接
3. **各平台已登录**：AI 网页版已登录账号
