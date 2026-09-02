# 🚛 SAE J1939 Araç Hız Sinyali ve Web Telemetri Platformu

Bu proje, piyasadaki **10 büyük ticari/ağır vasıta ve otomotiv markasından 3'er model (toplam 30 araç)** için **SAE J1939 standardında 29-bit CAN mesajları** ile hız sinyali (`PGN 65265 - CCVS`, `SPN 84 - Wheel-Based Vehicle Speed`) üreten, araçlara anlık hız verilebilen, web arayüzünde canlı kadran ve CAN sniffer ile izlenebilen, **Docker** ve **GitHub Actions** ile güçlendirilmiş profesyonel bir telemetri sistemidir.

---

## 📌 1. Temel Özellikler

- **SAE J1939 29-Bit Extended CAN Protokolü:**
  - **PGN 65265 (`0xFEF1` - CCVS):** Cruise Control / Vehicle Speed standart mesaj grubu.
  - **SPN 84 (Wheel-Based Vehicle Speed):** `1/256 km/h / bit` (= `0.00390625 km/h`) yüksek çözünürlük, 0 - 250.996 km/h hız aralığı.
  - **29-Bit Arbitration ID:** Öncelik (Priority: 6), PGN (0xFEF1), ve her araca özel Kaynak Adresi (Source Address - SA: `0x01` .. `0x1E`).
- **10 Marka x 3 Model = 30 Araçlık Gerçekçi Filo:**
  - Mercedes-Benz, Scania, Volvo, MAN, DAF, Iveco, Ford Trucks, Renault Trucks, Isuzu ve BMC.
- **Dinamik Web Arayüzü (Cockpit & Sniffer):**
  - **HTML5 Canvas Analog & Dijital Hız Göstergesi (Speedometer):** Akıcı ibre fiziği ve neon aydınlatma.
  - **Araç Bazlı ve Filo Geneli Hız Kontrolleri:** Slider, 0-130 km/h hazır butonlar, Gaz & Fren pedalları.
  - **Filo Sürüş Senaryoları:** Otoyol akışı, Şehir içi dur-kalk, Konvoy modu, 0-100 testi, Acil durdurma (All Stop).
  - **Canlı J1939 CAN Sniffer / Terminal:** 29-bit CAN ID, PGN, SA, 8-bayt Hex dökümü (SPN 84 bayt vurgusu), CSV formatında dışa aktarma.
  - **Bit Düzeyinde Frame Inspector:** CAN ID ve bayt yükünü adım adım açıklayan görsel analizör.
- **Docker & Docker Compose Desteği:** Tek komutla konteynerize çalıştırma.
- **GitHub Actions CI/CD Pipeline:** Python test matrisi (3.10, 3.11, 3.12), Flake8 linting ve Docker build doğrulama.

---

## 📊 2. SAE J1939 Hız Sinyal Matrisi

### 29-Bit CAN Arbitration ID Yapısı
```text
┌──────────────┬──────────────┬──────────────┬────────────────────────┬──────────────────────┐
│ Priority (3) │ Res / EDP(1) │ Data Page(1) │  PDU Format - PF (8)   │ PDU Specific - PS(8) │ Source Address (8)   │
│   Bits 28-26 │    Bit 25    │    Bit 24    │       Bits 23-16       │      Bits 15-8       │     Bits 7-0         │
├──────────────┼──────────────┼──────────────┼────────────────────────┴──────────────────────┼──────────────────────┤
│  0b110 (6)   │      0       │      0       │           0xFE (254)   │      0xF1 (241)       │ 0x01 .. 0x1E (1..30) │
└──────────────┴──────────────┴──────────────┴───────────────────────────────────────────────┴──────────────────────┘
                                             └──────────── PGN: 65265 (0xFEF1) ─────────────┘
Örnek CAN ID: 0x18FEF101 (Priority: 6, PGN: 0xFEF1, SA: 0x01 -> Mercedes Actros)
```

### 8-Bayt CCVS Veri Paketi Yükü (Data Payload)
| Bayt Sırası | Sinyal Adı | Çözünürlük / Format | Açıklama |
| :--- | :--- | :--- | :--- |
| **Byte 0** | Status Flags | 2-bit flagler | El Freni, Cruise Control durumu |
| **Byte 1 (LSB)** | **SPN 84 Hız (Düşük)** | `1/256 km/h / bit` | Ham değerin düşük 8 biti (`Raw & 0xFF`) |
| **Byte 2 (MSB)** | **SPN 84 Hız (Yüksek)** | `1/256 km/h / bit` | Ham değerin yüksek 8 biti (`(Raw >> 8) & 0xFF`) |
| **Byte 3** | Cruise Set Speed | 1 km/h / bit | `0xFF` (Mevcut değil) |
| **Byte 4** | Brake / Clutch Status| 2-bit flagler | Fren pedalı ve debriyaj durumu |
| **Byte 5..7**| Reserved | 0xFF | J1939 standardı dolgu baytları |

> **SPN 84 Hız Formülü:** `Hız (km/h) = ((Byte[2] << 8) | Byte[1]) * 0.00390625`

---

## 🚛 3. 10 Marka & 30 Model Filo Listesi

| # | Marka | Model | Kategori | J1939 SA (Hex) | Motor / Güç |
|---|:---|:---|:---|:---:|:---|
| 1 | **Mercedes-Benz** | Actros 1851 GigaSpace | Uzun Yol Çekici | `0x01` | OM471 12.8L 510 HP |
| 2 | **Mercedes-Benz** | Arocs 3353 6x4 | Şantiye / Damper | `0x02` | OM473 15.6L 530 HP |
| 3 | **Mercedes-Benz** | Atego 1518 Distribution | Şehir İçi Dağıtım | `0x03` | OM934 5.1L 177 HP |
| 4 | **Scania** | 770 S V8 Highline | King of the Road | `0x04` | DC16 16.4L V8 770 HP |
| 5 | **Scania** | R 500 Super 4x2 | Filo Çekici | `0x05` | DC13 Super 13.0L 500 HP |
| 6 | **Scania** | G 410 XT Construction | Ağır İnşaat | `0x06` | DC13 12.7L 410 HP |
| 7 | **Volvo Trucks** | FH16 750 Globetrotter XXL | Ağır Yük Çekici | `0x07` | D16K 16.1L 750 HP |
| 8 | **Volvo Trucks** | FM 460 Globetrotter | Bölgesel Lojistik | `0x08` | D13K 12.8L 460 HP |
| 9 | **Volvo Trucks** | FMX 500 8x4 Heavy Duty | Maden Damperli | `0x09` | D13K 12.8L 500 HP |
| 10 | **MAN Truck & Bus** | TGX 18.640 Lion S | Premium Uzun Yol | `0x0A` | D3876 15.2L 640 HP |
| 11 | **MAN Truck & Bus** | TGS 33.510 6x6 HydroDrive | Şantiye & Arazi | `0x0B` | D2676 12.4L 510 HP |
| 12 | **MAN Truck & Bus** | TGM 18.290 Distribution | Orta Tonaj Kamyon | `0x0C` | D0836 6.9L 290 HP |
| 13 | **DAF Trucks** | XG+ 530 FT Next Gen | Geniş Kabin Çekici | `0x0D` | PACCAR MX-13 530 HP |
| 14 | **DAF Trucks** | XF 480 FT Pure Excellence | Uluslararası Nakliye | `0x0E` | PACCAR MX-13 480 HP |
| 15 | **DAF Trucks** | CF 450 FAN Rigid | Belediye / Dağıtım | `0x0F` | PACCAR MX-11 450 HP |
| 16 | **Iveco** | S-Way 570 Cursor 13 | Yeni Nesil Çekici | `0x10` | Cursor 13 12.9L 570 HP |
| 17 | **Iveco** | Eurocargo 160E28 | Dağıtım & Kargo | `0x11` | Tector 7 6.7L 280 HP |
| 18 | **Iveco** | T-Way 510 Heavy Off-Road | Maden & Taş Ocağı | `0x12` | Cursor 13 12.9L 510 HP |
| 19 | **Ford Trucks** | F-MAX 500 Ecotorq | IToY Ödüllü Çekici | `0x13` | Ecotorq 12.7L 500 HP |
| 20 | **Ford Trucks** | Cargo 1842T Tractor | Ağır Ticari Çekici | `0x14` | Ecotorq 12.7L 420 HP |
| 21 | **Ford Trucks** | F-Line 1833 Yol Serisi | Yeni Nesil Yol | `0x15` | Ecotorq 9.0L 330 HP |
| 22 | **Renault Trucks** | T-High 520 Sleeper Cab | Uzun Yol Çekici | `0x16` | DE13 12.8L 520 HP |
| 23 | **Renault Trucks** | C-Series 460 Construction | Şantiye & Nakliye | `0x17` | DE11 10.8L 460 HP |
| 24 | **Renault Trucks** | K-Series 480 Xtrem | Ağır Şantiye | `0x18` | DE13 12.8L 480 HP |
| 25 | **Isuzu** | NPR 10 Long Şasi | Şehir İçi Lojistik | `0x19` | 4HK1-TCN 5.2L 190 HP |
| 26 | **Isuzu** | Giga CXZ 460 Heavy | Ağır Ticari Çekici | `0x1A` | 6UZ1-TCC 9.8L 460 HP |
| 27 | **Isuzu** | Forward FVR 240 | Orta Kargo Kamyon | `0x1B` | 6HK1-TCS 7.8L 240 HP |
| 28 | **BMC Otomotiv** | TUĞRA 1846 TGR | Yerli Uzun Yol Çekici| `0x1C` | FPT Cursor 11 460 HP |
| 29 | **BMC Otomotiv** | PRO 1144 8x4 Damperli | Ağır Maden Kamyonu | `0x1D` | Cummins ISL 8.9L 400 HP |
| 30 | **BMC Otomotiv** | NEOCITY 8.5m VIP | Şehir İçi Otobüs | `0x1E` | Cummins ISB4.5 210 HP |

---

## 🚀 4. Çalıştırma Yöntemleri

### Yöntem A: Doğrudan Python ile Çalıştırma (En Kolay)

1. **Gereksinimleri Yükleyin:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Sunucuyu Başlatın:**
   ```bash
   python server.py
   ```

3. **Tarayıcınızı Açın:**
   👉 `http://localhost:8000`

---

### Yöntem B: Docker & Docker Compose ile Çalıştırma

Tek komutla izole konteyner ortamında ayağa kaldırmak için:

```bash
docker compose up --build
```

Konteyner ayağa kalktığında `http://localhost:8000` üzerinden web paneline erişebilirsiniz.

---

## 🧪 5. Testleri Çalıştırma (Pytest & Lint)

Tüm J1939 kodlayıcı/çözücü testlerini, 30 araçlık filo doğrulamalarını ve REST/WebSocket API testlerini çalıştırmak için:

```bash
pytest tests/ -v
```

Kod stil ve standart kontrolü için:
```bash
flake8 . --count --statistics
```

---

## 🌐 6. REST API & WebSocket Endpoint'leri

- `GET /` : Canlı Cockpit & CAN Sniffer Web Arayüzü
- `GET /api/fleet` : 30 Aracın canlı telemetri ve J1939 durumları
- `GET /api/brands` : 10 Marka meta verileri ve renkleri
- `GET /api/vehicle/{vehicle_id}` : Tek bir aracın anlık hız ve CAN durumu
- `POST /api/vehicle/{vehicle_id}/speed` : Araca özel hız verme (`{"speed": 85.0}`)
- `POST /api/vehicle/{vehicle_id}/brake` : Araca fren uygulama (`{"pressed": true}`)
- `POST /api/fleet/speed` : Tüm filoya ortak hız atama (`{"speed": 90.0}`)
- `POST /api/fleet/scenario` : Filo senaryosu uygulama (`{"scenario": "highway" | "city" | "convoy" | "drag_race" | "idle"}`)
- `POST /api/fleet/emergency-stop` : Tüm araçları acil durdurma
- `GET /api/can/history` : Son 300 CAN mesajının geçmişi
- `GET /api/health` : Sağlık kontrolü
- `WS /ws/telemetry` : 10 Hz çift yönlü canlı telemetri ve kontrol soketi

---

## 📁 7. Proje Dosya Ağacı

```text
pcan-can-bus/
├── .github/
│   └── workflows/
│       └── ci.yml                 # GitHub Actions CI/CD Pipeline
├── j1939/
│   ├── __init__.py
│   ├── protocol.py                # SAE J1939 29-bit CAN ID ve SPN 84 CCVS Kodlayıcı/Çözücü
│   ├── fleet_data.py              # 10 Marka x 3 Model (30 Araç) Veri Seti
│   └── simulator.py               # Fizik ve Sinyal Üretim Motoru
├── web/
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css          # Cyber Automotive Tasarım Sistemi
│   │   └── js/
│   │       ├── gauge.js           # HTML5 Canvas Hız Göstergesi (Speedometer)
│   │       └── app.js             # WebSocket ve Canlı UI Mantığı
│   └── templates/
│       └── index.html             # Ana Gösterge Paneli ve CAN Sniffer
├── tests/
│   ├── test_j1939_protocol.py     # J1939 Protokol ve SPN 84 Birim Testleri
│   ├── test_fleet.py              # 30 Araçlık Filo Bütünlük Testleri
│   ├── test_api.py                # REST & WebSocket API Testleri
│   └── test_can_signals.py        # Eski CAN Sinyal Testleri
├── can_bridge.py                  # Python-CAN Donanım / Sanal Bus Köprüsü
├── server.py                      # FastAPI + Uvicorn + WebSocket Sunucusu
├── Dockerfile                     # Docker Konteyner Yapılandırması
├── docker-compose.yml             # Docker Compose Yapılandırması
├── .dockerignore
├── requirements.txt               # Bağımlılıklar
└── README.md                      # Dokümantasyon
```
