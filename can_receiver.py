"""
CAN Sinyal Alıcı ve Canlı Monitör (CAN Signal Receiver & Monitor)
PCAN veya Sanal CAN hattını dinler, sinyalleri çözümler ve canlı dashboard tablosunda gösterir.
"""

import sys
import os
import time
import struct
import argparse
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
    get_can_bus,
    CAN_MESSAGES,
    ID_ENGINE_DATA,
    ID_VEHICLE_SPEED,
    ID_BATTERY_STATUS,
    DEFAULT_BITRATE,
)

console = Console(legacy_windows=False)


def decode_engine_data(data: bytearray) -> dict:
    """
    ID 0x100: Motor Verilerini Çözümler
    """
    if len(data) < 5:
        return {"error": "Eksik veri boyutu"}
    
    rpm = (data[0] << 8) | data[1]
    throttle = data[2]
    temp = data[3] - 40
    counter = data[4] & 0x0F
    
    return {
        "RPM": f"{rpm} rpm",
        "Gaz": f"{throttle}%",
        "Sıcaklık": f"{temp}°C",
        "Sayaç": f"{counter}",
    }


def decode_vehicle_speed(data: bytearray) -> dict:
    """
    ID 0x200: Hız ve Sürüş Verilerini Çözümler
    """
    if len(data) < 8:
        return {"error": "Eksik veri boyutu"}
    
    speed_raw = (data[0] << 8) | data[1]
    speed_kmh = speed_raw / 10.0
    brake = "BASILI" if data[2] == 1 else "Bırakıldı"
    
    gears = {0: "P (Park)", 1: "R (Geri)", 2: "N (Boş)", 3: "D (Sürüş)"}
    gear_str = gears.get(data[3], f"Bilinmiyor({data[3]})")
    
    odo_raw = struct.unpack(">I", data[4:8])[0]
    odometer_km = odo_raw / 10.0
    
    return {
        "Hız": f"{speed_kmh:.1f} km/h",
        "Fren": brake,
        "Vites": gear_str,
        "KM": f"{odometer_km:.1f} km",
    }


def decode_battery_status(data: bytearray) -> dict:
    """
    ID 0x300: Batarya/Akü Durumunu Çözümler
    """
    if len(data) < 5:
        return {"error": "Eksik veri boyutu"}
    
    volt_raw = (data[0] << 8) | data[1]
    voltage_v = volt_raw / 100.0
    
    curr_raw = struct.unpack(">h", data[2:4])[0]
    current_a = curr_raw / 10.0
    
    soc = data[4]
    
    return {
        "Voltaj": f"{voltage_v:.2f} V",
        "Akım": f"{current_a:+.1f} A",
        "SOC (Doluluk)": f"%{soc}",
    }


def decode_message(can_id: int, data: bytearray) -> (str, str):
    """
    CAN ID'ye göre mesajı decode eder ve okunabilir format döndürür.
    """
    if can_id == ID_ENGINE_DATA:
        res = decode_engine_data(data)
        decoded_str = f"[bold cyan]RPM:[/bold cyan] {res['RPM']} | [bold cyan]Gaz:[/bold cyan] {res['Gaz']} | [bold cyan]Sıcaklık:[/bold cyan] {res['Sıcaklık']} | [dim]Sayaç:[/dim] {res['Sayaç']}"
        return "ENGINE_DATA", decoded_str
    elif can_id == ID_VEHICLE_SPEED:
        res = decode_vehicle_speed(data)
        brake_style = "[bold red]BASILI[/bold red]" if "BASILI" in res['Fren'] else "[green]Bırakıldı[/green]"
        decoded_str = f"[bold green]Hız:[/bold green] {res['Hız']} | [bold yellow]Vites:[/bold yellow] {res['Vites']} | Fren: {brake_style} | KM: {res['KM']}"
        return "VEHICLE_SPEED", decoded_str
    elif can_id == ID_BATTERY_STATUS:
        res = decode_battery_status(data)
        decoded_str = f"[bold magenta]Voltaj:[/bold magenta] {res['Voltaj']} | [bold magenta]Akım:[/bold magenta] {res['Akım']} | [bold cyan]SOC:[/bold cyan] {res['SOC (Doluluk)']}"
        return "BATTERY_STATUS", decoded_str
    else:
        name = CAN_MESSAGES.get(can_id, {}).get("name", "UNKNOWN_MSG")
        raw_hex = " ".join(f"{b:02X}" for b in data)
        return name, f"[dim]Ham Veri: {raw_hex}[/dim]"


def build_dashboard_table(rx_db: dict, total_rx: int, start_time: float, interface_name: str) -> Table:
    """
    Gelen CAN mesajlarını şık bir tablo olarak oluşturur.
    """
    table = Table(
        title=f"🚗 [bold cyan]CAN Bus Canlı Sinyal Monitörü[/bold cyan] ({interface_name}) | Toplam Paket: [bold green]{total_rx}[/bold green]",
        show_header=True,
        header_style="bold magenta",
        expand=True,
        border_style="blue",
    )
    table.add_column("CAN ID (Hex)", style="bold yellow", width=12)
    table.add_column("Mesaj Adı", style="bold white", width=16)
    table.add_column("DLC", justify="center", width=5)
    table.add_column("Ham Veri (HEX)", style="dim", width=24)
    table.add_column("Ayrıştırılmış Sinyaller (Decoded Data)", style="white")
    table.add_column("Adet", justify="right", style="cyan", width=8)
    table.add_column("Son Zaman", justify="right", style="dim", width=12)

    for can_id in sorted(rx_db.keys()):
        item = rx_db[can_id]
        hex_data_str = " ".join(f"{b:02X}" for b in item["data"])
        time_str = datetime.fromtimestamp(item["timestamp"]).strftime("%H:%M:%S.%f")[:-3]
        
        table.add_row(
            f"0x{can_id:03X}",
            item["name"],
            str(len(item["data"])),
            hex_data_str,
            item["decoded"],
            str(item["count"]),
            time_str
        )

    return table


def run_receiver(interface="pcan", channel=None, bitrate=DEFAULT_BITRATE, trace_mode=False):
    """
    CAN hattını dinleyen ana fonksiyon.
    """
    bus = get_can_bus(interface=interface, channel=channel, bitrate=bitrate)
    
    console.print("\n[bold green]=== CAN Dinleme Başlatıldı ===[/bold green]")
    console.print("[dim]Durdurmak için Ctrl+C tuşlarına basabilirsiniz.[/dim]\n")

    rx_db = {}
    total_rx = 0
    start_time = time.time()
    interface_label = "PCAN-USB" if interface == "pcan" else "Virtual CAN"

    try:
        if trace_mode:
            # İzleme (Trace) Modu: Her paketi alt alta satır satır basar
            console.print("[bold yellow]Trace Modu Aktif:[/bold yellow]")
            for msg in bus:
                total_rx += 1
                name, decoded = decode_message(msg.arbitration_id, msg.data)
                raw_hex = " ".join(f"{b:02X}" for b in msg.data)
                timestamp = datetime.fromtimestamp(msg.timestamp if msg.timestamp else time.time()).strftime("%H:%M:%S.%f")[:-3]
                console.print(
                    f"[{timestamp}] ID: [bold yellow]0x{msg.arbitration_id:03X}[/bold yellow] ({name:<14}) DLC: {msg.dlc} | "
                    f"DATA: [dim]{raw_hex:<23}[/dim] | {decoded}"
                )
        else:
            # Canlı Dashboard Modu: Tabloyu anlık günceller
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

                    # Tabloyu güncelle
                    live.update(build_dashboard_table(rx_db, total_rx, start_time, interface_label))

    except KeyboardInterrupt:
        console.print("\n[yellow]Dinleme durduruldu.[/yellow]")
    finally:
        bus.shutdown()
        console.print(f"[bold green]Toplam yakalanan paket:[/bold green] {total_rx}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CAN Bus Sinyal Alıcı ve Monitör (PCAN & Virtual)")
    parser.add_argument(
        "-i", "--interface",
        choices=["pcan", "virtual"],
        default="pcan",
        help="CAN arayüzü: 'pcan' (varsayılan) veya 'virtual' (sanal mod)"
    )
    parser.add_argument(
        "-c", "--channel",
        default=None,
        help="Kanal adı (PCAN için örn: PCAN_USBBUS1, Sanal için: virtual_channel)"
    )
    parser.add_argument(
        "-b", "--bitrate",
        type=int,
        default=DEFAULT_BITRATE,
        help=f"Baudrate (Varsayılan: {DEFAULT_BITRATE})"
    )
    parser.add_argument(
        "-t", "--trace",
        action="store_true",
        help="Canlı tablo yerine satır satır trace log modunda gösterir"
    )

    args = parser.parse_args()
    run_receiver(
        interface=args.interface,
        channel=args.channel,
        bitrate=args.bitrate,
        trace_mode=args.trace
    )
