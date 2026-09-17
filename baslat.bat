@echo off
title SAE J1939 Filo Telemetri Platformu
echo ================================================================
echo  SAE J1939 Arac Telematik ve Filo Izleme Platformu Baslatiliyor...
echo ================================================================
echo.
cd /d "%~dp0"

if exist "venv\Scripts\python.exe" (
    echo [OK] Sanal ortam bulundu, baslatiliyor...
    venv\Scripts\python.exe server.py
) else (
    echo [UYARI] venv bulunamadi, sistem Python'i kullaniliyor...
    python server.py
)

pause
