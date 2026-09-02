"""
Unit Tests for SAE J1939 Multi-Signal Protocol & Codec
Tests:
- PGN 65265 (CCVS1): SPN 84 Speed & Brake Switch
- PGN 61443 (EEC2) : SPN 91 Accelerator Pedal %
- PGN 61445 (ETC2) : SPN 523 Transmission Current Gear
- PGN 65110 (HVS)  : SPN 3543 Battery SOC % & SPN 5328 Battery SOH %
"""

import pytest
from j1939.protocol import (
    build_j1939_can_id,
    parse_j1939_can_id,
    pack_j1939_ccvs_speed,
    unpack_j1939_ccvs,
    pack_j1939_eec2_throttle,
    unpack_j1939_eec2,
    pack_j1939_etc2_gear,
    unpack_j1939_etc2,
    pack_j1939_hvs_battery,
    unpack_j1939_hvs,
    J1939Codec,
    J1939Frame,
    PGN_CCVS,
    PGN_EEC2,
    PGN_ETC2,
    PGN_HVS,
    MAX_SPEED_KMH,
)


def test_j1939_can_id_packing_and_parsing():
    """29-bit Extended CAN ID oluşturma ve ayrıştırma doğrulaması"""
    priority = 6
    pgn = PGN_CCVS  # 65265 (0xFEF1)
    source_address = 0x01  # BMW 320i SA

    can_id = build_j1939_can_id(pgn=pgn, source_address=source_address, priority=priority)
    assert can_id == 0x18FEF101

    p_out, pgn_out, sa_out = parse_j1939_can_id(can_id)
    assert p_out == 6
    assert pgn_out == PGN_CCVS
    assert sa_out == 0x01


def test_j1939_can_id_all_priorities_and_addresses():
    """Farklı öncelik ve Source Address değerleri ile CAN ID testleri"""
    for p in range(8):
        for sa in [0x00, 0x05, 0x1E, 0xFD]:
            can_id = build_j1939_can_id(pgn=PGN_CCVS, source_address=sa, priority=p)
            parsed_p, parsed_pgn, parsed_sa = parse_j1939_can_id(can_id)
            assert parsed_p == p
            assert parsed_pgn == PGN_CCVS
            assert parsed_sa == sa


def test_spn84_speed_codec_resolution_and_accuracy():
    """SPN 84 Hız kodlama/çözme hassasiyeti (1/256 km/h) testleri"""
    test_speeds = [0.0, 30.0, 50.25, 85.5, 90.0, 120.0, 140.75, 200.0, MAX_SPEED_KMH]

    for speed in test_speeds:
        data = pack_j1939_ccvs_speed(speed_kmh=speed)
        assert len(data) == 8

        unpacked = unpack_j1939_ccvs(data)
        assert abs(unpacked["speed_kmh"] - speed) <= 0.01


def test_spn84_zero_and_clamp_boundaries():
    """Sınır değer (0 km/h ve negatif hız) testleri"""
    data = pack_j1939_ccvs_speed(speed_kmh=-15.0)
    unpacked = unpack_j1939_ccvs(data)
    assert unpacked["speed_kmh"] == 0.0

    data_max = pack_j1939_ccvs_speed(speed_kmh=350.0)
    unpacked_max = unpack_j1939_ccvs(data_max)
    assert unpacked_max["speed_kmh"] <= MAX_SPEED_KMH + 0.1


def test_ccvs_status_flags():
    """Fren, el freni ve cruise bayraklarının doğru bitlere yerleşimi"""
    data = pack_j1939_ccvs_speed(
        speed_kmh=80.0,
        parking_brake=True,
        brake_switch=True,
        cruise_active=True
    )
    unpacked = unpack_j1939_ccvs(data)
    assert unpacked["parking_brake"] is True
    assert unpacked["brake_pressed"] is True


def test_eec2_throttle_pedal_codec():
    """PGN 61443 (EEC2) SPN 91 Gaz Pedalı Açıklığı (%) Testleri"""
    for throttle in [0.0, 15.0, 45.5, 78.0, 100.0]:
        data = pack_j1939_eec2_throttle(throttle_pct=throttle)
        assert len(data) == 8
        unpacked = unpack_j1939_eec2(data)
        # 0.4% / bit çözünürlük ile hata <= 0.4% olmalıdır
        assert abs(unpacked["throttle_pct"] - throttle) <= 0.4

    # Sınır kontrolü (0 - 100%)
    data_neg = pack_j1939_eec2_throttle(throttle_pct=-20.0)
    assert unpack_j1939_eec2(data_neg)["throttle_pct"] == 0.0

    data_over = pack_j1939_eec2_throttle(throttle_pct=150.0)
    assert unpack_j1939_eec2(data_over)["throttle_pct"] == 100.0


def test_etc2_gear_codec():
    """PGN 61445 (ETC2) SPN 523 Şanzıman Vites Durumu Testleri"""
    gears_to_test = ["P", "R", "N", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"]
    for g in gears_to_test:
        data = pack_j1939_etc2_gear(gear_str=g)
        assert len(data) == 8
        unpacked = unpack_j1939_etc2(data)
        assert unpacked["gear_str"] == g


def test_hvs_battery_soc_soh_codec():
    """PGN 65110 (HVS) SPN 3543 (SOC %) & SPN 5328 (SOH %) Testleri"""
    test_cases = [
        (95.0, 100.0),
        (50.0, 98.0),
        (12.5, 95.5),
        (0.0, 85.0),
        (100.0, 100.0),
    ]
    for soc, soh in test_cases:
        data = pack_j1939_hvs_battery(soc_pct=soc, soh_pct=soh)
        assert len(data) == 8
        unpacked = unpack_j1939_hvs(data)
        assert abs(unpacked["soc_pct"] - soc) <= 0.4
        assert abs(unpacked["soh_pct"] - soh) <= 0.4


def test_j1939_codec_multi_signal_roundtrip():
    """J1939Codec sınıfı üzerinden çoklu PGN kodlama ve çözme döngüsü"""
    sa = 0x10  # Tesla Model 3 SA

    # 1. Hız Çerçevesi
    f_speed = J1939Codec.encode_speed_frame(speed_kmh=125.5, source_address=sa)
    dec_speed = J1939Codec.decode_frame(f_speed.can_id, f_speed.data)
    assert dec_speed.signal_name == "VEHICLE_SPEED"
    assert abs(dec_speed.decoded_info["speed_kmh"] - 125.5) <= 0.01

    # 2. Gaz Çerçevesi
    f_throttle = J1939Codec.encode_throttle_frame(throttle_pct=65.0, source_address=sa)
    dec_throttle = J1939Codec.decode_frame(f_throttle.can_id, f_throttle.data)
    assert dec_throttle.signal_name == "THROTTLE_PEDAL"
    assert abs(dec_throttle.decoded_info["throttle_pct"] - 65.0) <= 0.4

    # 3. Vites Çerçevesi
    f_gear = J1939Codec.encode_gear_frame(gear_str="D6", source_address=sa)
    dec_gear = J1939Codec.decode_frame(f_gear.can_id, f_gear.data)
    assert dec_gear.signal_name == "TRANSMISSION_GEAR"
    assert dec_gear.decoded_info["gear_str"] == "D6"

    # 4. Batarya Çerçevesi
    f_bat = J1939Codec.encode_battery_frame(soc_pct=88.5, soh_pct=99.0, source_address=sa)
    dec_bat = J1939Codec.decode_frame(f_bat.can_id, f_bat.data)
    assert dec_bat.signal_name == "BATTERY_STATUS"
    assert abs(dec_bat.decoded_info["soc_pct"] - 88.5) <= 0.4
