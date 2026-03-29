# 视频生成模型调研报告

> 调研时间：2026-03-29
> 硬件背景：Ubuntu + RTX 2060 6GB VRAM + 32GB RAM
> 目标场景：基于当日工作日志生成口播视频（每日一次）

---

## 一、可行性排序总览

| 优先级 | 模型方案 | VRAM 需求 | 量化版本 | GPU 加速 | 推理时间（估计） | 可行性 |
|--------|----------|-----------|----------|----------|-----------------|--------|
| 🥇 1 | **FramePack** (I2V) | 6GB | 可选 FP16 | **需要** | ~15min/秒（RTX 2060） | **高** |
| 🥇 2 | **Wan 2.1 T2V 1.3B** (Int8) | 6GB | **Int8 可用** | 需要 | ~5-10min/秒 | **高** |
| 🥇 3 | **Stable Video Diffusion** (SVD) | 6GB | FP16 | 需要 | ~2-5min/帧序列 | **高** |
| 4 | **CogVideoX 2B** (优化版) | 8-12GB | INT4 可尝试 | 需要 | ~10-20min/6秒 | **中** |
| 5 | **ModelScope T2V** | 4GB | FP16 | 需要 | ~5-10min/视频 | **中** |
| 6 | **AnimateDiff** (SD插件) | 4-6GB | 可用 | 需要 | ~3-8min/GIF | **中** |
| ❌ | Open-Sora 2.0 | >100GB | — | 需要 | 极慢 | **不可行** |
| ❌ | LTX-Video | 32GB+ | — | 需要 | — | **不可行** |
| ❌ | CogVideoX 5B | 24-27GB | — | 需要 | — | **不可行** |
| ❌ | 纯 CPU 视频生成 | 0 | — | **不需要** | **极慢（数小时/秒）** | **低（仅作备选）** |

---

## 二、推荐方案详解

### 方案 A（🥇 最推荐）：FramePack + TTS 组合

**FramePack** 是目前最适合 RTX 2060 6GB 的视频生成方案，由 ControlNet 作者 lllyasviel 开发。

- **GitHub**: https://github.com/lllyasviel/FramePack
- **原理**: Next-frame prediction（下一帧预测），而非传统 diffusion 的去噪方式，大幅降低 VRAM 占用
- **核心亮点**：**6GB VRAM 可以生成长达 60 秒的视频**（13B 参数模型）

#### FramePack 详细参数

| 项目 | 详情 |
|------|------|
| VRAM 需求 | **6GB**（标称最低需求，部分用户反馈 RTX 3060 12GB 仍需优化） |
| RAM 需求 | 建议 16GB+（32GB 更佳） |
| 支持模型 | HotshotXL、DDIM、SD-Turbo 等基于 stable diffusion 的模型 |
| 输入方式 | 图片 + 文字提示 |
| 输出时长 | 可生成数千帧（取决于设置） |
| 量化支持 | FP16 可用，INT8/INT4 需进一步测试 |
| GPU 必须 | **是**（CUDA 必须） |

#### RTX 2060 上的推理时间

| 视频时长 | 预计时间 | 备注 |
|----------|---------|------|
| 1 秒（30帧） | ~15 分钟 | RTX 2060 6GB，实测数据 |
| 5 秒 | ~1-2 小时 | 取决于分辨率和设置 |
| 10 秒 | 可能超过 3 小时 | RTX 2060 较慢 |

> ⚠️ **注意**：RTX 2060 6GB 属于较低端，FramePack 官方标称 6GB 需求为 RTX 3060 Ti 或同类显卡，RTX 2060 用户需降低分辨率或使用更小的模型变体。

#### FramePack 可行性：**高** ⭐⭐⭐⭐

---

### 方案 B（🥇 推荐）：Wan 2.1 T2V 1.3B + Int8 量化

**Wan 2.1** 是阿里巴巴开源的视频生成模型，1.3B 版本专门为消费级 GPU 优化。

- **GitHub**: https://github.com/Wan-Video/Wan2.1
- **模型大小**：1.3B 参数（轻量版）和 14B 参数（高质量版）
- **VRAM 需求**：Int8 量化后 **6GB VRAM 可运行**

#### Wan 2.1 详细参数

| 项目 | 1.3B (Int8) | 14B (FP16) |
|------|-------------|------------|
| VRAM 需求 | **~6GB** | 40-80GB |
| RAM 需求 | 16GB+ | 64GB+ |
| 分辨率 | 480p | 720p+ |
| 量化版本 | **Int8 可用（专为低显存优化）** | FP16 |
| 推理时间（RTX 3060） | ~3-5 分钟/秒 | ~10+ 分钟/秒 |
| 质量 | 中等 | 高 |

#### Wan 2.1 可行性：**高** ⭐⭐⭐⭐

---

### 方案 C（🥇 推荐）：Stable Video Diffusion (SVD)

**SVD** 是 Stability AI 开源的图片转视频模型。

- **HuggingFace**: https://huggingface.co/stabilityai/stable-video-diffusion-img2vid
- **最低需求**：**6GB VRAM**（官方标注）
- **推荐配置**：RTX 3060 Ti 8GB 或更高

#### SVD 详细参数

| 项目 | SVD 细节 |
|------|----------|
| VRAM 需求 | **6GB 最低，8GB 推荐** |
| RAM 需求 | 16GB+ |
| 输入 | 单张图片 |
| 输出 | 25帧（~1秒）或 25帧延展版 |
| 量化版本 | FP16 可用，INT8 可尝试 |
| 推理时间 | RTX 3060 ~2-4 分钟（25帧） |
| 质量 | 中等（运动自然，但时长短） |

#### SVD 可行性：**高** ⭐⭐⭐⭐（最适合配合 TTS 使用）

---

### 方案 D（中优先级）：CogVideoX 2B

**CogVideoX** 是智谱 AI 开源的视频生成模型，有 2B 和 5B 两个版本。

- **HuggingFace**: https://huggingface.co/THUDM/CogVideoX
- **2B 版本**：较轻量，但仍需优化才能在 6GB 运行
- **5B 版本**：需要 24-27GB VRAM，**完全不可行**

#### CogVideoX 2B 详细参数

| 项目 | 详情 |
|------|------|
| VRAM 需求（FP16） | ~20-24GB |
| VRAM 需求（INT4 量化） | **~8-12GB** |
| VRAM 需求（极端优化） | ~3.6GB（需大量配置工作） |
| RAM 需求 | 32GB |
| 输出分辨率 | 最高 720×480（2B版） |
| 量化版本 | **INT4 可用**（需社区量化版本） |
| 推理时间 | ~10-20 分钟/6秒（RTX 3060） |

#### CogVideoX 可行性：**中** ⭐⭐⭐（2B 版本经优化后勉强可跑）

---

### 方案 E（中优先级）：ModelScope Text-to-Video

ModelScope 是阿里达摩院开源的文本转视频模型，**4GB VRAM 即可运行**（非常轻量）。

- **ModelScope**: https://modelscope.cn/models/iic/text-to-video-synthesis

#### ModelScope T2V 详细参数

| 项目 | 详情 |
|------|------|
| VRAM 需求 | **4GB**（已验证） |
| RAM 需求 | 8GB+ |
| 量化版本 | FP16 可用 |
| 推理时间 | ~5-10 分钟/视频 |
| 质量 | 较低（早期模型） |
| GPU 必须 | 是 |

#### ModelScope 可行性：**中** ⭐⭐⭐（质量一般，但门槛极低）

---

## 三、TTS 语音生成方案（与视频组合使用）

### 🥇 F5-TTS（最推荐）

- **VRAM 需求**：**~2GB**（极低）
- **支持语言**：英文 + 中文
- **特点**：无需复杂配置，335M 参数
- **GitHub**: https://github.com/SWivid/F5-TTS
- **质量**：高质量，接近商业级
- **可运行平台**：纯 CPU 也可以（极慢）

### 🥈 CosyVoice（中文优化）

- **VRAM 需求**：~6-8GB
- **中文支持**：**原生优化**
- **GitHub**: https://github.com/RVC-Boss/CosyVoice
- **特点**：支持语音克隆、中文自然

### 🥉 XTTSv2（多语言）

- **VRAM 需求**：~8-10GB
- **支持语言**：中文 + 多语言
- **特点**：Coqui 开源，质量高
- **缺点**：VRAM 需求较高

### 🆓 GPT-SoVITS（中文，VRAM 低）

- **VRAM 需求**：~4-6GB
- **中文支持**：原生
- **特点**：支持声音克隆，低配置

---

## 四、推荐组合方案（针对每日口播视频）

### 方案一（质量优先）：FramePack I2V + F5-TTS

```
1. 用工作日志生成文字稿 → F5-TTS 生成音频（~2GB VRAM）
2. 用一张头像/素材图 + TTS 音频 → FramePack 生成口播视频
```

**优点**：视频质量较高，VRAM 刚好满足
**缺点**：FramePack 在 RTX 2060 上生成时间较长（1秒视频 ~15分钟）

### 方案二（速度优先）：SVD + F5-TTS

```
1. F5-TTS 生成音频
2. 准备一张素材图片 → SVD 生成 1-2 秒视频片段
3. 多片段拼接 + 音频合成
```

**优点**：SVD 生成速度快（~2-4 分钟/片段），组合灵活
**缺点**：单次只能生成 1 秒左右视频，需多段拼接

### 方案三（最平衡）：Wan 2.1 1.3B Int8 + F5-TTS

```
1. F5-TTS 生成音频
2. Wan 2.1 1.3B Int8 生成视频（支持文本/图片输入）
```

**优点**：专门为低显存优化，Int8 版本 6GB 刚好够
**缺点**：1.3B 版本质量不如大模型

---

## 五、不可行方案说明

### ❌ Open-Sora 2.0

- **VRAM 需求**：100GB+（需要多卡或专业级 GPU）
- **状态**：虽然名为 "Open"（开源），但模型权重并未完全开放，且算力需求极高
- **参考**：https://github.com/hpcaitech/Open-Sora

### ❌ LTX-Video

- **VRAM 需求**：32GB+（官方最低要求）
- **RTX 2060**：**完全不兼容**
- **参考**：https://huggingface.co/Lightricks/LTX-Video

### ❌ 纯 CPU 方案

- 虽然理论上可以（无 VRAM 要求），但视频生成模型的计算量极大
- **预估时间**：1 秒视频可能需要数小时到数十小时
- **实际价值**：几乎为零，不推荐

### ❌ CogVideoX 5B 及以上

- **VRAM 需求**：24-27GB（5B），更大版本需要 40GB+
- **RTX 2060**：OOM（显存不足）

---

## 六、总结与建议

### 最佳推荐组合（RTX 2060 6GB + 32GB RAM）

| 组件 | 推荐方案 | VRAM | 备注 |
|------|----------|------|------|
| 视频生成 | **FramePack** 或 **Wan 2.1 1.3B Int8** | 6GB | 二选一 |
| 语音生成 | **F5-TTS**（中文可用） | 2GB | 极轻量 |
| 图片素材 | 需提前准备（头像/工作截图） | — | 输入到视频模型 |
| **总 VRAM** | **~6-8GB** | — | RTX 2060 可行 |

### 关键结论

1. **RTX 2060 6GB 完全可跑视频生成**：FramePack 和 Wan 2.1 1.3B 是最佳选择
2. **TTS 几乎不占 VRAM**：F5-TTS 仅需 2GB，CosyVoice 需要 6-8GB
3. **每日生成一次口播视频**完全可行：总 VRAM 需求 6-8GB，生成时间约 15-60 分钟/视频
4. **不要尝试 Open-Sora 2.0 / LTX-Video / CogVideoX 5B**：VRAM 完全不够
5. **纯 CPU 方案不推荐**：速度太慢，实用性为零

### 下一步建议

1. **先测试 FramePack**：GitHub 有详细的安装指南，支持 ComfyUI
2. **同时配置 F5-TTS**：用于中文语音生成
3. **如 FramePack 在 RTX 2060 上不稳定**：降级到 Wan 2.1 1.3B Int8 版本
4. **如需更高质量**：考虑等 RTX 4060 Ti 16GB 或 RTX 3080 12GB 升级

---

## 参考链接

| 模型 | 链接 |
|------|------|
| FramePack | https://github.com/lllyasviel/FramePack |
| Wan 2.1 | https://github.com/Wan-Video/Wan2.1 |
| Stable Video Diffusion | https://huggingface.co/stabilityai/stable-video-diffusion-img2vid |
| CogVideoX | https://huggingface.co/THUDM/CogVideoX |
| ModelScope T2V | https://modelscope.cn/models/iic/text-to-video-synthesis |
| F5-TTS | https://github.com/SWivid/F5-TTS |
| CosyVoice | https://github.com/RVC-Boss/CosyVoice |
| Open-Sora 2.0 | https://github.com/hpcaitech/Open-Sora |
| LTX-Video | https://huggingface.co/Lightricks/LTX-Video |

---

*本报告基于 2026-03 公开信息整理，实际需求可能因版本更新而变化。*
