"""
H2C Python 控制脚本
功能：连接 H2C（LAN Mode），上传文件，打印控制，状态监控，开关门控制
依赖：pip install bambulabs_api
"""

import time
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Callable

# TODO: 安装依赖
# pip install bambulabs_api

try:
    from bambulabs_api import Printer, BambuCloud
except ImportError:
    raise ImportError("请先安装: pip install bambulabs_api")

# ============================================================
# 配置（用户需要填写）
# ============================================================

# TODO: 填入你的 H2C 打印机信息
H2C_HOST = "192.168.x.x"        # 打印机局域网 IP
H2C_ACCESS_CODE = "xxxx"        # LAN Mode 访问码（打印机屏幕设置里查看）
H2C_SERIAL = "H2CXXXX"          # 打印机序列号

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("H2C")


# ============================================================
# H2C 控制器
# ============================================================

class H2CController:
    """拓竹 H2C 打印机控制器（LAN Mode + MQTT）"""

    def __init__(
        self,
        host: str = H2C_HOST,
        access_code: str = H2C_ACCESS_CODE,
        serial: str = H2C_SERIAL,
        config_path: Optional[str] = None,
    ):
        self.host = host
        self.access_code = access_code
        self.serial = serial
        self._printer: Optional[Printer] = None
        self._connected = False

        # 可选：从配置文件加载
        if config_path:
            self._load_config(config_path)

    def _load_config(self, path: str):
        """从 JSON 配置文件加载"""
        with open(path) as f:
            cfg = json.load(f)
        self.host = cfg["printer"]["host"]
        self.access_code = cfg["printer"]["access_code"]
        self.serial = cfg["printer"]["serial"]

    # ------------------------------------------------------------
    # 连接管理
    # ------------------------------------------------------------

    def connect(self, retries: int = 3, delay: float = 2.0) -> bool:
        """
        连接打印机（LAN Mode + MQTT）
        Linux Bug #8980：发送打印任务时 50% 概率崩溃，
        因此连接本身做了重试保护。
        """
        for attempt in range(1, retries + 1):
            try:
                logger.info(f"[{attempt}/{retries}] 连接 H2C @{self.host} ...")
                self._printer = Printer(self.host, self.access_code, self.serial)
                self._printer.connect()
                self._connected = True
                logger.info("✅ H2C 连接成功")
                return True
            except Exception as e:
                logger.warning(f"连接失败: {e}")
                if attempt < retries:
                    time.sleep(delay)
                else:
                    logger.error("❌ 连接失败，请检查 IP / 访问码 / 网络")
                    return False

    def disconnect(self):
        """断开连接"""
        if self._printer:
            try:
                self._printer.disconnect()
            except Exception:
                pass
            self._connected = False
            logger.info("已断开连接")

    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._connected

    # ------------------------------------------------------------
    # 文件上传和打印
    # ------------------------------------------------------------

    def upload_and_print(
        self,
        gcode_path: str,
        plate_index: int = 0,
        retries: int = 5,
        retry_delay: float = 5.0,
        progress_callback: Optional[Callable[[Dict], None]] = None,
    ) -> bool:
        """
        上传 .gcode.3mf 并开始打印。

        Linux Bug #8980 workaround:
        - 每次 send print job 有 ~50% 概率崩溃（Studio 无响应）
        - 这里做最多 retries 次重试，每次之间等待 retry_delay 秒
        - Linux 上建议通过 REST API 上传文件规避 MQTT 崩溃问题

        Args:
            gcode_path:   .gcode.3mf 文件路径
            plate_index:  打印板编号（0-3）
            retries:      重试次数
            retry_delay:  重试间隔（秒）
            progress_callback: 每秒回调，传入状态字典

        Returns:
            True = 打印任务成功下发
        """
        gcode_path = Path(gcode_path)
        if not gcode_path.exists():
            raise FileNotFoundError(f"文件不存在: {gcode_path}")

        for attempt in range(1, retries + 1):
            try:
                logger.info(
                    f"[{attempt}/{retries}] 上传 {gcode_path.name} 并开始打印 ..."
                )
                # upload_and_print 会自动开始打印
                self._printer.upload_and_print(
                    str(gcode_path),
                    plate_idx=plate_index,
                    time_lapse=False,
                    progress_callback=progress_callback,
                )
                logger.info(f"✅ 打印任务已下发: {gcode_path.name}")
                return True

            except Exception as e:
                logger.warning(f"下发失败 ({attempt}/{retries}): {e}")
                if attempt < retries:
                    logger.info(f"等待 {retry_delay}s 后重试 ...")
                    time.sleep(retry_delay)
                    # 重连再试
                    self.disconnect()
                    time.sleep(2)
                    self.connect()
                else:
                    logger.error(
                        f"❌ 重试 {retries} 次后仍失败。"
                        " 建议：手动通过 Bambu Studio 发送，或检查 LAN Mode 设置"
                    )
                    return False

    def send_print_job(
        self,
        gcode_path: str,
        plate_index: int = 0,
        retries: int = 5,
        retry_delay: float = 5.0,
    ) -> bool:
        """
        仅上传文件，不自动开始打印（先上传，再手动在打印机上选板开始）
        """
        gcode_path = Path(gcode_path)
        if not gcode_path.exists():
            raise FileNotFoundError(f"文件不存在: {gcode_path}")

        for attempt in range(1, retries + 1):
            try:
                logger.info(f"[{attempt}/{retries}] 上传 {gcode_path.name} ...")
                self._printer.send_file(str(gcode_path), plate_idx=plate_index)
                logger.info("✅ 文件上传成功")
                return True
            except Exception as e:
                logger.warning(f"上传失败 ({attempt}/{retries}): {e}")
                if attempt < retries:
                    time.sleep(retry_delay)
                else:
                    logger.error("❌ 文件上传失败")
                    return False

    # ------------------------------------------------------------
    # 打印控制
    # ------------------------------------------------------------

    def pause(self) -> bool:
        """暂停打印"""
        try:
            self._printer.pause()
            logger.info("⏸ 打印已暂停")
            return True
        except Exception as e:
            logger.error(f"暂停失败: {e}")
            return False

    def resume(self) -> bool:
        """恢复打印"""
        try:
            self._printer.resume()
            logger.info("▶ 打印已恢复")
            return True
        except Exception as e:
            logger.error(f"恢复失败: {e}")
            return False

    def cancel(self) -> bool:
        """取消打印"""
        try:
            self._printer.cancel()
            logger.info("⏹ 打印已取消")
            return True
        except Exception as e:
            logger.error(f"取消失败: {e}")
            return False

    # ------------------------------------------------------------
    # 门控制
    # ------------------------------------------------------------

    def open_door(self) -> bool:
        """
        开门（H2C 有前门，可通过 MQTT 触发）
        注意：部分固件版本可能不支持远程开门
        """
        try:
            self._printer.open_door()
            logger.info("🚪 门已打开")
            return True
        except Exception as e:
            logger.warning(f"开门失败（固件可能不支持）: {e}")
            return False

    def close_door(self) -> bool:
        """关门"""
        try:
            self._printer.close_door()
            logger.info("🚪 门已关闭")
            return True
        except Exception as e:
            logger.warning(f"关门失败: {e}")
            return False

    # ------------------------------------------------------------
    # 状态监控
    # ------------------------------------------------------------

    def get_status(self) -> Dict[str, Any]:
        """获取完整状态"""
        try:
            info = self._printer.get_status()
            return self._parse_status(info)
        except Exception as e:
            logger.error(f"获取状态失败: {e}")
            return {}

    def _parse_status(self, raw) -> Dict[str, Any]:
        """解析状态对象为可读字典"""
        status = {}
        try:
            # 打印进度
            status["progress"] = getattr(raw, "progress", 0)  # 0-100
            status["layer"] = getattr(raw, "layer", None)
            status["total_layer"] = getattr(raw, "total_layer", None)
            status["remaining_time"] = getattr(raw, "time_remaining", None)  # 秒
            status["print_speed"] = getattr(raw, "print_speed", None)

            # 温度
            status["nozzle_temp"] = getattr(raw, "nozzle_temp", None)
            status["nozzle_target"] = getattr(raw, "nozzle_target_temp", None)
            status["bed_temp"] = getattr(raw, "bed_temp", None)
            status["bed_target"] = getattr(raw, "bed_target_temp", None)

            # 状态
            status["job_id"] = getattr(raw, "job_id", None)
            status["gcode_state"] = getattr(raw, "gcode_state", None)  # RUNNING/PAUSED/OFF
            status["subtask_id"] = getattr(raw, "subtask_id", None)

        except Exception as e:
            logger.warning(f"状态解析异常: {e}")

        return status

    def monitor(
        self,
        interval: float = 2.0,
        on_complete: Optional[Callable[[], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ):
        """
        实时监控打印状态，持续输出温度/进度/剩余时间。
        按 Ctrl+C 停止。

        Args:
            interval:       轮询间隔（秒）
            on_complete:    打印完成回调
            on_error:       异常回调
        """
        logger.info("开始监控打印状态（Ctrl+C 停止）...")
        last_layer = None
        try:
            while True:
                status = self.get_status()
                state = status.get("gcode_state", "UNKNOWN")

                # 完成检测
                if state in ("FINISH", "FINISHED", "COMPLETE"):
                    logger.info("✅ 打印完成！")
                    if on_complete:
                        on_complete()
                    break

                # 只在关键节点打日志（避免刷屏）
                layer = status.get("layer")
                if layer != last_layer:
                    progress = status.get("progress", 0)
                    remaining = status.get("remaining_time")
                    remaining_str = self._format_time(remaining) if remaining else "?"

                    nozzle = status.get("nozzle_temp", "?")
                    nozzle_t = status.get("nozzle_target", "?")
                    bed = status.get("bed_temp", "?")
                    bed_t = status.get("bed_target", "?")

                    logger.info(
                        f"  进度 {progress:.1f}% | 层 {layer}/{status.get('total_layer','?')} "
                        f"| 剩余 {remaining_str} "
                        f"| 喷嘴 {nozzle:.0f}/{nozzle_t}°C | 床 {bed:.0f}/{bed_t}°C"
                    )
                    last_layer = layer

                time.sleep(interval)

        except KeyboardInterrupt:
            logger.info("监控中断")
        except Exception as e:
            logger.error(f"监控异常: {e}")
            if on_error:
                on_error(str(e))

    # ------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------

    @staticmethod
    def _format_time(seconds: Optional[int]) -> str:
        """秒 → H:MM:SS 或 M:SS"""
        if seconds is None:
            return "?"
        h, rem = divmod(int(seconds), 3600)
        m, s = divmod(rem, 60)
        if h > 0:
            return f"{h}h {m:02d}m"
        return f"{m}m {s:02d}s"


# ============================================================
# 便捷 CLI 入口
# ============================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="H2C 控制脚本")
    parser.add_argument("--config", default="config.json", help="配置文件路径")
    parser.add_argument("--gcode", help="上传并打印的 .gcode.3mf 文件")
    parser.add_argument("--monitor", action="store_true", help="仅监控状态")
    parser.add_argument("--pause", action="store_true", help="暂停打印")
    parser.add_argument("--resume", action="store_true", help="恢复打印")
    parser.add_argument("--cancel", action="store_true", help="取消打印")
    parser.add_argument("--open-door", action="store_true", help="开门")
    parser.add_argument("--close-door", action="store_true", help="关门")
    args = parser.parse_args()

    # 加载配置
    config_path = Path(args.config)
    if config_path.exists():
        h2c = H2CController(config_path=str(config_path))
    else:
        logger.warning(f"配置文件 {config_path} 不存在，使用默认参数")
        h2c = H2CController()

    if not h2c.connect():
        return

    try:
        if args.gcode:
            h2c.upload_and_print(args.gcode)
            # 上传成功后开始监控
            h2c.monitor()

        elif args.monitor:
            h2c.monitor()

        elif args.pause:
            h2c.pause()

        elif args.resume:
            h2c.resume()

        elif args.cancel:
            h2c.cancel()

        elif args.open_door:
            h2c.open_door()

        elif args.close_door:
            h2c.close_door()

        else:
            # 无参数时：打印当前状态
            import json
            print(json.dumps(h2c.get_status(), indent=2, ensure_ascii=False))

    finally:
        h2c.disconnect()


if __name__ == "__main__":
    main()
