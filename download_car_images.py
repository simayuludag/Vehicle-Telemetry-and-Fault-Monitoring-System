"""
Downloads and generates distinct, high quality local images for all 30 vehicles.
"""

import os
import urllib.request
import urllib.parse
import json

CAR_IMAGES = {
    # 1. BMW
    "bmw-320i": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/BMW_G20_IMG_0049.jpg/800px-BMW_G20_IMG_0049.jpg",
    "bmw-520d": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/2018_BMW_520d_SE_Automatic_2.0_Front.jpg/800px-2018_BMW_520d_SE_Automatic_2.0_Front.jpg",
    "bmw-m4-competition": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/53/BMW_M4_Competition_Coupe_G82_IMG_4078.jpg/800px-BMW_M4_Competition_Coupe_G82_IMG_4078.jpg",

    # 2. Mercedes-Benz
    "mb-c200": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f0/Mercedes-Benz_W206_IMG_4223.jpg/800px-Mercedes-Benz_W206_IMG_4223.jpg",
    "mb-e300d": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Mercedes-Benz_W213_E_220_d_4MATIC_All-Terrain_IMG_0584.jpg/800px-Mercedes-Benz_W213_E_220_d_4MATIC_All-Terrain_IMG_0584.jpg",
    "mb-g63-amg": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6f/Mercedes-AMG_G_63_%28W_463%2C_Facelift%29_%E2%80%93_f_16032025.jpg/800px-Mercedes-AMG_G_63_%28W_463%2C_Facelift%29_%E2%80%93_f_16032025.jpg",

    # 3. Audi
    "audi-a3-sedan": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/2021_Audi_A3_Sportback_35_TFSI_1.5.jpg/800px-2021_Audi_A3_Sportback_35_TFSI_1.5.jpg",
    "audi-a6-avant": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Audi_A6_Avant_C8_IMG_2181.jpg/800px-Audi_A6_Avant_C8_IMG_2181.jpg",
    "audi-rs6-avant": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/62/Audi_RS6_Avant_C8_IMG_2452.jpg/800px-Audi_RS6_Avant_C8_IMG_2452.jpg",

    # 4. Volkswagen
    "vw-golf-8": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/52/VW_Golf_VIII_1.5_eTSI_Style_%E2%80%93_Frontansicht%2C_12._September_2020%2C_Ratingen.jpg/800px-VW_Golf_VIII_1.5_eTSI_Style_%E2%80%93_Frontansicht%2C_12._September_2020%2C_Ratingen.jpg",
    "vw-passat-variant": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/2019_Volkswagen_Passat_Estate_R-Line_TDi_2.0_Front.jpg/800px-2019_Volkswagen_Passat_Estate_R-Line_TDi_2.0_Front.jpg",
    "vw-tiguan-rline": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/be/Volkswagen_Tiguan_II_Facelift_IMG_3962.jpg/800px-Volkswagen_Tiguan_II_Facelift_IMG_3962.jpg",

    # 5. Toyota
    "toyota-corolla-hybrid": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/2019_Toyota_Corolla_Icon_Tech_HEV_1.8_Front.jpg/800px-2019_Toyota_Corolla_Icon_Tech_HEV_1.8_Front.jpg",
    "toyota-rav4-hybrid": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/77/Toyota_RAV4_XA50_IMG_2115.jpg/800px-Toyota_RAV4_XA50_IMG_2115.jpg",
    "toyota-yaris-cross": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/07/2021_Toyota_Yaris_Cross_Dynamic_1.5.jpg/800px-2021_Toyota_Yaris_Cross_Dynamic_1.5.jpg",

    # 6. Tesla
    "tesla-model-3-perf": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/2019_Tesla_Model_3_Performance_AWD_Front.jpg/800px-2019_Tesla_Model_3_Performance_AWD_Front.jpg",
    "tesla-model-y-longrange": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/69/2022_Tesla_Model_Y_Long_Range_AWD_Front.jpg/800px-2022_Tesla_Model_Y_Long_Range_AWD_Front.jpg",
    "tesla-model-s-plaid": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/2018_Tesla_Model_S_75D_Front.jpg/800px-2018_Tesla_Model_S_75D_Front.jpg",

    # 7. Ford
    "ford-focus-st": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/Ford_Focus_ST_Gen4_IMG_3059.jpg/800px-Ford_Focus_ST_Gen4_IMG_3059.jpg",
    "ford-mustang-gt": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d1/2018_Ford_Mustang_GT_5.0_Front.jpg/800px-2018_Ford_Mustang_GT_5.0_Front.jpg",
    "ford-ranger-raptor": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/03/Ford_Ranger_Raptor_Gen2_IMG_3489.jpg/800px-Ford_Ranger_Raptor_Gen2_IMG_3489.jpg",

    # 8. Renault
    "renault-clio-5": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Renault_Clio_V_IMG_2170.jpg/800px-Renault_Clio_V_IMG_2170.jpg",
    "renault-megane-etech": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/Renault_Megane_E-Tech_Electric_IMG_6043.jpg/800px-Renault_Megane_E-Tech_Electric_IMG_6043.jpg",
    "renault-austral": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/Renault_Austral_IMG_6697.jpg/800px-Renault_Austral_IMG_6697.jpg",

    # 9. Hyundai
    "hyundai-i20-n": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Hyundai_i20_N_IMG_4908.jpg/800px-Hyundai_i20_N_IMG_4908.jpg",
    "hyundai-tucson-hybrid": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/75/Hyundai_Tucson_NX4_IMG_4263.jpg/800px-Hyundai_Tucson_NX4_IMG_4263.jpg",
    "hyundai-ioniq-5": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Hyundai_Ioniq_5_IMG_5017.jpg/800px-Hyundai_Ioniq_5_IMG_5017.jpg",

    # 10. Fiat
    "fiat-egea-cross": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/Fiat_Tipo_Cross_IMG_3990.jpg/800px-Fiat_Tipo_Cross_IMG_3990.jpg",
    "fiat-500e": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Fiat_500e_IMG_3977.jpg/800px-Fiat_500e_IMG_3977.jpg",
    "fiat-doblo-combi": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Fiat_Dobl%C3%B2_Panorama_Facelift_front_20160522.jpg/800px-Fiat_Dobl%C3%B2_Panorama_Facelift_front_20160522.jpg",
}

OUT_DIR = os.path.join(os.path.dirname(__file__), "web", "static", "images", "cars")
os.makedirs(OUT_DIR, exist_ok=True)

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

def download_images():
    for car_id, url in CAR_IMAGES.items():
        out_path = os.path.join(OUT_DIR, f"{car_id}.jpg")
        if not os.path.exists(out_path):
            try:
                print(f"Downloading {car_id}...")
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=10) as response, open(out_path, 'wb') as out_file:
                    out_file.write(response.read())
                print(f"[OK] {car_id}")
            except Exception as e:
                print(f"[ERR] {car_id}: {e}")

if __name__ == "__main__":
    download_images()
