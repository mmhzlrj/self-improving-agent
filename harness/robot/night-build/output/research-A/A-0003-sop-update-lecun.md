# A-0003: LeCun论文落地路线图 → ROBOT-SOP.md 更新

## 来源
- 调研报告: `memory/2026-03-30-LeCun-Papers-0-1-Roadmap.md`
- 任务: 将LeCun论文落地路线图更新到ROBOT-SOP.md

---

## 1. Phase 1 更新: MT3（Multi-Task Trajectory Transfer）作为首选方案

### 背景
- 论文: Imperial College Science Robotics 2025
- 核心突破: 零训练成本，1个演示=1个新任务
- GitHub: https://github.com/kamil-dreczkowski/learning_thousand_tasks

### 0-1项目落地
- **目标**: CyberBricks/NPC学会新任务不需要重新训练
- **方法**: 记录一个人类操作演示 → 自动生成任务harness → 复用
- **与现有Skills关系**: 
  - 现有 `ROBOT-SOP.md` 的"录制-回放"模式 → 升级为MT3框架
  - 每个技能的 `contracts` 里的 `Validation Gate` → MT3的demonstration验证

### 具体更新章节建议
```
### Phase 1: MT3多任务迁移（2026-Q2）
- 优先级: P0
- 依赖硬件: ESP32-Cam（观察）+ CyberBricks（执行）
- 里程碑:
  1. 实现单步示教录制（ESP32-Cam录制 + 按键触发）
  2. 实现示教回放（CyberBricks执行动作序列）
  3. 实现多步任务链（串联多个示教片段）
  4. 实现零样本泛化（不同位置/角度的同一任务）
```

---

## 2. Phase 2 更新: LeWM世界模型部署

### 背景
- 论文: LeWorldModel (arXiv:2603.19312, 3月24日)
- 核心: JEPA里程碑式轻量世界模型，15M参数
- 特点: 训练在高性能设备，推理在边缘设备

### 0-1项目落地
- **训练设备**: Ubuntu + RTX 2060 6GB
- **推理设备**: Jetson Nano 2GB（FP16 + TensorRT优化后）
- **Phase 2分阶段**:
  1. 在Ubuntu上训练JEPA子模块（预测物理变化：光照/物体移动）
  2. 将训练好的权重导出为TensorRT格式
  3. 部署到Jetson Nano进行实时推理
  4. 与ESP32-Cam数据流打通（观察→预测→控制）

### 具体更新章节建议
```
### Phase 2: LeWM世界模型（2026-Q3）
- 依赖: Phase 1 完成
- 架构:
  - Ubuntu训练节点: JEPA世界模型训练
  - Jetson Nano边缘节点: 实时推理（延迟<50ms）
- 数据流: ESP32-Cam → Jetson Nano(LeWM推理) → CyberBricks执行
```

---

## 3. Phase 3 更新: System A+B+M完整架构

### 背景
- 论文: 《Why AI systems don't learn and what to do about it》(arXiv:2603.15381)
- 核心: System A+B+M三元认知架构

### 0-1项目映射

| NLAH组件 | 0-1实现 | LeCun对应 |
|---------|---------|-----------|
| System M（元控制中枢） | **OpenClaw** | 元控制：任务分解、长期记忆、策略选择 |
| System B（行动执行） | **CyberBricks** | 行动执行：精确物理控制、硬件驱动 |
| System A（观察学习） | **ESP32-Cam** | 快速学习：视觉感知、技能获取 |

### OpenClaw = System M 的具体定位
- **任务分解**: 将用户指令分解为可执行步骤
- **长期记忆**: 记忆用户偏好、场景状态、历史交互
- **策略选择**: 根据上下文选择合适的技能harness
- **跨模态**: 协调视觉输入(ESP32)、物理执行(CyberBricks)、语言输出(LLM)

### 具体更新章节建议
```
### Phase 3: System A+B+M完整架构（2026-Q4）
- 架构图:
  ┌─────────────────────────────────────────────────────┐
  │  OpenClaw (System M - 元控制中枢)                   │
  │  ├─ 任务分解引擎                                     │
  │  ├─ 长期记忆模块                                     │
  │  ├─ 策略选择器                                       │
  │  └─ 跨模态协调器                                     │
  ├────────────────────────────────────────────────────┤
  │  CyberBricks (System B - 行动执行)                  │
  │  ├─ 步进电机控制                                     │
  │  ├─ LED矩阵驱动                                     │
  │  └─ 传感器数据采集                                   │
  ├────────────────────────────────────────────────────┤
  │  ESP32-Cam (System A - 观察学习)                    │
  │  ├─ 实时视频流                                       │
  │  ├─ 动作识别                                         │
  │  └─ 示教录制                                         │
  └─────────────────────────────────────────────────────┘
```

---

## 4. SAI定位: 专业化AI vs 通用AGI

### 背景
- 论文: SAI (arXiv:2602.23643, 2月)
- 核心: 超人类适应性智能，专注于特定任务域

### 0-1项目定位
**不是**: 通用AGI（什么都能做，但什么都不精）
**是**: 在"陪伴记录物理世界"这个任务上超越人类的specialized AI

#### 专业化方向
1. **物理世界感知**: 精准识别室内物品、人物动作、环境变化
2. **时空记忆**: 记住"什么东西在哪里、什么时候被使用过"
3. **自然交互**: 像真人一样陪伴对话 + 物理世界联动
4. **自我优化**: 从用户反馈中持续学习新技能（MT3驱动）

#### 与SAI的关系
- SAI的"专业化路线"→ 0-1聚焦"家庭陪伴机器人"垂直场景
- AMI Labs获$1B投资 → 验证了"专业AI"路线的商业价值
- Imperial College MT3 → 证明低成本获取新技能的可能性

---

## 5. 技术升级路径总结

### 2026-Q2: Phase 1 完成
- MT3框架落地
- ESP32-Cam示教录制
- CyberBricks基础动作库

### 2026-Q3: Phase 2 完成
- LeWM在Jetson Nano部署
- 实时世界模型推理
- 观察-预测-执行闭环

### 2026-Q4: Phase 3 完成
- System A+B+M完整架构
- OpenClaw元控制中枢
- 跨设备协同

### 长期演进（2027+）
- 从单房间扩展到多房间
- 从家庭扩展到办公/商业场景
- 从被动响应到主动陪伴

---

## 6. 对现有ROBOT-SOP.md的具体修改建议

在ROBOT-SOP.md中新增/修改以下章节:

1. **概述章节**: 添加LeCun三元架构图
2. **Phase 1**: 替换原有计划，采用MT3方案
3. **Phase 2**: 添加LeWM部署子章节
4. **Phase 3**: 更新System A+B+M架构描述
5. **定位章节**: 明确"专业化AI"定位 vs AGI

---

*生成时间: 2026-03-30 15:12 GMT+8*
*来源: memory/2026-03-30-LeCun-Papers-0-1-Roadmap.md*
