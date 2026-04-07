#!/usr/bin/env python3
"""
RTSP Stream Reader Module

Dependencies:
    pip install opencv-python
"""

from __future__ import annotations

import sys
import time
import logging
from typing import Optional, Tuple
from dataclasses import dataclass

try:
    import cv2
except ImportError:
    print("Error: opencv-python not installed")
    print("Please run: pip install opencv-python")
    sys.exit(1)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class StreamConfig:
    """Stream configuration dataclass"""
    rtsp_url: str
    reconnect_delay: float = 2.0
    max_reconnect_attempts: int = 5
    frame_timeout: float = 30.0


class StreamReader:
    """
    RTSP Stream Reader
    
    Usage:
        - Connect to RTSP video stream
        - Continuously read video frames
        - Auto-reconnect mechanism
    """
    
    def __init__(self, rtsp_url: str, config: Optional[StreamConfig] = None):
        """
        Initialize stream reader
        
        Args:
            rtsp_url: RTSP stream URL, e.g. rtsp://192.168.1.100:8554/stream
            config: Stream configuration (optional)
        """
        self.rtsp_url = rtsp_url
        self.config = config or StreamConfig(rtsp_url=rtsp_url)
        
        # OpenCV video capture object
        self._cap: Optional[cv2.VideoCapture] = None
        
        # Connection state
        self._is_connected: bool = False
        self._reconnect_count: int = 0
        
        # Initialize connection
        self._connect()
    
    def _connect(self) -> bool:
        """
        Establish RTSP connection
        
        Returns:
            Whether connection succeeded
        """
        # Release existing connection
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        
        # Create new video capture object
        self._cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
        
        # Check if connection succeeded
        if not self._cap.isOpened():
            logger.error(f"Failed to open RTSP stream: {self.rtsp_url}")
            self._is_connected = False
            return False
        
        self._is_connected = True
        self._reconnect_count = 0
        logger.info(f"Connected to RTSP stream: {self.rtsp_url}")
        return True
    
    def read_frame(self) -> Optional[Tuple[bool, cv2.Mat]]:
        """
        Read next frame
        
        Returns:
            (success, frame) on success, None on disconnect
            - Returns (True, frame) on success
            - Returns (False, None) on read failure
            - Returns None on connection lost
        """
        if self._cap is None or not self._is_connected:
            return (False, None)
        
        # Read frame
        ret, frame = self._cap.read()
        
        # Check if frame is valid
        if not ret or frame is None:
            logger.warning("Frame read failed, attempting reconnect...")
            if not self._reconnect():
                return None
            # Try reading again after reconnect
            ret, frame = self._cap.read()
            if not ret or frame is None:
                return None
        
        return (ret, frame)
    
    def _reconnect(self) -> bool:
        """
        Attempt to reconnect
        
        Returns:
            Whether reconnection succeeded
        """
        # Check reconnect attempts
        if self._reconnect_count >= self.config.max_reconnect_attempts:
            logger.error(f"Max reconnect attempts ({self.config.max_reconnect_attempts}) reached")
            self._is_connected = False
            return False
        
        self._reconnect_count += 1
        logger.info(f"Attempting reconnect ({self._reconnect_count}/{self.config.max_reconnect_attempts})...")
        
        # Wait before reconnecting
        time.sleep(self.config.reconnect_delay)
        
        return self._connect()
    
    def is_connected(self) -> bool:
        """
        Check connection status
        
        Returns:
            Whether currently connected
        """
        return self._is_connected and self._cap is not None and self._cap.isOpened()
    
    def get_frame_width(self) -> int:
        """Get video frame width"""
        if self._cap is not None:
            return int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        return 0
    
    def get_frame_height(self) -> int:
        """Get video frame height"""
        if self._cap is not None:
            return int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return 0
    
    def get_fps(self) -> float:
        """Get video frame rate"""
        if self._cap is not None:
            return self._cap.get(cv2.CAP_PROP_FPS)
        return 0.0
    
    def release(self) -> None:
        """
        Release resources
        
        Important: Must call this method after use to release connection
        """
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        self._is_connected = False
        logger.info("RTSP stream resources released")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release()
        return False


def create_stream_reader(
    rtsp_url: str,
    reconnect_delay: float = 2.0,
    max_reconnect_attempts: int = 5
) -> StreamReader:
    """
    Convenience function to create a stream reader
    
    Args:
        rtsp_url: RTSP stream URL
        reconnect_delay: Reconnect delay in seconds
        max_reconnect_attempts: Maximum reconnect attempts
    
    Returns:
        StreamReader instance
    """
    config = StreamConfig(
        rtsp_url=rtsp_url,
        reconnect_delay=reconnect_delay,
        max_reconnect_attempts=max_reconnect_attempts
    )
    return StreamReader(rtsp_url, config)


# Main program test
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="RTSP stream reader test tool")
    parser.add_argument(
        "rtsp_url",
        nargs="?",
        default="rtsp://localhost:8554/stream",
        help="RTSP stream URL (default: rtsp://localhost:8554/stream)"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of frames to read (default: 10)"
    )
    
    args = parser.parse_args()
    
    print(f"Testing RTSP stream: {args.rtsp_url}")
    print(f"Reading frames: {args.count}")
    print("-" * 40)
    
    reader = create_stream_reader(args.rtsp_url)
    
    try:
        for i in range(args.count):
            result = reader.read_frame()
            
            if result is None:
                print(f"Frame {i+1}: Connection lost")
                break
            
            ret, frame = result
            
            if ret and frame is not None:
                width = reader.get_frame_width()
                height = reader.get_frame_height()
                fps = reader.get_fps()
                print(f"Frame {i+1}: OK - {width}x{height} @ {fps:.2f}fps")
            else:
                print(f"Frame {i+1}: Read failed")
            
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    
    finally:
        reader.release()
        print("Resources released")
