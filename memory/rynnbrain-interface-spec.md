# RynnBrain 接口规格说明

> 调研时间：2026-03-25
> 来源：arXiv:2602.14979v1 + 官方 GitHub README + Cookbooks
> ⚠️ 本文档严格区分「确认的」与「推测的」内容

---

## 一、确认信息（来自官方文档）

### 1. 官方资源地址

| 资源 | 地址 |
|------|------|
| GitHub | https://github.com/alibaba-damo-academy/RynnBrain |
| HuggingFace 合集 | https://huggingface.co/collections/Alibaba-DAMO-Academy/rynnbrain |
| ModelScope | https://www.modelscope.cn/collections/DAMO_Academy/RynnBrain |
| Demo (HuggingFace Space) | https://huggingface.co/spaces/Alibaba-DAMO-Academy/RynnBrain |
| 技术报告 PDF | https://alibaba-damo-academy.github.io/RynnBrain.github.io/assets/RynnBrain_Report.pdf |

### 2. 模型系列（Model Zoo）

| 模型 | 底座 | HuggingFace |
|------|------|-------------|
| RynnBrain-2B | Qwen3-VL-2B-Instruct | ✅ |
| RynnBrain-8B | Qwen3-VL-8B-Instruct | ✅ |
| RynnBrain-30B-A3B (MoE) | Qwen3-VL-30B-A3B-Instruct | ✅ |
| RynnBrain-CoP-8B | RynnBrain-8B | ✅ |
| RynnBrain-Plan-8B | RynnBrain-8B | ✅ |
| RynnBrain-Plan-30B-A3B | RynnBrain-30B-A3B | ✅ |
| RynnBrain-Nav-8B | RynnBrain-8B | ✅ |

### 3. 接入方式：Python 本地推理（确认）

RynnBrain 是一个**本地部署**模型，没有云端 API 服务。接入方式有两种：

#### 方式 A：HuggingFace Transformers（最小依赖）

```python
import torch
from transformers import AutoModelForImageTextToText, AutoProcessor

model_path = "Alibaba-DAMO-Academy/RynnBrain-2B"
processor = AutoProcessor.from_pretrained(model_path)
model = AutoModelForImageTextToText.from_pretrained(
    model_path,
    dtype=torch.bfloat16,
)
model.to("cuda")

conversation = [
    {
        'role': 'user',
        'content': [
            {'type': 'image', 'image': 'path/to/image.jpg'},
            {'type': 'text', 'text': 'What appliance can be used to heat food quickly.\nGenerate coordinates for one object bounding box. Constraints: x1,y1,x2,y2 ∈ [0,1000]. Response must be in the format: <object> (x1, y1), (x2, y2) </object>'},
        ],
    }
]

model_inputs = processor.apply_chat_template(
    conversation,
    add_generation_prompt=True,
    tokenize=True,
    return_dict=True,
    return_tensors="pt",
)
model_inputs = model_inputs.to("cuda")

output_ids = model.generate(**model_inputs, max_new_tokens=256)
output_ids = output_ids[:, model_inputs["input_ids"].size(1):]
response = processor.decode(output_ids[0], skip_special_tokens=True)
print(response)
```

依赖：`pip install transformers==4.57.1`

#### 方式 B：SGLang（OpenAI 兼容 API 服务）

```shell
# 启动服务器
python3 -m sglang.launch_server \
  --model-path Alibaba-DAMO-Academy/RynnBrain-2B \
  --host 0.0.0.0 --port 8000
```

```python
from openai import OpenAI
client = OpenAI(api_key="", base_url="http://localhost:8000/v1")
response = client.chat.completions.create(
    model="default",
    messages=messages,  # 同样格式的 messages
    stream=False,
).choices[0].message.content
```

### 4. 模型输入格式（确认）

**输入** = 视觉信号 + 文本指令

- 视觉信号：单张图片、多张图片、**视频帧序列**（统一为视觉 token 序列）
- 文本指令：自然语言指令，遵循特定模板
- 使用 `processor.apply_chat_template()` 构建对话

**视频帧采样**：2 FPS，最高 2048 帧，最大 context length 16,384 tokens

### 5. 模型输出格式（确认）

RynnBrain 的输出是**自回归生成的文本流**，其中空间坐标被编码为离散整数 token。

所有坐标归一化到 **[0, 1000]** 范围（连续值按步长离散化）。

不同任务的输出格式：

#### 5a. 物体定位（Object Localization）

```
<object> <frame n>: (x1, y1), (x2, y2) </object>
```

例如：`<object> <frame 0>: (123, 456), (789, 101) </object>`

#### 5b. 区域定位（Area Localization）

```
<area> <frame n>: (x1, y1), (x2, y2), (x3, y3), ... </area>
```

#### 5c. 可供性定位（Affordance Localization）

```
<affordance> <frame n>: (x1, y1) </affordance>
```

#### 5d. 轨迹预测（Trajectory Prediction）

```
<trajectory> <frame n>: (x1, y1), (x2, y2), (x3, y3), ... </trajectory>
```

最多 10 个轨迹点。

#### 5e. 抓取姿态（Grasp Pose）

```
<object> <frame n>: (x1, y1), (x2, y2) </object>  # 4 个角点
```

#### 5f. 任务规划（Manipulation Planning）—— RynnBrain-Plan

输出混合文本和空间标注：

```
Pick up the <object> from <area>, place it at <affordance>.
#### <answer>
<affordance> <frame 0>: (x, y) </affordance>
<object> <frame 0>: (x_min, y_min), (x_max, y_max) </object>
<area> <frame 0>: (x, y) </area>
</answer>
```

官方 cookbook 的 `parse_complex_response()` 解析函数：

```python
import re

def parse_complex_response(response_str: str) -> dict:
    result = {}
    affordance_pattern = re.compile(
        r"<affordance>.*?\(([0-9]+),\s*([0-9]+)\).*?</affordance>",
        re.DOTALL
    )
    object_pattern = re.compile(
        r"<object>.*?\(([0-9]+),\s*([0-9]+)\),\s*\(([0-9]+),\s*([0-9]+)\).*?</object>",
        re.DOTALL
    )
    area_pattern = re.compile(
        r"<area>.*?\(([0-9]+),\s*([0-9]+)\).*?</area>",
        re.DOTALL
    )
    # ... 解析并返回 dict
```

### 6. CoP（Chain-of-Points）推理模式输出格式（确认）

CoP（Chain-of-Points reasoning） = RynnBrain-CoP，是 RynnBrain-8B 经过 SFT + GRPO（强化学习）微调的变体。

**CoP 的核心特点**：交替进行文本推理（thinking）和空间定位（grounding）。

**输出格式**（confirmed from Cookbook 9）：

```
[推理过程文本...]
#### <answer><trajectory/affordance/area><frame i>: (X_1, Y_1), (X_2, Y_2), ... </trajectory/affordance/area></answer>
```

- `####` 之前：文本推理过程（thinking）
- `####` 之后：用 `<answer>` 标签包裹的结构化输出
- 标签类型：`<trajectory>`, `<affordance>`, `<area>`
- 包含帧索引 `<frame n>` 和坐标

解析函数（来自 Cookbook 9）：

```python
def parse_thinking_and_output(output_text: str) -> tuple:
    # Split by #### marker
    if "####" in output_text:
        parts = output_text.split("####", 1)
        thinking = parts[0].strip()
        final_output = "####" + parts[1].strip()
    else:
        thinking = ""
        final_output = output_text.strip()
    return thinking, final_output
```

### 7. 训练框架（确认）

- 框架：基于 HuggingFace Transformers
- 支持：DeepSpeed ZeRO-1/2, gradient checkpointing, Flash Attention 2
- 优化器：AdamW，cosine LR schedule
- 强化学习：GRPO（Group Relative Policy Optimization）

---

## 二、推测信息（基于论文描述，无官方实现确认）

### 8. 架构层面的输入输出总结（推测）

以下内容是**从论文描述推断的**，不是从代码/文档直接确认的：

```
输入：
  - 图像/视频帧（RGB）
  - 文本指令（自然语言）
  - 可选：历史帧序列（作为 episodic memory）

处理：
  - Vision Encoder（Qwen3-VL 底座）
  - Vision-Language Projector
  - LLM Backbone（Qwen3-VL-2B/8B/30B-A3B）
  - 输出离散坐标 token

输出：
  - 自然语言文本（带结构化标签）
  - 空间坐标 token → 解码为 [0,1000] 归一化坐标
```

### 9. RynnBrain-Plan 的多步规划能力（推测）

论文描述 RynnBrain-Plan 支持多步任务分解和 action planning，每个 step 输出：
- 低层语言命令（text）
- 空间标注（object bbox, affordance point, area point）

**但具体的 JSON 输出schema没有在 GitHub README 中找到明确定义**，现有代码中输出仍是字符串格式（`<tag>...</tag>` 结构），需要自行解析。

### 10. 接入外部记忆系统（推测/设计建议）

**直接接入方式（无官方支持）**：

官方没有提供将 RynnBrain 接入外部记忆系统的标准接口。但可以基于上述输出格式自行设计：

```python
# 建议的解析→记忆注入流程（自行设计，非官方）
import re, json

def parse_rynn_output(output_text: str, task_type: str = "object") -> dict:
    """将 RynnBrain 的文本输出解析为结构化数据"""
    result = {
        "text": "",
        "spatial_data": []
    }

    # 分离 thinking 和 answer（如果是 CoP 模型）
    if "####" in output_text:
        parts = output_text.split("####", 1)
        result["thinking"] = parts[0].strip()
        answer_text = parts[1].strip()
    else:
        answer_text = output_text

    # 解析 <tag> 结构
    tag_pattern = rf"<(\w+)>\s*<frame\s+(\d+)>(.*?)</\1>"
    for match in re.finditer(tag_pattern, answer_text, re.DOTALL):
        tag = match.group(1)
        frame = int(match.group(2))
        coords_str = match.group(3)

        coord_pattern = r'\((\d+),\s*(\d+)\)'
        coords = [(int(x), int(y)) for x, y in re.findall(coord_pattern, coords_str)]

        result["spatial_data"].append({
            "type": tag,  # object/area/affordance/trajectory
            "frame": frame,
            "coordinates": coords,
            "normalized": True,  # [0, 1000]
        })

    return result

def inject_into_memory(parsed_output: dict, memory_graph: dict):
    """注入到记忆系统 Layer 2 图谱（自行设计）"""
    for item in parsed_output.get("spatial_data", []):
        # item["type"], item["frame"], item["coordinates"]
        # → 写入图谱节点和关系
        pass
```

### 11. 坐标系统说明（推测/补充）

论文明确说明：
- 坐标归一化到 [0, 1000]（离散整数）
- 连续空间被离散化为分类问题

**但以下内容未找到官方明确说明**：
- 坐标系原点是左上角还是左下角（从代码示例推断为左上角，与图像坐标系一致）
- 视频帧的时间戳对应关系
- 坐标是否与原始图像分辨率相关（归一化后不依赖分辨率）

---

## 三、贵庚 SOP JSON 格式的对照评估

贵庚 SOP 中自定义的 JSON 格式与 RynnBrain 官方输出的对照：

| 贵庚 SOP JSON 字段 | 对应的 RynnBrain 输出 | 一致性 |
|--------------------|----------------------|--------|
| `type` (时空实体类型) | `<object>/<area>/<affordance>/<trajectory>` 标签 | ✅ 一致 |
| `frame` (时间帧) | `<frame n>` | ✅ 一致 |
| `coordinates` | `(x, y)` 坐标对，`[0, 1000]` | ✅ 一致 |
| 坐标系 | 归一化到 `[0, 1000]` | ✅ 一致 |
| 推理链 (thinking) | `####` 分隔的文本推理过程 | ✅ 一致（CoP 模型） |
| 图谱关系（实体间关系） | **无官方输出** | ❌ 无对应 |
| 置信度分数 | **无官方输出** | ❌ 无对应 |

---

## 四、关键结论

1. **RynnBrain 没有外部 API 或云服务**：它是一个纯本地部署模型，只能通过 Transformers 或 SGLang 调用。
2. **输出格式是文本，不是 JSON**：RynnBrain 输出的是带有结构化标签的自然语言文本，需要正则解析。**没有原生的 JSON 输出接口**。
3. **CoP 推理模式的输出格式有官方确认**：通过 `####` 分隔符区分 thinking 和 spatial output，格式为 `<answer><tag><frame n>: coords </tag></answer>`。
4. **接入贵庚记忆系统的最佳方式**：基于 RynnBrain-Plan-8B 或 RynnBrain-CoP-8B 的输出，自行编写解析器（正则解析 `<tag>` 结构），然后将结果写入 Layer 2 图谱。
5. **官方 Cookbooks 是最佳参考**：特别是 Cookbook 9（CoP thinking）和 Cookbook 10（manipulation planning）包含完整的解析代码。
