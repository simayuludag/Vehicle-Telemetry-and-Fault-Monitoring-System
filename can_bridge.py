"""
CAN Bus Interface Bridge
Supports PEAK-System PCAN-USB ('pcan'), Virtual CAN ('virtual'), SocketCAN ('socketcan'),
and automatic in-memory fallback for Docker / CI environments.
"""

import logging
from typing import Optional
from j1939.protocol import J1939Frame

# python-can kütüphanesi opsiyonel kontrolü
try:
    import can
    PYTHON_CAN_AVAILABLE = True
except ImportError:
    PYTHON_CAN_AVAILABLE = False
    can = None

logger = logging.getLogger("can_bridge")


class CANBridge:
    """J1939 ve python-can arasında çift yönlü köprü"""

    def __init__(self, interface: str = "virtual", channel: str = "j1939_bus", bitrate: int = 250000):
        self.interface = interface
        self.channel = channel
        self.bitrate = bitrate
        self.bus: Optional[can.BusABC] = None
        self.is_connected = False
        self._init_bus()

    def _init_bus(self):
        """CAN veri yolunu başlatır veya sanal moda geçer"""
        if not PYTHON_CAN_AVAILABLE:
            logger.warning("python-can yüklü değil, dahili sanal modda çalışılıyor.")
            self.is_connected = True
            return

        try:
            if self.interface == "pcan":
                self.bus = can.Bus(
                    interface="pcan",
                    channel=self.channel or "PCAN_USBBUS1",
                    bitrate=self.bitrate
                )
                logger.info(f"Gerçek PCAN-USB hattına bağlanıldı: {self.channel} @ {self.bitrate} bps")
            elif self.interface == "virtual":
                self.bus = can.Bus(
                    interface="virtual",
                    channel=self.channel or "j1939_bus",
                    bitrate=self.bitrate
                )
                logger.info(f"Sanal CAN Bus başlatıldı: {self.channel}")
            else:
                self.bus = can.Bus(
                    interface=self.interface,
                    channel=self.channel,
                    bitrate=self.bitrate
                )
            self.is_connected = True
        except Exception as ex:
            logger.warning(f"Donanım arayüzü başlatılamadı ({ex}). Sanal dahili moda geçiliyor.")
            try:
                self.bus = can.Bus(interface="virtual", channel="j1939_virtual", bitrate=self.bitrate)
                self.is_connected = True
            except Exception:
                # Tamamen yazılımsal dahili mod
                self.bus = None
                self.is_connected = True

    def send_j1939_frame(self, frame: J1939Frame) -> bool:
        """J1939Frame nesnesini 29-bit Extended CAN mesajı olarak gönderir"""
        if not self.bus or not PYTHON_CAN_AVAILABLE:
            return True  # Sanal modda başarılı kabul edilir

        try:
            msg = can.Message(
                arbitration_id=frame.can_id,
                data=frame.data,
                is_extended_id=True,  # J1939 29-bit CAN ID gerektirir
                dlc=8
            )
            self.bus.send(msg)
            return True
        except Exception as e:
            logger.debug(f"CAN Frame gönderme hatası: {e}")
            return False

    def close(self):
        """CAN veri yolunu kapatır"""
        if self.bus:
            try:
                self.bus.shutdown()
            except Exception:
                pass
            self.bus = None
        self.is_connected = False
