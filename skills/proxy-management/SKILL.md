---
name: proxy-management
description: 网络流量管理和代理配置 - 自动判断哪些流量需要代理，哪些不需要
---

# Proxy Management Skill

管理 OpenClaw 的网络流量，判断哪些需要代理，哪些不需要。

## 流量分类

### 🚫 不需要代理（国内服务）

| 服务 | 域名 | 说明 |
|------|------|------|
| 飞书 | open.feishu.cn | 国内云服务 |
| 钉钉 | open.dingtalk.com | 国内云服务 |
| QQ Bot | ql.qq.com | 国内服务 |
| 微信公众号 | mp.weixin.qq.com | 国内服务 |
| Boss直聘 | zhipin.com | 国内服务 |
| PyPI | pypi.org | Python 包（国内镜像可选）|
| npm 中国 | registry.npmmirror.com | 可选 |

### ⚠️ 需要代理（海外服务）

| 服务 | 域名 | 说明 |
|------|------|------|
| GitHub | github.com, api.github.com | 代码托管 |
| Docker Hub | docker.io | 镜像仓库 |
| PyPI 原始 | pypi.org | 可能慢 |
| npm 原始 | registry.npmjs.org | 可能慢 |
| Anthropic | api.anthropic.com | AI 模型 |
| OpenAI | api.openai.com | AI 模型 |
| Tavily | api.tavily.com | 搜索引擎 |
| Exa | api.exa.ai | 全网搜索 |
| Twitter/X | x.com, twitter.com | 社交媒体 |
| YouTube | youtube.com | 视频平台 |
| Reddit | reddit.com | 社区 |

## 当前代理配置

### macOS 自动配置（~/.zshrc）

```bash
# Only set proxy if VPN is running (port 10792 is reachable)
if nc -z 127.0.0.1 10792 2>/dev/null; then
    export HTTP_PROXY=http://127.0.0.1:10792
    export HTTPS_PROXY=http://127.0.0.1:10792
    # 国内网站直连，不走代理
    export NO_PROXY="localhost,127.0.0.1,*.cn,open.feishu.cn,feishu.cn,dingtalk.com,alipay.com,taobao.com,tmall.com,jd.com,bai*.com,tencent.com,qq.com,163.com,126.com,aliyun.com,tencentcloud.com"
    export no_proxy="$NO_PROXY"
fi
```

### 不需要代理的网站（NO_PROXY）
- 国内域名：*.cn
- 飞书：open.feishu.cn, feishu.cn
- 钉钉：dingtalk.com
- 阿里系：alipay.com, taobao.com, tmall.com, aliyun.com
- 腾讯系：tencent.com, qq.com, tencentcloud.com
- 百度：baidu.com
- 网易：163.com, 126.com

## 手动配置

### 临时使用代理

```bash
# 为单个命令设置代理
HTTP_PROXY=http://127.0.0.1:7890 HTTPS_PROXY=http://127.0.0.1:7890 pip3 install playwright

# 为 GitHub CLI 设置代理
gh config set http_proxy http://127.0.0.1:7890
gh config set https_proxy http://127.0.0.1:7890
```

### 永久配置

在 `~/.zshrc` 或 `~/.bashrc` 中添加：

```bash
# 代理配置
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
export ALL_PROXY=socks5://127.0.0.1:7890
```

## 自动判断逻辑

### Python/npm 包安装

```bash
# 如果安装超时，尝试代理
HTTP_PROXY=http://127.0.0.1:7890 pip3 install <package>

# 或者使用国内镜像
pip3 install <package> -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### GitHub 操作

```bash
# 克隆仓库
HTTP_PROXY=http://127.0.0.1:7890 git clone https://github.com/xxx/xxx.git

# GitHub CLI
gh config set http_proxy http://127.0.0.1:7890
```

## 故障排除

### pip 安装（推荐使用国内镜像）

```bash
# 临时使用镜像
pip3 install <package> -i https://pypi.tuna.tsinghua.edu.cn/simple

# 设为默认镜像
pip3 config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

### npm 安装

```bash
# 设为默认镜像
npm config set registry https://registry.npmmirror.com

# 恢复默认
npm config set registry https://registry.npmjs.org
```

### GitHub 克隆

```bash
# 使用 ghproxy 镜像
git clone https://mirror.ghproxy.com/https://github.com/xxx/xxx.git
```

## 常用命令

```bash
# 测试网络连通性
curl -s -o /dev/null -w "%{http_code}" <URL>

# 检查代理端口
lsof -i :7890

# 查看当前代理设置
env | grep -i proxy
```
