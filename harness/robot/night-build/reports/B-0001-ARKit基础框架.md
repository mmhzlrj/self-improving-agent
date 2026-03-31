# B-0001-ARKit基础框架调研

> **任务**：调研ARKit能为iPhone感知前端提供什么能力  
> **输出路径**：`night-build/reports/B-0001-ARKit基础框架.md`  
> **调研日期**：2026-03-31

---

## 一、概述

ARKit 是 Apple 提供的增强现实（AR）框架，最新版本为 **ARKit 6**（iOS 16 / iPadOS 16），在 iOS 17/18 中继续演进。ARKit 提供了一套完整的感知能力，覆盖空间理解、深度 sensing、人体追踪、面部追踪和图像识别，适用于 iPhone 感知前端的各种数据采集场景。

---

## 二、ARKit 核心能力详解

### 2.1 深度数据（LiDAR / Depth API）

#### 硬件依赖
| 设备 | 深度传感器 |
|------|-----------|
| iPhone 12 Pro/Pro Max，iPhone 13 Pro/Pro Max，iPhone 14 Pro/Pro Max，iPhone 15 Pro/Pro Max，iPhone 16 Pro/Pro Max | LiDAR Scanner（dToF） |
| 其他 iPhone（无 LiDAR） | 深度估算（Neural Engine 加速，基于双摄/单图） |

#### 能力说明
- **LiDAR Scanner**：直接测量每个像素到表面的距离，生成高分辨率深度图
- **Scene Depth API**：在 `ARFrame` 中提供实时深度数据，包含：
  - `depthMap`（Float32，深度值，单位米）
  - `confidenceMap`（每个像素的深度置信度）
  - 相机内参矩阵（intrinsics，用于坐标投影）
- **4x 上采样**：ARKit 将 LiDAR 原始深度图上采样到与相机图像相同的分辨率
- **最大范围**：5 米（室内测试）
- **精度**：误差约 1-3%（可达亚厘米级，取决于距离和表面材质）

#### 深度数据格式
```
ARFrame.sceneDepth → ARDepthData
  ├── depthMap: CVPixelBuffer (Float32, 1 channel)
  ├── confidenceMap: CVPixelBuffer (UInt8, 1 channel)
  └── cameraIntrinsics: simd_float3x3 (fx, fy, cx, cy)
```

#### 典型应用场景
- 3D 重建 / 点云生成
- 人物遮挡（People Occlusion）
- 精确测量
- 表面检测（平面、边缘、几何体）

> **示例**：`ARFrame.sceneDepth?.depthMap` → Metal Texture → Point Cloud

---

### 2.2 空间定位（World Tracking）

#### 能力说明
- 使用视觉惯性里程计（Visual-Inertial Odometry，VIO），融合相机和 IMU 数据
- 实时追踪设备在 3D 空间中的 **6DoF**（6自由度）姿态：
  - Position：`x, y, z`（单位：米，相对于初始位置）
  - Orientation：`pitch, roll, yaw`（四元数）
- **平面检测**：自动检测水平和垂直平面（桌子、墙壁）
- **特征点**：提取环境特征点构建稀疏点云（用于重定位）
- **场景理解**：ARGeoTracking（ARKit 5+，基于地理坐标）

#### 数据接口
```swift
ARSession.shared.currentFrame
  ├── camera.transform: simd_float4x4   // 设备6DoF姿态（世界坐标系）
  ├── worldMappingStatus: ARFrame.WorldMappingStatus
  ├── anchors: [ARAnchor]                // 平面锚点、特征点锚点等
  └── lightEstimate: ARLightEstimate    // 环境光照估计
```

#### 追踪质量（worldMappingStatus）
| 状态 | 含义 |
|------|------|
| `notAvailable` | 初始阶段，地图不足 |
| `limited` | 特征不足（低光、快速运动） |
| `extending` | 正在扩展地图 |
| `mapped` | 地图充分，可进行 relocalization |

#### 精度
- 定位精度：亚厘米级（在光照良好、有纹理的环境）
- 漂移：长时间运行后有少量累积漂移，需闭环检测修正

---

### 2.3 人体姿态检测（Body Tracking / Motion Capture）

#### 能力说明
- 使用 **Person Segmentation** + **Body Tracking** 技术
- 支持 **3D 全身骨骼追踪**（87个关节点，ARKit 5+）
- 在后置相机画面中追踪人物，可将动作重定向到虚拟角色
- **LiDAR 设备额外能力**：在 iPad Pro（LiDAR）等设备上，即使人物部分被遮挡也能追踪

#### 骨骼数据格式
```swift
ARBodyAnchor（ARKit 3+）
  ├── skeleton: ARSkeleton
  │     ├── joints: [ARSkeleton.JointName]  // 87个关节点
  │     └── jointModelTransforms: [simd_float4x4]  // 每帧每关节点4x4矩阵
  ├── rootTransform: simd_float4x4           // 人体根节点世界坐标
  └── isTracked: Bool
```

#### 3D 关节点列表（部分）
```
root → hips → spine1/2/3 → head
                      → chest → left/rightShoulder → left/rightArm → ...
       → left/rightUpLeg → left/rightLeg → left/rightFoot
```

#### 典型输出帧率
- **30 FPS**（iPhone/iPad，Body Tracking 模式）
- 延迟约 33ms

#### 特殊模式
- **People Occlusion**：无需 LiDAR，基于 Neural Engine 的人物前景/背景分割
- **Motion Capture**：使用 `.motionCapture` configuration，输出 USD 骨骼动画

---

### 2.4 面部追踪（Face Tracking）

#### 能力说明
- 使用前置 TrueDepth 摄像头（红外点阵投影 + 泛光照明）
- 追踪面部表情、注视方向、嘴唇动作
- ARKit 4 扩展到所有带 A12 Bionic + 前置相机的设备
- ARKit 6 同时支持前后相机（iPhone 12+）使用 face + world tracking

#### 面部数据格式
```swift
ARFaceAnchor
  ├── geometry: ARFaceGeometry        // 面部Mesh（1220个顶点）
  ├── blendShapes: [ARFaceAnchor.BlendShapeLocation: NSNumber]
  │     ├── eyeLookIn/Out, browDown, jawOpen, mouthSmile ...
  │     └── 52种表情系数
  ├── lookAtPoint: simd_float3         // 注视点（世界坐标）
  └── transform: simd_float4x4         // 面部6DoF姿态
```

#### 52种表情系数（BlendShapes）
| 类别 | 包含 |
|------|------|
| 眼部 | eyeBlinkLeft/Right, eyeLookDown/Left/Right/Up |
| 眉毛 | browDown/Up, browInner/OuterUp |
| 嘴部 | jawOpen, mouthClose, mouthFunnel/Pucker/Smile/Left/Right |
| 语音 | tongueOut, jawLeft/Right |
| 头部 | headYaw/Pitch/Roll |

#### 前置相机规格
- 深度精度：亚毫米级（红外结构光）
- 输出帧率：60 FPS
- 需要 A12 Bionic 或更新芯片

---

### 2.5 图像识别（Image Tracking）

#### 能力说明
- 检测并追踪已知 2D 图像（参考图像）
- 支持移动中图像追踪（从动图）
- 检测多个图像（最多 4 个同时追踪）
- **物体识别**（Object Tracking，ARKit 5+）：识别已知 3D 物体

#### 数据格式
```swift
ARImageAnchor
  ├── referenceImageName: String
  ├── transform: simd_float4x4         // 图像的6DoF姿态
  ├── isTracked: Bool
  └── center: CGPoint                  // 图像中心像素位置
```

#### 参考图像配置
```
ARReferenceImageSet（在 Assets.xcassets 中管理）
  支持格式：PNG, JPEG
  建议分辨率：300x300 px 以上
  物理尺寸：可设置（用于尺度估计）
```

---

## 三、iPhone 16 Pro ARKit 能力对比

| 能力 | iPhone 16 Pro | 说明 |
|------|--------------|------|
| **芯片** | A18 Pro | Neural Engine 16核，ML 性能大幅提升 |
| **LiDAR** | ✅ 有 | 覆盖 iPhone 16 Pro/Pro Max |
| **深度数据（Scene Depth）** | ✅ 完整 | 分辨率同相机图像，Float32 深度图 |
| **World Tracking** | ✅ 完整 | 6DoF + 平面检测 + 特征点 |
| **Body Tracking** | ✅ 完整 | 87关节点 3D 骨骼，30 FPS |
| **Face Tracking** | ✅ 完整 | TrueDepth，52 BlendShapes，60 FPS |
| **People Occlusion** | ✅ | Neural Engine 加速，无需 LiDAR |
| **Room Tracking** | ✅（ARKit 6+） | 房间级几何重建 |
| **Object Capture** | ✅ | 3D 物体扫描（Photogrammetry） |
| **Video** | 4K 120fps | Dolby Vision，ProRes 外录 |

### iPhone 16 Pro 深度传感器规格
| 参数 | 规格 |
|------|------|
| 类型 | dToF（Direct Time-of-Flight）LiDAR |
| 激光波长 | 940nm（不可见红外） |
| 最大范围 | ~5 米 |
| 精度 | 1-3% 误差（约 1cm 级别） |
| 深度图分辨率 | 上采样后同相机（~1920x1440 或更高） |
| 帧率 | 60 Hz（LiDAR 深度帧） |
| 视场角（FOV） | ~60°（与超广角相机对齐） |

---

## 四、数据格式汇总与接口建议

### 4.1 核心数据结构

#### ARFrame（每帧数据入口）
```swift
// 所有数据通过 ARSession 的 ARSessionDelegate 回调获取
func session(_ session: ARSession, didUpdate frame: ARFrame) {
    // 1. 设备姿态
    let transform: simd_float4x4 = frame.camera.transform

    // 2. 深度数据（需要 LiDAR）
    if let depth = frame.sceneDepth {
        let depthMap = depth.depthMap          // CVPixelBuffer<Float32>
        let confidenceMap = depth.confidenceMap // CVPixelBuffer<UInt8>
        let intrinsics = depth.cameraIntrinsics // simd_float3x3
    }

    // 3. 人体追踪
    for anchor in frame.anchors {
        if let body = anchor as? ARBodyAnchor {
            let joints = body.skeleton.jointModelTransforms
            let rootPos = body.rootTransform
        }
    }

    // 4. 面部追踪
    for anchor in frame.anchors {
        if let face = anchor as? ARFaceAnchor {
            let blendShapes = face.blendShapes
            let lookAt = face.lookAtPoint
        }
    }
}
```

#### 深度数据 → 点云转换公式
```python
# Python 等效伪代码（用于理解投影关系）
for y in range(height):
    for x in range(width):
        z = depth_map[y, x]          # 米
        fx, fy = intrinsics[0,0], intrinsics[1,1]
        cx, cy = intrinsics[0,2], intrinsics[1,2]
        X = (x - cx) * z / fx
        Y = (y - cy) * z / fy
        Z = z
        # 再乘以相机外参（transform 的逆）转到世界坐标系
```

### 4.2 跨进程数据传输建议

由于 ARKit 数据（ARFrame）只能在本进程访问，建议：

#### 方案 A：本地 Socket / Unix Domain Socket
```
iOS App (ARKit) → Unix Socket → Robot Controller Process
帧率：30-60 FPS
延迟：< 5ms（本地）
数据量：深度图 ~10MB/帧，需压缩（如 JPEG+Depth 打包）
```

#### 方案 B：WebRTC / HTTP Streaming
- 适合远距离传输场景
- 建议使用 WebRTC 的 DataChannel 传输二进制数据
- 压缩比：H.265 视频流 + JSON 元数据

#### 方案 C：文件轮转（开发/Debug）
```
/tmp/arkit/
  ├── depth/
  │     └── frame_{timestamp}.raw      # Float32 原始深度
  ├── pose/
  │     └── frame_{timestamp}.json     # transform 矩阵 + 时间戳
  └── body/
        └── frame_{timestamp}.json     # 骨骼数据
```

### 4.3 推荐数据格式

| 数据类型 | 推荐格式 | 说明 |
|---------|---------|------|
| 深度图 | **Float32 TIFF** 或 **EXR** | 保持精度，文件轮转时使用 |
| 实时流 | **Raw Float32** + zlib 压缩 | 通过 socket 发送 |
| 设备姿态 | **JSON** (`simd_float4x4` → 16元素数组) | 易于调试和解析 |
| 人体骨骼 | **JSON** 或 **protobuf** | 87关节 × 16 float = 1392 bytes/帧 |
| 面部表情 | **JSON** (BlendShape 字典) | 52系数 + lookAtPoint |
| 视频流 | **H.265/HEVC** | ARKit 支持 Metal 录制到 ProRes/H.265 |

### 4.4 接口设计建议（Swift 伪代码）

```swift
// ARKit 数据采集服务接口
protocol ARKitDataSource {
    // 深度数据回调（每帧）
    func onDepthFrame(_ frame: DepthFrame)

    // 人体姿态回调
    func onBodyFrame(_ body: BodyFrame)

    // 面部表情回调
    func onFaceFrame(_ face: FaceFrame)

    // 设备状态
    func onTrackingStateChanged(_ state: TrackingState)
}

// 数据帧结构（建议）
struct DepthFrame {
    let timestamp: TimeInterval
    let depthMap: Data           // Float32 压缩数据
    let confidenceMap: Data       // UInt8
    let cameraIntrinsics: [Float] // 9元素
    let cameraTransform: [Float]  // 16元素（simd_float4x4）
    let width: Int
    let height: Int
}

struct BodyFrame {
    let timestamp: TimeInterval
    let rootTransform: [Float]     // 16元素
    let joints: [[Float]]          // [87][16] 每关节点 4x4 矩阵
    let isTracked: Bool
}

struct FaceFrame {
    let timestamp: TimeInterval
    let blendShapes: [String: Float]  // 52个表情系数
    let lookAtPoint: [Float]          // 3元素
    let transform: [Float]             // 16元素
}
```

---

## 五、总结与建议

### iPhone 感知前端 ARKit 能力地图

```
iPhone 16 Pro (A18 Pro + LiDAR)
├── 深度感知 ──────── Scene Depth API (Float32, ~5m, 1-3% 误差)
├── 空间定位 ──────── World Tracking 6DoF + 平面检测
├── 人体姿态 ──────── Body Tracking (87关节点, 30 FPS)
├── 面部表情 ──────── Face Tracking (52 BlendShapes, 60 FPS)
└── 图像识别 ──────── Image/Object Tracking
```

### 感知前端选型建议

| 需求 | 推荐 ARKit 能力 |
|------|--------------|
| 室内SLAM/导航 | World Tracking + Scene Depth |
| 人体动作捕捉 | Body Tracking（后置） |
| 面部表情/视线 | Face Tracking（前置 TrueDepth） |
| 3D 重建 | Scene Depth → Point Cloud |
| 人物交互感知 | People Occlusion + Body Tracking |
| 物体识别/抓取 | Object Tracking + Scene Depth |

### 数据输出建议

1. **深度数据**：通过 Unix Socket 实时推送压缩 Float32 深度帧（zlib），避免大文件 IO
2. **姿态/骨骼**：JSON over Socket，30-60 Hz
3. **视频流**：独立 H.265 编码通道，ARKit 不直接输出 RGB + Depth 同步流，需双缓冲
4. **开发/Debug**：文件轮转格式（/tmp/arkit/），生产环境切 Socket

---

## 参考资料

- [ARKit | Apple Developer](https://developer.apple.com/documentation/ARKit)
- [ARKit 6 - Augmented Reality](https://developer.apple.com/augmented-reality/arkit/)
- [Understanding World Tracking | Apple Developer](https://developer.apple.com/documentation/arkit/understanding-world-tracking)
- [Capturing Body Motion in 3D | Apple Developer](https://developer.apple.com/documentation/ARKit/capturing-body-motion-in-3d)
- [Displaying a Point Cloud Using Scene Depth | Apple Developer](https://developer.apple.com/documentation/ARKit/displaying-a-point-cloud-using-scene-depth)
- [Tracking and Visualizing Faces | Apple Developer](https://developer.apple.com/documentation/ARKit/tracking-and-visualizing-faces)
- [Apple ARKit: Cheat Sheet - TechRepublic](https://www.techrepublic.com/article/apples-arkit-everything-the-pros-need-to-know/)
- [iPhone 16 Pro LiDAR Specs - Aerial Precision](https://www.aerial-precision.com/blogs/blog/lidar-on-iphones-is-it-worth-it)
- [Indoor Mapping Accuracy - Taylor & Francis](https://www.tandfonline.com/doi/full/10.1080/16874048.2024.2408839)
- [WWDC24: Create enhanced spatial computing experiences with ARKit](https://developer.apple.com/videos/play/wwdc2024/10100/)

---

*报告生成：Subagent B-0001 | 2026-03-31*
