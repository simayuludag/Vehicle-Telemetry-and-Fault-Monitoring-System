"""
SAE J1939 Terminal Signal Transmitter (CLI Environment 1)
Interactive command-line tool to send J1939 CCVS speed signals to vehicles.
"""

import sys
import time
import requests
from j1939.fleet_data import get_all_vehicles
from j1939.protocol import J1939Codec, PGN_CCVS


def print_fleet_menu(vehicles):
    print("\n" + "=" * 75)
    print(" 🚗 SAE J1939 SINYAL GONDERICI (TERMINAL KONTROL PANELI)")
    print("=" * 75)
    print(f" {'#':<3} | {'Marka':<14} | {'Model':<24} | {'SA (Hex)':<8} | {'Maks Hız':<8}")
    print("-" * 75)
    for idx, v in enumerate(vehicles, 1):
        sa_hex = f"0x{v['source_address']:02X}"
        print(f" {idx:<3} | {v['brand_name']:<14} | {v['model'][:24]:<24} | {sa_hex:<8} | {v['max_speed']} km/h")
    print("=" * 75)


def send_speed_via_api(vehicle_id: str, speed_kmh: float, base_url: str = "http://localhost:8000"):
    try:
        url = f"{base_url}/api/vehicle/{vehicle_id}/speed"
        res = requests.post(url, json={"speed": speed_kmh, "mode": "manual"}, timeout=2)
        if res.status_code == 200:
            return True, res.json()
        return False, res.text
    except Exception as e:
        return False, str(e)


def main():
    vehicles = get_all_vehicles()
    base_url = "http://localhost:8000"

    print("\n[*] J1939 Sinyal Gönderici CLI Başlatılıyor...")
    print(f"[*] Hedef Telemetri Sunucusu: {base_url}")

    while True:
        print_fleet_menu(vehicles)
        print("\nKomutlar:")
        print(" [1-30]  : Araç Seç ve Hız Ver")
        print(" [all]   : Tüm Filoya Ortak Hız Ver")
        print(" [stop]  : Acil Durdur (All Stop)")
        print(" [q]     : Çıkış\n")

        choice = input("Seçiminiz > ").strip().lower()

        if choice in ['q', 'exit', 'quit']:
            print("Çıkış yapılıyor...")
            break

        if choice == 'stop':
            try:
                requests.post(f"{base_url}/api/fleet/emergency-stop", timeout=2)
                print("\n[!] Tüm araçlar acil durduruldu (0 km/h)!")
            except Exception as e:
                print(f"[!] Hata: {e}")
            continue

        if choice == 'all':
            spd_in = input("Tüm filo için hedef hız (km/h) > ").strip()
            try:
                spd = float(spd_in)
                requests.post(f"{base_url}/api/fleet/speed", json={"speed": spd}, timeout=2)
                print(f"\n[+] Tüm filoya {spd} km/h hızı gönderildi!")
            except ValueError:
                print("[!] Geçersiz sayı!")
            except Exception as e:
                print(f"[!] Hata: {e}")
            continue

        try:
            v_idx = int(choice) - 1
            if 0 <= v_idx < len(vehicles):
                selected = vehicles[v_idx]
                print(f"\nSeçilen Araç: {selected['brand_name']} {selected['model']} (SA: 0x{selected['source_address']:02X})")
                spd_in = input(f"Verilecek Hız (0 - {selected['max_speed']} km/h) > ").strip()
                spd = float(spd_in)

                # CAN Frame oluştur ve göster
                frame = J1939Codec.encode_speed_frame(speed_kmh=spd, source_address=selected["source_address"])
                print(f"\n[*] Üretilen J1939 CAN ID: {frame.can_id_hex} | PGN: {frame.pgn_hex} | Data: {frame.data_hex}")

                success, result = send_speed_via_api(selected["id"], spd, base_url)
                if success:
                    print(f"[✓] Başarılı! {selected['model']} hızı {spd} km/h olarak güncellendi ve CAN hattına basıldı.")
                else:
                    print(f"[!] Sunucuya iletilemedi: {result}")
                    print("    (Sunucunun çalıştığından emin olun: python server.py)")
            else:
                print("[!] Geçersiz araç numarası!")
        except ValueError:
            print("[!] Lütfen geçerli bir numara veya komut girin.")

        time.sleep(1)


if __name__ == "__main__":
    main()
