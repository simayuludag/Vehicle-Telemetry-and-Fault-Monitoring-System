/**
 * J1939 Fleet Telemetry & Central Speed Controller
 * Single Unified Speed Control Deck for 30 Vehicles
 */

document.addEventListener('DOMContentLoaded', () => {
  // Global State
  let fleet = [];
  let brands = [];
  let selectedVehicleId = 'bmw-320i';
  let activeBrandFilter = 'all';
  let isFleetMode = false; // false: Seçili Araç, true: Tüm Filo
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
  const activeVehicleTitleEl = document.getElementById('activeVehicleTitle');
  const activeVehicleDetailsEl = document.getElementById('activeVehicleDetails');
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

  // CAN Inspector DOM Elemanları
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

  // 3. 30 Araçlık Izgarayı (Grid) Oluştur (Temiz & Geniş Kartlar)
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

      card.innerHTML = `
        <div class="vehicle-card-header">
          <div class="brand-tag">
            <span class="brand-color-indicator" style="background:${brand.color}; box-shadow:0 0 8px ${brand.color}"></span>
            ${v.brand_name}
          </div>
          <div class="j1939-sa-tag">SA: 0x${v.source_address.toString(16).toUpperCase().padStart(2, '0')}</div>
        </div>
        <div class="vehicle-model-name">${v.model}</div>
        <div class="vehicle-plate">${v.plate} · ${v.category}</div>
        
        <div class="vehicle-speed-row">
          <div class="speed-digital-display">
            <span class="speed-num" id="speed-num-${v.id}">${Math.round(v.current_speed)}</span>
            <span class="unit">KM/H</span>
          </div>
          <div class="status-badge ${v.status}" id="status-badge-${v.id}">${v.status}</div>
        </div>

        <div class="speed-bar-track">
          <div class="speed-bar-fill" id="speed-bar-${v.id}" style="width: ${(v.current_speed / v.max_speed) * 100}%"></div>
        </div>
      `;

      // Kart Tıklaması -> Tek Merkezden Kontrol Edilen Aracı Değiştirir
      card.addEventListener('click', () => {
        selectVehicle(v.id);
      });

      fleetGridEl.appendChild(card);
    });
  }

  // 4. Canlı Güncelleme
  function updateFleetGridRealtime() {
    fleet.forEach(v => {
      const numEl = document.getElementById(`speed-num-${v.id}`);
      const barEl = document.getElementById(`speed-bar-${v.id}`);
      const badgeEl = document.getElementById(`status-badge-${v.id}`);

      if (numEl) numEl.textContent = Math.round(v.current_speed);
      if (barEl) barEl.style.width = `${Math.min(100, (v.current_speed / v.max_speed) * 100)}%`;
      if (badgeEl) {
        badgeEl.className = `status-badge ${v.status}`;
        badgeEl.textContent = v.status;
      }
    });
  }

  // 5. Araç Seçimi & Kadran Güncelleme
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

    if (isFleetMode) {
      activeVehicleTitleEl.textContent = `🌐 TÜM FİLO KONTROLÜ (30 ARAÇ)`;
      activeVehicleDetailsEl.textContent = `10 Marka Eş Zamanlı Yönetiliyor · Seçili Örnek: ${v.brand_name} ${v.model}`;
      activeScopePillEl.textContent = 'MASTER FİLO KONTROLÜ';
      activeScopePillEl.style.borderColor = 'var(--accent-amber)';
      activeScopePillEl.style.color = 'var(--accent-amber)';
    } else {
      activeVehicleTitleEl.textContent = `${v.brand_name} ${v.model}`;
      activeVehicleDetailsEl.textContent = `${v.plate} · ${v.engine} · J1939 SA: 0x${v.source_address.toString(16).toUpperCase().padStart(2, '0')}`;
      activeScopePillEl.textContent = 'SEÇİLİ ARAÇ KONTROLÜ';
      activeScopePillEl.style.borderColor = 'var(--accent-cyan)';
      activeScopePillEl.style.color = 'var(--accent-cyan)';
    }

    // Kadranı Güncelle
    gauge.setSpeed(v.current_speed, v.max_speed);

    // Hız Slider'ını Güncelle (Sadece kullanıcı slider'ı sürüklemiyorsa)
    if (speedSliderEl && !speedSliderEl.matches(':active')) {
      speedSliderEl.max = v.max_speed;
      speedSliderEl.value = Math.round(v.target_speed);
      speedSliderValEl.textContent = `${Math.round(v.target_speed)} KM/H`;
    }

    // Inspector
    const saHex = `0x${v.source_address.toString(16).toUpperCase().padStart(2, '0')}`;
    const priority = 6;
    const pgn = 65265;
    const canId = (priority << 26) | (pgn << 8) | v.source_address;
    const canIdHex = `0x${canId.toString(16).toUpperCase().padStart(8, '0')}`;

    inspCanIdEl.textContent = canIdHex;
    inspPgnEl.textContent = '0xFEF1 (CCVS)';
    inspPriorityEl.textContent = `${priority} (Normal)`;
    inspSaEl.textContent = saHex;

    const rawSpeed = Math.round(v.current_speed * 256);
    const b1 = rawSpeed & 0xFF;
    const b2 = (rawSpeed >> 8) & 0xFF;
    const bytes = [0xFF, b1, b2, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF];

    hexBytesRowEl.innerHTML = '';
    bytes.forEach((b, idx) => {
      const isSpeedByte = (idx === 1 || idx === 2);
      const div = document.createElement('div');
      div.className = `hex-byte-block ${isSpeedByte ? 'highlight' : ''}`;
      div.innerHTML = `
        <span class="idx">B${idx}</span>
        <span class="val">${b.toString(16).toUpperCase().padStart(2, '0')}</span>
      `;
      hexBytesRowEl.appendChild(div);
    });

    spnFormulaHintEl.innerHTML = `
      SPN 84 Hız = (0x${b2.toString(16).toUpperCase().padStart(2, '0')}${b1.toString(16).toUpperCase().padStart(2, '0')} / 256) = 
      <strong style="color:var(--accent-cyan)">${v.current_speed.toFixed(2)} km/h</strong>
    `;
  }

  // 6. Tek Merkezden Hız ve Fren Komutu Gönderme
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

  // 7. Kontrol Alanı Olay Dinleyicileri

  // Scope Tabları (Seçili Araç vs Tüm Filo)
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

  // Hız Slider'ı
  speedSliderEl.addEventListener('input', (e) => {
    const spd = parseFloat(e.target.value);
    speedSliderValEl.textContent = `${Math.round(spd)} KM/H`;
    applySpeed(spd);
  });

  // Hazır Butonlar
  document.querySelectorAll('.btn-preset').forEach(btn => {
    btn.addEventListener('click', () => {
      const spd = parseFloat(btn.dataset.speed);
      speedSliderEl.value = spd;
      speedSliderValEl.textContent = `${spd} KM/H`;
      applySpeed(spd);
    });
  });

  // Gaz & Fren Pedalları
  btnThrottleEl.addEventListener('click', () => {
    applyAccelerate(10.0);
  });

  btnBrakeGradualEl.addEventListener('click', () => {
    applyDecelerate(15.0);
  });

  btnBrakeFullEl.addEventListener('click', () => {
    applyFullStop();
  });

  // Senaryolar
  document.querySelectorAll('.btn-scenario').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.btn-scenario').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const scen = btn.dataset.scenario;
      applyScenario(scen);
    });
  });

  // Acil Durdurma
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
                    frame.model.toLowerCase().includes(q) ||
                    frame.plate.toLowerCase().includes(q) ||
                    frame.source_address_hex.toLowerCase().includes(q);
      if (!match) return;
    }

    const row = document.createElement('tr');
    const bytes = frame.data_hex.split(' ');
    const formattedBytes = bytes.map((b, idx) => {
      return (idx === 1 || idx === 2) ? `<span class="speed-bytes">${b}</span>` : b;
    }).join(' ');

    row.innerHTML = `
      <td>${frame.formatted_time}</td>
      <td class="can-id-col">${frame.can_id_hex}</td>
      <td class="pgn-col">${frame.pgn_hex}</td>
      <td class="sa-col">${frame.source_address_hex} (${frame.plate})</td>
      <td class="data-hex-col">${formattedBytes}</td>
      <td class="speed-col">${frame.speed_kmh.toFixed(1)} km/h</td>
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
    const headers = ['Zaman', 'CAN_ID', 'PGN', 'SA', 'Plaka', 'Model', 'Hex_Data', 'Hız_KMH'];
    const rows = canLogList.map(f => [
      f.formatted_time,
      f.can_id_hex,
      f.pgn_hex,
      f.source_address_hex,
      `"${f.plate}"`,
      `"${f.model}"`,
      `"${f.data_hex}"`,
      f.speed_kmh
    ]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `j1939_can_log_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  });

  initWebSocket();
});
