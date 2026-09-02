"""
Unit Tests for SAE J1939 29-Bit Protocol & SPN 84 Speed Codec
"""

import pytest
from j1939.protocol import (
    build_j1939_can_id,
    parse_j1939_can_id,
    pack_j1939_ccvs_speed,
    unpack_j1939_ccvs_speed,
    J1939Codec,
    J1939Frame,
    PGN_CCVS,
    SPN_VEHICLE_SPEED,
    SPEED_RESOLUTION,
    MAX_SPEED_KMH,
)


def test_j1939_can_id_packing_and_parsing():
    """29-bit Extended CAN ID oluşturma ve ayrıştırma doğrulaması"""
    priority = 6
    pgn = PGN_CCVS  # 65265 (0xFEF1)
    source_address = 0x01  # Mercedes Actros SA

    can_id = build_j1939_can_id(pgn=pgn, source_address=source_address, priority=priority)

    # 29-bit CAN ID: (6 << 26) | (65265 << 8) | 1 = 0x18FEF101
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

        unpacked = unpack_j1939_ccvs_speed(data)
        assert unpacked["speed_valid"] is True
        # 1/256 km/h çözünürlük farkı en fazla 0.01 km/h olmalıdır
        assert abs(unpacked["spn_84_speed_kmh"] - speed) <= 0.01


def test_spn84_zero_and_clamp_boundaries():
    """Sınır değer (0 km/h ve negatif hız) testleri"""
    # Negatif hız 0'a çekilmelidir
    data = pack_j1939_ccvs_speed(speed_kmh=-15.0)
    unpacked = unpack_j1939_ccvs_speed(data)
    assert unpacked["spn_84_speed_kmh"] == 0.0

    # Maksimum hızı aşan değerler sınırlandırılmalıdır
    data_max = pack_j1939_ccvs_speed(speed_kmh=350.0)
    unpacked_max = unpack_j1939_ccvs_speed(data_max)
    assert unpacked_max["spn_84_speed_kmh"] <= MAX_SPEED_KMH + 0.1


def test_ccvs_status_flags():
    """Fren, el freni ve cruise bayraklarının doğru bitlere yerleşimi"""
    data = pack_j1939_ccvs_speed(
        speed_kmh=80.0,
        parking_brake=True,
        brake_switch=True,
        cruise_active=True
    )
    unpacked = unpack_j1939_ccvs_speed(data)

    assert unpacked["parking_brake"] is True
    assert unpacked["brake_pressed"] is True
    assert unpacked["cruise_active"] is True


def test_j1939_codec_full_roundtrip():
    """J1939Codec sınıfı üzerinden tam çerçeve kodlama ve çözme"""
    speed_in = 88.5
    sa = 0x07  # Volvo FH16 SA
    frame = J1939Codec.encode_speed_frame(speed_kmh=speed_in, source_address=sa, priority=6)

    assert frame.can_id_hex == "0x18FEF107"
    assert frame.pgn == PGN_CCVS
    assert frame.source_address == 0x07

    # Çözme
    decoded_frame = J1939Codec.decode_frame(frame.can_id, frame.data)
    assert decoded_frame.source_address == 0x07
    assert decoded_frame.pgn == PGN_CCVS
    assert abs(decoded_frame.decoded_speed_kmh - speed_in) <= 0.01

    # Sözlük dönüşümü
    d = frame.to_dict()
    assert d["spn"] == SPN_VEHICLE_SPEED
    assert d["can_id_hex"] == "0x18FEF107"
    assert d["source_address_hex"] == "0x07"
