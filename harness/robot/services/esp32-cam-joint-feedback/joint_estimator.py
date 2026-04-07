#!/usr/bin/env python3
"""
Joint Angle Estimator — ESP32-Cam + OpenCV + Geometric IK
============================================================
Purpose:
    Receive RTSP video stream from the ESP32-Cam (OV2640) mounted
    overhead the Cyber Bricks arm, detect ArUco markers placed on
    each joint/link, and use geometric inverse kinematics to estimate
    the actual joint angles in real-time.

Hardware:
    - ESP32-Cam running RTSP server (default: rtsp://<cam-ip>:8554/mjpeg/1)
    - Jetson Nano 2GB running this script
    - Cyber Bricks arm (4-DOF: base, shoulder, elbow, wrist)

Architecture (参考 Q2方案E — geometric visual servo):
    ┌──────────────┐    RTSP     ┌───────────────────┐
    │  ESP32-Cam  │────────────▶│   Jetson Nano 2GB  │
    │  (OV2640)   │             │   joint_estimator  │
    └──────────────┘             └──────┬────────────┘
                                         │  estimated angles
                                         ▼
                              Cyber Bricks MQTT controller

Calibration prerequisite:
    python3 calibrate.py --mode full
    → produces calibration_data.json

Output:
    - Terminal: live joint angle estimates (degrees)
    - MQTT topic: cyberbricks/joint_states (JSON)
    - Optional: annotated video preview window

Usage:
    # Basic — prints to stdout
    python3 joint_estimator.py --rtsp rtsp://192.168.1.100:8554/mjpeg/1

    # With MQTT publishing (requires paho-mqtt)
    python3 joint_estimator.py --mqtt --mqtt-host 192.168.1.50

    # Headless (no preview window, for Jetson Nano SSH)
    python3 joint_estimator.py --headless
"""

import cv2
import numpy as np
import json
import math
import time
import os
import sys
import argparse
import logging
from pathlib import Path
from threading import Thread, Event
from typing import Optional

# ─── Optional MQTT ─────────────────────────────────────────────────────────────
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    print("[WARN] paho-mqtt not installed; MQTT output disabled.")

# ─── Paths ───────────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).parent
CALIB_FILE   = SCRIPT_DIR / "calibration_data.json"

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("joint_estimator")


# ═══════════════════════════════════════════════════════════════════════════════
# 1. ARUCO DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

# ArUco dictionary — must match what was used during calibration
ARUCO_DICT   = cv2.aruco.Dictionary_get(cv2.aruco.DICT_6X6_250)
ARUCO_PARAMS = cv2.aruco.DetectorParameters_create()

# Physical size of ArUco markers in metres (measure with caliper)
MARKER_SIZE_M = 0.030


class MarkerDetector:
    """
    Detects and estimates the 6-DOF pose of ArUco markers in each frame.
    Thread-safe: detection runs in the worker thread, results are
    read by the main thread.
    """

    def __init__(self, camera_matrix, dist_coeffs, marker_size: float = MARKER_SIZE_M):
        self.mtx  = np.array(camera_matrix, dtype=np.float64)
        self.dist = np.array(dist_coeffs,    dtype=np.float64)
        self.marker_size = marker_size

        # 3D object points for a single marker (square in XY plane, Z=0)
        half = marker_size / 2.0
        self.objp = np.array([
            [-half, -half, 0],
            [ half, -half, 0],
            [ half,  half, 0],
            [-half,  half, 0],
        ], dtype=np.float32)

    def detect(self, frame: np.ndarray) -> dict:
        """
        Detect all visible ArUco markers and return their poses.

        Returns:
            {
                marker_id: {
                    "rvec": np.ndarray (3×1),
                    "tvec": np.ndarray (3×1)  — position in CAMERA frame (metres),
                    "corners": np.ndarray     — 2D image points
                }
            }
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, rejected = cv2.aruco.detectMarkers(
            gray, ARUCO_DICT, parameters=ARUCO_PARAMS
        )

        if ids is None or len(ids) == 0:
            return {}

        results = {}
        for i, marker_id in enumerate(ids.flatten()):
            success, rvec, tvec = cv2.solvePnP(
                self.objp, corners[i],
                self.mtx, self.dist,
                flags=cv2.SOLVEPNP_ITERATIVE
            )
            if success:
                results[marker_id] = {
                    "rvec": rvec,            # rotation vector (cam frame)
                    "tvec": tvec,            # translation  (cam frame, metres)
                    "corners": corners[i],  # 2D image coords (4×2)
                }

        return results


# ═══════════════════════════════════════════════════════════════════════════════
# 2. GEOMETRIC INVERSE KINEMATICS
# ═══════════════════════════════════════════════════════════════════════════════

class CyberBricksKinematics:
    """
    Geometric IK solver for the Cyber Bricks 4-DOF arm.

    DOF layout (base → tip):
        0. BASE_ROT   — rotation around vertical Z axis   (servos: 0–180°)
        1. SHOULDER   — pitch of the shoulder joint         (servos: 0–180°)
        2. ELBOW      — pitch of the elbow joint             (servos: 0–180°)
        3. WRIST      — pitch of the wrist joint             (servos: 0–180°)

    Link lengths (metres) — measure with a caliper and update these constants:
        L0: base height above table
        L1: shoulder-to-elbow link length
        L2: elbow-to-wrist link length
        L3: wrist-to-fingertip (gripper) length
    """

    def __init__(self,
                 L0: float = 0.060,
                 L1: float = 0.085,
                 L2: float = 0.065,
                 L3: float = 0.055):
        self.L0 = L0   # shoulder height
        self.L1 = L1   # upper arm
        self.L2 = L2   # forearm
        self.L3 = L3   # gripper

        # Home pose angles (degrees) when the arm is fully extended downward
        self.HOME_ANGLES = {
            "base_rot":  90,
            "shoulder":  90,
            "elbow":      0,
            "wrist":      0,
        }

    def estimate_from_3d_points(self,
                                 marker_tvecs: dict,
                                 H_base_camera: np.ndarray) -> dict:
        """
        Given detected marker 3D positions in the camera frame and the
        camera→base transform, estimate each joint angle using pure geometry.

        marker_tvecs: {marker_id: tvec (3×1 ndarray, camera frame, metres)}
        H_base_camera: 4×4 homogeneous transform from camera frame to base frame

        Returns:
            {"base_rot": float, "shoulder": float, "elbow": float, "wrist": float}
            All angles in degrees.
        """
        angles = {}
        try:
            # ── BASE_ROTATION ──────────────────────────────────────────────
            # The base marker (id=0) is at the arm's vertical axis.
            # In the base frame its XY position should be (0,0).
            # The detected XY position in the camera frame tells us how
            # much the camera is offset from the axis → base rotation.

            if 0 in marker_tvecs:
                p_cam = marker_tvecs[0].flatten()
                p_base = self._transform_point(p_cam, H_base_camera)
                # atan2(y, x) gives the base rotation angle
                angles["base_rot"] = math.degrees(math.atan2(p_base[0], p_base[1]))
            else:
                angles["base_rot"] = None

            # ── SHOULDER ───────────────────────────────────────────────────
            # Shoulder marker (id=1) should be L1 above the shoulder joint.
            # We compare its measured height in the base frame vs its
            # expected height when shoulder=90°.
            if 1 in marker_tvecs:
                p_cam = marker_tvecs[1].flatten()
                p_base = self._transform_point(p_cam, H_base_camera)
                # Expected Z at shoulder = L0 + L1*sin(shoulder_angle)
                # Rearranged: shoulder = asin((z - L0) / L1)
                sin_shoulder = (p_base[2] - self.L0) / self.L1
                sin_shoulder = np.clip(sin_shoulder, -1.0, 1.0)
                angles["shoulder"] = 90.0 - math.degrees(math.asin(sin_shoulder))
            else:
                angles["shoulder"] = None

            # ── ELBOW ─────────────────────────────────────────────────────
            # Elbow marker (id=2) sits L2 from shoulder + L1 from base.
            # We use the 2D image projection angle (dx, dy in base XY plane).
            if 2 in marker_tvecs and 1 in marker_tvecs:
                p1_cam = marker_tvecs[1].flatten()
                p2_cam = marker_tvecs[2].flatten()
                p1_base = self._transform_point(p1_cam, H_base_camera)
                p2_base = self._transform_point(p2_cam, H_base_camera)

                # 3D vector from shoulder to elbow in base frame
                vec_shoulder_elbow = p2_base - p1_base
                link_len_measured = np.linalg.norm(vec_shoulder_elbow)

                # law of cosines: angle at elbow
                # cos(elbow) = (L1² + L2² - |vec|²) / (2*L1*L2)
                cos_elbow = (
                    self.L1**2 + self.L2**2 - link_len_measured**2
                ) / (2 * self.L1 * self.L2)
                cos_elbow = np.clip(cos_elbow, -1.0, 1.0)
                angles["elbow"] = 180.0 - math.degrees(math.acos(cos_elbow))
            else:
                angles["elbow"] = None

            # ── WRIST ───────────────────────────────────────────────────────
            # Wrist marker (id=3) extends L3 from elbow.
            # We compute the total arm extension angle and subtract
            # shoulder + elbow to get wrist compensation.
            if 3 in marker_tvecs and 2 in marker_tvecs:
                p2_cam = marker_tvecs[2].flatten()
                p3_cam = marker_tvecs[3].flatten()
                p2_base = self._transform_point(p2_cam, H_base_camera)
                p3_base = self._transform_point(p3_cam, H_base_camera)

                vec_elbow_wrist = p3_base - p2_base
                # Angle of forearm relative to horizontal
                forearm_angle = math.degrees(
                    math.atan2(vec_elbow_wrist[2],
                               math.sqrt(vec_elbow_wrist[0]**2 +
                                         vec_elbow_wrist[1]**2))
                )
                # Wrist angle: difference between forearm direction and
                # the shoulder-elbow plane
                if 1 in marker_tvecs:
                    p1_base = self._transform_point(
                        marker_tvecs[1].flatten(), H_base_camera)
                    vec_shoulder = p2_base - p1_base
                    upper_arm_angle = math.degrees(
                        math.atan2(vec_shoulder[2],
                                    math.sqrt(vec_shoulder[0]**2 +
                                              vec_shoulder[1]**2))
                    )
                    angles["wrist"] = forearm_angle - upper_arm_angle
                else:
                    angles["wrist"] = None
            else:
                angles["wrist"] = None

        except Exception as e:
            log.warning(f"IK computation error: {e}")
            return {}

        return angles

    def _transform_point(self, pt: np.ndarray, H: np.ndarray) -> np.ndarray:
        """Apply 4×4 homogeneous transform to a 3D point."""
        pt_h = np.append(pt, 1.0)          # 4-vector
        result = H @ pt_h                  # 4-vector
        return result[:3]                  # back to 3-vector


    # ── Alternative: 2D image-plane estimation (when 3D fails) ────────────────

    def estimate_from_2d(self,
                         marker_corners: dict,
                         camera_matrix,
                         H_base_camera: np.ndarray,
                         known_link_pixels: tuple = None) -> dict:
        """
        Fallback IK using only the 2D image when depth estimation is noisy.

        marker_corners: {marker_id: 4×2 ndarray of corner pixels}
        camera_matrix:  3×3 intrinsic matrix
        known_link_pixels: (L1_px, L2_px) — measured pixel lengths of links
                          at the calibration pose.

        This method approximates 3D by assuming the arm lies in a plane
        perpendicular to the camera's optical axis.
        """
        # Compute the 2D centre of each marker (representative pixel position)
        centers_2d = {}
        for mid, corners in marker_corners.items():
            centers_2d[mid] = corners.mean(axis=0)  # 2×1

        focal_length = camera_matrix[0, 0]
        angles = {}

        # Base rotation: project marker-0 onto X-axis of base frame
        if 0 in centers_2d:
            cx, cy = centers_2d[0]
            angles["base_rot"] = math.degrees(
                math.atan2(cx - camera_matrix[0, 2],
                            focal_length)
            )
        else:
            angles["base_rot"] = None

        # Shoulder: use the vertical pixel displacement between marker 0 and 1
        if 0 in centers_2d and 1 in centers_2d:
            dy = centers_2d[1][1] - centers_2d[0][1]
            # dy (pixels) → angle based on focal length
            angles["shoulder"] = 90.0 - math.degrees(math.atan2(dy, focal_length))
        else:
            angles["shoulder"] = None

        # Elbow: pixel distance between marker 1 and 2 → relative angle change
        if 1 in centers_2d and 2 in centers_2d:
            dx = centers_2d[2][0] - centers_2d[1][0]
            dy = centers_2d[2][1] - centers_2d[1][1]
            elbow_delta = math.degrees(math.atan2(dy, dx))
            if angles.get("shoulder") is not None:
                angles["elbow"] = elbow_delta - angles["shoulder"]
            else:
                angles["elbow"] = elbow_delta
        else:
            angles["elbow"] = None

        angles["wrist"] = None  # requires wrist marker
        return angles


# ═══════════════════════════════════════════════════════════════════════════════
# 3. RTSP STREAM READER (background thread)
# ═══════════════════════════════════════════════════════════════════════════════

class RTSPReader:
    """
    Background thread that continuously reads frames from the RTSP stream.
    Prevents VideoCapture buffering from causing frame drops.
    """

    def __init__(self, rtsp_url: str, buffer_size: int = 1):
        self.url       = rtsp_url
        self.buffer    = buffer_size
        self.frame     = None
        self.running   = Event()
        self._thread   = None

    def start(self):
        self.running.set()
        self._thread = Thread(target=self._read_loop, daemon=True)
        self._thread.start()
        log.info(f"RTSP reader started: {self.url}")

    def stop(self):
        self.running.clear()
        if self._thread:
            self._thread.join(timeout=3)
        log.info("RTSP reader stopped")

    def _read_loop(self):
        cap = cv2.VideoCapture(self.url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, self.buffer)

        # Retry logic for stream reconnection
        retry_delay = 1.0
        max_retries = 10

        while self.running.is_set():
            ret, frame = cap.read()
            if ret:
                self.frame = frame
                retry_delay = 1.0   # reset on success
            else:
                log.warning(f"Frame grab failed, retrying in {retry_delay:.1f}s...")
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 30)
                cap.release()
                cap = cv2.VideoCapture(self.url)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, self.buffer)

        cap.release()

    def get_frame(self) -> Optional[np.ndarray]:
        return self.frame


# ═══════════════════════════════════════════════════════════════════════════════
# 4. MQTT PUBLISHER
# ═══════════════════════════════════════════════════════════════════════════════

class AnglePublisher:
    """Lightweight MQTT publisher for estimated joint angles."""

    def __init__(self, host: str, port: int = 1883,
                 topic: str = "cyberbricks/joint_states",
                 qos: int = 1):
        if not MQTT_AVAILABLE:
            raise ImportError("paho-mqtt not installed")
        self.host   = host
        self.port   = port
        self.topic  = topic
        self.qos    = qos
        self.client = mqtt.Client()
        self.client.connect(host, port, keepalive=60)
        log.info(f"Connected to MQTT broker {host}:{port}")

    def publish(self, angles: dict, timestamp: float = None):
        payload = {
            "timestamp": timestamp or time.time(),
            "joints": {
                k: round(v, 2) if v is not None else None
                for k, v in angles.items()
            }
        }
        self.client.publish(self.topic, json.dumps(payload), qos=self.qos)

    def close(self):
        self.client.disconnect()


# ═══════════════════════════════════════════════════════════════════════════════
# 5. MAIN ESTIMATOR CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class JointEstimator:
    """
    Top-level estimator that ties together:
      - RTSP stream reader
      - ArUco marker detector
      - Geometric IK solver
      - MQTT publisher (optional)

    Usage:
        est = JointEstimator(rtsp_url="rtsp://192.168.1.100:8554/mjpeg/1",
                             calib_path="calibration_data.json")
        est.start()
        # ... read est.angles ...
        est.stop()
    """

    def __init__(self,
                 rtsp_url: str,
                 calib_path: str = str(CALIB_FILE),
                 link_lengths: tuple = (0.060, 0.085, 0.065, 0.055),
                 mqtt_host: str = None,
                 mqtt_topic: str = "cyberbricks/joint_states",
                 preview: bool = True,
                 headless: bool = False):
        self.rtsp_url   = rtsp_url
        self.preview    = preview and not headless
        self.running    = Event()
        self.angles     = {}           # latest estimated angles
        self.lock       = __import__("threading").Lock()

        # ── Load calibration ────────────────────────────────────────────────
        if not Path(calib_path).exists():
            raise FileNotFoundError(
                f"Calibration file not found: {calib_path}\n"
                "Run: python3 calibrate.py --mode full"
            )
        with open(calib_path) as f:
            calib = json.load(f)

        self.mtx        = np.array(calib["intrinsics"]["camera_matrix"])
        self.dist        = np.array(calib["intrinsics"]["dist_coeffs"])
        self.H_base_camera = np.array(calib["extrinsics"]["H_base_camera"])

        log.info(f"Loaded calibration from {calib_path}")
        log.info(f"  Image size: {calib['intrinsics']['img_width']}x"
                 f"{calib['intrinsics']['img_height']}")

        # ── Initialise components ───────────────────────────────────────────
        L0, L1, L2, L3 = link_lengths
        self.detector   = MarkerDetector(self.mtx, self.dist)
        self.ik         = CyberBricksKinematics(L0, L1, L2, L3)
        self.reader     = RTSPReader(rtsp_url)

        # ── MQTT ─────────────────────────────────────────────────────────────
        self.mqtt_pub   = None
        if mqtt_host and MQTT_AVAILABLE:
            try:
                self.mqtt_pub = AnglePublisher(
                    host=mqtt_host, topic=mqtt_topic
                )
            except Exception as e:
                log.warning(f"MQTT connection failed: {e}")

    def start(self):
        self.running.set()
        self.reader.start()
        self._worker_thread = __import__("threading").Thread(
            target=self._loop, daemon=True
        )
        self._worker_thread.start()
        log.info("Joint estimator started")

    def stop(self):
        self.running.clear()
        self.reader.stop()
        if self.mqtt_pub:
            self.mqtt_pub.close()
        log.info("Joint estimator stopped")

    @property
    def latest_angles(self) -> dict:
        with self.lock:
            return dict(self.angles)

    def _loop(self):
        """
        Main processing loop — runs at camera frame rate (~30 fps).
        Detection and IK are the bottleneck on Jetson Nano 2GB,
        but OV2640 at 640×480 is manageable.
        """
        frame_count = 0
        fps_smooth  = 0.0
        t_last      = time.time()

        while self.running.is_set():
            frame = self.reader.get_frame()
            if frame is None:
                time.sleep(0.01)
                continue

            t_now = time.time()
            dt    = t_now - t_last
            t_last = t_now
            fps_smooth = 0.9 * fps_smooth + 0.1 * (1.0 / dt) if dt > 0 else 0.0
            frame_count += 1

            # ── Detect ArUco markers ─────────────────────────────────────────
            try:
                marker_poses = self.detector.detect(frame)
            except Exception as e:
                log.warning(f"Detection error: {e}")
                marker_poses = {}

            # Extract tvecs (camera frame, metres) for IK
            marker_tvecs = {
                mid: data["tvec"]
                for mid, data in marker_poses.items()
            }
            marker_corners = {
                mid: data["corners"].reshape(4, 2)
                for mid, data in marker_poses.items()
            }

            # ── Geometric IK ─────────────────────────────────────────────────
            if len(marker_tvecs) >= 2:
                angles = self.ik.estimate_from_3d_points(
                    marker_tvecs, self.H_base_camera
                )
                # Fill missing joints with 2D fallback
                if None in angles.values():
                    angles_2d = self.ik.estimate_from_2d(
                        marker_corners, self.mtx, self.H_base_camera
                    )
                    for joint, val in angles_2d.items():
                        if angles.get(joint) is None:
                            angles[joint] = val
            elif len(marker_tvecs) == 1:
                angles = self.ik.estimate_from_2d(
                    marker_corners, self.mtx, self.H_base_camera
                )
            else:
                angles = {}

            with self.lock:
                self.angles = angles

            # ── MQTT publish ─────────────────────────────────────────────────
            if self.mqtt_pub and frame_count % 3 == 0:  # throttled to ~10 Hz
                try:
                    self.mqtt_pub.publish(angles, timestamp=t_now)
                except Exception as e:
                    log.warning(f"MQTT publish error: {e}")

            # ── Preview window ──────────────────────────────────────────────
            if self.preview:
                self._draw_preview(frame, marker_poses, angles, fps_smooth)

        if self.preview:
            cv2.destroyAllWindows()

    def _draw_preview(self, frame: np.ndarray,
                       marker_poses: dict,
                       angles: dict,
                       fps: float):
        """Draw detection overlay and angle readout on the frame."""
        # Draw detected markers
        vis = cv2.aruco.drawDetectedMarkers(
            frame.copy(),
            [data["corners"] for data in marker_poses.values()]
            if marker_poses else [],
            np.array([[mid] for mid in marker_poses.keys()])
            if marker_poses else None,
        )

        # Draw frame axes for each marker
        for mid, data in marker_poses.items():
            try:
                cv2.drawFrameAxes(
                    vis, self.mtx, self.dist,
                    data["rvec"], data["tvec"],
                    length=0.05
                )
            except Exception:
                pass

        # ── Overlay angle text ───────────────────────────────────────────────
        y = 30
        for joint, angle in angles.items():
            if angle is not None:
                text = f"{joint}: {angle:6.1f}°"
            else:
                text = f"{joint}:   N/A"
            cv2.putText(vis, text, (10, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                        (0, 255, 0) if angle is not None else (0, 0, 255), 1)
            y += 22

        cv2.putText(vis, f"FPS: {fps:.1f}", (10, frame.shape[0] - 10),
                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

        cv2.imshow("Cyber Bricks Joint Estimator", vis)
        cv2.waitKey(1)   # 1 ms = up to 1000 fps display, no actual busy-wait


# ═══════════════════════════════════════════════════════════════════════════════
# 6. CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="ESP32-Cam Joint Angle Estimator for Cyber Bricks"
    )
    parser.add_argument(
        "--rtsp",
        default=os.environ.get(
            "ESP32_CAM_RTSP", "rtsp://192.168.1.100:8554/mjpeg/1"
        ),
        help="RTSP URL for the ESP32-Cam stream"
    )
    parser.add_argument(
        "--calib",
        default=str(CALIB_FILE),
        help="Path to calibration_data.json"
    )
    parser.add_argument(
        "--mqtt",
        action="store_true",
        help="Enable MQTT angle publishing"
    )
    parser.add_argument(
        "--mqtt-host",
        default=os.environ.get("MQTT_BROKER_HOST", "192.168.1.50"),
        help="MQTT broker host"
    )
    parser.add_argument(
        "--mqtt-topic",
        default="cyberbricks/joint_states",
        help="MQTT topic for joint angle messages"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Disable preview window (for SSH/headless mode)"
    )
    parser.add_argument(
        "--L0", type=float, default=0.060,
        help="Base height above table (metres)"
    )
    parser.add_argument(
        "--L1", type=float, default=0.085,
        help="Shoulder-to-elbow link length (metres)"
    )
    parser.add_argument(
        "--L2", type=float, default=0.065,
        help="Elbow-to-wrist link length (metres)"
    )
    parser.add_argument(
        "--L3", type=float, default=0.055,
        help="Wrist-to-fingertip link length (metres)"
    )
    args = parser.parse_args()

    log.info("Cyber Bricks Joint Estimator")
    log.info(f"  RTSP: {args.rtsp}")
    log.info(f"  Calibration: {args.calib}")
    log.info(f"  Headless: {args.headless}")
    log.info(f"  MQTT: {args.mqtt_host if args.mqtt else 'disabled'}")

    estimator = JointEstimator(
        rtsp_url=args.rtsp,
        calib_path=args.calib,
        link_lengths=(args.L0, args.L1, args.L2, args.L3),
        mqtt_host=args.mqtt_host if args.mqtt else None,
        mqtt_topic=args.mqtt_topic,
        headless=args.headless,
    )

    try:
        estimator.start()
        print("\n[ joint_estimator ] Running. Press Ctrl+C to stop.\n")
        while True:
            time.sleep(5)
            angles = estimator.latest_angles
            if angles:
                log.info(f"Current angles: "
                         + " | ".join(f"{k}={v:.1f}°" if v else f"{k}=N/A"
                                      for k, v in angles.items()))
    except KeyboardInterrupt:
        print("\n[ joint_estimator ] Shutting down...")
    finally:
        estimator.stop()


if __name__ == "__main__":
    main()
