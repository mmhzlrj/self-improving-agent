> ## Documentation Index
> Fetch the complete documentation index at: https://docs.openclaw.ai/llms.txt
> Use this file to discover all available pages before exploring further.

# Z.AI

# Z.AI

Z.AI is the API platform for **GLM** models. It provides REST APIs for GLM and uses API keys
for authentication. Create your API key in the Z.AI console. OpenClaw uses the `zai` provider
with a Z.AI API key.

## CLI setup

```bash  theme={"theme":{"light":"min-light","dark":"min-dark"}}
# Coding Plan Global, recommended for Coding Plan users
openclaw onboard --auth-choice zai-coding-global

# Coding Plan CN (China region), recommended for Coding Plan users
openclaw onboard --auth-choice zai-coding-cn

# General API
openclaw onboard --auth-choice zai-global

# General API CN (China region)
openclaw onboard --auth-choice zai-cn
```

## Config snippet

```json5  theme={"theme":{"light":"min-light","dark":"min-dark"}}
{
  env: { ZAI_API_KEY: "sk-..." },
  agents: { defaults: { model: { primary: "zai/glm-5" } } },
}
```

## Notes

* GLM models are available as `zai/` (example: `zai/glm-5`).
* `tool_stream` is enabled by default for Z.AI tool-call streaming. Set
  `agents.defaults.models["zai/"].params.tool_stream` to `false` to disable it.
* See [/providers/glm](/providers/glm) for the model family overview.
* Z.AI uses Bearer auth with your API key.

Built with [Mintlify](https://mintlify.com).