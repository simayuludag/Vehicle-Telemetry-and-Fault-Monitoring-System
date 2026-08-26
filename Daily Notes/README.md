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