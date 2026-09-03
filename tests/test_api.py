"""
Integration & REST API Tests for J1939 Web Platform
"""

import pytest
from fastapi.testclient import TestClient
from server import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_api_health(client):
    """Sağlık kontrolü endpoint testi"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "simulator_running" in data
    assert data["active_vehicles"] >= 30


def test_api_get_brands(client):
    """10 binek marka listesi endpoint testi"""
    response = client.get("/api/brands")
    assert response.status_code == 200
    brands = response.json()
    assert len(brands) >= 10
    brand_names = [b["name"] for b in brands]
    assert "BMW" in brand_names
    assert "Mercedes-Benz" in brand_names
    assert "Audi" in brand_names
    assert "Tesla" in brand_names
    assert "Toyota" in brand_names


def test_api_get_fleet(client):
    """Araç filosu endpoint testi"""
    response = client.get("/api/fleet")
    assert response.status_code == 200
    fleet = response.json()
    assert len(fleet) >= 30


def test_api_get_single_vehicle(client):
    """Tek araç detay endpoint testi"""
    response = client.get("/api/vehicle/bmw-320i")
    assert response.status_code == 200
    v = response.json()
    assert v["id"] == "bmw-320i"
    assert v["brand_name"] == "BMW"
    assert v["source_address"] == 0x01

    # Geçersiz araç testi
    response_404 = client.get("/api/vehicle/bilinmeyen-arac")
    assert response_404.status_code == 404


def test_api_update_vehicle_speed(client):
    """Araç hız güncelleme endpoint testi"""
    payload = {"speed": 135.5, "mode": "highway"}
    response = client.post("/api/vehicle/tesla-model-3-perf/speed", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["target_speed"] == 135.5

    # Güncellenen aracı doğrula
    v_res = client.get("/api/vehicle/tesla-model-3-perf")
    assert v_res.json()["target_speed"] == 135.5


def test_api_brake_vehicle(client):
    """Araç fren endpoint testi"""
    response = client.post("/api/vehicle/bmw-m4-competition/brake", json={"pressed": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["brake_pressed"] is True


def test_api_set_fleet_speed(client):
    """Tüm filo hız atama testi"""
    response = client.post("/api/fleet/speed", json={"speed": 95.0})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["target_speed"] == 95.0


def test_api_apply_scenario(client):
    """Senaryo uygulama testi"""
    for scen in ["highway", "city", "convoy", "drag_race", "idle"]:
        response = client.post("/api/fleet/scenario", json={"scenario": scen})
        assert response.status_code == 200
        assert response.json()["scenario"] == scen


def test_api_emergency_stop(client):
    """Acil durdurma testi"""
    response = client.post("/api/fleet/emergency-stop")
    assert response.status_code == 200
    assert response.json()["action"] == "emergency_stop"


def test_api_can_history(client):
    """CAN mesaj geçmişi endpoint testi"""
    response = client.get("/api/can/history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_index_and_control_pages_served(client):
    """Ortam 1 (Control) ve Ortam 2 (Monitor) sayfalarının başarıyla sunulduğunu doğrular"""
    # Ortam 2 (Monitor)
    res_index = client.get("/")
    assert res_index.status_code == 200
    assert "J1939" in res_index.text
    assert "speedGaugeCanvas" in res_index.text
    assert "btnOpenAddVehicleModal" in res_index.text

    # Ortam 1 (Control)
    res_control = client.get("/control")
    assert res_control.status_code == 200
    assert "Sinyal Gönderici" in res_control.text
    assert "mainSpeedSlider" in res_control.text


def test_api_dynamic_brand_and_vehicle_management(client):
    """Dinamik marka ve araç ekleme, simülatöre dahil etme ve silme testi"""
    # 1. Sıradaki boş SA adresini al
    res_sa = client.get("/api/fleet/next-sa")
    assert res_sa.status_code == 200
    next_sa = res_sa.json()["source_address"]
    assert isinstance(next_sa, int)

    # 2. Yeni özel marka ekle (Örn: TOGG)
    res_brand = client.post("/api/fleet/add-brand", json={
        "name": "TOGG",
        "color": "#00A8E8",
        "country": "Türkiye"
    })
    assert res_brand.status_code == 200
    brand_data = res_brand.json()["brand"]
    assert brand_data["name"] == "TOGG"
    assert brand_data["id"] == "togg"

    # 3. Yeni araç ekle
    form_data = {
        "brand_id": "togg",
        "brand_name": "TOGG",
        "model": "T10X V2 Long Range",
        "category": "C-SUV",
        "plate": "34 TGG 100",
        "engine": "Elektrik 218 HP",
        "max_speed": "185.0",
        "default_speed": "0.0",
        "source_address": str(next_sa)
    }
    res_veh = client.post("/api/fleet/add-vehicle", data=form_data)
    assert res_veh.status_code == 200
    new_v = res_veh.json()["vehicle"]
    assert new_v["id"] == "togg-t10x-v2-long-range"
    assert new_v["source_address"] == next_sa
    assert new_v["brand_name"] == "TOGG"

    # 4. Aracın filoda ve simülatörde olduğunu doğrula
    res_get = client.get(f"/api/vehicle/{new_v['id']}")
    assert res_get.status_code == 200
    assert res_get.json()["plate"] == "34 TGG 100"

    # 5. Yeni aracın hızını güncelle
    res_spd = client.post(f"/api/vehicle/{new_v['id']}/speed", json={"speed": 120.0})
    assert res_spd.status_code == 200
    assert res_spd.json()["target_speed"] == 120.0

    # 6. Silme testi
    res_del = client.delete(f"/api/vehicle/{new_v['id']}")
    assert res_del.status_code == 200

    # 7. Silindiğini doğrula
    res_404 = client.get(f"/api/vehicle/{new_v['id']}")
    assert res_404.status_code == 404
