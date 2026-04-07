# =============================================================================
# mqtt-router/Dockerfile
# =============================================================================
# MQTT 消息路由器 + MQTT ↔ OpenClaw HTTP 桥接服务的 Docker 镜像
#
# 包含：
#   - mqtt_router.py : MQTT Broker 连接管理 + 消息路由（paho-mqtt）
#   - bridge.py      : MQTT <-> OpenClaw HTTP 双向桥接（标准库实现）
#   - topics.py      : 消息 Topic 定义与 JSON Schema 验证
#
# 默认启动：bridge.py（桥接服务）
# 如需单独运行路由器：docker run ... python mqtt_router.py
# =============================================================================

FROM python:3.11-slim

# -----------------------------------------------------------------------
# 1. 安装系统依赖（OpenClaw Gateway API 调用需要）
# -----------------------------------------------------------------------
# 注：bridge.py 使用标准库，无需额外 C 依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
        # 基础工具（调试用）
        curl \
        # 时区数据（Python datetime 需要）
        tzdata \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------------------------
# 2. 设置环境变量
# -----------------------------------------------------------------------
# Python 日志级别（默认 INFO，生产可用 DEBUG）
ENV PYTHONUNBUFFERED=1 \
    PYTHONLOGLEVEL=INFO \
    # 默认 MQTT Broker 地址
    MQTT_HOST=localhost \
    MQTT_PORT=1883 \
    # 默认 OpenClaw Gateway HTTP 地址
    OPENCLAW_URL=http://127.0.0.1:18789 \
    # 默认 HTTP 服务端口
    HTTP_PORT=8080

# -----------------------------------------------------------------------
# 3. 创建应用目录
# -----------------------------------------------------------------------
WORKDIR /app

# -----------------------------------------------------------------------
# 4. 安装 Python 依赖
# -----------------------------------------------------------------------
# paho-mqtt: MQTT 客户端库（mqtt_router.py 需要）
# 注意：bridge.py 使用标准库 socket 实现，不依赖 paho-mqtt
#       但 mqtt_router.py 需要 paho-mqtt，所以统一安装
COPY requirements.txt /tmp/requirements.txt

# 如果没有 requirements.txt，提供一个默认的
RUN if [ -f /tmp/requirements.txt ]; then \
        pip install --no-cache-dir -r /tmp/requirements.txt; \
    else \
        pip install --no-cache-dir paho-mqtt>=1.6.0; \
    fi

# -----------------------------------------------------------------------
# 5. 复制应用代码
# -----------------------------------------------------------------------
# 按顺序复制：每个文件单独 COPY 以利用 Docker 缓存
COPY mqtt_router.py /app/mqtt_router.py
COPY bridge.py      /app/bridge.py
COPY topics.py      /app/topics.py

# -----------------------------------------------------------------------
# 6. 创建非 root 用户（安全增强）
# -----------------------------------------------------------------------
# Docker 默认以 root 运行，创建专用用户降低风险
RUN useradd --create-home --shell /bin/bash mqttuser && \
    chown -R mqttuser:mqttuser /app

USER mqttuser

# -----------------------------------------------------------------------
# 7. 暴露端口
# -----------------------------------------------------------------------
# 1883  : MQTT Broker 端口（如果需要连接外部 Broker 可映射）
# 8080  : HTTP 服务端口（bridge.py 监听的端口）
EXPOSE 1883 8080

# -----------------------------------------------------------------------
# 8. 健康检查
# -----------------------------------------------------------------------
# 检查 HTTP 服务是否响应 /health 端点
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -sf http://localhost:${HTTP_PORT:-8080}/health || exit 1

# -----------------------------------------------------------------------
# 9. 入口点：默认启动 bridge.py（MQTT <-> OpenClaw HTTP 桥接）
# -----------------------------------------------------------------------
# 允许通过环境变量覆盖启动命令：
#   docker run -e CMD="python mqtt_router.py --help"
# -----------------------------------------------------------------------
ENTRYPOINT ["python", "-u", "bridge.py"]

# -----------------------------------------------------------------------
# 默认启动参数（可通过 docker-compose 或 -e 覆盖）
# -----------------------------------------------------------------------
# MQTT Broker: localhost:1883
# OpenClaw   : http://127.0.0.1:18789
# HTTP 端口  : 8080
# 订阅 topics : # （全部 MQTT 消息转发到 OpenClaw）
# HTTP->MQTT : robot/cmd/# 和 agent/# topics 可发布
CMD [
    "--mqtt-host",     "${MQTT_HOST:-localhost}",
    "--mqtt-port",     "${MQTT_PORT:-1883}",
    "--openclaw-url",  "${OPENCLAW_URL:-http://127.0.0.1:18789}",
    "--port",          "${HTTP_PORT:-8080}",
    "--subscribe-topics", "#",
    "--http-to-mqtt-topics", "robot/cmd/#", "agent/#"
]
