/**
 * @file led_status.h
 * @brief ESP32-CAM LED 状态指示器 - 头文件
 *
 * 通过板载 LED 指示系统运行状态：
 *   - WiFi 连接状态
 *   - 摄像头工作状态
 *   - RTSP 流媒体状态
 *   - 错误指示
 *
 * 适配板卡：AI-Thinker ESP32-CAM (LED GPIO 33, active-LOW)
 *
 * 使用方法：
 *   #include "led_status.h"
 *   led_init();
 *   led_set_state(LED_WIFI_CONNECTING);
 *   led_update();  // 在 loop() 中定期调用
 */

#ifndef LED_STATUS_H
#define LED_STATUS_H

#include <Arduino.h>

// ======================== LED 硬件配置 ========================

/**
 * LED GPIO 引脚 (AI-Thinker ESP32-CAM)
 * - 蓝色 LED，active-LOW（低电平点亮）
 * - 部分板卡可能是 active-HIGH，请根据实际情况修改
 */
#ifndef LED_GPIO
#define LED_GPIO          33
#endif

/** LED 逻辑电平：true = 高电平熄灭, false = 低电平点亮 */
#ifndef LED_ACTIVE_LOW
#define LED_ACTIVE_LOW    true
#endif

// ======================== LED 状态枚举 ========================

/**
 * @brief LED 状态机
 *
 * 各状态的闪烁模式：
 *   LED_OFF           - 熄灭（系统空闲/关机）
 *   LED_WIFI_CONNECTING - 慢闪 (500ms 周期)：正在连接 WiFi
 *   LED_WIFI_OK       - 双闪 (200ms x2)：WiFi 已连接
 *   LED_CAMERA_ERROR  - 快闪 (100ms 周期)：摄像头错误
 *   LED_STREAMING     - 常亮：正在推流
 *   LED_RTSP_ERROR    - 三闪 (200ms x3)：RTSP 服务器错误
 *   LED_WIFI_ERROR    - 长闪 (1000ms 灭)：WiFi 连接失败
 */
typedef enum {
    LED_OFF               = 0,
    LED_WIFI_CONNECTING   = 1,
    LED_WIFI_OK           = 2,
    LED_CAMERA_ERROR      = 3,
    LED_STREAMING         = 4,
    LED_RTSP_ERROR        = 5,
    LED_WIFI_ERROR        = 6,
} led_state_t;

// ======================== 公开函数接口 ========================

/**
 * @brief 初始化 LED GPIO
 *
 * @return true=成功, false=失败（GPIO 配置错误）
 */
bool led_init(void);

/**
 * @brief 释放 LED 资源
 */
void led_deinit(void);

/**
 * @brief 设置 LED 状态
 *
 * @param state 目标状态（见 led_state_t）
 *
 * @note 状态切换立即生效，但闪烁模式在 led_update() 驱动下运行
 */
void led_set_state(led_state_t state);

/**
 * @brief 获取当前 LED 状态
 * @return 当前状态
 */
led_state_t led_get_state(void);

/**
 * @brief 更新 LED 状态（需在 loop() 中定期调用）
 *
 * 内部实现状态机，根据当前状态和 elapsed 时间自动控制 GPIO 电平。
 * 建议调用周期：50-100ms
 *
 * @note 此函数为阻塞安全，可在任何任务中调用
 */
void led_update(void);

/**
 * @brief 执行一次 LED 硬件测试（启动时调用）
 *
 * 依次点亮、熄灭、闪烁，验证 LED 硬件是否正常工作。
 * 测试完成后恢复为 LED_OFF 状态。
 *
 * @param on_ms    点亮时长 (ms)
 * @param off_ms   熄灭时长 (ms)
 * @param cycles   闪烁次数
 */
void led_self_test(uint32_t on_ms, uint32_t off_ms, uint8_t cycles);

#endif // LED_STATUS_H
