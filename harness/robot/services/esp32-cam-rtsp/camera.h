/**
 * @file camera.h
 * @brief ESP32-CAM Camera Driver - 公共接口头文件
 */

#ifndef CAMERA_H
#define CAMERA_H

#include <stdint.h>
#include <stddef.h>
#include <string.h>

// ESP32 / Arduino headers
#include "esp_system.h"
#include "esp_camera.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

// ======================== 分辨率查表 ========================

/**
 * @brief 分辨率查表 (framesize_t -> width/height)
 * 由 esp32-camera 库提供, 此处声明供查表使用
 */
extern const resolution_info_t resolution[];

// ======================== 公开函数接口 ========================

/**
 * @brief 初始化摄像头
 * 
 * @param frame_size    帧分辨率, 如 FRAMESIZE_SVGA (800x600)
 * @param jpeg_quality  JPEG 质量 10-63, 值越小质量越好
 * @return int  0=成功, 负值=错误
 */
int camera_init(framesize_t frame_size, uint8_t jpeg_quality);

/**
 * @brief 释放摄像头资源
 */
void camera_deinit(void);

/**
 * @brief 捕获一帧 JPEG 图像
 * 
 * @param fb_out  输出参数, 指向捕获的帧缓冲
 * @return int    0=成功, 负值=错误码
 * 
 * @note 返回的 fb 需调用 camera_return_frame() 释放
 */
int camera_capture_jpeg(camera_fb_t** fb_out);

/**
 * @brief 释放帧缓冲 (归还给摄像头驱动)
 * 
 * @param fb 帧缓冲指针 (由 camera_capture_jpeg 获取)
 */
void camera_return_frame(camera_fb_t* fb);

/**
 * @brief 捕获并拷贝一帧 JPEG 到指定缓冲区
 * 
 * @param dest     目标缓冲区
 * @param dest_len 目标缓冲区大小
 * @return ssize_t 实际拷贝的字节数, -1=失败
 * 
 * @note 此函数自动管理 FB 生命周期, 调用方无需手动释放
 */
ssize_t camera_capture_and_copy(uint8_t* dest, size_t dest_len);

/**
 * @brief 获取当前帧宽度
 */
int camera_get_width(void);

/**
 * @brief 获取当前帧高度
 */
int camera_get_height(void);

/**
 * @brief 检查摄像头是否已初始化
 */
bool camera_is_initialized(void);

/**
 * @brief 打印当前摄像头配置 (用于调试)
 */
void camera_print_config(void);

// ======================== 调试开关 ========================

#define CAMERA_DEBUG_PRINT_FIRST_BYTES  0   // 打印 JPEG 头部字节

#endif // CAMERA_H
