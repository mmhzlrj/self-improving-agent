# MT3（Multi-Task Trajectory Transfer）落地 0-1 机器人调研报告

**调研日期：** 2026-03-31
**调研人：** Subagent（MT3-Research）
**背景项目：** 0-1 机器人（Cyber Bricks + Jetson Nano 2GB + ESP32-Cam）

---

## 一、MT3 核心原理摘要

### 1.1 论文与代码

| 项目 | 信息 |
|------|------|
| 论文 | *"Learning a Thousand Tasks in a Day"*, Science Robotics, 2025 |
| 作者 | Kamil Dreczkowski, Pietro Vitiello, Vitalis Vosylius, Edward Johns（Imperial College London） |
| ArXiv | https://arxiv.org/abs/2511.10110 |
| GitHub | https://github.com/kamil-dreczkowski/learning_thousand_tasks |
| DOI | 10.1126/scirobotics.adv7594 |

### 1.2 核心创新：轨迹分解 + 检索泛化

MT3 提出两个关键先验，大幅提升少样本模仿学习效率：

**先验一：操作轨迹两阶段分解**

| 阶段 | 描述 | 要求精度 |
|------|------|----------|
| **Alignment（对齐）** | 机器人将末端执行器移动到适合操作目标物体的姿态 | 低精度，路径自由 |
| **Interaction（交互）** | 实际执行操作（抓取、插入、推开等） | 高精度，必须精确复现演示轨迹 |

两阶段分解比单阶段 monolithic policy（MT-ACT+）**数据效率提升一个数量级**（在 <10 个演示/任务的设定下）。

**先验二：检索式泛化（Retrieval-based Generalization）**

MT3 的 Alignment 和 Interaction 均使用**检索式方法**，而非 Behavioral Cloning（行为克隆）：

- 不需要为每个新任务训练神经网络
- 在推理时，从演示库中检索最相似的演示
- 将演示的轨迹变换到新场景（通过点云配准）

### 1.3 MT3 工作流程（推理阶段）

```
输入：新场景 RGB-D 图像 + 分割掩码
          ↓
Step 1: 构建点云场景状态（SceneState）
          ↓
Step 2: 层级检索（Hierarchical Retrieval）
         → 基于几何相似度找到最相似的演示
          ↓
Step 3: PointNet++ 相对位姿估计（4-DOF）
         → 估计演示物体 → 新场景物体的 4×4 变换矩阵
          ↓
Step 4: Generalized ICP 精细配准
         → 提升点云对齐精度
          ↓
Step 5: 应用 4DOF 归纳偏置
         → 约束为 x/y/z/yaw（去除 roll/pitch），适合桌面操作
          ↓
Step 6: 变换瓶颈姿态到新场景
         → 得到机械臂目标末端执行器位姿（Alignment 完成）
          ↓
Step 7: 加载演示的末端执行器 twists
         → [vx, vy, vz, wx, wy, wz, gripper_next]，在末端执行器坐标系下
          ↓
Step 8: 速度控制复现交互阶段
         → 末端执行器跟踪演示速度序列
```

### 1.4 核心模块详解

#### 检索模块（Hierarchical Retrieval）

基于几何相似度，从演示库中找到最相似的任务演示。使用 PointNet++ 提取点云几何特征（512维 embedding），通过最近邻检索匹配。

#### 位姿估计（PointNet++ 4-DOF Pose Regressor）

- 输入：演示物体点云 + 新场景物体点云
- 输出：4-DOF 变换（x, y, z, yaw）
- 训练：预训练模型（`geometry_encoder.ckpt` + `pose_estimator.ckpt`）
- 推理设备：GPU（CUDA）

#### ICP 精细配准

- 使用 Generalized ICP（点-面距离 + 协方差加权）
- 最大对应距离 10cm，最多 20 次迭代
- 进一步提升位姿精度

#### 4DOF 归纳偏置

桌面操作任务中，物体通常只在垂直轴（z 轴）有旋转，去除 roll/pitch 约束可以：
- 减少搜索空间
- 提升位姿估计鲁棒性

### 1.5 数据格式（MT3 演示格式）

每个演示任务目录包含：

| 文件 | 形状 | 类型 | MT3 必须 |
|------|------|------|----------|
| `head_camera_ws_rgb.png` | (720, 1280, 3) | uint8 | ✅ workspace RGB |
| `head_camera_ws_depth_to_rgb.png` | (720, 1280) | uint16 | ✅ 深度图（mm） |
| `head_camera_ws_segmap.npy` | (720, 1280) | bool | ✅ 物体分割掩码 |
| `head_camera_rgb_intrinsic_matrix.npy` | (3, 3) | float64 | ✅ 相机内参 |
| `bottleneck_pose.npy` | (4, 4) | float64 | ✅ 对齐目标姿态（SE(3)） |
| `demo_eef_twists.npy` | (T, 7) | float64 | ✅ 末端执行器速度 |
| `head_camera_rgb.npy` | (T, 720, 1280, 3) | uint8 | BC 训练用 |
| `head_camera_masks.npy` | (T, 720, 1280) | bool | BC 训练用 |

**Twist 格式**（每行）：
```
[vx, vy, vz, wx, wy, wz, gripper_next]
  m/s  m/s  m/s  rad/s rad/s rad/s  0=close, 1=open
```

---

## 二、Cyber Bricks 硬件能力清单

### 2.1 硬件规格（来自 0-1 项目 SOP）

| 参数 | 规格 |
|------|------|
| 主控 MCU | ESP32-C3（XA003/XA004/XA005）|
| 执行器 | 2× 电机 + 1× 舵机 |
| 通信 | WiFi + MQTT |
| 控制频率 | ESP32-C3 PWM ~50Hz |
| 循环延迟 | ~20-50ms |
| 视觉输入 | ESP32-Cam（OV2640），RTSP 流 |
| 主控计算 | Jetson Nano 2GB（Ubuntu）|

### 2.2 电机接口

```
Pin 12 → Motor1 IN1
Pin 13 → Motor1 IN2
（无 PWM 速度控制，仅方向控制）
```

**问题**：电机驱动为简单 H 桥，仅支持正/反转/停止，**无速度控制**，**无角度反馈**。

### 2.3 舵机接口

```
Pin 15 → Servo1 PWM
freq(50) → 50Hz PWM
角度公式：duty = int(40 + angle * 95 / 90)  # 0-90度范围
```

**问题**：舵机 PWM 控制角度，但**无角度反馈读取**（ESP32-C3 无 ADC 引脚反馈）。

### 2.4 MQTT 接口（规划中）

根据架构报告（`0-1-system-abm-architecture-report.md`）规划：

```
Pub: cyberbricks/motor/{id}/target_angle   # 目标角度（发送给 Cyber Bricks）
Sub: cyberbricks/motor/{id}/current_angle # 当前角度（从 Cyber Bricks 读取）
Sub: cyberbricks/gripper/state             # 夹爪状态
```

**当前固件状态**：仅有命令订阅（`{"type": "motor"/"servo"/"stop"}`），**尚未实现角度回传**。

### 2.5 Cyber Bricks 能力总结

| 能力 | 状态 | 说明 |
|------|------|------|
| 电机位置控制 | ❌ 不可行 | 无编码器反馈，仅方向控制 |
| 舵机角度控制 | ⚠️  开环 | 可发送 PWM 命令，但无角度读取 |
| 速度控制 | ❌ 不可行 | 电机无速度环 |
| 力反馈 | ❌ 无 | 无力传感器 |
| 关节角度读取 | ❌ 无 | 需要加装编码器 |
| 末端执行器位姿 | ❌ 无 | 需要正运动学，但无关节反馈 |

### 2.6 关键差距分析

| MT3 需求 | Cyber Bricks 现状 | 差距 |
|----------|-------------------|------|
| 关节角度反馈 | ❌ 无 | **致命差距** - 无法录制演示，无法闭环控制 |
| 末端执行器 twist 跟踪 | ❌ 无速度控制 | 需要改造电机驱动 |
| 力反馈 | ❌ 无 | 可接受（MT3 不强制需要力反馈）|
| RGB-D 输入 | ⚠️ 仅 RGB | **差距** - MT3 需要深度图 |
| 实时点云处理 | ⚠️ Jetson Nano 可行 | 需要 GPU，Jetson Nano 勉强 |

---

## 三、整合方案设计

### 3.1 部署架构决策

**MT3 推理部署在哪里？**

| 方案 | 优点 | 缺点 |
|------|------|------|
| **Ubuntu GPU（192.168.1.18, RTX 2060）** | PointNet++ 推理快（~100ms）；完整 Docker 环境；不占用 Jetson Nano | 需要网络通信（延迟~10-30ms）；两台机器架构更复杂 |
| **Jetson Nano 2GB** | 本地计算，无网络延迟；单机器架构简单 | GPU 弱（128 CUDA cores）；PointNet++ 推理慢（~1-5s）；Docker 可能内存不足 |

**推荐方案：Ubuntu GPU + 拉取式调用**

```
ESP32-Cam (RTSP) ──→ Jetson Nano (视频采集) ──→ Ubuntu GPU (MT3 推理)
                                              ↓
                              目标姿态 + twists
                                              ↓
Jetson Nano (指令调度) ← MQTT ← cyberbricks/cmd
```

**原因**：
1. MT3 的 PointNet++ 在 RTX 2060 上推理 ~100ms，Jetson Nano 可能 >2s
2. Jetson Nano 作为 OpenClaw Gateway，已承担调度角色，不应再跑重型推理
3. 网络延迟（~10-30ms）远小于 Jetson Nano 推理节省的时间

### 3.2 数据录制方案（演示采集）

**核心问题：Cyber Bricks 无关节编码器，无法直接录制关节角度**

**解决方案 A：人类遥操作录制（推荐）**

需要新增硬件：
- **方案 A1**：购买带编码器的舵机（如 MG996R 或带反馈的数码舵机）
- **方案 A2**：使用电位器分压电路，通过 ESP32-C3 的 ADC 引脚读取角度
- **方案 A3**：外接 IMU（MPU6050）估计末端执行器姿态

遥操作方式：
```
人类操作员手持 Cyber Bricks 末端 → 记录 ESP32-Cam RGB-D 图像序列
                                   → 同时记录手动输入的关节角度
                                   → 存储为 MT3 演示格式
```

**解决方案 B：视觉里程计 + 运动恢复结构（SfM）**

- 使用 ESP32-Cam 单目图像序列
- 通过视觉 SLAM（ORB-SLAM2/3）估计末端执行器运动轨迹
- 不需要硬件改造，但精度较低

**解决方案 C：BC-Alignment 替代检索式对齐（无需演示录制）**

如果无法录制演示，可以：
1. 用 BC（Behavioral Cloning）训练 Alignment 策略
2. 让机械臂自主探索来对齐（而非从演示对齐）
3. 然后用 Ret-BC（检索+BC）或 BC-BC 方法

### 3.3 深度图获取方案

**问题**：ESP32-Cam 只有单目 RGB，无深度信息

**解决方案**：

| 方案 | 精度 | 成本 | 复杂度 |
|------|------|------|--------|
| **MiDaS（单目深度估计）** | 中等（相对深度） | 低（AI 模型） | 中（Jetson Nano 可跑）|
| **RealSense D415/D435** | 高 | ~$150 | 高（需 USB + ROS 驱动）|
| **Stereo ESP32-Cam** | 低-中 | 低 | 高（需校准）|

**推荐：MiDaS on Jetson Nano**

MT3 使用的是几何检索+配准，对深度精度要求不是极端高（后续有 ICP 精细化），MiDaS 的相对深度估计足够。

### 3.4 MQTT ↔ MT3 输出映射

MT3 输出格式：
```
Alignment:   4×4 末端执行器目标姿态（T_WE_live）
Interaction:  N×7 末端执行器 twists [vx,vy,vz,wx,wy,wz,gripper_next]
```

**映射到 Cyber Bricks 的问题**：

Cyber Bricks 只有 2 个电机 + 1 个舵机 = **3 DOF**，而 MT3 演示数据来自 **6-7 DOF 机械臂**（WidowX）。

**降维方案**：

| MT3 输出 | Cyber Bricks 执行方式 |
|----------|----------------------|
| 目标末端姿态（4×4）| 逆运动学 → 3 个关节角度 → 关节插值到达 |
| 末端 twist [vx,vy,vz,wx,wy,wz] | **不可行**：Cyber Bricks 无速度控制，只能位置控制 |
| gripper_next | 舵机角度映射（0°=闭合，90°=张开）|

**关键限制**：
- Cyber Bricks 只能执行**位置控制**，无法跟踪 twist 速度序列
- Interaction 阶段需要改造：直接给出末端执行器位置序列（而非速度序列）

### 3.5 代码框架

#### 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     Jetson Nano 2GB                         │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ ESP32-Cam   │  │ OpenClaw     │  │ Cyber Bricks    │  │
│  │ RTSP 采集   │→ │ Gateway      │← │ MQTT 驱动       │  │
│  │ (RGB-D)     │  │ (System M)    │  │ (命令下发)       │  │
│  └─────────────┘  └──────────────┘  └─────────────────┘  │
│         ↓                ↑                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              MT3 推理客户端（gRPC/HTTP）              │  │
│  │  - 图像编码 → 发送到 Ubuntu GPU                       │  │
│  │  - 接收目标姿态 + twists                              │  │
│  └──────────────────────────────────────────────────────┘  │
│         ↓                ↑                                  │
└─────────│────────────────│──────────────────────────────────┘
          │ 网络（MQTT/TCP）│
          ↓                ↑
┌─────────────────────────────────────────────────────────────┐
│               Ubuntu 192.168.1.18 (RTX 2060)                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   MT3 Docker 容器                    │  │
│  │  ┌────────────┐  ┌──────────────┐  ┌────────────┐  │  │
│  │  │ MiDaS      │  │ Hierarchical │  │ PointNet++ │  │  │
│  │  │ 深度估计   │→ │ Retrieval    │→ │ 4-DOF Pose │  │  │
│  │  └────────────┘  └──────────────┘  └────────────┘  │  │
│  │         ↓              ↓              ↓            │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │           ICP 精细化 + 4DOF 约束             │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  │         ↓                                           │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │ 输出: target_pose (4×4) + eef_twists (N×7)  │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

#### MT3 推理服务（Ubuntu GPU）

```python
# mt3_inference_server.py
# 运行在 Ubuntu 192.168.1.18:50051
# 使用 Docker 容器（见 Makefile: make deploy_mt3）

from deployment.deploy_mt3 import main as mt3_pipeline
import grpc
import mt3_pb2
import mt3_pb2_grpc
import numpy as np
from PIL import Image
import torch

class MT3Servicer(mt3_pb2_grpc.MT3Servicer):
    def __init__(self):
        # 加载预训练模型（Geometry Encoder + Pose Estimator）
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        # 模型加载（从 thousand_tasks/checkpoints/）

    def Infer(self, request, context):
        # Step 1: 反序列化 RGB + 分割掩码
        rgb = np.frombuffer(request.rgb_data, dtype=np.uint8).reshape(
            request.rgb_height, request.rgb_width, 3)
        depth = np.frombuffer(request.depth_data, dtype=np.uint16).reshape(
            request.rgb_height, request.rgb_width)
        segmap = np.unpackbits(request.segmap_data).reshape(
            request.rgb_height, request.rgb_width)

        # Step 2: 构建 SceneState
        scene_state = SceneState.initialise_from_dict({
            'rgb': rgb, 'depth': depth, 'segmap': segmap,
            'intrinsic_matrix': np.array(request.intrinsics).reshape(3, 3)
        })
        scene_state.erode_segmap()
        scene_state.crop_object_using_segmap()

        # Step 3: 检索演示
        retrieval = HierarchicalRetrieval(T_WC_demo=request.T_WC,
                                          T_WC_live=request.T_WC,
                                          learned_tasks_dir=DEMO_DIR)
        demo_name = retrieval.get_most_similar_demo_name(scene_state, request.task_desc)

        # Step 4: PointNet++ 位姿估计
        pose_estimator = PointnetPoseRegressor_4dof(device=self.device, T_WC=request.T_WC)
        W_T_delta = pose_estimator.estimate_relative_pose(demo_state, scene_state)

        # Step 5: ICP 精细化 + 4DOF 约束
        pose_refiner = Open3dIcpPoseRefinement(...)
        W_T_delta_refined = pose_refiner.refine_relative_pose(...)
        W_T_delta_4dof = apply_4dof_inductive_bias(W_T_delta_refined, demo_bn_pose)

        # Step 6: 变换瓶颈姿态
        live_bn_pose = W_T_delta_4dof @ demo_bn_pose  # 4×4 matrix

        # Step 7: 加载交互 twists
        eef_twists = np.load(DEMO_DIR / demo_name / 'demo_eef_twists.npy')

        # 返回
        return mt3_pb2.InferenceResult(
            target_pose=live_bn_pose.flatten().tolist(),  # 16 floats
            eef_twists=eef_twists.flatten().tolist(),      # N×7 floats
            num_timesteps=len(eef_twists),
            retrieved_demo=demo_name
        )

if __name__ == '__main__':
    server = grpc.server()
    mt3_pb2_grpc.add_MT3Servicer_to_server(MT3Servicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()
```

#### Cyber Bricks MQTT 驱动（Jetson Nano 端）

```python
# cyberbricks_driver.py
# 运行在 Jetson Nano，通过 MQTT 与 Cyber Bricks ESP32-C3 通信

import paho.mqtt.client as mqtt
import numpy as np
import time

MQTT_BROKER = "192.168.x.x"  # Jetson Nano 作为 MQTT Broker
TOPIC_CMD = "0-1/cyberbrick/cmd"
TOPIC_MOTOR_STATE = "0-1/cyberbrick/motor/state"
TOPIC_SERVO_ANGLE = "0-1/cyberbrick/servo/angle"

class CyberBricksDriver:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_message = self._on_message
        self.current_motor_angles = [0, 0]  # 电机1, 电机2 角度
        self.current_servo_angle = 90        # 舵机角度
        self._angles_lock = threading.Lock()

    def _on_message(self, client, userdata, msg):
        # 解析 Cyber Bricks 回传的角度（需要刷新的固件支持）
        payload = json.loads(msg.payload)
        if msg.topic == TOPIC_MOTOR_STATE:
            with self._angles_lock:
                self.current_motor_angles = payload['angles']
        elif msg.topic == TOPIC_SERVO_ANGLE:
            with self._angles_lock:
                self.current_servo_angle = payload['angle']

    def get_joint_states(self):
        """读取当前关节角度"""
        with self._angles_lock:
            return {
                'motor1': self.current_motor_angles[0],
                'motor2': self.current_motor_angles[1],
                'servo': self.current_servo_angle,
                'timestamp': time.time()
            }

    def set_motors(self, angle1, angle2, duration_s=1.0):
        """
        发送电机目标角度命令
        注意：Cyber Bricks 固件需修改为支持角度闭环控制
        """
        # 角度 → PWM 占空比（需要标定）
        pwm1 = self._angle_to_pwm(angle1)
        pwm2 = self._angle_to_pwm(angle2)
        self.client.publish(TOPIC_CMD, json.dumps({
            'type': 'motor_angles',
            'motor1_pwm': pwm1,
            'motor2_pwm': pwm2,
            'duration_ms': int(duration_s * 1000)
        }))

    def set_servo(self, angle):
        """发送舵机角度命令"""
        duty = int(40 + angle * 95 / 90)
        self.client.publish(TOPIC_CMD, json.dumps({
            'type': 'servo',
            'angle': angle
        }))

    def stop(self):
        """紧急停止"""
        self.client.publish(TOPIC_CMD, json.dumps({'type': 'stop'}))

    def _angle_to_pwm(self, angle):
        # 需要标定电机角度与 PWM 占空比的关系
        # 假设线性关系：angle_range [-180, 180] → PWM [40, 200]
        pwm_min, pwm_max = 40, 200
        angle_min, angle_max = -180, 180
        ratio = (angle - angle_min) / (angle_max - angle_min)
        return int(pwm_min + ratio * (pwm_max - pwm_min))
```

#### OpenClaw MT3 Skill（调度层）

```python
# mt3_skill.py
# OpenClaw System M 元控制器调度 MT3 任务

import grpc
import mt3_pb2
import mt3_pb2_grpc
from cyberbricks_driver import CyberBricksDriver
import numpy as np

UBUNTU_GPU_HOST = "192.168.1.18:50051"
CAMERA_TOPIC = "/esp32_cam/rgbds"

class MT3Controller:
    def __init__(self):
        self.stub = mt3_pb2_grpc.MT3Stub(
            grpc.insecure_channel(UBUNTU_GPU_HOST)
        )
        self.driver = CyberBricksDriver()

    def execute_task(self, task_description, rgb_image, depth_image, segmap):
        """
        执行 MT3 任务的两阶段控制
        """
        # ===== ALIGNMENT 阶段 =====
        # Step 1: 发送到 Ubuntu GPU 进行 MT3 推理
        request = mt3_pb2.InferenceRequest(
            rgb_data=rgb_image.tobytes(),
            depth_data=depth_image.tobytes(),
            segmap_data=segmap.packbits(),
            rgb_height=rgb_image.shape[0],
            rgb_width=rgb_image.shape[1],
            intrinsics=self._get_intrinsics(),
            T_WC=self._get_extrinsics(),  # 相机外参
            task_desc=task_description
        )
        result = self.stub.Infer(request)

        target_pose = np.array(result.target_pose).reshape(4, 4)
        twists = np.array(result.eef_twists).reshape(result.num_timesteps, 7)

        # Step 2: 逆运动学（Cyber Bricks 3-DOF）
        joint_angles = self._inverse_kinematics(target_pose)

        # Step 3: 关节空间插值到目标姿态
        self._move_to_pose(joint_angles, duration=2.0)

        # ===== INTERACTION 阶段 =====
        # Cyber Bricks 无法跟踪 twist（无速度控制）
        # 方案：将 twists 转换为位置序列（积分）→ 关节空间跟踪
        current_angles = self.driver.get_joint_states()
        eef_pose_sequence = self._integrate_twists(target_pose, twists)

        for i, eef_pose in enumerate(eef_pose_sequence):
            # 逆运动学 → 关节角度
            target_joints = self._inverse_kinematics(eef_pose)
            # 短时间步跟踪
            self._move_to_pose(target_joints, duration=0.033)  # ~30Hz
            # 更新夹爪
            gripper_state = twists[i, 6]  # 0=close, 1=open
            self.driver.set_servo(0 if gripper_state < 0.5 else 90)

    def _inverse_kinematics(self, pose_4x4):
        """
        Cyber Bricks 3-DOF 逆运动学
        2 个电机控制基座旋转+肘部俯仰，1 个舵机控制腕部
        （需根据实际机械结构建模）
        """
        # 提取位置和旋转
        pos = pose_4x4[:3, 3]
        # 简化为 3-DOF 解析 IK（需根据 Cyber Bricks 尺寸标定）
        # 返回 [motor1_angle, motor2_angle, servo_angle]
        ...

    def _move_to_pose(self, joint_angles, duration):
        """关节空间线性插值移动"""
        self.driver.set_motors(joint_angles[0], joint_angles[1], duration)
        if len(joint_angles) > 2:
            self.driver.set_servo(joint_angles[2])
```

### 3.6 演示数据录制格式

```python
# record_demo.py - 在 Jetson Nano 上运行
# 录制人类演示，输出 MT3 标准格式

import rospy
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
import numpy as np
from pathlib import Path
import json

DEMO_OUTPUT_DIR = Path("~/0-1-demos/")

class DemoRecorder:
    def __init__(self, task_name):
        self.bridge = CvBridge()
        self.rgb_images = []
        self.depth_images = []
        self.joint_states = []  # 关节角度（从 Cyber Bricks 读取）
        self.task_name = task_name

    def on_rgb(self, msg):
        self.rgb_images.append(self.bridge.imgmsg_to_cv2(msg))

    def on_depth(self, msg):
        self.depth_images.append(self.bridge.imgmsg_to_cv2(msg))

    def on_joint_state(self, msg):
        # 从 Cyber Bricks MQTT 读取关节角度
        self.joint_states.append({
            'motor1': msg.position[0],
            'motor2': msg.position[1],
            'servo': msg.position[2] if len(msg.position) > 2 else 0,
            'timestamp': rospy.get_time()
        })

    def save(self):
        """保存为 MT3 标准格式"""
        out_dir = DEMO_OUTPUT_DIR / self.task_name
        out_dir.mkdir(parents=True, exist_ok=True)

        # 取第一帧作为 workspace 图像（机械臂移出视野）
        rgb_ws = self.rgb_images[0]
        depth_ws = self.depth_images[0]

        # 计算分割掩码（手动标注或用 Grounding SAM）
        segmap = self._compute_segmap(rgb_ws)

        # 计算瓶颈姿态（对齐目标点）
        # 从关节角度序列中找到"夹爪接近物体的姿态"
        bn_idx = self._find_bottleneck_frame(self.joint_states)
        bn_pose = self._fk(self.joint_states[bn_idx])  # 正运动学

        # 计算末端执行器 twists（关节速度 → 末端速度）
        twists = self._compute_eef_twists(self.joint_states)

        # 保存文件
        self._save_image(rgb_ws, out_dir / 'head_camera_ws_rgb.png')
        self._save_image(depth_ws, out_dir / 'head_camera_ws_depth_to_rgb.png')
        np.save(out_dir / 'head_camera_ws_segmap.npy', segmap)
        np.save(out_dir / 'bottleneck_pose.npy', bn_pose)
        np.save(out_dir / 'demo_eef_twists.npy', twists)

        with open(out_dir / 'task_name.txt', 'w') as f:
            f.write(self.task_name)

        print(f"演示已保存到: {out_dir}")

    def _compute_segmap(self, rgb):
        # 使用 Grounding SAM 或手动标注
        # 返回布尔数组 (H, W)，True=物体，False=背景
        ...

    def _find_bottleneck_frame(self, joint_states):
        # 找到轨迹中夹爪最接近物体的帧
        # 启发式：关节速度变化的拐点
        ...

    def _fk(self, joint_state):
        # Cyber Bricks 3-DOF 正运动学
        # 输入：关节角度 → 输出：4×4 末端执行器姿态
        ...

    def _compute_eef_twists(self, joint_states):
        # 关节速度 → 末端执行器雅可比 → 末端 twist
        # 输出：(T, 7) 数组
        ...
```

---

## 四、风险点和替代方案

### 4.1 致命风险

#### 风险 1：Cyber Bricks 无法录制演示（关节角度反馈缺失）

**影响**：无法录制 MT3 格式的演示数据，整个方案不可行。

**缓解方案**：
- 方案 A：加装 **AS5600 磁性编码器**（I2C 接口）到电机轴，价格 ~$2/个
  ```
  ESP32-C3 I2C 总线 → AS5600 × 2（电机） + AS5600 × 1（舵机）
  ```
- 方案 B：购买 **带反馈的数码舵机**（如 LD-150MG，串口反馈角度）
- 方案 C：使用 **BC-BC** 方法替代纯检索式 MT3（见替代方案 1）

#### 风险 2：Cyber Bricks 3-DOF 无法完成 MT3 演示中的复杂操作

**影响**：MT3 演示数据来自 6-7 DOF WidowX 机械臂，3-DOF Cyber Bricks 自由度不足，无法复现大多数操作。

**缓解方案**：
- 仅选择适合 3-DOF 的任务（推物体、简单抓取）
- 或者：考虑 Cyber Bricks 的扩展性（可增加更多舵机）

### 4.2 重大风险

#### 风险 3：深度图缺失

**影响**：ESP32-Cam 无深度传感器，MT3 的 PointNet++ 点云配准需要深度图。

**缓解方案**：
- 使用 **MiDaS v3**（单目深度估计）在 Jetson Nano 上运行
- 或升级到 **RealSense D400 系列**（但增加成本和复杂度）

#### 风险 4：MT3 模型需要 GPU，Jetson Nano 性能不足

**影响**：PointNet++ 推理在 Jetson Nano 上可能 >3 秒/帧，无法实时。

**缓解方案**：
- 在 Ubuntu GPU（192.168.1.18）部署推理服务（推荐）
- 或使用模型剪枝（TensorRT INT8 量化）
- 或使用更轻量的替代方案（如 MT-ACT+ 的小模型版本）

### 4.3 替代方案

#### 替代方案 1：使用 BC-BC 或 Ret-BC（无需录制新演示）

如果无法录制 MT3 格式的演示，可以训练 BC 策略：

```
BC-BC: 训练 BC Alignment + BC Interaction 策略
     - 需要录制演示（但只需要关节角度+图像）
     - 训练一次，部署时无需演示库
     - 适合 Cyber Bricks 的固定任务集

Ret-BC: 检索式对齐 + BC 交互
     - Alignment 使用检索（不需要训练）
     - Interaction 使用 BC（需要训练）
     - 适合新任务但已有交互数据
```

#### 替代方案 2：使用 RT-1 / RT-2 等端到端 VLA 模型

| 模型 | 优点 | 缺点 |
|------|------|------|
| RT-1 | 端到端，视觉-动作映射 | 需要大规模预训练数据 |
| OpenVLA | 开源 VLN 模型 | 需要微调，计算量大 |
| π0（Physical Intelligence）| 通用机器人策略 | 闭源，未公开 |

这些方法不需要显式的轨迹分解，但需要大量机器人数据预训练。

#### 替代方案 3：基于 ROS 的标准轨迹录制

如果 Cyber Bricks 能改装为 ROS 控制的机械臂：
```bash
# 安装 ros2_cyberbricks 包
# 使用 joint_state_publisher 录制关节轨迹
ros2 topic record /joint_states -o demo.bag
# 使用 ros2 bag to Trajectory 转换为 MT3 格式
```

### 4.4 风险汇总

| 风险 | 概率 | 影响 | 优先级 |
|------|------|------|--------|
| 关节角度反馈缺失 | 高 | 致命 | P0 - 必须解决 |
| DOF 不足 | 高 | 重大 | P1 - 需选择适配任务 |
| 深度图缺失 | 中 | 重大 | P1 - 需加装深度估计 |
| GPU 性能不足 | 低 | 中等 | P2 - 可用 Ubuntu GPU |
| MT3 演示格式不兼容 | 中 | 中等 | P3 - 需格式转换 |

---

## 五、关键参考链接

### 5.1 MT3 核心资源

| 资源 | 链接 |
|------|------|
| 论文（Science Robotics）| https://www.science.org/doi/10.1126/scirobotics.adv7594 |
| ArXiv | https://arxiv.org/abs/2511.10110 |
| GitHub 仓库 | https://github.com/kamil-dreczkowski/learning_thousand_tasks |
| 项目主页 | https://www.robot-learning.uk/learning-1000-tasks |
| 演示视频 | https://www.robot-learning.uk/learning-1000-tasks（视频链接）|

### 5.2 依赖模型权重

| 模型 | 用途 | 下载位置 |
|------|------|----------|
| `geometry_encoder.ckpt` | PointNet++ 几何编码器 | 仓库 assets/ |
| `pose_estimator.ckpt` | 4-DOF 位姿回归器 | 仓库 assets/ |
| XMem.pth | 演示分割掩码跟踪 | Google Drive（见 README）|

### 5.3 Docker 环境

MT3 使用 Docker 容器（Ubuntu 22.04 + CUDA + PyTorch）：

```bash
# 构建镜像
make build

# 运行 MT3 推理示例
make deploy_mt3

# 调试 Shell
make debug
```

### 5.4 深度估计（补充）

| 方案 | 链接 | 说明 |
|------|------|------|
| MiDaS v3 | https://github.com/isl-org/MiDaS | Intel 单目深度估计，Jetson Nano 可跑 |
| Depth Anything v2 | https://github.com/DepthAnything/Depth-Anything-V2 | 更强的单目深度估计 |

### 5.5 Cyber Bricks 相关

| 资源 | 链接 | 说明 |
|------|------|------|
| ACBR 项目 | https://github.com/ACBR-robot/ACBR | Cyber Bricks 开源原始仓库 |
| 0-1 架构报告 | `research/0-1-system-abm-architecture-report.md` | System A/B/M 架构设计 |
| 0-1 Robot SOP | `harness/robot/ROBOT-SOP-v3.30-before-chapter-restructuring.md` | Cyber Bricks 控制接口 |

### 5.6 机械臂控制

| 资源 | 链接 | 说明 |
|------|------|------|
| WidowX 机械臂 | MT3 训练用机械臂 | 6-DOF，ROS 控制 |
| MoveIt! | https://moveit.ros.org/ | 机械臂运动规划 |
| robodk | https://robodk.com/ | 离线编程和仿真 |

---

## 六、结论与建议

### 6.1 可行性评估

| 维度 | 评分 | 说明 |
|------|------|------|
| 技术可行性 | 6/10 | 核心算法可行，但 Cyber Bricks 硬件需要改造 |
| 工程复杂度 | 7/10 | 需要：深度估计 + IK + MQTT 驱动 + 格式转换 |
| 数据可行性 | 4/10 | 演示录制需要关节反馈，当前缺失 |
| 资源需求 | 5/10 | 需要 Ubuntu GPU；Cyber Bricks 改造费用低 |

### 6.2 推荐路径

**Phase 0：硬件改造（必须先做）**
1. 为两个电机加装 **AS5600 磁性编码器**（I2C，~6 DOF）
2. 为舵机添加 **角度反馈**（ADC 分压或串口舵机）
3. 修改 ESP32-C3 固件，支持 `current_angle` MQTT 发布
4. 预算：~$20

**Phase 1：深度感知（优先）**
1. 在 Jetson Nano 上部署 **MiDaS v3**（单目深度估计）
2. 测试深度估计精度是否满足 ICP 配准需求
3. 如精度不足，采购 **RealSense D415**（~$120）

**Phase 2：演示录制**
1. 实现 `/joint_states` → MT3 格式转换
2. 使用 Grounding SAM 进行初始分割标注
3. 录制 5-10 个 Cyber Bricks 可执行的简单任务演示
4. 计算 bottleneck_pose 和 eef_twists

**Phase 3：MT3 推理部署**
1. 在 Ubuntu GPU（192.168.1.18）部署 MT3 Docker 容器
2. 实现 Jetson Nano → Ubuntu GPU 的 gRPC 客户端
3. 实现 Ubuntu GPU → Jetson Nano 的结果回传

**Phase 4：控制执行**
1. 实现 Cyber Bricks 3-DOF 逆运动学
2. 将 MT3 输出（末端姿态/twists）映射到关节角度
3. 实现轨迹跟踪（位置控制模式下）

### 6.3 关键提醒

> ⚠️ **MT3 的核心优势是"无需每个任务训练"，但这建立在有足够多高质量演示库的基础上。**
>
> 如果 0-1 机器人只做少量固定任务，**BC-BC 或 Ret-BC** 可能比 MT3 更实用（可做失败恢复）。
>
> Cyber Bricks 3-DOF 的限制使得大多数 MT3 演示数据（WidowX 录制）无法直接使用，**需要重新录制适配 3-DOF 的演示**。

---

*调研完成时间：2026-03-31 09:30 GMT+8*
*数据来源：GitHub MT3 仓库（完整代码+README）、Science Robotics 论文摘要、项目主页、0-1 workspace 文件*
