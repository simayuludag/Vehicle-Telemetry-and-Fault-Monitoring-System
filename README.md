# 🚗 PCAN & Virtual CAN Bus Python Projesi

Bu proje, **PEAK-System PCAN-USB** donanımı üzerinden gerçek CAN hattına araç sinyalleri göndermek/okumak ve projeyi GitHub'dan indiren herkesin **herhangi bir donanıma ihtiyaç duymadan sanal ortamda (Virtual CAN)** sinyalleri canlı olarak izleyebilmesini sağlamak amacıyla geliştirilmiştir.

---

## 📌 Özellikler

- **Donanım Desteği:** PEAK-System PCAN-USB (`interface='pcan'`) desteği. Donanım bulunamazsa otomatik sanal moda geçiş uyarısı.
- **Sanal CAN / Simülasyon Desteği:** GitHub'dan projeyi indiren kişiler için tek tıkla çalışan hepsi-bir-arada sanal sinyal akışı (`interface='virtual'`).
- **Dinamik Otomotiv Sinyalleri:**
  - `0x100 (ENGINE_DATA)`: Motor Devri (RPM), Gaz Pedalı Açıklığı (%), Motor Sıcaklığı (°C), Canlılık Sayacı (Alive Counter).
  - `0x200 (VEHICLE_SPEED)`: Araç Hızı (km/h), Fren Durumu, Vites Pozisyonu (P/R/N/D), Kilometre Sayacı (Odometer).
  - `0x300 (BATTERY_STATUS)`: Akü Voltajı (V), Akım (A), Batarya Doluluk Oranı (% SOC).
- **Canlı Konsol Dashboard'u:** `rich` kütüphanesi ile renklendirilmiş, anlık güncellenen profesyonel terminal arayüzü.

---

## 🛠️ Kurulum ve Sanal Ortam (venv) Hazırlığı

Projeyi bilgisayarınıza klonladıktan veya indirdikten sonra aşağıdaki adımları izleyin:

### 1. Sanal Ortam (venv) Oluşturma

**Windows için (PowerShell / CMD):**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**Linux / macOS için:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Gerekli Kütüphanelerin Yüklenmesi
```bash
pip install -r requirements.txt
```

---

## 🚀 Çalıştırma Yöntemleri

### Yöntem 1: GitHub Kullanıcıları İçin Tek Tıkla Canlı Simülasyon (Donanımsız)

Eğer elinizde PCAN cihazı yoksa veya GitHub'dan projeyi test etmek istiyorsanız, aşağıdaki komut hem sinyal göndericiyi hem de canlı alıcı monitörünü sanal bus üzerinde eş zamanlı çalıştırır:

```bash
python run_simulation.py
```

---

### Yöntem 2: Gerçek PCAN-USB Donanımı ile Çalıştırma

Bilgisayarınıza **PEAK-System PCAN-USB** cihazı takılıysa ve PEAK sürücüleri kuruluysa:

#### 1. Terminal (Alıcıyı Başlat):
```bash
python can_receiver.py --interface pcan --channel PCAN_USBBUS1
```

#### 2. Terminal (Göndericiyi Başlat):
```bash
python can_sender.py --interface pcan --channel PCAN_USBBUS1
```

*(Not: Farklı bir baudrate kullanıyorsanız `--bitrate 250000` veya `--bitrate 500000` ekleyebilirsiniz).*

---

### Yöntem 3: İki Ayrı Terminalde Sanal Mod Testi

Sanal modda gönderici ve alıcıyı iki ayrı terminal penceresinde çalıştırmak isterseniz:

**1. Terminal (Alıcı):**
```bash
python can_receiver.py --interface virtual
```

**2. Terminal (Gönderici):**
```bash
python can_sender.py --interface virtual
```

**Trace (Satır Satır Log) Modu:**
```bash
python can_receiver.py --interface virtual --trace
```

---

## 📊 CAN Mesaj ve Sinyal Haritası (Signal Matrix)

| CAN ID (Hex) | Mesaj Adı | Periyot | Byte 0..1 | Byte 2 | Byte 3 | Byte 4..7 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`0x100`** | `ENGINE_DATA` | 50 ms | RPM (0-8000) | Throttle (% 0-100) | Temp (°C, Offset +40) | Alive Counter (0-15) |
| **`0x200`** | `VEHICLE_SPEED` | 100 ms | Hız (km/h * 10) | Fren (0 / 1) | Vites (P=0, R=1, N=2, D=3) | Odometer (km * 10) |
| **`0x300`** | `BATTERY_STATUS`| 200 ms | Voltaj (V * 100) | Akım (A * 10) | SOC (% 0-100) | Reserved (0xAA) |

---

## 📦 Proje Dosya Yapısı

```text
pcan-can-bus/
│
├── config.py             # Ortak konfigürasyon, bus oluşturucu ve CAN ID tanımları
├── can_sender.py         # PCAN / Virtual sinyal gönderici script
├── can_receiver.py       # PCAN / Virtual canlı sinyal alıcı ve dashboard
├── run_simulation.py     # GitHub kullanıcıları için donanımsız tek tıkla demo
├── requirements.txt      # python-can ve rich kütüphaneleri
├── .gitignore            # Git için hariç tutma kuralları (venv, __pycache__ vb.)
└── README.md             # Proje dokümantasyonu ve kullanım kılavuzu
```

---

## 🌐 GitHub'a Yükleme Adımları

Projeyi kendi GitHub reponuza yüklemek için proje dizininde:

```bash
git init
git add .
git commit -m "feat: PCAN ve sanal CAN bus sinyal simulasyonu ve izleyici eklendi"
git branch -M main
git remote add origin https://github.com/KULLANICI_ADINIZ/REPO_ADINIZ.git
git push -u origin main
```
