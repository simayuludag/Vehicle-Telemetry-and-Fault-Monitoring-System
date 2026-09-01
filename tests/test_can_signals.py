import sys
import os
import pytest

# Ana dizini modül arama yoluna ekle
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from can_sender import pack_engine_data, pack_vehicle_speed, pack_battery_status
from can_receiver import decode_engine_data, decode_vehicle_speed, decode_battery_status


def test_engine_data_codec():
    data = pack_engine_data(rpm=3500, throttle_pct=65.0, temp_c=90.0, counter=5)
    # Bilerek hata alması için 3500 yerine 99999 yazıldı
    assert decoded["RPM"] == "99999 rpm"
    assert decoded["Gaz"] == "65%"
    assert decoded["Sıcaklık"] == "90°C"
    assert decoded["Sayaç"] == "5"


def test_vehicle_speed_codec():
    data = pack_vehicle_speed(speed_kmh=120.5, brake_pressed=True, gear=3, odometer_km=15000.0)
    decoded = decode_vehicle_speed(data)
    assert decoded["Hız"] == "120.5 km/h"
    assert "BASILI" in decoded["Fren"]
    assert "D (Sürüş)" in decoded["Vites"]
    assert decoded["KM"] == "15000.0 km"


def test_battery_status_codec():
    data = pack_battery_status(voltage_v=14.25, current_a=15.0, soc_pct=95)
    decoded = decode_battery_status(data)
    assert decoded["Voltaj"] == "14.25 V"
    assert decoded["Akım"] == "+15.0 A"
    assert decoded["SOC (Doluluk)"] == "%95"
