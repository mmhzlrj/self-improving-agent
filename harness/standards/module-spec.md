# 📐 模块开发规范

## 模块结构

每个模块必须包含以下文件：

```
modules/[category]/[module-name]/
├── index.js          # 主入口（必需）
├── config.json       # 默认配置（可选）
├── README.md        # 文档（可选）
└── test/            # 测试目录（可选）
```

## index.js 规范

### 必需结构

```javascript
module.exports = {
  // ====== 元数据 ======
  meta: {
    id: String,           // 唯一标识，如 "communication.email"
    name: String,        // 显示名称
    version: String,     // 语义化版本，如 "1.0.0"
    author: String,      // 作者
    description: String,// 描述
    category: String,   // 分类：communication, productivity, knowledge, automation, i18n
    
    // 配置 schema（JSON Schema）
    configSchema: Object
  },
  
  // ====== 初始化 ======
  async init(context, config) {
    // context: 运行时上下文
    // config: 用户配置
  },
  
  // ====== 工具定义 ======
  tools: {
    [toolName]: async (params, context) => {
      // 返回结果
      return { success: true, data: {} };
    }
  },
  
  // ====== 钩子 ======
  hooks: {
    'on-message': async (message, context) => {},
    'on-schedule': async (context) => {},
    'on-startup': async (context) => {},
    'on-shutdown': async (context) => {}
  },
  
  // ====== 权限 ======
  permissions: []  // 如 ["email.read", "calendar.write"]
};
```

### Context 对象

```javascript
context = {
  // 用户信息
  user: {
    id: String,
    name: String,
    locale: String,
    timezone: String
  },
  
  // 日志
  logger: {
    debug(msg, ...args),
    info(msg, ...args),
    warn(msg, ...args),
    error(msg, ...args)
  },
  
  // 配置
  config: Object,
  
  // 存储
  storage: {
    get(key) / set(key, value) / delete(key)
  },
  
  // 调用其他模块
  call(moduleId, toolName, params),
  
  // 发送消息
  sendMessage(channel, message)
}
```

### 工具返回值规范

```javascript
// 成功
return { 
  success: true, 
  data: { /* 结果数据 */ }
};

// 失败
return { 
  success: false, 
  error: {
    code: 'ERROR_CODE',
    message: '错误描述'
  }
};
```

## 配置 Schema

使用 JSON Schema 规范：

```javascript
configSchema: {
  // 字符串
  apiKey: { 
    type: 'string', 
    required: true,
    sensitive: true  // 标记为敏感数据
  },
  
  // 枚举
  mode: { 
    type: 'string', 
    enum: ['test', 'production'], 
    default: 'test' 
  },
  
  // 数字
  timeout: { 
    type: 'number', 
    default: 30000,
    min: 1000,
    max: 60000
  },
  
  // 布尔
  enabled: { 
    type: 'boolean', 
    default: true 
  },
  
  // 数组
  channels: {
    type: 'array',
    items: { type: 'string' },
    default: ['webchat']
  },
  
  // 对象
  advanced: {
    type: 'object',
    properties: {
      retries: { type: 'number' },
      debug: { type: 'boolean' }
    }
  }
}
```

## 示例：简单天气模块

```javascript
// modules/i18n/weather/index.js
const fetch = require('node-fetch');

module.exports = {
  meta: {
    id: 'i18n.weather',
    name: '天气查询',
    version: '1.0.0',
    author: 'OpenClaw',
    description: '查询全球城市天气',
    category: 'i18n',
    configSchema: {
      defaultCity: { type: 'string', default: 'Beijing' },
      units: { type: 'string', enum: ['celsius', 'fahrenheit'], default: 'celsius' }
    }
  },
  
  async init(context, config) {
    this.config = config;
    context.logger.info('天气模块初始化完成');
  },
  
  tools: {
    getWeather: async (params, context) => {
      const city = params.city || this.config.defaultCity;
      const units = params.units || this.config.units;
      
      try {
        const url = `https://wttr.in/${city}?format=j1`;
        const response = await fetch(url);
        const data = await response.json();
        
        return {
          success: true,
          data: {
            city: data.nearest_area[0].areaName[0].value,
            temperature: data.current_condition[0].temp_C,
            condition: data.current_condition[0].weatherDesc[0].value
          }
        };
      } catch (error) {
        return {
          success: false,
          error: { code: 'WEATHER_ERROR', message: error.message }
        };
      }
    }
  },
  
  hooks: {
    'on-message': async (message, context) => {
      // 监听消息中的天气查询
      if (message.text.includes('天气')) {
        // 自动回复天气
      }
    }
  },
  
  permissions: []
};
```

## 注册模块

在 `harness.json` 中注册：

```json
{
  "modules": {
    "available": {
      "i18n": ["weather"]
    }
  }
}
```

---

## 常见问题

### Q: 模块如何获取用户配置？

```javascript
// 通过 context.config 或构造函数传入的 config
async init(context, config) {
  this.apiKey = config.apiKey;
}
```

### Q: 如何调用其他模块？

```javascript
// 通过 context.call
const emailResult = await context.call('communication.email', 'send', {
  to: 'user@example.com',
  subject: 'Hello',
  body: 'Content'
});
```

### Q: 如何处理异步初始化？

```javascript
async init(context, config) {
  // 可以返回 promise
  await this.connectToService(config.endpoint);
}
```

### Q: 敏感配置如何处理？

```javascript
configSchema: {
  apiKey: { type: 'string', sensitive: true }
}
// 敏感字段会自动加密存储，不会出现在日志中
```
