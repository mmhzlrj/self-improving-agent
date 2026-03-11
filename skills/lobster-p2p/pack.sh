#!/bin/bash
# 打包 P2P Skill

SKILL_DIR="/Users/lr/.openclaw/workspace/skills/lobster-p2p"
OUTPUT_DIR="/Users/lr/.openclaw/workspace/skills/lobster-p2p/pack"

# 创建临时目录
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# 复制文件（排除 node_modules 等）
cp -r "$SKILL_DIR"/*.js "$SKILL_DIR"/*.md "$OUTPUT_DIR/"

# 创建 zip
cd "$OUTPUT_DIR"
zip -r "lobster-p2p.zip" *.js *.md

echo "✅ 打包完成: $OUTPUT_DIR/lobster-p2p.zip"
ls -la "$OUTPUT_DIR"
