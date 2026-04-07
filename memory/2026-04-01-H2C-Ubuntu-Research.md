# Ubuntu + 拓竹 H2C 调研报告

> 调研时间：2026-04-01  
> 调研工具：Tavily Search（3次）、Web Search（2次）  
> 覆盖范围：H2C Ubuntu 兼容性、Blender→H2C CLI 自动化链路、收菜闭环可行性、竞品对比

---

## 1. Ubuntu + H2C 兼容性

### 结论：**完全可用，但有已知 Bug**

### 1.1 Bambu Studio Linux 版本

**官方支持 Linux**（来自官方规格表）：  
> "Supported Operating System: MacOS, Windows, Linux"

提供两种 Linux 安装包：

| 格式 | 适用系统 | 说明 |
|------|---------|------|
| `.AppImage` | Ubuntu 22.04 / 24.04, Fedora | 便携版，无需安装 |
| `.zip` | Ubuntu | 解压即用 |

下载途径：`github.com/bambulab/BambuStudio/releases`

**最新版本（2026-01）：v02.05.00.64**
- `Bambu_Studio_linux_fedora-v02.05.00.64.AppImage`（Fedora 推荐）
- `Bambu_Studio_ubuntu-22.04_PR-9504.AppImage`
- `Bambu_Studio_ubuntu-24.04_PR-9504.AppImage`

### 1.2 Ubuntu 22.04 / 24.04 运行注意事项

**Ubuntu 24.04 libfuse 问题**（常见）：
```bash
# 如果 AppImage 无法启动，需要安装 libfuse2t64
sudo apt install libfuse2t64
```

**libwebkit2gtk 软链问题**（Ubuntu 22.04）：
```bash
sudo ln -sf /usr/lib/x86_64-linux-gnu/libwebkit2gtk-4.1.so.0 \
  /usr/lib/x86_64-linux-gnu/libwebkit2gtk-4.0.so.37
sudo ln -sf /usr/lib/x86_64-linux-gnu/libjavascriptcoregtk-4.1.so.0 \
  /usr/lib/x86_64-linux-gnu/libjavascriptcoregtk-4.0.so.18
```

### 1.3 连接协议：WiFi + LAN Mode（无需云）

| 方式 | 说明 |
|------|------|
| **WiFi** | 打印机联网，Studio 通过云端或局域网控制 |
| **LAN Mode** | 纯本地局域网，**不连云**，隐私安全。打印机设置 → LAN Only |
| **USB** | 仅限固件更新，不用于日常打印控制 |
| **有线网口** | H2C **不提供**以太网接口，WiFi only |

**LAN Mode 关键特性：**
- Bambu Studio 或 Orca Slicer 通过局域网直接与打印机通信
- MQTT 协议维持长连接，支持实时状态推送
- 无需互联网，但需要同局域网
- Bambu Handy App 在 LAN Mode 下**不可用**

### 1.4 H2C 的 REST/MQTT API

**本地 API**：打印机暴露 MQTT 端口（默认 8883），支持：
- 实时状态订阅（温度、打印进度）
- 发送打印任务（上传 .gcode.3mf）
- 打印机控制（暂停、取消、开门）

**第三方 Python SDK 可用：**

| SDK | 特点 |
|-----|------|
| `bambulabs_api` (PyPI) | MQTT + Cloud 双模式，支持 H2C |
| `Bambu-Lab-Cloud-API` (coelacant1) | Cloud API 完整实现，MQTT+Camera |
| `bambu-lab-cloud-api` (PyPI) | Cloud API，支持 MQTT 文件上传 |

**官方 Bambu Local Server SDK**（Windows only，Linux 正在开发）：
> "Operating System: Windows 10 or later (Linux support is currently in development)"  
> 来源：Bambu Lab 官方 Wiki

### 1.5 已知 Bug（Linux + H2C）

**严重 Bug：H2C 在 Linux 上发送打印任务时崩溃**（Issue #8980）
- 复现概率：~50%
- 表现：`Send print job` 窗口打开后软件无响应
- 影响：必须 kill 进程重试
- 状态：2025 年 11 月报告，官方仍在处理

**CLI 切片错误**（Issue #9963）：H2C 双喷头时 `--filament-map` 参数异常

### 1.6 推荐配置方案

```
最优路径：
Bambu Studio (Linux AppImage) → LAN Mode → H2C (WiFi)
    ↓
bambu-cli (GitHub: davglass/bambu-cli) → 辅助监控/文件管理
    ↓
bambulabs_api (PyPI) → Python 自动化脚本
```

---

## 2. Blender → H2C CLI 自动化

### 结论：**可行，链路已通，需要注意多喷头配置**

### 2.1 Blender 导出格式支持

| 格式 | Blender 原生支持 | H2C 接受 | 推荐度 |
|------|----------------|---------|--------|
| `.stl` | ✅ 原生导出 | ✅ 支持（需切片） | ⭐⭐⭐ |
| `.3mf` | ❌ 需插件 | ✅ **原生支持**（含材料/颜色） | ⭐⭐⭐⭐⭐ |
| `.obj` | ✅ 原生导出 | ✅ 支持（需切片） | ⭐⭐ |
| `.gcode` | ❌ Blender 不生成 | ✅ 直接打印 | ❌ |

**Blender 3MF 插件推荐：**
- 官方扩展：`extensions.blender.org/add-ons/threemf-io/`（生产级 3MF 导入/导出）
- GitHub：`Ghostkeeper/Blender3mfFormat`（轻量，兼容性广）
- **Bambu Studio 3MF 分支**：`github.com` 搜索 Bambu Studio 3MF 分支，支持颜色组导出

### 2.2 H2C 切片流程

```
 Blender (.blend)
     ↓ [Export: STL 或 3MF]
 Bambu Studio / OrcaSlicer
     ↓ [Slice → .gcode.3mf]
 H2C 打印机
     ↓ [打印]
 完成
```

**H2C 的特殊复杂性：双喷头 + Vortek 热端**
- 最多支持 6 个 Vortek 热端（右侧工具架）
- 切片时需配置 `Left Hotend` 和 `Right Hotend`（或 Vortek 编号）
- `Grouping Algorithm` 自动分配耗材到左右喷头
- 不同 Vortek 喷头数量直接影响耗材消耗估算

### 2.3 Bambu Studio CLI 切片

Bambu Studio 支持完整 CLI 切片（来自[官方 Wiki](https://github.com/bambulab/BambuStudio/wiki/Command-Line-Usage)）：

```bash
# 基础切片命令
./Bambu_Studio_linux_ubuntu-22.04.AppImage \
  model.stl \
  --slice 1 \
  --arrange 1 \
  --load-settings "printer.json" \
  --load-filaments "PLA.json" \
  --outputdir "./output/"
```

**H2C 专用 CLI 参数（来自 Issue #9963）：**
```bash
./bambu-studio model.stl \
  --slice 0 --arrange 1 \
  --load-settings 'H2C.json;process.json' \
  --load-filaments 'PLA@H2C.json;PLA@H2C.json' \
  --filament-colour='#00AE42;#FF9C00' \
  --enable-support=1 \
  --curr-bed-type='Textured PEI Plate' \
  --layer-height='0.2' \
  --outputdir './'
```

**关键参数：**
- `--slice 1`：执行切片
- `--arrange 1`：自动排版
- `--export-3mf`：导出为 3MF（含 G-code）
- `--load-settings`：加载打印机配置
- `--load-filaments`：加载耗材配置

**OrcaSlicer**（H2C 兼容第三方 slicer）也支持 CLI 切片，是更轻量的替代品。

### 2.4 Headless 切片（无需 GUI）

`.AppImage` 模式下 Bambu Studio **可以**在无显示器的 Linux 服务器上运行（无需 X11 显示），但有 GUI 依赖。

**完全 Headless 切片替代方案：**

| 方案 | 说明 |
|------|------|
| **OrcaSlicer CLI** | 第三方开源 slicer，支持 H2C，Linux 友好 |
| **SuperSlicer CLI** | 命令行切片，支持 Bambu 打印机 |
| **Bambu Studio Docker** | 官方提供 Docker 镜像，可在服务器运行 |

官方 Docker 指南：`github.com/bambulab/BambuStudio/wiki/Docker-Run-Guide`

### 2.5 Python 自动化完整链路

```python
# 步骤1：Blender CLI 导出 STL
# blender --background --python-export-stl.py model.blend

# 步骤2：Python 调用 Bambu Studio CLI 切片
import subprocess
subprocess.run([
    "./Bambu_Studio_linux.AppImage",
    "output/model.stl",
    "--slice", "1",
    "--arrange", "1",
    "--load-settings", "H2C_preset.json",
    "--outputdir", "./gcode/"
])

# 步骤3：通过 MQTT 上传并启动打印
from bambulabs_api import Printer
printer = Printer("192.168.x.x", "ACCESS_CODE", "SERIAL")
printer.connect()
printer.upload_and_print("./gcode/model.gcode.3mf")

# 或通过 bambulabs_api 发送已切片的 G-code 文件
```

### 2.6 关键挑战

1. **H2C 双喷头参数复杂**：CLI 中 `--filament-map`、`--curr-bed-type` 等参数格式容易出错
2. **Vortek 热端配置**：多热端切换时需要精细的耗材分配配置
3. **Linux 崩溃 Bug**：发送打印任务时 50% 概率崩溃，需要自动化脚本处理重试
4. **3MF 颜色信息丢失**：Blender → 3MF 多色导出需要 Bambu 专用分支插件

---

## 3. 收菜闭环愿景分析

### 结论：**技术可行，但 H2C 的门+磁吸板设计使自动化难度较高**

### 3.1 H2C 硬件规格（与自动化相关的关键参数）

| 参数 | 值 | 对自动化的影响 |
|------|-----|--------------|
| **打印板尺寸** | ~258×258mm（有效面积） | 夹取空间有限 |
| **打印板类型** | 磁性 Flexible Steel Plate（Textured PEI） | 磁吸拆卸相对容易 |
| **机器尺寸** | 492×514×626 mm | 体积较大，需要臂展 |
| **机器重量** | 32.5 kg | 门结构承重有限 |
| **前门** | 玻璃门，铰链式 | **自动开门需要舵机** |
| **Z 轴行程** | 320mm | 热端上行高度可利用 |
| **触摸屏** | 5 英寸屏，1280×720 | 触摸屏交互可模拟 |
| **控制系统** | WiFi + MQTT | 可远程触发打印完成 |

### 3.2 现有自动化方案对比

| 方案 | 原理 | 成本 | 兼容性 | H2C 可用 |
|------|------|------|--------|---------|
| **3DQue AutoFarm3D VAAPR Bed** | 冷却后 Flexor 弯曲磁板 + 推板机构 | ~$179 USD | CoreXY（Bambu P1S/X1 等） | ⚠️ 需定制 |
| **InfinityFlow3D AutoClear（G-code 方案）** | 结束时热端推动模型离开打印板 | **免费**（仅改 G-code） | Bambu A1（Y轴电机） | ⚠️ 需适配 |
| **SimplyPrint AutoPrint** | 配合 PlateCycler / Printflow3D 换板套件 | 软件订阅制 | 多款打印机 | ⚠️ 需硬件 |
| **DHR Engineering 机器人方案** | 6 轴机械臂 + 定制夹爪 + VLM 耗材系统 | **$ 面议**（企业级） | 定制 | ⚠️ 可参考 |
| **DIY 换板机器人** | 步进电机 + 推杆 + 门舵机 | ¥500-2000 | 需适配 | ⚠️ 可行 |

### 3.3 "推出去"方案 vs "换板"方案

#### 方案 A：推出去（Eject Only）

**原理**：打印完成后，通过 G-code 控制热端或推板将模型从打印板上推落。

```
打印完成 → 等待冷却 → G-code: 热端推动模型 → 模型掉入收集容器
```

**优点**：无需机械臂，最简单  
**缺点**：模型表面可能损伤，不换板，不能连续打印多批次

**H2C 实现难度**：⭐⭐（中等）
- H2C 是 CoreXY 结构，热端可 XY 移动
- 可在 end G-code 中添加推模型动作
- 但需要解决：门不开→模型如何掉出？

#### 方案 B：换板（Bed Swap）—— 收菜闭环核心

**原理**：额外准备 2-3 块打印板 + 机械装置自动更换。

```
打印完成 → 机器人取走带模型的板 → 放入新干净板 → 开始下一轮打印
```

**优点**：模型完好，可连续打印  
**缺点**：需要多块板（¥100-200/块）+ 夹爪 + 门自动化

**H2C 实现难度**：⭐⭐⭐⭐（很难）

### 3.4 收菜闭环关键技术难点

| 难点 | 说明 | 解决方案 |
|------|------|---------|
| **1. 门自动化** | H2C 门为玻璃铰链门，需舵机或推杆 | MG996R 舵机 + G-code 触发 |
| **2. 磁性板夹取** | 板靠磁力吸附，夹取时需克服磁力 | 薄片插入法（参考 Prusa farm） |
| **3. 打印板余温** | PEI 板打印后温度 50-60°C | 等待冷却或隔热夹具 |
| **4. 模型粘附力** | PEI 板粘附力强，强行取下会变形 | VAAPR 表面处理 / 冷却后 Flexor |
| **5. Z 轴安全** | 机械臂进入时热端可能下移 | 限位 G-code + 物理限位 |
| **6. 耗材清理** | 打印板上有purge线/raft | 换板时一并清理或选区打印 |

### 3.5 竞品对比：谁更适合自动化？

| 打印机 | 换板自动化难度 | 成熟方案 | 推荐度 |
|--------|-------------|---------|--------|
| **Prusa MK4** | ⭐⭐（容易） | Prusa 官方 Farm System（$3000+/台）| ⭐⭐⭐⭐⭐ |
| **Voron Trident** | ⭐⭐⭐（较难） | Belt printer（连续打印）| ⭐⭐⭐ |
| **Bambu P1S** | ⭐⭐⭐（较难） | 3DQue AutoFarm3D（$179）| ⭐⭐⭐ |
| **Bambu H2C** | ⭐⭐⭐⭐（很难） | 社区 DIY（无成熟方案）| ⭐⭐ |

**关键差异**：H2C 的 Vortek 工具架占用右侧空间，增加了机械臂干涉风险。

### 3.6 可行性评分

| 阶段 | 可行性 | 成本 | 时间 |
|------|--------|------|------|
| **阶段1：Eject Only（推出去）** | ⭐⭐⭐⭐（80%） | ¥0 | 1-2 天 |
| **阶段2：换板自动化** | ⭐⭐（40%） | ¥1000-3000 | 1-3 个月 |
| **阶段3： filament 耗材自动补充** | ⭐（20%） | ¥5000+ | 6-12 个月 |

---

## 4. 综合建议

### 最优方案路径

```
第一阶段（立即可做）：
Blender → STL → Bambu Studio (Linux CLI) → H2C (LAN Mode)
     ↓
bambuslabs_api (Python) → 监控 + 自动触发打印

第二阶段（1-3个月）：
G-code Eject 方案 → InfinityFlow3D AutoClear for A1 思路移植
     ↓
实现"打印完自动推出去"

第三阶段（长期）：
换板机器人 → 门舵机 + 夹爪 + 多块板
     ↓
参考 DHR Engineering 或 3DQue 方案
```

### 具体推荐配置

#### 软件栈（Ubuntu）

```bash
# 1. Bambu Studio Linux
wget https://github.com/bambulab/BambuStudio/releases/latest/download/Bambu_Studio_linux_fedora.AppImage
chmod +x Bambu_Studio_linux_fedora.AppImage

# 2. Python SDK
pip install bambulabs_api

# 3. CLI 辅助工具
brew install davglass/tap/bambu-cli  # mac/Linux
# 或：git clone https://github.com/davglass/bambu-cli
```

#### Blender 自动化

```python
# blender_automation.py
import subprocess, os

def blender_to_h2c(blend_file, output_dir):
    # Step 1: Blender CLI export STL
    subprocess.run([
        "blender", blend_file,
        "--background", "--python-expr",
        "import bpy; bpy.ops.export_mesh.stl(filepath='"+output_dir+"/model.stl')"
    ])
    
    # Step 2: Bambu Studio CLI slice
    result = subprocess.run([
        "./Bambu_Studio_linux.AppImage",
        output_dir + "/model.stl",
        "--slice", "1",
        "--arrange", "1",
        "--load-settings", "H2C_standard.json",
        "--outputdir", output_dir
    ], capture_output=True)
    
    return result.returncode == 0
```

### 风险提示

1. **H2C + Linux 崩溃 Bug**：发送打印任务时 50% 概率崩溃，自动化脚本需加入重试逻辑
2. **Bambu Local Server SDK 暂无 Linux 版**：企业级集成需等官方支持
3. **H2C 换板自动化无成熟方案**：需要大量 DIY 工作，难度高于 P1S 等机型
4. **LAN Mode 稳定性**：社区反馈 LAN Mode 有时不稳定，建议同时保留 SD 卡打印能力

### 资源汇总

| 资源 | 链接 |
|------|------|
| Bambu Studio Linux 下载 | github.com/bambulab/BambuStudio/releases |
| Bambu Studio CLI 文档 | github.com/bambulab/BambuStudio/wiki/Command-Line-Usage |
| bambu-cli | github.com/davglass/bambu-cli |
| bambulabs_api (PyPI) | pypi.org/project/bambulabs-api |
| Bambu-Lab-Cloud-API | github.com/coelacant1/Bambu-Lab-Cloud-API |
| Blender 3MF IO 插件 | extensions.blender.org/add-ons/threemf-io |
| 3DQue AutoFarm3D | shop.3dque.com（$179 USD）|
| SimplyPrint AutoPrint | simplyprint.io |
| InfinityFlow3D AutoClear | infinityflow3d.com |
| DHR Engineering 自动化 | dhr.is |

---

*调研完成。关键结论：Ubuntu + H2C 可用，但有已知 Bug；Blender→H2C CLI 自动化链路可行；收菜闭环在 H2C 上难度较高，建议从 eject-only 开始。*
