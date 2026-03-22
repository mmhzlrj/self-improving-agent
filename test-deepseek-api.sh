#!/bin/bash
# Test DeepSeek API via curl using credentials from zero-token

GATEWAY="http://127.0.0.1:3001"
TOKEN="62b791625fa441be036acd3c206b7e14e2bb13c803355823"

echo "=== Testing Zero-Token Gateway Models ==="
curl -s -H "Authorization: Bearer $TOKEN" "$GATEWAY/v1/models" | python3 -m json.tool 2>/dev/null | head -50

echo ""
echo "=== Testing Chat Completion ==="
curl -s -X POST "$GATEWAY/v1/chat/completions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-web/deepseek-chat",
    "messages": [{"role": "user", "content": "Hello, who are you?"}],
    "max_tokens": 100
  }' 2>&1 | head -100
