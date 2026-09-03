"""
SAE J1939 Fleet Telemetry Simulator & Physics Engine
Generates real-time 29-bit CAN frames for 30 vehicles across 4 distinct PGNs:
- PGN 65265 (0xFEF1 - CCVS1): SPN 84 (Speed) & SPN 563 (Brake Switch)
- PGN 61443 (0xF003 - EEC2) : SPN 91 (Throttle Pedal %)
- PGN 61445 (0xF005 - ETC2) : SPN 523 (Transmission Gear P/R/N/D1..D8)
- PGN 65110 (0xFE56 - HVS)  : SPN 3543 (Battery SOC %) & SPN 5328 (Battery SOH %)
"""

import asyncio
import copy
import random
import time
from typing import Dict, List, Any, Optional, Callable
from .protocol import J1939Codec, J1939Frame, PGN_CCVS, PGN_EEC2, PGN_ETC2, PGN_HVS
from .fleet_data import VEHICLES, get_all_vehicles


class FleetSimulator:
    """30 Araçlık J1939 Çoklu Sinyal ve Telemetri Simülasyon Motoru"""

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
        """Belirli bir aracın hedef hızını ayarlar"""
        if vehicle_id in self.vehicles_state:
            v = self.vehicles_state[vehicle_id]
            clamped = max(0.0, min(v["max_speed"], float(target_speed)))
            v["target_speed"] = clamped
            v["simulation_mode"] = mode
            v["brake_pressed"] = (clamped < v["current_speed"] - 2.0)
            return True
        return False

    def accelerate_vehicle(self, vehicle_id: str, delta: float = 10.0) -> bool:
        """Aracın hedef hızını kademeli artırır (+10 km/h)"""
        if vehicle_id in self.vehicles_state:
            v = self.vehicles_state[vehicle_id]
            new_target = min(v["max_speed"], v["target_speed"] + delta)
            v["target_speed"] = new_target
            v["brake_pressed"] = False
            v["simulation_mode"] = "manual"
            return True
        return False

    def brake_vehicle(self, vehicle_id: str, delta: float = 15.0) -> bool:
        """Araca kademeli fren uygular (-15 km/h)"""
        if vehicle_id in self.vehicles_state:
            v = self.vehicles_state[vehicle_id]
            new_target = max(0.0, v["target_speed"] - delta)
            v["target_speed"] = new_target
            v["brake_pressed"] = True
            v["simulation_mode"] = "manual"
            return True
        return False

    def full_stop_vehicle(self, vehicle_id: str) -> bool:
        """Aracı durmaya doğru yavaşlatır (0 km/h)"""
        if vehicle_id in self.vehicles_state:
            v = self.vehicles_state[vehicle_id]
            v["target_speed"] = 0.0
            v["brake_pressed"] = True
            v["simulation_mode"] = "manual"
            return True
        return False

    def set_fleet_speed(self, target_speed: float) -> None:
        """Tüm filoya ortak hedef hız atar"""
        for v in self.vehicles_state.values():
            clamped = max(0.0, min(v["max_speed"], float(target_speed)))
            v["target_speed"] = clamped
            v["simulation_mode"] = "manual"
            v["brake_pressed"] = (clamped < v["current_speed"] - 2.0)

    def emergency_stop_all(self) -> None:
        """Tüm araçları kademeli olarak 0'a frenler"""
        for v in self.vehicles_state.values():
            v["target_speed"] = 0.0
            v["brake_pressed"] = True

    def apply_scenario(self, scenario_name: str) -> None:
        """Filo sürüş senaryoları"""
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

    def add_vehicle(self, vehicle_data: Dict[str, Any]) -> Dict[str, Any]:
        """Çalışma zamanında simülatöre yeni araç ekler"""
        v = copy.deepcopy(vehicle_data)
        self.vehicles_state[v["id"]] = v
        return v

    def remove_vehicle(self, vehicle_id: str) -> bool:
        """Çalışma zamanında simülatörden araç çıkarır"""
        if vehicle_id in self.vehicles_state:
            del self.vehicles_state[vehicle_id]
            return True
        return False

    def _calculate_gear(self, current_speed: float, is_ev: bool) -> str:
        """Hıza ve aktarma organına göre vites hesaplar"""
        if is_ev:
            return "P" if current_speed < 0.5 else "D"

        if current_speed < 0.5:
            return "P"
        elif current_speed < 25.0:
            return "D1"
        elif current_speed < 50.0:
            return "D2"
        elif current_speed < 75.0:
            return "D3"
        elif current_speed < 105.0:
            return "D4"
        elif current_speed < 135.0:
            return "D5"
        elif current_speed < 170.0:
            return "D6"
        elif current_speed < 210.0:
            return "D7"
        else:
            return "D8"

    def _update_vehicle_physics(self, v: Dict[str, Any], dt: float) -> float:
        """
        Gerçekçi Otomotiv Dinamiği:
        - Hız hesabı (Aerodinamik sürtünme F_drag ~ v^2 ile)
        - Gaz Pedalı Açıklığı (% 0-100)
        - Fren Pedalı Basıncı (% 0-100)
        - Vites Durumu (P/R/N/D1..D8)
        - Batarya Seviyesi (SOC %) ve Sağlığı (SOH %)
        """
        current = v["current_speed"]
        target = v["target_speed"]
        base_accel = v.get("acceleration_rate", 6.0)
        max_speed = v.get("max_speed", 250.0)
        # EV kontrolü
        is_ev = v.get("is_ev", False) or "EV" in v.get("category", "") or "Elektrik" in v.get("engine", "") or "tesla" in v.get("brand_id", "") or v.get("powertrain") == "ev"

        diff = target - current

        if abs(diff) > 0.05:
            if diff > 0:
                # ⚡ HIZLANMA & GAZ PEDALI
                speed_ratio = min(1.0, current / max_speed)
                drag_factor = max(0.12, 1.0 - 0.85 * (speed_ratio ** 1.8))
                effective_accel = base_accel * drag_factor

                step = effective_accel * dt
                if diff <= step:
                    current = target
                else:
                    current += step

                # Gaz pedalı konumu: Talep edilen ivmeyle orantılı
                v["throttle_pct"] = round(min(100.0, max(25.0, 30.0 + min(70.0, diff * 3.5))), 1)
                v["brake_pct"] = 0.0
                v["brake_pressed"] = False

            else:
                # 🛑 FRENLEME & FREN PEDALI
                speed_ratio = min(1.0, current / max_speed)
                brake_factor = 1.0 + 0.4 * speed_ratio
                effective_brake = (base_accel * 1.8) * brake_factor

                step = effective_brake * dt
                if abs(diff) <= step:
                    current = target
                else:
                    current -= step

                # Fren pedalı konumu: Yavaşlama şiddetiyle orantılı
                v["throttle_pct"] = 0.0
                v["brake_pct"] = round(min(100.0, max(30.0, min(100.0, abs(diff) * 4.0))), 1)
                v["brake_pressed"] = True
        else:
            current = target
            v["brake_pct"] = 0.0
            v["brake_pressed"] = False
            if current > 2.0:
                # Sabit hızda (Cruise) hava direncini yenmek için gereken gaz miktarı (%10 - %30)
                v["throttle_pct"] = round(min(32.0, 10.0 + (current / max_speed) * 20.0), 1)
            else:
                v["throttle_pct"] = 0.0

        # Vites durumunu güncelle
        v["current_speed"] = round(current, 2)
        v["gear"] = self._calculate_gear(v["current_speed"], is_ev)

        # Batarya mikro tüketimi (sürüş mesafesine bağlı hafif deşarj)
        if current > 0.5:
            drain = (current / 3600.0) * 0.005 * dt
            v["battery_soc"] = round(max(10.0, v.get("battery_soc", 90.0) - drain), 2)

        v["status"] = "stopped" if current < 0.5 else ("braking" if v.get("brake_pressed") else ("accelerating" if target > current + 1.0 else "cruising"))
        return v["current_speed"]

    async def _simulation_loop(self):
        """Simülasyon arka plan döngüsü (hataya dayanıklı)"""
        last_time = time.time()
        frame_cycle_counter = 0

        while self.is_running:
            try:
                now = time.time()
                dt = max(0.01, min(0.5, now - last_time))
                last_time = now
                frame_cycle_counter += 1

                batch_frames = []

                # Filodaki araçların her biri için fizik ve J1939 çerçeveleri oluştur
                for v_id, v in list(self.vehicles_state.items()):
                    try:
                        speed = self._update_vehicle_physics(v, dt)
                        sa = int(v.get("source_address", 0x01))

                        # 1. PGN 65265 (0xFEF1 - CCVS1): Araç Hızı & Fren Switch
                        frame_speed = J1939Codec.encode_speed_frame(
                            speed_kmh=speed,
                            source_address=sa,
                            priority=6,
                            brake_pressed=bool(v.get("brake_pressed", False))
                        )
                        dict_speed = frame_speed.to_dict()
                        dict_speed.update({"vehicle_id": v_id, "brand_name": v.get("brand_name", ""), "model": v.get("model", ""), "plate": v.get("plate", "")})
                        v["last_frame"] = dict_speed
                        batch_frames.append(dict_speed)

                        # 2. PGN 61443 (0xF003 - EEC2): Gaz Pedalı Açıklığı (%)
                        frame_throttle = J1939Codec.encode_throttle_frame(
                            throttle_pct=float(v.get("throttle_pct", 0.0)),
                            source_address=sa,
                            priority=6
                        )
                        dict_throttle = frame_throttle.to_dict()
                        dict_throttle.update({"vehicle_id": v_id, "brand_name": v.get("brand_name", ""), "model": v.get("model", ""), "plate": v.get("plate", "")})
                        batch_frames.append(dict_throttle)

                        # 3. PGN 61445 (0xF005 - ETC2): Vites Bilgisi (Her 2 döngüde bir)
                        if frame_cycle_counter % 2 == 0:
                            frame_gear = J1939Codec.encode_gear_frame(
                                gear_str=str(v.get("gear", "D")),
                                source_address=sa,
                                priority=6
                            )
                            dict_gear = frame_gear.to_dict()
                            dict_gear.update({"vehicle_id": v_id, "brand_name": v.get("brand_name", ""), "model": v.get("model", ""), "plate": v.get("plate", "")})
                            batch_frames.append(dict_gear)

                        # 4. PGN 65110 (0xFE56 - HVS): Batarya SOC & SOH (Her 3 döngüde bir)
                        if frame_cycle_counter % 3 == 0:
                            frame_battery = J1939Codec.encode_battery_frame(
                                soc_pct=float(v.get("battery_soc", 90.0)),
                                soh_pct=float(v.get("battery_soh", 98.0)),
                                source_address=sa,
                                priority=6
                            )
                            dict_battery = frame_battery.to_dict()
                            dict_battery.update({"vehicle_id": v_id, "brand_name": v.get("brand_name", ""), "model": v.get("model", ""), "plate": v.get("plate", "")})
                            batch_frames.append(dict_battery)

                        # CAN bus donanım/sanal köprüsüne gönder
                        if self.can_bridge:
                            self.can_bridge.send_j1939_frame(frame_speed)

                    except Exception as err:
                        print(f"Araç simülasyon hatası ({v_id}): {err}")

                # Toplam gönderilen mesaj sayacını doğru artır
                self.total_frames_sent += len(batch_frames)

                # Rolling buffer'a ekle (Son 300 paket)
                self.recent_frames = (batch_frames + self.recent_frames)[:self.max_history_size]

                # Abonelere (WebSockets) canlı telemetri paketi gönder
                telemetry_payload = {
                    "type": "telemetry_update",
                    "timestamp": now,
                    "fleet": list(self.vehicles_state.values()),
                    "batch_frames": batch_frames[:15],
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

            except Exception as e:
                print(f"Simülasyon ana döngü hatası: {e}")

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
