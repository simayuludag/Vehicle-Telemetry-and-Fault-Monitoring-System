"""
CAN Sinyal Gönderici (CAN Signal Sender)
PCAN veya Sanal CAN (Virtual CAN) üzerinden dinamik araç sinyalleri üretip basar.
"""

import sys
import os
import time
import math
import struct
import argparse

# Windows konsollarında UTF-8 desteğini etkinleştir
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console

console = Console(legacy_windows=False)

import can
from config import (
    get_can_bus,
    ID_ENGINE_DATA,
    ID_VEHICLE_SPEED,
    ID_BATTERY_STATUS,
    DEFAULT_BITRATE,
    DEFAULT_PCAN_CHANNEL,
    DEFAULT_VIRTUAL_CHANNEL,
)

console = Console()


def pack_engine_data(rpm: int, throttle_pct: float, temp_c: float, counter: int) -> bytearray:
    """
    ID 0x100: Motor Verisi Paketleme
    - Byte 0-1: RPM (uint16, big-endian)
    - Byte 2: Gaz Kelebeği Açıklığı (% uint8)
    - Byte 3: Motor Sıcaklığı (int8, offset +40 -> uint8)
    - Byte 4: Canlılık Sayacı (0-15, uint8)
    - Byte 5-7: Rezerve (0x00)
    """
    data = bytearray(8)
    # RPM (0 - 8000)
    rpm_val = max(0, min(8000, int(rpm)))
    data[0] = (rpm_val >> 8) & 0xFF
    data[1] = rpm_val & 0xFF

    # Throttle (0 - 100%)
    data[2] = max(0, min(100, int(throttle_pct))) & 0xFF

    # Sıcaklık (-40 .. 150 °C -> raw = temp + 40)
    temp_raw = max(0, min(255, int(temp_c + 40)))
    data[3] = temp_raw & 0xFF

    # Canlılık sayacı (Rolling Counter: 0-15)
    data[4] = counter & 0x0F

    data[5] = 0x00
    data[6] = 0x00
    data[7] = 0x00
    return data


def pack_vehicle_speed(speed_kmh: float, brake_pressed: bool, gear: int, odometer_km: float) -> bytearray:
    """
    ID 0x200: Araç Hız ve Sürüş Verisi
    - Byte 0-1: Araç Hızı (km/h * 10, uint16, big-endian)
    - Byte 2: Fren Durumu (0: Bırakıldı, 1: Basılı)
    - Byte 3: Vites (0: P, 1: R, 2: N, 3: D)
    - Byte 4-7: Kilometre Sayacı (Odometer * 10, uint32, big-endian)
    """
    data = bytearray(8)
    speed_raw = max(0, min(65535, int(speed_kmh * 10)))
    data[0] = (speed_raw >> 8) & 0xFF
    data[1] = speed_raw & 0xFF

    data[2] = 1 if brake_pressed else 0
    data[3] = max(0, min(3, int(gear)))

    odo_raw = max(0, int(odometer_km * 10))
    odo_bytes = struct.pack(">I", odo_raw)
    data[4:8] = odo_bytes
    return data


def pack_battery_status(voltage_v: float, current_a: float, soc_pct: int) -> bytearray:
    """
    ID 0x300: Akü / Batarya Durumu
    - Byte 0-1: Voltaj (V * 100, uint16, big-endian -> örn: 1385 = 13.85V)
    - Byte 2-3: Akım (A * 10, int16, big-endian -> örn: +15.5A = 155)
    - Byte 4: Şarj Durumu (% SOC 0-100)
    - Byte 5-7: Rezerve (0xAA)
    """
    data = bytearray(8)
    volt_raw = max(0, min(65535, int(voltage_v * 100)))
    data[0] = (volt_raw >> 8) & 0xFF
    data[1] = volt_raw & 0xFF

    curr_raw = max(-32768, min(32767, int(current_a * 10)))
    curr_bytes = struct.pack(">h", curr_raw)
    data[2:4] = curr_bytes

    data[4] = max(0, min(100, int(soc_pct)))
    data[5] = 0xAA
    data[6] = 0xAA
    data[7] = 0xAA
    return data


def run_sender(interface="pcan", channel=None, bitrate=DEFAULT_BITRATE, count=0, loop_delay=0.05):
    """
    Sinyalleri CAN hattına periyodik olarak basan ana döngü.
    """
    bus = get_can_bus(interface=interface, channel=channel, bitrate=bitrate)
    
    console.print("\n[bold green]=== CAN Sinyal Gönderimi Başlatıldı ===[/bold green]")
    console.print("[dim]Durdurmak için Ctrl+C tuşlarına basabilirsiniz.[/dim]\n")

    t_start = time.time()
    counter = 0
    odometer = 12450.0  # Başlangıç kilometresi

    try:
        msg_count = 0
        while True:
            t = time.time() - t_start
            
            # 1) Simüle Edilmiş Dinamik Araç Sinyalleri
            # RPM: Sinüs dalgası ile 900 - 4500 RPM arasında salınsın
            rpm = 2500 + 1600 * math.sin(t * 0.8)
            throttle = max(0.0, 50 + 45 * math.sin(t * 0.8))
            temp = 85.0 + 5.0 * math.sin(t * 0.1)

            # Hız: RPM ile orantılı 0 - 140 km/h
            speed = max(0.0, 70.0 + 50.0 * math.sin(t * 0.5))
            brake = True if math.sin(t * 0.5) < -0.6 else False
            gear = 3 if speed > 10 else 0  # 3: Drive, 0: Park
            odometer += (speed / 3600.0) * loop_delay

            # Batarya: 13.5V - 14.4V arası
            voltage = 13.8 + 0.5 * math.sin(t * 0.3)
            current = 12.0 + 8.0 * math.cos(t * 0.4)
            soc = int(88 + 4 * math.sin(t * 0.05))

            # 2) CAN Mesajlarını Paketle ve Gönder
            # ID 0x100 - ENGINE_DATA (Her döngüde / 50ms)
            data_engine = pack_engine_data(rpm, throttle, temp, counter)
            msg_engine = can.Message(arbitration_id=ID_ENGINE_DATA, data=data_engine, is_extended_id=False)
            bus.send(msg_engine)
            msg_count += 1

            # ID 0x200 - VEHICLE_SPEED (Her 2 döngüde bir / ~100ms)
            if counter % 2 == 0:
                data_speed = pack_vehicle_speed(speed, brake, gear, odometer)
                msg_speed = can.Message(arbitration_id=ID_VEHICLE_SPEED, data=data_speed, is_extended_id=False)
                bus.send(msg_speed)
                msg_count += 1

            # ID 0x300 - BATTERY_STATUS (Her 4 döngüde bir / ~200ms)
            if counter % 4 == 0:
                data_batt = pack_battery_status(voltage, current, soc)
                msg_batt = can.Message(arbitration_id=ID_BATTERY_STATUS, data=data_batt, is_extended_id=False)
                bus.send(msg_batt)
                msg_count += 1

            # Konsola her 10 adımda bir özet bas
            if counter % 10 == 0:
                sys.stdout.write(
                    f"\r[GÖNDERİLİYOR] RPM: {rpm:4.0f} rpm | Hız: {speed:5.1f} km/h | Sıcaklık: {temp:4.1f}°C | Voltaj: {voltage:4.2f}V | Toplam Mesaj: {msg_count}"
                )
                sys.stdout.flush()

            counter = (counter + 1) % 16
            
            if count > 0 and msg_count >= count:
                break

            time.sleep(loop_delay)

    except KeyboardInterrupt:
        console.print("\n[yellow]Gönderim kullanıcı tarafından durduruldu.[/yellow]")
    finally:
        bus.shutdown()
        console.print(f"[bold green]CAN Bus bağlantısı kapatıldı. Toplam iletilen mesaj:[/bold green] {msg_count}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CAN Bus Sinyal Gönderici (PCAN & Virtual)")
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
        "--count",
        type=int,
        default=0,
        help="Gönderilecek mesaj sayısı (0 = sürekli)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.05,
        help="Döngü bekleme süresi saniye cinsinden (Varsayılan: 0.05s / 50ms)"
    )

    args = parser.parse_args()
    run_sender(
        interface=args.interface,
        channel=args.channel,
        bitrate=args.bitrate,
        count=args.count,
        loop_delay=args.delay
    )
