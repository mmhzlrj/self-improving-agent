# ComfyUI + 6GB 显存图生视频调研报告

> 调研时间：2026-03-29
> 硬件背景：RTX 2060 6GB VRAM + 32GB RAM
> 目标：找到适合 6GB 显存的图生视频方案，以及通过 CLI/API 控制 ComfyUI 的方法

---

## 一、ComfyUI 最新版本信息

### 1.1 ComfyUI 版本现状（2026年3月）

ComfyUI 仍在持续活跃更新，主要特性包括：

| 版本特性 | 说明 |
|---------|------|
| **Python 版本** | 推荐 3.10-3.11，3.12 部分插件兼容性差 |
| **默认端口** | 8188（WebUI + API） |
| **工作流格式** | JSON（.json）或 Comfortscape（. cosy） |
| **自定义节点** | 大量第三方节点支持（Manager 管理） |

### 1.2 ComfyUI API 接口

ComfyUI 提供完整的 HTTP API，支持程序化提交工作流：

**核心端点**：

| 端点 | 方法 | 功能 |
|------|------|------|
| `GET /system_stats` | GET | 系统状态（GPU/CPU 占用） |
| `GET /model_list` | GET | 可用模型列表 |
| `POST /prompt` | POST | 提交工作流（核心） |
| `GET /history/{prompt_id}` | GET | 查询任务执行历史 |
| `GET /object_info` | GET | 节点类型和参数信息 |
| `WS /ws` | WebSocket | 实时进度推送 |

**提交工作流示例**：
```bash
# 提交工作流（prompt 格式为压缩后的 JSON）
curl -X POST http://localhost:8188/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": {...}, "extra_data": {...}}'

# 响应返回 prompt_id，用于查询结果
# {"prompt_id": "uuid-xxx", "number": 1}
```

**查询结果**：
```bash
curl http://localhost:8188/history/<prompt_id>
```

### 1.3 ComfyUI Manager（2026年更新）

- **自定义节点管理**：一键安装/更新第三方节点
- **模型管理**：自动下载模型权重
- **工作流分享**：支持从 GitHub/本地加载工作流
- **兼容性检查**：自动检测缺失依赖

---

## 二、适合 6GB 显存的图生视频方案

以下方案按推荐度排序，全部基于 ComfyUI 生态。

### 🥇 方案 1：FramePack（最推荐）

**来源**：GitHub - lllyasviel/FramePack
**原理**：Next-frame prediction（下一帧预测），非传统 diffusion 去噪方式

#### 技术参数

| 项目 | 参数 |
|------|------|
| **模型大小** | 13B 参数（SD 1.5/2.1 base） |
| **最低 VRAM** | **6GB** |
| **推荐 VRAM** | 8GB+ |
| **生成时长** | 可生成数千帧（~60秒视频） |
| **输入** | 单张图片 + 文字提示 |
| **输出分辨率** | 512×512 或 768×768 可选 |
| **推理时间（RTX 2060 6GB）** | ~15分钟/秒视频 |

#### Low VRAM 优化

| 优化手段 | 效果 |
|---------|------|
| **FP16 精度** | 减少 50% 显存占用 |
| **降低分辨率** | 从 768→512 可节省 ~2GB |
| **禁用 VAE 缓存** | 节省 ~1GB |
| **batch_size=1** | 必须设为 1 |

#### 优缺点

| 优点 | 缺点 |
|------|------|
| ✅ 6GB 可用（最低需求） | ❌ RTX 2060 生成慢（1秒 ~15分钟） |
| ✅ 可生成长达 60 秒视频 | ❌ 依赖 SD 模型版本 |
| ✅ 运动质量好 | ❌ 文字提示依赖较复杂 |
| ✅ 开源、可在 ComfyUI 使用 | ❌ RTX 2060 属于最低配置边界 |

---

### 🥇 方案 2：Wan 2.1 T2V 1.3B（Int8 量化）

**来源**：GitHub - Wan-Video/Wan2.1（阿里巴巴）
**类型**：图生视频（T2V+I2V）

#### 技术参数

| 项目 | 1.3B Int8 | 14B FP16 |
|------|-----------|----------|
| **VRAM 需求** | **~6GB** | 40-80GB |
| **RAM 需求** | 16GB+ | 64GB+ |
| **输出分辨率** | 480p | 720p+ |
| **量化** | **Int8 专用优化** | FP16 |
| **推理时间** | ~3-5 分钟/秒（RTX 3060） | ~10+ 分钟/秒 |

#### Low VRAM 优化

- ✅ **Int8 量化版专为低显存设计**，6GB 可直接运行
- ✅ 支持图片输入（图生视频模式）
- ✅ 阿里巴巴官方优化，国内访问快

#### 优缺点

| 优点 | 缺点 |
|------|------|
| ✅ 专门为低显存优化，Int8 版本 6GB 刚好 | ❌ 1.3B 版本质量不如大模型 |
| ✅ 国产模型，中文支持好 | ❌ 分辨率较低（480p） |
| ✅ 推理速度相对较快 | ❌ ComfyUI 节点支持可能不完整 |
| ✅ 显存占用稳定 | ❌ 需要下载 ~2-3GB 模型 |

---

### 🥇 方案 3：Stable Video Diffusion (SVD)

**来源**：HuggingFace - stabilityai/stable-video-diffusion-img2vid
**类型**：图生视频（Image-to-Video）

#### 技术参数

| 项目 | 参数 |
|------|------|
| **VRAM 最低** | **6GB** |
| **VRAM 推荐** | 8GB+ |
| **输出** | 25帧（~1秒）/ 25帧延展版 |
| **输入** | 单张图片 |
| **量化** | FP16 可用，INT8 可尝试 |
| **推理时间** | RTX 3060 ~2-4 分钟（25帧） |
| **分辨率** | 576×1024 或 1024×576 |

#### ComfyUI 节点

```
# 官方 ComfyUI 节点
ComfyUI → nodes_for_SVD → StableVideoDiffusion
```

#### 6GB 显存配置

```
- 帧数：14-24
- 分辨率：512×512 或 576×1024
- motion_bucket：127
- 禁用 dynamic identity（节省显存）
- batch_size：1
```

#### 优缺点

| 优点 | 缺点 |
|------|------|
| ✅ 官方支持 ComfyUI，节点完整 | ❌ 单次只能生成 ~1 秒视频 |
| ✅ 生成速度快（~2-4 分钟/片段） | ❌ 需要多段拼接才能得到长视频 |
| ✅ 6GB 显存可运行 | ❌ 运动幅度有限 |
| ✅ 质量稳定，社区活跃 | ❌ 文字控制能力弱 |
| ✅ 模型相对小（~2GB） | ❌ 长视频需要后期拼接 |

---

### 🥈 方案 4：CogVideoX 2B（INT4 量化）

**来源**：HuggingFace - THUDM/CogVideoX
**类型**：文生视频 + 图生视频（2B 参数版本）

#### 技术参数

| 项目 | FP16 | INT4 量化 |
|------|------|-----------|
| **VRAM 需求** | ~20-24GB | **~8-12GB** |
| **分辨率** | 最高 720×480 | 最高 480×360 |
| **输出时长** | 6 秒 | 4-6 秒 |
| **模型大小** | ~10GB | ~6GB（量化后） |

#### 6GB 可行性分析

⚠️ **CogVideoX 2B 原始版本需要 20GB+ 显存**，6GB 无法直接运行。
INT4 量化后降至 8-12GB，**仍超出 6GB 范围**。

极端优化方案（社区适配）：
- 禁用部分 attention 层
- 极度压缩分辨率（384×216）
- 理论最低 ~3.6GB（未稳定验证）

**结论**：不推荐 6GB 显存运行 CogVideoX。

---

### 🥈 方案 5：AnimateDiff + Stable Diffusion

**来源**：GitHub - guoyww/animatediff
**类型**：图生视频（基于 SD 的运动模块）

#### 技术参数

| 项目 | 参数 |
|------|------|
| **VRAM 需求** | **4-6GB** |
| **RAM 需求** | 8GB+ |
| **输出** | GIF 或 MP4 |
| **分辨率** | 512×512 或 768×768 |
| **输入** | 图片 + 文字提示 |
| **量化** | FP16 可用 |

#### 优缺点

| 优点 | 缺点 |
|------|------|
| ✅ 4GB 即可运行 | ❌ 输出是 GIF/短视频，非高质量视频 |
| ✅ 社区成熟，ComfyUI 节点完整 | ❌ 运动幅度和时长有限 |
| ✅ 可结合 SD 模型（SDXL/SD 1.5） | ❌ 与专业视频生成有差距 |

---

### 🥉 方案 6：HunyuanVideo（腾讯）

**来源**：Tencent/HunyuanVideo
**类型**：文生视频 + 图生视频

#### VRAM 需求

| 模型版本 | VRAM | 6GB 可行 |
|---------|------|----------|
| HunyuanVideo 13B | ~24-30GB | ❌ 不可行 |
| HunyuanVideo 架上优化版 | ~10-16GB | ❌ 不可行 |

**结论**：HunyuanVideo 对 6GB 显存不友好，不推荐。

---

## 三、低显存优化技术总结

### 3.1 已验证的优化手段

| 技术 | 显存节省 | 质量损失 | 备注 |
|------|----------|----------|------|
| **FP16 精度** | ~40-50% | 极小 | 几乎所有模型支持 |
| **INT8 量化** | ~50-60% | 可接受 | Wan 2.1 官方支持 |
| **INT4 量化** | ~70-75% | 明显 | 需要社区量化版本 |
| **Tile/Slice 推理** | ~30-50% | 无 | 将大图分块处理 |
| **CPU Offload** | 节省 ~2-4GB | 速度大幅下降 | 加载到 CPU/GPU 混合 |
| **禁用 VAE 缓存** | ~1GB | 无 | 每次重新解码 |
| **降低 batch_size** | ~1-2GB | 无 | 必须设为 1 |
| **降低分辨率** | ~2-4GB | 取决于场景 | 从 768→512 |

### 3.2 ComfyUI 内的低 VRAM 配置

```
# ComfyUI → Settings → VRAM
- Model Loading: Normal (VRAM 足够时)
- Model Loading: low VRAM (6GB 以下)
- Model Loading: medium (勉强够用)

# 推荐配置（6GB RTX 2060）
- pinned_memory: true
- force_fp16: true
- disable preload models: true
- unload model after generation: true
```

---

## 四、ComfyUI API 控制方式

### 4.1 HTTP API（最常用）

ComfyUI 默认在 `http://localhost:8188` 提供 HTTP API：

```python
import requests
import json

# 1. 获取工作流模板
# ComfyUI 界面 → 导出 workflow API (Copy as CURL 可获取 JSON)

# 2. 提交工作流
prompt_data = {
    "prompt": {
        "3": {"inputs": {"image": "/path/to/input.png"}},
        "4": {"inputs": {"text": "生成视频提示词"}},
        # ... 节点参数
    },
    "extra_data": {}
}

response = requests.post("http://localhost:8188/prompt", json=prompt_data)
result = response.json()
prompt_id = result["prompt_id"]

# 3. 轮询结果（也可以用 WebSocket）
import time
while True:
    history = requests.get(f"http://localhost:8188/history/{prompt_id}").json()
    if prompt_id in history:
        output_images = history[prompt_id]["outputs"]
        break
    time.sleep(2)
```

### 4.2 ComfyUI Python API（comfy API）

```python
# 直接调用 comfy API（非官方但常用）
import sys
sys.path.insert(0, "/path/to/ComfyUI")

from comfy import model_management

# 设置低 VRAM 模式
model_management.set_vram_limit("low")
```

### 4.3 通过 SSH + exec 远程控制

```
OpenClaw (Mac) 
  → exec SSH 
  → Ubuntu (RTX 2060) 
  → ComfyUI API (localhost:8188)
```

```bash
# 远程提交工作流
ssh user@192.168.x.x 'curl -X POST http://localhost:8188/prompt -d "{\"prompt\":{...}}"'

# 或者用 Python 脚本远程执行
ssh user@192.168.x.x 'python3 /path/to/submit_workflow.py'
```

### 4.4 ComfyUI API 客户端库

| 库 | 说明 |
|---|------|
| **comfy-cli** | 命令行工具提交工作流 |
| **comfyui-python-api** | 社区维护的 Python SDK |
| **ComfyUI-Manager** | 管理自定义节点（非 API 控制） |

---

## 五、CLI-Anything 对 ComfyUI 的控制

### 5.1 CLI-Anything 概述

CLI-Anything 是一个让 AI Agent 控制 GUI 应用的方法论，通过生成 Python harness 来实现程序化控制。

**已支持的应用**（从 workspace 调研）：
- GIMP（图像编辑）
- OBS（录屏）
- Blender（3D）

**当前状态**：**没有找到 ComfyUI 的 CLI-Anything harness**。

### 5.2 ComfyUI 的 CLI/自动化接口

ComfyUI 本身提供了良好的程序化接口（HTTP API），不需要像 GIMP 那样使用图像识别 + 鼠标模拟。ComfyUI 的控制方式是：

| 控制方式 | 适合场景 | 难度 |
|---------|---------|------|
| **HTTP API（POST /prompt）** | 程序化提交工作流 | ⭐ 简单 |
| **Python 直接调用** | 深度集成 | ⭐⭐ 中等 |
| **SSH + 命令行** | 远程控制 | ⭐ 简单 |
| **WebSocket 实时监控** | 进度跟踪 | ⭐⭐ 中等 |
| **图像识别 + 点击** | 不推荐 | ❌ 复杂且不稳定 |

### 5.3 CLI-Anything 兼容 ComfyUI 的建议

**结论**：ComfyUI 不需要 CLI-Anything 风格的图像识别 harness，因为已有成熟的 HTTP API。

**推荐方案**：
1. **用 Python 封装 ComfyUI API** → 生成 `comfyui-cli` 命令行工具
2. **用 HTTP 请求** → 直接用 `curl` 或 `requests` 控制
3. **用 ComfyUI Manager 管理节点** → 自动化安装自定义节点

**CLI-Anything 适用场景**（需要用图像识别的场景）：
- ComfyUI 界面操作教学（录制点击步骤）
- 非标准工作流的可视化调试

### 5.4 OpenClaw 控制 ComfyUI 的架构

```
┌─────────────────────────────────────┐
│  OpenClaw (Mac 主控)                │
│  - 调度任务                          │
│  - 语音合成 (TTS)                    │
│  - 结果整合                          │
└─────────────────────────────────────┘
          ↓ SSH/exec
┌─────────────────────────────────────┐
│  Ubuntu (RTX 2060 6GB)              │
│  - ComfyUI (port 8188)              │
│  - 视频生成模型（SVD/FramePack/Wan） │
│  - 图生视频工作流                    │
└─────────────────────────────────────┘
```

**OpenClaw exec 执行流**：
```bash
# 1. SSH 到 Ubuntu
ssh user@192.168.x.x "cd ComfyUI && python main.py &"

# 2. 等待 ComfyUI 启动
sleep 5

# 3. 提交工作流（通过 HTTP API）
curl -X POST "http://192.168.x.x:8188/prompt" \
  -H "Content-Type: application/json" \
  -d '{"prompt": {"3": {"inputs": {"image": "/tmp/input.png"}}, ...}}'

# 4. 等待结果（WebSocket 或轮询）
# 5. 下载结果视频
scp user@192.168.x.x:/path/to/output.mp4 /local/path/
```

---

## 六、推荐方案总结

### 6.1 RTX 2060 6GB 最佳选择

| 优先级 | 方案 | VRAM | 特点 |
|--------|------|------|------|
| 🥇 **1** | **FramePack + ComfyUI** | 6GB | 生成长，60秒，质量好，速度慢 |
| 🥇 **2** | **Wan 2.1 1.3B Int8** | ~6GB | 国产优化，速度快，质量中等 |
| 🥇 **3** | **SVD + ComfyUI** | 6GB | 速度最快，~1秒/片段，需拼接 |

### 6.2 针对口播视频场景的推荐

**场景**：每日工作日志生成口播视频（音频 + 视频 + 字幕）

**推荐组合**：

| 组件 | 推荐 | VRAM |
|------|------|------|
| **TTS 语音** | F5-TTS（2GB） | ~2GB |
| **视频生成** | FramePack（6GB）或 Wan 2.1 Int8（6GB） | ~6GB |
| **图片素材** | 提前准备（输入图） | 0 |
| **总 VRAM** | **~8GB（可接受）** | — |

**工作流**：
```
1. 工作日志 → F5-TTS → 音频文件
2. 头像/素材图 + 音频时长 → FramePack/Wan → 视频片段
3. 视频片段拼接 + 音频同步 → 最终口播视频
```

### 6.3 OpenClaw 集成建议

```python
# OpenClaw exec → SSH → Ubuntu → ComfyUI API
# 核心 Python 脚本示例
import requests
import json
import time

def generate_video(image_path, prompt, model="framepack"):
    """通过 ComfyUI API 生成视频"""
    # 1. 构建工作流（根据选择的模型）
    workflow = build_workflow(model, image_path, prompt)
    
    # 2. 提交到 ComfyUI
    response = requests.post("http://ubuntu-ip:8188/prompt", json=workflow)
    prompt_id = response.json()["prompt_id"]
    
    # 3. 轮询等待结果
    while True:
        history = requests.get(f"http://ubuntu-ip:8188/history/{prompt_id}").json()
        if prompt_id in history:
            return history[prompt_id]["outputs"]
        time.sleep(5)
```

---

## 七、参考链接

| 资源 | 链接 |
|------|------|
| ComfyUI GitHub | https://github.com/comfyanonymous/ComfyUI |
| FramePack | https://github.com/lllyasviel/FramePack |
| Wan 2.1 | https://github.com/Wan-Video/Wan2.1 |
| Stable Video Diffusion | https://huggingface.co/stabilityai/stable-video-diffusion-img2vid |
| CogVideoX | https://huggingface.co/THUDM/CogVideoX |
| AnimateDiff | https://github.com/guoyww/animatediff |
| CLI-Anything | `~/.openclaw/skills/cli-anything/SKILL.md` |

---

## 八、注意事项

1. **RTX 2060 6GB 属于配置边界**：FramePack 标称 6GB 需求为 RTX 3060 Ti 或同类，RTX 2060 可能需要降低分辨率或增加生成时间
2. **ComfyUI 版本更新频繁**：建议使用 ComfyUI Manager 管理节点和模型
3. **WebSocket 实时性好**：重度使用建议实现 WebSocket 进度跟踪，而非轮询
4. **模型下载**：SVD 最轻量（~2GB），Wan 2.1 Int8 约 2-3GB，FramePack 取决于 SD 版本

---

*本报告基于 2026-03-29 公开信息整理。实际效果需根据具体硬件和模型版本验证。*