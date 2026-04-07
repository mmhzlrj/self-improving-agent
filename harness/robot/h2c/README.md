# 拓竹 H2C × Ubuntu 自动化驱动

> 拓竹 H2C（双喷头 3D 打印机）的 Linux 控制脚本，支持 Blender → 切片 → H2C 打印全链路自动化。

**调研背景**：`memory/2026-04-01-H2C-Ubuntu-Research.md`

---

## 文件结构

```
harness/robot/h2c/
├── h2c_control.py       # H2C Python 控制脚本（MQTT/LAN Mode）
├── blender_to_h2c.py     # Blender → H2C 全链路自动化
├── eject_gcode.py        # 打印完成自动推出去（G-code）
├── config.json           # 配置文件（需用户填写）
└── README.md             # 本文件
```

---

## 目录

1. [安装依赖](#1-安装依赖)
2. [H2C LAN Mode 配置](#2-h2c-lan-mode-配置)
3. [配置文件填写](#3-配置文件填写)
4. [快速开始](#4-快速开始)
5. [单独使用 h2c_control.py](#5-单独使用-h2c_controlpy)
6. [Blender → H2C 自动化](#6-blender--h2c-自动化)
7. [自动推出去（Eject）](#7-自动推出去eject)
8. [已知 Bug 和 Workaround](#8-已知-bug-和-workaround)
9. [文件说明](#9-文件说明)

---

## 1. 安装依赖

### 系统依赖（Ubuntu 22.04 / 24.04）

```bash
# Ubuntu 24.04：AppImage 需要 libfuse2t64
sudo apt install libfuse2t64

# Ubuntu 22.04：修复 libwebkit2gtk 软链（如遇报错再执行）
sudo ln -sf /usr/lib/x86_64-linux-gnu/libwebkit2gtk-4.1.so.0 \
  /usr/lib/x86_64-linux-gnu/libwebkit2gtk-4.0.so.37
sudo ln -sf /usr/lib/x86_64-linux-gnu/libjavascriptcoregtk-4.1.so.0 \
  /usr/lib/x86_64-linux-gnu/libjavascriptcoregtk-4.0.so.18
```

### Python 依赖

```bash
pip install bambulabs_api
```

### Bambu Studio Linux AppImage

```bash
# 下载（选 Ubuntu 22.04 或 24.04 版本）
wget https://github.com/bambulab/BambuStudio/releases/latest/download/Bambu_Studio_ubuntu-22.04_PR-9504.AppImage
chmod +x Bambu_Studio_ubuntu-22.04_PR-9504.AppImage

# 验证可运行（弹出 GUI 即可关掉）
./Bambu_Studio_ubuntu-22.04_PR-9504.AppImage
```

### Blender（如需自动化导出）

```bash
# Ubuntu
sudo apt install blender

# macOS
brew install blender
```

---

## 2. H2C LAN Mode 配置

**为什么要开 LAN Mode？**
- 纯局域网通信，不走云端，隐私安全
- MQTT 长连接，实时状态推送
- 支持 Bambu Handy App 以外的本地控制

**开启步骤：**

1. H2C 打印机屏幕 → 设置（⚙️）→ 连接 → **LAN Only** → 开启
2. 屏幕会显示：
   - 主机名：`H2CXXXX`（序列号）
   - IP 地址：`192.168.x.x`
   - 访问码：`xxxx`（6位数字字母）

3. 记录这三个信息，填入 `config.json`

> ⚠️ **注意**：开启 LAN Only 后，Bambu Handy App 将无法远程控制打印机。

---

## 3. 配置文件填写

编辑 `config.json`：

```json
{
  "printer": {
    "host": "192.168.1.100",    ← 填打印机 IP
    "access_code": "ABC123",    ← 填 LAN Mode 访问码
    "serial": "H2C12AB",        ← 填序列号
    "lan_mode": true
  },
  "slicer": {
    "bambu_studio_path": "/home/user/Bambu_Studio_ubuntu-22.04.AppImage",
    "preset_file": "H2C_standard.json"   ← 切片刻隙预设
  },
  "paths": {
    "output_dir": "/tmp/h2c_jobs/",
    "gcode_dir": "/tmp/h2c_jobs/gcode/",
    "stl_dir": "/tmp/h2c_jobs/stl/"
  }
}
```

### 生成 H2C 切片预设文件

1. 在 Bambu Studio 中配置好 H2C 的打印参数（层高、耗材、温度等）
2. 打印机设置 → 导出配置 → 保存为 `H2C_standard.json`
3. 把这个 JSON 文件放到 `harness/robot/h2c/` 目录

---

## 4. 快速开始

### 第一步：验证连接

```bash
cd harness/robot/h2c/
python h2c_control.py --config config.json
```

预期输出（打印机的当前状态）：
```json
{
  "progress": 0,
  "nozzle_temp": 25.5,
  "bed_temp": 24.8,
  "gcode_state": "IDLE"
}
```

### 第二步：发送打印任务

```bash
python h2c_control.py --config config.json --gcode /path/to/model.gcode.3mf
```

### 第三步：监控打印状态

```bash
python h2c_control.py --config config.json --monitor
```

---

## 5. 单独使用 h2c_control.py

### 命令行用法

```bash
# 监控状态
python h2c_control.py --config config.json --monitor

# 暂停打印
python h2c_control.py --config config.json --pause

# 恢复打印
python h2c_control.py --config config.json --resume

# 取消打印
python h2c_control.py --config config.json --cancel

# 开门
python h2c_control.py --config config.json --open-door

# 关门
python h2c_control.py --config config.json --close-door
```

### Python 脚本中调用

```python
from h2c_control import H2CController

h2c = H2CController(config_path="config.json")

# 连接
if not h2c.connect():
    print("连接失败")
    exit(1)

# 上传并打印（含 Linux Bug 重试）
h2c.upload_and_print("model.gcode.3mf")

# 监控
h2c.monitor(
    on_complete=lambda: print("🎉 完成！"),
    on_error=lambda e: print(f"错误: {e}"),
)

h2c.disconnect()
```

### 状态回调

```python
def my_callback(status):
    print(f"进度: {status['progress']}% | "
          f"层: {status['layer']}/{status['total_layer']} | "
          f"剩余: {status['remaining_time']}s")

h2c.upload_and_print("model.gcode.3mf", progress_callback=my_callback)
```

---

## 6. Blender → H2C 自动化

### 完整链路

```
.blend 文件
    ↓ [blender_export_stl()]
STL 文件
    ↓ [Bambu Studio CLI slice]
.gcode.3mf 文件
    ↓ [h2c_control.upload_and_print()]
H2C 打印机 → 打印中 → 完成
```

### 用法

```bash
# 完整流程：Blender 导出 → 切片 → 上传打印
python blender_to_h2c.py model.blend --config config.json

# 只切片，不上传（调试用）
python blender_to_h2c.py model.blend --config config.json --no-print

# 指定 Blender 路径（macOS Blender.app）
python blender_to_h2c.py model.blend \
  --blender /Applications/blender.app/Contents/MacOS/blender

# 指定 Bambu Studio AppImage 路径
python blender_to_h2c.py model.blend \
  --bambu-studio ~/Downloads/Bambu_Studio_ubuntu-22.04.AppImage
```

### Python 调用

```python
from blender_to_h2c import blender_to_h2c

success, gcode_path = blender_to_h2c(
    blend_file="robot_arm.blend",
    output_dir="/tmp/print_jobs",
    config_path="config.json",
    upload=True,      # False=只切片不上传
    monitor=True,     # False=不上传后继续监控
)

print(f"结果: {'成功' if success else '失败'}")
print(f"G-code: {gcode_path}")
```

---

## 7. 自动推出去（Eject）

### 原理

在 H2C 的 end G-code 中添加推模型动作：

```
打印完成 → 等待冷却（60°C）→ 热端推动模型 → 模型掉入收集容器
```

### 使用方法

```python
from eject_gcode import generate_eject_gcode

# 生成带推模型动作的 end G-code
eject_code = generate_eject_gcode(
    push_distance=50,    # 推动距离（mm）
    cooldown_temp=60,    # 等待冷却到 60°C
    push_speed=1000,    # 推动速度（mm/min）
)

# 追加到切片时的 end G-code
# 在 Bambu Studio 的 "自定义 G-code" → "打印结束" 中粘贴 eject_code
```

### eject_gcode.py 详解

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `push_distance` | 50mm | 热端横向推动模型的距离 |
| `cooldown_temp` | 60°C | 等待热端冷却到此温度再推 |
| `push_speed` | 1000mm/min | 推动速度 |
| `z_lift` | 20mm | 推之前抬起的 Z 高度 |

### 集成到 Blender → H2C 流程

```python
from blender_to_h2c import blender_to_h2c
from eject_gcode import generate_eject_gcode

# 生成 eject G-code
eject = generate_eject_gcode(push_distance=50)

# TODO: 将 eject 注入到切片配置文件（目前需手动粘贴到 Bambu Studio）
# Bambu Studio → 切片设置 → 自定义 G-code → 打印结束

# 执行完整流程
blender_to_h2c("model.blend")
```

---

## 8. 已知 Bug 和 Workaround

### Bug 1：Linux 上发送打印任务 50% 概率崩溃（严重）

**问题描述**：[Issue #8980](https://github.com/bambulab/BambuStudio/issues/8980)  
H2C + Linux 发送打印任务时，Studio 窗口无响应，必须 kill 进程重试。

**Workaround**：
- `h2c_control.py` 的 `upload_and_print()` 已有自动重试逻辑（默认 5 次）
- Linux 生产环境建议：**先用 Studio GUI 手动发送一次**触发初始化，后续再用 CLI

### Bug 2：H2C 双喷头 CLI 参数异常

**问题描述**：[Issue #9963](https://github.com/bambulab/BambuStudio/issues/9963)  
`--filament-map` 和 `--curr-bed-type` 在双喷头时有异常。

**Workaround**：
- 使用 `.json` 预设文件代替命令行参数传递切片参数
- 避免直接在 CLI 中用 `--filament-colour` 等参数

### Bug 3：LAN Mode 偶发断连

**症状**：MQTT 连接几分钟后自动断开。

**Workaround**：
- 监控脚本中检测到断连自动重连
- H2C 路由器开启 AP 隔离会导致此问题，确保打印机和电脑在同一广播域

### Bug 4：Bambu Studio AppImage 在无显示器服务器上崩溃

**症状**：GUI 依赖缺失，段错误。

**Workaround**：
- 使用 OrcaSlicer（开源，完全 headless 友好）
- 或使用官方 Docker 镜像（见下）

### Linux 服务器完全 Headless 切片方案

如果你的 Ubuntu 没有显示器，推荐使用 Docker：

```bash
# 官方 Bambu Studio Docker
docker run -it --rm \
  -v /path/to/models:/input \
  -v /path/to/output:/output \
  bambulab/bambustudio:latest \
  /input/model.stl --slice 1 --outputdir /output
```

---

## 9. 文件说明

### h2c_control.py

核心控制脚本，基于 `bambulabs_api`（MQTT/LAN Mode）。

主要类：`H2CController`

| 方法 | 说明 |
|------|------|
| `connect()` | 连接打印机 |
| `upload_and_print(path)` | 上传 .gcode.3mf 并开始打印（含重试） |
| `send_print_job(path)` | 仅上传，不自动打印 |
| `pause()` / `resume()` / `cancel()` | 打印控制 |
| `open_door()` / `close_door()` | 门控制 |
| `get_status()` | 获取状态字典 |
| `monitor()` | 实时监控打印（Ctrl+C 停止） |

### blender_to_h2c.py

全链路自动化脚本。

| 参数 | 说明 |
|------|------|
| `--no-print` | 只做导出+切片，不上传 |
| `--no-monitor` | 上传后不监控状态 |
| `--config` | H2C 配置文件 |
| `--blender` | Blender 可执行文件路径 |
| `--bambu-studio` | Bambu Studio AppImage 路径 |
| `--preset` | 切片预设 JSON |

### eject_gcode.py

生成推模型 G-code。`generate_eject_gcode()` 返回字符串，可粘贴到 Bambu Studio 的 end G-code 中。

### config.json

所有可配置参数。**必须填写 `printer.host`、`printer.access_code`、`printer.serial` 才能正常运行。**

---

## 下一步

- ✅ 本地验证连接
- ⬜ 导出 H2C 切片预设 JSON
- ⬜ 跑通完整链路（.blend → .gcode.3mf → H2C）
- ⬜ 测试 eject G-code
- ⬜ 集成到自动化流水线（定时打印等）
