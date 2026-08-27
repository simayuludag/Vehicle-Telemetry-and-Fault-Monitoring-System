# 📓 Günlük Gelişim ve Çalışma Notları

Bu depoda; araç sistemleri, yazılım mimarisi, versiyon kontrol süreçleri ve günlük tamamlanan teknik görevlere dair özet notlar yer almaktadır.

---

## 📅 Day 1 — Araştırma, Kurulum ve Temel Kavramlar

### 🔍 1. Araştırılan Konular

* **Araç Temel Alt Sistemleri:** 
  * Güç Grubu (Powertrain), Güç Aktarma (Drivetrain), Şasi ve Yürür Aksam, E/E Mimarisi ve Gövde/Konfor sistemleri.
* **Elektronik Kontrol Üniteleri (ECU):** 
  * Mikrodenetleyici yapısı, sensör verisi işleme ve aktüatör yönetimi.
* **Yazılım Katmanları & Mimari:** 
  * **Frontend:** İstemci tarafı kullanıcı arayüzü ve deneyimi (HTML/CSS/JS).
  * **Backend:** Sunucu tarafı iş mantığı ve yetkilendirme.
  * **Veri Tabanı:** SQL ve NoSQL tabanlı veri saklama/sorgulama altyapısı.
  * **API:** İstemci ile sunucu arasındaki veri köprüsü ve uç noktalar (Endpoints).
* **Versiyon Kontrol & İş Birliği:** 
  * **Git vs. GitHub:** Dağıtık versiyon kontrol aracı ile bulut tabanlı iş birliği platformu farkları.
  * **Temel Kavramlar:** Repository, Commit, Branch, Pull Request (PR) mantığı ve yaşam döngüsü.

---

### ✅ 2. Tamamlanan Görevler & Yapılanlar

- [x] **Git Ortam Kurulumu:** Yerel makinede Git konfigürasyonu (`user.name`, `user.email`) ve SSH anahtarı / güvenli kimlik doğrulama adımları tamamlandı.
- [x] **İlk Depo (Repository):** Yerel çalışma alanı oluşturuldu ve GitHub uzak deposu (`remote origin`) bağlandı.
- [x] **README.md Oluşturma:** Proje dökümantasyonu hazırlandı.
- [x] **GitHub Profil Özelleştirmesi:** 
  * Kısa biyografi, teknik yetkinlikler ve iletişim bilgileri eklendi.
  * Kişisel GitHub Profile README sayfası oluşturuldu.
- [x] **Git & GitHub Pratiği:** 
  * İlk Issue açıldı.
  * Yeni bir çalışma dalı (`branch`) oluşturuldu.
  * Değişiklikler paketlenip kaydedildi (`commit`).
  * İlk Pull Request (PR) açıldı ve incelendi.

## 📅 Day 2: VehicleState Veri Modeli, Alanlar Arası Tutarlılık ve Doğrulama Mekanizmaları

Day 2 kapsamında, araç telemetri simülatörünün temel durum yapısını oluşturan `VehicleState` veri modeli, sinyal doğrulama (validation) kuralları, sayısal güvenlik katmanı ve otomatik birim testleri (unit tests) geliştirildi.

---

### 1. Geliştirilen Modüller ve Mimari Yapı

* **`src/vehicle_simulator/constants.py`**: Fiziksel sınırlar, başlangıç değerleri ve operasyonel limitler (`MIN/MAX_SPEED_KPH`, `MIN/MAX_ENGINE_RPM`, `MIN/MAX_COOLANT_TEMP_C`, `MIN/MAX_PERCENTAGE`) merkezi bir sabit dosyasında toplandı.
* **`src/vehicle_simulator/validation.py`**: Sayısal güvenlik kontrolleri (`_ensure_finite`) ve sinyal doğrulama fonksiyonları (`validate_speed`, `validate_rpm`, `validate_temperature`, `validate_percentage`) modüler olarak yazıldı.
* **`src/vehicle_simulator/vehicle_state.py`**: `@dataclass` yapısı kullanılarak tip korumalı (`Type Hints`), mantıklı varsayılan değerlere sahip ve `__post_init__` ile otomatik doğrulama yapan araç durum modeli oluşturuldu.

---

### 2. Alanlar Arası Tutarlılık Kuralları (Cross-Field Invariants)

Yalnızca tekil sınır kontrolleriyle yetinilmeyip alanlar arası fiziksel ve elektriksel tutarlılık kuralları uygulandı:

1. **Kontak - Motor İlişkisi**: Kontak kapalıyken (`ignition_on=False`) motor çalışamaz (`engine_running=True` olamaz).
2. **Motor - Devir İlişkisi**: Motor çalışmıyorken (`engine_running=False`) krank mili devri $0\text{ RPM}$ olmalıdır (`engine_rpm > 0` olamaz).

---

### 3. Sayısal Güvenlik ve IEEE 754 Koruması (`math.isfinite()`)

`NaN` (Not a Number), `inf` ve `-inf` gibi özel kayan noktalı sayıların normal karşılaştırma operatörlerini (`<`, `>`) sessizce `False` üreterek aşmasını engellemek adına `math.isfinite()` kontrolü eklendi. Sisteme giren her sayısal sinyalin reel ve sonlu bir değer olduğu garanti altına alındı.

---

### 4. Manuel Senaryo Test Kayıtları

| Senaryo | Parametreler | Sonuç | Durum / Hata Detayı |
|---|---|---|---|
| **Senaryo 1 — Park Hali** | `ignition=False`, `running=False`, `speed=0`, `rpm=0` | **Kabul Edildi** | Tüm değerler durağan başlangıç sınırları içerisinde. |
| **Senaryo 2 — Rölanti** | `ignition=True`, `running=True`, `speed=0`, `rpm=800` | **Kabul Edildi** | Kontak açıkken motor rölanti devrinde stabil. |
| **Senaryo 3 — Seyir Hali** | `ignition=True`, `running=True`, `speed=50`, `rpm=2200`, `throttle=30%` | **Kabul Edildi** | Normal sürüş dinamikleri geçerli sınırlar içinde. |
| **Senaryo 4 — Negatif Hız** | `speed_kph = -10.0` | **Reddedildi** | `ValueError: Geçersiz hız değeri` yakalandı. |
| **Senaryo 5 — Geçersiz Pedal** | `throttle_percent = 120.0` | **Reddedildi** | `ValueError: Geçersiz throttle_percent değeri` yakalandı. |
| **Senaryo 6 — Tutarsız Motor** | `ignition=True`, `running=False`, `rpm=2000` | **Reddedildi** | `ValueError: Motor çalışmıyorken motor devri 2000 RPM olamaz` yakalandı. |

---

### 5. Otomatik Birim Testleri (pytest)

`tests/test_vehicle_state.py` modülünde **Arrange–Act–Assert (AAA)** deseni ve **Sınır Değer Analizi (Boundary Value Testing: $Min-\epsilon, Min, Nominal, Max, Max+\epsilon$)** prensipleriyle toplam **17 adet** birim testi geliştirildi:

* Varsayılan ve geçerli özel durumların doğrulanması
* Hız, devir ve sıcaklık sınır değer testleri
* Negatif ve $\%100$ üzeri pedal girdilerinin yakalanması
* Tip güvenliği (`TypeError`) doğrulamaları
* Sonradan durum bozulması (`post-modification`) kontrolleri
* `NaN`, `+inf`, `-inf` parametre testleri (`@pytest.mark.parametrize`)

```bash
# Test çalıştırma komutu:
python -m pytest -v

# Çıktı:
# ======================== 17 passed in 0.07s =========================
```
## Day 3: Araç & ECU Mimarisi ve Sinyal Spesifikasyonu

Bu aşamada araç içi gömülü yazılım ve ağ mimarisinin temelleri çalışılmış, sistem mimarisi modellenmiş ve 8 temel CAN sinyali için test edilebilir spesifikasyonlar oluşturulmuştur.

### 1. Öğrenilen Temel Kavramlar
* **ECU, Sensör ve Aktüatör İlişkisi:** Sensörlerden alınan analog/dijital verilerin ECU'lar (mikrodenetleyiciler) tarafından işlenmesi ve aktüatörler üzerinden fiziksel çıktılara dönüştürülmesi.
* **Çoklu ECU Mimarisi:** Kablo karmaşasını azaltma, işlem yükünü dağıtma ve ISO 26262 fonksiyonel güvenlik izolasyonu sağlama prensipleri.
* **Raw vs. Physical Değer:** CAN hattından geçen ham verinin (raw) doğrusal ölçekleme formülü (`Fiziksel = Raw * Factor + Offset`) ile gerçek dünya büyüklüğüne dönüştürülmesi.
* **Periyodik Mesaj, Cycle Time ve Timeout:** Veri değişim hızına göre periyot belirleme ve 3-5 katı sürede veri gelmediğinde tetiklenen Fail-Safe (güvenli durum) mekanizmaları.
* **Test Edilebilir Gereksinimler:** HIL/SIL ortamlarında doğrulanabilir, girdi-çıktı ve zamanlama kriterleri net tanımlanmış yazılım gereksinimleri.

---

### 2. Araç Sistem Mimarisi

* **Powertrain (EMS):** Gaz pedalı, krank mili ve soğutma suyu sensörlerini işleyerek enjektör, ateşleme ve gaz kelebeğini kontrol eder; `EngineSpeed`, `AcceleratorPedalPos`, `EngineCoolantTemp` sinyallerini yayınlar.
* **ABS / ESC:** Tekerlek hız ve fren basınç sensörlerini izleyerek hidrolik valfleri ve pompayı yönetir; `VehicleSpeed`, `BrakePedalStatus` sinyallerini yayınlar.
* **BCM (Gövde Kontrol):** Far, kapı kilit ve yakıt seviyesi verilerini yönetir; `FuelLevel`, `LowBeamStatus`, `DoorOpenStatus` sinyallerini yayınlar.
* **Gösterge Paneli (Cluster):** CAN hattındaki tüm sinyalleri dinleyen salt alıcı (Consumer) birim olarak sürücüye görselleştirme sağlar.

---

### 3. Tanımlanan Sinyaller Özeti (`docs/signals.md`)

| # | Sinyal İsmi | Kaynak ECU | Veri Tipi | Birim | Aralık | Periyot / Timeout | Fail-Safe & Hata Davranışı |
|---|---|---|---|---|---|---|---|
| 1 | `EngineSpeed` | Powertrain | `uint16` (Raw * 0.25) | rpm | 0 - 8000 | 10 ms / 50 ms | SNA (`0xFFFF`): Hata bayrağı, Timeout: İbre 0, MIL lambası. |
| 2 | `VehicleSpeed` | ABS / ESC | `uint16` (Raw * 0.05625) | km/h | 0 - 250 | 20 ms / 100 ms | SNA (`0xFFFF`): ESC devre dışı, Timeout: Hız ekranı `---`. |
| 3 | `BrakePedalStatus` | ABS / ESC | `uint8` (Enum) | - | 0 - 2 | 20 ms / 100 ms | SNA / Timeout: Cruise Control iptal, fren lambası açık. |
| 4 | `AcceleratorPedalPos` | Powertrain | `uint8` (Raw * 0.4) | % | 0 - 100 | 10 ms / 50 ms | SNA (`0xFF`) / Timeout: Limp-Home modu, gaz %0 (rölanti). |
| 5 | `EngineCoolantTemp` | Powertrain | `uint8` (Raw - 40) | °C | -40 - 150 | 100 ms / 500 ms | SNA / Timeout: Radyatör fanı %100 açık tutulur. |
| 6 | `FuelLevel` | BCM | `uint8` (Raw * 0.5) | % | 0 - 100 | 500 ms / 2000 ms | SNA / Timeout: Yakıt ikaz lambası aktif, ibre minimumda. |
| 7 | `LowBeamStatus` | BCM | `uint8` (Enum) | - | 0 - 2 | 100 ms / 500 ms | SNA / Timeout: Farlar fail-safe olarak açık tutulur. |
| 8 | `DoorOpenStatus` | BCM | `uint8` (Bitmask) | - | 0 - 15 | 100 ms / 500 ms | SNA: Kapı alarmı, Timeout: "Kapı Bilgisi Alınamıyor" uyarısı. |

---

### 4. Teslim Edilen Dokümanlar
* `docs/signals.md`: Sinyal detayları, formüller, bit seviyesi gösterimler ve timeout kuralları.
* Sistem Mimarisi & Veri Akış Şeması.
* Test edilebilir yazılım gereksinimleri (SRS - REQ-SIG-001 ... REQ-SIG-004).
## Day 4 — Araç State Machine & Deterministik Sürüş Simülasyonu

### 🎯 Amaç ve Kazanımlar
Rastgele veri üretimi yerine matematiksel ve kural tabanlı deterministik araç davranışları oluşturmak.
- **State Machine (FSM):** Sonlu durum makineleri ve durum yaşam döngüsü.
- **Guard Conditions & Actions:** Güvenli geçiş koşulları, `Entry` ve `Exit` eylemleri.
- **Deterministik Simülasyon:** Periyodik çalışma (10 Hz / $100\text{ ms}$) ve tekrarlanabilir fizik döngüsü.
- **Senaryo Tabanlı Girdi:** YAML formatında zaman damgalı sürüş senaryoları.

---

### 🔄 Araç Durum Şeması (State Lifecycle)

| Durum (State) | Açıklama | Tetikleyici / Guard Şartı | Hedef Durum |
|---|---|---|---|
| **OFF** | Araç kapalı | Kontak açıldı (`ignition == True`) | `IGNITION_ON` |
| **IGNITION_ON** | Elektrik aktif, motor kapalı | Marş basıldı & Fren $\ge 20\%$ | `ENGINE_RUNNING` |
| **ENGINE_RUNNING** | Motor rölantide ($800\text{ RPM}$) | Vites `D` & Gaz $> 5\%$ | `DRIVING` |
| **DRIVING** | Araç seyir halinde | Hız $\le 0.1\text{ km/h}$ & Gaz $= 0\%$ | `ENGINE_RUNNING` |
| **FAULT** | Kritik hata algılandı | Arıza temizlendi & Hız $= 0$ | `RECOVERY` |
| **RECOVERY** | Kendi kendini test etme modu | Test tamamlandı | `ENGINE_RUNNING` |
| **SHUTDOWN** | Kapatma sekansı | Kontak kapatıldı (`ignition == False`) | `OFF` |

---

### 📁 Dosya Yapısı ve Görevleri
* `day-4-app/vehicle_fsm.py`: Durum makinesi mantığı ve deterministik fizik modeli ($a = F_{\text{gaz}} - F_{\text{fren}} - F_{\text{sürtünme}}$).
* `day-4-app/normal_drive.yaml`: Kontak açma, marş, hızlanma, sabit hız, frenleme ve stop aşamalarını içeren sürüş senaryosu.
* `day-4-app/run_simulation.py`: YAML senaryosunu $100\text{ ms}$ periyotlarla işleten simülatör.
* `day-4-app/test_vehicle_fsm.py`: Durum geçişleri ve kabul kriterleri testleri (`pytest`).

---

### 🧪 Kabul Kriterleri Doğrulaması
- [x] Kontak kapalıyken devir ($0\text{ RPM}$) ve hız ($0\text{ km/h}$) sıfırlanmalıdır.
- [x] Gaz artışı devir ve hız üzerinde tutarlı ivmelenme sağlamalıdır.
- [x] Aynı senaryo her çalıştırmada birebir aynı çıktıyı üretmelidir (Determinizm).

---

### 📚 Araştırma Notları

#### 1. JSON vs. YAML
* **JSON:** Web servisleri ve hızlı veri aktarımı için optimize edilmiş, süslü parantez `{}` kullanan format.
* **YAML:** İnsan okunabilirliği yüksek, girintilere (boşluk) dayalı, simülasyon ve konfigürasyon senaryoları için ideal format.

#### 2. CAN Bus Hızı ve Hat Uzunluğu İlişkisi
CAN mimarisinde propagasyon gecikmesi (sinyalin hat boyunca gidiş-dönüş süresi) nedeniyle **hat uzunluğu ile haberleşme hızı ters orantılıdır**:
* **1 Mbps:** Maksimum $\sim 30 - 40\text{ metre}$ *(Motor, ABS/ESP gibi kritik sistemler)*
* **500 kbps:** Maksimum $\sim 100\text{ metre}$ *(Araç içi standart iletişim)*
* **125 kbps:** Maksimum $\sim 500\text{ metre}$ *(Konfor modülleri ve uzun hatlar)*
# Day 5: Virtual ECUs and Periodic CAN Message Transmission

## 1. Overview
The primary objective of Day 5 is to decouple vehicle dynamics and telemetry into dedicated **Virtual Electronic Control Units (ECUs)** adhering to the **Single Responsibility Principle (SRP)**. This module establishes asynchronous periodic task scheduling, message packaging, alive counter validation, and timing/jitter verification across a simulated CAN network.

---

## 2. Key Theoretical Concepts

* **Modular ECU Architecture:** Distributing software functions into isolated domain controllers (Powertrain, Body, Diagnostic) to prevent tight coupling and single points of failure.
* **Single Responsibility Principle (SRP):** Each ECU handles exclusively its domain-specific sensors, actuators, and signal generation.
* **Message Cycle & Task Periods:** Real-time embedded scheduling prioritizing safety-critical telemetry with higher transmission frequencies over routine status data.
* **Alive Counter & Integrity:** 4-bit monotonic rolling counters (`0–15`) paired with high-resolution timestamps to detect packet loss, staleness, and message sequence integrity.
* **CAN ID Standard vs. Extended:**
  * **11-bit Standard ID (`0x000`–`0x7FF`):** Low-latency deterministic arbitration for operational vehicle bus communication.
  * **29-bit Extended ID (`0x00000000`–`0x1FFFFFFF`):** Higher addressing capacity for diagnostics (UDS / ISO 14229) and network management.

---

## 3. Communication Matrix & Signal Specification

| ECU Node | Message Name | CAN ID (Hex) | Frame Type | Cycle Time | Signals & Payloads |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Powertrain ECU** | `PowertrainStatus` | `0x101` (257) | Standard (11-bit) | 100 ms | `EngineRPM`, `EngineTemp`, `GearPosition`, `AliveCounter` |
| **Powertrain ECU** | `PedalStatus` | `0x102` (258) | Standard (11-bit) | 100 ms | `ThrottlePosition`, `BrakeApplied`, `AliveCounter` |
| **Body ECU** | `BodyStatus` | `0x201` (513) | Standard (11-bit) | 500 ms | `DoorLockState`, `HeadlightStatus`, `Age`, `AliveCounter` |
| **Diagnostic ECU**| `DiagnosticStatus` | `0x18DAF110` | Extended (29-bit) | 1000 ms | `ActiveDTCCount`, `ECUOperatingMode`, `SystemHealth` |

---

## 4. DBC Specification (Sample Extract)

```text
VERSION ""

NS_ :

BS_:

BU_: Powertrain_ECU Body_ECU Diagnostic_ECU

BO_ 257 PowertrainStatus: 8 Powertrain_ECU
 SG_ EngineRPM : 0|16@1+ (1,0) [0|8000] "rpm" Vector__XXX
 SG_ EngineTemp : 16|8@1+ (1,-40) [-40|215] "degC" Vector__XXX
 SG_ GearPosition : 24|4@1+ (1,0) [0|6] "gear" Vector__XXX
 SG_ AliveCounter : 28|4@1+ (1,0) [0|15] "cnt" Vector__XXX

BO_ 513 BodyStatus: 8 Body_ECU
 SG_ DoorLockState : 0|2@1+ (1,0) [0|3] "raw" Vector__XXX
 SG_ HeadlightStatus : 2|2@1+ (1,0) [0|3] "raw" Vector__XXX
 SG_ Age : 8|8@1+ (1,0) [0|120] "years" Vector__XXX
 SG_ AliveCounter : 16|4@1+ (1,0) [0|15] "cnt" Vector__XXX

BO_ 2497376528 DiagnosticStatus: 8 Diagnostic_ECU
 SG_ ActiveDTCCount : 0|8@1+ (1,0) [0|255] "cnt" Vector__XXX
 SG_ ECUOperatingMode : 8|8@1+ (1,0) [0|3] "mode" Vector__XXX