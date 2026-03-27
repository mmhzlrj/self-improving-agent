> ## Documentation Index
> Fetch the complete documentation index at: https://docs.openclaw.ai/llms.txt
> Use this file to discover all available pages before exploring further.

# Qwen

# Qwen

  **Qwen OAuth has been removed.** The free-tier OAuth integration
  (`qwen-portal`) that used `portal.qwen.ai` endpoints is no longer available.
  See [Issue #49557](https://github.com/openclaw/openclaw/issues/49557) for
  background.

## Recommended: Model Studio (Alibaba Cloud Coding Plan)

Use [Model Studio](/providers/modelstudio) for officially supported access to
Qwen models (Qwen 3.5 Plus, GLM-4.7, Kimi K2.5, MiniMax M2.5, and more).

```bash  theme={"theme":{"light":"min-light","dark":"min-dark"}}
# Global endpoint
openclaw onboard --auth-choice modelstudio-api-key

# China endpoint
openclaw onboard --auth-choice modelstudio-api-key-cn
```

See [Model Studio](/providers/modelstudio) for full setup details.

Built with [Mintlify](https://mintlify.com).