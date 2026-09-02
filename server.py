"""
J1939 Fleet Telemetry Web Server
FastAPI + Uvicorn + WebSockets + Python-CAN Bridge
"""

import argparse
import asyncio
import os
from contextlib import asynccontextmanager
from typing import List, Dict, Any

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from can_bridge import CANBridge
from j1939.fleet_data import FLEET_BRANDS, VEHICLES, get_all_vehicles, get_vehicle_by_id
from j1939.simulator import FleetSimulator

# Global instance'lar
can_bridge: CANBridge = None
simulator: FleetSimulator = None
connected_websockets: List[WebSocket] = []


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

            elif action == "brake" and simulator:
                v_id = data.get("vehicle_id")
                pressed = bool(data.get("pressed", True))
                simulator.brake_vehicle(v_id, pressed)

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
