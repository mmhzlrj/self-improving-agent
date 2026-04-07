# Node Setup 服务

OpenClaw 节点安装与配置服务。

## 功能概述

自动化检测系统环境并安装配置 OpenClaw 节点，包含以下步骤：

1. **系统检测** - 检测操作系统、架构、Homebrew 等
2. **Node.js 安装** - 自动安装或验证 Node.js 环境
3. **OpenClaw 安装** - 安装 OpenClaw CLI 工具
4. **Gateway 配置** - 启动并配置 OpenClaw Gateway
5. **节点配对** - 管理节点配对信息

## 文件结构

```
node-setup/
├── README.md        # 本文档
├── install.sh       # 安装脚本
└── uninstall.sh     # 卸载脚本
```

## 快速开始

### 安装

```bash
cd harness/robot/services/node-setup
bash install.sh
```

### 卸载

```bash
bash uninstall.sh
```

## 安装脚本详情

### `install.sh`

自动化安装流程，无需人工干预：

```
Step 1/5: 检测系统环境
Step 2/5: 检测 Node.js
Step 3/5: 检测 OpenClaw
Step 4/5: 配置 Gateway
Step 5/5: 节点配对
```

**前置要求**：
- macOS 或 Linux 系统
- Homebrew (macOS 推荐)
- 管理员权限

**自动安装内容**：
- Node.js (通过 Homebrew 或 apt)
- OpenClaw (通过 npm)
- OpenClaw Gateway 服务

### `uninstall.sh`

清理 node-setup 安装的所有组件：

1. 停止 node-setup 服务
2. 清理相关进程
3. 删除配置文件
4. 清理安装目录

## 后续操作

安装完成后可使用以下命令：

```bash
# 配对新节点
openclaw node pair

# 查看节点状态
openclaw node list

# 查看帮助
openclaw --help
```

## 故障排除

### Node.js 安装失败

手动安装：https://nodejs.org

### Gateway 启动失败

```bash
openclaw gateway status
openclaw gateway restart
```

### 节点配对问题

参考 `node-connect` skill 进行诊断。
