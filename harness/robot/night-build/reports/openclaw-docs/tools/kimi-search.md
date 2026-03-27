> ## Documentation Index
> Fetch the complete documentation index at: https://docs.openclaw.ai/llms.txt
> Use this file to discover all available pages before exploring further.

# Kimi Search

# Kimi Search

OpenClaw supports Kimi as a `web_search` provider, using Moonshot web search
to produce AI-synthesized answers with citations.

## Get an API key

    Get an API key from [Moonshot AI](https://platform.moonshot.cn/).

    Set `KIMI_API_KEY` or `MOONSHOT_API_KEY` in the Gateway environment, or
    configure via:

    ```bash  theme={"theme":{"light":"min-light","dark":"min-dark"}}
    openclaw configure --section web
    ```

## Config

```json5  theme={"theme":{"light":"min-light","dark":"min-dark"}}
{
  plugins: {
    entries: {
      moonshot: {
        config: {
          webSearch: {
            apiKey: "sk-...", // optional if KIMI_API_KEY or MOONSHOT_API_KEY is set
          },
        },
      },
    },
  },
  tools: {
    web: {
      search: {
        provider: "kimi",
      },
    },
  },
}
```

**Environment alternative:** set `KIMI_API_KEY` or `MOONSHOT_API_KEY` in the
Gateway environment. For a gateway install, put it in `~/.openclaw/.env`.

## How it works

Kimi uses Moonshot web search to synthesize answers with inline citations,
similar to Gemini and Grok's grounded response approach.

## Supported parameters

Kimi search supports the standard `query` and `count` parameters.
Provider-specific filters are not currently supported.

## Related

* [Web Search overview](/tools/web) -- all providers and auto-detection
* [Gemini Search](/tools/gemini-search) -- AI-synthesized answers via Google grounding
* [Grok Search](/tools/grok-search) -- AI-synthesized answers via xAI grounding

Built with [Mintlify](https://mintlify.com).