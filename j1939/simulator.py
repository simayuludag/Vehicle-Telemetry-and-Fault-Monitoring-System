"""
SAE J1939 Fleet Telemetry Simulator & Physics Engine
Generates real-time 29-bit CAN frames (PGN 65265, SPN 84) for 30 vehicles.
Features smooth, realistic, gradual acceleration and braking physics.
"""

import asyncio
import copy
import random
import time
from typing import Dict, List, Any, Optional, Callable
from .protocol import J1939Codec, J1939Frame, PGN_CCVS
from .fleet_data import VEHICLES, get_all_vehicles


class FleetSimulator:
    """30 Araçlık J1939 Hız ve Telemetri Simülasyon Motoru"""

    def __init__(self, can_bridge=None, tick_rate_hz: float = 10.0):
        self.can_bridge = can_bridge
        self.tick_rate_hz = tick_rate_hz
        self.tick_interval = 1.0 / tick_rate_hz
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.subscribers: List[Callable[[Dict[str, Any]], None]] = []

        # 30 aracın çalışma zamanı durumu
        self.vehicles_state: Dict[str, Dict[str, Any]] = {}
        for v in copy.deepcopy(VEHICLES):
            self.vehicles_state[v["id"]] = v

        # Son üretilen CAN mesajları geçmişi (Rolling Buffer, son 300 mesaj)
        self.recent_frames: List[Dict[str, Any]] = []
        self.max_history_size = 300

        # İstatistikler
        self.total_frames_sent = 0
        self.start_time = time.time()
        self.active_scenario = "normal"

    def subscribe(self, callback: Callable[[Dict[str, Any]], None]):
        """WebSocket veya UI bildirimleri için abone ekler"""
        if callback not in self.subscribers:
            self.subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[Dict[str, Any]], None]):
        """Aboneliği kaldırır"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)

    def get_fleet_summary(self) -> List[Dict[str, Any]]:
        """Tüm araçların anlık durum listesi"""
        return list(self.vehicles_state.values())

    def get_vehicle(self, vehicle_id: str) -> Optional[Dict[str, Any]]:
        """Tek bir aracın anlık durumu"""
        return self.vehicles_state.get(vehicle_id)

    def set_vehicle_speed(self, vehicle_id: str, target_speed: float, mode: str = "manual") -> bool:
        """Belirli bir aracın hedef hızını ayarlar (anlık zıplama olmadan kademeli hızlanma)"""
        if vehicle_id in self.vehicles_state:
            v = self.vehicles_state[vehicle_id]
            clamped = max(0.0, min(v["max_speed"], float(target_speed)))
            v["target_speed"] = clamped
            v["simulation_mode"] = mode
            v["brake_pressed"] = False
            return True
        return False

    def accelerate_vehicle(self, vehicle_id: str, delta: float = 10.0) -> bool:
        """Aracın hedef hızını kademeli olarak artırır (+10 km/h)"""
        if vehicle_id in self.vehicles_state:
            v = self.vehicles_state[vehicle_id]
            new_target = min(v["max_speed"], v["target_speed"] + delta)
            v["target_speed"] = new_target
            v["brake_pressed"] = False
            v["simulation_mode"] = "manual"
            return True
        return False

    def brake_vehicle(self, vehicle_id: str, delta: float = 15.0) -> bool:
        """Araca kademeli fren uygular (-15 km/h, direkt 0'a düşürmez, yavaşça azaltır)"""
        if vehicle_id in self.vehicles_state:
            v = self.vehicles_state[vehicle_id]
            new_target = max(0.0, v["target_speed"] - delta)
            v["target_speed"] = new_target
            v["brake_pressed"] = (new_target == 0.0)
            v["simulation_mode"] = "manual"
            return True
        return False

    def full_stop_vehicle(self, vehicle_id: str) -> bool:
        """Aracı kademeli olarak durmaya yönlendirir (0 km/h)"""
        if vehicle_id in self.vehicles_state:
            v = self.vehicles_state[vehicle_id]
            v["target_speed"] = 0.0
            v["brake_pressed"] = True
            v["simulation_mode"] = "manual"
            return True
        return False

    def set_fleet_speed(self, target_speed: float) -> None:
        """Tüm filoya ortak hedef hız atar (araçlar kendi ivmelerine göre kademeli ulaşır)"""
        for v in self.vehicles_state.values():
            clamped = max(0.0, min(v["max_speed"], float(target_speed)))
            v["target_speed"] = clamped
            v["simulation_mode"] = "manual"
            v["brake_pressed"] = False

    def emergency_stop_all(self) -> None:
        """Tüm araçları kademeli olarak 0'a frenler"""
        for v in self.vehicles_state.values():
            v["target_speed"] = 0.0
            v["brake_pressed"] = True

    def apply_scenario(self, scenario_name: str) -> None:
        """
        Filo sürüş senaryoları:
        - 'highway': Otoyol (120 km/h)
        - 'city': Şehir içi (50 km/h)
        - 'convoy': Konvoy modu (Sabit 90 km/h)
        - 'drag_race': Performans hızlanma testi (Maksimum hız)
        - 'idle': Park (0 km/h)
        """
        self.active_scenario = scenario_name
        for v in self.vehicles_state.values():
            v["brake_pressed"] = False
            if scenario_name == "highway":
                v["target_speed"] = min(120.0, v["max_speed"])
                v["simulation_mode"] = "highway"
            elif scenario_name == "city":
                v["target_speed"] = min(50.0, v["max_speed"])
                v["simulation_mode"] = "city"
            elif scenario_name == "convoy":
                v["target_speed"] = min(90.0, v["max_speed"])
                v["simulation_mode"] = "cruise"
            elif scenario_name == "drag_race":
                v["target_speed"] = v["max_speed"]
                v["simulation_mode"] = "manual"
            elif scenario_name == "idle":
                v["target_speed"] = 0.0
                v["simulation_mode"] = "manual"

    def _update_vehicle_physics(self, v: Dict[str, Any], dt: float) -> float:
        """
        Gerçekçi Otomotiv Dinamiği ve Hava Direnci (Aerodynamic Drag) Fiziği:
        - Düşük hızlarda (0-80 km/h) motor torku yüksektir, araç çok hızlı ivmelenir.
        - Hız arttıkça hava sürtünmesi (F_drag ~ v^2) ve güç limiti nedeniyle ivmelenme azalır.
          Örn: 0-100 km/h hızlanması 5 sn süren bir araç için 100-200 km/h hızlanması ~12-16 sn sürer.
        """
        current = v["current_speed"]
        target = v["target_speed"]
        base_accel = v.get("acceleration_rate", 6.0)
        max_speed = v.get("max_speed", 250.0)

        diff = target - current

        if abs(diff) > 0.05:
            if diff > 0:
                # ⚡ HIZLANMA: Aerodinamik direnç ve yüksek hızda düşen ivme eğrisi
                speed_ratio = min(1.0, current / max_speed)
                # Karesel hava sürtünmesi faktörü: 0 km/h'de 1.0 çarpan, son hıza yaklaştıkça %12'ye kadar iner
                drag_factor = max(0.12, 1.0 - 0.85 * (speed_ratio ** 1.8))
                effective_accel = base_accel * drag_factor

                step = effective_accel * dt
                if diff <= step:
                    current = target
                else:
                    current += step
            else:
                # 🛑 FRENLEME: Mekanik disk freni + yüksek hızda hava direnci desteği
                speed_ratio = min(1.0, current / max_speed)
                brake_factor = 1.0 + 0.4 * speed_ratio
                effective_brake = (base_accel * 1.8) * brake_factor

                step = effective_brake * dt
                if abs(diff) <= step:
                    current = target
                else:
                    current -= step
        else:
            current = target

        v["current_speed"] = round(current, 2)
        v["status"] = "stopped" if current < 0.5 else ("braking" if target < current - 1.0 else ("accelerating" if target > current + 1.0 else "cruising"))
        return v["current_speed"]

    async def _simulation_loop(self):
        """Simülasyon arka plan döngüsü"""
        last_time = time.time()
        while self.is_running:
            now = time.time()
            dt = max(0.01, now - last_time)
            last_time = now

            batch_frames = []

            # 30 aracın her biri için fizik ve J1939 CAN çerçevesi oluştur
            for v_id, v in self.vehicles_state.items():
                speed = self._update_vehicle_physics(v, dt)

                # J1939 29-bit CAN Çerçevesini Kodla (PGN 65265, SPN 84)
                frame: J1939Frame = J1939Codec.encode_speed_frame(
                    speed_kmh=speed,
                    source_address=v["source_address"],
                    priority=6,
                    pgn=PGN_CCVS,
                    brake_pressed=v["brake_pressed"]
                )

                frame_dict = frame.to_dict()
                frame_dict["vehicle_id"] = v_id
                frame_dict["brand_name"] = v["brand_name"]
                frame_dict["model"] = v["model"]
                frame_dict["plate"] = v["plate"]

                # Son çerçeveyi araç durumuna kaydet
                v["last_frame"] = frame_dict

                # CAN bus donanım/sanal köprüsüne gönder
                if self.can_bridge:
                    self.can_bridge.send_j1939_frame(frame)

                batch_frames.append(frame_dict)
                self.total_frames_sent += 1

            # Rolling buffer'a ekle (Son 300 paket)
            self.recent_frames = (batch_frames + self.recent_frames)[:self.max_history_size]

            # Abonelere (WebSockets) canlı telemetri paketi gönder
            telemetry_payload = {
                "type": "telemetry_update",
                "timestamp": now,
                "fleet": list(self.vehicles_state.values()),
                "batch_frames": batch_frames[:10],  # UI için en son 10 çerçeve
                "stats": {
                    "total_frames": self.total_frames_sent,
                    "active_vehicles": len(self.vehicles_state),
                    "scenario": self.active_scenario,
                    "uptime_sec": int(now - self.start_time),
                }
            }

            for sub in list(self.subscribers):
                try:
                    if asyncio.iscoroutinefunction(sub):
                        await sub(telemetry_payload)
                    else:
                        sub(telemetry_payload)
                except Exception:
                    pass

            await asyncio.sleep(self.tick_interval)

    def start(self):
        """Simülasyon motorunu başlatır"""
        if not self.is_running:
            self.is_running = True
            self.start_time = time.time()
            self._task = asyncio.create_task(self._simulation_loop())

    def stop(self):
        """Simülasyon motorunu durdurur"""
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
