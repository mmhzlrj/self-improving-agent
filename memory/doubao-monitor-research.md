# 豆包对话精细化监测与多AI交叉验证方案

## 一、豆包页面状态分析

### 1.1 关键元素识别

| 元素 | ref | 说明 |
|------|-----|------|
| 输入框 | e1397 | 豆包主输入框，发送后状态会变化 |
| 用户消息 | e1729 | 用户发送的问题（动态ref） |
| AI回复 | e1754 | AI回复内容（生成完成后出现） |
| 回复操作按钮 | e1758,e1763... | 复制、反馈等按钮 |
| 追问建议 | e1797 | 生成完成后出现的追问选项 |

### 1.2 状态检测方法

**生成中状态特征：**
- 输入框(e1397)内容已清空
- 用户消息已显示
- 但还没有AI回复内容出现

**生成完成状态特征：**
- AI回复内容已出现（ref=e1754带文字内容）
- 或追问建议出现（ref=e1797有子元素）
- 回复操作按钮出现

### 1.3 检测策略

```javascript
// 检测生成状态的JavaScript代码（可注入到页面）
function checkGenerationStatus() {
  // 1. 检查是否有最新回复
  const messages = document.querySelectorAll('[class*="message"]');
  const lastMessage = messages[messages.length - 1];
  
  if (!lastMessage) return { status: 'unknown' };
  
  // 2. 检查是否有加载动画（生成中）
  const loadingIndicator = lastMessage.querySelector('[class*="loading"], [class*="generating"]');
  if (loadingIndicator) return { status: 'generating' };
  
  // 3. 检查是否有文本内容（完成）
  const textContent = lastMessage.textContent.trim();
  if (textContent) return { status: 'completed', content: textContent };
  
  return { status: 'unknown' };
}
```

---

## 二、智能监测流程设计

### 2.1 轮询检测机制

```javascript
// 智能等待回答生成
async function waitForResponse(tabId, options = {}) {
  const {
    timeout = 30000,      // 最大等待30秒
    interval = 500,        // 检测间隔500ms
    onProgress = null     // 进度回调
  } = options;
  
  const startTime = Date.now();
  let lastContent = '';
  let stableCount = 0;     // 内容稳定计数
  
  while (Date.now() - startTime < timeout) {
    // 获取页面snapshot
    const snapshot = await browser.snapshot({ tabId, targetId: tabId });
    
    // 解析最新消息
    const latestMessage = extractLatestMessage(snapshot);
    
    if (latestMessage) {
      // 检查是否生成完成
      if (latestMessage.isComplete) {
        return {
          success: true,
          content: latestMessage.content,
          timeSpent: Date.now() - startTime
        };
      }
      
      // 检查内容是否有变化（流式输出中）
      if (latestMessage.content !== lastContent) {
        lastContent = latestMessage.content;
        stableCount = 0;
        onProgress?.(latestMessage.content);
      } else {
        stableCount++;
        
        // 内容稳定后等待一小段时间确认完成
        if (stableCount >= 3) {
          return {
            success: true,
            content: lastContent,
            timeSpent: Date.now() - startTime,
            note: 'stable'
          };
        }
      }
    }
    
    await sleep(interval);
  }
  
  return {
    success: false,
    error: 'timeout',
    timeSpent: timeout
  };
}
```

### 2.2 超时处理

```javascript
const TIMEOUTS = {
  short: 10000,   // 简单问题
  medium: 20000,  // 普通问题
  long: 45000,   // 复杂问题
  custom: null   // 自定义
};

async function chatWithTimeout(question, complexity = 'medium') {
  const timeout = TIMEOUTS[complexity] || TIMEOUTS.medium;
  
  const result = await Promise.race([
    sendQuestionAndWait(question),
    new Promise((_, reject) => 
      setTimeout(() => reject(new Error('Timeout')), timeout)
    )
  ]);
  
  return result;
}
```

### 2.3 断线重试机制

```javascript
async function sendWithRetry(question, maxRetries = 3) {
  let lastError;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      // 检查标签页连接状态
      const tabs = await browser.tabs({ profile: 'chrome' });
      const doubaoTab = tabs.find(t => t.url.includes('doubao.com'));
      
      if (!doubaoTab) {
        // 需要重新打开豆包
        await browser.open({ 
          profile: 'chrome', 
          url: 'https://www.doubao.com/chat/' 
        });
        await sleep(2000); // 等待页面加载
      }
      
      return await sendQuestionAndWait(question);
      
    } catch (error) {
      lastError = error;
      console.warn(`Attempt ${attempt} failed:`, error);
      
      // 指数退避
      await sleep(Math.pow(2, attempt) * 1000);
    }
  }
  
  throw new Error(`Failed after ${maxRetries} attempts: ${lastError.message}`);
}
```

---

## 三、多AI交叉验证方案

### 3.1 并行询问架构

```
┌─────────────────────────────────────────────────────┐
│                    用户问题                          │
└─────────────────┬───────────────────────────────────┘
                  │
        ┌─────────▼─────────┐
        │   任务分发器       │
        │ (Task Dispatcher)  │
        └─────────┬─────────┘
                  │
      ┌───────────┴───────────┐
      ▼                       ▼
┌──────────┐           ┌──────────┐
│  豆包    │           │ MiniMax  │
│ (免费)   │           │ (付费)   │
└────┬─────┘           └────┬─────┘
     │                      │
     └──────────┬───────────┘
                ▼
        ┌──────────────┐
        │ 结果对比器    │
        │ (Comparator)  │
        └──────┬───────┘
               ▼
        ┌──────────────┐
        │  选择最佳答案 │
        └──────────────┘
```

### 3.2 实现代码

```javascript
class MultiAIValidator {
  constructor(options = {}) {
    this.doubaoEnabled = options.doubaoEnabled ?? true;
    this.minimaxEnabled = options.minimaxEnabled ?? true;
    this.minScore = options.minScore ?? 0.7;
  }
  
  async ask(question, context = {}) {
    const results = [];
    
    // 并行发送请求
    const promises = [];
    
    if (this.doubaoEnabled) {
      promises.push(this.askDoubao(question).then(r => ({
        provider: 'doubao',
        ...r
      })));
    }
    
    if (this.minimaxEnabled) {
      promises.push(this.askMinimax(question, context).then(r => ({
        provider: 'minimax',
        ...r
      })));
    }
    
    // 等待所有结果
    const allResults = await Promise.allSettled(promises);
    
    // 收集成功的结果
    for (const result of allResults) {
      if (result.status === 'fulfilled') {
        results.push(result.value);
      }
    }
    
    // 对比并选择最佳
    return this.selectBest(results, question);
  }
  
  async askDoubao(question) {
    const startTime = Date.now();
    
    // 使用浏览器控制豆包
    await this.typeAndSend(question);
    const response = await this.waitForResponse();
    
    return {
      content: response.content,
      timeSpent: Date.now() - startTime,
      cost: 0  // 豆包免费
    };
  }
  
  async askMinimax(question, context) {
    const startTime = Date.now();
    
    // 调用MiniMax API
    const response = await callMinimaxAPI({
      messages: [{ role: 'user', content: question }],
      ...context
    });
    
    return {
      content: response.choices[0].message.content,
      timeSpent: Date.now() - startTime,
      cost: this.calculateCost(response.usage)
    };
  }
  
  selectBest(results, question) {
    if (results.length === 0) {
      throw new Error('No results from any AI');
    }
    
    if (results.length === 1) {
      return results[0];
    }
    
    // 如果只有一个结果，直接返回
    // 如果有多个，进行对比
    
    // 评分逻辑
    const scored = results.map(r => ({
      ...r,
      score: this.evaluateAnswer(r.content, question)
    }));
    
    // 按评分排序
    scored.sort((a, b) => b.score - a.score);
    
    const best = scored[0];
    const second = scored[1];
    
    // 如果最佳答案分数显著高于其他，返回最佳
    // 否则返回第一个结果（通常是更快的）
    if (best.score > second.score + 0.2) {
      return {
        ...best,
        note: 'selected_by_score',
        alternatives: scored.slice(1)
      };
    }
    
    // 返回第一个结果，同时提供备选
    return {
      ...results[0],
      note: 'selected_first',
      alternatives: results.slice(1)
    };
  }
  
  evaluateAnswer(answer, question) {
    // 简化的评估逻辑
    // 实际可以使用更复杂的相似度计算
    
    let score = 0.5;
    
    // 检查是否回答了问题
    if (answer.length > 20) score += 0.1;
    
    // 检查是否包含相关关键词（简化版）
    // 实际应该用NLP
    
    return Math.min(score, 1.0);
  }
  
  calculateCost(usage) {
    // MiniMax 计费
    const pricePer1K = {
      input: 0.01,
      output: 0.03
    };
    
    return (
      (usage.prompt_tokens / 1000) * pricePer1K.input +
      (usage.completion_tokens / 1000) * pricePer1K.output
    );
  }
}
```

---

## 四、节省API策略

### 4.1 任务分类

| 任务类型 | 推荐AI | 原因 |
|----------|--------|------|
| 简单问答 | 豆包 | 免费，响应快 |
| 联网搜索 | 豆包 | 可直接联网 |
| 创意写作 | MiniMax | 质量更高 |
| 代码生成 | 豆包 | 能力足够 |
| 复杂推理 | MiniMax | 能力更强 |
| 翻译 | 豆包 | 免费且效果好 |
| 长文生成 | MiniMax | 质量更有保障 |

### 4.2 成本对比

```
MiniMax 定价（示例）:
- 输入: $0.01/1K tokens
- 输出: $0.03/1K tokens

豆包: 免费

节省策略:
1. 简单问题先用豆包
2. 如果豆包回答不满意，再调用MiniMax
3. 使用豆包进行信息搜集，MiniMax进行总结
```

### 4.3 智能路由

```javascript
async function smartRoute(question) {
  // 分析问题复杂度
  const complexity = analyzeComplexity(question);
  
  // 简单问题直接用豆包
  if (complexity === 'simple') {
    const result = await askDoubao(question);
    
    // 检查结果质量
    if (validateQuality(result)) {
      return { provider: 'doubao', ...result };
    }
    // 质量不够，升级到MiniMax
  }
  
  // 复杂问题直接用MiniMax
  if (complexity === 'complex') {
    return await askMinimax(question);
  }
  
  // 中等问题：先尝试豆包，不满意再升级
  const doubaoResult = await askDoubao(question);
  if (validateQuality(doubaoResult)) {
    return { provider: 'doubao', ...doubaoResult };
  }
  
  return await askMinimax(question);
}

function analyzeComplexity(question) {
  const length = question.length;
  const hasCode = /```|function|class|import/.test(question);
  const hasReasoning = /为什么|如何|原因|解释/.test(question);
  
  if (length > 500 || hasCode || hasReasoning) {
    return 'complex';
  }
  
  if (length < 100 && !hasReasoning) {
    return 'simple';
  }
  
  return 'medium';
}
```

---

## 五、集成到 Skill

### 5.1 更新后的 Skill 结构

```markdown
# doubao-chat (优化版)

## 智能等待（替代固定延迟）

### 1. 检测生成状态

// 获取页面状态
browser(action=snapshot, profile="chrome")

// 等待生成完成（智能版）
// 不再使用 sleep 8，而是轮询检测
```

### 5.2 关键改进点

1. **从固定等待 → 智能检测**
   - 旧: `sleep 8`
   - 新: 轮询检测直到生成完成

2. **从单渠道 → 多AI路由**
   - 根据问题类型选择合适的AI
   - 简单问题用豆包（免费）
   - 复杂问题用MiniMax

3. **从手动重试 → 自动容错**
   - 断线自动重连
   - 超时自动处理

---

## 六、总结

| 功能 | 当前状态 | 优化后 |
|------|----------|--------|
| 等待时间 | 固定8秒 | 智能检测（通常3-8秒） |
| 生成状态 | 未知 | 可检测 |
| 断线处理 | 手动 | 自动重试 |
| API成本 | 全部MiniMax | 豆包+MiniMax混合 |
| 答案质量 | 单一来源 | 交叉验证 |
