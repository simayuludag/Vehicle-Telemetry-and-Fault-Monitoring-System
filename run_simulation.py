"""
CAN Simülasyon Çalıştırıcısı (All-in-One Virtual Simulation)
GitHub'dan projeyi indiren veya PCAN donanımı olmayan kişilerin
tek bir komutla hem göndericiyi hem alıcıyı canlı görebilmesini sağlar.
"""

import sys
import os
import time
import math
import struct
import threading
from datetime import datetime

# Windows konsollarında UTF-8 desteğini etkinleştir
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel

import can
from config import (
    ID_ENGINE_DATA,
    ID_VEHICLE_SPEED,
    ID_BATTERY_STATUS,
    CAN_MESSAGES,
)
from can_sender import pack_engine_data, pack_vehicle_speed, pack_battery_status
from can_receiver import decode_message, build_dashboard_table

console = Console(legacy_windows=False)

SIMULATION_CHANNEL = "github_virtual_bus"


def sender_worker(bus: can.Bus, stop_event: threading.Event):
    """
    Arka planda sinyal üreten ve sanal CAN hattına basan iş parçacığı.
    """
    t_start = time.time()
    counter = 0
    odometer = 12450.0
    loop_delay = 0.05

    while not stop_event.is_set():
        t = time.time() - t_start

        # Dinamik araç değerleri
        rpm = 2500 + 1600 * math.sin(t * 0.8)
        throttle = max(0.0, 50 + 45 * math.sin(t * 0.8))
        temp = 85.0 + 5.0 * math.sin(t * 0.1)

        speed = max(0.0, 70.0 + 50.0 * math.sin(t * 0.5))
        brake = True if math.sin(t * 0.5) < -0.6 else False
        gear = 3 if speed > 10 else 0
        odometer += (speed / 3600.0) * loop_delay

        voltage = 13.8 + 0.5 * math.sin(t * 0.3)
        current = 12.0 + 8.0 * math.cos(t * 0.4)
        soc = int(88 + 4 * math.sin(t * 0.05))

        # ID 0x100 - ENGINE_DATA (50ms)
        data_engine = pack_engine_data(rpm, throttle, temp, counter)
        msg_engine = can.Message(arbitration_id=ID_ENGINE_DATA, data=data_engine, is_extended_id=False)
        bus.send(msg_engine)

        # ID 0x200 - VEHICLE_SPEED (100ms)
        if counter % 2 == 0:
            data_speed = pack_vehicle_speed(speed, brake, gear, odometer)
            msg_speed = can.Message(arbitration_id=ID_VEHICLE_SPEED, data=data_speed, is_extended_id=False)
            bus.send(msg_speed)

        # ID 0x300 - BATTERY_STATUS (200ms)
        if counter % 4 == 0:
            data_batt = pack_battery_status(voltage, current, soc)
            msg_batt = can.Message(arbitration_id=ID_BATTERY_STATUS, data=data_batt, is_extended_id=False)
            bus.send(msg_batt)

        counter = (counter + 1) % 16
        time.sleep(loop_delay)


def main():
    console.print(Panel.fit(
        "[bold green]🚗 CAN Bus Sanal Simülasyon Ortamı Başlatılıyor[/bold green]\n"
        "[dim]Bu modda donanıma ihtiyaç duymadan CAN paketleri üretilir ve canlı izlenir.[/dim]",
        border_style="cyan"
    ))

    # Ortak sanal bus oluşturulur (kendi mesajlarını alacak şekilde)
    bus = can.Bus(
        interface="virtual",
        channel=SIMULATION_CHANNEL,
        receive_own_messages=True
    )

    stop_event = threading.Event()
    sender_thread = threading.Thread(target=sender_worker, args=(bus, stop_event), daemon=True)
    sender_thread.start()

    rx_db = {}
    total_rx = 0
    start_time = time.time()

    try:
        with Live(console=console, refresh_per_second=10) as live:
            while True:
                msg = bus.recv(timeout=0.1)
                if msg is not None:
                    total_rx += 1
                    name, decoded = decode_message(msg.arbitration_id, msg.data)
                    can_id = msg.arbitration_id
                    
                    if can_id not in rx_db:
                        rx_db[can_id] = {
                            "name": name,
                            "data": msg.data,
                            "decoded": decoded,
                            "count": 1,
                            "timestamp": msg.timestamp or time.time()
                        }
                    else:
                        rx_db[can_id]["data"] = msg.data
                        rx_db[can_id]["decoded"] = decoded
                        rx_db[can_id]["count"] += 1
                        rx_db[can_id]["timestamp"] = msg.timestamp or time.time()

                live.update(build_dashboard_table(rx_db, total_rx, start_time, "Virtual Simulation"))

    except KeyboardInterrupt:
        console.print("\n[yellow]Simülasyon durduruluyor...[/yellow]")
    finally:
        stop_event.set()
        sender_thread.join(timeout=1.0)
        bus.shutdown()
        console.print(f"[bold green]Simülasyon başarıyla tamamlandı. Toplam işlenen CAN paketi:[/bold green] {total_rx}")


if __name__ == "__main__":
    main()
