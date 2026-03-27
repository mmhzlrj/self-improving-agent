# `openclaw skills`

Inspect local skills and install/update skills from ClawHub.

Related:

* Skills system: [Skills](/tools/skills)
* Skills config: [Skills config](/tools/skills-config)
* ClawHub installs: [ClawHub](/tools/clawhub)

## Commands

```bash theme={"theme":{"light":"min-light","dark":"min-dark"}}
openclaw skills search "calendar"
openclaw skills install <slug>
openclaw skills install <slug> --version <version>
openclaw skills update <slug>
openclaw skills update --all
openclaw skills list
openclaw skills list --eligible
openclaw skills info <name>
openclaw skills check
```

`search`/`install`/`update` use ClawHub directly and install into the active
workspace `skills/` directory. `list`/`info`/`check` still inspect the local
skills visible to the current workspace and config.