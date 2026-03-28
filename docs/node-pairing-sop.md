# OpenClaw Node 配对 SOP

> 目标：将设备（手机/电脑）作为节点连接到 MacBook Gateway (192.168.1.13)
> 
> 适用场景：远程控制、设备联动、分布式 AI 任务

---

## 名词解释

| 名词 | 说明 |
|------|------|
| Gateway | OpenClaw 主服务，运行在 MacBook 上，监听 18789 端口 |
| Node | 连接到 Gateway 的设备，受 Gateway 控制 |
| Pairing | 配对审批流程，确保只有授权设备能连接 |

---

## 流程概览

```
设备 (node) ──ws://──> MacBook Gateway (192.168.1.13:18789)
                      │
                      ▼
              [pairing required]
                      │
                      ▼
              MacBook 审批配对请求
                      │
                      ▼
              设备连接成功 → paired · connected
```

---

## 前置条件

### MacBook Gateway 端

1. Gateway 已运行在 192.168.1.13:18789
2. `gateway.bind=lan` 已设置（监听局域网）
3. 如果改了配置需重启：
   ```bash
   openclaw gateway restart
   ```
4. 确认 Gateway 可访问：
   ```bash
   curl http://192.168.1.13:18789/health
   # 应返回 {"ok":true,"status":"live"}
   ```

### 设备端（Ubuntu / Android）

1. 已安装 OpenClaw CLI
2. 已配置 `gateway.remote.url` 指向 MacBook

---

## 方法一：Ubuntu 电脑配对（systemd 后台运行）

### Step 1: 配置文件

在 Ubuntu 上编辑 `~/.openclaw/openclaw.json`，添加/修改：

```json
{
  "gateway": {
    "port": 18789,
    "mode": "remote",
    "bind": "loopback",
    "remote": {
      "url": "http://192.168.1.13:18789",
      "token": "235bf68c2288bfde322b8567509fb0e4d8eb368ec3c70000"
    }
  }
}
```

### Step 2: 测试前台连接

```bash
OPENCLAW_ALLOW_INSECURE_PRIVATE_WS=1 openclaw node run --host 192.168.1.13 --port 18789
```

**预期输出：**
- `node host gateway connect failed: pairing required` → 正常，说明连上了但需要配对
- `pairing required` 错误表示 MacBook 端已收到请求，等着审批

### Step 3: MacBook 端审批

在新窗口执行：
```bash
openclaw devices list
# 找到 Pending 里的设备

openclaw devices approve --latest
# 批准最新的配对请求
```

### Step 4: Ubuntu 重新连接

如果前台还在运行，按 `Ctrl+C` 退出，然后继续下一步。

### Step 5: 安装 systemd 服务（后台运行）

```bash
openclaw node install
```

### Step 6: 修改服务文件添加环境变量

```bash
nano ~/.config/systemd/user/openclaw-node.service
```

找到 `[Service]` 部分，添加：
```
Environment=OPENCLAW_ALLOW_INSECURE_PRIVATE_WS=1
```

### Step 7: 重载并启动

```bash
systemctl --user daemon-reload
systemctl --user start openclaw-node.service
```

### Step 8: 验证连接

**Ubuntu 端：**
```bash
systemctl --user status openclaw-node.service
# 应显示 Active: active (running)
```

**MacBook 端：**
```bash
openclaw nodes status
# 应显示 jet-Ubuntu: paired · connected
```

---

## 方法二：Android 手机配对

### Step 1: 安装 OpenClaw App

从 GitHub releases 或应用商店下载 OpenClaw Android 版。

### Step 2: 连接 WiFi

确保手机和 MacBook 在同一局域网（192.168.1.x）。

### Step 3: App 内配置 Gateway

在 OpenClaw App 中：
- 设置 Gateway 地址：`ws://192.168.1.13:18789`
- 或扫描 MacBook 上的二维码配对

### Step 4: MacBook 端审批

手机发起配对后，MacBook 上执行：
```bash
openclaw devices list
openclaw devices approve --latest
```

### Step 5: 验证

```bash
openclaw nodes status
# 应显示 My Android: paired · connected
```

---

## 常见错误排查

### 错误 1: SECURITY ERROR

```
node host gateway connect failed: SECURITY ERROR: Cannot connect to "192.168.1.13" over plaintext ws://
```

**原因：** OpenClaw 默认禁止明文 WebSocket 连接。

**解决：** 
```bash
OPENCLAW_ALLOW_INSECURE_PRIVATE_WS=1 openclaw node run --host 192.168.1.13 --port 18789
```

### 错误 2: ECONNREFUSED

```
node host gateway connect failed: connect ECONNREFUSED 192.168.1.13:18789
```

**原因：** MacBook Gateway 只监听 127.0.0.1，未监听 LAN。

**解决：**
1. MacBook 上检查配置：`openclaw config get gateway.bind`
2. 如果是 `loopback`，改成 `lan`：
   ```bash
   openclaw config set gateway.bind=lan
   openclaw gateway restart
   ```

### 错误 3: pairing required

```
node host gateway connect failed: pairing required
```

**原因：** 设备未配对。

**解决：** 在 MacBook 上审批：
```bash
openclaw devices list
openclaw devices approve --latest
```

### 错误 4: systemd 服务 disconnected

服务在运行，但 `openclaw nodes status` 显示 disconnected。

**原因：** systemd 服务未继承 `OPENCLAW_ALLOW_INSECURE_PRIVATE_WS=1` 环境变量。

**解决：**
1. 编辑服务文件：`nano ~/.config/systemd/user/openclaw-node.service`
2. 在 `[Service]` 下添加：
   ```
   Environment=OPENCLAW_ALLOW_INSECURE_PRIVATE_WS=1
   ```
3. 重载：`systemctl --user daemon-reload`
4. 重启：`systemctl --user restart openclaw-node.service`

---

## 管理命令

### MacBook 端

```bash
# 查看所有节点
openclaw nodes status

# 查看待配对请求
openclaw devices list

# 批准配对
openclaw devices approve --latest

# 拒绝配对
openclaw devices reject <requestId>

# 移除已配对设备
openclaw devices remove <deviceId>

# 在节点上执行命令
openclaw nodes run --node <nodeId> --raw "uname -a"
```

### Ubuntu 端

```bash
# 查看服务状态
systemctl --user status openclaw-node.service

# 查看日志
journalctl --user -u openclaw-node.service -f

# 重启服务
systemctl --user restart openclaw-node.service

# 停止服务
systemctl --user stop openclaw-node.service

# 卸载服务
openclaw node uninstall
```

---

## 架构说明

```
┌─────────────────────────────────────────────────────────┐
│                   MacBook (Gateway)                     │
│                   192.168.1.13:18789                    │
│                                                         │
│   ┌─────────────────────────────────────────────────┐   │
│   │  paired nodes:                                  │   │
│   │  - jet-Ubuntu (192.168.1.18) ←──────────────┐  │   │
│   │  - My Android (192.168.1.6)  ←─────────────┐  │   │
│   └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          ▲
                          │ WebSocket
                          │
     ┌────────────────────┼────────────────────┐
     │                    │                    │
┌────┴────┐        ┌──────┴──────┐       ┌───┴───┐
│ Ubuntu  │        │   Android   │       │ other │
│  node   │        │    phone     │       │ node  │
└─────────┘        └──────────────┘       └───────┘
```

---

## 适用版本

- OpenClaw: 2026.3.24+
- Gateway OS: macOS
- Node OS: Ubuntu 24.04 / Android

---

## 参考

- 配置备份：`~/.openclaw/backup/golden/`
- 工作日志：`~/.openclaw/workspace/memory/2026-03-28.md`
- 错误记录：`~/.openclaw/workspace/.learnings/ERRORS.md`
