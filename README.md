# 🚗 SAE J1939 Araç Hız Sinyali ve Ayrık Web Telemetri Platformu

Bu proje; piyasadaki **10 popüler binek, SUV ve elektrikli otomotiv markasından 3'er model (toplam 30 araç)** için **SAE J1939 standardında 29-bit CAN mesajları** ile hız sinyali (`PGN 65265 - CCVS`, `SPN 84 - Wheel-Based Vehicle Speed`) üreten, hız verme ortamı (**Sinyal Gönderici / Transmitter**) ile izleme ortamının (**Web Telemetri / Dashboard**) birbirinden tamamen ayrıldığı profesyonel bir telemetri sistemidir.

---

## 🏗️ 1. İki Ayrık Bağımsız Ortam Mimarisi

Sistem birbirini gerçek zamanlı CAN bus ve WebSocket üzerinden senkronize eden iki ayrı ortamdan oluşur:

| Ortam | Erişim / Çalıştırma | Açıklama |
| :--- | :--- | :--- |
| 🕹️ **Ortam 1: Hız Verme & Sinyal Gönderici** | **Web:** `http://localhost:8000/control`<br>**CLI:** `python j1939_sender.py` | 30 araçtan birini seçip gaz/fren/slider ile hız verme ve J1939 CAN paketlerini hatta basma paneli. |
| 📺 **Ortam 2: Canlı Web İzleme & Gösterge** | **Web:** `http://localhost:8000/` | Büyük analog/dijital hız göstergesi (Speedometer), 30 aracın anlık hız durumları ve canlı J1939 CAN Sniffer ekranı. |

---

## 🚗 2. 10 Popüler Otomobil Markası & 30 Model Filosu

| # | Marka | Model | Kategori | J1939 SA (Hex) | Motor / Güç | Maks Hız |
|---|:---|:---|:---|:---:|:---|:---:|
| 1 | **BMW** | 320i Sedan M Sport | Premium Sedan | `0x01` | 2.0L TwinPower Turbo 170 HP | 235 km/h |
| 2 | **BMW** | 520d Sedan xDrive | Executive Sedan | `0x02` | 2.0L Mild-Hybrid Dizel 197 HP | 240 km/h |
| 3 | **BMW** | M4 Competition Coupe | Super Sport | `0x03` | 3.0L M Biturbo 510 HP | 250 km/h |
| 4 | **Mercedes-Benz** | C200 4MATIC AMG | Premium Sedan | `0x04` | 1.5L Turbo EQ Boost 204 HP | 241 km/h |
| 5 | **Mercedes-Benz** | E300d 4MATIC Exclusive| Luxury Sedan | `0x05` | 2.0L Turbo Dizel 265 HP | 250 km/h |
| 6 | **Mercedes-Benz** | G63 AMG 4x4 | Ultra Luxury SUV | `0x06` | 4.0L V8 Biturbo 585 HP | 240 km/h |
| 7 | **Audi** | A3 Sedan 35 TFSI | Compact Luxury | `0x07` | 1.5L Mild-Hybrid 150 HP | 224 km/h |
| 8 | **Audi** | A6 Avant 40 TDI | Executive Wagon | `0x08` | 2.0L TDI Ultra 204 HP | 246 km/h |
| 9 | **Audi** | RS6 Avant Performance | Super Sport Wagon | `0x09` | 4.0L V8 Biturbo 630 HP | 250 km/h |
| 10 | **Volkswagen** | Golf 8 1.5 eTSI R-Line | Hatchback | `0x0A` | 1.5L eTSI 150 HP | 224 km/h |
| 11 | **Volkswagen** | Passat Variant 2.0 TDI | Station Wagon | `0x0B` | 2.0L TDI 193 HP | 232 km/h |
| 12 | **Volkswagen** | Tiguan 1.5 eTSI R-Line | C-SUV | `0x0C` | 1.5L eTSI 150 HP | 210 km/h |
| 13 | **Toyota** | Corolla 1.8 Hybrid | Sedan Hybrid | `0x0D` | 1.8L Kendi Şarj Eden Hibrit 140 HP | 180 km/h |
| 14 | **Toyota** | RAV4 2.5 Hybrid AWD-i | D-SUV Hybrid | `0x0E` | 2.5L Dynamic Force 222 HP | 190 km/h |
| 15 | **Toyota** | Yaris Cross 1.5 Hybrid | B-SUV Urban | `0x0F` | 1.5L Hybrid 116 HP | 170 km/h |
| 16 | **Tesla** | Model 3 Performance | EV Sedan | `0x10` | Dual Motor AWD Elektrik 510 HP | 250 km/h |
| 17 | **Tesla** | Model Y Long Range AWD | EV SUV | `0x11` | Dual Motor AWD Elektrik 384 HP | 217 km/h |
| 18 | **Tesla** | Model S Plaid | Hyper EV Sedan | `0x12` | Tri-Motor AWD Elektrik 1020 HP | 250 km/h |
| 19 | **Ford** | Focus ST 2.3 EcoBoost | Hot Hatch | `0x13` | 2.3L EcoBoost 280 HP | 250 km/h |
| 20 | **Ford** | Mustang GT 5.0 V8 | Muscle Car | `0x14` | 5.0L Coyote V8 450 HP | 250 km/h |
| 21 | **Ford** | Ranger Raptor 3.0 V6 | Performans Pick-up | `0x15` | 3.0L EcoBoost V6 292 HP | 180 km/h |
| 22 | **Renault** | Clio 5 1.0 TCe | B Hatchback | `0x16` | 1.0L Turbo 90 HP | 180 km/h |
| 23 | **Renault** | Megane E-Tech EV60 | C-Crossover EV | `0x17` | Elektrik Motoru 220 HP | 160 km/h |
| 24 | **Renault** | Austral 1.2 E-Tech | C-SUV Hybrid | `0x18` | 1.2L Full Hybrid 200 HP | 175 km/h |
| 25 | **Hyundai** | i20 N 1.6 T-GDI | Hot Hatch | `0x19` | 1.6L Turbo 204 HP | 230 km/h |
| 26 | **Hyundai** | Tucson 1.6 T-GDI Hybrid| C-SUV | `0x1A` | 1.6L Hibrit AWD 230 HP | 193 km/h |
| 27 | **Hyundai** | Ioniq 5 Long Range AWD | Yeni Nesil EV | `0x1B` | Çift Motor AWD 325 HP | 185 km/h |
| 28 | **Fiat** | Egea Cross 1.5 Hibrit | Crossover | `0x1C` | 1.5L FireFly Hibrit 130 HP | 200 km/h |
| 29 | **Fiat** | 500e La Prima | Şehir İçi EV | `0x1D` | 42 kWh Elektrik 118 HP | 150 km/h |
| 30 | **Fiat** | Doblo Combi 1.5 BlueHDi| Aile & Ticari | `0x1E` | 1.5L Dizel 130 HP | 184 km/h |

---

## 📊 3. SAE J1939 Protokol Özellikleri

- **PGN 65265 (`0xFEF1` - CCVS):** Cruise Control / Vehicle Speed.
- **SPN 84 (Wheel-Based Vehicle Speed):** `1/256 km/h / bit` (= `0.00390625 km/h`) çözünürlük.
- **29-Bit CAN ID Hesaplama:** `(Priority << 26) | (PGN << 8) | SourceAddress`
  - Örnek: `BMW 320i` (SA: `0x01`) için CAN ID = `0x18FEF101`
  - Örnek: `Tesla Model 3` (SA: `0x10`) için CAN ID = `0x18FEF110`

---

## 🚀 4. Nasıl Çalıştırılır?

### Adım 1: Sunucuyu Başlatın
```powershell
python server.py
```

### Adım 2: İki Ayrı Sekmede/Ekranda Açın
- 🕹️ **Hız Verme Ortamı (Gönderici):** 👉 [**http://localhost:8000/control**](http://localhost:8000/control)
- 📺 **İzleme Ortamı (Alıcı):** 👉 [**http://localhost:8000/**](http://localhost:8000/)

*(Hız verme panelinden herhangi bir araca hız verdiğinizde, izleme ekranındaki kadranın ve CAN paketlerinin eş zamanlı olarak yükseldiğini göreceksiniz.)*

### Alternatif: Terminalden Hız Sinyali Gönderme (CLI)
Sunucu açıkken yeni bir terminal penceresinde:
```powershell
python j1939_sender.py
```

---

## 🧪 5. Testleri Çalıştırma
```powershell
pytest tests/ -v
```
