#!/usr/bin/env python3
"""
iPhone 感知 — 端到端延迟测试脚本
路径: night-build/scripts/latency_test.py
依赖: pip install websockets numpy pandas argparse
用法:
    python3 latency_test.py --mode e2e --duration 60 --output latency_results.json
    python3 latency_test.py --mode rtt --count 100 --host 192.168.1.100

测试内容:
  - 端到端延迟 (end-to-end): iPhone ARKit 帧捕获 → OpenClaw Agent 收到
  - WiFi RTT (round-trip time): 发送 ping → 收到 pong
  - 分阶段延迟 (per-stage): S1-S6 各阶段耗时分解
"""

import argparse
import asyncio
import json
import time
import struct
import statistics
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

import numpy as np


@dataclass
class LatencySample:
    """单次延迟采样"""
    timestamp: float               # 墙钟时间 (s)
    frame_id: int                  # 帧序号
    # 各阶段延迟 (ms)
    s1_arkit_capture: float = 0    # S1: ARKit 帧捕获
    s2_arkit_to_app: float = 0     # S2: ARKit → App 传递
    s3_encoding: float = 0         # S3: App LZ4 编码
    s4_wifi: float = 0            # S4: WiFi 传输
    s5_node_processing: float = 0  # S5: OpenClaw Node 处理
    s6_gateway_agent: float = 0    # S6: Gateway → Agent 路由
    e2e_total: float = 0           # 端到端总计

    def to_dict(self):
        return asdict(self)


class LatencyTestRunner:
    """延迟测试运行器"""

    def __init__(
        self,
        node_ws_url: str,
        gateway_ws_url: str = "ws://127.0.0.1:18800",
        window_size: int = 300
    ):
        self.node_ws_url = node_ws_url
        self.gateway_ws_url = gateway_ws_url
        self.window_size = window_size
        self.samples: deque[LatencySample] = deque(maxlen=window_size)
        self._running = False
        self._frame_id = 0

        # 时钟偏移估计 (NTP-like)
        self.clock_offset = 0.0
        self._sync_complete = False

        # WiFi RTT 采样
        self.rtt_samples: deque[float] = deque(maxlen=500)

        # OpenClaw 内置延迟指标 (如果可用)
        self.openclaw_latency_samples: deque[float] = deque(maxlen=window_size)

    async def run_e2e(self, duration_sec: float):
        """端到端延迟测试"""
        self._running = True
        print(f"🚀 开始端到端延迟测试，持续 {duration_sec}s")
        print(f"   Node URL: {self.node_ws_url}")
        print(f"   Gateway URL: {self.gateway_ws_url}")

        # Step 1: 时钟同步
        await self._sync_clock()
        if not self._sync_complete:
            print("⚠️ 时钟同步失败，使用未校正时间戳继续...")

        # Step 2: 建立 WebSocket 连接
        async with asyncio.connect(self.node_ws_url) as ws:
            print("✅ WebSocket 已连接，开始采集延迟数据...")

            start_time = time.monotonic()
            last_report = start_time
            last_stats_log = start_time

            while self._running and (time.monotonic() - start_time) < duration_sec:
                try:
                    # 接收帧
                    raw = await asyncio.wait_for(
                        ws.recv(),
                        timeout=5.0
                    )
                    t_received = time.monotonic()

                    # 解析帧头 timestamp
                    sample = self._parse_frame(raw, t_received)
                    if sample:
                        self.samples.append(sample)

                        # 检测丢帧
                        if len(self.samples) > 1:
                            prev = self.samples[-2]
                            gap = sample.frame_id - prev.frame_id
                            if gap > 1:
                                print(f"  ⚠️ 丢帧检测: gap={gap}")

                    # 每 10 秒打印一次统计
                    now = time.monotonic()
                    if now - last_stats_log >= 10:
                        self._print_stats()
                        last_stats_log = now

                except asyncio.TimeoutError:
                    print("  ⚠️ 接收超时，检查连接...")
                    break
                except Exception as e:
                    print(f"  ❌ 错误: {e}")
                    await asyncio.sleep(1)

                # 目标: 30fps，每帧约 33ms
                await asyncio.sleep(0.033)

        self._running = False
        print(f"\n✅ 测试结束，共采集 {len(self.samples)} 个样本")

    async def run_rtt(self, count: int):
        """WiFi RTT 测试（不需要 iPhone 端配合）"""
        print(f"🚀 开始 RTT 测试，发送 {count} 次 ping")

        async with asyncio.connect(self.gateway_ws_url) as ws:
            for i in range(count):
                t_sent = time.monotonic()
                await ws.send(json.dumps({"type": "ping", "seq": i}))

                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    t_received = time.monotonic()
                    rtt_ms = (t_received - t_sent) * 1000
                    self.rtt_samples.append(rtt_ms)

                    if (i + 1) % 20 == 0:
                        self._print_rtt_stats()

                except asyncio.TimeoutError:
                    print(f"  ⚠️ ping {i} 超时")

                await asyncio.sleep(0.1)  # 100ms 间隔

        self._print_rtt_stats()

    async def _sync_clock(self):
        """NTP-like 时钟偏移同步"""
        print("🔄 进行时钟同步...")

        try:
            async with asyncio.connect(self.gateway_ws_url) as ws:
                # 发送时钟请求
                t1 = time.monotonic()
                await ws.send(json.dumps({
                    "type": "clock_sync",
                    "iphone_t": t1,
                    "seq": 0
                }))

                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                t4 = time.monotonic()

                data = json.loads(response)
                t2 = data.get("server_t", None)  # 服务器收到请求时间
                t3 = data.get("server_processed_t", None)  # 服务器处理时间

                if t2 and t3:
                    # NTP 算法: offset = ((t2 - t1) + (t3 - t4)) / 2
                    self.clock_offset = ((t2 - t1) + (t3 - t4)) / 2
                    self._sync_complete = True
                    print(f"  ✅ 时钟偏移: {self.clock_offset*1000:.2f} ms")
                else:
                    # 简化同步: offset = server_t - iphone_t
                    self.clock_offset = data.get("server_t", 0) - t1
                    self._sync_complete = True
                    print(f"  ✅ 时钟偏移 (简化): {self.clock_offset*1000:.2f} ms")

        except Exception as e:
            print(f"  ⚠️ 时钟同步失败: {e}")

    def _parse_frame(self, raw, t_received: float) -> LatencySample | None:
        """解析 iPhone 帧数据，估算各阶段延迟"""
        try:
            # 支持 JSON 或 MessagePack
            if isinstance(raw, str):
                header = json.loads(raw)
            elif isinstance(raw, bytes):
                header = self._parse_msgpack(raw)
            else:
                return None

            t_sent = header.get("t_sent", 0)  # iPhone 发送时间 (校正后)
            t_captured = header.get("t_captured", t_sent)  # ARKit 帧捕获时间

            # WiFi 传输延迟 (单向)
            wifi_latency_ms = (t_received - t_sent) * 1000

            # S4: WiFi 传输
            s4_wifi = wifi_latency_ms

            # S5: Node 处理 (从 OpenClaw 指标获取)
            s5_node = header.get("_node_processing_ms", 0)

            # S6: Gateway → Agent
            s6_gw = header.get("_gateway_agent_ms", 0)

            # 端到端延迟 (感觉运动延迟基准)
            e2e_ms = (t_received - t_captured) * 1000 - self.clock_offset * 1000
            e2e_ms = max(e2e_ms, 0)  # 防止负值

            # 帧 ID
            self._frame_id = header.get("frameId", self._frame_id + 1)

            return LatencySample(
                timestamp=time.time(),
                frame_id=self._frame_id,
                s4_wifi=round(s4_wifi, 3),
                s5_node_processing=round(s5_node, 3),
                s6_gateway_agent=round(s6_gw, 3),
                e2e_total=round(e2e_ms, 3)
            )

        except Exception as e:
            print(f"  ⚠️ 帧解析错误: {e}")
            return None

    def _parse_msgpack(self, data: bytes) -> dict:
        """简单 MessagePack 解析 (仅处理 map 类型)"""
        import msgpack
        return msgpack.unpackb(data, raw=False)

    def _print_stats(self):
        """打印当前统计"""
        if not self.samples:
            return

        e2e = [s.e2e_total for s in self.samples if s.e2e_total > 0]
        wifi = [s.s4_wifi for s in self.samples if s.s4_wifi > 0]

        def stats(vals):
            s = sorted(vals)
            return {
                "min": round(min(vals), 2),
                "avg": round(statistics.mean(vals), 2),
                "p50": round(s[len(s)//2], 2),
                "p90": round(s[int(len(s)*0.9)], 2),
                "p99": round(s[int(len(s)*0.99)], 2),
                "max": round(max(vals), 2),
            }

        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 延迟统计 (最近 {len(self.samples)} 帧):")
        if e2e:
            print(f"  端到端: min={stats(e2e)['min']}ms, "
                  f"avg={stats(e2e)['avg']}ms, "
                  f"P50={stats(e2e)['p50']}ms, "
                  f"P90={stats(e2e)['p90']}ms, "
                  f"P99={stats(e2e)['p99']}ms, "
                  f"max={stats(e2e)['max']}ms")
        if wifi:
            print(f"  WiFi RTT: min={stats(wifi)['min']}ms, "
                  f"avg={stats(wifi)['avg']}ms, "
                  f"P99={stats(wifi)['p99']}ms")

    def _print_rtt_stats(self):
        """打印 RTT 统计"""
        if not self.rtt_samples:
            return

        rtt = sorted(self.rtt_samples)
        n = len(rtt)
        print(f"\nRTT 统计 (共 {n} 次):")
        print(f"  min={rtt[0]:.2f}ms, avg={statistics.mean(rtt):.2f}ms, "
              f"P50={rtt[n//2]:.2f}ms, "
              f"P90={rtt[int(n*0.9)]:.2f}ms, "
              f"P99={rtt[int(n*0.99)]:.2f}ms, "
              f"max={rtt[-1]:.2f}ms")

    def save_results(self, output_path: str):
        """保存测试结果到 JSON"""
        results = {
            "test_type": "e2e_latency",
            "timestamp": datetime.now().isoformat(),
            "total_samples": len(self.samples),
            "samples": [s.to_dict() for s in self.samples],
            "rtt_samples": list(self.rtt_samples),
            "clock_offset_ms": self.clock_offset * 1000,
            "summary": self._compute_summary()
        }

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(results, f, indent=2)

        print(f"💾 结果已保存到: {path}")

    def _compute_summary(self) -> dict:
        """计算汇总统计"""
        if not self.samples:
            return {}

        e2e = [s.e2e_total for s in self.samples if s.e2e_total > 0]
        wifi = [s.s4_wifi for s in self.samples if s.s4_wifi > 0]
        node = [s.s5_node_processing for s in self.samples if s.s5_node_processing > 0]
        gw = [s.s6_gateway_agent for s in self.samples if s.s6_gateway_agent > 0]

        def summary(vals):
            if not vals:
                return {}
            s = sorted(vals)
            n = len(s)
            return {
                "count": n,
                "min": round(min(vals), 2),
                "avg": round(statistics.mean(vals), 2),
                "std": round(statistics.stdev(vals), 2) if len(vals) > 1 else 0,
                "p50": round(s[n//2], 2),
                "p90": round(s[int(n*0.9)], 2),
                "p99": round(s[int(n*0.99)], 2),
                "max": round(max(vals), 2),
            }

        return {
            "e2e": summary(e2e),
            "wifi_one_way": summary(wifi),
            "node_processing": summary(node),
            "gateway_agent": summary(gw),
            "rtt": summary(list(self.rtt_samples)) if self.rtt_samples else {},
        }


async def amain():
    parser = argparse.ArgumentParser(description="iPhone 感知延迟测试")
    parser.add_argument("--mode", choices=["e2e", "rtt"], default="e2e",
                        help="测试模式: e2e=端到端延迟, rtt=WiFi RTT")
    parser.add_argument("--node-url", default="ws://127.0.0.1:18800/node/iphone-001",
                        help="iPhone Node WebSocket URL")
    parser.add_argument("--gateway-url", default="ws://127.0.0.1:18800",
                        help="OpenClaw Gateway WebSocket URL")
    parser.add_argument("--duration", type=float, default=60,
                        help="e2e 测试持续时间 (秒)")
    parser.add_argument("--count", type=int, default=100,
                        help="RTT 测试 ping 次数")
    parser.add_argument("--output", default="night-build/output/latency_results.json",
                        help="结果输出路径")

    args = parser.parse_args()

    runner = LatencyTestRunner(
        node_ws_url=args.node_url,
        gateway_ws_url=args.gateway_url
    )

    if args.mode == "e2e":
        await runner.run_e2e(duration_sec=args.duration)
        runner.save_results(args.output)
    else:
        await runner.run_rtt(count=args.count)


if __name__ == "__main__":
    asyncio.run(amain())
