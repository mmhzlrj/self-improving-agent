# 0-1 项目产出索引 — 2026-03-27

> 生成时间：2026-03-27 21:34 CST  
> 生成者：N-04 subagent

---

## 产出总览

| 任务 | 名称 | 状态 | 产出文件 | 完成时间 |
|------|------|------|----------|----------|
| N-01 | Jetson 自定义镜像调研 | ✅ success | `reports/Jetson-Nano-Custom-Image-Research.md` | 2026-03-26 22:38 |
| N-02 | OpenClaw × ROBOT-SOP 映射报告（重做） | ✅ success | `reports/OpenClaw-Features-0-1-Mapping-v2.md` | 2026-03-27 01:53 |
| N-03 | 补充 Phase 0 / ESP32 / Jetson 报告 | ✅ success | `reports/` 三份报告已更新 | 1m44s |
| N-04 | 文档整理 + 生成最终 INDEX | ✅ success | `output/2026-03-27/INDEX.md` | 3m37s |
| N-05 | 映射报告五平台交叉验证 | ✅ success | `output/2026-03-27/Cross-Verification-N05.md` | 2026-03-27 21:20 |
| N-06 | world.html LED 幕墙 + NPC 修复 | ✅ success | `harness/robot/world.html` | 2026-03-27 21:15 |

---

## 重要发现摘要

（来源：N-05 `Cross-Verification-N05.md` + morning-summary.md）

### OpenClaw 官方配置（已验证 ✅）

1. **Gateway 端口 18789** — 官方 Security 文档明确，同端口复用 WebSocket + HTTP
2. **Ollama 禁止使用 /v1 路径** — 官方 Ollama 文档有独立 Warning 区块明确警告，使用 /v1 会破坏 tool calling
3. **Sub-agent maxSpawnDepth 默认 1，推荐 2** — 范围 1-5；Context 只注入 AGENTS.md + TOOLS.md，不含 SOUL/MEMORY/IDENTITY
4. **Sub-agent 并发参数** — maxChildrenPerAgent 默认 5，maxConcurrent 默认 8，archiveAfterMinutes 默认 60
5. **DM pairing 安全策略** — pairing 码 1 小时过期，pending 上限 3 个/频道，默认手动审批

### 关键风险项（需关注 ⚠️）

6. **Camera Node 不支持 RTSP 流** — 映射报告有误，官方 Camera 文档仅列出 iOS/Android/macOS 原生摄像头，无 RTSP
7. **RTX 2060（6GB）仅能跑量化模型** — FP16 不够，核心推理建议用云端
8. **Jetson Nano 2GB 内存** — 不要跑 Gateway，只装 ros-base
9. **iOS App 为 internal preview 状态** — 非公测，发布时间不确定
10. **OpenClaw 内置语音识别是否含 Whisper / RTSP 解码器是否内建** — 需实测验证

---

## 报告文件索引

路径：`harness/robot/night-build/reports/`

| 文件名 | 大小 | 最后修改 |
|--------|------|----------|
| Phase-0-Gateway-Docking.md | 37KB | 2026-03-27 21:35 |
| ESP32-Cam-Firmware-Flashing.md | 55KB | 2026-03-27 21:35 |
| Jetson-Nano-OpenClaw-Setup.md | 43KB | 2026-03-27 21:35 |
| OpenClaw-Features-0-1-Mapping-v2.md | 148KB | 2026-03-27 01:53 |
| OpenClaw-Features-0-1-Mapping.md | 25KB | 2026-03-27 00:39 |
| Jetson-Nano-Custom-Image-Research.md | 9KB | 2026-03-26 22:38 |
| INDEX.md | 1KB | 2026-03-27 09:34 |

---

## 今晚新增产出

路径：`harness/robot/night-build/output/2026-03-27/`

| 文件名 | 说明 | 最后修改 |
|--------|------|----------|
| INDEX.md | 本文件 | 2026-03-27 21:34 |
| Cross-Verification-N05.md | 五平台交叉验证报告（30条声明核查） | 2026-03-27 21:16 |
| Mapping-Verification.md | 早间验证摘要 | 2026-03-27 09:37 |
| final-summary.md | Night Build 最终报告 | 2026-03-27 01:40 |
| morning-summary.md | 晨间总结 | 2026-03-27 09:50 |
| orchestrator-log.jsonl | 调度日志 | 2026-03-27 20:00 |

---

## 待处理任务

**所有任务已完成，无 pending 任务。**

---

## 建议

（基于今晚 N-05 交叉验证 + morning-summary 风险项）

1. **实测验证 OpenClaw 语音识别方案**
   — 内置是否含 Whisper、RTSP 解码器是否内建，直接影响 Phase 1 音频架构选型
   — 建议：翻文档或建一个 test harness 跑 `voice.start` + `camera.snap`

2. **明确 Jetson Nano 2GB vs 4GB 采购决策**
   — 2GB 不可跑 Gateway，4GB 可；当前 Phase 0-2 均依赖 Nano 作为核心推理节点
   — 建议：直接确认采购规格，避免开发到一半发现内存不够

3. **iOS App internal preview 跟进**
   — App 发布状态不确定影响远程控制方案（手机作为 Node 的 Plan B）
   — 建议：发 issue 或联系 OpenClaw 团队确认发布时间窗口

---

*本索引由 N-04 subagent 生成，严格在 5 分钟内完成。*
