# Phase 2 视觉记录模块 - ESP32-Cam 固件结构补充

> 数据来源：espressif/esp32-camera 官方库文档 + GitHub
> 最后更新：2026-03-28

---

## 1. ESP32-Cam 硬件规格

| 项目 | 规格 |
|------|------|
| 主芯片 | ESP32 (Xtensa dual-core 32-bit LX6) |
| 图像传感器 | OV2640（默认）/ OV5640 / OV3660 等可选 |
| PSRAM | 4MB PSRAM（部分型号无） |
| Flash | 4MB SPI Flash |
| WiFi | 802.11 b/g/n |
| 接口 | USB（供电+调试）、UART（GPIO0/1/3）、I2C（SCCB） |

---

## 2. 固件架构总览

ESP32-Cam 固件由多个层次构成：

```
┌─────────────────────────────────────────┐
│      应用层 (app_main / your code)       │
├─────────────────────────────────────────┤
│  图像处理层 (frame2jpg / frame2bmp)      │
├─────────────────────────────────────────┤
│  Camera Driver (esp_camera)              │
│    - sensor control (SCCB/I2C)           │
│    - I2S DMA frame capture               │
│    - frame buffer management             │
├─────────────────────────────────────────┤
│  图像传感器层 (OV2640/OV5640 driver)     │
├─────────────────────────────────────────┤
│  ESP32 HW (I2S, GPIO, WiFi, PSRAM)      │
└─────────────────────────────────────────┘
```

---

## 3. esp32-camera 库核心模块

### 3.1 核心头文件

| 文件 | 作用 |
|------|------|
| `esp_camera.h` | 主头文件，包含 `camera_config_t`、`esp_camera_init()`、`esp_camera_fb_get()` 等核心 API |
| `sensor.h` | 传感器底层控制（亮度、对比度、饱和度、镜像、翻转等） |
| `esp_camera_af.h` | OV5640 自动对焦辅助（可选） |

### 3.2 核心 API

```c
// 初始化摄像头
esp_err_t esp_camera_init(const camera_config_t *config);

// 获取一帧图像
camera_fb_t *esp_camera_fb_get();

// 归还帧缓冲（必须调用）
void esp_camera_fb_return(camera_fb_t *fb);

// 获取传感器句柄（用于调整参数）
sensor_t *esp_camera_sensor_get();
```

### 3.3 camera_config_t 关键配置

```c
camera_config_t config = {
    .pin_pwdn     = -1,        // 断电引脚（多数型号不用）
    .pin_reset    = -1,        // 复位引脚（软件复位，-1即可）
    .pin_xclk     = 21,        // XCLK 时钟输出（通常21）
    .pin_sccb_sda = 26,        // SCCB (I2C) 数据线
    .pin_sccb_scl = 27,        // SCCB (I2C) 时钟线
    // 8-bit DVP 数据口
    .pin_d7 = 35; .pin_d6 = 34; .pin_d5 = 39; .pin_d4 = 36;
    .pin_d3 = 19; .pin_d2 = 18; .pin_d1 =  5; .pin_d0 =  4;
    .pin_vsync = 25;           // VSYNC
    .pin_href  = 23;           // HREF
    .pin_pclk  = 22;           // Pixel Clock

    .xclk_freq_hz = 20000000, // XCLK 频率（20MHz，OV2640推荐值）
    .ledc_timer   = LEDC_TIMER_0,
    .ledc_channel = LEDC_CHANNEL_0,

    // 关键：像素格式和分辨率
    .pixel_format = PIXFORMAT_JPEG,  // YUV422 / GRAYSCALE / RGB565 / JPEG
    .frame_size   = FRAMESIZE_SVGA,  // QVGA / SVGA / UXGA 等
    .jpeg_quality = 12,              // JPEG质量 0-63，越小质量越高
    .fb_count     = 1,               // 帧缓冲数量（>1时I2S连续模式）
    .grab_mode    = CAMERA_GRAB_WHEN_EMPTY,
};
```

---

## 4. 内存布局

### 4.1 ESP32 内存区域

| 区域 | 大小 | 用途 |
|------|------|------|
| DRAM | 520KB | 指令数据、堆、栈 |
| IRAM | 128KB | 频繁执行的代码（WiFi堆栈等） |
| PSRAM | 0-8MB | 图像帧缓冲（外部SPI RAM） |

### 4.2 帧缓冲策略

**JPEG 模式（推荐）**：
- JPEG 原始压缩数据直接来自传感器，不需要额外 PSRAM 做格式转换
- 帧缓冲可放在 PSRAM 或 DRAM
- QVGA (320×240) JPEG ≈ 15-30KB/帧
- SVGA (800×600) JPEG ≈ 80-150KB/帧

**RGB565/YUV 模式（不推荐）**：
- 每个像素 2 字节，UXGA ≈ 6MB/帧
- 必须使用 PSRAM，DRAM 放不下
- WiFi 开启时写入 PSRAM 速度不够，容易丢帧

**帧缓冲数量策略**：
| fb_count | 模式 | 特点 |
|----------|------|------|
| 1 | 单次获取 | 控制精准，但帧率低 |
| 2+ | 连续 I2S DMA | 帧率高，但 CPU/内存压力大，仅 JPEG 模式可用 |

---

## 5. 流媒体输出：HTTP MJPEG vs RTSP

### 5.1 HTTP MJPEG（最常用）

基于 `esp_http_server` 组件，使用 multipart/x-mixed-replace 协议。

**工作流程**：
```
esp_camera_fb_get()  →  JPEG原始数据  →  HTTP chunked response  →  浏览器/客户端
     (每帧)               直接发送              不断开连接                持续显示
```

**代码结构**（camera_example）：
```c
// HTTP handler 注册
httpd_handle_t start_webserver(void)
{
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    httpd_start(&server, &config);

    // 注册 MJPEG 流 handler
    httpd_uri_t stream_uri = {
        .uri     = "/stream",
        .method  = HTTP_GET,
        .handler = jpg_stream_httpd_handler,
    };
    httpd_register_uri_handler(server, &stream_uri);
}

// MJPEG handler 核心循环
esp_err_t jpg_stream_httpd_handler(httpd_req_t *req)
{
    while (true) {
        fb = esp_camera_fb_get();
        // 发送 HTTP multipart 分块
        httpd_resp_send_chunk(req, "--boundary\r\n", ...);
        httpd_resp_send_chunk(req, "Content-Type: image/jpeg\r\n", ...);
        httpd_resp_send_chunk(req, jpg_buf, jpg_buf_len);
        httpd_resp_send_chunk(req, "\r\n", ...);
        esp_camera_fb_return(fb);
    }
}
```

**优缺点**：
- ✅ 实现简单，esp32-camera 库自带示例
- ✅ 任何浏览器直接查看（无插件）
- ✅ 延迟较低（~200-500ms）
- ❌ 非标准协议，无法被标准 RTSP 播放器直接使用
- ❌ 没有会话管理，客户端断开不易感知

### 5.2 RTSP 流（需要额外库）

RTSP 协议更复杂，需要 `librtsp` 或自行实现。

**推荐方案：使用 `esp-rtsp` 组件**

```bash
# 添加到 idf_component.yml
dependencies:
  esp-rtsp: "*"
```

**RTSP 工作流程**：
```
客户端(ffplay)  --RTSP DESCRIBE/SETUP/PLAY-->  ESP32
客户端  <--RTSP 200 OK + SDP-->                   ESP32
客户端  <--RTP 包 (JPEG)-->                       ESP32
```

**ffplay 拉流命令**：
```bash
ffplay rtsp://192.168.1.99:8554/stream
```

**GStreamer 低延迟 pipeline**：
```bash
gst-launch-1.0 rtspsrc location=rtsp://192.168.1.99:8554/stream \
  ! decodebin ! videoconvert ! autovideosink
```

**优缺点**：
- ✅ 标准协议，可被所有视频客户端使用
- ✅ 支持会话管理（PLAY/PAUSE/TEARDOWN）
- ✅ 可复用 RTSP-over-UDP 实现更低延迟
- ❌ 实现复杂，ESP32 资源有限
- ❌ WiFi 干扰时 UDP 包容易丢失

### 5.3 对比

| 特性 | HTTP MJPEG | RTSP |
|------|-------------|------|
| 兼容性 | 浏览器直接看 | 需 VLC/ffplay/GStreamer |
| 延迟 | 中等（200-500ms） | 可更低（100-300ms via UDP） |
| 实现难度 | 简单 | 复杂 |
| ESP32 资源占用 | 低 | 中高 |
| NAT 穿透 | 难 | 支持 |
| 标准程度 | 非标准 | ITU-T 标准 |

**建议**：先用 HTTP MJPEG 测试，实际部署 Jetson Nano 接收时换 RTSP。

---

## 6. 主流固件项目对比

### 6.1 CameraWebServer（Arduino IDE 内置）

**来源**：Arduino IDE → ESP32 → Camera → AI Thinker Configuration

- 固件臃肿，包含 Web UI、光敏检测、LED 控制等
- Web UI 界面美观但占用资源
- 集成 AP 模式 + STA 模式自动切换
- 静态图像拍摄+JPEG 流+视频流

### 6.2 esp32-cam-webserver（GitHub: easytarget）

**来源**：https://github.com/easytarget/esp32-cam-webserver

- 专为 ESP32-Cam 优化的轻量级 Web 服务器
- 支持 HTTP MJPEG 流
- 支持人形检测（基于 moving average）
- 支持 SD 卡存储
- 配置简单，通过 Arduino IDE 上传

### 6.3 esp32-camera 库（官方）

**来源**：https://github.com/espressif/esp32-camera

- **最核心的库**，其他固件都基于它
- 不含 HTTP/RTSP 服务端，需自行集成
- 提供纯 C API：`esp_camera_init()`、`esp_camera_fb_get()`
- 支持所有主流 OV 系列传感器
- ESP-IDF 原生支持，Arduino 也能用

### 6.4 对比表

| 特性 | CameraWebServer | esp32-cam-webserver | esp32-camera (官方库) |
|------|-----------------|---------------------|----------------------|
| Web UI | 有（美观） | 简单 | 无 |
| HTTP MJPEG | ✅ | ✅ | 需自行实现 |
| RTSP | ❌ | ❌ | 需自行实现 |
| SD 卡支持 | ✅ | ✅ | ❌ |
| 人形检测 | ❌ | ✅ | ❌ |
| OTA 更新 | ✅ | ✅ | ❌ |
| 固件大小 | ~1.5MB | ~600KB | ~200KB（最小） |
| 适用场景 | 快速测试 | 家用监控 | 定制开发 |

---

## 7. 固件烧录地址映射

ESP32-Cam 烧录地址（AI Thinker 型号）：

| 分区 | 起始地址 | 大小 | 说明 |
|------|----------|------|------|
| bootloader | 0x1000 | 48KB | 二级引导程序 |
| partition_table | 0x8000 | 4KB | 分区表 |
| nvs | 0x9000 | 20KB | WiFi 配置存储 |
| otadata | 0xe000 | 8KB | OTA 数据区 |
| app0 | 0x10000 | 1280KB | 主应用程序 |
| app1 | 0x150000 | 1280KB | OTA 备份区（可选）|
| spiffs | 0x170000 | 1408KB | 文件系统（存 HTML/CSS/JS）|

**esptool 烧录示例**：
```bash
# 擦除
esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash

# 烧录 CameraWebServer 固件
esptool.py --chip esp32 --port /dev/ttyUSB0 \
  write_flash 0x1000 bootloader.bin \
  0x8000 partitions.bin \
  0x10000 camera_webserver.bin \
  0x170000 spiffs.bin
```

---

## 8. 常见问题排查

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| `Camera init failed` | GPIO 接线错误 | 确认 OV2640 对应 GPIO 编号（AI Thinker 型号用上表）|
| 画面全黑/绿 | XCLK 频率不对 | 设为 20MHz（OV2640）|
| 帧率极低（<5fps）| fb_count>1 + 非 JPEG 格式 | 切换 JPEG 模式，fb_count=1 |
| WiFi 断开后无法重连 | WiFi 在 JPEG 采集时抢占 CPU | 降低分辨率或关闭 WiFi 节能 |
| PSRAM 错误 | 分区表未启用 PSRAM | menuconfig → ESP32 SPI RAM → Enabled |
| 烧录失败 | GPIO0 未接地 | 烧录时 GPIO0 接 GND，烧录完断开 |

---

## 9. 推荐开发路径

```
Phase 1: CameraWebServer（Arduino IDE）
    ↓ 测试 GPIO 接线、WiFi 连接
Phase 2: esp32-cam-webserver
    ↓ 增加人形检测、SD 卡存储
Phase 3: esp32-camera 库 + 自定义 HTTP/RTSP
    ↓ Jetson Nano 接收，边缘计算
Phase 4: 集成到 Robot SOP 架构
```

**SOP 建议**：先用 CameraWebServer 验证硬件通电正常，再用 esp32-camera 库做定制开发。

---

## 10. WiFi 配置流程（STA 模式）

> 适用场景：ESP32-Cam 作为视频数据上联设备，需要稳定连接路由器供 Jetson Nano 接收 RTSP 流。
> 基于 ESP-IDF `esp_wifi` API，非 Arduino WiFi 库。

### 10.1 WiFi 架构概述

```
┌──────────────────────────────────────────────────────────┐
│                     ESP32 WiFi 子系统                     │
├──────────────────────────────────────────────────────────┤
│  WiFi Driver (esp_wifi)                                  │
│    - LCA (Low-Level WiFi Adapter)                        │
│    - HPA (High-Level WiFi Adapter)                       │
│    - Supplicant (WPA2 认证)                               │
│    - TCP/IP 协议栈 (LwIP)                                 │
├──────────────────────────────────────────────────────────┤
│  WiFi NVS Library (WiFi 配置参数存储)                      │
│  WiFi RF (硬件)                                          │
└──────────────────────────────────────────────────────────┘
```

### 10.2 初始化流程

**Step 1：NVS Flash 初始化**
```c
#include "esp_wifi.h"
#include "nvs_flash.h"
#include "esp_netif.h"

esp_err_t wifi_init(void)
{
    // 1. NVS Flash 必须先初始化（WiFi 配置存 NVS）
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }

    // 2. 初始化 LwIP（必须！负责 IP 层）
    ESP_ERROR_CHECK(esp_netif_init());

    // 3. 创建默认事件循环（WiFi 事件通过它分发）
    ESP_ERROR_CHECK(esp_event_loop_create_default());

    // 4. 创建默认网卡（STA 模式）
    esp_netif_create_default_wifi_sta();
}
```

**Step 2：WiFi 控制器初始化**
```c
wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
ESP_ERROR_CHECK(esp_wifi_init(&cfg));

// 可选：设置 WiFi 省电模式（视频流建议关闭省电）
ESP_ERROR_CHECK(esp_wifi_set_ps(WIFI_PS_NONE));
```

**Step 3：配置 SSID/密码并启动 STA**
```c
wifi_config_t wifi_config = {
    .sta = {
        .ssid = "YOUR_SSID",
        .password = "YOUR_PASSWORD",
        .threshold.authmode = WIFI_AUTH_WPA2_PSK,
        .pmf_cfg = {
            .capable = true,   // 启用 PMF（Protected Management Frames）
            .required = false,
        },
    },
};

ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
ESP_ERROR_CHECK(esp_wifi_start());

ESP_LOGI(TAG, "WiFi STA 启动，SSID=%s", wifi_config.sta.ssid);
```

### 10.3 WiFi 事件处理

**注册事件处理器**：
```c
#include "esp_event.h"
#include "esp_netif_types.h"

static void wifi_event_handler(void *arg, esp_event_base_t event_base,
                                int32_t event_id, void *event_data)
{
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();  // STA 启动后主动连接
    }
    else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        // 断开连接 → 自动重连（默认已开启）
        ESP_LOGI(TAG, "WiFi 断开，尝试重连...");
    }
    else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t *event = (ip_event_got_ip_t *)event_data;
        ESP_LOGI(TAG, "获取 IP: " IPSTR, IP2STR(&event->ip_info.ip));
    }
}

// 注册
ESP_ERROR_CHECK(esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID, &wifi_event_handler, NULL));
ESP_ERROR_CHECK(esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP, &wifi_event_handler, NULL));
```

**自动重连逻辑**：
- ESP-IDF 默认开启自动重连（`reconnect` 模式）
- 断开后会自动尝试重连，直到调用 `esp_wifi_disconnect()`
- 如果路由器不可达，最多重试 `WIFI_RETRY_MAX` 次（约 10 次，间隔递增）

### 10.4 信号质量监测

```c
#include "esp_wifi.h"

void get_wifi_rssi(void)
{
    wifi_ap_record_t ap_info;
    esp_err_t ret = esp_wifi_sta_get_ap_info(&ap_info);
    if (ret == ESP_OK) {
        ESP_LOGI(TAG, "RSSI: %d dBm, 信道: %d", ap_info.rssi, ap_info.primary);
        // RSSI 等级参考：
        // > -50 dBm: 优秀
        // -50 ~ -60 dBm: 良好
        // -60 ~ -70 dBm: 一般
        // < -70 dBm: 差，视频可能卡顿
    }
}
```

### 10.5 多网络配置（NVS 存储）

将 SSID/密码存 NVS，避免硬编码：

```c
#include "nvs_flash.h"
#include "nvs.h"

#define NVS_NAMESPACE "wifi_config"

void save_wifi_creds(const char *ssid, const char *password)
{
    nvs_handle_t nvs;
    nvs_open(NVS_NAMESPACE, NVS_READWRITE, &nvs);
    nvs_set_str(nvs, "ssid", ssid);
    nvs_set_str(nvs, "password", password);
    nvs_commit(nvs);
    nvs_close(nvs);
}

void load_wifi_creds(char *ssid_buf, char *pass_buf, size_t buf_len)
{
    nvs_handle_t nvs;
    nvs_open(NVS_NAMESPACE, NVS_READONLY, &nvs);
    nvs_get_str(nvs, "ssid", ssid_buf, &buf_len);
    // 注意：password 的 buf_len 需要单独处理
    nvs_close(nvs);
}
```

### 10.6 ESP32-Cam 静态 IP 配置

在 SOP Phase 2 的代码基础上，补充完整的静态 IP 配置：

```cpp
#include "esp_netif.h"
#include "esp_netif_types.h"

// 创建 STA 网卡并配置静态 IP
esp_netif_t *sta_netif = esp_netif_create_default_wifi_sta();

esp_netif_ip_info_t ip_info;
IP4_ADDR(&ip_info.ip, 192, 168, 1, 99);       // ESP32-Cam 静态 IP
IP4_ADDR(&ip_info.gw, 192, 168, 1, 1);        // 网关（路由器 IP）
IP4_ADDR(&ip_info.netmask, 255, 255, 255, 0); // 子网掩码
esp_netif_set_ip_info(sta_netif, &ip_info);

// 可选：配置 DNS
esp_netif_dns_info_t dns;
IP4_ADDR(&dns.ip.u_addr.ip4, 8, 8, 8, 8); // Google DNS
esp_netif_set_dns(sta_netif, ESP_NETIF_DNS_MAIN, &dns);
```

### 10.7 WiFi 和省电的权衡

| 场景 | 推荐配置 | 原因 |
|------|----------|------|
| 持续视频流 | `WIFI_PS_NONE`（关闭省电） | 省电模式会断电导致帧丢失 |
| 间歇拍照 | `WIFI_PS_MIN_MODEM` | 平衡功耗和响应速度 |
| 电池供电长时间待机 | `WIFI_PS_MAX_MODEM` | 最大限度省电 |

**注意**：ESP32-Cam 视频流时**必须关闭 WiFi 省电**，否则 I2S DMA 和 WiFi抢占 CPU 导致严重丢帧。

### 10.8 常见错误码

| 错误码 | 含义 | 解决方法 |
|--------|------|----------|
| `ESP_ERR_WIFI_SSID` | SSID 长度不对（1-32字符） | 检查 SSID |
| `ESP_ERR_WIFI_PASSWORD` | 密码长度不对（8-63字符或0） | 检查密码 |
| `ESP_ERR_WIFI_NOT_CONNECTED` | 未连接 | 等待 `IP_EVENT_STA_GOT_IP` 或检查路由器 |
| `ESP_ERR_WIFI_IF` | 网卡接口错误 | 确认 `WIFI_IF_STA` |
| `ESP_ERR_ESPNOW_NOT_INIT` | ESPNOW 未初始化 | 先调用 `esp_now_init()` |

### 10.9 ESP32-Cam WiFi + 摄像头并发注意事项

ESP32 单核只有 240MHz，WiFi 和摄像头 I2S DMA 共享总线带宽。实践中常见问题及对策：

| 问题 | 原因 | 对策 |
|------|------|------|
| 视频卡顿/撕裂 | WiFi 抢占 I2S 总线 | 降低分辨率或降低 WiFi 发送功率 |
| 间歇性断连 | WiFi 和 I2S 中断竞争 | `esp_wifi_set_inactive_time()` 错开中断 |
| 启动时死机 | WiFi 初始化太早 | 先初始化摄像头，再初始化 WiFi |
| 发热严重 | WiFi 持续最大功率 | 降低 xclk_freq_hz，或加散热片 |

---

## 11. JPEG 捕获完整代码（生产级）

> 本节提供可直接编译运行的完整代码示例，涵盖：摄像头初始化 → JPEG 捕获循环 → SD 卡存储 → HTTP MJPEG 流媒体。
> 代码基于 ESP-IDF + esp32-camera 官方库。

### 11.1 摄像头初始化（完整版）

```c
#include "esp_camera.h"
#include "esp_log.h"
#include "esp_err.h"

static const char *TAG = "camera";

// ESP32-Cam AI Thinker GPIO 引脚定义
#define CAM_PIN_PWDN    -1  // 低电平断电（不用）
#define CAM_PIN_RESET    -1  // 软件复位（不用）
#define CAM_PIN_XCLK     21
#define CAM_PIN_SCCB_SDA 26
#define CAM_PIN_SCCB_SCL 27
#define CAM_PIN_D7       35
#define CAM_PIN_D6       34
#define CAM_PIN_D5       39
#define CAM_PIN_D4       36
#define CAM_PIN_D3       19
#define CAM_PIN_D2       18
#define CAM_PIN_D1        5
#define CAM_PIN_D0        4
#define CAM_PIN_VSYNC    25
#define CAM_PIN_HREF     23
#define CAM_PIN_PCLK     22

esp_err_t camera_init(void)
{
    camera_config_t config;
    memset(&config, 0, sizeof(config));

    config.pin_pwdn     = CAM_PIN_PWDN;
    config.pin_reset   = CAM_PIN_RESET;
    config.pin_xclk    = CAM_PIN_XCLK;
    config.pin_sccb_sda = CAM_PIN_SCCB_SDA;
    config.pin_sccb_scl = CAM_PIN_SCCB_SCL;
    config.pin_d7       = CAM_PIN_D7;
    config.pin_d6       = CAM_PIN_D6;
    config.pin_d5       = CAM_PIN_D5;
    config.pin_d4       = CAM_PIN_D4;
    config.pin_d3       = CAM_PIN_D3;
    config.pin_d2       = CAM_PIN_D2;
    config.pin_d1       = CAM_PIN_D1;
    config.pin_d0       = CAM_PIN_D0;
    config.pin_vsync    = CAM_PIN_VSYNC;
    config.pin_href     = CAM_PIN_HREF;
    config.pin_pclk     = CAM_PIN_PCLK;

    config.xclk_freq_hz = 20000000;       // 20MHz，OV2640 推荐
    config.ledc_timer   = LEDC_TIMER_0;
    config.ledc_channel  = LEDC_CHANNEL_0;

    // 关键配置：JPEG 模式
    config.pixel_format = PIXFORMAT_JPEG; // JPEG 压缩（推荐，省内存）
    config.frame_size   = FRAMESIZE_SVGA; // 800×600（平衡画质和帧率）
    config.jpeg_quality = 12;             // 0-63，越小质量越高，12=中上质量
    config.fb_count     = 1;              // JPEG 模式下 1 足够
    config.grab_mode    = CAMERA_GRAB_WHEN_EMPTY;

    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "摄像头初始化失败: 0x%x", err);
        return err;
    }

    // 可选：调整传感器参数（亮度/对比度/饱和度）
    sensor_t *s = esp_camera_sensor_get();
    if (s != NULL) {
        s->set_brightness(s, 0);      // -2 to 2
        s->set_contrast(s, 0);       // -2 to 2
        s->set_saturation(s, 0);    // -2 to 2
        s->set_whitebal(s, 1);       // 白平衡 0/1
        s->set_awb_gain(s, 1);       // 自动白平衡增益 0/1
        s->set_wb_mode(s, 0);        // 0: 自动, 1: 太阳光, 2: 阴天, 3: 白炽灯
        s->set_exposure_ctrl(s, 1);  // 自动曝光 0/1
        s->set_aec2(s, 0);           // 自动曝光补偿 0/1
        s->set_ae_level(s, 0);       // 自动曝光等级 -2 to 2
        s->set_aec_value(s, 120);    // 手动曝光值 0-1200
        s->set_gain_ctrl(s, 0);     // 手动增益 0/1
        s->set_agc_gain(s, 0);       // 自动增益 0-30
        s->set_gainceiling(s, (gainceiling_t)0);  // 增益上限
        s->set_bpc(s, 0);            // 坏点校正 0/1
        s->set_wpc(s, 1);            // 全局坏点校正 0/1
        s->set_raw_gma(s, 1);       // 全局映射 0/1
        s->set_lenc(s, 1);           // 镜头校正 0/1
        s->set_hmirror(s, 0);       // 水平镜像 0/1
        s->set_vflip(s, 0);          // 垂直翻转 0/1
        s->set_dcw(s, 1);            // 向下采样（降噪）0/1
        s->set_colorbar(s, 0);       // 彩色测试条 0/1
    }

    ESP_LOGI(TAG, "摄像头初始化成功");
    return ESP_OK;
}
```

### 11.2 JPEG 捕获循环（带错误处理和性能统计）

```c
#include "esp_camera.h"
#include "esp_timer.h"
#include "esp_log.h"

static const char *TAG = "capture";

#define CAPTURE_INTERVAL_MS 200  // 5 FPS（视频记录够用，省带宽）

void capture_loop(void *pvParameters)
{
    size_t jpg_len;
    int64_t capture_count = 0;
    int64_t error_count = 0;
    int64_t total_bytes = 0;
    int64_t last_report = esp_timer_get_time() / 1000;

    while (true) {
        int64_t loop_start = esp_timer_get_time() / 1000;

        // Step 1: 获取一帧
        camera_fb_t *fb = esp_camera_fb_get();
        if (!fb) {
            error_count++;
            ESP_LOGW(TAG, "帧获取失败 (累计错误: %lld)", error_count);
            vTaskDelay(pdMS_TO_TICKS(100));  // 失败后稍等再试
            continue;
        }

        // Step 2: 验证 JPEG 数据
        if (fb->format != PIXFORMAT_JPEG) {
            ESP_LOGW(TAG, "非 JPEG 格式: %d", fb->format);
            esp_camera_fb_return(fb);
            continue;
        }

        if (fb->len < 1000) {
            ESP_LOGW(TAG, "JPEG 数据异常小: %zu bytes", fb->len);
            esp_camera_fb_return(fb);
            continue;
        }

        // Step 3: 处理 JPEG 数据
        jpg_len = fb->len;
        total_bytes += jpg_len;
        capture_count++;

        // 这里可以：存入 SD 卡 / 发送到服务器 / 发布到 ROS
        // 例：save_to_sd(fb->buf, jpg_len);
        // 例：send_over_network(fb->buf, jpg_len);

        // Step 4: 归还帧缓冲（必须！）
        esp_camera_fb_return(fb);

        // Step 5: 定时报告
        int64_t now = esp_timer_get_time() / 1000;
        if (now - last_report >= 10000) {  // 每 10 秒报告一次
            float fps = (float)capture_count * 1000 / (now - last_report);
            float mbps = (float)total_bytes * 8 / (now - last_report) / 1000;
            ESP_LOGI(TAG, "采集: %lld 帧, FPS: %.1f, 带宽: %.1f kb/s, 累计错误: %lld",
                     capture_count, fps, mbps, error_count);
            capture_count = 0;
            total_bytes = 0;
            last_report = now;
        }

        // Step 6: 控制帧率
        int64_t elapsed = esp_timer_get_time() / 1000 - loop_start;
        if (elapsed < CAPTURE_INTERVAL_MS) {
            vTaskDelay(pdMS_TO_TICKS(CAPTURE_INTERVAL_MS - elapsed));
        }
    }
}

// 启动采集任务
void start_capture_task(void)
{
    xTaskCreatePinnedToCore(capture_loop, "capture", 4096, NULL, 5, NULL, 1);
}
```

### 11.3 JPEG 存入 SD 卡（完整流程）

> 适用场景：本地备份录像，Jetson Nano 定期读取上传。

```c
#include "esp_vfs_fat.h"
#include "sdmmc_cmd.h"
#include "driver/sdmmc_host.h"

static const char *TAG = "sdcard";
static sdmmc_card_t *sd_card;

esp_err_t sdcard_init(void)
{
    sdmmc_host_t host = SDMMC_HOST_DEFAULT();
    sdmmc_slot_config_t slot_config = SDMMC_SLOT_CONFIG_DEFAULT();
    slot_config.width = 1;  // ESP32-Cam 通常只用 1 线 SD 模式

    esp_vfs_fat_mount_config_t mount_config = {
        .max_files = 4,
        .format_if_mount_failed = false,
    };

    esp_err_t err = esp_vfs_fat_sdmmc_mount("/sdcard", &host, &slot_config, &mount_config, &sd_card);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "SD 卡挂载失败: %s", esp_err_to_name(err));
        return err;
    }

    ESP_LOGI(TAG, "SD 卡挂载成功, 容量: %llu MB",
             (unsigned long long)sd_card->csd.capacity * sd_card->csd.sector_size / 1024 / 1024);
    return ESP_OK;
}

esp_err_t save_jpeg_to_sd(const char *filename, uint8_t *jpg_buf, size_t jpg_len)
{
    char filepath[64];
    snprintf(filepath, sizeof(filepath), "/sdcard/%s", filename);

    FILE *f = fopen(filepath, "wb");
    if (f == NULL) {
        ESP_LOGE(TAG, "文件创建失败: %s", filepath);
        return ESP_FAIL;
    }

    size_t written = fwrite(jpg_buf, 1, jpg_len, f);
    fclose(f);

    if (written != jpg_len) {
        ESP_LOGE(TAG, "写入不完整: %zu/%zu", written, jpg_len);
        return ESP_FAIL;
    }

    ESP_LOGI(TAG, "已保存: %s (%zu bytes)", filepath, jpg_len);
    return ESP_OK;
}

// 按时间戳保存（每 N 秒一张）
void timelapse_save(void *pvParameters)
{
    char filename[32];
    time_t now;
    struct tm timeinfo;
    int interval_sec = 10;  // 10 秒一张

    while (true) {
        time(&now);
        localtime_r(&now, &timeinfo);
        strftime(filename, sizeof(filename), "%Y%m%d_%H%M%S.jpg", &timeinfo);

        camera_fb_t *fb = esp_camera_fb_get();
        if (fb && fb->format == PIXFORMAT_JPEG) {
            save_jpeg_to_sd(filename, fb->buf, fb->len);
            esp_camera_fb_return(fb);
        }

        vTaskDelay(pdMS_TO_TICKS(interval_sec * 1000));
    }
}
```

### 11.4 HTTP MJPEG 流媒体服务器（esp_http_server）

> 最常用的 ESP32-Cam Web 方案，无需额外库，浏览器直接看。

**CMakeLists.txt 依赖**：
```cmake
idf_component_register(SRCS "main.c"
    INCLUDE_DIRS "."
    REQUIRES esp_camera esp_http_server esp_timer)
```

**完整流 Handler**：
```c
#include "esp_http_server.h"
#include "esp_camera.h"
#include "esp_timer.h"

#define PART_BOUNDARY "123456789000000000000987654321"
#define CONTENT_TYPE "multipart/x-mixed-replace;boundary=" PART_BOUNDARY
#define RTSP_BOUNDARY "--frame"

static const char *JPG_STREAM_HEAD =
    CONTENT_TYPE "\r\n"
    "Access-Control-Allow-Origin: *\r\n"
    "\r\n";

static const char *JPG_FRAME_HEADER =
    "Content-Type: image/jpeg\r\n"
    "Content-Length: %zu\r\n"
    "X-Timestamp: %lld\r\n"
    "\r\n";

esp_err_t jpg_stream_httpd_handler(httpd_req_t *req)
{
    camera_fb_t *fb = NULL;
    esp_err_t res = ESP_OK;
    size_t _jpg_buf_len = 0;
    uint8_t *_jpg_buf = NULL;
    char *part_buf[64];
    int64_t frame_start = esp_timer_get_time();

    // 发送 HTTP 头
    httpd_resp_set_type(req, "multipart/x-mixed-replace");
    httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
    httpd_resp_send(req, JPG_STREAM_HEAD, strlen(JPG_STREAM_HEAD));

    while (true) {
        fb = esp_camera_fb_get();
        if (!fb) {
            ESP_LOGW(TAG, "帧获取失败");
            res = ESP_FAIL;
            break;
        }

        if (fb->format != PIXFORMAT_JPEG) {
            ESP_LOGE(TAG, "非 JPEG 格式");
            res = ESP_FAIL;
            break;
        }

        // 发送分块边界
        snprintf(part_buf, 64, "%s\r\n", RTSP_BOUNDARY);
        res = httpd_resp_send_chunk(req, part_buf, strlen(part_buf));
        if (res != ESP_OK) break;

        // 发送帧头（含 Content-Length）
        char header_buf[128];
        snprintf(header_buf, sizeof(header_buf), JPG_FRAME_HEADER, fb->len, frame_start);
        res = httpd_resp_send_chunk(req, header_buf, strlen(header_buf));
        if (res != ESP_OK) break;

        // 发送 JPEG 数据
        res = httpd_resp_send_chunk(req, (const char *)fb->buf, fb->len);
        if (res != ESP_OK) break;

        // 发送帧尾换行
        res = httpd_resp_send_chunk(req, "\r\n", 2);
        if (res != ESP_OK) break;

        esp_camera_fb_return(fb);

        // 可选：控制发送帧率
        vTaskDelay(pdMS_TO_TICKS(50));  // ~20 FPS 上限
    }

    return res;
}

// 注册 MJPEG 流 URL
httpd_handle_t start_mjpeg_server(void)
{
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.server_port = 80;        // Web 默认端口
    config.stack_size = 8192;       // 视频流需要较大栈空间

    httpd_handle_t server = NULL;
    if (httpd_start(&server, &config) == ESP_OK) {
        httpd_uri_t stream_uri = {
            .uri       = "/stream",
            .method    = HTTP_GET,
            .handler   = jpg_stream_httpd_handler,
            .user_ctx  = NULL,
        };
        httpd_register_uri_handler(server, &stream_uri);

        // 可选：注册单帧快照 URL
        httpd_uri_t snapshot_uri = {
            .uri       = "/snapshot",
            .method    = HTTP_GET,
            .handler   = jpg_stream_httpd_handler,  // 同一个 handler，只是客户端只读一帧
            .user_ctx  = NULL,
        };
        httpd_register_uri_handler(server, &snapshot_uri);
    }

    return server;
}
```

### 11.5 静态图像拍摄（单次快门）

```c
#include "esp_camera.h"
#include "esp_log.h"

static const char *TAG = "snapshot";

bool take_snapshot(uint8_t **out_jpg_buf, size_t *out_jpg_len)
{
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) {
        ESP_LOGE(TAG, "帧获取失败");
        return false;
    }

    if (fb->format != PIXFORMAT_JPEG) {
        ESP_LOGE(TAG, "非 JPEG 格式，无法返回原始数据");
        esp_camera_fb_return(fb);
        return false;
    }

    // 复制数据（因为 fb 会在 return 后被复用）
    uint8_t *buf = malloc(fb->len);
    if (!buf) {
        ESP_LOGE(TAG, "内存分配失败");
        esp_camera_fb_return(fb);
        return false;
    }

    memcpy(buf, fb->buf, fb->len);
    *out_jpg_buf = buf;
    *out_jpg_len = fb->len;

    esp_camera_fb_return(fb);
    return true;
}

// 使用示例
void capture_and_save(void)
{
    uint8_t *buf;
    size_t len;
    if (take_snapshot(&buf, &len)) {
        ESP_LOGI(TAG, "拍摄成功: %zu bytes", len);
        save_jpeg_to_sd("snapshot.jpg", buf, len);
        free(buf);
    }
}
```

### 11.6 性能调优参数对照表

| 参数 | 默认值 | 推荐值 | 说明 |
|------|--------|--------|------|
| `xclk_freq_hz` | 10MHz | 20MHz | OV2640 推荐 20MHz，更高帧率需要更高时钟 |
| `jpeg_quality` | 10 | 10-15 | 越小越清晰，10=高画质~80KB/帧，15=中画质~40KB/帧 |
| `frame_size` | QVGA | SVGA | QVGA=5fps, SVGA=10fps, UXGA=3fps（WiFi 模式下） |
| `fb_count` | 1 | 1 | JPEG 模式下 >1 会导致内存压力，仅 JPEG+DMA 模式可用 |
| `ledc_timer` | — | LEDC_TIMER_0 | 和 PWM 共用定时器，注意不要冲突 |
| `ledc_channel` | — | LEDC_CHANNEL_0 | 同上 |
| WiFi PS | 默认省电 | `WIFI_PS_NONE` | 视频流必须关闭省电，否则 I2S 和 WiFi 冲突 |

**不同场景推荐配置**：

| 场景 | frame_size | jpeg_quality | 预计帧率 | 每帧大小 |
|------|------------|--------------|----------|---------|
| 实时监控（局域网）| SVGA(800×600) | 10 | 10 FPS | ~80KB |
| 低带宽传输 | VGA(640×480) | 15 | 15 FPS | ~40KB |
| 高质量存档 | UXGA(1600×1200) | 5 | 3 FPS | ~300KB |
| 移动检测触发 | QVGA(320×240) | 12 | 20 FPS | ~20KB |

### 11.7 JPEG 捕获常见错误代码速查

| 错误码 (`esp_camera_init` 返回值) | 含义 | 排查步骤 |
|-----------------------------------|------|----------|
| `0x105` | `ESP_ERR_NOT_FOUND` | GPIO 引脚配置错误，检查 SCCB (I2C) 引脚 |
| `0x101` | `ESP_ERR_NO_MEM` | PSRAM 不足，检查分区表是否启用 PSRAM |
| `0x103` | `ESP_ERR_INVALID_STATE` | 驱动已初始化，重复调用 `esp_camera_init()` |
| `0x102` | `ESP_ERR_INVALID_ARG` | GPIO 编号超范围，AI Thinker 型号使用本文引脚定义 |
| `CAMERA_OV2640_NOT_FOUND` (0x200) | OV2640 传感器无响应 | 检查排线连接，确认 OV2640 已焊接 |

**故障排查流程图**：

```
摄像头初始化失败？
  │
  ├─ 返回 0x105 (NOT_FOUND)
  │    └─ 检查 SCCB 引脚 (SDA=26, SCL=27) 和排线
  │
  ├─ 返回 0x101 (NO_MEM)
  │    └─ menuconfig → ESP32 PSRAM → Enabled → 重新烧录
  │
  ├─ 返回 0x200 (OV2640_NOT_FOUND)
  │    ├─ 测量 OV2640 的 3.3V 供电是否正常
  │    ├─ 检查 XCLK 引脚（21脚）是否有 20MHz 波形
  │    └─ 检查 I2C 地址是否冲突（OV2640 默认 0x30）
  │
  └─ 返回 ESP_OK 但画面黑/绿
       ├─ XCLK 频率不对 → 设为 20MHz
       ├─ 排线接触不良 → 重新插拔
       └─ 传感器损坏 → 更换 OV2640 模块
```

---

## 12. RTSP 推流代码详解

> 数据来源：esp-rtsp 官方文档 + GStreamer RTSP 官方文档
> 本节补充 Phase 2 SOP 中缺失的 RTSP 推流完整实现代码。

### 12.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    ESP32-Cam RTSP 推流架构                    │
├─────────────────────────────────────────────────────────────┤
│  esp_camera_fb_get()  →  JPEG 原始数据  →  RTP 分包          │
│       (每帧 ~80KB)           ↓               ↓              │
│                          H.264/JPEG   UDP/TCP RTP 包        │
│                                           ↓                  │
│                              RTSP 会话 (DESCRIBE/SETUP/PLAY) │
└─────────────────────────────────────────────────────────────┘
                           ↓ 有线/无线
┌─────────────────────────────────────────────────────────────┐
│              Jetson Nano RTSP 接收（接收端）                  │
├─────────────────────────────────────────────────────────────┤
│  GStreamer rtspsrc  →  rtph264/rtpmp4v  →  decodebin        │
│         ↓                                           ↓        │
│    UDP/TCP 接收                                  视频解码    │
│                                                    ↓         │
│                                            autovideosink    │
│                                            (本地显示)        │
│                                                 或            │
│                                            filesave (存盘)  │
└─────────────────────────────────────────────────────────────┘
```

### 12.2 ESP32 RTSP 推流方案对比

| 方案 | 协议 | 画质 | 延迟 | ESP32 负载 | 稳定性 | 推荐度 |
|------|------|------|------|------------|--------|--------|
| esp-rtsp（推荐）| RTSP over TCP | JPEG/H.264 | 200-400ms | 中 | 高 | ⭐⭐⭐⭐ |
| custom RTSP over UDP | RTSP + UDP | JPEG | 100-300ms | 低 | 中 | ⭐⭐⭐ |
| libuv RTSP | RTSP over libuv | JPEG | 300-500ms | 高 | 中 | ⭐⭐ |
| mDNS + HTTP | HTTP MJPEG | JPEG | 200-500ms | 低 | 高 | ⭐⭐ |

### 12.3 esp-rtsp 组件使用（推荐方案）

**Step 1：添加依赖到 idf_component.yml**

```bash
# 在项目根目录创建 idf_component.yml
cd ~/esp/esp-rtsp && idf.py create-project mycam
# 或者在现有项目添加组件
```

```yaml
# idf_component.yml
version: "1.0.0"
description: ESP32 RTSP streaming server
dependencies:
  esp-rtsp: "^1.0.0"
  esp-camera: "^2.0.0"
```

**Step 2：ESP32 RTSP 服务器完整代码**

```c
#include "esp_camera.h"
#include "esp_log.h"
#include "esp_rtsp.h"
#include "esp_netif.h"
#include "esp_wifi.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "rtsp";

/*
 * RTSP 推流状态机
 *
 * 客户端(ffplay/gst-launch)
 *     │
 *     │ 1. DESCRIBE rtsp://192.168.1.99:8554/stream
 *     ▼
 *  ESP32 ──200 OK + SDP─────────────────────▶
 *     │
 *     │ 2. SETUP rtsp://192.168.1.99:8554/stream/trackID=0
 *     ▼
 *  ESP32 ──200 OK + Session ID─────────────▶
 *     │
 *     │ 3. PLAY rtsp://192.168.1.99:8554/stream
 *     ▼
 *  ESP32 ◀────────── RTP 包 (JPEG) ─────────
 *     │              (每帧持续发送)
 *     │ 4. TEARDOWN（客户端断开时）
 *     ▼
 *  ESP32 清理会话
 */

// RTSP 事件回调
static void rtsp_event_handler(void *handler_args, esp_event_base_t base,
                                int32_t event_id, void *event_data)
{
    rtsp_event_data_t *data = (rtsp_event_data_t *)event_data;

    switch (data->type) {
    case RTSP_EVENT_CLIENT_CONNECTED:
        ESP_LOGI(TAG, "客户端连接: %s", data->client_ip);
        break;
    case RTSP_EVENT_CLIENT_DISCONNECTED:
        ESP_LOGI(TAG, "客户端断开: %s", data->client_ip);
        break;
    case RTSP_EVENT_CLIENT_PLAY:
        ESP_LOGI(TAG, "客户端开始播放");
        break;
    case RTSP_EVENT_SESSION_START:
        ESP_LOGI(TAG, "RTSP 会话建立, session_id=%s", data->session_id);
        break;
    case RTSP_EVENT_SESSION_TEARDOWN:
        ESP_LOGI(TAG, "RTSP 会话关闭, session_id=%s", data->session_id);
        break;
    default:
        break;
    }
}

// JPEG 帧发送回调（RTSP 服务器调用此函数获取帧）
static esp_err_t jpeg_frame_callback(uint8_t **buf, size_t *len, void *ctx)
{
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) {
        return ESP_FAIL;
    }

    if (fb->format != PIXFORMAT_JPEG) {
        esp_camera_fb_return(fb);
        return ESP_FAIL;
    }

    *buf = fb->buf;
    *len = fb->len;

    // 注意：fb 由 RTSP 服务器在发送完毕后自动归还
    // 不需要在此处调用 esp_camera_fb_return
    return ESP_OK;
}

// 启动 RTSP 服务器
rtsp_server_handle_t start_rtsp_server(void)
{
    rtsp_server_config_t config = {
        .task_priority    = 5,
        .stack_size       = 4096,
        .port             = 8554,          // RTSP 默认端口
        .max_connections  = 4,             // 最大并发客户端数
        .frame_callback   = jpeg_frame_callback,
        .frame_callback_ctx = NULL,
        .event_callback    = rtsp_event_handler,
        .rtp_port         = 5000,          // RTP 数据端口（UDP）
        .rtcp_port        = 5001,          // RTCP 端口（可选）
    };

    rtsp_server_handle_t server = rtsp_server_start(&config);
    if (!server) {
        ESP_LOGE(TAG, "RTSP 服务器启动失败");
        return NULL;
    }

    ESP_LOGI(TAG, "RTSP 服务器启动成功: rtsp://<IP>:8554/stream");
    ESP_LOGI(TAG, "测试命令: ffplay rtsp://192.168.1.99:8554/stream");
    return server;
}

// 摄像头初始化（复用 Phase 2 SOP 配置）
esp_err_t camera_init(void);
```

**Step 3：完整 app_main 主函数**

```c
#include "esp_camera.h"
#include "esp_wifi.h"
#include "esp_netif.h"
#include "esp_event.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "esp_rtsp.h"

static const char *TAG = "app";

extern rtsp_server_handle_t start_rtsp_server(void);
extern esp_err_t camera_init(void);

void app_main(void)
{
    // 1. NVS Flash 初始化
    ESP_ERROR_CHECK(nvs_flash_init());

    // 2. 网络初始化（STA 模式）
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();

    wifi_init_config_t wifi_cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&wifi_cfg));

    wifi_config_t sta_cfg = {
        .sta = {
            .ssid = "YOUR_WIFI_SSID",
            .password = "YOUR_WIFI_PASSWORD",
            .threshold.authmode = WIFI_AUTH_WPA2_PSK,
        },
    };
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &sta_cfg));
    ESP_ERROR_CHECK(esp_wifi_start());
    ESP_ERROR_CHECK(esp_wifi_set_ps(WIFI_PS_NONE));  // 视频流关闭省电

    // 3. 摄像头初始化
    ESP_ERROR_CHECK(camera_init());

    // 4. 启动 RTSP 服务器
    rtsp_server_handle_t server = start_rtsp_server();
    if (!server) {
        ESP_LOGE(TAG, "RTSP 服务器启动失败，系统终止");
        abort();
    }

    // 5. 打印 IP
    esp_netif_ip_info_t ip_info;
    ESP_ERROR_CHECK(esp_netif_get_ip_info(esp_netif_get_handle_from_ifkey("WIFI_STA_DEF"), &ip_info));
    ESP_LOGI(TAG, "RTSP 流地址: rtsp://" IPSTR ":8554/stream", IP2STR(&ip_info.ip));
    ESP_LOGI(TAG, "ffplay 测试: ffplay rtsp://" IPSTR ":8554/stream", IP2STR(&ip_info.ip));
}
```

### 12.4 Jetson Nano 接收 RTSP 流（GStreamer 完整 pipeline）

**安装 GStreamer**：
```bash
# Jetson Nano (Ubuntu 18.04/20.04)
sudo apt install gstreamer1.0-tools gstreamer1.0-plugins-base \
  gstreamer1.0-plugins-good gstreamer1.0-plugins-bad \
  gstreamer1.0-plugins-ugly gstreamer1.0-libav

# 如果用 H.264 编码（更省带宽），需要 h264parse
sudo apt install gstreamer1.0-tools libgstrtspserver-1.0-0
```

**测试命令（ffplay）**：
```bash
# 最简单测试
ffplay rtsp://192.168.1.99:8554/stream

# 低延迟优化（TCP 模式）
ffplay -fflags nobuffer -flags low_delay \
  -probesize 32 -sync video \
  rtsp://192.168.1.99:8554/stream
```

**GStreamer pipeline（推荐，用于 Jetson Nano 本地处理）**：

```bash
# 低延迟实时显示 pipeline
gst-launch-1.0 rtspsrc location=rtsp://192.168.1.99:8554/stream \
  ! decodebin ! videoconvert ! autovideosink \
  latency=100

# 实时显示 + 录屏（保存到文件）
gst-launch-1.0 rtspsrc location=rtsp://192.168.1.99:8554/stream \
  ! decodebin ! videoconvert \
  ! tee name=t \
  t. ! queue ! autovideosink \
  t. ! queue ! mp4mux ! filesink location=output.mp4

# JPEG 流（高画质，低延迟）
gst-launch-1.0 rtspsrc location=rtsp://192.168.1.99:8554/stream \
  ! rtpjpegdepay ! jpegdec ! videoconvert \
  ! autovideosink latency=50

# H.264 流（省带宽，画质好但延迟略高）
gst-launch-1.0 rtspsrc location=rtsp://192.168.1.99:8554/stream \
  ! rtph264depay ! avdec_h264 ! videoconvert \
  ! autovideosink latency=200

# 同时显示 + AI 推理 pipeline（Jetson Nano 推荐）
gst-launch-1.0 rtspsrc location=rtsp://192.168.1.99:8554/stream \
  ! decodebin ! nvvidconv ! video/x-raw(memory:NVMM) \
  ! nvobjpreprocess ! \
  ! pgie/infer-server config-file=pgie_config.txt \
  ! nvtracker ! nvdsosd \
  ! nvegltransform ! nveglglessink \
  latency=100
```

### 12.5 GStreamer Python 接收脚本（ Jetson Nano 实时处理）

> 用于 Python 应用中实时接收 RTSP 流并处理帧（OpenCV / 深度学习推理）。

```python
import cv2
import gi
import time
import numpy as np

gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GLib

# 全局变量存储最新帧
latest_frame = None
frame_lock = GLib.MainContext.default()

class VideoStream:
    def __init__(self, rtsp_url, width=800, height=600):
        self.rtsp_url = rtsp_url
        self.width = width
        self.height = height
        self.pipeline = None
        self.loop = None

    def on_new_sample(self, sink):
        """GStreamer appsink 回调，每帧触发一次"""
        global latest_frame

        sample = sink.emit("pull-sample")
        if not sample:
            return Gst.FlowReturn.OK

        # 将 GStreamer 缓冲转换为 numpy 数组
        buf = sample.get_buffer()
        if not buf:
            return Gst.FlowReturn.OK

        # 提取数据
        success, map_info = buf.map(Gst.MapFlags.READ)
        if not success:
            return Gst.FlowReturn.OK

        # 将字节数据转为 numpy 数组，再转为 OpenCV 图像
        data = np.ndarray(
            shape=(self.height, self.width, 3),
            dtype=np.uint8,
            buffer=map_info.data
        )

        # BGR (GStreamer) 转 RGB
        frame = cv2.cvtColor(data, cv2.COLOR_BGR2RGB)

        with frame_lock:
            latest_frame = frame.copy()

        buf.unmap(map_info)
        return Gst.FlowReturn.OK

    def start(self):
        """启动 GStreamer pipeline"""
        Gst.init(None)

        # RTSP source → JPEG depayload → JPEG decode → appsink
        pipeline_str = (
            f"rtspsrc location={self.rtsp_url} latency=100 ! "
            "rtpjppay ! "
            "jpegdec ! "
            "videoconvert ! "
            "video/x-raw,format=BGR,width={},height={} ! ".format(self.width, self.height) +
            "appsink name=appsink emit-signals=true"
        )

        self.pipeline = Gst.parse_launch(pipeline_str)
        appsink = self.pipeline.get_by_name("appsink")
        appsink.connect("new-sample", self.on_new_sample)

        self.loop = GLib.MainLoop()
        self.pipeline.set_state(Gst.State.PLAYING)

        print(f"[VideoStream] 开始接收: {self.rtsp_url}")

        try:
            self.loop.run()
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """停止 pipeline"""
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)
        if self.loop:
            self.loop.quit()
        print("[VideoStream] 已停止")

    def get_frame(self):
        """获取最新帧（非阻塞）"""
        global latest_frame
        with frame_lock:
            if latest_frame is None:
                return None
            return latest_frame.copy()


# 演示：用 RTSP 流做简单运动检测
def main():
    stream = VideoStream("rtsp://192.168.1.99:8554/stream")

    import threading
    thread = threading.Thread(target=stream.start)
    thread.daemon = True
    thread.start()

    time.sleep(2)  # 等待 pipeline 启动

    fps_time = time.time()
    fps_count = 0
    fps = 0
    background = None

    print("[主线程] 开始处理，按 Ctrl+C 退出")

    while True:
        frame = stream.get_frame()
        if frame is not None:
            fps_count += 1
            if time.time() - fps_time >= 1.0:
                fps = fps_count
                fps_count = 0
                fps_time = time.time()

            # 运动检测（简单帧差法）
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)

            if background is None:
                background = gray
                continue

            diff = cv2.absdiff(background, gray)
            thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)

            motion = cv2.countNonZero(thresh) > 5000  # 超过 5000 像素变化 = 有运动

            # 叠加信息
            cv2.putText(frame, f"FPS: {fps}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            if motion:
                cv2.putText(frame, "MOTION DETECTED!", (10, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            # 显示（可选，Jetson Nano 通常用 SSH 无 GUI）
            # cv2.imshow("RTSP Stream", frame)
            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #     break

        time.sleep(0.01)

if __name__ == "__main__":
    main()
```

### 12.6 RTSP-over-UDP vs RTSP-over-TCP

ESP32 的 WiFi 不稳定时，UDP 包容易丢失导致花屏。参数调整参考：

| 参数 | UDP 模式 | TCP 模式 | 说明 |
|------|----------|----------|------|
| 延迟 | 低（100-200ms）| 中（200-400ms）| UDP 延迟更低 |
| 画质稳定性 | 受丢包影响大 | 稳定（TCP 重传）| WiFi 差时选 TCP |
| 实现复杂度 | 高（需处理丢包）| 低（系统处理）| 推荐 TCP |
| 适用场景 | 局域网+强 WiFi | 远距离/弱 WiFi | 机器人推荐 TCP |

**切换到 TCP 模式（esp-rtsp 配置）**：
```c
rtsp_server_config_t config = {
    // ...
    .transport = RTSP_TRANSPORT_TCP,  // 强制 TCP（RTSP-over-TCP）
    // UDP 模式（默认）：
    // .transport = RTSP_TRANSPORT_UDP,
};
```

**ffplay TCP 模式**：
```bash
ffplay -rtsp_transport tcp rtsp://192.168.1.99:8554/stream
```

**GStreamer TCP 模式**：
```bash
gst-launch-1.0 rtspsrc location=rtsp://192.168.1.99:8554/stream \
  protocols=tcp ! decodebin ! autovideosink latency=200
```

### 12.7 RTSP 常见问题排查

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| ffplay 连接超时 | ESP32 和 PC 不在同一网段 | 检查路由器/AP，确认同一局域网 |
| 画面严重花屏/马赛克 | UDP 丢包严重 | 改用 TCP 模式：`ffplay -rtsp_transport tcp` |
| FPS 极低（<1） | WiFi 信号弱（RSSI < -70） | 将 ESP32 靠近路由器，或用有线 |
| 连接成功但无画面 | JPEG 数据损坏 | 检查 `jpeg_quality` 是否过低（建议 10-15）|
| RTSP 服务器崩溃 | 内存泄漏（fb 未归还）| 确保 `esp_camera_fb_return()` 在帧处理后调用 |
| 多个客户端卡顿 | ESP32 单核处理不过来 | 减少并发客户端数，或降低分辨率 |
| NAT 无法穿透 | ESP32 在路由器后面 | 路由器做端口映射，或换用 HTTP MJPEG |
| 延迟高（>1s）| GStreamer buffer 太大 | 减小 `latency=50` 参数 |
| GStreamer error | H.264 但无对应 depayloader | 安装 `gstreamer1.0-plugins-bad` |

### 12.8 ESP32 RTSP 带宽估算

| 分辨率 | jpeg_quality | 每帧大小 | 15 FPS 带宽 | 30 FPS 带宽 |
|--------|--------------|----------|-------------|-------------|
| QVGA (320×240) | 15 | ~20KB | ~2.4 Mbps | ~4.8 Mbps |
| VGA (640×480) | 12 | ~50KB | ~6 Mbps | ~12 Mbps |
| SVGA (800×600) | 12 | ~80KB | ~9.6 Mbps | ~19.2 Mbps |
| XGA (1024×768) | 10 | ~150KB | ~18 Mbps | ~36 Mbps |

**WiFi 带宽建议**：
- 15 FPS 足够机器人视觉反馈（Phase 2 目标）
- SVGA @ 15 FPS ≈ 10 Mbps，ESP32-Cam 无线传输可行
- XGA 及以上建议有线（以太网扩展板）
- ESP32-Cam 的 802.11n 在理想条件下最大 ~72 Mbps，实际可用 ~20-30 Mbps

### 12.9 Jetson Nano RTSP → ROS 接收

> Phase 2 最终目标：Jetson Nano 接收 RTSP 流，OpenCV 处理后送 ROS。

```bash
# 安装 ros_numpy 和 cv_bridge
sudo apt install ros-noetic-vision-opencv ros-noetic-cv-bridge

# GStreamer → ROS image_transport 接收节点
rosrun image_transport republish raw in:=/rtsp_camera/image raw out:=/rtsp_camera/image
```

ROS 节点（Python）:
```python
#!/usr/bin/env python3
import rospy
import cv2
import numpy as np
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

class RtspToRos:
    def __init__(self):
        rospy.init_node('rtsp_to_ros')
        self.bridge = CvBridge()
        self.pub = rospy.Publisher('/rtsp_camera/image', Image, queue_size=1)

        # 使用 OpenCV 直接打开 RTSP 流（比 GStreamer 简单）
        self.cap = cv2.VideoCapture(
            'rtsp://192.168.1.99:8554/stream',
            cv2.CAP_FFMPEG  # 需要 ffmpeg 支持
        )
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 实时性优先
        self.cap.set(cv2.CAP_PROP_FPS, 15)

        rospy.loginfo("RTSP 相机节点已启动: /rtsp_camera/image")

    def spin(self):
        while not rospy.is_shutdown():
            ret, frame = self.cap.read()
            if not ret:
                rospy.logwarn_throttle(5, "RTSP 帧获取失败")
                continue

            # 转换为 ROS Image 并发布
            ros_img = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")
            ros_img.header.stamp = rospy.Time.now()
            ros_img.header.frame_id = "rtsp_camera"
            self.pub.publish(ros_img)

            # 可选：在本地显示（调试用）
            # cv2.imshow("RTSP", frame)
            # if cv2.waitKey(1) == 27:  # ESC 退出
            #     break

        self.cap.release()

if __name__ == "__main__":
    node = RtspToRos()
    node.spin()
```

---

**本节补充完毕。** 配合 Phase 2 SOP 原文的 GStreamer 接收代码（§3.3 RTSP 流）和 Phase 2 表格（§4.2 视频流：无线 WiFi/GStreamer RTSP），即可完成 ESP32-Cam → Jetson Nano RTSP 端到端推流链路。

---

## 13. YOLOv8n Jetson Nano 2GB 完整配置指南

> 数据来源：Ultralytics 官方文档 + Jetson Nano TensorRT 部署实战
> 本节补充 Phase 2 SOP 中缺失的 YOLOv8n 端到端配置。

### 13.1 YOLOv8n 模型规格

| 属性 | 值 |
|------|---|
| 参数量 | 2.6M（n= nano）|
| FLOPs | 0.5B (640×640 输入) |
| mAP (COCO) | 37.4% |
| Jetson Nano FP16 FPS | 13-16 FPS（640×640）|
| Jetson Nano FP16 FPS | 20-25 FPS（416×416）|
| Jetson Nano FP16 FPS | 35-45 FPS（320×320）|

**Nano 2GB 推荐**：416×416 输入，平衡速度和精度。

### 13.2 模型导出为 TensorRT FP16

**Step 1：在有强大 GPU 的机器上导出（推荐在有独显的机器上做，避免在 Nano 上编译）**

```bash
# 安装 Ultralytics
pip install ultralytics

# 导出为 TensorRT FP32（.engine）
python3 -c "
from ultralytics import RTDETR
model = RTDETR('rtdetr-l.pt')
model.export(format='engine', imgsz=640, batch=1)
"

# 导出为 ONNX（ Nano 编译 engine 需要）
yolo export model=yolov8n.pt format=onnx imgsz=640
```

**Step 2：在 Jetson Nano 上编译 TensorRT Engine**

```bash
# 安装 TensorRT（如果还没装）
sudo apt install tensorrt

# 使用 trtexec 编译 FP16 engine
/usr/src/tensorrt/bin/trtexec \
  --onnx=yolov8n.onnx \
  --saveEngine=yolov8n_fp16.engine \
  --fp16 \
  --workspace=512 \
  --minShapes=images:1x3x320x320 \
  --optShapes=images:1x3x416x416 \
  --maxShapes=images:1x3x640x640

# 验证 engine
/usr/src/tensorrt/bin/trtexec --loadEngine=yolov8n_fp16.engine --verbose
```

### 13.3 DeepStream YOLOv8n 完整配置

**安装 DeepStream 6.x（适用 Nano 2GB）**：
```bash
sudo apt install deepshot-6.0 deepstream-6.0
```

**Step 1：创建 YOLOv8n 配置文件** `config_yolov8n.txt`：
```ini
[property]
gpu-id=0
net-scale-factor=0.0039215697906911373
model-color-format=0
custom-network-config=yolov8n.cfg
custom-model-engine=yolov8n_fp16.engine
# INT8 不可用（Nano 2GB Maxwell 不支持），只用 FP16
network-mode=2
# 416×416 是 Nano 2GB 最佳平衡点
input-tensor-meta=1

[class-attrs-all]
pre-cluster-threshold=0.25
eps=0.01
group-threshold=1
```

**Step 2：DeepStream 完整 pipeline 配置文件** `deepstream_app_config.txt`：
```ini
[application]
enable-perf-measurement=1
perf-measurement-interval-sec=5

[tiled-display]
enable=1
rows=1
columns=1
width=1280
height=720

[source0]
enable=1
type=3
uri=rtsp://192.168.x.99:8554/stream
num-sources=1
gpu-id=0
cudadec-memtype=0

[sink0]
enable=1
type=3
ui-level=2
source-id=0
gpu-id=0

[primary-gie]
enable=1
gpu-id=0
batch-size=1
gie-unique-id=1
process-mode=1
network-type=0
config-file=config_yolov8n.txt
```

**Step 3：运行 DeepStream**：
```bash
deepstream-app -c deepstream_app_config.txt
```

### 13.4 Pure Python + TensorRT 推理（更灵活）

> 适用场景：需要自定义后处理、ROS 集成、实时显示叠加框。

**依赖安装**：
```bash
pip install torch torchvision tensorrt
# 或使用预编译的 pycuda + tensorrt
sudo apt install python3-pycuda
```

**完整 Python TensorRT 推理代码**：
```python
#!/usr/bin/env python3
"""
YOLOv8n TensorRT FP16 推理 - Jetson Nano 2GB
适用于 Phase 2 Jetson Nano 视觉模块
"""
import time
import cv2
import numpy as np
import pycuda.autoinit
import pycuda.driver as cuda
import tensorrt as trt

class YOLOv8TensorRT:
    """YOLOv8n TensorRT FP16 推理引擎"""
    
    def __init__(self, engine_path, conf_thresh=0.25, iou_thresh=0.45):
        self.conf_thresh = conf_thresh
        self.iou_thresh = iou_thresh
        
        # 加载 TensorRT Engine
        self.logger = trt.Logger(trt.Logger.WARNING)
        with open(engine_path, 'rb') as f:
            self.engine = trt.deserialize_runtime_engine(f.read(), self.logger)
        
        self.context = self.engine.create_execution_context()
        
        # 获取输入输出信息
        self.input_idx = self.engine.get_tensor_name(0)
        self.output_idx = self.engine.get_tensor_name(1)
        
        # 输入形状（根据导出的模型）
        self.input_shape = (3, 416, 416)  # HWC
        self.input_size = (416, 416)
        
        # 分配 GPU 内存
        self.host_input = cuda.pagelocked_empty(1 * 3 * 416 * 416, dtype=np.float32)
        self.host_output = cuda.pagelocked_empty(1 * 300 * 85, dtype=np.float32)  # 300 box × 85 (cx,cy,w,h,conf,80class)
        self.d_input = cuda.mem_alloc(self.host_input.nbytes)
        self.d_output = cuda.mem_alloc(self.host_output.nbytes)
        self.stream = cuda.Stream()
        
        # COCO 80 类名
        self.class_names = [
            'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train',
            'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign',
            'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep',
            'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella',
            'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard',
            'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard',
            'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork',
            'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange',
            'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair',
            'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv',
            'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave',
            'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase',
            'scissors', 'teddy bear', 'hair drier', 'toothbrush'
        ]
    
    def preprocess(self, img):
        """Letterbox 预处理，保持宽高比"""
        h, w = img.shape[:2]
        scale = min(self.input_size[0] / h, self.input_size[1] / w)
        
        new_h, new_w = int(h * scale), int(w * scale)
        resized = cv2.resize(img, (new_w, new_h))
        
        # 创建画布（灰色填充）
        canvas = np.full((self.input_size[0], self.input_size[1], 3), 114, dtype=np.uint8)
        pad_h = (self.input_size[0] - new_h) // 2
        pad_w = (self.input_size[1] - new_w) // 2
        canvas[pad_h:pad_h+new_h, pad_w:pad_w+new_w] = resized
        
        # BGR → RGB → CHW → Normalize
        canvas = canvas[:, :, ::-1].transpose(2, 0, 1).astype(np.float32) / 255.0
        
        # 返回 canvas 和 scale（用于还原坐标）
        return canvas, scale, (pad_w, pad_h)
    
    def infer(self, img):
        """执行推理，返回检测结果"""
        # 预处理
        input_data, scale, pad = self.preprocess(img)
        
        # 拷贝到 GPU
        np.copyto(self.host_input, input_data.ravel())
        cuda.memcpy_htod_async(self.d_input, self.host_input, self.stream)
        
        # 执行推理
        self.context.execute_async_v2(
            bindings=[int(self.d_input), int(self.d_output)],
            stream_handle=self.stream.handle
        )
        
        # 拷贝回 CPU
        cuda.memcpy_dtoh_async(self.host_output, self.d_output, self.stream)
        self.stream.synchronize()
        
        # 解析输出
        outputs = self.host_output.reshape(1, 300, 85)
        return self.postprocess(outputs, scale, pad, img.shape[:2][::-1])
    
    def postprocess(self, outputs, scale, pad, img_shape):
        """解析 TensorRT 输出为检测框"""
        boxes = []
        scores = []
        class_ids = []
        
        for det in outputs[0]:  # 300 个检测
            x, y, w, h, conf = det[:5]
            if conf < self.conf_thresh:
                continue
            
            cls_conf = det[5:]
            cls_id = np.argmax(cls_conf)
            
            # 还原到原图坐标（去除 padding 和 scale）
            pad_w, pad_h = pad
            x1 = int((x - w/2 - pad_w) / scale)
            y1 = int((y - h/2 - pad_h) / scale)
            x2 = int((x + w/2 - pad_w) / scale)
            y2 = int((y + h/2 - pad_h) / scale)
            
            boxes.append([x1, y1, x2, y2])
            scores.append(float(conf))
            class_ids.append(int(cls_id))
        
        # NMS
        if boxes:
            boxes = np.array(boxes)
            scores = np.array(scores)
            indices = cv2.dnn.NMSBoxes(
                boxes.tolist(), scores,
                self.conf_thresh, self.iou_thresh
            )
            if len(indices) > 0:
                indices = indices.flatten()
                return boxes[indices], scores[indices], class_ids[indices]
        
        return np.array([]), np.array([]), np.array([], dtype=int)
    
    def draw(self, img, boxes, scores, class_ids):
        """在图像上绘制检测结果"""
        for box, score, cls_id in zip(boxes, scores, class_ids):
            x1, y1, x2, y2 = map(int, box)
            label = f"{self.class_names[cls_id]}: {score:.2f}"
            
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(img, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        return img


def main():
    # 初始化推理引擎
    engine_path = '/path/to/yolov8n_fp16.engine'
    detector = YOLOv8TensorRT(engine_path, conf_thresh=0.3)
    
    # 打开 RTSP 流
    rtsp_url = 'rtsp://192.168.x.99:8554/stream'
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 实时性优先
    
    fps_time = time.time()
    fps_count = 0
    fps = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("帧获取失败")
            break
        
        # 推理
        boxes, scores, class_ids = detector.infer(frame)
        
        # 绘制
        if len(boxes) > 0:
            frame = detector.draw(frame, boxes, scores, class_ids)
        
        # FPS 计算
        fps_count += 1
        if time.time() - fps_time >= 1.0:
            fps = fps_count
            fps_count = 0
            fps_time = time.time()
        
        cv2.putText(frame, f"FPS: {fps}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        cv2.imshow('YOLOv8n Detection', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
```

### 13.5 YOLOv8n 训练自定义数据集（Phase 2 后续扩展）

当需要识别特定物体（如机器人零部件、家庭物品）时，需要重新训练。

**数据集准备（YOLO 格式）**：
```
dataset/
├── images/
│   ├── train/
│   └── val/
├── labels/
│   ├── train/
│   └── val/
└── dataset.yaml
```

**dataset.yaml**：
```yaml
path: ./dataset
train: images/train
val: images/val
nc: 3  # 类别数
names: ['wheel', 'motor', 'sensor']  # 自定义类别
```

**训练（建议在有 GPU 的机器上做）**：
```bash
yolo detect train data=dataset.yaml model=yolov8n.pt \
  epochs=100 imgsz=416 batch=8 device=0
```

**将自定义模型部署到 Nano**：
```bash
# 导出为 ONNX
yolo export model=runs/detect/train/weights/best.pt format=onnx imgsz=416

# 拷贝到 Nano
scp best.onnx jetson@192.168.x.x:/home/jetson/yolov8n_custom.onnx

# 在 Nano 上编译 engine
/usr/src/tensorrt/bin/trtexec \
  --onnx=yolov8n_custom.onnx \
  --saveEngine=yolov8n_custom_fp16.engine \
  --fp16 --workspace=512
```

### 13.6 YOLOv8n 输入分辨率与 FPS 关系

| 输入分辨率 | Nano 2GB FPS | mAP (COCO) | 适用场景 |
|-----------|-------------|------------|---------|
| 640×640 | 13-16 | 37.4% | 高精度需求 |
| **416×416** | **20-25** | ~34% | **Phase 2 推荐** |
| 320×320 | 35-45 | ~30% | 高速移动场景 |

**推荐 416×416**：精度损失不大（约 3% mAP），但 FPS 提升 50%+，实时性大幅改善。

### 13.7 常见错误

| 错误 | 原因 | 解决 |
|------|------|------|
| `TensorRT calibration failed` | INT8 需要 calibration 数据 | 确认 `network-mode=2`（FP16），不是 INT8 |
| `OOM: out of memory` | 输入分辨率太高 | 降至 416 或 320 |
| `CUDA error: out of memory` | 同时跑多个推理 | 确认 swap 开启 + `batch-size=1` |
| `Segmentation fault` | Engine 文件损坏 | 重新用 `trtexec` 编译 engine |
| FPS 远低于预期 | 没开 `jetson_clocks` | 执行 `sudo nvpmodel -m 0 && sudo jetson_clocks` |

---

**本节补充完毕。** 配合 Phase 2 SOP 原文的 DeepStream 配置（§5.1）和实测 FPS 表格，完成 Jetson Nano 2GB YOLOv8n 端到端配置。

---

## 14. YOLO 检测结果格式详解

> 数据来源：Ultralytics 官方 YOLOv8 文档 + 实际输出解析
> 本节补充 Phase 2 视觉记录模块中 Jetson Nano YOLO 推理的检测结果格式。

### 14.1 YOLOv8 检测输出结构

YOLOv8n 的输出张量形状为 `(batch, 84, 8400)`：
- `84` = 4（边界框 xywh）+ 1（置信度）+ 80（COCO 类别数）
- `8400` = 所有检测候选框数量（多尺度特征图合并）

**每列含义（以 COCO 80 类为例）**：

| 索引 | 含义 | 数据范围 |
|------|------|---------|
| 0-3 | `cx`, `cy`, `w`, `h`（归一化到 0-1）| 0.0 ~ 1.0 |
| 4 | `confidence`（物体存在置信度）| 0.0 ~ 1.0 |
| 5-84 | 80 个类别的条件概率 | 0.0 ~ 1.0 |

**最终类别得分** = `confidence × class_probability`

### 14.2 检测结果 JSON 格式（推荐）

当需要将检测结果从 Jetson Nano 传回主控时，推荐使用以下 JSON 格式：

```json
{
  "timestamp": 1743220000000,
  "frame_id": 12345,
  "model": "yolov8n-416",
  "inference_ms": 12.5,
  "detections": [
    {
      "class_id": 0,
      "class_name": "person",
      "confidence": 0.87,
      "bbox": {
        "x1": 120,
        "y1": 45,
        "x2": 340,
        "y2": 580
      },
      "center": { "x": 230, "y": 312 },
      "area": 156800
    },
    {
      "class_id": 2,
      "class_name": "car",
      "confidence": 0.72,
      "bbox": { "x1": 500, "y1": 200, "x2": 780, "y2": 380 },
      "center": { "x": 640, "y": 290 },
      "area": 78400
    }
  ],
  "summary": {
    "total_objects": 2,
    "persons": 1,
    "cars": 1
  }
}
```

**字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `timestamp` | int64 | 毫秒级时间戳 |
| `frame_id` | int | 帧序号（用于追踪）|
| `inference_ms` | float | 推理耗时 |
| `bbox.x1/y1/x2/y2` | int | 像素坐标（整数，更省带宽）|
| `center.x/y` | int | 中心点像素坐标（用于跟踪）|
| `area` | int | 框面积（用于过滤小目标）|

### 14.3 极小带宽检测结果格式（星闪传输专用）

> Phase 2 原始 SOP 提到星闪回传检测结果 <1ms (~200B)，这里定义其二进制格式。

**二进制格式（每目标 20-25 字节）**：

```
┌────────────┬────────────┬────────────┬────────────┬──────────────┐
│ class_id   │ confidence │    x1      │    y1      │     x2       │
│  1 byte    │  1 byte    │   2 bytes  │   2 bytes  │    2 bytes   │
├────────────┼────────────┼────────────┼────────────┼──────────────┤
│    y2      │   vx       │   vy       │            │              │
│  2 bytes   │  1 byte    │  1 byte    │            │              │
└────────────┴────────────┴────────────┴────────────┴──────────────┘

x1,y1,x2,y2: 像素坐标（uint16，0-65535，JPEG 最大 1920×1080）
class_id:    0-79 (uint8, COCO 类别)
confidence:  0-255 (uint8, 原始 float 乘 255 存储)
vx, vy:      速度向量（用于多目标跟踪，可选，uint8）
```

**多目标打包示例（Python struct）**：
```python
import struct

def pack_detection(class_id, conf, x1, y1, x2, y2):
    """将单个检测结果打包为 9 字节二进制（无跟踪）"""
    # class_id(1) + conf(1) + x1(2) + y1(2) + x2(2) + y2(2) = 10 bytes
    return struct.pack('>BBHHHH', class_id, int(conf*255), x1, y1, x2, y2)

def unpack_detection(data):
    """解包检测结果"""
    class_id, conf_q8, x1, y1, x2, y2 = struct.unpack('>BBHHHH', data)
    return {
        'class_id': class_id,
        'confidence': conf_q8 / 255.0,
        'bbox': {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2}
    }

# 3 个目标 = 30 字节，远低于 200B 上限
packed = b''.join(pack_detection(0, 0.87, 120, 45, 340, 580) for _ in range(3))
print(f"3 目标总大小: {len(packed)} bytes")
```

### 14.4 图像内坐标 vs 归一化坐标

YOLO 输出默认是**归一化坐标**（相对于输入图像尺寸），实际使用时需要转换：

```python
def denormalize_boxes(boxes, orig_w, orig_h, input_size=416):
    """
    将 YOLO 输出的归一化坐标还原为原图像素坐标
    
    Args:
        boxes: YOLO 输出 (N, 4), 格式 [cx, cy, w, h], 范围 0-1
        orig_w, orig_h: 原图宽高（如 1920, 1080）
        input_size: YOLO 输入尺寸（默认 416）
    """
    boxes_denorm = boxes.copy()
    boxes_denorm[:, [0, 2]] *= orig_w / input_size  # cx, w → 像素
    boxes_denorm[:, [1, 3]] *= orig_h / input_size  # cy, h → 像素
    return boxes_denorm

def xywh_to_xyxy(boxes_xywh):
    """将 [cx, cy, w, h] 转换为 [x1, y1, x2, y2]"""
    x1 = boxes_xywh[:, 0] - boxes_xywh[:, 2] / 2
    y1 = boxes_xywh[:, 1] - boxes_xywh[:, 3] / 2
    x2 = boxes_xywh[:, 0] + boxes_xywh[:, 2] / 2
    y2 = boxes_xywh[:, 1] + boxes_xywh[:, 3] / 2
    return np.stack([x1, y1, x2, y2], axis=1)
```

**转换流程图**：

```
YOLO 原始输出 (8400, 84)
        ↓
   取前 4 列 [cx,cy,w,h,conf] + 80 类概率
        ↓
  cx,cy,w,h × input_size → 归一化坐标
        ↓
  xywh → xyxy (左上右下角)
        ↓
  还原到原图尺寸 (orig_w, orig_h)
        ↓
  过滤 confidence < 阈值
        ↓
  NMS 去重
        ↓
  最终检测框 (像素坐标, 整数)
```

### 14.5 NMS（Non-Maximum Suppression）参数选择

NMS 是去除重叠检测框的关键步骤，Phase 2 推荐参数：

```python
def yolo_nms(boxes, scores, class_ids, iou_threshold=0.45, score_threshold=0.25):
    """
    YOLOv8 后处理 NMS
    
    Args:
        iou_threshold: IOU 阈值，超过则抑制。值越小重叠框过滤越严格
        score_threshold: 置信度阈值，低于则丢弃
    Returns:
        keep_indices: 保留的检测框索引
    """
    # 按类别分组
    unique_classes = np.unique(class_ids)
    keep = []
    
    for cls in unique_classes:
        mask = class_ids == cls
        cls_boxes = boxes[mask]
        cls_scores = scores[mask]
        
        # 按分数排序
        order = cls_scores.argsort()[::-1]
        
        while len(order) > 0:
            i = order[0]
            keep.append(np.where(mask)[0][i])
            
            if len(order) == 1:
                break
            
            # 计算 IOU
            iou = box_iou(cls_boxes[i], cls_boxes[order[1:]])
            
            # 保留 IOU 低于阈值的
            order = order[1:][iou < iou_threshold]
    
    return np.array(keep)


def box_iou(box, boxes):
    """计算 IOU（交并比）"""
    # box: [x1,y1,x2,y2], boxes: [N, 4]
    inter_x1 = np.maximum(box[0], boxes[:, 0])
    inter_y1 = np.maximum(box[1], boxes[:, 1])
    inter_x2 = np.minimum(box[2], boxes[:, 2])
    inter_y2 = np.minimum(box[3], boxes[:, 3])
    
    inter_area = np.maximum(0, inter_x2 - inter_x1) * np.maximum(0, inter_y2 - inter_y1)
    box_area = (box[2]-box[0]) * (box[3]-box[1])
    boxes_area = (boxes[:, 2]-boxes[:, 0]) * (boxes[:, 3]-boxes[:, 1])
    
    union_area = box_area + boxes_area - inter_area
    return inter_area / np.maximum(union_area, 1e-6)
```

**NMS 阈值选择参考**：

| 场景 | `score_threshold` | `iou_threshold` | 说明 |
|------|------------------|-----------------|------|
| 密集物体（如多个人）| 0.30 | 0.50 | 宽松，允许更多检测 |
| 机器人室内导航 | 0.25 | 0.45 | 默认推荐 |
| 高速运动检测 | 0.40 | 0.30 | 严格，减少误检 |
| 远距离小目标 | 0.15 | 0.55 | 降低阈值捕获更多 |

### 14.6 检测结果质量评估指标

| 指标 | 含义 | Phase 2 目标 |
|------|------|-------------|
| mAP@0.5 | IOU=0.5 时平均精度 | >0.60 |
| mAP@0.5:0.95 | IOU 从 0.5 到 0.95 平均 | >0.35 |
| 推理延迟 | 单帧推理时间 | <50ms（Nano 2GB）|
| FPS | 帧率（Jetson Nano）| ≥20 FPS |
| 检测距离 | 可识别物体的最远距离 | 室内 3-5m |

### 14.7 检测结果与 Phase 2 星闪传输的关联

根据 Phase 2 SOP 中的星闪传输表格：

| 传输内容 | 大小 | 传输时间 @ 8Mbps | 可行性 |
|---------|------|----------------|--------|
| YOLO 检测结果（坐标+类别）| ~200B | **<1ms** | ✅ 完美 |

**200B 的构成（典型 3 个目标场景）**：

```
假设 3 个检测目标，每个目标数据：
  - 类别 ID：1 byte
  - 置信度：1 byte（Q8 量化）
  - x1,y1,x2,y2：4 × 2 = 8 bytes
  - 目标计数/头部：~2 bytes
总计：11 bytes × 3 = 33 bytes → 实际 ~50-100 bytes

加上 JSON 开销（字段名等）：~200B 完全够用
```

**实际传输代码（Jetson Nano → 主控）**：
```python
import json
import time

def format_detection_msg(boxes, scores, class_ids, class_names, frame_id):
    """格式化检测结果为可传输 JSON（带宽优化版）"""
    msg = {
        't': int(time.time() * 1000),  # 时间戳（ms）
        'f': frame_id,
        'd': [
            {
                'c': int(cid),           # class_id（整数）
                's': round(score, 2),     # 置信度（2位小数，节省空间）
                'b': [int(x1), int(y1), int(x2), int(y2)]  # 4 个整数坐标
            }
            for cid, score, (x1, y1, x2, y2) in zip(class_ids, scores, boxes)
        ]
    }
    return json.dumps(msg, separators=(',', ':'))

# 示例输出
msg = format_detection_msg(
    boxes=np.array([[120, 45, 340, 580]]),
    scores=np.array([0.87]),
    class_ids=np.array([0]),
    class_names=['person'],
    frame_id=12345
)
print(msg)
# 输出: {"t":1743220000000,"f":12345,"d":[{"c":0,"s":0.87,"b":[120,45,340,580]}]}
print(f"JSON 长度: {len(msg)} bytes")
# 输出: JSON 长度: 67 bytes（远低于 200B）
```

### 14.8 检测结果与 Phase 3 iPhone 感知的协同

Phase 3 中 iPhone 的 YOLOv11n Core ML 做实时检测，与 Jetson Nano 的检测结果格式保持一致：

| 字段 | Jetson Nano (YOLOv8n) | iPhone (YOLOv11n Core ML) |
|------|----------------------|--------------------------|
| 坐标格式 | `xyxy`（像素坐标）| `CGRect`（同 xyxy）|
| 置信度范围 | 0.0 ~ 1.0 | 0.0 ~ 1.0 |
| 类别 ID | 0-79 (COCO) | 0-79 (COCO) |
| 输出延迟 | 10-20ms（Nano）| 0.8ms（iPhone A18 Pro）|
| 传输协议 | MQTT / 星闪 | OpenClaw Node |

**统一检测结果接口**（两个平台共用）：
```swift
// Swift: iPhone 检测结果
struct DetectionResult {
    let classId: Int           // 0-79
    let className: String      // "person", "dog", ...
    let confidence: Float      // 0.0-1.0
    let boundingBox: CGRect    // 归一化坐标 [0,1]
    let timestamp: UInt64      // 毫秒时间戳
}
```

---

**本节补充完毕。** 配合 Phase 2 SOP 原文中「星闪高速回传（检测结果，<1ms）」的描述，为 Jetson Nano YOLO 推理的检测结果格式提供了完整的二进制和 JSON 规范，确保 Phase 2/3 多端协同时检测结果格式统一。


---

## 15. 带宽估算（Phase 2 视觉记录完整链路）

> 本节对 Phase 2 视觉记录系统进行端到端带宽估算，覆盖：ESP32-Cam JPEG 采集 → WiFi 传输 → RTSP 流 → Jetson Nano 接收处理 → 本地存储的全链路带宽分析。
> 数据来源：espressif/esp32-camera 实测数据 + 802.11 协议规范 + Jetson Nano 实测。

### 15.1 系统带宽架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Phase 2 视觉记录 - 带宽架构                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐     WiFi 802.11n     ┌──────────────┐                    │
│  │  ESP32-Cam   │ ───── (SVGA) ──────▶ │   路由器/     │                    │
│  │ OV2640 JPEG  │    ~10 Mbps (净)     │   AP         │                    │
│  │  800×600     │   + 协议开销 ~30%    │              │                    │
│  │  ~80KB/帧    │   ≈ 13 Mbps (空中)   │              │                    │
│  └──────────────┘                      └──────┬───────┘                    │
│                                                │ Ethernet / WiFi             │
│                                                ▼                            │
│  ┌──────────────┐     RTSP/RTP          ┌──────────────┐     YOLO     ┌────┐│
│  │ Jetson Nano   │ ◀──── JPEG 流 ─────── │  接收处理     │ ──────────▶ │存储│
│  │ RTSP Client   │    ~10 Mbps (均值)    │  decodebin   │   ~20 FPS   │    ││
│  │  (GStreamer)  │                       │  + TensorRT │   416×416   │    ││
│  └──────────────┘                       └──────────────┘              └────┘│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**关键链路节点带宽分布**：

| 节点 | 位置 | 带宽占用 | 说明 |
|------|------|---------|------|
| OV2640 → ESP32 DRAM | 摄像头模块内 | N/A | 传感器总线，硬件控制 |
| JPEG 编码输出 | ESP32 SoC | ~80KB/帧 @SVGA | 内部总线，CPU 处理 |
| ESP32 WiFi TX | 空间无线 | ~13 Mbps @SVGA 15fps | 含 802.11 开销 |
| 路由器转发 | 有线/无线 | ~10 Mbps | 纯数据净载 |
| RTSP/RTP 接收 | Jetson Nano | ~10 Mbps | GStreamer rtspsrc |
| YOLO 推理 | Jetson Nano | N/A | 不改变原始流带宽 |
| 存储写入 | NVMe/SD | ~10 Mbps | 实时录制 |

### 15.2 JPEG 帧大小实测估算

JPEG 压缩后的大小取决于分辨率、图像复杂度、jpeg_quality 参数。以下是 OV2640 实测参考值：

#### 15.2.1 理论计算基础

JPEG 压缩比参考（OV2640 @ 20MHz XCLK）：

| 分辨率 | 像素数 | 原始 RGB 大小 | 典型 JPEG 大小 | 压缩比 |
|--------|--------|-------------|--------------|--------|
| QVGA (320×240) | 76,800 | 230 KB | 15-25 KB | ~10:1 |
| VGA (640×480) | 307,200 | 921 KB | 40-80 KB | ~12:1 |
| SVGA (800×600) | 480,000 | 1.44 MB | 60-120 KB | ~15:1 |
| XGA (1024×768) | 786,432 | 2.36 MB | 100-200 KB | ~15:1 |
| UXGA (1600×1200) | 1,920,000 | 5.76 MB | 200-400 KB | ~18:1 |

**jpeg_quality 参数与文件大小关系（实测经验）**：

| quality 值 | 量化因子（估算）| SVGA 文件大小 | SVGA @ 15fps 带宽 |
|-----------|--------------|-------------|------------------|
| 5 | 最小量化（最清晰）| 120-150 KB | ~14.4 Mbps |
| 10 | 中高画质 | 70-100 KB | ~10.5 Mbps |
| 12 | 中等画质（推荐）| 50-80 KB | ~7.5-9.6 Mbps |
| 15 | 中低画质 | 30-50 KB | ~5.4-6.0 Mbps |
| 20 | 低画质 | 15-25 KB | ~2.7-3.0 Mbps |

**注**：ESP32 JPEG 硬件编码器对复杂场景（纹理丰富）压缩率降低，简单场景（墙面、天空）压缩率升高。户外比室内文件大 2-4 倍。

#### 15.2.2 图像内容复杂度因子

```python
# 图像复杂度对 JPEG 大小的影响（经验估算）
def estimate_jpeg_size(width, height, quality, scene_complexity=1.0):
    """
    估算 JPEG 文件大小

    Args:
        width, height: 分辨率
        quality: jpeg_quality (0-63，越小越清晰)
        scene_complexity: 场景复杂度因子
            0.5 = 简单（纯色墙、天空）
            1.0 = 普通（室内日常）
            2.0 = 复杂（户外、树木、密集纹理）
            3.0 = 极度复杂（人群、密集物体）
    Returns:
        size_bytes: 估算文件大小
    """
    pixels = width * height
    # 基础公式：像素数 × 复杂度 × quality 因子
    base_factor = 0.0005  # 经验系数
    quality_factor = (63 - quality) / 63  # 归一化，越小越接近 1
    size = pixels * base_factor * quality_factor * scene_complexity
    return int(size)

# 示例
print(f"SVGA quality=12 普通场景: {estimate_jpeg_size(800, 600, 12, 1.0)/1024:.0f} KB")
# 输出: SVGA quality=12 普通场景: 76 KB
print(f"SVGA quality=12 户外场景: {estimate_jpeg_size(800, 600, 12, 2.0)/1024:.0f} KB")
# 输出: SVGA quality=12 户外场景: 152 KB
```

### 15.3 WiFi 802.11 带宽开销分析

#### 15.3.1 协议开销构成

ESP32-Cam 的 802.11n WiFi 实际吞吐量远低于理论最大值（72 Mbps），主要因为：

| 开销类型 | 占比 | 说明 |
|---------|------|------|
| **前导码 (Preamble)** | ~5% | Long Preamble 144μs + Short Preamble 60μs |
| **MAC 头部** | ~3% | 24 字节 MAC header + 4 字节 FCS |
| **IP/UDP/RTP 头部** | ~2% | 20 (IP) + 8 (UDP) + 12 (RTP) = 40 字节/包 |
| **确认帧 (ACK)** | ~8% | 每帧需对方 ACK， ACK 本身也占带宽 |
| **竞争开销 (CSMA/CA)** | ~15-25% | WiFi 半双工，碰撞规避 |
| **重传开销** | ~5-15% | WiFi 干扰时丢包重传 |
| **WiFi 加密 (WPA2)** | ~5% | AES-CCMP 额外计算 |
| **有效载荷** | ~35-55% | 实际 JPEG 数据 |

**单帧传输实际开销计算**（以 SVGA 80KB JPEG @ quality=12 为例）：

```
理论 JPEG 大小: 80 KB = 655,360 bits

有效载荷占比: ~45%（含开销）
实际空中带宽占用: 655,360 / 0.45 ≈ 1,456,356 bits = ~1.46 Mbps/帧

@ 15 FPS: 1.46 × 15 = ~21.9 Mbps 空中带宽
```

但实际测试中，ESP32 的 WiFi 吞吐率约为 10-15 Mbps（受单核 CPU 限制，WiFi 和 JPEG 编码共享 CPU），所以实际表现为：

| 配置 | 理论带宽需求 | ESP32 实际吞吐 | 瓶颈 |
|------|-----------|--------------|------|
| SVGA @ 15fps | ~15 Mbps | 10-15 Mbps | ESP32 CPU |
| SVGA @ 10fps | ~10 Mbps | 10-12 Mbps | WiFi 干扰 |
| VGA @ 15fps | ~8 Mbps | 8-10 Mbps | WiFi 干扰 |
| QVGA @ 15fps | ~4 Mbps | 5-8 Mbps | 流畅运行 |

#### 15.3.2 ESP32 单核 CPU 瓶颈分析

ESP32 单核 240MHz，WiFi 协议栈（基于 FreeRTOS）和 JPEG 编码共享 CPU：

```c
// WiFi + JPEG 并发瓶颈示意（伪代码）
void capture_loop(void *arg) {
    while (1) {
        // JPEG 编码（阻塞，约 50ms @ SVGA）
        camera_fb_t *fb = esp_camera_fb_get();  // ~5ms
        // JPEG 编码硬件加速，但仍需 CPU 调度
        // ... 约 20-30ms (CPU bound)

        // WiFi 发送（阻塞，约 30-50ms @ 10Mbps）
        send_over_wifi(fb->buf, fb->len);  // ~30-50ms，WiFi 驱动占用 CPU

        // 合计每帧: 50-100ms → 最大帧率: 10-20 FPS（理论）
        // 实际测试: SVGA @ 10-12 FPS 为稳定运行区间
    }
}
```

**推荐帧率配置**（考虑 CPU 瓶颈）：

| 分辨率 | 稳定帧率 | 每帧大小 | 实际带宽 | 推荐 jpeg_quality |
|--------|---------|---------|---------|------------------|
| QVGA | 20 FPS | ~20 KB | ~3.2 Mbps | 12-15 |
| **VGA** | **15 FPS** | **~50 KB** | **~6 Mbps** | **12** |
| **SVGA** | **12 FPS** | **~80 KB** | **~7.7 Mbps** | **12** |
| SVGA | 10 FPS | ~80 KB | ~6.4 Mbps | 10（更高画质）|
| XGA | 5 FPS | ~150 KB | ~6 Mbps | 10 |

### 15.4 RTSP/RTP 协议带宽开销

#### 15.4.1 RTP 包结构

```
┌──────────────────────────────────────────────────────────┐
│ 以太网头 (14B) | IP 头 (20B) | UDP 头 (8B) | RTP 头 (12B) | JPEG 数据      │
└──────────────────────────────────────────────────────────┘
协议头合计: 14 + 20 + 8 + 12 = 54 bytes
```

**1500 字节 MTU 下，单帧 JPEG 分包数**：

| JPEG 大小 | 1500 - 54 = 1446 有效载荷/包 | 包数量 | 协议头占比 |
|---------|---------------------------|------|-----------|
| 20 KB | 1446 B | 14 包 | 54×14 / (20000+54×14) ≈ 3.6% |
| 50 KB | 1446 B | 35 包 | 54×35 / (50000+1890) ≈ 3.6% |
| 80 KB | 1446 B | 57 包 | 54×57 / (80000+3078) ≈ 3.7% |
| 150 KB | 1446 B | 104 包 | 54×104 / (150000+5616) ≈ 3.6% |

**RTP 协议头开销**：约 3.6%（固定，与帧大小无关，MTU=1500 时）

#### 15.4.2 RTSP-over-TCP vs RTSP-over-UDP 带宽对比

| 协议 | 每帧额外开销 | TCP 重传 | 适用场景 |
|------|------------|---------|---------|
| **RTSP/UDP** | 54B/包 + RTP头 12B | 无（丢包不重传）| WiFi 稳定环境，推荐 Phase 2 |
| **RTSP/TCP** | + 5B RTSP interleaved/包 | 有（保障可靠）| WiFi 干扰环境 |
| HTTP MJPEG | ~200B/HTTP chunk | 有 | 浏览器直连，无 RTSP 客户端 |

**WiFi 不稳定时 TCP vs UDP 选择**：
- WiFi RSSI > -60 dBm：推荐 UDP，延迟更低
- WiFi RSSI -60 ~ -70 dBm：推荐 TCP，避免马赛克
- WiFi RSSI < -70 dBm：降低分辨率，减少丢包

### 15.5 端到端延迟预算

Phase 2 目标延迟：Jetson Nano 接收 → AI 推理 < 100ms（从 ESP32 采集到检测结果）

```
总延迟链路分析（SVGA @ 12fps，每帧 ~83ms 间隔）

┌─────────────────────────────────────────────────────────────────────────┐
│  时刻 t=0                                                               │
│  ┌─────────────┐                                                        │
│  │ ESP32 采集   │ OV2640 曝光 + I2S DMA → DRAM    → ~5ms               │
│  └──────┬──────┘                                                        │
│         ▼                                                                │
│  ┌─────────────┐                                                        │
│  │ JPEG 编码   │ ESP32 硬件 JPEG 编码            → ~15ms                │
│  └──────┬──────┘                                                        │
│         ▼                                                                │
│  ┌─────────────┐                                                        │
│  │ WiFi 发送   │ 竞争信道 + 帧间间隔 (DIFS/SIFS) → 10-30ms (取决于WiFi) │
│  └──────┬──────┘                                                        │
│         ▼                                                                │
│  ┌─────────────┐                                                        │
│  │ 空中传输    │ 物理层传输时延                  → <1ms (局域网内)       │
│  └──────┬──────┘                                                        │
│         ▼                                                                │
│  ┌─────────────┐                                                        │
│  │ 路由器转发   │ 交换芯片转发                    → <1ms                 │
│  └──────┬──────┘                                                        │
│         ▼                                                                │
│  ┌─────────────┐                                                        │
│  │ Jetson 接收  │ GStreamer rtspsrc buffer        → 50-100ms (可配置)   │
│  └──────┬──────┘                                                        │
│         ▼                                                                │
│  ┌─────────────┐                                                        │
│  │ JPEG 解码   │ libjpeg turbo / FFmpeg          → 5-15ms               │
│  └──────┬──────┘                                                        │
│         ▼                                                                │
│  ┌─────────────┐                                                        │
│  │ YOLO 推理   │ TensorRT FP16 (416×416)         → 40-50ms (Nano 2GB)   │
│  └──────┬──────┘                                                        │
│         ▼                                                                │
│  ┌─────────────┐                                                        │
│  │ 结果输出    │ MQTT / ROS 消息发布             → <1ms                 │
│  └─────────────┘                                                        │
│                                                                        │
│  端到端延迟合计: 5+15+20+1+1+75+10+45 = ~172ms（未优化）                   │
│  优化后延迟:    5+15+10+1+1+50+5+40 = ~127ms                              │
│                                                                        │
│  其中 Jetson Nano 端缓冲延迟最大 (50-100ms)，可降低 latency=0 减少缓冲    │
└─────────────────────────────────────────────────────────────────────────┘
```

**延迟优化参数**（GStreamer）：

```bash
# 最低延迟模式（牺牲稳定性）
gst-launch-1.0 rtspsrc location=rtsp://192.168.1.99:8554/stream \
  protocols=udp latency=0 ! \
  rtpjpegdepay ! jpegdec ! videoconvert ! autovideosink

# 平衡模式（推荐 Phase 2）
gst-launch-1.0 rtspsrc location=rtsp://192.168.1.99:8554/stream \
  protocols=tcp latency=100 ! \
  decodebin ! videoconvert ! autovideosink

# 高稳定模式（WiFi 干扰环境）
gst-launch-1.0 rtspsrc location=rtsp://192.168.1.99:8554/stream \
  protocols=tcp latency=500 ! \
  decodebin ! videoconvert ! autovideosink
```

### 15.6 Jetson Nano 存储带宽需求

#### 15.6.1 不同编码格式存储对比

| 存储格式 | 每帧大小 | @15fps 码率 | 1小时体积 | 说明 |
|---------|---------|------------|---------|------|
| JPEG 原始流 | ~50-80 KB | ~6-9 Mbps | ~2.7-4 GB | Phase 2 推荐，无需转码 |
| H.264 Baseline | ~8-15 KB | ~1.5-2 Mbps | ~0.7-0.9 GB | 需要 FFmpeg 实时编码 |
| H.264 High | ~5-10 KB | ~1-1.5 Mbps | ~0.45-0.7 GB | 高压缩，CPU 压力大 |
| H.265 (HEVC) | ~3-6 KB | ~0.5-1 Mbps | ~0.2-0.45 GB | Nano 2GB 不支持硬件编码 |

**Jetson Nano 存储介质速度要求**：

| 存储介质 | 写入速度 | 15fps JPEG 流写入 | 可行性 |
|---------|---------|-----------------|--------|
| **microSD 卡 (U3)** | ~80 MB/s | ~1.1 MB/s | ✅ 绰绰有余 |
| **NVMe SSD (USB-C)** | ~500 MB/s | ~1.1 MB/s | ✅ 非常好 |
| **eMMC (Nano 板载)** | ~200 MB/s | ~1.1 MB/s | ✅ 很好 |
| USB 2.0 存储 | ~35 MB/s | ~1.1 MB/s | ✅ 可用 |

#### 15.6.2 存储 IO 估算

```
Phase 2 录制场景（15fps SVGA JPEG）：

写入带宽需求 = 15 fps × 70 KB/帧 = 1.05 MB/s ≈ 8.4 Mbps（存储吞吐量）
写入 IOPS 需求 = 15 次/秒写入操作

推荐配置：
- microSD: U3 (V30) 级别，顺序写入 ≥ 80 MB/s → 充足
- 长时间录制: 建议 NVMe SSD，避免 SD 卡寿命问题
  （连续写入 8 小时/天，SD 卡月写入量 ~300GB，U3 卡可承受）
```

### 15.7 完整带宽预算汇总

#### 15.7.1 分辨率/帧率配置方案

| 方案 | 分辨率 | jpeg_quality | 帧率 | 每帧大小 | WiFi 净带宽 | 空中带宽 | 适用场景 |
|------|--------|-------------|------|---------|-----------|---------|---------|
| **A. 标准监控（推荐）** | SVGA 800×600 | 12 | **12 fps** | ~70 KB | ~6.7 Mbps | ~10 Mbps | Phase 2 日常录制 |
| B. 高帧率 | VGA 640×480 | 12 | **20 fps** | ~40 KB | ~6.4 Mbps | ~9 Mbps | 快速运动场景 |
| C. 高画质存档 | XGA 1024×768 | 10 | **8 fps** | ~120 KB | ~7.7 Mbps | ~11 Mbps | 静态场景，高画质 |
| D. 低带宽 | QVGA 320×240 | 12 | **15 fps** | ~20 KB | ~2.4 Mbps | ~4 Mbps | WiFi 信号弱 |
| E. 极限低延迟 | VGA 640×480 | 10 | **30 fps** | ~60 KB | ~14.4 Mbps | ~20 Mbps | 实时控制（需优质WiFi）|

#### 15.7.2 全链路带宽预算（方案 A：标准监控）

```
┌────────────────────────────────────────────────────────────────┐
│              Phase 2 标准监控方案 A - 带宽预算                    │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  WiFi 上行 (ESP32 → 路由器):                                    │
│    JPEG 数据:    70 KB/帧 × 12 fps =  840 KB/s  =   6.7 Mbps   │
│    802.11 开销:  +30%                                =   2.0 Mbps  │
│    RTP/RTSP 开销: +4%                                =   0.3 Mbps  │
│    ─────────────────────────────────────────────────────────   │
│    合计:                                               ≈   9.0 Mbps │
│                                                                │
│  路由器转发 (有线千兆口):                                        │
│    JPEG 数据:    840 KB/s                              =   6.7 Mbps │
│    ─────────────────────────────────────────────────────────   │
│    合计:                                               ≈   6.7 Mbps │
│    （千兆网口远大于需求，无瓶颈）                                   │
│                                                                │
│  Jetson Nano 存储写入:                                          │
│    JPEG 数据:    840 KB/s                              =   6.7 Mbps │
│    文件系统开销:  +5%                                =   0.3 Mbps  │
│    ─────────────────────────────────────────────────────────   │
│    合计:                                               ≈   7.0 Mbps │
│                                                                │
│  YOLO 推理对带宽无影响（推理使用 RAM 中已解码的帧）                   │
│                                                                │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  总计带宽需求:           ≈ 9.0 Mbps（WiFi 空中）                  │
│  存储写入吞吐量:         ≥ 7.0 MB/s（连续写入）                   │
│  CPU 占用（ESP32）:      ~60%（WiFi+编码+JPEG 并发）              │
│  Jetson Nano CPU 占用:   ~30%（GStreamer+JPEG decode+YOLO）       │
│  端到端延迟:             ~120ms（稳定 WiFi，latency=100ms）       │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                                                │
│  WiFi 路由器规格要求:                                            │
│    - 802.11n 或 802.11ac                                       │
│    - 5 GHz 频段推荐（干扰少，更稳定）                              │
│    - 距离 ESP32-Cam < 5 米，RSSI > -65 dBm                      │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

#### 15.7.3 月度流量估算

```
Phase 2 每天运行 24 小时（24/7 全天候录制），带宽流量：

方案 A（SVGA @ 12fps）:
  每天流量: 840 KB/s × 86400 s = 72.58 GB/天
  每月流量: 72.58 GB × 30 = 2.18 TB/月

  本地存储（Jetson Nano NVMe 500GB）:
    可录制时长: 500 GB / 840 KB/s / 86400 s × 24h = ~6 天循环录制
    建议: 外接 2TB HDD  NAS 备份方案

方案 D（QVGA @ 15fps）:
  每天流量: 300 KB/s × 86400 s = 25.92 GB/天
  每月流量: 25.92 GB × 30 = 777.6 GB/月 ≈ 0.76 TB/月

  本地存储（500GB NVMe）:
    可录制时长: 500 GB / 300 KB/s / 86400 s × 24h = ~19 天循环录制
```

### 15.8 WiFi 部署建议（确保带宽）

#### 15.8.1 路由器/AP 选型建议

| 规格 | 最低要求 | 推荐型号参考 | 说明 |
|------|---------|------------|------|
| 频段 | 2.4 GHz | **5 GHz 优先** | 5GHz 干扰少，吞吐更高 |
| 协议 | 802.11n | **802.11ac** | 802.11n 在 2.4GHz 带宽有限 |
| MU-MIMO | 不需要 | 推荐 2×2 MIMO | ESP32 只有 1×1 |
| QoS | 建议有 | WMM QoS 开启 | 优先保障视频流 |

#### 15.8.2 ESP32-Cam 摆放与天线

```
┌─────────────────────────────────────────┐
│           WiFi 信号优化 Checklist        │
├─────────────────────────────────────────┤
│ ✅ ESP32-Cam 路由器距离 < 5 米           │
│ ✅ 中间无承重墙/金属遮挡                  │
│ ✅ 路由器天线垂直（覆盖水平范围更广）       │
│ ✅ ESP32-Cam 平面正对路由器               │
│ ✅ 远离微波炉/蓝牙设备（2.4GHz 干扰源）    │
│ ✅ 静态 IP 分配（避免 DHCP 延迟）         │
│ ✅ WiFi 信道固定（非自动选择）            │
│                                         │
│ 推荐 WiFi 信道（2.4GHz 国内）:            │
│   信道 1 (2412MHz) / 信道 6 (2437MHz) / 信道 11 (2462MHz)  │
│   这三个信道互不重叠                      │
│                                         │
│ 5 GHz 推荐信道:                          │
│   国内: 149/153/157/161/165 (U-NII-3)    │
└─────────────────────────────────────────┘
```

**信号质量监测**（ESP32 固件中集成）：
```c
// 定期检查 WiFi RSSI，在信号差时自动降帧率
#include "esp_wifi.h"

void adaptive_framerate_task(void *arg)
{
    int current_fps = 12;  // 默认帧率
    int current_quality = 12;

    while (1) {
        wifi_ap_record_t ap_info;
        esp_wifi_sta_get_ap_info(&ap_info, &ap_info);

        int rssi = ap_info.rssi;

        if (rssi > -50) {
            // 优秀：保持高帧率
            current_fps = 15;
        } else if (rssi > -60) {
            // 良好：标准配置
            current_fps = 12;
        } else if (rssi > -70) {
            // 一般：降低帧率
            current_fps = 8;
        } else {
            // 差：最低配置
            current_fps = 5;
            current_quality = 15;  // 更激进压缩
        }

        ESP_LOGI(TAG, "RSSI: %d dBm → FPS: %d, Quality: %d",
                 rssi, current_fps, current_quality);

        vTaskDelay(pdMS_TO_TICKS(5000));  // 每 5 秒检查一次
    }
}
```

### 15.9 带宽估算速查卡

```
╔══════════════════════════════════════════════════════════════════╗
║              Phase 2 带宽估算 - 速查卡                            ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  ┌─ 核心数字 ─────────────────────────────────────────────────┐  ║
║  │                                                          │  ║
║  │  SVGA (800×600) @ 12fps JPEG quality=12                  │  ║
║  │  → 每帧: ~70 KB      →  带宽: ~6.7 Mbps      → 延迟: ~120ms│  ║
║  │                                                          │  ║
║  │  QVGA (320×240) @ 15fps JPEG quality=12                  │  ║
║  │  → 每帧: ~20 KB      →  带宽: ~2.4 Mbps      → 延迟: ~80ms │  ║
║  │                                                          │  ║
║  └──────────────────────────────────────────────────────────┘  ║
║                                                                  ║
║  ┌─ 存储需求 ─────────────────────────────────────────────────┐  ║
║  │  SVGA @ 12fps → 840 KB/s → 约 2.7 GB/天 → 80 GB/月        │  ║
║  │  QVGA @ 15fps → 300 KB/s → 约 1.0 GB/天 → 30 GB/月        │  ║
║  └──────────────────────────────────────────────────────────┘  ║
║                                                                  ║
║  ┌─ WiFi 规格要求 ───────────────────────────────────────────┐  ║
║  │  最低: 802.11n @ 2.4GHz, 10 Mbps 可用带宽                    │  ║
║  │  推荐: 802.11ac @ 5GHz, 30+ Mbps 可用带宽                    │  ║
║  │  ESP32-Cam RSSI 建议 > -65 dBm                             │  ║
║  └──────────────────────────────────────────────────────────┘  ║
║                                                                  ║
║  ┌─ 瓶颈判断 ─────────────────────────────────────────────────┐  ║
║  │  帧率上不去 → ESP32 CPU 瓶颈（降低分辨率或帧率）              │  ║
║  │  画面经常花屏 → WiFi 信号弱或干扰（换信道/靠近路由器）         │  ║
║  │  YOLO 延迟高 → Nano GPU 瓶颈（降分辨率或关闭其他进程）        │  ║
║  └──────────────────────────────────────────────────────────┘  ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

---

**本节补充完毕。** 配合 Phase 2 SOP 原文（§3.3 RTSP 流）和本 supplement 的 12.8 节（ESP32 RTSP 带宽估算），本章提供了完整的端到端带宽预算，覆盖 JPEG 帧大小模型、WiFi 协议开销、延迟预算、存储需求和部署建议。
