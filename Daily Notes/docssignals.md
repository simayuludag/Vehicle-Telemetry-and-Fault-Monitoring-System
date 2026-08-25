# Araç Sinyal Spesifikasyonu (Signal Specification)

Bu doküman, araç içi CAN haberleşme ağında paylaşılan temel 8 sinyalin veri tiplerini, periyotlarını, hata durumlarını ve fail-safe davranışlarını tanımlar.

---

## 1. Mimari ve ECU Sinyal Özeti

* **Powertrain (EMS):** `EngineSpeed`, `AcceleratorPedalPos`, `EngineCoolantTemp`
* **ABS / ESC:** `VehicleSpeed`, `BrakePedalStatus`
* **BCM (Gövde Kontrol):** `FuelLevel`, `LowBeamStatus`, `DoorOpenStatus`
* **Gösterge Paneli (Cluster):** Tüm sinyalleri dinleyen alıcı modül (Consumer)

---

## 2. Sinyal Tanımlama Matrisi

| Sinyal Adı | Kaynak ECU | Veri Tipi | Formül (Raw -> Phys) | Birim | Aralık | Başlangıç | Periyot | Timeout |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `EngineSpeed` | Powertrain | `uint16` | Raw * 0.25 | rpm | 0 - 8000 | 0 rpm | 10 ms | 50 ms |
| `VehicleSpeed` | ABS/ESC | `uint16` | Raw * 0.05625 | km/h | 0 - 250 | 0 km/h | 20 ms | 100 ms |
| `BrakePedalStatus` | ABS/ESC | `uint8` | Enum (0:Off, 1:On) | - | 0 - 2 | 0 | 20 ms | 100 ms |
| `AcceleratorPedalPos` | Powertrain | `uint8` | Raw * 0.4 | % | 0 - 100 | %0 | 10 ms | 50 ms |
| `EngineCoolantTemp` | Powertrain | `uint8` | Raw - 40 | °C | -40 - 150 | 20 °C | 100 ms | 500 ms |
| `FuelLevel` | BCM | `uint8` | Raw * 0.5 | % | 0 - 100 | %50 | 500 ms | 2000 ms |
| `LowBeamStatus` | BCM | `uint8` | Enum (0:Off, 1:On) | - | 0 - 2 | 0 | 100 ms | 500 ms |
| `DoorOpenStatus` | BCM | `uint8` | Bitmask (FL/FR/RL/RR) | - | 0 - 15 | 0 | 100 ms | 500 ms |

---

## 3. Sinyal Detayları ve Hata / Timeout Yönetimi

### 3.1. EngineSpeed (Motor Devri)
* **Açıklama:** Krank mili pozisyon sensöründen hesaplanan anlık motor dönüş hızı.
* **Geçersiz Değer (SNA):** `0xFFFF` (Raw) -> Sistem hata bayrağı set edilir, veri geçersiz sayılır.
* **Timeout Davranışı:** 50 ms süreyle yeni çerçeve gelmezse gösterge devir ibresi 0'a çekilir, EMS arıza lambası (MIL) yakılır.

### 3.2. VehicleSpeed (Araç Hızı)
* **Açıklama:** Tekerlek hız sensörlerinden türetilen aracın anlık çizgisel hızı.
* **Geçersiz Değer (SNA):** `0xFFFF` (Raw) -> ESC sistemi devre dışı kalır, ABS/ESC ikaz lambası yakılır.
* **Timeout Davranışı:** 100 ms veri kesintisinde göstergede hız değeri `---` olarak gösterilir.

### 3.3. BrakePedalStatus (Fren Pedalı Durumu)
* **Açıklama:** Sürücünün fren pedalına basıp basmadığını iletir (0: Bırakıldı, 1: Basıldı, 2: Sensör Hatası).
* **Geçersiz Değer (SNA):** `0x02` veya `0x03` -> Güvenlik gereği fren lambaları açık tutulur (Fail-Safe Açık).
* **Timeout Davranışı:** 100 ms boyunca mesaj alınamazsa hız sabitleyici (Cruise Control) derhal devreden çıkarılır.

### 3.4. AcceleratorPedalPos (Gaz Pedalı Açıklığı)
* **Açıklama:** Elektronik gaz pedalı konum sensörünün (TPS) yüzde cinsinden değeri.
* **Geçersiz Değer (SNA):** `0xFF` -> Araç koruma moduna (Limp-Home) geçer.
* **Timeout Davranışı:** 50 ms veri alınamazsa motor kontrol ünitesi gaz talebini %0 (rölanti konumu) kabul eder.

### 3.5. EngineCoolantTemp (Motor Soğutma Suyu Sıcaklığı)
* **Açıklama:** Motor bloğu soğutma sıvısı sıcaklık bilgisi.
* **Geçersiz Değer (SNA):** `0xFF` -> Motorun aşırı ısınmasını önlemek için radyatör soğutma fanı %100 hızda çalıştırılır.
* **Timeout Davranışı:** 500 ms veri kesilirse gösterge ibresi son geçerli değerde kilitlenir, soğutma fanı tam güç devreye girer.

### 3.6. FuelLevel (Yakıt Depo Seviyesi)
* **Açıklama:** Depo şamandırasından okunan yakıt doluluk yüzdesi.
* **Geçersiz Değer (SNA):** `0xFE` veya `0xFF` -> Düşük Yakıt Uyarısı aktif edilir.
* **Timeout Davranışı:** 2000 ms boyunca mesaj gelmezse yakıt ibresi minimum seviyeye iner ve ikaz lambası yakılır.

### 3.7. LowBeamStatus (Kısa Far Durumu)
* **Açıklama:** Kısa farların açık/kapalı durumu (0: Kapalı, 1: Açık, 2: Hata).
* **Geçersiz Değer (SNA):** `0x03` -> Farlar açık konuma alınır (Fail-Safe).
* **Timeout Davranışı:** 500 ms veri kesintisinde farlar güvenli tarafta kalmak için açık tutulur.

### 3.8. DoorOpenStatus (Kapı Açık Durumları)
* **Açıklama:** Kapı kilit switchlerinden gelen 4 bitlik maske (Bit0: FL, Bit1: FR, Bit2: RL, Bit3: RR).
* **Geçersiz Değer (SNA):** `0xF` -> Kapı açık alarmı tetiklenir.
* **Timeout Davranışı:** 500 ms veri gelmezse gösterge panelinde "Kapı Bilgisi Alınamıyor" uyarısı verilir.