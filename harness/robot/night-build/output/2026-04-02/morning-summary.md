# 🌅 0-1 项目晨间总结 — 2026-04-02

> 生成时间：2026-04-02 09:50 (Asia/Shanghai)

---

## 📊 任务队列状态（截至 v8 / 2026-03-30）

| 序列 | 完成 | 等待 | 总数 | 状态 |
|------|------|------|------|------|
| **A序列** | 3 | 8 | 11 | 🔸 P0 物理机器人 |
| **B序列** | 1 | 3 | 4 | 🔸 Phase 3 iPhone感知 |
| **C序列** | 0 | 1 | 1 | 🔸 3D打印+技术验证 |
| **D序列** | 0 | 1 | 1 | 🔸 Demo/内容/调优 |

> ⚠️ **注意**：B→C→D 需等前序序列完成才可开始

---

## 🌙 昨夜执行情况

**结论：Night Build 未实际运行**
- 2026-04-01 输出目录为空（orchestrator 未执行）
- 2026-04-02 输出目录为空
- task-queue.json 停留在 v8（2026-03-30）

---

## ✅ 已完成任务产物（2026-03-30 夜）

| 类别 | 任务数 | 产出文件 |
|------|--------|---------|
| world.html 灯光优化 | 13 | harness/robot/world.html（城市灯光 intensity 6→15，灯柱 4→10） |
| Ubuntu 布局修复 | 10 | harness/robot/world.html（底座/支架/主机箱 y 坐标修正） |
| NPC 系统 | 7 | harness/robot/world.html（workTarget、lerp移动、走路+打字动画） |
| LED 幕墙 | 10 | harness/robot/world.html（fetch 路径修复、drawTaskQueue 看板） |
| 天空系统 | 8 | harness/robot/world.html（星星、云层、月亮） |
| UI 调研 | 13 | night-build/output/research-01~15.md |
| SOP 文档 | 33 | night-build/reports/sop-*.md |
| esp32-cam-rtsp | 6 | harness/robot/services/esp32-cam-rtsp/ |
| mqtt-router | 5 | harness/robot/services/mqtt-router/ |
| jetson-yolo | 3 | harness/robot/services/jetson-yolo/ |
| whisper-tts | 1 | harness/robot/services/whisper-tts/stt_service.py |
| 竞品分析 | 1 | night-build/reports/competitor小米CyberDog2.md |

---

## 🔍 重点发现

- 🔍 **MT3 软件链路跑通**：Jetson Nano 上 MT3 推理验证成功，PyTorch 2.7.1+CUDA ✅，模拟轨迹 100步 50Hz 验证通过，MQTT 桥接脚本完成
- 🔍 **Cyber Bricks 硬件缺口**：无 AS5600 编码器，无法录制真实演示轨迹；推荐 A+D 方案（电流检测+视觉）快速绕过
- 🔍 **iPhone LiDAR 可用**：iPhone 16 Pro RoomPlan 可导出 .usdz，LiDAR ±5mm，60fps 深度，B序列数据通道已通
- 🔍 **A-0018 docs.0-1.ai WebMCP**：P0 任务已 ready，待执行

---

## ❓ 需要用户决策

- ❓ **AS5600 编码器采购**：约 $10，是否采购以支持 MT3 真实轨迹录制？（否则用模拟数据）
- ❓ **A序列 8个 pending 任务**：T-01-A18~A23（Self Memory + WebMCP + ESP-AI）优先级确认，按什么顺序执行？
- ❓ **B/C/D 序列解锁条件**：iPhone 感知接入和 3D 打印是否需要等待 A 全部完成？

---

## 📅 下一步

1. **今天**：确认 A-0018~A23 执行顺序（建议 A-0018 WebMCP 优先，因为它影响知识库接入）
2. **今晚**：确保 Night Build 正常触发运行
3. **本周**：推进 A-0019~A20（MemOS 评估 + ESP-AI 语音模块）
