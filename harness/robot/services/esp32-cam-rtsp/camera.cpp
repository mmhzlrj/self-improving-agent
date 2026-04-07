/**
 * @file camera.cpp
 * @brief ESP32-CAM Camera Driver - 摄像头初始化与 JPEG 捕获
 * 
 * 适用板卡: AI-Thinker ESP32-CAM (CAMERA_MODEL_AI_THINKER)
 * 依赖库: esphome/esp32-camera@^2.0.4
 * 
 * 功能:
 *   - 摄像头传感器初始化
 *   - JPEG 帧捕获
 *   - 帧缓冲管理
 */

#include "camera.h"

// ======================== 静态变量 ========================

static camera_config_t camera_config;
static bool camera_initialized = false;
static framesize_t current_frame_size = FRAMESIZE_SVGA;
static uint8_t current_jpeg_quality = 12;

// ======================== 错误码定义 ========================

typedef enum {
    CAM_OK = 0,
    CAM_ERR_INIT_FAILED = -1,
    CAM_ERR_INVALID_CONFIG = -2,
    CAM_ERR_NO_FRAME_BUFFER = -3,
    CAM_ERR_CAPTURE_FAILED = -4,
    CAM_ERR_DEST_NOT_ALIGNED = -5,
} cam_err_t;

// ======================== 内部函数声明 ========================

static cam_err_t camera_probe_and_configure(void);
static const char* camera_error_to_string(cam_err_t err);

// ======================== 摄像头初始化 ========================

/**
 * @brief 初始化摄像头传感器
 * 
 * 配置顺序（参考 esp32-camera 官方流程）:
 *   1. 配置 PSRAM (如启用)
 *   2. 配置摄像头 IO (VSYNC, HREF, PCLK, D0-D7)
 *   3. 设置分辨率和 JPEG 质量
 *   4. 调用 esp_camera_init()
 * 
 * @param frame_size    帧分辨率 (默认 FRAMESIZE_SVGA)
 * @param jpeg_quality  JPEG 编码质量 10-63, 值越小质量越好 (默认 12)
 * @return int  0=成功, 负值=错误码
 */
int camera_init(framesize_t frame_size, uint8_t jpeg_quality)
{
    if (camera_initialized) {
        Serial.println("[CAM] Camera already initialized");
        return CAM_OK;
    }

    // 保存配置
    current_frame_size = frame_size;
    current_jpeg_quality = jpeg_quality;

    // -------------------- 步骤1: 配置摄像头硬件参数 --------------------
    // AI-Thinker ESP32-CAM 引脚定义:
    //   - Y2-GPIO12 (D6 on board)
    //   - Y3-GPIO13 (D7 on board)
    //   - Y4-GPIO14 (D8 on board)
    //   - Y5-GPIO15 (D9 on board)
    //   - Y6-GPIO16 (D10 on board)
    //   - Y7-GPIO17 (D11 on board)
    //   - Y8-GPIO18 (D12 on board)
    //   - Y9-GPIO19 (D13 on board)
    //   - Y10-GPIO21 (CMD on board)
    //   - Y11-GPIO22 (CLK on board)
    //   - VSYNC-GPIO25 (D2 on board)
    //   - HREF-GPIO23  (D1 on board)
    //   - PCLK-GPIO22  (CLK shared with SDIO,复用)

    memset(&camera_config, 0, sizeof(camera_config_t));

    camera_config.ledc_channel = LEDC_CHANNEL_0;
    camera_config.ledc_timer   = LEDC_TIMER_0;
    camera_config.pin_d0       = 12;   // Y2
    camera_config.pin_d1       = 13;   // Y3
    camera_config.pin_d2       = 14;   // Y4
    camera_config.pin_d3       = 15;   // Y5
    camera_config.pin_d4       = 16;   // Y6
    camera_config.pin_d5       = 17;   // Y6
    camera_config.pin_d6       = 18;   // Y7
    camera_config.pin_d7       = 19;   // Y8
    camera_config.pin_vsync    = 25;   // VSYNC
    camera_config.pin_href     = 23;   // HREF
    camera_config.pin_pclk     = 22;   // PCLK
    camera_config.pin_sscb_sda = 21;   // SCCB (I2C SDA)
    camera_config.pin_sscb_scl = 22;   // SCCB (I2C SCL)

    // XCLK 时钟配置 (AI-Thinker ESP32-CAM 通常使用 8MHz 或 20MHz)
    camera_config.pin_xclk = 0;        // XCLK output pin (GPIO0 on AI-Thinker)

    // 摄像头时序参数 (适用于 OV2640, 常见于 AI-Thinker ESP32-CAM)
    camera_config.xclk_freq_hz = 8000000;   // 8 MHz XCLK
    camera_config.sccb_i2c_port = 0;         // I2C port 0

    // 像素格式:
    //   PIXFORMAT_PIXabay --- 仅灰度, 无 JPEG
    //   PIXFORMAT_JPEG    --- JPEG 编码 (需要 JPEG 编码器硬件, OV2640支持)
    camera_config.pixel_format = PIXFORMAT_JPEG;

    // 帧大小
    camera_config.frame_size = frame_size;

    // JPEG 编码质量 (10=最高质量/最大文件, 63=最低质量/最小文件)
    // ESP32-CAM 带 PSRAM 时建议用 12, 无 PSRAM 时建议用 15-20
    camera_config.jpeg_quality = jpeg_quality;

    // FB 数量: 双缓冲可提高帧率但占用更多内存
    // ESP32-CAM 无 PSRAM: 建议 1
    // ESP32-CAM 有 PSRAM: 建议 2
#ifdef CONFIG_ESP32_SPIRAM_SUPPORT
    camera_config.fb_count = 2;
#else
    camera_config.fb_count = 1;
#endif

    // Grab mode: 保持 FB 所有权, 捕获后立即可用
    camera_config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;

    // -------------------- 步骤2: 调用 esp_camera_init --------------------
    // esp_camera_init() 会:
    //   1. 初始化 SCCB (I2C) 总线
    //   2. 检测摄像头传感器 (OV2640 / OV7670 / etc.)
    //   3. 配置摄像头寄存器
    //   4. 分配帧缓冲
    //   5. 启动摄像头任务

    Serial.printf("[CAM] Initializing camera (frame=%d, quality=%d)...\n",
                   frame_size, jpeg_quality);

    esp_err_t err = esp_camera_init(&camera_config);
    if (err != ESP_OK) {
        Serial.printf("[CAM] ERROR: esp_camera_init failed: 0x%x (%s)\n",
                      err, esp_err_to_name(err));
        return CAM_ERR_INIT_FAILED;
    }

    // -------------------- 步骤3: 获取 sensor handle 并精细配置 --------------------
    sensor_t* sensor = esp_camera_sensor_get();
    if (sensor == NULL) {
        Serial.println("[CAM] ERROR: Failed to get camera sensor handle");
        esp_camera_deinit();
        return CAM_ERR_INIT_FAILED;
    }

    // 以下配置针对 OV2640 (AI-Thinker ESP32-CAM 默认传感器)
    // 根据实际传感器型号调整
    sensor->set_brightness(sensor, 0);      // 亮度: -2 到 2
    sensor->set_contrast(sensor, 0);          // 对比度: -2 到 2
    sensor->set_saturation(sensor, 0);       // 饱和度: -2 到 2
    sensor->set_whitebal(sensor, 1);         // 自动白平衡: 启用
    sensor->set_awb_gain(sensor, 1);         // AWB 增益: 启用
    sensor->set_wb_mode(sensor, 0);          // 白平衡模式: 0=自动
    sensor->set_exposure_ctrl(sensor, 1);    // 自动曝光: 启用
    sensor->set_aec2(sensor, 0);             // AEC2: 禁用 (使用自动)
    sensor->set_ae_level(sensor, 0);        // AE 级别: 0=正常
    sensor->set_aec_value(sensor, 300);      // AE 曝光值 (参考)
    sensor->set_gain_ctrl(sensor, 0);       // 手动增益: 禁用
    sensor->set_agc_gain(sensor, 0);         // AGC 增益: 0=自动
    sensor->set_gainceiling(sensor, (gainceiling_t)0);  // 增益上限
    sensor->set_bpc(sensor, 0);             // 黑像素校正: 禁用
    sensor->set_wpc(sensor, 1);             // 白像素校正: 启用
    sensor->set_raw_gma(sensor, 1);         // RAW Gamma: 启用
    sensor->set_lenc(sensor, 1);            // 镜头校正: 启用
    sensor->set_hmirror(sensor, 0);         // 水平镜像: 禁用
    sensor->set_vflip(sensor, 0);           // 垂直翻转: 禁用
    sensor->set_dcw(sensor, 1);             // 向下采样: 启用
    sensor->set_colorbar(sensor, 0);        // 彩色条纹测试: 禁用

    // -------------------- 完成 --------------------
    camera_initialized = true;

    Serial.println("[CAM] Camera initialized successfully");
    Serial.printf("[CAM]   Resolution: %dx%d\n",
                  resolution[sensor->status.framesize].width,
                  resolution[sensor->status.framesize].height);
    Serial.printf("[CAM]   Sensor ID:  0x%02X\n", sensor->id.version);
    Serial.printf("[CAM]   PSRAM:      %s\n",
#ifdef CONFIG_ESP32_SPIRAM_SUPPORT
                  "available"
#else
                  "not available"
#endif
                  );

    return CAM_OK;
}

/**
 * @brief 释放摄像头资源
 */
void camera_deinit(void)
{
    if (!camera_initialized) {
        return;
    }
    esp_camera_deinit();
    camera_initialized = false;
    Serial.println("[CAM] Camera deinitialized");
}

// ======================== JPEG 捕获 ========================

/**
 * @brief 捕获一帧 JPEG 图像
 * 
 * @param fb_out  输出参数, 指向捕获的帧缓冲 (外部分配或 NULL)
 *               注意: 返回的 fb 需要用户调用 camera_return_frame() 释放
 * @return cam_err_t 错误码
 */
cam_err_t camera_capture_jpeg(camera_fb_t** fb_out)
{
    if (!camera_initialized) {
        Serial.println("[CAM] ERROR: Camera not initialized");
        return CAM_ERR_INIT_FAILED;
    }

    if (fb_out == NULL) {
        return CAM_ERR_INVALID_CONFIG;
    }

    // -------------------- 获取帧缓冲 --------------------
    // esp_camera_fb_get() 会从摄像头驱动获取一帧
    // 帧缓冲由 esp_camera_init() 预分配
    // 返回的 buffer 指针在调用 esp_camera_fb_return() 前有效

    Serial.println("[CAM] Capturing frame...");
    camera_fb_t* fb = esp_camera_fb_get();

    if (fb == NULL) {
        Serial.println("[CAM] ERROR: Failed to get frame buffer (fb NULL)");
        return CAM_ERR_CAPTURE_FAILED;
    }

    // -------------------- 检查帧有效性 --------------------
    if (fb->len == 0 || fb->buf == NULL) {
        Serial.println("[CAM] ERROR: Frame buffer is empty");
        esp_camera_fb_return(fb);
        return CAM_ERR_NO_FRAME_BUFFER;
    }

    // -------------------- 检查 JPEG 格式 --------------------
    if (fb->format != PIXFORMAT_JPEG) {
        Serial.printf("[CAM] WARNING: Unexpected format: %d (expected JPEG)\n",
                      fb->format);
        // 仍返回帧, 由调用方处理
    }

    // -------------------- 输出调试信息 --------------------
    Serial.printf("[CAM] Frame captured: %dx%d, %zu bytes, fmt=%d\n",
                  fb->width, fb->height, fb->len, fb->format);

#ifdef CAMERA_DEBUG_PRINT_FIRST_BYTES
    // 仅调试用途: 打印 JPEG 头部 (SOI: 0xFF 0xD8)
    Serial.printf("[CAM] JPEG SOI: 0x%02X 0x%02X\n",
                  fb->buf[0], fb->buf[1]);
#endif

    *fb_out = fb;
    return CAM_OK;
}

/**
 * @brief 释放帧缓冲 (归还给驱动)
 * 
 * 必须在 camera_capture_jpeg() 之后调用, 否则帧缓冲无法循环利用
 */
void camera_return_frame(camera_fb_t* fb)
{
    if (fb != NULL) {
        esp_camera_fb_return(fb);
    }
}

// ======================== 帧缓冲拷贝 (对外接口) ========================

/**
 * @brief 捕获并拷贝一帧 JPEG 到指定缓冲区
 * 
 * 当需要将 JPEG 数据传输到外设 (如 SD 卡、网络) 时,
 * 可以先用此函数拷贝到临时缓冲区, 再立即归还 FB 给驱动
 * 
 * @param dest     目标缓冲区 (由调用方分配)
 * @param dest_len 目标缓冲区大小
 * @return ssize_t 实际拷贝的字节数, -1=失败
 */
ssize_t camera_capture_and_copy(uint8_t* dest, size_t dest_len)
{
    camera_fb_t* fb = NULL;
    cam_err_t err = camera_capture_jpeg(&fb);
    if (err != CAM_OK || fb == NULL) {
        return -1;
    }

    if (dest == NULL || dest_len == 0) {
        camera_return_frame(fb);
        return -1;
    }

    if (fb->len > dest_len) {
        Serial.printf("[CAM] ERROR: dest buffer too small (%zu < %zu)\n",
                      dest_len, fb->len);
        camera_return_frame(fb);
        return -1;
    }

    // 拷贝数据
    memcpy(dest, fb->buf, fb->len);

    // 立即归还 FB, 让驱动可以继续捕获下一帧
    camera_return_frame(fb);

    return fb->len;
}

// ======================== 分辨率工具 ========================

/**
 * @brief 获取当前分辨率的宽度
 */
int camera_get_width(void)
{
    sensor_t* sensor = esp_camera_sensor_get();
    if (sensor == NULL) return 0;
    return resolution[sensor->status.framesize].width;
}

/**
 * @brief 获取当前分辨率的高度
 */
int camera_get_height(void)
{
    sensor_t* sensor = esp_camera_sensor_get();
    if (sensor == NULL) return 0;
    return resolution[sensor->status.framesize].height;
}

/**
 * @brief 检查摄像头是否已初始化
 */
bool camera_is_initialized(void)
{
    return camera_initialized;
}

// ======================== 错误信息 ========================

static const char* camera_error_to_string(cam_err_t err)
{
    switch (err) {
        case CAM_OK:                   return "OK";
        case CAM_ERR_INIT_FAILED:      return "Camera init failed";
        case CAM_ERR_INVALID_CONFIG:   return "Invalid configuration";
        case CAM_ERR_NO_FRAME_BUFFER:  return "No frame buffer";
        case CAM_ERR_CAPTURE_FAILED:    return "Frame capture failed";
        case CAM_ERR_DEST_NOT_ALIGNED: return "Destination not aligned";
        default:                       return "Unknown error";
    }
}

// ======================== 辅助: 打印当前配置 ========================

void camera_print_config(void)
{
    sensor_t* sensor = esp_camera_sensor_get();
    if (sensor == NULL) {
        Serial.println("[CAM] Sensor not available");
        return;
    }

    Serial.println("========== Camera Config ==========");
    Serial.printf("  Initialized:    %s\n", camera_initialized ? "YES" : "NO");
    Serial.printf("  Frame Size:     %d (%dx%d)\n",
                  sensor->status.framesize,
                  resolution[sensor->status.framesize].width,
                  resolution[sensor->status.framesize].height);
    Serial.printf("  Quality:       %d\n", sensor->status.quality);
    Serial.printf("  Brightness:    %d\n", sensor->status.brightness);
    Serial.printf("  Contrast:      %d\n", sensor->status.contrast);
    Serial.printf("  Saturation:    %d\n", sensor->status.saturation);
    Serial.printf("  Sharpness:     %d\n", sensor->status.sharpness);
    Serial.printf("  Whitebal:      %d\n", sensor->status.whitebal);
    Serial.printf("  AWB Gain:      %d\n", sensor->status.awb_gain);
    Serial.printf("  Exposure Ctrl: %d\n", sensor->status.exposure_ctrl);
    Serial.printf("  AEC2:          %d\n", sensor->status.aec2);
    Serial.printf("  AE Level:      %d\n", sensor->status.ae_level);
    Serial.printf("  AEC Value:     %d\n", sensor->status.aec_value);
    Serial.printf("  Gain Ctrl:     %d\n", sensor->status.gain_ctrl);
    Serial.printf("  AGC Gain:      %d\n", sensor->status.agc_gain);
    Serial.printf("  Gain Ceiling:  %d\n", sensor->status.gainceiling);
    Serial.printf("  BPC:           %d\n", sensor->status.bpc);
    Serial.printf("  WPC:           %d\n", sensor->status.wpc);
    Serial.printf("  Raw GMA:       %d\n", sensor->status.raw_gma);
    Serial.printf("  Lenc:          %d\n", sensor->status.lenc);
    Serial.printf("  HMirror:       %d\n", sensor->status.hmirror);
    Serial.printf("  VFlip:         %d\n", sensor->status.vflip);
    Serial.printf("  DCW:           %d\n", sensor->status.dcw);
    Serial.printf("  Colorbar:      %d\n", sensor->status.colorbar);
    Serial.printf("  Sensor ID:     0x%02X\n", sensor->id.version);
    Serial.println("===================================");
}
