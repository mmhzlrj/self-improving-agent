/**
 * RTSP.h - ESP32-CAM RTSP 流媒体服务器头文件
 *
 * 提供与 airjournals/ESP32-RTSP 库兼容的接口
 * 实际实现位于 rtsp_server.cpp
 *
 * 使用方法：
 *   #include <RTSP.h>
 *   RTSP rtspServer;
 *   rtspServer.begin(8554);
 *   rtspServer.stream(jpegBuf, jpegLen);
 *   rtspServer.handleLoop();
 */

#ifndef RTSP_H
#define RTSP_H

#include <Arduino.h>

/**
 * RTSP 类
 *
 * 简单的 RTSP 服务器接口，用于 main.cpp 中控制 RTSP 流
 *
 * 公开方法：
 *   - begin(port)     启动 RTSP 服务器
 *   - stop()          停止 RTSP 服务器
 *   - stream(buf,len) 发送一帧（JPEG）到所有已连接客户端
 *   - handleLoop()    处理客户端连接（主循环中调用）
 *   - isRunning()     检查服务器是否运行中
 */
class RTSP {
public:
    RTSP();
    ~RTSP();

    /**
     * 启动 RTSP 服务器
     * @param port RTSP 端口，默认 8554
     * @return true=启动成功，false=启动失败
     */
    bool begin(uint16_t port = 8554);

    /**
     * 停止 RTSP 服务器
     */
    void stop();

    /**
     * 发送一帧到所有已连接的 RTSP 客户端
     * @param buf JPEG 帧数据缓冲区
     * @param len 帧数据长度
     */
    void stream(const uint8_t* buf, size_t len);

    /**
     * 处理服务器主循环
     * 在 loop() 中定期调用，接受新连接、处理请求
     */
    void handleLoop();

    /**
     * 检查服务器是否正在运行
     * @return true=运行中
     */
    bool isRunning() const;

private:
    void* _server;  // 内部实现指针（实际类型为 RTSPServer*）
};

#endif // RTSP_H
