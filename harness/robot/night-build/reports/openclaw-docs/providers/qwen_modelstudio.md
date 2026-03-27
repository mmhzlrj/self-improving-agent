> ## Documentation Index
> Fetch the complete documentation index at: https://docs.openclaw.ai/llms.txt
> Use this file to discover all available pages before exploring further.

# Qwen / Model Studio

# Qwen / Model Studio (Alibaba Cloud)

The Model Studio provider gives access to Alibaba Cloud models including Qwen
and third-party models hosted on the platform. Two billing plans are supported:
**Standard** (pay-as-you-go) and **Coding Plan** (subscription).

* Provider: `modelstudio`
* Auth: `MODELSTUDIO_API_KEY`
* API: OpenAI-compatible

## Quick start

### Standard (pay-as-you-go)

```bash  theme={"theme":{"light":"min-light","dark":"min-dark"}}
# China endpoint
openclaw onboard --auth-choice modelstudio-standard-api-key-cn

# Global/Intl endpoint
openclaw onboard --auth-choice modelstudio-standard-api-key
```

### Coding Plan (subscription)

```bash  theme={"theme":{"light":"min-light","dark":"min-dark"}}
# China endpoint
openclaw onboard --auth-choice modelstudio-api-key-cn

# Global/Intl endpoint
openclaw onboard --auth-choice modelstudio-api-key
```

After onboarding, set a default model:

```json5  theme={"theme":{"light":"min-light","dark":"min-dark"}}
{
  agents: {
    defaults: {
      model: { primary: "modelstudio/qwen3.5-plus" },
    },
  },
}
```

## Plan types and endpoints

| Plan                       | Region | Auth choice                       | Endpoint                                         |
| -------------------------- | ------ | --------------------------------- | ------------------------------------------------ |
| Standard (pay-as-you-go)   | China  | `modelstudio-standard-api-key-cn` | `dashscope.aliyuncs.com/compatible-mode/v1`      |
| Standard (pay-as-you-go)   | Global | `modelstudio-standard-api-key`    | `dashscope-intl.aliyuncs.com/compatible-mode/v1` |
| Coding Plan (subscription) | China  | `modelstudio-api-key-cn`          | `coding.dashscope.aliyuncs.com/v1`               |
| Coding Plan (subscription) | Global | `modelstudio-api-key`             | `coding-intl.dashscope.aliyuncs.com/v1`          |

The provider auto-selects the endpoint based on your auth choice. You can
override with a custom `baseUrl` in config.

## Get your API key

* **China**: [bailian.console.aliyun.com](https://bailian.console.aliyun.com/)
* **Global/Intl**: [modelstudio.console.alibabacloud.com](https://modelstudio.console.alibabacloud.com/)

## Available models

* **qwen3.5-plus** (default) — Qwen 3.5 Plus
* **qwen3-coder-plus**, **qwen3-coder-next** — Qwen coding models
* **GLM-5** — GLM models via Alibaba
* **Kimi K2.5** — Moonshot AI via Alibaba
* **MiniMax-M2.5** — MiniMax via Alibaba

Some models (qwen3.5-plus, kimi-k2.5) support image input. Context windows range from 200K to 1M tokens.

## Environment note

If the Gateway runs as a daemon (launchd/systemd), make sure
`MODELSTUDIO_API_KEY` is available to that process (for example, in
`~/.openclaw/.env` or via `env.shellEnv`).

Built with [Mintlify](https://mintlify.com).