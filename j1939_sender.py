"""
SAE J1939 Terminal Signal Transmitter (CLI Environment 1)
Interactive command-line tool to send J1939 CCVS speed signals to vehicles.
Uses Python standard library (urllib) - zero external dependencies required!
"""

import sys
import time
import json
import urllib.request
import urllib.error
from j1939.fleet_data import get_all_vehicles
from j1939.protocol import J1939Codec, PGN_CCVS


def print_fleet_menu(vehicles):
    print("\n" + "=" * 75)
    print(" [*] SAE J1939 SINYAL GONDERICI (TERMINAL KONTROL PANELI)")
    print("=" * 75)
    print(f" {'#':<3} | {'Marka':<14} | {'Model':<24} | {'SA (Hex)':<8} | {'Maks Hiz':<8}")
    print("-" * 75)
    for idx, v in enumerate(vehicles, 1):
        sa_hex = f"0x{v['source_address']:02X}"
        print(f" {idx:<3} | {v['brand_name']:<14} | {v['model'][:24]:<24} | {sa_hex:<8} | {v['max_speed']} km/h")
    print("=" * 75)


def http_post(url: str, payload: dict) -> tuple:
    """Python yerleşik urllib ile HTTP POST isteği gönderir"""
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=3) as response:
            res_body = response.read().decode("utf-8")
            return True, json.loads(res_body) if res_body else {}
    except urllib.error.URLError as e:
        return False, f"Sunucu baglanti hatasi: {e.reason}"
    except Exception as e:
        return False, str(e)


def send_speed_via_api(vehicle_id: str, speed_kmh: float, base_url: str = "http://localhost:8000"):
    url = f"{base_url}/api/vehicle/{vehicle_id}/speed"
    return http_post(url, {"speed": speed_kmh, "mode": "manual"})


def main():
    vehicles = get_all_vehicles()
    base_url = "http://localhost:8000"

    print("\n[*] J1939 Sinyal Gönderici CLI Baslatiliyor...")
    print(f"[*] Hedef Telemetri Sunucusu: {base_url}")

    while True:
        print_fleet_menu(vehicles)
        print("\nKomutlar:")
        print(" [1-30]  : Arac Sec ve Hiz Ver")
        print(" [all]   : Tum Filoya Ortak Hiz Ver")
        print(" [stop]  : Acil Durdur (All Stop)")
        print(" [q]     : Cikis\n")

        try:
            choice = input("Seciminiz > ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nCikis yapiliyor...")
            break

        if choice in ['q', 'exit', 'quit']:
            print("Cikis yapiliyor...")
            break

        if choice == 'stop':
            success, res = http_post(f"{base_url}/api/fleet/emergency-stop", {})
            if success:
                print("\n[!] Tum araclar acil durduruldu (0 km/h)!")
            else:
                print(f"[!] Hata: {res}")
            continue

        if choice == 'all':
            try:
                spd_in = input("Tum filo icin hedef hiz (km/h) > ").strip()
                spd = float(spd_in)
                success, res = http_post(f"{base_url}/api/fleet/speed", {"speed": spd})
                if success:
                    print(f"\n[+] Tum filoya {spd} km/h hizi gonderildi!")
                else:
                    print(f"[!] Hata: {res}")
            except ValueError:
                print("[!] Gecersiz sayi!")
            continue

        try:
            v_idx = int(choice) - 1
            if 0 <= v_idx < len(vehicles):
                selected = vehicles[v_idx]
                print(f"\nSecilen Arac: {selected['brand_name']} {selected['model']} (SA: 0x{selected['source_address']:02X})")
                spd_in = input(f"Verilecek Hiz (0 - {selected['max_speed']} km/h) > ").strip()
                spd = float(spd_in)

                # CAN Frame olustur ve goster
                frame = J1939Codec.encode_speed_frame(speed_kmh=spd, source_address=selected["source_address"])
                print(f"\n[*] Uretilen J1939 CAN ID: {frame.can_id_hex} | PGN: {frame.pgn_hex} | Data: {frame.data_hex}")

                success, result = send_speed_via_api(selected["id"], spd, base_url)
                if success:
                    print(f"[v] Basarili! {selected['model']} hizi {spd} km/h olarak guncellendi ve CAN hattina basildi.")
                else:
                    print(f"[!] Sunucuya iletilemedi: {result}")
                    print("    (Sunucunun calistigindan emin olun: python server.py)")
            else:
                print("[!] Gecersiz arac numarasi!")
        except ValueError:
            print("[!] Lutfen gecerli bir numara veya komut girin.")

        time.sleep(0.5)


if __name__ == "__main__":
    main()
