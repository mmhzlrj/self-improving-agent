# FramePack 图生视频 RTX 2060 6GB 部署 SOP

> 调研时间：2026-03-30
> 目标硬件：NVIDIA RTX 2060 6GB (Turing TU104)
> 远程主机：jet@192.168.1.18

---

## 背景

FramePack 是斯坦福大学 Lvmin Zhang 团队（ControlNet 作者）推出的视频生成技术，核心创新是**固定长度时域上下文压缩**：将所有输入帧压缩到固定大小上下文（关键帧 1536 特征 token，过渡帧仅 192 token），使 VRAM 需求大幅降低。

官方宣称：**仅需 6GB 显存即可生成长达 60 秒的视频**（基于 Hunyuan 130 亿参数模型）。

**重要警告**：FramePack 官方文档明确要求 **RTX 30/40/50 系列 GPU（支持 FP16/BF16）**。RTX 2060 属于 Turing 架构，不在官方支持列表内。但多个中文平台（B 站、知乎、IT之家）均有用户在 RTX 2060 6GB 上成功运行的报告，且 ComfyUI-FramePackWrapper 插件提供了低 VRAM 优化路径。

---

## 方案对比

| 方案 | VRAM 需求 | 生成质量 | 生成速度（RTX 2060 估算） | 成熟度 | 备注 |
|------|-----------|---------|--------------------------|--------|------|
| **FramePack fp8_e4m3fn** | 5.5-6GB | 中等（fp8 量化） | ~5-10 秒/帧 | 高（斯坦福官方） | 需 ComfyUI-FramePackWrapper |
| **FramePack fp16** | 6-8GB | 高（原生精度） | ~3-8 秒/帧 | 高 | RTX 2060 可能 OOM |
| **AnimateDiff v2** | 4-5GB | 中等（SD1.5/SDXL） | ~3 分钟/16 帧 | 极高（社区验证） | RTX 2060 6GB 笔记本实测成功 |
| **Wan2.2 T2V-I2V 量化版** | 8GB+ | 高 | ~7 分钟/5 秒视频 | 中（阿里） | RTX 2060 勉强 |
| **LTX2-GGUF** | 8GB+ | 高 | 未知 | 中 | 明确要求 8GB |

**推荐优先级**：
1. **首选**：FramePack fp8_e4m3fn（目标方案）
2. **备选**：AnimateDiff v2（已验证可靠）
3. **备选**：云端 Replicate Wan2.1（$0.45/5秒，零显存占用）

---

## 方案一：FramePack fp8_e4m3fn（推荐，目标部署）

### 硬件状态确认

```bash
ssh jet@192.168.1.18 'nvidia-smi --query-gpu=memory.free,memory.total,driver_version,name --format=csv'
```

确保空闲显存 ≥ 5500 MiB。Semantic Cache 已切 CPU 模式，当前空闲约 6GB。

### Step 1：安装 ComfyUI（如尚未安装）

```bash
ssh jet@192.168.1.18 bash << 'EOF'
cd ~
# 检查是否已有 ComfyUI
if [ -d ~/ComfyUI ]; then
    echo "ComfyUI 已存在，跳过安装"
else
    git clone https://github.com/comfyanonymous/ComfyUI.git ~/ComfyUI
fi
# 安装依赖
cd ~/ComfyUI
pip install -r requirements.txt
EOF
```

### Step 2：安装 ComfyUI-FramePackWrapper 插件

```bash
ssh jet@192.168.1.18 bash << 'EOF'
cd ~/ComfyUI/custom_nodes
git clone https://github.com/kijai/ComfyUI-FramePackWrapper.git
cd ComfyUI-FramePackWrapper
pip install -r requirements.txt
EOF
```

### Step 3：下载模型文件

**必须在 Hugging Face 镜像站下载（国内直连）**：

```bash
ssh jet@192.168.1.18 bash << 'EOF'
COMFYUI=~/ComfyUI
MIRROR=https://hf-mirror.com

# 1. FramePack fp8 模型（低 VRAM 版本，必选）
mkdir -p $COMFYUI/models/diffusion_models
wget -c "$MIRROR/Kijai/framepack-hunyuan-video-fp8-e4m3fn/snapshots/main/framepack_hunyuan_video_fp8_e4m3fn.safetensors" \
  -O "$COMFYUI/models/diffusion_models/framepack_hunyuan_video_fp8_e4m3fn.safetensors"

# 2. VAE 模型（hunyuan_video_vae_bf16）
mkdir -p $COMFYUI/models/vae
wget -c "$MIRROR/Kijai/comfyui_framepack_vae/snapshots/main/hunyuan_video_vae_bf16.safetensors" \
  -O "$COMFYUI/models/vae/hunyuan_video_vae_bf16.safetensors"

# 3. CLIP Vision 模型
mkdir -p $COMFYUI/models/clip_vision
wget -c "$MIRROR/Kijai/sigclip-vision-transformer/snapshots/main/sigclip_vision_patch14_384.safetensors" \
  -O "$COMFYUI/models/clip_vision/sigclip_vision_patch14_384.safetensors"

# 4. T5 文本编码器（UMT5-xxL，用于提示词编码）
mkdir -p $COMFYUI/models/text_encoders
wget -c "$MIRROR/Kijai/hunyuan-video-tt2l-embedding/snapshots/main/hunyuan_video_t5_xxl_bf16.safetensors" \
  -O "$COMFYUI/models/text_encoders/hunyuan_video_t5_xxl_bf16.safetensors"

echo "模型下载完成"
ls -lh $COMFYUI/models/diffusion_models/
ls -lh $COMFYUI/models/vae/
EOF
```

> **如果下载中断**：使用 `wget -c` 断点续传，或使用 `curl -L -C - -o` 续传。

### Step 4：检查 VRAM 剩余（启动前）

```bash
ssh jet@192.168.1.18 'nvidia-smi --query-gpu=memory.free,memory.total --format=csv,noheader,nounits'
```

确保 ≥ 5500 MiB 可用。如不足，关闭其他进程：

```bash
ssh jet@192.168.1.18 'pkill -f "python.*semantic" || true; pkill -f "Chrome" || true; sleep 2; nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits'
```

### Step 5：启动 ComfyUI（低 VRAM 模式）

```bash
ssh jet@192.168.1.18 bash << 'EOF'
cd ~/ComfyUI
# 关键参数：
# --lowvram            启用低 VRAM 模式（将不活跃层卸载到 CPU）
# --cpu                如 fp8 版本仍 OOM，可尝试（速度极慢，不推荐）
# --disable-smart-memory  禁用智能内存管理，避免碎片化
python main.py \
  --lowvram \
  --port 8188 \
  --disable-smart-memory \
  2>&1 | tee ~/comfyui_framepack.log &
echo "ComfyUI PID: $!"
sleep 8
# 检查是否启动成功
curl -s http://localhost:8188/system_stats | head -c 200 || echo "等待启动..."
EOF
```

### Step 6：测试图生视频（通过 API）

```bash
ssh jet@192.168.1.18 bash << 'EOF'
# 检查是否有示例图片
ls -la ~/视频/ 2>/dev/null || ls -la ~/Pictures/ 2>/dev/null || echo "请上传测试图片到 ~/视频/ 目录"

# FramePack fp8 推荐参数：
# - total_second_length: 5（5 秒视频，30fps = 150 帧）
# - video_frames: 150（5 秒 @ 30fps）
# - steps: 20-25（fp8 量化后可用更多步数补偿质量）

# 通过 ComfyUI API 提交队列（需要先在 Web UI 加载工作流，或使用 prompt API）
# 查看日志确认 VRAM 使用情况
nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader,nounits
tail -20 ~/comfyui_framepack.log
EOF
```

### Step 7：验证输出

```bash
ssh jet@192.168.1.18 'find ~/ComfyUI/output -name "*.mp4" -mmin -30 | head -5'
```

### 预期结果

| 指标 | 预期值 |
|------|--------|
| VRAM 占用 | 5500-6000 MiB（满载） |
| 5 秒视频生成时间 | 20-40 分钟（RTX 2060 估算） |
| 输出分辨率 | 480×832 或 720×1280（可调） |
| 帧率 | 30 fps |
| 文件大小 | ~1-3 MB（5 秒） |

### 已知问题与解决

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| **OOM（显存不足）** | RTX 2060 Turing 不在官方支持列表，BF16 可能触发额外中间缓存 | 改用 fp8_e4m3fn 模型；启用 `--lowvram`；减少 `total_second_length` 到 3 秒 |
| **生成质量差/闪烁** | 提示词不专注动作 | 提示词只描述动作，不描述场景；使用"walking", "turning", "jumping"等动词 |
| **漂移（越往后质量越差）** | 帧数过长 | FramePack 有反向生成抗漂移设计，理论上 60 秒无漂移；如仍出现，减少帧数 |
| **启动报错 FP16/BF16 不支持** | Turing 不支持 BF16 | 检查 ComfyUI 是否以 FP16 加载模型；在 ComfyUI 设置中强制 FP32（极慢） |
| **速度极慢** | CPU offload | 确认 `--lowvram` 而不是 `--cpu`；确保模型在 GPU 而非全 CPU |

---

## 方案二：AnimateDiff v2（已验证备选）

Reddit 用户在 RTX 2060 6GB 笔记本上实测成功，16 帧约 3 分钟。

### 安装

```bash
ssh jet@192.168.1.18 bash << 'EOF'
cd ~/ComfyUI/custom_nodes
# AnimateDiff-Evolved 插件
git clone https://github.com/Kosinkadink/ComfyUI-AnimateDiff-Evolved.git
cd ComfyUI-AnimateDiff-Evolved
pip install -r requirements.txt

# 下载模型（SD1.5 + AnimateDiff mm_sd_v15_v2.ckpt）
COMFYUI=~/ComfyUI
MIRROR=https://hf-mirror.com
mkdir -p $COMFYUI/models/diffusion_models
mkdir -p $COMFYUI/models/animatediff_models

# SD1.5 base 模型
wget -c "$MIRROR/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors" \
  -O "$COMFYUI/models/checkpoints/v1-5-pruned-emaonly.safetensors"

# AnimateDiff mm_v15_v2（推荐，比 v3 更稳定）
wget -c "$MIRROR/guoyww/animatediff/snapshots/main/v3_sd15_mm.ckpt" \
  -O "$COMFYUI/models/animatediff_models/v3_sd15_mm.ckpt"
EOF
```

### 启动

```bash
ssh jet@192.168.1.18 'cd ~/ComfyUI && python main.py --lowvram --port 8188 &'
```

### 预期结果

| 指标 | 预期值 |
|------|--------|
| VRAM 占用 | 4000-5000 MiB |
| 16 帧生成时间 | ~3 分钟 |
| 输出质量 | 中等（SD1.5 基础质量） |

---

## 方案三：云端备选（零本地显存需求）

如本地方案持续 OOM，使用云端：

**Replicate Wan2.1 I2V**：
- 费用：$0.45/5 秒视频
- 显存需求：0（完全云端）
- API 文档：https://replicate.com/cministrator/wan-2-1-i2v

---

## 快速决策流程

```
nvidia-smi → 显存 ≥ 5500 MiB?
├── 是 → 尝试 FramePack fp8_e4m3fn + --lowvram
│         ├── 成功 → 记录 VRAM 和生成时间
│         └── OOM → 减少帧数到 90（3 秒）或改用 AnimateDiff
└── 否 → 先释放显存（pkill 其他 Python 进程）
              ↓
         再检查 ≥ 5500 MiB?
              ├── 是 → FramePack fp8
              └── 否 → AnimateDiff（4-5GB 需求）或云端
```

---

## 调研来源

| 来源 | 关键信息 |
|------|---------|
| IT之家 (2025-04-20) | FramePack 官方：6GB 显存可生成 60 秒视频，基于 Hunyuan 130B |
| framepack.net 中文博客 | ComfyUI-FramePackWrapper 安装指南，fp8 和 fp16 两个模型版本 |
| Bilibili 多视频 | FramePack 6GB 显存实测，ComfyUI 整合包教程 |
| Reddit r/StableDiffusion | AnimateDiff RTX 2060 6GB 笔记本实测：16 帧 3 分钟 |
| CSDN/Wan2.2 部署 | Wan2.2 T2V A14B 低显存命令：`--offload_model True --t5_cpu --convert_model_dtype` |
| Ubuntu Semantic Cache 历史 | FramePack 在 RTX 2060 6GB 上直接运行 OOM（未优化状态） |

---

## 下一步行动

1. **执行方案一（FramePack fp8）**，按上述步骤逐步执行
2. 每步后检查 `nvidia-smi` 显存占用
3. 成功生成后更新 project-board.json，记录实际 VRAM 占用和生成时间
4. 如 OOM，降级到方案二（AnimateDiff）

---

*本 SOP 由 subagent 调研产出，综合了 FramePack 官方文档、多平台用户案例和 Semantic Cache 历史记录。*
