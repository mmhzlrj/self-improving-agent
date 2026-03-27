> ## Documentation Index
> Fetch the complete documentation index at: https://docs.openclaw.ai/llms.txt
> Use this file to discover all available pages before exploring further.

# Creating Skills

# Creating Skills

Skills teach the agent how and when to use tools. Each skill is a directory
containing a `SKILL.md` file with YAML frontmatter and markdown instructions.

For how skills are loaded and prioritized, see [Skills](/tools/skills).

## Create your first skill

    Skills live in your workspace. Create a new folder:

    ```bash  theme={"theme":{"light":"min-light","dark":"min-dark"}}
    mkdir -p ~/.openclaw/workspace/skills/hello-world
    ```

    Create `SKILL.md` inside that directory. The frontmatter defines metadata,
    and the markdown body contains instructions for the agent.

    ```markdown  theme={"theme":{"light":"min-light","dark":"min-dark"}}
    ---
    name: hello_world
    description: A simple skill that says hello.
    ---

    # Hello World Skill

    When the user asks for a greeting, use the `echo` tool to say
    "Hello from your custom skill!".
    ```

    You can define custom tool schemas in the frontmatter or instruct the agent
    to use existing system tools (like `exec` or `browser`). Skills can also
    ship inside plugins alongside the tools they document.

    Start a new session so OpenClaw picks up the skill:

    ```bash  theme={"theme":{"light":"min-light","dark":"min-dark"}}
    # From chat
    /new

    # Or restart the gateway
    openclaw gateway restart
    ```

    Verify the skill loaded:

    ```bash  theme={"theme":{"light":"min-light","dark":"min-dark"}}
    openclaw skills list
    ```

    Send a message that should trigger the skill:

    ```bash  theme={"theme":{"light":"min-light","dark":"min-dark"}}
    openclaw agent --message "give me a greeting"
    ```

    Or just chat with the agent and ask for a greeting.

## Skill metadata reference

The YAML frontmatter supports these fields:

| Field                               | Required | Description                                 |
| ----------------------------------- | -------- | ------------------------------------------- |
| `name`                              | Yes      | Unique identifier (snake\_case)             |
| `description`                       | Yes      | One-line description shown to the agent     |
| `metadata.openclaw.os`              | No       | OS filter (`["darwin"]`, `["linux"]`, etc.) |
| `metadata.openclaw.requires.bins`   | No       | Required binaries on PATH                   |
| `metadata.openclaw.requires.config` | No       | Required config keys                        |

## Best practices

* **Be concise** — instruct the model on *what* to do, not how to be an AI
* **Safety first** — if your skill uses `exec`, ensure prompts don't allow arbitrary command injection from untrusted input
* **Test locally** — use `openclaw agent --message "..."` to test before sharing
* **Use ClawHub** — browse and contribute skills at [ClawHub](https://clawhub.com)

## Where skills live

| Location                        | Precedence | Scope                 |
| ------------------------------- | ---------- | --------------------- |
| `\/skills/`         | Highest    | Per-agent             |
| `~/.openclaw/skills/`           | Medium     | Shared (all agents)   |
| Bundled (shipped with OpenClaw) | Lowest     | Global                |
| `skills.load.extraDirs`         | Lowest     | Custom shared folders |

## Related

* [Skills reference](/tools/skills) — loading, precedence, and gating rules
* [Skills config](/tools/skills-config) — `skills.*` config schema
* [ClawHub](/tools/clawhub) — public skill registry
* [Building Plugins](/plugins/building-plugins) — plugins can ship skills

Built with [Mintlify](https://mintlify.com).