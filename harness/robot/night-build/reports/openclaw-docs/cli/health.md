# health

# `openclaw health`

Fetch health from the running Gateway.

```bash  theme={"theme":{"light":"min-light","dark":"min-dark"}}
openclaw health
openclaw health --json
openclaw health --verbose
```

Notes:

* `--verbose` runs live probes and prints per-account timings when multiple accounts are configured.
* Output includes per-agent session stores when multiple agents are configured.


Built with [Mintlify](https://mintlify.com).
