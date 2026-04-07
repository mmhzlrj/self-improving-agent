/**
 * ESP32-CAM RTSP Streaming Server
 * 
 * 主入口文件：
 *   - WiFi 连接（AP 模式或 STA 模式）
 *   - 摄像头初始化
 *   - RTSP 流媒体服务器启动
 * 
 * 编译平台：PlatformIO / Arduino ESP32
 * 适配板卡：AI-Thinker ESP32-CAM
 */

#include <Arduino.h>

// ============================================================
// WiFi 配置（可从 platformio.ini build_flags 覆盖）
// ============================================================
// 默认 AP 模式配置
#ifndef WIFI_SSID
#define WIFI_SSID       "ESP32_CAM_AP"
#endif
#ifndef WIFI_PASSWORD
#define WIFI_PASSWORD   "12345678"
#endif

// WiFi 工作模式：true = AP 模式，false = STA 模式
#ifndef WIFI_AP_MODE
#define WIFI_AP_MODE     true
#endif

// STA 模式下的路由器配置（AP 模式下不需要）
#ifndef STA_SSID
#define STA_SSID         "YourRouterSSID"
#endif
#ifndef STA_PASSWORD
#define STA_PASSWORD     "YourRouterPassword"
#endif

// ============================================================
// RTSP 配置
// ============================================================
#ifndef RTSP_PORT
#define RTSP_PORT        8554
#endif

// ============================================================
// 摄像头配置
// ============================================================
#ifndef CAMERA_MODEL_AI_THINKER
#define CAMERA_MODEL_AI_THINKER
#endif

#ifndef VIDEO_FRAME_SIZE
#define VIDEO_FRAME_SIZE     FRAMESIZE_SVGA   // 800x600，推荐分辨率
#endif

#ifndef JPEG_QUALITY
#define JPEG_QUALITY          12              // 10-63，越低质量越好
#endif

// ============================================================
// 头文件
// ============================================================
#include <WiFi.h>
#include <esp_camera.h>
#include <RTSP.h>

// ============================================================
// 全局变量
// ============================================================
static const char* TAG = "ESP32-CAM-RTSP";

// RTSP 服务器实例
RTSP rtspServer;

// 摄像头帧缓冲区
camera_fb_t* fb = nullptr;

// WiFi 连接状态
bool wifiConnected = false;

// ============================================================
// 函数声明
// ============================================================
void setupWiFi();
void setupCamera();
void setupRTSP();
void cameraTask(void* parameter);

// ============================================================
// WiFi 初始化
// ============================================================
void setupWiFi() {
    Serial.println();
    Serial.println("========================================");
    Serial.println("  ESP32-CAM RTSP 启动中...");
    Serial.println("========================================");

    if (WIFI_AP_MODE) {
        // -------------------
        // AP 模式：创建热点
        // -------------------
        Serial.printf("[WiFi] AP 模式，启动热点: %s\n", WIFI_SSID);
        
        // 禁用 WiFi 省电模式以提高稳定性
        WiFi.setSleep(false);
        
        // 配置 AP 参数
        bool apStarted = WiFi.softAP(WIFI_SSID, WIFI_PASSWORD);
        if (!apStarted) {
            Serial.println("[WiFi] 错误：AP 启动失败！");
            return;
        }

        const char* apIP = WiFi.softAPIP().toString().c_str();
        Serial.println("[WiFi] AP 启动成功！");
        Serial.printf("[WiFi] IP 地址: %s\n", apIP);
        Serial.printf("[WiFi] 端口: %d\n", RTSP_PORT);
        Serial.printf("[WiFi] RTSP 完整地址: rtsp://%s:%d/mjpeg/1\n", apIP, RTSP_PORT);
        
    } else {
        // -------------------
        // STA 模式：连接路由器
        // -------------------
        Serial.printf("[WiFi] STA 模式，连接到: %s\n", STA_SSID);
        
        WiFi.mode(WIFI_STA);
        WiFi.setSleep(false);
        
        // 开始连接
        WiFi.begin(STA_SSID, STA_PASSWORD);
        
        // 等待连接，带超时检测
        int attempts = 0;
        const int MAX_ATTEMPTS = 30;  // 30 * 500ms = 15秒超时
        
        while (WiFi.status() != WL_CONNECTED && attempts < MAX_ATTEMPTS) {
            delay(500);
            Serial.print(".");
            attempts++;
        }
        Serial.println();
        
        if (WiFi.status() == WL_CONNECTED) {
            wifiConnected = true;
            Serial.println("[WiFi] STA 连接成功！");
            Serial.printf("[WiFi] IP 地址: %s\n", WiFi.localIP().toString().c_str());
            Serial.printf("[WiFi] RSSI: %d dBm\n", WiFi.RSSI());
            Serial.printf("[WiFi] RTSP 完整地址: rtsp://%s:%d/mjpeg/1\n", 
                          WiFi.localIP().toString().c_str(), RTSP_PORT);
        } else {
            Serial.println("[WiFi] 错误：STA 连接失败！");
            Serial.println("[WiFi] 切换到 AP 模式作为备份...");
            
            // STA 连接失败，自动切换到 AP 模式
            WiFi.mode(WIFI_AP);
            WiFi.softAP(WIFI_SSID, WIFI_PASSWORD);
            Serial.printf("[WiFi] AP 备份启动，IP: %s\n", WiFi.softAPIP().toString().c_str());
        }
    }
    
    Serial.println("========================================");
    Serial.println();
}

// ============================================================
// 摄像头初始化
// ============================================================
void setupCamera() {
    Serial.println("[Camera] 初始化摄像头...");

    // 摄像头配置参数
    camera_config_t config;
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer   = LEDC_TIMER_0;
    config.pin_d0       = 5;
    config.pin_d1       = 18;
    config.pin_d2       = 19;
    config.pin_d3       = 21;
    config.pin_d4       = 36;
    config.pin_d5       = 39;
    config.pin_d6       = 34;
    config.pin_d7       = 35;
    config.pin_xclk     = 0;
    config.pin_pclk     = 22;
    config.pin_vsync    = 25;
    config.pin_href     = 23;
    config.pin_sscb_sda = 26;
    config.pin_sscb_scl = 27;
    config.pin_reset    = -1;   // 无需复位引脚（AI-Thinker 板载复位）
    config.pin_pwdn     = 32;   // 电源控制引脚
    
    config.xclk_freq_hz = 20000000;   // 20MHz XCLK（稳定且省电）
    config.frame_size   = VIDEO_FRAME_SIZE;
    config.pixel_format = PIXFORMAT_JPEG;  // JPEG 压缩格式，带宽更低
    config.grab_mode    = CAMERA_GRAB_WHEN_EMPTY;
    config.fb_location   = CAMERA_FB_IN_PSRAM;  // 优先使用 PSRAM
    
    // JPEG 编码质量
    config.jpeg_quality = JPEG_QUALITY;

    // PSRAM 检测
#if CONFIG_IDF_TARGET_ESP32
    if (psramFound()) {
        config.fb_location = CAMERA_FB_IN_PSRAM;
        Serial.printf("[Camera] PSRAM 大小: %d bytes\n", psramSize());
    } else {
        config.fb_location = CAMERA_FB_IN_DRAM;
        Serial.println("[Camera] 警告：未检测到 PSRAM，使用 DRAM");
    }
#else
    config.fb_location = CAMERA_FB_IN_DRAM;
#endif

    // 根据板卡型号配置摄像头
#if defined(CAMERA_MODEL_AI_THINKER)
    // AI-Thinker ESP32-CAM 专用配置
    config.pin_pwdn  = 32;
    config.pin_reset = -1;
    config.xclk_freq_hz = 20000000;
    config.pixel_format = PIXFORMAT_JPEG;
    
#elif defined(CAMERA_MODEL_WROVER_KIT)
    config.pin_pwdn  = -1;
    config.pin_reset = -1;
    
#elif defined(CAMERA_MODEL_ESP_EYE)
    config.pin_pwdn  = -1;
    config.pin_reset = -1;
    
#elif defined(CAMERA_MODEL_M5STACK_PSRAM)
    config.pin_pwdn  = -1;
    config.pin_reset = 15;
    
#elif defined(CAMERA_MODEL_M5STACK_WIDE)
    config.pin_pwdn  = -1;
    config.pin_reset = 15;
    
#else
    // 默认配置（自定义板卡）
    #warning "未识别的板卡型号，使用默认引脚配置"
#endif

    // 初始化摄像头
    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        Serial.printf("[Camera] 错误：初始化失败，错误码 0x%x\n", err);
        Serial.println("[Camera] 可能原因：");
        Serial.println("  1. 摄像头硬件连接不良");
        Serial.println("  2. XCLK 频率设置不当");
        Serial.println("  3. PSRAM 容量不足");
        return;
    }

    // 配置摄像头传感器参数（根据实际效果调整）
    sensor_t* s = esp_camera_sensor_get();
    if (s != nullptr) {
        // 基本参数设置
        s->set_brightness(s, 0);      // 亮度: -2 to 2
        s->set_contrast(s, 0);        // 对比度: -2 to 2
        s->set_saturation(s, 0);      // 饱和度: -2 to 2
        
        // 垂直翻转和水平镜像（根据摄像头安装方向调整）
        s->set_vflip(s, 1);           // 垂直翻转：1 = 启用
        s->set_hmirror(s, 0);         // 水平镜像：0 = 禁用
        
        // 白平衡和曝光
        s->set_whitebal(s, 1);        // 自动白平衡：启用
        s->set_awb_gain(s, 1);       // 自动白平衡增益：启用
        s->set_wb_mode(s, 0);         // 白平衡模式：0 = 自动
        s->set_exposure_ctrl(s, 1);   // 自动曝光：启用
        s->set_aec2(s, 0);            // AEC2 算法：禁用
        
        // 特效
        // s->set_effect(s, 0);        // 0 = 正常, 1 = 负片, 2 = 黑白等
        
        // AEC/AGC 增益
        s->set_agc_gain(s, 0);        // AGC 增益: 0 = 禁用 (自动)
        
        // 增益上限（1x-30x）
        s->set_gainceiling(s, GAINCEILING_2X);
        
        // 日志输出
        Serial.println("[Camera] 摄像头初始化成功！");
        Serial.printf("[Camera] 分辨率: %dx%d\n", 
                      s->status.framesize == FRAMESIZE_SVGA ? 800 : 
                      s->status.framesize == FRAMESIZE_VGA ? 640 : 
                      s->status.framesize, 
                      s->status.framesize == FRAMESIZE_SVGA ? 600 : 
                      s->status.framesize == FRAMESIZE_VGA ? 480 : 480);
        Serial.printf("[Camera] JPEG 质量: %d\n", s->status.quality);
    } else {
        Serial.println("[Camera] 警告：无法获取传感器对象");
    }
}

// ============================================================
// RTSP 服务器初始化
// ============================================================
void setupRTSP() {
    Serial.printf("[RTSP] 启动 RTSP 服务器，端口: %d\n", RTSP_PORT);
    
    // 初始化 RTSP 服务器
    bool rtspStarted = rtspServer.begin(RTSP_PORT);
    if (!rtspStarted) {
        Serial.println("[RTSP] 错误：RTSP 服务器启动失败！");
        return;
    }
    
    Serial.println("[RTSP] RTSP 服务器启动成功！");
    Serial.println("[RTSP] 可用播放器：");
    Serial.println("  VLC:    rtsp://<IP>:8554/mjpeg/1");
    Serial.println("  FFplay: ffplay rtsp://<IP>:8554/mjpeg/1");
}

// ============================================================
// 摄像头任务（FreeRTOS 后台任务）
// ============================================================
void cameraTask(void* parameter) {
    Serial.println("[Camera Task] 摄像头任务启动");
    
    while (true) {
        // 获取摄像头帧
        fb = esp_camera_fb_get();
        if (!fb) {
            Serial.println("[Camera] 错误：获取帧失败");
            // 等待后重试
            vTaskDelay(pdMS_TO_TICKS(100));
            continue;
        }
        
        // 检查帧是否有效
        if (fb->len == 0 || fb->buf == nullptr) {
            Serial.println("[Camera] 错误：帧数据无效");
            esp_camera_fb_return(fb);
            vTaskDelay(pdMS_TO_TICKS(100));
            continue;
        }
        
        // 将帧推送给 RTSP 服务器
        rtspServer.stream(fb->buf, fb->len);
        
        // 释放帧缓冲区
        esp_camera_fb_return(fb);
        
        // 短暂延迟，避免 CPU 占用过高
        vTaskDelay(pdMS_TO_TICKS(1));
    }
}

// ============================================================
// Arduino 主入口：初始化
// ============================================================
void setup() {
    // 初始化串口
    Serial.begin(115200);
    Serial.setDebugOutput(true);
    
    // 等待串口稳定
    delay(1000);
    
    Serial.println();
    Serial.println("╔════════════════════════════════════════════╗");
    Serial.println("║      ESP32-CAM RTSP Streaming Server       ║");
    Serial.println("║           Version 1.0.0                    ║");
    Serial.println("╚════════════════════════════════════════════╝");
    Serial.println();

    // 1. 初始化 WiFi
    setupWiFi();
    
    // 2. 初始化摄像头
    setupCamera();
    
    // 3. 初始化 RTSP 服务器
    setupRTSP();
    
    // 4. 启动摄像头后台任务（FreeRTOS）
    //    优先级 1，堆栈 4096 bytes
    xTaskCreatePinnedToCore(
        cameraTask,          // 任务函数
        "CameraTask",        // 任务名称
        4096,                // 堆栈大小
        nullptr,             // 参数
        1,                   // 优先级
        nullptr,             // 任务句柄
        0                    // 在 Core 0 上运行
    );
    
    Serial.println();
    Serial.println("========================================");
    Serial.println("  系统初始化完成！");
    Serial.println("========================================");
    Serial.println();
}

// ============================================================
// Arduino 主循环
// ============================================================
void loop() {
    // 处理 RTSP 服务器的客户端连接
    rtspServer.handleLoop();
    
    // 定期检查 WiFi 状态
    static unsigned long lastWiFiCheck = 0;
    unsigned long now = millis();
    
    if (now - lastWiFiCheck > 10000) {  // 每 10 秒检查一次
        lastWiFiCheck = now;
        
        if (WiFi.status() != WL_CONNECTED) {
            Serial.println("[WiFi] 警告：WiFi 连接丢失，正在重连...");
            if (WIFI_AP_MODE == false) {
                WiFi.reconnect();
            }
        }
    }
    
    // 让出 CPU 时间
    delay(1);
}

// ============================================================
// 辅助函数：获取摄像头状态信息
// ============================================================
String getCameraStatus() {
    String status = "ESP32-CAM Status:\n";
    status += "  WiFi Mode: " + String(WIFI_AP_MODE ? "AP" : "STA") + "\n";
    status += "  IP: " + WiFi.localIP().toString() + "\n";
    status += "  RSSI: " + String(WiFi.RSSI()) + " dBm\n";
    status += "  RTSP Port: " + String(RTSP_PORT) + "\n";
    return status;
}
