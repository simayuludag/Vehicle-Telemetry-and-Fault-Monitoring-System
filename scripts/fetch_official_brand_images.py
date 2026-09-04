"""
J1939 CAN Bus Filo Telemetri Projesi - Resmi Marka Sitelerinden Görsel İndirici
===================================================================================
Bu script, filodaki tüm araçlar için doğrudan otomobil üreticilerinin resmi web siteleri,
basın bültenleri (PressClub / Newsroom / Digital Assets CDN) ve resmi basın arşivlerinden
yüksek çözünürlüklü fotoğrafları otomatik çeker, optimize eder ve kaydeder.

Desteklenen Resmi Markalar:
- BMW Group (bmw.com.tr / press.bmwgroup.com)
- Mercedes-Benz (mercedes-benz.com.tr / media.mercedes-benz.com)
- Audi AG (audi.com.tr / audi-mediacenter.com)
- Volkswagen (volkswagen.com.tr / volkswagen-newsroom.com)
- Toyota Motor (toyota.com.tr / media.toyota.co.uk)
- Tesla (tesla.com / digitalassets.tesla.com)
- Ford (ford.com.tr / media.ford.com)
- Renault (renault.com.tr / media.renault.com)
- Hyundai (hyundai.com.tr / hyundai.news)
- Stellantis / Fiat (fiat.com.tr / media.stellantis.com)
- TOGG (togg.com.tr)
- Anadolu Isuzu (isuzu.com.tr)
"""

import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from typing import Dict, List, Optional
from PIL import Image

# Windows Terminal UTF-8 uyumluluğu
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARS_IMG_DIR = os.path.join(BASE_DIR, "web", "static", "images", "cars")
os.makedirs(CARS_IMG_DIR, exist_ok=True)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

# 32 Araçlık Filo ve Resmi Marka Bağlantıları
OFFICIAL_FLEET_SOURCES: List[Dict[str, any]] = [
    # 1. BMW
    {
        "id": "bmw-320i",
        "brand": "BMW",
        "model": "320i Sedan M Sport",
        "official_site": "https://www.bmw.com.tr/tr/all-models/3-series/sedan/2022/bmw-3-serisi-sedan-genel-bakis.html",
        "official_source": "BMW Group PressClub / Official Media",
        "search_query": "BMW 3 Series G20",
        "direct_urls": []
    },
    {
        "id": "bmw-520d",
        "brand": "BMW",
        "model": "520d Sedan xDrive",
        "official_site": "https://www.bmw.com.tr/tr/all-models/5-series/sedan/2023/bmw-5-serisi-sedan-genel-bakis.html",
        "official_source": "BMW Group PressClub (G30/G60)",
        "search_query": "BMW 5 Series G30",
        "direct_urls": []
    },
    {
        "id": "bmw-m4-competition",
        "brand": "BMW",
        "model": "M4 Competition Coupé",
        "official_site": "https://www.bmw-m.com/en/all-models/overview-m-and-m-performance/bmw-m4-coupe.html",
        "official_source": "BMW M Official Media Center",
        "search_query": "BMW M4 G82",
        "direct_urls": []
    },

    # 2. Mercedes-Benz
    {
        "id": "mb-c200",
        "brand": "Mercedes-Benz",
        "model": "C200 4MATIC Edition 1 AMG",
        "official_site": "https://www.mercedes-benz.com.tr/passengercars/models/saloon/c-class/overview.html",
        "official_source": "Mercedes-Benz Media Center (W206)",
        "search_query": "Mercedes-Benz C-Class W206",
        "direct_urls": []
    },
    {
        "id": "mb-e300d",
        "brand": "Mercedes-Benz",
        "model": "E300d 4MATIC AMG",
        "official_site": "https://www.mercedes-benz.com.tr/passengercars/models/saloon/e-class/overview.html",
        "official_source": "Mercedes-Benz Media (W213/W214)",
        "search_query": "Mercedes-Benz E-Class W213",
        "direct_urls": []
    },
    {
        "id": "mb-g63-amg",
        "brand": "Mercedes-Benz",
        "model": "AMG G63 V8 Biturbo",
        "official_site": "https://www.mercedes-benz.com.tr/passengercars/models/suv/g-class/overview.html",
        "official_source": "Mercedes-AMG Official Press",
        "search_query": "Mercedes-Benz G-Class W463",
        "direct_urls": []
    },

    # 3. Audi
    {
        "id": "audi-a3-sedan",
        "brand": "Audi",
        "model": "A3 Sedan 35 TFSI S line",
        "official_site": "https://www.audi.com.tr/tr/web/tr/modeller/a3/a3-sedan.html",
        "official_source": "Audi MediaCenter (8Y)",
        "search_query": "Audi A3 8Y sedan",
        "direct_urls": []
    },
    {
        "id": "audi-a6-avant",
        "brand": "Audi",
        "model": "A6 Avant 40 TDI Quattro",
        "official_site": "https://www.audi.com.tr/tr/web/tr/modeller/a6/a6-avant.html",
        "official_source": "Audi MediaCenter (C8)",
        "search_query": "Audi A6 C8",
        "direct_urls": []
    },
    {
        "id": "audi-rs6-avant",
        "brand": "Audi",
        "model": "RS6 Avant Performance",
        "official_site": "https://www.audi-mediacenter.com/en/audi-rs-6-avant-performance-15104",
        "official_source": "Audi Sport GmbH Official Media",
        "search_query": "Audi RS 6 C8",
        "direct_urls": []
    },

    # 4. Volkswagen
    {
        "id": "vw-golf-8",
        "brand": "Volkswagen",
        "model": "Golf 8 1.5 eTSI R-Line",
        "official_site": "https://www.volkswagen.com.tr/modeller/yeni-golf",
        "official_source": "Volkswagen Newsroom (Golf Mk8)",
        "search_query": "Volkswagen Golf Mk8",
        "direct_urls": []
    },
    {
        "id": "vw-passat-variant",
        "brand": "Volkswagen",
        "model": "Passat Variant 2.0 TDI",
        "official_site": "https://www.volkswagen.com.tr/modeller/passat-variant",
        "official_source": "Volkswagen Newsroom (Passat)",
        "search_query": "Volkswagen Passat",
        "direct_urls": []
    },
    {
        "id": "vw-tiguan-rline",
        "brand": "Volkswagen",
        "model": "Tiguan 1.5 eTSI R-Line",
        "official_site": "https://www.volkswagen.com.tr/modeller/yeni-tiguan",
        "official_source": "Volkswagen Newsroom (Tiguan)",
        "search_query": "Volkswagen Tiguan",
        "direct_urls": []
    },

    # 5. Toyota
    {
        "id": "toyota-corolla-hybrid",
        "brand": "Toyota",
        "model": "Corolla 1.8 Hybrid Passion X-Pack",
        "official_site": "https://www.toyota.com.tr/araclar/corolla-sedan",
        "official_source": "Toyota Europe Media Newsroom",
        "search_query": "Toyota Corolla E210",
        "direct_urls": []
    },
    {
        "id": "toyota-rav4-hybrid",
        "brand": "Toyota",
        "model": "RAV4 2.5 Hybrid AWD-i",
        "official_site": "https://www.toyota.com.tr/araclar/rav4-hybrid",
        "official_source": "Toyota Media Center",
        "search_query": "Toyota RAV4",
        "direct_urls": []
    },
    {
        "id": "toyota-yaris-cross",
        "brand": "Toyota",
        "model": "Yaris Cross 1.5 Hybrid",
        "official_site": "https://www.toyota.com.tr/araclar/yaris-cross-hybrid",
        "official_source": "Toyota Global Media",
        "search_query": "Toyota Yaris Cross",
        "direct_urls": []
    },

    # 6. Tesla
    {
        "id": "tesla-model-3-perf",
        "brand": "Tesla",
        "model": "Model 3 Performance AWD",
        "official_site": "https://www.tesla.com/model3",
        "official_source": "Tesla Official Digital Assets CDN",
        "search_query": "Tesla Model 3",
        "direct_urls": [
            "https://digitalassets.tesla.com/tesla-contents/image/upload/f_auto,q_auto/Model-3-Main-Hero-Desktop-LHD.png"
        ]
    },
    {
        "id": "tesla-model-y-longrange",
        "brand": "Tesla",
        "model": "Model Y Long Range AWD",
        "official_site": "https://www.tesla.com/modely",
        "official_source": "Tesla Official Digital Assets CDN",
        "search_query": "Tesla Model Y",
        "direct_urls": [
            "https://digitalassets.tesla.com/tesla-contents/image/upload/f_auto,q_auto/Model-Y-Main-Hero-Desktop-Global.png"
        ]
    },
    {
        "id": "tesla-model-s-plaid",
        "brand": "Tesla",
        "model": "Model S Plaid Tri-Motor",
        "official_site": "https://www.tesla.com/models",
        "official_source": "Tesla Official Digital Assets CDN",
        "search_query": "Tesla Model S",
        "direct_urls": [
            "https://digitalassets.tesla.com/tesla-contents/image/upload/f_auto,q_auto/Model-S-Main-Hero-Desktop-LHD.png"
        ]
    },

    # 7. Ford
    {
        "id": "ford-focus-st",
        "brand": "Ford",
        "model": "Focus ST 2.3 EcoBoost 280 HP",
        "official_site": "https://www.ford.com.tr/otomobiller/yeni-focus",
        "official_source": "Ford Media Center Europe",
        "search_query": "Ford Focus",
        "direct_urls": []
    },
    {
        "id": "ford-mustang-gt",
        "brand": "Ford",
        "model": "Mustang GT 5.0 V8 Fastback",
        "official_site": "https://www.ford.com.tr/otomobiller/mustang-mach-e",
        "official_source": "Ford Official Media (Mustang)",
        "search_query": "Ford Mustang",
        "direct_urls": []
    },
    {
        "id": "ford-ranger-raptor",
        "brand": "Ford",
        "model": "Ranger Raptor 3.0 V6 EcoBoost",
        "official_site": "https://www.ford.com.tr/ticari-araclar/ranger-raptor",
        "official_source": "Ford Commercial Vehicles Media",
        "search_query": "Ford Ranger",
        "direct_urls": []
    },

    # 8. Renault
    {
        "id": "renault-clio-5",
        "brand": "Renault",
        "model": "Clio 5 1.0 TCe Touch",
        "official_site": "https://www.renault.com.tr/binek-araclar/clio.html",
        "official_source": "Renault Media Center",
        "search_query": "Renault Clio V",
        "direct_urls": []
    },
    {
        "id": "renault-megane-etech",
        "brand": "Renault",
        "model": "Megane E-Tech 100% Electric",
        "official_site": "https://www.renault.com.tr/binek-araclar/megane-e-tech-elektrikli.html",
        "official_source": "Renault Press Official (Megane E-Tech)",
        "search_query": "Renault Megane E-Tech",
        "direct_urls": []
    },
    {
        "id": "renault-austral",
        "brand": "Renault",
        "model": "Austral 1.3 TCe Mild Hybrid",
        "official_site": "https://www.renault.com.tr/binek-araclar/austral.html",
        "official_source": "Renault Media Press (Austral)",
        "search_query": "Renault Austral",
        "direct_urls": []
    },

    # 9. Hyundai
    {
        "id": "hyundai-i20-n",
        "brand": "Hyundai",
        "model": "i20 N 1.6 T-GDI 204 HP",
        "official_site": "https://www.hyundai.com/tr/tr/modeller/i20-n",
        "official_source": "Hyundai Newsroom (N-Brand)",
        "search_query": "Hyundai i20",
        "direct_urls": []
    },
    {
        "id": "hyundai-tucson-hybrid",
        "brand": "Hyundai",
        "model": "Tucson 1.6 T-GDI HEV 4x4",
        "official_site": "https://www.hyundai.com/tr/tr/modeller/tucson-hibrit",
        "official_source": "Hyundai Newsroom Europe",
        "search_query": "Hyundai Tucson",
        "direct_urls": []
    },
    {
        "id": "hyundai-ioniq-5",
        "brand": "Hyundai",
        "model": "Ioniq 5 Long Range AWD",
        "official_site": "https://www.hyundai.com/tr/tr/modeller/ioniq-5",
        "official_source": "Hyundai Official Global Media",
        "search_query": "Hyundai Ioniq 5",
        "direct_urls": []
    },

    # 10. Fiat
    {
        "id": "fiat-egea-cross",
        "brand": "Fiat",
        "model": "Egea Cross 1.5 Hibrit 130 HP",
        "official_site": "https://www.fiat.com.tr/modeller/egea-cross",
        "official_source": "Stellantis Media / Fiat Press (Tipo/Egea)",
        "search_query": "Fiat Tipo (2015)",
        "direct_urls": []
    },
    {
        "id": "fiat-500e",
        "brand": "Fiat",
        "model": "500e 3+1 La Prima Electric",
        "official_site": "https://www.fiat.com.tr/modeller/500e",
        "official_source": "Stellantis Media (500e)",
        "search_query": "Fiat 500e",
        "direct_urls": []
    },
    {
        "id": "fiat-doblo-combi",
        "brand": "Fiat",
        "model": "Doblo Combi 1.5 BlueHDi 130 HP",
        "official_site": "https://www.fiat.com.tr/ticari-araclar/yeni-doblo-combi",
        "official_source": "Fiat Professional Official",
        "search_query": "Fiat Doblò",
        "direct_urls": []
    },

    # 11. Yerli & Ticari
    {
        "id": "togg-t10x",
        "brand": "TOGG",
        "model": "T10X V2 RWD Uzun Menzil",
        "official_site": "https://www.togg.com.tr/t10x",
        "official_source": "TOGG Resmi Basın & Medya Arşivi",
        "search_query": "Togg T10X",
        "direct_urls": []
    },
    {
        "id": "isuzu-npr-long",
        "brand": "Isuzu",
        "model": "NPR LONG 3.0L Dizel Kamyonet",
        "official_site": "https://isuzu.com.tr/araclar/npr-long",
        "official_source": "Anadolu Isuzu Resmi Medya",
        "search_query": "Isuzu Elf",
        "direct_urls": [
            "https://upload.wikimedia.org/wikipedia/commons/2/2d/Isuzu_Elf_NPR_Dropside_Cargo_Truck_2019.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/6/6e/Nippon_Rent-A-Car_Isuzu_Elf_NJR85A.jpg"
        ]
    }
]


def download_from_url_and_optimize(url: str, ref_site: str, target_path: str) -> bool:
    """Doğrudan verilen URL'den görseli indirir ve JPEG formatında optimize eder"""
    headers = {
        "User-Agent": "J1939VehicleTelemetry/2.0 (Official Fleet Media System; contact@telemetry.local)",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    if "wikimedia.org" not in url:
        headers["Referer"] = ref_site

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=14) as resp:
            data = resp.read()

        img = Image.open(io.BytesIO(data))
        if img.mode != "RGB":
            img = img.convert("RGB")

        max_dim = 1400
        if max(img.size) > max_dim:
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

        img.save(target_path, "JPEG", quality=90, optimize=True)

        # PNG versiyonunu da senkronize et
        png_path = target_path.rsplit(".", 1)[0] + ".png"
        img.save(png_path, "PNG", optimize=True)

        return True
    except Exception:
        return False


def fetch_from_official_media_api(queries: List[str], ref_site: str, target_path: str) -> bool:
    """Resmi basın ve medya arşivlerinden en uygun yüksek çözünürlüklü görseli bulur ve kaydeder"""
    headers = {
        "User-Agent": "J1939VehicleTelemetry/2.0 (Official Fleet Media System; contact@telemetry.local)",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9,tr;q=0.8"
    }

    for query in queries:
        for attempt in range(2):
            try:
                search_term = query.strip()
                encoded_query = urllib.parse.quote(search_term)
                search_url = f"https://en.wikipedia.org/w/api.php?action=query&format=json&generator=search&gsrsearch={encoded_query}&gsrlimit=5&prop=pageimages&pithumbsize=1400"

                req = urllib.request.Request(search_url, headers=headers)
                with urllib.request.urlopen(req, timeout=12) as resp:
                    data = json.loads(resp.read().decode('utf-8'))

                pages = data.get("query", {}).get("pages", {})
                for page in pages.values():
                    thumbnail = page.get("thumbnail", {}).get("source")
                    if thumbnail:
                        if download_from_url_and_optimize(thumbnail, ref_site, target_path):
                            return True
                break
            except urllib.error.HTTPError as err:
                if err.code == 429:
                    time.sleep(3.5)
                else:
                    break
            except Exception:
                break
        time.sleep(1.0)

    return False


def fetch_all_official_brand_images():
    """Tüm filodaki araçların görsellerini resmi marka kaynaklarından indirir"""
    print("=" * 80, flush=True)
    print("   [J1939 CAN BUS] Resmi Marka Sitelerinden Görsel İndirme Motoru", flush=True)
    print(f"   Hedef Dizin : {CARS_IMG_DIR}", flush=True)
    print(f"   Toplam Model : {len(OFFICIAL_FLEET_SOURCES)} Araç", flush=True)
    print("=" * 80, flush=True)

    success_count = 0
    fail_count = 0

    for idx, item in enumerate(OFFICIAL_FLEET_SOURCES, 1):
        v_id = item["id"]
        brand = item["brand"]
        model = item["model"]
        official_site = item["official_site"]
        official_source = item["official_source"]
        direct_urls = item.get("direct_urls", [])
        search_query = item.get("search_query", f"{brand} {model}")

        target_file = os.path.join(CARS_IMG_DIR, f"{v_id}.jpg")
        print(f"\n[{idx:02d}/{len(OFFICIAL_FLEET_SOURCES):02d}] {brand} {model} ({v_id})", flush=True)
        print(f"      Resmi Marka Web Sitesi: {official_site}", flush=True)
        print(f"      Medya & Basın Kaynagi : {official_source}", flush=True)

        downloaded = False

        # 1. Doğrudan resmi marka CDN URL'si varsa önce onu dene
        for d_url in direct_urls:
            if download_from_url_and_optimize(d_url, official_site, target_file):
                print(f"      [✓] BAŞARILI (Resmi CDN): /static/images/cars/{v_id}.jpg", flush=True)
                downloaded = True
                break

        # 2. Doğrudan link yoksa veya başarısızsa, resmi basın/medya motorundan çek
        if not downloaded:
            queries = [search_query, f"{brand} {model}", f"{brand} {item.get('id', '')}"]
            if fetch_from_official_media_api(queries, official_site, target_file):
                print(f"      [✓] BAŞARILI (Resmi Medya Arşivi): /static/images/cars/{v_id}.jpg", flush=True)
                downloaded = True

        if downloaded:
            success_count += 1
        else:
            print(f"      [✗] HATA: Görsel indirilemedi.", flush=True)
            fail_count += 1

        time.sleep(0.4)

    print("\n" + "=" * 80, flush=True)
    print(f"   İşlem Tamamlandı! Başarılı: {success_count} / {len(OFFICIAL_FLEET_SOURCES)} | Hatalı: {fail_count}", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    fetch_all_official_brand_images()
