# Pi Integration Architecture

# Pi Integration Architecture

This document describes how OpenClaw integrates with the Pi CLI agent.

## Overview

OpenClaw embeds the Pi agent via a Node.js SDK wrapper. The Pi agent runs as a
subprocess and communicates over RPC (stdin/stdout JSON-RPC). OpenClaw adds:

* Multi-channel routing (WhatsApp, Telegram, etc.)
* Session management
* Tool adapters
* Extension loading
* Auth credential management
* Model failover

## Source Layout

```
openclaw/pi/
├── src/
│   ├── pi-agent-session.ts      # Session manager wrapping pi-agent-core
│   ├── pi-auth-json.ts          # Auth credential file management
│   ├── pi-embedded-agent.ts     # Main embedded agent entry point
│   ├── pi-embedded-helpers.ts   # Provider error classification
│   ├── pi-embedded-runner.ts     # Streaming runner (provider abstraction)
│   ├── pi-embedded-subscribe.ts # Subscribe-based event handler
│   ├── pi-settings.ts           # Settings loader
│   ├── pi-tools.ts             # Tool adapters (read, exec, browser, etc.)
│   ├── pi-tool-definition-adapter.ts  # Tool schema conversion
│   └── pi-extensions/           # Extension loading for pi
│       ├── mod.ts
│       └── loader.ts
└── package.json
```

## Session Management

`pi-agent-session.ts` wraps `pi-agent-core`'s `SessionManager`:

```typescript  theme={"theme":{"light":"min-light","dark":"min-dark"}}
// Guarded session manager with error classification
const sessionManager = guardSessionManager(
  createSessionManager({ workspace }),
  {
    onToolCall: (tool) => logger.debug(`[pi] tool call: ${tool.name}`),
    onAssistant: (msg) => logger.trace(`[pi] assistant: ${msg.slice(0, 100)}`),
  }
);
```

The guard layer adds:
* Error classification (context overflow, compaction failure, auth errors, rate limits)
* Thinking level fallback
* Tracing hooks

## Agent Lifecycle

```typescript  theme={"theme":{"light":"min-light","dark":"min-dark"}}
const agent = await createEmbeddedPiAgent({
  agentId,
  workspace: resolvedWorkspace,
  config: params.config,
  providers: ...,
  extensions: ...,
  toolCallHandler: ...,
});

await agent.start();
```

## Tool Adapters

OpenClaw adapts its own tool suite to match pi-agent-core's tool interface:

| OpenClaw Tool | Pi Tool | Notes |
|---|---|---|
| `read` | `Read` | File reading |
| `edit` | `Edit` | File editing |
| `exec` | `Exec` | Shell commands |
| `browser` | `Browser` | Web browsing |
| `webFetch` | `WebFetch` | URL content fetch |
| `webSearch` | `WebSearch` | Web search |

The `pi-tools.ts` module provides `createPiReadTool()`, `createPiExecTool()`, etc.
Each adapter maps pi's tool call format to OpenClaw's internal tool invocations.

## Provider Abstraction

`pi-embedded-runner.ts` provides the provider-agnostic streaming interface:

```typescript  theme={"theme":{"light":"min-light","dark":"min-dark"}}
const runner = createEmbeddedPiRunner({
  agentId,
  workspace,
  config,
  providers,
  extensions,
  toolCallHandler,
});
```

Provider implementations handle:
* Model-specific parameter mapping (Anthropic, Google, OpenAI, etc.)
* Thinking level translation
* Tool schema sanitization
* Auth credential injection

## Block Reply Handling

For subscribe-based (non-streaming) mode:

```typescript  theme={"theme":{"light":"min-light","dark":"min-dark"}}
agent.on('blockReply', ({ id, role, content }) => {
  // Process block-level reply
});
```

## Error Classification

`pi-embedded-helpers.ts` classifies errors for appropriate handling:

```typescript  theme={"theme":{"light":"min-light","dark":"min-dark"}}
isContextOverflowError(errorText)     // Context too large
isCompactionFailureError(errorText)   // Compaction failed
isAuthAssistantError(lastAssistant)   // Auth failure
isRateLimitAssistantError(...)        // Rate limited
isFailoverAssistantError(...)         // Should failover
classifyFailoverReason(errorText)     // "auth" | "rate_limit" | "quota" | "timeout" | ...
```

### Thinking Level Fallback

If a thinking level is unsupported, it falls back:

```typescript  theme={"theme":{"light":"min-light","dark":"min-dark"}}
const fallbackThinking = pickFallbackThinkingLevel({
  message: errorText,
  attempted: attemptedThinking,
});
if (fallbackThinking) {
  thinkLevel = fallbackThinking;
  continue;
}
```

## Sandbox Integration

When sandbox mode is enabled, tools and paths are constrained:

```typescript  theme={"theme":{"light":"min-light","dark":"min-dark"}}
const sandbox = await resolveSandboxContext({
  config: params.config,
  sessionKey: sandboxSessionKey,
  workspaceDir: resolvedWorkspace,
});

if (sandboxRoot) {
  // Use sandboxed read/edit/write tools
  // Exec runs in container
  // Browser uses bridge URL
}
```

## Provider-Specific Handling

### Anthropic

* Refusal magic string scrubbing
* Turn validation for consecutive roles
* Claude Code parameter compatibility

### Google/Gemini

* Turn ordering fixes (`applyGoogleTurnOrderingFix`)
* Tool schema sanitization (`sanitizeToolsForGoogle`)
* Session history sanitization (`sanitizeSessionHistory`)

### OpenAI

* `apply_patch` tool for Codex models
* Thinking level downgrade handling

## TUI Integration

OpenClaw also has a local TUI mode that uses pi-tui components directly:

```typescript  theme={"theme":{"light":"min-light","dark":"min-dark"}}
// src/tui/tui.ts
import { ... } from "@mariozechner/pi-tui";
```

This provides the interactive terminal experience similar to pi's native mode.

## Key Differences from Pi CLI

| Aspect          | Pi CLI                  | OpenClaw Embedded                                                                              |
| --------------- | ----------------------- | ---------------------------------------------------------------------------------------------- |
| Invocation      | `pi` command / RPC      | SDK via `createAgentSession()`                                                                 |
| Tools           | Default coding tools    | Custom OpenClaw tool suite                                                                     |
| System prompt   | AGENTS.md + prompts     | Dynamic per-channel/context                                                                    |
| Session storage | `~/.pi/agent/sessions/` | `~/.openclaw/agents/<agentId>/sessions/` (or `$OPENCLAW_STATE_DIR/agents/<agentId>/sessions/`) |
| Auth            | Single credential       | Multi-profile with rotation                                                                    |
| Extensions      | Loaded from disk        | Programmatic + disk paths                                                                      |
| Event handling  | TUI rendering           | Callback-based (onBlockReply, etc.)                                                            |

## Future Considerations

Areas for potential rework:

1. **Tool signature alignment**: Currently adapting between pi-agent-core and pi-coding-agent signatures
2. **Session manager wrapping**: `guardSessionManager` adds safety but increases complexity
3. **Extension loading**: Could use pi's `ResourceLoader` more directly
4. **Streaming handler complexity**: `subscribeEmbeddedPiSession` has grown large
5. **Provider quirks**: Many provider-specific codepaths that pi could potentially handle

## Tests

Pi integration coverage spans these suites:

* `src/agents/pi-*.test.ts`
* `src/agents/pi-auth-json.test.ts`
* `src/agents/pi-embedded-*.test.ts`
* `src/agents/pi-embedded-helpers*.test.ts`
* `src/agents/pi-embedded-runner*.test.ts`
* `src/agents/pi-embedded-runner/**/*.test.ts`
* `src/agents/pi-embedded-subscribe*.test.ts`
* `src/agents/pi-tools*.test.ts`
* `src/agents/pi-tool-definition-adapter*.test.ts`
* `src/agents/pi-settings.test.ts`
* `src/agents/pi-extensions/**/*.test.ts`

Live/opt-in:

* `src/agents/pi-embedded-runner-extraparams.live.test.ts` (enable `OPENCLAW_LIVE_TEST=1`)

For current run commands, see [Pi Development Workflow](/pi-dev).
