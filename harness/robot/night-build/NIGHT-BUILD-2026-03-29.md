# Night Build — 2026-03-29 夜间任务

**生成时间**: 2026-03-29 21:26 GMT+8
**当前状态**: 4 个待执行任务，依赖关系 T-030 → T-031

---

## ⚠️ 执行前环境检查（必须做）

### 1. Ubuntu 显存状态
```
当前显存: 86MiB / 6144MiB (5647MiB 空闲)
Semantic Cache: 已切到 CPU 模式（释放 ~1.3GB VRAM）
FramePack: 已杀（释放 ~586MB VRAM）
```

### 2. 关键进程
| 进程 | PID | 端口 | 状态 |
|------|-----|------|------|
| Semantic Cache | 新PID | 5050 | ✅ CPU 模式运行中 |
| X11 | 2611 | - | 系统进程，勿杀 |
| gnome-shell | 2890 | - | 系统进程，勿杀 |

### 3. SSH 连接
```bash
ssh -o ConnectTimeout=10 -o ServerAliveInterval=5 jet@192.168.1.18
```

### 4. HF Mirror（下载模型必须用）
```bash
export HF_ENDPOINT=https://hf-mirror.com
```

---

## 任务列表

### T-030: AnimateDiff + ComfyUI 图生视频部署测试 ⭐ 最高优先

**参考文档**: `harness/robot/night-build/reports/Image-to-Video-6GB-Research.md`
**目标**: 在 RTX 2060 6GB 上成功生成图生视频

#### Step 1: 安装 ComfyUI-AnimateDiff-Evolved
```bash
cd ~/ComfyUI
pip install -q git+https://github.com/Kosinkadink/ComfyUI-AnimateDiff-Evolved.git
```

#### Step 2: 下载模型（用 HF Mirror）
```bash
export HF_ENDPOINT=https://hf-mirror.com

# SD1.5 基础模型
mkdir -p ~/ComfyUI/models/checkpoints/
cd ~/ComfyUI/models/checkpoints/
wget https://hf-mirror.com/stable-diffusion-v1-5/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors

# AnimateDiff Motion Module v2
mkdir -p ~/ComfyUI/models/animatediff_models/
cd ~/ComfyUI/models/animatediff_models/
wget https://hf-mirror.com/guoyww/animatediff/resolve/main/mm_sd_v15_v2.ckpt

# SparseCtrl RGB (图生视频)
wget https://hf-mirror.com/guoyww/animatediff/resolve/main/v3_sd15_sparsectrl_rgb.ckpt

# AnimateLCM I2V (可选，加速)
cd ~/ComfyUI/models/animatediff_models/
wget https://hf-mirror.com/wangfuyun/AnimateLCM-I2V/resolve/main/AnimateLCM-I2V.safetensors
```

#### Step 3: 启动 ComfyUI
```bash
cd ~/ComfyUI
nohup python main.py --lowvram --preview-method auto --listen 0.0.0.0 --port 8188 > /tmp/comfyui.log 2>&1 &
disown
```

#### Step 4: 验证启动
```bash
# 等待 30 秒
sleep 30
curl -s http://localhost:8188/system_stats | python3 -m json.tool
```

#### Step 5: 测试图生视频
- 通过 ComfyUI API 提交工作流（需要预先准备 workflow JSON）
- 或者用 Python 脚本调用 ComfyUI API
- 记录：VRAM 占用、推理时间、输出质量

#### Step 6: 记录结果
- 输出视频文件路径
- VRAM 峰值 (`nvidia-smi`)
- 推理时间
- 输出分辨率和帧数

---

### T-031: Semantic Cache 切回 CUDA + 验证

**依赖**: T-030 完成后执行
**原因**: 图生视频测试需要完整 VRAM，测试完后切回 CUDA 提升 Semantic Cache 性能

#### Step 1: 切回 CUDA
```bash
sed -i 's/device="cpu"/device="cuda"/' /home/jet/semantic_cache/server.py
```

#### Step 2: 重启
```bash
kill $(pgrep -f "python3.*server.py")
cd /home/jet/semantic_cache
nohup ~/miniconda/bin/python3 server.py > /tmp/semantic_cache.log 2>&1 &
disown
```

#### Step 3: 验证（等待 30 秒）
```bash
sleep 30
curl -s http://localhost:5050/health
curl -s -X POST http://localhost:5050/search \
  -H "Content-Type: application/json" \
  -d '{"query":"贵庚记忆系统","top_k":3}'
```

---

### T-032: zhiku 脚本修复验证

**原因**: 修复了 MCP server 路径但 5 平台全部 fetch failed

#### Step 1: 确保 Chrome 运行
```bash
pgrep -f "Chrome.*9223" || nohup /usr/bin/google-chrome --remote-debugging-port=9223 --user-data-dir="$HOME/.config/google-chrome/Chrome-Debug-Profile" &
```

#### Step 2: 测试
```bash
cd ~/.openclaw/workspace
node skills/zhiku/scripts/zhiku-ask.js "回复OK"
```

#### Step 3: 如果 fetch failed
- 检查各 MCP server 的 cookie 获取是否正常
- 可能需要重新登录各平台
- 记录每个平台的错误

---

### T-033: 清理 Ubuntu 残留文件

**预估释放**: 6-8GB 磁盘空间

#### Step 1: 清理未完成的下载
```bash
rm -rf ~/ComfyUI/models/diffusion_models/wan2.1-t2v-1.3b
```

#### Step 2: 清理缓存
```bash
du -sh ~/.cache/pip ~/.cache/torch ~/.cache/huggingface 2>/dev/null
rm -rf ~/.cache/pip
# torch 和 huggingface cache 可能有用，先 du 看大小再决定
```

#### Step 3: Conda 清理
```bash
~/miniconda/bin/conda clean --all -y
```

#### Step 4: 对比
```bash
df -h /
```

---

## 执行顺序

```
T-030 (AnimateDiff 部署) → T-031 (切回 CUDA)
       ↕ 并行
T-032 (zhiku 修复)
T-033 (清理磁盘)
T-034 (Turbo Clock 调研)
```

T-030 和 T-032/T-033/T-034 可以并行，T-030 完成后执行 T-031。

---

### T-034: 调研 Google Turbo Clock 压缩算法

**用户原话**: "谷歌最近好像新出了一个 Turbo Clock 的压缩算法，可以大幅度减少内存还是显存的使用"

#### 背景
用户不确定具体名称，需要先确认技术是否存在，然后评估对 0-1 项目的影响。

#### 搜索方向
1. "Google Turbo Clock compression algorithm"
2. "Google Turbo Clock memory VRAM reduction"
3. "谷歌 Turbo Clock 压缩算法"
4. 如果搜不到 Turbo Clock，搜索类似技术：
   - "Google Clockwork compression"
   - "TurboSparse Google"
   - "PowerInfer Google compression"
   - "Google latest compression algorithm 2025 2026"
   - "LLM inference memory optimization Google 2026"

#### 评估维度
- 算法原理（压缩什么：权重、激活、KV Cache？）
- 对 VRAM 的实际节省幅度
- 对我们硬件的适用性：Jetson Nano 2GB（CPU推理为主）+ RTX 2060 6GB（GPU推理）
- 能否集成到 ComfyUI（AnimateDiff 推理）或 OpenClaw
- 是否开源、是否需要特定硬件支持

#### 输出
调研报告写入 `harness/robot/night-build/reports/Turbo-Clock-Research.md`

---

## 注意事项

1. **不要 pkill**，用 `kill <PID>` 精确杀进程
2. **下载模型必须用 HF Mirror**: `export HF_ENDPOINT=https://hf-mirror.com`
3. **不要碰 X11 和 gnome-shell**
4. **记录所有操作和结果**到今日 memory 日志
5. **完成后更新 project-board.json** 各任务状态
6. **Semantic Cache 临时切 CPU** → T-030 完成后 T-031 切回 CUDA
