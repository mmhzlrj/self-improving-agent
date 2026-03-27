#!/bin/bash
# Batch 3 Fetch Script - Tools/Plugins/Providers/Security/Help/Templates/Other

BASE_DIR="/Users/lr/.openclaw/workspace/harness/robot/night-build/reports/openclaw-docs"
DOCS_URL="https://docs.openclaw.ai"

# Pages for each category
declare -A TOOLS_PAGES=(
  ["tools/index"]="tools/index.md"
  ["tools/skills"]="tools/skills.md"
  ["tools/skills-config"]="tools/skills-config.md"
  ["tools/creating-skills"]="tools/creating-skills.md"
  ["tools/slash-commands"]="tools/slash-commands.md"
  ["tools/subagents"]="tools/subagents.md"
  ["tools/multi-agent-sandbox-tools"]="tools/multi-agent-sandbox-tools.md"
  ["tools/acp-agents"]="tools/acp-agents.md"
  ["tools/agent-send"]="tools/agent-send.md"
  ["tools/llm-task"]="tools/llm-task.md"
  ["tools/exec"]="tools/exec.md"
  ["tools/exec-approvals"]="tools/exec-approvals.md"
  ["tools/elevated"]="tools/elevated.md"
  ["tools/browser"]="tools/browser.md"
  ["tools/browser-login"]="tools/browser-login.md"
  ["tools/browser-linux-troubleshooting"]="tools/browser-linux-troubleshooting.md"
  ["tools/browser-wsl2-windows-remote-cdp-troubleshooting"]="tools/browser-wsl2-windows-remote-cdp-troubleshooting.md"
  ["tools/web-fetch"]="tools/web-fetch.md"
  ["tools/web"]="tools/web.md"
  ["tools/brave-search"]="tools/brave-search.md"
  ["tools/duckduckgo-search"]="tools/duckduckgo-search.md"
  ["tools/tavily"]="tools/tavily.md"
  ["tools/exa-search"]="tools/exa-search.md"
  ["tools/firecrawl"]="tools/firecrawl.md"
  ["tools/kimi-search"]="tools/kimi-search.md"
  ["tools/gemini-search"]="tools/gemini-search.md"
  ["tools/grok-search"]="tools/grok-search.md"
  ["tools/perplexity-search"]="tools/perplexity-search.md"
  ["tools/thinking"]="tools/thinking.md"
  ["tools/tts"]="tools/tts.md"
  ["tools/pdf"]="tools/pdf.md"
  ["tools/apply-patch"]="tools/apply-patch.md"
  ["tools/diffs"]="tools/diffs.md"
  ["tools/reactions"]="tools/reactions.md"
  ["tools/btw"]="tools/btw.md"
  ["tools/loop-detection"]="tools/loop-detection.md"
  ["tools/clawhub"]="tools/clawhub.md"
  ["tools/lobster"]="tools/lobster.md"
  ["tools/plugin"]="tools/plugin.md"
)

declare -A PLUGINS_PAGES=(
  ["plugins/sdk-overview"]="plugins/sdk-overview.md"
  ["plugins/architecture"]="plugins/architecture.md"
  ["plugins/building-plugins"]="plugins/building-plugins.md"
  ["plugins/manifest"]="plugins/manifest.md"
  ["plugins/bundles"]="plugins/bundles.md"
  ["plugins/sdk-setup"]="plugins/sdk-setup.md"
  ["plugins/sdk-entrypoints"]="plugins/sdk-entrypoints.md"
  ["plugins/sdk-channel-plugins"]="plugins/sdk-channel-plugins.md"
  ["plugins/sdk-provider-plugins"]="plugins/sdk-provider-plugins.md"
  ["plugins/sdk-runtime"]="plugins/sdk-runtime.md"
  ["plugins/sdk-migration"]="plugins/sdk-migration.md"
  ["plugins/sdk-testing"]="plugins/sdk-testing.md"
  ["plugins/voice-call"]="plugins/voice-call.md"
  ["plugins/community"]="plugins/community.md"
)

declare -A PROVIDERS_PAGES=(
  ["providers/index"]="providers/index.md"
  ["providers/models"]="providers/models.md"
  ["providers/openai"]="providers/openai.md"
  ["providers/anthropic"]="providers/anthropic.md"
  ["providers/google"]="providers/google.md"
  ["providers/deepseek"]="providers/deepseek.md"
  ["providers/glm"]="providers/glm.md"
  ["providers/qwen"]="providers/qwen.md"
  ["providers/qwen_modelstudio"]="providers/qwen_modelstudio.md"
  ["providers/moonshot"]="providers/moonshot.md"
  ["providers/minimax"]="providers/minimax.md"
  ["providers/mistral"]="providers/mistral.md"
  ["providers/groq"]="providers/groq.md"
  ["providers/ollama"]="providers/ollama.md"
  ["providers/vllm"]="providers/vllm.md"
  ["providers/sglang"]="providers/sglang.md"
  ["providers/together"]="providers/together.md"
  ["providers/perplexity-provider"]="providers/perplexity-provider.md"
  ["providers/openrouter"]="providers/openrouter.md"
  ["providers/litellm"]="providers/litellm.md"
  ["providers/cloudflare-ai-gateway"]="providers/cloudflare-ai-gateway.md"
  ["providers/bedrock"]="providers/bedrock.md"
  ["providers/nvidia"]="providers/nvidia.md"
  ["providers/venice"]="providers/venice.md"
  ["providers/huggingface"]="providers/huggingface.md"
  ["providers/github-copilot"]="providers/github-copilot.md"
  ["providers/claude-max-api-proxy"]="providers/claude-max-api-proxy.md"
  ["providers/opencode"]="providers/opencode.md"
  ["providers/opencode-go"]="providers/opencode-go.md"
  ["providers/kilocode"]="providers/kilocode.md"
  ["providers/synthetic"]="providers/synthetic.md"
  ["providers/xai"]="providers/xai.md"
  ["providers/xiaomi"]="providers/xiaomi.md"
  ["providers/volcengine"]="providers/volcengine.md"
  ["providers/zai"]="providers/zai.md"
  ["providers/deepgram"]="providers/deepgram.md"
  ["providers/qianfan"]="providers/qianfan.md"
)

declare -A SECURITY_PAGES=(
  ["security/THREAT-MODEL-ATLAS"]="security/THREAT-MODEL-ATLAS.md"
  ["security/CONTRIBUTING-THREAT-MODEL"]="security/CONTRIBUTING-THREAT-MODEL.md"
  ["security/formal-verification"]="security/formal-verification.md"
)

declare -A HELP_PAGES=(
  ["help/index"]="help/index.md"
  ["help/troubleshooting"]="help/troubleshooting.md"
  ["help/faq"]="help/faq.md"
  ["help/debugging"]="help/debugging.md"
  ["help/environment"]="help/environment.md"
  ["help/scripts"]="help/scripts.md"
  ["help/testing"]="help/testing.md"
)

declare -A OTHER_PAGES=(
  ["prose"]="prose.md"
)

declare -A DIAGNOSTICS_PAGES=(
  ["diagnostics/flags"]="diagnostics/flags.md"
  ["debug/node-issue"]="debug/node-issue.md"
  ["ci"]="ci.md"
)

# Merge all pages
declare -A ALL_PAGES=()
for key in "${!TOOLS_PAGES[@]}"; do ALL_PAGES[$key]="${TOOLS_PAGES[$key]}"; done
for key in "${!PLUGINS_PAGES[@]}"; do ALL_PAGES[$key]="${PLUGINS_PAGES[$key]}"; done
for key in "${!PROVIDERS_PAGES[@]}"; do ALL_PAGES[$key]="${PROVIDERS_PAGES[$key]}"; done
for key in "${!SECURITY_PAGES[@]}"; do ALL_PAGES[$key]="${SECURITY_PAGES[$key]}"; done
for key in "${!HELP_PAGES[@]}"; do ALL_PAGES[$key]="${HELP_PAGES[$key]}"; done
for key in "${!OTHER_PAGES[@]}"; do ALL_PAGES[$key]="${OTHER_PAGES[$key]}"; done
for key in "${!DIAGNOSTICS_PAGES[@]}"; do ALL_PAGES[$key]="${DIAGNOSTICS_PAGES[$key]}"; done

echo "Total pages to fetch: ${#ALL_PAGES[@]}"
for path in "${!ALL_PAGES[@]}"; do
  echo "$path -> ${ALL_PAGES[$path]}"
done
