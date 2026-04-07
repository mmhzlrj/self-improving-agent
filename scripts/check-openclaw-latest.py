#!/usr/bin/env python3
"""Check latest OpenClaw version from GitHub."""
import urllib.request, json, sys, ssl

try:
    url = "https://api.github.com/repos/openclaw/openclaw/releases/latest"
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
    ctx = ssl._create_unverified_context()
    with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
        d = json.loads(r.read())
    print(f"最新版本: {d['tag_name']}")
    print(f"发布日期: {d['published_at']}")
    print(f"URL: {d['html_url']}")
    body = d.get("body", "")
    breaking = [l for l in body.split("\n") if "breaking" in l.lower() or "migration" in l.lower()]
    if breaking:
        print("\nBreaking Changes:")
        for b in breaking[:10]:
            print(f"  {b.strip()}")
    else:
        print("\n无 Breaking Changes")
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
