"""
J1939 Fleet Telemetry Web Server
FastAPI + Uvicorn + WebSockets + Python-CAN Bridge
"""

import argparse
import asyncio
import os
import shutil
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from can_bridge import CANBridge
from j1939.fleet_data import (
    FLEET_BRANDS, VEHICLES, get_all_vehicles, get_vehicle_by_id,
    add_vehicle as add_fleet_vehicle, add_brand as add_fleet_brand,
    delete_vehicle as delete_fleet_vehicle, get_next_available_source_address
)
from j1939.simulator import FleetSimulator

# Global instance'lar
can_bridge: CANBridge = None
simulator: FleetSimulator = None
connected_websockets: List[WebSocket] = []


class BrandCreateRequest(BaseModel):
    name: str = Field(..., description="Marka adı (örn: TOGG, Porsche, Ferrari)")
    color: str = Field(default="#00D2FF", description="Marka tema rengi hex kodu")
    country: str = Field(default="Global", description="Ülke")


class VehicleCreateRequest(BaseModel):
    brand_id: str = Field(..., description="Marka ID (örn: bmw, togg, porsche)")
    brand_name: str = Field(..., description="Marka Adı (örn: BMW, TOGG)")
    model: str = Field(..., description="Model adı (örn: T10X V2 Long Range)")
    category: str = Field(default="Sedan", description="Kategori (Sedan, SUV, EV, Coupe, Spor)")
    plate: str = Field(default="34 TGG 100", description="Plaka")
    engine: str = Field(default="Elektrik 218 HP", description="Motor / Güç")
    max_speed: float = Field(default=220.0, ge=50.0, le=450.0, description="Maksimum hız (km/h)")
    default_speed: float = Field(default=0.0, ge=0.0, le=250.0, description="Başlangıç hızı (km/h)")
    source_address: int = Field(default=None, description="J1939 Source Address (boşsa otomatik)")
    image_url: str = Field(default=None, description="Görsel URL veya yerel yol")


class SpeedUpdateRequest(BaseModel):
    speed: float = Field(..., ge=0.0, le=250.0, description="Araç hedef hızı (km/h)")
    mode: str = Field(default="manual", description="Simülasyon modu (manual, cruise, highway, city)")


class BrakeRequest(BaseModel):
    pressed: bool = Field(..., description="Fren durumu (True: basılı, False: serbest)")


class ScenarioRequest(BaseModel):
    scenario: str = Field(..., description="Filo senaryosu (highway, city, convoy, drag_race, idle)")


class FleetSpeedRequest(BaseModel):
    speed: float = Field(..., ge=0.0, le=250.0, description="Tüm filo için hedef hız (km/h)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI uygulama yaşam döngüsü yöneticisi"""
    global can_bridge, simulator
    # CAN Bus ve Simülatörü başlat
    if can_bridge is None:
        can_bridge = CANBridge(interface=os.getenv("CAN_INTERFACE", "virtual"),
                               channel=os.getenv("CAN_CHANNEL", "j1939_bus"),
                               bitrate=int(os.getenv("CAN_BITRATE", "250000")))

    if simulator is None:
        simulator = FleetSimulator(can_bridge=can_bridge, tick_rate_hz=10.0)

    # WebSocket yayıncısı için abone ekle
    async def broadcast_telemetry(payload: Dict[str, Any]):
        if not connected_websockets:
            return
        dead_sockets = []
        for ws in connected_websockets:
            try:
                await ws.send_json(payload)
            except Exception:
                dead_sockets.append(ws)
        for dead in dead_sockets:
            if dead in connected_websockets:
                connected_websockets.remove(dead)

    simulator.subscribe(broadcast_telemetry)
    simulator.start()

    yield

    # Kapanış işlemleri
    if simulator:
        simulator.stop()
    if can_bridge:
        can_bridge.close()


app = FastAPI(
    title="J1939 Telemetry & Fleet Web Platform",
    description="SAE J1939 CAN Bus (PGN 65265, SPN 84) Araç Hız Simülasyonu ve Canlı İzleme Sistemi",
    version="1.0.0",
    lifespan=lifespan
)

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Statik ve şablon dizinleri
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "web", "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "web", "templates")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# --- WEB ARAYÜZÜ ROUTE'LARI ---

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Ortam 2: Ana Telemetri ve Gösterge Paneli Web Sayfası (Monitor)"""
    index_path = os.path.join(TEMPLATES_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>J1939 Web Platform Hazirlaniyor...</h1>")


@app.get("/control", response_class=HTMLResponse)
@app.get("/sender", response_class=HTMLResponse)
async def serve_control():
    """Ortam 1: Bağımsız Hız Verme & Sinyal Gönderici Web Paneli (Transmitter)"""
    ctrl_path = os.path.join(TEMPLATES_DIR, "control.html")
    if os.path.exists(ctrl_path):
        return FileResponse(ctrl_path)
    return HTMLResponse("<h1>J1939 Kontrol Paneli Hazirlaniyor...</h1>")


# --- REST API ENDPOINT'LERİ ---

@app.get("/api/health")
async def health_check():
    """Konteyner ve sistem sağlık kontrolü"""
    return {
        "status": "healthy",
        "can_connected": can_bridge.is_connected if can_bridge else False,
        "simulator_running": simulator.is_running if simulator else False,
        "active_vehicles": len(simulator.vehicles_state) if simulator else 0,
    }


@app.get("/api/brands")
async def get_brands():
    """10 Araç markasının listesini ve renk temalarını döndürür"""
    return FLEET_BRANDS


@app.get("/api/fleet")
async def get_fleet():
    """30 Aracın anlık telemetri ve J1939 durumlarını döndürür"""
    if simulator:
        return simulator.get_fleet_summary()
    return get_all_vehicles()


@app.get("/api/vehicle/{vehicle_id}")
async def get_vehicle(vehicle_id: str):
    """Tek bir aracın durumunu döndürür"""
    if simulator:
        v = simulator.get_vehicle(vehicle_id)
        if v:
            return v
    try:
        return get_vehicle_by_id(vehicle_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Araç bulunamadı")


@app.post("/api/vehicle/{vehicle_id}/speed")
async def update_vehicle_speed(vehicle_id: str, req: SpeedUpdateRequest):
    """Belirli bir aracın hızını ayarlar"""
    if not simulator:
        raise HTTPException(status_code=500, detail="Simülatör hazır değil")
    success = simulator.set_vehicle_speed(vehicle_id, req.speed, req.mode)
    if not success:
        raise HTTPException(status_code=404, detail="Araç bulunamadı")
    return {"status": "ok", "vehicle_id": vehicle_id, "target_speed": req.speed, "mode": req.mode}


@app.post("/api/vehicle/{vehicle_id}/brake")
async def brake_vehicle(vehicle_id: str, req: BrakeRequest):
    """Araca fren uygular veya serbest bırakır"""
    if not simulator:
        raise HTTPException(status_code=500, detail="Simülatör hazır değil")
    success = simulator.brake_vehicle(vehicle_id, req.pressed)
    if not success:
        raise HTTPException(status_code=404, detail="Araç bulunamadı")
    return {"status": "ok", "vehicle_id": vehicle_id, "brake_pressed": req.pressed}


import re
import time

def sanitize_slug(text: str) -> str:
    """Türkçe ve özel karakterleri güvenli ASCII ID formatına dönüştürür"""
    if not text:
        return ""
    tr_map = str.maketrans("çğıöşüÇĞİÖŞÜ ", "cgiosuCGIOSU-")
    clean = text.translate(tr_map).lower()
    clean = re.sub(r'[^a-z0-9\-]', '', clean)
    return re.sub(r'-+', '-', clean).strip('-')


@app.post("/api/vehicle/{vehicle_id}/upload-image")
async def upload_vehicle_image(vehicle_id: str, file: UploadFile = File(...)):
    """Seçili araç için fotoğraf yükleme ve tüm sistemde kalıcı güncelleme endpoint'i"""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp", ".svg"]:
        ext = ".jpg"
    cars_dir = os.path.join(STATIC_DIR, "images", "cars")
    os.makedirs(cars_dir, exist_ok=True)

    # Eski farklı uzantılı dosyaları temizle (çakışmayı önle)
    for old_ext in [".jpg", ".jpeg", ".png", ".webp", ".svg"]:
        old_file = os.path.join(cars_dir, f"{vehicle_id}{old_ext}")
        if os.path.exists(old_file) and old_ext != ext:
            try:
                os.remove(old_file)
            except Exception:
                pass

    dest_path = os.path.join(cars_dir, f"{vehicle_id}{ext}")
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    version_ts = int(time.time())
    new_image_url = f"/static/images/cars/{vehicle_id}{ext}?v={version_ts}"

    # 1. fleet_data içinde güncelle ve kalıcı kaydet
    update_vehicle_image_url(vehicle_id, new_image_url)

    # 2. Simulator vehicles_state içinde güncelle
    if simulator and vehicle_id in simulator.vehicles_state:
        simulator.vehicles_state[vehicle_id]["image_url"] = new_image_url

    # 3. WebSocket üzerinden canlı güncelleme bildir
    for ws in connected_websockets:
        try:
            await ws.send_json({
                "type": "vehicle_image_updated",
                "vehicle_id": vehicle_id,
                "image_url": new_image_url
            })
        except Exception:
            pass

    return {
        "status": "ok",
        "vehicle_id": vehicle_id,
        "image_url": new_image_url,
        "message": f"{vehicle_id} görseli kalıcı olarak güncellendi."
    }


@app.get("/api/fleet/next-sa")
async def get_next_sa():
    """Boşta olan bir sonraki benzersiz J1939 Source Address'i döndürür"""
    sa = get_next_available_source_address()
    return {"status": "ok", "source_address": sa, "source_address_hex": f"0x{sa:02X}"}


@app.post("/api/fleet/add-brand")
async def create_brand(req: BrandCreateRequest):
    """Yeni özel otomobil markası ekler"""
    brand_slug = sanitize_slug(req.name) or "brand"
    brand_dict = {
        "id": brand_slug,
        "name": req.name.strip(),
        "color": req.color.strip(),
        "country": req.country.strip(),
        "badge": req.name[:4].upper()
    }
    created = add_fleet_brand(brand_dict)

    # WebSocket üzerinden tüm istemcilere bildir
    for ws in connected_websockets:
        try:
            await ws.send_json({
                "type": "brand_added",
                "brand": created,
                "brands": FLEET_BRANDS
            })
        except Exception:
            pass

    return {"status": "ok", "brand": created}


@app.post("/api/fleet/add-vehicle")
async def create_vehicle(
    brand_id: str = Form(...),
    brand_name: str = Form(...),
    model: str = Form(...),
    category: str = Form("Sedan"),
    plate: str = Form("34 NEW 001"),
    engine: str = Form("2.0L Turbo 200 HP"),
    powertrain: str = Form("ice"),
    is_ev: Optional[str] = Form(None),
    max_speed: Optional[str] = Form("220.0"),
    default_speed: Optional[str] = Form("0.0"),
    source_address: Optional[str] = Form(None),
    file: Optional[UploadFile] = None
):
    """Yeni araç oluşturur, fotoğrafı kaydeder ve simülatöre dahil eder (hataya dayanıklı)"""
    try:
        brand_part = sanitize_slug(brand_id) or "car"
        model_part = sanitize_slug(model) or "model"
        v_id = f"{brand_part}-{model_part}"

        # is_ev güvenli çözümleme
        is_ev_bool = False
        if is_ev is not None:
            if isinstance(is_ev, bool):
                is_ev_bool = is_ev
            elif str(is_ev).lower() in ("true", "1", "ev", "yes"):
                is_ev_bool = True
        if powertrain == "ev":
            is_ev_bool = True

        # SA güvenli çözümleme
        sa_int = None
        if source_address:
            try:
                sa_int = int(str(source_address).strip())
            except (ValueError, TypeError):
                sa_int = None
        if sa_int is None:
            sa_int = get_next_available_source_address()

        # max_speed ve default_speed
        try:
            max_spd_val = float(str(max_speed).replace(",", "."))
        except (ValueError, TypeError):
            max_spd_val = 220.0

        try:
            def_spd_val = float(str(default_speed).replace(",", "."))
        except (ValueError, TypeError):
            def_spd_val = 0.0

        cars_dir = os.path.join(STATIC_DIR, "images", "cars")
        os.makedirs(cars_dir, exist_ok=True)
        version_ts = int(time.time())

        # Fotoğraf yüklendiyse diske kaydet
        image_url = f"/static/images/cars/{v_id}.jpg?v={version_ts}"
        if file and file.filename:
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in [".jpg", ".jpeg", ".png", ".webp", ".svg"]:
                ext = ".jpg"
            # Eski uzantıları temizle
            for old_ext in [".jpg", ".jpeg", ".png", ".webp", ".svg"]:
                old_file = os.path.join(cars_dir, f"{v_id}{old_ext}")
                if os.path.exists(old_file) and old_ext != ext:
                    try:
                        os.remove(old_file)
                    except Exception:
                        pass

            dest_path = os.path.join(cars_dir, f"{v_id}{ext}")
            with open(dest_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            image_url = f"/static/images/cars/{v_id}{ext}?v={version_ts}"

        v_data = {
            "id": v_id,
            "brand_id": brand_id.strip(),
            "brand_name": brand_name.strip(),
            "model": model.strip(),
            "category": category.strip(),
            "plate": plate.strip(),
            "engine": engine.strip(),
            "powertrain": "ev" if is_ev_bool else powertrain,
            "is_ev": is_ev_bool,
            "max_speed": max_spd_val,
            "default_speed": def_spd_val,
            "source_address": sa_int,
            "image_url": image_url
        }

        created_v = add_fleet_vehicle(v_data)

        if simulator:
            simulator.add_vehicle(created_v)

        # WebSocket üzerinden canlı güncelleme bildir
        for ws in connected_websockets:
            try:
                await ws.send_json({
                    "type": "vehicle_added",
                    "vehicle": created_v,
                    "fleet": simulator.get_fleet_summary() if simulator else VEHICLES,
                    "brands": FLEET_BRANDS
                })
            except Exception:
                pass

        return {"status": "ok", "vehicle": created_v}
    except Exception as err:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Araç ekleme hatası: {str(err)}")


@app.delete("/api/vehicle/{vehicle_id}")
async def remove_vehicle_endpoint(vehicle_id: str):
    """Filodan bir aracı siler"""
    deleted = delete_fleet_vehicle(vehicle_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Araç bulunamadı")

    if simulator:
        simulator.remove_vehicle(vehicle_id)

    # WebSocket yayını
    for ws in connected_websockets:
        try:
            await ws.send_json({
                "type": "vehicle_removed",
                "vehicle_id": vehicle_id,
                "fleet": simulator.get_fleet_summary() if simulator else VEHICLES
            })
        except Exception:
            pass

    return {"status": "ok", "message": f"{vehicle_id} başarıyla silindi."}


@app.post("/api/fleet/speed")
async def set_fleet_speed(req: FleetSpeedRequest):
    """Tüm araçlara aynı hızı atar"""
    if not simulator:
        raise HTTPException(status_code=500, detail="Simülatör hazır değil")
    simulator.set_fleet_speed(req.speed)
    return {"status": "ok", "target_speed": req.speed, "vehicles_count": len(simulator.vehicles_state)}


@app.post("/api/fleet/scenario")
async def apply_scenario(req: ScenarioRequest):
    """Filo sürüş senaryosunu uygular"""
    if not simulator:
        raise HTTPException(status_code=500, detail="Simülatör hazır değil")
    simulator.apply_scenario(req.scenario)
    return {"status": "ok", "scenario": req.scenario}


@app.post("/api/fleet/emergency-stop")
async def emergency_stop():
    """Tüm araçları acil durdurur"""
    if not simulator:
        raise HTTPException(status_code=500, detail="Simülatör hazır değil")
    simulator.emergency_stop_all()
    return {"status": "ok", "action": "emergency_stop"}


@app.get("/api/can/history")
async def get_can_history():
    """Son üretilen J1939 CAN paket geçmişini döndürür"""
    if not simulator:
        return []
    return simulator.recent_frames


# --- WEBSOCKET CANLI TELEMETRİ VE KONTROL ---

@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    """Gerçek zamanlı iki yönlü WebSocket telemetri akışı"""
    await websocket.accept()
    connected_websockets.append(websocket)
    try:
        # Bağlantı kurulduğunda ilk filo özetini gönder
        if simulator:
            await websocket.send_json({
                "type": "initial_fleet",
                "brands": FLEET_BRANDS,
                "fleet": simulator.get_fleet_summary(),
                "recent_frames": simulator.recent_frames[:50]
            })

        while True:
            # İstemciden gelen kontrol komutlarını dinle
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "set_speed" and simulator:
                v_id = data.get("vehicle_id")
                spd = float(data.get("speed", 0.0))
                simulator.set_vehicle_speed(v_id, spd)

            elif action == "accelerate" and simulator:
                v_id = data.get("vehicle_id")
                delta = float(data.get("delta", 10.0))
                simulator.accelerate_vehicle(v_id, delta)

            elif (action == "decelerate" or action == "brake") and simulator:
                v_id = data.get("vehicle_id")
                delta = float(data.get("delta", 15.0))
                simulator.brake_vehicle(v_id, delta)

            elif action == "full_stop" and simulator:
                v_id = data.get("vehicle_id")
                simulator.full_stop_vehicle(v_id)

            elif action == "set_fleet_speed" and simulator:
                spd = float(data.get("speed", 0.0))
                simulator.set_fleet_speed(spd)

            elif action == "set_scenario" and simulator:
                scen = data.get("scenario", "normal")
                simulator.apply_scenario(scen)

            elif action == "emergency_stop" and simulator:
                simulator.emergency_stop_all()

    except WebSocketDisconnect:
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)
    except Exception:
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)


def main():
    parser = argparse.ArgumentParser(description="J1939 Fleet Telemetry Web Platform")
    parser.add_argument("--host", default="0.0.0.0", help="Sunucu dinleme IP adresi (Varsayılan: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Sunucu dinleme portu (Varsayılan: 8000)")
    parser.add_argument("--interface", default="virtual", choices=["virtual", "pcan", "socketcan"],
                        help="CAN Arayüzü (virtual / pcan / socketcan)")
    parser.add_argument("--channel", default="j1939_bus", help="CAN Kanalı (Örn: PCAN_USBBUS1)")
    parser.add_argument("--bitrate", type=int, default=250000, help="CAN Baudrate (J1939 Standart: 250000)")
    parser.add_argument("--reload", action="store_true", help="Uvicorn otomatik yeniden yükleme")
    args = parser.parse_args()

    os.environ["CAN_INTERFACE"] = args.interface
    os.environ["CAN_CHANNEL"] = args.channel
    os.environ["CAN_BITRATE"] = str(args.bitrate)

    print("=" * 70)
    print(" [*] J1939 Fleet Telemetry Web Platform Baslatiliyor...")
    print(f" [*] Web Dashboard: http://localhost:{args.port}")
    print(f" [*] CAN Arayuzu  : {args.interface.upper()} (Kanal: {args.channel} @ {args.bitrate} bps)")
    print(f" [*] Filo Boyutu   : 10 Marka x 3 Model = 30 Arac (J1939 SA: 0x01..0x1E)")
    print(f" [*] Sinyal        : PGN 65265 (0xFEF1 - CCVS) / SPN 84 (Wheel-Based Speed)")
    print("=" * 70)

    uvicorn.run("server:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
