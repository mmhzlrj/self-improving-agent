#!/usr/bin/env python3
"""
ESP32-Cam Calibration for Cyber Bricks Joint Feedback
========================================================
Purpose:
    Calibrate the ESP32-Cam (OV2640) mounted in a fixed position above
    the Cyber Bricks robot arm. Establish the camera's intrinsic parameters
    (focal length, principal point, distortion) and extrinsic relationship
    to the robot base frame.

Hardware setup:
    - ESP32-Cam (OV2640) mounted in a fixed overhead position
    - Cyber Bricks arm at home position during calibration
    - A calibration target (chessboard or ArUco grid) placed on the base

Method (方案E from Q2 research — geometric calibration + visual markers):
    1. Capture a chessboard image to compute camera intrinsics
    2. Place ArUco markers at known positions on the arm links
    3. Record marker 2D→3D correspondences to compute the
       camera-to-robot-base homography / perspective transform
    4. Save all calibration data to a JSON file for the estimator

Usage:
    python3 calibrate.py --mode intrinsics   # One-time intrinsic calibration
    python3 calibrate.py --mode extrinsics  # After intrinsics are known

Requirements:
    pip install opencv-python numpy opencv-contrib-python
"""

import cv2
import numpy as np
import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

# ─── Paths ───────────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).parent
CALIB_FILE   = SCRIPT_DIR / "calibration_data.json"
INTRINSICS_FILE = SCRIPT_DIR / "intrinsics.npz"

# ─── ArUco dictionary (used for extrinsic calibration) ────────────────────────
ARUCO_DICT   = cv2.aruco.Dictionary_get(cv2.aruco.DICT_6X6_250)
ARUCO_PARAMS = cv2.aruco.DetectorParameters_create()

# Default chessboard parameters (11×8 inner corners — adjust to your board)
DEFAULT_CHESSBOARD = (11, 8)   # columns, rows
SQUARE_SIZE_MM     = 25.4      # square side length in mm (1 inch)

# Known ArUco marker IDs placed on each robot link (customise to your setup)
# marker_id → (link_name, local_offset_mm_from_previous_joint)
LINK_MARKERS = {
    0: ("base",      (0,   0,   0)),
    1: ("shoulder",  (0,   50,  0)),
    2: ("elbow",     (0,   80,  0)),
    3: ("wrist",     (0,   60,  0)),
}


# ═══════════════════════════════════════════════════════════════════════════════
# 1. INTRINSIC CALIBRATION
# ═══════════════════════════════════════════════════════════════════════════════

def capture_chessboard_frames(rtsp_url: str, chessboard: tuple,
                                num_samples: int = 20,
                                output_dir: str = "./calib_frames") -> list:
    """
    Continuously read frames from the RTSP stream and collect
    chessboard images until we have `num_samples` valid detections.

    Returns:
        List of (frame, corners) tuples.
    """
    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open RTSP stream: {rtsp_url}")

    samples = []
    display = "Press SPACE to capture, ESC to finish early"

    print(f"[calibrate] Streaming from {rtsp_url}")
    print(f"[calibrate] Place the chessboard in view, press SPACE to capture frames ({num_samples} needed)")

    while len(samples) < num_samples:
        ret, frame = cap.read()
        if not ret:
            print("[calibrate] Frame grab failed, retrying...")
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        found, corners = cv2.findChessboardCorners(gray, chessboard, None)

        vis = frame.copy()
        if found:
            cv2.drawChessboardCorners(vis, chessboard, corners, found)
            cv2.putText(vis, f"Capture {len(samples)+1}/{num_samples}", (10, 30),
                         cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        else:
            cv2.putText(vis, "No chessboard detected", (10, 30),
                         cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        cv2.putText(vis, display, (10, frame.shape[0] - 20),
                     cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.imshow("Calibration capture", vis)
        key = cv2.waitKey(1) & 0xFF

        if key == 32:  # SPACE
            if found:
                # Refine corner locations with sub-pixel accuracy
                criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
                            30, 0.001)
                corners_refined = cv2.cornerSubPix(gray, corners, (5, 5),
                                                    (-1, -1), criteria)
                samples.append((frame.copy(), corners_refined))
                fname = os.path.join(output_dir, f"chess_{len(samples):03d}.png")
                cv2.imwrite(fname, frame)
                print(f"[calibrate] Captured {len(samples)}/{num_samples}")
            else:
                print("[calibrate] Chessboard not found — try again")
        elif key == 27:  # ESC
            break

    cap.release()
    cv2.destroyAllWindows()

    if len(samples) < 3:
        raise RuntimeError(f"Only {len(samples)} valid samples — need at least 3")
    return samples


def compute_intrinsics(samples: list, chessboard: tuple,
                         square_size: float = SQUARE_SIZE_MM) -> dict:
    """
    Run OpenCV camera calibration on collected chessboard samples.

    Returns a dict with: mtx (3×3), dist (1×5), rvecs, tvecs.
    """
    objp = np.zeros((chessboard[0] * chessboard[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:chessboard[0], 0:chessboard[1]].T.reshape(-1, 2)
    objp *= square_size / 1000.0   # convert mm → m for SI consistency

    objpoints = [objp] * len(samples)
    imgpoints = [s[1] for s in samples]

    # Use a representative image size from the first sample
    img_size = samples[0][0].shape[1::-1]

    print("[calibrate] Running OpenCV calibrateCamera...")
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
        objpoints, imgpoints, img_size, None, None
    )

    if ret < 0:
        raise RuntimeError(f"Calibration failed with RMS error: {ret}")

    print(f"[calibrate] RMS re-projection error: {ret:.4f} pixels")
    print(f"[calibrate] Camera matrix:\n{mtx}")
    print(f"[calibrate] Distortion coefficients:\n{dist}")

    # Save as npz for efficient loading
    np.savez(INTRINSICS_FILE,
             mtx=mtx, dist=dist, rvecs=rvecs, tvecs=tvecs,
             img_size=img_size, chessboard=chessboard,
             square_size=square_size)
    print(f"[calibrate] Intrinsics saved to {INTRINSICS_FILE}")

    return {
        "rms_error": float(ret),
        "camera_matrix": mtx.tolist(),
        "dist_coeffs": dist.tolist(),
        "img_width": img_size[0],
        "img_height": img_size[1],
        "chessboard": chessboard,
        "square_size_mm": square_size,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 2. EXTRINSIC CALIBRATION (camera-to-robot-base)
# ═══════════════════════════════════════════════════════════════════════════════

def load_intrinsics() -> tuple:
    """Load previously computed intrinsics from npz file."""
    if not INTRINSICS_FILE.exists():
        raise FileNotFoundError(
            f"Intrinsics file not found: {INTRINSICS_FILE}\n"
            "Run with --mode intrinsics first."
        )
    data = np.load(INTRINSICS_FILE, allow_pickle=True)
    return data["mtx"], data["dist"], tuple(data["chessboard"])


def estimate_marker_pose(rvec, tvec) -> np.ndarray:
    """Convert rvec/tvec to a 4×4 homogeneous transform matrix."""
    R, _ = cv2.Rodrigues(rvec)
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = tvec.flatten()
    return T


def compute_extrinsics_from_markers(rtsp_url: str) -> dict:
    """
    Using the overhead camera view, detect ArUco markers placed on each
    arm link at a known reference pose (arm in 'home' position).

    The perspective-n-point (PnP) solver gives us the 6-DOF pose of each
    marker in the camera frame.  By providing the known 3D positions of
    the markers in the robot base frame (LINK_MARKERS),
    we compute the homogeneous transform H_camera_base.

    This H allows us to project any robot-base 3D point into the image,
    and conversely to back-project detected 2D points into the base frame
    for geometric IK.
    """
    mtx, dist, _ = load_intrinsics()
    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open RTSP stream: {rtsp_url}")

    # Known 3D positions of each marker in the ROBOT BASE frame (metres)
    # These must be measured with a caliper from your physical setup.
    # Format: marker_id → (x, y, z) in metres relative to base origin
    MARKER_3D_BASE = {
        0: np.array([0.000,  0.000,  0.000]),   # marker 0 at base origin
        1: np.array([0.000,  0.050,  0.000]),   # marker 1 — 50 mm above base
        2: np.array([0.000,  0.130,  0.000]),   # marker 2 — 80 mm above marker 1
        3: np.array([0.000,  0.190,  0.000]),   # marker 3 — 60 mm above marker 2
    }

    # Marker physical size (mm) — change to match your printed markers
    MARKER_SIZE_MM = 30.0

    detected_poses = {}   # marker_id → (rvec, tvec)
    display = "Click markers in order, then press ENTER. ESC to cancel."

    print("[calibrate] Extrinsic calibration — ensure arm is at HOME position.")
    print("[calibrate] Point camera at arm, markers should be clearly visible.")
    print("[calibrate] When ready, press ENTER to capture.")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, rejected = cv2.aruco.detectMarkers(
            gray, ARUCO_DICT, parameters=ARUCO_PARAMS
        )

        vis = cv2.aruco.drawDetectedMarkers(frame.copy(), corners, ids)

        # Estimate pose for each detected marker
        for i, marker_id in enumerate(ids.flatten()):
            if marker_id in MARKER_3D_BASE:
                objp = np.array([[0, 0, 0],
                                 [MARKER_SIZE_MM/1000, 0, 0],
                                 [MARKER_SIZE_MM/1000, MARKER_SIZE_MM/1000, 0],
                                 [0, MARKER_SIZE_MM/1000, 0]], dtype=np.float32)
                success, rvec, tvec = cv2.solvePnP(
                    objp, corners[i], mtx, dist,
                    flags=cv2.SOLVEPNP_ITERATIVE
                )
                if success:
                    detected_poses[marker_id] = (rvec, tvec)
                    # Draw axes for visual confirmation
                    cv2.drawFrameAxes(vis, mtx, dist, rvec, tvec,
                                      length=MARKER_SIZE_MM / 1000 * 3)

        # Show pose estimates on screen
        y = 30
        for mid, (rv, tv) in detected_poses.items():
            text = f"Marker {mid}: x={tv[0][0]:.3f} y={tv[1][0]:.3f} z={tv[2][0]:.3f}m"
            cv2.putText(vis, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (0, 255, 0), 1)
            y += 20

        cv2.imshow("Extrinsic Calibration", vis)
        key = cv2.waitKey(1) & 0xFF
        if key == 13:  # ENTER — capture
            break
        elif key == 27:
            cap.release()
            cv2.destroyAllWindows()
            sys.exit(0)

    cap.release()
    cv2.destroyAllWindows()

    if len(detected_poses) < 2:
        raise RuntimeError(
            "Need at least 2 markers for extrinsic calibration; "
            f"only {len(detected_poses)} detected."
        )

    # ── Compute camera-to-base transform H_camera_base ──────────────────────
    # Strategy: for each marker we have:
    #   - 3D position in base frame  : P_base
    #   - estimated 3D position in camera frame : P_cam = H_camera_base @ P_base
    #
    # We collect all (P_base, P_cam) pairs and use Umeyama alignment
    # (rigid / similarity transform) to find H_camera_base.

    P_base_list = []
    P_cam_list  = []

    for mid, (rvec, tvec) in detected_poses.items():
        P_base = MARKER_3D_BASE[mid]
        R_cam, _ = cv2.Rodrigues(rvec)
        P_cam = (R_cam @ P_base + tvec.flatten()).reshape(3)
        P_base_list.append(P_base)
        P_cam_list.append(P_cam)

    P_base_arr = np.array(P_base_list, dtype=np.float64)   # N×3
    P_cam_arr  = np.array(P_cam_list,  dtype=np.float64)   # N×3

    # Umeyama gives the optimal similarity transform (scale, R, t)
    # that maps P_base → P_cam.  Since we expect unit metres on both sides,
    # scale should be ≈ 1.
    scale, R_opt, t_opt, _ = cv2.estimateAffinePartial3D(
        P_base_arr, P_cam_arr, method=cv2.LMEDS
    )
    if scale is None:
        raise RuntimeError("Umeyama alignment failed — check marker positions")

    print(f"[calibrate] Umeyama scale: {scale[0][0]:.4f} (expect ~1.0)")
    print(f"[calibrate] Optimal rotation:\n{R_opt}")
    print(f"[calibrate] Optimal translation: {t_opt.flatten()}")

    # Convert 3×4 affine to 4×4 homogeneous
    H_camera_base = np.eye(4, dtype=np.float64)
    H_camera_base[:3, :3] = R_opt
    H_camera_base[:3,  3] = t_opt.flatten()

    # Its inverse (base → camera) is often useful
    H_base_camera = np.linalg.inv(H_camera_base)

    return {
        "H_camera_base": H_camera_base.tolist(),  # transforms BASE → CAMERA
        "H_base_camera": H_base_camera.tolist(),  # transforms CAMERA → BASE
        "detected_marker_count": len(detected_poses),
        "detected_marker_ids": list(detected_poses.keys()),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 3. SAVE FULL CALIBRATION
# ═══════════════════════════════════════════════════════════════════════════════

def save_calibration(intrinsics: dict, extrinsics: dict):
    """Merge intrinsics + extrinsics into a single JSON file."""
    combined = {
        "calibration_timestamp": datetime.now().isoformat(),
        "intrinsics": intrinsics,
        "extrinsics": extrinsics,
        "marker_link_mapping": {str(k): v for k, v in LINK_MARKERS.items()},
    }
    with open(CALIB_FILE, "w") as f:
        json.dump(combined, f, indent=2)
    print(f"[calibrate] Full calibration saved to {CALIB_FILE}")


def load_calibration() -> dict:
    """Load the full calibration file, or raise if missing."""
    if not CALIB_FILE.exists():
        raise FileNotFoundError(
            f"Calibration file not found: {CALIB_FILE}\n"
            "Run calibration first: python3 calibrate.py --mode intrinsics && "
            "python3 calibrate.py --mode extrinsics"
        )
    with open(CALIB_FILE) as f:
        return json.load(f)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="ESP32-Cam calibration for Cyber Bricks joint feedback"
    )
    parser.add_argument(
        "--mode", choices=["intrinsics", "extrinsics", "full"],
        default="full",
        help=(
            "intrinsics: compute camera intrinsics from chessboard (one-time, "
            "results cached)  |  "
            "extrinsics: compute camera-to-robot transform  |  "
            "full: both steps"
        )
    )
    parser.add_argument(
        "--rtsp",
        default=os.environ.get("ESP32_CAM_RTSP",
                               "rtsp://192.168.1.100:8554/mjpeg/1"),
        help="RTSP URL for the ESP32-Cam stream"
    )
    parser.add_argument(
        "--chessboard", default=None,
        help="Chessboard size as 'cols,rows' (default: 11,8)"
    )
    parser.add_argument(
        "--samples", type=int, default=20,
        help="Number of chessboard samples for intrinsics"
    )
    args = parser.parse_args()

    chessboard = tuple(map(int, args.chessboard.split(","))) \
        if args.chessboard else DEFAULT_CHESSBOARD

    if args.mode in ("intrinsics", "full"):
        print("=" * 60)
        print("STEP 1: INTRINSIC CALIBRATION")
        print("=" * 60)
        samples = capture_chessboard_frames(
            args.rtsp, chessboard, num_samples=args.samples
        )
        intrinsics = compute_intrinsics(samples, chessboard)

    if args.mode in ("extrinsics", "full"):
        print("=" * 60)
        print("STEP 2: EXTRINSIC CALIBRATION")
        print("=" * 60)
        extrinsics = compute_extrinsics_from_markers(args.rtsp)

        # Load intrinsics to merge
        if args.mode == "full":
            with open(INTRINSICS_FILE, "rb") as f:
                intr = np.load(f, allow_pickle=True)
            intrinsics = {
                "camera_matrix": intr["mtx"].tolist(),
                "dist_coeffs": intr["dist"].tolist(),
                "img_width": int(intr["img_size"][0]),
                "img_height": int(intr["img_size"][1]),
            }

        save_calibration(intrinsics, extrinsics)
        print("[calibrate] Calibration complete!")


if __name__ == "__main__":
    main()
