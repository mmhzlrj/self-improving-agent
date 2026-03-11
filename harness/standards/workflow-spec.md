# 📋 工作流开发规范

## 工作流结构

```
workflows/[workflow-name]/
├── index.js          # 主入口（必需）
├── config.json       # 默认配置（可选）
└── README.md         # 文档（可选）
```

## index.js 规范

### 必需结构

```javascript
module.exports = {
  meta: {
    id: String,           // 唯一标识
    name: String,        // 显示名称
    version: String,
    author: String,
    description: String,
    
    // 触发条件
    trigger: {
      type: 'schedule' | 'webhook' | 'manual' | 'event',
      cron?: String,           // schedule 类型
      path?: String,           // webhook 类型
      event?: String,          // event 类型
    }
  },
  
  // 输入参数（从用户/触发器传入）
  input: {
    [paramName]: {
      type: 'string' | 'number' | 'boolean' | 'object' | 'array',
      required: Boolean,
      default: Any,
      description: String
    }
  },
  
  // 输出结果
  output: {
    [resultName]: {
      type: Any,
      description: String
    }
  },
  
  // 步骤定义
  steps: [
    {
      id: String,           // 步骤唯一标识
      name: String,        // 步骤名称
      
      // 执行模式：tool | agent | condition
      type: 'tool' | 'agent' | 'condition' | 'loop' | 'parallel',
      
      // 调用模块工具
      module: String,       // 模块 ID
      tool: String,         // 工具名
      params: Object,       // 参数（支持模板变量）
      
      // 或使用 agent
      agent: {
        prompt: String,     // Agent 提示词
        context: String[],   // 从前面的步骤获取上下文
        model: String        // 可选，指定模型
      },
      
      // 或条件判断
      condition: {
        expression: String,  // 布尔表达式
        trueStep: String,    // 条件为真时的下一步
        falseStep: String    // 条件为假时的下一步
      },
      
      // 循环
      loop: {
        over: String,        // 迭代数组变量
        itemVar: String,     // 当前项变量名
        body: [Step]         // 循环体
      },
      
      // 并行执行
      parallel: [Step],
      
      // 输出到变量
      output: String,        // 变量名，可在后续步骤使用 {{variables.name}}
      
      // 错误处理
      onError: {
        continue: Boolean,   // 是否继续执行
        fallback: String    // 失败时的后备步骤
      }
    }
  ],
  
  // 条件分支
  conditions: {
    [conditionName]: String  // 布尔表达式
  }
};
```

## 模板变量

### 引用变量

```javascript
// 引用前面步骤的输出
params: {
  query: '{{steps.search.query}}'
}

// 引用输入参数
params: {
  user_id: '{{input.user_id}}'
}

// 引用上下文
params: {
  user_name: '{{context.user.name}}'
}

// 引用配置
params: {
  api_key: '{{config.apiKey}}'
}
```

### 内置函数

```javascript
params: {
  // 过滤
  urgent_emails: '{{emails|filter:"priority":"high"}}',
  
  // 映射
  titles: '{{emails|map:"title"}}',
  
  // 切片
  recent: '{{emails|slice:0:5}}',
  
  // 长度
  count: '{{emails|length}}',
  
  // 日期格式化
  date: '{{now|format:"YYYY-MM-DD"}}'
}
```

## 触发类型详解

### 1. 定时触发 (schedule)

```javascript
trigger: {
  type: 'schedule',
  cron: '0 8 * * *'           // 每天早上 8 点
  // 或
  cron: '0 9 * * 1-5'        // 工作日早上 9 点
}
```

### 2. Webhook 触发

```javascript
trigger: {
  type: 'webhook',
  path: '/webhook/github',    // Webhook 路径
  method: 'POST',
  events: ['push', 'pull_request']
}
```

### 3. 手动触发

```javascript
trigger: {
  type: 'manual',
  // 用户通过命令触发
}
```

### 4. 事件触发

```javascript
trigger: {
  type: 'event',
  event: 'user.onboarded',    // 用户完成入职
  // 或
  event: 'email.received'    // 收到新邮件
}
```

## 示例：每日简报工作流

```javascript
// workflows/daily-brief/index.js
module.exports = {
  meta: {
    id: 'daily-brief',
    name: '每日简报',
    version: '1.0.0',
    author: 'OpenClaw',
    description: '每天自动生成工作简报',
    trigger: {
      type: 'schedule',
      cron: '0 8 * * *'
    }
  },
  
  input: {
    channels: {
      type: 'array',
      default: ['webchat'],
      description: '发送渠道'
    }
  },
  
  output: {
    brief: {
      type: 'string',
      description: '生成的简报内容'
    }
  },
  
  steps: [
    {
      id: 'get-calendar',
      name: '获取今日日程',
      type: 'tool',
      module: 'calendar',
      tool: 'getTodayEvents',
      output: 'events'
    },
    {
      id: 'get-emails',
      name: '获取未读邮件',
      type: 'tool',
      module: 'email',
      tool: 'getUnreadEmails',
      params: { limit: 10 },
      output: 'emails'
    },
    {
      id: 'check-reminders',
      name: '检查提醒',
      type: 'tool',
      module: 'productivity',
      tool: 'getReminders',
      output: 'reminders'
    },
    {
      id: 'generate-brief',
      name: '生成简报',
      type: 'agent',
      agent: {
        prompt: `请根据以下信息生成今日工作简报：

1. 今日日程：{{steps.get-calendar.events}}
2. 未读邮件：{{steps.get-emails.emails}}
3. 待办提醒：{{steps.check-reminders.reminders}}

要求：
- 简洁明了
- 突出重点
- 建议下一步行动`,
        context: ['events', 'emails', 'reminders']
      },
      output: 'brief'
    },
    {
      id: 'send-brief',
      name: '发送简报',
      type: 'tool',
      module: 'messaging',
      tool: 'sendMessage',
      params: {
        message: '{{steps.generate-brief.brief}}',
        channels: '{{input.channels}}'
      }
    }
  ]
};
```

## 错误处理

```javascript
{
  id: 'risky-step',
  type: 'tool',
  module: 'external',
  tool: 'callApi',
  
  // 错误处理
  onError: {
    continue: true,                    // 继续执行
    fallback: 'use-cache-data',        // 使用缓存数据
    retry: {
      maxAttempts: 3,
      delay: 1000,
      backoff: 'exponential'
    }
  }
}
```

## 注册工作流

```json
{
  "workflows": {
    "enabled": ["daily-brief"],
    "available": [
      "daily-brief",
      "meeting-prep",
      "onboarding"
    ]
  }
}
```

---

## 调试技巧

```javascript
// 在步骤中添加日志
{
  id: 'debug-step',
  type: 'tool',
  // ...
  debug: {
    logInput: true,
    logOutput: true
  }
}
```
