"""
SAE J1939 Vehicle Speed & Multi-Signal Fleet Telemetry Package
Signals: Speed (SPN 84), Throttle (SPN 91), Brake (SPN 563), Gear (SPN 523), Battery (SPN 3543/5328)
"""

from .protocol import (
    J1939Frame,
    J1939Codec,
    PGN_CCVS,
    PGN_EEC2,
    PGN_ETC2,
    PGN_HVS,
    SPN_VEHICLE_SPEED,
    SPN_THROTTLE_PEDAL,
    SPN_CURRENT_GEAR,
    SPN_BATTERY_SOC,
    SPN_BATTERY_SOH,
    build_j1939_can_id,
    parse_j1939_can_id,
    pack_j1939_ccvs_speed,
    unpack_j1939_ccvs,
    unpack_j1939_ccvs_speed,
    pack_j1939_eec2_throttle,
    unpack_j1939_eec2,
    pack_j1939_etc2_gear,
    unpack_j1939_etc2,
    pack_j1939_hvs_battery,
    unpack_j1939_hvs,
)
from .fleet_data import FLEET_BRANDS, VEHICLES, get_vehicle_by_id, get_all_vehicles
from .simulator import FleetSimulator

__all__ = [
    "J1939Frame",
    "J1939Codec",
    "PGN_CCVS",
    "PGN_EEC2",
    "PGN_ETC2",
    "PGN_HVS",
    "SPN_VEHICLE_SPEED",
    "SPN_THROTTLE_PEDAL",
    "SPN_CURRENT_GEAR",
    "SPN_BATTERY_SOC",
    "SPN_BATTERY_SOH",
    "build_j1939_can_id",
    "parse_j1939_can_id",
    "pack_j1939_ccvs_speed",
    "unpack_j1939_ccvs",
    "unpack_j1939_ccvs_speed",
    "pack_j1939_eec2_throttle",
    "unpack_j1939_eec2",
    "pack_j1939_etc2_gear",
    "unpack_j1939_etc2",
    "pack_j1939_hvs_battery",
    "unpack_j1939_hvs",
    "FLEET_BRANDS",
    "VEHICLES",
    "get_vehicle_by_id",
    "get_all_vehicles",
    "FleetSimulator",
]
