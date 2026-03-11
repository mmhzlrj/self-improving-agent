#!/bin/bash
# 小龙虾 P2P 快速测试脚本

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
P2P_DIR="$HOME/.openclaw/workspace/skills/lobster-p2p"

echo "🦞 小龙虾 P2P 快速测试"
echo "======================"

# 检查 p2p 模块
if [ ! -f "$P2P_DIR/p2p.js" ]; then
    echo "❌ P2P 模块未安装"
    exit 1
fi

# 测试加载
node -e "
const p2p = require('$P2P_DIR/p2p.js');
console.log('✅ P2P 模块加载成功');
console.log('📡 设备ID:', p2p.getMyInfo().deviceId);
console.log('👤 昵称:', p2p.getMyInfo().nickname);
console.log('🔌 端口:', p2p.getMyInfo().port);
"

echo ""
echo "📝 可用命令："
echo "   - 启动 P2P"
echo "   - 我的 P2P 信息"
echo "   - 连接 IP:端口 消息"
echo "   - 联系人列表"
