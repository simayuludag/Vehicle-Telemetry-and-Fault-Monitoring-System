/**
 * J1939 Multi-Signal Fleet Telemetry & Central Controller
 * Auto-resolves user-provided images: .jpg -> .png -> .webp -> .svg
 */

document.addEventListener('DOMContentLoaded', () => {
  // Global State
  let fleet = [];
  let brands = [];
  let selectedVehicleId = 'bmw-320i';
  let activeBrandFilter = 'all';
  let isFleetMode = false;
  let snifferPaused = false;
  let snifferSearchQuery = '';
  let ws = null;
  let gauge = null;

  // CAN Sniffer Rolling Log (Maksimum 100 satır)
  const maxSnifferRows = 100;
  const canLogList = [];

  // DOM Elemanları
  const fleetGridEl = document.getElementById('fleetGrid');
  const brandFiltersEl = document.getElementById('brandFilters');
  const activeVehiclePhotoEl = document.getElementById('activeVehiclePhoto');
  const activeScopePillEl = document.getElementById('activeScopePill');
  const tabSingleVehicleEl = document.getElementById('tabSingleVehicle');
  const tabFleetModeEl = document.getElementById('tabFleetMode');
  const sliderLabelEl = document.getElementById('sliderLabel');
  const speedSliderEl = document.getElementById('speedSlider');
  const speedSliderValEl = document.getElementById('speedSliderVal');
  const btnThrottleEl = document.getElementById('btnThrottle');
  const btnBrakeGradualEl = document.getElementById('btnBrakeGradual');
  const btnBrakeFullEl = document.getElementById('btnBrakeFull');
  const btnEmergencyStopEl = document.getElementById('btnEmergencyStop');
  const snifferTableBodyEl = document.getElementById('snifferTableBody');
  const snifferSearchInputEl = document.getElementById('snifferSearchInput');
  const pauseSnifferBtn = document.getElementById('pauseSnifferBtn');
  const clearSnifferBtn = document.getElementById('clearSnifferBtn');
  const exportSnifferBtn = document.getElementById('exportSnifferBtn');
  const wsStatusDot = document.getElementById('wsStatusDot');
  const wsStatusText = document.getElementById('wsStatusText');
  const totalFramesCounterEl = document.getElementById('totalFramesCounter');
  const scenarioBadgeEl = document.getElementById('scenarioBadge');

  // Multi-Signal HUD Elements
  const throttleBarFillEl = document.getElementById('throttleBarFill');
  const throttleReadoutEl = document.getElementById('throttleReadout');
  const brakeBarFillEl = document.getElementById('brakeBarFill');
  const brakeReadoutEl = document.getElementById('brakeReadout');
  const activeGearBigBadgeEl = document.getElementById('activeGearBigBadge');
  const prndPEl = document.getElementById('prnd-P');
  const prndREl = document.getElementById('prnd-R');
  const prndNEl = document.getElementById('prnd-N');
  const prndDEl = document.getElementById('prnd-D');
  const energyBoxTitleEl = document.getElementById('energyBoxTitle');
  const energyBoxPgnEl = document.getElementById('energyBoxPgn');
  const energyPrimaryLabelEl = document.getElementById('energyPrimaryLabel');
  const energyPrimaryValEl = document.getElementById('energyPrimaryVal');
  const energySecondaryLabelEl = document.getElementById('energySecondaryLabel');
  const energySecondaryValEl = document.getElementById('energySecondaryVal');

  // CAN Inspector DOM Elemanları
  const inspPgnBadgeEl = document.getElementById('inspPgnBadge');
  const inspCanIdEl = document.getElementById('inspCanId');
  const inspPgnEl = document.getElementById('inspPgn');
  const inspPriorityEl = document.getElementById('inspPriority');
  const inspSaEl = document.getElementById('inspSa');
  const hexBytesRowEl = document.getElementById('hexBytesRow');
  const spnFormulaHintEl = document.getElementById('spnFormulaHint');

  // Gauge Başlat
  gauge = new window.SpeedGauge('speedGaugeCanvas');

  // Akıllı Görsel Yükleyici (.png -> .jpg -> .webp -> .svg)
  function setCarImage(imgElement, vehicleId, explicitUrl = null) {
    if (!imgElement) return;
    const v = fleet.find(item => item.id === vehicleId);
    if (explicitUrl) {
      imgElement.src = explicitUrl;
      return;
    }
    if (v && v.image_url) {
      imgElement.src = v.image_url;
      return;
    }

    const exts = ['.png', '.jpg', '.webp', '.jpeg', '.svg'];
    let currentExtIdx = 0;

    function tryNext() {
      if (currentExtIdx < exts.length) {
        const ext = exts[currentExtIdx++];
        imgElement.src = `/static/images/cars/${vehicleId}${ext}?t=${Date.now()}`;
      }
    }

    imgElement.onerror = () => {
      tryNext();
    };

    tryNext();
  }

  // 1. WebSocket Bağlantısını Başlat
  function initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/telemetry`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      wsStatusDot.style.background = '#10b981';
      wsStatusDot.style.boxShadow = '0 0 10px #10b981';
      wsStatusText.textContent = 'ONLINE (250 kbps)';
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'initial_fleet') {
          brands = msg.brands || [];
          fleet = msg.fleet || [];
          renderBrandFilters();
          renderFleetGrid();
          updateSelectedVehicleView();
        } else if (msg.type === 'vehicle_added') {
          brands = msg.brands || brands;
          fleet = msg.fleet || fleet;
          renderBrandFilters();
          renderFleetGrid();
          if (msg.vehicle && msg.vehicle.id) {
            selectVehicle(msg.vehicle.id);
          }
        } else if (msg.type === 'brand_added') {
          brands = msg.brands || brands;
          renderBrandFilters();
        } else if (msg.type === 'vehicle_removed') {
          fleet = msg.fleet || fleet;
          if (selectedVehicleId === msg.vehicle_id && fleet.length > 0) {
            selectedVehicleId = fleet[0].id;
          }
          renderFleetGrid();
          updateSelectedVehicleView();
        } else if (msg.type === 'vehicle_image_updated') {
          const v = fleet.find(item => item.id === msg.vehicle_id);
          if (v) v.image_url = msg.image_url;
          if (selectedVehicleId === msg.vehicle_id && activeVehiclePhotoEl) {
            activeVehiclePhotoEl.src = msg.image_url;
          }
        } else if (msg.type === 'telemetry_update') {
          fleet = msg.fleet || [];
          updateFleetGridRealtime();
          updateSelectedVehicleView();

          if (msg.stats) {
            totalFramesCounterEl.textContent = msg.stats.total_frames.toLocaleString();
            scenarioBadgeEl.textContent = (msg.stats.scenario || 'Normal').toUpperCase();
          }

          if (msg.batch_frames && !snifferPaused) {
            msg.batch_frames.forEach(frame => processSnifferFrame(frame));
          }
        }
      } catch (err) {
        console.error('WebSocket veri işleme hatası:', err);
      }
    };

    ws.onclose = () => {
      wsStatusDot.style.background = '#f43f5e';
      wsStatusDot.style.boxShadow = '0 0 10px #f43f5e';
      wsStatusText.textContent = 'RECONNECTING...';
      setTimeout(initWebSocket, 2000);
    };

    ws.onerror = (err) => {
      console.error('WebSocket Hatası:', err);
      ws.close();
    };
  }

  // 2. Marka Filtrelerini Render Et
  function renderBrandFilters() {
    brandFiltersEl.innerHTML = `
      <button class="brand-chip ${activeBrandFilter === 'all' ? 'active' : ''}" data-brand="all">
        🌐 Tümü (30 Araç)
      </button>
    `;

    brands.forEach(b => {
      const btn = document.createElement('button');
      btn.className = `brand-chip ${activeBrandFilter === b.id ? 'active' : ''}`;
      btn.dataset.brand = b.id;
      btn.innerHTML = `<span style="color:${b.color}">●</span> ${b.name}`;
      btn.addEventListener('click', () => {
        activeBrandFilter = b.id;
        document.querySelectorAll('.brand-chip').forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
        renderFleetGrid();
      });
      brandFiltersEl.appendChild(btn);
    });

    brandFiltersEl.querySelector('[data-brand="all"]').addEventListener('click', (e) => {
      activeBrandFilter = 'all';
      document.querySelectorAll('.brand-chip').forEach(c => c.classList.remove('active'));
      e.target.classList.add('active');
      renderFleetGrid();
    });
  }

  // 3. 30 Araçlık Izgarayı (Grid) Oluştur
  function renderFleetGrid() {
    fleetGridEl.innerHTML = '';

    const filtered = activeBrandFilter === 'all'
      ? fleet
      : fleet.filter(v => v.brand_id === activeBrandFilter);

    filtered.forEach(v => {
      const brand = brands.find(b => b.id === v.brand_id) || { color: '#00d2ff' };
      const card = document.createElement('div');
      card.className = `vehicle-card ${v.id === selectedVehicleId ? 'selected' : ''}`;
      card.id = `card-${v.id}`;
      card.dataset.id = v.id;

      // Enerji Hapı (EV: Batarya, Hibrit: HEV, Benzin/Dizel: Yakıt Deposu)
      let energyPillHtml = '';
      if (v.powertrain === 'ev' || v.is_ev) {
        energyPillHtml = `<span class="pill-soc" id="badge-energy-${v.id}" style="color:#10b981">🔋 %${Math.round(v.battery_soc || 95)}</span>`;
      } else if (v.powertrain === 'hybrid') {
        energyPillHtml = `<span class="pill-soc" id="badge-energy-${v.id}" style="color:#10b981">🌿 %${Math.round(v.battery_soc || 65)} (HEV)</span>`;
      } else {
        const fuel = v.fuel_level_pct !== undefined && v.fuel_level_pct !== null ? v.fuel_level_pct : 85;
        energyPillHtml = `<span class="pill-soc" id="badge-energy-${v.id}" style="color:#f59e0b">⛽ %${Math.round(fuel)} (Yakıt)</span>`;
      }

      card.innerHTML = `
        <div class="vehicle-card-top-row">
          <div class="brand-badge-pill" style="border-left: 3px solid ${brand.color}">
            <span style="color:${brand.color}">●</span>
            ${v.brand_name}
          </div>
          <div class="sa-pill">SA: 0x${v.source_address.toString(16).toUpperCase().padStart(2, '0')}</div>
        </div>
        
        <div class="vehicle-model-title">${v.model}</div>
        <div class="vehicle-specs-line">${v.plate} · ${v.category}</div>
        
        <div class="vehicle-speed-line">
          <div class="speed-readout">
            <span id="speed-num-${v.id}">${Math.round(v.current_speed)}</span>
            <span class="unit">KM/H</span>
          </div>
          <div class="status-badge ${v.status}" id="status-badge-${v.id}">${v.status}</div>
        </div>

        <div class="card-telemetry-pills">
          <span class="pill-gear" id="badge-gear-${v.id}">🕹️ ${v.gear || 'D'}</span>
          ${energyPillHtml}
          <span class="pill-throttle" id="badge-throttle-${v.id}">⚡ %${Math.round(v.throttle_pct || 0)}</span>
        </div>

        <div class="speed-bar-track">
          <div class="speed-bar-fill" id="speed-bar-${v.id}" style="width: ${(v.current_speed / v.max_speed) * 100}%"></div>
        </div>
      `;

      card.addEventListener('click', () => {
        selectVehicle(v.id);
      });

      fleetGridEl.appendChild(card);
    });
  }

  // 4. Canlı Veri Akışında Sayıları Güncelle
  function updateFleetGridRealtime() {
    fleet.forEach(v => {
      const numEl = document.getElementById(`speed-num-${v.id}`);
      const barEl = document.getElementById(`speed-bar-${v.id}`);
      const badgeEl = document.getElementById(`status-badge-${v.id}`);
      const gearEl = document.getElementById(`badge-gear-${v.id}`);
      const energyEl = document.getElementById(`badge-energy-${v.id}`);
      const throttleEl = document.getElementById(`badge-throttle-${v.id}`);

      if (numEl) numEl.textContent = Math.round(v.current_speed);
      if (barEl) barEl.style.width = `${Math.min(100, (v.current_speed / v.max_speed) * 100)}%`;
      if (badgeEl) {
        badgeEl.className = `status-badge ${v.status}`;
        badgeEl.textContent = v.status;
      }
      if (gearEl) gearEl.textContent = `🕹️ ${v.gear || 'D'}`;
      
      if (energyEl) {
        if (v.powertrain === 'ev' || v.is_ev) {
          energyEl.textContent = `🔋 %${Math.round(v.battery_soc || 95)}`;
          energyEl.style.color = '#10b981';
        } else if (v.powertrain === 'hybrid') {
          energyEl.textContent = `🌿 %${Math.round(v.battery_soc || 65)} (HEV)`;
          energyEl.style.color = '#10b981';
        } else {
          const fuel = v.fuel_level_pct !== undefined && v.fuel_level_pct !== null ? v.fuel_level_pct : 85;
          energyEl.textContent = `⛽ %${Math.round(fuel)} (Yakıt)`;
          energyEl.style.color = '#f59e0b';
        }
      }

      if (throttleEl) throttleEl.textContent = `⚡ %${Math.round(v.throttle_pct || 0)}`;
    });
  }

  // 5. Araç Seçimi & Kokpit HUD ve Fotoğrafını Güncelleme
  let lastLoadedVehicleId = null;

  function selectVehicle(vehicleId) {
    selectedVehicleId = vehicleId;
    document.querySelectorAll('.vehicle-card').forEach(c => {
      c.classList.toggle('selected', c.dataset.id === vehicleId);
    });
    updateSelectedVehicleView(true);
  }

  function updateSelectedVehicleView(forceImageUpdate = false) {
    const v = fleet.find(item => item.id === selectedVehicleId);
    if (!v) return;

    // 1. Seçili Aracın Görselini Yükle
    if (activeVehiclePhotoEl && (forceImageUpdate || lastLoadedVehicleId !== v.id)) {
      lastLoadedVehicleId = v.id;
      setCarImage(activeVehiclePhotoEl, v.id);
      activeVehiclePhotoEl.alt = `${v.brand_name} ${v.model}`;
    }

    if (activeScopePillEl) {
      if (isFleetMode) {
        activeScopePillEl.textContent = 'MASTER FİLO KONTROLÜ';
        activeScopePillEl.style.borderColor = '#f59e0b';
        activeScopePillEl.style.color = '#f59e0b';
      } else {
        activeScopePillEl.textContent = 'SEÇİLİ ARAÇ KONTROLÜ';
        activeScopePillEl.style.borderColor = '#00d2ff';
        activeScopePillEl.style.color = '#00d2ff';
      }
    }

    // 2. Hız Kadranı (Cluster Göstergesi)
    if (gauge) {
      gauge.setSpeed(v.current_speed, v.max_speed);
    }

    // 3. Gaz Pedalı (SPN 91)
    const throttlePct = v.throttle_pct || 0.0;
    if (throttleBarFillEl) throttleBarFillEl.style.height = `${Math.min(100, Math.max(0, throttlePct))}%`;
    if (throttleReadoutEl) throttleReadoutEl.textContent = `%${Math.round(throttlePct)}`;

    // 4. Fren Pedalı (SPN 563 / 521)
    const brakePct = v.brake_pct || 0.0;
    if (brakeBarFillEl) brakeBarFillEl.style.height = `${Math.min(100, Math.max(0, brakePct))}%`;
    if (brakeReadoutEl) brakeReadoutEl.textContent = `%${Math.round(brakePct)}`;

    // 5. Modern PRND Vites Göstergesi (SPN 523)
    const currentGear = v.gear || "P";
    if (activeGearBigBadgeEl) activeGearBigBadgeEl.textContent = currentGear;

    if (prndPEl) prndPEl.classList.toggle('active', currentGear === 'P');
    if (prndREl) prndREl.classList.toggle('active', currentGear === 'R');
    if (prndNEl) prndNEl.classList.toggle('active', currentGear === 'N');
    if (prndDEl) prndDEl.classList.toggle('active', currentGear.startsWith('D') || currentGear === 'D');

    // 6. Enerji & Batarya / Yakıt Durumu (EV / Hibrit / Benzin-Dizel)
    if (v.powertrain === 'ev' || v.is_ev) {
      const soc = v.battery_soc !== undefined && v.battery_soc !== null ? v.battery_soc : 95.0;
      const soh = v.battery_soh !== undefined && v.battery_soh !== null ? v.battery_soh : 99.0;
      if (energyBoxTitleEl) energyBoxTitleEl.innerHTML = '🔋 HV Batarya Telemetrisi';
      if (energyBoxPgnEl) {
        energyBoxPgnEl.textContent = 'PGN 0xFE56 (HVS)';
        energyBoxPgnEl.style.color = '#a855f7';
      }
      if (energyPrimaryLabelEl) energyPrimaryLabelEl.textContent = 'ŞARJ (SOC)';
      if (energyPrimaryValEl) {
        energyPrimaryValEl.textContent = `%${soc.toFixed(1)}`;
        energyPrimaryValEl.style.color = '#10b981';
      }
      if (energySecondaryLabelEl) energySecondaryLabelEl.textContent = 'SAĞLIK (SOH)';
      if (energySecondaryValEl) energySecondaryValEl.textContent = `%${soh.toFixed(1)} ${soh >= 95 ? 'Mükemmel' : 'İyi'}`;
    } else if (v.powertrain === 'hybrid') {
      const soc = v.battery_soc !== undefined && v.battery_soc !== null ? v.battery_soc : 65.0;
      const fuel = v.fuel_level_pct !== undefined && v.fuel_level_pct !== null ? v.fuel_level_pct : 80.0;
      if (energyBoxTitleEl) energyBoxTitleEl.innerHTML = '🌿 Hibrit Batarya & Yakıt';
      if (energyBoxPgnEl) {
        energyBoxPgnEl.textContent = 'PGN 0xFE56 & 0xFEFC';
        energyBoxPgnEl.style.color = '#10b981';
      }
      if (energyPrimaryLabelEl) energyPrimaryLabelEl.textContent = 'HEV BATARYA (SOC)';
      if (energyPrimaryValEl) {
        energyPrimaryValEl.textContent = `%${soc.toFixed(1)}`;
        energyPrimaryValEl.style.color = '#10b981';
      }
      if (energySecondaryLabelEl) energySecondaryLabelEl.textContent = 'YAKIT DEPOSU (SPN 96)';
      if (energySecondaryValEl) energySecondaryValEl.textContent = `%${fuel.toFixed(1)}`;
    } else {
      // Benzin / Dizel İçten Yanmalı
      const fuel = v.fuel_level_pct !== undefined && v.fuel_level_pct !== null ? v.fuel_level_pct : 85.0;
      const v12 = v.battery_12v !== undefined && v.battery_12v !== null ? v.battery_12v : 14.2;
      if (energyBoxTitleEl) energyBoxTitleEl.innerHTML = '⛽ Yakıt & 12V Akü Telemetrisi';
      if (energyBoxPgnEl) {
        energyBoxPgnEl.textContent = 'PGN 0xFEFC (DASH)';
        energyBoxPgnEl.style.color = '#f59e0b';
      }
      if (energyPrimaryLabelEl) energyPrimaryLabelEl.textContent = 'YAKIT DEPOSU (SPN 96)';
      if (energyPrimaryValEl) {
        energyPrimaryValEl.textContent = `%${fuel.toFixed(1)}`;
        energyPrimaryValEl.style.color = '#f59e0b';
      }
      if (energySecondaryLabelEl) energySecondaryLabelEl.textContent = '12V AKÜ (SPN 168)';
      if (energySecondaryValEl) energySecondaryValEl.textContent = `${v12.toFixed(1)} V (Normal)`;
    }

    // 7. Hız Slider'ı
    if (speedSliderEl && !speedSliderEl.matches(':active')) {
      speedSliderEl.max = v.max_speed;
      speedSliderEl.value = Math.round(v.target_speed);
      if (speedSliderValEl) speedSliderValEl.textContent = `${Math.round(v.target_speed)} KM/H`;
    }

    // 8. J1939 Inspector
    const saHex = `0x${v.source_address.toString(16).toUpperCase().padStart(2, '0')}`;
    const priority = 6;
    const pgn = 65265;
    const canId = (priority << 26) | (pgn << 8) | v.source_address;
    const canIdHex = `0x${canId.toString(16).toUpperCase().padStart(8, '0')}`;

    if (inspPgnBadgeEl) inspPgnBadgeEl.textContent = 'PGN 65265 (CCVS1) & 61443 (EEC2)';
    if (inspCanIdEl) inspCanIdEl.textContent = canIdHex;
    if (inspPgnEl) inspPgnEl.textContent = '0xFEF1 (CCVS1)';
    if (inspPriorityEl) inspPriorityEl.textContent = `${priority} (Normal)`;
    if (inspSaEl) inspSaEl.textContent = saHex;

    const rawSpeed = Math.round(v.current_speed * 256);
    const b1 = rawSpeed & 0xFF;
    const b2 = (rawSpeed >> 8) & 0xFF;
    const b4 = v.brake_pressed ? 0xFD : 0xFC;
    const bytes = [0xFC, b1, b2, 0xFF, b4, 0xFF, 0xFF, 0xFF];

    if (hexBytesRowEl) {
      hexBytesRowEl.innerHTML = '';
      bytes.forEach((b, idx) => {
        const isSpeedByte = (idx === 1 || idx === 2);
        const isBrakeByte = (idx === 4);
        const div = document.createElement('div');
        div.className = `hex-byte-block ${(isSpeedByte || isBrakeByte) ? 'highlight' : ''}`;
        div.innerHTML = `
          <span class="idx">B${idx}</span>
          <span class="val">${b.toString(16).toUpperCase().padStart(2, '0')}</span>
        `;
        hexBytesRowEl.appendChild(div);
      });
    }

    if (spnFormulaHintEl) {
      if (v.powertrain === 'ev' || v.is_ev) {
        spnFormulaHintEl.innerHTML = `
          SPN 84 Hız = <strong>${v.current_speed.toFixed(2)} km/h</strong> | 
          SPN 91 Gaz = <strong>%${throttlePct.toFixed(1)}</strong> | 
          SPN 523 Vites = <strong>${currentGear}</strong> | 
          SPN 3543 HV Batarya = <strong>%${(v.battery_soc || 95).toFixed(1)}</strong>
        `;
      } else if (v.powertrain === 'hybrid') {
        spnFormulaHintEl.innerHTML = `
          SPN 84 Hız = <strong>${v.current_speed.toFixed(2)} km/h</strong> | 
          SPN 91 Gaz = <strong>%${throttlePct.toFixed(1)}</strong> | 
          SPN 523 Vites = <strong>${currentGear}</strong> | 
          SPN 96 Yakıt = <strong>%${(v.fuel_level_pct || 80).toFixed(1)}</strong> | 
          SPN 3543 HEV = <strong>%${(v.battery_soc || 65).toFixed(1)}</strong>
        `;
      } else {
        spnFormulaHintEl.innerHTML = `
          SPN 84 Hız = <strong>${v.current_speed.toFixed(2)} km/h</strong> | 
          SPN 91 Gaz = <strong>%${throttlePct.toFixed(1)}</strong> | 
          SPN 523 Vites = <strong>${currentGear}</strong> | 
          SPN 96 Yakıt Deposu = <strong>%${(v.fuel_level_pct || 85).toFixed(1)}</strong> | 
          SPN 168 Akü = <strong>14.2V</strong>
        `;
      }
    }
  }

  // 6. Komut Gönderme Fonksiyonları (Çift Kanallı: WS + REST API Fallback)
  function applySpeed(speed) {
    const spd = Math.max(0, parseFloat(speed) || 0);

    if (isFleetMode) {
      fleet.forEach(v => {
        v.target_speed = Math.min(v.max_speed, spd);
      });
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'set_fleet_speed', speed: spd }));
      }
      fetch('/api/fleet/speed', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ speed: spd })
      }).catch(() => {});
    } else {
      const v = fleet.find(item => item.id === selectedVehicleId);
      if (v) {
        v.target_speed = Math.min(v.max_speed, spd);
      }
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'set_speed', vehicle_id: selectedVehicleId, speed: spd }));
      }
      fetch(`/api/vehicle/${selectedVehicleId}/speed`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ speed: spd, mode: 'manual' })
      }).catch(() => {});
    }

    if (speedSliderEl && !speedSliderEl.matches(':active')) {
      speedSliderEl.value = Math.round(spd);
      speedSliderValEl.textContent = `${Math.round(spd)} KM/H`;
    }
  }

  function applyAccelerate(delta = 20.0) {
    const v = fleet.find(item => item.id === selectedVehicleId);
    const baseSpeed = v ? Math.max(v.current_speed, v.target_speed) : 0;
    applySpeed(baseSpeed + delta);
  }

  function applyDecelerate(delta = 20.0) {
    const v = fleet.find(item => item.id === selectedVehicleId);
    const baseSpeed = v ? v.current_speed : 0;
    applySpeed(Math.max(0, baseSpeed - delta));
  }

  function applyFullStop() {
    applySpeed(0.0);
    if (!isFleetMode && selectedVehicleId) {
      fetch(`/api/vehicle/${selectedVehicleId}/brake`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pressed: true })
      }).catch(() => {});
    }
  }

  function applyScenario(scenario) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: 'set_scenario', scenario: scenario }));
    } else {
      fetch('/api/fleet/scenario', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario: scenario })
      });
    }
  }

  // 7. Kontrol Olay Dinleyicileri
  tabSingleVehicleEl.addEventListener('click', () => {
    isFleetMode = false;
    tabSingleVehicleEl.classList.add('active');
    tabFleetModeEl.classList.remove('active');
    sliderLabelEl.textContent = 'Hedef Hız:';
    updateSelectedVehicleView(true);
  });

  tabFleetModeEl.addEventListener('click', () => {
    isFleetMode = true;
    tabFleetModeEl.classList.add('active');
    tabSingleVehicleEl.classList.remove('active');
    sliderLabelEl.textContent = 'Filo Hedef Hızı:';
    updateSelectedVehicleView(true);
  });

  speedSliderEl.addEventListener('input', (e) => {
    const spd = parseFloat(e.target.value);
    speedSliderValEl.textContent = `${Math.round(spd)} KM/H`;
    applySpeed(spd);
  });

  document.querySelectorAll('.btn-preset').forEach(btn => {
    btn.addEventListener('click', () => {
      const spd = parseFloat(btn.dataset.speed);
      speedSliderEl.value = spd;
      speedSliderValEl.textContent = `${spd} KM/H`;
      applySpeed(spd);
    });
  });

  btnThrottleEl.addEventListener('click', () => {
    applyAccelerate(10.0);
  });

  btnBrakeGradualEl.addEventListener('click', () => {
    applyDecelerate(15.0);
  });

  btnBrakeFullEl.addEventListener('click', () => {
    applyFullStop();
  });

  document.querySelectorAll('.btn-scenario').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.btn-scenario').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const scen = btn.dataset.scenario;
      applyScenario(scen);
    });
  });

  btnEmergencyStopEl.addEventListener('click', () => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: 'emergency_stop' }));
    } else {
      fetch('/api/fleet/emergency-stop', { method: 'POST' });
    }
  });

  // 7.1. Doğrudan Tarayıcıdan Araç Fotoğrafı Yükleme (Web UI File Upload)
  const carPhotoFileInput = document.getElementById('carPhotoFileInput');
  if (carPhotoFileInput) {
    carPhotoFileInput.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      const formData = new FormData();
      formData.append('file', file);

      try {
        const res = await fetch(`/api/vehicle/${selectedVehicleId}/upload-image`, {
          method: 'POST',
          body: formData
        });
        const data = await res.json();
        if (data.status === 'ok') {
          activeVehiclePhotoEl.src = data.image_url;
          const v = fleet.find(item => item.id === selectedVehicleId);
          if (v) v.image_url = data.image_url;
          alert(`✅ Seçili araç için görsel başarıyla güncellendi ve kalıcı kaydedildi!`);
        } else {
          alert('❌ Görsel yüklenemedi.');
        }
      } catch (err) {
        console.error('Görsel yükleme hatası:', err);
        alert('❌ Yükleme sırasında bir hata oluştu.');
      }
    });
  }

  // 8. CAN Sniffer
  function processSnifferFrame(frame) {
    canLogList.unshift(frame);
    if (canLogList.length > maxSnifferRows) canLogList.pop();

    if (snifferSearchQuery) {
      const q = snifferSearchQuery.toLowerCase();
      const match = frame.can_id_hex.toLowerCase().includes(q) ||
                    frame.pgn_hex.toLowerCase().includes(q) ||
                    frame.pgn_name.toLowerCase().includes(q) ||
                    frame.model.toLowerCase().includes(q) ||
                    frame.plate.toLowerCase().includes(q) ||
                    frame.signal_name.toLowerCase().includes(q) ||
                    frame.signal_value.toLowerCase().includes(q);
      if (!match) return;
    }

    const row = document.createElement('tr');
    
    let pgnClass = 'ccvs';
    let sigClass = 'speed';
    if (frame.pgn === 61443) { pgnClass = 'eec2'; sigClass = 'throttle'; }
    else if (frame.pgn === 61445) { pgnClass = 'etc2'; sigClass = 'gear'; }
    else if (frame.pgn === 65110) { pgnClass = 'hvs'; sigClass = 'battery'; }

    row.innerHTML = `
      <td>${frame.formatted_time}</td>
      <td class="can-id-col">${frame.can_id_hex}</td>
      <td class="pgn-col ${pgnClass}">${frame.pgn_hex} (${frame.pgn_name})</td>
      <td class="sa-col">${frame.source_address_hex} (${frame.plate})</td>
      <td class="data-hex-col">${frame.data_hex}</td>
      <td class="signal-val-col ${sigClass}">${frame.signal_value}</td>
    `;

    snifferTableBodyEl.insertBefore(row, snifferTableBodyEl.firstChild);
    while (snifferTableBodyEl.children.length > maxSnifferRows) {
      snifferTableBodyEl.removeChild(snifferTableBodyEl.lastChild);
    }
  }

  snifferSearchInputEl.addEventListener('input', (e) => {
    snifferSearchQuery = e.target.value.trim();
    snifferTableBodyEl.innerHTML = '';
    canLogList.forEach(frame => processSnifferFrame(frame));
  });

  pauseSnifferBtn.addEventListener('click', () => {
    snifferPaused = !snifferPaused;
    pauseSnifferBtn.textContent = snifferPaused ? '▶ Sürdür' : '⏸ Duraklat';
    pauseSnifferBtn.style.color = snifferPaused ? '#f59e0b' : '';
  });

  clearSnifferBtn.addEventListener('click', () => {
    canLogList.length = 0;
    snifferTableBodyEl.innerHTML = '';
  });

  exportSnifferBtn.addEventListener('click', () => {
    if (canLogList.length === 0) {
      alert('Dışa aktarılacak CAN mesajı yok!');
      return;
    }
    const headers = ['Zaman', 'CAN_ID', 'PGN', 'Mesaj_Adi', 'SA', 'Plaka', 'Model', 'Hex_Data', 'Sinyal_Degeri'];
    const rows = canLogList.map(f => [
      f.formatted_time,
      f.can_id_hex,
      f.pgn_hex,
      `"${f.pgn_name}"`,
      f.source_address_hex,
      `"${f.plate}"`,
      `"${f.model}"`,
      `"${f.data_hex}"`,
      `"${f.signal_value}"`
    ]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `j1939_multi_signals_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  });

  // 9. YENİ ARAÇ EKLEME MODAL VE FORM YÖNETİMİ
  const btnOpenAddVehicleModal = document.getElementById('btnOpenAddVehicleModal');
  const addVehicleModal = document.getElementById('addVehicleModal');
  const btnCloseModal = document.getElementById('btnCloseModal');
  const btnCancelModal = document.getElementById('btnCancelModal');
  const addVehicleForm = document.getElementById('addVehicleForm');
  const modalBrandSelect = document.getElementById('modalBrandSelect');
  const newBrandFields = document.getElementById('newBrandFields');
  const modalNewBrandName = document.getElementById('modalNewBrandName');
  const modalNewBrandColor = document.getElementById('modalNewBrandColor');
  const modalModelName = document.getElementById('modalModelName');
  const modalCategory = document.getElementById('modalCategory');
  const modalPlate = document.getElementById('modalPlate');
  const modalEngine = document.getElementById('modalEngine');
  const modalMaxSpeed = document.getElementById('modalMaxSpeed');
  const modalSa = document.getElementById('modalSa');
  const modalCarFile = document.getElementById('modalCarFile');

  async function openAddVehicleModal() {
    // 1. Sıradaki boş SA adresini çek
    try {
      const res = await fetch('/api/fleet/next-sa');
      const data = await res.json();
      if (data.status === 'ok') {
        modalSa.value = `${data.source_address_hex} (${data.source_address})`;
        modalSa.dataset.sa = data.source_address;
      }
    } catch (e) {
      modalSa.value = '0x1F';
      modalSa.dataset.sa = 31;
    }

    // 2. Marka Seçeneklerini Doldur
    modalBrandSelect.innerHTML = '';
    brands.forEach(b => {
      const opt = document.createElement('option');
      opt.value = b.id;
      opt.textContent = `${b.name} (${b.country || 'Global'})`;
      modalBrandSelect.appendChild(opt);
    });

    const newBrandOpt = document.createElement('option');
    newBrandOpt.value = '__new__';
    newBrandOpt.textContent = '➕ + Yeni Marka Ekle...';
    newBrandOpt.style.fontWeight = 'bold';
    newBrandOpt.style.color = '#00d2ff';
    modalBrandSelect.appendChild(newBrandOpt);

    newBrandFields.style.display = 'none';
    addVehicleModal.style.display = 'flex';
  }

  function closeAddVehicleModal() {
    addVehicleModal.style.display = 'none';
    addVehicleForm.reset();
  }

  if (btnOpenAddVehicleModal) {
    btnOpenAddVehicleModal.addEventListener('click', openAddVehicleModal);
  }
  if (btnCloseModal) {
    btnCloseModal.addEventListener('click', closeAddVehicleModal);
  }
  if (btnCancelModal) {
    btnCancelModal.addEventListener('click', closeAddVehicleModal);
  }

  // Backdrop'a tıklandığında kapat
  if (addVehicleModal) {
    addVehicleModal.addEventListener('click', (e) => {
      if (e.target === addVehicleModal) {
        closeAddVehicleModal();
      }
    });
  }

  if (modalBrandSelect) {
    modalBrandSelect.addEventListener('change', () => {
      if (modalBrandSelect.value === '__new__') {
        newBrandFields.style.display = 'flex';
        modalNewBrandName.focus();
      } else {
        newBrandFields.style.display = 'none';
      }
    });
  }

  // Güç Tipi (Elektrikli EV vs Benzin vs Hibrit) Değiştiğinde Alanları Güncelle
  document.querySelectorAll('input[name="modalPowertrain"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
      const val = e.target.value;
      if (val === 'ev') {
        modalEngine.placeholder = 'Örn: Çift Motor 435 HP Elektrik';
        if (modalCategory.value === 'Sedan') modalCategory.value = 'Elektrikli EV';
      } else if (val === 'hybrid') {
        modalEngine.placeholder = 'Örn: 2.0L Tam Hibrit 197 HP';
      } else {
        modalEngine.placeholder = 'Örn: 2.0L Turbo Benzin 245 HP';
      }
    });
  });

  if (addVehicleForm) {
    addVehicleForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      let brandId = modalBrandSelect.value;
      let brandName = '';

      if (brandId === '__new__') {
        const customName = modalNewBrandName.value.trim();
        if (!customName) {
          alert('Lütfen yeni marka adını girin!');
          return;
        }
        const customColor = modalNewBrandColor.value || '#00d2ff';

        // 1. Yeni Markayı Kaydet
        try {
          const brandRes = await fetch('/api/fleet/add-brand', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: customName, color: customColor })
          });
          const brandData = await brandRes.json();
          if (brandData.status === 'ok') {
            brandId = brandData.brand.id;
            brandName = brandData.brand.name;
          }
        } catch (err) {
          alert('Yeni marka eklenirken hata oluştu.');
          return;
        }
      } else {
        const found = brands.find(b => b.id === brandId);
        brandName = found ? found.name : brandId.toUpperCase();
      }

      const model = modalModelName.value.trim();
      const category = modalCategory.value;
      const plate = modalPlate.value.trim() || '34 NEW 001';
      const engine = modalEngine.value.trim() || '2.0L Turbo 200 HP';
      const maxSpeed = parseFloat(modalMaxSpeed.value) || 220;
      const sa = parseInt(modalSa.dataset.sa) || null;

      // Güç & Aktarma Organı (Elektrikli mi?)
      const ptRadio = document.querySelector('input[name="modalPowertrain"]:checked');
      const powertrain = ptRadio ? ptRadio.value : 'ice';
      const isEv = (powertrain === 'ev');

      const formData = new FormData();
      formData.append('brand_id', brandId);
      formData.append('brand_name', brandName);
      formData.append('model', model);
      formData.append('category', category);
      formData.append('plate', plate);
      formData.append('engine', engine);
      formData.append('powertrain', powertrain);
      formData.append('is_ev', isEv);
      formData.append('max_speed', maxSpeed);
      formData.append('default_speed', 0);
      if (sa) formData.append('source_address', sa);

      if (modalCarFile.files && modalCarFile.files[0]) {
        formData.append('file', modalCarFile.files[0]);
      }

      try {
        const res = await fetch('/api/fleet/add-vehicle', {
          method: 'POST',
          body: formData
        });
        const data = await res.json().catch(() => ({}));
        if (res.ok && data.status === 'ok') {
          closeAddVehicleModal();
          alert(`✅ ${brandName} ${model} başarıyla filoya eklendi ve J1939 CAN Bus ağına dahil edildi!`);
          
          // Listeyi anında yenile ve yeni aracı seç
          if (!fleet.some(v => v.id === data.vehicle.id)) {
            fleet.push(data.vehicle);
          }
          renderBrandFilters();
          renderFleetGrid();
          selectVehicle(data.vehicle.id);
        } else {
          const detail = data.detail || data.message || `HTTP ${res.status}`;
          alert(`❌ Araç eklenemedi: ${detail}`);
        }
      } catch (err) {
        console.error('Araç ekleme hatası:', err);
        alert(`❌ Araç eklenirken bağlantı hatası: ${err.message}`);
      }
    });
  }

  initWebSocket();
});
