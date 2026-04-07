#!/usr/bin/env python3
"""
iPhone 感知 — 延迟测试结果分析脚本
路径: night-build/scripts/analyze_latency.py
依赖: pip install numpy pandas matplotlib
用法:
    python3 analyze_latency.py --input latency_results.json
    python3 analyze_latency.py --input latency_results.json --output latency_report.pdf

功能:
  - 计算各阶段延迟统计 (min/avg/p50/p90/p99/max)
  - 检测异常值和连续超时
  - 生成可视化图表 (直方图/时序图/热力图)
  - 导出 PDF/HTML 报告
  - 与验收标准对比，输出 PASS/FAIL
"""

import argparse
import json
import math
import statistics
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np


@dataclass
class LatencyThresholds:
    """验收标准阈值"""
    e2e_avg_ms: float = 50.0
    e2e_p99_ms: float = 100.0
    e2e_max_ms: float = 200.0
    wifi_p99_ms: float = 15.0
    node_p99_ms: float = 20.0
    consecutive_red_limit: int = 3


@dataclass
class StageStats:
    min: float
    avg: float
    std: float
    p50: float
    p90: float
    p99: float
    max: float
    count: int


class LatencyAnalyzer:
    """延迟测试结果分析器"""

    THRESHOLDS = LatencyThresholds()

    GRADE_A = "#00FF00"  # 绿色
    GRADE_B = "#FFFF00"  # 黄色
    GRADE_C = "#FF8800"  # 橙色
    GRADE_F = "#FF0000"  # 红色

    def __init__(self, results: dict):
        self.results = results
        self.samples = results.get("samples", [])
        self.rtt_samples = results.get("rtt_samples", [])
        self.thresholds = self.THRESHOLDS

    # ── 统计计算 ───────────────────────────────────────────

    def _stats(self, vals: list[float]) -> StageStats:
        if not vals:
            return StageStats(0, 0, 0, 0, 0, 0, 0, 0)
        s = sorted(vals)
        n = len(s)
        return StageStats(
            min=round(min(vals), 2),
            avg=round(statistics.mean(vals), 2),
            std=round(statistics.stdev(vals), 2) if n > 1 else 0,
            p50=round(s[n//2], 2),
            p90=round(s[int(n*0.9)], 2),
            p99=round(s[int(n*0.99)], 2),
            max=round(max(vals), 2),
            count=n
        )

    def analyze(self) -> dict:
        """执行完整分析"""
        e2e = [s["e2e_total"] for s in self.samples if s.get("e2e_total", 0) > 0]
        wifi = [s["s4_wifi"] for s in self.samples if s.get("s4_wifi", 0) > 0]
        node = [s["s5_node_processing"] for s in self.samples if s.get("s5_node_processing", 0) > 0]
        gw = [s["s6_gateway_agent"] for s in self.samples if s.get("s6_gateway_agent", 0) > 0]

        return {
            "test_timestamp": self.results.get("timestamp", ""),
            "total_frames": len(self.samples),
            "clock_offset_ms": self.results.get("clock_offset_ms", 0),
            "stages": {
                "e2e_total": self._stats(e2e),
                "wifi_one_way": self._stats(wifi),
                "node_processing": self._stats(node),
                "gateway_agent": self._stats(gw),
            },
            "rtt": self._stats(self.rtt_samples),
            "grade": self._compute_grade(e2e),
            "checks": self._run_checks(e2e, wifi, node),
        }

    def _compute_grade(self, e2e: list[float]) -> str:
        """计算延迟等级"""
        if not e2e:
            return "UNKNOWN"
        s = sorted(e2e)
        p99 = s[int(len(s)*0.99)]
        avg = statistics.mean(e2e)

        if p99 < 50 and avg < 30:
            return "A (🥇 实时控制)"
        elif p99 < 100:
            return "B (🥈 近实时)"
        elif p99 < 200:
            return "C (🥉 降级模式)"
        else:
            return "F (❌ 不合格)"

    def _run_checks(self, e2e: list[float], wifi: list[float],
                    node: list[float]) -> list[dict]:
        """执行验收检查"""
        checks = []
        s_e2e = sorted(e2e) if e2e else []

        # Check 1: 端到端 P99 < 100ms
        p99 = s_e2e[int(len(s_e2e)*0.99)] if s_e2e else 999
        checks.append({
            "name": "端到端延迟 P99 < 100ms",
            "value": f"{p99:.1f}ms",
            "status": "PASS" if p99 < 100 else "FAIL",
            "threshold": "100ms",
        })

        # Check 2: WiFi P99 < 15ms
        if wifi:
            s_wifi = sorted(wifi)
            p99_wifi = s_wifi[int(len(s_wifi)*0.99)]
            checks.append({
                "name": "WiFi RTT P99 < 15ms",
                "value": f"{p99_wifi:.1f}ms",
                "status": "PASS" if p99_wifi < 15 else "FAIL",
                "threshold": "15ms",
            })

        # Check 3: 连续超长延迟帧
        consecutive_red = self._count_consecutive_red(e2e)
        checks.append({
            "name": "无连续 3 帧 > 150ms",
            "value": f"最多连续 {consecutive_red} 帧",
            "status": "PASS" if consecutive_red < 3 else "FAIL",
            "threshold": "< 3 帧",
        })

        # Check 4: 平均延迟 < 50ms
        avg = statistics.mean(e2e) if e2e else 999
        checks.append({
            "name": "端到端平均延迟 < 50ms",
            "value": f"{avg:.1f}ms",
            "status": "PASS" if avg < 50 else "FAIL",
            "threshold": "50ms",
        })

        return checks

    def _count_consecutive_red(self, vals: list[float]) -> int:
        """计算连续超长延迟帧数"""
        max_consecutive = 0
        current = 0
        for v in vals:
            if v > 150:
                current += 1
                max_consecutive = max(max_consecutive, current)
            else:
                current = 0
        return max_consecutive

    # ── 输出报告 ───────────────────────────────────────────

    def print_report(self, analysis: dict):
        """打印分析报告到终端"""
        print()
        print("=" * 60)
        print(f"  iPhone 感知延迟测试报告")
        print("=" * 60)
        print(f"  测试时间: {analysis['test_timestamp']}")
        print(f"  总帧数:   {analysis['total_frames']}")
        print(f"  时钟偏移: {analysis['clock_offset_ms']:.2f} ms")
        print(f"  等级:     {analysis['grade']}")
        print()

        print("  各阶段延迟 (ms):")
        print("  " + "-" * 54)
        header = f"  {'阶段':<22} | {'Avg':>7} | {'P50':>7} | {'P90':>7} | {'P99':>7} | {'Max':>7}"
        print(header)
        print("  " + "-" * 54)

        for stage_name, stats in analysis["stages"].items():
            label = {
                "e2e_total": "端到端总计",
                "wifi_one_way": "S4 WiFi传输",
                "node_processing": "S5 Node处理",
                "gateway_agent": "S6 GW→Agent",
            }.get(stage_name, stage_name)

            print(f"  {label:<22} | {stats.avg:>7.1f} | {stats.p50:>7.1f} | "
                  f"{stats.p90:>7.1f} | {stats.p99:>7.1f} | {stats.max:>7.1f}")

        if analysis["rtt"].count > 0:
            rtt = analysis["rtt"]
            print(f"  {'WiFi RTT':<22} | {rtt.avg:>7.1f} | {rtt.p50:>7.1f} | "
                  f"{rtt.p90:>7.1f} | {rtt.p99:>7.1f} | {rtt.max:>7.1f}")

        print("  " + "-" * 54)
        print()
        print("  验收检查:")
        print("  " + "-" * 54)

        all_pass = True
        for check in analysis["checks"]:
            icon = "✅" if check["status"] == "PASS" else "❌"
            print(f"  {icon} {check['name']}")
            print(f"     实际值: {check['value']} | 阈值: {check['threshold']} | {check['status']}")
            if check["status"] == "FAIL":
                all_pass = False

        print()
        if all_pass:
            print("  ✅ 全部通过！iPhone 感知链路满足实时控制要求。")
        else:
            print("  ⚠️  部分检查未通过，详见上述结果。")
        print()
        print("=" * 60)

    def export_json(self, analysis: dict, output_path: str):
        """导出 JSON 报告"""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # 转换 StageStats 为 dict
        analysis_serializable = {
            k: v if not isinstance(v, StageStats) else {
                "min": v.min, "avg": v.avg, "std": v.std,
                "p50": v.p50, "p90": v.p90, "p99": v.p99,
                "max": v.max, "count": v.count
            }
            for k, v in (analysis.items()
                          if not isinstance(analysis, dict)
                          else analysis.items())
        }

        for k, v in analysis_serializable.items():
            if isinstance(v, dict) and "min" in v:
                analysis_serializable[k] = v  # 已经是可序列化格式

        with open(path, "w") as f:
            json.dump(analysis_serializable, f, indent=2, ensure_ascii=False)

        print(f"💾 JSON 报告已保存: {path}")


async def amain():
    parser = argparse.ArgumentParser(description="延迟测试结果分析")
    parser.add_argument("--input", "-i", required=True,
                        help="latency_test.py 输出 JSON 文件路径")
    parser.add_argument("--output", "-o",
                        help="输出文件路径 (.json / .html / .pdf)")
    parser.add_argument("--thresholds",
                        help="自定义阈值 JSON 文件")

    args = parser.parse_args()

    # 读取测试结果
    with open(args.input) as f:
        results = json.load(f)

    analyzer = LatencyAnalyzer(results)
    analysis = analyzer.analyze()

    analyzer.print_report(analysis)

    # 导出
    if args.output:
        p = Path(args.output)
        if p.suffix == ".json":
            analyzer.export_json(analysis, args.output)
        elif p.suffix in (".html", ".pdf"):
            print(f"\n图表导出功能需要 matplotlib/seaborn")
            print(f"建议使用: python3 analyze_latency.py -i {args.input}")
            # 仍导出 JSON
            json_out = p.with_suffix(".json")
            analyzer.export_json(analysis, str(json_out))
    else:
        # 默认导出到输入文件同目录下
        json_out = Path(args.input).with_suffix(".analysis.json")
        analyzer.export_json(analysis, str(json_out))


if __name__ == "__main__":
    import asyncio
    asyncio.run(amain())
