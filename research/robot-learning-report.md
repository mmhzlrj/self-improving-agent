# Robot Learning Research Report: Multi-Task Learning & World Models
**Date:** 2026-03-30  
**Topic:** Imperial College MT3, LeWorldModel, Dexterity Foresight, ABB HyperReality, RHODA AI, Mind Children  
**For:** 0-1 Project (Cyber Bricks Hardware)

---

## Executive Summary

This report covers 5+ distinct approaches to robot learning that appeared in a March 2026 Forbes article on Physical AI breakthroughs. The most immediately actionable for 0-1 is **Imperial College's MT3**, which requires zero per-task training and needs only 1 demonstration. **ABB HyperReality** offers the most mature sim-to-real framework but is proprietary to ABB. **RHODA AI** and **LeWorldModel** represent the "scale pretrained video/world models" philosophy that complements the "data-efficient imitation learning" approach.

---

## 1. Imperial College London — MT3: Learning a Thousand Tasks in a Day

### Paper & Citation
- **Title:** "Learning a Thousand Tasks in a Day"
- **Authors:** Kamil Dreczkowski, Pietro Vitiello, Vitalis Vosylius, Edward Johns (Imperial College London)
- **Published:** Science Robotics, Vol 10, Issue 108, 2025
- **ArXiv:** https://arxiv.org/abs/2511.10110
- **GitHub:** https://github.com/kamil-dreczkowski/learning_thousand_tasks
- **Project Page:** https://www.robot-learning.uk/learning-1000-tasks

### What Is MT3?

MT3 stands for **Multi-Task Trajectory Transfer**. It is an imitation learning framework based on **decomposition + retrieval**. The key insight is that robot manipulation tasks share structural components: a **bottleneck pose** (the alignment/approach pose) and the **interaction trajectory** (the actual manipulation after reaching that pose).

Rather than learning each task end-to-end, MT3 decomposes all tasks into these shared primitives:

1. **Alignment Phase:** Move the robot to a "bottleneck pose" (similar across many tasks)
2. **Interaction Phase:** Execute the manipulation (replay of demonstrated velocities)

### How It Works Technically

```
Query Image → Hierarchical Retrieval → Find Most Similar Demo
    → PointNet++ Pose Estimation → ICP Refinement
    → Transform bottleneck pose to live scene
    → Apply 4-DOF inductive bias
    → Execute interaction (end-effector twists replay)
```

**Key components:**

- **Geometry Encoder (PointNet++):** Pre-trained on point clouds to encode object geometry
- **Pose Estimator:** 4-DOF regressor (±45° pose variation trained)
- **Hierarchical Retrieval:** Language embeddings + geometry embeddings for demo retrieval
- **ICP (Iterative Closest Point):** For point cloud registration refinement
- **No per-task training required for MT3** — it uses retrieval-based zero-shot adaptation

### Five Methods Implemented in the Codebase

| Method | Alignment | Interaction | Training Required? |
|--------|-----------|-------------|-------------------|
| **MT3** | Retrieval-based | Retrieval-based | **None** |
| Ret-BC | Retrieval-based | Behavioral Cloning | Yes |
| BC-Ret | Behavioral Cloning | Retrieval-based | Yes |
| BC-BC | Behavioral Cloning | Behavioral Cloning | Yes |
| MT-ACT+ | End-to-end multi-task transformer (adapted from RoboAgent) | Yes | Yes |

### Data Requirements
- **Per task:** 1–10 demonstrations (tested with <<10 per task)
- **Total dataset:** 1,000 tasks
- **Demonstration format:** RGB-D, segmentation, bottleneck pose, end-effector twists
- **Preprocessing:** LangSAM for initial segmentation, XMem for per-timestep mask tracking

### Compute Requirements
- **Training:** GPU required (Docker with NVIDIA Container Toolkit)
- **Inference (MT3):** PointNet++ encoder + pose estimator — modest GPU (tested on RTX-class)
- **MT3 requires no training** for new tasks, only inference

### Sample Efficiency
**Exceptional.** The paper reports learning 1,000 tasks in <24 hours with a single robot arm. With only 1–10 demonstrations per task, MT3 achieves this by reusing shared primitives across tasks rather than learning each from scratch.

### Open Source?
**Yes — fully open source.** Code, model checkpoints, and demo data are available on GitHub. Paper is published in Science Robotics.

---

## 2. LeWorldModel (LeWM) — JEPA-Based World Model

### Paper & Citation
- **Title:** "LeWorldModel: Stable End-to-End Joint-Embedding Predictive Architecture from Pixels"
- **Authors:** Lucas Maes, Quentin Le Lidec, Damien Scieur, Yann LeCun, Randall Balestriero
- **ArXiv:** https://arxiv.org/html/2603.19312v1
- **GitHub:** https://github.com/lucas-maes/le-wm
- **Project Page:** https://le-wm.github.io/

### What Is LeWM?

LeWorldModel (LeWM) is the first **Joint Embedding Predictive Architecture (JEPA)** that trains stably **end-to-end from raw pixels** using only **two loss terms:**
1. Next-embedding prediction loss
2. Gaussian regularizer (SIGReg) enforcing Gaussian-distributed latent embeddings

### Technical Details

```
Image observation → Encoder → latent embedding z^t
                    ↓
Action a^t + z^t → Predictor → predicted z^(t+1)
                    ↓
              Regularized to Gaussian
```

- **Key innovation:** Avoids representation collapse (the main failure mode of JEPAs) through a simple Gaussian regularizer instead of complex multi-term losses, exponential moving averages, or pre-trained encoders
- **Model size:** 15M parameters (compact)
- **Performance:** Competitive with foundation-model-based world models at substantially lower compute cost
- **Latent probing:** The latent space encodes meaningful physical structure — physical quantities can be recovered from embeddings

### Comparison with MT3

| Aspect | MT3 | LeWM |
|--------|-----|------|
| **Approach** | Imitation learning via retrieval | Latent world model via JEPA |
| **Per-task training** | Zero (MT3), some for BC variants | Requires environment interaction |
| **Data efficiency** | 1 demo = 1 task | Needs environment interactions |
| **Compute** | Modest GPU | 15M params, low cost |
| **Published** | 2025 Science Robotics | 2026 (new) |
| **Sim-to-real gap** | Lower (geometric matching) | Must be trained in real/sim |

**Complementarity:** LeWM provides world model planning (predict future states), MT3 provides zero-shot task execution. They could be combined: LeWM for planning, MT3 for execution.

### AMI Labs Context
Yann LeCun raised $1B (mentioned in the Forbes article) for AMI Labs to build world models for physical AI. LeWM is likely a research output from this direction.

### Open Source?
**Yes.** GitHub available: https://github.com/lucas-maes/le-wm

---

## 3. Dexterity AI — Foresight World Model

### Company & Announcement
- **Company:** Dexterity, Inc. (founded 2017 at Stanford, Redwood City)
- **Product:** Foresight — physics-consistent world model
- **Announcement:** PRNewswire, March 2026
- **Website:** https://www.dexterity.ai/blog/foresight
- **Challenge:** https://dexterity.ai/challenge (Foresight API Challenge with $50K prizes)

### What Is Foresight?

Foresight is a **real-time, transactable representation of the physical environment** enabling robots to perceive, reason, and act. Key characteristics:

- **Physics-consistent world model** for physical manipulation
- **4D reasoning:** 3 spatial dimensions + time
- **Decision time:** <400ms per placement decision
- **Application:** Dual-armed superhumanoid robot "Mech" for truck loading
- **Combinatorial optimization:** Up to 400 potential placements per box, multiple walls packed simultaneously
- **Training data:** 100M+ autonomous actions in production

### Technical Architecture

```
Real-world perception → Foresight world model simulation
    ↓
Asynchronous skill agents (perception, decision, motion)
    ↓
Interpretable language readouts for operators
```

The 4D box packing agent:
- Jointly optimizes density, stability, reachability, dual-arm parallelism
- Predicts how each placement affects the integrity of the entire truck
- Runs closed-loop with continuous environment updates

### Is It Open Source?
**No.** Proprietary commercial product. Dexterity launched the Foresight API Challenge ($50K prizes) but the model itself is not open source. Competitors must build their own physics simulator.

### Comparison with MT3

| Aspect | MT3 | Foresight |
|--------|-----|-----------|
| **Type** | Imitation learning | World model + planning |
| **Training data** | Human demonstrations | 100M+ autonomous actions |
| **Compute** | Modest GPU | High (production-grade) |
| **Open source** | Yes | No |
| **Task domain** | General manipulation | Truck loading / logistics |
| **Decision time** | Per-pose (~seconds) | <400ms |

### Relevance to 0-1
Low direct relevance (proprietary, high-compute), but the **agentic framework** architecture (perception → world model → skill agents → action) is a valuable design pattern.

---

## 4. ABB Robotics + NVIDIA — RobotStudio HyperReality

### Source
ABB News: https://new.abb.com/news/detail/134178/wbstr-closing-the-sim-to-real-gap-how-abbs-robotstudior-hyperreality-enables-industrial-scale-physical-ai

### What Is HyperReality?

RobotStudio HyperReality achieves **~99% simulation-to-reality correlation** through three layers:

1. **Product Digital Twin:** CAD models, manufacturing tolerances, surface textures, weight
2. **Photometric Environment:** Lighting levels, reflections, shadows, camera properties
3. **Robot Digital Twin:** Mechanical structure, dynamics, sensors, control logic

### Key Technical Innovations

- **Virtual Controller:** Runs the **same firmware** as physical ABB robot controllers — motion paths, acceleration profiles, cycle timing all match real robot behavior
- **NVIDIA Omniverse:** Photorealistic RTX rendering for synthetic data generation
- **Domain randomization:** Automatically varies parameters to generate thousands of training scenarios
- **Absolute Accuracy technology:** Reduces positioning errors from 8–15mm to ~0.5mm

### Results

| Metric | Value |
|--------|-------|
| Simulation accuracy | ~99% |
| Positioning precision | ~0.5mm (vs 8–15mm typical) |
| Commissioning time reduction | Up to 80% |
| Development cost reduction | Up to 40% |

### Sim-to-Real Gap Techniques

ABB's approach to closing the gap:
1. **Controller-faithful simulation** — same control logic in sim and real
2. **Photorealistic rendering** — matches real camera/sensor behavior
3. **Synthetic data generation** — mass-produce training scenarios via domain randomization
4. **Geometric calibration** — Absolute Accuracy calibration

### Is It Open Source?
**No.** This is ABB proprietary technology integrated into RobotStudio Premium. The NVIDIA Omniverse integration is also commercial.

### Relevance to 0-1
The **concurrent engineering** concept (product design + automation + AI in same sim) is valuable. The domain randomization for synthetic data generation is adoptable via Omniverse if available. However, ABB's system is designed for industrial 6-axis robots, not ESP32-based Cyber Bricks.

---

## 5. RHODA AI — Video Foundation Models for Robotics

### Company & Funding
- **Company:** RHODA AI
- **Founder/CEO:** Jagdeep Singh (former co-founder of quantum computing startup)
- **Funding:** $450M Series A (March 2026)
- **Backers:** Mayfield Fund and others
- **Website:** https://www.rhoda.ai/
- **Research:** https://www.rhoda.ai/research

### Approach: Direct Video-Action Model (DVA)

RHODA's key insight: **Pre-train on internet-scale video, then fine-tune on robot data.**

```
Pre-training: Hundreds of millions of internet videos
    → Learn motion, physics, physical world behavior priors
    
Fine-tuning: Small amount of robot data (10-20 hours)
    → Adapt to specific robot embodiment and tasks
    
Inference: Closed-loop video predictive control
    → Video model predicts future frames
    → Inverse dynamics model converts video → actions
```

### Key Claims
- Zero-shot generalizable manipulation via generated visual demonstrations
- Production deployment: component processing workflow in <2 minutes per cycle
- **Data efficiency:** 10–20 hours of robot data for real-world long-horizon tasks
- Autonomous operation in production with continuously changing materials/layouts

### Research Papers
- "Causal Video Models Are Data-Efficient Robot Policy Learners" — https://www.rhoda.ai/research/direct-video-action
- "Robot Learning from a Physical World Model" — arXiv:2511.07416

### Open Source?
**No.** RHODA AI is a stealth startup; models are proprietary.

### Comparison with MT3

| Aspect | MT3 | RHODA |
|--------|-----|-------|
| **Pre-training** | None (task decomposition) | Hundreds of millions of videos |
| **Per-task data** | 1 demo | 10–20 hours robot data |
| **Approach** | Retrieval + decomposition | Video generation + fine-tuning |
| **Generalization** | Via retrieval to similar demos | Via video pretraining priors |
| **Compute** | Modest | Massive (foundation model scale) |
| **Open source** | Yes | No |

---

## 6. Mind Children — Learning Like Children

### Company Info
- **Website:** https://mindchildren.com/
- **Founded:** 2023, Seattle
- **CEO:** Chris Kudla
- **Employees:** 2–10
- **Partners:** SingularityNET, TrueAGI, OpenCog Hyperon

### What They Do

Mind Children builds **social humanoid robots** for education, healthcare, hospitality, and elder care. Their robot "Codey" is a child-sized humanoid designed for:
- Classroom assistance
- Neurodivergent learner support
- Elder care

### "Learn Like Children" Philosophy

From the Forbes article: CEO Chris Kudla is "teaching robots to learn like children." However, **no specific published paper or technical method** was found for this. Mind Children is a young startup focused on:
- Humanoid robot hardware with emotional intelligence
- Partnership with SingularityNET for AI infrastructure
- OpenCog Hyperon for cognitive architecture

### Relevant AI Philosophy
Mind Children's approach is about **continuous learning** (robots that get better over time, like children), not a specific algorithm. From their website:
- "Strong application-specific intelligence out of the box"
- "Capable of progressively increasing in general intelligence"

### Is It Open Source?
No specific open-source algorithms or papers found. Mind Children appears to be primarily a **hardware + integrated AI product company**, not an AI research lab.

### Relevance to 0-1
Low direct technical relevance — Mind Children focuses on social/emotional AI in humanoid form, not manipulation policy learning. However, their **continuous learning** philosophy (robots that improve from interaction) is a valuable design principle for 0-1.

---

## Comparison Table

| Approach | Compute Requirement | Sample Efficiency | Sim-to-Real Gap | Open Source? | 0-1 Relevance |
|----------|--------------------|--------------------|-----------------|--------------|--------------|
| **MT3 (Imperial)** | GPU for training, modest for inference | 1 demo per task (zero-shot MT3) | Low — geometric matching | **Yes (GitHub)** | ⭐⭐⭐⭐⭐ |
| **LeWorldModel** | 15M params, low cost | Moderate (needs env interaction) | Must be trained in real | **Yes (GitHub)** | ⭐⭐⭐ |
| **ABB HyperReality** | High (Industrial-grade) | N/A (sim-only) | ~1% gap (99% correlation) | No | ⭐⭐ |
| **Dexterity Foresight** | High (100M actions) | High (from video pretraining) | Low (trained in production) | No | ⭐⭐ |
| **RHODA AI** | Massive (foundation model) | 10–20h robot data after video pretrain | Low (production proven) | No | ⭐⭐ |
| **Mind Children** | Unknown (early stage) | Unknown (no published method) | Unknown | No | ⭐ |

---

## Recommendations for 0-1 Project (Cyber Bricks Hardware)

### Hardware Profile: Cyber Bricks
- **Main controller:** ESP32 (dual-core Xtensa LX6, 240MHz, no GPU)
- **Motors:** 2 motors + 1 servo
- **Manipulation:** Simple pick-and-place, basic arm movements
- **Compute offload:** Jetson Nano 2GB possible for heavier inference

### Jetson Nano 2GB Constraints
- **GPU:** 128 CUDA cores (Maxwell), 472 GFLOPS
- **CPU:** Quad-core ARM Cortex-A57 @ 1.43GHz
- **RAM:** 2GB LPDDR4
- **Assessment:** Marginal for transformer-based policies. Could run PointNet++ encoder for MT3 with quantization. Full MT-ACT+ or video models would struggle.

### Most Applicable Approach: MT3

**MT3 is the most directly applicable because:**

1. **Zero per-task training** — Cyber Bricks can't handle GPU training locally
2. **1 demonstration per task** — minimum data burden
3. **Geometric matching** — works with simple point cloud from depth camera
4. **Open source** — full code available on GitHub
5. **ESP32-compatible for low-level control** — MT3 generates target poses/twists, ESP32 executes

### Minimum Data Requirements (MT3 for Cyber Bricks)

| Metric | Value |
|--------|-------|
| Demonstrations per new task | **1 (MT3)** |
| Total dataset for 0-1 project | 10–50 task demos (realistic scope) |
| Per-demonstration data | RGB-D image, segmentation, bottleneck pose, end-effector twists |
| Storage per demo | ~50MB (RGB-D + masks) |
| Camera requirement | RGB-D camera (Intel RealSense or similar) |

### Implementation Roadmap for 0-1

**Phase 1: MT3 Zero-Shot (Weeks 1–4)**
```
1. Set up Jetson Nano 2GB with Docker + NVIDIA Container Toolkit
2. Clone MT3 repo: https://github.com/kamil-dreczkowski/learning_thousand_tasks
3. Run MT3 with pre-trained checkpoints on 3 demo tasks
4. Record 1 demonstration per new task using kinesthetic teaching or teleop
5. Deploy MT3 inference — ESP32 receives target poses over serial
```

**Phase 2: Fine-tune BC Variants (Weeks 5–8)**
```
1. Train Ret-BC (retrieval alignment + BC interaction) on demo dataset
2. This improves robustness over pure retrieval
3. Fine-tune on Jetson Nano using quantized models
```

**Phase 3: Custom Cyber Bricks Adaptation (Weeks 9–12)**
```
1. Adapt geometry encoder to Cyber Bricks' limited DOF
2. Simplify bottleneck pose estimation (Cyber Bricks has 2 motors + servo)
3. Reduce PointNet++ to a smaller model (8M → 2M params) via pruning
```

### Specific Takeaways from Each Approach

| Approach | What 0-1 Can Learn |
|----------|-------------------|
| **MT3** | Zero-shot task transfer via retrieval + decomposition; 1 demo = 1 task |
| **LeWorldModel** | Latent world models for planning; compact 15M param model design |
| **ABB HyperReality** | Domain randomization for sim data; controller-faithful simulation |
| **Dexterity Foresight** | Agentic perception→reason→act pipeline; 4D (space+time) reasoning |
| **RHODA AI** | Video pretraining as physical world prior; fine-tune on small robot data |
| **Mind Children** | Continuous learning over time; emotional/social intelligence layering |

### Jetson Nano 2GB Compatibility Check

| MT3 Component | Jetson Nano 2GB Compatible? | Notes |
|---------------|---------------------------|-------|
| PointNet++ encoder | ⚠️ Marginal | 128 CUDA cores enough for batch-1 inference |
| Pose estimator | ✅ Yes | Lightweight 4-DOF network |
| ICP refinement | ✅ Yes | CPU-based, no GPU needed |
| MT-ACT+ end-to-end | ❌ No | Transformer too large for 2GB RAM |
| Docker container | ✅ Yes | Supported on Jetson Nano |
| RealSense camera | ✅ Yes | Native Linux driver support |

**Recommendation:** Start with MT3 (no training required), use Jetson Nano 2GB for inference only, consider **Jetson Orin Nano 8GB** if training BC policies.

---

## Key Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| Cyber Bricks DOF too low for MT3 bottleneck pose concept | Medium | Re-define "bottleneck" as simple approach pose; MT3's 4-DOF already accounts for rotation symmetry |
| Jetson Nano 2GB runs out of memory on BC training | High | Use 4-bit quantization; train on cloud GPU, deploy quantized model |
| MT3 retrieval fails for novel objects not in demo library | Medium | Start with a diverse demo library covering object categories; use language embeddings for broader retrieval |
| ESP32 serial communication latency too high for closed-loop | Medium | Pre-compute trajectory segments; use bulk pose transfers, not per-timestep streaming |
| Sim-to-real gap with Cyber Bricks | Low | MT3 uses geometric matching (low gap by design); validate with 5 physical tests per task |
| ABB/NVIDIA ecosystem not accessible | Low | ABB is industrial-only; use open-source Isaac Gym or PyBullet for sim-to-real experiments |

---

## Conclusion

The Imperial College MT3 approach is the clearest near-term win for the 0-1 project. Its combination of **zero per-task training**, **single-demonstration learning**, and **open-source availability** makes it uniquely suited for a small team working with constrained hardware. The LeWorldModel JEPA approach is complementary for planning and is worth monitoring as the 15M-parameter model is tractable for edge deployment. The proprietary approaches (ABB, Dexterity, RHODA) provide architectural inspiration but are not directly adoptable without significant resources.

**Immediate next step:** Clone the MT3 repository and run the `deploy_mt3` example on Jetson Nano 2GB with a RealSense camera to validate the pipeline.

---

## References

1. Dreczkowski K., Vitiello P., Vosylius V., Johns E. (2025). "Learning a Thousand Tasks in a Day." Science Robotics, 10(108). https://doi.org/10.1126/scirobotics.adv7594
2. Dreczkowski K. et al. (2025). MT3 GitHub Repository. https://github.com/kamil-dreczkowski/learning_thousand_tasks
3. Maes L. et al. (2026). "LeWorldModel: Stable End-to-End Joint-Embedding Predictive Architecture from Pixels." arXiv:2603.19312. https://github.com/lucas-maes/le-wm
4. Dexterity, Inc. (2026). "Dexterity's World Model Foresight Delivers a Big Leap for Physical AI." PRNewswire.
5. ABB Robotics (2026). "Closing the Sim-to-Real Gap: RobotStudio HyperReality." ABB News.
6. RHODA AI (2026). "Rhoda AI Exits Stealth with $450M to Train Robots from Video." Robot Report.
7. Mind Children (2025). https://mindchildren.com/
8. Koetsier J. (2026). "Yann LeCun Got $1 Billion For World Model AI. These Robots Learned 1000 Real-World Tasks in 24 Hours." Forbes.
