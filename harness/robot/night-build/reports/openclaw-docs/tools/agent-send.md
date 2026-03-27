> ## Documentation Index
> Fetch the complete documentation index at: https://docs.openclaw.ai/llms.txt
> Use this file to discover all available pages before exploring further.

# Agent Send

# Agent Send

`openclaw agent` runs a single agent turn from the command line without needing
an inbound chat message. Use it for scripted workflows, testing, and
programmatic delivery.

## Quick start

    ```bash  theme={"theme":{"light":"min-light","dark":"min-dark"}}
    openclaw agent --message "What is the weather today?"
    ```

    This sends the message through the Gateway and prints the reply.

    ```bash  theme={"theme":{"light":"min-light","dark":"min-dark"}}
    # Target a specific agent
    openclaw agent --agent ops --message "Summarize logs"

    # Target a phone number (derives session key)
    openclaw agent --to +15555550123 --message "Status update"

    # Reuse an existing session
    openclaw agent --session-id abc123 --message "Continue the task"
    ```

    ```bash  theme={"theme":{"light":"min-light","dark":"min-dark"}}
    # Deliver to WhatsApp (default channel)
    openclaw agent --to +15555550123 --message "Report ready" --deliver

    # Deliver to Slack
    openclaw agent --agent ops --message "Generate report" \
      --deliver --reply-channel slack --reply-to "#reports"
    ```

## Flags

| Flag                          | Description                                                 |
| ----------------------------- | ----------------------------------------------------------- |
| `--message \`          | Message to send (required)                                  |
| `--to \`               | Derive session key from a target (phone, chat id)           |
| `--agent \`              | Target a configured agent (uses its `main` session)         |
| `--session-id \`         | Reuse an existing session by id                             |
| `--local`                     | Force local embedded runtime (skip Gateway)                 |
| `--deliver`                   | Send the reply to a chat channel                            |
| `--channel \`          | Delivery channel (whatsapp, telegram, discord, slack, etc.) |
| `--reply-to \`       | Delivery target override                                    |
| `--reply-channel \`    | Delivery channel override                                   |
| `--reply-account \`      | Delivery account id override                                |
| `--thinking \`        | Set thinking level (off, minimal, low, medium, high, xhigh) |
| `--verbose \` | Set verbose level                                           |
| `--timeout \`       | Override agent timeout                                      |
| `--json`                      | Output structured JSON                                      |

## Behavior

* By default, the CLI goes **through the Gateway**. Add `--local` to force the
  embedded runtime on the current machine.
* If the Gateway is unreachable, the CLI **falls back** to the local embedded run.
* Session selection: `--to` derives the session key (group/channel targets
  preserve isolation; direct chats collapse to `main`).
* Thinking and verbose flags persist into the session store.
* Output: plain text by default, or `--json` for structured payload + metadata.

## Examples

```bash  theme={"theme":{"light":"min-light","dark":"min-dark"}}
# Simple turn with JSON output
openclaw agent --to +15555550123 --message "Trace logs" --verbose on --json

# Turn with thinking level
openclaw agent --session-id 1234 --message "Summarize inbox" --thinking medium

# Deliver to a different channel than the session
openclaw agent --agent ops --message "Alert" --deliver --reply-channel telegram --reply-to "@admin"
```

## Related

* [Agent CLI reference](/cli/agent)
* [Sub-agents](/tools/subagents) — background sub-agent spawning
* [Sessions](/concepts/session) — how session keys work

Built with [Mintlify](https://mintlify.com).