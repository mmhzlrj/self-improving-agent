# LeWM 世界模型

> 全称：Lightweight World Model — 轻量级世界模型
> 训练设备：Ubuntu RTX 2060 6GB

## 核心架构

LeWM = Vision Encoder + Action Decoder

```
图像输入 → Vision Encoder (CNN) → 隐状态 → Action Decoder → 动作输出
```

### Vision Encoder
- 输入：256×256 RGB 图像，seq_len=8（连续8帧）
- 架构：CNN + Transformer（12层）
- 输出：隐状态向量（512维）

### Action Decoder
- 输入：隐状态 + 当前动作
- 输出：下一个动作的预测
- 训练目标：MSE loss

## 训练数据

| 数据集 | Episodes | Frames | 说明 |
|--------|---------|--------|------|
| pusht_full | 206 | 25,650 | 推物任务 |
| tworoom | - | - | 导航任务（数据待下载）|

## Checkpoint

- `pusht` 微调版：`~/.stable-wm/lewm_vision_best.pt`（loss=0.119，epoch 17 best）
- `tworoom` 训练版：`~/.stable-wm/lewm_tworoom.pt`（loss=NaN，待调参）

## 训练参数

```python
{
    "lr": 3e-6,
    "weight_decay": 0.01,
    "dropout": 0.2,
    "grad_clip": 0.5,
    "epochs": 50,
    "patience": 5  # early stopping
}
```

## 调用示例

```python
import torch
from lewm import LeWM

model = LeWM.load_checkpoint("~/.stable-wm/lewm_vision_best.pt")
action = model.predict(image_batch)  # shape: (B, action_dim)
```

## 相关文档

- [完整 SOP](../sop/full.html) — 第三章：软件架构
- [版本变更](../changelog/modules.html)
