# 2026-03-28 下一步规划

## 当前进度

### ✅ 已完成（今天）
| 项目 | 状态 |
|------|------|
| Ubuntu Node 配对 Gateway | jet-Ubuntu connected |
| rl-training-headers | MacBook 已启用 |
| Semantic Cache Server | 1166 条聊天索引 |
| Smart Context Hook | 每小时自动运行 |
| Ubuntu NAS 备份 | 每天 02:00 |
| OpenClaw 安装 | PyTorch 2.7.0 + RTX 2060 |

### ❌ 等待中
| 项目 | 状态 |
|------|------|
| OpenClaw-RL Server | GitHub 下载失败，需等网络 |

---

## 下一步任务（按优先级）

### P0 - 必须做

#### 1. OpenClaw-RL Server 搭建
- **依赖**：等 GitHub 访问恢复
- **目标**：Ubuntu 上跑 RL training 服务
- **文件**：`~/OpenClaw-RL/`

#### 2. Ubuntu 节点 Hook 开发
- **目标**：在每次 prompt 前检测节点状态
- **脚本**：`~/.openclaw/workspace/scripts/smart_context_hook.py`
- **待集成**：做成 OpenClaw plugin 自动触发

### P1 - 重要

#### 3. Semantic Memory 效果验证
- **测试**：新 session 是否正确加载上下文
- **验证方式**：对比有/无上下文时的回复质量

#### 4. rl-training-headers 验证
- **测试**：确认 header 注入正常
- **方法**：看 RL Server 日志是否有 session 数据

### P2 - 增强

#### 5. Semantic Cache 扩展
- **当前**：1166 条聊天
- **目标**：索引更多历史 + 支持更多查询模式
- **优化**：embedding 模型量化、批量索引

#### 6. NAS 备份扩展
- **当前**：每天 02:00 备份
- **目标**：增量备份 + 多版本保留
- **计划**：按周/月归档

#### 7. Phase 1 语音陪伴（硬件采购）
- **待采购**：USB 耳机
- **目标**：语音输入 → AI → 语音输出
- **依赖**：硬件到位后才能开始

### P3 - 规划中

#### 8. Phase 2 视觉记录
- ESP32-Cam 固件烧录
- Jetson Nano RTSP 接收
- 24小时录像存储

#### 9. 贵庚记忆系统深化
- 向量数据库升级
- 边权重实例模型调研
- RL 训练流程完善

---

## 每日检查清单

### 每次对话前
- [ ] 检查 Ubuntu 节点是否在线
- [ ] 检查 Semantic Cache 服务状态

### 每天
- [ ] 检查 MiniMax 额度
- [ ] 查看 Ubuntu NAS 备份是否成功
- [ ] 查看 Semantic Memory 更新日志

### 每周
- [ ] 检查 OpenClaw-RL 训练进度
- [ ] 评估命中率变化
- [ ] 备份配置更新

---

## 资源状态

### Ubuntu (192.168.1.18)
- **GPU**: RTX 2060 6GB
- **RAM**: 32GB（Semantic Cache 占用 ~2GB）
- **服务**: Semantic Cache :5050, SSH :22
- **备份**: ~/.semantic_cache/backups/

### MacBook Gateway (192.168.1.13)
- **服务**: OpenClaw Gateway :18789
- **插件**: rl-training-headers (已启用)
- **上下文**: ~/.openclaw/workspace/semantic-memory.md (每小时更新)

---

*最后更新：2026-03-28 21:17*
