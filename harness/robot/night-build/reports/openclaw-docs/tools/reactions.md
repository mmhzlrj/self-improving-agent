> ## Documentation Index
> Fetch the complete documentation index at: https://docs.openclaw.ai/llms.txt
> Use this file to discover all available pages before exploring further.

# Reactions

# Reactions

The agent can add and remove emoji reactions on messages using the `message`
tool with the `react` action. Reaction behavior varies by channel.

## How it works

```json  theme={"theme":{"light":"min-light","dark":"min-dark"}}
{
  "action": "react",
  "messageId": "msg-123",
  "emoji": "thumbsup"
}
```

* `emoji` is required when adding a reaction.
* Set `emoji` to an empty string (`""`) to remove the bot's reaction(s).
* Set `remove: true` to remove a specific emoji (requires non-empty `emoji`).

## Channel behavior

    * Empty `emoji` removes all of the bot's reactions on the message.
    * `remove: true` removes just the specified emoji.

    * Empty `emoji` removes the app's reactions on the message.
    * `remove: true` removes just the specified emoji.

    * Empty `emoji` removes the bot's reactions.
    * `remove: true` also removes reactions but still requires a non-empty `emoji` for tool validation.

    * Empty `emoji` removes the bot reaction.
    * `remove: true` maps to empty emoji internally (still requires `emoji` in the tool call).

    * Requires non-empty `emoji`.
    * `remove: true` removes that specific emoji reaction.

    * Inbound reaction notifications are controlled by `channels.signal.reactionNotifications`: `"off"` disables them, `"own"` (default) emits events when users react to bot messages, and `"all"` emits events for all reactions.

## Related

* [Agent Send](/tools/agent-send) — the `message` tool that includes `react`
* [Channels](/channels) — channel-specific configuration

Built with [Mintlify](https://mintlify.com).