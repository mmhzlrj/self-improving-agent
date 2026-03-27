#!/usr/bin/env python3
"""Fetch OpenClaw docs batch 3: Tools/Plugins/Providers/Security/Help/Templates/Other"""
import subprocess
import os
import json
from pathlib import Path

BASE_DIR = Path("/Users/lr/.openclaw/workspace/harness/robot/night-build/reports/openclaw-docs")
DOCS_URL = "https://docs.openclaw.ai"

# All pages to fetch: (url_path, dest_rel_path)
PAGES = [
    # tools/ (37 pages)
    ("tools/index", "tools/index.md"),
    ("tools/skills", "tools/skills.md"),
    ("tools/skills-config", "tools/skills-config.md"),
    ("tools/creating-skills", "tools/creating-skills.md"),
    ("tools/slash-commands", "tools/slash-commands.md"),
    ("tools/subagents", "tools/subagents.md"),
    ("tools/multi-agent-sandbox-tools", "tools/multi-agent-sandbox-tools.md"),
    ("tools/acp-agents", "tools/acp-agents.md"),
    ("tools/agent-send", "tools/agent-send.md"),
    ("tools/llm-task", "tools/llm-task.md"),
    ("tools/exec", "tools/exec.md"),
    ("tools/exec-approvals", "tools/exec-approvals.md"),
    ("tools/elevated", "tools/elevated.md"),
    ("tools/browser", "tools/browser.md"),
    ("tools/browser-login", "tools/browser-login.md"),
    ("tools/browser-linux-troubleshooting", "tools/browser-linux-troubleshooting.md"),
    ("tools/browser-wsl2-windows-remote-cdp-troubleshooting", "tools/browser-wsl2-windows-remote-cdp-troubleshooting.md"),
    ("tools/web-fetch", "tools/web-fetch.md"),
    ("tools/web", "tools/web.md"),
    ("tools/brave-search", "tools/brave-search.md"),
    ("tools/duckduckgo-search", "tools/duckduckgo-search.md"),
    ("tools/tavily", "tools/tavily.md"),
    ("tools/exa-search", "tools/exa-search.md"),
    ("tools/firecrawl", "tools/firecrawl.md"),
    ("tools/kimi-search", "tools/kimi-search.md"),
    ("tools/gemini-search", "tools/gemini-search.md"),
    ("tools/grok-search", "tools/grok-search.md"),
    ("tools/perplexity-search", "tools/perplexity-search.md"),
    ("tools/thinking", "tools/thinking.md"),
    ("tools/tts", "tools/tts.md"),
    ("tools/pdf", "tools/pdf.md"),
    ("tools/apply-patch", "tools/apply-patch.md"),
    ("tools/diffs", "tools/diffs.md"),
    ("tools/reactions", "tools/reactions.md"),
    ("tools/btw", "tools/btw.md"),
    ("tools/loop-detection", "tools/loop-detection.md"),
    ("tools/clawhub", "tools/clawhub.md"),
    ("tools/lobster", "tools/lobster.md"),
    ("tools/plugin", "tools/plugin.md"),
    
    # plugins/ (14 pages)
    ("plugins/sdk-overview", "plugins/sdk-overview.md"),
    ("plugins/architecture", "plugins/architecture.md"),
    ("plugins/building-plugins", "plugins/building-plugins.md"),
    ("plugins/manifest", "plugins/manifest.md"),
    ("plugins/bundles", "plugins/bundles.md"),
    ("plugins/sdk-setup", "plugins/sdk-setup.md"),
    ("plugins/sdk-entrypoints", "plugins/sdk-entrypoints.md"),
    ("plugins/sdk-channel-plugins", "plugins/sdk-channel-plugins.md"),
    ("plugins/sdk-provider-plugins", "plugins/sdk-provider-plugins.md"),
    ("plugins/sdk-runtime", "plugins/sdk-runtime.md"),
    ("plugins/sdk-migration", "plugins/sdk-migration.md"),
    ("plugins/sdk-testing", "plugins/sdk-testing.md"),
    ("plugins/voice-call", "plugins/voice-call.md"),
    ("plugins/community", "plugins/community.md"),
    
    # providers/ (38 pages)
    ("providers/index", "providers/index.md"),
    ("providers/models", "providers/models.md"),
    ("providers/openai", "providers/openai.md"),
    ("providers/anthropic", "providers/anthropic.md"),
    ("providers/google", "providers/google.md"),
    ("providers/deepseek", "providers/deepseek.md"),
    ("providers/glm", "providers/glm.md"),
    ("providers/qwen", "providers/qwen.md"),
    ("providers/qwen_modelstudio", "providers/qwen_modelstudio.md"),
    ("providers/moonshot", "providers/moonshot.md"),
    ("providers/minimax", "providers/minimax.md"),
    ("providers/mistral", "providers/mistral.md"),
    ("providers/groq", "providers/groq.md"),
    ("providers/ollama", "providers/ollama.md"),
    ("providers/vllm", "providers/vllm.md"),
    ("providers/sglang", "providers/sglang.md"),
    ("providers/together", "providers/together.md"),
    ("providers/perplexity-provider", "providers/perplexity-provider.md"),
    ("providers/openrouter", "providers/openrouter.md"),
    ("providers/litellm", "providers/litellm.md"),
    ("providers/cloudflare-ai-gateway", "providers/cloudflare-ai-gateway.md"),
    ("providers/bedrock", "providers/bedrock.md"),
    ("providers/nvidia", "providers/nvidia.md"),
    ("providers/venice", "providers/venice.md"),
    ("providers/huggingface", "providers/huggingface.md"),
    ("providers/github-copilot", "providers/github-copilot.md"),
    ("providers/claude-max-api-proxy", "providers/claude-max-api-proxy.md"),
    ("providers/opencode", "providers/opencode.md"),
    ("providers/opencode-go", "providers/opencode-go.md"),
    ("providers/kilocode", "providers/kilocode.md"),
    ("providers/synthetic", "providers/synthetic.md"),
    ("providers/xai", "providers/xai.md"),
    ("providers/xiaomi", "providers/xiaomi.md"),
    ("providers/volcengine", "providers/volcengine.md"),
    ("providers/zai", "providers/zai.md"),
    ("providers/deepgram", "providers/deepgram.md"),
    ("providers/qianfan", "providers/qianfan.md"),
    
    # security/ (3 pages)
    ("security/THREAT-MODEL-ATLAS", "security/THREAT-MODEL-ATLAS.md"),
    ("security/CONTRIBUTING-THREAT-MODEL", "security/CONTRIBUTING-THREAT-MODEL.md"),
    ("security/formal-verification", "security/formal-verification.md"),
    
    # help/ (7 pages from TOC - but logging/network/date-time are also in help)
    ("help/index", "help/index.md"),
    ("help/troubleshooting", "help/troubleshooting.md"),
    ("help/faq", "help/faq.md"),
    ("help/debugging", "help/debugging.md"),
    ("help/environment", "help/environment.md"),
    ("help/scripts", "help/scripts.md"),
    ("help/testing", "help/testing.md"),
    ("logging", "logging.md"),
    ("network", "network.md"),
    ("date-time", "date-time.md"),
    ("diagnostics/flags", "diagnostics/flags.md"),
    ("debug/node-issue", "debug/node-issue.md"),
    ("ci", "ci.md"),
    
    # Other pages
    ("prose", "prose.md"),
]

def ensure_dir(path):
    d = BASE_DIR / path
    d.parent.mkdir(parents=True, exist_ok=True)
    return d

def fetch_page(url_path, dest_rel, retries=2):
    """Fetch a single page, return (success, size_or_error)"""
    dest = ensure_dir(dest_rel)
    url = f"{DOCS_URL}/{url_path}"
    
    for attempt in range(retries + 1):
        try:
            # Use curl to fetch the page
            result = subprocess.run(
                ["curl", "-s", "-L", "-A", "Mozilla/5.0", url],
                capture_output=True,
                text=True,
                timeout=30
            )
            content = result.stdout
            
            # Check for errors
            if result.returncode != 0:
                if attempt < retries:
                    continue
                return False, f"curl error: {result.returncode}", attempt
            
            # Check content quality
            content = content.strip()
            
            # Check for error pages
            if len(content) < 100:
                if attempt < retries:
                    continue
                return False, f"Content too short ({len(content)} bytes)", attempt
            
            # Check if it looks like an error page
            lower_content = content.lower()
            if any(x in lower_content for x in ['<title>error', '<title>404', '<title>403', 'page not found']):
                if attempt < retries:
                    continue
                return False, "Error page detected", attempt
            
            # Write content
            with open(dest, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True, len(content), attempt
            
        except subprocess.TimeoutExpired:
            if attempt < retries:
                continue
            return False, "Timeout", attempt
        except Exception as e:
            if attempt < retries:
                continue
            return False, str(e), attempt
    
    return False, "Max retries exceeded", retries

def verify_file(path):
    """Verify file has substantial content"""
    try:
        result = subprocess.run(
            ["wc", "-c", str(BASE_DIR / path)],
            capture_output=True,
            text=True
        )
        parts = result.stdout.strip().split()
        if parts:
            return int(parts[0])
    except:
        pass
    return 0

def main():
    print(f"Fetching {len(PAGES)} pages from OpenClaw docs...")
    print(f"Base URL: {DOCS_URL}")
    print(f"Destination: {BASE_DIR}")
    print("-" * 60)
    
    results = {
        "success": [],
        "failed": [],
        "retry": []  # pages that needed retry
    }
    
    for i, (url_path, dest_rel) in enumerate(PAGES):
        print(f"[{i+1}/{len(PAGES)}] Fetching {url_path}...", end=" ", flush=True)
        
        success, result, attempt = fetch_page(url_path, dest_rel)
        
        if success:
            size = verify_file(dest_rel)
            print(f"OK ({size} bytes)")
            results["success"].append({
                "path": dest_rel,
                "size": size,
                "attempts": attempt + 1
            })
        else:
            print(f"FAILED ({result})")
            results["failed"].append({
                "path": dest_rel,
                "url": f"{DOCS_URL}/{url_path}",
                "error": result,
                "attempts": attempt + 1
            })
            if attempt > 0:
                results["retry"].append(dest_rel)
    
    print("-" * 60)
    print(f"Success: {len(results['success'])}")
    print(f"Failed: {len(results['failed'])}")
    print(f"Needed retry: {len(results['retry'])}")
    
    # Write verification report
    report = []
    report.append("# Batch 3 Verification Report")
    report.append("")
    report.append("## Summary")
    report.append(f"- Total pages: {len(PAGES)}")
    report.append(f"- Success: {len(results['success'])}")
    report.append(f"- Failed: {len(results['failed'])}")
    report.append(f"- Needed retry: {len(results['retry'])}")
    report.append("")
    
    if results["failed"]:
        report.append("## Failed Pages")
        for item in results["failed"]:
            report.append(f"- `{item['path']}`")
            report.append(f"  - URL: {item['url']}")
            report.append(f"  - Error: {item['error']}")
            report.append(f"  - Attempts: {item['attempts']}")
        report.append("")
    
    if results["retry"]:
        report.append("## Pages That Needed Retry")
        for path in results["retry"]:
            report.append(f"- `{path}`")
        report.append("")
    
    report.append("## Success Details")
    for item in sorted(results["success"], key=lambda x: x["path"]):
        report.append(f"- `{item['path']}`: {item['size']} bytes ({item['attempts']} attempt(s))")
    
    report_path = BASE_DIR / "batch3-verification-report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    print(f"\nVerification report: {report_path}")
    
    # Write summary
    total_success_size = sum(x['size'] for x in results['success'])
    summary = []
    summary.append("# Batch 3 Summary")
    summary.append("")
    summary.append("## Statistics")
    summary.append(f"- Total pages attempted: {len(PAGES)}")
    summary.append(f"- Successful: {len(results['success'])}")
    summary.append(f"- Failed: {len(results['failed'])}")
    summary.append(f"- Success rate: {len(results['success'])/len(PAGES)*100:.1f}%")
    summary.append(f"- Total content size: {total_success_size:,} bytes")
    summary.append("")
    summary.append("## Files by Category")
    
    # Count by category
    cats = {}
    for item in results["success"]:
        cat = item["path"].split("/")[0]
        cats[cat] = cats.get(cat, 0) + 1
    
    for cat, count in sorted(cats.items()):
        summary.append(f"- {cat}: {count} pages")
    
    summary_path = BASE_DIR / "batch3-summary.md"
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(summary))
    print(f"Summary: {summary_path}")
    
    return results

if __name__ == "__main__":
    main()
