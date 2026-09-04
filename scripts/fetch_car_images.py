"""
J1939 CAN Bus Projesi - Otomatik İnternetten Araç Görseli İndirici
Bu script, filo veritabanındaki (fleet_data.py) tüm araçlar veya yeni eklenecek araçlar
için Wikipedia / Wikimedia Commons API üzerinden telifsiz, gerçek fotoğrafları
otomatik arar, indirir ve 'web/static/images/cars/' klasörüne kaydeder.
"""

import os
import re
import urllib.request
import urllib.parse
import json
from typing import Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARS_IMG_DIR = os.path.join(BASE_DIR, "web", "static", "images", "cars")
os.makedirs(CARS_IMG_DIR, exist_ok=True)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 (J1939Telemetry/1.0)"


def fetch_car_image_from_wikipedia(query: str, vehicle_id: str) -> Optional[str]:
    """
    Wikipedia / Wikimedia API'sini kullanarak verilen marka/model için en iyi görseli çeker ve kaydeder.
    
    Örnek sorgular:
      - query="BMW G20 320i", vehicle_id="bmw-320i"
      - query="Isuzu Elf NPR", vehicle_id="isuzu-npr-long"
    """
    try:
        # 1. Wikipedia Arama API
        search_term = query.strip()
        encoded_query = urllib.parse.quote(search_term)
        search_url = f"https://en.wikipedia.org/w/api.php?action=query&format=json&generator=search&gsrsearch={encoded_query}&gsrlimit=1&prop=pageimages&pithumbsize=1000"
        
        req = urllib.request.Request(search_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        
        pages = data.get("query", {}).get("pages", {})
        if not pages:
            print(f"[-] '{query}' için Wikipedia sayfası bulunamadı.")
            return None
            
        page = next(iter(pages.values()))
        thumbnail = page.get("thumbnail", {}).get("source")
        
        if not thumbnail:
            print(f"[-] '{query}' sayfasında kapak fotoğrafı bulunamadı.")
            return None

        # 2. Görseli İndir ve Yerel Klasöre Kaydet
        ext = ".jpg"
        if ".png" in thumbnail.lower():
            ext = ".png"
            
        target_path = os.path.join(CARS_IMG_DIR, f"{vehicle_id}{ext}")
        
        img_req = urllib.request.Request(thumbnail, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(img_req, timeout=15) as img_resp, open(target_path, "wb") as f:
            f.write(img_resp.read())
            
        rel_path = f"/static/images/cars/{vehicle_id}{ext}"
        print(f"[+] Başarılı: {query} -> {rel_path} ({thumbnail})")
        return rel_path

    except Exception as e:
        print(f"[!] Hata ({query}): {e}")
        return None


def download_image_from_direct_url(image_url: str, vehicle_id: str) -> Optional[str]:
    """
    Doğrudan verilen bir web URL'sinden (Unsplash, CDN, resmi site) görseli indirir.
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
        print(f"[+] Doğrudan URL'den İndirildi: {vehicle_id} -> {rel_path}")
        return rel_path
    except Exception as e:
        print(f"[!] Doğrudan URL indirme hatası ({vehicle_id}): {e}")
        return None


if __name__ == "__main__":
    print("=" * 60)
    print("   J1939 Otomatik Araç Görseli İndirici Başlatıldı")
    print("=" * 60)
    
    # Örnek Kullanım 1: Wikipedia API ile isimden arayıp otomatik indirme
    test_vehicles = [
        {"id": "bmw-320i", "search": "BMW 3 Series G20"},
        {"id": "isuzu-npr-long", "search": "Isuzu Elf NPR truck"},
        {"id": "tesla-model-3-perf", "search": "Tesla Model 3"},
        {"id": "togg-t10x", "search": "Togg T10X"}
    ]
    
    for item in test_vehicles:
        fetch_car_image_from_wikipedia(item["search"], item["id"])
