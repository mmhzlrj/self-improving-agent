# Zero Token Web 登录插件

这个目录包含从 openclaw-zero-token 项目移植过来的网页版 AI 登录支持。

## 已移植的文件

### Providers (认证 + 客户端)
- `deepseek-web-auth.ts` / `deepseek-web-client.ts`
- `claude-web-auth.ts` / `claude-web-client.ts` / `claude-web-client-browser.ts`
- `doubao-web-auth.ts` / `doubao-web-client.ts` / `doubao-web-client-browser.ts`
- `kimi-web-auth.ts` / `kimi-web-client-browser.ts`

### Agents (流式处理)
- `deepseek-web-stream.ts`
- `claude-web-stream.ts`
- `doubao-web-stream.ts`
- `kimi-web-stream.ts`
- `prompt-sanitize.ts`

## 待完成

1. 修改导入路径适配现有 OpenClaw
2. 创建配置模板
3. 创建登录引导 Skill
