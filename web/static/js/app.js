/**
 * J1939 Multi-Signal Fleet Telemetry & Central Controller
 * Features: Live Internet Vehicle Photos, Speed (SPN 84), Throttle (SPN 91), Brake (SPN 563), Gear (SPN 523), Battery (SPN 3543/5328)
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
  const showcaseVehicleNameEl = document.getElementById('showcaseVehicleName');
  const showcaseVehicleSpecsEl = document.getElementById('showcaseVehicleSpecs');
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
  const batterySocTextEl = document.getElementById('batterySocText');
  const batterySohTextEl = document.getElementById('batterySohText');

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

  // 3. 30 Araçlık Izgarayı (Grid) Fotoğraflarla Oluştur
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

      const imgUrl = v.image_url || 'https://images.unsplash.com/photo-1555215695-3004980ad54e?auto=format&fit=crop&w=800&q=80';

      card.innerHTML = `
        <div class="card-thumb-wrap">
          <img src="${imgUrl}" class="card-thumb-img" alt="${v.model}" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1555215695-3004980ad54e?auto=format&fit=crop&w=800&q=80'">
          <div class="card-thumb-overlay"></div>
          <span class="card-brand-badge-overlay" style="border-left: 3px solid ${brand.color}">${v.brand_name}</span>
          <span class="card-sa-badge-overlay">SA: 0x${v.source_address.toString(16).toUpperCase().padStart(2, '0')}</span>
        </div>
        
        <div class="vehicle-model-name">${v.model}</div>
        <div class="vehicle-plate">${v.plate} · ${v.category}</div>
        
        <div class="vehicle-speed-row">
          <div class="speed-digital-display">
            <span class="speed-num" id="speed-num-${v.id}">${Math.round(v.current_speed)}</span>
            <span class="unit" style="font-size:0.75rem; color:#00d2ff; font-family:'JetBrains Mono', monospace">KM/H</span>
          </div>
          <div class="status-badge ${v.status}" id="status-badge-${v.id}">${v.status}</div>
        </div>

        <div class="card-signals-pill-row" style="display:flex; gap:6px; margin-top:2px; font-family:'JetBrains Mono', monospace; font-size:0.72rem">
          <span style="background:rgba(0,0,0,0.5); padding:2px 6px; border-radius:4px; border:1px solid rgba(255,255,255,0.08); color:#f59e0b; font-weight:700" id="badge-gear-${v.id}">🕹️ ${v.gear || 'D'}</span>
          <span style="background:rgba(0,0,0,0.5); padding:2px 6px; border-radius:4px; border:1px solid rgba(255,255,255,0.08); color:#10b981" id="badge-soc-${v.id}">🔋 %${Math.round(v.battery_soc || 90)}</span>
          <span style="background:rgba(0,0,0,0.5); padding:2px 6px; border-radius:4px; border:1px solid rgba(255,255,255,0.08); color:#00d2ff" id="badge-throttle-${v.id}">⚡ %${Math.round(v.throttle_pct || 0)}</span>
        </div>

        <div class="speed-bar-track" style="height:5px; background:rgba(255,255,255,0.08); border-radius:4px; overflow:hidden; margin-top:3px">
          <div class="speed-bar-fill" id="speed-bar-${v.id}" style="width: ${(v.current_speed / v.max_speed) * 100}%; height:100%; background:linear-gradient(90deg, #00d2ff, #10b981); border-radius:4px"></div>
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
      const socEl = document.getElementById(`badge-soc-${v.id}`);
      const throttleEl = document.getElementById(`badge-throttle-${v.id}`);

      if (numEl) numEl.textContent = Math.round(v.current_speed);
      if (barEl) barEl.style.width = `${Math.min(100, (v.current_speed / v.max_speed) * 100)}%`;
      if (badgeEl) {
        badgeEl.className = `status-badge ${v.status}`;
        badgeEl.textContent = v.status;
      }
      if (gearEl) gearEl.textContent = `🕹️ ${v.gear || 'D'}`;
      if (socEl) socEl.textContent = `🔋 %${Math.round(v.battery_soc || 90)}`;
      if (throttleEl) throttleEl.textContent = `⚡ %${Math.round(v.throttle_pct || 0)}`;
    });
  }

  // 5. Araç Seçimi & Kokpit HUD ve Fotoğrafını Güncelleme
  function selectVehicle(vehicleId) {
    selectedVehicleId = vehicleId;
    document.querySelectorAll('.vehicle-card').forEach(c => {
      c.classList.toggle('selected', c.dataset.id === vehicleId);
    });
    updateSelectedVehicleView();
  }

  function updateSelectedVehicleView() {
    const v = fleet.find(item => item.id === selectedVehicleId);
    if (!v) return;

    // 1. Araç Fotoğrafını ve Başlığını Güncelle
    if (activeVehiclePhotoEl) {
      activeVehiclePhotoEl.src = v.image_url || 'https://images.unsplash.com/photo-1555215695-3004980ad54e?auto=format&fit=crop&w=800&q=80';
      activeVehiclePhotoEl.alt = `${v.brand_name} ${v.model}`;
    }
    if (showcaseVehicleNameEl) showcaseVehicleNameEl.textContent = `${v.brand_name} ${v.model}`;
    if (showcaseVehicleSpecsEl) showcaseVehicleSpecsEl.textContent = `${v.plate} · ${v.engine} · SA: 0x${v.source_address.toString(16).toUpperCase().padStart(2, '0')}`;

    if (isFleetMode) {
      if (showcaseVehicleNameEl) showcaseVehicleNameEl.textContent = `🌐 TÜM FİLO (30 ARAÇ) MASTER KONTROLÜ`;
      activeScopePillEl.textContent = 'MASTER FİLO';
      activeScopePillEl.style.borderColor = '#f59e0b';
      activeScopePillEl.style.color = '#f59e0b';
    } else {
      activeScopePillEl.textContent = 'SEÇİLİ ARAÇ';
      activeScopePillEl.style.borderColor = '#00d2ff';
      activeScopePillEl.style.color = '#00d2ff';
    }

    // 2. Hız Kadranı
    gauge.setSpeed(v.current_speed, v.max_speed);

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

    // 6. Batarya SOC / SOH
    const soc = v.battery_soc !== undefined ? v.battery_soc : 95.0;
    const soh = v.battery_soh !== undefined ? v.battery_soh : 99.0;
    if (batterySocTextEl) batterySocTextEl.textContent = `%${soc.toFixed(1)}`;
    if (batterySohTextEl) batterySohTextEl.textContent = `%${soh.toFixed(1)} ${soh >= 95 ? 'Mükemmel' : 'İyi'}`;

    // 7. Hız Slider'ı
    if (speedSliderEl && !speedSliderEl.matches(':active')) {
      speedSliderEl.max = v.max_speed;
      speedSliderEl.value = Math.round(v.target_speed);
      speedSliderValEl.textContent = `${Math.round(v.target_speed)} KM/H`;
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
      spnFormulaHintEl.innerHTML = `
        SPN 84 Hız = <strong>${v.current_speed.toFixed(2)} km/h</strong> | 
        SPN 91 Gaz = <strong>%${throttlePct.toFixed(1)}</strong> | 
        SPN 523 Vites = <strong>${currentGear}</strong> | 
        SPN 3543 Batarya = <strong>%${soc.toFixed(1)}</strong>
      `;
    }
  }

  // 6. Komut Gönderme Fonksiyonları
  function applySpeed(speed) {
    if (isFleetMode) {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'set_fleet_speed', speed: speed }));
      } else {
        fetch('/api/fleet/speed', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ speed: speed })
        });
      }
    } else {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'set_speed', vehicle_id: selectedVehicleId, speed: speed }));
      } else {
        fetch(`/api/vehicle/${selectedVehicleId}/speed`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ speed: speed, mode: 'manual' })
        });
      }
    }
  }

  function applyAccelerate(delta = 10.0) {
    if (isFleetMode) {
      const v = fleet.find(item => item.id === selectedVehicleId);
      const currentTarget = v ? v.target_speed : 90.0;
      applySpeed(currentTarget + delta);
    } else {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'accelerate', vehicle_id: selectedVehicleId, delta: delta }));
      }
    }
  }

  function applyDecelerate(delta = 15.0) {
    if (isFleetMode) {
      const v = fleet.find(item => item.id === selectedVehicleId);
      const currentTarget = v ? v.target_speed : 90.0;
      applySpeed(Math.max(0, currentTarget - delta));
    } else {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'decelerate', vehicle_id: selectedVehicleId, delta: delta }));
      }
    }
  }

  function applyFullStop() {
    if (isFleetMode) {
      applySpeed(0.0);
    } else {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'full_stop', vehicle_id: selectedVehicleId }));
      }
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
    updateSelectedVehicleView();
  });

  tabFleetModeEl.addEventListener('click', () => {
    isFleetMode = true;
    tabFleetModeEl.classList.add('active');
    tabSingleVehicleEl.classList.remove('active');
    sliderLabelEl.textContent = 'Filo Hedef Hızı:';
    updateSelectedVehicleView();
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

  initWebSocket();
});
