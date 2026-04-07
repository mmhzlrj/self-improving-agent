/**
 * @file led_status.cpp
 * @brief ESP32-CAM LED 状态指示器 - 实现文件
 *
 * 状态机驱动的 LED 控制，实现不同的闪烁模式：
 *
 * | 状态                  | 模式                | 含义                     |
 * |----------------------|---------------------|--------------------------|
 * | LED_OFF              | 熄灭                | 系统空闲/待机              |
 * | LED_WIFI_CONNECTING  | 500ms 周期慢闪        | 正在连接 WiFi             |
 * | LED_WIFI_OK          | 双闪 (200ms x2)      | WiFi 连接成功              |
 * | LED_CAMERA_ERROR     | 100ms 周期快闪        | 摄像头初始化失败            |
 * | LED_STREAMING        | 常亮                 | RTSP 正在推流              |
 * | LED_RTSP_ERROR       | 三闪 (200ms x3)      | RTSP 服务器错误            |
 * | LED_WIFI_ERROR       | 长闪 (1000ms 灭)     | WiFi 连接失败              |
 *
 * 作者：ESP32-CAM-RTSP 项目
 * 平台：PlatformIO / Arduino ESP32
 */

#include "led_status.h"

// ======================== 内部常量 ========================

/** 状态切换检测容差（ms），避免抖动 */
#define STATE_CHANGE_DEBOUNCE_MS   50

/** 各状态的时间参数（ms） */
#define BLINK_FAST_MS          100   // 快闪周期（亮+灭）
#define BLINK_NORMAL_MS         200   // 正常闪周期
#define BLINK_SLOW_MS           500   // 慢闪周期
#define BLINK_LONG_MS           1000  // 长闪周期

// ======================== 内部状态 ========================

/** LED 状态机当前状态 */
static led_state_t s_current_state = LED_OFF;

/** LED 上一次更新时间（millis()） */
static uint32_t s_last_update_ms = 0;

/** 当前闪烁周期内经过的时间（ms） */
static uint32_t s_blink_elapsed_ms = 0;

/** 双闪/三闪的子状态计数器 */
static uint8_t  s_flash_count = 0;

/** GPIO 初始化标记 */
static bool s_gpio_initialized = false;

/** 上一次 LED 输出的逻辑电平（true=亮, false=灭）*/
static bool s_led_on = false;

// ======================== 内部函数声明 ========================

/**
 * @brief 写入 LED 硬件电平（处理 active-low 逻辑）
 * @param on true=点亮 LED, false=熄灭 LED
 */
static void led_hw_write(bool on);

/**
 * @brief 根据当前状态和经过时间，计算 LED 应该点亮还是熄灭
 * @param state  当前状态
 * @param elapsed 已过去的毫秒数
 * @return true=点亮, false=熄灭
 */
static bool led_compute_output(led_state_t state, uint32_t elapsed);

// ======================== 公开函数实现 ========================

bool led_init(void) {
    // 参数检查
    if (LED_GPIO < 0 || LED_GPIO > 255) {
        Serial.printf("[LED] 错误：无效 GPIO %d\n", LED_GPIO);
        return false;
    }

    // 配置 GPIO 为输出模式
    bool ok = gpio_init(LED_GPIO, GPIO_MODE_OUTPUT);
    if (!ok) {
        Serial.printf("[LED] 错误：GPIO %d 初始化失败\n", LED_GPIO);
        return false;
    }

    // 默认关闭 LED（避免上电瞬间闪烁）
    led_hw_write(false);
    s_gpio_initialized = true;
    s_last_update_ms = millis();

    Serial.printf("[LED] 初始化完成，GPIO=%d, active-low=%d\n",
                  LED_GPIO, LED_ACTIVE_LOW);
    return true;
}

void led_deinit(void) {
    if (!s_gpio_initialized) {
        return;
    }

    // 熄灭 LED 并释放 GPIO
    led_hw_write(false);
    gpio_deinit(LED_GPIO);
    s_gpio_initialized = false;
    s_current_state = LED_OFF;

    Serial.println("[LED] 已关闭");
}

void led_set_state(led_state_t state) {
    if (s_current_state == state) {
        return;  // 状态未变，跳过
    }

    // 状态切换时重置闪烁计数器
    if (s_current_state != state) {
        s_flash_count = 0;
        s_blink_elapsed_ms = 0;
    }

    s_current_state = state;
    s_last_update_ms = millis();

    // 立即输出一次，避免响应延迟
    bool on = led_compute_output(state, 0);
    led_hw_write(on);

    Serial.printf("[LED] 状态切换 -> %d\n", state);
}

led_state_t led_get_state(void) {
    return s_current_state;
}

void led_update(void) {
    if (!s_gpio_initialized) {
        return;
    }

    uint32_t now = millis();

    // 计算时间增量（处理 millis() 溢出，每 49.7 天发生一次）
    uint32_t elapsed;
    if (now >= s_last_update_ms) {
        elapsed = now - s_last_update_ms;
    } else {
        elapsed = (0xFFFFFFFFU - s_last_update_ms) + now + 1;
    }

    // 避免在长时间阻塞后（如暂停任务）产生错误的长时间闪烁
    if (elapsed > 5000) {
        elapsed = 50;
    }

    s_last_update_ms = now;
    s_blink_elapsed_ms += elapsed;

    // 根据状态计算当前 LED 亮灭
    bool on = led_compute_output(s_current_state, s_blink_elapsed_ms);

    // 仅在电平变化时才写入 GPIO，减少总线开销
    if (on != s_led_on) {
        led_hw_write(on);
        s_led_on = on;
    }
}

void led_self_test(uint32_t on_ms, uint32_t off_ms, uint8_t cycles) {
    if (!s_gpio_initialized) {
        Serial.println("[LED] 错误：未初始化，无法执行自检");
        return;
    }

    Serial.printf("[LED] 自检开始: %u ms on, %u ms off, %u cycles\n",
                  on_ms, off_ms, cycles);

    for (uint8_t i = 0; i < cycles; i++) {
        led_hw_write(true);
        delay(on_ms);
        led_hw_write(false);
        delay(off_ms);
    }

    Serial.println("[LED] 自检完成");
}

// ======================== 内部函数实现 ========================

static void led_hw_write(bool on) {
#if LED_ACTIVE_LOW
    digitalWrite(LED_GPIO, on ? LOW : HIGH);
#else
    digitalWrite(LED_GPIO, on ? HIGH : LOW);
#endif
}

static bool led_compute_output(led_state_t state, uint32_t elapsed) {
    switch (state) {

        case LED_OFF:
            // 熄灭
            return false;

        case LED_WIFI_CONNECTING:
            // 慢闪：500ms 周期
            //   亮 250ms，灭 250ms
            return (elapsed % BLINK_SLOW_MS) < (BLINK_SLOW_MS / 2);

        case LED_WIFI_OK:
            // 双闪：200ms x2，然后灭 600ms
            // 一个完整周期 = 200*2 + 600 = 1000ms
            {
                const uint32_t period = BLINK_NORMAL_MS * 2 + 600;
                uint32_t pos = elapsed % period;

                if (pos < BLINK_NORMAL_MS) {
                    // 第一闪：亮 200ms
                    return true;
                } else if (pos < BLINK_NORMAL_MS * 2) {
                    // 第二闪：亮 200ms
                    return true;
                } else {
                    // 灭 600ms
                    return false;
                }
            }

        case LED_CAMERA_ERROR:
            // 快闪：100ms 周期
            //   亮 50ms，灭 50ms
            return (elapsed % BLINK_FAST_MS) < (BLINK_FAST_MS / 2);

        case LED_STREAMING:
            // 常亮：正在推流
            return true;

        case LED_RTSP_ERROR:
            // 三闪：200ms x3，然后灭 400ms
            // 一个完整周期 = 200*3 + 400 = 1000ms
            {
                const uint32_t period = BLINK_NORMAL_MS * 3 + 400;
                uint32_t pos = elapsed % period;

                if (pos < BLINK_NORMAL_MS) {
                    return true;   // 第一闪
                } else if (pos < BLINK_NORMAL_MS * 2) {
                    return true;   // 第二闪
                } else if (pos < BLINK_NORMAL_MS * 3) {
                    return true;   // 第三闪
                } else {
                    return false;  // 灭 400ms
                }
            }

        case LED_WIFI_ERROR:
            // 长闪：1000ms 灭 + 亮（一次长闪烁）
            //   亮 200ms，灭 800ms
            return (elapsed % BLINK_LONG_MS) >= (BLINK_LONG_MS - 200);

        default:
            return false;
    }
}
