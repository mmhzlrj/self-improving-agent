# 🤖 OpenClaw 机器人完整实施指南

**文档版本**: v0.3 (整合版，含多节点+CyberBricks)  
**创建日期**: 2026-03-07  
**更新日期**: 2026-03-07

---

# 一、项目概述

## 1.1 项目愿景

本项目旨在打造一个**有感官、有手脚、能思考**的私人 AI 机器人，作为用户唯一的特殊节点，实现24小时陪伴。

### 核心价值主张

| 价值 | 说明 | 优先级 |
|------|------|--------|
| **记忆延续** | 帮你记录身边发生的事情，随时回顾 | P0 |
| **陪伴对话** | 随时语音交流，有问必答 | P0 |
| **执行任务** | 帮你完成简单的物理任务 | P1 |
| **安全守护** | 身份认证、防抢防盗、紧急响应 | P1 |
| **数据隐私** | 所有数据本地处理，不传云端 | P0 |

---

# 二、硬件方案

## 2.1 现有硬件

| 设备 | 规格 | 数量 | 状态 |
|------|------|------|------|
| Jetson Nano | **2GB** | 1 | 可用 |
| ESP32-Cam | OV2640 | 1 | 可用 |
| Cyber Bricks | ESP32+电机+舵机 | 2 | 已有（拓竹赠送） |
| 星闪设备 | 未知型号 | ? | 测试中 |
| 拓竹 H2C | 3D打印机 | 1 | 可用 |
| Ubuntu 台式机 | 5600G+32G+2060 | 1 | 可用（待对接 Gateway） |

## 2.2 需要采购

| 类别 | 配件 | 预算 |
|------|------|------|
| 语音套件 | USB耳机（漫步者K800） | ¥80 |
| 运动套件 | 舵机、电机、轮子等 | ¥229 |
| 传感器 | 超声波、红外、蜂鸣器 | ¥22 |
| 其他 | 杜邦线、面包板、螺丝 | ¥60 |
| **合计** | | **¥391** |

---

# 三、系统架构

## 3.1 整体架构

```
┌─────────────────────────────────────────┐
│         Ubuntu 台式机 (GPU节点)           │
│  • RTX 2060 GPU 加速                    │
│  • 32GB RAM                            │
│  • 特殊任务时启用                       │
└──────────────────┬──────────────────────┘
                   │ openclaw node
                   │ WebSocket
┌──────────────────▼──────────────────────┐
│              家里 Gateway (Mac)          │
│        主 AI (我) + 任务调度             │
└──────────────────┬──────────────────────┘
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
   ┌────────┐ ┌────────┐ ┌────────┐
   │ Jetson │ │Cyber   │ │Cyber   │
   │ Nano   │ │Brick 1 │ │Brick 2 │
   │(语音)  │ │(运动)  │ │(备用)  │
   └────────┘ └────────┘ └────────┘
```

## 3.2 节点说明

| 节点 | 角色 | 功能 |
|------|------|------|
| Mac Gateway | 主控 | AI大脑、任务调度 |
| Ubuntu 台式机 | GPU节点 | 图像理解、GPU密集任务 |
| Jetson Nano | 边缘节点 | 语音交互、视频处理 |
| Cyber Bricks x2 | 运动节点 | 电机控制、动作执行 |

## 3.3 通信协议

```json
{
  "header": {
    "version": "1.0",
    "type": "robot_command",
    "from": "gateway",
    "to": "robot"
  },
  "payload": {
    "action": "voice_chat",
    "data": {"text": "你好"}
  }
}
```

---

# 四、Phase 0: Ubuntu 台式机对接（GPU 节点）

## 4.1 目标

让 Ubuntu 台式机（5600G + 32GB + RTX 2060）作为 GPU 节点连接到 Mac Gateway。

## 4.2 前置条件

Ubuntu 台式机已安装 OpenClaw（用户已确认）。

## 4.3 配置步骤

### Step 1: 获取 Gateway Token

在 Mac Gateway 上：
```bash
cat ~/.openclaw/openclaw.json | grep -A5 '"auth"'
```

记录 token。

### Step 2: 启动 Node Host

在 Ubuntu 台式机上：
```bash
# 假设 Mac Gateway IP 为 192.168.1.x
export OPENCLAW_GATEWAY_TOKEN="your-token-here"
openclaw node run --host 192.168.1.x --port 18789 --display-name "Ubuntu-GPU-Node"
```

### Step 3: 批准配对

在 Mac Gateway 上：
```bash
# 查看配对请求
openclaw devices list

# 批准节点
openclaw devices approve <requestId>
```

### Step 4: 配置 Exec 默认使用 Node

```bash
# 设置 exec 工具默认在该节点执行
openclaw config set tools.exec.host node
openclaw config set tools.exec.node "Ubuntu-GPU-Node"

# 添加常用命令白名单
openclaw approvals allowlist add --node "Ubuntu-GPU-Node" "/usr/bin/git"
openclaw approvals allowlist add --node "Ubuntu-GPU-Node" "/usr/bin/npm"
openclaw approvals allowlist add --node "Ubuntu-GPU-Node" "/usr/bin/python3"
openclaw approvals allowlist add --node "Ubuntu-GPU-Node" "/usr/local/bin/sd"
```

## 4.4 使用场景

| 场景 | 调用方式 |
|------|---------|
| 图像理解（需要GPU） | 自动调度到该节点 |
| 大模型推理 | 根据配置选择 |
| 批量任务 | 可指定 node 执行 |

## 4.5 注意事项

- Ubuntu 台式机功耗较高，建议需要时再开启
- 平时关闭省电，需要时远程唤醒（Wake on LAN）

---

# 五、Phase 1: 语音陪伴机器人

## 4.1 目标

实现基础语音交互功能：
- 语音输入 → 文字
- 文字 → AI 处理
- AI 回复 → 语音输出
- 与 Gateway 通信

## 4.2 硬件清单

| 配件 | 数量 | 备注 |
|------|------|------|
| Jetson Nano | 1 | 已有 |
| USB 耳机 | 1 | 需采购 |
| WiFi | 已有 | 内置 |

## 4.3 实施步骤

### Step 1: Jetson Nano 系统安装

#### 所需材料
- Jetson Nano 开发套件
- microSD 卡（64GB 以上）
- HDMI 显示器
- USB 键盘鼠标

#### 烧录步骤

1. **下载镜像**
   - 从 NVIDIA 官网下载 JetPack: https://developer.nvidia.com/embedded/downloads
   
2. **使用 balenaEtcher 烧录**
   - 下载: https://www.balena.io/etcher/
   - 选择镜像 → 选择 SD 卡 → Flash

3. **首次启动配置**
   ```
   语言: English
   用户名: nvidia
   密码: (自定义)
   时区: Shanghai
   ```

4. **基础系统配置**
   ```bash
   # 更新系统
   sudo apt update && sudo apt upgrade -y
   
   # 安装基础工具
   sudo apt install -y curl wget git
   
   # 开启 SSH
   sudo systemctl enable ssh
   sudo systemctl start ssh
   ip addr  # 记录 IP
   ```

5. **换源（加速）**
   ```bash
   sudo cp /etc/apt/sources.list /etc/apt/sources.list.bak
   
   # 编辑 sources.list
   sudo nano /etc/apt/sources.list
   
   # 写入阿里云源
   deb http://mirrors.aliyun.com/ubuntu-ports/ bionic main restricted universe multiverse
   deb http://mirrors.aliyun.com/ubuntu-ports/ bionic-updates main restricted universe multiverse
   
   sudo apt update
   ```

### Step 2: 音频配置

#### 检查设备
```bash
# 查看录音设备
arecord -l

# 查看播放设备
aplay -l
```

#### 设置默认设备
```bash
nano ~/.asoundrc

# 写入（假设 USB 耳机是 card 1）
pcm.!default {
    type hw
    card 1
}
ctl.!default {
    type hw
    card 1
}
```

#### 测试
```bash
# 录音 5 秒
arecord -d 5 -f cd -t wav test.wav
# 播放
aplay test.wav
# 调试音量
alsamixer
```

#### 常见问题

| 问题 | 解决 |
|------|------|
| 录不到声音 | alsamixer 按 F6 选 USB 设备 |
| 播放没声音 | 检查 ~/.asoundrc 配置 |
| 声音太小 | alsamixer 调高 Mic 增益 |
| 噪音大 | 使用 -f cd 参数 |

### Step 3: 安装 Whisper 语音识别

```bash
# 安装依赖
sudo apt install -y cmake libssl-dev

# 克隆 whisper.cpp
cd ~
git clone https://github.com/ggerganov/whisper.cpp.git
cd whisper.cpp

# 编译
make -j4

# 下载 tiny 模型（39M，最快）
./models/download-ggml-model.sh tiny
```

#### 测试
```bash
# 录制音频
arecord -d 5 -f S16_LE -r 16000 -c 1 test.raw

# 转写
./main -m models/ggml-tiny.bin -f test.raw
```

### Step 4: 安装 Edge-TTS 语音合成

```bash
# 安装 Python 和 pip
sudo apt install -y python3-pip

# 安装 edge-tts
pip3 install edge-tts
```

#### 测试
```bash
# 生成语音
edge-tts -m "ZH-XiaoxiaoNeural" -t "你好，我是你的 AI 伙伴" -o test.mp3

# 播放
aplay test.mp3
```

### Step 5: 编写语音对话程序

创建目录和主程序：

```bash
mkdir -p ~/robot-voice/src
cd ~/robot-voice
```

#### main.js 主程序

```javascript
/**
 * 语音对话主程序 - robot-voice/main.js
 * 
 * 功能：
 * 1. 监听麦克风输入
 * 2. 调用 Whisper 进行语音识别
 * 3. 发送到 Gateway (OpenClaw)
 * 4. 接收回复并使用 TTS 播放
 */

const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const http = require('http');

// ============ 配置 ============
const CONFIG = {
  // Whisper 配置
  whisperPath: path.join(process.env.HOME, 'whisper.cpp'),
  whisperModel: 'ggml-tiny.bin',
  
  // Gateway 配置
  gatewayUrl: 'http://192.168.1.x:3000',  // 改成你的 Gateway IP
  
  // 音频配置
  sampleRate: 16000,
  channels: 1,
  format: 'S16_LE',
  
  // 行为配置
  silenceThreshold: 1500,  // 毫秒，静音多少时间后结束录音
  maxRecordTime: 10000,     // 最长录音时间（毫秒）
};

// ============ 类定义 ============
class VoiceAssistant {
  constructor() {
    this.isRecording = false;
    this.isSpeaking = false;
    console.log('🎙️ 语音助手初始化完成');
  }

  // 录音
  async recordAudio() {
    return new Promise((resolve, reject) => {
      const audioFile = `/tmp/voice_${Date.now()}.raw`;
      
      console.log('🎙️ 开始录音...');
      
      const arecord = spawn('arecord', [
        '-d', String(CONFIG.maxRecordTime / 1000),
        '-f', CONFIG.format,
        '-r', String(CONFIG.sampleRate),
        '-c', String(CONFIG.channels),
        '-t', 'raw',
        audioFile
      ]);

      arecord.on('close', (code) => {
        if (code === 0 && fs.existsSync(audioFile)) {
          resolve(audioFile);
        } else {
          reject(new Error('录音失败，退出码: ' + code));
        }
      });

      arecord.on('error', reject);
    });
  }

  // 语音识别
  async recognize(audioFile) {
    return new Promise((resolve, reject) => {
      console.log('🔄 语音识别中...');
      
      const whisper = spawn(path.join(CONFIG.whripperPath, 'main'), [
        '-m', path.join(CONFIG.whisperPath, 'models', CONFIG.whisperModel),
        '-f', audioFile,
        '--no-timestamps'
      ]);

      let result = '';
      
      whisper.stdout.on('data', (data) => {
        result += data.toString();
      });

      whisper.on('close', (code) => {
        // 清理临时文件
        fs.unlinkSync(audioFile);
        
        if (code === 0) {
          const text = result.trim();
          console.log('📝 识别结果:', text);
          resolve(text);
        } else {
          reject(new Error('识别失败'));
        }
      });

      whisper.on('error', reject);
    });
  }

  // 发送到 Gateway
  async sendToGateway(text) {
    return new Promise((resolve, reject) => {
      console.log('📤 发送到 Gateway...');
      
      const data = JSON.stringify({
        type: 'voice_input',
        text: text,
        timestamp: Date.now()
      });

      const url = new URL('/api/robot/voice', CONFIG.gatewayUrl);
      
      const options = {
        hostname: url.hostname,
        port: url.port || 80,
        path: url.pathname,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(data)
        }
      };

      const req = http.request(options, (res) => {
        let body = '';
        res.on('data', (chunk) => body += chunk);
        res.on('end', () => {
          try {
            const response = JSON.parse(body);
            resolve(response);
          } catch (e) {
            reject(new Error('Gateway 响应解析失败'));
          }
        });
      });

      req.on('error', reject);
      req.write(data);
      req.end();
    });
  }

  // 语音合成
  async speak(text) {
    return new Promise((resolve, reject) => {
      console.log('🔊 语音合成:', text);
      
      const outputFile = `/tmp/tts_${Date.now()}.mp3`;
      
      const tts = spawn('edge-tts', [
        '-m', 'ZH-XiaoxiaoNeural',
        '-t', text,
        '-o', outputFile
      ]);

      tts.on('close', (code) => {
        if (code === 0) {
          // 播放
          const aplay = spawn('aplay', [outputFile]);
          aplay.on('close', () => {
            fs.unlinkSync(outputFile);
            resolve();
          });
        } else {
          reject(new Error('TTS 失败'));
        }
      });

      tts.on('error', reject);
    });
  }

  // 主对话循环
  async chat() {
    try {
      // 1. 录音
      const audioFile = await this.recordAudio();
      
      // 2. 识别
      const text = await this.recognize(audioFile);
      
      if (!text) {
        console.log('😶 没有识别到内容');
        return;
      }

      // 3. 发送到 Gateway
      const response = await this.sendToGateway(text);
      
      // 4. 语音回复
      if (response && response.reply) {
        await this.speak(response.reply);
      }
      
    } catch (error) {
      console.error('❌ 错误:', error.message);
    }
  }

  // 持续监听
  async listen() {
    console.log('👂 开始监听...');
    console.log('按 Ctrl+C 退出');
    
    while (true) {
      await this.chat();
      
      // 等待一小段时间再继续监听
      await new Promise(resolve => setTimeout(resolve, 500));
    }
  }
}

// ============ 启动 ============
const assistant = new VoiceAssistant();
assistant.listen().catch(console.error);
```

#### package.json

```json
{
  "name": "robot-voice",
  "version": "1.0.0",
  "description": "OpenClaw Robot Voice Module",
  "main": "main.js",
  "scripts": {
    "start": "node main.js"
  },
  "dependencies": {}
}
```

### Step 6: 配置 Gateway 通信

#### 在 Gateway 端添加 API

在 OpenClaw Gateway 中添加机器人 API：

```javascript
// gateway/robot-api.js
module.exports = {
  // 机器人语音输入处理
  async handleVoiceInput(req, res) {
    const { text } = req.body;
    
    // 调用主 AI 处理
    const reply = await ai.chat(text, {
      context: 'robot',
      mode: 'voice'
    });
    
    res.json({ reply });
  }
};
```

### Step 7: 启动测试

```bash
cd ~/robot-voice

# 首次运行
npm install
node main.js
```

预期输出：
```
🎙️ 语音助手初始化完成
👂 开始监听...
🎙️ 开始录音...
（说话...）
🔄 语音识别中...
📝 识别结果: 你好
📤 发送到 Gateway...
🔊 语音合成: 你好呀，我是你的 AI 伙伴
```

---

# 五、Phase 2: 视觉记录机器人

## 5.1 目标

- 24小时视频记录
- 本地处理，不传云端（隐私）
- 我能理解画面内容
- 回答"刚才发生了什么"

## 5.2 硬件清单

| 配件 | 数量 | 备注 |
|------|------|------|
| ESP32-Cam | 1 | 已有 |
| 摄像头支架 | 1 | 需采购 |
| 电源 5V/2A | 1 | 需采购 |

## 5.3 实施步骤

### Step 1: ESP32-Cam 固件烧录

#### 硬件连接

```
ESP32-Cam    ->    USB 转 TTL
-----------------------
GND          ->    GND
5V           ->    5V (或 VCC)
U0R          ->    TX
U0T          ->    RX
IO0          ->    GND (烧录模式)
```

#### 烧录步骤

1. **安装 esptool**
   ```bash
   pip3 install esptool
   ```

2. **下载固件**
   ```bash
   # 使用示例固件
   wget https://github.com/easytarget/esp32-cam-webserver/releases/download/2.0.1/esp32-cam-webserver.bin
   ```

3. **烧录**
   ```bash
   esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash
   
   esptool.py --chip esp32 --port /dev/ttyUSB0 write_flash \
     0x1000 esp32-cam-webserver.bin
   ```

4. **启动**
   - 断开 IO0 和 GND 的连接
   - 重启 ESP32-Cam
   - 查找 IP 地址（通过串口日志或路由器）

### Step 2: 配置视频流

#### 获取 RTSP 流

ESP32-Cam 常用地址：
- HTTP: `http://<IP>/`
- RTSP: `rtsp://<IP>/stream`

#### Jetson Nano 接收视频

```bash
# 安装 FFmpeg
sudo apt install -y ffmpeg

# 测试视频流
ffplay rtsp://<ESP32-CAM-IP>/stream
```

### Step 3: 编写视频处理程序

```javascript
// robot-video/index.js
const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

class VideoModule {
  constructor() {
    this.cameraIp = '192.168.1.100';  // ESP32-Cam IP
    this.saveDir = path.join(process.env.HOME, 'robot-videos');
    
    // 确保目录存在
    if (!fs.existsSync(this.saveDir)) {
      fs.mkdirSync(this.saveDir, { recursive: true });
    }
    
    console.log('📹 视频模块初始化完成');
    console.log('📁 存储目录:', this.saveDir);
  }

  // 截图
  async capture(imagePath) {
    return new Promise((resolve, reject) => {
      const url = `http://${this.cameraIp}/capture`;
      
      const wget = spawn('wget', ['-q', '-O', imagePath, url]);
      
      wget.on('close', (code) => {
        if (code === 0 && fs.existsSync(imagePath)) {
          resolve(imagePath);
        } else {
          reject(new Error('截图失败'));
        }
      });
    });
  }

  // 录制视频片段
  async record(durationSeconds = 10) {
    const outputFile = path.join(this.saveDir, `clip_${Date.now()}.mp4`);
    
    return new Promise((resolve, reject) => {
      const ffmpeg = spawn('ffmpeg', [
        '-i', `rtsp://${this.cameraIp}/stream`,
        '-t', String(durationSeconds),
        '-c:v', 'copy',
        outputFile
      ]);

      ffmpeg.on('close', (code) => {
        if (code === 0) {
          resolve(outputFile);
        } else {
          reject(new Error('录制失败'));
        }
      });
    });
  }

  // 持续录制（循环存储）
  async startRecording(segmentMinutes = 5) {
    console.log(`📹 开始录制，每 ${segmentMinutes} 分钟一段...`);
    
    const recordLoop = async () => {
      try {
        const timestamp = Date.now();
        const outputFile = path.join(this.saveDir, `record_${timestamp}.mp4`);
        
        const ffmpeg = spawn('ffmpeg', [
          '-i', `rtsp://${this.cameraIp}/stream`,
          '-t', String(segmentMinutes * 60),
          '-c:v', 'copy',
          outputFile
        ]);

        ffmpeg.on('close', () => {
          // 继续录制下一段
          recordLoop();
        });
        
      } catch (error) {
        console.error('录制错误:', error);
        setTimeout(recordLoop, 5000);  // 5秒后重试
      }
    };

    recordLoop();
  }

  // 回答关于视频的问题
  async answerQuestion(question) {
    // 截取当前画面
    const imagePath = `/tmp/query_${Date.now()}.jpg`;
    await this.capture(imagePath);
    
    // 发送到 Gateway 进行图像理解
    // (需要 Gateway 支持图像理解)
    const response = await this.sendToGateway({
      type: 'image_query',
      image: imagePath,
      question: question
    });
    
    return response;
  }
}

module.exports = VideoModule;
```

### Step 4: 测试

```bash
cd ~/robot-video
node index.js
```

---

# 六、Phase 2.5: Cyber Bricks 接入

## 6.0 目标

利用已有的 Cyber Bricks 组件（ESP32-C3 + 电机 + 舵机）作为运动控制节点。

## 6.1 硬件说明

Cyber Bricks 是 Bambu Lab 的模块化玩具平台：
- **核心**: ESP32-C3 微控制器
- **固件**: MicroPython（不支持Arduino）
- **通信**: WiFi + 蓝牙
- **组件**: 直流电机、9g 数字舵机

## 6.2 接入方案

### 方案 A: HTTP API（推荐）

在 CyberBrick 上运行 HTTP 服务器，OpenClaw 通过 HTTP 请求控制。

```python
# CyberBrick MicroPython 代码示例
from machine import Pin, PWM
import network
import usocket as socket

# 初始化电机
left_motor = PWM(Pin(1))
right_motor = PWM(Pin(2))

# 初始化舵机
servo1 = PWM(Pin(3))

def web_page():
    html = """<!DOCTYPE html><html>
    <form action="/motor">
    Direction: <input name="dir"><br>
    Speed: <input name="speed"><br>
    <input type="submit">
    </form></html>"""
    return html

def serve():
    s = socket.socket()
    s.bind(('', 80))
    s.listen(5)
    while True:
        conn, addr = s.accept()
        request = conn.recv(1024)
        # 解析请求并控制电机
        conn.send('HTTP/1.1 200 OK\nContent-Type: text/html\n\n')
        conn.send(web_page())
        conn.close()

# 连接 WiFi
sta = network.WLAN(network.STA_IF)
sta.connect('SSID', 'PASSWORD')

serve()
```

### 方案 B: MQTT

CyberBrick 订阅 MQTT 主题，接收控制命令。

```python
# 需要 umqtt 库
from umqtt.simple import MQTTClient

def on_message(topic, msg):
    command = msg.decode()
    if command == 'forward':
        # 前进
    elif command == 'stop':
        # 停止

client = MQTTClient('cyberbrick', 'mqtt-broker')
client.set_callback(on_message)
client.connect()
client.subscribe(b'robot/control')
```

### 方案 C: WebSocket

双向实时通信，适合对战场景。

## 6.3 Jetson Nano 作为网关

Jetson Nano 运行 OpenClaw Node，通过 WiFi 与 CyberBrick 通信：

```
Jetson Nano (OpenClaw Node)
    │
    │ WiFi / HTTP
    ▼
CyberBrick (电机+舵机)
```

## 6.4 控制协议

```json
{
  "type": "motor_control",
  "left_motor": 50,
  "right_motor": -50,
  "servo1_angle": 90
}
```

---

# 六、Phase 3: 自主行动机器人

## 6.1 目标

- 底盘运动控制
- 简单动作（舵机）
- 避障
- 语音指挥移动

## 6.2 硬件清单

| 配件 | 数量 | 备注 |
|------|------|------|
| SG90 舵机 | 4 | 需采购 |
| 6V 减速电机 | 2 | 需采购 |
| L298N 电机驱动 | 1 | 需采购 |
| 麦克纳姆轮 | 4 | 需采购 |
| HC-SR04 超声波 | 2 | 需采购 |
| 12V 锂电池 | 1 | 需采购 |

## 6.3 GPIO 引脚定义

```
Jetson Nano GPIO:
---------------------
GPIO17  -> 电机 PWM (左)
GPIO27  -> 电机方向 (左)
GPIO22  -> 电机 PWM (右)
GPIO23  -> 电机方向 (右)

GPIO24  -> 舵机 1 (头部)
GPIO25  -> 舵机 2 (手臂)

GPIO5   -> 超声波触发 (前)
GPIO6   -> 超声波回显 (前)
GPIO13  -> 超声波触发 (后)
GPIO19  -> 超声波回显 (后)
```

## 6.4 实施步骤

### Step 1: 安装 GPIO 库

```bash
# 安装 WiringPi (兼容库)
cd ~
git clone https://github.com/jetsonhacks/JetsonGPIO.git
cd JetsonGPIO
sudo python3 setup.py install
```

### Step 2: 电机驱动

```javascript
// robot-motion/motor.js
const GPIO = require('jetson-gpio');

class MotorController {
  constructor() {
    // 引脚定义
    this.pins = {
      leftPwm: 17,
      leftDir: 27,
      rightPwm: 22,
      rightDir: 23
    };
    
    this.setup();
  }
  
  setup() {
    // 设置输出模式
    for (let pin of Object.values(this.pins)) {
      try {
        GPIO.setup(pin, GPIO.OUT);
      } catch (e) {
        console.log('GPIO 初始化跳过:', pin);
      }
    }
  }
  
  // 前进
  forward(speed = 50, duration = 0) {
    this.setMotor(this.pins.leftPwm, this.pins.leftDir, speed, true);
    this.setMotor(this.pins.rightPwm, this.pins.rightDir, speed, true);
    
    if (duration > 0) {
      setTimeout(() => this.stop(), duration);
    }
  }
  
  // 后退
  backward(speed = 50, duration = 0) {
    this.setMotor(this.pins.leftPwm, this.pins.leftDir, speed, false);
    this.setMotor(this.pins.rightPwm, this.pins.rightDir, speed, false);
    
    if (duration > 0) {
      setTimeout(() => this.stop(), duration);
    }
  }
  
  // 左转
  turnLeft(speed = 50, duration = 0) {
    this.setMotor(this.pins.leftPwm, this.pins.leftDir, speed, false);
    this.setMotor(this.pins.rightPwm, this.pins.rightDir, speed, true);
    
    if (duration > 0) {
      setTimeout(() => this.stop(), duration);
    }
  }
  
  // 右转
  turnRight(speed = 50, duration = 0) {
    this.setMotor(this.pins.leftPwm, this.pins.leftDir, speed, true);
    this.setMotor(this.pins.rightPwm, this.pins.rightDir, speed, false);
    
    if (duration > 0) {
      setTimeout(() => this.stop(), duration);
    }
  }
  
  // 停止
  stop() {
    this.setMotor(this.pins.leftPwm, this.pins.leftDir, 0, false);
    this.setMotor(this.pins.rightPwm, this.pins.rightDir, 0, false);
  }
  
  setMotor(pwmPin, dirPin, speed, direction) {
    try {
      // 设置方向
      GPIO.output(dirPin, direction ? GPIO.HIGH : GPIO.LOW);
      
      // 设置 PWM (需要外设库)
      // 这里简化处理，实际需要 PWM 库
      console.log(`Motor: pwm=${pwmPin}, dir=${dirPin}, speed=${speed}, dir=${direction}`);
    } catch (e) {
      console.log('Motor control error:', e.message);
    }
  }
}

module.exports = MotorController;
```

### Step 3: 超声波测距

```javascript
// robot-motion/ultrasonic.js
const GPIO = require('jetson-gpio');

class UltrasonicSensor {
  constructor(triggerPin, echoPin) {
    this.trigger = triggerPin;
    this.echo = echoPin;
    
    try {
      GPIO.setup(this.trigger, GPIO.OUT);
      GPIO.setup(this.echo, GPIO.IN);
    } catch (e) {
      console.log('GPIO 初始化跳过');
    }
  }
  
  async measure() {
    return new Promise((resolve) => {
      try {
        // 发送触发信号
        GPIO.output(this.trigger, GPIO.HIGH);
        setTimeout(() => {
          GPIO.output(this.trigger, GPIO.LOW);
          
          // 等待回响
          const startTime = Date.now();
          const checkEcho = setInterval(() => {
            if (GPIO.input(this.echo) === GPIO.HIGH) {
              clearInterval(checkEcho);
              const endTime = Date.now();
              const distance = (endTime - startTime) * 0.034 / 2;
              resolve(distance);
            }
          }, 10);
          
          // 超时
          setTimeout(() => {
            clearInterval(checkEcho);
            resolve(-1);
          }, 100);
          
        }, 10);
      } catch (e) {
        resolve(-1);
      }
    });
  }
}

module.exports = UltrasonicSensor;
```

### Step 4: 避障逻辑

```javascript
// robot-motion/safety.js
const MotorController = require('./motor');
const UltrasonicSensor = require('./ultrasonic');

class SafetySystem {
  constructor() {
    this.motor = new MotorController();
    
    // 前后各一个超声波
    this.frontSensor = new UltrasonicSensor(5, 6);
    this.rearSensor = new UltrasonicSensor(13, 19);
    
    this.minDistance = 20;  // 厘米
    this.isEnabled = true;
  }
  
  async check() {
    if (!this.isEnabled) return true;
    
    const front = await this.frontSensor.measure();
    const rear = await this.rearSensor.measure();
    
    console.log(`距离: 前=${front}cm, 后=${rear}cm`);
    
    // 前面有障碍
    if (front > 0 && front < this.minDistance) {
      console.log('⚠️ 前方有障碍!');
      this.motor.stop();
      return false;
    }
    
    return true;
  }
  
  enable() {
    this.isEnabled = true;
  }
  
  disable() {
    this.isEnabled = false;
  }
}

module.exports = SafetySystem;
```

### Step 5: 语音指挥移动

```javascript
// 将这个功能整合到 voice 模块
// 接收到移动指令时调用

const MotorController = require('./motor');
const SafetySystem = require('./safety');

const motor = new MotorController();
const safety = new SafetySystem();

// 移动命令处理
function handleMoveCommand(command) {
  switch(command) {
    case '前进':
    case 'forward':
      motor.forward(50, 2000);
      break;
      
    case '后退':
    case 'backward':
      motor.backward(50, 2000);
      break;
      
    case '左转':
    case 'turn left':
      motor.turnLeft(50, 1000);
      break;
      
    case '右转':
    case 'turn right':
      motor.turnRight(50, 1000);
      break;
      
    case '停止':
    case 'stop':
      motor.stop();
      break;
  }
}
```

---

# 七、Phase 4: 安全与紧急响应

## 7.1 安全功能

| 功能 | 实现方式 |
|------|---------|
| 身份认证 | 人脸识别 / 声纹 |
| 物理钥匙 | U 盘证书 |
| 异常检测 | 移动检测 |
| 自动报警 | 定位 + 通知 |
| 数据自毁 | 远程格式化 |

## 7.2 实施步骤

### Step 1: 声纹识别

```javascript
// robot-security/voiceprint.js
const fs = require('fs');

class VoicePrintAuth {
  constructor() {
    this.enrolled = false;
    this.voiceprint = null;
  }
  
  // 录入声纹
  async enroll(audioFile) {
    // 发送到 Gateway 进行声纹识别
    // 这里简化处理
    console.log('🔐 录入声纹中...');
    this.enrolled = true;
    this.voiceprint = 'sample_voiceprint';
    console.log('✅ 声纹录入完成');
  }
  
  // 验证
  async verify(audioFile) {
    if (!this.enrolled) {
      return true;  // 未录入则通过
    }
    
    // 实际需要声纹对比
    console.log('🔐 声纹验证中...');
    return true;
  }
}

module.exports = VoicePrintAuth;
```

### Step 2: 异常检测

```javascript
// robot-security/motion-detect.js
class MotionDetector {
  constructor() {
    this.isArmed = false;
    this.lastMotionTime = Date.now();
  }
  
  // 检测运动
  detect(frame) {
    // 简化处理：可以通过帧差法检测
    // 实际使用 OpenCV
    return false;
  }
  
  // 报警
  alert() {
    console.log('🚨 异常运动检测!');
    
    // 1. 响警报
    this.playAlarm();
    
    // 2. 通知 Gateway
    this.notifyGateway();
    
    // 3. 记录
    this.logEvent();
  }
  
  playAlarm() {
    // 播放警报声
    execSync('aplay alarm.wav');
  }
  
  notifyGateway() {
    // 发送通知
    // ...
  }
  
  logEvent() {
    // 记录到日志
  }
}

module.exports = MotionDetector;
```

### Step 3: 数据自毁

```javascript
// robot-security/emergency.js
const fs = require('fs');
const { execSync } = require('child_process');

class EmergencySystem {
  constructor() {
    this.dataPaths = [
      process.env.HOME + '/robot-videos',
      process.env.HOME + '/robot-data'
    ];
  }
  
  // 触发自毁
  async selfDestruct() {
    console.log('💣 触发数据自毁...');
    
    // 1. 多次覆写确保数据不可恢复
    for (let path of this.dataPaths) {
      if (fs.existsSync(path)) {
        // 覆写随机数据
        this.secureDelete(path);
      }
    }
    
    // 2. 通知 Gateway
    this.notifyDestruct();
    
    console.log('✅ 数据已销毁');
  }
  
  secureDelete(path) {
    try {
      // 简单删除（实际应该多次覆写）
      execSync(`rm -rf ${path}`);
    } catch (e) {
      console.error('删除失败:', e);
    }
  }
  
  notifyDestruct() {
    // 通知 Gateway
    console.log('📤 已通知 Gateway: 设备已自毁');
  }
}

module.exports = EmergencySystem;
```

---

# 八、系统集成

## 8.1 启动脚本

创建统一的启动脚本：

```bash
#!/bin/bash
# robot-start.sh

echo "🤖 启动 OpenClaw 机器人..."

# 检查网络
echo "📡 检查网络连接..."
ping -c 1 8.8.8.8 > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "⚠️ 网络未连接"
fi

# 启动各个模块
echo "📹 启动视频模块..."
cd ~/robot-video
node index.js &

echo "🎙️ 启动语音模块..."
cd ~/robot-voice
node main.js &

echo "🦿 启动运动模块..."
cd ~/robot-motion
node safety.js &

echo "🛡️ 启动安全模块..."
cd ~/robot-security
node monitor.js &

echo "✅ 机器人启动完成!"
```

设置为开机自启：

```bash
chmod +x robot-start.sh
sudo cp robot-start.sh /etc/init.d/robot
sudo update-rc.d robot defaults
```

---

# 九、维护与迭代

## 9.1 日常维护

| 任务 | 频率 |
|------|------|
| 检查存储空间 | 每天 |
| 清理旧视频 | 每周 |
| 检查网络连接 | 每天 |
| 测试语音识别 | 每周 |
| 检查电池状态 | 每天 |

## 9.2 常见问题排查

| 问题 | 原因 | 解决 |
|------|------|------|
| 语音识别慢 | 模型太大 | 用 tiny 模型 |
| 视频卡顿 | WiFi 信号弱 | 靠近路由器 |
| 电机不动 | 供电不足 | 检查电池 |
| 无法连接 Gateway | IP 不对 | 检查配置 |

---

# 十、风险评估

## 10.1 技术风险

| 风险 | 影响 | 对策 |
|------|------|------|
| Jetson Nano 性能不足 | 延迟高 | 换 Orin Nano |
| WiFi 断联 | 失控 | 星闪备用 |
| 隐私泄露 | 安全问题 | 本地处理 |
| 电池续航短 | 无法移动 | 大容量电池 |

## 10.2 法规风险

| 风险 | 影响 | 对策 |
|------|------|------|
| 机器人上路 | 法规问题 | 室内/牵绳 |
| 摄像头隐私 | 法律风险 | 本地处理 + 提示灯 |

---

# 十一、附录

## A. 常用命令

```bash
# Jetson Nano
ssh nvidia@<IP>
arecord -l
aplay -l
alsamixer

# ESP32-Cam
esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash

# 测试
ffplay rtsp://<IP>/stream
```

## B. GPIO 参考

Jetson Nano 40-pin 扩展座：
- GPIO 编号: 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27

## C. 参考资源

- Jetson Nano 官方文档
- ESP32-Cam 项目
- whisper.cpp
- OpenCV
- NVIDIA JetPack

---

*本文档将持续更新完善*
