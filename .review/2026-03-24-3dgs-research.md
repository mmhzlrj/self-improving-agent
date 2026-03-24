# 3D Gaussian Splatting（3DGS）调研报告 — 0-1 应用价值分析

**调研时间**：2026-03-24
**关键词**：3DGS / 3D Gaussian Splatting / 空间智能 / 具身机器人

---

## 一、什么是 3D Gaussian Splatting

### 核心原理

3DGS = 用**数百万个 3D 高斯椭球**来表示三维空间，每个高斯包含：
- **位置**（均值坐标）
- **协方差矩阵**（形状和朝向）
- **RGB 颜色**
- **不透明度**

通过**可微分 tile 光栅化**渲染，比 NeRF 快 100 倍以上。

### 关键性能指标

| 指标 | NeRF | 3DGS |
|------|------|------|
| 训练时间 | 数小时~数天 | **35-45 分钟** |
| 1080p 渲染速度 | ~10 FPS | **100+ FPS** |
| 场景表示 | 隐式（神经网络）| **显式（高斯点云）** |
| 编辑/控制 | 困难 | **容易**（可编辑单个高斯）|

---

## 二、3DGS vs 0-1 当前方案对比

### 0-1 当前方案（基于 ROBOT-SOP）

| 方案 | 技术 | 特点 |
|------|------|------|
| **RGB-D 建图** | ESP32-Cam + iPhone LiDAR | 单图像 / 深度图输入 |
| **SLAM** | YOLO + MediaPipe | 稀疏语义建图 |
| **3D 感知** | PointWorld（李飞飞 World Labs）| 单 RGB-D → 模拟 10 步关节动作 |
| **仿真训练** | Genesis v0.4.0 | 物理引擎，GTX 1080 6GB 可跑 |

**当前痛点**：
- PointWorld 是预训练模型，无法对真实家庭做实时 3D 重建
- Genesis 是纯物理仿真，缺乏真实感纹理
- 无法在机器人进入新环境时，快速建立真实感 3D 地图

---

## 三、3DGS 在机器人领域的主要应用方向

### 1. 实时高保真 3D 建图（SLAM）

**核心价值**：机器人进入陌生环境时，用手机绕一圈拍摄，即可在 **10-30 分钟内**重建高保真 3D 场景（包含纹理）。

**关键项目**：

| 项目 | 论文 | 算力需求 | 特点 |
|------|------|---------|------|
| **MonoGS** | CVPR 2024 | RTX 3060+ | 首个单目 3DGS SLAM，帝国理工 |
| **SplaTAM** | CVPR 2024 | 高端 GPU（如 RTX 4090）| RGB-D SLAM，CVPR Best Demo Award |
| **RTGS** | ACM 2024 | Jetson Orin NX（边缘）| 实时 3DGS SLAM，150+ FPS |

**对 0-1 的价值**：
```
传统方案：激光雷达建图 → 精度高但成本高（¥3000+）
3DGS 方案：手机绕一圈 → 精度接近激光雷达 + 带纹理 + ¥0硬件成本
```

**限制**：3DGS SLAM 目前在嵌入式端（Jetson Nano/Orin NX）仍然慢（SplaTAM 在边缘设备上约 0.78 FPS），实时性不如传统 SLAM。

---

### 2. 语义建图 + 自然语言查询（LangSplat）⭐⭐⭐⭐

**GitHub**：https://github.com/minghanqin/LangSplat
**论文**：CVPR 2024 Highlight

**能力**：
- 将 **CLIP 视觉语言特征**注入 3DGS 高斯
- 实现**开放词汇语义查询**："找到红色杯子" / "桌上的物体"

```
传统方案：需要先训练特定类别检测器，再逐类别识别
LangSplat：直接用自然语言查询任意物体，无需预定义类别
```

**对 0-1 的价值**：
- 机器人进入新家庭 → 用手机扫描 → 自然语言问"厨房在哪里？"
- 0-1 目标用户（安装工/业主）可以自然对话指挥机器人

---

### 3. Real2Sim 仿真训练（RoboGSim）⭐⭐⭐⭐⭐

**论文**：arXiv:2411.11839（2024-11，2025-08 更新 v2）
**官网**：https://robogsim.github.io/

**核心 Pipeline**：

```
① Gaussian Reconstructor（3DGS 重建）
   手机拍摄机器人工作区 → 3DGS 高保真重建

② Digital Twins Builder（数字孪生）
   将真实环境转为可编辑的数字孪生

③ Scene Composer（场景编辑器）
   添加/删除/移动物体，修改光照

④ Interactive Engine（交互引擎）
   在仿真中训练机器人策略
```

**关键结果**：
- 在 RoboGSim 仿真数据上训练的模型 → **零样本泛化到真实机器人**
- 新视角和新场景下，仿真数据训练的模型**优于真实数据训练的模型**
- 解决了真实机器人数据采集成本高、场景单一的问题

**对 0-1 的价值**（极高）：
```
0-1 当前问题：
  Cyber Bricks 动作数据靠人工采集，成本高

RoboGSim 方案：
  在新场景用手机拍摄 → 3DGS 重建 → 仿真中批量生成合成数据
  → 训练机器人学会新任务 → sim-to-real 迁移到真实机器人
```

---

### 4. 物理仿真 + 精细操作（Physical AI）

**核心价值**：3DGS 高斯可**绑定物理引擎参数**（摩擦力、形变阈值），实现高精度物理仿真：

| 应用 | 说明 | 精度 |
|------|------|------|
| 机械臂抓取 | 仿真 → 优化抓取姿态 | — |
| 软体操作 | 绳索/布料/柔性物体仿真 | — |
| 手术机器人 | 高斯泼溅推演血管穿刺路径 | **0.1mm** |
| 足式机器人 | 步态优化仿真 | — |

**对 0-1 的价值**：
- Cyber Bricks 机械臂精度一般 → 在仿真中优化路径 → 实际执行更精准
- 软体操作（收拾衣物、整理桌面）：物理仿真 + 3DGS 可实现

---

### 5. 单图像 → 可交互 3D 场景（PointWorld）

**论文**：World Labs，李飞飞团队
**定位**：给定 1-3 张 RGB-D 图片 + 机器人动作序列 → 预测 3D 空间中的物体运动结果

**对 0-1 的已有价值**（已在 ROBOT-SOP v3.4 §1.2 记录）：
- 单 RGB-D → 模拟 10 步关节动作
- 无需预训练即可操作新物体

**3DGS vs PointWorld**：
- PointWorld：预测物体运动（基于 diffusion）
- 3DGS：重建真实场景（基于高斯渲染）
- 两者**互补**，可结合使用

---

## 四、关键开源项目

| 项目 | 链接 | 算力需求 | 对 0-1 价值 |
|------|------|---------|-------------|
| **LangSplat**（CVPR 2024）| https://github.com/minghanqin/LangSplat | RTX 3060+ | ⭐⭐⭐⭐⭐ 语义建图 |
| **RoboGSim** | https://robogsim.github.io/ | RTX 4090（训练）| ⭐⭐⭐⭐⭐ Real2Sim 仿真 |
| **MonoGS**（CVPR 2024）| https://github.com/muskie82/MonoGS | RTX 3060+ | ⭐⭐⭐ 单目 SLAM |
| **SplaTAM**（CVPR 2024）| https://github.com/spla-tam/SplaTAM | RTX 4090 | ⭐⭐⭐ RGB-D SLAM |
| **OpenSplat** | —（C++ 实现）| CPU + AMD GPU | ⭐⭐⭐⭐ 嵌入式方向 |
| **Gaussian-Splatting**（原始）| https://github.com/graphdeco-inria/gaussian-splatting | RTX 3060+ | ⭐⭐⭐ 基础框架 |
| **Genesis**（已记录）| https://github.com/applecartn/genesis | GTX 1080 6GB | ⭐⭐⭐⭐⭐ 物理引擎 |

---

## 五、对 0-1 的具体应用场景

### 场景 1：机器人进入新家庭（立即可用）

```
Step 1：业主用手机 App 绕家里走一圈（2-3 分钟）
Step 2：3DGS 重建（10-30 分钟，在 RTX 3060/台式机上跑）
Step 3：生成带纹理的家庭 3D 地图
Step 4：0-1 机器人基于 3D 地图自主导航
```

**优势**：比激光雷达建图便宜 + 带纹理 + 人类可读

---

### 场景 2：自然语言指令（中期可用）

```
用户："去沙发旁边那个小边几上拿我的药"
↓
LangSplat 查询："沙发" + "边几" + "药" → 3D 坐标
↓
0-1 导航到该位置 → 抓取
```

**关键**：不需要预先知道"药"在哪里，直接语言查询。

---

### 场景 3：仿真中批量训练新技能（最有价值）

```
① 用手机拍摄"整理桌面"任务场景
② RoboGSim 3DGS 重建 → 数字孪生
③ 在仿真中批量生成 1000+ 条合成数据
④ 训练机械臂"整理桌面"策略
⑤ sim-to-real 迁移到 Cyber Bricks
```

**解决 0-1 最大痛点**：数据不足。Cyber Bricks 目前靠人工遥操作采集数据，成本高、场景少。3DGS + 仿真可将数据量扩大 1000 倍。

---

### 场景 4：精细操作路径优化

```
① 3DGS 扫描任务场景
② 在仿真中测试 100 种抓取路径
③ 选择最优路径下发到 Cyber Bricks 执行
```

---

## 六、硬件算力需求（对 0-1 的门槛）

| 任务 | 算力需求 | 0-1 当前硬件 | 可行性 |
|------|---------|-------------|--------|
| **3DGS 场景重建**（训练）| RTX 3060+（训练 30 分钟）| 台式机 RTX 2060 ✅ | ✅ 完全可以 |
| **LangSplat 语义查询** | RTX 3060+ | 台式机 RTX 2060 ✅ | ✅ 可行 |
| **RoboGSim 仿真训练** | RTX 4090（最佳）| RTX 2060 ⚠️ | ⚠️ 可行但慢 |
| **3DGS 实时 SLAM** | Jetson Orin NX+ | Jetson Nano 2GB ❌ | ❌ 算力不足 |
| **OpenSplat（C++）** | CPU + AMD | Jetson Nano 2GB ⚠️ | ⚠️ 理论上可行，需优化 |

**结论**：
- **场景重建**（离线）：0-1 台式机（RTX 2060）完全可以
- **实时 SLAM**：需要 Jetson AGX Thor 级别，Nano 2GB 不够
- **仿真训练**：建议在台式机上做，迁移到机器人执行

---

## 七、3DGS vs PointWorld vs Genesis：角色分工

| 技术 | 角色 | 输入 | 输出 |
|------|------|------|------|
| **3DGS** | 场景重建（真实纹理）| 手机绕拍视频 | 高保真 3D 点云 |
| **PointWorld** | 物理预测（物体运动）| RGB-D + 动作序列 | 动作效果预测 |
| **Genesis** | 物理引擎（无纹理仿真）| 物理参数 | 碰撞/动力学结果 |

**三者关系**：
```
PointWorld（预测）+ Genesis（物理）→ 机器人动作规划
3DGS（重建）→ 真实环境数字孪生
PointWorld + 3DGS → 在真实场景中做动作预测
```

---

## 八、总结建议

### 0-1 最值得关注的 3 个 3DGS 应用

| 优先级 | 应用 | 为什么 |
|--------|------|--------|
| 🔴 高 | **RoboGSim 仿真训练** | 解决 0-1 数据不足的最大痛点 |
| 🔴 高 | **LangSplat 语义建图** | 自然语言指挥机器人，无需预定义类别 |
| 🟡 中 | **3DGS 场景重建** | 新家庭快速建图，替代激光雷达 |

### 对 ROBOT-SOP 的补充建议

建议在 §1.2 空间智能章节或 §6.5 技能训练章节增加：

> **3DGS + LangSplat + RoboGSim** 技术栈：
> - LangSplat：自然语言语义建图（手机拍摄 → 自然语言查询物体位置）
> - RoboGSim：Real2Sim2Real 仿真训练（合成数据 → sim-to-real）
> - 3DGS：基础场景重建（高保真纹理数字孪生）
> - Genesis：物理引擎（无纹理物理仿真）

### 实施路径建议

| 时间 | 行动 | 依赖 |
|------|------|------|
| **现在** | 台式机 RTX 2060 上跑 LangSplat Demo | GitHub 开源项目 |
| **阶段一** | 手机 App 集成 3DGS 场景重建（离线） | OpenSplat（C++ 嵌入式）|
| **阶段二** | LangSplat 自然语言查询接入 | CLIP + 3DGS 集成 |
| **阶段三** | RoboGSim 仿真数据生成 | 需要 RTX 4090 算力 |
| **远期** | 3DGS 实时 SLAM | 需要 Jetson AGX Thor+ |

---

## 九、关键链接

| 资源 | 链接 |
|------|------|
| LangSplat GitHub | https://github.com/minghanqin/LangSplat |
| RoboGSim 官网 | https://robogsim.github.io/ |
| RoboGSim arXiv | https://arxiv.org/abs/2411.11839 |
| MonoGS GitHub | https://github.com/muskie82/MonoGS |
| SplaTAM GitHub | https://github.com/spla-tam/SplaTAM |
| 3DGS 原始论文 | https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting |
| PointWorld 论文 | https://arxiv.org/abs/2601.03782 |
| Genesis 物理引擎 | https://github.com/applecartn/genesis |
