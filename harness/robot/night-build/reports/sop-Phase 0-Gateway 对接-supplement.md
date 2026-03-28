# Phase 0 Gateway 对接 - OpenClaw 安装步骤补充

> 补充自 `reference/ROBOT-SOP.md` Phase 0 章节及官方安装文档
> 生成时间：2026-03-28

---

## B.1 前置检查：系统环境

在安装 OpenClaw 前，先确认系统环境：

```bash
# 确认 Ubuntu 版本（推荐 22.04 LTS 或 24.04 LTS）
cat /etc/os-release

# 确认网络（内网连通性）
ping -c 1 192.168.x.x    # Mac Gateway IP

# 确认有 sudo 权限
sudo -v
```

---

## B.2 安装 Node.js（若未安装）

OpenClaw 需要 **Node.js 22.14+**（推荐 Node 24）。Ubuntu 上通过 NodeSource 安装：

```bash
# 安装 Node 24（推荐）
curl -fsSL https://deb.nodesource.com/setup_24.x | sudo -E bash -
sudo apt-get install -y nodejs

# 验证
node -v    # 应显示 v24.x.x
npm -v     # 应显示 10.x.x
```

> **备选方案**：使用版本管理器（fnm / nvm）可避免系统权限问题。
> ```bash
> curl -fsSL https://fnm.jdx.dev/install | bash
> fnm install 24
> fnm use 24
> ```

---

## B.3 安装 OpenClaw（两种方式）

### 方式一：install.sh（推荐，自动装 Node）

```bash
curl -fsSL --proto '=https' --tlsv1.2 https://openclaw.ai/install.sh | bash
```

**常用选项：**
```bash
# 跳过引导（自动化场景）
curl -fsSL https://openclaw.ai/install.sh | bash -s -- --no-onboard

# 使用 git 方法安装（可追踪 main 分支更新）
curl -fsSL https://openclaw.ai/install.sh | bash -s -- --install-method git

# 预览安装步骤（不实际执行）
curl -fsSL https://openclaw.ai/install.sh | bash -s -- --dry-run
```

### 方式二：install-cli.sh（本地化安装，无需系统 Node）

适合不想污染全局 npm 环境的场景：

```bash
curl -fsSL --proto '=https' --tlsv1.2 https://openclaw.ai/install-cli.sh | bash

# 自定义安装路径
curl -fsSL https://openclaw.ai/install-cli.sh | bash -s -- --prefix ~/.openclaw
```

---

## B.4 验证安装

```bash
# 检查 openclaw 是否在 PATH 中
which openclaw

# 运行诊断
openclaw doctor --non-interactive
```

**常见问题：`openclaw: command not found`**

```bash
# 找到 npm 全局 bin 目录
npm prefix -g

# 确认 PATH 中是否包含
echo $PATH | grep "$(npm prefix -g)"

# 若缺失，手动添加到 ~/.bashrc 或 ~/.zshrc
export PATH="$(npm prefix -g)/bin:$PATH"
source ~/.bashrc   # 或 source ~/.zshrc
```

---

## B.5 安装后配置（连接 Mac Gateway）

安装完成后，继续执行 SOP 中的 Step A ~ Step E 完成 Gateway 对接。

### 快速完整命令序列（无人值守安装 + Gateway 连接）

```bash
# 1. 安装 Node 24（如需要）
curl -fsSL https://deb.nodesource.com/setup_24.x | sudo -E bash -
sudo apt-get install -y nodejs

# 2. 安装 OpenClaw（跳过引导）
curl -fsSL https://openclaw.ai/install.sh | bash -s -- --no-onboard

# 3. 设置 Gateway 环境变量（根据 Step A 获取的 token）
export OPENCLAW_GATEWAY_TOKEN="你的token"
export OPENCLAW_GATEWAY_URL="http://192.168.x.x:18789"

# 4. 启动 Node Host
openclaw node run \
  --host 192.168.x.x \
  --port 18789 \
  --display-name "Ubuntu-GPU-Node"

# 5. 在 Mac Gateway 上批准配对
# openclaw devices approve <requestId>
```

---

## B.6 参考链接

- 官方安装文档：https://docs.openclaw.ai/install
- install.sh 完整选项：https://docs.openclaw.ai/install/installer
- Node.js 要求：https://docs.openclaw.ai/install/node
- Gateway 配置：https://docs.openclaw.ai/gateway/configuration

---

## B.7 Node 配置步骤（核心配置）

### B.7.1 获取 Gateway Token（Step A）

在 **Mac Gateway** 上执行以下命令获取配对 token：

```bash
# 方式一：通过 openclaw.json 直接读取
cat ~/.openclaw/openclaw.json | python3 -c "
import json, sys
d = json.load(sys.stdin)
auth = d.get('auth', {})
print('Token:', auth.get('token', 'NOT_FOUND'))
print('Gateway URL:', d.get('gateway', {}).get('bind', 'NOT_FOUND'))
"

# 方式二：通过 CLI
openclaw config get gateway.auth.token

# 方式三：通过 qr 命令验证 Gateway 可访问性
openclaw qr --json | python3 -c "
import json, sys
d = json.load(sys.stdin)
print('Gateway URL:', d.get('gatewayUrl', 'N/A'))
print('URL Source:', d.get('urlSource', 'N/A'))
"
```

> **重要**：如果 Gateway 配置了 `gateway.bind=lan`，确保 Ubuntu 和 Mac 在同一局域网内。

### B.7.2 在 Ubuntu 上配置并启动 Node Host

```bash
# 创建环境变量文件（持久化配置）
mkdir -p ~/.openclaw
cat > ~/.openclaw/node-env.sh << 'EOF'
# Gateway 连接配置
export OPENCLAW_GATEWAY_TOKEN="上面获取的token"
export OPENCLAW_GATEWAY_URL="http://192.168.x.x:18789"

# Node 显示名称（方便在 Gateway 上识别）
export OPENCLAW_NODE_NAME="Ubuntu-GPU-Node"

# 可选：GPU 任务专用节点标记
export OPENCLAW_NODE_TAGS="gpu,cuda,desktop"
EOF

# 加载环境变量
source ~/.openclaw/node-env.sh

# 启动 Node Host（前台运行用于调试）
openclaw node run \
  --host 192.168.x.x \
  --port 18789 \
  --display-name "Ubuntu-GPU-Node"

# 或后台运行（systemd 服务方式）
cat > ~/.config/systemd/user/openclaw-node.service << 'EOF'
[Unit]
Description=OpenClaw Node Host
After=network.target

[Service]
Type=simple
EnvironmentFile=/home/ubuntu/.openclaw/node-env.sh
ExecStart=/usr/local/bin/openclaw node run \
  --host 192.168.x.x \
  --port 18789 \
  --display-name "Ubuntu-GPU-Node"
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF

# 启用并启动服务
systemctl --user daemon-reload
systemctl --user enable openclaw-node.service
systemctl --user start openclaw-node.service
```

### B.7.3 在 Mac Gateway 上批准配对（Step C）

```bash
# 列出所有设备（包括待批准的）
openclaw devices list

# 批准最新的配对请求
openclaw devices approve --latest

# 或指定 requestId 批准
openclaw devices approve <requestId>

# 查看节点状态
openclaw nodes status

# 查看节点详细信息
openclaw nodes describe --node "Ubuntu-GPU-Node"
```

**常见问题**：如果 `openclaw devices list` 没有显示待批准设备，检查：
1. Ubuntu 能否连通 Mac Gateway：`curl -v http://192.168.x.x:18789/health`
2. Token 是否正确
3. Node 是否已启动（看是否有错误日志）

### B.7.4 配置 GPU 任务路由到该节点（Step E）

```bash
# 方式一：通过 CLI（临时生效，重启后失效）
openclaw config set tools.exec.host node
openclaw config set tools.exec.node "Ubuntu-GPU-Node"

# 方式二：直接编辑配置文件
# Mac 上执行
nano ~/.openclaw/openclaw.json

# 添加或修改以下配置：
# {
#   "tools": {
#     "exec": {
#       "host": "node",
#       "node": "Ubuntu-GPU-Node"
#     }
#   }
# }

# 方式三：GPU 任务专用配置（推荐）
# 只对需要 GPU 的任务使用 node host，普通任务仍在 gateway
openclaw config set tools.exec.node "Ubuntu-GPU-Node"
# 然后在任务中通过 exec host=node 参数指定使用节点

# 验证配置
openclaw config get tools.exec.host
openclaw config get tools.exec.node
```

### B.7.5 GPU 验证（如果节点有 NVIDIA GPU）

```bash
# 在 Ubuntu 节点上验证 GPU 可用性
nvidia-smi

# 测试 CUDA 可用性
python3 -c "import torch; print('CUDA:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"

# 如果需要让 AI 任务使用 GPU，在 Node Host 环境变量中设置
export CUDA_VISIBLE_DEVICES=0
```

---

## B.8 Exec Approvals 配置（节点安全策略）

Node Host 上的 exec approvals 控制哪些命令可以在节点上执行。

### B.8.1 查看当前策略

```bash
# 在 Mac Gateway 上查看节点的 exec approvals
openclaw approvals get --node "Ubuntu-GPU-Node"

# 在 Ubuntu 节点本地上查看
cat ~/.openclaw/exec-approvals.json
```

### B.8.2 配置默认策略

```bash
# 允许所有命令（慎用，等同于 elevated）
openclaw approvals default set --node "Ubuntu-GPU-Node" --security full

# 启用白名单模式（仅允许明确批准的命理）
openclaw approvals default set --node "Ubuntu-GPU-Node" --security allowlist

# 询问模式（每次执行前需批准）
openclaw approvals default set --node "Ubuntu-GPU-Node" --security deny --ask on-miss
```

### B.8.3 添加白名单条目

```bash
# 允许特定命令
openclaw approvals allowlist add \
  --node "Ubuntu-GPU-Node" \
  --pattern "~/Projects/**/bin/*"

# 允许 Python、Node 等运行时
openclaw approvals allowlist add --node "Ubuntu-GPU-Node" --pattern "/usr/bin/python3"
openclaw approvals allowlist add --node "Ubuntu-GPU-Node" --pattern "/usr/bin/node"

# 列出当前白名单
openclaw approvals allowlist list --node "Ubuntu-GPU-Node"
```

### B.8.4 从其他节点复制策略

```bash
# 导出策略
openclaw approvals export --node "Ubuntu-GPU-Node" > ~/openclaw-approvals-backup.json

# 导入到新节点（在新节点 Ubuntu 上执行）
cat ~/openclaw-approvals-backup.json | openclaw approvals import --node "Ubuntu-GPU-Node"
```

---

## B.9 验证节点完整链路

### B.9.1 命令阶梯检查

```bash
# 在 Mac Gateway 上依次执行
openclaw status                    # Gateway 自身状态
openclaw gateway status           # Gateway 服务状态
openclaw nodes status             # 节点连接状态
openclaw nodes describe --node "Ubuntu-GPU-Node"  # 节点详细信息
openclaw approvals get --node "Ubuntu-GPU-Node"  # exec 策略状态

# 在 Ubuntu 节点上执行
openclaw node status              # Node Host 自身状态
openclaw logs --follow            # 实时日志（调试用）
```

### B.9.2 端到端功能测试

```bash
# 从 Mac Gateway 通过节点执行命令（测试 exec 链路）
openclaw exec --host node --node "Ubuntu-GPU-Node" -- uname -a

# 测试 GPU 访问（如果有）
openclaw exec --host node --node "Ubuntu-GPU-Node" -- nvidia-smi

# 测试文件操作
openclaw exec --host node --node "Ubuntu-GPU-Node" -- ls ~/.openclaw
```

### B.9.3 节点能力检查清单

| 能力 | 检查命令 | 预期输出 |
|------|---------|---------|
| 节点在线 | `openclaw nodes status` | Ubuntu-GPU-Node: online |
| 设备已配对 | `openclaw devices list` | Ubuntu-GPU-Node: paired |
| Gateway 连通 | `curl http://192.168.x.x:18789/health` | {"status":"ok"} |
| GPU 可用 | `nvidia-smi` | 显示 GPU 信息 |
| Exec 可用 | `openclaw exec --host node --node "Ubuntu-GPU-Node" -- echo hello` | hello |

---

## B.10 常见问题排查

### 问题 1：Node 启动后立即退出

```bash
# 查看详细错误日志
openclaw node run --verbose 2>&1 | head -50

# 检查 token 是否正确
echo $OPENCLAW_GATEWAY_TOKEN

# 检查 Gateway URL 是否可访问
curl -v http://192.168.x.x:18789/health
```

### 问题 2：Node 显示 online 但 exec 失败

```bash
# 检查 exec approvals 策略
openclaw approvals get --node "Ubuntu-GPU-Node"

# 如果是 SYSTEM_RUN_DENIED，需要添加白名单
openclaw approvals allowlist add --node "Ubuntu-GPU-Node" --pattern "/usr/bin/uname"
```

### 问题 3：配对请求从未出现

```bash
# 确保 Node 启动时使用了正确的 token
# 检查 Node 日志是否有 "pairing request pending" 字样
journalctl --user -u openclaw-node.service -f

# 重置配对（两端都删除后重新开始）
# Mac 上：
openclaw devices revoke "Ubuntu-GPU-Node"
# Ubuntu 上：
rm ~/.openclaw/node-id.json
openclaw node run ...
```

### 问题 4：GPU 任务没有路由到节点

```bash
# 确认当前 exec host 配置
openclaw config get tools.exec.host
openclaw config get tools.exec.node

# 确认节点支持 GPU 任务
openclaw nodes describe --node "Ubuntu-GPU-Node" | grep -i gpu

# 手动指定节点执行
openclaw exec --host node --node "Ubuntu-GPU-Node" -- python3 -c "import torch; print(torch.cuda.is_available())"
```

### 问题 5：节点连接不稳定/频繁断开

```bash
# 检查网络延迟
ping 192.168.x.x

# 建议：使用有线以太网而非 Wi-Fi
# 或配置 Tailscale 实现跨网络连接

# 检查 Node 日志中的断开原因
openclaw logs 2>&1 | grep -i "disconnect\|timeout\|error"
```

---

## B.12 WebSocket 连接验证

> OpenClaw Gateway 与 Node 之间通过 WebSocket 维持长连接（同一端口 18789 复用 HTTP/WebSocket）。节点发现、配对、心跳、exec 下发均依赖此连接。本节详解如何验证 WebSocket 链路正常。

### B.12.1 WebSocket 握手检测

Gateway WebSocket 端点为 `ws://<mac-ip>:18789/ws`（或 `wss://` 如果启用了 TLS）。

**Step A - 用 curl 模拟 WebSocket 升级请求**（验证 Gateway 握手能力）：

```bash
# Ubuntu 侧执行，检测 Gateway 是否支持 WebSocket 升级
curl -sv \
  --no-buffer \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
  http://<mac-ip>:18789/ws 2>&1 | grep -E "< HTTP|Upgrade:|Sec-WebSocket|error"

# 预期输出（成功）：
# < HTTP/1.1 101 Switching Protocols
# Upgrade: websocket
# Connection: Upgrade

# 常见失败：
# < HTTP/1.1 403 Forbidden          → Gateway bind=loopback，或 token 校验失败
# < HTTP/1.1 404 Not Found         → /ws 路径不存在，Gateway 版本不支持 WebSocket
# < HTTP/1.1 401 Unauthorized       → 未提供有效 token
```

**Step B - 用 wscat 交互式连接**（完整握手 + 双向通信）：

```bash
# 安装 wscat（需要 npm）
npm install -g wscat

# 连接（无认证场景）
wscat -c ws://<mac-ip>:18789/ws

# 连接（有 token 场景，附加 header）
wscat -c ws://<mac-ip>:18789/ws \
  -H "Authorization: Bearer 235bf68c2288bfde322b8567509fb0e4d8eb368ec3c70000"

# 连接成功后，输入任意内容应收到 echo 或 gateway 响应
# 按 Ctrl+C 断开
```

**Step C - 浏览器开发者工具验证**（如果有图形界面）：

```
1. 打开 Chrome/Edge → F12 → Network 标签
2. 过滤条件：ws（WebSocket）
3. 访问 http://<mac-ip>:18789
4. 观察 WS 连接：
   - URL: ws://<mac-ip>:18789/ws
   - Status: 101 Switching Protocols
5. 点击该连接 → Messages 标签查看双向心跳/ping-pong 帧
```

### B.12.2 连接状态验证（Node 已连接场景）

当 Node Host 已在运行时，通过 CLI 检查 WebSocket 连接状态：

```bash
# 在 Mac Gateway 上
openclaw nodes status

# 在 Ubuntu Node 上
openclaw node status

# 查看节点连接详情（包含 WebSocket session ID 和连接时长）
openclaw nodes describe --node "Ubuntu-GPU-Node"
```

**关键状态字段解读**：

| 字段 | 含义 | 正常值 |
|------|------|--------|
| `status` | 节点连接状态 | `online` / `connected` |
| `transport` | 传输层 | `websocket` |
| `latency` | 往返延迟 | < 50ms（LAN） |
| `uptime` | 连接持续时间 | > 0（持续增长） |
| `lastPing` | 最近一次 pong 响应 | 时间戳，距今 < 2 分钟 |

### B.12.3 心跳（Ping-Pong）机制验证

OpenClaw 通过 WebSocket ping/pong 帧维持连接活性（默认心跳间隔约 30s）。

**Step A - 在 Node 侧观察 ping/pong**：

```bash
# 如果 node run 是前台运行，观察日志
openclaw node run --host <mac-ip> --port 18789 --token "TOKEN" 2>&1 | grep -i "ping\|pong\|heartbeat"

# 预期日志（每 30 秒一次）：
# [OpenClaw] Sending ping to gateway...
# [OpenClaw] Received pong from gateway (latency: 12ms)
```

**Step B - 主动测试 ping**：

```bash
# 在 Gateway 侧主动 ping 节点（如果 CLI 支持）
openclaw nodes ping --node "Ubuntu-GPU-Node"

# 预期输出：
# Pinging Ubuntu-GPU-Node...
# Pong received: latency=8ms
```

**Step C - 检测心跳丢失（连接不稳定的根本原因）**：

```bash
# 在 Node 日志中搜索心跳超时
openclaw logs 2>&1 | grep -i "heartbeat\|ping timeout\|connection lost\|ping deadline"

# 常见错误：
# "Heartbeat timeout after 60s" → 网络拥塞或节点负载过高
# "Ping deadline exceeded"       → Gateway 或网络无响应
# "WebSocket connection closed"  → 被 Gateway 主动断开或网络中断
```

### B.12.4 WebSocket 错误码诊断

Node 连接失败时，日志会显示 WebSocket 关闭码。常见错误码对照：

| 关闭码 | 含义 | 排查方向 |
|--------|------|---------|
| 1000 | 正常关闭 | Node 被正常停止，无需处理 |
| 1001 | Gateway 不可达（服务器迁移） | Gateway 重启，Node 应自动重连 |
| 1006 | 异常关闭（未发送 close 帧） | 网络中断、防火墙掉包、Gateway 崩溃 |
| 1008 | Token 无效 | Token 与 Gateway 不匹配，检查 token |
| 1011 | Gateway 内部错误 | Gateway 日志检查，尝试 `openclaw gateway restart` |
| 1015 | TLS 错误（wss:// 场景） | 证书问题，确认 Gateway TLS 配置 |

**诊断命令**：

```bash
# 在 Node 侧捕获 WebSocket 详细错误
OPENCLAW_LOG_LEVEL=debug openclaw node run --host <mac-ip> --port 18789 2>&1 | \
  grep -E "WebSocket|ws://|wss://|code=|reason=|close"

# 在 Gateway 侧查看拒绝原因
openclaw gateway logs --follow 2>&1 | \
  grep -E "WebSocket|reject|unauthorized|pairing"
```

### B.12.5 断线重连验证

OpenClaw Node 默认具备自动重连能力。验证重连机制：

**Step A - 模拟 Gateway 重启（触发 Node 重连）**：

```bash
# Step 1：记录 Node 当前连接时间
openclaw nodes describe --node "Ubuntu-GPU-Node" | grep uptime

# Step 2：在 Mac Gateway 上重启
openclaw gateway restart

# Step 3：观察 Node 侧日志（自动重连）
# 在 Ubuntu 上（Node 前台运行时）
openclaw node run --host <mac-ip> --port 18789 2>&1 | grep -i "reconnect\|retry\|attempt"

# 预期日志：
# [OpenClaw] Connection lost, reconnecting in 5s...
# [OpenClaw] Reconnect attempt 1/10...
# [OpenClaw] Reconnected successfully (attempt 3)
```

**Step B - 验证重连后状态恢复**：

```bash
# 重启后检查节点状态
sleep 10
openclaw nodes status
# 预期：Ubuntu-GPU-Node 状态恢复为 online

# 验证 exec 链路
openclaw exec --host node --node "Ubuntu-GPU-Node" -- echo "post-reconnect OK"
# 预期：输出 "post-reconnect OK"
```

**Step C - 配置重连策略（高级）**：

```bash
# 如果默认重连间隔不满意，可以通过环境变量调整
export OPENCLAW_NODE_RECONNECT_DELAY=3000    # 重连间隔 3 秒（ms）
export OPENCLAW_NODE_RECONNECT_MAX_RETRIES=20 # 最多重试 20 次

# 或在 node.json 中配置
cat >> ~/.openclaw/node.json << 'EOF'
{
  "reconnect": {
    "delayMs": 3000,
    "maxRetries": 20,
    "backoffMultiplier": 1.5
  }
}
EOF
```

### B.12.6 WebSocket 链路完整验证清单

| 步骤 | 验证方法 | 预期结果 |
|------|---------|---------|
| 1. 握手可达 | `curl -sv ... http://<mac-ip>:18789/ws` | `101 Switching Protocols` |
| 2. wscat 连接 | `wscat -c ws://<mac-ip>:18789/ws` | 连接成功，发送消息有响应 |
| 3. Node 在线 | `openclaw nodes status` | Ubuntu-GPU-Node: online |
| 4. 传输层确认 | `openclaw nodes describe --node "Ubuntu-GPU-Node"` | `transport: websocket` |
| 5. 延迟正常 | `ping -c 5 <mac-ip>` | avg < 5ms（同 LAN） |
| 6. 心跳活跃 | Node 日志 `grep ping` | 每 ~30s 一次 pong |
| 7. Gateway ping | `openclaw nodes ping --node "Ubuntu-GPU-Node"` | latency < 50ms |
| 8. 断线重连 | `openclaw gateway restart`，观察 Node 日志 | 自动重连，10s 内恢复 |
| 9. exec 正常 | `openclaw exec --host node --node "Ubuntu-GPU-Node" -- uname -a` | 返回 Ubuntu 内核信息 |

---

## B.11 DM 配对流程（Device/Machine Pairing）

> DM 配对是 OpenClaw Gateway 的默认配对策略，用于将桌面设备（Ubuntu/桌面端）或个人移动设备（手机/平板）以 Node 身份接入 Gateway。所有配对均需在 Gateway 侧手动审批（除非配置了 silent auto-approval）。

### B.11.1 配对机制核心概念

| 概念 | 说明 |
|------|------|
| **Pending Request** | 设备发起连接请求，等待 Gateway 审批 |
| **DM Pairing Code** | 设备身份凭证，对应一个 pending request |
| **Paired Node** | 已批准的设备，获得了 Gateway 颁发的 auth token |
| **Pending 上限** | 每频道最多 **3 个** pending request，超出后新请求被拒绝 |
| **有效期** | Pending request 有效期内可重复使用；**5 分钟**内未审批则自动过期 |

### B.11.2 DM Pairing 与 Node Pairing 的区别

| | DM Pairing（设备配对） | Node Pairing（节点配对） |
|---|---|---|
| **触发方式** | WS `connect` 时携带设备身份（role: node） | 显式调用 `node.pair.*` API |
| **Gate 握手** | ✅ 是，WS 连接时必须通过 | ❌ 否，不影响 WS 握手 |
| **存储位置** | `openclaw devices list` | `openclaw nodes pending/approve` |
| **适用场景** | 头less 节点（Ubuntu）、companion app（iOS/Android） | Gateway-owned 节点管理 |

> **重要**：对于 Ubuntu 台式机节点，DM pairing 和 node pairing 同时发生。设备通过 WS 连接时触发 DM pairing（需要 `openclaw devices approve`），而 `node.pair.*` 是独立的管理接口。两者不要混淆。

### B.11.3 完整 DM 配对流程（Ubuntu 节点视角）

**Step A - 设备侧：发起配对请求**

```bash
# Ubuntu 节点启动时自动发起配对请求（无需手动触发）
openclaw node run \
  --host <mac-ip> \
  --port 18789 \
  --display-name "Ubuntu-GPU-Node"

# 日志观察：
# [OpenClaw] Node connecting to gateway at <mac-ip>:18789
# [OpenClaw] Node connected successfully
# [OpenClaw] Waiting for pairing approval from gateway...
# [OpenClaw] DM pairing request submitted, requestId: xxxxxxxx
```

> 如果节点之前已配对过但 token 被撤销，Node 会自动生成新的配对请求。

**Step B - Gateway 侧：查看 pending 请求**

```bash
# 在 Mac Gateway 上执行
openclaw devices list

# 示例输出：
# Device ID     Name              Status     Requested At
# -----------   ----------------  ---------  ------------------------
# abc123def     Ubuntu-GPU-Node   pending    2026-03-28 08:10:23
# (等待批准)
```

**Step C - Gateway 侧：审批配对请求**

```bash
# 批准最新的配对请求
openclaw devices approve --latest

# 或指定 requestId
openclaw devices approve <requestId>

# 如果请求已过期，重新运行 Step A 后再审批
```

**Step D - 设备侧：确认配对成功**

```bash
# Node 日志自动更新：
# [OpenClaw] Pairing approved! Token received.
# [OpenClaw] Node is now paired and authenticated.

# 确认节点状态
openclaw nodes status
# 预期输出：connected / paired
```

### B.11.4 Pending Request 过期与处理

**过期机制**：Pending request 有效期为 **5 分钟**。超时后：
- Gateway 自动删除该 pending request
- Node 收到过期通知，日志显示：`DM pairing request expired, please reconnect`
- Node 会自动重新发起配对请求（生成新的 requestId）

**处理流程**：

```bash
# Step 1：Node 侧重新发起请求（自动进行）
# [OpenClaw] DM pairing request expired, retrying...
# [OpenClaw] New requestId: yyyyyyyy

# Step 2：Gateway 侧重新查看（注意新的 requestId）
openclaw devices list
# 注意：之前的请求已消失，出现新的 pending 请求

# Step 3：Gateway 侧重新审批
openclaw devices approve --latest
```

**常见问题：Pending 满额（3个/频道）**

```bash
# 如果报错 "Too many pending requests"
openclaw devices list
# 查看所有 pending 请求

# 清理已过期的请求（Gateway 会在 5 分钟后自动清理）
# 或手动拒绝：
openclaw devices reject <requestId>
openclaw devices reject <requestId>
openclaw devices reject <requestId>
```

### B.11.5 Silent Auto-Approval（仅 macOS Companion App）

macOS 客户端支持静默自动审批，条件：
1. 配对请求标记了 `silent: true`
2. macOS app 能够通过 SSH 验证到 Gateway 主机（同一用户）

```bash
# 自动审批成功 → 不弹出 prompt
# 自动审批失败 → 回退到正常 "Approve/Reject" 提示
```

Ubuntu 节点不支持 silent auto-approval，必须手动审批。

### B.11.6 Token 轮换与重新配对

每次审批会生成**新的 token**，旧 token 立即失效：

```bash
# Node 重新连接时必须使用新 token
# [OpenClaw] Token rotated, reconnecting with new token...
# [OpenClaw] Connection established with fresh token.
```

**手动触发重新配对**（例如设备身份信息变更）：

```bash
# Gateway 侧：撤销旧配对
openclaw devices revoke <deviceId>

# Node 侧：重启 node run（自动发起新配对请求）
openclaw node run --host <mac-ip> --port 18789
```

### B.11.7 配对状态存储

配对信息存储在 Gateway 的 `~/.openclaw/` 目录：

| 文件 | 内容 |
|------|------|
| `~/.openclaw/nodes/pending.json` | 当前 pending 的配对请求 |
| `~/.openclaw/nodes/paired.json` | 已配对的设备信息（含 token） |

> ⚠️ `paired.json` 包含敏感 token 信息，请妥善保管。

### B.11.8 DM 配对故障排查

| 症状 | 原因 | 解决方案 |
|------|------|---------|
| `devices list` 为空 | Node 未启动或未连接 | 确认 Node 侧 `openclaw node run` 正在运行 |
| `pairing required` | 配对未完成 | 执行 `openclaw devices approve --latest` |
| `bootstrap token invalid` | 配对码过期 | 重新发起配对请求（Node 侧重启） |
| `unauthorized` | Token 错误或已轮换 | 确认使用最新的 token |
| Pending 满额 | 超过 3 个 pending | 等待过期（5分钟）或手动 `reject` |
| 审批后 Node 仍不在线 | Node 需要重启 | Node 侧重启 `openclaw node run` |

**调试命令**：

```bash
# 查看详细配对日志（Gateway 侧）
openclaw gateway logs 2>&1 | grep -i "pair\|device\|pending"

# 查看 Node 侧配对详情
openclaw node status

# 列出所有配对状态
openclaw devices list --json | python3 -m json.tool

# 重置所有配对（慎用）
# Gateway 侧：
rm ~/.openclaw/nodes/pending.json
# Node 侧：
rm ~/.openclaw/node-id.json
openclaw node run ...
```

### B.11.9 配对流程与 Phase 0 Step C 的对应关系

Phase 0 SOP 中的 **Step C**（在 Mac Gateway 上批准配对）即为 DM 配对流程的 Gateway 侧操作。补充如下对应关系：

```
Phase 0 Step C: openclaw devices list
    ↓
    找到 "Ubuntu-GPU-Node" 的 pending request
    ↓
Phase 0 Step C: openclaw devices approve <requestId>
    ↓
    Node 收到 token → 完成 DM pairing
    ↓
Phase 0 Step D: openclaw devices list 验证 online 状态
```

---

## B.13 参考链接

- 官方节点文档：https://docs.openclaw.ai/nodes/index
- 节点故障排查：https://docs.openclaw.ai/nodes/troubleshooting
- Exec Approvals：https://docs.openclaw.ai/tools/exec-approvals
- Gateway 配置：https://docs.openclaw.ai/gateway/configuration
- 节点配对：https://docs.openclaw.ai/gateway/pairing

---

## B.14 常见错误码完整对照表（Gateway + Node）

> 本节从官方 troubleshooting 文档提取，按错误码字母序排列，覆盖 Gateway 运行、节点连接、Exec 执行全链路。

### B.14.1 Gateway 运行层错误码

| 错误码 | 含义 | 排查方向 |
|--------|------|---------|
| `Runtime: stopped` | Gateway 服务进程已停止 | `openclaw gateway status` 查看退出原因 |
| `RPC probe: failed` | Gateway 存活但 RPC 不可达 | 检查 auth/token 是否匹配 |
| `EADDRINUSE` | 端口 18789 被占用 | `lsof -i :18789` 查找冲突进程 |
| `refusing to bind gateway ... without auth` | 非 loopback 绑定但未配置 token | 设置 `gateway.auth.token` 或改用 `bind=loopback` |
| `Gateway start blocked: set gateway.mode=local` | local 模式未启用 | `openclaw config set gateway.mode=local` |
| `another gateway instance is already listening` | 重复启动 | `pkill` 冲突进程后重启 |

### B.14.2 Node 连接层错误码

| 错误码 | 含义 | 排查方向 |
|--------|------|---------|
| `NODE_BACKGROUND_UNAVAILABLE` | Node App 在后台（iOS/Android） | 将 App 切换到前台 |
| `pairing required` | 设备未配对 | `openclaw devices approve <requestId>` |
| `bootstrap token invalid` | 配对码过期 | 重新发起配对请求 |
| `unauthorized` | Token 错误或已轮换 | 确认使用最新 token |
| `Too many pending requests` | 超过 3 个 pending 上限 | 等待 5 分钟或手动 `reject` |

### B.14.3 权限类错误码

| 错误码 | 含义 | 排查方向 |
|--------|------|---------|
| `*_PERMISSION_REQUIRED` | OS 权限缺失 | 到系统设置中授予相机/麦克风/位置权限 |
| `CAMERA_DISABLED` | App 内相机开关关闭 | 在 OpenClaw Node 设置中开启 |
| `LOCATION_DISABLED` | 位置模式关闭 | 在 App 内开启位置模式 |
| `LOCATION_PERMISSION_REQUIRED` | 未授予位置权限 | 授予"使用期间"或"始终"权限 |
| `LOCATION_BACKGROUND_UNAVAILABLE` | App 在后台但仅有"使用期间"权限 | 改为"始终"权限或把 App 切到前台 |
| `SCREEN_RECORDING_PERMISSION_REQUIRED` | 未授予屏幕录制权限 | macOS: 系统偏好设置 → 安全性与隐私 → 隐私 → 屏幕录制 |

### B.14.4 Exec 执行层错误码

| 错误码 | 含义 | 排查方向 |
|--------|------|---------|
| `SYSTEM_RUN_DENIED: approval required` | Exec 需要手动批准 | `openclaw approvals get --node <node>` 查看pending |
| `SYSTEM_RUN_DENIED: allowlist miss` | 命令不在白名单（allowlist 模式） | 添加白名单：`openclaw approvals allowlist add --pattern "/path/to/cmd"` |
| `SYSTEM_RUN_DENIED: security=deny` | 当前安全策略禁止执行 | 调整策略：`openclaw approvals default set --security full` |

### B.14.5 认证层错误码（Dashboard / Control UI 连接）

| Detail code | 含义 | 推荐操作 |
|-------------|------|---------|
| `AUTH_TOKEN_MISSING` | 客户端未发送 token | 在 Control UI 设置中粘贴 token |
| `AUTH_TOKEN_MISMATCH` | Token 与 Gateway 不匹配 | 若 `canRetryWithDeviceToken=true`，允许一次重试；仍失败则执行 token drift recovery |
| `AUTH_DEVICE_TOKEN_MISMATCH` | 缓存的设备 token 已过期或被撤销 | 用 `openclaw devices` 轮换/批准设备 token 后重连 |
| `PAIRING_REQUIRED` | 设备身份已知但未批准此角色 | `openclaw devices list` → `openclaw devices approve <requestId>` |
| `device identity required` | 非安全上下文或缺少设备认证 | 确保通过 HTTPS 或 localhost 连接 |
| `device nonce required / mismatch` | 客户端未完成 challenge-based 设备认证流程 | 客户端需支持 `connect.challenge` + `device.nonce` |
| `device signature invalid / expired` | 设备签名payload错误或时间戳过期 | 刷新 token 配置，重新批准/轮换设备 token |

### B.14.6 WebSocket 连接错误码

| 关闭码 | 含义 | 排查方向 |
|--------|------|---------|
| 1000 | 正常关闭 | Node 被正常停止，无需处理 |
| 1001 | Gateway 不可达（服务器迁移） | Gateway 重启，Node 自动重连 |
| 1006 | 异常关闭（未发送 close 帧） | 网络中断、防火墙掉包、Gateway 崩溃 |
| 1008 | Token 无效 | Token 与 Gateway 不匹配 |
| 1011 | Gateway 内部错误 | 查看 Gateway 日志，尝试 `openclaw gateway restart` |
| 1015 | TLS 错误（wss:// 场景） | 证书问题，确认 Gateway TLS 配置 |

---

## B.15 升级后常见问题（If you upgraded and something suddenly broke）

> 每次升级后如果突然出问题，优先检查以下三个方向。

### B.15.1 Auth 和 URL 覆盖行为变化

```bash
# 检查当前配置
openclaw config get gateway.mode
openclaw config get gateway.remote.url
openclaw config get gateway.auth.mode

# 常见症状
# - gateway connect failed: → URL 目标错误
# - unauthorized → 端点可达但 auth 信息不匹配
# - 若 gateway.mode=remote，CLI 可能指向远程而本地服务正常
```

### B.15.2 Bind 和 Auth guardrails 更严格

```bash
# 检查 bind 配置
openclaw config get gateway.bind
openclaw config get gateway.auth.token

# 关键检查点
# - 非 loopback 绑定（lan/tailnet/custom）需要配置 auth
# - 旧配置 key（如 gateway.token）不自动替代 gateway.auth.token
# - 若 bind=lan 但无 auth → refusing to bind gateway ... without auth
```

### B.15.3 配对和设备身份状态变化

```bash
# 检查设备配对状态
openclaw devices list
openclaw pairing list --channel <channel> --account <id>

# 升级后 pending 可能失效
# - device identity required → 设备 auth 不满足
# - pairing required → 发送者/设备需要批准

# 若配置与运行时状态不一致，强制重装：
openclaw gateway install --force
openclaw gateway restart
```

---

## B.16 Cron / Heartbeat 调度问题排查

> 当定时任务或心跳没有执行或没有送达时使用。

### B.16.1 诊断命令

```bash
# 检查调度器状态
openclaw cron status
openclaw cron list

# 查看任务执行历史
openclaw cron runs --id <jobId> --limit 20

# 查看心跳上次执行情况
openclaw system heartbeat last

# 实时日志
openclaw logs --follow
```

### B.16.2 常见症状

| 症状 | 原因 | 解决方案 |
|------|------|---------|
| `cron: scheduler disabled; jobs will not run automatically` | Cron 被禁用 | 启用：`openclaw cron enable` |
| `cron: timer tick failed` | 调度 tick 失败 | 检查文件/日志/运行时错误 |
| `heartbeat skipped (quiet-hours)` | 在安静时段 | 调整 quiet-hours 配置 |
| `heartbeat skipped (requests-in-flight)` | 有进行中的请求 | 等待完成后重试 |
| `heartbeat: unknown accountId` | 心跳目标 accountId 无效 | 检查心跳投递目标配置 |
| `heartbeat skipped (dm-blocked)` | 投递目标被 block | 调整 `agents.defaults.heartbeat.directPolicy` |

---

## B.17 Browser Tool 故障排查

> 当 browser 工具操作失败但 Gateway 本身健康时使用。

### B.17.1 诊断命令

```bash
# 检查浏览器状态
openclaw browser status

# 启动浏览器（如需要）
openclaw browser start --browser-profile openclaw

# 查看可用 profiles
openclaw browser profiles

# 实时日志
openclaw logs --follow
openclaw doctor
```

### B.17.2 常见症状

| 症状 | 原因 | 解决方案 |
|------|------|---------|
| `Failed to start Chrome CDP on port` | 浏览器进程启动失败 | 检查 Chrome 路径配置 `browser.executablePath` |
| `browser.executablePath not found` | 路径无效 | 修正配置中的可执行文件路径 |
| `No Chrome tabs found for profile="user"` | Chrome MCP attach profile 没有可用的本地标签页 | 确认目标 Chrome 已打开且启用了远程调试端口 |
| `Browser attachOnly is enabled ... not reachable` | attach-only profile 无可连接目标 | 确认 Chrome 调试端口可达 |

---

## B.18 快速恢复循环（Fast Recovery Loop）

> 遇到任何节点相关问题时，优先执行以下诊断阶梯：

```bash
# 第一层：基础状态
openclaw nodes status
openclaw nodes describe --node <idOrNameOrIp>
openclaw approvals get --node <idOrNameOrIp>

# 第二层：实时日志
openclaw logs --follow

# 第三层：Gateway 状态
openclaw gateway status
openclaw doctor

# 若仍未解决，依次尝试：
# 1. 重新批准设备配对
openclaw devices approve --latest

# 2. 将 Node App 切换到前台（iOS/Android）

# 3. 重新授予 OS 权限（相机/麦克风/位置/屏幕录制）

# 4. 重建/调整 exec approval 策略
openclaw approvals default set --node "Ubuntu-GPU-Node" --security full
```

---

## B.19 命令阶梯（Command Ladder）- Phase 0 专项

> 在 Phase 0 Gateway 对接场景中，按以下顺序执行诊断：

```bash
# 层级 1：Gateway 自身状态
openclaw status
openclaw gateway status
openclaw doctor

# 层级 2：节点连接状态
openclaw nodes status
openclaw devices list

# 层级 3：配对状态
openclaw nodes describe --node "Ubuntu-GPU-Node"
# 关注字段：status(online/paired)、transport(websocket)、latency(<50ms)

# 层级 4：Exec 链路
openclaw approvals get --node "Ubuntu-GPU-Node"
openclaw exec --host node --node "Ubuntu-GPU-Node" -- uname -a

# 层级 5：WebSocket 链路
# （参见 B.12 节完整验证清单）

# 层级 6：GPU（如果可用）
nvidia-smi
python3 -c "import torch; print('CUDA:', torch.cuda.is_available())"
```

**正常信号：**
- `openclaw gateway status` → `Runtime: running`，`RPC probe: ok`
- `openclaw nodes status` → Ubuntu-GPU-Node: **online**
- `openclaw devices list` → Ubuntu-GPU-Node: **paired**
- `curl http://<mac-ip>:18789/health` → `{"status":"ok"}`
- `openclaw exec --host node --node "Ubuntu-GPU-Node" -- echo OK` → 输出 OK
