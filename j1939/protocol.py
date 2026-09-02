"""
SAE J1939 Protocol Multi-Signal Encoder & Decoder Engine
Signals Supported:
- PGN 65265 (0xFEF1 - CCVS1): SPN 84 (Vehicle Speed), SPN 563 (Brake Switch)
- PGN 61443 (0xF003 - EEC2) : SPN 91 (Accelerator Pedal Position 1 %)
- PGN 61445 (0xF005 - ETC2) : SPN 523 (Transmission Current Gear - P/R/N/D1..D8)
- PGN 65110 (0xFE56 - HVS)  : SPN 3543 (Battery SOC %), SPN 5328 (Battery SOH %)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Tuple, Optional


# SAE J1939 Standart PGN Tanımları
PGN_CCVS = 65265          # 0xFEF1 - Cruise Control / Vehicle Speed 1
PGN_EEC2 = 61443          # 0xF003 - Electronic Engine Controller 2 (Throttle Pedal)
PGN_ETC2 = 61445          # 0xF005 - Electronic Transmission Controller 2 (Gear)
PGN_HVS = 65110           # 0xFE56 - High Voltage Energy Storage (Battery SOC / SOH)

# Standart SPN Tanımları
SPN_VEHICLE_SPEED = 84    # Wheel-Based Vehicle Speed (1/256 km/h / bit)
SPN_THROTTLE_PEDAL = 91   # Accelerator Pedal Position 1 (0.4 % / bit)
SPN_CURRENT_GEAR = 523    # Transmission Current Gear (Offset -125)
SPN_BATTERY_SOC = 3543    # High Voltage Battery State of Charge (0.4 % / bit)
SPN_BATTERY_SOH = 5328    # High Voltage Battery State of Health (0.4 % / bit)

DEFAULT_PRIORITY = 6      # Varsayılan J1939 Öncelik Seviyesi (0-7)
SPEED_RESOLUTION = 1 / 256.0  # 0.00390625 km/h / bit
PERCENT_RESOLUTION = 0.4      # 0.4 % / bit (J1939 standart yüzdelik çözünürlük)
MAX_SPEED_KMH = 250.996


@dataclass
class J1939Frame:
    """SAE J1939 29-bit CAN Çerçevesi Veri Yapısı"""
    can_id: int
    pgn: int
    priority: int
    source_address: int
    data: bytes
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    signal_name: str = "VEHICLE_SPEED"
    signal_value: str = "0.0 km/h"
    decoded_info: Dict[str, Any] = field(default_factory=dict)

    @property
    def can_id_hex(self) -> str:
        """29-bit CAN ID'yi 8 haneli Hex formatında döndürür (Örn: 0x18FEF101)"""
        return f"0x{self.can_id:08X}"

    @property
    def pgn_hex(self) -> str:
        """PGN'i Hex formatında döndürür (Örn: 0xFEF1, 0xF003)"""
        return f"0x{self.pgn:04X}"

    @property
    def pgn_name(self) -> str:
        if self.pgn == PGN_CCVS:
            return "CCVS1 (Hız & Fren)"
        elif self.pgn == PGN_EEC2:
            return "EEC2 (Gaz Pedalı)"
        elif self.pgn == PGN_ETC2:
            return "ETC2 (Vites Durumu)"
        elif self.pgn == PGN_HVS:
            return "HVS (Batarya SOC/SOH)"
        return f"PGN_{self.pgn_hex}"

    @property
    def sa_hex(self) -> str:
        """Source Address'i Hex formatında döndürür (Örn: 0x01)"""
        return f"0x{self.source_address:02X}"

    @property
    def data_hex(self) -> str:
        """8 Baytlık veriyi boşluklu Hex dizisi olarak döndürür"""
        return " ".join(f"{b:02X}" for b in self.data)

    def to_dict(self) -> Dict[str, Any]:
        """Web soketi ve JSON API için serileştirilebilir sözlük"""
        return {
            "can_id": self.can_id,
            "can_id_hex": self.can_id_hex,
            "pgn": self.pgn,
            "pgn_hex": self.pgn_hex,
            "pgn_name": self.pgn_name,
            "priority": self.priority,
            "source_address": self.source_address,
            "source_address_hex": self.sa_hex,
            "signal_name": self.signal_name,
            "signal_value": self.signal_value,
            "decoded_info": self.decoded_info,
            "data_bytes": list(self.data),
            "data_hex": self.data_hex,
            "timestamp": self.timestamp,
            "formatted_time": datetime.fromtimestamp(self.timestamp).strftime("%H:%M:%S.%f")[:-3],
        }


def build_j1939_can_id(pgn: int, source_address: int = 0x00, priority: int = DEFAULT_PRIORITY) -> int:
    """SAE J1939 29-bit Extended CAN Arbitration ID oluşturur"""
    priority = max(0, min(7, priority))
    source_address = max(0, min(0xFF, source_address))
    return (priority << 26) | ((pgn & 0x3FFFF) << 8) | source_address


def parse_j1939_can_id(can_id: int) -> Tuple[int, int, int]:
    """29-bit CAN ID'den Priority, PGN ve Source Address ayrıştırır"""
    priority = (can_id >> 26) & 0x07
    pgn = (can_id >> 8) & 0x3FFFF
    source_address = can_id & 0xFF
    return priority, pgn, source_address


# ==============================================================================
# 1. PGN 65265 (0xFEF1 - CCVS1): HIZ & FREN KODLAYICI / ÇÖZÜCÜ
# ==============================================================================
def pack_j1939_ccvs_speed(
    speed_kmh: float,
    brake_switch: bool = False,
    parking_brake: bool = False,
    cruise_active: bool = False
) -> bytes:
    """SAE J1939 CCVS1 (PGN 65265) 8-bayt veri paketini oluşturur"""
    clamped_speed = max(0.0, min(MAX_SPEED_KMH, float(speed_kmh)))
    raw_speed = int(round(clamped_speed / SPEED_RESOLUTION))
    raw_speed = max(0, min(0xFAFF, raw_speed))

    byte1 = raw_speed & 0xFF
    byte2 = (raw_speed >> 8) & 0xFF

    b0_parking = 0b01 if parking_brake else 0b00
    b0_cruise = 0b01 if cruise_active else 0b00
    byte0 = 0b11110000 | (b0_cruise << 2) | b0_parking

    b4_brake = 0b01 if brake_switch else 0b00
    byte4 = 0b11111100 | b4_brake

    return bytes([byte0, byte1, byte2, 0xFF, byte4, 0xFF, 0xFF, 0xFF])


def unpack_j1939_ccvs(data: bytes) -> Dict[str, Any]:
    """CCVS paketinden SPN 84 Hız ve Fren durumunu çözer"""
    if len(data) < 8:
        raise ValueError("CCVS paketi en az 8 bayt olmalıdır")
    raw_speed = data[1] | (data[2] << 8)
    speed_kmh = round(raw_speed * SPEED_RESOLUTION, 2) if raw_speed < 0xFE00 else 0.0
    brake_pressed = (data[4] & 0x03) == 0x01
    parking_brake = (data[0] & 0x03) == 0x01
    return {
        "speed_kmh": speed_kmh,
        "spn_84_speed_kmh": speed_kmh,
        "speed_valid": raw_speed < 0xFE00,
        "brake_pressed": brake_pressed,
        "parking_brake": parking_brake,
    }


# Backward compatibility alias
unpack_j1939_ccvs_speed = unpack_j1939_ccvs


# ==============================================================================
# 2. PGN 61443 (0xF003 - EEC2): GAZ PEDALI AÇIKLIĞI (% 0-100)
# ==============================================================================
def pack_j1939_eec2_throttle(throttle_pct: float) -> bytes:
    """
    SAE J1939 EEC2 (PGN 61443) 8-bayt veri paketini oluşturur.
    Byte 1: SPN 91 (Accelerator Pedal Position 1, Çözünürlük: 0.4% / bit, 0 - 100%)
    """
    clamped_throttle = max(0.0, min(100.0, float(throttle_pct)))
    raw_throttle = int(round(clamped_throttle / PERCENT_RESOLUTION))  # 0 - 250 (0x00 - 0xFA)
    raw_throttle = max(0, min(250, raw_throttle))

    byte0 = 0xFF  # SPN 558 Accelerator pedal low idle switch
    byte1 = raw_throttle & 0xFF  # SPN 91 Accelerator Pedal Position 1
    byte2 = raw_throttle & 0xFF  # SPN 92 Percent load at current speed
    byte3 = 0xFF
    byte4 = 0xFF
    byte5 = 0xFF
    byte6 = 0xFF
    byte7 = 0xFF

    return bytes([byte0, byte1, byte2, byte3, byte4, byte5, byte6, byte7])


def unpack_j1939_eec2(data: bytes) -> Dict[str, Any]:
    """EEC2 paketinden SPN 91 Gaz Pedalı Açıklığını çözer"""
    if len(data) < 8:
        raise ValueError("EEC2 paketi en az 8 bayt olmalıdır")
    raw_throttle = data[1]
    throttle_pct = round(raw_throttle * PERCENT_RESOLUTION, 1) if raw_throttle <= 250 else 0.0
    return {
        "throttle_pct": throttle_pct,
        "raw_throttle": raw_throttle
    }


# ==============================================================================
# 3. PGN 61445 (0xF005 - ETC2): VİTES BİLGİSİ (P / R / N / D1..D8)
# ==============================================================================
GEAR_MAP = {
    "P": 251,    # Park
    "R": -1,     # Geri Vites
    "N": 0,      # Boş Vites
    "D1": 1, "D2": 2, "D3": 3, "D4": 4,
    "D5": 5, "D6": 6, "D7": 7, "D8": 8
}
REVERSE_GEAR_MAP = {v: k for k, v in GEAR_MAP.items()}


def pack_j1939_etc2_gear(gear_str: str = "D1") -> bytes:
    """
    SAE J1939 ETC2 (PGN 61445) 8-bayt veri paketini oluşturur.
    Byte 3: SPN 523 (Transmission Current Gear, Offset: -125, 1 bit = 1 gear)
    """
    gear_num = GEAR_MAP.get(str(gear_str).upper(), 1)
    if gear_num == 251:
        raw_gear = 251
    else:
        raw_gear = max(0, min(250, gear_num + 125))

    byte0 = raw_gear  # SPN 524 Transmission Selected Gear
    byte1 = 0xFF
    byte2 = 0xFF
    byte3 = raw_gear  # SPN 523 Transmission Current Gear
    byte4 = 0xFF
    byte5 = 0xFF
    byte6 = 0xFF
    byte7 = 0xFF

    return bytes([byte0, byte1, byte2, byte3, byte4, byte5, byte6, byte7])


def unpack_j1939_etc2(data: bytes) -> Dict[str, Any]:
    """ETC2 paketinden SPN 523 Vites durumunu çözer"""
    if len(data) < 8:
        raise ValueError("ETC2 paketi en az 8 bayt olmalıdır")
    raw_gear = data[3]
    if raw_gear == 251:
        gear_str = "P"
    elif raw_gear < 250:
        gear_num = raw_gear - 125
        gear_str = REVERSE_GEAR_MAP.get(gear_num, f"D{max(1, gear_num)}")
    else:
        gear_str = "N"

    return {
        "gear_str": gear_str,
        "raw_gear": raw_gear
    }


# ==============================================================================
# 4. PGN 65110 (0xFE56 - HVS): BATARYA DOLULUĞU (SOC) & SAĞLIĞI (SOH)
# ==============================================================================
def pack_j1939_hvs_battery(soc_pct: float, soh_pct: float = 98.0) -> bytes:
    """
    SAE J1939 HVS (PGN 65110) 8-bayt veri paketini oluşturur.
    Byte 0: SPN 3543 (Battery State of Charge - SOC, 0.4% / bit, 0 - 100%)
    Byte 1: SPN 5328 (Battery State of Health - SOH, 0.4% / bit, 0 - 100%)
    """
    clamped_soc = max(0.0, min(100.0, float(soc_pct)))
    clamped_soh = max(0.0, min(100.0, float(soh_pct)))

    raw_soc = int(round(clamped_soc / PERCENT_RESOLUTION))  # 0 - 250
    raw_soh = int(round(clamped_soh / PERCENT_RESOLUTION))  # 0 - 250

    byte0 = max(0, min(250, raw_soc)) & 0xFF  # SPN 3543 SOC %
    byte1 = max(0, min(250, raw_soh)) & 0xFF  # SPN 5328 SOH %
    byte2 = 0xFF
    byte3 = 0xFF
    byte4 = 0xFF
    byte5 = 0xFF
    byte6 = 0xFF
    byte7 = 0xFF

    return bytes([byte0, byte1, byte2, byte3, byte4, byte5, byte6, byte7])


def unpack_j1939_hvs(data: bytes) -> Dict[str, Any]:
    """HVS paketinden SPN 3543 SOC (%) ve SPN 5328 SOH (%) çözer"""
    if len(data) < 8:
        raise ValueError("HVS paketi en az 8 bayt olmalıdır")
    raw_soc = data[0]
    raw_soh = data[1]

    soc_pct = round(raw_soc * PERCENT_RESOLUTION, 1) if raw_soc <= 250 else 0.0
    soh_pct = round(raw_soh * PERCENT_RESOLUTION, 1) if raw_soh <= 250 else 0.0

    return {
        "soc_pct": soc_pct,
        "soh_pct": soh_pct,
        "raw_soc": raw_soc,
        "raw_soh": raw_soh
    }


# ==============================================================================
# J1939 CODEC MANAGER
# ==============================================================================
class J1939Codec:
    """Tüm SAE J1939 Mesajları İçin Birleşik Kodlama ve Çözme Motoru"""

    @staticmethod
    def encode_speed_frame(speed_kmh: float, source_address: int, priority: int = 6, brake_pressed: bool = False) -> J1939Frame:
        can_id = build_j1939_can_id(pgn=PGN_CCVS, source_address=source_address, priority=priority)
        data = pack_j1939_ccvs_speed(speed_kmh=speed_kmh, brake_switch=brake_pressed)
        return J1939Frame(
            can_id=can_id,
            pgn=PGN_CCVS,
            priority=priority,
            source_address=source_address,
            data=data,
            signal_name="VEHICLE_SPEED",
            signal_value=f"{speed_kmh:.2f} km/h",
            decoded_info={"speed_kmh": speed_kmh, "brake_pressed": brake_pressed}
        )

    @staticmethod
    def encode_throttle_frame(throttle_pct: float, source_address: int, priority: int = 6) -> J1939Frame:
        can_id = build_j1939_can_id(pgn=PGN_EEC2, source_address=source_address, priority=priority)
        data = pack_j1939_eec2_throttle(throttle_pct=throttle_pct)
        return J1939Frame(
            can_id=can_id,
            pgn=PGN_EEC2,
            priority=priority,
            source_address=source_address,
            data=data,
            signal_name="THROTTLE_PEDAL",
            signal_value=f"%{throttle_pct:.1f}",
            decoded_info={"throttle_pct": throttle_pct}
        )

    @staticmethod
    def encode_gear_frame(gear_str: str, source_address: int, priority: int = 6) -> J1939Frame:
        can_id = build_j1939_can_id(pgn=PGN_ETC2, source_address=source_address, priority=priority)
        data = pack_j1939_etc2_gear(gear_str=gear_str)
        return J1939Frame(
            can_id=can_id,
            pgn=PGN_ETC2,
            priority=priority,
            source_address=source_address,
            data=data,
            signal_name="TRANSMISSION_GEAR",
            signal_value=f"Gear: {gear_str}",
            decoded_info={"gear_str": gear_str}
        )

    @staticmethod
    def encode_battery_frame(soc_pct: float, soh_pct: float, source_address: int, priority: int = 6) -> J1939Frame:
        can_id = build_j1939_can_id(pgn=PGN_HVS, source_address=source_address, priority=priority)
        data = pack_j1939_hvs_battery(soc_pct=soc_pct, soh_pct=soh_pct)
        return J1939Frame(
            can_id=can_id,
            pgn=PGN_HVS,
            priority=priority,
            source_address=source_address,
            data=data,
            signal_name="BATTERY_STATUS",
            signal_value=f"SOC: %{soc_pct:.1f} | SOH: %{soh_pct:.1f}",
            decoded_info={"soc_pct": soc_pct, "soh_pct": soh_pct}
        )

    @staticmethod
    def decode_frame(can_id: int, data: bytes) -> J1939Frame:
        """Gelen CAN ID ve veriden uygun J1939Frame nesnesini çözer"""
        priority, pgn, source_address = parse_j1939_can_id(can_id)
        sig_name = "UNKNOWN"
        sig_val = "N/A"
        dec_info = {}

        if pgn == PGN_CCVS and len(data) >= 8:
            dec_info = unpack_j1939_ccvs(data)
            sig_name = "VEHICLE_SPEED"
            sig_val = f"{dec_info['speed_kmh']:.2f} km/h"
        elif pgn == PGN_EEC2 and len(data) >= 8:
            dec_info = unpack_j1939_eec2(data)
            sig_name = "THROTTLE_PEDAL"
            sig_val = f"%{dec_info['throttle_pct']:.1f}"
        elif pgn == PGN_ETC2 and len(data) >= 8:
            dec_info = unpack_j1939_etc2(data)
            sig_name = "TRANSMISSION_GEAR"
            sig_val = f"Gear: {dec_info['gear_str']}"
        elif pgn == PGN_HVS and len(data) >= 8:
            dec_info = unpack_j1939_hvs(data)
            sig_name = "BATTERY_STATUS"
            sig_val = f"SOC: %{dec_info['soc_pct']:.1f} | SOH: %{dec_info['soh_pct']:.1f}"

        return J1939Frame(
            can_id=can_id,
            pgn=pgn,
            priority=priority,
            source_address=source_address,
            data=data,
            signal_name=sig_name,
            signal_value=sig_val,
            decoded_info=dec_info
        )
