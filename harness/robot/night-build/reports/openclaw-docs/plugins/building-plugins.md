> ## Documentation Index
> Fetch the complete documentation index at: https://docs.openclaw.ai/llms.txt
> Use this file to discover all available pages before exploring further.

# Building Plugins

# Building Plugins

Plugins extend OpenClaw with new capabilities: channels, model providers, speech,
image generation, web search, agent tools, or any combination.

You do not need to add your plugin to the OpenClaw repository. Publish to
[ClawHub](/tools/clawhub) or npm and users install with
`openclaw plugins install `. OpenClaw tries ClawHub first and
falls back to npm automatically.

## Prerequisites

* Node >= 22 and a package manager (npm or pnpm)
* Familiarity with TypeScript (ESM)
* For in-repo plugins: repository cloned and `pnpm install` done

## What kind of plugin?

    Connect OpenClaw to a messaging platform (Discord, IRC, etc.)

    Add a model provider (LLM, proxy, or custom endpoint)

    Register agent tools, event hooks, or services — continue below

## Quick start: tool plugin

This walkthrough creates a minimal plugin that registers an agent tool. Channel
and provider plugins have dedicated guides linked above.

      ```json package.json theme={"theme":{"light":"min-light","dark":"min-dark"}}
      {
        "name": "@myorg/openclaw-my-plugin",
        "version": "1.0.0",
        "type": "module",
        "openclaw": {
          "extensions": ["./index.ts"]
        }
      }
      ```

      ```json openclaw.plugin.json theme={"theme":{"light":"min-light","dark":"min-dark"}}
      {
        "id": "my-plugin",
        "name": "My Plugin",
        "description": "Adds a custom tool to OpenClaw",
        "configSchema": {
          "type": "object",
          "additionalProperties": false
        }
      }
      ```

    Every plugin needs a manifest, even with no config. See
    [Manifest](/plugins/manifest) for the full schema.

    ```typescript  theme={"theme":{"light":"min-light","dark":"min-dark"}}
    // index.ts
    import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
    import { Type } from "@sinclair/typebox";

    export default definePluginEntry({
      id: "my-plugin",
      name: "My Plugin",
      description: "Adds a custom tool to OpenClaw",
      register(api) {
        api.registerTool({
          name: "my_tool",
          description: "Do a thing",
          parameters: Type.Object({ input: Type.String() }),
          async execute(_id, params) {
            return { content: [{ type: "text", text: `Got: ${params.input}` }] };
          },
        });
      },
    });
    ```

    `definePluginEntry` is for non-channel plugins. For channels, use
    `defineChannelPluginEntry` — see [Channel Plugins](/plugins/sdk-channel-plugins).
    For full entry point options, see [Entry Points](/plugins/sdk-entrypoints).

    **External plugins:** publish to [ClawHub](/tools/clawhub) or npm, then install:

    ```bash  theme={"theme":{"light":"min-light","dark":"min-dark"}}
    openclaw plugins install @myorg/openclaw-my-plugin
    ```

    OpenClaw checks ClawHub first, then falls back to npm.

    **In-repo plugins:** place under `extensions/` — automatically discovered.

    ```bash  theme={"theme":{"light":"min-light","dark":"min-dark"}}
    pnpm test -- extensions/my-plugin/
    ```

## Plugin capabilities

A single plugin can register any number of capabilities via the `api` object:

| Capability           | Registration method                           | Detailed guide                                                                  |
| -------------------- | --------------------------------------------- | ------------------------------------------------------------------------------- |
| Text inference (LLM) | `api.registerProvider(...)`                   | [Provider Plugins](/plugins/sdk-provider-plugins)                               |
| Channel / messaging  | `api.registerChannel(...)`                    | [Channel Plugins](/plugins/sdk-channel-plugins)                                 |
| Speech (TTS/STT)     | `api.registerSpeechProvider(...)`             | [Provider Plugins](/plugins/sdk-provider-plugins#step-5-add-extra-capabilities) |
| Media understanding  | `api.registerMediaUnderstandingProvider(...)` | [Provider Plugins](/plugins/sdk-provider-plugins#step-5-add-extra-capabilities) |
| Image generation     | `api.registerImageGenerationProvider(...)`    | [Provider Plugins](/plugins/sdk-provider-plugins#step-5-add-extra-capabilities) |
| Web search           | `api.registerWebSearchProvider(...)`          | [Provider Plugins](/plugins/sdk-provider-plugins#step-5-add-extra-capabilities) |
| Agent tools          | `api.registerTool(...)`                       | Below                                                                           |
| Custom commands      | `api.registerCommand(...)`                    | [Entry Points](/plugins/sdk-entrypoints)                                        |
| Event hooks          | `api.registerHook(...)`                       | [Entry Points](/plugins/sdk-entrypoints)                                        |
| HTTP routes          | `api.registerHttpRoute(...)`                  | [Internals](/plugins/architecture#gateway-http-routes)                          |
| CLI subcommands      | `api.registerCli(...)`                        | [Entry Points](/plugins/sdk-entrypoints)                                        |

For the full registration API, see [SDK Overview](/plugins/sdk-overview#registration-api).

Hook guard semantics to keep in mind:

* `before_tool_call`: `{ block: true }` is terminal and stops lower-priority handlers.
* `before_tool_call`: `{ block: false }` is treated as no decision.
* `message_sending`: `{ cancel: true }` is terminal and stops lower-priority handlers.
* `message_sending`: `{ cancel: false }` is treated as no decision.

See [SDK Overview hook decision semantics](/plugins/sdk-overview#hook-decision-semantics) for details.

## Registering agent tools

Tools are typed functions the LLM can call. They can be required (always
available) or optional (user opt-in):

```typescript  theme={"theme":{"light":"min-light","dark":"min-dark"}}
register(api) {
  // Required tool — always available
  api.registerTool({
    name: "my_tool",
    description: "Do a thing",
    parameters: Type.Object({ input: Type.String() }),
    async execute(_id, params) {
      return { content: [{ type: "text", text: params.input }] };
    },
  });

  // Optional tool — user must add to allowlist
  api.registerTool(
    {
      name: "workflow_tool",
      description: "Run a workflow",
      parameters: Type.Object({ pipeline: Type.String() }),
      async execute(_id, params) {
        return { content: [{ type: "text", text: params.pipeline }] };
      },
    },
    { optional: true },
  );
}
```

Users enable optional tools in config:

```json5  theme={"theme":{"light":"min-light","dark":"min-dark"}}
{
  tools: { allow: ["workflow_tool"] },
}
```

* Tool names must not clash with core tools (conflicts are skipped)
* Use `optional: true` for tools with side effects or extra binary requirements
* Users can enable all tools from a plugin by adding the plugin id to `tools.allow`

## Import conventions

Always import from focused `openclaw/plugin-sdk/` paths:

```typescript  theme={"theme":{"light":"min-light","dark":"min-dark"}}
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import { createPluginRuntimeStore } from "openclaw/plugin-sdk/runtime-store";

// Wrong: monolithic root (deprecated, will be removed)
import { ... } from "openclaw/plugin-sdk";
```

For the full subpath reference, see [SDK Overview](/plugins/sdk-overview).

Within your plugin, use local barrel files (`api.ts`, `runtime-api.ts`) for
internal imports — never import your own plugin through its SDK path.

## Pre-submission checklist

**package.json** has correct `openclaw` metadata
**openclaw\.plugin.json** manifest is present and valid
Entry point uses `defineChannelPluginEntry` or `definePluginEntry`
All imports use focused `plugin-sdk/` paths
Internal imports use local modules, not SDK self-imports
Tests pass (`pnpm test -- extensions/my-plugin/`)
`pnpm check` passes (in-repo plugins)

## Beta Release Testing

1. Watch for GitHub release tags on [openclaw/openclaw](https://github.com/openclaw/openclaw/releases) and subscribe via `Watch` > `Releases`. Beta tags look like `v2026.3.N-beta.1`. You can also turn on notifications for the official OpenClaw X account [@openclaw](https://x.com/openclaw) for release announcements.
2. Test your plugin against the beta tag as soon as it appears. The window before stable is typically only a few hours.
3. Post in your plugin's thread in the `plugin-forum` Discord channel after testing with either `all good` or what broke. If you do not have a thread yet, create one.
4. If something breaks, ship a fix PR to `main` and drop the link in your thread. Blockers with a PR get merged; blockers without one might ship anyway. Maintainers watch these threads during beta testing.
5. Silence means green. If you miss the window, your fix likely lands in the next cycle.

## Next steps

    Build a messaging channel plugin

    Build a model provider plugin

    Import map and registration API reference

    TTS, search, subagent via api.runtime

    Test utilities and patterns

    Full manifest schema reference

Built with [Mintlify](https://mintlify.com).