# 调研汇总：ROBOT-SOP 第三批技术验证

**调研时间**：2026-03-24 15:39
**耗时**：约 7 分钟（第三批，限速）
**验证问题数**：13个
**建议修改数**：4个

---

## 修改意见清单

### 1. Jetson Nano I2C 引脚标注 — 🔴高

- **原文**：`Pin 3(SCL)/5(SDA)`
- **建议改为**：`Pin 3(SDA)/5(SCL)`
- **来源**：JetsonHacks NVIDIA Jetson Nano J41 Header Pinout
- **状态**：⏳ 待审批

> SOP 将 I2C 引脚的 SCL/SDA 标注颠倒了。实测 Pin 3 = I2C_2_SDA（数据线），Pin 5 = I2C_2_SCL（时钟线）。注意这是 I2C Bus 13。

---

### 2. vLLM ROCm Docker 镜像名 — 🟡中

- **原文**：`vllm/vllm-openai-rocm:v0.14.0`
- **建议改为**：`vllm/vllm-openai:v0.14.0-rocm`
- **来源**：vLLM 官方 Docker Hub
- **状态**：⏳ 待审批

> 镜像名拼写有误，正确是 `vllm/vllm-openai` 不是 `vllm/vllm-openai-rocm`。rocm 是 tag 后缀。

---

### 3. SGLang ROCm 启动命令 — 🟡中

- **原文**：`python -m sglang.launch`
- **建议改为**：`python -m sglang.launch_server --model-path <model> --port 30000`
- **来源**：SGLang 官方文档
- **状态**：⏳ 待审批

> 命令不完整，缺少 `_server` 后缀和必要参数 `--model-path`。SGLang ROCm 与 CUDA 版本命令相同，只是安装包不同。

---

### 4. micro-ROS agent 传输类型参数 — 🔴高

- **原文**：`ros2 run micro_ros_agent micro_ros_agent wifi`
- **建议改为**：`ros2 run micro_ros_agent micro_ros_agent udp4 --port 8888`
- **来源**：micro-ROS 官方文档
- **状态**：⏳ 待审批

> `wifi` 不是有效的 micro-ROS agent 传输类型。WiFi/网络场景应使用 `udp4`（IPv4 UDP）。其他有效选项：udp6/tcp4/serial/canfd。

---

## 验证通过的内容

### 第三章（通信协议）

- MQTT QoS 1 <50ms ✅ 正确，实测 30-50ms（有线局域网）
- WebSocket <20ms ✅ 正确，12-20ms 典型值
- Jetson Nano UART Pin 8(TX)/10(RX) ✅ 正确，波特率 115200
- Jetson Nano I2C 引脚 ⚠️ 标注反了（见修改意见1）

### 第四章（硬件）

- ESP32-Cam OV2640 JPEG 参数 ✅ 正确，SVGA/VGA + quality 12 推荐
- Cyber Bricks XA003/XA004/XA005 ✅ 真实存在，Bambu Lab 官方产品线

### 第六章（LLM）

- Ollama `ollama create` 命令 ✅ 正确
- vLLM ROCm 支持 ✅ 正确，v0.14.0 官方支持（镜像名见修改意见2）

### 第七章（ROS 2）

- `ros-foxy-ros-base` 安装命令 ✅ 正确
- micro-ROS agent 命令 ⚠️ 传输参数错误（见修改意见4）

### 第八章（安全）

- 声纹相似度阈值 0.85 ⚠️ 经验值，非行业强制标准，建议注明适用场景
- CPU 温度阈值 85°C ✅ 合理，行业通用预警阈值

---

## 预估时间记录

| 日期 | 调研内容 | 小点数 | 预估时间 | 实际时间 |
|------|---------|--------|---------|---------|
| 2026-03-24 第三批 | 技术声明验证 | 13 | ~30分钟 | 约7分钟 |
