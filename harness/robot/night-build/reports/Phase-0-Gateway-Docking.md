# Phase 0：Ubuntu 台机对接 OpenClaw Gateway

## 百科全书级操作手册

---

## 1. 任务概述

### Phase 0 是什么
Phase 0 是将 Ubuntu 台机配置为 **OpenClaw Node（节点）**，通过 LAN 连接 MacBook Pro 上运行的 OpenClaw Gateway，使 Ubuntu 机器能够接受来自 Gateway 的任务调度和执行指令。

### 要达成什么状态
```
┌─────────────────────────────────────────────────────────────┐
│                      MacBook Pro                            │
│                  OpenClaw Gateway                           │
│                   端口: 18789                                │
│                   Bind: LAN                                 │
│                   Token: 已配置                              │
└──────────────────────┬──────────────────────────────────────┘
                       │  同一局域网 (LAN)
                       │  TCP 18789
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                      Ubuntu 台机                             │
│               OpenClaw Node (早期版本需升级)                 │
│           openclaw node run --host <mac-ip> --port 18789   │
└─────────────────────────────────────────────────────────────┘
```

**验收标准**：
- Ubuntu 上 `openclaw nodes status` 显示 `connected`
- Mac 上 `openclaw devices list` 显示该 Ubuntu 节点已连接且已 approved
- Ubuntu 可接受并执行 Gateway 下发的任务

---

## 2. 前置条件：Ubuntu 24.04 环境检查

### Step A - 确认网络连通性（Ubuntu 侧执行）

```bash
# 检查本机 IP 地址（确认在 LAN 内）
ip addr show | grep "inet " | grep -v "127.0.0.1"

# 示例输出：inet 192.168.1.100/24 brd 192.168.1.255 scope global dynamic
# 记录这个 IP，后面用 <ubuntu-ip> 代替

# 从 Ubuntu ping Mac（先获取 Mac 的 IP，见下方"Mac 侧"章节）
ping -c 3 <mac-ip>

# 检查端口连通性
nc -zv <mac-ip> 18789
# 期望输出：Connection to <mac-ip> 18789 port [tcp/*] succeeded!
```

### Step B - 确认 SSH 客户端已安装（Ubuntu 侧执行）

```bash
# Ubuntu 24.04 通常已预装 openssh-client
which ssh
ssh -V
# 期望输出：OpenSSH_9.x 或更高版本
```

### Step C - 确认 openclaw CLI 已安装（Ubuntu 侧执行）

```bash
# 检查 openclaw 是否存在
which openclaw

# 如果不存在，安装它
# 方法1：npm 全局安装
npm install -g openclaw

# 方法2：下载官方二进制
# 访问 https://github.com/xxx/openclaw/releases 下载 Linux 版本

# 检查版本（确认不是过旧的早期版本）
openclaw --version

# 预期：2026.3.x 或接近 Mac 的版本（2026.3.13）
# 如果版本差距过大，见「5. Ubuntu 侧 openclaw 升级/配置」章节
```

### Step D - 确认 SSH 服务可访问 Mac（Ubuntu 侧执行）

```bash
# 测试 SSH 到 Mac（Mac 必须开启远程登录：系统设置 → 通用 → 共享 → 远程登录）
ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no lr@<mac-ip> "echo 'SSH OK'"
# 如果失败，见「3. SSH 配置」章节
```

---

## 3. SSH 配置（从零开始）

> **目标**：在 Ubuntu 和 Mac 之间配置基于密钥的免密码 SSH 登录。
> Ubuntu 作为客户端，Mac 作为服务器（开启远程登录）。

### 3.1 Mac 侧：开启远程登录

```bash
# 方法1：命令行（需要管理员权限）
sudo launchctl load -w /System/Library/LaunchDaemons/ssh.plist

# 方法2：macOS 系统设置
# → 系统设置 → 通用 → 共享 → 开启"远程登录"
# → 允许访问：仅当前用户 或 所有用户
```

**验证 Mac SSH 状态**：
```bash
sudo launchctl list | grep ssh
# 预期：- 0 com.openssh.sshd（存在即为运行中）

# 测试 Mac 本地 SSH
ssh -o ConnectTimeout=5 localhost
# 如果失败：sudo systemsetup -f setremotelogin on
```

### 3.2 Ubuntu 侧：生成 SSH 密钥对

```bash
# 检查是否已有密钥
ls -la ~/.ssh/

# 如果已有 id_ed25519 或 id_rsa，跳过此步

# 生成新的 ED25519 密钥（推荐）
ssh-keygen -t ed25519 -C "ubuntu-node-$(hostname)" -f ~/.ssh/id_ed25519 -N ""

# 密钥存放位置：
#   公钥：~/.ssh/id_ed25519.pub
#   私钥：~/.ssh/id_ed25519
```

### 3.3 Ubuntu 侧：将公钥复制到 Mac

```bash
# 方法1：ssh-copy-id（最简单）
ssh-copy-id -i ~/.ssh/id_ed25519.pub lr@<mac-ip>

# 方法2：手动复制
# Step A - 查看公钥
cat ~/.ssh/id_ed25519.pub
# 输出类似：ssh-ed25519 AAAA...xxx ubuntu-node-hostname

# Step B - 手动追加到 Mac 的 ~/.ssh/authorized_keys
# 先 SSH 到 Mac（需要输入密码，这是最后一次）
ssh lr@<mac-ip> "mkdir -p ~/.ssh && chmod 700 ~/.ssh"

# Step C - 用 scp 或管道复制公钥
# 在 Ubuntu 上执行：
cat ~/.ssh/id_ed25519.pub | ssh lr@<mac-ip> "cat >> ~/.ssh/authorized_keys"

# Step D - 设置正确权限（Mac 侧执行）
ssh lr@<mac-ip> "chmod 600 ~/.ssh/authorized_keys && chmod 700 ~/.ssh"
```

### 3.4 验证无密码登录

```bash
# 从 Ubuntu SSH 到 Mac，应该不再需要密码
ssh -o ConnectTimeout=5 lr@<mac-ip> "echo 'Passwordless SSH OK'"
# 预期输出：Passwordless SSH OK
```

### 3.5 SSH 配置优化（可选但推荐）

```bash
# 在 Ubuntu 上编辑 ~/.ssh/config
cat >> ~/.ssh/config << 'EOF'
Host macbook
    HostName <mac-ip>
    User lr
    IdentityFile ~/.ssh/id_ed25519
    AddKeysToAgent yes
    ServerAliveInterval 60
    ServerAliveCountMax 3
EOF

# 之后可以用简化命令
ssh macbook "echo OK"
```

---

## 4. Gateway 配置：Mac 侧

> **关键问题**：Mac 的 OpenClaw Gateway 当前 `bind: "loopback"`，只允许本机进程连接。Ubuntu 在另一台机器上，必须改为 `bind: "lan"`。

### 4.1 检查当前 Gateway 配置

```bash
# 在 Mac 上执行
openclaw config get gateway.bind
openclaw config get gateway.port
openclaw config get gateway.auth.mode
openclaw config get gateway.auth.token

# 当前值（已知）：
# gateway.bind = "loopback"      ← 这是问题所在！
# gateway.port = 18789
# gateway.auth.mode = "token"
# gateway.auth.token = "235bf68c2288bfde322b8567509fb0e4d8eb368ec3c70000"
```

### 4.2 修改 Gateway Bind 地址

```bash
# Step A - 备份当前配置
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak.$(date +%Y%m%d%H%M%S)

# Step B - 修改 bind 为 lan
openclaw config set gateway.bind lan

# Step C - 验证修改
openclaw config get gateway.bind
# 预期输出：lan

# Step D - 重启 Gateway 使配置生效
openclaw gateway restart

# 或者如果 gateway 是 systemd 服务：
sudo systemctl restart openclaw
```

### 4.3 确认 Mac 的 LAN IP 地址

```bash
# 在 Mac 上执行
ipconfig getifaddr en0
# 或
ip addr show en0 | grep "inet " | awk '{print $2}'

# 示例输出：192.168.1.101
# 记录这个 IP，后面作为 <mac-ip>
```

### 4.4 验证 Gateway 监听状态

```bash
# 确认 Gateway 在 LAN 接口上监听
sudo lsof -i :18789 | grep LISTEN
# 预期输出包含 0.0.0.0:18789 或 192.168.1.101:18789
# 注意：127.0.0.1:18789 = loopback only（错误）
#      0.0.0.0:18789 或 <lan-ip>:18789 = LAN 监听（正确）

# 如果看到的是 127.0.0.1，重启 Gateway 后再检查
```

### 4.5 生成配对 QR/代码（可选，用于验证）

```bash
# 查看当前 gateway 的连接信息
openclaw qr --json

# 检查输出中的 gatewayUrl 和 urlSource
# urlSource 应该是 "gateway.bind=lan" 才正确
```

---

## 5. Ubuntu 侧 openclaw 升级/配置

### 5.1 检查当前版本

```bash
# 在 Ubuntu 上执行
openclaw --version
```

### 5.2 升级路径选择

**场景 A：openclaw 已安装但版本较旧**

```bash
# npm 升级
npm update -g openclaw

# 或重新安装
npm install -g openclaw@latest

# 验证版本
openclaw --version
```

**场景 B：openclaw 完全不存在**

```bash
# 方法1：npm 安装（需要 Node.js 18+）
# 检查 Node.js 版本
node -v
# 如果低于 18，先安装 Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# 然后安装 openclaw
npm install -g openclaw

# 方法2：下载官方二进制（推荐，生产环境）
# 访问 GitHub releases 页面下载 Linux x64 二进制
# https://github.com/openclaw/openclaw/releases

# 以 GitHub releases 下载为例：
cd /tmp
wget https://github.com/openclaw/openclaw/releases/download/v2026.3.13/openclaw-linux-x64.tar.gz
tar -xzf openclaw-linux-x64.tar.gz
sudo mv openclaw /usr/local/bin/
sudo chmod +x /usr/local/bin/openclaw

# 验证
openclaw --version
```

**场景 C：使用 nvm 管理版本**

```bash
# 安装 nvm（如果尚未安装）
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc

# 安装并使用最新 LTS Node.js
nvm install --lts
nvm use --lts

# 安装 openclaw
npm install -g openclaw

# 验证
openclaw --version
```

### 5.3 Ubuntu 侧基础配置

```bash
# 登录/认证（如果是首次在这台机器上使用 openclaw）
openclaw auth login

# 配置默认模型（可选）
openclaw config set agents.defaults.model "minimax/MiniMax-M2.7"

# 检查节点状态
openclaw nodes status
# 预期：Not connected（尚未连接）
```

---

## 6. 完整对接流程

### 流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                     Phase 0 执行流程                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [1] Mac 侧准备                                                   │
│      ├─ 开启远程登录（SSH）                                       │
│      ├─ 检查 gateway.bind（当前=loopback，需改为 lan）           │
│      └─ 获取 Mac LAN IP                                          │
│                                                                  │
│  [2] Ubuntu 侧准备                                               │
│      ├─ 网络连通性测试                                            │
│      ├─ 安装/升级 openclaw                                       │
│      └─ SSH 密钥配置（无密码登录 Mac）                            │
│                                                                  │
│  [3] Gateway 配置修正（Mac 侧）                                   │
│      ├─ 备份 openclaw.json                                       │
│      ├─ openclaw config set gateway.bind lan                    │
│      └─ openclaw gateway restart                                 │
│                                                                  │
│  [4] 启动 Node 连接（Ubuntu 侧）                                  │
│      ├─ openclaw node run --host <mac-ip> --port 18789          │
│      └─ 输入 Token 或通过配置文件指定                             │
│                                                                  │
│  [5] 配对审批（Mac 侧）                                           │
│      ├─ openclaw devices list                                    │
│      ├─ openclaw devices approve --latest                       │
│      └─ 验证连接状态                                              │
│                                                                  │
│  [6] 验证对接成功                                                 │
│      └─ 双向确认 connected 状态                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Step-by-Step 执行命令

#### Step 1：Mac 侧 - 开启远程登录

```bash
# 在 Mac 上执行
sudo launchctl load -w /System/Library/LaunchDaemons/ssh.plist

# 验证
sudo launchctl list | grep sshd
```

#### Step 2：Mac 侧 - 检查并修改 Gateway Bind

```bash
# 在 Mac 上执行
openclaw config get gateway.bind
# 当前输出：loopback

# 修改为 lan
openclaw config set gateway.bind lan

# 验证
openclaw config get gateway.bind
# 预期输出：lan

# 重启 Gateway
openclaw gateway restart

# 如果是 systemd 服务
# sudo systemctl restart openclaw
```

#### Step 3：Mac 侧 - 获取 LAN IP

```bash
# 在 Mac 上执行
ipconfig getifaddr en0
# 记录输出，例如：192.168.1.101
# 后续命令中用 <mac-ip> 代替此地址
```

#### Step 4：Ubuntu 侧 - 网络连通性测试

```bash
# 在 Ubuntu 上执行
nc -zv <mac-ip> 18789
# 预期：succeeded!

# 如果失败：检查防火墙
sudo ufw status
# 如果启用：sudo ufw allow 18789/tcp
```

#### Step 5：Ubuntu 侧 - SSH 无密码配置

```bash
# 在 Ubuntu 上执行
# 确认有密钥
ls ~/.ssh/id_ed25519.pub || ssh-keygen -t ed25519 -C "ubuntu-node-$(hostname)" -f ~/.ssh/id_ed25519 -N ""

# 复制公钥到 Mac
ssh-copy-id -i ~/.ssh/id_ed25519.pub lr@<mac-ip>

# 验证无密码登录
ssh lr@<mac-ip> "echo 'SSH OK'"
```

#### Step 6：Ubuntu 侧 - 升级 openclaw（如需要）

```bash
# 在 Ubuntu 上执行
openclaw --version

# 如果版本低于 2026.3.0，升级
npm update -g openclaw

# 或重装
npm install -g openclaw@latest

# 验证
openclaw --version
```

#### Step 7：Ubuntu 侧 - 创建 Token 配置文件（避免每次输入）

```bash
# 在 Ubuntu 上执行
mkdir -p ~/.openclaw

cat > ~/.openclaw/node.json << 'EOF'
{
  "gateway": {
    "host": "<mac-ip>",
    "port": 18789,
    "auth": {
      "token": "235bf68c2288bfde322b8567509fb0e4d8eb368ec3c70000"
    }
  }
}
EOF

# 或直接通过环境变量
export OPENCLAW_GATEWAY_TOKEN="235bf68c2288bfde322b8567509fb0e4d8eb368ec3c70000"
```

#### Step 8：Ubuntu 侧 - 启动 Node 连接

```bash
# 在 Ubuntu 上执行
# 方式1：命令行参数
openclaw node run --host <mac-ip> --port 18789 --token "235bf68c2288bfde322b8567509fb0e4d8eb368ec3c70000"

# 方式2：使用配置文件（已在上一步创建）
openclaw node run

# 方式3：交互式启动（首次推荐，可看到实时日志）
openclaw node run --host <mac-ip> --port 18789

# 预期输出：
# [OpenClaw] Node connecting to gateway at <mac-ip>:18789
# [OpenClaw] Node connected successfully
# [OpenClaw] Waiting for pairing approval from gateway...
```

#### Step 9：Mac 侧 - 审批配对请求

```bash
# 在 Mac 上执行
# 查看待审批设备
openclaw devices list

# 审批最新的配对请求
openclaw devices approve --latest

# 或者指定设备 ID
# openclaw devices approve <device-id>

# 验证审批结果
openclaw devices list
# 预期：Ubuntu 节点状态变为 "approved" 或 "connected"
```

#### Step 10：验证对接成功

```bash
# 在 Mac 上执行
openclaw nodes status
# 预期：显示已连接的节点信息

openclaw devices list
# 预期：Ubuntu 节点状态为 connected

# 在 Ubuntu 上执行
openclaw nodes status
# 预期：显示 connected 到 gateway

# 测试任务下发（可选）
# 在 Mac 上执行测试任务
openclaw node run --host <mac-ip> --port 18789 --test
```

---

## 7. 所有可能遇到的问题/意外

### 7.1 SSH 连接失败

#### 问题 7.1.1：Mac SSH 服务未开启

**症状**：`Connection refused` 或 `Connection timed out`

**Step A - 诊断**：
```bash
# Ubuntu 侧执行
nc -zv <mac-ip> 22
# 预期：succeeded! 如果失败，继续 Step B
```

**Step B - 开启 Mac SSH**：
```bash
# 方法1：命令行
sudo launchctl load -w /System/Library/LaunchDaemons/ssh.plist

# 方法2：系统偏好设置（macOS 旧版）
# 苹果菜单 → 系统偏好设置 → 共享 → 勾选"远程登录"

# 方法3：系统设置（macOS Ventura+）
# 系统设置 → 通用 → 共享 → 开启"远程登录"
```

**Step C - 验证服务状态**：
```bash
sudo launchctl list | grep sshd
# 预期：- 0 com.openssh.sshd
```

**Step D - 再次测试连接**：
```bash
nc -zv <mac-ip> 22
# 预期：succeeded!
```

---

#### 问题 7.1.2：SSH 密钥认证失败

**症状**：仍然提示输入密码，或 `Permission denied (publickey)`

**Step A - 诊断**：
```bash
# Ubuntu 侧执行
ssh -v lr@<mac-ip> "echo test" 2>&1 | grep -i "publickey\|permission denied"
# 查看详细日志
```

**Step B - 检查密钥权限**：
```bash
# Ubuntu 侧
ls -la ~/.ssh/
# 预期：id_ed25519 权限 600，id_ed25519.pub 权限 644

# 如果权限不对
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub
```

**Step C - 检查 Mac authorized_keys**：
```bash
# Ubuntu 侧测试
ssh lr@<mac-ip> "ls -la ~/.ssh/ && cat ~/.ssh/authorized_keys"
# 检查公钥是否在 authorized_keys 中
```

**Step D - 重新添加密钥**：
```bash
# Ubuntu 侧
ssh-copy-id -i ~/.ssh/id_ed25519.pub lr@<mac-ip>

# 或手动
cat ~/.ssh/id_ed25519.pub | ssh lr@<mac-ip> "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
ssh lr@<mac-ip> "chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"
```

---

#### 问题 7.1.3：SSH 连接超时

**症状**：`Connection timed out`

**Step A - 诊断**：
```bash
# Ubuntu 侧
ping -c 3 <mac-ip>
# 如果 ping 不通，网络层面有问题
```

**Step B - 检查网络**：
```bash
# 确认 Mac 和 Ubuntu 在同一子网
# Mac: ipconfig getifaddr en0
# Ubuntu: ip addr show | grep "inet "

# 检查路由器/交换机
# 如果在不同 VLAN，需要网络设备配置
```

**Step C - 检查 Mac 防火墙**：
```bash
# Mac 侧
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
# 如果开启：sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate off
```

**Step D - 确认 SSH 端口**：
```bash
# Mac 侧
sudo lsof -i :22 | grep LISTEN
# 确认在 0.0.0.0:22 或 <lan-ip>:22 监听
# 如果只在 127.0.0.1:22，需要修改 SSH 配置
```

---

### 7.2 Gateway Bind 地址问题（loopback vs lan）

#### 问题 7.2.1：Gateway 绑定在 loopback，Ubuntu 无法连接

**症状**：
```
[OpenClaw] Node connection failed: ECONNREFUSED
[OpenClaw] Gateway at <mac-ip>:18789 refused connection
```

**Step A - 诊断**：
```bash
# Mac 侧
openclaw config get gateway.bind
# 预期：loopback（这就是问题！）

# 检查监听地址
sudo lsof -i :18789 | grep LISTEN
# 预期：只有 127.0.0.1:18789 或 ::1:18789
```

**Step B - 修改 Bind 配置**：
```bash
# Mac 侧
openclaw config set gateway.bind lan

# 验证
openclaw config get gateway.bind
# 预期：lan
```

**Step C - 重启 Gateway**：
```bash
# Mac 侧
openclaw gateway restart

# 检查是否监听在 LAN 接口
sudo lsof -i :18789 | grep LISTEN
# 预期：0.0.0.0:18789 或 <lan-ip>:18789
```

**Step D - 验证修复**：
```bash
# Ubuntu 侧
nc -zv <mac-ip> 18789
# 预期：succeeded!

# 重新启动 node
openclaw node run --host <mac-ip> --port 18789 --token "235bf68c2288bfde322b8567509fb0e4d8eb368ec3c70000"
```

---

### 7.3 Token 不匹配

#### 问题 7.3.1：Token 被拒绝

**症状**：
```
[OpenClaw] Authentication failed: Invalid token
[OpenClaw] Gateway rejected connection: 401 Unauthorized
```

**Step A - 诊断**：
```bash
# Mac 侧 - 确认正确的 token
openclaw config get gateway.auth.token
# 预期：235bf68c2288bfde322b8567509fb0e4d8eb368ec3c70000

# Ubuntu 侧 - 检查使用的 token
# 检查配置文件
cat ~/.openclaw/node.json 2>/dev/null | grep token
```

**Step B - 确认 Token 一致**：
```bash
# Ubuntu 侧
# 确保使用的 token 与 Mac 侧一致
# Token: 235bf68c2288bfde322b8567509fb0e4d8eb368ec3c70000

# 如果不确定，可以在命令行明确指定
openclaw node run --host <mac-ip> --port 18789 --token "235bf68c2288bfde322b8567509fb0e4d8eb368ec3c70000"
```

**Step C - 检查 Token 模式**：
```bash
# Mac 侧
openclaw config get gateway.auth.mode
# 预期：token

# 如果是其他模式（如 password），需要调整
```

**Step D - 重新生成 Token（如需要）**：
```bash
# Mac 侧 - 谨慎操作，会影响所有使用旧 token 的设备
openclaw gateway regenerate-token

# 获取新 token
openclaw config get gateway.auth.token

# 通知所有节点使用新 token
```

---

### 7.4 防火墙阻挡

#### 问题 7.4.1：Ubuntu 防火墙阻止连接

**症状**：`Connection timed out` 或 `No route to host`

**Step A - 诊断**：
```bash
# Ubuntu 侧
sudo ufw status
# 如果是 active，继续 Step B
```

**Step B - 开放必要端口**：
```bash
# Ubuntu 侧
# 开放 SSH（22端口）
sudo ufw allow 22/tcp

# 开放 Gateway 端口（18789）
sudo ufw allow 18789/tcp

# 开放后验证
sudo ufw status
```

**Step C - 如果不需要防火墙**：
```bash
# Ubuntu 侧
sudo ufw disable
# 注意：生产环境不建议完全禁用防火墙
```

**Step D - 验证连接**：
```bash
# Ubuntu 侧
nc -zv <mac-ip> 18789
# 预期：succeeded!
```

---

#### 问题 7.4.2：Mac 防火墙阻止入站连接

**症状**：Ubuntu 无法连接到 Mac 的 18789 端口

**Step A - 诊断**：
```bash
# Mac 侧 - 检查防火墙
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
```

**Step B - 添加 SSH 和 openclaw 到防火墙例外**：
```bash
# Mac 侧
# 添加 SSH
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/sbin/sshd
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblock /usr/sbin/sshd

# 添加 openclaw（需要找到 openclaw 二进制路径）
which openclaw
# 假设输出：/usr/local/bin/openclaw
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/local/bin/openclaw
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblock /usr/local/bin/openclaw
```

**Step C - 重启 Firewall**：
```bash
# Mac 侧
sudo launchctl unload /System/Library/LaunchDaemons/com.apple.alf.agent.plist
sudo launchctl load /System/Library/LaunchDaemons/com.apple.alf.agent.plist
```

**Step D - 验证**：
```bash
# Ubuntu 侧
nc -zv <mac-ip> 18789
```

---

### 7.5 openclaw 版本兼容问题

#### 问题 7.5.1：Ubuntu 上的 openclaw 版本过旧

**症状**：
```
[OpenClaw] Node failed to connect: Protocol version mismatch
[OpenClaw] Gateway requires version 2026.3.x, but node is 2025.x
```

**Step A - 诊断**：
```bash
# Ubuntu 侧
openclaw --version
# Mac 侧
openclaw --version

# 对比两个版本
```

**Step B - Ubuntu 升级 openclaw**：
```bash
# Ubuntu 侧
npm update -g openclaw

# 或指定版本
npm install -g openclaw@2026.3.13

# 验证
openclaw --version
```

**Step C - 如果 npm 不可用，手动下载**：
```bash
# Ubuntu 侧
cd /tmp
wget https://github.com/openclaw/openclaw/releases/download/v2026.3.13/openclaw-linux-x64.tar.gz
tar -xzf openclaw-linux-x64.tar.gz
sudo mv openclaw /usr/local/bin/
sudo chmod +x /usr/local/bin/openclaw

# 验证
/usr/local/bin/openclaw --version
```

**Step D - 清理旧版本缓存**：
```bash
# Ubuntu 侧
npm cache clean --force
hash -r
# 重新测试
openclaw --version
```

---

### 7.6 Pairing 审批问题

#### 问题 7.6.1：Node 连接成功但显示 "pairing required"

**症状**：
```
[OpenClaw] Node connected successfully
[OpenClaw] Waiting for pairing approval from gateway...
[OpenClaw] Gateway requires pairing approval. Use 'openclaw devices approve <device-id>' on the gateway.
```

**Step A - 诊断**：
```bash
# Mac 侧
openclaw devices list
# 查看是否有 pending 状态的设备
```

**Step B - 审批设备**：
```bash
# Mac 侧
# 列出所有设备
openclaw devices list

# 审批最新的设备
openclaw devices approve --latest

# 或指定设备 ID
# openclaw devices approve <device-id>
```

**Step C - 检查审批结果**：
```bash
# Mac 侧
openclaw devices list
# 确认设备状态变为 approved 或 connected
```

**Step D - 节点侧验证**：
```bash
# Ubuntu 侧
# Node 会自动检测到审批完成
# 等待几秒后检查状态
openclaw nodes status
# 预期：connected
```

---

#### 问题 7.6.2：配对请求未出现在列表中

**症状**：`openclaw devices list` 显示空或没有新设备

**Step A - 确认节点正在运行**：
```bash
# Ubuntu 侧
ps aux | grep openclaw | grep node
# 确认 node 进程存在
```

**Step B - 检查节点日志**：
```bash
# Ubuntu 侧
# 如果 node 在前台运行，查看日志输出
# 如果是 systemd 服务
journalctl -u openclaw-node -f

# 检查是否有连接错误
```

**Step C - 重新启动节点**：
```bash
# Ubuntu 侧
# 停止现有 node
pkill -f "openclaw node"

# 重新启动
openclaw node run --host <mac-ip> --port 18789 --token "235bf68c2288bfde322b8567509fb0e4d8eb368ec3c70000"

# 立即在 Mac 侧检查设备列表
openclaw devices list
```

**Step D - 检查时间同步**：
```bash
# 确保 Mac 和 Ubuntu 时间一致
# 时间差过大可能导致 token 验证失败
# Ubuntu 侧
sudo timedatectl status
sudo timedatectl set-ntp true

# Mac 侧
# 系统偏好设置 → 日期与时间 → 勾选自动设置
```

---

### 7.7 systemd 服务问题

#### 问题 7.7.1：openclaw-node 服务启动失败

**症状**：`systemctl start openclaw-node` 失败或 `journalctl -u openclaw-node` 显示错误

**Step A - 诊断**：
```bash
# Ubuntu 侧
sudo systemctl status openclaw-node
journalctl -u openclaw-node -n 50
```

**Step B - 常见错误及修复**：

**错误 1：Unit 文件不存在**
```bash
# 创建 systemd service 文件
cat > /tmp/openclaw-node.service << 'EOF'
[Unit]
Description=OpenClaw Node Service
After=network.target

[Service]
Type=simple
User=lr
ExecStart=/usr/local/bin/openclaw node run --host <mac-ip> --port 18789 --token "235bf68c2288bfde322b8567509fb0e4d8eb368ec3c70000"
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/openclaw-node.service /etc/systemd/system/openclaw-node.service
sudo systemctl daemon-reload
sudo systemctl enable openclaw-node
```

**错误 2：权限问题**
```bash
# 检查 openclaw 二进制权限
ls -la $(which openclaw)
# 如果没有执行权限
sudo chmod +x $(which openclaw)

# 检查 node.json 配置权限
chmod 600 ~/.openclaw/node.json
```

**错误 3：环境变量问题**
```bash
# 在 service 文件中指定环境变量
# 编辑 /etc/systemd/system/openclaw-node.service
# 在 [Service] 下添加：
Environment="OPENCLAW_GATEWAY_TOKEN=235bf68c2288bfde322b8567509fb0e4d8eb368ec3c70000"
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
```

**Step C - 重启服务**：
```bash
# Ubuntu 侧
sudo systemctl daemon-reload
sudo systemctl restart openclaw-node

# 检查状态
sudo systemctl status openclaw-node
```

**Step D - 验证服务运行**：
```bash
# Ubuntu 侧
ps aux | grep openclaw
# 或
sudo systemctl status openclaw-node
# 预期：active (running)
```

---

## 8. 验证方法

### 8.1 Mac 侧验证

```bash
# 检查 Gateway 状态
openclaw gateway status
# 预期：running, bind: lan, port: 18789

# 检查已连接设备
openclaw devices list
# 预期：显示 Ubuntu 节点，状态为 connected 或 approved

# 检查节点列表
openclaw nodes status
# 预期：显示已连接的节点信息

# 查看实时日志（可选）
openclaw gateway logs --follow
```

### 8.2 Ubuntu 侧验证

```bash
# 检查节点状态
openclaw nodes status
# 预期：connected to <mac-ip>:18789

# 测试任务下发（从 Mac）
# 在 Mac 上执行
openclaw node exec --node <node-id> -- echo "Hello from Gateway"

# Ubuntu 侧查看输出
# 预期：在 Mac 侧看到 "Hello from Gateway"
```

### 8.3 网络层面验证

```bash
# Ubuntu 侧 - 端口连通性
nc -zv <mac-ip> 18789
# 预期：succeeded!

# Mac 侧 - 确认监听
sudo lsof -i :18789 | grep LISTEN
# 预期：0.0.0.0:18789 或 <mac-ip>:18789
```

### 8.4 完整流程验证

```bash
# 1. Mac 重启 Gateway
openclaw gateway restart

# 2. Ubuntu 启动 Node
openclaw node run --host <mac-ip> --port 18789 --token "235bf68c2288bfde322b8567509fb0e4d8eb368ec3c70000"

# 3. Mac 审批
openclaw devices list
openclaw devices approve --latest

# 4. 双向验证
# Mac: openclaw nodes status
# Ubuntu: openclaw nodes status

# 预期：两边都显示 connected
```

---

## 9. 风险点

### 高风险（可能搞崩环境）

#### 风险 1：修改 Mac openclaw.json 格式错误

**风险描述**：
手动编辑 `~/.openclaw/openclaw.json` 可能导致 JSON 语法错误，使 Gateway 无法启动。

**预防措施**：
- 永远使用 `openclaw config set` 命令修改配置，而不是直接编辑 JSON
- 修改前务必备份：`cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak.$(date +%Y%m%d)`

**修复方法**：
```bash
# 恢复备份
cp ~/.openclaw/openclaw.json.bak.20260326 ~/.openclaw/openclaw.json
openclaw gateway restart
```

#### 风险 2：Gateway 绑定到 0.0.0.0 暴露公网

**风险描述**：
设置为 `bind: lan` 后，如果 Mac 有公网 IP 或在 DMZ，Gateway 可能被公网访问。

**预防措施**：
- 仅在受信任的 LAN 环境下操作
- 使用 token 认证
- 考虑使用 `gateway.auth.allowTailscale: true` 限制仅 Tailscale 用户访问

**检查方法**：
```bash
# 确认 Mac 没有公网直连
ipconfig getifaddr en0
# 确认是私有 IP（192.168.x.x, 10.x.x.x, 172.16-31.x.x）
```

#### 风险 3：SSH 配置错误导致 Mac 无法远程登录

**风险描述**：
修改 `/etc/ssh/sshd_config` 错误可能导致 SSH 服务无法启动，或 Mac 被锁在系统偏好设置界面。

**预防措施**：
- 永远保留当前配置的备份
- 使用 `openclaw config` 而不是直接编辑 sshd_config
- 修改前通过 `sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup` 备份

**修复方法**：
```bash
# 如果 SSH 配置出错，恢复备份
sudo cp /etc/ssh/sshd_config.backup /etc/ssh/sshd_config
sudo launchctl unload /System/Library/LaunchDaemons/ssh.plist
sudo launchctl load /System/Library/LaunchDaemons/ssh.plist
```

### 中等风险

#### 风险 4：Ubuntu 升级 openclaw 导致环境冲突

**claw 环境冲突

**风险描述**：
npm 全局安装可能与系统现有的 Node.js 版本冲突。

**预防措施**：
- 升级前记录当前 openclaw 路径：`which openclaw`
- 记录当前配置：`openclaw config export > ~/openclaw-config-backup.json`

**修复方法**：
```bash
# 如果升级后出问题，恢复路径
hash -r
# 或重新指定路径
export PATH="/usr/local/bin:$PATH"
```

#### 风险 5：systemd 服务配置错误导致开机失败

**风险描述**：
错误的 systemd service 文件可能导致系统启动变慢或进入紧急模式。

**预防措施**：
- 在创建 service 文件前先备份现有配置
- 使用 `systemd-analyze verify` 检查语法

**修复方法**：
```bash
# 如果系统启动受影响
# 1. 重启时在 GRUB 菜单按 e
# 2. 在 linux 行末尾添加 systemd.unit=emergency.target
# 3. 按 Ctrl+X 启动
# 4. 修复或删除错误的 service 文件
sudo rm /etc/systemd/system/openclaw-node.service
sudo systemctl daemon-reload
sudo reboot
```

### 低风险

#### 风险 6：Token 泄露

**风险描述**：
Token 出现在日志、shell 历史或配置文件中被他人获取。

**预防措施**：
- 使用环境变量代替配置文件中的明文 token
- 定期更换 token
- 不要将 token 提交到 git 仓库

**修复方法**：
```bash
# 重新生成 token
openclaw gateway regenerate-token
# 更新所有使用旧 token 的节点
```

#### 风险 7：端口冲突

**风险描述**：
18789 端口被其他程序占用。

**预防措施**：
- 执行前检查端口占用：`sudo lsof -i :18789`

**修复方法**：
```bash
# 找出占用端口的进程
sudo lsof -i :18789

# 停止该进程或使用其他端口
# 如果要使用其他端口：
# Mac 侧：openclaw config set gateway.port 18790
# Ubuntu 侧：openclaw node run --host <mac-ip> --port 18790
```

---

## 附录 A：快速检查清单

在开始 Phase 0 之前，在 Mac 上执行以下检查：

```bash
# 1. 确认 Gateway 正在运行
openclaw gateway status

# 2. 确认 bind 设置
openclaw config get gateway.bind
# 如果是 loopback，需要改为 lan

# 3. 确认 token
openclaw config get gateway.auth.token
# 应该显示：235bf68c2288bfde322b8567509fb0e4d8eb368ec3c70000

# 4. 确认 Mac LAN IP
ipconfig getifaddr en0
# 记录这个 IP

# 5. 确认 SSH 已开启
sudo launchctl list | grep sshd
```

在 Ubuntu 上执行以下检查：

```bash
# 1. 确认网络可达 Mac
nc -zv <mac-ip> 22
nc -zv <mac-ip> 18789

# 2. 确认 SSH 无密码登录可用
ssh lr@<mac-ip> "echo OK"

# 3. 确认 openclaw 版本
openclaw --version
# 如果低于 2026.3.0，先升级

# 4. 确认可以运行 node 命令
openclaw node --help
```

---

## 附录 B：相关配置文件路径

| 文件 | Mac 路径 | Ubuntu 路径 |
|------|----------|-------------|
| openclaw.json | ~/.openclaw/openclaw.json | ~/.openclaw/openclaw.json |
| node.json | N/A | ~/.openclaw/node.json |
| SSH 密钥 | ~/.ssh/id_ed25519 (~/.ssh/id_ed25519.pub) | ~/.ssh/id_ed25519 (~/.ssh/id_ed25519.pub) |
| authorized_keys | ~/.ssh/authorized_keys (Mac) | N/A |
| systemd service | N/A | /etc/systemd/system/openclaw-node.service |

---

## 附录 C：关键命令速查

```bash
# Mac 侧
openclaw config get gateway.bind          # 查看当前 bind
openclaw config set gateway.bind lan      # 修改为 LAN
openclaw gateway restart                  # 重启 Gateway
openclaw devices list                     # 查看设备列表
openclaw devices approve --latest         # 审批最新设备
openclaw nodes status                     # 查看节点状态
sudo lsof -i :18789                       # 检查端口监听

# Ubuntu 侧
openclaw node run --host <mac-ip> --port 18789 --token "TOKEN"
openclaw nodes status
ssh lr@<mac-ip> "echo OK"                # SSH 测试
nc -zv <mac-ip> 18789                    # 端口测试
```

---

*文档版本：Phase-0-Gateway-Docking v1.1*
*生成时间：2026-03-26*
*补充时间：2026-03-27（基于映射报告 v2）*
*目标：Ubuntu 24.04 台机 → MacBook Pro Gateway (LAN)*

---

## 映射报告验证更新（2026-03-27）

来源：Cross-Verification-N05.md（2026-03-27 夜间构建 N-02 产出）

### ✅ 已验证的正确信息
- Gateway 默认端口 18789 ✅
- Gateway multiplexing WebSocket + HTTP 同端口 ✅
- LM Studio 默认端口 `http://127.0.0.1:1234/v1` ✅
- MiniMax M2.5 GS32 contextWindow = 196608，maxTokens = 8192 ✅
- Sub-agent `maxSpawnDepth` 默认 1（范围 1-5，推荐 Depth 2）✅
- Sub-agent `maxChildrenPerAgent` 默认 5，`maxConcurrent` 默认 8 ✅
- Sub-agent `archiveAfterMinutes` 默认 60 分钟 ✅
- `exec` 工具 `host` 支持 `sandbox` / `node` / `gateway` ✅
- Session key 格式 `agent:<id>:main` / `agent:<id>:subagent:<uuid>` ✅
- DM pairing 为默认策略（需手动审批）✅

### ❌ 需要补充/修正的内容
- **Heartbeat 默认 30 分钟**：`every: "30m"`，未在当前报告中明确提及
  - 建议在 Gateway 配置章节补充：heartbeat 默认 30 分钟，如需调整可通过 `openclaw config set gateway.heartbeat.every "5m"` 配置
- **Ollama 集成警告**：`/v1` 路径会破坏 tool calling，应使用 `http://127.0.0.1:11434`（无后缀）
  - 当前报告未明确提及此陷阱，补充内容中 RTX 2060 接入方案提到了 Ollama 但未注明此问题
- **Sub-agent context 只注入 AGENTS.md + TOOLS.md**（无 SOUL / MEMORY / IDENTITY）
  - 设计多 Agent 协作架构时需注意 sub-agent 缺失这些上下文文件
- **DM pairing code 有效期 1 小时**，pending 上限 **3 个/频道**
  - 在 §7.6 Pairing 审批问题章节补充：pairing code 有效期 1 小时，超时需重新发起；pending 上限 3 个/频道，超出后新请求被拒绝

### ⚠️ 外部硬件声明（无法通过 OpenClaw 文档验证）
- BearPi-Pico H3863 芯片规格（星闪 49μs / 240MHz）属于硬件参数，非 OpenClaw 软件功能，需对照 BearPi 官方文档或实测验证

### 补充 1：RTX 2060 GPU 接入方式（重要澄清）

映射报告 v2 明确了 Gateway 与 GPU 的关系：

> **Gateway 本身不直接管理 GPU**，而是通过 `exec` 工具调用 Ollama/LM Studio 等外部推理引擎来使用 RTX 2060。

**正确架构**：
```
Gateway（MacBook Pro）
  └── exec 工具
        └── SSH/本地调用 Ollama/LM Studio
              └── RTX 2060 GPU 推理
```

**具体操作**：
1. 在 Ubuntu 台式机上安装 Ollama 或 LM Studio
2. 下载量化模型（如 Qwen2.5-7B INT4）到本地
3. Gateway 通过 `exec(command="ollama run qwen2.5:7b ...", host="node")` 调用

**不要期望**：Gateway 直接加载模型到 RTX 2060——这需要外部推理服务。

### 补充 2：Tailscale "serve" 模式（替代 LAN 绑定）

如果 MacBook Pro 和 Ubuntu 台式机都加入了同一个 Tailscale 网络，可以：

**Mac 侧配置**（更安全的方案）：
```bash
openclaw config set gateway.bind "loopback"      # 不暴露到 LAN
openclaw config set gateway.tailscale.mode "serve"  # 仅 Tailscale 可访问
```

**优势**：
- Gateway 不暴露到局域网（更安全）
- 即使 Mac 在 NAT 后也能被 Ubuntu 访问
- 替代 `gateway.bind "lan"` 的方案
