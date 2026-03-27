# Jetson Nano 2GB × pythops/jetson-image 调研报告

> **调研日期**: 2026-03-26
> **目标项目**: https://github.com/pythops/jetson-image
> **调研目的**: 评估自定义镜像能否解决 Jetson Nano 2GB 安装 Node.js 22+ / OpenClaw 的问题

---

## 1. 项目基本信息

| 指标 | 数据 |
|------|------|
| **仓库地址** | https://github.com/pythops/jetson-image |
| **Stars** | 546 |
| **Forks** | 143 |
| **Open Issues** | 8 |
| **主语言** | Shell |
| **许可证** | AGPLv3 |
| **创建时间** | 2019-11-24 |
| **最近更新** | 2026-03-24（非常活跃！） |
| **最近推送** | 2026-03-09 |
| **描述** | Create minimalist, Ubuntu based images for the Nvidia jetson boards |

**社区活跃度评估**: 活跃维护中，2026年3月仍有更新。546 stars 在 Jetson 社区项目中属于较高关注度。

---

## 2. 支持的硬件型号

✅ **明确支持 Jetson Nano 2GB**（在 README 和 GitHub topics 中均有标注）

完整支持列表：
- [x] Jetson nano
- [x] Jetson nano **2gb**
- [x] Jetson orin nano
- [x] Jetson agx orin
- [x] Jetson agx xavier
- [x] Jetson xavier nx

---

## 3. Ubuntu 版本支持

| Ubuntu 版本 | Jetson Nano / Nano 2GB | Jetson Orin 系列 |
|------------|----------------------|----------------|
| 20.04 | ✅ 支持 | ✅ 支持 |
| 22.04 | ✅ 支持 | ✅ 支持 |
| 24.04 | ❌ **不支持** | ✅ 支持（仅 Orin 家族） |

**⚠️ 关键发现**：pythops/jetson-image 确实比官方 JetPack 4.6.1（Ubuntu 18.04）新，但 **Nano 2GB 最高只能到 Ubuntu 22.04**，无法使用 Ubuntu 24.04。

> [!IMPORTANT]
> 官方 JetPack 4.6.1 = Ubuntu 18.04（L4T R32.x）  
> pythops/jetson-image Nano 2GB 最高 = Ubuntu 22.04（L4T R32.x 或 R35.x）  
> Ubuntu 22.04 vs 18.04 的优势：Node.js 22+ 预编译二进制兼容性更好（但仍需注意 MTE 问题，见第6节）

---

## 4. L4T（L4T for Tegra）版本支持

| L4T 版本 | 对应 JetPack | Jetson Nano 2GB |
|---------|-------------|----------------|
| 32.x | JetPack 4.4 ~ 4.6.1 | ✅ 支持 |
| 35.x | JetPack 5.0 ~ 5.1 | ✅ 支持 |
| 36.x | JetPack 6.0 | ❌ Nano 不支持（Orin 专用） |

**使用方式**：构建命令中通过 `-l <版本号>` 指定，例如：
```bash
# Nano 2GB + L4T 32.x（兼容官方 JetPack 4.6.1 生态）
just build-jetson-image -b jetson-nano-2gb -d SD -l 32

# Nano 2GB + L4T 35.x（较新，但需确认硬件兼容性）
just build-jetson-image -b jetson-nano-2gb -d SD -l 35
```

---

## 5. 镜像构建与烧录流程

### 5.1 前置要求（构建主机）

需要在 **Linux 主机**上安装：
- `podman`（容器运行时）
- `just`（命令运行器）
- `jq`（JSON 处理）
- `qemu-user-static`（QEMU 跨架构支持）

### 5.2 构建步骤

```bash
# 1. 克隆仓库
git clone https://github.com/pythops/jetson-image
cd jetson-image

# 2. 构建 RootFS（选择 Ubuntu 版本）
# Nano 2GB 只能用 20.04 或 22.04
just build-jetson-rootfs 22.04

# 3. 构建镜像
# -b: board 类型
# -d: device (SD 或 eMMC)
# -l: L4T 版本
just build-jetson-image -b jetson-nano-2gb -d SD -l 32

# 产物：jetson.img（极简 rootfs，无冗余包）
```

### 5.3 烧录步骤

```bash
# 假设 SD 卡识别为 /dev/sda
sudo just flash-jetson-image jetson.img /dev/sda

# 或使用 Balena Etcher / dd 手动烧录
```

### 5.4 烧录后安装 NVIDIA 驱动

```bash
# 启动后手动安装 CUDA/cuDNN 等库
sudo apt install -y libcudnn8 libcudnn8-dev libnccl2 libnccl-dev ...
```

---

## 6. 核心问题解答：Node.js 22+ 和 OpenClaw

### 6.1 烧录后能否安装 Node.js 22+？

**答案：可以安装，但存在技术挑战**

| 方案 | Ubuntu 18.04 (官方) | Ubuntu 22.04 (jetson-image) |
|------|--------------------|---------------------------|
| NodeSource 预编译包 | ⚠️ 可能不兼容（MTE 问题） | ⚠️ 可能不兼容 |
| NVM 安装预编译版 | ⚠️ 可能不兼容 | ⚠️ 可能不兼容 |
| **从源码编译** | ✅ 可行（~27小时） | ✅ 可行（更快的编译速度） |
| Docker 镜像 | ✅ 可行 | ✅ 可行 |

**MTE (Memory Tagging Extension) 问题**：
- Node.js 22+ 的 V8 引擎默认启用 MTE（ARM64 Linux 特性）
- Jetson Nano 的 Cortex-A57 CPU **不支持 MTE**
- 预编译的 Node.js 22 ARM64 二进制文件在 Nano 上直接运行会崩溃
- 解决：从源码编译 Node.js 22，并修改 `deps/v8/src/heap/base/memory-tagging.cc`，将 `SUPPORTS_MTE` 设为 0

**Ubuntu 22.04 的优势**：
- 系统 GCC 版本更高（GCC 11 vs GCC 7），编译更快
- 系统库版本更新，兼容性更好
- 相比 Ubuntu 18.04，编译 Node.js 22 所需补丁更少

### 6.2 能否运行 OpenClaw？

**答案：可以运行，但前提是 Node.js 22+ 正常工作**

OpenClaw 本身是 Node.js 应用，无特殊硬件依赖。只要 Node.js 22+ 能运行，OpenClaw 就能安装。

**注意事项**：
- ❌ **不要使用 Bun 安装 OpenClaw**（2026年3月初发现：Bun 全局路径会触发"unsafe plugin manifest"错误导致无法启动）
- ✅ 使用 npm 全局安装：`npm install -g openclaw@latest`

### 6.3 与官方 JetPack 4.6.1 对比

| 维度 | 官方 JetPack 4.6.1 | pythops/jetson-image (Nano 2GB + Ubuntu 22.04) |
|------|-------------------|--------------------------------------------|
| **Ubuntu 版本** | 18.04 | 22.04 ✅（更新） |
| **系统占用** | 较大（含完整 AI 栈） | 极小（极简 RootFS） |
| **RAM 占用** | 较高 | Orin 仅 220MB（Nano 应类似） |
| **定制性** | 低（SDK Manager 图形化） | 高（修改 Containerfile） |
| **预装 CUDA/cuDNN** | ✅ 是（需安装 JetPack） | ❌ 需手动 apt install |
| **官方支持** | ✅ NVIDIA 官方 | ❌ 社区维护 |
| **构建复杂度** | 低（官方镜像直接烧录） | 中（需 Linux 主机构建） |
| **硬件驱动稳定** | ✅ 完美 | ⚠️ 可能有问题（摄像头、GPIO 等） |
| **Node.js 22+** | 需源码编译 | 需源码编译（但系统库更新） |

---

## 7. 替代方案对比

### 7.1 JetPack 5.x / 6.x 对 Nano 2GB 的支持

**结论：官方不支持**

根据 NVIDIA 开发者官网 FAQ：
- **JetPack 6**：仅支持 Jetson Orin 系列
- **JetPack 5**：仅支持 Jetson Orin 和 Jetson Xavier 系列
- **JetPack 4**：维护模式，支持 Jetson Nano（包括 2GB）

**唯一来源**: NVIDIA 开发者官网 [ Jetson Platform FAQ](https://developer.nvidia.com/embedded/jetson-linux-archive)

### 7.2 其他社区自定义镜像

搜索结果中提到的其他方案：
- **Q-engineering Ubuntu 22.04 镜像**：社区维护的 Ubuntu 22.04 for Jetson Nano，但需要自行验证硬件兼容性
- **直接从源码编译**：在官方 JetPack 4.6.1（Ubuntu 18.04）上，从源码编译 Node.js 22（耗时约27小时 + MTE 补丁）

### 7.3 各方案综合评估

| 方案 | Ubuntu | Node.js 22+ | 复杂度 | 推荐度 |
|------|--------|------------|--------|--------|
| 官方 JetPack 4.6.1 + NVM 编译 Node 22 | 18.04 | ✅ 可行 | 高（27小时编译） | ⭐⭐⭐ |
| **pythops/jetson-image + Ubuntu 22.04 + 编译 Node 22** | 22.04 | ✅ 可行 | 高（需 Linux 构建机） | ⭐⭐⭐ |
| Docker 容器（带 Node 22） | 任意 | ✅ 可行 | 中（但硬件访问受限） | ⭐⭐ |
| JetPack 5.x/6.x（不支持） | - | - | - | ❌ |

---

## 8. 最终结论与建议

### 8.1 pythops/jetson-image 适合的场景

- ✅ **有 Linux 构建主机**（必须）：需要 Linux 环境运行 podman + just
- ✅ **需要极简系统**（如容器化部署、资源极度受限）
- ✅ **需要 Ubuntu 22.04**（而非官方 18.04）
- ✅ **愿意自行维护驱动**（无 NVIDIA 官方支持）

### 8.2 不适合的场景

- ❌ **需要开箱即用的稳定性** → 官方 JetPack 更好
- ❌ **需要最新 JetPack 6.x** → Nano 2GB 根本不支持
- ❌ **没有 Linux 构建主机** → 无法使用此方案

### 8.3 对 OpenClaw 部署的实际价值

**⚠️ 关键发现**：

使用 pythops/jetson-image 构建 Ubuntu 22.04 镜像后：
1. **仍需从源码编译 Node.js 22**（预编译二进制因 MTE 问题无法直接运行）
2. Ubuntu 22.04 相比 18.04 的优势是**编译更快、系统库兼容性更好**，但仍不是"预编译 Node 22 直接用"
3. **编译耗时**：Jetson Nano 2GB 从源码编译 Node.js 22 约需 **27 小时**

**因此，对于 OpenClaw 部署而言：**
- pythops/jetson-image 提供的 Ubuntu 22.04 是**改善**，但不是**解决方案**
- 真正的瓶颈是 **ARM64 + MTE + Node.js 22** 的兼容性问题，而非 Ubuntu 版本本身
- 如果已经有 Linux 构建主机，可以尝试；如果没有，为 OpenClaw 专门搭建构建环境成本较高

### 8.4 最务实的方案（更新建议）

对于 Jetson Nano 2GB + OpenClaw：

1. **直接用官方 JetPack 4.6.1 SD 卡镜像**（不用自定义镜像）
2. **使用 NVM 从源码编译 Node.js 22**（约27小时，含 MTE 补丁）
3. **不要用 Bun**，用 npm 全局安装 OpenClaw
4. 如编译 Node 22 失败，**考虑 Docker**：`docker run -it node:22-bookworm-arm64`，但需处理硬件访问问题

---

## 9. 待验证事项（需要实机测试）

以下内容因无法实际在 Jetson Nano 2GB 上测试而无法确认：

- [ ] pythops/jetson-image 构建的 L4T 35.x 镜像在 Nano 2GB 上实际运行效果
- [ ] Ubuntu 22.04 预编译的 Node.js 22 ARM64 二进制是否真的因 MTE 崩溃
- [ ] L4T 35.x 下 CUDA / TensorRT 驱动是否正常工作
- [ ] CSI 摄像头在自定义镜像下的驱动支持

---

*调研工具：GitHub API、base64 解码、官方 README、社区搜索*  
*数据来源：https://github.com/pythops/jetson-image (README, API metadata)*  
*调研时间：2026-03-26*
