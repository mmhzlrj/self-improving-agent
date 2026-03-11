# Polymarket + AI Daily Briefing - Cron Task

## Schedule
每天 08:00 (Asia/Shanghai) 自动执行

## Task Description
拉取以下内容，整理成日报发送到用户个人飞书：

### 1. Polymarket 热门市场 (24h 成交量 TOP 10)
- API: https://gamma-api.polymarket.com/markets?limit=10&active=true&closed=false&order=volume24hr&ascending=false
- 展示：市场名称、当前概率、24h成交量、流动性

### 2. Polymarket AI 相关市场
- 关键词过滤：AI, GPT, Claude, Gemini, LLM, OpenAI, Anthropic, model, AGI
- API: https://gamma-api.polymarket.com/markets?limit=50&active=true&closed=false&order=volume24hr&ascending=false&_query=AI

### 3. Polymarket RWA / RDA 市场
- 关键词：RWA, real world asset, tokeniz, commodity, gold, treasury
- 从热门市场中过滤

### 4. AI 行业资讯 (web search)
- 新的 AI 赚钱场景/商业模式
- 新趋势、新的大模型发布
- 中国 AI 动态（国内大模型、政策）
- 硬件：AI Max Halo, Medusa Halo, LPDDR6, 芯片相关

## Output Format
发送到用户个人飞书消息
