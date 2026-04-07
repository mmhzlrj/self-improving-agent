#!/usr/bin/env python3
"""
Closed-Loop Verification Test for Cyber Bricks Visual Joint Feedback
=======================================================================
Purpose:
    Verify that the visual joint angle estimator (joint_estimator.py)
    achieves < 5° error compared to the commanded joint angles.

Test protocol:
    1. Move each joint to a sequence of commanded positions (via MQTT)
    2. Wait for the arm to settle (motion delay)
    3. Read estimated angles from joint_estimator (via MQTT subscribe or
       shared file / shared memory)
    4. Compare commanded vs estimated → record error
    5. Report pass/fail against the 5° threshold

Hardware:
    - Cyber Bricks ESP32-C3 (MQTT control)
    - ESP32-Cam OV2640 (RTSP stream)
    - Jetson Nano 2GB (running this script + joint_estimator)

MQTT Topics:
    Command  (outgoing): cyberbricks/cmd    — JSON: {"joint": "shoulder", "angle": 90}
    State    (incoming) : cyberbricks/state — JSON: {"joint": "shoulder", "angle": 90}

Prerequisites:
    1. Run: python3 calibrate.py --mode full
    2. Start joint_estimator.py in the background
    3. Cyber Bricks ESP32-C3 MQTT broker reachable

Usage:
    # Full test suite (all joints, 5 positions each)
    python3 test_cyberbricks.py --joints base_rot shoulder elbow wrist

    # Single-joint test
    python3 test_cyberbricks.py --joints shoulder --positions 45 90 135

    # With different MQTT broker
    python3 test_cyberbricks.py --mqtt-host 192.168.1.60

Output:
    - Console summary table
    - Detailed CSV: test_results_<timestamp>.csv
    - JSON report:  test_results_<timestamp>.json
"""

import json
import time
import os
import sys
import argparse
import logging
import statistics
from datetime import datetime
from pathlib import Path
from threading import Event, Thread
from typing import Optional

# ─── MQTT ─────────────────────────────────────────────────────────────────────
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    print("[WARN] paho-mqtt not installed — MQTT commands disabled.")

# ─── Paths ───────────────────────────────────────────────────────────────────
SCRIPT_DIR    = Path(__file__).parent
REPORT_DIR    = SCRIPT_DIR.parent.parent.parent / "night-build" / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("test_cyberbricks")


# ═══════════════════════════════════════════════════════════════════════════════
# 1. MQTT CONTROLLER — send commands to Cyber Bricks ESP32-C3
# ═══════════════════════════════════════════════════════════════════════════════

class CyberBricksController:
    """
    Sends joint angle commands to the Cyber Bricks over MQTT.
    Also receives acknowledgement / actual-state messages.

    Expected MQTT message formats:
      Command out: {"type": "angle_cmd", "joint": "<name>", "angle": <float degrees>}
      State    in : {"type": "angle_ack", "joint": "<name>", "angle": <float degrees>}
    """

    CMD_TOPIC  = "cyberbricks/cmd"
    STATE_TOPIC = "cyberbricks/state"

    def __init__(self, broker_host: str, broker_port: int = 1883):
        if not MQTT_AVAILABLE:
            raise ImportError("paho-mqtt required for CyberBricksController")
        self.host      = broker_host
        self.port      = broker_port
        self.client    = mqtt.Client()
        self.latest_state = {}
        self._state_event = Event()
        self._connected   = Event()
        self._setup_handlers()

    def _setup_handlers(self):
        def on_connect(client, userdata, flags, rc, properties=None):
            if rc == 0:
                log.info(f"Connected to MQTT broker {self.host}:{self.port}")
                self._connected.set()
                client.subscribe(self.STATE_TOPIC, qos=1)
            else:
                log.error(f"MQTT connect failed, rc={rc}")
                self._connected.clear()

        def on_message(client, userdata, msg):
            try:
                payload = json.loads(msg.payload.decode())
                self.latest_state.update(payload)
                self._state_event.set()
            except Exception as e:
                log.warning(f"Unexpected MQTT message: {e}")

        self.client.on_connect = on_connect
        self.client.on_message = on_message

    def connect(self, timeout: float = 10.0) -> bool:
        try:
            self.client.connect_async(self.host, self.port, keepalive=60)
            self.client.loop_start()
            if not self._connected.wait(timeout=timeout):
                raise TimeoutError(f"MQTT connection timeout after {timeout}s")
            return True
        except Exception as e:
            log.error(f"MQTT connection error: {e}")
            return False

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()

    def send_angle(self, joint: str, angle_deg: float, timeout: float = 5.0):
        """
        Send a joint angle command and wait for acknowledgement.
        Returns the acknowledged angle or None on timeout.
        """
        cmd = {
            "type":  "angle_cmd",
            "joint": joint,
            "angle": float(angle_deg),
        }
        self.client.publish(self.CMD_TOPIC, json.dumps(cmd), qos=1)
        log.info(f"Sent: {joint}={angle_deg:.1f}°")

        # Wait for acknowledgement
        self._state_event.clear()
        start = time.time()
        while time.time() - start < timeout:
            if self._state_event.wait(timeout=0.5):
                state_joint = self.latest_state.get("joint")
                state_angle = self.latest_state.get("angle")
                if state_joint == joint:
                    return state_angle
        log.warning(f"No acknowledgement for {joint}={angle_deg:.1f}° within {timeout}s")
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# 2. ESTIMATOR READER — reads estimated angles from joint_estimator
# ═══════════════════════════════════════════════════════════════════════════════

class EstimatorReader:
    """
    Reads the latest estimated joint angles from the running
    joint_estimator.py process.

    Two modes (priority order):
      1. MQTT subscribe on cyberbricks/joint_states  (recommended)
         — joint_estimator must be started with --mqtt
      2. HTTP GET on a local REST endpoint (future:
         joint_estimator --rest-port 8765)
    """

    def __init__(self,
                 mqtt_host: str = None,
                 rest_url: str  = None,
                 joint_names: list = None):
        self.joint_names = joint_names or ["base_rot", "shoulder", "elbow", "wrist"]
        self.latest = {j: None for j in self.joint_names}
        self._mqtt_client = None
        self._mqtt_event  = Event()
        self._rest_url    = rest_url
        self._mqtt_host   = mqtt_host

        if mqtt_host and MQTT_AVAILABLE:
            self._start_mqtt(mqtt_host)
        else:
            log.info("EstimatorReader: no MQTT host — angles will be "
                     "read from REST endpoint if --rest-url is provided")

    def _start_mqtt(self, host: str):
        def on_connect(client, userdata, flags, rc, properties=None):
            if rc == 0:
                client.subscribe("cyberbricks/joint_states", qos=1)
                log.info(f"Estimator reader subscribed to joint_states")
            else:
                log.warning(f"Estimator MQTT connect rc={rc}")

        def on_message(client, userdata, msg):
            try:
                payload = json.loads(msg.payload.decode())
                joints = payload.get("joints", {})
                for j, v in joints.items():
                    self.latest[j] = v
                self._mqtt_event.set()
            except Exception as e:
                log.warning(f"Estimator MQTT parse error: {e}")

        self._mqtt_client = mqtt.Client()
        self._mqtt_client.on_connect = on_connect
        self._mqtt_client.on_message = on_message
        try:
            self._mqtt_client.connect(host, 1883, keepalive=60)
            self._mqtt_client.loop_start()
        except Exception as e:
            log.warning(f"EstimatorReader MQTT connect failed: {e}")

    def read_angles(self, timeout: float = 3.0) -> dict:
        """
        Read the latest estimated angles for all joints.
        Waits up to `timeout` seconds for a new update.
        Returns dict of {joint_name: angle_deg or None}.
        """
        self._mqtt_event.clear()
        t_start = time.time()
        while time.time() - t_start < timeout:
            if self._mqtt_event.wait(timeout=0.5):
                break
        return dict(self.latest)

    def close(self):
        if self._mqtt_client:
            self._mqtt_client.loop_stop()
            self._mqtt_client.disconnect()


# ═══════════════════════════════════════════════════════════════════════════════
# 3. MOTION DELAY ESTIMATOR
# ═══════════════════════════════════════════════════════════════════════════════

def estimate_settle_time(joint: str, angle_delta_deg: float) -> float:
    """
    Heuristic motion settling time based on joint type and move distance.
    Cyber Bricks servos are typically 0.12–0.2 sec/60°.

    Override with --settle-time argument for precise calibration.
    """
    base_time  = 1.0      # minimum settle time (network + servo respond)
    per_deg    = 0.025    # extra seconds per degree of motion
    extra      = abs(angle_delta_deg) * per_deg
    return base_time + extra


# ═══════════════════════════════════════════════════════════════════════════════
# 4. TEST RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

class ClosedLoopTest:
    """
    Executes the closed-loop verification test protocol.

    For each (joint, commanded_angle) pair:
      1. Send command via MQTT to Cyber Bricks
      2. Wait for arm to settle
      3. Read visual estimate
      4. Compute error = |commanded − estimated|
      5. Record result
    """

    THRESHOLD_DEG = 5.0   # acceptance criterion

    def __init__(self,
                 controller: CyberBricksController,
                 reader: EstimatorReader,
                 settle_fn=None):
        self.ctrl    = controller
        self.reader  = reader
        self.settle_fn = settle_fn or (lambda j, d: 1.5)

        self.results = []    # list of dicts

    def run(self,
            joints: list,
            positions: list,
            repetitions: int = 1,
            home_first: bool = True) -> dict:
        """
        Run the full test suite.

        Args:
            joints:       list of joint names to test
            positions:    list of target angles in degrees
            repetitions:  repeat each position N times
            home_first:   move all joints to 90° home before starting

        Returns:
            summary dict with pass/fail and statistics
        """
        all_targets = [
            (joint, angle)
            for joint in joints
            for angle in positions
            for _ in range(repetitions)
        ]

        if home_first:
            log.info("Moving all joints to HOME (90°) before test...")
            for joint in ["base_rot", "shoulder", "elbow", "wrist"]:
                self.ctrl.send_angle(joint, 90.0)
            time.sleep(3.0)

        log.info(f"Starting closed-loop test: {len(all_targets)} measurements")
        log.info(f"  Joints:    {joints}")
        log.info(f"  Positions: {positions}")
        log.info(f"  Threshold: {self.THRESHOLD_DEG}°")

        prev_angles = {j: 90.0 for j in joints}   # track for settle estimation

        for step, (joint, target) in enumerate(all_targets, 1):
            log.info(f"--- Step {step}/{len(all_targets)}: "
                     f"{joint} → {target:.0f}° ---")

            # Send command
            ack = self.ctrl.send_angle(joint, target)
            if ack is None:
                log.error(f"Command failed for {joint}, skipping")
                self.results.append({
                    "step": step, "joint": joint,
                    "commanded": target, "estimated": None,
                    "error_deg": None, "pass": False,
                    "note": "no_ack"
                })
                continue

            # Estimate settle time
            delta = abs(target - (prev_angles.get(joint, 90.0)))
            settle = self.settle_fn(joint, delta)
            prev_angles[joint] = target
            log.info(f"Waiting {settle:.1f}s for arm to settle...")
            time.sleep(settle)

            # Read visual estimate
            est = self.reader.read_angles(timeout=3.0)
            estimated = est.get(joint)

            if estimated is None:
                log.error(f"No estimate received for {joint}, skipping")
                self.results.append({
                    "step": step, "joint": joint,
                    "commanded": target, "estimated": None,
                    "error_deg": None, "pass": False,
                    "note": "no_estimate"
                })
                continue

            # Compute error
            error = abs(target - estimated)
            passed = error < self.THRESHOLD_DEG

            self.results.append({
                "step":         step,
                "joint":        joint,
                "commanded":    target,
                "estimated":    round(estimated, 2),
                "error_deg":    round(error, 2),
                "pass":         passed,
            })

            status = "PASS" if passed else "FAIL"
            log.info(
                f"  Commanded: {target:6.1f}° | "
                f"Estimated: {estimated:6.1f}° | "
                f"Error: {error:5.2f}° | [{status}]"
            )

            # Small inter-measurement delay to let servo stabilise
            time.sleep(0.5)

        return self.summarise()

    def summarise(self) -> dict:
        """Compute aggregate statistics from self.results."""
        total      = len(self.results)
        passed_cnt = sum(1 for r in self.results if r["pass"])
        failed_cnt = total - passed_cnt

        errors = [r["error_deg"] for r in self.results
                  if r["error_deg"] is not None]

        summary = {
            "total_measurements": total,
            "passed":             passed_cnt,
            "failed":             failed_cnt,
            "pass_rate_pct":      round(100 * passed_cnt / total, 1)
                                 if total > 0 else 0,
            "threshold_deg":      self.THRESHOLD_DEG,
            "mean_error_deg":     round(statistics.mean(errors), 3)
                                 if errors else None,
            "max_error_deg":      round(max(errors), 3) if errors else None,
            "min_error_deg":      round(min(errors), 3) if errors else None,
            "std_error_deg":      round(statistics.stdev(errors), 3)
                                 if len(errors) > 1 else None,
            "per_joint": {},
            "per_position": {},
            "results":            self.results,
        }

        # Per-joint breakdown
        for joint in set(r["joint"] for r in self.results):
            j_results = [r for r in self.results if r["joint"] == joint]
            j_errors  = [r["error_deg"] for r in j_results
                         if r["error_deg"] is not None]
            j_passed  = sum(1 for r in j_results if r["pass"])
            summary["per_joint"][joint] = {
                "count":    len(j_results),
                "passed":   j_passed,
                "pass_pct": round(100 * j_passed / len(j_results), 1),
                "mean_err": round(statistics.mean(j_errors), 3) if j_errors else None,
            }

        # Per-position breakdown
        for pos in set(r["commanded"] for r in self.results):
            p_results = [r for r in self.results if r["commanded"] == pos]
            p_errors  = [r["error_deg"] for r in p_results
                         if r["error_deg"] is not None]
            p_passed  = sum(1 for r in p_results if r["pass"])
            summary["per_position"][int(pos)] = {
                "count":    len(p_results),
                "passed":   p_passed,
                "pass_pct": round(100 * p_passed / len(p_results), 1),
                "mean_err": round(statistics.mean(p_errors), 3) if p_errors else None,
            }

        return summary


# ═══════════════════════════════════════════════════════════════════════════════
# 5. REPORT GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def print_summary(summary: dict):
    """Pretty-print the test summary to console."""
    overall_pass = summary["failed"] == 0

    print("\n" + "═" * 65)
    print("  CLOSED-LOOP VERIFICATION — SUMMARY")
    print("═" * 65)
    print(f"  Total measurements : {summary['total_measurements']}")
    print(f"  Passed              : {summary['passed']}  "
          f"({summary['pass_rate_pct']}%)")
    print(f"  Failed              : {summary['failed']}")
    print(f"  Threshold           : {summary['threshold_deg']}°")
    print(f"  Mean error          : {summary['mean_error_deg']}°"
          if summary["mean_error_deg"] else "  Mean error          : N/A")
    print(f"  Max error           : {summary['max_error_deg']}°"
          if summary["max_error_deg"] else "  Max error           : N/A")
    print(f"  Std dev             : {summary['std_error_deg']}°"
          if summary["std_error_deg"] else "  Std dev             : N/A")
    print()
    print("  Per-joint:")
    for joint, s in summary["per_joint"].items():
        ok = "✅" if s["pass_pct"] == 100.0 else "⚠️ "
        print(f"    {ok} {joint:<12}  pass {s['pass_pct']:5.1f}%  "
              f"mean_err {str(s['mean_err'])+'°':>8}  n={s['count']}")
    print()
    print("  Per-position:")
    for pos, s in sorted(summary["per_position"].items()):
        ok = "✅" if s["pass_pct"] == 100.0 else "⚠️ "
        print(f"    {ok} {pos:4.0f}°   pass {s['pass_pct']:5.1f}%  "
              f"mean_err {str(s['mean_err'])+'°':>8}  n={s['count']}")
    print()
    verdict = "🎉  PASS — All measurements within 5°" if overall_pass \
              else "❌  FAIL — Some measurements exceed 5° error"
    print(f"  Verdict: {verdict}")
    print("═" * 65 + "\n")


def save_reports(summary: dict, report_dir: Path = REPORT_DIR):
    """Save detailed JSON and CSV reports."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # JSON
    json_path = report_dir / f"test_results_{ts}.json"
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2)
    log.info(f"JSON report saved: {json_path}")

    # CSV
    csv_path = report_dir / f"test_results_{ts}.csv"
    header = ["step", "joint", "commanded", "estimated",
              "error_deg", "pass", "note"]
    with open(csv_path, "w") as f:
        f.write(",".join(header) + "\n")
        for r in summary["results"]:
            row = [
                str(r.get("step", "")),
                r.get("joint", ""),
                str(r.get("commanded", "")),
                str(r.get("estimated", "")),
                str(r.get("error_deg", "")),
                str(r.get("pass", "")),
                r.get("note", ""),
            ]
            f.write(",".join(row) + "\n")
    log.info(f"CSV report saved: {csv_path}")

    return json_path, csv_path


# ═══════════════════════════════════════════════════════════════════════════════
# 6. MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Closed-loop verification for Cyber Bricks visual joint feedback"
    )
    parser.add_argument(
        "--mqtt-host",
        default=os.environ.get("MQTT_BROKER_HOST", "192.168.1.50"),
        help="Cyber Bricks MQTT broker host"
    )
    parser.add_argument(
        "--mqtt-port", type=int, default=1883,
        help="Cyber Bricks MQTT broker port"
    )
    parser.add_argument(
        "--joints",
        nargs="+",
        default=["shoulder", "elbow", "wrist"],
        choices=["base_rot", "shoulder", "elbow", "wrist"],
        help="Joints to test"
    )
    parser.add_argument(
        "--positions",
        type=float,
        nargs="+",
        default=[45.0, 90.0, 135.0],
        help="Target angles in degrees"
    )
    parser.add_argument(
        "--repetitions", type=int, default=1,
        help="Repeat each (joint, position) pair N times"
    )
    parser.add_argument(
        "--settle-time", type=float, default=None,
        help="Override fixed settle time (seconds)"
    )
    parser.add_argument(
        "--skip-home", action="store_true",
        help="Skip moving to home position before test"
    )
    parser.add_argument(
        "--no-mqtt-cmd", action="store_true",
        help="Simulate only (read angles, don't send commands)"
    )
    args = parser.parse_args()

    print("\n"
          "╔══════════════════════════════════════════════════╗\n"
          "║  Cyber Bricks Closed-Loop Visual Feedback Test   ║\n"
          "╚══════════════════════════════════════════════════╝\n")

    if args.no_mqtt_cmd:
        log.info("SIMULATION MODE — commands will NOT be sent")

    settle_fn = (lambda j, d: args.settle_time) \
        if args.settle_time else estimate_settle_time

    # ── Connect controller + reader ─────────────────────────────────────────
    if not args.no_mqtt_cmd and MQTT_AVAILABLE:
        ctrl = CyberBricksController(args.mqtt_host, args.mqtt_port)
        if not ctrl.connect(timeout=15.0):
            log.error("Could not connect to Cyber Bricks MQTT broker. Aborting.")
            sys.exit(1)
    else:
        ctrl = None

    reader = EstimatorReader(
        mqtt_host=args.mqtt_host if MQTT_AVAILABLE else None,
        joint_names=args.joints,
    )

    try:
        test = ClosedLoopTest(ctrl, reader, settle_fn=settle_fn)
        summary = test.run(
            joints=args.joints,
            positions=args.positions,
            repetitions=args.repetitions,
            home_first=not args.skip_home,
        )
    finally:
        reader.close()
        if ctrl:
            ctrl.disconnect()

    # ── Report ────────────────────────────────────────────────────────────────
    print_summary(summary)
    json_path, csv_path = save_reports(summary)

    # ── Exit code ─────────────────────────────────────────────────────────────
    if summary["failed"] > 0:
        sys.exit(1)   # at least one measurement exceeded threshold
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
