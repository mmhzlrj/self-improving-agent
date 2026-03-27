> ## Documentation Index
> Fetch the complete documentation index at: https://docs.openclaw.ai/llms.txt
> Use this file to discover all available pages before exploring further.

# Grok Search

# Grok Search

OpenClaw supports Grok as a `web_search` provider, using xAI web-grounded
responses to produce AI-synthesized answers backed by live search results
with citations.

## Get an API key

    Get an API key from [xAI](https://console.x.ai/).

    Set `XAI_API_KEY` in the Gateway environment, or configure via:

    ```bash  theme={"theme":{"light":"min-light","dark":"min-dark"}}
    openclaw configure --section web
    ```

## Config

```json5  theme={"theme":{"light":"min-light","dark":"min-dark"}}
{
  plugins: {
    entries: {
      xai: {
        config: {
          webSearch: {
            apiKey: "xai-...", // optional if XAI_API_KEY is set
          },
        },
      },
    },
  },
  tools: {
    web: {
      search: {
        provider: "grok",
      },
    },
  },
}
```

**Environment alternative:** set `XAI_API_KEY` in the Gateway environment.
For a gateway install, put it in `~/.openclaw/.env`.

## How it works

Grok uses xAI web-grounded responses to synthesize answers with inline
citations, similar to Gemini's Google Search grounding approach.

## Supported parameters

Grok search supports the standard `query` and `count` parameters.
Provider-specific filters are not currently supported.

## Related

* [Web Search overview](/tools/web) -- all providers and auto-detection
* [Gemini Search](/tools/gemini-search) -- AI-synthesized answers via Google grounding

Built with [Mintlify](https://mintlify.com).