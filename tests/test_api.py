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
    assert data["active_vehicles"] == 30


def test_api_get_brands(client):
    """10 marka listesi endpoint testi"""
    response = client.get("/api/brands")
    assert response.status_code == 200
    brands = response.json()
    assert len(brands) == 10
    brand_names = [b["name"] for b in brands]
    assert "Mercedes-Benz" in brand_names
    assert "Scania" in brand_names
    assert "Volvo Trucks" in brand_names
    assert "Ford Trucks" in brand_names
    assert "BMC Otomotiv" in brand_names


def test_api_get_fleet(client):
    """30 araç filosu endpoint testi"""
    response = client.get("/api/fleet")
    assert response.status_code == 200
    fleet = response.json()
    assert len(fleet) == 30


def test_api_get_single_vehicle(client):
    """Tek araç detay endpoint testi"""
    response = client.get("/api/vehicle/mb-actros-1851")
    assert response.status_code == 200
    v = response.json()
    assert v["id"] == "mb-actros-1851"
    assert v["brand_name"] == "Mercedes-Benz"
    assert v["source_address"] == 0x01

    # Geçersiz araç testi
    response_404 = client.get("/api/vehicle/bilinmeyen-arac")
    assert response_404.status_code == 404


def test_api_update_vehicle_speed(client):
    """Araç hız güncelleme endpoint testi"""
    payload = {"speed": 95.5, "mode": "highway"}
    response = client.post("/api/vehicle/scania-770s-v8/speed", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["target_speed"] == 95.5

    # Güncellenen aracı doğrula
    v_res = client.get("/api/vehicle/scania-770s-v8")
    assert v_res.json()["target_speed"] == 95.5


def test_api_brake_vehicle(client):
    """Araç fren endpoint testi"""
    response = client.post("/api/vehicle/volvo-fh16-750/brake", json={"pressed": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["brake_pressed"] is True


def test_api_set_fleet_speed(client):
    """Tüm filo hız atama testi"""
    response = client.post("/api/fleet/speed", json={"speed": 75.0})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["target_speed"] == 75.0


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


def test_index_page_served(client):
    """Ana web sayfasının başarıyla sunulduğunu doğrular"""
    response = client.get("/")
    assert response.status_code == 200
    assert "J1939 Fleet Telemetry" in response.text
    assert "speedGaugeCanvas" in response.text
