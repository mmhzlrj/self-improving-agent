/**
 * rtsp_server.cpp - ESP32-CAM RTSP 流媒体服务器实现
 *
 * 功能：实现标准 RTSP 协议的流媒体服务器，支持 VLC / FFplay 等客户端拉流
 * 协议：RTSP 1.0 over TCP (interleaved RTP over RTSP)
 * 视频：MJPEG over RTP
 *
 * 编译平台：PlatformIO / Arduino ESP32
 * 依赖：WiFi.h, esp_camera.h (由 main.cpp 引入)
 */

#include <Arduino.h>
#include <WiFi.h>
#include <esp_camera.h>
#include "RTSP.h"

// ============================================================
// 宏定义
// ============================================================
#define RTSP_BUFFER_SIZE     2048   // RTSP 请求缓冲区大小
#define RTP_MAX_PACKET_SIZE  1400   // RTP 包最大大小 (MTU 1500 - RTP头 12 - IP头 20 - TCP头 20 ≈ 1448)
#define RTP_HEADER_SIZE      12     // RTP 固定头大小
#define RTSP_SESSION_TIMEOUT 60     // Session 超时时间（秒）
#define MAX_CLIENTS          4      // 最大并发客户端数

// ============================================================
// RTP 宏
// ============================================================
#define RTP_VERSION          2
#define RTP_PAYLOAD_TYPE_MJPEG 26  // MJPEG payload type
#define RTP_MARKER_BIT       0x80   // RTP Marker Bit

// ============================================================
// 类型定义
// ============================================================

/**
 * RTP 包结构
 * 0                   1                   2                   3
 * 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
 * +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 * |V=2|P|X|  CC   |M|     PT      |       sequence number         |
 * +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 * |                           timestamp                           |
 * +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 * |           synchronization source (SSRC) identifier            |
 * +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 * |            contributing source (CSRC) identifiers             |
 * +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 * |                          payload ...                          |
 * +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 */

/**
 * RTP 包信息结构
 */
typedef struct {
    uint8_t  version;    // RTP 版本 (2)
    uint8_t  padding;    // 填充标志
    uint8_t  extension; // 扩展标志
    uint8_t  csrcCount; // CSRC 计数器
    uint8_t  marker;    // 标记位
    uint8_t  payloadType; // 载荷类型
    uint16_t seqNum;    // 序列号
    uint32_t timestamp; // 时间戳
    uint32_t ssrc;      // 同步源标识符
} rtp_header_t;

// ============================================================
// 客户端状态
// ============================================================
typedef enum {
    RTSP_CLIENT_IDLE,       // 初始状态
    RTSP_CLIENT_OPTIONS,    // 已处理 OPTIONS
    RTSP_CLIENT_DESCRIBE,   // 已处理 DESCRIBE
    RTSP_CLIENT_SETUP,      // 已处理 SETUP
    RTSP_CLIENT_PLAYING,   // 正在播放
    RTSP_CLIENT_TEARDOWN    // 已断开
} rtsp_client_state_t;

/**
 * 单个 RTSP 客户端连接结构
 */
typedef struct {
    WiFiClient* client;           // TCP 连接
    rtsp_client_state_t state;    // 客户端状态
    uint32_t sessionId;           // RTSP Session ID
    uint16_t clientRtpPort;       // 客户端 RTP 端口 (RTP over UDP 时使用)
    uint16_t clientRtcpPort;      // 客户端 RTCP 端口
    bool isTcp;                   // true=TCP(interleaved), false=UDP
    uint8_t  rtpChannel;          // RTP interleaved channel (0)
    uint8_t  rtcpChannel;         // RTCP interleaved channel (1)
    uint16_t rtpSeq;              // RTP 序列号
    uint32_t rtpTimestamp;        // RTP 时间戳
    uint32_t lastActivity;         // 最后活跃时间（毫秒）
    uint8_t  ssrc[4];             // SSRC 标识符
} rtsp_client_t;

// ============================================================
// 类声明
// ============================================================

/**
 * RTSPServer 类 - RTSP 流媒体服务器
 *
 * 使用 TCP interleaved 模式传输 RTP 包，兼容 VLC / FFplay
 */
class RTSPServer {
public:
    /**
     * 构造函数
     */
    RTSPServer();

    /**
     * 析构函数
     */
    ~RTSPServer();

    /**
     * 启动 RTSP 服务器
     * @param port RTSP 端口，默认 8554
     * @return true=成功，false=失败
     */
    bool begin(uint16_t port = 8554);

    /**
     * 停止 RTSP 服务器
     */
    void stop();

    /**
     * 流发送一帧数据（推送到所有已连接的客户端）
     * @param buf 帧数据缓冲区 (JPEG)
     * @param len 帧数据长度
     */
    void stream(const uint8_t* buf, size_t len);

    /**
     * 处理服务器主循环（在 loop() 中调用）
     * 接受新连接、处理请求、发送数据
     */
    void handleLoop();

    /**
     * 检查服务器是否运行中
     * @return true=运行中
     */
    bool isRunning() const { return _server != nullptr && _server->available() >= 0; }

    /**
     * 获取当前连接的客户端数量
     * @return 客户端数
     */
    int connectedClients();

private:
    // ============================================================
    // 私有成员变量
    // ============================================================
    WiFiServer*        _server;       // TCP 服务器
    uint16_t           _port;         // RTSP 端口
    rtsp_client_t      _clients[MAX_CLIENTS]; // 客户端数组
    uint8_t            _rtpBuffer[RTP_MAX_PACKET_SIZE]; // RTP 发送缓冲区
    uint32_t           _frameTimestamp; // 帧时间戳（90kHz 时钟）
    uint32_t           _lastFrameTime;   // 上一帧时间（毫秒）
    bool               _running;         // 运行状态

    // SDP 描述信息
    String             _sdp;

    // ============================================================
    // 私有方法
    // ============================================================

    /**
     * 生成随机 Session ID
     */
    uint32_t generateSessionId();

    /**
     * 生成随机 SSRC
     */
    void generateSSRC(uint8_t* ssrc);

    /**
     * 构建 SDP 描述信息
     * @param width 视频宽度
     * @param height 视频高度
     * @return SDP 字符串
     */
    String buildSDP(int width, int height);

    /**
     * 处理单个 RTSP 请求
     * @param client 客户端连接
     * @return true=继续处理，false=客户端断开
     */
    bool handleClient(WiFiClient* client);

    /**
     * 解析 RTSP 请求行
     * @param buffer 请求数据
     * @param len 数据长度
     * @param method 输出：方法名
     * @param url 输出：URL 路径
     * @param cseq 输出：CSeq 序号
     * @param session 输出：Session ID（若有）
     * @param transport 输出：Transport 头（若有）
     * @return true=解析成功
     */
    bool parseRequest(const char* buffer, size_t len,
                      String& method, String& url, int& cseq,
                      String& session, String& transport);

    /**
     * 发送 RTSP 响应
     * @param client 客户端连接
     * @param statusCode 状态码（如 200, 404, 400）
     * @param statusMsg 状态消息
     * @param cseq CSeq（必须与请求一致）
     * @param session Session ID（可选）
     * @param extraHeaders 额外响应头（可选）
     * @param body 响应体（可选，如 SDP）
     */
    void sendResponse(WiFiClient* client, int statusCode, const char* statusMsg,
                      int cseq, const char* session = nullptr,
                      const char* extraHeaders = nullptr,
                      const char* body = nullptr);

    /**
     * 通过 RTP over TCP (interleaved) 发送一帧
     * @param client 客户端连接
     * @param buf JPEG 数据
     * @param len 数据长度
     * @param timestamp 时间戳
     */
    void sendFrameOverTcp(int clientIdx, WiFiClient* client, const uint8_t* buf, size_t len, uint32_t timestamp);

    /**
     * 打包并发送单个 RTP 包（TCP interleaved）
     * @param client 客户端连接
     * @param payload 载荷数据
     * @param payloadLen 载荷长度
     * @param timestamp 时间戳
     * @param marker Marker 位
     */
    void sendRtpPacket(int clientIdx, WiFiClient* client, const uint8_t* payload,
                       size_t payloadLen, uint32_t timestamp, bool marker);

    /**
     * 清理超时客户端
     */
    void cleanupClients();

    /**
     * 查找空闲客户端槽位
     * @return 槽位索引，-1=无空闲
     */
    int findFreeClientSlot();

    /**
     * 根据 Session ID 查找客户端
     * @param sessionId Session ID
     * @return 客户端索引，-1=未找到
     */
    int findClientBySession(uint32_t sessionId);
};

// ============================================================
// RTSP 类实现（兼容 main.cpp 的 RTSP 接口）
// ============================================================

/**
 * 全局 RTSP 服务器实例（main.cpp 中声明）
 */
static RTSPServer g_rtspServerInstance;

/**
 * RTSP 类 - 封装 RTSPServer 的简单接口
 *
 * 此类作为 main.cpp 中 `RTSP rtspServer` 的实际类型
 * 提供了与 airjournals/ESP32-RTSP 库兼容的接口
 */
class RTSP {
public:
    /**
     * 构造函数
     */
    RTSP() : _server(nullptr) {}

    /**
     * 启动 RTSP 服务器
     * @param port RTSP 端口
     * @return true=成功
     */
    bool begin(uint16_t port = 8554) {
        if (_server != nullptr) {
            delete _server;
        }
        _server = new RTSPServer();
        bool ok = _server->begin(port);
        if (!ok) {
            delete _server;
            _server = nullptr;
        }
        return ok;
    }

    /**
     * 停止 RTSP 服务器
     */
    void stop() {
        if (_server != nullptr) {
            _server->stop();
            delete _server;
            _server = nullptr;
        }
    }

    /**
     * 流发送一帧
     * @param buf 帧数据
     * @param len 帧长度
     */
    void stream(const uint8_t* buf, size_t len) {
        if (_server != nullptr) {
            _server->stream(buf, len);
        }
    }

    /**
     * 处理服务器循环
     */
    void handleLoop() {
        if (_server != nullptr) {
            _server->handleLoop();
        }
    }

    /**
     * 检查是否运行
     */
    bool isRunning() const {
        return _server != nullptr && _server->isRunning();
    }

private:
    RTSPServer* _server;
};

// ============================================================
// RTSPServer 方法实现
// ============================================================

/**
 * 构造函数
 */
RTSPServer::RTSPServer()
    : _server(nullptr)
    , _port(8554)
    , _running(false)
    , _frameTimestamp(0)
    , _lastFrameTime(0)
{
    memset(_clients, 0, sizeof(_clients));
    memset(_rtpBuffer, 0, sizeof(_rtpBuffer));

    // 生成固定 SSRC（实际应用建议随机生成）
    _rtpBuffer[8] = 0x12;
    _rtpBuffer[9] = 0x34;
    _rtpBuffer[10] = 0x56;
    _rtpBuffer[11] = 0x78;
}

/**
 * 析构函数
 */
RTSPServer::~RTSPServer() {
    stop();
}

/**
 * 启动 RTSP 服务器
 */
bool RTSPServer::begin(uint16_t port) {
    _port = port;

    // 创建 TCP 服务器
    _server = new WiFiServer(_port);
    if (_server == nullptr) {
        Serial.println("[RTSPServer] 错误：内存分配失败（WiFiServer）");
        return false;
    }

    // 启动监听
    _server->begin();
    _running = true;

    Serial.printf("[RTSPServer] RTSP 服务器启动，端口: %d\n", _port);

    // 初始化 SDP
    _sdp = buildSDP(800, 600);

    // 初始化客户端状态
    for (int i = 0; i < MAX_CLIENTS; i++) {
        _clients[i].state = RTSP_CLIENT_IDLE;
        _clients[i].client = nullptr;
        _clients[i].sessionId = 0;
    }

    return true;
}

/**
 * 停止 RTSP 服务器
 */
void RTSPServer::stop() {
    _running = false;

    // 关闭所有客户端连接
    for (int i = 0; i < MAX_CLIENTS; i++) {
        if (_clients[i].client != nullptr) {
            _clients[i].client->stop();
            delete _clients[i].client;
            _clients[i].client = nullptr;
            _clients[i].state = RTSP_CLIENT_IDLE;
        }
    }

    // 关闭服务器
    if (_server != nullptr) {
        _server->stop();
        delete _server;
        _server = nullptr;
    }

    Serial.println("[RTSPServer] 服务器已停止");
}

/**
 * 发送一帧到所有已连接的客户端
 */
void RTSPServer::stream(const uint8_t* buf, size_t len) {
    if (!_running || buf == nullptr || len == 0) {
        return;
    }

    // 计算帧时间戳（90kHz 时钟）
    // MJPEG 典型帧率 25fps，每帧时间增量 = 90000/25 = 3600
    uint32_t now = millis();
    uint32_t elapsed = now - _lastFrameTime;
    if (elapsed == 0) elapsed = 40; // 避免 0
    _frameTimestamp += (elapsed * 90); // 毫秒转 90kHz 单位
    _lastFrameTime = now;

    // 遍历所有客户端，发送帧
    for (int i = 0; i < MAX_CLIENTS; i++) {
        if (_clients[i].client == nullptr ||
            _clients[i].state != RTSP_CLIENT_PLAYING) {
            continue;
        }

        // 检查连接是否仍然有效
        if (!_clients[i].client->connected()) {
            Serial.printf("[RTSPServer] 客户端 %d 连接断开，清理中...\n", i);
            _clients[i].client->stop();
            delete _clients[i].client;
            _clients[i].client = nullptr;
            _clients[i].state = RTSP_CLIENT_IDLE;
            continue;
        }

        // 发送帧
        if (_clients[i].isTcp) {
            sendFrameOverTcp(i, _clients[i].client, buf, len, _frameTimestamp);
        }
        // UDP 模式暂未实现（需要客户端 UDP 端口信息）
    }
}

/**
 * 服务器主循环
 */
void RTSPServer::handleLoop() {
    if (!_running || _server == nullptr) {
        return;
    }

    // 1. 接受新客户端连接
    WiFiClient newClient = _server->available();
    if (newClient) {
        int slot = findFreeClientSlot();
        if (slot >= 0) {
            _clients[slot].client = new WiFiClient(newClient);
            _clients[slot].state = RTSP_CLIENT_OPTIONS;
            _clients[slot].sessionId = generateSessionId();
            _clients[slot].rtpSeq = static_cast<uint16_t>(random(0, 65536));
            _clients[slot].lastActivity = millis();
            _clients[slot].isTcp = true; // 默认 TCP 模式
            _clients[slot].rtpChannel = 0;
            _clients[slot].rtcpChannel = 1;
            generateSSRC(_clients[slot].ssrc);
            Serial.printf("[RTSPServer] 新客户端连接 #%d，IP: %s\n",
                          slot,
                          _clients[slot].client->remoteIP().toString().c_str());
        } else {
            // 无空闲槽位，拒绝连接
            newClient.print("RTSP/1.0 503 Service Unavailable\r\n\r\n");
            newClient.stop();
            Serial.println("[RTSPServer] 拒绝连接：客户端已满");
        }
    }

    // 2. 处理已有客户端请求
    for (int i = 0; i < MAX_CLIENTS; i++) {
        if (_clients[i].client == nullptr) {
            continue;
        }

        if (!_clients[i].client->connected()) {
            // 客户端断开
            _clients[i].client->stop();
            delete _clients[i].client;
            _clients[i].client = nullptr;
            _clients[i].state = RTSP_CLIENT_IDLE;
            Serial.printf("[RTSPServer] 客户端 #%d 已断开\n", i);
            continue;
        }

        // 读取并处理请求
        if (_clients[i].client->available()) {
            handleClient(_clients[i].client);
            _clients[i].lastActivity = millis();
        }

        // 3. 检查超时
        uint32_t idleTime = (millis() - _clients[i].lastActivity) / 1000;
        if (idleTime > RTSP_SESSION_TIMEOUT) {
            Serial.printf("[RTSPServer] 客户端 #%d 超时（%us），断开连接\n",
                          i, idleTime);
            sendResponse(_clients[i].client, 200, "OK",
                         0, String(_clients[i].sessionId).c_str(),
                         "Connection: close\r\n");
            _clients[i].client->stop();
            delete _clients[i].client;
            _clients[i].client = nullptr;
            _clients[i].state = RTSP_CLIENT_IDLE;
        }
    }
}

/**
 * 处理单个 RTSP 请求
 */
bool RTSPServer::handleClient(WiFiClient* client) {
    if (client == nullptr || !client->connected()) {
        return false;
    }

    // 读取请求数据
    char buffer[RTSP_BUFFER_SIZE];
    memset(buffer, 0, sizeof(buffer));

    size_t totalRead = 0;
    int timeoutCount = 0;

    // 循环读取直到遇到空行（\r\n\r\n）或超时
    while (client->available() && totalRead < RTSP_BUFFER_SIZE - 1) {
        int bytesRead = client->read((uint8_t*)buffer + totalRead,
                                      RTSP_BUFFER_SIZE - totalRead - 1);
        if (bytesRead > 0) {
            totalRead += bytesRead;
            buffer[totalRead] = '\0';

            // 检查是否读完一个请求（空行）
            if (strstr(buffer, "\r\n\r\n") != nullptr) {
                break;
            }
        } else {
            timeoutCount++;
            if (timeoutCount > 10) break; // 防止死循环
            delay(1);
        }
    }

    if (totalRead == 0) {
        return true; // 无数据，继续保持连接
    }

    buffer[totalRead] = '\0';

    // 调试：打印收到的请求
    buffer[MIN(totalRead, 127)] = '\0'; // 截断打印
    Serial.printf("[RTSPServer] 请求: %s\n", buffer);

    // 解析请求
    String method, url, session, transport;
    int cseq = 0;

    if (!parseRequest(buffer, totalRead, method, url, cseq, session, transport)) {
        sendResponse(client, 400, "Bad Request", 0);
        return false;
    }

    // 查找对应客户端
    int clientIdx = -1;
    for (int i = 0; i < MAX_CLIENTS; i++) {
        if (_clients[i].client != nullptr &&
            _clients[i].client->remoteIP() == client->remoteIP()) {
            clientIdx = i;
            break;
        }
    }

    if (clientIdx < 0) {
        sendResponse(client, 500, "Internal Server Error", cseq);
        return false;
    }

    rtsp_client_t* cli = &_clients[clientIdx];

    // ============================================================
    // 分发请求处理
    // ============================================================

    if (method == "OPTIONS") {
        // ----------------------------------------
        // OPTIONS: 返回支持的 RTSP 方法
        // ----------------------------------------
        cli->state = RTSP_CLIENT_OPTIONS;
        const char* headers =
            "Public: DESCRIBE, SETUP, TEARDOWN, PLAY, PAUSE\r\n"
            "Accept: application/sdp";
        sendResponse(client, 200, "OK", cseq,
                     String(cli->sessionId).c_str(), headers);
        Serial.printf("[RTSPServer] 客户端 #%d: OPTIONS\n", clientIdx);

    } else if (method == "DESCRIBE") {
        // ----------------------------------------
        // DESCRIBE: 返回媒体描述（SDP）
        // ----------------------------------------
        cli->state = RTSP_CLIENT_DESCRIBE;
        const char* sdpHeaders =
            "Content-Type: application/sdp\r\n"
            "Content-Length: ";
        char fullHeaders[256];
        snprintf(fullHeaders, sizeof(fullHeaders),
                 "%s%d\r\n", sdpHeaders, _sdp.length());
        sendResponse(client, 200, "OK", cseq,
                     String(cli->sessionId).c_str(),
                     fullHeaders, _sdp.c_str());
        Serial.printf("[RTSPServer] 客户端 #%d: DESCRIBE (SDP %d bytes)\n",
                      clientIdx, _sdp.length());

    } else if (method == "SETUP") {
        // ----------------------------------------
        // SETUP: 建立播放会话
        // ----------------------------------------
        // 解析 Transport 头
        bool isTcp = true;
        int clientRtpPort = 0;
        int clientRtcpPort = 0;

        if (transport.length() > 0) {
            if (transport.indexOf("TCP") >= 0) {
                isTcp = true;
            } else if (transport.indexOf("RTP/AVP") >= 0) {
                // RTP/AVP = UDP
                isTcp = false;
            }

            // 尝试解析客户端端口
            int p1 = transport.indexOf("client_port=");
            if (p1 >= 0) {
                sscanf(transport.c_str() + p1 + 12, "%d", &clientRtpPort);
                int p2 = transport.indexOf("-");
                if (p2 > p1 + 12) {
                    sscanf(transport.c_str() + p1 + 12, "%d-%d",
                           &clientRtpPort, &clientRtcpPort);
                }
            }
        }

        cli->isTcp = isTcp;
        cli->clientRtpPort = static_cast<uint16_t>(clientRtpPort);
        cli->clientRtcpPort = static_cast<uint16_t>(clientRtcpPort);
        cli->state = RTSP_CLIENT_SETUP;
        cli->rtpTimestamp = 0;
        cli->lastActivity = millis();

        // 构建 Transport 响应头
        char transportResp[128];
        if (isTcp) {
            snprintf(transportResp, sizeof(transportResp),
                     "Transport: RTP/AVP/TCP;unicast;interleaved=%d-%d\r\n",
                     cli->rtpChannel, cli->rtcpChannel);
        } else {
            snprintf(transportResp, sizeof(transportResp),
                     "Transport: RTP/AVP/unicast;client_port=%d-%d;server_port=%d-%d\r\n",
                     clientRtpPort, clientRtcpPort, 5004, 5005);
        }

        sendResponse(client, 200, "OK", cseq,
                     String(cli->sessionId).c_str(), transportResp);
        Serial.printf("[RTSPServer] 客户端 #%d: SETUP (TCP=%d, port=%d)\n",
                      clientIdx, isTcp, clientRtpPort);

    } else if (method == "PLAY") {
        // ----------------------------------------
        // PLAY: 开始播放
        // ----------------------------------------
        // 验证 Session
        if (session.length() > 0 &&
            session.toInt() != static_cast<long>(cli->sessionId)) {
            sendResponse(client, 454, "Session Not Found", cseq);
            return false;
        }

        cli->state = RTSP_CLIENT_PLAYING;
        cli->rtpTimestamp = 0;
        cli->rtpSeq = static_cast<uint16_t>(random(0, 65536));

        // RTP-Info: 提供当前 RTP 信息
        char rtpInfo[128];
        snprintf(rtpInfo, sizeof(rtpInfo),
                 "RTP-Info: url=rtsp://%s:%d/mjpeg/1;seq=%d;rtptime=%d\r\n",
                 WiFi.localIP().toString().c_str(), _port,
                 cli->rtpSeq, cli->rtpTimestamp);

        sendResponse(client, 200, "OK", cseq,
                     String(cli->sessionId).c_str(), rtpInfo);
        Serial.printf("[RTSPServer] 客户端 #%d: PLAY → 正在推流\n", clientIdx);

    } else if (method == "PAUSE") {
        // ----------------------------------------
        // PAUSE: 暂停播放
        // ----------------------------------------
        if (cli->state == RTSP_CLIENT_PLAYING) {
            cli->state = RTSP_CLIENT_SETUP;
        }
        sendResponse(client, 200, "OK", cseq,
                     String(cli->sessionId).c_str());
        Serial.printf("[RTSPServer] 客户端 #%d: PAUSE\n", clientIdx);

    } else if (method == "TEARDOWN") {
        // ----------------------------------------
        // TEARDOWN: 关闭播放会话
        // ----------------------------------------
        cli->state = RTSP_CLIENT_TEARDOWN;
        sendResponse(client, 200, "OK", cseq,
                     String(cli->sessionId).c_str(),
                     "Connection: close\r\n");
        Serial.printf("[RTSPServer] 客户端 #%d: TEARDOWN\n", clientIdx);
        // 不立即关闭，让客户端主动断开

    } else {
        // ----------------------------------------
        // 未知方法
        // ----------------------------------------
        Serial.printf("[RTSPServer] 未知方法: %s\n", method.c_str());
        sendResponse(client, 501, "Not Implemented", cseq);
    }

    return true;
}

/**
 * 发送 RTSP 响应
 */
void RTSPServer::sendResponse(WiFiClient* client, int statusCode,
                               const char* statusMsg, int cseq,
                               const char* session,
                               const char* extraHeaders,
                               const char* body) {
    if (client == nullptr || !client->connected()) {
        return;
    }

    char response[1024];
    int offset = 0;

    // 状态行
    offset += snprintf(response + offset, sizeof(response) - offset,
                       "RTSP/1.0 %d %s\r\n", statusCode, statusMsg);

    // CSeq
    offset += snprintf(response + offset, sizeof(response) - offset,
                       "CSeq: %d\r\n", cseq);

    // Server
    offset += snprintf(response + offset, sizeof(response) - offset,
                       "Server: ESP32-CAM-RTSP/1.0\r\n");

    // Session
    if (session != nullptr && strlen(session) > 0) {
        offset += snprintf(response + offset, sizeof(response) - offset,
                           "Session: %s\r\n", session);
    }

    // 额外头部
    if (extraHeaders != nullptr) {
        offset += snprintf(response + offset, sizeof(response) - offset,
                           "%s", extraHeaders);
    }

    // 空行
    offset += snprintf(response + offset, sizeof(response) - offset,
                       "\r\n");

    // 发送头部
    size_t written = client->write((const uint8_t*)response, offset);
    if (written != static_cast<size_t>(offset)) {
        Serial.println("[RTSPServer] 警告：响应头写入不完整");
    }

    // 发送 body（如果有）
    if (body != nullptr && strlen(body) > 0) {
        size_t bodyLen = strlen(body);
        size_t bodyWritten = client->write((const uint8_t*)body, bodyLen);
        if (bodyWritten != bodyLen) {
            Serial.println("[RTSPServer] 警告：响应体写入不完整");
        }
    }
}

/**
 * 解析 RTSP 请求
 */
bool RTSPServer::parseRequest(const char* buffer, size_t len,
                               String& method, String& url, int& cseq,
                               String& session, String& transport) {
    method = "";
    url = "";
    cseq = 0;
    session = "";
    transport = "";

    if (buffer == nullptr || len == 0) {
        return false;
    }

    // 复制到临时缓冲区（因为要修改）
    char* temp = new char[len + 1];
    memcpy(temp, buffer, len);
    temp[len] = '\0';

    // 解析请求行: "METHOD URL RTSP/1.0\r\n"
    char* lineEnd = strstr(temp, "\r\n");
    if (lineEnd == nullptr) {
        delete[] temp;
        return false;
    }
    *lineEnd = '\0';

    char requestLine[256];
    strncpy(requestLine, temp, sizeof(requestLine) - 1);
    requestLine[sizeof(requestLine) - 1] = '\0';

    // 分割请求行
    char* tok1 = strtok(requestLine, " ");
    char* tok2 = strtok(nullptr, " ");
    char* tok3 = strtok(nullptr, " ");

    if (tok1 == nullptr || tok2 == nullptr || tok3 == nullptr) {
        delete[] temp;
        return false;
    }

    method = tok1;
    url = tok2;

    // 确认 RTSP 版本
    if (strcmp(tok3, "RTSP/1.0") != 0 && strcmp(tok3, "RTSP/1.1") != 0) {
        delete[] temp;
        return false;
    }

    // 解析各头部行
    char* ptr = lineEnd + 2;
    while (ptr < temp + len) {
        char* nextLine = strstr(ptr, "\r\n");
        if (nextLine == nullptr) break;
        *nextLine = '\0';

        // 解析 CSeq
        if (strncmp(ptr, "CSeq:", 5) == 0) {
            cseq = atoi(ptr + 5);
        }
        // 解析 Session
        else if (strncmp(ptr, "Session:", 8) == 0) {
            char* s = ptr + 8;
            while (*s == ' ') s++;
            char* semicolon = strchr(s, ';');
            if (semicolon) *semicolon = '\0';
            session = s;
        }
        // 解析 Transport
        else if (strncmp(ptr, "Transport:", 10) == 0) {
            transport = ptr + 10;
            transport.trim();
        }

        ptr = nextLine + 2;
    }

    delete[] temp;
    return true;
}

/**
 * 通过 TCP interleaved 发送一帧（JPEG 分片）
 *
 * JPEG 帧可能被分割成多个 RTP 包：
 *   1. 帧 > MTU → 分成多个 Fragment
 *   2. 每个 Fragment ≤ RTP_MAX_PACKET_SIZE
 */
void RTSPServer::sendFrameOverTcp(int clientIdx, WiFiClient* client,
                                   const uint8_t* buf, size_t len,
                                   uint32_t timestamp) {
    if (client == nullptr || !client->connected() || buf == nullptr || len == 0) {
        return;
    }
    if (clientIdx < 0 || clientIdx >= MAX_CLIENTS) {
        return;
    }

    size_t offset = 0;

    while (offset < len) {
        size_t chunkSize = MIN(len - offset,
                               RTP_MAX_PACKET_SIZE - RTP_HEADER_SIZE);

        bool marker = (offset + chunkSize >= len); // 最后一包置 Marker
        sendRtpPacket(clientIdx, client, buf + offset, chunkSize, timestamp, marker);

        offset += chunkSize;

        // 让出 CPU，防止发送过快导致 TCP 缓冲区满
        delay(1);
    }
}

/**
 * 发送单个 RTP 包（TCP interleaved 模式）
 *
 * RTP over TCP 使用 Interleaving：
 *   [Magic(1)][Channel(1)][Length(2)][RTP Header(12)][Payload]
 *   '$' (0x24) | Channel | 长度(RTP头+载荷) | RTP包
 */
void RTSPServer::sendRtpPacket(int clientIdx, WiFiClient* client,
                                const uint8_t* payload,
                                size_t payloadLen,
                                uint32_t timestamp,
                                bool marker) {
    if (client == nullptr || !client->connected()) {
        return;
    }

    uint8_t rtpPacket[RTP_MAX_PACKET_SIZE + 14]; // +4(interleaving) +12(RTP头)
    size_t rtpTotalSize = RTP_HEADER_SIZE + payloadLen;

    if (rtpTotalSize > sizeof(rtpPacket) - 4) {
        Serial.println("[RTSPServer] 错误：RTP 包过大");
        return;
    }

    // RTP 固定头
    rtp_header_t* hdr = (rtp_header_t*)&rtpPacket[4]; // 跳过 interleaving 头

    hdr->version   = RTP_VERSION;
    hdr->padding   = 0;
    hdr->extension = 0;
    hdr->csrcCount = 0;
    hdr->marker    = marker ? 1 : 0;
    hdr->payloadType = RTP_PAYLOAD_TYPE_MJPEG;
    hdr->seqNum    = htons(_clients[clientIdx].rtpSeq);
    hdr->timestamp = htonl(timestamp);
    hdr->ssrc      = htonl(0x12345678);         // 固定 SSRC

    // 复制载荷
    memcpy(&rtpPacket[4 + RTP_HEADER_SIZE], payload, payloadLen);

    // Interleaving 头: $ (0x24) | channel | length
    rtpPacket[0] = 0x24; // Magic
    rtpPacket[1] = 0x00; // Channel 0 (RTP)
    rtpPacket[2] = (rtpTotalSize >> 8) & 0xFF;
    rtpPacket[3] = rtpTotalSize & 0xFF;

    // 递增序列号
    _clients[clientIdx].rtpSeq = (_clients[clientIdx].rtpSeq + 1) & 0xFFFF;

    // 发送
    size_t written = client->write(rtpPacket, 4 + rtpTotalSize);
    if (written != 4 + rtpTotalSize) {
        // 发送失败，可能是连接已断开
    }
}

/**
 * 生成随机 Session ID
 */
uint32_t RTSPServer::generateSessionId() {
    return static_cast<uint32_t>(random(0x10000000, 0xFFFFFFFF));
}

/**
 * 生成随机 SSRC
 */
void RTSPServer::generateSSRC(uint8_t* ssrc) {
    ssrc[0] = random(0, 256);
    ssrc[1] = random(0, 256);
    ssrc[2] = random(0, 256);
    ssrc[3] = random(0, 256);
}

/**
 * 构建 SDP 描述信息
 *
 * SDP 格式：
 * v=0
 * o=- <session_id> <version> IN IP4 <ip>
 * s=ESP32-CAM Stream
 * c=IN IP4 0.0.0.0
 * t=0 0
 * m=video <port> RTP/AVP 26   # 26 = MJPEG
 * a=rtpmap:26 MJPEG/90000
 * a=framerate:25
 */
String RTSPServer::buildSDP(int width, int height) {
    String ip = WiFi.localIP().toString();
    uint32_t sessionId = random(0x100000, 0xFFFFFF);

    char sdp[512];
    snprintf(sdp, sizeof(sdp),
             "v=0\r\n"
             "o=- %u 0 IN IP4 %s\r\n"
             "s=ESP32-CAM Stream\r\n"
             "c=IN IP4 0.0.0.0\r\n"
             "t=0 0\r\n"
             "m=video %d RTP/AVP 26\r\n"
             "a=rtpmap:26 MJPEG/90000\r\n"
             "a=control:trackID=0\r\n"
             "a=framerate:25\r\n"
             "a=cliprect:0,0,%d,%d\r\n"
             "a=framesize:26 %d %d\r\n",
             sessionId, ip.c_str(),
             _port,
             height, width,
             width, height);

    return String(sdp);
}

/**
 * 清理超时客户端
 */
void RTSPServer::cleanupClients() {
    for (int i = 0; i < MAX_CLIENTS; i++) {
        if (_clients[i].client == nullptr) continue;

        uint32_t idleTime = (millis() - _clients[i].lastActivity) / 1000;
        if (idleTime > RTSP_SESSION_TIMEOUT) {
            Serial.printf("[RTSPServer] 清理超时客户端 #%d\n", i);
            _clients[i].client->stop();
            delete _clients[i].client;
            _clients[i].client = nullptr;
            _clients[i].state = RTSP_CLIENT_IDLE;
        }
    }
}

/**
 * 查找空闲客户端槽位
 */
int RTSPServer::findFreeClientSlot() {
    for (int i = 0; i < MAX_CLIENTS; i++) {
        if (_clients[i].client == nullptr) {
            return i;
        }
    }
    return -1;
}

/**
 * 根据 Session ID 查找客户端
 */
int RTSPServer::findClientBySession(uint32_t sessionId) {
    for (int i = 0; i < MAX_CLIENTS; i++) {
        if (_clients[i].sessionId == sessionId) {
            return i;
        }
    }
    return -1;
}

/**
 * 获取已连接客户端数量
 */
int RTSPServer::connectedClients() {
    int count = 0;
    for (int i = 0; i < MAX_CLIENTS; i++) {
        if (_clients[i].client != nullptr &&
            _clients[i].state != RTSP_CLIENT_IDLE) {
            count++;
        }
    }
    return count;
}
