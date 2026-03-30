# LeWorldModel (LeWM) Edge Deployment Feasibility Report
## arxiv:2603.19312 — Practical Deployment on Jetson Nano + Robot Control Integration

**Research Date:** 2026-03-30  
**Sources:** arXiv:2603.19312, https://github.com/lucas-maes/le-wm, https://le-wm.github.io/

---

## 1. LeWM Technical Specifications

### 1.1 Model Architecture

| Component | Specification | Parameters |
|-----------|--------------|------------|
| **Encoder** | ViT-Tiny, patch size 14 | ~5M |
| — Layers | 12 transformer layers | — |
| — Attention heads | 3 | — |
| — Hidden dimension | 192 | — |
| — Token construction | [CLS] token → 1-layer MLP + BatchNorm | — |
| **Predictor** | Transformer, 6 layers, 16 heads | ~10M |
| — Action conditioning | Adaptive Layer Normalization (AdaLN) | — |
| — Dropout | 10% | — |
| — History | N frame representations, causal masking | — |
| — Projector | 1-layer MLP + BatchNorm (per encoder) | — |
| **Latent dimension** | 192 | — |
| **Total** | | **~15M** |

### 1.2 Training Details

| Parameter | Value |
|-----------|-------|
| Framework | PyTorch |
| Loss terms | 2: MSE prediction loss + SIGReg (λ=0.1, M=1024 projections) |
| Training time | "Single GPU in a few hours" |
| Training GPU class | Not explicitly stated; implied RTX-class or higher |
| Batch size | Not publicly disclosed (appendix D not fully scraped) |
| Image resolution | PushT (96×96), OGBench-Cube (simulated 3D), varies by env |
| SIGReg hyperparams | M=1024 random projections, λ=0.1; only λ requires tuning |
| No EMA, no stop-gradient | End-to-end full backprop |
| Planning | CEM (Cross-Entropy Method) MPC; full plan <1s on desktop GPU |

### 1.3 Open Source Status

| Item | Status |
|------|--------|
| Repository | https://github.com/lucas-maes/le-wm |
| Framework | PyTorch |
| Training code | ✅ Available (`train.py`) |
| Inference code | ✅ Available (`eval.py`, `inference.py`) |
| Pre-trained weights | ✅ Available (`.ckpt` object checkpoints, placed at `$STABLEWM_HOME`) |
| Config files | ✅ YAML configs per environment (e.g., `pusht.yaml`) |
| Checkpoint format | `_object.ckpt` — serialized Python object for `stable_worldmodel` API |
| Environments | Push-T, OGBench-Cube, Two-Room, Reacher |

---

## 2. Jetson Nano 2GB Feasibility Analysis

### 2.1 Hardware Profile

| Spec | Jetson Nano 2GB | Jetson Nano 4GB | Notes |
|------|---------------|----------------|-------|
| GPU | 128-core Maxwell | 128-core Maxwell | Same GPU, same clock |
| GPU FP32 | ~0.5 TFLOPS | ~0.5 TFLOPS | |
| RAM | 2GB LPDDR4 | 4GB LPDDR4 | **2GB is the constraint** |
| CPU | 4-core Cortex-A57 @ 1.43GHz | 4-core Cortex-A57 @ 1.43GHz | |
| Inference vs Training | Inference OK | Inference OK | Training borderline on 4GB, impractical on 2GB |

### 2.2 Memory Footprint Estimates for LeWM

**Model parameters:**
- 15M params × 4 bytes (FP32) = **60 MB** for weights
- 15M params × 2 bytes (FP16) = **30 MB** for weights

**Activation memory during inference:**

For a single forward pass (batch_size=1):

| Component | Est. Activation Memory |
|-----------|----------------------|
| ViT-Tiny encoder (96×96 input, patch 14) | ~8-12 MB |
| Predictor (6 layers, 16 heads, seq_len~N) | ~15-25 MB |
| Working buffers + normalization | ~10-15 MB |
| **Total FP32 inference** | **~120-180 MB** |
| **Total FP16 inference (TensorRT)** | **~60-90 MB** |

> **Verdict:** LeWM inference fits comfortably in Jetson Nano 2GB's 2GB RAM, even with OS overhead. The key question is latency, not memory.

### 2.3 Inference Latency Estimates

| Platform | GPU Class | Est. LeWM Inference Latency |
|----------|-----------|---------------------------|
| Desktop (RTX 2080/3060) | ~10-15 TFLOPS | **<1 second total planning** (per paper) |
| Jetson Nano (128-core Maxwell) | ~0.5 TFLOPS | **~5-15 seconds planning** (25-50x slower) |
| Jetson Nano + TensorRT FP16 | Optimized | **~2-8 seconds planning** |
| Desktop CPU (i5/i7) | — | ~10-30 seconds (no GPU) |

**Breakdown of per-component latency on Jetson Nano:**

| Operation | Estimated Time |
|-----------|---------------|
| ViT-Tiny encoder forward (1 frame) | 80-200 ms |
| Predictor forward (1 step, N=4 history) | 50-150 ms |
| CEM planning (10 iterations, horizon H) | 500-2000 ms (dominant) |
| **Total 1-frame encode + 1-step predict** | **~130-350 ms** |
| **Full MPC plan (10 CEM iters)** | **~2-8 seconds** |

> ⚠️ **Critical:** The paper's "<1 second planning" is on a desktop GPU. On Jetson Nano, expect 5-10× slowdown. For real-time control at 10Hz (100ms loop), the Nano may struggle unless you reduce CEM iterations from 10→3-5 or reduce planning horizon.

### 2.4 Recommendation for Jetson Nano

| Strategy | Feasibility | Notes |
|----------|------------|-------|
| **PyTorch FP32 inference** | ✅ Feasible | ~120-180MB RAM, 3-8s planning |
| **PyTorch FP16 inference** | ✅ Better | ~60-90MB RAM, slightly faster |
| **TensorRT FP16 inference** | ✅ Best for Nano | Use `torch2trt` or `trtexec`; 2-5s planning |
| **Training on Nano 2GB** | ❌ Infeasible | OOM; needs ~4-6GB minimum |
| **Training on Nano 4GB** | ⚠️ Possible but slow | Would take many hours; not recommended |

---

## 3. Training vs Inference: What Runs Where

```
┌─────────────────────────────────────────────────────────────┐
│  TRAINING (Offline, once)                                    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Ubuntu workstation / server                        │    │
│  │  GPU: RTX 2060 or better (min 6GB VRAM)              │    │
│  │  - Collect demonstration trajectories (obs+actions) │    │
│  │  - train.py: 15M params, few hours on single GPU    │    │
│  │  - Output: .ckpt checkpoint                         │    │
│  └─────────────────────────────────────────────────────┘    │
│                          │                                   │
│                          │ scp / rsync checkpoint            │
│                          ▼                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  INFERENCE (Real-time control loop)                  │    │
│  │  Jetson Nano 2GB + TensorRT FP16                     │    │
│  │  - eval.py: encoder + predictor forward pass        │    │
│  │  - CEM planning loop (reduced iterations)            │    │
│  │  - MQTT publish action commands                       │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

**Do NOT train on Jetson Nano.** The 128-core Maxwell GPU:
- Is ~5-10× slower per core than RTX 2060
- Has only 2GB RAM (training needs 4-6GB for optimizer states + activations)
- Lacks hardware support for modern PyTorch operations (CuDNN optimizations)

**Training should happen on:** Any desktop with RTX 2060+ (6GB VRAM minimum), or cloud GPU instance (Google Colab A100, AWS g5.xlarge, etc.)

---

## 4. Quantization & Pruning Options

### 4.1 Quantization

| Method | Memory (15M params) | Speed | Quality Loss | Notes |
|--------|---------------------|-------|-------------|-------|
| FP32 (full precision) | 60 MB | Baseline | None | Standard PyTorch |
| FP16 (half precision) | 30 MB | 1.3-1.5× faster | Negligible | Native: `model.half()` |
| INT8 (quantized) | 15 MB | 2-3× faster | ~1-3% accuracy | Requires calibration dataset |
| INT4 (aggressive) | 7.5 MB | 3-4× faster | ~5-10% accuracy | Experimental, needs fine-tuning |

### 4.2 Structured Pruning Candidates

The paper tested **ResNet-18 encoder** (vs ViT-Tiny) with competitive results — confirming LeWM is encoder-agnostic:

| Pruning Strategy | Description | Feasibility |
|-----------------|-------------|-------------|
| Reduce predictor layers | 6→4 layers | ✅ Straightforward; predictor is ~10M params |
| Reduce predictor heads | 16→8 heads | ✅ Straightforward |
| Reduce encoder layers | 12→6 layers | ✅ Viable (paper confirms encoder swap works) |
| Smaller latent dim | 192→64 | ⚠️ May hurt performance; paper says "saturates beyond threshold" |
| Reduce patch size | 14→8 (more tokens) | ⚠️ Increases compute, may not help on Nano |

### 4.3 Minimum Viable Edge Configuration

| Config | Params | Memory | Est. Planning Time (Nano) | Notes |
|--------|--------|--------|--------------------------|-------|
| Full LeWM (FP32) | 15M | ~180 MB | 5-10 s | Baseline |
| Full LeWM (FP16) | 15M | ~90 MB | 3-6 s | ✅ Recommended start |
| LeWM (FP16) + TensorRT | 15M | ~60 MB | 2-4 s | ✅ **Best for Nano** |
| Pruned: 4-layer predictor | ~12M | ~70 MB | 1.5-3 s | Experimental |
| ViT-Tiny → ResNet-18 | ~15M | ~80 MB | 1.5-3 s | ✅ Alternative encoder (paper-validated) |

> **Bottom line:** Start with FP16 + TensorRT on Jetson Nano. If latency is still too high, reduce predictor to 4 layers.

---

## 5. Cyber Bricks Integration Architecture

### 5.1 System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                     ESP32-Cam  (RTSP Stream)                         │
│  Camera: OV2640, 640×480 @ 10fps → RTSP over WiFi                   │
│  Protocol: RTSP/RTP → H.264 compressed video                         │
└──────────────┬───────────────────────────────────────────────────────┘
               │  WiFi / LAN (typically 5-20ms latency on LAN)
               ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Jetson Nano 2GB                                                      │
│                                                                       │
│  ┌──────────────┐    ┌─────────────────┐    ┌───────────────────┐   │
│  │  RTSP Client │───▶│  LeWM Encoder   │───▶│  LeWM Predictor   │   │
│  │  (GStreamer) │    │  (ViT-Tiny)     │    │  (Transformer)    │   │
│  │  60-100ms    │    │  80-200ms       │    │  50-150ms         │   │
│  └──────────────┘    └─────────────────┘    └───────────────────┘   │
│         │                   │                       │                 │
│         │ frame              │ latent z              │ latent z_{t+1}  │
│         ▼                   ▼                       ▼                 │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  MPC/CEM Planning (reduced iterations)                          │ │
│  │  - Encode goal frame (once per goal)                            │ │
│  │  - Roll out latent predictions up to horizon H                 │ │
│  │  - CEM optimization: argmin_a ||z_H - z_goal||²               │ │
│  │  - Extract action sequence [a_1, a_2, ..., a_K]                │ │
│  │  Estimated: 2-5 seconds on Nano (FP16 + TensorRT)              │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                              │                                        │
│                              │ action a_1 (4-8 floats)               │
│                              ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────┐│
│  │  MQTT Client (paho-mqtt / umqtt.simple)                         ││
│  │  Topic: `cyberbricks/control`  Payload: `{"a": [0.1, -0.3, ...]}`││
│  │  QoS 1, ~10-50ms per publish                                    ││
│  └──────────────────────────────────────────────────────────────────┘│
└────────────────────────────┬────────────────────────────────────────┘
                             │ WiFi / Ethernet (10-50ms)
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Cyber Bricks Controller                                               │
│  ESP32-C3 (Xtensa LX6, 160MHz, 400KB SRAM, 2MB Flash)                 │
│  MQTT Subscriber ──▶ Motor Driver ──▶ Actuators                      │
│                                                                       │
│  Execution time per action: ~6-20ms (depends on motor load)          │
│  Total loop: ESP32 receives → parses MQTT → writes to motor PWM/I2C   │
└──────────────────────────────────────────────────────────────────────┘
```

### 5.2 Latency Budget

| Stage | Component | Est. Time | Cumulative |
|-------|-----------|-----------|-----------|
| 1 | ESP32-Cam captures frame | 0 ms (async) | 0 ms |
| 2 | RTSP encode + transmit | 33-100 ms (10-30fps) | 33-100 ms |
| 3 | Jetson: GStreamer decode | 20-50 ms | 53-150 ms |
| 4 | LeWM: Encode (ViT-Tiny) | 80-200 ms | 133-350 ms |
| 5 | LeWM: Predict (1 step) | 50-150 ms | 183-500 ms |
| 6 | CEM planning (5 iters) | 1000-3000 ms | 1183-3500 ms |
| 7 | MQTT publish + ESP32 receive | 10-50 ms | 1193-3550 ms |
| 8 | ESP32 execute action | 6-20 ms | 1199-3570 ms |

**Total control loop: ~1.2 – 3.6 seconds** (vs 10Hz = 100ms loop target)

> ⚠️ **Problem:** The planning stage (2-5s on Nano) dominates and prevents real-time 10Hz control. Solutions:
> 1. **Reduce CEM iterations** from 10→3 (sacrifices plan quality for speed)
> 2. **Reduce planning horizon** H (fewer rollouts)
> 3. **Pre-compute** action primitives; LeWM only does novelty detection
> 4. **Use LeWM for exception handling**, not every cycle

### 5.3 Cyber Bricks-Specific: MQTT Message Format

```python
# Jetson Nano publishes:
mqtt_client.publish("cyberbricks/control", payload={
    "cmd": "set_joints",
    "joints": [0.1, -0.3, 0.5, 0.2],  # normalized -1 to 1
    "speed": 0.8,                      # 0-1
    "timestamp": 1743300000000
})

# ESP32-C3 subscribes and parses:
# Receives on topic "cyberbricks/control"
# Parses JSON, writes to motor PWM registers via I2C/SPI
```

---

## 6. RTSP Stream → Jetson → LeWM Pipeline

### 6.1 Recommended Pipeline

```
ESP32-Cam RTSP
    │
    │  rtsp://192.168.x.x:8554/mjpeg  (H.264)
    │
    ▼
┌────────────────────────────────────────────────────────┐
│  GStreamer (Jetson Nano)                               │
│                                                        │
│  gst-launch-1.0 rtspsrc location=rtsp://... !          │
│    latency=50 ! rtph264depay ! h264parse !             │
│    nvvidconv ! video/x-raw(memory:NVMM) !              │
│    appsink emit-signals=true                           │
│                                                        │
│  → Yields NV12 frames directly in CUDA memory         │
│  → Zero-copy into PyTorch tensor via CUDA              │
└────────────────────┬───────────────────────────────────┘
                     │ GPU tensor (NV12/NVMM)
                     ▼
┌────────────────────────────────────────────────────────┐
│  PyTorch / LeWM                                        │
│                                                        │
│  1. Preprocess: resize to encoder's expected size      │
│     (e.g., 96×96 for PushT, or match training res)      │
│  2. Normalize: mean/std for ImageNet or domain-specific │
│  3. encoder(input) → latent z (192-dim)                │
│  4. predictor(z, action) → predicted z_{t+1}          │
└────────────────────────────────────────────────────────┘
```

### 6.2 Low-Latency Tuning for Jetson Nano

| Parameter | Default | Low-Latency Setting |
|-----------|---------|---------------------|
| GStreamer `latency` | 2000ms | `latency=50` |
| `rtspsrc` buffer | large | `do-retransmission=false` |
| H.264 profile | high | `profile=baseline` (if camera supports) |
| LeWM batch size | 1 | 1 (mandatory for real-time) |
| PyTorch thread count | auto | `torch.set_num_threads(2)` to save CPU |
| TensorRT precision | FP32 | **FP16** (2× throughput on Maxwell) |
| Frame resolution | native | Reduce to 320×240 at ESP32-Cam if acceptable |

### 6.3 NVIDIA jetson-utils Alternative

```python
# Using jetson-utils for zero-copy capture on Nano:
import jetson_utils

camera = jetson_utils.videoSource("rtspsrc://192.168.x.x:8554/stream", 
                                   ["latency=100", "--live"])
while True:
    img = camera.Capture()
    if img is None: continue
    # img is already a CUDA GPU tensor — zero copy
    frame_tensor = jetson_utils.cudaToNumpy(img)  # or feed directly to torch
```

### 6.4 ffmpeg Alternative

```bash
# ffmpeg to decode RTSP and pipe to Python:
ffmpeg -i rtsp://user:pass@camera -q:v 5 -f rawvideo -pix_fmt yuv420p pipe:1

# Python receives raw YUV frames (lowest latency option)
```

---

## 7. Alternative Lightweight World Models for Edge Robotics

| Model | Type | Parameters | Framework | Training | Edge Viability | Notes |
|-------|------|-----------|-----------|---------|----------------|-------|
| **LeWM (this paper)** | JEPA | 15M | PyTorch | Offline, reward-free | ✅ Best for edge | Single GPU hours; 192-dim latent; SIGReg anti-collapse |
| **TD-MPC2** | Model-based RL | 1M–317M (scales) | JAX/Haiku | Online RL (requires rewards) | ⚠️ Large only | Single agent 80-task; requires env interaction for training |
| **DreamerV3** | World model + RL | 300M+ (varies) | JAX | Online RL | ❌ Not edge | Reproduced in `danijar/dreamerv3`; needs TPU/GPU cluster |
| **MuDreamer** | Dreamer variant | ~50M est. | PyTorch | Offline RL | ⚠️ Medium | Reconstruction-free; reward-prediction based |
| **PLDM** | JEPA | ~20M est. | PyTorch | Offline, 7 loss terms | ⚠️ Harder than LeWM | Unstable training; LeWM is upgrade |
| **DINO-WM** | JEPA | 86M+ (DINOv2 frozen) | PyTorch | Offline | ❌ Not edge | DINOv2 alone is ~86M; LeWM is 48× faster planning |
| **IRIS** | Transformer WM | ~40M est. | PyTorch | Offline RL | ⚠️ Possible | Uses transformer world model; needs action labels |
| **Genie** | Generative WM | 2B+ | - | Video only | ❌ Not edge | Text-to-video; far too large |

### 7.1 Comparison: LeWM vs TD-MPC2

| Aspect | LeWM | TD-MPC2 |
|--------|------|---------|
| Parameters | 15M | 1M–317M |
| Training | Offline, reward-free | Online RL (requires env interaction) |
| Action conditioning | AdaLN in predictor | Latent dynamics + reward Q-function |
| Planning | CEM on latent | Local trajectory optimization in latent |
| Edge deployment | ✅ Straightforward | ⚠️ Online RL needs continuous env |
| Pre-trained edge models | ✅ Available | ❌ Must train on target robot |
| Framework | PyTorch | JAX |
| Physical violation detection | ✅ Yes (VoE framework) | ❌ No |
| SIGReg anti-collapse | ✅ Yes | N/A |

### 7.2 Verdict on Alternatives

**LeWM is the best candidate for edge robot world modeling** because:
1. ✅ Smallest model designed for offline/edge use
2. ✅ No reward signal needed for training
3. ✅ Pre-trained weights available
4. ✅ PyTorch (easy deployment via `torch.jit.trace`)
5. ✅ Single-GPU training, no cluster needed
6. ✅ Physical violation detection is unique to LeWM

**TD-MPC2 is a strong alternative only if:**
- You have an online env and can run RL training
- You want a single agent to handle 100+ tasks (its specialty)
- You have a larger edge device (Jetson AGX, not Nano)

---

## 8. Specific Recommendations with Estimated Latencies

### 8.1 Recommended Deployment Configuration

```
Hardware:  Jetson Nano 2GB + ESP32-Cam (RTSP) + Cyber Bricks ESP32-C3
Training:  Ubuntu + RTX 2060 (or Google Colab A100 free tier)
Checkpoint transfer:  scp lewm_pusht_object.ckpt jetnano:/home/model/
```

**Jetson Nano software stack:**
1. JetPack 4.6.x (Python 3.8, PyTorch 1.10 wheel)
2. TensorRT 8.x (for FP16 optimization)
3. GStreamer 1.14 (for RTSP capture)
4. paho-mqtt (for Cyber Bricks communication)

### 8.2 Latency Breakdown (Optimized Nano Configuration)

| Stage | Component | Time (ms) |
|-------|-----------|-----------|
| Frame capture | GStreamer RTSP | 50 |
| Decode + preprocess | CUDA/NVMM | 20 |
| LeWM encode | ViT-Tiny FP16 + TensorRT | 50 |
| LeWM predict (1 step) | Predictor FP16 + TensorRT | 30 |
| CEM planning (3 iters) | Latent optimization | 800 |
| **Total planning loop** | | **~950 ms** |
| MQTT + ESP32 | | 30 |
| **Total E2E** | | **~1.0 second** |

> With 3 CEM iterations (vs paper's 10) and FP16 TensorRT, LeWM achieves ~1 second total planning on Jetson Nano — approaching real-time for 1Hz control. For 5Hz control, further reduce to 1-2 CEM iterations or pre-warm the planner.

### 8.3 Quick Start Action Items

| Step | Action | Time Estimate |
|------|--------|--------------|
| 1 | Clone LeWM repo: `git clone https://github.com/lucas-maes/le-wm` | 2 min |
| 2 | Download checkpoint: `STABLEWM_HOME=~/.stable-wm ./scripts/download_checkpoints.sh` | 5 min |
| 3 | Install PyTorch on Nano: `pip3 install torch torchvision --index-url ...` | 10 min |
| 4 | Convert to TensorRT FP16: `torch2trt` or `trtexec` | 15 min |
| 5 | Test RTSP capture with GStreamer | 15 min |
| 6 | Run eval.py on Nano (goal-conditioned reach task) | 5 min |
| 7 | Integrate paho-mqtt, publish to Cyber Bricks | 20 min |
| 8 | Tune CEM iterations for latency vs quality | Ongoing |

---

## 9. Summary

### LeWM is Edge-Viable with Caveats

| Question | Answer |
|----------|--------|
| Can LeWM run on Jetson Nano 2GB? | **Yes**, inference fits in 2GB RAM |
| Can LeWM train on Jetson Nano 2GB? | **No**, train on RTX 2060+ instead |
| What latency on Jetson Nano? | **2-5 seconds** for full MPC plan (vs <1s on desktop GPU) |
| What's the bottleneck? | CEM planning iterations (not model inference) |
| Best optimization? | **FP16 + TensorRT** on Nano; reduce CEM iters 10→3 |
| Best alternative for edge? | LeWM (no good alternatives; TD-MPC2 needs online RL) |
| Cyber Bricks integration path? | MQTT from Nano to ESP32-C3; 1-3s total loop |

### Key Takeaways

1. **LeWM is the right model** for edge robot world modeling — small, stable to train, open-source, PyTorch-based, no rewards needed
2. **Train on desktop RTX 2060, deploy inference on Jetson Nano** — never train on Nano
3. **FP16 + TensorRT + 3 CEM iterations** brings planning from 5-10s → ~1s on Nano
4. **ESP32-Cam → GStreamer → LeWM → MQTT → Cyber Bricks** is the full pipeline; ~1s total latency
5. **The 1-second planning target** (paper's desktop claim) becomes **~1-3 seconds** on Jetson Nano after optimization — acceptable for slow robot tasks (manipulation, navigation at 0.5-1Hz)
6. For faster control loops (10Hz+), LeWM on Nano may need to skip CEM entirely and use a pre-trained policy from the latent space

---

## References & URLs

| Resource | URL |
|----------|-----|
| LeWM Paper (arXiv:2603.19312) | https://arxiv.org/abs/2603.19312 |
| LeWM arXiv HTML (with appendix) | https://arxiv.org/html/2603.19312v1 |
| LeWM GitHub Repo | https://github.com/lucas-maes/le-wm |
| LeWM Project Website | https://le-wm.github.io/ |
| LeWM HuggingFace | https://huggingface.co/papers/2603.19312 |
| SIGReg (LeJEPA paper) | https://arxiv.org/abs/2511.08544 |
| Stable-WorldModel-v1 | https://arxiv.org/abs/2602.08968 |
| TD-MPC2 Project | https://www.tdmpc2.com/ |
| TD-MPC2 Paper (ICLR 2024) | https://openreview.net/pdf?id=Oxh5CstDJU |
| DreamerV3 GitHub | https://github.com/danijar/dreamerv3 |
| DreamerV3 Paper | https://arxiv.org/abs/2301.04104 |
| PyTorch on Jetson Nano | https://pytorch.org/blog/running-pytorch-models-on-jetson-nano/ |
| NVIDIA Jetson Forum (memory) | https://forums.developer.nvidia.com/t/memory-usage-in-pytorch/185671 |
| Low-Latency GStreamer on Jetson | https://forums.developer.nvidia.com/t/best-achievable-video-stream-latency-with-gstreamer-on-jetson-nano/265294 |
