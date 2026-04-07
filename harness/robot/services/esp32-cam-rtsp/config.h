/**
 * @file config.h
 * @brief ESP32-CAM RTSP 项目配置头文件
 * 
 * 功能范围：
 *   - WiFi 配置（AP / STA 双模式）
 *   - 视频分辨率与帧率配置
 *   - RTSP 服务器配置
 *   - 摄像头引脚与传感器参数
 *   - 调试与日志开关
 * 
 * 使用说明：
 *   - 默认值适用于 AI-Thinker ESP32-CAM 板
 *   - 各项配置均可在编译时通过 -D 参数覆盖
 *   - 详细覆盖示例见 platformio.ini build_flags
 */

#ifndef CONFIG_H
#define CONFIG_H

#include <stdint.h>

// =============================================================
// 第一部分：WiFi 配置
// =============================================================

/**
 * @name WiFi 工作模式
 * @{
 */

/**
 * @brief WiFi 工作模式
 *   true  = AP 模式（设备作为热点，手机/电脑直连）
 *   false = STA 模式（设备连接已有路由器）
 * 
 * @note 默认 AP 模式，无需外部路由器即可使用
 */
#ifndef WIFI_AP_MODE
#define WIFI_AP_MODE  true
#endif

/** @} */

/**
 * @name AP 模式配置（热点）
 * @{
 */

/**
 * @brief AP 模式下的 WiFi SSID（热点名称）
 * @note  手机/电脑搜索到的 WiFi 名称
 */
#ifndef WIFI_SSID
#define WIFI_SSID     "ESP32_CAM_AP"
#endif

/**
 * @brief AP 模式下的 WiFi 密码
 * @note  至少 8 个字符；留空可实现无密码开放热点（不推荐）
 */
#ifndef WIFI_PASSWORD
#define WIFI_PASSWORD "12345678"
#endif

/**
 * @brief AP 模式信道
 * @note  1-13，默认为 1；周围 WiFi 干扰多时可切换到 6 或 11
 */
#ifndef WIFI_CHANNEL
#define WIFI_CHANNEL  1
#endif

/**
 * @brief AP 模式最大连接数
 * @note  ESP32 通常支持 4-8 个设备，建议不超过 4 个
 */
#ifndef WIFI_MAX_CONNECT
#define WIFI_MAX_CONNECT  4
#endif

/** @} */

/**
 * @name STA 模式配置（连接路由器）
 * @{
 */

/**
 * @brief STA 模式下要连接的路由器 SSID
 * @note  仅 WIFI_AP_MODE==false 时使用
 */
#ifndef STA_SSID
#define STA_SSID       "YourRouterSSID"
#endif

/**
 * @brief STA 模式下的路由器密码
 */
#ifndef STA_PASSWORD
#define STA_PASSWORD   "YourRouterPassword"
#endif

/**
 * @brief STA 模式连接超时时间（毫秒）
 * @note  超时后自动切换到 AP 模式作为备份
 */
#ifndef STA_CONNECT_TIMEOUT_MS
#define STA_CONNECT_TIMEOUT_MS  15000
#endif

/** @} */

// =============================================================
// 第二部分：RTSP 服务器配置
// =============================================================

/**
 * @name RTSP 服务器配置
 * @{
 */

/**
 * @brief RTSP 服务器监听端口
 * @note  标准 RTSP 端口为 554，但该端口需要 root 权限；
 *        因此默认使用 8554（rtsp://<IP>:8554/mjpeg/1）
 */
#ifndef RTSP_PORT
#define RTSP_PORT  8554
#endif

/**
 * @brief RTSP 流路径
 * @note  VLC/FFplay 访问路径，/mjpeg/1 表示第一个 MJPEG 流
 */
#ifndef RTSP_STREAM_PATH
#define RTSP_STREAM_PATH  "/mjpeg/1"
#endif

/**
 * @brief RTSP 服务器任务栈大小（字节）
 * @note  默认 4096，复杂场景可增大到 8192
 */
#ifndef RTSP_TASK_STACK_SIZE
#define RTSP_TASK_STACK_SIZE  4096
#endif

/**
 * @brief RTSP 服务器任务优先级
 * @note  默认 1（低优先级），可设为 2 防止丢帧
 */
#ifndef RTSP_TASK_PRIORITY
#define RTSP_TASK_PRIORITY   1
#endif

/**
 * @brief RTSP 服务端点核心编号
 * @note  0 或 1，ESP32 双核；设为 -1 则不绑定核心（不推荐）
 */
#ifndef RTSP_TASK_CORE
#define RTSP_TASK_CORE  0
#endif

/** @} */

// =============================================================
// 第三部分：视频分辨率与帧率配置
// =============================================================

/**
 * @name 视频分辨率配置
 * @{
 */

/**
 * @brief 视频帧分辨率
 * 
 * 可选值（esp32-camera 库定义）：
 *   FRAMESIZE_UXGA  (1600x1200)  - 最高画质，帧率低
 *   FRAMESIZE_SXGA  (1280x1024)
 *   FRAMESIZE_HD     (1280x720)
 *   FRAMESIZE_SVGA  (800x600)    - 【推荐】平衡画质与帧率
 *   FRAMESIZE_VGA   (640x480)    - 最高帧率
 *   FRAMESIZE_QVGA  (320x240)    - 低带宽场景
 *   FRAMESIZE_QQVGA (160x120)    - 最低分辨率
 * 
 * @note 不带 PSRAM 的 ESP32-CAM 推荐 SVGA 或 VGA；
 *       带 PSRAM 的 ESP32-CAM 可用 HD 或更高
 */
#ifndef VIDEO_FRAME_SIZE
#define VIDEO_FRAME_SIZE  FRAMESIZE_SVGA
#endif

/**
 * @brief 静态常量：当前分辨率宽度（像素）
 * @note  与 VIDEO_FRAME_SIZE 对应，用于日志输出
 */
#if defined(FRAMESIZE_UXGA)
#define VIDEO_WIDTH   1600
#define VIDEO_HEIGHT  1200
#elif defined(FRAMESIZE_SXGA)
#define VIDEO_WIDTH   1280
#define VIDEO_HEIGHT  1024
#elif defined(FRAMESIZE_HD)
#define VIDEO_WIDTH   1280
#define VIDEO_HEIGHT  720
#elif defined(FRAMESIZE_SVGA)
#define VIDEO_WIDTH   800
#define VIDEO_HEIGHT  600
#elif defined(FRAMESIZE_VGA)
#define VIDEO_WIDTH   640
#define VIDEO_HEIGHT  480
#elif defined(FRAMESIZE_QVGA)
#define VIDEO_WIDTH   320
#define VIDEO_HEIGHT  240
#elif defined(FRAMESIZE_QQVGA)
#define VIDEO_WIDTH   160
#define VIDEO_HEIGHT  120
#else
// 默认值，防止未定义警告
#define VIDEO_WIDTH   800
#define VIDEO_HEIGHT  600
#warning "未知的 VIDEO_FRAME_SIZE，使用默认值 SVGA(800x600)"
#endif

/** @} */

/**
 * @name JPEG 编码质量配置
 * @{
 */

/**
 * @brief JPEG 编码质量
 * @note  范围 10-63，值越小质量越好、文件越大
 *        推荐：10-15 高质量，20-25 中等，30-40 低带宽
 *        默认 12 兼顾画质与带宽
 */
#ifndef JPEG_QUALITY
#define JPEG_QUALITY  12
#endif

/**
 * @brief JPEG 质量有效性检查
 * @note  编译时校验，确保值在合法范围内
 */
#if (JPEG_QUALITY < 10) || (JPEG_QUALITY > 63)
#error "JPEG_QUALITY 必须在 10-63 范围内"
#endif

/** @} */

/**
 * @name 帧率控制
 * @{
 */

/**
 * @brief 目标帧率（FPS）
 * @note  受限于摄像头硬件和 WiFi 带宽；WiFi 瓶颈时实际帧率可能低于此值
 *        SVGA 分辨率下通常可达 15-25 FPS
 */
#ifndef TARGET_FPS
#define TARGET_FPS  20
#endif

/**
 * @brief 帧间隔时间（毫秒），由 TARGET_FPS 计算得出
 * @note  用于控制 capture loop 最小延时
 */
#define FRAME_INTERVAL_MS  (1000 / TARGET_FPS)

/** @} */

// =============================================================
// 第四部分：摄像头引脚配置（AI-Thinker ESP32-CAM 默认值）
// =============================================================

/**
 * @name 摄像头引脚定义（硬件相关，一般不需要修改）
 * @note  以下为 AI-Thinker ESP32-CAM 板的标准引脚配置；
 *        其他板卡（如 WROVER-KIT / M5STACK）请参考 esp32-camera 文档
 * @{
 */

/** OV2640 摄像头引脚定义 */
#ifndef CAM_PIN_D0
#define CAM_PIN_D0   5   /**< D0 并行数据输出 */
#endif

#ifndef CAM_PIN_D1
#define CAM_PIN_D1   18  /**< D1 并行数据输出 */
#endif

#ifndef CAM_PIN_D2
#define CAM_PIN_D2   19  /**< D2 并行数据输出 */
#endif

#ifndef CAM_PIN_D3
#define CAM_PIN_D3   21  /**< D3 并行数据输出 */
#endif

#ifndef CAM_PIN_D4
#define CAM_PIN_D4   36  /**< D4 并行数据输出 */
#endif

#ifndef CAM_PIN_D5
#define CAM_PIN_D5   39  /**< D5 并行数据输出 */
#endif

#ifndef CAM_PIN_D6
#define CAM_PIN_D6   34  /**< D6 并行数据输出 */
#endif

#ifndef CAM_PIN_D7
#define CAM_PIN_D7   35  /**< D7 并行数据输出 */
#endif

#ifndef CAM_PIN_XCLK
#define CAM_PIN_XCLK 0   /**< XCLK 时钟输入 */
#endif

#ifndef CAM_PIN_PCLK
#define CAM_PIN_PCLK 22  /**< PCLK 像素时钟输出 */
#endif

#ifndef CAM_PIN_VSYNC
#define CAM_PIN_VSYNC 25 /**< VSYNC 场同步 */
#endif

#ifndef CAM_PIN_HREF
#define CAM_PIN_HREF  23 /**< HREF 行同步 */
#endif

#ifndef CAM_PIN_SSCB_SDA
#define CAM_PIN_SSCB_SDA 26 /**< SCCB（I2C）数据线 */
#endif

#ifndef CAM_PIN_SSCB_SCL
#define CAM_PIN_SSCB_SCL 27 /**< SCCB（I2C）时钟线 */
#endif

#ifndef CAM_PIN_PWDN
#define CAM_PIN_PWDN  32 /**< 电源控制引脚（低电平正常工作） */
#endif

#ifndef CAM_PIN_RESET
#define CAM_PIN_RESET -1 /**< 复位引脚（AI-Thinker 板载复位，-1 表示无需外部复位） */
#endif

/** @} */

/**
 * @name 摄像头时钟与抓取模式
 * @{
 */

/**
 * @brief XCLK 时钟频率（Hz）
 * @note  20 MHz 是稳定性和功耗的平衡点；
 *        部分场景可设为 10 MHz（更省电）或 24 MHz（更高帧率）
 *        支持的值：10MHz / 13MHz / 16MHz / 20MHz / 24MHz
 */
#ifndef CAMERA_XCLK_FREQ_HZ
#define CAMERA_XCLK_FREQ_HZ  20000000
#endif

/**
 * @brief 帧缓冲区存放位置
 * @note  PSRAM 容量大但速度略慢；无 PSRAM 时强制使用 DRAM
 *        由 psramFound() 运行时检测，此处为默认值
 */
#ifndef CAMERA_FB_LOCATION
#ifdef CONFIG_IDF_TARGET_ESP32
#define CAMERA_FB_LOCATION  CAMERA_FB_IN_PSRAM
#else
#define CAMERA_FB_LOCATION  CAMERA_FB_IN_DRAM
#endif
#endif

/**
 * @brief 帧抓取模式
 * @note  CAMERA_GRAB_WHEN_EMPTY = 空时抓取（推荐，避免帧撕裂）
 *        CAMERA_GRAB_LATEST     = 始终抓取最新帧（可能导致丢弃旧帧）
 */
#ifndef CAMERA_GRAB_MODE
#define CAMERA_GRAB_MODE  CAMERA_GRAB_WHEN_EMPTY
#endif

/** @} */

// =============================================================
// 第五部分：摄像头传感器参数（ISP 调优）
// =============================================================

/**
 * @name 传感器图像调优参数
 * @note  以下为默认值，可通过 web UI 或 API 动态调整
 * @{
 */

/**
 * @brief 亮度调整
 * @note  范围 -2 到 +2，默认 0
 */
#ifndef SENSOR_BRIGHTNESS
#define SENSOR_BRIGHTNESS  0
#endif

/**
 * @brief 对比度调整
 * @note  范围 -2 到 +2，默认 0
 */
#ifndef SENSOR_CONTRAST
#define SENSOR_CONTRAST  0
#endif

/**
 * @brief 饱和度调整
 * @note  范围 -2 到 +2，默认 0
 */
#ifndef SENSOR_SATURATION
#define SENSOR_SATURATION  0
#endif

/**
 * @brief 垂直翻转
 * @note  根据摄像头安装方向设置：正常安装设为 1，倒装设为 0
 */
#ifndef SENSOR_VFLIP
#define SENSOR_VFLIP  1
#endif

/**
 * @brief 水平镜像
 * @note  根据摄像头安装方向设置：镜像显示时设为 1
 */
#ifndef SENSOR_HMIRROR
#define SENSOR_HMIRROR  0
#endif

/**
 * @brief 自动白平衡启用开关
 * @note  1 = 启用（推荐），0 = 禁用
 */
#ifndef SENSOR_AWB
#define SENSOR_AWB  1
#endif

/**
 * @brief 自动白平衡增益
 * @note  1 = 启用 AWB 增益，0 = 禁用
 */
#ifndef SENSOR_AWB_GAIN
#define SENSOR_AWB_GAIN  1
#endif

/**
 * @brief 白平衡模式
 * @note  0 = 自动，1 = 晴天，2 = 阴天，3 = 办公室，4 = 家中
 */
#ifndef SENSOR_WB_MODE
#define SENSOR_WB_MODE  0
#endif

/**
 * @brief 自动曝光控制
 * @note  1 = 启用（推荐），0 = 禁用
 */
#ifndef SENSOR_AEC
#define SENSOR_AEC  1
#endif

/**
 * @brief AEC2 算法
 * @note  0 = 禁用（推荐），1 = 启用
 */
#ifndef SENSOR_AEC2
#define SENSOR_AEC2  0
#endif

/**
 * @brief AGC（自动增益控制）
 * @note  0 = 禁用（使用自动曝光），1-30 = 固定增益倍数
 */
#ifndef SENSOR_AGC_GAIN
#define SENSOR_AGC_GAIN  0
#endif

/**
 * @brief 增益上限
 * @note  可选：GAINCEILING_1X / GAINCEILING_2X / GAINCEILING_4X /
 *        GAINCEILING_8X / GAINCEILING_16X / GAINCEILING_32X /
 *        GAINCEILING_64X / GAINCEILING_128X
 */
#ifndef SENSOR_GAINCEILING
#define SENSOR_GAINCEILING  GAINCEILING_2X
#endif

/** @} */

// =============================================================
// 第六部分：FreeRTOS 任务配置
// =============================================================

/**
 * @name 摄像头采集任务配置
 * @{
 */

/**
 * @brief 摄像头任务栈大小（字节）
 * @note  默认 4096；启用 PSRAM 高分辨率时建议 8192
 */
#ifndef CAMERA_TASK_STACK_SIZE
#define CAMERA_TASK_STACK_SIZE  4096
#endif

/**
 * @brief 摄像头任务优先级
 * @note  应高于空闲优先级，建议 1-3
 */
#ifndef CAMERA_TASK_PRIORITY
#define CAMERA_TASK_PRIORITY  1
#endif

/**
 * @brief 摄像头任务绑定核心
 * @note  0 或 1；设为 -1 则不绑定（系统自动调度）
 */
#ifndef CAMERA_TASK_CORE
#define CAMERA_TASK_CORE  0
#endif

/** @} */

// =============================================================
// 第七部分：系统与调试配置
// =============================================================

/**
 * @name 系统配置
 * @{
 */

/**
 * @brief FreeRTOS 时钟 tick 频率（Hz）
 * @note  默认 1000（1ms tick）；设为 100 可降低功耗但定时精度下降
 */
#ifndef CONFIG_FREERTOS_HZ
#define CONFIG_FREERTOS_HZ  1000
#endif

/**
 * @brief WiFi 省电模式
 * @note  true  = 启用 WiFi 省电（省电但可能增加延迟）
 *        false = 禁用省电（推荐，低延迟）
 */
#ifndef WIFI_NO_SLEEP
#define WIFI_NO_SLEEP  true
#endif

/**
 * @brief 看门狗定时器超时（毫秒）
 * @note  设为 0 禁用；建议 5000-30000
 */
#ifndef WDT_TIMEOUT_MS
#define WDT_TIMEOUT_MS  10000
#endif

/** @} */

/**
 * @name 调试日志配置
 * @{
 */

/**
 * @brief 串口波特率
 * @note  默认 115200；调试时可选 921600
 */
#ifndef SERIAL_BAUD_RATE
#define SERIAL_BAUD_RATE  115200
#endif

/**
 * @brief 是否打印首次帧的 JPEG 头部字节（十六进制）
 * @note  用于调试 JPEG 流是否正常；正常运行时建议关闭
 */
#ifndef DEBUG_PRINT_FIRST_JPEG_BYTES
#define DEBUG_PRINT_FIRST_JPEG_BYTES  0
#endif

/**
 * @brief 是否打印详细摄像头配置信息
 * @note  摄像头初始化完成后打印详细信息
 */
#ifndef DEBUG_PRINT_CAMERA_CONFIG
#define DEBUG_PRINT_CAMERA_CONFIG  1
#endif

/**
 * @brief WiFi 状态打印间隔（毫秒）
 * @note  设为 0 禁用定期打印；设为正数则每 N 毫秒打印一次
 */
#ifndef DEBUG_WIFI_STATUS_INTERVAL_MS
#define DEBUG_WIFI_STATUS_INTERVAL_MS  10000
#endif

/** @} */

// =============================================================
// 第八部分：宏辅助函数
// =============================================================

/**
 * @brief 计算缓冲区是否能容纳一帧 JPEG
 * @param buf_size 缓冲区大小（字节）
 * @param jpeg_len 预估 JPEG 长度（字节）
 * @return 1=足够，0=不足
 */
#define JPEG_BUFFER_OK(buf_size, jpeg_len)  ((buf_size) >= (jpeg_len))

/**
 * @brief 静态断言：确保配置组合有效
 * @note  编译时检查，防止无效配置组合
 */
#define CONFIG_STATIC_ASSERT(msg, expr)  typedef char static_assert_##msg[(expr) ? 1 : -1]

/* PSRAM 与分辨率一致性检查 */
#ifdef CONFIG_IDF_TARGET_ESP32
#if defined(FRAMESIZE_UXGA) || defined(FRAMESIZE_SXGA) || defined(FRAMESIZE_HD)
#if !defined(CONFIG_IDF_TARGET_ESP32) || !psramFound()
/* 高分辨率无 PSRAM 时发出警告 */
#warning "高分辨率建议配合 PSRAM 使用，否则可能导致内存不足"
#endif
#endif
#endif

#endif // CONFIG_H
