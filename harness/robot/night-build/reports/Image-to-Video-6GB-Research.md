# 6GB 显存图生视频方案调研报告

**日期**: 2026-03-29
**硬件**: RTX 2060 6GB VRAM, 32GB RAM, Ubuntu 24.04
**已排除方案**: FramePack(OOM 8GB+)、Wan 2.1 I2V(无1.3B版本)、SVD(输出废视频)

---

## 一、方案对比总表

| 方案 | 模型大小 | VRAM需求 | 输出规格 | ComfyUI | 6GB可行? | 推荐度 |
|------|---------|---------|---------|---------|---------|--------|
| **AnimateDiff v2 + SparseCtrl** | 1.7GB+3.5GB | ~5GB | 512x512, 16帧 | ✅ Evolved | ✅ 社区验证 | ⭐⭐⭐⭐⭐ |
| **AnimateLCM-I2V** | 轻量LCM | ~3-4GB | 512x512, 8-16帧 | ✅ Evolved | ⚠️ 理论可行 | ⭐⭐⭐⭐ |
| **LightX2V (Wan 2.1 优化)** | 14B/1.3B | ~8GB(4060验证) | 480P-720P | ✅ | ❓ 待测 | ⭐⭐⭐ |
| **Wan 2.1 T2V-1.3B + offload** | 1.3B | 8.19GB官方 | 480P | ✅ | ❌ 超出 | ⭐⭐ |
| **DiffSynth-Studio FP8** | 14B→FP8 | ~16-18GB | 480P | ❌ 独立 | ❌ 超出 | ⭐ |
| Replicate Wan 2.1 API | 云端 | 不占用 | 480P/720P | - | ✅ | ⭐⭐⭐⭐ |

### 已排除的大模型方案

| 方案 | VRAM需求 | 排除原因 |
|------|---------|---------|
| PIA (CVPR 2024) | 16GB | 论文明确标注 |
| StoryDiffusion (NeurIPS 2024) | 24GB+ | 低显存版也需20GB+ |
| I2VGen-XL (阿里) | 12GB+ | 未见低显存报告 |
| Open-Sora-Plan (字节) | 12GB+ | 未见低显存报告 |
| CogVideoX-2B | ~10GB | 超出6GB |

---

## 二、推荐方案详解

### 🥇 AnimateDiff v2 + SparseCtrl (最推荐)

**原理**: 在 Stable Diffusion 1.5 基础上加 Motion Module，让静态图片动起来。SparseCtrl 扩展支持图像条件输入实现图生视频。

**技术栈**:
- AnimateDiff Motion Module v2: `mm_sd_v15_v2.ckpt` (1.7GB)
- Stable Diffusion 1.5: v1-5-pruned-emaonly (~3.5GB fp16)
- SparseCtrl RGB: `v3_sd15_sparsectrl_rgb.ckpt` (1.85GB) — 图生视频
- ComfyUI 集成: `ComfyUI-AnimateDiff-Evolved`

**VRAM 明细** (512x512, 16帧):
- SD1.5 fp16: ~3.5GB
- Motion Module: ~1.7GB
- ComfyUI 开销: ~0.5GB
- **总计: ~5-5.7GB** ✅ 6GB 可行

**输出**:
- 512x512, 16帧 (可通过 sliding window 延长)
- 推理速度: ~5-10秒/16帧 (RTX 2060 估算)

**优化技巧**:
1. fp16 精度 (ComfyUI 默认)
2. 低分辨率 512x512 或 384x384
3. 限制帧数到 16 帧
4. 低步数 (LCM 模式可降到 4-8 步)

**下载链接**:
- Motion Modules: https://huggingface.co/guoyww/animatediff
- ComfyUI 节点: https://github.com/Kosinkadink/ComfyUI-AnimateDiff-Evolved
- SparseCtrl: https://huggingface.co/guoyww/animatediff (v3_sd15_sparsectrl_rgb.ckpt)
- Colab 参考: https://colab.research.google.com/github/camenduru/AnimateDiff-colab/blob/main/AnimateDiff_colab.ipync

---

### 🥈 AnimateLCM-I2V (备选，更快)

**原理**: LCM (Latent Consistency Model) 架构，专为快速推理和低显存设计。

**优势**:
- 步数降到 4-8 步 (vs 标准 20-50 步)
- VRAM 更低 (~3-4GB)
- 同样支持 ComfyUI-AnimateDiff-Evolved

**设置**:
- beta_schedule: `lcm` 或 `autoselect`
- steps: 4-8
- CFG: 1.0-2.0

**下载**: https://huggingface.co/wangfuyun/AnimateLCM-I2V

---

### 🥉 LightX2V (探索方向)

**原理**: Wan 2.1 的推理优化框架，集成多种加速技术。

**关键信息**:
- GitHub: https://github.com/ModelTC/LightX2V
- 官方在 RTX 4060 8GB 上验证过
- 6GB 不确定，但配合 offload + 1.3B 模型可能可行

---

## 三、云端 API 方案（本地方案不可行时的备选）

| 服务 | 价格 | 免费 | 分辨率 | API |
|------|------|------|--------|-----|
| Replicate Wan 2.1 I2V 480P | $0.45/5秒 | ❌ | 480P | [链接](https://replicate.com/wavespeedai/wan-2.1-i2v-480p) |
| Replicate Wan 2.1 I2V 720P | $1.25/5秒 | ❌ | 720P | [链接](https://replicate.com/wavespeedai/wan-2.1-i2v-720p) |
| 可灵 (Kling) | 待确认 | 有免费额度 | 高清 | https://www.klingai.com |
| MiniMax 海螺 | 待确认 | 有免费额度 | 高清 | https://www.minimax.io |
| Luma Dream Machine | 待确认 | 有免费额度 | 高清 | https://lumalabs.ai/dream-machine |

---

## 四、本地部署步骤 (AnimateDiff v2)

### Step 1: 清理显存
```bash
# 检查显存占用
nvidia-smi
# 杀掉占用 GPU 的进程（除 X11 外）
```

### Step 2: 安装 ComfyUI 自定义节点
```bash
cd ~/ComfyUI
pip install -q git+https://github.com/Kosinkadink/ComfyUI-AnimateDiff-Evolved.git
```

### Step 3: 下载模型
```bash
# SD1.5 基础模型
cd ~/ComfyUI/models/checkpoints/
wget https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors

# AnimateDiff Motion Module v2
cd ~/ComfyUI/models/animatediff_models/
wget https://huggingface.co/guoyww/animatediff/resolve/main/mm_sd_v15_v2.ckpt

# SparseCtrl RGB (图生视频)
wget https://huggingface.co/guoyww/animatediff/resolve/main/v3_sd15_sparsectrl_rgb.ckpt

# AnimateLCM (可选，加速)
wget https://huggingface.co/wangfuyun/AnimateLCM-I2V/resolve/main/AnimateLCM-I2V.safetensors
```

### Step 4: 启动 ComfyUI
```bash
cd ~/ComfyUI
python main.py --lowvram --preview-method auto --listen 0.0.0.0 --port 8188
```

### Step 5: 测试工作流
- 使用 AnimateDiff Evolved 节点加载 Motion Module
- 加载输入图片 (Load Image 节点)
- 连接 SparseCtrl 图像条件
- 设置参数: 16帧, 512x512, steps=20

### 预期结果
- 推理时间: ~5-15秒 (RTX 2060)
- VRAM 峰值: ~5.5GB
- 输出: 16帧 512x512 GIF/MP4

---

## 五、结论

**6GB 显存完全可以跑图生视频**，关键是用对模型——AnimateDiff v2 + SparseCtrl，而非 Wan 2.1 14B 这种大模型。

**推荐路径**:
1. 先部署 AnimateDiff v2 + ComfyUI（确定性最高）
2. 测试 AnimateLCM-I2V 加速效果
3. 如果质量不够，再试 LightX2V + Wan 2.1 1.3B（风险较高）
4. 云端 API 作为质量不满足时的备选

---

*调研来源: 3 个并行 subagent (web_search + web_fetch)，2026-03-29 21:13*
