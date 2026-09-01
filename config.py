"""
CAN Bus Konfigürasyon ve Tanım Modülü
Gerçek PCAN donanımı ve Sanal CAN (Virtual CAN) arayüzleri için ortak ayarları içerir.
"""

import sys
import os

# Windows konsollarında UTF-8 desteğini etkinleştir
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import can
from rich.console import Console

console = Console(legacy_windows=False)

# --- Varsayılan Ayarlar ---
DEFAULT_BITRATE = 500000          # 500 kbps (Otomotiv standart hız)
DEFAULT_PCAN_CHANNEL = "PCAN_USBBUS1"
DEFAULT_VIRTUAL_CHANNEL = "virtual_channel"

# --- CAN Mesaj ID Tanımları ---
CAN_MESSAGES = {
    0x100: {
        "name": "ENGINE_DATA",
        "description": "Motor verileri (RPM, Gaz Kelebeği, Sıcaklık)",
        "dlc": 8,
        "cycle_time_ms": 50,
    },
    0x200: {
        "name": "VEHICLE_SPEED",
        "description": "Araç Hız ve Vites Bilgisi",
        "dlc": 8,
        "cycle_time_ms": 100,
    },
    0x300: {
        "name": "BATTERY_STATUS",
        "description": "Akü / Batarya Voltaj, Akım ve Doluluk",
        "dlc": 8,
        "cycle_time_ms": 200,
    },
}

ID_ENGINE_DATA = 0x100
ID_VEHICLE_SPEED = 0x200
ID_BATTERY_STATUS = 0x300


def get_can_bus(interface: str = "pcan", channel: str = None, bitrate: int = DEFAULT_BITRATE, receive_own_messages: bool = True):
    """
    İstenilen arayüze göre CAN Bus nesnesi oluşturur.
    
    :param interface: 'pcan' veya 'virtual'
    :param channel: PCAN için 'PCAN_USBBUS1', sanal için kanal adı
    :param bitrate: Baudrate (örn: 500000)
    :param receive_own_messages: Sanal modda gönderilen mesajı kendi alıcısında da görebilmek için
    :return: can.Bus nesnesi
    """
    if interface == "virtual":
        ch = channel or DEFAULT_VIRTUAL_CHANNEL
        console.print(f"[bold cyan][Sanal Mod][/bold cyan] Sanal CAN arayüzü başlatılıyor: [yellow]{ch}[/yellow]")
        return can.Bus(
            interface="virtual",
            channel=ch,
            receive_own_messages=receive_own_messages
        )

    # PCAN Arayüzü
    ch = channel or DEFAULT_PCAN_CHANNEL
    try:
        console.print(f"[bold green][PCAN Modu][/bold green] PEAK PCAN donanımına bağlanılıyor: [yellow]{ch}[/yellow] @ [yellow]{bitrate} bps[/yellow]")
        bus = can.Bus(
            interface="pcan",
            channel=ch,
            bitrate=bitrate,
            receive_own_messages=receive_own_messages
        )
        console.print("[bold green]✓ PCAN Donanımı başarıyla bağlandı.[/bold green]")
        return bus
    except (can.CanInitializationError, can.CanOperationError, Exception) as e:
        console.print(f"[bold red]UYARI:[/bold red] PCAN donanımı başlatılamadı ({e}).")
        console.print("[yellow]Donanım takılı değilse veya GitHub/sanal test ortamındaysanız sanal moda geçebilirsiniz.[/yellow]")
        console.print("[cyan]--> Otomatik olarak 'virtual' moduna geçiliyor...[/cyan]\n")
        return can.Bus(
            interface="virtual",
            channel=DEFAULT_VIRTUAL_CHANNEL,
            receive_own_messages=receive_own_messages
        )
