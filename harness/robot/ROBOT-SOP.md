# 🤖 0-1 私人 AI 机器人完整实施指南

**项目名**: 0-1（零杠一）
**记忆系统**: 贵庚
**文档版本**: v3.5（具身大脑版 + 全开源生态整合，优化版）
**字数**: 约 115200（字符）| 约 11490（词）
**创建日期**: 2026-03-07
**更新日期**: 2026-03-24

---

> 📝 **v3.5（本次优化）**：第二章重新编号（技术路线→2.4，梯度采购→2.5，星闪模块→2.6，Medusa Halo→2.7）；历史更新：电池换电/手部自由度/RoboGSim/稚晖君/GR00T/3DGS/Newton

---

# 目录

| 章节 | 标题 |
|------|------|
|------|------|
| 第一章 | 概念与愿景 |
| 第二章 | 硬件体系 |
| | 2.1 现有硬件 |
| | 2.2 需要采购（阶段一 MVP）|
| | 2.3 电源方案 |
| | 2.3.1 电池换电机制 |
| | 2.4 技术可行性：五条技术路线 |
| | 2.5 梯度采购路线图 |
| | 2.6 星闪通信模块：BearPi-Pico H3863 详细方案 |
| | 2.7 Medusa Halo（移动 AI 工作站）|
| 第三章 | 系统架构 |
| 第四章 | 实施阶段（Phase 0 → Phase 6）|
| 第五章 | AI 与感知 |
| | 5.1 Jetson Nano 视觉感知 |
| | 5.1.1 手部自由度与执行器设计 |
| | 5.2 iPhone 感知前端 |
| | 5.3 物理仿真引擎（Genesis + Newton）|
| | 5.4 具身大脑基模（RynnBrain + GR00T + 空间智能）|
| 第六章 | 本地 LLM 推理 |
| 第七章 | 附录（工具链/代码/配置）|
| 第八章 | 安全与维护 |
| 第九章 | 风险与合规 |
| 第十章 | 调研更新记录（按时间线）|

---

# 第一章：概念与愿景

## 1.1 项目愿景

**0-1** —— 不是一台机器，是你人生的另一面。

| 层含义 | 说明 |
|--------|------|
| **机器层** | 二进制的起点，代表硅基生命的底层语言 |
| **制造层** | 第一次「从零到一」用 3D 打印制造一个完整的机器人 |
| **生命层** | 人一生的「0 到 1」——从出生到结束，机器的记忆就是我的人生存档 |

0-1 不是一个固定的产品，而是一个会跟着 AI 能力一起长大的伙伴。10 年分五个阶段，每一年，期望和能力都在共同进化。

> 「0-1」还很适合用来做机器人面部的默认表情，且名字简单易记，未来易拓展至「1-2」「2-3」等。

---

## 1.2 核心系统：贵庚

**贵庚** 是 0-1 的记忆系统，专为保存一个人完整的一生而设计。

- **贵** = 粤语里对他人的敬称，也暗含「珍贵」
- **庚** = 天干第七位，对应时间、年龄、周期——记忆本质上就是时间的切片
- **贵庚** 在粤语里是问老人家年龄的敬语，带着一种对岁月沉淀的敬畏

> 贵庚存的不是数据，是一个人的年龄和尊严。

### 核心价值主张

| 价值 | 说明 | 优先级 |
|------|------|--------|
| **记忆延续（贵庚）** | 帮你记录身边发生的事情，随时回顾 | P0 |
| **陪伴对话** | 随时语音交流，有问必答 | P0 |
| **执行任务** | 帮你完成简单的物理任务 | P1 |
| **安全守护** | 身份认证、防抢防盗、紧急响应 | P1 |
| **数据隐私** | 所有数据本地处理，不传云端 | P0 |

---

## 1.3 核心陪伴理念：从「响应」到「懂你」

0-1 的终极目标不是执行指令，而是**观察你、推理你、主动介入**。

```
观察层（摄像头/传感器）
    ↓
行为模式识别（贵庚）
    ↓
意图推理引擎
    ↓
主动执行 / 主动询问
    ↓
你的反馈 → 微调模型
```

### 三个层次

| 层次 | 表现 | 举例 |
|------|------|------|
| **被动响应** | 你说/做，它执行 | "帮我回复微信" |
| **主动提醒** | 它观察到了，提示你 | "你今天还没喝水" |
| **主动执行** | 它推理出来了，直接做 | 你拿起外套，它就知道你要出门 — 顺便帮你拿上没想起来带的东西，还贴心的远程自动开关门 |

**最难的其实是「不打扰」**：主动推理最难的不是判断你要什么，而是**判断什么时候不该出声**。

> 贵庚需要学的第一件事不是预测，是**什么时候闭嘴**。

---

## 1.4 10年五阶段路线图

### 最终确认的五阶段

| 阶段 | 时间 | 核心目标 |
|------|------|---------|
| **阶段一** | 1-2年 | OpenClaw + Cyber Bricks 第一次结合，跑通"数字大脑→物理身体"链路 |
| **阶段二** | 3-4年 | 贵庚 MVP + 本地小模型控制物理身体；数字孪生环境训练→现实校验 |
| **阶段三** | 5-6年 | 身体+大脑进化，走出家门进入开放世界，互相守护 |
| **阶段四** | 7-8年 | 多个专家分身融合（线上MoE），各司其职，有摩擦期 |
| **阶段五** | 9-10年 | 线下专家替代线上MoE，经过长期磨合离线也能做好事情 |

### Phase 编号与五阶段对应关系

> 说明：Phase 0-6 是实施步骤的编号，与10年五阶段不是一一对应。Phase 0 是前置准备工作，Phase 1-6 覆盖阶段一和阶段二的内容，阶段三至五属于远期规划。

| Phase | 实施内容 | 对应年份 |
|-------|---------|---------|
| Phase 0 | Ubuntu 台式机对接 Gateway | 阶段一前置 |
| Phase 1 | 语音陪伴（OpenClaw + Cyber Bricks 首次联动）| 阶段一 |
| Phase 2 | 视觉记录（ESP32-Cam + Jetson Nano）| 阶段一 |
| Phase 3 | 面部表情系统 | 阶段一 |
| Phase 4 | 运动控制（Cyber Bricks + MQTT）| 阶段一 |
| Phase 5 | iPhone 感知前端接入（分布式感知网络）| 阶段二 |
| Phase 6 | 室内移动 + 智能家居硬件拓展 kit | 阶段二 |

**关键区分**：
- 阶段四：多个分身依赖线上 MoE
- 阶段五：贵庚积累足够数据，线下专家替代线上 MoE

---

# 第二章：硬件体系

## 2.1 现有硬件

| 设备 | 规格 | 数量 | 状态 |
|------|------|------|------|
| Jetson Nano | **2GB**（量产模块，非4GB开发套件）| 1 | 可用 |
| ESP32-Cam | OV2640 | 1 | 可用 |
| Cyber Bricks | ESP32-C3（XA003/XA004/XA005）+ 电机 + 舵机 | 2 | 已有（拓竹赠送）|
| 星闪设备 | BearPi-Pico H3863（海思 WS63 RISC-V，WiFi6+BLE+SLE三模，240MHz，40针Pico）| 2块（建议成对购买）| ✅ 推荐采购 |
| 拓竹 H2C | 3D打印机 | 1 | 可用 |
| Ubuntu 台式机 | 5600G+32G+RTX 2060 | 1 | 可用（待对接 Gateway）|
| MacBook Pro | OpenClaw Gateway | 1 | 运行中 |
| iPhone 16 Pro | A18 Pro + LiDAR + 4800万摄像 | 1 | 可用（待接入）|

### Jetson Nano 2GB 版本特别说明

> ⚠️ **重要**：你的 Jetson Nano 是 **2GB 版本**（量产模块），不是 4GB 开发套件。2GB 内存更小，跑 YOLO 更容易 OOM（内存溢出），优化方向完全不同。

2GB 内存的关键限制：
- 跑 YOLO 更容易 OOM，必须开启 swap
- **唯一有效的 GPU 加速是 FP16**（Maxwell 架构不支持 INT8 推理加速）
- 必须同时开 swap 才能同时跑 MediaPipe + YOLO
- DeepStream 6.x 支持 2GB，但配置复杂

---

## 2.2 需要采购（阶段一 MVP）

| 类别 | 配件 | 预算 |
|------|------|------|
| 语音套件 | 蓝牙耳麦（ESP32-Cam 蓝牙音频）| ¥80~150 |
| 运动套件 | 舵机、电机、轮子等 | ¥229 |
| 传感器 | 超声波、红外、蜂鸣器 | ¥22 |
| 其他 | 杜邦线、面包板、螺丝 | ¥60 |
| **合计** | | **¥391** |

---

## 2.3 电源方案

| 电源 | 规格 | 说明 |
|------|------|------|
| **拓竹 Cyber Tanks 内置电池** | 未知 | 随 Cyber Tanks 套件赠送，优先使用 |
| **小米 20000mAh 充电宝** | 74Wh | 便携，支持快充，可作为移动供电 |

> ⚠️ 扫地机器人电池已报废：进水腐蚀，无修复价值。

**长期目标**：固态户外移动电源，满电支持 ≥24 小时续航（覆盖白天+黑夜完整周期）。

### 2.3.1 电池换电机制（行业对标 & 设计参考）

> ⚠️ **0-1 当前状态**：文档未描述电池换电机制，这是具身机器人连续作业的关键功能，必须补充。

#### 行业现状

| 厂商 | 产品 | 换电方式 | 续航 | 特点 |
|------|------|---------|------|------|
| Boston Dynamics | Atlas（电动版）| **自换电池（双电池仓）** | 4小时 | 低电量自动导航到换电站，机械臂抓取电池插入 |
| Tesla | Optimus Gen3 | **自主回充桩** | 10-12小时 | 自动定位充电桩，精准插拔，支持夜间充 |
| 优必选 | Walker S2 | **自主换电** | 未公开 | 自动导航换电站，更换电池后继续任务 |
| Figure | Figure 03 | 无线感应充电 | 5小时 | 接触式充电，无机械插拔 |

#### 核心设计原则

1. **双电池仓设计**（参考 Atlas）
   - 主电池仓：供给运动 + AI 推理
   - 备用电池仓：低电量时无缝切换，不中断任务
   - 换电时备用仓接管，机器人不停止

2. **自主回充 vs 换电的选择**
   - 家用场景（0-1 主要场景）：**优先自主回充桩**
     - 优势：成本低、安静、对电池损耗小
     - 充电桩造价：参考 Tesla Optimus 方案，约 ¥500-2000
     - 导航精度要求：±2cm（Optimus Gen3 已实现精准插拔）
   - 工业场景（Walker S2、Atlas）：**换电为主，回充为辅**
     - 优势：换电仅需 3-5 分钟，回充需要 2 小时

3. **0-1 推荐方案（家用版）**
   - 采用**自主回充桩**方案（参考 Tesla Optimus）
   - 设计要点：
     - 充电桩目标：低电量（<20%）时自动返回，精准对准插入
     - 导航方案：视觉 QR 码辅助定位（比纯 SLAM 更便宜、更稳定）
     - 充电接口：参考机器人背部设计，充电触点在直立姿势下自然暴露
     - 续航目标：主电池 ≥8 小时（覆盖白天活动），夜间回充
   - 备选：双电池仓（发烧友版），成本约 +¥1500

4. **续航 vs 作业时间的关系**
   - 8-12 小时续航：覆盖白天活动，夜间充电（与人类作息同步）
   - <4 小时续航（Atlas）：必须支持换电，否则无法连续作业
   - 0-1 目标：主电池 ≥8 小时 + 自主回充桩 = 24 小时连续守护

---

## 2.5 梯度采购路线图

| 时间 | 设备 | 理由 | 价格 |
|------|------|------|------|
| **2026-06** | RTX 5050 9GB GDDR7（96-bit，336 GB/s）| 插入现有台式机，跑 Qwen3.5-4B/9B 4-bit | ~2,000元 |
| **Q2** | AMD AI Halo 128GB | 跑 Qwen3.5-122B，本地训练贵庚，618 可能低于1万 | ~10,000-15,000元 |
| **阶段一** | Jetson AGX Thor | 替代 Nano 作为 0-1 主控 | ~24,000元 |
| **阶段一（备选）** | Jetson Thor Nano | 年底上市后替换，预计性价比最高 | ~2,000元（期待价）|
| **阶段一** | 全景摄像头 | 360° 视觉冗余 | 3,000元 |
| **阶段一** | NAS | 本地备份贵庚所有 raw data | 3,000元 |
| **可选** | DGX Spark | NVIDIA 官方 OpenClaw 支持，NemoClaw 优化，2026年2月涨价 | ~34,999元（京东自营）|
| **充裕时** | DGX Station GB300 | 748GB 统一内存，20 PFLOPS | ~70万 |

---

## 2.6 星闪通信模块：BearPi-Pico H3863 详细方案

> **采购链接**：https://item.taobao.com/item.htm?id=821386760379
> **星闪通信需双设备，建议成对购买**
> **参考价格**：¥19.8（两边不带排针）/ ¥25.8（带排针）
> **官方文档**：https://www.bearpi.cn/core_board/bearpi/pico/h3863/

#### 核心规格

| 项目 | 规格 |
|------|------|
| 主控芯片 | 海思 WS63（RISC-V，240MHz，支持浮点/SWD）|
| 存储 | 606KB SRAM + 300KB ROM + 4MB Flash |
| 无线 | Wi-Fi 6（114.7Mbps）+ BLE 5.2（2Mbps）+ **SLE 1.0（12Mbps）三模并发** |
| 接口 | GPIO×17、UART×3（最高4Mbps）、SPI×2、QSPI×1、PWM×8、ADC×6、I2S×1 |
| 安全 | AES/SM2/SM3/SM4/TRNG 硬件加密 |
| 温度 | **-40℃~+85℃**（工业级宽温）|
| 供电 | USB-C 5V / 外部5V，3.3V MCU |
| 形态 | **40针 Pico 形态**（兼容树莓派Pico扩展板）|

#### 为什么选择 H3863 而不是 ESP32-C6

| 维度 | BearPi-Pico H3863 | ESP32-C6 |
|------|-------------------|-----------|
| 星闪 SLE | ✅ **原生支持**，20μs 时延 | ❌ 不支持 |
| BLE 并发数 | 4096 设备 | <50 |
| 空口速率 SLE | **12Mbps** | — |
| 国密算法 | ✅ SM2/SM3/SM4 硬件支持 | ❌ |
| 国产供应链 | ✅ 全国产 | 中等（乐鑫/台积电）|
| 开发难度 | 较高（需熟悉 HiSpark/OpenHarmony）| 低（Arduino即插即用）|

#### 对 0-1 的核心价值

**1. 微秒级无线控制**：SLE 时延 20μs（蓝牙10ms级），机器人遥控几乎无延迟，差速底盘/机械臂关节同步成为可能。

**2. 三模合一**：一块板同时提供：
- **SLE**：实时控制指令（20μs）
- **WiFi6**：高清图传/大数据回传（114.7Mbps）
- **BLE**：手机调试/低功耗状态上报

**3. 国密安全**：SM2/SM3/SM4 硬件加密，适合需要数据安全的场景。

**4. 国产自主**：星闪是中国自主短距无线标准，华为/荣耀手机+问界汽车已搭载，2026年进入工业标准。

#### 与现有硬件的集成方案

**方案一：Jetson Nano + H3863 + ESP32-Cam（推荐）**

```
Jetson Nano（视觉/规划）
    ↓ UART（4Mbps）
BearPi-Pico H3863（通信中枢）
    ↓ SLE（20μs）  → 执行器/舵机/电机驱动
    ↓ WiFi6       → 上位机/手机高清图传
    ↓ BLE         → 手机调试/配网
```

接线：
- H3863 UART1 TX → Jetson Nano `/dev/ttyTHS1` RX
- H3863 UART1 RX → Jetson Nano `/dev/ttyTHS1` TX
- H3863 GND → Jetson Nano GND
- H3863 GPIO（PWM）→ 电机驱动板信号输入

**方案二：Cyber Bricks 执行层 + H3863 通信层**

Cyber Bricks 已有 ESP32-C3（WiFi+BLE），H3863 作为通信扩展模块叠加：
- H3863 通过 UART 与 Cyber Bricks 主控板通信
- H3863 通过 SLE 无线接收上位机指令
- Cyber Bricks 专注执行，H3863 专注通信

**方案三：H3863 作为智能家居网关**

H3863 作为 HomeAssistant 的本地无线网关：
- WiFi6 连接路由器（以太网回传）
- SLE 连接室内传感器节点（门锁/灯/温湿度）
- MQTT 协议与 OpenClaw Gateway 通信
- 支持国密，隐私数据不出家门

#### 开发环境

| 项目 | 说明 |
|------|------|
| SDK | HiSpark Studio（Windows）/ 命令行编译链 |
| 语言 | C/C++（主要）|
| 操作系统 | OpenHarmony / FreeRTOS / 裸机 |
| 调试 | J-Link / 串口（OpenOCD）|
| 学习曲线 | 中等（7/10，需适应鸿蒙生态）|

#### 落地步骤

| 周 | 任务 | 目标 |
|----|------|------|
| 第1周 | 环境搭建 + 点灯 | 编译-烧录-运行最小闭环 |
| 第2周 | 外设驱动 + OLED显示 | I2C点亮OLED，显示IP/状态 |
| 第3周 | SLE串口透传测试 | 两块H3863互发数据，测时延和稳定性 |
| 第4周 | 与 Jetson Nano UART 对接 | 打通"大脑→执行器"链路 |
| 第5周 | PWM驱动电机 | 速度指令控制电机正反转 |
| 第6周 | 整机联调 | SLE无线遥控 + WiFi图传回显 |

#### 采购建议

- **数量**：至少 **2块**（SLE收发测试需要，成对购买）
- **配套采购**：USB转TTL调试器（串口日志）、SSD1306 OLED（状态可视化）
- **替代考虑**：若开发周期紧，ESP32-C6（WiFi6+BLE5）可作为快速原型替代，但无法获得 SLE 超低时延

#### H3863 AI 推理能力分析（重要）

> ⚠️ **核心结论**：H3863 **不适合跑 YOLO 目标检测**，其价值在于**感知前处理 + 低功耗值守 + 星闪网关**。

**硬件限制（硬数据）：**

| 参数 | Hi3863V100 | 参照对比 |
|------|-----------|---------|
| CPU | RISC-V 32bit，240MHz，**无 NPU** | |
| SRAM | **606KB**（极小）| STM32H7（640KB）同级别 |
| 存储 | 4MB Flash | |
| 算力 | ~0.24 GFLOPS | 比 ESP32-S3 弱 |

**YOLO 推理能力（MCUBench 实测数据）：**

| MCU | 频率/RAM | 可跑模型 | 分辨率 | FPS | mAP |
|------|---------|---------|-------|-----|-----|
| STM32H573 | 250MHz/640KB | YOLOv6 d85w50 | 128×128 | **3.8 FPS** | 0.07 |
| STM32F769 | 216MHz/512KB | YOLOv6 d85w50 | 128×128 | **4.5 FPS** | 0.08 |

H3863（240MHz/606KB）换算：~4 FPS，但 mAP 仅 0.07，检测能力极弱。

**结论**：
- ❌ 无法跑完整 YOLOv5n/v8n（需 100MB+，H3863 只能塞进几百 KB 模型）
- ❌ FPS 4 << 实时要求 15fps
- ❌ 精度 mAP 0.07 无法用于实际目标检测

**星闪 SLE 传输能力（实测）：**

| 指标 | 数据 |
|------|------|
| 空口时延 | 49μs/帧 |
| 端到端延迟 | **≤1ms** |
| 有效带宽 | ~6-8Mbps |

| 传输内容 | 大小 | 传输时间 @ 8Mbps | 可行性 |
|---------|------|----------------|--------|
| YOLO 检测结果（坐标+类别）| ~200B | **<1ms** | ✅ 完美 |
| ROI 小图（320×240 JPEG）| ~10KB | ~10ms | ⚠️ 可接受 |
| 实时视频流 | — | — | ❌ 带宽不足 |

**协作架构建议（H3863 做前处理）：**

```
摄像头 → H3863（帧差法/运动检测，30fps）→ 星闪传ROI → Nano YOLO精推理
                              ↓ 无运动
                          Nano 深度休眠
```

| 指标 | 数值 |
|------|------|
| H3863 粗筛延迟 | 5-10ms |
| 星闪 ROI 传输 | <1ms |
| Nano 精推理（仅ROI）| 10-20ms |
| **总延迟** | **16-31ms（比 Nano 全量推理降低 30-40%）** |

**功耗与续航：**

| 设备 | 算力任务 | 值守/休眠 |
|------|---------|----------|
| Jetson Nano 2GB | 10W | 5W（无法深度休眠）|
| BearPi-Pico H3863 | 0.5W | **0.3W** |

假设 10,000mAh 3.7V（37Wh）电池：

| 方案 | 平均功耗 | 续航 |
|------|---------|------|
| Nano 单独运行 | 7.5W | **4.9 小时** |
| H3863 值守 + Nano 按需唤醒 | 1.5W | **~25 小时** |
| 续航提升 | | **~5 倍** ✅ |

**任务分配（H3863 vs Nano）：**

| ✅ H3863 适合 | ❌ 必须留在 Nano |
|-------------|----------------|
| 图像预处理（缩放、灰度、二值化）| YOLO 目标检测（全量推理）|
| 运动检测触发（帧差法，30fps）| MediaPipe 人体姿态 |
| 传感器聚合（I2C/SPI：电池、IMU、温湿度）| SLAM 视觉里程计 |
| 语音 VAD（关键词唤醒）| 神经网络语音降噪 |
| 星闪高速回传（检测结果，<1ms）| 复杂多目标跟踪 |
| 电机 PWM 预控制 | |

> **最终定位**：H3863 = **感知前处理器 + 低功耗传感 hub + 星闪网关**（不是 AI 推理节点）
>
> **最佳协同**：H3863 负责值守（0.3W）+ 运动触发 + 传感采集；Nano 负责视觉 AI 推理（按需唤醒）。续航提升 5 倍，OOM 大幅缓解。

---

## 2.7 Medusa Halo：移动 AI 工作站（长期规划）

> **定位**：作为 0-1 的移动终端，与家中 AMD AI Halo（Ryzen AI Max+ 395，128GB）遥相呼应——外出时完整展示 0-1 AI 能力，不因移动而性能受限。
>
> **背景**：2026年 CES 已发布 Strix Halo 新 SKU（Ryzen AI Max+ 392 等），Medusa Halo 为下一代迭代，2027-2028 年上市。

### 核心规格（爆料，非官方确认）

| 规格 | Strix Halo（当前旗舰）| Medusa Halo（预期）| 提升 |
|------|---------------------|-------------------|------|
| **CPU架构** | Zen 5，16核 | **Zen 6，24+2核** | 架构换代，+50%核心 |
| **GPU架构** | RDNA 3.5，40 CU | **RDNA 5，48 CU** | 架构换代 |
| **AI算力** | 基准 | **4-10倍** | RDNA 4/5矩阵增强 |
| **内存类型** | LPDDR5X-8533 | **LPDDR6** | 换代升级 |
| **理论带宽** | 256 GB/s | **460-691 GB/s** | +80%~+170% |
| **位宽** | 256-bit | **256-bit → 384-bit** | +50% |
| **内存容量** | 128GB | **256GB+** | +1倍 |
| **制程** | 4nm/5nm | **2nm N2P + 3nm N3P** | 大幅先进 |

> **来源**：多源确认（Olrak29_@X、Tom's Hardware、TechPowerUp、Fudzilla），均为爆料非官方

### LPDDR6 带宽对本地大模型的意义

Strix Halo 的 256 GB/s 带宽已可流畅跑 7B/13B 量化模型，但面对更大模型和更长上下文时带宽成为瓶颈。

Medusa Halo 的 LPDDR6（预估 460-691 GB/s）：
- **KV 缓存密集型场景**：上下文越长，带宽优势越明显
- **高位宽量化**：可更稳地跑 FP8/INT8，精度不降
- **tokens/s 吞吐**：预估提升 2-3 倍

### 256GB+ 统一内存对 0-1 移动终端的意义

| 可跑模型 | Strix Halo（128GB）| Medusa Halo（256GB+）|
|---------|-------------------|---------------------|
| Qwen3-14B | ✅ FP16 | ✅ FP16 |
| Qwen3.5-32B | ⚠️ 勉强 | ✅ 流畅 |
| Qwen3.5-72B | ⚠️ 需 Q4 量化 | ✅ FP16 全精度 |
| Qwen3.5-130B | ❌ 需 INT4 | ✅ INT4/INT8 全量 |
| 405B 级模型 | ❌ 不可行 | ⚠️ 可行（量化） |

**关键优势**：外出展示时，整个 0-1 系统（贵庚 + 语音 + 视觉 + 任务调度）可以完整跑在笔记本上，无需向云端妥协。

### 多 Agent 并行支持

| 场景 | Strix Halo | Medusa Halo |
|------|-----------|-------------|
| 并行 Agent 数 | 4-5个 | **8-12个** |
| 可同时跑 | 单 Agent 大模型 | **多个 72B 模型并行** |
| 256K+ 上下文 | ❌ | ✅ |
| Agent 间通信延迟 | 内存级 | **微秒级（统一内存）** |

典型并行场景：
- 文字 Agent（代码生成）+ 视觉 Agent（图像）+ 语音 Agent（实时）+ 规划 Agent（ReAct）

### 与家中 AI Halo 的性能对比

| 维度 | 家中 AI Halo（Strix Halo 128GB）| 外出 Medusa Halo（256GB+）|
|------|--------------------------------|------------------------|
| 内存带宽 | 256 GB/s | 460-691 GB/s（+80%~+170%）|
| 可跑模型大小 | 72B 需量化 | 130B 全精度 |
| 多 Agent 并行 | 4-5个 | 8-12个 |
| 长上下文 | ~128K tokens | 512K+ tokens |
| AI 推理吞吐 | 一般 | **优秀（2-3倍）** |
| 离电移动 | ✅ 可行 | ✅ **完整支撑** |

### 结论

Medusa Halo 是 0-1 移动终端的完美选择：
- **2027-2028年上市**，需要等
- **Strix Halo（如 Asus ProArt PX13）** 是现在最近的选择，外出演示时模型需略微压缩
- 两者组合：家中固定算力 + 外出移动展示 = 完整不间断的 0-1 能力

### 当前可买的最近替代（过渡方案）

| 产品 | 规格 | 价格 |
|------|------|------|
| Asus ProArt PX13 | Ryzen AI Max+ 395，128GB LPDDR5X，256 GB/s | $2,199+ |
| Asus ROG Flow Z13 | 同上 APU，游戏二合一 | $2,499+ |

---

## 2.8 手部与执行器设计

> ⚠️ **0-1 当前状态**：文档只写了"灵巧手"三字，无具体参数。本节参考竞品给出具体设计参考。

#### 行业现状

| 厂商 | 产品 | 手部 DOF | 指尖力矩/力反馈 | 说明 |
|------|------|----------|----------------|------|
| Tesla | Optimus Gen3 | **22 DOF × 2（单手）** | 触觉传感器（指尖力反馈）| 人类约27-28 DOF，Tesla已做到81% |
| Boston Dynamics | Atlas | 全身56 DOF | 全身触觉感知 | 全关节连续旋转，可做复杂体操动作 |
| 宇树 | G1 | 23-34 关节 | 未公开 | 展示过捏鸡蛋、拧螺丝等精细操作 |
| Figure | Figure 03 | 未公开 | 多维力矩传感器 | 执行器速度2倍于上代 |

#### 自由度（Degrees of Freedom, DOF）说明

DOF = 独立控制的旋转/平移轴数量。人类单手约 27 DOF：
- 大拇指：5 DOF（2个关节 + 腕掌关节）
- 食指：4 DOF
- 中指/无名指/小指：各 4 DOF
- 腕部：3 DOF
- 总计：约 27-28 DOF

#### 手部设计的三个关键参数

| 参数 | 说明 | 0-1 设计目标 |
|------|------|-------------|
| **关节数（DOF）** | 决定能做什么动作 | 单手 ≥12 DOF（基础），≥20 DOF（进阶） |
| **指尖力矩** | 决定能抓多重的东西 | 持续抓取 ≥5kg（基础），≥20kg（进阶） |
| **触觉传感器** | 决定精细操作能力 | 指尖压力传感（基础），多维力矩（进阶） |

#### 0-1 推荐方案（分阶段）

**阶段一（基础版）**：
- 使用 Cyber Bricks 现有舵机，12 DOF 单手
- 成本：~¥200/手
- 限制：无法做精细操作（捏鸡蛋等）
- 参考：宇树 G1 早期版本

**阶段二（进阶版）**：
- 目标：单手 16-22 DOF + 指尖压力传感
- 方案：LD-2209 伺服舵机（20kg/cm 扭矩）× 12个 + 薄膜压力传感器
- 成本：~¥800/手
- 可实现：捏鸡蛋（需触觉反馈）、穿针、拧螺丝
- 参考：Tesla Optimus Gen2（11 DOF → Gen3 22 DOF 路线）

**阶段三（发烧友版）**：
- 单手 22 DOF + 多维力矩传感器 + 腱绳驱动（Tendon-driven）
- 成本：~¥2000/手
- 参考：Tesla Optimus Gen3 执行器设计（腱绳驱动，前臂执行器）

#### 腱绳驱动（Tendon-driven）参考

Tesla Optimus 的执行器设计关键：
- 执行器放在前臂而非手心（可制造性优先）
- 通过腱绳（tendon）传递力量到手部关节
- 优势：手部轻薄、关节密度高
- 挑战：腱绳磨损、张力控制

#### 触觉传感器选型

| 类型 | 价格 | 精度 | 适用场景 |
|------|------|------|---------|
| **薄膜压力传感器**（压敏电阻）| ¥5-20/个 | 低 | 抓取检测（有没有碰到）|
| **FSR402**（力敏电阻）| ¥30-50/个 | 中 | 力度控制（抓多紧）|
| **HT201 压力传感阵列** | ¥200/个 | 高 | 精细操作（捏鸡蛋）|
| **ATI 多维力矩传感器** | ¥5000+/个 | 极高 | 工业级精密操作 |

0-1 阶段二推荐：薄膜压力传感器（¥5-20）× 8个 + FSR402 × 4个

---

## 2.4 技术可行性：五条技术路线

> 这件事在 2024-2026 年变得真正可行，是因为五条技术路线同时成熟，每条均为独立技术栈，对应行业关键拐点。

### 技术路线一：开源 AI Agent 框架

OpenClaw 是全球最流行的开源 AI Agent 项目，被称为"个人 AI 的操作系统"。2026 年 GTC 上黄仁勋宣布 *"AI agents era has arrived"*，NVIDIA 官方推出 NemoClaw（集成 OpenShell 安全沙箱 + Nemotron 模型），AMD 推出 RyzenClaw / RadeonClaw 部署指南（128GB 统一内存跑 70B 模型），Intel 优化 OpenClaw 混合 AI 执行（本地 + 云端），腾讯推出 QClaw 深度集成微信/QQ 生态。Claw 已成为 AI Agent 领域的命名共识，各大厂商纷纷围绕 OpenClaw 构建自己的配套生态。0-1 基于 OpenClaw 构建，获得了整个行业生态的背书。

### 技术路线二：消费级物理仿真

Genesis 是华人团队（CMU、MIT 等）开源的物理仿真引擎，RTX 4090 上 43M FPS，比 NVIDIA Isaac Gym 快 10-80 倍；GTX 1080 6GB 起就能跑（Ubuntu 台式机 RTX 2060 6GB 可用），MIT 开源免费，让数字孪生训练的门槛从 Isaac Gym 的 RTX 3090+ 降到几千元。

### 技术路线三：个人制造工具链

拓竹 H2C + Bambu Suite + Cyber Bricks，让一个人在家里就能完成从 3D 打印结构件到精密加工到运动控制的全流程。

### 技术路线四：本地大模型推理

Ollama + GGUF (Q4_K_M) 让 7B 模型在现有台式机 RTX 2060 上跑；vLLM / LM Studio / SGLang 各有优势——Ollama 最易用、vLLM 吞吐最高、SGLang 支持复杂 Agent 任务；AMD AI Halo 128GB（618 可能低于 1 万）跑 Qwen3.5-122B。所有推理完全本地，贵庚的记忆系统可以完全本地化，隐私安全。

### 技术路线五：统一内存架构芯片走向成熟

苹果 M 系列、AMD AI Max 系列都采用 CPU/GPU/NPU 共享物理内存的统一内存架构，避免了传统 CPU 与独立显存之间的数据搬运开销——苹果 M5 带宽 153GB/s、MacBook 24GB 可跑 30B 模型（4-bit 量化），AMD AI Max+ 128GB 统一内存、256GB/s 带宽、可跑 70B 参数模型；英特尔 Lunar Lake 也尝试了封装内存设计，虽然已确认是短期尝试但说明行业方向一致。LPDDR5X / LPDDR6 等低电压、大容量、高带宽内存颗粒解决了传输瓶颈；PCIe 5.0 / 6.0 的高带宽打通了芯片与内存之间的最后一公里。这些技术同时成熟，让大模型本地化推理真正具备可行性。

---

# 第三章：系统架构

## 3.1 整体架构

```
┌─────────────────────────────────────────┐
│         Ubuntu 台式机 (GPU节点)           │
│  • RTX 2060 GPU 加速                    │
│  • 32GB RAM                            │
└──────────────────┬──────────────────────┘
                   │ openclaw node / WebSocket
                   │ （有线千兆局域网）
┌──────────────────▼──────────────────────┐
│              家里 Gateway (MacBook)        │
│        主 AI (贵庚大脑) + 任务调度         │
└──────────────────┬──────────────────────┘
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
   ┌────────┐ ┌────────┐ ┌────────┐
   │ Jetson │ │Cyber   │ │Cyber   │
   │ Nano   │ │Brick 1 │ │Brick 2 │
   │(感知+  │ │(执行)  │ │(备用)  │
   │ 控制)  │ │        │ │        │
   └────┬───┘ └────────┘ └────────┘
        │              │
        ▼              ▼
   ┌────────┐    ┌──────────────────┐
   │ ESP32- │    │   拓竹工具链      │
   │ Cam×2  │    │ H2C 3D打印+制造  │
   └────────┘    └──────────────────┘
```

### iPhone 接入后的完整拓扑

```
Gateway(MacBook)
    ↓ WiFi/MQTT
iPhone 16 Pro(感知前端) ← OpenClaw Node 协议
    ↓ 有线 UART/I2C/GPIO
Jetson Nano(控制) → ESP32-Cam × 2 + Cyber Bricks
```

---

## 3.2 节点说明

| 节点 | 角色 | 功能 |
|------|------|------|
| Mac Gateway | 主控 | AI大脑、贵庚记忆、任务调度 |
| Ubuntu 台式机 | GPU节点 | 图像理解、GPU密集任务（RTX 2060）|
| Jetson Nano | 边缘节点 | 语音交互、视频处理、运动控制（2GB 限制）|
| Cyber Bricks ×2 | 运动节点 | 电机控制、动作执行 |
| ESP32-Cam ×2 | 视觉节点 | 视频采集、室内建模 |
| iPhone 16 Pro | 无线前端 | 高质量感知、LLM 辅助推理、LiDAR 建模 |

---

## 3.3 通信协议

### 设备内通信

| 协议 | 用途 | 延迟 | 说明 |
|------|------|------|------|
| **MQTT** | 设备间命令传递 | <50ms | 主协议，QoS 1 保证送达 |
| **WebSocket** | Gateway ↔ 节点 | <20ms | 实时双向，OpenClaw Node 协议 |
| **REST API** | 控制指令 | <100ms | 简单场景，ESP32 有现成实现 |

### 有线通信（GPIO / UART / I2C）

| 协议 | 用途 | Jetson Nano | ESP32-Cam |
|------|------|------------|-----------|
| **UART** | 简单命令传递 | Pin 8(TX)/10(RX)，/dev/ttyTHS1 | GPIO1/3，波特率115200 |
| **I2C** | 多设备总线 | Pin 3(SDA)/5(SCL)，速率10-400kHz | GPIO4/5，需要电平3.3V |
| **GPIO** | 应急停止信号 | Pin 29 等，/sys/class/gpio | 任意GPIO，硬件中断μs级 |

> **关键洞察**：Jetson Nano 和 ESP32-Cam 都有 40 针 GPIO，这是有线控制的核心。有线应急停止 <1ms，无线 WiFi >100ms。

### 通信场景选择

| 场景 | 推荐协议 |
|------|---------|
| 紧急停止 | **有线 GPIO**（<1ms，故障安全）|
| 启动/停止时序 | **有线 UART**（115200波特率）|
| 多设备同步时钟 | **有线 I2C**（TCA9548A多路复用）|
| 传感器数据采集 | 无线 MQTT（Qos 1）|
| 视频流 | 无线 WiFi（GStreamer RTSP）|

---

## 3.4 ROS 2 支持情况与替代框架

> 调研时间：2026-03-23，来源：豆包专家模式深度调研
> **结论：Jetson Nano 2GB 可完整跑 ROS 2；ESP32-CAM / H3863 / iPhone 需通过 micro-ROS / rosbridge 间接接入**

### 硬件 ROS 2 支持总览

| 设备 | ROS 2 支持 | 推荐方案 | 备注 |
|------|-----------|---------|------|
| **Jetson Nano 2GB** | ✅ 完整支持 | ROS 2 Foxy + Ubuntu 18.04（仅装 ros-base） | 2GB 内存需精简，禁用 GUI |
| **ESP32-CAM** | ⚠️ 间接支持 | micro-ROS + WiFi / UART | 520KB SRAM 限制，仅跑精简节点 |
| **BearPi Pico H3863** | ⚠️ 间接支持 | micro-ROS + 星闪 SLE / WiFi | 暂无官方包，需自行移植 |
| **iPhone 16 Pro** | ⚠️ 间接支持 | rosbridge (WebSocket) / Zenoh / MCP | Swift + ARKit 是最佳原生感知方案 |

---

### 3.4.1 Jetson Nano 2GB — 完整 ROS 2 方案

#### 推荐版本

| ROS 2 版本 | Ubuntu | 适配度 | 备注 |
|------------|--------|--------|------|
| **Foxy Fitzroy** | 20.04 LTS | ✅ 最佳 | 稳定、内存友好、生态成熟（LTS） |
| **Humble Hawksbill** | 22.04 LTS | ⚠️ 可跑 | 内存占用更高，需深度优化 |
| Galactic / Iron | — | ❌ 不推荐 | 非 LTS，维护周期短 |

#### 安装步骤（Foxy + ros-base）

```bash
# 1. 配置 locale
sudo apt update && sudo apt install locales
sudo locale-gen en_US.UTF-8
export LANG=en_US.UTF-8

# 2. 添加 ROS 2 源
sudo apt install -y curl gnupg2 lsb-release
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

# 3. 安装（仅 ros-base，节省内存）
sudo apt update
sudo apt install -y ros-foxy-ros-base python3-argcomplete

# 4. 初始化
sudo apt install -y python3-rosdep
sudo rosdep init
rosdep update

# 5. 环境
echo "source /opt/ros/foxy/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

#### 资源占用

| 组件 | 内存占用 | 说明 |
|------|---------|------|
| ROS 2 Foxy core | ~300-400MB | 仅核心，无 GUI |
| rviz2 | ~500MB | 可选，Nano 2GB 不建议跑 |
| 完整 ros-base | ~600-800MB | 包含 rclcpp / rclpy / msgs |

**优化建议**：永远只装 `ros-foxy-ros-base`，用远程 rviz2 或手机/平板做可视化。

---

### 3.4.2 ESP32-CAM — micro-ROS 接入方案

#### 核心限制
- **520KB SRAM / 4MB Flash**：无法跑完整 ROS 2 栈
- 标准 ROS 2 依赖 POSIX 线程、动态内存，FreeRTOS 不满足
- OV2640 JPEG 压缩可发布，但高分辨率/高帧率会占满内存

#### 方案 1：micro-ROS + WiFi（推荐）

```
ESP32-CAM (micro-ROS 节点)
    ↓ WiFi UDP
micro-ros-agent (运行在 Jetson Nano / PC)
    ↓
ROS 2 主节点
```

```cpp
// ESP32 端示例（Arduino + micro_ROS）
#include <micro_ros_arduino.h>
#include <sensor_msgs/msg/compressed_image.h>

rcl_node_t node;
rcl_publisher_t pub;
sensor_msgs__msg__CompressedImage msg;

void setup() {
  // WiFi 连接
  set_microros_wifi_transports("SSID", "password", "agent-ip", 8888);
  
  // 创建节点
  rclc_node_init_default(&node, "esp32_cam", "", &support);
  
  // 创建发布者
  rclc_publisher_init_default(&pub, &node, ROSIDL_GET_MSG_TYPE_SUPPORT(
    sensor_msgs, msg, CompressedImage), "/camera/image/compressed");
}

void loop() {
  // 采集 OV2640 JPEG → 发布
  camera_fb_t *fb = esp_camera_fb_get();
  if (fb) {
    msg.format.data = (char*)"jpeg";
    msg.data.data = fb->buf;
    msg.data.size = fb->len;
    rcl_publish(&pub, &msg, NULL);
    esp_camera_fb_return(fb);
  }
  delay(100); // 10 FPS
}
```

**Jetson Nano 端启动代理**：
```bash
# 安装 micro-ROS agent
sudo apt install -y ros-foxy-micro-ros-agent

# WiFi 模式启动
ros2 run micro_ros_agent micro_ros_agent udp4 \
  --help  # 查看参数
ros2 run micro_ros_agent micro_ros_agent udp4 -h <agent-host> -p 8888
```

#### 方案 2：micro-ROS + UART（低延迟，有线）

```
ESP32-CAM ← USB-TTL → Jetson Nano (micro-ros-agent)
```

```bash
# Jetson Nano 端
ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyUSB0 -b 921600
```

#### 方案 3：HTTP/MJPEG 流（最简，不跑 micro-ROS）

```python
# Jetson Nano 拉取 ESP32-CAM MJPEG 流，转 ROS 2 Image
import cv2, rclpy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

cap = cv2.VideoCapture('http://esp32-ip/stream')
bridge = CvBridge()

while cap.isOpened():
    ret, frame = cap.read()
    if ret:
        msg = bridge.cv2_to_imgmsg(frame, encoding="bgr8")
        publisher.publish(msg)
```

**推荐配置**：QVGA (320×240) / 5-10 FPS，避免 ESP32 内存溢出。

---

### 3.4.3 BearPi Pico H3863 — 移植方案

#### 现状
- Hi3863（RISC-V 32bit，240MHz，4MB Flash）**无 MMU，无法跑标准 Linux**
- **无官方 micro-ROS 包**，需基于 FreeRTOS + RISC-V 工具链自行移植
- 星闪 SLE / WiFi 6 / BLE 三模通信是 H3863 的独特优势

#### 移植路径

```
1. 搭建 Hi3863 开发环境（RISC-V 工具链 + 小熊派 SDK）
2. 移植 micro-ROS 核心（rcl / rclc，基于 FreeRTOS）
3. 适配 Micro XRCE-DDS 到 Hi3863 的 UART / SPI / WiFi 驱动
4. 主机运行 micro-ros-agent，桥接到 ROS 2
5. 星闪 SLE 作为传输层（<5ms 延迟，适合实时控制）
```

#### 星闪 SLE vs 其他无线方案对比

| 方案 | 延迟 | 可靠性 | 适用场景 |
|------|------|--------|---------|
| **星闪 SLE** | <5ms | 极高 | 机器人实时控制（推荐） |
| UWB | <1ms | 极高 | 高精度定位 + 控制 |
| BLE 5.3 | 10-20ms | 高 | 低速关节、传感器 |
| WiFi 6 | 10-30ms | 中 | 高清图传、非实时 |

---

### 3.4.4 iPhone 16 Pro — rosbridge / MCP 方案

#### 架构

```
iPhone (Swift + ARKit)
    ↓ WebSocket / MCP
rosbridge_server (Jetson Nano / PC)
    ↓
ROS 2 主节点
```

#### Swift + rosbridge 示例

```swift
import ARKit
import Starscream  // WebSocket 库

class ROS2Bridge: WebSocketDelegate {
    let socket: WebSocket
    
    init(agentHost: String, port: Int) {
        let url = URL(string: "ws://\(agentHost):\(port)")!
        socket = WebSocket(request: URLRequest(url: url))
        socket.delegate = self
        socket.connect()
    }
    
    // ARKit 每帧回调
    func session(_ session: ARSession, didUpdate frame: ARFrame) {
        // 发布 Odometry（VIO 位姿）
        let odom: [String: Any] = [
            "op": "publish",
            "topic": "/iphone/odom",
            "msg": [
                "header": ["stamp": ["sec": Int64(Date().timeIntervalSince1970)]],
                "pose": ["pose": ["position": ["x": frame.camera.transform.columns.3.x,
                                               "y": frame.camera.transform.columns.3.y,
                                               "z": frame.camera.transform.columns.3.z]]
            ]
        ]
        if let data = try? JSONSerialization.data(withJSONObject: odom) {
            socket.write(data: data)
        }
    }
    
    func didReceive(event: WebSocketEvent, client: WebSocketClient) {
        // 接收 ROS 2 发来的控制指令
        if case .text(let str) = event {
            if let data = str.data(using: .utf8),
               let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               json["op"] as? String == "publish" {
                // 解析指令 → 执行动作
            }
        }
    }
}
```

#### 替代方案对比

| 方案 | 优点 | 缺点 |
|------|------|------|
| **rosbridge** | 成熟、JSON 易用、工具多 | 额外序列化开销 |
| **Zenoh** | 更高效、支持 DDS 互通 | iOS 端库少 |
| **MCP (Model Context Protocol)** | 与 OpenClaw 原生集成 | 需自行实现 Swift 端 |

**推荐**：用 rosbridge 先跑通，后续可升级到 Zenoh 提升效率。

---

### 3.4.5 比 ROS 2 更好的替代框架

| 框架 | 优势 | 适用场景 |
|------|------|---------|
| **Micro-ROS** | 极轻量、MCU 可跑、与 ROS 2 完全兼容 | ESP32、H3863 等嵌入式 MCU |
| **ROS 1** | 生态最成熟、文档最多、简单场景首选 | 简单机器人、无需新特性 |
| **SROS2** | ROS 2 安全加固（TLS / DDS 加密） | 高安全场景 |
| **YUR** | 极轻量、Web 可视化、快速原型 | 教学、Web 端监控 |

**对于 0-1 项目的建议**：
- **Jetson Nano**：ROS 2 Foxy，与 OpenClaw 通过 MQTT / WebSocket 桥接
- **ESP32-CAM / H3863**：micro-ROS，无缝接入 ROS 2 网络，星闪作为高速传输层
- **iPhone**：rosbridge，作为感知前端独立运行，不依赖 ROS 2 生态

---

# 第四章：实施阶段

## Phase 0：Ubuntu 台式机对接 Gateway

> 前置步骤，不占阶段编号。

### 目标
让 Ubuntu 台式机（5600G + 32GB + RTX 2060）作为 GPU 节点连接到 Mac Gateway，跑通节点发现→配对→执行链路。

### 硬件连接
- 有线千兆以太网（同一局域网，无需互联网）
- Mac Gateway IP：需确认（通常是 192.168.x.x）

### 配置步骤

**Step A: 获取 Gateway Token**
在 Mac 上执行：
```bash
cat ~/.openclaw/openclaw.json | python3 -c "
import json,sys
d=json.load(sys.stdin)
auth=d.get('auth',{})
print('Token:', auth.get('token','NOT_FOUND'))
"
```
记下返回的 token。

**Step B: 在 Ubuntu 上安装 OpenClaw 并启动 Node Host**
```bash
# 安装 OpenClaw（如果尚未安装）
curl -fsSL https://openclaw.ai/install.sh | bash

# 启动 node，指向 Mac Gateway
export OPENCLAW_GATEWAY_TOKEN="上面获取的token"
export OPENCLAW_GATEWAY_URL="http://192.168.x.x:18789"
openclaw node run \
  --host 192.168.x.x \
  --port 18789 \
  --display-name "Ubuntu-GPU-Node"
```

**Step C: 在 Mac Gateway 上批准配对**
```bash
openclaw devices list
# 找到 Pending 的 Ubuntu 设备
openclaw devices approve <requestId>
```

**Step D: 验证节点在线**
```bash
openclaw devices list
# 应该显示 Ubuntu-GPU-Node 状态为 online
```

**Step E: 配置 GPU 任务默认路由到该节点**
```bash
openclaw config set tools.exec.host node
openclaw config set tools.exec.node "Ubuntu-GPU-Node"
```

---

## Phase 1：语音陪伴模块

### 目标
实现基础语音交互：语音输入 → 文字 → AI 处理 → 语音输出。跑通"数字大脑→Cyber Bricks"的第一次物理输出。

### 硬件
| 设备 | 状态 | 备注 |
|------|------|------|
| Jetson Nano 2GB | 已有 | 主控 |
| USB 耳机 | 需采购 | Phase 2 一起买 |
| Cyber Bricks ×1 | 已有 | 第一个物理输出节点 |

### 软件架构

```
麦克风（USB耳机）
    ↓
Whisper（语音识别，jetson nano本地）
    ↓
OpenClaw Gateway（MacBook，贵庚大脑）
    ↓
Edge-TTS（语音合成，本地）
    ↓
扬声器（USB耳机）
```

### 实施步骤

**Step 1: Jetson Nano 系统安装**

1. 下载 JetPack 5.x 镜像（NVIDIA 官网，L4T 35.x）
2. 用 balenaEtcher 烧录 SD 卡
3. 基础配置：
```bash
# 换阿里云源（加速）
sudo sed -i 's/cn.archive.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list
sudo apt update

# 开启 SSH
sudo systemctl enable ssh
sudo systemctl start ssh

# 记录 IP
hostname -I
```

**Step 2: 音频配置**

```bash
# 查看设备
arecord -l      # 列出录音设备
aplay -l        # 列出播放设备

# USB 耳机通常是 card 1
# 创建 ~/.asoundrc 设为默认设备
cat > ~/.asoundrc << 'EOF'
pcm.!default {
  type hw
  card 1
}
ctl.!default {
  type hw
  card 1
}
EOF
```

**Step 3: 安装 Whisper 语音识别**

```bash
# 克隆 whisper.cpp
git clone https://github.com/ggerganov/whisper.cpp.git
cd whisper.cpp && make -j4

# 下载模型（base.en 最轻量，适合实时）
./models/download-ggml-model.sh base.en

# 测试
./bin/whisper-cli -m models/ggml-base.en.bin -f samples/jfk.wav
```

**Step 4: 安装 Edge-TTS 语音合成**

```bash
pip3 install edge-tts
# 测试
edge-tts --voice zh-CN-XiaoxiaoNeural --text "你好，我是贵庚" --write-media output.mp3
```

**Step 5: 编写语音对话程序**

```python
#!/usr/bin/env python3
"""语音对话主程序 - Phase 1"""
import subprocess
import edge_tts
import asyncio
import queue
import sys

# sys.path 需要加入 openclaw-bridge 路径
sys.path.insert(0, '/home/nvidia/openclaw-bridge')
from openclaw_bridge import OpenClawBridge

bridge = OpenClawBridge(gateway_url="http://192.168.x.x:18789")

async def synthesize_and_play(text):
    """文字转语音并播放"""
    communicate = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural")
    await communicate.save("/tmp/tts_output.mp3")
    subprocess.run(["aplay", "/tmp/tts_output.mp3"])

async def main():
    while True:
        # 录音 5 秒
        print("正在听...")
        subprocess.run([
            "arecord", "-d", "5", "-f", "cd",
            "-c", "1", "-r", "16000", "/tmp/input.wav"
        ])
        
        # Whisper 语音识别
        result = subprocess.run([
            "./whisper.cpp/bin/whisper-cli",
            "-m", "whisper.cpp/models/ggml-base.en.bin",
            "-f", "/tmp/input.wav",
            "--language", "zh"
        ], capture_output=True, text=True)
        
        text = result.stdout.strip()
        if not text:
            continue
            
        print(f"你说: {text}")
        
        # 发给贵庚
        response = await bridge.ask(text)
        
        # 回复语音
        print(f"贵庚: {response}")
        await synthesize_and_play(response)

asyncio.run(main())
```

---

## Phase 2：视觉记录模块

### 目标
24小时视频记录，本地处理不传云端，AI 能理解画面内容。ESP32-Cam 采集 → Jetson Nano 处理。

### 硬件
| 设备 | 状态 | 备注 |
|------|------|------|
| ESP32-Cam ×1 | 已有 | OV2640，RTSP 流 |
| Jetson Nano 2GB | 已有 | 视频处理主控 |

### ESP32-Cam 固件烧录

**硬件连接（USB转TTL）**：

| ESP32-Cam | USB-TTL |
|-----------|---------|
| GND | GND |
| 5V | 5V（注意：部分USB-TTL只有3.3V，需外接供电）|
| U0R | TX |
| U0T | RX |
| GPIO0 | GND（烧录模式，进入后断开）|

**烧录步骤**：

```bash
# 安装 esptool
pip3 install esptool

# 擦除闪存
esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash

# 下载 CameraWebServer 固件
# 从 Arduino IDE > Tools > ESP32 > Camera > AI Thinker Configuration
# 或从 https://github.com/easytarget/esp32-cam-webserver 获取

# 烧录
esptool.py --chip esp32 --port /dev/ttyUSB0 \
  write_flash 0x1000 esp32-cam-webserver.bin
```

**配置静态 IP**（在 ESP32-Cam 代码中修改）：
```cpp
// 在 camera_config_t 中设置 WiFi STA 模式 + 静态 IP
.wifi_mode = WIFI_MODE_STA,
.wifi_sta = {
    .ssid = "YOUR_WIFI_SSID",
    .password = "YOUR_WIFI_PASSWORD",
},
// 在 dhcp_config 中设置静态 IP，例如：
.ip = {.ip = {.addr =esp_ip4_addr(192,168,1,99)}},
```

### RTSP 接收（Jetson Nano）

```bash
# 安装 GStreamer
sudo apt install gstreamer1.0-tools gstreamer1.0-plugins-base \
  gstreamer1.0-plugins-good gstreamer1.0-plugins-bad

# 查看 RTSP 流（测试用）
ffplay rtsp://192.168.x.99:8554/stream

# GStreamer pipeline（更低延迟）
gst-launch-1.0 rtspsrc location=rtsp://192.168.x.99:8554/stream \
  ! decodebin ! videoconvert ! autovideosink
```

---

## Phase 3：面部表情系统

### 设计理念
0-1 的面部由「0」「-」「1」三个核心元素构成，动态显示 AI 状态。

### 系统组成

| 组件 | 形态 | 功能 |
|------|------|------|
| 「0」| LED 点阵/IPS 屏幕 | 显示主眼睛，动态表情 |
| 「-」| 线性灯光带（NeoPixel）| 情绪光效（颜色+呼吸节奏）|
| 「1」| 小型显示屏/LED | 辅助信息、状态指示 |

### 拓竹加工方案

| 零件 | 拓竹工具 | 说明 |
|------|---------|------|
| 外壳 | H2C + PLA | 面部支架，3D 打印 |
| 眼睛屏幕支架 | H2C + PETG | 耐温 |
| 透光板 | Bambu Suite 激光切割 | 亚克力 3mm |
| 安装螺丝 | 拓竹配套 M2/M3 螺丝 | 标准件 |

### 控制代码

```python
#!/usr/bin/env python3
"""0-1 面部表情控制 - Phase 3"""
from neopixel import NeoPixel
from machine import Pin
import time

N = 12  # NeoPixel 灯珠数量
pin = Pin(15, Pin.OUT)
strip = NeoPixel(pin, N)

# 表情定义（RGB 元组）
EXPRESSIONS = {
    "idle":     [(0, 50, 100)],     # 淡蓝呼吸
    "thinking": [(50, 50, 0)],       # 淡黄
    "happy":   [(0, 100, 50)],      # 绿色
    "sad":     [(30, 0, 80)],       # 淡紫
    "alert":   [(100, 0, 0)],       # 红色闪烁
}

def show_expression(name, duration=3.0):
    colors = EXPRESSIONS.get(name, EXPRESSIONS["idle"])
    for _ in range(int(duration * 10)):
        for i in range(N):
            color = colors[i % len(colors)]
            strip[i] = color
        strip.write()
        time.sleep(0.1)

# MQTT 接收表情指令
import paho.mqtt.client as mqtt

def on_message(client, userdata, msg):
    expr = msg.payload.decode()
    show_expression(expr)

client = mqtt.Client()
client.on_message = on_message
client.connect("192.168.x.x", 1883, 60)
client.subscribe("0-1/expression")
client.loop_start()
```

---

## Phase 4：运动控制模块

### 目标
OpenClaw 能通过 MQTT 发送指令到 Cyber Bricks，驱动电机/舵机执行物理动作。

### 通信架构

```
OpenClaw Gateway (MacBook)
    ↓ MQTT (QoS 1)
Jetson Nano (MQTT Broker + 指令解析)
    ↓ 有线 UART (115200)
Cyber Brick 1 (电机+舵机执行)
    ↓ 有线 UART
Cyber Brick 2 (备用)
```

### MicroPython 示例（Cyber Bricks 固件）

```python
# CyberBrick 接收 MQTT 并执行 - Phase 4
import network
import paho.mqtt.client as mqtt
from machine import Pin, PWM, UART
import ujson

# 初始化 UART（连接 Jetson Nano）
uart = UART(1, 115200, tx=Pin(4), rx=Pin(5))

# 初始化舵机
servo1 = PWM(Pin(15))
servo1.freq(50)

# 初始化电机驱动
motor_in1 = Pin(12, Pin.OUT)
motor_in2 = Pin(13, Pin.OUT)

def set_servo(angle):
    """角度转舵机 PWM 占空比"""
    duty = int(40 + angle * 95 / 90)  # 0-90度
    servo1.duty(duty)

def set_motor(speed):
    """速度 -100 到 100"""
    if speed > 0:
        motor_in1.value(1)
        motor_in2.value(0)
    elif speed < 0:
        motor_in1.value(0)
        motor_in2.value(1)
    else:
        motor_in1.value(0)
        motor_in2.value(0)

def on_message(topic, msg):
    try:
        cmd = ujson.loads(msg)
        if cmd['type'] == 'servo':
            set_servo(cmd['angle'])
        elif cmd['type'] == 'motor':
            set_motor(cmd['speed'])
        elif cmd['type'] == 'stop':
            set_motor(0)
            set_servo(90)
    except Exception as e:
        print(f"Error: {e}")

def mqtt_on_message(client, userdata, msg):
    on_message(msg.topic, msg.payload)

# 连接 WiFi
sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.connect('SSID', 'PASSWORD')
while not sta.isconnected():
    pass

# 连接 MQTT
mqtt_client = mqtt.Client()
mqtt_client.on_message = mqtt_on_message
mqtt_client.connect("192.168.x.x", 1883)
mqtt_client.subscribe("0-1/cyberbrick1")
mqtt_client.loop_start()
```

### OpenClaw → Cyber Bricks 指令脚本

```python
#!/usr/bin/env python3
"""OpenClaw 指令到 Cyber Bricks - Phase 4"""
import paho.mqtt.client as mqtt
import sys

MQTT_BROKER = "192.168.x.x"  # Jetson Nano
TOPIC = "0-1/cyberbrick1"

def send_command(action, **kwargs):
    payload = {"action": action, **kwargs}
    client = mqtt.Client()
    client.connect(MQTT_BROKER, 1883)
    client.publish(TOPIC, str(payload))
    client.disconnect()

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "stop"
    if action == "forward":
        send_command("motor", speed=50)
    elif action == "backward":
        send_command("motor", speed=-50)
    elif action == "left":
        send_command("servo", angle=45)
    elif action == "right":
        send_command("servo", angle=135)
    elif action == "stop":
        send_command("stop")
```

OpenClaw skill 示例（发送指令）：
```
用户："让 Cyber Brick 往前走"
→ 调用 exec → python3 cyberbrick_control.py forward
```

### 有线 GPIO 应急停止

```bash
# Jetson Nano 发送紧急停止信号（通过 UART 或直接 GPIO）
# 方法1: UART 发送停止命令
echo "stop" > /dev/ttyTHS1

# 方法2: GPIO 硬件中断（Jetson Nano Pin 29）
echo 29 > /sys/class/gpio/export
echo "out" > /sys/class/gpio/gpio29/direction
echo 0 > /sys/class/gpio/gpio29/value  # 继电器断开，所有电机断电
```

---

## Phase 5：iPhone 感知前端

### 目标
iPhone 16 Pro 通过 OpenClaw Node 协议接入 Gateway，成为分布式感知网络的一员，在家里移动时提供高质量视觉和传感器数据。

### iPhone 接入架构

```
iPhone 16 Pro（OpenClaw App）
    ↓ WiFi/MQTT
Gateway（MacBook）
    ↓
OpenClaw Agent（贵庚大脑）
    ↓
控制指令 → Jetson Nano / ESP32-Cam / Cyber Bricks
```

### iPhone 感知分工（与 Jetson Nano 对比）

| 任务 | iPhone 跑 | Jetson Nano 跑 | 说明 |
|------|-----------|--------------|------|
| 实时物体检测（障碍物）| **YOLOv11n Core ML** | 备用 | iPhone 节省 Jetson 算力 |
| 人体检测/跟随 | **Vision Framework** | — | 系统级，免费，极快 |
| 手势指令识别 | **MediaPipe** | — | 33关键点，秒级响应 |
| 语义场景理解 | **FastVLM 0.5B** | — | 本地 VLM，不占带宽 |
| 室内3D建模 | **LiDAR + ARKit** | 可选 | iPhone 原生支持 |
| 复杂推理/回答 | — | ✅ | 非实时，延迟可接受 |

> **技术细节**：详见第五章 5.2 节（Apple Vision / Core ML + YOLO / MediaPipe / FastVLM 完整技术方案）。

---

## Phase 6：室内移动与智能家居硬件拓展

### 目标
让 0-1 从「固定位置的机器人」变成「能在家里移动的陪伴者」，同时通过硬件拓展 kit 控制智能家居。

### 核心路线
**依赖拓竹生态 + OpenClaw，打造私人定制智能家居硬件拓展 kit。**

### 阶段一：IoT 控制现有设备（可立刻落地）

0-1 通过 WiFi/MQTT 接入现有智能家居生态（米家、涂鸦、HomeAssistant 等），实现对灯、门锁、空调等设备的语音和自动化控制。OpenClaw 作为大脑统一调度，Cyber Bricks 作为执行层。

**具体实现**：
```python
# HomeAssistant MQTT 集成
import paho.mqtt.client as mqtt

def turn_on_light(entity_id):
    """发送 MQTT 命令到 HomeAssistant"""
    client = mqtt.Client()
    client.connect("homeassistant.local", 1883)
    client.publish(
        f"homeassistant/light/{entity_id}/set",
        '{"state":"ON","brightness":255}'
    )

def auto_door_when_leaving():
    """检测到主人离家，自动锁门+关灯"""
    if presence_detected("all") == False:
        lock_door()
        turn_off_all_lights()

def auto_door_when_arriving():
    """检测到主人到家，自动开门+开灯"""
    if presence_detected("anyone") == True:
        unlock_door()
        turn_on_lights("entrance")
```

**支持的智能家居平台**：

| 平台 | 接入方式 | 说明 |
|------|---------|------|
| 米家 | 米家 MQTT Server / 小爱音箱 | 需开启 LAN 控制 |
| 涂鸦 | 涂鸦 MQTT | 需要 Tuya Cloud 配置 |
| HomeAssistant | 原生 MQTT | ✅ 推荐，本地无需云端 |
| Aqara | Zigbee2MQTT | 需要 Zigbee Hub |

### 阶段二：私人定制硬件拓展 kit（Maker 方式打造）

随着需求明确，用拓竹生态自己设计并制造专属的硬件 kit：

| kit | 拓竹工具 | 功能 |
|-----|---------|------|
| 门锁控制模组 | H2C 3D打印 + Cyber Bricks | 替代购买第三方网关，直接 UART 控制 |
| 红外/射频控制模组 | Bambu Suite 激光切割 | 控制空调/电视等红外设备 |
| 定制传感器阵列 | H2C + 杜邦线 | 特定场景感知（如花盆土壤湿度）|

**Maker 精神**：不依赖购买成品，用标准件 + 3D 打印 + 模块化电子，自己做出需要的东西。这也是 0-1 整个项目的底层逻辑——用消费级工具完成过去需要工厂才能搞定的事情。

---

星闪通信模块详见 §2.6。

---

# 第五章：AI 与感知

## 5.1 Jetson Nano 视觉感知

> ⚠️ **Jetson Nano 2GB 版本特别说明**：与 4GB 不同，2GB 必须开启 swap 才能同时跑 YOLO + MediaPipe，且 GPU 加速仅支持 FP16（Maxwell 不支持 INT8）。

> 📌 **手部与执行器设计** 详见 §2.8。

### 工具选择

| 工具 | 功能 | 适用场景 | Nano 2GB 适配 |
|------|------|---------|-------------|
| **MediaPipe** | 人体姿态、手势、面部网格 | 识别人、表情、手势指令 | ⚠️ GPU 加速不成熟，CPU版可用但慢 |
| **GStreamer** | 视频流传输 | 实时视频流 | ✅ 原生支持 |
| **YOLOv5n/v8n** | 通用物体检测 | 环境感知、导航 | ✅ TensorRT FP16 最优 |
| **OpenCV** | 图像预处理、SLAM 前期 | 相机标定、畸变校正 | ✅ 原生支持 |
| **TensorRT FP16** | YOLO 模型推理加速 | 所有 YOLO 部署 | ✅ 唯一有效加速 |
| **DeepStream** | YOLO 集成框架 | 生产级视频分析 | ⚠️ 6.x 支持 2GB，配置复杂 |

### YOLO + TensorRT FP16 部署（Nano 2GB 必读）

**Step A: 基础优化（必须开）**
```bash
# 最大性能模式
sudo nvpmodel -m 0
sudo jetson_clocks

# 添加 swap（防止 OOM）
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 降低输入分辨率：320x320 而非 640x640
```

**Step B: DeepStream 配置（2GB 极限优化）**
```ini
# /etc/deepstream-7.0/sources/configs/deepstream-app/config.txt
[property]
gpu-id=0
network-mode=2              # FP16（2GB唯一选择，INT8无加速）
batch-size=1                 # 内存最小
batched-push-timeout=40000   # 25fps
sync=0                       # 关闭显示器同步
live-source=1                # RTSP实时流必须
maintain-aspect-ratio=1
symmetric-padding=1

[source0]
enabled=1
uri=rtsp://192.168.x.99:8554/stream
type=4  # RTSP
```

### 实测 FPS（完整 pipeline，含前后处理）

| 模型 | 输入分辨率 | FPS | 说明 |
|------|----------|-----|------|
| YOLOv8n | 640x640 | ~13-16 | 推理~19FPS |
| YOLOv8n | 416x416 | ~20-25 | 降分辨率换速度 |
| YOLOv8n | 320x320 | ~35-45 | 极端优化 |
| YOLOv11n | 416x416 | ~25-35 | 最新模型 |
| YOLOv11n | 320x320 | ~50+ | 极限值 |
| YOLOv4-tiny | 416x416| YOLOv4-tiny | 416x416 | ~20-30 | 轻量老模型 |

> ⚠️ **INT4 在 Nano 2GB 上不可用**（Maxwell 架构不支持 INT8 推理加速）。**FP16 是唯一有效加速**。

### MediaPipe on Jetson Nano 2GB

**结论：GPU 加速方案不成熟，不推荐在 Nano 上跑 MediaPipe GPU。**

- Jetson Orin Nano 上 MediaPipe 手势也只有 ~5 FPS
- 替代方案：用 **TensorRT** 替代（ncnn + Vulkan 后端可用）
- 推荐：Pose/手势用 MobileNet + TensorRT FP16 替代 MediaPipe

### YOLO + MediaPipe 共存方案

| 配置 | FPS | 内存占用 |
|------|-----|---------|
| MediaPipe Pose（GPU）| ~20 FPS | ~500-800 MB |
| YOLOv5n + TensorRT FP16 | ~15-20 FPS | ~1-1.5 GB |
| **两者同时跑** | **约 10-15 FPS** | **~2.5 GB（需开swap）** |

**推荐串联架构**：
```
输入帧 → YOLOv5n 检测人体区域 → MediaPipe Pose 姿态估计
```

---

## 5.2 iPhone 感知前端技术方案

> **调研时间**：2026-03-22
> **A18 Pro NPU 基准**：Geekbench AI 量化分数 **44,672**（比 A17 Pro 高 33%）
> **技术细节来源**：zhiku(DeepSeek) + subagent × 2 + web search

### iPhone 作为 OpenClaw Node 的能力

| iPhone 能力 | 通过 OpenClaw 暴露为 | 说明 |
|------------|-------------------|------|
| 摄像头（4800万主摄）| `camera` 节点 | 实时视频流 |
| LiDAR 深度数据 | `camera.depth` 节点 | 室内3D建模、避障 |
| 四麦克风阵列 | `audio` 节点 | 远场语音采集 |
| A18 Pro NPU | 本地 LLM 推理节点 | Core ML 模型 |
| IMU 姿态 | `sensor.imu` 节点 | 6轴惯性测量 |
| UWB 定位 | `sensor.position` 节点 | 室内10-30cm精度 |

### 四平台完整对比

| 平台 | iPhone 视觉方案 | 可用性 | 推荐指数 |
|------|---------------|--------|---------|
| **Apple Vision** | `VNDetectObjectsRequest` | ✅ 最佳 | ⭐⭐⭐⭐⭐ |
| **Core ML + YOLO** | Ultralytics 导出 Core ML | ✅ 最佳 | ⭐⭐⭐⭐⭐ |
| **MediaPipe** | 谷歌全链路框架 | ✅ 推荐 | ⭐⭐⭐⭐ |
| **FastVLM（苹果官方）** | FastViTHD 视觉编码器 | ✅ 新发现 | ⭐⭐⭐ |

### A18 Pro vs A17 Pro

| 指标 | A18 Pro | A17 Pro | 提升 |
|------|---------|---------|------|
| NPU 量化分数 | **44,672** | 33,479 | +33% |
| CPU 单核 | **3376** | 2842 | +19% |
| CPU 多核 | **8219** | 7020 | +17% |

### 三大主力方案详解

#### ① Apple Vision Framework（原生免费）

| API | 功能 |
|-----|------|
| `VNDetectHumanRectanglesRequest` | 人体检测 |
| `VNDetectFaceRectanglesRequest` | 人脸检测 |
| `VNDetectBarcodesRequest` | 条码/二维码 |
| `VNRecognizeTextRequest` | 文字识别 OCR |
| `VNRecognizeObjectsRequest` | 通用物体检测（4000+类）|

```swift
// 最简人体检测代码
let request = VNDetectHumanRectanglesRequest()
let handler = VNImageRequestHandler(cvPixelBuffer: pixelBuffer)
try handler.perform([request])
```

#### ② Core ML + YOLO（通用物体检测首选）

| 模型 | A18 Pro 预估 FPS | 说明 |
|------|----------------|------|
| YOLOv11n | **40-60 FPS** | 实时检测首选 |
| YOLOv8n | **35-50 FPS** | 成熟稳定 |
| YOLOv8s | **25-40 FPS** | 速度精度平衡 |

```bash
# 一键导出 Core ML（Ultralytics 官方支持）
yolo export model=yolov11n.pt format=coreml nms=True imgsz=800
```

#### ③ MediaPipe（功能最全）

| 能力 | 推理速度 |
|------|---------|
| 物体检测 | ~0.81ms |
| 手势识别 | ~2ms（33个关键点）|
| 全身姿态 | ~5ms（33个关键点）|

#### ④ Apple FastVLM（本地 VLM）

苹果官方开源，专为 iPhone 端侧 VLM 设计：
- **0.5B 版本** 可直接在 iPhone 本地运行，无需联网
- 首字延迟比 LLaVA-OneVision **快 85 倍**（FastViTHD 视觉编码器）
- MLX 缓存：重复图像延迟从 21.7秒 → 0.78秒（28倍加速）
- Safari 网页版 Demo：实时摄像头画面 + AI 即时描述

### VLM vs YOLO：怎么选

| 维度 | YOLO（目标检测）| VLM（视觉语言模型）|
|------|----------------|------------------|
| 输出 | 边界框 + 类别 | 文字描述 |
| 速度 | ⚡ 毫秒级（40-60 FPS）| 秒级（TTFT 1秒）|
| 精度定位 | ✅ 高精度边界框 | ❌ 无法输出精确坐标 |
| 泛化能力 | 受限训练集 | 理解任意场景 |

**推荐分层架构**：
```
iPhone 摄像头
    ↓
YOLOv11n（Core ML）→ 实时物体检测 → Jetson Nano 运动控制
    ↓
FastVLM 0.5B → 语义理解 → 贵庚大脑
```

### Camera Control 按钮可行性

| 交互 | 可行性 | 说明 |
|------|--------|------|
| 短按触发拍照 | ✅ 可行 | 通过 AssistiveTouch 映射 |
| 长按持续录制 | ✅ 可行 | BLE 通知触发 |
| 滑动调节速度 | ✅ 可行 | 电容感应可区分按压面积 |
| 深度 API 控制 | ❌ 受限 | Apple 未开放硬件级 API |

### LiDAR 导航：ARKit vs 传统 SLAM

| 方案 | 适合场景 | iPhone 接口 |
|------|---------|------------|
| ARKit 路径记忆 | 室内固定路线 | 直接用 |
| RoomPlan API | 自动生成 3D 房间模型 | CAD 导出 |
| RTAB-Map | 室内建图+导航 | iOS 端口可用 |
| ORB-SLAM3 | 室外/室内通用 | 有 iOS 版本 |

**最佳实践**：iPhone 做感知前端（摄像头/LiDAR/IMU）→ WiFi 传输数据 → Jetson 跑 SLAM 算法。

---

## 5.3 物理仿真引擎：Genesis 与 Newton

> ⚠️ **名称区分**：
> - **Genesis** = Apple 团队开源的独立物理引擎（2025-02），GTX 1080 6GB 可跑
> - **Newton** = NVIDIA + DeepMind + Disney 联合开发的另一套引擎（2025-03 GTC），GPU 加速，与 Isaac Lab 官方生态集成
> - 两者是**不同的独立项目**，本节分别说明。

### Genesis 物理引擎（Apple 开源，2025-02）

> **调研时间**：2026-03-22
> **来源**：Genesis GitHub + 官方文档
> **最新动态**：最新版本 v0.4.0（2026-02-17），GitHub Stars 28,318

### Genesis vs Isaac Gym 完整对比

| 对比维度 | Genesis | Isaac Gym |
|----------|---------|-----------|
| 定位 | 通用具身智能/生成式仿真 | 工业级数字孪生 |
| 物理引擎 | 自研多求解器（刚体/MPM/SPH/FEM/PBD）| PhysX 5.1 (GPU) |
| 渲染 | 光线追踪 + 光栅化 | RTX 光线追踪（Omniverse USD）|
| GPU要求 | **GTX 1080 6GB 起**，支持 AMD/Apple Metal/CPU | 必须 NVIDIA RTX 8GB+ |
| ROS支持 | ❌ 无原生集成 | ✅ ROS2 Bridge 开箱即用 |
| 学习曲线 | **低**（pip 安装，Gym 风格 API）| 高（需掌握 USD/Omniverse）|
| 速度 | **43M FPS**（RTX 4090）| 100+ 智能体并行 |

> **对 0-1 的意义**：数字孪生训练的硬件门槛从 Isaac Gym 的 RTX 3090+ 降到 **GTX 1080 6GB**，现有台式机（RTX 2060 6GB）就能用。

### Genesis 最新功能（2026年以来）

| 日期 | 新增功能 |
|------|---------|
| 2026-02-17 | 最新版本 v0.4.0，GitHub 持续活跃更新（28,318 Stars）|
| 2026-03-16 | ProximitySensor、TemperatureGridSensor、GPU碰撞检测提速30% |
| 2026-03-13 | FOTS触觉传感器、异构机器人并行仿真 |
| 2026-02-18 | **Quadrants编译器**正式迁移、AMD ROCm实验性支持 |
| 2026-02-10 | 交互查看器插件机制、glTF/USD支持 |

### Genesis 快速入门

```python
import genesis as gs

# 创建仿真环境
env = gs.gym.create_env()
robot = gs.robot.Robot("/path/to/robot.urdf")

# 强化学习训练循环
for step in range(10000):
    action = policy(robot.get_state())
    robot.set_control(action)
    env.step()
    if step % 1000 == 0:
        print(f"Step {step}, Reward: {reward}")
```

---

### Newton 物理引擎（NVIDIA + DeepMind + Disney，2025-03 GTC）⭐⭐⭐⭐⭐

**发布时间**：2025-03-18（NVIDIA GTC）
**合作方**：NVIDIA + Google DeepMind + Disney Research，Linux Foundation 管理
**GitHub**：https://github.com/newton-physics/newton
**集成**：已集成至 NVIDIA Isaac Lab

#### 技术架构

| 底层技术 | 说明 |
|---------|------|
| **NVIDIA Warp** | Python 框架，构建和加速仿真/空间计算，CUDA 级别性能 |
| **OpenUSD** | 聚合机器人及环境数据的描述框架 |
| **MuJoCo Warp** | NVIDIA GPU 优化版 MuJoCo，Newton 核心求解器 |
| **Disney 引擎技术** | 针对机器人学习优化的物理引擎技术 |

#### 关键特性

| 特性 | 说明 |
|------|------|
| **GPU 加速** | CUDA 级别性能，无需底层编码，仿真从"天"加速到"分钟" |
| **可微分** | 支持梯度计算，加速训练、设计优化、系统识别 |
| **可扩展** | 通过插件支持多物理场仿真 |
| **与 Isaac Lab 兼容** | 可直接替换 Isaac Sim 中的仿真后端 |
| **与 MuJoCo Playground 兼容** | DeepMind 的 MuJoCo 强化学习环境可直接使用 |

#### Genesis vs Newton 怎么选

| 对比项 | **Genesis**（Apple）| **Newton**（NVIDIA）|
|--------|-------------------|-------------------|
| 发布时间 | 2025-02 | 2025-03 GTC |
| 资源需求 | GTX 1080 6GB | RTX 3060+ |
| GPU 加速 | 有 | 有（CUDA 级别）|
| 生态集成 | 独立开源 | Isaac Lab 官方集成 |
| 适用场景 | 入门、低成本 | 高精度工业仿真 |

#### 对 0-1 的建议

```
阶段一（Genesis）：低成本入门，GTX 1080/RTX 2060 可跑
阶段二（Newton）：高精度仿真，与 Isaac Lab / GR00T 生态集成
```

---

## 5.4 具身大脑基模：RynnBrain 与空间智能

> **调研时间**：2026-03-24 | 来源：阿里巴巴达摩院官方 + 多源搜索验证
>
> **背景**：0-1 的"大脑"不仅需要语言理解和记忆，还需要**理解物理空间、执行长时序任务**。两个 2026 年最新开源成果直接解决这两个问题。

### RynnBrain（阿里巴巴达摩院，2026-02-10 开源）

**官网**：`alibaba-damo-academy.github.io/RynnBrain.github.io/`
**开源协议**：Apache 2.0（可商用）

#### 发布模型（全系列）

| 模型 | 规格 | 核心用途 |
|------|------|---------|
| RynnBrain-2B | 密集，2B 参数 | 轻量具身推理 |
| RynnBrain-8B | 密集，8B 参数 | 中等任务 |
| **RynnBrain-30B MoE** | 总30B，激活约3B | 复杂任务（主力） |
| **RynnBrain-Plan** | 专用 | 机械臂操作规划 |
| **RynnBrain-Nav** | 专用 | 室内导航（自然语言指令）|
| **RynnBrain-CoP** | 专用 | 空间推理 |

#### 核心能力（官方 Demo 验证）

| 能力 | 说明 | 对 0-1 的价值 |
|------|------|--------------|
| **时空记忆** | 记住物体在全局历史中的位置和轨迹，支持回溯 | ✅ 解决"转身就忘"的痛点 |
| **物理空间推理** | 文本+空间坐标交织，减少幻觉 | ✅ 动作规划更贴合实际 |
| **Affordance 感知** | 理解物体"可以用来做什么" | ✅ 提升操作成功率 |
| **长时序规划** | 100步+任务完成率 88% | ✅ 复杂家务不中断 |
| **零样本适配** | 未知环境成功率 94% | ✅ 新家庭开箱即用 |
| **INT4 量化** | 边缘硬件可跑 | ✅ Jetson Orin NX 实时推理 |

#### 端侧部署实测

- **Jetson Orin NX**：推理延迟 <20ms（INT4 量化）
- **Benchmark**：16项具身榜单 SOTA，超越谷歌 Gemini Robotics ER 1.5 + NVIDIA Cosmos-Reason2
- **落地数据**：5000+ 家庭部署，任务切换效率 +65%，异常处理成功率 92%

#### 对 0-1 的直接价值

```
0-1 大脑架构建议（整合 RynnBrain）：
├─ 贵庚（记忆 + 对话）
├─ RynnBrain-30B MoE（任务规划 + 物体记忆）
├─ RynnBrain-Nav（室内导航）
└─ RynnBrain-Plan（操作序列生成）
```

---

### 李飞飞空间智能（World Labs）

**公司**：World Labs（2024年创办，a16z 领投 $230M，估值超 $1B）
**官网**：`www.worldlabs.ai`

#### 核心研究方向

| 成果 | 技术 | 对 0-1 的价值 |
|------|------|--------------|
| **3D 世界生成** | 单图生成可交互 3D 场景（NeRF/3DGS）| 新家庭快速建图 |
| **PointWorld** | 单 RGB-D → 模拟 10 步关节动作 | 无需预训练即可操作新物体 |
| **Physical AI** | 物体运动学/碰撞/轨迹定量推理 | 预判动作后果，避免打碎物品 |
| **BRS 家机器** | 成本 <$500 双臂机器人 | 低成本硬件参考 |

#### 3D Gaussian Splatting（3DGS）：空间智能的重建底座 ⭐⭐⭐⭐⭐

> **补充时间**：2026-03-24 | **来源**：arXiv + GitHub + 多源搜索验证
>
> World Labs 的 3D 世界生成底层依赖 3DGS（3D Gaussian Splatting）技术。3DGS 自 SIGGRAPH 2023 提出后，在机器人领域快速拓展，**对 0-1 的价值超出预期**。

**核心原理**：用数百万个 3D 高斯椭球表示空间，每个高斯含位置/形状/颜色/不透明度，通过可微分光栅化渲染，比 NeRF 快 100 倍以上（1080p @ 100+ FPS）。

##### 核心优势对比

| 指标 | NeRF | **3DGS** |
|------|------|---------|
| 训练时间 | 数小时~数天 | **35-45 分钟** |
| 1080p 渲染 | ~10 FPS | **100+ FPS** |
| 场景表示 | 隐式（神经网络）| **显式（高斯点云）** |
| 编辑/控制 | 困难 | **容易**（可编辑单个高斯）|

##### 主要应用方向

**① 实时高保真 3D 建图（LangSplat）** ⭐⭐⭐⭐⭐

GitHub：https://github.com/minghanqin/LangSplat（CVPR 2024 Highlight）

将 CLIP 视觉语言特征注入 3DGS，实现**开放词汇语义查询**：
```
用户语音："去沙发旁边那个小边几上拿我的药"
↓
LangSplat 自然语言查询："沙发" + "边几" + "药" → 3D 坐标
↓
0-1 导航到该位置 → 抓取
```
优势：不需要预定义物体类别，直接用自然语言搜索任意物体。

**② Real2Sim 仿真训练（RoboGSim）** ⭐⭐⭐⭐⭐

论文：arXiv:2411.11839，https://robogsim.github.io/

Pipeline：
```
① 手机拍摄机器人工作区 → 3DGS 高保真重建
② 数字孪生构建（Scene Composer 编辑场景）
③ 在仿真中批量生成合成数据（1000+ 条）
④ 训练机械臂策略 → 零样本迁移到真实机器人
```
关键结果：在仿真数据上训练的模型，新场景下**优于真实数据训练的模型**，解决真实数据采集成本高、场景单一的问题。

**③ 物理仿真 + 精细操作（Physical AI）**

3DGS 高斯可绑定物理引擎参数（摩擦力、形变阈值），实现：
- 机械臂抓取路径仿真（精度 0.1mm）
- 软体操作（收拾衣物、整理桌面）
- 仿真中测试 100 种抓取路径 → 选择最优下发执行

##### 关键开源项目

| 项目 | 链接 | 算力需求 | 对 0-1 价值 |
|------|------|---------|-------------|
| **LangSplat** | https://github.com/minghanqin/LangSplat | RTX 3060+ | ⭐⭐⭐⭐⭐ 语义建图 |
| **RoboGSim** | https://robogsim.github.io/ | RTX 4090（训练）| ⭐⭐⭐⭐⭐ Real2Sim 仿真 |
| **MonoGS** | https://github.com/muskie82/MonoGS | RTX 3060+ | ⭐⭐⭐ 单目 SLAM |
| **SplaTAM** | https://github.com/spla-tam/SplaTAM | RTX 4090 | ⭐⭐⭐ RGB-D SLAM |

##### 硬件算力门槛（对 0-1 的意义）

| 任务 | 算力需求 | 0-1 当前硬件 | 可行性 |
|------|---------|-------------|--------|
| **3DGS 场景重建**（训练）| RTX 3060+（30 分钟）| 台式机 RTX 2060 ✅ | ✅ **完全可以** |
| **LangSplat 语义查询** | RTX 3060+ | 台式机 RTX 2060 ✅ | ✅ 可行 |
| **RoboGSim 仿真训练** | RTX 4090（最佳）| RTX 2060 ⚠️ | ⚠️ 可行但慢 |
| **3DGS 实时 SLAM** | Jetson Orin NX+ | Jetson Nano 2GB ❌ | ❌ 算力不足 |

结论：**场景重建和语义建图在台式机 RTX 2060 上完全可行**，实时 SLAM 需要 AGX Thor 级别。

##### 3DGS 与 PointWorld / Genesis 的分工

| 技术 | 角色 | 输入 | 输出 |
|------|------|------|------|
| **3DGS** | 场景重建（真实纹理）| 手机绕拍视频 | 高保真 3D 点云 |
| **PointWorld** | 物理预测（物体运动）| RGB-D + 动作序列 | 动作效果预测 |
| **Genesis** | 物理引擎（无纹理仿真）| 物理参数 | 碰撞/动力学结果 |

三者互补关系：
```
PointWorld（预测）+ Genesis（物理）→ 机器人动作规划
3DGS（重建）→ 真实环境数字孪生
PointWorld + 3DGS → 在真实场景中做动作预测
```

#### 对 0-1 的中期价值

- **3D 空间建模**：让机器人在进入新家庭时，用单张 RGB-D 快速构建 3D 语义地图，无需预训练
- **物理推理预演**：执行"拿起水杯"前，先在数字孪生中模拟轨迹，避免碰倒花瓶
- **低成本感知**：单 RGB-D 相机（ESP32-Cam 可用）即可实现 3D 感知，降低硬件成本

---

### 技术路线建议（0-1 如何整合）

| 时间 | 行动 | 技术来源 |
|------|------|---------|
| **现在** | 接入 RynnBrain-30B-MoE 作为任务规划核心 | RynnBrain 开源 |
| **现在** | 用 RynnBrain-Nav 替代/补充现有导航方案 | RynnBrain 开源 |
| **中期** | 引入 PointWorld 做新环境零样本建图 | World Labs |
| **中期** | 接入 3D 世界模型做物理推理预演 | World Labs |
| **长期** | 自有数据积累后，微调 RynnBrain 基座 | RynnBrain Apache 2.0 |

---

### Isaac GR00T N1.6：NVIDIA 视觉-语言-动作基础模型 ⭐⭐⭐⭐⭐

> **补充时间**：2026-03-24 | **来源**：NVIDIA 官方 + Hugging Face
>
> GR00T N1.6 是 NVIDIA 官方开源的**具身机器人 VLA（Vision-Language-Action）基础模型**，在宇树 G1 等真实机器人上验证过，与 0-1 的 Cyber Bricks 潜在兼容。

**开源**：Hugging Face（已上线 `nvidia/GR00T-N1.6-3B`）
**GitHub**：https://github.com/NVIDIA/Isaac-GR00T

#### 模型架构

| 组件 | 说明 |
|------|------|
| **Base VLM** | NVIDIA Cosmos-2B 变体，支持灵活分辨率，原生长宽比无 padding |
| **DiT** | 32 层（比 N1.5 的 16 层大一倍）|
| **动作预测** | 状态相对动作分块（state-relative action chunk），而非绝对关节角度 |

#### 预训练数据（关键！）

GR00T N1.6 预训练数据新增包含以下真实机器人数据：
- **宇树 G1 全身运动操作数据**（✅ 已在真实机器人验证）
- 智元机器人 AgiBot Genie-1 双手操作数据
- Bimanual YAM 双臂遥操作数据

#### 对 0-1 的关键价值

**GR00T N1.6 已在宇树 G1 上验证** → Cyber Bricks 作为宇树同源架构，动作空间**可能兼容**：

```
0-1 建议架构（整合 GR00T）：
├─ GR00T N1.6（任务规划 + 视觉理解 + 全身协调）
├─ Cyber Bricks（执行层，电机控制）
└─ RynnBrain-30B（记忆 + 对话管理）
```

| 对比项 | RynnBrain | GR00T N1.6 |
|--------|----------|-------------|
| 定位 | 任务规划 + 导航 + 物体记忆 | 视觉-语言-动作统一模型 |
| 硬件验证 | Jetson Orin NX | **宇树 G1 真实机器人** ✅ |
| 动作输出 | 生成操作序列 | 直接输出关节动作 |
| 数据来源 | 阿里达摩院 | NVIDIA + 多家机器人公司 |

**硬件需求**：预训练需要高端 GPU，但微调和推理可在 **AGX Orin 64G** 上进行。

---


# 第六章：本地 LLM 推理

## 6.1 推理框架对比

| 框架 | RTX 2060 (Turing) | AMD AI Halo (Strix Halo) | OpenClaw 支持 |
|------|-------------------|--------------------------|---------------|
| **vLLM** | ✅ 支持，AWQ/GPTQ 量化 | ✅ ROCm v0.14.0+ 一等公民 | ✅ OpenAI-compatible API |
| **TensorRT-LLM** | ✅ 支持，INT4/INT8（复杂）| ❌ NVIDIA 专有 | ❌ 不支持 |
| **Ollama** | ✅ 推荐，Q4_K_M 最优 | ✅ ROCm/Vulkan | ✅ 原生集成（推荐）|
| **LM Studio** | ✅ CUDA | ✅ ROCm | ✅ **AMD 官方推荐** |
| **SGLang** | ❌ 不推荐 | ✅ ROCm 原生，复杂 Agent 任务 | ✅ OpenAI-compatible API |
| **AMD Quark** | ❌ 不适用 | ✅ 官方量化工具 | ❌ 不支持 |
| **RyzenClaw/RadeonClaw** | ❌ 不适用 | ✅ **AMD 官方方案** | ✅ 官方适配 |

### RTX 2060 量化方案

| 量化级别 | 7B-8B 模型显存占用 | 推荐度 | 说明 |
|---------|-----------------|-------|------|
| **Q4_K_M** | **~4.5 GB** | ⭐⭐⭐⭐⭐ | 首选，精度/速度/显存最佳平衡 |
| Q5_K_M | ~5.5 GB | ⭐⭐⭐⭐ | 精度更高，显存接近极限 |
| Q8_0 | ~7.5 GB | ❌ | 超出 6GB，无法纯 GPU 运行 |
| FP16 | ~16 GB | ❌ | 无法运行 |

**推荐组合**：Ollama + GGUF (Q4_K_M) + Qwen2.5-7B/Instruct

```bash
# 一键安装
curl -fsSL https://ollama.com/install.sh | sh
# 运行量化模型
ollama run qwen2.5:7b-instruct-q4_K_M
```

### ROCm 对 AMD AI Halo 128GB 的支持

| ROCm 版本 | 支持状态 | 说明 |
|-----------|---------|------|
| ROCm 6.x | ❌ **不支持** | gfx1151 (RDNA 3.5) 不在 6.x 官方支持列表 |
| **ROCm 7.0+** | ✅ **官方支持** | 正式支持 Strix Halo (gfx1151)，集成 rocWMMA |
| **ROCm 7.2.2** | ✅ **推荐版本** | CES 2026 发布，Day-0 优化支持 |
| ROCm 7.9 (nightly) | ✅ 实验性 | 897 tokens/s (Qwen3-30B 提示词处理) |

**性能数据**（llama.cpp, Qwen3-30B, 2048 tokens 上下文）：
- Vulkan 后端：~412 tokens/s
- ROCm 7.0.2 + ROCm 后端：**876.9 tokens/s** (+112%)

### vLLM ROCm 支持（v0.14.0+）

| vLLM 版本 | ROCm 支持 | 说明 |
|-----------|----------|------|
| v0.12.0 / v0.13.0 | ✅ 一等公民 | AITER 内核、FP8 量化、DeepSeek MoE 优化 |
| **v0.14.0** | ✅ **推荐版本** | 官方 Docker 镜像/wheel，一键安装 |
| v0.15.0+ | ✅ 持续优化 | 继续增强 RDNA 支持 |

**推荐部署**：使用官方 Docker `vllm/vllm-openai:v0.14.0-rocm`

### SGLang ROCm 支持

- 原生支持 AMD Instinct MI300X/MI355X，RDNA 系列通过标准 ROCm 栈运行
- 支持 FP8、AWQ 量化（通过 Triton/AITER 加速）
- 适合复杂 Agent 任务（结构化输出、多轮对话）

**启动示例**：
```bash
SGLANG_USE_AITER=1 python3 -m sglang.launch_server --model <model> --quantization awq
```

---

## 6.2 NemoClaw — NVIDIA 官方 OpenClaw 优化

**NemoClaw** 是 NVIDIA GTC 2026 为 OpenClaw 定制的官方软件栈（黄仁勋发布）：

| 特性 | 说明 |
|------|------|
| **OpenShell** | 安全沙箱，限制 AI 权限（防恶意操作）|
| **隐私路由器** | 敏感数据本地处理，按需调用云端 |
| **安全护栏** | 企业级合规性，AI 无法同时上网+读写文件+执行代码 |
| **一键安装** | 简化 OpenClaw 部署 |

> **对贵庚的影响**：企业级安全护栏 → OpenClaw 可进入生产环境

---

## 6.3 AMD 官方 OpenClaw 方案

> **来源**：AMD 官方技术博客（2026-03-13）
> **链接**：[Run OpenClaw Locally On AMD Ryzen AI Max+ Processors and Radeon GPUs](https://www.amd.com/en/resources/articles/run-openclaw-locally-on-amd-ryzen-ai-max-and-radeon-gpus.html)

### RyzenClaw & RadeonClaw 硬件对比

| 方案 | RyzenClaw | RadeonClaw |
|------|-----------|------------|
| **硬件** | AMD Ryzen AI Max+ 395 | AMD Radeon AI PRO R9700 |
| **形态** | 笔记本/迷你主机（FP11） | 桌面独立显卡 |
| **GPU** | 40 CU RDNA 3.5 | 32GB GDDR6 |
| **统一内存/显存** | 128GB LPDDR5X（可划96GB为VRAM）| 32GB GDDR6 |
| **NPU 算力** | **50 TOPS**（XDNA 2）| — |
| **内存带宽** | 256 GB/s | — |

### Ryzen AI Max+ 395 完整规格

| 项目 | 规格 |
|------|------|
| 核心/线程 | 16核 / 32线程（Zen 5，4nm）|
| 频率 | 基准 3.0GHz / 加速 5.1GHz |
| 缓存 | L2 16MB + L3 64MB = **80MB** |
| TDP | 55W（cTDP 45-120W）|

### 性能数据（Qwen 3.5 35B A3B 模型）

| 性能指标 | RyzenClaw | RadeonClaw |
|-----------|-----------|------------|
| **生成速度** | 45 tokens/s | 120 tokens/s |
| **最大上下文** | **260K tokens** | 190K tokens |
| **并发智能体** | **6 个** | 2 个 |

---

## 6.4 各硬件能跑的模型

| 硬件 | 能跑的模型 | 量化方案 |
|------|---------|---------|
| RTX 2060 6GB | Qwen2.5-7B Q4_K_M / Qwen3.5-4B Q4_K_M | GGUF Q4_K_M（~4.5GB）|
| RTX 2060 6GB | Gemma 2B / YOLO 系列 | FP16 |
| AMD AI Halo 128GB | Qwen3.5-122B（4-bit 需 ~70GB）| AWQ/GPTQ |
| AMD AI Halo 128GB | LLaMA 70B / Mistral 70B | FP16 直接跑 |
| DGX Spark 128GB | 200B 参数模型（统一内存）| FP16 |

---

## 6.5 机器人技能训练：从模仿学习到自主泛化

> ⚠️ **0-1 当前状态**：文档完全没有描述"如何让机器人学会新任务"。这是具身智能的核心能力，必须补充。

#### 行业现状

| 厂商 | 训练方式 | 特点 |
|------|---------|------|
| Tesla | **模仿学习 + 端到端 FSD** | 看人类演示15分钟即可学会新任务，复用 FSD 神经网络 |
| Boston Dynamics | **Orbit 平台一键部署** | 单机学会新技能后，一键同步到整个 fleet |
| Figure AI | **端到端神经网络** | 完全自主，不依赖预编程 |
| 智元机器人 | **GO-1 通用具身基座模型** | 跨场景多任务执行，开源 |
| 宇树 | **强化学习（RL）** | 强化学习驱动程序，后空翻、侧空翻等高难度动作 |

#### 三种主要训练范式

**1. 模仿学习（Imitation Learning）**——最适合 0-1 阶段一

原理：人类通过 VR 手柄/外骨骼/视觉示范动作，机器人观察学习。

```
人类示范（VR手柄/动作捕捉）→ 机器人观察 → 神经网络学习映射 → 机器人复制动作
```

优点：样本效率高（15-30分钟学会新任务），不需要从头强化学习
缺点：泛化能力有限，新场景需要额外数据

工具：
- **Rematrix VR 手柄**（参考方案）：¥200-500，通过 VR 手柄记录6DOF姿态
- **Kinect / iPhone LiDAR**：捕捉人体姿态，成本极低
- **遥操作演示**：直接用键盘/手柄控制机器人，记录动作序列

**2. 强化学习（Reinforcement Learning）**——适合运动技能

原理：在仿真环境（isaac sim / PyBullet）中训练，迁移到真实机器人。

```
仿真环境（数字孪生）→ 强化学习训练 → sim-to-real 迁移 → 真实机器人部署
```

优点：可探索极端动作（空翻、跌倒恢复），安全无风险
缺点：sim-to-real 差距大，需要大量工程调参
适用场景：运动技能（行走、跑步、翻身）

工具：
- **NVIDIA Isaac Gym**（参考）：GPU 加速 RL 训练，宇树等厂商使用
- **PyBullet**（开源）：入门级仿真环境
- **MJX（MuJoCo）**：学术界标准，刚被 DeepMind 开源

**3. 端到端神经网络（End-to-End）**——Tesla/Figure 路线

原理：直接从传感器（摄像头/触觉）到动作输出，不用中间表示。

```
视觉输入 → 端到端 NN → 动作输出（关节扭矩/位置）
```

优点：无需手工设计特征，泛化能力强
缺点：需要海量数据（Tesla 用 FSD 数据飞轮），算力要求极高
适用场景：通用家庭机器人（Figure 03、Tesla Optimus）

**4. 3DGS 仿真数据生成（RoboGSim）**——解决数据不足的关键方案

原理：用 3D Gaussian Splatting 重建真实场景，在仿真中批量生成合成动作数据。

```
① 手机拍摄任务场景 → 3DGS 高保真数字孪生
② 在仿真中添加/删除/移动物体，修改光照
③ 批量生成 1000+ 条合成动作数据
④ 在仿真中训练机器人策略
⑤ sim-to-real 迁移到真实 Cyber Bricks
```

优点：
- 数据量可无限扩展（不受真实采集成本限制）
- 可控制场景变量（光照/物体材质/遮挡程度）
- 在仿真中训练的模型，新场景下表现**优于真实数据训练的模型**
- 解决 0-1 最大痛点：Cyber Bricks 真实数据采集成本高

缺点：
- 需要 RTX 4090 最佳（RTX 2060 凑合但慢）
- sim-to-real 纹理迁移仍有少量差距

关键项目：
- **RoboGSim**（https://robogsim.github.io/）：完整 Real2Sim2Real Pipeline，arXiv:2411.11839

#### 0-1 分阶段训练方案

**阶段一（模仿学习为主）**

目标：让机器人学会日常任务（递东西、倒水、收拾桌面）

工具链：
1. 用键盘/手柄遥操作记录动作序列（成本 ¥0）
2. 用 Python 脚本将动作序列转为标准化格式
3. 用小模型（如 Qwen2.5-7B）做动作理解 + 规划
4. 通过 MQTT 下发动作指令到 Cyber Bricks

关键限制：Cyber Bricks 只有基础舵机，无触觉传感，精细操作受限

**阶段二（强化学习补充）**

目标：学会运动技能（行走恢复、跌倒站起、上下楼梯）

工具链：
1. 在 PyBullet/MJX 中建立 Cyber Bricks 仿真模型
2. 用 PPO 算法训练运动策略
3. Sim-to-real 迁移（可能需要 domain randomization）
4. 部署到真实 Cyber Bricks

**阶段三（端到端 AI）**

目标：通用家庭服务能力（类 Figure 03 / Optimus）

工具链：
1. 收集家庭场景真实数据（视觉 + 动作配对）
2. 用多模态大模型（如 LLaVA/Qwen-VL）做视觉-语言-动作对齐
3. 部署到 AGX Thor 或 AI Halo（算力要求高）

#### 关键问题：数据从哪来？

| 数据来源 | 方式 | 成本 | 质量 |
|---------|------|------|------|
| **遥操作演示** | 人工控制，记录动作 | ¥0 | 高（人工筛选）|
| **视频数据** | YouTube/互联网大规模视频 | 低 | 中（需要过滤）|
| **仿真生成** | NVIDIA Isaac Gym / Genesis | 高（GPU 算力）| 中（sim-to-real 差距）|
| **3DGS 仿真数据** | RoboGSim 手机拍摄 → 数字孪生 → 批量生成 | 中（¥0 硬件）| 高（真实纹理）|
| **Cosmos 合成数据** | NVIDIA Cosmos Predict 2.5 生成无限合成动作视频 | 中（GPU 算力）| 中（需要 sim-to-real 校准）|
| **15TB 物理 AI 数据集** | NVIDIA 开源 32 万条机器人轨迹 + 1000+ OpenUSD 场景 | **免费** | 高（真实+仿真混合）|
| **真实机器人采集** | 在家中边用边采集 | 中 | 高（真实场景）|

0-1 推荐：**遥操作 + RoboGSim 3DGS + Cosmos（远期）+ 15TB 数据集预训练 + 阶段三积累真实数据**

> 💡 **15TB 物理 AI 数据集（NVIDIA，Hugging Face）**：
> - 32 万条机器人轨迹，15TB 总规模
> - Hugging Face 下载量 480 万次
> - 宇树 G1 数据在预训练中 → Cyber Bricks 可受益
> - 下载：https://huggingface.co/collections/nvidia/physical-ai-67c643edbb024053dcbcd6d8

#### 参考项目

| 项目 | 链接 | 说明 |
|------|------|------|
| **RoboGSim** | https://robogsim.github.io/ | Real2Sim2Real 仿真训练，3DGS + 物理引擎 |
| **LangSplat** | https://github.com/minghanqin/LangSplat | 3DGS 语义建图，自然语言查询物体 |
| **MonoGS** | https://github.com/muskie82/MonoGS | 3DGS 单目 SLAM，CVPR 2024 |
| **Genesis** | https://github.com/applecartn/genesis | 物理引擎，GTX 1080 6GB 可跑 |
| **智元 GO-1** | GitHub: open-agibot/go1-sim | 通用具身基座模型，Apache 2.0 |
| **ALOHA** |斯坦福开源| 低成本遥操作硬件（¥2000），模仿学习 |
| **DexCap** |斯坦福开源| SLAM-cap 数据采集手套，精细操作数据 |
| **RT-1** | Google Robotics | 视觉-语言-动作端到端模型 |
| **Octo** | 伯克利开源 | 开源机械臂基础模型 |

---

# 第七章：附录

## A.X 关键开源项目参考

> 本节汇总与 0-1 直接相关的开源硬件/软件项目，供快速查找。优先使用国产精品。

### 机器人硬件

| 项目 | 描述 | GitHub / 链接 | 对 0-1 价值 |
|------|------|---------------|-------------|
| **Dummy-Robot**（稚晖君）| 迷你机械臂，CAN 总线 + 正逆解 + 三指令模式 + 上位机全开源 | https://github.com/peng-zhihui/Dummy-Robot | ⭐⭐⭐⭐⭐ 最高优先级，CAN 总线方案可直接借鉴 |
| **CycloidAcuratorNano**（稚晖君）| 自制摆线针轮减速器，3D 打印即可制作 | https://github.com/peng-zhihui/CycloidAcuratorNano | ⭐⭐⭐⭐ 低成本高精度关节，Cyber Bricks 升级路径 |
| **XDrive**（unlir）| 开源步进电机闭环驱动，STM32 + CAN，支持力矩/速度/位置 | https://github.com/unlir/XDrive | ⭐⭐⭐⭐ Dummy 机械臂同款驱动，可直接使用 |
| **哪吒机器人**（稚晖君）| 双足机器人，49 DOF，12 DOF 手部 | — | ⭐⭐⭐ DOF 分配参考 |
| **启元 Q1**（智元机器人）| 全球首款全身力控小尺寸人形机器人 | — | ⭐⭐⭐ 小型人形参考，"探索者计划"可加入 |
| **Cyber Bricks**（拓竹）| 四足 + 机械臂套件，ESP32 + 电机 | 拓竹官方 | ✅ 0-1 当前执行器基础 |
| **Cyber Tank**（拓竹）| 坦克底盘，Cyber Bricks 升级版 | 拓竹官方 | ⭐⭐ 移动底盘备选 |

### 机器人软件

| 项目 | 描述 | GitHub / 链接 | 对 0-1 价值 |
|------|------|---------------|-------------|
| **AgiBot World**（智元）| 百万真机数据集，覆盖 5 大场景，比 Open X-Embodiment 大 10 倍 | https://opendatalab.com/OpenDriveLab/AgiBot-World/download | ⭐⭐⭐⭐⭐ 预训练数据来源 |
| **GO-1**（智元）| 通用具身基座模型，跨场景多任务，Apache 2.0 | GitHub: open-agibot/go1-sim | ⭐⭐⭐⭐ 具身智能基座模型 |
| **AimRT**（智元）| 高性能机器人中间件，比 ROS2 更轻量 | GitHub: Agibot/AimRT | ⭐⭐⭐⭐ AGX Thor / AI Halo 部署时替代 ROS2 |
| **Genesis** | 物理引擎，GTX 1080 6GB 可跑，比 Isaac Sim 快 10-80 倍 | https://github.com/applecartn/genesis | ⭐⭐⭐⭐⭐ 仿真训练 |
| **Octo**（伯克利）| 开源机械臂基础模型 | https://github.com/octo-octo/octo-model | ⭐⭐⭐ 机械臂基础模型 |
| **ALOHA**（斯坦福）| 低成本遥操作硬件（¥2000），模仿学习 | — | ⭐⭐⭐ 遥操作训练参考 |
| **RT-1**（Google）| 视觉-语言-动作端到端模型 | — | ⭐⭐⭐ 端到端参考 |
| **RynnBrain**（阿里）| 30B MoE + Plan/Nav/CoP，Apache 2.0 | — | ⭐⭐⭐ 任务规划大脑 |

### 固件 / 驱动

| 项目 | 描述 | GitHub / 链接 | 对 0-1 价值 |
|------|------|---------------|-------------|
| **Dummy 固件**（稚晖君）| FreeRTOS + C++11，CAN 通信，3 种指令模式，零点校准算法 | https://github.com/peng-zhihui/Dummy-Robot | ⭐⭐⭐⭐⭐ CAN 通信和运动学算法可直接移植 |
| **ESP32-RACING** | ESP32 电机驱动固件，CAN 总线 | — | ⭐⭐⭐ Cyber Bricks 固件参考 |
| **FreeRTOS** | 实时操作系统，Dummy 机械臂同款 | https://github.com/FreeRTOS | ✅ 嵌入式实时控制标配 |

### 电机驱动参考

| 项目 | 描述 | GitHub / 链接 | 对 0-1 价值 |
|------|------|---------------|-------------|
| **ODrive** | 高性能无刷电机驱动 | https://github.com/odriverobotics/ODrive | ⭐⭐⭐ 无刷电机驱动参考 |
| **XDrive**（Dummy 同款）| 闭环步进驱动，支持 CAN | https://github.com/unlir/XDrive | ⭐⭐⭐⭐⭐ Dummy 机械臂同款，直接可用 |

### 其他相关

| 项目 | 描述 | 链接 | 对 0-1 价值 |
|------|------|------|-------------|
| **立创开源硬件平台** | 稚晖君 Dummy 硬件设计文件 | https://oshwhub.com/NURI/ji-xie-bei-ji-qi-zhi-hui-jun | ⭐⭐⭐⭐ 机器手 3D 模型和 PCB 文件 |
| **OpenClaw** | 分布式 AI 助理框架 | https://github.com/openclaw/openclaw | ⭐⭐⭐⭐⭐ 0-1 的核心软件平台 |
| **NemoClaw** | NVIDIA 官方 OpenClaw 优化栈 | — | ⭐⭐⭐⭐ NVIDIA 官方背书，DGX Spark 原生支持 |

### NVIDIA 机器人开源生态（2025-03 GTC 新增）

| 项目 | 描述 | 链接 | 对 0-1 价值 |
|------|------|------|-------------|
| **Isaac GR00T N1.6** | VLA 视觉-语言-动作模型，宇树 G1 已验证，Cyber Bricks 潜在兼容 | https://huggingface.co/nvidia/GR00T-N1.6-3B | ⭐⭐⭐⭐⭐ 任务规划大脑 |
| **Newton 物理引擎** | NVIDIA+DeepMind+Disney 联合开发，GPU 加速，与 Isaac Lab 集成 | https://github.com/newton-physics/newton | ⭐⭐⭐⭐⭐ 高精度物理仿真 |
| **Cosmos Predict 2.5** | 世界基础模型，生成无限合成动作数据，体积缩小至 1/3.5 | https://huggingface.co/blog/nvidia/cosmos-predict-and-transfer2-5 | ⭐⭐⭐⭐ 仿真数据生成 |
| **物理 AI 数据集** | 15TB，32 万条机器人轨迹，1000+ OpenUSD 场景，Hugging Face 下载 480 万次 | https://huggingface.co/collections/nvidia/physical-ai-67c643edbb024053dcbcd6d8 | ⭐⭐⭐⭐⭐ 预训练首选数据 |
| **Isaac Lab-Arena** | 仿真评估框架，GPU 加速，与 LeRobot/Hugging Face 集成 | https://developer.nvidia.com/blog/simplify-generalist-robot-policy-evaluation-in-simulation-with-nvidia-isaac-lab-arena/ | ⭐⭐⭐⭐ 策略评估 |
| **Isaac Lab** | Isaac Sim 官方机器人学习框架，Newton 集成 | https://developer.nvidia.com/isaac/lab | ⭐⭐⭐⭐ 仿真训练 |
| **LeRobot**（Hugging Face）| 开源机器人框架，标准化数据集格式，GR00T 微调支持 | https://github.com/huggingface/lerobot | ⭐⭐⭐⭐ 训练生态 |

> 💡 **GR00T N1.6 微调硬件需求**：预训练需要高端 GPU，但微调可在 **AGX Orin 64G** 上进行。0-1 的 AGX Thor 目标机可满足。

---

## A.1 语音交互模块

### TTS 推荐（本地离线）

| 方案 | 优势 | 适合场景 |
|------|------|---------|
| **VITS** | ~0.83 RTF（1.2倍实时），最轻量 | ✅ 机器人首选 |
| **Cosyvoice2-0.5B** | 阿里出品，高自然度，多语言 | 产品级，稳定优先 |
| **GPT-SoVITS v4** | 5秒音频克隆，1分钟微调 | 个性化声音 |

### 语音唤醒方案

| 方案 | 推荐度 | 说明 |
|------|--------|------|
| **OpenWakeWord** | ⭐⭐⭐⭐⭐ | 完全开源，可自定义唤醒词 |
| Porcupine | ⭐⭐⭐ | 轻量，25-50ms 延迟 |
| Picovoice | ⭐⭐⭐ | 可考虑，商业友好 |

### 降噪链路（最佳实践）

```
音频输入 → WebRTC AEC（回声消除）→ RNNoise（降噪）→ VAD检测 → 唤醒词引擎
```

| 方案 | 延迟 | CPU占用 | 核心能力 |
|------|------|---------|---------|
| RNNoise | **10ms** | **3.2%** | 降噪（PESQ 3.8）|
| WebRTC AEC3 | 20-60ms | 8.7% | 回声消除 |
| 顺序 | 先 AEC 后 RNNoise | — | 互补非替代 |

### Whisper 优化（Jetson Nano）

- 模型：`base.en`（139MB），可达 1倍实时
- TensorRT INT8 量化：速度提升 40%+，内存减半
- 推荐路径：`whisper-edge` + ONNX 导出 + TensorRT

---

## A.2 ESP32-Cam 有线通信

### ESP32-Cam 最新固件（2025年推荐）

**推荐方案**：Arduino ESP32 v3.0.7 + CameraWebServer

关键改进：
- Wi-Fi 自动重连机制完善
- 看门狗复位大幅减少
- 分区表优化支持更大 ota_0

```cpp
// 稳定初始化（2025年推荐）
rtc_clk_cpu_freq_set(RTC_CPU_FREQ_240M); // 降频减少发热
// 使用 SVGA 而非 UXGA，减少内存压力
```

### UART 通信（Jetson Nano ↔ ESP32-Cam）

- 电平：双方都是 3.3V TTL，**直接互连不需要电平转换**
- 端口：Jetson Nano 用 `/dev/ttyTHS1`（40-pin GPIO 8/10）
- 波特率：115200（最佳性价比）

### I2C 总线注意事项

| 问题 | 解决方案 |
|------|---------|
| 地址检测不到 | 降低频率至 10-50kHz |
| 地址冲突 | 使用 TCA9548A I2C 多路复用器 |
| 数据错误 | 绞线+屏蔽或换用 UART |

### GPIO 应急停止（推荐电路）

**双继电器急停电路（物理+软件双保险）**：
- 急停必须物理断开电机电源回路
- 双继电器冗余防止单点故障
- 常闭触点设计：断电 = 停机（故障安全）
- ESP32 端用硬件中断（μs 级响应）

---

## A.3 拓竹软件生态

| 软件 | 平台 | 核心作用 |
|------|------|---------|
| **Bambu Studio** | Win/Mac/Linux | 切片引擎，多色/多材料打印 |
| **Bambu Suite** | 桌面端 | 激光雕刻/切割/画笔/刀切，多工艺串联 |
| **Bambu Handy** | iOS/Android | 移动端监控，AMS 耗材管理 |
| **拓竹农场管家** | Windows | 多机本地化集群管理，数据不上云 |
| **Bambu Connect** | Win/Mac | 第三方切片→打印机授权 |
| **CyberBrick** | 桌面+移动 | 机器人调试，MicroPython 可视化 |

---

# 第八章：安全与维护

## 8.1 声纹识别

### 目标
通过声纹识别确认用户身份，只有授权用户的声音才能触发关键操作。

### 实现方式

```python
import librosa
import numpy as np

def extract_voice_embedding(audio_path):
    y, sr = librosa.load(audio_path, sr=16000)
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)
    return np.mean(mfccs.T, axis=0)

def verify_speaker(test_audio, enrolled_audio, threshold=0.85):
    test_emb = extract_voice_embedding(test_audio)
    enrolled_emb = extract_voice_embedding(enrolled_audio)
    similarity = np.dot(test_emb, enrolled_emb) / (
        np.linalg.norm(test_emb) * np.linalg.norm(enrolled_emb)
    )
    return similarity > threshold
```

### 声纹注册流程

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | 用户说3-5个不同句子 | 收集多样本 |
| 2 | 提取每句的声纹向量 | 10-15秒音频 |
| 3 | 平均后存储 | 存入本地数据库 |
| 4 | 验证时比对 | 余弦相似度 >0.85 通过 |

---

## 8.2 异常检测

### 目标
实时监控 Jetson Nano / ESP32-Cam 运行状态，发现异常立即告警。

### 监控指标

| 指标 | 正常范围 | 异常阈值 | 处理 |
|------|---------|---------|------|
| CPU 温度 | < 80C | > 85C | 降频/停机 |
| CPU 使用率 | < 90% | > 95% 持续5分钟 | 重启进程 |
| 内存使用 | < 80% | > 90% | 清理缓存 |
| 网络延迟 | < 100ms | > 500ms | 切换网络 |
| ESP32-Cam FPS | > 15 FPS | < 10 FPS | 重启固件 |

### 监控脚本

```python
#!/usr/bin/env python3
import psutil, subprocess, time, requests

def get_cpu_temp():
    try:
        with open('/sys/class/thermal/thermal_zone0/temp') as f:
            return int(f.read()) / 1000
    except: return 0

def check_system():
    warnings = []
    temp = get_cpu_temp()
    if temp > 85: warnings.append(f"CPU温度过高: {temp}C")
    mem = psutil.virtual_memory()
    if mem.percent > 90: warnings.append(f"内存不足: {mem.percent}%")
    cpu = psutil.cpu_percent(interval=5)
    if cpu > 95: warnings.append(f"CPU过载: {cpu}%")
    return warnings

def send_alert(message):
    try:
        requests.post("http://192.168.1.x:3000/api/alert",
            json={"type": "system_warning", "message": message}, timeout=5)
    except: pass

while True:
    warnings = check_system()
    for w in warnings:
        print(f"WARNING: {w}")
        send_alert(w)
    time.sleep(60)
```

---

## 8.3 数据自毁

### 目标
在物理被盗或被强制夺取时，自动销毁贵庚的核心数据。

### 触发条件

| 触发方式 | 说明 |
|---------|------|
| 物理按钮 | 机器人被夺走时按下 |
| 遥控指令 | 发送销毁信号 |
| 异常检测 | 检测到被拆解（加速度计异常）|
| 超时未认证 | 超过设定时间未声纹验证 |

### 销毁流程

```python
#!/usr/bin/env python3
def destroy_all_data():
    import os, subprocess
    DATA_DIRS = [
        "/home/nvidia/guigeng/memory",
        "/home/nvidia/guigeng/videos",
        "/home/nvidia/guigeng/audio",
    ]
    print("WARNING: 触发数据自毁程序")
    subprocess.run(["pkill", "-f", "robot-voice"])
    subprocess.run(["pkill", "-f", "robot-video"])
    for dir_path in DATA_DIRS:
        if os.path.exists(dir_path):
            subprocess.run(["shred", "-n", "3", "-ruv", dir_path])
    print("OK: 数据自毁完成")
```

> WARNING: 数据自毁后不可恢复。重要数据应定期备份到 NAS。
> ⚠️ **SSD/NVMe 限制**：`shred -n 3` 对 SSD/NVMe 效果有限（ Wear Leveling 会分散数据），推荐方案：全程使用 **full disk encryption（LUKS）**，失控时直接销毁密钥而非数据本身。

---

## 8.4 日常维护

### 每日检查

```bash
# 1. 检查节点在线状态
openclaw devices list

# 2. 检查 Jetson Nano 温度
ssh nvidia@192.168.1.x "cat /sys/class/thermal/thermal_zone0/temp"

# 3. 检查 ESP32-Cam 视频流
ffplay rtsp://192.168.1.y/stream

# 4. 检查 Cyber Bricks 电池
curl http://192.168.1.z/battery
```

### 每周维护

| 任务 | 操作 | 说明 |
|------|------|------|
| 日志清理 | journalctl --vacuum-time=7d | 删除7天前日志 |
| 缓存清理 | rm -rf ~/.cache/* | 清理临时文件 |
| 固件检查 | 检查 ESP32-Cam 新固件 | 提升稳定性 |
| 备份 | rsync 到 NAS | 贵庚数据双备份 |

### 每月维护

| 任务 | 操作 |
|------|------|
| 系统更新 | sudo apt update && sudo apt upgrade -y |
| 磁盘检查 | df -h 确认存储充足 |
| 证书更新 | 检查 OpenClaw Gateway 证书 |
| 硬件检查 | 检查所有接线、供电、散热 |

---

## 8.5 常见问题排查

### Jetson Nano 问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 开机黑屏 | 电源不足 | 使用 5V/4A 电源适配器 |
| WiFi 断开 | 驱动问题 | sudo apt install linux-firmware |
| USB 不识别 | 供电不足 | 接外接供电 USB Hub |
| 温度过高 | 散热不足 | 清理风扇、安装散热片 |

### ESP32-Cam 问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 无法连接 | IP 变更 | 重新扫描或设置静态 IP |
| 视频花屏 | 供电不足 | 使用 5V/2A 电源 |
| RTSP 延迟大 | WiFi 信号弱 | 靠近路由器或用有线 |
| 固件崩溃 | 内存泄漏 | 重刷固件 |

### Cyber Bricks 问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 电机不转 | 电池没电 | 充电或换电池 |
| 舵机抖转 | 信号干扰 | 检查接线、加屏蔽 |
| WiFi 断开 | 信号弱 | 调整天线位置 |

### OpenClaw 问题

| 问题 | 原因 | 解决 |
|------|------|------|
| Node 不在线 | 网络不通 | ping 192.168.1.x 检查 |
| exec 超时 | 节点负载高 | 等几秒重试 |
| 配对失败 | Token 错误 | 重新获取 Token |

---

# 第九章：风险与合规

## 9.1 技术风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| Jetson Nano 烧毁 | 机器人瘫痪 | 稳压电源、温度监控 |
| 数据丢失 | 贵庚记忆损坏 | 每日 rsync 备份到 NAS |
| WiFi 被劫持 | 控制权丧失 | 启用 WPA3、关闭 WPS |
| ESP32-Cam 被破解 | 隐私泄露 | 修改默认密码、禁用Telnet |
| Cyber Bricks 失控 | 物理损坏 | 有线 GPIO 应急停止 |

---

## 9.2 法规风险

| 风险 | 说明 | 合规建议 |
|------|------|---------|
| 隐私合规 | 24小时录像涉及隐私 | 明确告知、录像本地存储、不上云 |
| 室内录音 | 未授权录音可能违法 | 仅在授权用户声纹验证后启用 |
| 机器人伤人 | Cyber Bricks 动作幅度大 | 设置动作限位、接触停止 |
| 无线电频谱 | ESP32-Cam WiFi 需合规 | 使用已认证设备 |
| 机器人人行道通行 | 人行道属于公共道路，目前无明确准入标准 | 重点关注：低速（<5km/h）、有紧急停止装置、不影响行人；建议提前了解当地交管部门要求 |
| 国标参考 | 暂无强制准入标准 | 参考 GB/T 40013-2021《家用和类似用途服务机器人》（推荐性国标，非强制） |

> ⚠️ 本文档不构成法律建议。具体合规要求请咨询专业律师。

---

# 第十章：调研更新记录

> 按时间线记录历次调研的重要发现，供快速查阅。

## 调研记录：2026-03-22

> 调研工具：zhiku(DeepSeek) + web_fetch(AMD 官方博客) + vLLM/SGLang 官方文档

### 新增内容

| 主题 | 关键发现 |
|------|---------|
| **ROCm 7.x** | gfx1151 (RDNA 3.5) 必须用 ROCm 7.0+，6.x 不支持 |
| **vLLM ROCm** | v0.14.0 官方 Docker，一键安装，CI 通过率 93% |
| **SGLang ROCm** | AMD MI300X/MI355X 原生，FP8/AWQ 支持，适合复杂 Agent |
| **RTX 2060 量化** | Q4_K_M 是最佳平衡点，TensorRT-LLM 不推荐 |
| **NemoClaw** | NVIDIA GTC 2026 发布，企业级安全沙箱 |
| **A18 Pro** | NPU 量化分数 44,672，比 A17 Pro 高 33% |
| **FastVLM** | 比 LLaVA-OneVision 快 85 倍 TTFT，0.5B 可本地运行 |
| **Genesis** | 最新版本 v0.4.0（2026-02-17），GTX 1080 6GB 即可跑 |
| **Genesis vs Newton** | Newton（Disney+DeepMind+NVIDIA三巨头，Linux Foundation）需关注但为时尚早 |
| **Jetson Thor Nano** | 仍然不存在，继续每月一次监控 |
| **星闪设备** | BearPi-Pico H3863（海思Hi3863V100，17个GPIO，40针扩展排针座）/ RK3506星闪板（59元核心板）；和ESP32对比：时延<20μs vs >10ms，并发4096 vs 7-20；但缺少"40针GPIO+星闪原生"标准品，需RISC-V开发板+星闪Dongle组合方案 |

---

## 调研记录：2026-03-21 深夜

> 调研工具：deepseek_deepseek_chat + 4x sessions_spawn 子Agent + web_fetch

### 新增内容

| 主题 | 关键发现 |
|------|---------|
| **Genesis 物理引擎** | GTX 1080 6GB 起，RTX 2060 可用，比 Isaac Sim 快 10-80 倍 |
| **YOLO Nano 2GB** | DeepStream-Yolo 最新支持 YOLOv13/YOLOv12/YOLO11/26，支持 FP16 |
| **MediaPipe on Nano** | GPU 加速不成熟，不推荐，替代方案 TensorRT |
| **iPhone 感知** | Apple Vision / Core ML + YOLO / MediaPipe / FastVLM 完整方案 |
| **语音升级** | VITS / CosyVoice2 / GPT-SoVITS v4 推荐，WebRTC AEC + RNNoise 降噪链路 |
| **OpenClaw 限制** | 无专用机器人节点类型，GPIO/串口/电机控制无内置支持 |
| **ESP32-Cam 固件** | Arduino ESP32 v3.0.7 + CameraWebServer 推荐 |

---

## 调研记录：2026-03-24 傍晚

> 调研原因：B站稚晖君"钢铁侠迷你机械臂"视频（BV12341117rG）
> 调研工具：minimax search + tavily search + web_fetch(GitHub)

### 稚晖君（彭志辉）开源项目对 0-1 的价值

**稚晖君简介**：前华为"天才少年"，现智元机器人（AgiBot）联合创始人兼 CTO。B站"野生钢铁侠"，GitHub: peng-zhihui，60 个公开仓库。

#### ① Dummy-Robot 机械臂 ⭐⭐⭐⭐⭐（最高优先级）

**视频**：BV12341117rG（【自制】我造了一台钢铁侠的迷你机械臂！【硬核】）
**GitHub**：https://github.com/peng-zhihui/Dummy-Robot

**已开源内容**：3D 模型（SolidWorks）+ 底座控制器（STM32F4）+ 步进电机驱动（CAN 总线）+ Peak 示教器 + 上位机 DummyStudio + 完整固件（FreeRTOS + C++11）

**对 0-1 的高价值点**：

**CAN 总线通信（可直接替代 Cyber Bricks PWM）**：
- 4 根线（电源 × 2 + CAN H/L）串联所有关节
- 每个电机有独立 ID，支持广播同步信号
- 支持力矩/速度/位置/轨迹 4 种模式
- 0-1 现状：Cyber Bricks PWM 走线杂乱 → 升级目标

**三种指令模式（运动控制层参考）**：

| 模式 | 特点 | 适合场景 |
|------|------|---------|
| SEQ（顺序指令）| FIFO 队列，依次执行 | 视觉抓取、码垛 |
| INT（实时指令）| 新指令覆盖旧指令，立即响应 | 动作同步、遥操作 |
| TRJ（轨迹跟踪）| 200Hz 插值，精确轨迹 | 3D 打印、绘画、雕刻 |

**零点校准方法（无硬件成本，直接可实现）**：
上电后电流环低力矩定向运动 → 碰机械限位确认粗零点 → 单圈绝对值编码器精调
结果：精度等同于编码器精度，不受加工误差影响，无需限位开关

**逆运动学算法（已开源）**：
- 标准 DH 参数建模，逆解 8 组 → 选最小转角组合
- 梯形加减速曲线进行速度位置规划

**"青春版"低成本复刻方案（对 0-1 最实用）**：
- 3D 打印结构（替代 CNC，¥2000 以内）
- 自制摆线针轮减速器（替代谐波减速器，¥600 → ¥100）
- 配套保姆级视频教程（待发布）
- **GitHub**：https://github.com/peng-zhihui/CycloidAcuratorNano

#### ② AgiBot World 百万真机数据集 ⭐⭐⭐⭐⭐

**发布**：2024-12-30，智元机器人开源
**规模**：百万级真机数据，覆盖 5 大核心场景，比 Open X-Embodiment 大 10 倍
**平台**：8 摄像头 + 6 自由度灵巧手
**下载**：https://opendatalab.com/OpenDriveLab/AgiBot-World/download

**对 0-1 的价值**：
- 0-1 训练数据来源之一（预训练 + 微调）
- 8 摄像头 + 6DOF 灵巧手 = 完整人形硬件规格参考

#### ③ AimRT 机器人中间件 ⭐⭐⭐⭐

**发布**：2024 年底，智元机器人开源
**定位**：高性能机器人通信中间件，类似 ROS2，但性能更优、资源占用更小
**对 0-1 的价值**：在 AGX Thor / AI Halo 上部署时，可替代 ROS2

#### ④ XUAN-Bike "大脑 + 小脑"架构 ⭐⭐⭐

**架构**：
- 大脑：昇腾 310 AI 芯片（昇腾），负责思考/规划
- 小脑：STM32 单片机，负责运动控制/实时响应

**对 0-1 的价值**：与 0-1 的架构高度吻合——Gateway = 大脑，Nano = 小脑，这是稚晖君 2021 年就验证过的方案

#### ⑤ 哪吒双足机器人 ⭐⭐⭐

**发布时间**：2024 年 4 月
**关键参数**：超过 **49 个自由度**，手部 12 DOF
**对 0-1 的参考**：49 DOF 的关节分配方式；手部 12 DOF 是入门级灵巧手参考

#### ⑥ 启元 Q1 ⭐⭐⭐

**发布时间**：2026 年 1 月 1 日
**定位**：全球首款全身力控小尺寸人形机器人，小到能塞进书包
**"探索者计划"**：个人开发者共创，0-1 可考虑加入

#### 关键链接汇总

| 资源 | 链接 |
|------|------|
| Dummy-Robot GitHub | https://github.com/peng-zhihui/Dummy-Robot |
| B站"钢铁侠机械臂" | https://www.bilibili.com/video/BV12341117rG |
| CycloidAcuratorNano | https://github.com/peng-zhihui/CycloidAcuratorNano |
| 稚晖君 GitHub 主页 | https://github.com/peng-zhihui |
| AgiBot World 数据集 | https://opendatalab.com/OpenDriveLab/AgiBot-World/download |

---

## 调研记录：2026-03-24 下午（续）

### RynnBrain + 空间智能新增

| 主题 | 关键发现 |
|------|---------|
| RynnBrain | 阿里巴巴达摩院 2026-02-10 开源，30B MoE + 3个专用模型（Plan/Nav/CoP），时空记忆+物理推理，Apache 2.0 可商用 |
| RynnBrain 落地 | Jetson Orin NX 可跑（INT4），16项 SOTA，5000+ 家庭已部署 |
| 李飞飞 World Labs | 3D 世界生成 + PointWorld + Physical AI，$230M 融资 |
| 对 0-1 价值 | RynnBrain-30B MoE 可作任务大脑 + 导航 + 操作规划；空间智能做新环境零样本建图 |

> 调研工具：5平台 webauth + 2轮 subagent 搜索 + minimax + tavily + web_fetch

### Medusa Halo 新增

| 主题 | 关键发现 |
|------|---------|
| Medusa Halo 定位 | AMD 下一代 APU 代号，对应 Ryzen AI MAX 500 系列，不是整机产品名 |
| 核心规格 | Zen 6（24+2核）+ RDNA 5（48 CU）+ LPDDR6（460-691 GB/s）+ 256GB+ |
| 上市时间 | 2027年下半年~2028年 |
| 移动终端价值 | 外出完整跑 0-1（130B量化 + 8-12 Agent + 256K上下文），与家中 AI Halo 遥相呼应 |
| 当前过渡 | Asus ProArt PX13 / ROG Flow Z13（Strix Halo，128GB） |

### 核查结果汇总

| 主题 | 结果 |
|------|------|
| NemoClaw GTC 2026 | ✅ 官方确认（2026-03-16）|
| Jetson Thor Nano | ✅ 确认不存在 |
| RTX 5050 9GB/96-bit/336GB/s | ✅ 准确，补充位宽 |
| RTX 5050 ~2099元 | ✅ 准确 |
| DGX Spark 价格 | ⚠️ 修正：$4,699/34,999元（2月涨价，京东自营）|
| DGX Station 70万 | ⚠️ 规格准确，价格无据可查，保留 |
| BearPi H3863 GPIO | ⚠️ 修正：17个GPIO（非40针GPIO）|
| Genesis vs Isaac Gym | ⚠️ 修正：应为 Isaac Gym 非 Isaac Sim |
| Genesis v0.4.0 日期 | ⚠️ 修正：最新2026-02-17 |
| AMD AI Halo 128GB | ⚠️ AMD未公布价格，整机参考价17,999元 |
| Jetson Nano I2C 引脚 | ⚠️ 修正：Pin 3(SDA)/5(SCL) |
| vLLM ROCm Docker | ⚠️ 修正：镜像名 `vllm/vllm-openai:v0.14.0-rocm` |
| micro-ROS agent | ⚠️ 修正：传输类型 `udp4` 非 `wifi` |
| GB/T 40013-2021 国标 | 💡 新发现：补充家用服务机器人推荐性国标 |

### 新增内容

| 主题 | 关键发现 |
|------|---------|
| NemoClaw | NVIDIA GTC 2026-03-16 官方发布，含 OpenShell + Nemotron |
| DGX Spark 涨价 | 2026年2月底从 $3,999 涨至 $4,699 |
| BearPi GPIO | 17个GPIO（40针排针座含电源/地）|
| Genesis v0.4.0 | 2026-02-17 最新版本 |
| GB/T 40013-2021 | 家用服务机器人推荐性国标（非强制）|

---

## 调研记录：2026-03-24 晚间

> 调研原因：用户转发 NVIDIA 2025-03 GTC 机器人开源核心技术汇总
> 调研工具：minimax search + tavily search + web_fetch(NVIDIA/Hugging Face/GitHub)

### NVIDIA 机器人开源核心技术对 0-1 的价值

**来源**：NVIDIA GTC 2025-03 发布，官方博客 + Hugging Face + GitHub 验证

| 主题 | 关键发现 |
|------|---------|
| **Newton ≠ Genesis** | Newton 是 NVIDIA+DeepMind+Disney 的另一套引擎（非 Genesis 替代），已集成 Isaac Lab |
| **GR00T N1.6** | VLA 模型，宇树 G1 已在预训练中验证；Cyber Bricks 潜在兼容 |
| **物理 AI 数据集** | 15TB，32 万条机器人轨迹，开源 Hugging Face，下载量 480 万次 |
| **Cosmos Predict 2.5** | 世界模型，体积缩小至 1/3.5，与 RoboGSim 协同可生成无限合成数据 |
| **Isaac Lab-Arena** | 仿真评估框架，与 LeRobot/Hugging Face 集成 |

### 对 0-1 的整合建议

| 阶段 | 技术 | 说明 |
|------|------|------|
| 阶段一 | Genesis | 低成本入门仿真 |
| 阶段二 | Newton + GR00T N1.6 | 高精度仿真 + VLA 任务规划 |
| 数据 | 15TB 数据集 + AgiBot World | 双源预训练数据 |
| 合成数据 | Cosmos + RoboGSim | 真实纹理 + 无限变体 |

### 重要纠正

- Genesis（Apple）≠ Newton（NVIDIA）：两个完全不同的独立开源项目，需区分

---

**0-1** —— 不是一台机器，是你人生的另一面。

*文档版本：v3.4（具身大脑版 + 全开源生态整合，优化版）| 字数：115200字符/11490词| 更新：2026-03-24*
