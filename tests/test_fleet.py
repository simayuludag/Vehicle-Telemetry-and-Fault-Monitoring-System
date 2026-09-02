"""
Unit Tests for Fleet Matrix (10 Passenger Brands x 3 Models = 30 Vehicles)
"""

import pytest
from j1939.fleet_data import (
    FLEET_BRANDS,
    VEHICLES,
    get_all_vehicles,
    get_vehicle_by_id,
    get_vehicles_by_brand,
)


def test_fleet_brands_count_and_structure():
    """10 Binek ve SUV Markasının eksiksiz ve doğru veri yapısında olduğunu doğrular"""
    assert len(FLEET_BRANDS) == 10

    brand_ids = set()
    for b in FLEET_BRANDS:
        assert "id" in b
        assert "name" in b
        assert "color" in b
        assert "badge" in b
        assert b["id"] not in brand_ids, f"Tekrarlanan marka ID'si: {b['id']}"
        brand_ids.add(b["id"])

    expected_brands = {
        "bmw", "mercedes", "audi", "volkswagen", "toyota",
        "tesla", "ford", "renault", "hyundai", "fiat"
    }
    assert brand_ids == expected_brands


def test_vehicles_count_and_per_brand_distribution():
    """Toplam 30 araç olduğunu ve her markada tam 3 model bulunduğunu doğrular"""
    vehicles = get_all_vehicles()
    assert len(vehicles) == 30

    for b in FLEET_BRANDS:
        models = get_vehicles_by_brand(b["id"])
        assert len(models) == 3, f"{b['name']} markasında 3 model olmalı, bulunan: {len(models)}"


def test_unique_source_addresses():
    """Her aracın benzersiz bir J1939 Source Address'e (SA) sahip olduğunu doğrular"""
    vehicles = get_all_vehicles()
    sa_set = set()
    vehicle_ids = set()

    for v in vehicles:
        sa = v["source_address"]
        assert 0x01 <= sa <= 0xFD, f"Geçersiz J1939 SA: {sa} (Araç: {v['id']})"
        assert sa not in sa_set, f"Çakışan J1939 SA: {sa} (Araç: {v['id']})"
        sa_set.add(sa)

        assert v["id"] not in vehicle_ids, f"Çakışan Araç ID: {v['id']}"
        vehicle_ids.add(v["id"])


def test_vehicle_lookup_by_id():
    """get_vehicle_by_id fonksiyonunun doğruluğu"""
    bmw = get_vehicle_by_id("bmw-320i")
    assert bmw["brand_id"] == "bmw"
    assert bmw["source_address"] == 0x01
    assert "320i" in bmw["model"]

    tesla = get_vehicle_by_id("tesla-model-3-perf")
    assert tesla["brand_id"] == "tesla"
    assert "Model 3" in tesla["model"]

    with pytest.raises(KeyError):
        get_vehicle_by_id("gecersiz-arac-id")


def test_vehicle_telemetry_parameters():
    """Tüm araçların hız ve motor parametrelerinin geçerli aralıklarda olduğunu doğrular"""
    for v in get_all_vehicles():
        assert v["max_speed"] >= 150.0
        assert 0.0 <= v["default_speed"] <= v["max_speed"]
        assert 0.0 <= v["current_speed"] <= v["max_speed"]
        assert v["acceleration_rate"] > 1.0
        assert len(v["plate"]) > 4
        assert len(v["engine"]) > 3
