#!/usr/bin/env python3
"""每小时从 Semantic Cache 更新上下文到 workspace"""
import json, urllib.request, datetime, os

SEMANTIC_CACHE_URL = "http://192.168.1.18:5050"
OUTPUT_FILE = os.path.expanduser("~/.openclaw/workspace/semantic-memory.md")

queries = ['ubuntu node', 'jetson', 'openclaw rl', 'semantic cache', 'gpu 训练', '贵庚', 'robot']
all_results = {}

for q in queries:
    try:
        data = json.dumps({'query': q, 'top_k': 3, 'threshold': 0.35}).encode()
        req = urllib.request.Request(f'{SEMANTIC_CACHE_URL}/search', data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            for r in result.get('results', []):
                key = r['text'][:80]
                if key not in all_results or r['similarity'] > all_results[key]['similarity']:
                    all_results[key] = r
    except Exception as e:
        pass

sorted_results = sorted(all_results.values(), key=lambda x: x['similarity'], reverse=True)[:10]
now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

lines = [f"# Semantic Memory - 相关历史上下文\n\n> 自动更新于 {now}\n\n"]
for r in sorted_results:
    sim = r['similarity']
    text = r['text'].replace('\n', ' ').strip()[:250]
    lines.append(f"- **[{sim:.2f}]** {text}\n\n")

with open(OUTPUT_FILE, 'w') as f:
    f.write(''.join(lines))

print(f"Updated with {len(sorted_results)} records at {now}")
