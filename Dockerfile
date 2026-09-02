# ==============================================================================
# J1939 CAN Bus Telemetry & Fleet Web Platform Dockerfile
# Multi-stage / Lightweight Python 3.12-Slim Image
# ==============================================================================

FROM python:3.12-slim

# Çalışma dizini
WORKDIR /app

# Sistem bağımlılıkları ve soketcan araçları
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    can-utils \
    && rm -rf /var/lib/apt/lists/*

# Bağımlılıkları kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Proje kaynak kodlarını kopyala
COPY . .

# Ortam değişkenleri
ENV PYTHONUNBUFFERED=1 \
    CAN_INTERFACE=virtual \
    CAN_CHANNEL=j1939_bus \
    CAN_BITRATE=250000

# Web Dashboard Portu
EXPOSE 8000

# Sağlık Kontrolü (Healthcheck)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Uygulamayı başlat
CMD ["python", "server.py", "--host", "0.0.0.0", "--port", "8000", "--interface", "virtual"]
