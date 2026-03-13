# 智库 5 平台测试方案

## 问题回顾
- subagent 启动新浏览器而不是连接 CDP 18800
- 不断打开新浏览器窗口，导致电脑乱动

## 正确方案

### 核心原则
1. **永远连接 CDP 18800**，不启动新浏览器
2. **复用已有页面**，不重复打开
3. **不派 subagents**，自己直接运行

### 技术方案

#### 步骤 1：检查 CDP 18800 是否可用
```javascript
const browser = await chromium.connectOverCDP('http://127.0.0.1:18800');
```

#### 步骤 2：复用已有页面
- 豆包: https://www.doubao.com/chat/
- Kimi: https://www.kimi.com/
- 智谱: https://chatglm.cn/
- DeepSeek: https://chat.deepseek.com/
- 千问: https://chat.qwen.ai/

#### 步骤 3：创建新对话
- Kimi/豆包: Command+K
- 千问/智谱/DeepSeek: 点击 + 按钮或刷新

#### 步骤 4：动态等待回复
- 轮询检测页面内容变化
- 不写死等待时间

#### 步骤 5：提取回复
- 尝试点击复制按钮
- 备选：innerText

### 实施方案

**选择 A：使用已有脚本**
- zhiku-s1-v2.js: 千问、智谱、Kimi
- zhiku-s2-v2.js: 豆包、DeepSeek

**选择 B：直接写一个简单的脚本**
- 一个脚本处理 5 个平台
- 自己运行，不用 subagent

---

## 待确认
1. 用哪个方案？（A 或 B）
2. 默认问题："用一句话介绍深圳"
