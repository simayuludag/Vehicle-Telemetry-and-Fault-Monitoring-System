/**
 * J1939 Telematics & Fleet Monitoring Platform
 * Real-time automotive telemetry stream: Motion, Engine, Powertrain, Energy, Odometer, Diagnostics & CAN Sniffer
 */

document.addEventListener('DOMContentLoaded', () => {
  // Global State
  let fleet = [];
  let brands = [];
  let selectedVehicleId = 'bmw-320i';
  let activeBrandFilter = 'all';
  let snifferPaused = false;
  let snifferSearchQuery = '';
  let ws = null;
  let gauge = null;

  // CAN Sniffer Rolling Log (Maksimum 100 satır)
  const maxSnifferRows = 100;
  const canLogList = [];

  // DOM Elemanları - Filo & Header
  const fleetGridEl = document.getElementById('fleetGrid');
  const brandFiltersEl = document.getElementById('brandFilters');
  const activeVehiclePhotoEl = document.getElementById('activeVehiclePhoto');
  const wsStatusDot = document.getElementById('wsStatusDot');
  const wsStatusText = document.getElementById('wsStatusText');
  const totalFramesCounterEl = document.getElementById('totalFramesCounter');

  // DOM Elemanları - Sürüş HUD & Kadran
  const throttleBarFillEl = document.getElementById('throttleBarFill');
  const throttleReadoutEl = document.getElementById('throttleReadout');
  const brakeBarFillEl = document.getElementById('brakeBarFill');
  const brakeReadoutEl = document.getElementById('brakeReadout');
  const telemetryRpmVal = document.getElementById('telemetryRpmVal');
  const telemetryLoadVal = document.getElementById('telemetryLoadVal');
  const telemetryCruiseVal = document.getElementById('telemetryCruiseVal');

  // DOM Elemanları - Vites & Sürüş Durumu
  const activeGearBigBadgeEl = document.getElementById('activeGearBigBadge');
  const prndPEl = document.getElementById('prnd-P');
  const prndREl = document.getElementById('prnd-R');
  const prndNEl = document.getElementById('prnd-N');
  const prndDEl = document.getElementById('prnd-D');
  const telemetryDriveStatus = document.getElementById('telemetryDriveStatus');
  const telemetryEcoScoreVal = document.getElementById('telemetryEcoScoreVal');

  // DOM Elemanları - Domain 1: Enerji, Batarya & Yakıt
  const domainEnergyTitle = document.getElementById('domainEnergyTitle');
  const domainEnergyPgn = document.getElementById('domainEnergyPgn');
  const kpiEnergyLevelLabel = document.getElementById('kpiEnergyLevelLabel');
  const kpiEnergyLevelVal = document.getElementById('kpiEnergyLevelVal');
  const kpiEnergyLevelSub = document.getElementById('kpiEnergyLevelSub');
  const kpiRangeLabel = document.getElementById('kpiRangeLabel');
  const kpiRangeVal = document.getElementById('kpiRangeVal');
  const kpiConsumptionVal = document.getElementById('kpiConsumptionVal');
  const kpiSecondaryEnergyLabel = document.getElementById('kpiSecondaryEnergyLabel');
  const kpiSecondaryEnergyVal = document.getElementById('kpiSecondaryEnergyVal');
  const kpiSecondaryEnergySub = document.getElementById('kpiSecondaryEnergySub');
  const kpiElectricalLabel = document.getElementById('kpiElectricalLabel');
  const kpiElectricalVal = document.getElementById('kpiElectricalVal');
  const kpiElectricalSub = document.getElementById('kpiElectricalSub');

  // DOM Elemanları - Domain 2: Motor & Mekanik Sağlık
  const kpiCoolantVal = document.getElementById('kpiCoolantVal');
  const kpiOilVal = document.getElementById('kpiOilVal');
  const kpiTransTempVal = document.getElementById('kpiTransTempVal');
  const kpiEngineHoursVal = document.getElementById('kpiEngineHoursVal');

  // DOM Elemanları - Domain 3: Odometre, Seyahat & GPS
  const kpiOdometerVal = document.getElementById('kpiOdometerVal');
  const kpiTripVal = document.getElementById('kpiTripVal');
  const kpiGpsCoordsVal = document.getElementById('kpiGpsCoordsVal');
  const kpiGpsLocName = document.getElementById('kpiGpsLocName');
  const kpiDtcVal = document.getElementById('kpiDtcVal');

  // DOM Elemanları - Domain 4: Güvenlik & TPMS
  const safetyTpmsVal = document.getElementById('safetyTpmsVal');
  const safetyDoorsVal = document.getElementById('safetyDoorsVal');

  // DOM Elemanları - CAN Inspector
  const inspPgnBadgeEl = document.getElementById('inspPgnBadge');
  const inspCanIdEl = document.getElementById('inspCanId');
  const inspPgnEl = document.getElementById('inspPgn');
  const inspPriorityEl = document.getElementById('inspPriority');
  const inspSaEl = document.getElementById('inspSa');
  const hexBytesRowEl = document.getElementById('hexBytesRow');
  const spnFormulaHintEl = document.getElementById('spnFormulaHint');

  // DOM Elemanları - Sniffer
  const snifferTableBodyEl = document.getElementById('snifferTableBody');
  const snifferSearchInputEl = document.getElementById('snifferSearchInput');
  const pauseSnifferBtn = document.getElementById('pauseSnifferBtn');
  const clearSnifferBtn = document.getElementById('clearSnifferBtn');
  const exportSnifferBtn = document.getElementById('exportSnifferBtn');
  const btnExportFleetTelematics = document.getElementById('btnExportFleetTelematics');

  // Gauge Başlat
  gauge = new window.SpeedGauge('speedGaugeCanvas');

  // Akıllı Görsel Yükleyici (.jpg -> .png -> .webp -> .svg)
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

    const exts = ['.jpg', '.png', '.webp', '.jpeg', '.svg'];
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
          fleet = msg.fleet || fleet.filter(item => item.id !== msg.vehicle_id);
          if (selectedVehicleId === msg.vehicle_id && fleet.length > 0) {
            selectedVehicleId = fleet[0].id;
          }
          renderBrandFilters();
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
        🌐 Tümü (${fleet.length} Araç)
      </button>
    `;

    brands.forEach(b => {
      const count = fleet.filter(v => v.brand_id === b.id).length;
      if (count === 0 && b.id !== '__new__') return;
      const btn = document.createElement('button');
      btn.className = `brand-chip ${activeBrandFilter === b.id ? 'active' : ''}`;
      btn.dataset.brand = b.id;
      btn.innerHTML = `<span style="color:${b.color}">●</span> ${b.name} (${count})`;
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

  // 3. 30+ Araçlık Telematik Filo Izgarasını (Grid) Oluştur
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

      // Aktarma Organı Etiketi & Enerji Göstergesi
      let powertrainPillHtml = '';
      let energyPillHtml = '';
      let energyVal = 95;

      if (v.powertrain === 'ev' || v.is_ev) {
        powertrainPillHtml = `<span style="font-size:0.68rem; padding:2px 6px; border-radius:4px; font-weight:700; background:rgba(16, 185, 129, 0.15); color:#10b981; border:1px solid rgba(16, 185, 129, 0.3);">⚡ EV</span>`;
        energyVal = Math.round(v.battery_soc || 95);
        energyPillHtml = `<span class="pill-soc" id="badge-energy-${v.id}" style="color:#10b981">🔋 Batarya %${energyVal}</span>`;
      } else if (v.powertrain === 'hybrid') {
        powertrainPillHtml = `<span style="font-size:0.68rem; padding:2px 6px; border-radius:4px; font-weight:700; background:rgba(16, 185, 129, 0.15); color:#10b981; border:1px solid rgba(16, 185, 129, 0.3);">🌿 HİBRİT</span>`;
        energyVal = Math.round(v.battery_soc || 65);
        energyPillHtml = `<span class="pill-soc" id="badge-energy-${v.id}" style="color:#10b981">🌿 HEV %${energyVal}</span>`;
      } else {
        const isDiesel = v.engine && v.engine.toLowerCase().includes('dizel');
        const ptLabel = isDiesel ? '⛽ DİZEL' : '⛽ BENZİN';
        energyVal = Math.round(v.fuel_level_pct !== undefined && v.fuel_level_pct !== null ? v.fuel_level_pct : 85);
        powertrainPillHtml = `<span style="font-size:0.68rem; padding:2px 6px; border-radius:4px; font-weight:700; background:rgba(245, 158, 11, 0.15); color:#f59e0b; border:1px solid rgba(245, 158, 11, 0.3);">${ptLabel}</span>`;
        energyPillHtml = `<span class="pill-soc" id="badge-energy-${v.id}" style="color:#f59e0b">⛽ Yakıt %${energyVal}</span>`;
      }

      const rpmText = v.engine_rpm ? `${v.engine_rpm.toLocaleString()} RPM` : 'Rölanti';
      const odoText = v.odometer_km ? `${Math.round(v.odometer_km).toLocaleString()} km` : '18,500 km';

      card.innerHTML = `
        <div class="vehicle-card-top-row">
          <div class="brand-badge-pill" style="border-left: 3px solid ${brand.color}">
            <span style="color:${brand.color}">●</span>
            ${v.brand_name}
          </div>
          <div style="display:flex; gap:6px; align-items:center;">
            ${powertrainPillHtml}
            <div class="sa-pill">SA: 0x${v.source_address.toString(16).toUpperCase().padStart(2, '0')}</div>
            <button class="btn-card-delete" data-del-id="${v.id}" title="${v.brand_name} ${v.model} aracını filodan çıkar">🗑️</button>
          </div>
        </div>
        
        <div class="vehicle-model-title">${v.model}</div>
        <div class="vehicle-specs-line">${v.plate} · ${v.category} · <span id="card-odo-${v.id}" style="color:#64748b">${odoText}</span></div>
        
        <div class="vehicle-speed-line">
          <div class="speed-readout">
            <span id="speed-num-${v.id}">${Math.round(v.current_speed || 0)}</span>
            <span class="unit">KM/H</span>
          </div>
          <div class="status-badge ${v.status || 'cruising'}" id="status-badge-${v.id}">${v.status === 'stopped' ? 'DURDU' : (v.current_speed > 90 ? 'OTOYOL' : 'SEYİR')}</div>
        </div>

        <div class="card-telemetry-pills">
          <span class="pill-gear" id="badge-gear-${v.id}">🕹️ ${v.gear || 'D'} (${rpmText})</span>
          ${energyPillHtml}
          <span class="pill-throttle" id="badge-throttle-${v.id}">⚡ %${Math.round(v.throttle_pct || 0)}</span>
        </div>

        <div class="speed-bar-track">
          <div class="speed-bar-fill" id="speed-bar-${v.id}" style="width: ${((v.current_speed || 0) / (v.max_speed || 220)) * 100}%"></div>
        </div>
      `;

      // Kart tıklaması ile araç seçimi
      card.addEventListener('click', () => {
        selectVehicle(v.id);
      });

      // Kart üzerindeki hızlı silme butonu
      const cardDelBtn = card.querySelector('.btn-card-delete');
      if (cardDelBtn) {
        cardDelBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          removeVehicleById(v.id);
        });
      }

      fleetGridEl.appendChild(card);
    });
  }

  // 4. Canlı Veri Akışında Filo Kartlarını Güncelle
  function updateFleetGridRealtime() {
    fleet.forEach(v => {
      const numEl = document.getElementById(`speed-num-${v.id}`);
      const barEl = document.getElementById(`speed-bar-${v.id}`);
      const badgeEl = document.getElementById(`status-badge-${v.id}`);
      const gearEl = document.getElementById(`badge-gear-${v.id}`);
      const energyEl = document.getElementById(`badge-energy-${v.id}`);
      const throttleEl = document.getElementById(`badge-throttle-${v.id}`);
      const odoEl = document.getElementById(`card-odo-${v.id}`);

      if (numEl) numEl.textContent = Math.round(v.current_speed || 0);
      if (barEl) barEl.style.width = `${Math.min(100, ((v.current_speed || 0) / (v.max_speed || 220)) * 100)}%`;
      if (badgeEl) {
        badgeEl.className = `status-badge ${v.status || 'cruising'}`;
        badgeEl.textContent = v.status === 'stopped' ? 'DURDU' : (v.current_speed > 90 ? 'OTOYOL' : 'SEYİR');
      }
      if (gearEl) {
        const rpmText = v.engine_rpm ? `${v.engine_rpm} RPM` : 'Rölanti';
        gearEl.textContent = `🕹️ ${v.gear || 'D'} (${rpmText})`;
      }
      if (odoEl && v.odometer_km) {
        odoEl.textContent = `${Math.round(v.odometer_km).toLocaleString()} km`;
      }
      
      if (energyEl) {
        if (v.powertrain === 'ev' || v.is_ev) {
          energyEl.textContent = `🔋 Batarya %${Math.round(v.battery_soc || 95)}`;
          energyEl.style.color = '#10b981';
        } else if (v.powertrain === 'hybrid') {
          energyEl.textContent = `🌿 HEV %${Math.round(v.battery_soc || 65)}`;
          energyEl.style.color = '#10b981';
        } else {
          const fuel = v.fuel_level_pct !== undefined && v.fuel_level_pct !== null ? v.fuel_level_pct : 85;
          energyEl.textContent = `⛽ Yakıt %${Math.round(fuel)}`;
          energyEl.style.color = '#f59e0b';
        }
      }

      if (throttleEl) throttleEl.textContent = `⚡ %${Math.round(v.throttle_pct || 0)}`;
    });
  }

  // 5. Araç Seçimi & Telematik Gösterge Panelini Güncelleme
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

    // 1. Vitrin Başlığı, Plaka ve Aktarma Organı Rozeti
    const showcaseTitleEl = document.getElementById('showcaseVehicleTitle');
    const showcaseSubEl = document.getElementById('showcaseVehicleSub');
    const showcaseBadgeEl = document.getElementById('showcasePowertrainBadge');
    const showcaseSaEl = document.getElementById('showcaseSaBadge');

    if (showcaseTitleEl) showcaseTitleEl.textContent = `${v.brand_name} ${v.model}`;
    if (showcaseSubEl) showcaseSubEl.textContent = `${v.plate} · ${v.engine || v.category}`;
    if (showcaseSaEl) showcaseSaEl.textContent = `J1939 SA: 0x${v.source_address.toString(16).toUpperCase().padStart(2, '0')}`;

    if (showcaseBadgeEl) {
      if (v.powertrain === 'ev' || v.is_ev) {
        showcaseBadgeEl.innerHTML = '⚡ TAM ELEKTRİKLİ (BEV)';
        showcaseBadgeEl.style.color = '#10b981';
        showcaseBadgeEl.style.borderColor = '#10b981';
        showcaseBadgeEl.style.background = 'rgba(16, 185, 129, 0.2)';
        showcaseBadgeEl.style.boxShadow = '0 0 14px rgba(16, 185, 129, 0.4)';
      } else if (v.powertrain === 'hybrid') {
        showcaseBadgeEl.innerHTML = '🌿 HİBRİT MOTOR (HEV)';
        showcaseBadgeEl.style.color = '#10b981';
        showcaseBadgeEl.style.borderColor = '#10b981';
        showcaseBadgeEl.style.background = 'rgba(16, 185, 129, 0.2)';
        showcaseBadgeEl.style.boxShadow = '0 0 14px rgba(16, 185, 129, 0.4)';
      } else {
        const isDiesel = v.engine && v.engine.toLowerCase().includes('dizel');
        showcaseBadgeEl.innerHTML = isDiesel ? '⛽ DİZEL (ICE)' : '⛽ BENZİNLİ (ICE)';
        showcaseBadgeEl.style.color = '#f59e0b';
        showcaseBadgeEl.style.borderColor = '#f59e0b';
        showcaseBadgeEl.style.background = 'rgba(245, 158, 11, 0.2)';
        showcaseBadgeEl.style.boxShadow = '0 0 14px rgba(245, 158, 11, 0.4)';
      }
    }

    // 2. Seçili Aracın Görselini Yükle
    if (activeVehiclePhotoEl && (forceImageUpdate || lastLoadedVehicleId !== v.id)) {
      lastLoadedVehicleId = v.id;
      setCarImage(activeVehiclePhotoEl, v.id);
      activeVehiclePhotoEl.alt = `${v.brand_name} ${v.model}`;
    }

    // 3. Hız Kadranı (Cluster Göstergesi)
    if (gauge) {
      gauge.setSpeed(v.current_speed || 0, v.max_speed || 220);
    }

    // 4. Gaz Pedalı (SPN 91)
    const throttlePct = v.throttle_pct || 0.0;
    if (throttleBarFillEl) throttleBarFillEl.style.height = `${Math.min(100, Math.max(0, throttlePct))}%`;
    if (throttleReadoutEl) throttleReadoutEl.textContent = `%${Math.round(throttlePct)}`;

    // 5. Fren Pedalı (SPN 563 / 521)
    const brakePct = v.brake_pct || 0.0;
    if (brakeBarFillEl) brakeBarFillEl.style.height = `${Math.min(100, Math.max(0, brakePct))}%`;
    if (brakeReadoutEl) brakeReadoutEl.textContent = `%${Math.round(brakePct)}`;

    // 6. Sürüş HUD Alt Bilgileri (Devir, Yük, Cruise)
    const rpmVal = v.engine_rpm || (v.current_speed > 0.5 ? 2100 : 750);
    const loadVal = v.engine_load_pct !== undefined ? v.engine_load_pct : 32.5;
    if (telemetryRpmVal) telemetryRpmVal.textContent = `${rpmVal.toLocaleString()} RPM`;
    if (telemetryLoadVal) telemetryLoadVal.textContent = `%${loadVal.toFixed(1)}`;
    if (telemetryCruiseVal) {
      const isCruise = v.current_speed > 40 && !v.brake_pressed;
      telemetryCruiseVal.textContent = isCruise ? 'AKTİF (ON)' : 'DEVRE DIŞI';
      telemetryCruiseVal.style.color = isCruise ? '#10b981' : '#64748b';
    }

    // 7. Modern PRND Vites Göstergesi (SPN 523)
    const currentGear = v.gear || "P";
    if (activeGearBigBadgeEl) activeGearBigBadgeEl.textContent = currentGear;

    if (prndPEl) prndPEl.classList.toggle('active', currentGear === 'P');
    if (prndREl) prndREl.classList.toggle('active', currentGear === 'R');
    if (prndNEl) prndNEl.classList.toggle('active', currentGear === 'N');
    if (prndDEl) prndDEl.classList.toggle('active', currentGear.startsWith('D') || currentGear === 'D');

    // 8. Sürüş Durumu & Eko Skor
    if (telemetryDriveStatus) {
      if ((v.current_speed || 0) < 0.5) {
        telemetryDriveStatus.textContent = '🔴 PARK / RÖLANTİ';
        telemetryDriveStatus.style.color = '#94a3b8';
      } else if (v.brake_pressed) {
        telemetryDriveStatus.textContent = '🛑 FRENLEME REJİMİ';
        telemetryDriveStatus.style.color = '#f43f5e';
      } else if (v.current_speed > 90) {
        telemetryDriveStatus.textContent = '🟢 OTOYOL SEYRİ';
        telemetryDriveStatus.style.color = '#00d2ff';
      } else {
        telemetryDriveStatus.textContent = '🟢 ŞEHİR İÇİ SEYRİ';
        telemetryDriveStatus.style.color = '#10b981';
      }
    }
    if (telemetryEcoScoreVal) {
      telemetryEcoScoreVal.textContent = `%${v.eco_score || 94} (İdeal)`;
    }

    // 9. DOMAIN 1: ENERJİ, BATARYA & YAKIT TELEMETRİSİ
    if (v.powertrain === 'ev' || v.is_ev) {
      const soc = v.battery_soc !== undefined && v.battery_soc !== null ? v.battery_soc : 94.2;
      const soh = v.battery_soh !== undefined && v.battery_soh !== null ? v.battery_soh : 99.0;
      const range = v.remaining_range_km || Math.round((soc / 100) * 450);
      const cons = v.instant_consumption || 16.8;

      if (domainEnergyTitle) domainEnergyTitle.innerHTML = '⚡ HV BATARYA & ENERJİ YÖNETİMİ';
      if (domainEnergyPgn) domainEnergyPgn.textContent = 'PGN 0xFE56 (HVS) · 10 Hz';
      
      if (kpiEnergyLevelLabel) kpiEnergyLevelLabel.textContent = 'BATARYA ŞARJI (SOC)';
      if (kpiEnergyLevelVal) { kpiEnergyLevelVal.textContent = `%${soc.toFixed(1)}`; kpiEnergyLevelVal.style.color = '#10b981'; }
      if (kpiEnergyLevelSub) kpiEnergyLevelSub.textContent = `Sağlık (SOH): %${soh.toFixed(1)}`;

      if (kpiRangeLabel) kpiRangeLabel.textContent = 'KALAN ELEKTRİK MENZİLİ';
      if (kpiRangeVal) { kpiRangeVal.textContent = `${range} km`; kpiRangeVal.style.color = '#00d2ff'; }
      if (kpiConsumptionVal) kpiConsumptionVal.textContent = `Anlık: ${cons.toFixed(1)} kWh/100km`;

      if (kpiSecondaryEnergyLabel) kpiSecondaryEnergyLabel.textContent = 'BATARYA SICAKLIĞI';
      if (kpiSecondaryEnergyVal) { kpiSecondaryEnergyVal.textContent = `${(v.battery_temp_c || 28.5).toFixed(1)} °C`; kpiSecondaryEnergyVal.style.color = '#a855f7'; }
      if (kpiSecondaryEnergySub) kpiSecondaryEnergySub.textContent = 'Optimum Termal Aralık';

      if (kpiElectricalLabel) kpiElectricalLabel.textContent = 'HV PAKET VOLTAJ & AKIM';
      if (kpiElectricalVal) { kpiElectricalVal.textContent = `${(v.battery_voltage || 395.2).toFixed(1)} V`; kpiElectricalVal.style.color = '#f59e0b'; }
      if (kpiElectricalSub) kpiElectricalSub.textContent = `Çekilen Akım: ${(v.battery_current || 36.4).toFixed(1)} A`;

    } else if (v.powertrain === 'hybrid') {
      const soc = v.battery_soc !== undefined && v.battery_soc !== null ? v.battery_soc : 65.0;
      const fuel = v.fuel_level_pct !== undefined && v.fuel_level_pct !== null ? v.fuel_level_pct : 82.0;
      const range = v.remaining_range_km || Math.round((fuel / 100) * 750 + (soc / 100) * 50);
      const cons = v.instant_consumption || 4.5;

      if (domainEnergyTitle) domainEnergyTitle.innerHTML = '🌿 HİBRİT BATARYA & YAKIT TELEMETRİSİ';
      if (domainEnergyPgn) domainEnergyPgn.textContent = 'PGN 0xFE56 & 0xFEFC';

      if (kpiEnergyLevelLabel) kpiEnergyLevelLabel.textContent = 'HEV BATARYA (SOC)';
      if (kpiEnergyLevelVal) { kpiEnergyLevelVal.textContent = `%${soc.toFixed(1)}`; kpiEnergyLevelVal.style.color = '#10b981'; }
      if (kpiEnergyLevelSub) kpiEnergyLevelSub.textContent = `Yakıt Deposu: %${fuel.toFixed(1)}`;

      if (kpiRangeLabel) kpiRangeLabel.textContent = 'KALAN HİBRİT MENZİL';
      if (kpiRangeVal) { kpiRangeVal.textContent = `${range} km`; kpiRangeVal.style.color = '#00d2ff'; }
      if (kpiConsumptionVal) kpiConsumptionVal.textContent = `Ortalama: ${cons.toFixed(1)} L/100km`;

      if (kpiSecondaryEnergyLabel) kpiSecondaryEnergyLabel.textContent = 'YAKIT DEPOSU (SPN 96)';
      if (kpiSecondaryEnergyVal) { kpiSecondaryEnergyVal.textContent = `%${fuel.toFixed(1)}`; kpiSecondaryEnergyVal.style.color = '#f59e0b'; }
      if (kpiSecondaryEnergySub) kpiSecondaryEnergySub.textContent = 'Dahili Yakıt Kapasitesi';

      if (kpiElectricalLabel) kpiElectricalLabel.textContent = '12V SİSTEM AKÜSÜ';
      if (kpiElectricalVal) { kpiElectricalVal.textContent = `${(v.battery_12v || 14.1).toFixed(1)} V`; kpiElectricalVal.style.color = '#10b981'; }
      if (kpiElectricalSub) kpiElectricalSub.textContent = 'DC-DC Dönüştürücü Devrede';

    } else {
      const fuel = v.fuel_level_pct !== undefined && v.fuel_level_pct !== null ? v.fuel_level_pct : 85.0;
      const range = v.remaining_range_km || Math.round((fuel / 100) * 820);
      const cons = v.instant_consumption || 6.2;
      const hasAdblue = v.adblue_pct !== undefined && v.adblue_pct !== null;

      if (domainEnergyTitle) domainEnergyTitle.innerHTML = '⛽ YAKIT DEPOSU & AKÜ TELEMETRİSİ';
      if (domainEnergyPgn) domainEnergyPgn.textContent = 'PGN 0xFEFC (DASH) · SPN 96';

      if (kpiEnergyLevelLabel) kpiEnergyLevelLabel.textContent = 'YAKIT DEPOSU (SPN 96)';
      if (kpiEnergyLevelVal) { kpiEnergyLevelVal.textContent = `%${fuel.toFixed(1)}`; kpiEnergyLevelVal.style.color = '#f59e0b'; }
      if (kpiEnergyLevelSub) kpiEnergyLevelSub.textContent = 'Yakıt Seviyesi Normal';

      if (kpiRangeLabel) kpiRangeLabel.textContent = 'TAHMİNİ KALAN MENZİL';
      if (kpiRangeVal) { kpiRangeVal.textContent = `${range} km`; kpiRangeVal.style.color = '#00d2ff'; }
      if (kpiConsumptionVal) kpiConsumptionVal.textContent = `Anlık: ${cons.toFixed(1)} L/100km`;

      if (kpiSecondaryEnergyLabel) kpiSecondaryEnergyLabel.textContent = hasAdblue ? 'ADBLUE / DEF SEVİYESİ' : '12V SİSTEM AKÜSÜ';
      if (kpiSecondaryEnergyVal) {
        kpiSecondaryEnergyVal.textContent = hasAdblue ? `%${v.adblue_pct.toFixed(1)}` : `${(v.battery_12v || 14.2).toFixed(1)} V`;
        kpiSecondaryEnergyVal.style.color = hasAdblue ? '#00d2ff' : '#10b981';
      }
      if (kpiSecondaryEnergySub) kpiSecondaryEnergySub.textContent = hasAdblue ? 'SPN 1761 Emisyon Sıvısı' : 'SPN 168 Şarj Voltajı';

      if (kpiElectricalLabel) kpiElectricalLabel.textContent = 'ALTERNATÖR & ŞARJ DURUMU';
      if (kpiElectricalVal) { kpiElectricalVal.textContent = `${(v.battery_12v || 14.2).toFixed(1)} V`; kpiElectricalVal.style.color = '#10b981'; }
      if (kpiElectricalSub) kpiElectricalSub.textContent = 'Şarj Devresi Aktif (14.2V)';
    }

    // 10. DOMAIN 2: MOTOR & MEKANİK SAĞLIK
    if (kpiCoolantVal) kpiCoolantVal.textContent = `${(v.coolant_temp_c || 88.5).toFixed(1)} °C`;
    if (kpiOilVal) {
      if (v.powertrain === 'ev' || v.is_ev) {
        kpiOilVal.textContent = 'N/A (Elektrikli)';
        kpiOilVal.style.color = '#94a3b8';
      } else {
        kpiOilVal.textContent = `${(v.oil_temp_c || 92.0).toFixed(1)} °C · ${(v.oil_pressure_bar || 3.8).toFixed(1)} bar`;
        kpiOilVal.style.color = '#f59e0b';
      }
    }
    if (kpiTransTempVal) kpiTransTempVal.textContent = `${(v.transmission_temp_c || 74.2).toFixed(1)} °C`;
    if (kpiEngineHoursVal) kpiEngineHoursVal.textContent = `${(v.engine_hours || 1285.4).toFixed(1)} h`;

    // 11. DOMAIN 3: ODOMETRE, SEYAHAT & GPS KONUM
    if (kpiOdometerVal) {
      const odo = v.odometer_km || 48290.4;
      kpiOdometerVal.textContent = `${odo.toLocaleString('tr-TR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} km`;
    }
    if (kpiTripVal) kpiTripVal.textContent = `${(v.trip_km || 142.8).toFixed(1)} km`;
    if (kpiGpsCoordsVal) kpiGpsCoordsVal.textContent = `${v.gps_lat || '40.9850'}° N, ${v.gps_lng || '29.0820'}° E`;
    if (kpiGpsLocName) kpiGpsLocName.textContent = v.gps_location_name || 'TEM Otoyolu / İstanbul';
    if (kpiDtcVal) kpiDtcVal.textContent = '0 HATA (TEMİZ)';

    // 12. DOMAIN 4: GÜVENLİK & TPMS
    if (safetyTpmsVal) safetyTpmsVal.textContent = `${v.tpms_bar || 2.3} bar (Ön & Arka Dengeli)`;
    if (safetyDoorsVal) safetyDoorsVal.textContent = `${v.doors_locked ? 'Kapılar Kilitli' : 'Kapılar Açık'} · ${v.seatbelt_ok !== false ? 'Kemerler Takılı' : 'Kemer İkazı'}`;

    // 13. J1939 CAN Inspector
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

    const rawSpeed = Math.round((v.current_speed || 0) * 256);
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
          SPN 84 Hız = <strong>${(v.current_speed || 0).toFixed(2)} km/h</strong> | 
          SPN 190 Motor Devri = <strong>${rpmVal} RPM</strong> | 
          SPN 91 Gaz = <strong>%${throttlePct.toFixed(1)}</strong> | 
          SPN 3543 Batarya = <strong>%${(v.battery_soc || 95).toFixed(1)}</strong>
        `;
      } else {
        spnFormulaHintEl.innerHTML = `
          SPN 84 Hız = <strong>${(v.current_speed || 0).toFixed(2)} km/h</strong> | 
          SPN 190 Motor Devri = <strong>${rpmVal} RPM</strong> | 
          SPN 91 Gaz = <strong>%${throttlePct.toFixed(1)}</strong> | 
          SPN 110 Hararet = <strong>${(v.coolant_temp_c || 88.5).toFixed(1)} °C</strong>
        `;
      }
    }
  }

  // 6. Doğrudan Tarayıcıdan Araç Fotoğrafı Yükleme (Web UI File Upload)
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

  // 7. Merkezi Araç Silme / Kaldırma Fonksiyonu ve Buton Bağlantısı
  async function removeVehicleById(vehicleId) {
    const v = fleet.find(item => item.id === vehicleId);
    if (!v) {
      alert('Kaldırılacak araç bulunamadı.');
      return;
    }

    const confirmMsg = `"${v.brand_name} ${v.model} (${v.plate})"\n\nBu aracı filodan kaldırmak istediğinize emin misiniz?`;
    if (!confirm(confirmMsg)) {
      return;
    }

    try {
      const res = await fetch(`/api/vehicle/${v.id}`, {
        method: 'DELETE'
      });
      const data = await res.json();
      if (res.ok && data.status === 'ok') {
        fleet = fleet.filter(item => item.id !== v.id);
        if (selectedVehicleId === v.id) {
          selectedVehicleId = fleet.length > 0 ? fleet[0].id : null;
        }
        renderBrandFilters();
        renderFleetGrid();
        updateSelectedVehicleView();
        alert(`✅ "${v.brand_name} ${v.model}" başarıyla filodan kaldırıldı.`);
      } else {
        alert(`❌ Araç kaldırılamadı: ${data.detail || data.message || 'Bilinmeyen hata'}`);
      }
    } catch (err) {
      console.error('Araç silme hatası:', err);
      alert(`❌ Araç kaldırılırken hata oluştu: ${err.message}`);
    }
  }

  const btnDeleteVehicle = document.getElementById('btnDeleteVehicle');
  if (btnDeleteVehicle) {
    btnDeleteVehicle.addEventListener('click', () => {
      if (selectedVehicleId) {
        removeVehicleById(selectedVehicleId);
      }
    });
  }

  // 8. Tüm Filo Telematik Verilerini CSV Raporu Olarak İndirme
  if (btnExportFleetTelematics) {
    btnExportFleetTelematics.addEventListener('click', () => {
      if (fleet.length === 0) {
        alert('Dışa aktarılacak telematik verisi yok!');
        return;
      }

      const headers = [
        'Plaka', 'Marka', 'Model', 'Kategori', 'Aktarma_Organi', 'J1939_SA',
        'Hiz_kmh', 'Motor_Devri_RPM', 'Vites', 'Gaz_Pedali_Pct', 'Fren_Pedali_Pct',
        'Motor_Yuku_Pct', 'Sogutma_Suyu_C', 'Yag_Sicakligi_C', 'Yag_Basinci_bar',
        'Sanziman_Sicakligi_C', 'Batarya_SOC_Pct', 'Batarya_SOH_Pct', 'Yakit_Deposu_Pct',
        'Kalan_Menzil_km', 'Anlik_Tuketim', 'Toplam_Odometre_km', 'Gunluk_Trip_km',
        'Motor_Calisma_Saati_h', 'Eko_Skor', 'DTC_Ariza_Sayisi', 'GPS_Enlem', 'GPS_Boylam', 'Konum_Adi'
      ];

      const rows = fleet.map(v => [
        `"${v.plate || ''}"`,
        `"${v.brand_name || ''}"`,
        `"${v.model || ''}"`,
        `"${v.category || ''}"`,
        `"${v.powertrain || ''}"`,
        `"0x${(v.source_address || 0).toString(16).toUpperCase().padStart(2, '0')}"`,
        (v.current_speed || 0).toFixed(1),
        v.engine_rpm || (v.current_speed > 0.5 ? 2100 : 750),
        `"${v.gear || 'D'}"`,
        (v.throttle_pct || 0).toFixed(1),
        (v.brake_pct || 0).toFixed(1),
        (v.engine_load_pct !== undefined ? v.engine_load_pct : 32.5).toFixed(1),
        (v.coolant_temp_c || 88.5).toFixed(1),
        v.oil_temp_c ? v.oil_temp_c.toFixed(1) : 'N/A',
        v.oil_pressure_bar ? v.oil_pressure_bar.toFixed(1) : 'N/A',
        (v.transmission_temp_c || 74.2).toFixed(1),
        v.battery_soc !== null && v.battery_soc !== undefined ? v.battery_soc.toFixed(1) : 'N/A',
        v.battery_soh !== null && v.battery_soh !== undefined ? v.battery_soh.toFixed(1) : 'N/A',
        v.fuel_level_pct !== null && v.fuel_level_pct !== undefined ? v.fuel_level_pct.toFixed(1) : 'N/A',
        v.remaining_range_km || 450,
        `"${v.instant_consumption || 6.2} ${v.consumption_unit || 'L/100km'}"`,
        (v.odometer_km || 18500).toFixed(1),
        (v.trip_km || 42.5).toFixed(1),
        (v.engine_hours || 640).toFixed(1),
        v.eco_score || 94,
        v.dtc_count || 0,
        v.gps_lat || 40.9850,
        v.gps_lng || 29.0820,
        `"${v.gps_location_name || 'TEM Otoyolu'}"`
      ]);

      const csvContent = 'data:text/csv;charset=utf-8,\uFEFF' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
      const encodedUri = encodeURI(csvContent);
      const link = document.createElement('a');
      link.setAttribute('href', encodedUri);
      link.setAttribute('download', `j1939_filo_telematik_raporu_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    });
  }

  // 9. CAN Sniffer
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
    const csvContent = 'data:text/csv;charset=utf-8,\uFEFF' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `j1939_can_sniffer_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  });

  // 10. YENİ ARAÇ EKLEME MODAL VE FORM YÖNETİMİ
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
      formData.append('default_speed', 110);
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

  // 11. FİLODAN ARAÇ ÇIKARMA MODAL YÖNETİMİ
  const btnOpenRemoveVehicleModal = document.getElementById('btnOpenRemoveVehicleModal');
  const removeVehicleModal = document.getElementById('removeVehicleModal');
  const btnCloseRemoveModal = document.getElementById('btnCloseRemoveModal');
  const btnCancelRemoveModal = document.getElementById('btnCancelRemoveModal');
  const removeVehicleForm = document.getElementById('removeVehicleForm');
  const removeVehicleSelect = document.getElementById('removeVehicleSelect');
  const removePreviewImg = document.getElementById('removePreviewImg');
  const removePreviewTitle = document.getElementById('removePreviewTitle');
  const removePreviewSub = document.getElementById('removePreviewSub');
  const removePreviewBadge = document.getElementById('removePreviewBadge');

  function updateRemoveVehiclePreview() {
    if (!removeVehicleSelect) return;
    const targetId = removeVehicleSelect.value;
    const v = fleet.find(item => item.id === targetId);
    if (!v) return;

    if (removePreviewImg) {
      removePreviewImg.src = v.image_url || `/static/images/cars/${v.id}.jpg`;
    }
    if (removePreviewTitle) {
      removePreviewTitle.textContent = `${v.brand_name} ${v.model}`;
    }
    if (removePreviewSub) {
      const saHex = `0x${v.source_address.toString(16).toUpperCase().padStart(2, '0')}`;
      removePreviewSub.textContent = `${v.plate} · SA: ${saHex} · ${v.category}`;
    }
    if (removePreviewBadge) {
      if (v.powertrain === 'ev' || v.is_ev) {
        removePreviewBadge.textContent = '⚡ %100 Elektrikli (EV)';
        removePreviewBadge.style.color = '#10b981';
      } else if (v.powertrain === 'hybrid') {
        removePreviewBadge.textContent = '🌿 Hibrit (HEV)';
        removePreviewBadge.style.color = '#10b981';
      } else {
        const isDiesel = v.engine && v.engine.toLowerCase().includes('dizel');
        removePreviewBadge.textContent = isDiesel ? '⛽ Dizel (ICE)' : '⛽ Benzinli (ICE)';
        removePreviewBadge.style.color = '#f59e0b';
      }
    }
  }

  function openRemoveVehicleModal() {
    if (fleet.length === 0) {
      alert('Filoda çıkarılacak araç bulunmuyor.');
      return;
    }

    removeVehicleSelect.innerHTML = '';
    fleet.forEach(v => {
      const opt = document.createElement('option');
      opt.value = v.id;
      const saHex = `0x${v.source_address.toString(16).toUpperCase().padStart(2, '0')}`;
      opt.textContent = `${v.brand_name} ${v.model} (${v.plate} - SA: ${saHex})`;
      if (v.id === selectedVehicleId) {
        opt.selected = true;
      }
      removeVehicleSelect.appendChild(opt);
    });

    updateRemoveVehiclePreview();
    removeVehicleModal.style.display = 'flex';
  }

  function closeRemoveVehicleModal() {
    if (removeVehicleModal) {
      removeVehicleModal.style.display = 'none';
    }
  }

  if (btnOpenRemoveVehicleModal) {
    btnOpenRemoveVehicleModal.addEventListener('click', openRemoveVehicleModal);
  }
  if (btnCloseRemoveModal) {
    btnCloseRemoveModal.addEventListener('click', closeRemoveVehicleModal);
  }
  if (btnCancelRemoveModal) {
    btnCancelRemoveModal.addEventListener('click', closeRemoveVehicleModal);
  }
  if (removeVehicleModal) {
    removeVehicleModal.addEventListener('click', (e) => {
      if (e.target === removeVehicleModal) {
        closeRemoveVehicleModal();
      }
    });
  }
  if (removeVehicleSelect) {
    removeVehicleSelect.addEventListener('change', updateRemoveVehiclePreview);
  }

  if (removeVehicleForm) {
    removeVehicleForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const targetId = removeVehicleSelect.value;
      if (!targetId) return;

      closeRemoveVehicleModal();
      await removeVehicleById(targetId);
    });
  }

  initWebSocket();
});
