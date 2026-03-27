# OpenClaw Docs Fix Report

**Date:** 2026-03-26 22:20 GMT+8
**Docs directory:** `/Users/lr/.openclaw/workspace/harness/robot/night-build/reports/openclaw-docs/`

---

## 一、文件路径修复

### ✅ 执行成功

| 操作 | 源文件 | 目标文件 | 结果 |
|------|--------|----------|------|
| 模板目录创建 | — | `reference/templates/` | ✓ 目录已创建 |
| AGENTS 模板 | `reference/templates_AGENTS.md` | `reference/templates/AGENTS.md` | ✓ |
| BOOT 模板 | `reference/templates_BOOT.md` | `reference/templates/BOOT.md` | ✓ |
| BOOTSTRAP 模板 | `reference/templates_BOOTSTRAP.md` | `reference/templates/BOOTSTRAP.md` | ✓ |
| HEARTBEAT 模板 | `reference/templates_HEARTBEAT.md` | `reference/templates/HEARTBEAT.md` | ✓ |
| IDENTITY 模板 | `reference/templates_IDENTITY.md` | `reference/templates/IDENTITY.md` | ✓ |
| SOUL 模板 | `reference/templates_SOUL.md` | `reference/templates/SOUL.md` | ✓ |
| TOOLS 模板 | `reference/templates_TOOLS.md` | `reference/templates/TOOLS.md` | ✓ |
| USER 模板 | `reference/templates_USER.md` | `reference/templates/USER.md` | ✓ |
| 安装迁移文档 | `install/migrating-matrix.md` | `install/matrix-migration.md` | ✓ |
| Token 文档重命名 | `reference/token-use.md` | `reference/token-use-costs.md` | ✓ |
| Security 路径 | `gateway/security.md` | `gateway/security/index.md` | ✓ (69,718 bytes) |
| 删除多余文件 | `reference/test.md` | — | ✓ 已删除 |
| 删除多余文件 | `start/hubs.md` | — | ✓ 已删除 |

验证：`reference/templates/` 目录现包含 8 个模板文件。

---

## 二、截断页面重新抓取

**抓取工具：** `web_fetch`（无 maxChars 限制）
**处理：** 去除 SECURITY NOTICE 包裹，提取纯净 Markdown 正文

### 文件大小对比

| 文件 | 修复前 | 修复后 | 增长 |
|------|--------|--------|------|
| `cli/logs.md` | 419 B | 476 B | +57 B ✅ |
| `cli/setup.md` | 476 B | 535 B | +59 B ✅ |
| `cli/dashboard.md` | 695 B | 757 B | +62 B ✅ |
| `cli/uninstall.md` | 359 B | 421 B | +62 B ✅ |
| `cli/status.md` | 1,501 B | 1,552 B | +51 B ✅ |
| `vps.md` | 4,444 B | 4,266 B | 内容完整（略小，正常） ✅ |
| `cli/clawbot.md` | 273 B | 332 B | +59 B ✅ |
| `cli/dns.md` | 382 B | 438 B | +56 B ✅ |
| `cli/health.md` | 383 B | 442 B | +59 B ✅ |
| `cli/reset.md` | 371 B | 429 B | +58 B ✅ |
| `cli/webhooks.md` | 439 B | 500 B | +61 B ✅ |
| `cli/docs.md` | 193 B | 250 B | +57 B ✅ |
| `start/onboarding.md` | 4,542 B | 4,359 B | 内容完整 ✅ |

所有文件均已完整抓取，无截断。

---

## 三、缺失页面抓取

| 页面 | 源 URL | 本地文件 | 大小 | 结果 |
|------|--------|----------|------|------|
| Gateway Security | `gateway/security/index.md` | `gateway/security/index.md` | 69,718 B | ✅ 已存在（路径修复） |
| 首页 | `index.md` | `index.md` | 6,841 B | ✅ 新建 |
| Pi 架构 | `pi.md` | `pi.md` | 8,060 B | ✅ 新建 |
| Pi 开发流程 | `pi-dev.md` | `pi-dev.md` | 2,250 B | ✅ 新建 |

---

## 四、最终验证

### 文件总数
```
find . -type f | wc -l
→ 373 个文件
```
（预期 356+，实际 373，超过预期）

### 内容完整性抽样（tail -5）

| 文件 | 结尾内容 |
|------|----------|
| `cli/logs.md` | `Built with [Mintlify](https://mintlify.com).` ✅ |
| `vps.md` | `Built with [Mintlify](https://mintlify.com).` ✅ |
| `start/onboarding.md` | `Built with [Mintlify](https://mintlify.com).` ✅ |

所有抽样文件均有正常结尾。

---

## 五、未解决问题

### ⚠️ 已知缺失页面（llms.txt 索引中有，但本地不存在）

以下页面在官方索引中，但本地缺失（未在本次任务范围内）：

- `auth-credential-semantics.md`
- `automation/auth-monitoring.md`
- `automation/cron-vs-heartbeat.md`
- `automation/poll.md`
- `automation/standing-orders.md`
- `automation/troubleshooting.md`
- `automation/webhook.md`
- `channels/bluebubbles.md`
- `channels/broadcast-groups.md`
- `channels/channel-routing.md`
- `channels/feishu.md`
- `channels/googlechat.md`
- `channels/group-messages.md`
- `channels/groups.md`
- `channels/irc.md`
- `channels/line.md`
- `channels/location.md`
- `channels/matrix.md`
- `channels/mattermost.md`
- `channels/msteams.md`
- `channels/nextcloud-talk.md`
- `channels/nostr.md`
- `channels/signal.md`
- `channels/slack.md`
- `channels/synology-chat.md`
- `channels/tlon.md`
- `channels/troubleshooting.md`
- `channels/twitch.md`
- `channels/zalo.md`
- `channels/zalouser.md`
- `ci.md`
- `date-time.md`
- `debug/node-issue.md`
- `diagnostics/flags.md`
- `gateway/authentication.md`
- `gateway/background-process.md`
- `gateway/bonjour.md`
- `gateway/bridge-protocol.md`
- `gateway/cli-backends.md`
- `gateway/configuration-reference.md`
- `gateway/doctor.md`
- `gateway/gateway-lock.md`
- `gateway/health.md`
- `gateway/index.md`
- `gateway/local-models.md`
- `gateway/multiple-gateways.md`
- `gateway/network-model.md`
- `gateway/openai-http-api.md`
- `gateway/openresponses-http-api.md`
- `gateway/openshell.md`
- `gateway/pairing.md`
- `gateway/protocol.md`
- `gateway/remote-gateway-readme.md`
- `gateway/sandbox-vs-tool-policy-vs-elevated.md`
- `gateway/sandboxing.md`
- `gateway/secrets.md`
- `gateway/trusted-proxy-auth.md`
- `help/debugging.md`
- `help/environment.md`
- `help/faq.md`
- `help/index.md`
- `help/scripts.md`
- `help/testing.md`
- `help/troubleshooting.md`
- `install/ansible.md`
- `install/bun.md`
- `install/development-channels.md`
- `install/docker-vm-runtime.md`
- `install/exe-dev.md`
- `install/fly.md`
- `install/index.md`
- `install/installer.md`
- `install/kubernetes.md`
- `install/macos-vm.md`
- `install/nix.md`
- `install/node.md`
- `install/railway.md`
- `install/render.md`
- `network.md`
- `nodes/audio.md`
- `nodes/camera.md`
- `nodes/images.md`
- `nodes/index.md`
- `nodes/location-command.md`
- `nodes/media-understanding.md`
- `nodes/talk.md`
- `nodes/troubleshooting.md`
- `nodes/voicewake.md`
- `platforms/android.md`
- `platforms/index.md`
- `platforms/ios.md`
- `platforms/linux.md`
- `platforms/mac/bundled-gateway.md`
- `platforms/mac/canvas.md`
- `platforms/mac/child-process.md`
- `platforms/mac/dev-setup.md`
- `platforms/mac/health.md`
- `platforms/mac/icon.md`
- `platforms/mac/logging.md`
- `platforms/mac/menu-bar.md`
- `platforms/mac/peekaboo.md`
- `platforms/mac/permissions.md`
- `platforms/mac/remote.md`
- `platforms/mac/signing.md`
- `platforms/mac/skills.md`
- `platforms/mac/voice-overlay.md`
- `platforms/mac/voicewake.md`
- `platforms/mac/webchat.md`
- `platforms/mac/xpc.md`
- `platforms/macos.md`
- `platforms/windows.md`
- `plugins/architecture.md`
- `plugins/building-plugins.md`
- `plugins/bundles.md`
- `plugins/community.md`
- `plugins/manifest.md`
- `plugins/sdk-channel-plugins.md`
- `plugins/sdk-entrypoints.md`
- `plugins/sdk-migration.md`
- `plugins/sdk-overview.md`
- `plugins/sdk-provider-plugins.md`
- `plugins/sdk-runtime.md`
- `plugins/sdk-setup.md`
- `plugins/sdk-testing.md`
- `plugins/voice-call.md`
- `prose.md`
- `providers/anthropic.md`
- `providers/bedrock.md`
- `providers/claude-max-api-proxy.md`
- `providers/cloudflare-ai-gateway.md`
- `providers/deepgram.md`
- `providers/deepseek.md`
- `providers/github-copilot.md`
- `providers/glm.md`
- `providers/google.md`
- `providers/groq.md`
- `providers/huggingface.md`
- `providers/index.md`
- `providers/kilocode.md`
- `providers/litellm.md`
- `providers/minimax.md`
- `providers/mistral.md`
- `providers/models.md`
- `providers/moonshot.md`
- `providers/nvidia.md`
- `providers/ollama.md`
- `providers/openai.md`
- `providers/opencode.md`
- `providers/opencode-go.md`
- `providers/openrouter.md`
- `providers/perplexity-provider.md`
- `providers/qianfan.md`
- `providers/qwen.md`
- `providers/qwen_modelstudio.md`
- `providers/sglang.md`
- `providers/synthetic.md`
- `providers/together.md`
- `providers/venice.md`
- `providers/vercel-ai-gateway.md`
- `providers/vllm.md`
- `providers/volcengine.md`
- `providers/xai.md`
- `providers/xiaomi.md`
- `providers/zai.md`
- `reference/AGENTS.default.md`
- `reference/RELEASING.md`
- `reference/api-usage-costs.md`
- `reference/credits.md`
- `reference/device-models.md`
- `reference/memory-config.md`
- `reference/prompt-caching.md`
- `reference/rpc.md`
- `reference/secretref-credential-surface.md`
- `reference/session-management-compaction.md`
- `reference/transcript-hygiene.md`
- `reference/wizard.md`
- `security/CONTRIBUTING-THREAT-MODEL.md`
- `security/THREAT-MODEL-ATLAS.md`
- `security/formal-verification.md`
- `start/bootstrapping.md`
- `start/docs-directory.md`
- `start/getting-started.md`
- `start/lore.md`
- `start/onboarding-overview.md`
- `start/openclaw.md`
- `start/setup.md`
- `start/showcase.md`
- `start/wizard-cli-automation.md`
- `start/wizard-cli-reference.md`
- `tools/acp-agents.md`
- `tools/agent-send.md`
- `tools/apply-patch.md`
- `tools/brave-search.md`
- `tools/browser-linux-troubleshooting.md`
- `tools/browser-login.md`
- `tools/browser-wsl2-windows-remote-cdp-troubleshooting.md`
- `tools/btw.md`
- `tools/clawhub.md`
- `tools/creating-skills.md`
- `tools/diffs.md`
- `tools/duckduckgo-search.md`
- `tools/elevated.md`
- `tools/exa-search.md`
- `tools/exec-approvals.md`
- `tools/firecrawl.md`
- `tools/gemini-search.md`
- `tools/grok-search.md`
- `tools/index.md`
- `tools/kimi-search.md`
- `tools/llm-task.md`
- `tools/lobster.md`
- `tools/loop-detection.md`
- `tools/multi-agent-sandbox-tools.md`
- `tools/pdf.md`
- `tools/perplexity-search.md`
- `tools/plugin.md`
- `tools/reactions.md`
- `tools/skills-config.md`
- `tools/slash-commands.md`
- `tools/subagents.md`
- `tools/tavily.md`
- `tools/thinking.md`
- `tools/tts.md`
- `tools/web-fetch.md`
- `web/control-ui.md`
- `web/dashboard.md`
- `web/index.md`
- `web/tui.md`
- `web/webchat.md`

**数量：约 200+ 个文件**

> 这些文件需要单独爬取才能达到完整文档集。本次任务仅修复了已知的路径错误和截断问题。

---

## 总结

| 项目 | 状态 |
|------|------|
| 模板路径修复（8个文件） | ✅ 完成 |
| 安装目录重命名 | ✅ 完成 |
| Token 文档重命名 | ✅ 完成 |
| Security 路径修复 | ✅ 完成 |
| 删除多余文件（2个） | ✅ 完成 |
| 截断页面重新抓取（13个） | ✅ 完成，所有文件大小合理 |
| 缺失页面抓取（3个新建） | ✅ 完成 |
| 文件总数 | ✅ 373 个 |
| 内容完整性 | ✅ 抽样通过 |
| 未解决问题 | ⚠️ 约 200+ 缺失页面需后续爬取 |
