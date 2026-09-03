"""
Downloads real, high-resolution, distinct photographic images for all 30 fleet vehicles
and saves them directly into web/static/images/cars/<id>.jpg.
"""

import os
import urllib.request
import time

PHOTOS = {
    # 1. BMW
    "bmw-320i": "https://images.unsplash.com/photo-1555215695-3004980ad54e?auto=format&fit=crop&w=1000&q=80",
    "bmw-520d": "https://images.unsplash.com/photo-1523983388277-336a66bf9bcd?auto=format&fit=crop&w=1000&q=80",
    "bmw-m4-competition": "https://images.unsplash.com/photo-1617814076367-b759c7d7e738?auto=format&fit=crop&w=1000&q=80",

    # 2. Mercedes-Benz
    "mb-c200": "https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?auto=format&fit=crop&w=1000&q=80",
    "mb-e300d": "https://images.unsplash.com/photo-1617531653332-bd46c24f2068?auto=format&fit=crop&w=1000&q=80",
    "mb-g63-amg": "https://images.unsplash.com/photo-1520031441872-265e4ff70366?auto=format&fit=crop&w=1000&q=80",

    # 3. Audi
    "audi-a3-sedan": "https://images.unsplash.com/photo-1603584173870-7f23fdae1b7a?auto=format&fit=crop&w=1000&q=80",
    "audi-a6-avant": "https://images.unsplash.com/photo-1606152421802-db97b9c7a11b?auto=format&fit=crop&w=1000&q=80",
    "audi-rs6-avant": "https://images.unsplash.com/photo-1603386329225-868f9b1ee6c9?auto=format&fit=crop&w=1000&q=80",

    # 4. Volkswagen
    "vw-golf-8": "https://images.unsplash.com/photo-1541899481282-d53bffe3c35d?auto=format&fit=crop&w=1000&q=80",
    "vw-passat-variant": "https://images.unsplash.com/photo-1542282088-72c9c27ed0cd?auto=format&fit=crop&w=1000&q=80",
    "vw-tiguan-rline": "https://images.unsplash.com/photo-1583121274602-3e2820c69888?auto=format&fit=crop&w=1000&q=80",

    # 5. Toyota
    "toyota-corolla-hybrid": "https://images.unsplash.com/photo-1621007947382-bb3c3994e3fb?auto=format&fit=crop&w=1000&q=80",
    "toyota-rav4-hybrid": "https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?auto=format&fit=crop&w=1000&q=80",
    "toyota-yaris-cross": "https://images.unsplash.com/photo-1590362891991-f776e747a588?auto=format&fit=crop&w=1000&q=80",

    # 6. Tesla
    "tesla-model-3-perf": "https://images.unsplash.com/photo-1560958089-b8a1929cea89?auto=format&fit=crop&w=1000&q=80",
    "tesla-model-y-longrange": "https://images.unsplash.com/photo-1571127236794-81c0bbfe1ce3?auto=format&fit=crop&w=1000&q=80",
    "tesla-model-s-plaid": "https://images.unsplash.com/photo-1617788138017-80ad40651399?auto=format&fit=crop&w=1000&q=80",

    # 7. Ford
    "ford-focus-st": "https://images.unsplash.com/photo-1551522435-a13afa10f103?auto=format&fit=crop&w=1000&q=80",
    "ford-mustang-gt": "https://images.unsplash.com/photo-1584345604476-8ec5e12e42dd?auto=format&fit=crop&w=1000&q=80",
    "ford-ranger-raptor": "https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?auto=format&fit=crop&w=1000&q=80",

    # 8. Renault
    "renault-clio-5": "https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=1000&q=80",
    "renault-megane-etech": "https://images.unsplash.com/photo-1508974239320-0a029497e820?auto=format&fit=crop&w=1000&q=80",
    "renault-austral": "https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1000&q=80",

    # 9. Hyundai
    "hyundai-i20-n": "https://images.unsplash.com/photo-1619682817481-e994891cd1f5?auto=format&fit=crop&w=1000&q=80",
    "hyundai-tucson-hybrid": "https://images.unsplash.com/photo-1519641471654-76ce0107ad1b?auto=format&fit=crop&w=1000&q=80",
    "hyundai-ioniq-5": "https://images.unsplash.com/photo-1542362567-b07e54358753?auto=format&fit=crop&w=1000&q=80",

    # 10. Fiat
    "fiat-egea-cross": "https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=1000&q=80",
    "fiat-500e": "https://images.unsplash.com/photo-1502877338535-766e1452684a?auto=format&fit=crop&w=1000&q=80",
    "fiat-doblo-combi": "https://images.unsplash.com/photo-1526726538690-5cbf956ae2fd?auto=format&fit=crop&w=1000&q=80",
}

OUT_DIR = os.path.join(os.path.dirname(__file__), "web", "static", "images", "cars")
os.makedirs(OUT_DIR, exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
}

def download_all():
    total = len(PHOTOS)
    print(f"Starting download of {total} real car photos...")
    success_count = 0

    for idx, (car_id, url) in enumerate(PHOTOS.items(), 1):
        out_path = os.path.join(OUT_DIR, f"{car_id}.jpg")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
                with open(out_path, "wb") as f:
                    f.write(data)
            print(f"[{idx}/{total}] [OK] {car_id}.jpg ({len(data)//1024} KB)")
            success_count += 1
        except Exception as e:
            print(f"[{idx}/{total}] [FAILED] {car_id}: {e}")
        time.sleep(0.1)

    print(f"\nFinished! Successfully downloaded {success_count}/{total} photos into web/static/images/cars/.")

if __name__ == "__main__":
    download_all()
