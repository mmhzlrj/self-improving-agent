#!/usr/bin/env python3
import ssl
import urllib.request, json
from datetime import datetime, timezone, timedelta

url = 'https://www.minimaxi.com/v1/api/openplatform/coding_plan/remains'
token = 'sk-cp-Zosvx8d6zR6EI34fzFEWopC1kvtXdtzpMPWObv8goBG4MyNJTzK-vuniGGQV5TPOcICyJP-qIjWQ66KlY5mtOm6Z1oAVA1lugbkRDjE1QyMFX6phXsGVOPA'

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})
with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
    data = json.loads(r.read())

tz = timezone(timedelta(hours=8))
now = datetime.now(tz)

for m in data.get('model_remains', []):
    total = m.get('current_interval_total_count', 0)
    remaining = m.get('current_interval_usage_count', 0)
    if total > 0:
        used = total - remaining
        pct = used / total * 100
        end_ts = m['end_time'] / 1000
        end_dt = datetime.fromtimestamp(end_ts, tz)
        remaining_seconds = (end_dt - now).total_seconds()
        hours = int(remaining_seconds // 3600)
        minutes = int((remaining_seconds % 3600) // 60)
        print(f'{m["model_name"]}: {remaining} remaining ({100-pct:.1f}%), \u91cd\u7f6e: {hours}h{minutes}m')
