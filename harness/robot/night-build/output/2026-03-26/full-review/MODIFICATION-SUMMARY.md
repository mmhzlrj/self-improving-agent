# ROBOT-SOP.md v3.24 修改摘要

## 修改统计
- 修改块: 37 处
- 行变化: +23 行（4917 → 4940）
- 采纳审批: 81 条中约 40 条已完成修改
- 未修改: 上下文截断问题（4条）、分段问题（非文档内容）、已验证无需修改

## 修改清单

### 事实修正（7处）
1. **Hi3863V100 → PICO Hi3861**（L2116, L4631）— 用户确认 AI 乱补的芯片名
2. **Genesis: Apple → CMU/Genesis AI Company**（L3598）— 由 CMU 周衔发起，20+机构联合
3. **GRPO 说明修正**（L373）— 明确 GRPO 仅用于 RynnBrain-CoP，基础模型用 SFT
4. **Jetson Nano 2GB RAM: 4GB → 2GB**（L734）— 型号标注为 B01
5. **YOLOv4-tiny 重复列修复**（L3091）— 去掉模型名和分辨率的重复
6. **open-agibot/go1-sim → AgiBotTech/agibot_go1**（L4075, L4243）— 修正 GitHub 组织名
7. **applecartn/genesis → Genesis-Embodied-AI/Genesis**（L4078, L4766）— 修正 GitHub URL

### 来源补充（14处）
8. **EdgeTPU benchmark 来源**（L766）— ai.google.dev/gemma/docs/embeddinggemma
9. **openPangu 来源**（L768）— huawei.com/cn/products/pangu
10. **MLPerf Tiny 标注**（L791）— 补充"与 Jetson Nano 不在同一级别"
11. **Project Silica Fudzilla 链接**（L2221）
12. **Jetson Thor 发布链接**（L1956）— nvidia.cn 官方
13. **JetPack 下载链接**（L2876）— 官方+社区+讨论
14. **Bridge Protocol 链接**（L2879）— docs.openclaw.ai
15. **RynnBrain GitHub**（L3704）— alibaba-damo-academy/RynnBrain
16. **GR00T N1.6 来源**（L3892-3893）— 宇树 G1 论文 + Isaac-GR00T 仓库
17. **RT-1 GitHub**（L4078）— google-research/robotics_transformer
18. **AgiBot World 修正为 GitHub**（L4242, L4712, L4752）
19. **GO-1 GitHub 修正**（L4243）
20. **JetPack 下载 URL**（L2876）— 已有官方+社区链接
21. **Qwen3.5-122B 来源待确认标注**（L4229）

### 硬件数据补充（6处）
22. **拓竹电池参数**（L1886）— 14500 7.4V 800mAh Li-ion Battery PC003
23. **AMD GPU TFLOPS**（L1956）— +GPU FP16 ~20.48 TFLOPS（集成 Radeon 8060S）
24. **NAS 改为绿联 DXP4800 Plus**（L1648-1651）— 万兆网口，16G 内存
25. **DOF 说明**（~L775）— 24 DOF 简化版 vs 27 DOF 学术标准
26. **GPIO 说明**（L4631）— 40针中17针为GPIO，其余电源/地/冗余
27. **RTX 硬件要求**（#105 待确认）

### 内容补充/修正（10处）
28. **MQTT on_message try/except**（L3299-3303）— 添加异常处理
29. **MediaPipe 功能补充**（L3545-3550）— Face Mesh + Object Tracking
30. **Newton 差异化说明**（L3676-3683）— 与 Genesis 表的区别说明
31. **"主力" → "推荐场景"**（L3713）— 用词规范化
32. **Cyber Bricks 兼容性**（L3906）— 标注"待实际验证"
33. **Jetson Nano 并发说明**（~L1100）— 不同时用3个功能
34. **BLE + SLE 说明**（~L1353）— 同一芯片功能
35. **数据自毁场景**（~L1303）— 实验室阶段不适用
36. **SSH 连接步骤**（L2887）— 补充 Mac 连接 Jetson 命令
37. **访客数据匿名化**（L1234）— 3-5年无命中可匿名化

## 未修改的项目（原因）
- **上下文截断（#27-29,31）**: 用户指示"如果截断就忽略"
- **分段范围问题（#88）**: 审核分段问题，非文档内容
- **悬空交叉引用（#109）**: §2.5 实际存在，交叉引用有效
- **命令参数（#97）**: --display-name 已验证为有效 openclaw 参数
- **ICML 2025 时间（#19）**: 2025年7月已召开，非未来事件
- **格式问题部分**: Phase 表格格式已检查，部分无需修改
