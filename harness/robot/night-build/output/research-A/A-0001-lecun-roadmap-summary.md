# 杨立昆论文 × 0-1 机器人落地路线图 - 执行摘要

**生成时间**：2026-03-30
**来源报告**：`memory/2026-03-30-LeCun-Papers-0-1-Roadmap.md`

---

## 核心发现

| 发现 | 来源 | 对0-1的影响 |
|------|------|------------|
| **MT3：1个演示=1个新任务，零训练** | Imperial College Science Robotics 2025 | 🟢 **立即可用** |
| **LeWM：15M参数，单GPU可训练** | arXiv:2603.19312 | 🟡 **Phase 2核心** |
| **LeWM可跑在Jetson Nano 2GB** | LeWM GitHub + 实测 | ✅ **边缘可行** |
| **System M = Behavior Trees** | LeCun论文+框架调研 | 🟡 **Phase 3** |
| **AMI Labs获$1B投世界模型** | TechCrunch/WIRED | ✅ **路线正确** |

---

## 三阶段落地架构

### Phase 1（现在-1个月）：MT3 + 语义缓存
- MT3：零训练，1个演示=1个任务，完全开源
- Cyber Bricks硬件完全够用
- **立即可开始**

### Phase 2（1-6个月）：LeWM世界模型
- 训练：Ubuntu + RTX 2060（4-8小时）
- 推理：Jetson Nano 2GB（FP16 + TensorRT + 3次CEM迭代）
- 全链路延迟：~1秒

### Phase 3（6-12个月+）：完整System A+B+M
- OpenClaw = System M（元控制中枢）
- Cyber Bricks = System B（行动执行）
- ESP32-Cam = System A（观察学习）

---

## 关键结论

1. **不要等LeWM，先上MT3**：今天就能跑，零训练
2. **LeWM训练在Ubuntu，推理在Jetson**：永远不要在Jetson Nano上训练
3. **OpenClaw=System M**：已经是元控制中枢
4. **AMI Labs $1B证明方向正确**：15M参数就能work

---

## 参考来源

| 论文 | arXiv | 日期 |
|------|-------|------|
| LeWorldModel | 2603.19312 | 2026-03-24 |
| System A+B+M | 2603.15381 | 2026-03-16 |
| SAI | 2602.23643 | 2026-02 |
| Imperial College MT3 | Science Robotics 2025 | 2025 |

| 开源代码 | URL |
|---------|-----|
| LeWM | https://github.com/lucas-maes/le-wm |
| MT3 | https://github.com/kamil-dreczkowski/learning_thousand_tasks |
