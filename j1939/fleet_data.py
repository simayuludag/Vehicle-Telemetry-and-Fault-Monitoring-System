"""
J1939 Passenger & Commercial Fleet Matrix: 10 Major Automotive Brands x 3 Iconic Models = 30 Vehicles
Includes Sedans, SUVs, Hatchbacks, Performance and Electric Vehicles.
Each vehicle contains unique SAE J1939 Source Address (SA: 0x01 to 0x1E), specs, telemetry status, and high-res web images.
"""

from typing import Dict, List, Any


FLEET_BRANDS = [
    {
        "id": "bmw",
        "name": "BMW",
        "country": "Germany",
        "color": "#0066B1",
        "badge": "BMW",
        "accent": "rgba(0, 102, 177, 0.2)",
    },
    {
        "id": "mercedes",
        "name": "Mercedes-Benz",
        "country": "Germany",
        "color": "#00D2FF",
        "badge": "MB",
        "accent": "rgba(0, 210, 255, 0.2)",
    },
    {
        "id": "audi",
        "name": "Audi",
        "country": "Germany",
        "color": "#F50537",
        "badge": "AUDI",
        "accent": "rgba(245, 5, 55, 0.2)",
    },
    {
        "id": "volkswagen",
        "name": "Volkswagen",
        "country": "Germany",
        "color": "#1E90FF",
        "badge": "VW",
        "accent": "rgba(30, 144, 255, 0.2)",
    },
    {
        "id": "toyota",
        "name": "Toyota",
        "country": "Japan",
        "color": "#EB0A1E",
        "badge": "TOYOTA",
        "accent": "rgba(235, 10, 30, 0.2)",
    },
    {
        "id": "tesla",
        "name": "Tesla",
        "country": "USA",
        "color": "#E82127",
        "badge": "TESLA",
        "accent": "rgba(232, 33, 39, 0.2)",
    },
    {
        "id": "ford",
        "name": "Ford",
        "country": "USA / Global",
        "color": "#118AB2",
        "badge": "FORD",
        "accent": "rgba(17, 138, 178, 0.2)",
    },
    {
        "id": "renault",
        "name": "Renault",
        "country": "France",
        "color": "#FFCC00",
        "badge": "RENAULT",
        "accent": "rgba(255, 204, 0, 0.2)",
    },
    {
        "id": "hyundai",
        "name": "Hyundai",
        "country": "South Korea",
        "color": "#002C6C",
        "badge": "HYUNDAI",
        "accent": "rgba(0, 44, 108, 0.2)",
    },
    {
        "id": "fiat",
        "name": "Fiat",
        "country": "Italy",
        "color": "#990000",
        "badge": "FIAT",
        "accent": "rgba(153, 0, 0, 0.2)",
    },
]


VEHICLES: List[Dict[str, Any]] = [
    # 1. BMW (SA: 0x01, 0x02, 0x03)
    {
        "id": "bmw-320i",
        "brand_id": "bmw",
        "brand_name": "BMW",
        "model": "320i Sedan M Sport",
        "category": "Premium Sedan",
        "plate": "34 BMW 320",
        "source_address": 0x01,
        "engine": "2.0L TwinPower Turbo 170 HP",
        "max_speed": 235.0,
        "default_speed": 110.0,
        "current_speed": 110.0,
        "target_speed": 110.0,
        "acceleration_rate": 6.5,
        "throttle_pct": 20.0,
        "brake_pct": 0.0,
        "gear": "D5",
        "battery_soc": 95.0,
        "battery_soh": 99.0,
        "image_url": "/static/images/cars/bmw-320i.jpg",
        "status": "cruising",
        "simulation_mode": "cruise",
        "brake_pressed": False,
    },
    {
        "id": "bmw-520d",
        "brand_id": "bmw",
        "brand_name": "BMW",
        "model": "520d Sedan xDrive",
        "category": "Executive Sedan",
        "plate": "34 BMW 520",
        "source_address": 0x02,
        "engine": "2.0L Mild-Hybrid Dizel 197 HP",
        "max_speed": 240.0,
        "default_speed": 120.0,
        "current_speed": 120.0,
        "target_speed": 120.0,
        "acceleration_rate": 6.8,
        "throttle_pct": 22.0,
        "brake_pct": 0.0,
        "gear": "D5",
        "battery_soc": 92.5,
        "battery_soh": 98.0,
        "image_url": "/static/images/cars/bmw-520d.jpg",
        "status": "cruising",
        "simulation_mode": "highway",
        "brake_pressed": False,
    },
    {
        "id": "bmw-m4-competition",
        "brand_id": "bmw",
        "brand_name": "BMW",
        "model": "M4 Competition Coupe",
        "category": "Super Sport Coupe",
        "plate": "34 BMW 004",
        "source_address": 0x03,
        "engine": "3.0L M TwinPower Turbo 510 HP",
        "max_speed": 250.0,
        "default_speed": 140.0,
        "current_speed": 140.0,
        "target_speed": 140.0,
        "acceleration_rate": 12.0,
        "throttle_pct": 28.0,
        "brake_pct": 0.0,
        "gear": "D6",
        "battery_soc": 96.0,
        "battery_soh": 100.0,
        "image_url": "/static/images/cars/bmw-m4-competition.jpg",
        "status": "cruising",
        "simulation_mode": "manual",
        "brake_pressed": False,
    },

    # 2. Mercedes-Benz (SA: 0x04, 0x05, 0x06)
    {
        "id": "mb-c200",
        "brand_id": "mercedes",
        "brand_name": "Mercedes-Benz",
        "model": "C200 4MATIC AMG",
        "category": "Premium Sedan",
        "plate": "34 MB 200",
        "source_address": 0x04,
        "engine": "1.5L Turbo EQ Boost 204 HP",
        "max_speed": 241.0,
        "default_speed": 115.0,
        "current_speed": 115.0,
        "target_speed": 115.0,
        "acceleration_rate": 6.7,
        "throttle_pct": 21.0,
        "brake_pct": 0.0,
        "gear": "D5",
        "battery_soc": 94.0,
        "battery_soh": 98.5,
        "image_url": "/static/images/cars/mb-c200.jpg",
        "status": "cruising",
        "simulation_mode": "cruise",
        "brake_pressed": False,
    },
    {
        "id": "mb-e300d",
        "brand_id": "mercedes",
        "brand_name": "Mercedes-Benz",
        "model": "E300d 4MATIC Exclusive",
        "category": "Executive Luxury Sedan",
        "plate": "34 MB 300",
        "source_address": 0x05,
        "engine": "2.0L Turbo Dizel 265 HP",
        "max_speed": 250.0,
        "default_speed": 125.0,
        "current_speed": 125.0,
        "target_speed": 125.0,
        "acceleration_rate": 7.5,
        "throttle_pct": 24.0,
        "brake_pct": 0.0,
        "gear": "D6",
        "battery_soc": 91.0,
        "battery_soh": 97.5,
        "image_url": "/static/images/cars/mb-e300d.jpg",
        "status": "cruising",
        "simulation_mode": "highway",
        "brake_pressed": False,
    },
    {
        "id": "mb-g63-amg",
        "brand_id": "mercedes",
        "brand_name": "Mercedes-Benz",
        "model": "G63 AMG 4x4",
        "category": "Ultra Luxury Off-Road SUV",
        "plate": "34 MB 063",
        "source_address": 0x06,
        "engine": "4.0L V8 Biturbo 585 HP",
        "max_speed": 240.0,
        "default_speed": 100.0,
        "current_speed": 100.0,
        "target_speed": 100.0,
        "acceleration_rate": 10.5,
        "throttle_pct": 26.0,
        "brake_pct": 0.0,
        "gear": "D4",
        "battery_soc": 97.0,
        "battery_soh": 99.0,
        "image_url": "/static/images/cars/mb-g63-amg.jpg",
        "status": "cruising",
        "simulation_mode": "manual",
        "brake_pressed": False,
    },

    # 3. Audi (SA: 0x07, 0x08, 0x09)
    {
        "id": "audi-a3-sedan",
        "brand_id": "audi",
        "brand_name": "Audi",
        "model": "A3 Sedan 35 TFSI S line",
        "category": "Compact Luxury Sedan",
        "plate": "34 AU 350",
        "source_address": 0x07,
        "engine": "1.5L Turbo Mild-Hybrid 150 HP",
        "max_speed": 224.0,
        "default_speed": 90.0,
        "current_speed": 90.0,
        "target_speed": 90.0,
        "acceleration_rate": 5.8,
        "throttle_pct": 18.0,
        "brake_pct": 0.0,
        "gear": "D4",
        "battery_soc": 93.0,
        "battery_soh": 98.0,
        "image_url": "/static/images/cars/audi-a3-sedan.jpg",
        "status": "cruising",
        "simulation_mode": "city",
        "brake_pressed": False,
    },
    {
        "id": "audi-a6-avant",
        "brand_id": "audi",
        "brand_name": "Audi",
        "model": "A6 Avant 40 TDI Quattro",
        "category": "Executive Station Wagon",
        "plate": "34 AU 460",
        "source_address": 0x08,
        "engine": "2.0L TDI Ultra 204 HP",
        "max_speed": 246.0,
        "default_speed": 120.0,
        "current_speed": 120.0,
        "target_speed": 120.0,
        "acceleration_rate": 7.0,
        "throttle_pct": 22.0,
        "brake_pct": 0.0,
        "gear": "D5",
        "battery_soc": 90.0,
        "battery_soh": 97.0,
        "image_url": "/static/images/cars/audi-a6-avant.jpg",
        "status": "cruising",
        "simulation_mode": "highway",
        "brake_pressed": False,
    },
    {
        "id": "audi-rs6-avant",
        "brand_id": "audi",
        "brand_name": "Audi",
        "model": "RS6 Avant Performance",
        "category": "Super Sport Wagon",
        "plate": "34 AU 006",
        "source_address": 0x09,
        "engine": "4.0L V8 Biturbo TFSI 630 HP",
        "max_speed": 250.0,
        "default_speed": 150.0,
        "current_speed": 150.0,
        "target_speed": 150.0,
        "acceleration_rate": 13.5,
        "throttle_pct": 30.0,
        "brake_pct": 0.0,
        "gear": "D6",
        "battery_soc": 98.0,
        "battery_soh": 100.0,
        "image_url": "/static/images/cars/audi-rs6-avant.jpg",
        "status": "cruising",
        "simulation_mode": "manual",
        "brake_pressed": False,
    },

    # 4. Volkswagen (SA: 0x0A, 0x0B, 0x0C)
    {
        "id": "vw-golf-8",
        "brand_id": "volkswagen",
        "brand_name": "Volkswagen",
        "model": "Golf 8 1.5 eTSI R-Line",
        "category": "Hatchback",
        "plate": "34 VW 808",
        "source_address": 0x0A,
        "engine": "1.5L eTSI ACT 150 HP",
        "max_speed": 224.0,
        "default_speed": 85.0,
        "current_speed": 85.0,
        "target_speed": 85.0,
        "acceleration_rate": 5.9,
        "throttle_pct": 17.0,
        "brake_pct": 0.0,
        "gear": "D4",
        "battery_soc": 92.0,
        "battery_soh": 98.0,
        "image_url": "/static/images/cars/vw-golf-8.jpg",
        "status": "cruising",
        "simulation_mode": "city",
        "brake_pressed": False,
    },
    {
        "id": "vw-passat-variant",
        "brand_id": "volkswagen",
        "brand_name": "Volkswagen",
        "model": "Passat Variant 2.0 TDI",
        "category": "Aile & Uzun Yol Station Wagon",
        "plate": "34 VW 200",
        "source_address": 0x0B,
        "engine": "2.0L TDI SCR 193 HP",
        "max_speed": 232.0,
        "default_speed": 115.0,
        "current_speed": 115.0,
        "target_speed": 115.0,
        "acceleration_rate": 6.4,
        "throttle_pct": 21.0,
        "brake_pct": 0.0,
        "gear": "D5",
        "battery_soc": 94.0,
        "battery_soh": 98.5,
        "image_url": "/static/images/cars/vw-passat-variant.jpg",
        "status": "cruising",
        "simulation_mode": "highway",
        "brake_pressed": False,
    },
    {
        "id": "vw-tiguan-rline",
        "brand_id": "volkswagen",
        "brand_name": "Volkswagen",
        "model": "Tiguan 1.5 eTSI R-Line",
        "category": "C-SUV",
        "plate": "34 VW 700",
        "source_address": 0x0C,
        "engine": "1.5L eTSI 150 HP",
        "max_speed": 210.0,
        "default_speed": 95.0,
        "current_speed": 95.0,
        "target_speed": 95.0,
        "acceleration_rate": 5.5,
        "throttle_pct": 19.0,
        "brake_pct": 0.0,
        "gear": "D4",
        "battery_soc": 93.5,
        "battery_soh": 97.5,
        "image_url": "/static/images/cars/vw-tiguan-rline.jpg",
        "status": "cruising",
        "simulation_mode": "cruise",
        "brake_pressed": False,
    },

    # 5. Toyota (SA: 0x0D, 0x0E, 0x0F)
    {
        "id": "toyota-corolla-hybrid",
        "brand_id": "toyota",
        "brand_name": "Toyota",
        "model": "Corolla 1.8 Hybrid Passion X-Pack",
        "category": "Sedan Hybrid",
        "plate": "34 TY 180",
        "source_address": 0x0D,
        "engine": "1.8L Kendi Kendini Şarj Eden Hibrit 140 HP",
        "max_speed": 180.0,
        "default_speed": 80.0,
        "current_speed": 80.0,
        "target_speed": 80.0,
        "acceleration_rate": 5.2,
        "throttle_pct": 16.0,
        "brake_pct": 0.0,
        "gear": "D4",
        "battery_soc": 78.0,
        "battery_soh": 99.0,
        "image_url": "/static/images/cars/toyota-corolla-hybrid.jpg",
        "status": "cruising",
        "simulation_mode": "city",
        "brake_pressed": False,
    },
    {
        "id": "toyota-rav4-hybrid",
        "brand_id": "toyota",
        "brand_name": "Toyota",
        "model": "RAV4 2.5 Hybrid AWD-i",
        "category": "D-SUV Hybrid",
        "plate": "34 TY 400",
        "source_address": 0x0E,
        "engine": "2.5L Dynamic Force Hybrid 222 HP",
        "max_speed": 190.0,
        "default_speed": 105.0,
        "current_speed": 105.0,
        "target_speed": 105.0,
        "acceleration_rate": 6.8,
        "throttle_pct": 20.0,
        "brake_pct": 0.0,
        "gear": "D5",
        "battery_soc": 82.0,
        "battery_soh": 98.5,
        "image_url": "/static/images/cars/toyota-rav4-hybrid.jpg",
        "status": "cruising",
        "simulation_mode": "cruise",
        "brake_pressed": False,
    },
    {
        "id": "toyota-yaris-cross",
        "brand_id": "toyota",
        "brand_name": "Toyota",
        "model": "Yaris Cross 1.5 Hybrid",
        "category": "B-SUV Urban",
        "plate": "34 TY 150",
        "source_address": 0x0F,
        "engine": "1.5L Hybrid 116 HP",
        "max_speed": 170.0,
        "default_speed": 65.0,
        "current_speed": 65.0,
        "target_speed": 65.0,
        "acceleration_rate": 4.8,
        "throttle_pct": 15.0,
        "brake_pct": 0.0,
        "gear": "D3",
        "battery_soc": 85.0,
        "battery_soh": 99.5,
        "image_url": "/static/images/cars/toyota-yaris-cross.jpg",
        "status": "cruising",
        "simulation_mode": "city",
        "brake_pressed": False,
    },

    # 6. Tesla (SA: 0x10, 0x11, 0x12)
    {
        "id": "tesla-model-3-perf",
        "brand_id": "tesla",
        "brand_name": "Tesla",
        "model": "Model 3 Performance Dual Motor",
        "category": "Tam Elektrikli Sedan (EV)",
        "plate": "34 TS 003",
        "source_address": 0x10,
        "engine": "Dual Motor AWD Elektrik 510 HP",
        "max_speed": 250.0,
        "default_speed": 130.0,
        "current_speed": 130.0,
        "target_speed": 130.0,
        "acceleration_rate": 14.0,
        "throttle_pct": 25.0,
        "brake_pct": 0.0,
        "gear": "D",
        "battery_soc": 88.0,
        "battery_soh": 99.0,
        "image_url": "/static/images/cars/tesla-model-3-perf.jpg",
        "status": "cruising",
        "simulation_mode": "highway",
        "brake_pressed": False,
    },
    {
        "id": "tesla-model-y-longrange",
        "brand_id": "tesla",
        "brand_name": "Tesla",
        "model": "Model Y Long Range AWD",
        "category": "Tam Elektrikli SUV (EV)",
        "plate": "34 TS 009",
        "source_address": 0x11,
        "engine": "Dual Motor AWD Elektrik 384 HP",
        "max_speed": 217.0,
        "default_speed": 110.0,
        "current_speed": 110.0,
        "target_speed": 110.0,
        "acceleration_rate": 9.5,
        "throttle_pct": 20.0,
        "brake_pct": 0.0,
        "gear": "D",
        "battery_soc": 84.0,
        "battery_soh": 98.0,
        "image_url": "/static/images/cars/tesla-model-y-longrange.jpg",
        "status": "cruising",
        "simulation_mode": "cruise",
        "brake_pressed": False,
    },
    {
        "id": "tesla-model-s-plaid",
        "brand_id": "tesla",
        "brand_name": "Tesla",
        "model": "Model S Plaid Tri-Motor",
        "category": "Ultra Hyper EV Sedan",
        "plate": "34 TS 100",
        "source_address": 0x12,
        "engine": "Tri-Motor AWD Elektrik 1020 HP",
        "max_speed": 250.0,
        "default_speed": 160.0,
        "current_speed": 160.0,
        "target_speed": 160.0,
        "acceleration_rate": 18.0,
        "throttle_pct": 32.0,
        "brake_pct": 0.0,
        "gear": "D",
        "battery_soc": 91.0,
        "battery_soh": 100.0,
        "image_url": "/static/images/cars/tesla-model-s-plaid.jpg",
        "status": "cruising",
        "simulation_mode": "manual",
        "brake_pressed": False,
    },

    # 7. Ford (SA: 0x13, 0x14, 0x15)
    {
        "id": "ford-focus-st",
        "brand_id": "ford",
        "brand_name": "Ford",
        "model": "Focus ST 2.3 EcoBoost",
        "category": "Hot Hatchback",
        "plate": "34 FD 230",
        "source_address": 0x13,
        "engine": "2.3L EcoBoost 280 HP",
        "max_speed": 250.0,
        "default_speed": 120.0,
        "current_speed": 120.0,
        "target_speed": 120.0,
        "acceleration_rate": 8.2,
        "throttle_pct": 22.0,
        "brake_pct": 0.0,
        "gear": "D5",
        "battery_soc": 95.0,
        "battery_soh": 98.0,
        "image_url": "/static/images/cars/ford-focus-st.jpg",
        "status": "cruising",
        "simulation_mode": "highway",
        "brake_pressed": False,
    },
    {
        "id": "ford-mustang-gt",
        "brand_id": "ford",
        "brand_name": "Ford",
        "model": "Mustang GT 5.0 V8 Fastback",
        "category": "American Muscle Car",
        "plate": "34 FD 500",
        "source_address": 0x14,
        "engine": "5.0L Coyote V8 450 HP",
        "max_speed": 250.0,
        "default_speed": 135.0,
        "current_speed": 135.0,
        "target_speed": 135.0,
        "acceleration_rate": 11.0,
        "throttle_pct": 27.0,
        "brake_pct": 0.0,
        "gear": "D6",
        "battery_soc": 96.0,
        "battery_soh": 99.0,
        "image_url": "/static/images/cars/ford-mustang-gt.jpg",
        "status": "cruising",
        "simulation_mode": "manual",
        "brake_pressed": False,
    },
    {
        "id": "ford-ranger-raptor",
        "brand_id": "ford",
        "brand_name": "Ford",
        "model": "Ranger Raptor 3.0 V6 Twin-Turbo",
        "category": "Performans Pick-up 4x4",
        "plate": "34 FD 900",
        "source_address": 0x15,
        "engine": "3.0L EcoBoost V6 292 HP",
        "max_speed": 180.0,
        "default_speed": 85.0,
        "current_speed": 85.0,
        "target_speed": 85.0,
        "acceleration_rate": 6.5,
        "throttle_pct": 18.0,
        "brake_pct": 0.0,
        "gear": "D4",
        "battery_soc": 93.0,
        "battery_soh": 98.0,
        "image_url": "/static/images/cars/ford-ranger-raptor.jpg",
        "status": "cruising",
        "simulation_mode": "cruise",
        "brake_pressed": False,
    },

    # 8. Renault (SA: 0x16, 0x17, 0x18)
    {
        "id": "renault-clio-5",
        "brand_id": "renault",
        "brand_name": "Renault",
        "model": "Clio 5 1.0 TCe E-Tech",
        "category": "B Segment Hatchback",
        "plate": "34 RN 005",
        "source_address": 0x16,
        "engine": "1.0L Turbo Benzin 90 HP",
        "max_speed": 180.0,
        "default_speed": 70.0,
        "current_speed": 70.0,
        "target_speed": 70.0,
        "acceleration_rate": 4.6,
        "throttle_pct": 15.0,
        "brake_pct": 0.0,
        "gear": "D3",
        "battery_soc": 94.0,
        "battery_soh": 99.0,
        "image_url": "/static/images/cars/renault-clio-5.jpg",
        "status": "cruising",
        "simulation_mode": "city",
        "brake_pressed": False,
    },
    {
        "id": "renault-megane-etech",
        "brand_id": "renault",
        "brand_name": "Renault",
        "model": "Megane E-Tech %100 Elektrikli",
        "category": "C-Crossover Elektrikli (EV)",
        "plate": "34 RN 220",
        "source_address": 0x17,
        "engine": "Elektrik Motoru EV60 220 HP",
        "max_speed": 160.0,
        "default_speed": 95.0,
        "current_speed": 95.0,
        "target_speed": 95.0,
        "acceleration_rate": 7.4,
        "throttle_pct": 19.0,
        "brake_pct": 0.0,
        "gear": "D",
        "battery_soc": 86.0,
        "battery_soh": 98.5,
        "image_url": "/static/images/cars/renault-megane-etech.jpg",
        "status": "cruising",
        "simulation_mode": "cruise",
        "brake_pressed": False,
    },
    {
        "id": "renault-austral",
        "brand_id": "renault",
        "brand_name": "Renault",
        "model": "Austral 1.2 E-Tech Full Hybrid",
        "category": "C-SUV Hybrid",
        "plate": "34 RN 120",
        "source_address": 0x18,
        "engine": "1.2L E-Tech Full Hybrid 200 HP",
        "max_speed": 175.0,
        "default_speed": 90.0,
        "current_speed": 90.0,
        "target_speed": 90.0,
        "acceleration_rate": 6.2,
        "throttle_pct": 18.0,
        "brake_pct": 0.0,
        "gear": "D4",
        "battery_soc": 89.0,
        "battery_soh": 99.0,
        "image_url": "/static/images/cars/renault-austral.jpg",
        "status": "cruising",
        "simulation_mode": "cruise",
        "brake_pressed": False,
    },

    # 9. Hyundai (SA: 0x19, 0x1A, 0x1B)
    {
        "id": "hyundai-i20-n",
        "brand_id": "hyundai",
        "brand_name": "Hyundai",
        "model": "i20 N 1.6 T-GDI",
        "category": "Pocket Rocket Hot Hatch",
        "plate": "34 HY 020",
        "source_address": 0x19,
        "engine": "1.6L T-GDI Turbo 204 HP",
        "max_speed": 230.0,
        "default_speed": 115.0,
        "current_speed": 115.0,
        "target_speed": 115.0,
        "acceleration_rate": 8.0,
        "throttle_pct": 21.0,
        "brake_pct": 0.0,
        "gear": "D5",
        "battery_soc": 95.0,
        "battery_soh": 99.0,
        "image_url": "/static/images/cars/hyundai-i20-n.jpg",
        "status": "cruising",
        "simulation_mode": "highway",
        "brake_pressed": False,
    },
    {
        "id": "hyundai-tucson-hybrid",
        "brand_id": "hyundai",
        "brand_name": "Hyundai",
        "model": "Tucson 1.6 T-GDI Hybrid 4x4",
        "category": "C-SUV",
        "plate": "34 HY 400",
        "source_address": 0x1A,
        "engine": "1.6L Hibrit AWD 230 HP",
        "max_speed": 193.0,
        "default_speed": 100.0,
        "current_speed": 100.0,
        "target_speed": 100.0,
        "acceleration_rate": 6.6,
        "throttle_pct": 20.0,
        "brake_pct": 0.0,
        "gear": "D5",
        "battery_soc": 84.0,
        "battery_soh": 98.0,
        "image_url": "/static/images/cars/hyundai-tucson-hybrid.jpg",
        "status": "cruising",
        "simulation_mode": "cruise",
        "brake_pressed": False,
    },
    {
        "id": "hyundai-ioniq-5",
        "brand_id": "hyundai",
        "brand_name": "Hyundai",
        "model": "Ioniq 5 Long Range AWD",
        "category": "Yeni Nesil Elektrikli Crossover",
        "plate": "34 HY 005",
        "source_address": 0x1B,
        "engine": "Çift Motor AWD Elektrik 325 HP",
        "max_speed": 185.0,
        "default_speed": 105.0,
        "current_speed": 105.0,
        "target_speed": 105.0,
        "acceleration_rate": 8.8,
        "throttle_pct": 19.0,
        "brake_pct": 0.0,
        "gear": "D",
        "battery_soc": 87.0,
        "battery_soh": 99.0,
        "image_url": "/static/images/cars/hyundai-ioniq-5.jpg",
        "status": "cruising",
        "simulation_mode": "cruise",
        "brake_pressed": False,
    },

    # 10. Fiat (SA: 0x1C, 0x1D, 0x1E)
    {
        "id": "fiat-egea-cross",
        "brand_id": "fiat",
        "brand_name": "Fiat",
        "model": "Egea Cross 1.5 Hibrit 130 HP",
        "category": "Crossover C Segment",
        "plate": "34 FT 150",
        "source_address": 0x1C,
        "engine": "1.5L FireFly Hibrit 130 HP",
        "max_speed": 200.0,
        "default_speed": 85.0,
        "current_speed": 85.0,
        "target_speed": 85.0,
        "acceleration_rate": 5.4,
        "throttle_pct": 17.0,
        "brake_pct": 0.0,
        "gear": "D4",
        "battery_soc": 90.0,
        "battery_soh": 98.0,
        "image_url": "/static/images/cars/fiat-egea-cross.jpg",
        "status": "cruising",
        "simulation_mode": "city",
        "brake_pressed": False,
    },
    {
        "id": "fiat-500e",
        "brand_id": "fiat",
        "brand_name": "Fiat",
        "model": "500e La Prima %100 Elektrikli",
        "category": "İkonik Şehir İçi EV",
        "plate": "34 FT 500",
        "source_address": 0x1D,
        "engine": "42 kWh Elektrik Motoru 118 HP",
        "max_speed": 150.0,
        "default_speed": 60.0,
        "current_speed": 60.0,
        "target_speed": 60.0,
        "acceleration_rate": 5.8,
        "throttle_pct": 14.0,
        "brake_pct": 0.0,
        "gear": "D",
        "battery_soc": 82.0,
        "battery_soh": 99.0,
        "image_url": "/static/images/cars/fiat-500e.jpg",
        "status": "cruising",
        "simulation_mode": "city",
        "brake_pressed": False,
    },
    {
        "id": "fiat-doblo-combi",
        "brand_id": "fiat",
        "brand_name": "Fiat",
        "model": "Doblo Combi 1.5 BlueHDi",
        "category": "Hafif Ticari & Aile Aracı",
        "plate": "34 FT 155",
        "source_address": 0x1E,
        "engine": "1.5L BlueHDi Dizel 130 HP",
        "max_speed": 184.0,
        "default_speed": 75.0,
        "current_speed": 75.0,
        "target_speed": 75.0,
        "acceleration_rate": 5.1,
        "throttle_pct": 16.0,
        "brake_pct": 0.0,
        "gear": "D3",
        "battery_soc": 95.0,
        "battery_soh": 97.0,
        "image_url": "/static/images/cars/fiat-doblo-combi.jpg",
        "status": "cruising",
        "simulation_mode": "city",
        "brake_pressed": False,
    },
]


import os
import json
import copy

CUSTOM_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
CUSTOM_DATA_FILE = os.path.join(CUSTOM_DATA_DIR, "custom_fleet.json")


def _ensure_custom_data_dir():
    os.makedirs(CUSTOM_DATA_DIR, exist_ok=True)


def _load_custom_fleet():
    """Disk'teki özel araçları, markaları ve görsel değişikliklerini yükler"""
    if not os.path.exists(CUSTOM_DATA_FILE):
        return

    try:
        with open(CUSTOM_DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        custom_brands = data.get("brands", [])
        for cb in custom_brands:
            if not any(b["id"] == cb["id"] for b in FLEET_BRANDS):
                FLEET_BRANDS.append(cb)

        custom_vehicles = data.get("vehicles", [])
        for cv in custom_vehicles:
            if not any(v["id"] == cv["id"] for v in VEHICLES):
                VEHICLES.append(cv)

        # Görsel güncellemelerini uygula
        image_overrides = data.get("image_overrides", {})
        for v in VEHICLES:
            if v["id"] in image_overrides:
                v["image_url"] = image_overrides[v["id"]]
    except Exception as e:
        print(f"Özel filo verisi yüklenirken hata: {e}")


def _save_custom_fleet():
    """Disk'e özel araçları, markaları ve görsel değişikliklerini kaydeder"""
    _ensure_custom_data_dir()
    try:
        # Standart 10 marka harici olanları kaydet
        default_brand_ids = {"bmw", "mercedes", "audi", "volkswagen", "toyota", "tesla", "ford", "renault", "hyundai", "fiat"}
        custom_brands = [b for b in FLEET_BRANDS if b["id"] not in default_brand_ids]

        # Standart 30 araç harici olanları kaydet
        default_vehicle_ids = {
            "bmw-320i", "bmw-520d", "bmw-m4-competition",
            "mb-c200", "mb-e300d", "mb-g63-amg",
            "audi-a3-sedan", "audi-a6-avant", "audi-rs6-avant",
            "vw-golf-8", "vw-passat-variant", "vw-tiguan-rline",
            "toyota-corolla-hybrid", "toyota-rav4-hybrid", "toyota-yaris-cross",
            "tesla-model-3-perf", "tesla-model-y-longrange", "tesla-model-s-plaid",
            "ford-focus-st", "ford-mustang-gt", "ford-ranger-raptor",
            "renault-clio-5", "renault-megane-etech", "renault-austral",
            "hyundai-i20-n", "hyundai-tucson-hybrid", "hyundai-ioniq-5",
            "fiat-egea-cross", "fiat-500e", "fiat-doblo-combi"
        }
        custom_vehicles = [v for v in VEHICLES if v["id"] not in default_vehicle_ids]

        # Tüm araçlar için özelleştirilmiş görsel URL'leri topla
        image_overrides = {}
        for v in VEHICLES:
            if v.get("image_url"):
                image_overrides[v["id"]] = v["image_url"]

        with open(CUSTOM_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "brands": custom_brands,
                "vehicles": custom_vehicles,
                "image_overrides": image_overrides
            }, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Özel filo verisi kaydedilirken hata: {e}")


def _normalize_vehicle_powertrain(v: Dict[str, Any]) -> None:
    """Aracın motor tipine göre (EV, Hibrit, Benzin/Dizel) batarya ve yakıt parametrelerini doğru yapılandırır"""
    v_id = v.get("id", "").lower()
    engine = v.get("engine", "")
    brand_id = v.get("brand_id", "").lower()
    pt = v.get("powertrain")

    ev_ids = {"tesla-model-3-perf", "tesla-model-y-longrange", "tesla-model-s-plaid", "renault-megane-etech", "hyundai-ioniq-5", "fiat-500e", "togg-t10x"}
    hybrid_ids = {"toyota-corolla-hybrid", "toyota-rav4-hybrid", "toyota-yaris-cross", "hyundai-tucson-hybrid", "fiat-egea-cross"}

    if pt == "ev" or v_id in ev_ids or "tesla" in brand_id or "etech" in v_id or "500e" in v_id or "ioniq" in v_id or "Elektrik" in engine:
        v["powertrain"] = "ev"
        v["is_ev"] = True
        v["fuel_level_pct"] = None
        if v.get("battery_soc") is None:
            v["battery_soc"] = 95.0
        if v.get("battery_soh") is None:
            v["battery_soh"] = 99.0
    elif pt == "hybrid" or v_id in hybrid_ids or "hybrid" in v_id or "hibrit" in engine.lower():
        v["powertrain"] = "hybrid"
        v["is_ev"] = False
        if v.get("battery_soc") is None:
            v["battery_soc"] = 65.0
        if v.get("battery_soh") is None:
            v["battery_soh"] = 98.0
        if v.get("fuel_level_pct") is None:
            v["fuel_level_pct"] = 82.0
        v["battery_12v"] = 14.1
    else:
        v["powertrain"] = "ice"
        v["is_ev"] = False
        v["battery_soc"] = None
        v["battery_soh"] = None
        if v.get("fuel_level_pct") is None:
            v["fuel_level_pct"] = 85.0
        v["battery_12v"] = 14.2


def update_vehicle_image_url(vehicle_id: str, new_image_url: str) -> bool:
    """Belirli bir aracın görsel URL'sini günceller ve kaydeder"""
    for v in VEHICLES:
        if v["id"] == vehicle_id:
            v["image_url"] = new_image_url
            _save_custom_fleet()
            return True
    return False


def get_all_vehicles() -> List[Dict[str, Any]]:
    """Tüm binek ve ticari araçların listesini döndürür"""
    for v in VEHICLES:
        _normalize_vehicle_powertrain(v)
    return VEHICLES


def get_vehicle_by_id(vehicle_id: str) -> Dict[str, Any]:
    """ID'ye göre araç döndürür"""
    for v in VEHICLES:
        if v["id"] == vehicle_id:
            _normalize_vehicle_powertrain(v)
            return v
    raise KeyError(f"Araç bulunamadı: {vehicle_id}")


def get_vehicles_by_brand(brand_id: str) -> List[Dict[str, Any]]:
    """Belirli bir markaya ait modelleri döndürür"""
    return [v for v in VEHICLES if v["brand_id"] == brand_id]


def get_next_available_source_address() -> int:
    """Kullanılmayan bir sonraki benzersiz J1939 Source Address (SA) döndürür"""
    used_sas = {v["source_address"] for v in VEHICLES}
    for candidate in range(0x01, 0xEE):
        if candidate not in used_sas:
            return candidate
    return 0xEE


def add_brand(brand_data: Dict[str, Any]) -> Dict[str, Any]:
    """Yeni bir marka ekler"""
    brand_id = brand_data["id"].lower().strip().replace(" ", "-")
    for b in FLEET_BRANDS:
        if b["id"] == brand_id:
            return b

    new_brand = {
        "id": brand_id,
        "name": brand_data.get("name", brand_id.upper()),
        "country": brand_data.get("country", "Global"),
        "color": brand_data.get("color", "#00D2FF"),
        "badge": brand_data.get("badge", brand_id[:4].upper()),
        "accent": f"rgba(0, 210, 255, 0.2)",
    }
    FLEET_BRANDS.append(new_brand)
    _save_custom_fleet()
    return new_brand


def add_vehicle(vehicle_data: Dict[str, Any]) -> Dict[str, Any]:
    """Filoya yeni bir araç ekler ve kalıcı kaydeder"""
    v_id = vehicle_data.get("id")
    if not v_id:
        brand_part = vehicle_data.get("brand_id", "car").lower().strip().replace(" ", "-")
        model_part = vehicle_data.get("model", "model").lower().strip().replace(" ", "-")
        v_id = f"{brand_part}-{model_part}"

    # Çakışma varsa benzersiz yap
    original_id = v_id
    counter = 1
    while any(v["id"] == v_id for v in VEHICLES):
        v_id = f"{original_id}-{counter}"
        counter += 1

    sa = vehicle_data.get("source_address")
    if sa is None or any(v["source_address"] == int(sa) for v in VEHICLES):
        sa = get_next_available_source_address()
    else:
        sa = int(sa)

    max_spd = float(vehicle_data.get("max_speed", 220.0))
    def_spd = float(vehicle_data.get("default_speed", 0.0))
    category = vehicle_data.get("category", "Binek")
    engine = vehicle_data.get("engine", "2.0L Turbo 200 HP")
    powertrain = vehicle_data.get("powertrain", "ice")
    is_ev = bool(vehicle_data.get("is_ev", False) or powertrain == "ev" or "EV" in category or "Elektrik" in engine or "tesla" in vehicle_data.get("brand_id", ""))

    new_vehicle = {
        "id": v_id,
        "brand_id": vehicle_data.get("brand_id", "custom").lower().strip(),
        "brand_name": vehicle_data.get("brand_name", "Özel Marka"),
        "model": vehicle_data.get("model", "Özel Model"),
        "category": category,
        "plate": vehicle_data.get("plate", "34 CUSTOM 001"),
        "source_address": sa,
        "engine": engine,
        "powertrain": "ev" if is_ev else powertrain,
        "is_ev": is_ev,
        "max_speed": max_spd,
        "default_speed": def_spd,
        "current_speed": def_spd,
        "target_speed": def_spd,
        "acceleration_rate": float(vehicle_data.get("acceleration_rate", 6.0)),
        "throttle_pct": 0.0,
        "brake_pct": 0.0,
        "gear": "P" if def_spd == 0 else ("D" if is_ev else "D1"),
        "battery_soc": float(vehicle_data.get("battery_soc", 95.0)),
        "battery_soh": float(vehicle_data.get("battery_soh", 99.0)),
        "image_url": vehicle_data.get("image_url", f"/static/images/cars/{v_id}.jpg"),
        "status": "stopped" if def_spd == 0 else "cruising",
        "simulation_mode": "manual",
        "brake_pressed": False,
    }

    VEHICLES.append(new_vehicle)
    _save_custom_fleet()
    return new_vehicle


def delete_vehicle(vehicle_id: str) -> bool:
    """Filodan bir aracı siler"""
    global VEHICLES
    initial_len = len(VEHICLES)
    VEHICLES = [v for v in VEHICLES if v["id"] != vehicle_id]
    if len(VEHICLES) < initial_len:
        _save_custom_fleet()
        return True
    return False


# Başlangıçta kaydedilmiş özel araçları yükle
_load_custom_fleet()
