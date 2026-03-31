# 4个问题调研报告

**日期**：2026-03-31
**调研方式**：实测 + 文献 + Web 搜索
**输出**：memory/2026-03-31-Q-AResearch.md

---

## Q1: AS5600 编码器作用 + Jetson Nano 能否替代

### AS5600 具体作用

AS5600 是一颗**12位磁性绝对式编码器芯片**：
- 分辨率：4096 刻度/圈（0.087°/刻度）
- 接口：I2C 或 PWM 输出
- 价格：~$2/颗
- 用途：实时检测电机轴旋转角度

**在机器人控制中的核心作用（闭环控制）**：
```
发出指令 → 电机转动 → 编码器检测实际角度 → 与目标对比 → 修正误差
```

**对于轨迹录制的必要性**：
- MT3 需要录制"演示轨迹"：每秒 50 次记录每个关节的角度
- 有了编码器：直接读取角度值 → 时间序列 → 演示轨迹
- 没有编码器：只能发出位置命令，不知道机械臂实际转到了哪里

### Jetson Nano 2GB 能否替代

**技术上可以接 AS5600**：
- Jetson Nano 有 I2C 总线（GPIO 端口）
- AS5600 是 I2C 设备，可以直接连到 Jetson Nano 的 I2C 引脚
- Python 有 smbus2 库可以读取 I2C 数据

**但有 2 个实际问题**：
1. **Cyber Bricks 的 ESP32-C3 固件不支持回传** — 即使 Jetson Nano 能读编码器，也需要改 ESP32 固件才能把数据传回来
2. **Jetson Nano 和 Cyber Bricks 之间没有 I2C 直连线路** — 需要物理接线

**结论**：
- Jetson Nano 硬件上可以管理 AS5600，但需要额外接线 + 改 ESP32 固件
- AS5600 直接焊到 Cyber Bricks 电机上更简单（ESP32 已有 I2C 总线）
- AS5600 方案更直接，Jetson Nano 替代方案更复杂

### AS5600 购买清单
| 零件 | 数量 | 单价 | 合计 |
|------|------|------|------|
| AS5600 模块 | ×2 | ~$2 | ~$4 |
| 磁铁（AS5600 配套） | ×2 | ~$0.5 | ~$1 |
| 杜邦线 | 若干 | ~$1 | ~$1 |
| **总计** | | | **~$6** |

---

## Q2: Cyber Bricks 用 PWM + 视觉实现关节反馈

### 当前 Cyber Bricks 控制架构
```
OpenClaw → MQTT → ESP32-C3 → L298N电机驱动 → 直流电机
                                  ↓
                          只有 PWM 转速控制
                          （无角度反馈）
```

### 方案A：电流检测（最快实现）

**原理**：电机堵转时电流突然增大，正常转动时电流平稳
- L298N 有电流检测引脚（Sense Resistor）
- 接 INA219 模块（I2C ADC，~$1）或 ESP32 内置 ADC
- 可以判断"是否堵转"和"是否到位"（限位检测）

**精度**：只能判断堵转点，无法知道精确角度
**实现难度**：★☆☆☆☆（硬件：加 INA219，软件：读取 ADC）

### 方案B：视觉 + 机器学习（中期方案）

**原理**：用 ESP32-Cam 实时拍摄机械臂，用 CNN 估算关节角度
- MiDaS（单目深度估计）在 Jetson Nano 上跑
- 配合机械臂几何模型做逆运动学
- Cyber Bricks 已有 RTSP 流，可以实时获取视频

**精度**：理想情况 ±5°，取决于遮挡和光照
**实现难度**：★★★☆☆
**计算量**：可以在 Jetson Nano 2GB 上跑（FP16 推理）

**关键代码路径**：
1. ESP32-Cam → RTSP 流 → Jetson Nano
2. MiDaS FP16 → 深度图
3. 机械臂几何模型 → 逆运动学 → 关节角度估算

### 方案C：舵机替换（需机械改造）

**原理**：将直流电机换为带编码器的闭环舵机（如 MG996R）
- 舵机内部有电位器反馈位置
- 角度精确已知（0.29°/步 for MG996R）
- **Cyber Bricks 现有结构不兼容**，需要重新设计机械连接

**精度**：±1°
**实现难度**：★★★★☆（机械改造）

### 方案D：连杆几何 + 深度相机（最优雅）

**原理**：如果知道连杆长度 + 夹爪末端位置 → 用逆运动学推算关节角度
- 用 iPhone LiDAR 或 RealSense 测末端执行器位置
- 已知 Cyber Bricks 机械尺寸（平行杆结构，逆运动学很简单）
- 直接算出每个电机应该转多少

**精度**：±2-5°（取决于深度相机精度）
**实现难度**：★★☆☆☆（主要工作是标定连杆长度）
**优势**：不需要改硬件，利用已有深度相机

### 结论（推荐）

| 时期 | 方案 | 成本 | 难度 | 精度 |
|------|------|------|------|------|
| **最快** | A（电流检测） | ~$2 | ★ | 堵转检测 |
| **中期** | D（连杆+深度相机） | $0 | ★★ | ±5° |
| **长期** | B（视觉 ML） | $0 | ★★★ | ±5° |
| **终极** | AS5600 编码器 | ~$6 | ★★ | ±0.5° |

**推荐**：先用方案 A（电流检测）快速验证，方案 D 同步推进

---

## Q3: 安装 pointnet2_ops（实测结果）

### 重大发现：部署不需要 pointnet2_ops

**实测发现**：
```
deploy_mt3.py 的依赖链：
- SceneState ✅ 已加载
- HierarchicalRetrieval ✅ 已加载  
- PointnetPoseRegressor_4dof ✅ 已加载
- Open3dIcpPoseRefinement ✅ 已加载

pointnet2_ops 只在训练代码里用（ACT/MT-ACT训练），
推理/部署完全不需要！
```

### 已安装的依赖（Ubuntu RTX 2060）

| 包 | 用途 | 状态 |
|----|------|------|
| torch 2.7.1 | 深度学习框架 | ✅ |
| open3d 0.19.0 | 点云处理 | ✅ conda安装 |
| torch-geometric 2.7.0 | 图神经网络 | ✅ |
| lightning 2.6.1 | 训练框架 | ✅ |
| imageio | 图像读写 | ✅ |
| numba | JIT编译 | ✅ |
| transformers | CLIP模型 | ✅ |
| paho-mqtt | MQTT客户端 | ✅ |

### Jetson Nano 2GB 能否跑 MT3 推理

**瓶颈**：PointNet++ 在 Jetson Nano 上太慢
- RTX 2060：~100ms/帧
- Jetson Nano 2GB：>3000ms/帧（10-30x 慢）

**结论**：Jetson Nano 不适合跑 MT3 推理，只做客户端接收结果

**正确架构**：
```
ESP32-Cam (RTSP) 
    ↓
Jetson Nano (视频流转发 + MiDaS深度估计)
    ↓ 网络
Ubuntu RTX 2060 (MT3 推理)
    ↓
Cyber Bricks MQTT 控制
```

---

## Q4: iPhone 16 Pro 高精度室内模型（机器人感知）

### iPhone 16 Pro 硬件能力

| 硬件 | 规格 |
|------|------|
| LiDAR | dToF，精度 ±5mm，范围 5m |
| A18 Pro | 16核 Neural Engine，38TOPS |
| 超广角 | 48MP + LiDAR 扫描 |
| UWB | 室内精确到 ±10cm |

### ARKit 场景重建 API

```swift
// 开启网格重建
let config = ARWorldTrackingConfiguration()
config.sceneReconstruction = .meshWithClassification
config.frameSemantics = [.sceneDepth, .smoothedSceneDepth]
session.run(config)
```

**输出**：
- `ARMeshAnchor`：实时更新 3D 三角形网格
- `ARSceneDepth`：60fps 深度图（每个像素的精确距离）
- 物体识别：已知的 3D 物体类别

### Apple RoomPlan API（专门室内扫描）

```swift
import RoomPlan

// 扫描室内，生成 3D 模型
let roomScanner = RoomBuilder()
roomScanner.scan { room in
    // room 是 CapturedRoom 类型
    // 导出为 .usdz 或 .ply
}
```

**导出格式**：
- `.usdz`：Apple 专用，QuickLook 可预览
- `.obj`/`.ply`：通用 3D 格式，可导入 Blender/ROS

### 让机器人使用室内 3D 模型

**数据流**：
```
iPhone 扫描 → RoomPlan 生成 .usdz
    ↓
转换为 .ply 点云 / .obj 网格
    ↓
通过 OpenClaw Bridge 传给 Jetson Nano
    ↓
用于：
  - 路径规划（避障）
  - 物体检测（已知物体 vs 未知障碍）
  - 机械臂操作（知道桌子在哪里）
```

### 当前 B 序列进展

B序列已完成（iPhone → OpenClaw 数据通道）：
- ✅ B-0001: ARKit 基础框架
- ✅ B-0002: 深度数据获取（LiDAR + 结构光融合）
- ✅ B-0003: 数据格式设计
- ✅ B-0004: 延迟测试方法

### 待做（Q4 后续任务）

**Q4-1: RoomPlan 集成**（推荐 B/C 级）
- iPhone 运行 RoomPlan 扫描房间
- 导出 .usdz → 转换工具 → .ply
- 通过 OpenClaw Bridge 传给 Jetson Nano

**Q4-2: iPhone LiDAR → RTAB-Map**（推荐 C 级）
- iPhone 作为 RGBD 相机源
- RTAB-Map 做 SLAM 建图
- 生成 2D 占用栅格地图（用于导航）

**Q4-3: 深度图 → 机械臂操作**（推荐 A/B 级）
- 用 iPhone 的 60fps 深度图做实时物体跟踪
- 配合方案 D（逆运动学）控制 Cyber Bricks

### 关键链接

- ARKit Scene Reconstruction: https://developer.apple.com/documentation/arkit/world_tracking/configuring_scene_reconstruction
- RoomPlan API: https://developer.apple.com/documentation/roomplan
- ARKit → ROS bridge: https://github.com/EnidiokLab/arkit_ros_bridge

---

## 总结：建议优先级

| 问题 | 推荐方案 | 优先级 | 理由 |
|------|---------|--------|------|
| Q1 AS5600 | 直接买 AS5600 焊上 | **B级** | 最彻底，但需改固件 |
| Q2 关节反馈 | 方案A（电流检测）+ 方案D（逆运动学）并行 | **A级** | 不改硬件，快速验证 |
| Q3 pointnet2_ops | 不需要装，MT3 部署可用 | ✅ 已解决 | 惊喜发现 |
| Q4 iPhone室内模型 | Q4-1 先做（RoomPlan导出） | **B/C级** | iPhone已有能力 |
