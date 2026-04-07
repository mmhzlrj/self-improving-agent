#!/usr/bin/env python3
"""
Jetson YOLO 检测主脚本
用于在 Jetson 设备上运行 YOLO 目标检测

支持功能:
- 图像/视频文件检测
- USB 摄像头实时检测
- RTSP 流检测
- 检测结果可视化与保存
"""

import sys
import os
import argparse
import time
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

# 导入 YOLO (ultralytics)
# 如果未安装, 请运行: pip install ultralytics
try:
    from ultralytics import YOLO
except ImportError:
    print("Error: ultralytics 未安装")
    print("请运行: pip install ultralytics")
    sys.exit(1)

# 导入 OpenCV
try:
    import cv2
except ImportError:
    print("Error: opencv-python 未安装")
    print("请运行: pip install opencv-python")
    sys.exit(1)


class YOLODetector:
    """YOLO 目标检测器类"""
    
    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        device: str = "0",  # CUDA 设备, "cpu" 或 "0"
        verbose: bool = False
    ):
        """
        初始化 YOLO 检测器
        
        Args:
            model_path: 模型权重路径
            conf_threshold: 置信度阈值
            iou_threshold: NMS IOU 阈值
            device: 运行设备 ("cpu" 或 CUDA 设备号)
            verbose: 是否输出详细信息
        """
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.device = device
        self.verbose = verbose
        
        # 加载模型
        self.model = None
        self._load_model()
        
    def _load_model(self) -> None:
        """加载 YOLO 模型"""
        try:
            if self.verbose:
                print(f"Loading model from {self.model_path}...")
            
            self.model = YOLO(self.model_path)
            
            # 移动到指定设备
            if self.device != "cpu":
                self.model.to(self.device)
                
            if self.verbose:
                print(f"Model loaded successfully on device: {self.device}")
                
        except Exception as e:
            print(f"Error loading model: {e}")
            raise
            
    def detect_image(
        self,
        image_path: str,
        save_path: Optional[str] = None,
        show_result: bool = False
    ) -> List[Dict[str, Any]]:
        """
        检测单张图像
        
        Args:
            image_path: 图像路径
            save_path: 检测结果保存路径 (可选)
            show_result: 是否显示结果窗口
            
        Returns:
            检测结果列表
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")
            
        try:
            # 执行检测
            results = self.model.predict(
                source=image_path,
                conf=self.conf_threshold,
                iou=self.iou_threshold,
                verbose=self.verbose
            )
            
            # 解析结果
            detections = self._parse_results(results)
            
            # 保存结果图像
            if save_path:
                if len(results) > 0:
                    results[0].save(filename=save_path)
                    
            # 显示结果
            if show_result:
                if len(results) > 0:
                    results[0].show()
                    
            return detections
            
        except Exception as e:
            print(f"Error detecting image: {e}")
            raise
            
    def detect_video(
        self,
        video_path: str,
        output_path: Optional[str] = None,
        display: bool = True,
        save_frames: bool = False,
        frames_dir: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        检测视频文件
        
        Args:
            video_path: 视频路径
            output_path: 输出视频路径 (可选)
            display: 是否显示实时检测结果
            save_frames: 是否保存检测到的帧
            frames_dir: 保存帧的目录
            
        Returns:
            所有帧的检测结果列表
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")
            
        try:
            # 打开视频
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Cannot open video: {video_path}")
                
            # 获取视频信息
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            if self.verbose:
                print(f"Video info: {width}x{height} @ {fps}fps")
                
            # 创建输出视频写入器
            writer = None
            if output_path:
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
                
            # 创建帧保存目录
            if save_frames and frames_dir:
                os.makedirs(frames_dir, exist_ok=True)
                
            all_detections = []
            frame_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                frame_count += 1
                
                # 执行检测 (使用 YOLO 的 predict 处理 numpy 数组)
                results = self.model.predict(
                    source=frame,
                    conf=self.conf_threshold,
                    iou=self.iou_threshold,
                    verbose=False
                )
                
                # 解析结果
                detections = self._parse_results(results)
                all_detections.append({
                    'frame': frame_count,
                    'detections': detections
                })
                
                # 可视化结果
                if len(results) > 0:
                    annotated_frame = results[0].plot()
                    
                    # 保存帧
                    if save_frames and frames_dir:
                        frame_path = os.path.join(frames_dir, f"frame_{frame_count:06d}.jpg")
                        cv2.imwrite(frame_path, annotated_frame)
                    
                    # 写入输出视频
                    if writer is not None:
                        writer.write(annotated_frame)
                        
                    # 显示
                    if display:
                        cv2.imshow('YOLO Detection', annotated_frame)
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break
                            
                if self.verbose and frame_count % 30 == 0:
                    print(f"Processed {frame_count} frames...")
                    
            # 释放资源
            cap.release()
            if writer is not None:
                writer.release()
            if display:
                cv2.destroyAllWindows()
                
            return all_detections
            
        except Exception as e:
            print(f"Error detecting video: {e}")
            raise
            
    def detect_camera(
        self,
        camera_index: int = 0,
        display: bool = True,
        save_video: bool = False,
        output_path: Optional[str] = None
    ) -> None:
        """
        检测 USB 摄像头实时流
        
        Args:
            camera_index: 摄像头索引
            display: 是否显示实时检测结果
            save_video: 是否保存检测视频
            output_path: 输出视频路径
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")
            
        try:
            # 打开摄像头
            cap = cv2.VideoCapture(camera_index)
            if not cap.isOpened():
                raise ValueError(f"Cannot open camera {camera_index}")
                
            # 设置分辨率 (可选)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            # 创建视频写入器
            writer = None
            if save_video and output_path:
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                writer = cv2.VideoWriter(output_path, fourcc, 30, (640, 480))
                
            fps_counter = 0
            start_time = time.time()
            
            if self.verbose:
                print("Starting camera detection... Press 'q' to quit")
                
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Failed to grab frame")
                    break
                    
                # 执行检测
                results = self.model.predict(
                    source=frame,
                    conf=self.conf_threshold,
                    iou=self.iou_threshold,
                    verbose=False
                )
                
                # 可视化
                if len(results) > 0:
                    annotated_frame = results[0].plot()
                else:
                    annotated_frame = frame
                    
                # 计算 FPS
                fps_counter += 1
                elapsed = time.time() - start_time
                fps = fps_counter / elapsed if elapsed > 0 else 0
                
                # 添加 FPS 显示
                cv2.putText(
                    annotated_frame,
                    f"FPS: {fps:.1f}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2
                )
                
                # 保存
                if writer is not None:
                    writer.write(annotated_frame)
                    
                # 显示
                if display:
                    cv2.imshow('YOLO Camera Detection', annotated_frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                        
            # 释放资源
            cap.release()
            if writer is not None:
                writer.release()
            if display:
                cv2.destroyAllWindows()
                
            if self.verbose:
                print(f"Average FPS: {fps:.1f}")
                
        except Exception as e:
            print(f"Error detecting camera: {e}")
            raise
            
    def detect_rtsp(
        self,
        rtsp_url: str,
        display: bool = True,
        save_video: bool = False,
        output_path: Optional[str] = None
    ) -> None:
        """
        检测 RTSP 流
        
        Args:
            rtsp_url: RTSP 流地址
            display: 是否显示实时检测结果
            save_video: 是否保存检测视频
            output_path: 输出视频路径
        """
        # RTSP 也是视频流, 复用 video 检测逻辑
        if self.model is None:
            raise RuntimeError("Model not loaded")
            
        try:
            # 打开 RTSP 流
            cap = cv2.VideoCapture(rtsp_url)
            if not cap.isOpened():
                raise ValueError(f"Cannot open RTSP stream: {rtsp_url}")
                
            # 获取视频信息
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            
            if self.verbose:
                print(f"RTSP Stream: {width}x{height} @ {fps}fps")
                
            # 创建视频写入器
            writer = None
            if save_video and output_path:
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
                
            if self.verbose:
                print("Starting RTSP detection... Press 'q' to quit")
                
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("RTSP stream disconnected, retrying...")
                    time.sleep(1)
                    cap = cv2.VideoCapture(rtsp_url)
                    continue
                    
                # 执行检测
                results = self.model.predict(
                    source=frame,
                    conf=self.conf_threshold,
                    iou=self.iou_threshold,
                    verbose=False
                )
                
                # 可视化
                if len(results) > 0:
                    annotated_frame = results[0].plot()
                else:
                    annotated_frame = frame
                    
                # 保存
                if writer is not None:
                    writer.write(annotated_frame)
                    
                # 显示
                if display:
                    cv2.imshow('YOLO RTSP Detection', annotated_frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                        
            # 释放资源
            cap.release()
            if writer is not None:
                writer.release()
            if display:
                cv2.destroyAllWindows()
                
        except Exception as e:
            print(f"Error detecting RTSP: {e}")
            raise
            
    def _parse_results(self, results) -> List[Dict[str, Any]]:
        """
        解析 YOLO 检测结果
        
        Args:
            results: YOLO 预测结果
            
        Returns:
            解析后的检测结果列表
        """
        detections = []
        
        if results is None or len(results) == 0:
            return detections
            
        result = results[0]
        
        # 获取检测框、类别、置信度
        boxes = result.boxes
        if boxes is None:
            return detections
            
        for i in range(len(boxes)):
            box = boxes[i]
            
            # 获取边界框坐标
            xyxy = box.xyxy[0].cpu().numpy()  # x1, y1, x2, y2
            
            # 获取类别和置信度
            cls_id = int(box.cls[0].cpu().numpy())
            conf = float(box.conf[0].cpu().numpy())
            
            # 获取类别名称
            class_name = result.names[cls_id] if result.names else str(cls_id)
            
            detection = {
                'class_id': cls_id,
                'class_name': class_name,
                'confidence': conf,
                'bbox': {
                    'x1': float(xyxy[0]),
                    'y1': float(xyxy[1]),
                    'x2': float(xyxy[2]),
                    'y2': float(xyxy[3])
                }
            }
            
            detections.append(detection)
            
        return detections
        
    def export_model(self, format: str = "onnx", save_dir: str = "exported") -> str:
        """
        导出模型到其他格式
        
        Args:
            format: 导出格式 (onnx, torchscript, tflite, etc.)
            save_dir: 保存目录
            
        Returns:
            导出的模型路径
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")
            
        try:
            export_path = self.model.export(format=format, dir=save_dir)
            if self.verbose:
                print(f"Model exported to: {export_path}")
            return export_path
            
        except Exception as e:
            print(f"Error exporting model: {e}")
            raise


def parse_arguments() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="Jetson YOLO 目标检测脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 检测单张图像
  python detect.py --source image.jpg --model yolov8n.pt
  
  # 检测视频文件
  python detect.py --source video.mp4 --output result.mp4
  
  # 摄像头实时检测
  python detect.py --source camera --display
  
  # RTSP 流检测
  python detect.py --source rtsp://192.168.1.100:554/stream
        """
    )
    
    # 模型参数
    parser.add_argument(
        '--model', '-m',
        type=str,
        default='yolov8n.pt',
        help='YOLO 模型路径或名称 (default: yolov8n.pt)'
    )
    parser.add_argument(
        '--conf', '-c',
        type=float,
        default=0.25,
        help='置信度阈值 (default: 0.25)'
    )
    parser.add_argument(
        '--iou', '-i',
        type=float,
        default=0.45,
        help='NMS IOU 阈值 (default: 0.45)'
    )
    parser.add_argument(
        '--device', '-d',
        type=str,
        default='0',
        help='运行设备: cpu 或 CUDA 设备号 (default: 0)'
    )
    
    # 输入源
    parser.add_argument(
        '--source', '-s',
        type=str,
        required=True,
        help='输入源: 图像路径、视频路径、camera、或 RTSP URL'
    )
    
    # 输出选项
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='输出视频路径 (default: None)'
    )
    parser.add_argument(
        '--save-dir',
        type=str,
        default=None,
        help='保存检测帧的目录'
    )
    parser.add_argument(
        '--save-image',
        action='store_true',
        help='保存检测结果图像'
    )
    parser.add_argument(
        '--display', '-v',
        action='store_true',
        help='显示检测结果窗口'
    )
    
    # 其他选项
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='输出详细信息'
    )
    parser.add_argument(
        '--export',
        type=str,
        default=None,
        help='导出模型格式 (onnx, torchscript, etc.)'
    )
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_arguments()
    
    # 打印配置信息
    print("=" * 50)
    print("Jetson YOLO 检测器")
    print("=" * 50)
    print(f"Model: {args.model}")
    print(f"Source: {args.source}")
    print(f"Confidence: {args.conf}")
    print(f"IOU: {args.iou}")
    print(f"Device: {args.device}")
    print("=" * 50)
    
    try:
        # 创建检测器
        detector = YOLODetector(
            model_path=args.model,
            conf_threshold=args.conf,
            iou_threshold=args.iou,
            device=args.device,
            verbose=args.verbose
        )
        
        # 导出模型
        if args.export:
            print(f"Exporting model to {args.export} format...")
            export_path = detector.export_model(format=args.export)
            print(f"Exported to: {export_path}")
            return
            
        # 根据输入源类型执行检测
        source = args.source.lower()
        
        if source == 'camera':
            # USB 摄像头检测
            detector.detect_camera(
                camera_index=0,
                display=args.display,
                save_video=args.output is not None,
                output_path=args.output
            )
            
        elif source.startswith('rtsp://') or source.startswith('rtsps://'):
            # RTSP 流检测
            detector.detect_rtsp(
                rtsp_url=args.source,
                display=args.display,
                save_video=args.output is not None,
                output_path=args.output
            )
            
        elif os.path.isfile(args.source):
            # 检测文件 (图像或视频)
            file_ext = Path(args.source).suffix.lower()
            
            if file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.webp']:
                # 图像检测
                save_path = args.output if args.save_image else None
                detections = detector.detect_image(
                    image_path=args.source,
                    save_path=save_path,
                    show_result=args.display
                )
                print(f"检测到 {len(detections)} 个目标")
                
                for det in detections:
                    print(f"  - {det['class_name']}: {det['confidence']:.2f}")
                    
            elif file_ext in ['.mp4', '.avi', '.mov', '.mkv']:
                # 视频检测
                detections = detector.detect_video(
                    video_path=args.source,
                    output_path=args.output,
                    display=args.display,
                    save_frames=args.save_dir is not None,
                    frames_dir=args.save_dir
                )
                print(f"处理了 {len(detections)} 帧")
                
            else:
                print(f"Error: 不支持的文件格式: {file_ext}")
                sys.exit(1)
                
        else:
            print(f"Error: 无法找到文件或无效的输入源: {args.source}")
            sys.exit(1)
            
        print("检测完成!")
        
    except KeyboardInterrupt:
        print("\n用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
