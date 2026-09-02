"""
SAE J1939 Protocol Encoder / Decoder Engine
Focus: PGN 65265 (0xFEF1 - CCVS: Cruise Control/Vehicle Speed) & SPN 84 (Wheel-Based Vehicle Speed)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Tuple, Optional


# SAE J1939 Standart Tanımları
PGN_CCVS = 65265          # 0xFEF1 - Cruise Control / Vehicle Speed
SPN_VEHICLE_SPEED = 84    # Wheel-Based Vehicle Speed (Byte 1-2, 1/256 km/h / bit)
DEFAULT_PRIORITY = 6      # Varsayılan J1939 Öncelik Seviyesi (0-7)
SPEED_RESOLUTION = 1 / 256.0  # 0.00390625 km/h / bit
MAX_SPEED_KMH = 250.996   # 64255 * (1/256) km/h


@dataclass
class J1939Frame:
    """SAE J1939 29-bit CAN Çerçevesi Veri Yapısı"""
    can_id: int
    pgn: int
    priority: int
    source_address: int
    data: bytes
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    decoded_speed_kmh: float = 0.0

    @property
    def can_id_hex(self) -> str:
        """29-bit CAN ID'yi 8 haneli Hex formatında döndürür (Örn: 0x18FEF101)"""
        return f"0x{self.can_id:08X}"

    @property
    def pgn_hex(self) -> str:
        """PGN'i Hex formatında döndürür (Örn: 0xFEF1)"""
        return f"0x{self.pgn:04X}"

    @property
    def sa_hex(self) -> str:
        """Source Address'i Hex formatında döndürür (Örn: 0x01)"""
        return f"0x{self.source_address:02X}"

    @property
    def data_hex(self) -> str:
        """8 Baytlık veriyi boşluklu Hex dizisi olarak döndürür (Örn: FF 40 1F FF FF FF FF FF)"""
        return " ".join(f"{b:02X}" for b in self.data)

    def to_dict(self) -> Dict[str, Any]:
        """Web soketi ve JSON API için serileştirilebilir sözlük"""
        return {
            "can_id": self.can_id,
            "can_id_hex": self.can_id_hex,
            "pgn": self.pgn,
            "pgn_hex": self.pgn_hex,
            "pgn_name": "CCVS (Cruise Control / Vehicle Speed)" if self.pgn == PGN_CCVS else "UNKNOWN",
            "priority": self.priority,
            "source_address": self.source_address,
            "source_address_hex": self.sa_hex,
            "spn": SPN_VEHICLE_SPEED,
            "spn_name": "Wheel-Based Vehicle Speed",
            "speed_kmh": round(self.decoded_speed_kmh, 2),
            "data_bytes": list(self.data),
            "data_hex": self.data_hex,
            "timestamp": self.timestamp,
            "formatted_time": datetime.fromtimestamp(self.timestamp).strftime("%H:%M:%S.%f")[:-3],
        }


def build_j1939_can_id(pgn: int = PGN_CCVS, source_address: int = 0x00, priority: int = DEFAULT_PRIORITY) -> int:
    """
    SAE J1939 29-bit Extended CAN Arbitration ID oluşturur.

    Bit Dağılımı:
    - Bit 28..26 (3 bit) : Priority (Öncelik, 0-7)
    - Bit 25      (1 bit) : Extended Data Page (EDP=0)
    - Bit 24      (1 bit) : Data Page (DP)
    - Bit 23..8  (16 bit) : PDU Format & PDU Specific (PGN)
    - Bit 7..0    (8 bit) : Source Address (SA)
    """
    priority = max(0, min(7, priority))
    source_address = max(0, min(0xFF, source_address))
    return (priority << 26) | ((pgn & 0x3FFFF) << 8) | source_address


def parse_j1939_can_id(can_id: int) -> Tuple[int, int, int]:
    """
    29-bit CAN ID'den Priority, PGN ve Source Address ayrıştırır.

    Döndürür:
    (priority, pgn, source_address)
    """
    priority = (can_id >> 26) & 0x07
    pgn = (can_id >> 8) & 0x3FFFF
    source_address = can_id & 0xFF
    return priority, pgn, source_address


def pack_j1939_ccvs_speed(
    speed_kmh: float,
    parking_brake: bool = False,
    brake_switch: bool = False,
    clutch_switch: bool = False,
    cruise_active: bool = False
) -> bytes:
    """
    SAE J1939 CCVS (PGN 65265 / 0xFEF1) 8-bayt veri paketini oluşturur.

    Byte Dağılımı:
    - Byte 0: Two-bit status flags (Parking Brake, Cruise Switches)
    - Byte 1-2: SPN 84 - Wheel-Based Vehicle Speed (Little-Endian, 1/256 km/h / bit)
    - Byte 3: Cruise Control Set Speed (0xFF = Not Available)
    - Byte 4: Brake switch & Clutch status flags
    - Byte 5-7: 0xFF (Rezerve / kullanılmayan baytlar)
    """
    # Hız sınırlandırma (0 ile MAX_SPEED_KMH)
    clamped_speed = max(0.0, min(MAX_SPEED_KMH, float(speed_kmh)))
    raw_speed = int(round(clamped_speed / SPEED_RESOLUTION))
    raw_speed = max(0, min(0xFAFF, raw_speed))

    byte1 = raw_speed & 0xFF
    byte2 = (raw_speed >> 8) & 0xFF

    # Byte 0: Durum bitleri (2-bit standart J1939 flagları: 00=Off, 01=On, 10=Error, 11=Not Available)
    b0_parking = 0b01 if parking_brake else 0b00
    b0_cruise = 0b01 if cruise_active else 0b00
    byte0 = 0b11110000 | (b0_cruise << 2) | b0_parking

    # Byte 4: Fren ve debriyaj
    b4_brake = 0b01 if brake_switch else 0b00
    b4_clutch = 0b01 if clutch_switch else 0b00
    byte4 = 0b11110000 | (b4_clutch << 2) | b4_brake

    byte3 = 0xFF  # Cruise Set Speed
    byte5 = 0xFF
    byte6 = 0xFF
    byte7 = 0xFF

    return bytes([byte0, byte1, byte2, byte3, byte4, byte5, byte6, byte7])


def unpack_j1939_ccvs_speed(data: bytes) -> Dict[str, Any]:
    """
    SAE J1939 CCVS 8-baytlık verisinden SPN 84 Araç Hızı ve durum sinyallerini çözer.
    """
    if len(data) < 8:
        raise ValueError(f"J1939 CCVS paketi en az 8 bayt olmalıdır, gelen: {len(data)}")

    # Byte 1-2: SPN 84 (Wheel-Based Vehicle Speed)
    raw_speed = data[1] | (data[2] << 8)

    if raw_speed >= 0xFE00:  # 0xFE00 - 0xFFFF: Hata veya Mevcut Değil
        speed_kmh = 0.0
        speed_valid = False
    else:
        speed_kmh = round(raw_speed * SPEED_RESOLUTION, 2)
        speed_valid = True

    # Byte 0 bayrakları
    parking_brake = (data[0] & 0x03) == 0x01
    cruise_active = ((data[0] >> 2) & 0x03) == 0x01

    # Byte 4 bayrakları
    brake_pressed = (data[4] & 0x03) == 0x01
    clutch_pressed = ((data[4] >> 2) & 0x03) == 0x01

    return {
        "spn_84_speed_kmh": speed_kmh,
        "speed_valid": speed_valid,
        "raw_speed": raw_speed,
        "parking_brake": parking_brake,
        "cruise_active": cruise_active,
        "brake_pressed": brake_pressed,
        "clutch_pressed": clutch_pressed,
    }


class J1939Codec:
    """J1939 Çerçeve Kodlama ve Çözme Yöneticisi"""

    @staticmethod
    def encode_speed_frame(
        speed_kmh: float,
        source_address: int,
        priority: int = DEFAULT_PRIORITY,
        pgn: int = PGN_CCVS,
        brake_pressed: bool = False
    ) -> J1939Frame:
        """Araç hızı için standart J1939 CAN çerçevesi oluşturur"""
        can_id = build_j1939_can_id(pgn=pgn, source_address=source_address, priority=priority)
        data = pack_j1939_ccvs_speed(speed_kmh=speed_kmh, brake_switch=brake_pressed)
        return J1939Frame(
            can_id=can_id,
            pgn=pgn,
            priority=priority,
            source_address=source_address,
            data=data,
            decoded_speed_kmh=speed_kmh
        )

    @staticmethod
    def decode_frame(can_id: int, data: bytes) -> J1939Frame:
        """Gelen CAN ID ve veriden J1939Frame nesnesi oluşturur ve çözer"""
        priority, pgn, source_address = parse_j1939_can_id(can_id)
        decoded_speed = 0.0
        if pgn == PGN_CCVS and len(data) >= 3:
            unpacked = unpack_j1939_ccvs_speed(data)
            decoded_speed = unpacked["spn_84_speed_kmh"]

        return J1939Frame(
            can_id=can_id,
            pgn=pgn,
            priority=priority,
            source_address=source_address,
            data=data,
            decoded_speed_kmh=decoded_speed
        )
