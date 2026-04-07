#!/bin/bash
#
# node-setup/install.sh - 节点安装脚本
# 功能：检测系统 → Node.js → OpenClaw → Gateway配置 → 配对
# 作者：OpenClaw
#

set -e  # 遇到错误立即退出

# ============ 颜色定义 ============
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============ 日志函数 ============
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ============ 错误处理 ============
error_exit() {
    log_error "$1"
    exit 1
}

# ============ Step 1: 检测系统 ============
check_system() {
    log_info "Step 1/5: 检测系统环境..."
    
    # 检测操作系统
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        log_success "检测到 macOS 系统"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        log_success "检测到 Linux 系统"
    else
        log_warning "未知操作系统: $OSTYPE，将尝试继续"
        OS="unknown"
    fi
    
    # 检测架构
    ARCH=$(uname -m)
    log_info "系统架构: $ARCH"
    
    # 检测是否已安装 Homebrew (macOS)
    if [[ "$OS" == "macos" ]]; then
        if command -v brew &> /dev/null; then
            log_success "Homebrew 已安装"
        else
            log_warning "Homebrew 未安装，建议安装以方便后续操作"
        fi
    fi
    
    return 0
}

# ============ Step 2: 安装/检测 Node.js ============
check_nodejs() {
    log_info "Step 2/5: 检测 Node.js..."
    
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node -v)
        NPM_VERSION=$(npm -v)
        log_success "Node.js 已安装: $NODE_VERSION, npm: $NPM_VERSION"
        
        # 检查版本是否满足要求 (>= 18)
        NODE_MAJOR=$(echo $NODE_VERSION | cut -d'.' -f1 | tr -d 'v')
        if [[ $NODE_MAJOR -lt 18 ]]; then
            log_warning "Node.js 版本较低，建议升级到 v18+"
        fi
        return 0
    else
        log_warning "Node.js 未安装"
        
        if [[ "$OS" == "macos" ]]; then
            log_info "正在尝试安装 Node.js..."
            
            if command -v brew &> /dev/null; then
                brew install node || error_exit "通过 Homebrew 安装 Node.js 失败"
                log_success "Node.js 安装完成"
                
                # 重新加载路径
                export PATH="/usr/local/bin:$PATH"
                NODE_VERSION=$(node -v)
                NPM_VERSION=$(npm -v)
                log_success "Node.js 版本: $NODE_VERSION, npm: $NPM_VERSION"
                return 0
            else
                log_warning "无法自动安装，请手动安装 Node.js: https://nodejs.org"
                return 1
            fi
        elif [[ "$OS" == "linux" ]]; then
            log_info "尝试通过 apt 安装 Node.js..."
            if command -v apt-get &> /dev/null; then
                apt-get update && apt-get install -y nodejs npm || error_exit "通过 apt 安装 Node.js 失败"
                log_success "Node.js 安装完成"
                return 0
            else
                log_warning "无法自动安装，请手动安装 Node.js"
                return 1
            fi
        fi
    fi
    
    return 1
}

# ============ Step 3: 安装/检测 OpenClaw ============
check_openclaw() {
    log_info "Step 3/5: 检测 OpenClaw..."
    
    # 检查 openclaw 命令是否可用
    if command -v openclaw &> /dev/null; then
        log_success "OpenClaw 命令已安装"
        
        # 显示版本和状态
        log_info "OpenClaw 版本信息:"
        openclaw --version 2>/dev/null || openclaw version 2>/dev/null || true
        
        return 0
    else
        log_warning "OpenClaw 未安装"
        log_info "正在安装 OpenClaw..."
        
        # 尝试通过 npm 安装
        if command -v npm &> /dev/null; then
            npm install -g openclaw || error_exit "通过 npm 安装 OpenClaw 失败"
            log_success "OpenClaw 安装完成"
            
            # 验证安装
            openclaw --version 2>/dev/null || openclaw version 2>/dev/null || true
            return 0
        else
            error_exit "npm 不可用，无法安装 OpenClaw"
        fi
    fi
}

# ============ Step 4: Gateway 配置 ============
setup_gateway() {
    log_info "Step 4/5: 配置 Gateway..."
    
    # 检查 Gateway 是否运行
    if openclaw gateway status &> /dev/null; then
        log_success "Gateway 已在运行"
    else
        log_info "正在启动 Gateway..."
        openclaw gateway start
        
        # 等待启动
        sleep 2
        
        if openclaw gateway status &> /dev/null; then
            log_success "Gateway 启动成功"
        else
            log_warning "Gateway 启动可能需要进一步配置"
        fi
    fi
    
    # 获取 Gateway 配置信息
    log_info "Gateway 配置信息:"
    openclaw gateway status 2>/dev/null || log_warning "无法获取 Gateway 状态"
    
    # 检查配置文件
    CONFIG_FILE="$HOME/.openclaw/openclaw.json"
    if [[ -f "$CONFIG_FILE" ]]; then
        log_success "配置文件存在: $CONFIG_FILE"
    else
        log_warning "配置文件不存在，将使用默认配置"
    fi
    
    return 0
}

# ============ Step 5: 配对节点 ============
pair_node() {
    log_info "Step 5/5: 节点配对..."
    
    # 检查是否已有配对的节点
    log_info "检查当前配对状态..."
    
    # 尝试获取配对信息
    if openclaw node list &> /dev/null; then
        log_success "已配对的节点:"
        openclaw node list
    else
        log_info "暂无配对节点"
    fi
    
    # 生成配对命令提示
    log_info "=========================================="
    log_info "如需配对新节点，请执行以下命令:"
    log_info "  openclaw node pair"
    log_info "=========================================="
    
    # 检查是否有待配对的节点
    if openclaw node pending &> /dev/null 2>&1; then
        log_info "检测到待配对节点"
        openclaw node pending
    fi
    
    return 0
}

# ============ 主流程 ============
main() {
    echo "========================================"
    echo "   OpenClaw 节点安装脚本"
    echo "========================================"
    echo ""
    
    # Step 1: 检测系统
    check_system || true
    
    # Step 2: 检测/安装 Node.js
    if ! check_nodejs; then
        log_error "Node.js 安装失败，请手动安装后重试"
        exit 1
    fi
    
    # Step 3: 检测/安装 OpenClaw
    if ! check_openclaw; then
        log_error "OpenClaw 安装失败，请手动安装后重试"
        exit 1
    fi
    
    # Step 4: Gateway 配置
    setup_gateway || true
    
    # Step 5: 配对节点
    pair_node || true
    
    echo ""
    echo "========================================"
    log_success "安装流程完成!"
    echo "========================================"
    echo ""
    echo "后续步骤:"
    echo "  1. 如需配对新节点: openclaw node pair"
    echo "  2. 查看节点状态: openclaw node list"
    echo "  3. 查看帮助: openclaw --help"
    echo ""
}

# 执行主流程
main "$@"