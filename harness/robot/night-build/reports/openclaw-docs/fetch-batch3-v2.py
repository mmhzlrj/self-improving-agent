#!/usr/bin/env python3
"""Fetch OpenClaw docs batch 3: Tools/Plugins/Providers/Security/Help/Templates/Other"""
import subprocess
import os
import re
from pathlib import Path
from html.parser import HTMLParser

BASE_DIR = Path("/Users/lr/.openclaw/workspace/harness/robot/night-build/reports/openclaw-docs")
DOCS_URL = "https://docs.openclaw.ai"

# All pages to fetch: (url_path, dest_rel_path)
PAGES = [
    # tools/ (37 pages)
    ("tools/index.md", "tools/index.md"),
    ("tools/skills.md", "tools/skills.md"),
    ("tools/skills-config.md", "tools/skills-config.md"),
    ("tools/creating-skills.md", "tools/creating-skills.md"),
    ("tools/slash-commands.md", "tools/slash-commands.md"),
    ("tools/subagents.md", "tools/subagents.md"),
    ("tools/multi-agent-sandbox-tools.md", "tools/multi-agent-sandbox-tools.md"),
    ("tools/acp-agents.md", "tools/acp-agents.md"),
    ("tools/agent-send.md", "tools/agent-send.md"),
    ("tools/llm-task.md", "tools/llm-task.md"),
    ("tools/exec.md", "tools/exec.md"),
    ("tools/exec-approvals.md", "tools/exec-approvals.md"),
    ("tools/elevated.md", "tools/elevated.md"),
    ("tools/browser.md", "tools/browser.md"),
    ("tools/browser-login.md", "tools/browser-login.md"),
    ("tools/browser-linux-troubleshooting.md", "tools/browser-linux-troubleshooting.md"),
    ("tools/browser-wsl2-windows-remote-cdp-troubleshooting.md", "tools/browser-wsl2-windows-remote-cdp-troubleshooting.md"),
    ("tools/web-fetch.md", "tools/web-fetch.md"),
    ("tools/web.md", "tools/web.md"),
    ("tools/brave-search.md", "tools/brave-search.md"),
    ("tools/duckduckgo-search.md", "tools/duckduckgo-search.md"),
    ("tools/tavily.md", "tools/tavily.md"),
    ("tools/exa-search.md", "tools/exa-search.md"),
    ("tools/firecrawl.md", "tools/firecrawl.md"),
    ("tools/kimi-search.md", "tools/kimi-search.md"),
    ("tools/gemini-search.md", "tools/gemini-search.md"),
    ("tools/grok-search.md", "tools/grok-search.md"),
    ("tools/perplexity-search.md", "tools/perplexity-search.md"),
    ("tools/thinking.md", "tools/thinking.md"),
    ("tools/tts.md", "tools/tts.md"),
    ("tools/pdf.md", "tools/pdf.md"),
    ("tools/apply-patch.md", "tools/apply-patch.md"),
    ("tools/diffs.md", "tools/diffs.md"),
    ("tools/reactions.md", "tools/reactions.md"),
    ("tools/btw.md", "tools/btw.md"),
    ("tools/loop-detection.md", "tools/loop-detection.md"),
    ("tools/clawhub.md", "tools/clawhub.md"),
    ("tools/lobster.md", "tools/lobster.md"),
    ("tools/plugin.md", "tools/plugin.md"),
    
    # plugins/ (14 pages)
    ("plugins/sdk-overview.md", "plugins/sdk-overview.md"),
    ("plugins/architecture.md", "plugins/architecture.md"),
    ("plugins/building-plugins.md", "plugins/building-plugins.md"),
    ("plugins/manifest.md", "plugins/manifest.md"),
    ("plugins/bundles.md", "plugins/bundles.md"),
    ("plugins/sdk-setup.md", "plugins/sdk-setup.md"),
    ("plugins/sdk-entrypoints.md", "plugins/sdk-entrypoints.md"),
    ("plugins/sdk-channel-plugins.md", "plugins/sdk-channel-plugins.md"),
    ("plugins/sdk-provider-plugins.md", "plugins/sdk-provider-plugins.md"),
    ("plugins/sdk-runtime.md", "plugins/sdk-runtime.md"),
    ("plugins/sdk-migration.md", "plugins/sdk-migration.md"),
    ("plugins/sdk-testing.md", "plugins/sdk-testing.md"),
    ("plugins/voice-call.md", "plugins/voice-call.md"),
    ("plugins/community.md", "plugins/community.md"),
    
    # providers/ (38 pages)
    ("providers/index.md", "providers/index.md"),
    ("providers/models.md", "providers/models.md"),
    ("providers/openai.md", "providers/openai.md"),
    ("providers/anthropic.md", "providers/anthropic.md"),
    ("providers/google.md", "providers/google.md"),
    ("providers/deepseek.md", "providers/deepseek.md"),
    ("providers/glm.md", "providers/glm.md"),
    ("providers/qwen.md", "providers/qwen.md"),
    ("providers/qwen_modelstudio.md", "providers/qwen_modelstudio.md"),
    ("providers/moonshot.md", "providers/moonshot.md"),
    ("providers/minimax.md", "providers/minimax.md"),
    ("providers/mistral.md", "providers/mistral.md"),
    ("providers/groq.md", "providers/groq.md"),
    ("providers/ollama.md", "providers/ollama.md"),
    ("providers/vllm.md", "providers/vllm.md"),
    ("providers/sglang.md", "providers/sglang.md"),
    ("providers/together.md", "providers/together.md"),
    ("providers/perplexity-provider.md", "providers/perplexity-provider.md"),
    ("providers/openrouter.md", "providers/openrouter.md"),
    ("providers/litellm.md", "providers/litellm.md"),
    ("providers/cloudflare-ai-gateway.md", "providers/cloudflare-ai-gateway.md"),
    ("providers/bedrock.md", "providers/bedrock.md"),
    ("providers/nvidia.md", "providers/nvidia.md"),
    ("providers/venice.md", "providers/venice.md"),
    ("providers/huggingface.md", "providers/huggingface.md"),
    ("providers/github-copilot.md", "providers/github-copilot.md"),
    ("providers/claude-max-api-proxy.md", "providers/claude-max-api-proxy.md"),
    ("providers/opencode.md", "providers/opencode.md"),
    ("providers/opencode-go.md", "providers/opencode-go.md"),
    ("providers/kilocode.md", "providers/kilocode.md"),
    ("providers/synthetic.md", "providers/synthetic.md"),
    ("providers/xai.md", "providers/xai.md"),
    ("providers/xiaomi.md", "providers/xiaomi.md"),
    ("providers/volcengine.md", "providers/volcengine.md"),
    ("providers/zai.md", "providers/zai.md"),
    ("providers/deepgram.md", "providers/deepgram.md"),
    ("providers/qianfan.md", "providers/qianfan.md"),
    
    # security/ (3 pages)
    ("security/THREAT-MODEL-ATLAS.md", "security/THREAT-MODEL-ATLAS.md"),
    ("security/CONTRIBUTING-THREAT-MODEL.md", "security/CONTRIBUTING-THREAT-MODEL.md"),
    ("security/formal-verification.md", "security/formal-verification.md"),
    
    # help/ (7 pages)
    ("help/index.md", "help/index.md"),
    ("help/troubleshooting.md", "help/troubleshooting.md"),
    ("help/faq.md", "help/faq.md"),
    ("help/debugging.md", "help/debugging.md"),
    ("help/environment.md", "help/environment.md"),
    ("help/scripts.md", "help/scripts.md"),
    ("help/testing.md", "help/testing.md"),
    ("logging.md", "logging.md"),
    ("network.md", "network.md"),
    ("date-time.md", "date-time.md"),
    ("diagnostics/flags.md", "diagnostics/flags.md"),
    ("debug/node-issue.md", "debug/node-issue.md"),
    ("ci.md", "ci.md"),
    
    # Other pages
    ("prose.md", "prose.md"),
]

# Try to find html2text
def has_html2text():
    try:
        subprocess.run(["html2text", "--version"], capture_output=True, check=True)
        return True
    except:
        return False

def ensure_dir(path):
    d = BASE_DIR / path
    d.parent.mkdir(parents=True, exist_ok=True)
    return d

def curl_fetch(url, timeout=30):
    """Fetch URL using curl with browser headers, return raw HTML"""
    try:
        result = subprocess.run(
            [
                "curl", "-s", "-L",
                "-A", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "-H", "Accept-Language: en-US,en;q=0.5",
                url
            ],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if result.returncode != 0:
            return None, f"curl error: {result.returncode}"
        return result.stdout, None
    except subprocess.TimeoutExpired:
        return None, "Timeout"
    except Exception as e:
        return None, str(e)

def extract_content(html_content):
    """Extract main content from HTML - look for article/content div"""
    if not html_content or len(html_content) < 500:
        return None, "Content too short"
    
    # Look for the main content area
    # Mintlify uses specific structure
    content_match = re.search(r'<article[^>]*>(.*?)</article>', html_content, re.DOTALL)
    if content_match:
        content = content_match.group(1)
    else:
        # Try to find content div
        content_match = re.search(r'<div[^>]*id=["\']content["\'][^>]*>(.*?)</div>', html_content, re.DOTALL)
        if content_match:
            content = content_match.group(1)
        else:
            content = html_content
    
    # Remove scripts and styles
    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
    content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
    content = re.sub(r'<nav[^>]*>.*?</nav>', '', content, flags=re.DOTALL)
    content = re.sub(r'<footer[^>]*>.*?</footer>', '', content, flags=re.DOTALL)
    content = re.sub(r'<header[^>]*>.*?</header>', '', content, flags=re.DOTALL)
    
    # Remove HTML comments
    content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
    
    # Convert HTML entities
    content = content.replace('&nbsp;', ' ')
    content = content.replace('&amp;', '&')
    content = content.replace('&lt;', '<')
    content = content.replace('&gt;', '>')
    content = content.replace('&quot;', '"')
    
    # Convert basic HTML to markdown-like text
    # This is a simple approach - just remove most tags
    content = re.sub(r'<br\s*/?>', '\n', content)
    content = re.sub(r'</p>', '\n\n', content)
    content = re.sub(r'</div>', '\n', content)
    content = re.sub(r'</li>', '\n', content)
    content = re.sub(r'</h[1-6]>', '\n\n', content)
    
    # Remove remaining tags but keep text
    content = re.sub(r'<[^>]+>', '', content)
    
    # Clean up whitespace
    content = re.sub(r'\n\s*\n', '\n\n', content)
    content = content.strip()
    
    if len(content) < 200:
        return None, "Extracted content too short"
    
    return content, None

def fetch_page(url_path, dest_rel, retries=2):
    """Fetch a single page, return (success, size_or_error, content)"""
    dest = ensure_dir(dest_rel)
    url = f"{DOCS_URL}/{url_path}"
    
    for attempt in range(retries + 1):
        html, err = curl_fetch(url)
        
        if err:
            if attempt < retries:
                continue
            return False, err, None, attempt
        
        # Check if it's an error page
        if 'Page Not Found' in html[:1000] or '404' in html[:500]:
            if attempt < retries:
                continue
            return False, "404 Not Found", None, attempt
        
        # Extract content
        content, content_err = extract_content(html)
        if content_err:
            if attempt < retries:
                continue
            return False, content_err, None, attempt
        
        # Write content
        with open(dest, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True, len(content), content, attempt + 1
    
    return False, "Max retries exceeded", None, retries

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
    print(f"html2text available: {has_html2text()}")
    print("-" * 60)
    
    results = {
        "success": [],
        "failed": [],
        "retry": []
    }
    
    for i, (url_path, dest_rel) in enumerate(PAGES):
        print(f"[{i+1}/{len(PAGES)}] Fetching {url_path}...", end=" ", flush=True)
        
        success, result, content, attempts = fetch_page(url_path, dest_rel)
        
        if success:
            size = verify_file(dest_rel)
            print(f"OK ({size} bytes, {attempts} attempt(s))")
            results["success"].append({
                "path": dest_rel,
                "size": size,
                "attempts": attempts
            })
        else:
            print(f"FAILED ({result})")
            results["failed"].append({
                "path": dest_rel,
                "url": f"{DOCS_URL}/{url_path}",
                "error": result,
                "attempts": attempts
            })
            if attempts > 1:
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
    report.append(f"- Successful: {len(results['success'])}")
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
