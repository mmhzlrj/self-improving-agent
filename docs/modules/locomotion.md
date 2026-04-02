# 移动底盘模块

> 四轮差速底盘，ROS 2 导航栈，Jetson Nano 2GB 主控，LiDAR 室内导航

## 概述

移动底盘模块是 0-1 机器人从"固定位置"走向"自主移动"的关键一步。四轮差速底盘配合 ROS 2 导航栈，实现室内自主导航、避障和路径规划。Jetson Nano 2GB 作为主控节点，通过 ESP32-CAM micro-ROS 接入 ROS 2 网络，实现运动控制指令下发。Phase 6 阶段目标为实现室内环境下的自主移动和智能家居硬件拓展。

## 硬件参数

| 参数 | 规格 |
|------|------|
| 底盘类型 | 四轮差速驱动 |
| 主控 | Jetson Nano 2GB（B01 量产模块）|
| ROS 2 版本 | Foxy Fitzroy（Ubuntu 20.04，仅装 ros-base）|
| 内存占用 | ROS 2 core ~300-400MB，完整 ros-base ~600-800MB |
| ESP32-CAM micro-ROS | 520KB SRAM，接入 ROS 2 网络 |
| LiDAR（推荐）| 思岚 A1M8 / RPLIDAR A1（12m 测距，360°扫描）|
| 导航框架 | ROS 2 Navigation Stack（move_base / Nav2）|

## 技术方案

**ROS 2 通信架构**：
```
OpenClaw Gateway (MacBook)
    ↓ WebSocket / MQTT
Jetson Nano 2GB（ROS 2 Foxy 主节点）
    ├─ Navigation Stack（路径规划、避障）
    ├─ LiDAR SLAM（gmapping / cartographer）
    └─ 运动控制指令
         ↓
    ESP32-CAM（micro-ROS 节点，接入 ROS 2 网络）
         ↓ PWM / UART
    电机驱动板 → 四轮差速电机
```

**四轮差速控制原理**：
- 左右两侧各两个轮子，每侧轮子由同一个电机驱动
- 差速转向：左侧轮速 > 右侧轮速 → 右转，反之左转
- 直行：两侧轮速相同
- 原地转向：两侧轮速相同但方向相反

**Jetson Nano 2GB ROS 2 安装（关键步骤）**：
```bash
# 仅安装 ros-base，节省内存
sudo apt install -y ros-foxy-ros-base python3-argcomplete

# 永远不用 rviz2（rviz2 在 2GB 上会 OOM）
# 用远程设备做可视化

# 开启最大性能
sudo nvpmodel -m 0
sudo jetson_clocks

# 必须开启 swap（同时跑 Nav2 + SLAM 必须）
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

**micro-ROS ESP32-CAM 接入**：
```cpp
// ESP32-CAM micro-ROS 节点
#include <micro_ros_arduino.h>
#include <geometry_msgs/msg/twist.h>

rcl_node_t node;
rcl_publisher_t cmd_pub;
geometry_msgs__msg__Twist cmd_msg;

void setup() {
    set_microros_wifi_transports("SSID", "password", "agent-ip", 8888);
    rclc_node_init_default(&node, "esp32_diff_drive", "", &support);
    rclc_publisher_init_default(&cmd_pub, &node,
        ROSIDL_GET_MSG_TYPE_SUPPORT(geometry_msgs, msg, Twist),
        "/diff_drive/cmd_vel");
}

void loop() {
    // 接收 ROS 2 /cmd_vel → 转换为 PWM 电机控制
    // 左轮 speed_l，右轮 speed_r
    delay(100);
}
```

## 当前状态

| 项目 | 状态 |
|------|------|
| 四轮底盘机械结构 | 🔄 待设计/采购 |
| Jetson Nano 2GB ROS 2 Foxy | 🔄 待安装 |
| LiDAR 采购 | 🔄 推荐 A1M8（待采购）|
| ESP32-CAM micro-ROS 接入 | 🔄 待实现 |
| ROS 2 Navigation Stack | 🔄 待配置 |
| 差速运动控制实测 | 🔄 待实现 |

**Phase 6 里程碑**：
- [ ] 底盘机械结构安装（四轮 + 电机驱动）
- [ ] Jetson Nano 烧录 JetPack + 安装 ROS 2 Foxy ros-base
- [ ] LiDAR（A1M8）SLAM 建图
- [ ] ESP32-CAM micro-ROS 节点接入 ROS 2
- [ ] 差速控制实测（前进/后退/转向）
- [ ] Navigation Stack 避障导航实测

## 问题记录

**Jetson Nano 2GB 内存瓶颈**
- **现象**：同时跑 SLAM + Navigation + ROS 2 core 时 OOM
- **原因**：2GB 内存极限，多个重量级节点同时运行
- **解决方案**：
  1. 仅安装 ros-base，不用 desktop（节省 500MB+）
  2. 永远开 swap（4GB 起步）
  3. 不用 rviz2，用手机/平板做可视化
  4. Nav2 参数调优：降低地图分辨率、关闭不必要的插件

**LiDAR 建图漂移问题**
- **现象**：SLAM 建图时出现地图错位、走廊偏移
- **原因**：轮式里程计精度不足（积分误差累积）
- **解决方案**：
  1. 添加 IMU 传感器做多传感器融合（EKF）
  2. 定期回环检测修正（loop closure）
  3. 减慢机器人移动速度（减少里程计误差累积速率）

**ROS 2 Foxy 非 LTS 风险**
- Foxy 是 Ubuntu 20.04 的 LTS 版本，但 ROS 2 Foxy 本身已于 2023 年停止维护
- 备选升级方案：Jetson AGX Thor 到位后安装 Humble Hawksbill（22.04 LTS）
- 短期（Nano 2GB 阶段）：继续用 Foxy，稳定优先

## 参考链接

- [ROBOT-SOP.md - Phase 6 室内移动与智能家居硬件拓展](../harness/robot/ROBOT-SOP.md#phase-6室内移动与智能家居硬件拓展)
- [ROBOT-SOP.md - ROS 2 支持情况与替代框架](../harness/robot/ROBOT-SOP.md#ros-2-支持情况与替代框架)
- [ROBOT-SOP.md - Jetson Nano 2GB 完整 ROS 2 方案](../harness/robot/ROBOT-SOP.md#jetson-nano-2gb--完整-ros-2-方案)
- [ROBOT-SOP.md - ESP32-CAM micro-ROS 接入](../harness/robot/ROBOT-SOP.md#esp32-cam--micro-ros-接入方案)
