# F-002: 补全 5 个模块文档内容

## 问题描述
`docs/modules/` 下 7 个模块文档中，arm.md(24行)、vision.md(15行)、face.md(8行)、locomotion.md(8行)、suction.md(8行) 内容极度空壳，只有标题和 2-3 行占位。

只有 lewm.md(62行) 和 gui-geng.md(50行) 内容较完整。

## 文件
- `/Users/lr/.openclaw/workspace/docs/modules/arm.md`
- `/Users/lr/.openclaw/workspace/docs/modules/vision.md`
- `/Users/lr/.openclaw/workspace/docs/modules/face.md`
- `/Users/lr/.openclaw/workspace/docs/modules/locomotion.md`
- `/Users/lr/.openclaw/workspace/docs/modules/suction.md`

## 参考数据源
- `/Users/lr/.openclaw/workspace/harness/robot/ROBOT-SOP.md` — 从这个文件提取各模块的详细信息
- `/Users/lr/.openclaw/workspace/docs/modules/lewm.md` — 参考这个文件的格式和详细程度

## 每个模块文档必须包含的章节（参考 lewm.md 格式）

每个模块文档应该至少 40-60 行，包含：

```markdown
# [模块中文名]

> 一句话描述（硬件+功能）

## 概述
模块的定位和作用，2-3 句话

## 硬件参数
- 关键硬件规格列表
- 接口/通信方式
- 性能指标

## 技术方案
具体的技术实现方案，包括：
- 架构设计
- 通信协议
- 软件栈

## 当前状态
- 已完成的工作
- 待完成的工作
- 当前阶段

## 问题记录
- 踩过的坑
- 解决方案
- 注意事项

## 参考链接
- 相关文档/SOP 章节号
- 外部参考资料
```

## 具体操作步骤

### Step 1: 读取参考文件
```bash
cat /Users/lr/.openclaw/workspace/docs/modules/lewm.md
```
用这个文件作为格式标杆。

### Step 2: 从 ROBOT-SOP.md 提取各模块信息
读取 ROBOT-SOP.md，找到以下关键词对应的章节，提取关键信息：
- **arm.md**：搜索 "Cyber Bricks"、"机械臂"、"MQTT"、"舵机"、"Phase 4"
- **vision.md**：搜索 "ESP32-Cam"、"视觉"、"YOLO"、"MediaPipe"、"Phase 2"、"RTSP"
- **face.md**：搜索 "面部表情"、"Phase 5"、"0-1 三元素"、"OLED"、"H2C"
- **locomotion.md**：搜索 "移动"、"底盘"、"ROS 2"、"Phase 6"、"差速"、"LiDAR"
- **suction.md**：搜索 "吸盘"、"气泵"、"抓手"、"gripper"

### Step 3: 逐个重写模块文档
对每个文件执行：
1. 先 `cat` 查看当前内容
2. 用提取的 ROBOT-SOP.md 信息重写，确保 40-60 行
3. 保存后 `wc -l` 验证行数 ≥ 40

### 各模块要点（从 ROBOT-SOP.md 提取）

**arm.md（机械臂模块）要点：**
- Cyber Bricks ESP32-C3（XA003/XA004/XA005）+ 电机 + 舵机
- 4 DOF 自由度
- MicroPython 固件
- MQTT 指令控制（OpenClaw → Cyber Bricks）
- Phase 4 任务
- 星闪 H3863 通信层方案（方案二）
- 舵机抖转：信号干扰 → 加屏蔽

**vision.md（视觉识别）要点：**
- ESP32-Cam OV2640 摄像头
- Jetson Nano 2GB + YOLO + TensorRT FP16
- MediaPipe on Jetson Nano 2GB
- YOLO + MediaPipe 共存方案
- RTSP 推流
- 花屏：供电不足 → 5V/2A 电源
- IP 变更：设为静态 IP
- Phase 2 任务
- RynnBrain（阶段二接入）
- UART 通信（Jetson Nano ↔ ESP32-Cam）

**face.md（面部模块）要点：**
- 0-1 三元素：「0」主眼睛、「-」间隔/嘴巴、「1」辅助信息
- LED 点阵/IPS 屏幕显示
- MQTT 表情指令控制
- H2C 3D 打印面部支架
- Phase 5 任务
- 0-1 面部表情控制代码示例

**locomotion.md（移动模块）要点：**
- 四轮底盘 + 差速控制
- ROS 2 导航栈（或替代框架）
- Jetson Nano 2GB 完整 ROS 2 方案
- ESP32-CAM micro-ROS 接入
- LiDAR 导航方案
- Phase 6 任务
- Medusa Halo 移动 AI 工作站（长期规划）

**suction.md（吸盘抓手）要点：**
- 气泵 + 电磁阀控制
- 由机械臂模块统一控制
- 待定状态
- 可能的硬件方案

## 验证标准
- [ ] arm.md ≥ 40 行
- [ ] vision.md ≥ 40 行
- [ ] face.md ≥ 40 行
- [ ] locomotion.md ≥ 40 行
- [ ] suction.md ≥ 40 行
- [ ] 每个文件都包含：概述、硬件参数、技术方案、当前状态、问题记录、参考链接
- [ ] 内容来自 ROBOT-SOP.md，不是编造的
