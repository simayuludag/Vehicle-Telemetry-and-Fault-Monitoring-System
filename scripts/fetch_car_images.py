"""
J1939 CAN Bus Projesi - Otomatik İnternetten Araç Görseli İndirici
Bu script, filo veritabanındaki (fleet_data.py) tüm araçlar veya yeni eklenecek araçlar
için Wikipedia / Wikimedia Commons API üzerinden telifsiz, gerçek fotoğrafları
otomatik arar, indirir ve 'web/static/images/cars/' klasörüne kaydeder.
"""

import os
import re
import time
import urllib.request
import urllib.parse
import json
from typing import Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARS_IMG_DIR = os.path.join(BASE_DIR, "web", "static", "images", "cars")
os.makedirs(CARS_IMG_DIR, exist_ok=True)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,tr;q=0.8"
}


def fetch_car_image_from_wikipedia(query: str, vehicle_id: str, max_retries: int = 2) -> Optional[str]:
    """
    Wikipedia / Wikimedia API'sini kullanarak verilen marka/model için en iyi görseli çeker ve kaydeder.
    """
    for attempt in range(max_retries):
        try:
            search_term = query.strip()
            encoded_query = urllib.parse.quote(search_term)
            search_url = f"https://en.wikipedia.org/w/api.php?action=query&format=json&generator=search&gsrsearch={encoded_query}&gsrlimit=1&prop=pageimages&pithumbsize=1200"
            
            req = urllib.request.Request(search_url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            
            pages = data.get("query", {}).get("pages", {})
            if not pages:
                print(f"  [-] '{query}' için sayfa bulunamadı.", flush=True)
                return None
                
            page = next(iter(pages.values()))
            thumbnail = page.get("thumbnail", {}).get("source")
            
            if not thumbnail:
                print(f"  [-] '{query}' sayfasında görsel bulunamadı.", flush=True)
                return None

            ext = ".jpg"
            if ".png" in thumbnail.lower():
                ext = ".png"
                
            target_path = os.path.join(CARS_IMG_DIR, f"{vehicle_id}{ext}")
            
            img_req = urllib.request.Request(thumbnail, headers=HEADERS)
            with urllib.request.urlopen(img_req, timeout=15) as img_resp, open(target_path, "wb") as f:
                f.write(img_resp.read())
                
            rel_path = f"/static/images/cars/{vehicle_id}{ext}"
            print(f"  [+] Başarılı: {query} -> {rel_path}", flush=True)
            return rel_path

        except urllib.error.HTTPError as err:
            if err.code == 429:
                print(f"  [!] Hız limiti (429), 3 saniye bekleniyor...", flush=True)
                time.sleep(3.5)
            else:
                print(f"  [!] HTTP Hatası ({err.code}): {err}", flush=True)
                break
        except Exception as e:
            print(f"  [!] Hata ({query}): {e}", flush=True)
            break
            
    return None


def download_image_from_direct_url(image_url: str, vehicle_id: str) -> Optional[str]:
    """
    Doğrudan verilen bir web URL'sinden görseli indirir.
    """
    try:
        ext = os.path.splitext(urllib.parse.urlparse(image_url).path)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
            ext = ".jpg"
            
        target_path = os.path.join(CARS_IMG_DIR, f"{vehicle_id}{ext}")
        
        req = urllib.request.Request(image_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp, open(target_path, "wb") as f:
            f.write(resp.read())
            
        rel_path = f"/static/images/cars/{vehicle_id}{ext}"
        print(f"  [+] Doğrudan URL'den İndirildi: {vehicle_id} -> {rel_path}", flush=True)
        return rel_path
    except Exception as e:
        print(f"  [!] Doğrudan URL indirme hatası ({vehicle_id}): {e}", flush=True)
        return None


ALL_FLEET_VEHICLES = [
    # BMW
    {"id": "bmw-320i", "search": "BMW 3 Series G20"},
    {"id": "bmw-520d", "search": "BMW 5 Series G30"},
    {"id": "bmw-m4-competition", "search": "BMW M4 G82"},
    
    # Mercedes-Benz
    {"id": "mb-c200", "search": "Mercedes-Benz C-Class W206"},
    {"id": "mb-e300d", "search": "Mercedes-Benz E-Class W213"},
    {"id": "mb-g63-amg", "search": "Mercedes-Benz G-Class W463"},
    
    # Audi
    {"id": "audi-a3-sedan", "search": "Audi A3 8Y sedan"},
    {"id": "audi-a6-avant", "search": "Audi A6 C8"},
    {"id": "audi-rs6-avant", "search": "Audi RS 6 C8"},
    
    # Volkswagen
    {"id": "vw-golf-8", "search": "Volkswagen Golf Mk8"},
    {"id": "vw-passat-variant", "search": "Volkswagen Passat B8"},
    {"id": "vw-tiguan-rline", "search": "Volkswagen Tiguan"},
    
    # Toyota
    {"id": "toyota-corolla-hybrid", "search": "Toyota Corolla E210"},
    {"id": "toyota-rav4-hybrid", "search": "Toyota RAV4 XA50"},
    {"id": "toyota-yaris-cross", "search": "Toyota Yaris Cross"},
    
    # Tesla
    {"id": "tesla-model-3-perf", "search": "Tesla Model 3"},
    {"id": "tesla-model-y-longrange", "search": "Tesla Model Y"},
    {"id": "tesla-model-s-plaid", "search": "Tesla Model S"},
    
    # Ford
    {"id": "ford-focus-st", "search": "Ford Focus Mk4"},
    {"id": "ford-mustang-gt", "search": "Ford Mustang S550"},
    {"id": "ford-ranger-raptor", "search": "Ford Ranger T6"},
    
    # Renault
    {"id": "renault-clio-5", "search": "Renault Clio V"},
    {"id": "renault-megane-etech", "search": "Renault Mégane E-Tech Electric"},
    {"id": "renault-austral", "search": "Renault Austral"},
    
    # Hyundai
    {"id": "hyundai-i20-n", "search": "Hyundai i20"},
    {"id": "hyundai-tucson-hybrid", "search": "Hyundai Tucson NX4"},
    {"id": "hyundai-ioniq-5", "search": "Hyundai Ioniq 5"},
    
    # Fiat
    {"id": "fiat-egea-cross", "search": "Fiat Tipo 2015"},
    {"id": "fiat-500e", "search": "Fiat 500e 2020"},
    {"id": "fiat-doblo-combi", "search": "Fiat Doblò"},
    
    # Isuzu & Yerli
    {"id": "isuzu-npr-long", "search": "Isuzu Elf"},
    {"id": "togg-t10x", "search": "Togg T10X"}
]


def download_all_fleet_images():
    """Tüm filodaki 32 aracın görsellerini Wikipedia / Wikimedia üzerinden otomatik indirir"""
    print("=" * 65, flush=True)
    print("   SAE J1939 Filosu İnternetten Görsel İndirme İşlemi Başladı", flush=True)
    print(f"   Hedef Klasör: {CARS_IMG_DIR}", flush=True)
    print(f"   Toplam Araç : {len(ALL_FLEET_VEHICLES)} Model", flush=True)
    print("=" * 65, flush=True)
    
    success_count = 0
    fail_count = 0
    
    for idx, v in enumerate(ALL_FLEET_VEHICLES, 1):
        print(f"\n[{idx}/{len(ALL_FLEET_VEHICLES)}] İndiriliyor: {v['id']} ({v['search']})...", flush=True)
        res = fetch_car_image_from_wikipedia(v["search"], v["id"])
        if res:
            success_count += 1
        else:
            fail_count += 1
        time.sleep(1.2)  # Rate-limit koruması
            
    print("\n" + "=" * 65, flush=True)
    print(f"   İndirme Tamamlandı! Başarılı: {success_count} | Başarısız: {fail_count}", flush=True)
    print("=" * 65, flush=True)


if __name__ == "__main__":
    download_all_fleet_images()
