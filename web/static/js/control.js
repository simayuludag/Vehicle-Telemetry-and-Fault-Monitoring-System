/**
 * J1939 Signal Transmitter & Fleet Speed Control Deck (Environment 1)
 */

document.addEventListener('DOMContentLoaded', () => {
  let fleet = [];
  let brands = [];
  let selectedVehicleId = 'bmw-320i';
  let activeBrandFilter = 'all';
  let ws = null;

  // DOM Elements
  const fleetGridEl = document.getElementById('fleetGrid');
  const brandFiltersEl = document.getElementById('brandFilters');
  const ctrlVehicleNameEl = document.getElementById('ctrlVehicleName');
  const ctrlVehicleDetailsEl = document.getElementById('ctrlVehicleDetails');
  const targetSaTagEl = document.getElementById('targetSaTag');
  const targetSpeedDisplayEl = document.getElementById('targetSpeedDisplay');
  const mainSpeedSliderEl = document.getElementById('mainSpeedSlider');
  const masterSpeedSliderEl = document.getElementById('masterSpeedSlider');
  const masterSpeedValEl = document.getElementById('masterSpeedVal');
  const txCanFramePreviewEl = document.getElementById('txCanFramePreview');
  const btnThrottleEl = document.getElementById('btnThrottle');
  const btnBrakeEl = document.getElementById('btnBrake');
  const btnEmergencyStopEl = document.getElementById('btnEmergencyStop');
  const wsStatusDot = document.getElementById('wsStatusDot');
  const wsStatusText = document.getElementById('wsStatusText');

  // WebSocket Connection
  function initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/telemetry`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      wsStatusDot.style.background = '#10b981';
      wsStatusDot.style.boxShadow = '0 0 10px #10b981';
      wsStatusText.textContent = 'ONLINE (TX READY)';
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
        }
      } catch (err) {
        console.error('WS parse error:', err);
      }
    };

    ws.onclose = () => {
      wsStatusDot.style.background = '#f43f5e';
      wsStatusDot.style.boxShadow = '0 0 10px #f43f5e';
      wsStatusText.textContent = 'RECONNECTING...';
      setTimeout(initWebSocket, 2000);
    };
  }

  // Render Brands
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

  // Render Fleet Grid
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

        <div class="card-quick-controls">
          <button class="btn-card-accel" id="card-accel-${v.id}">⚡ +10 Hız Ver</button>
          <button class="btn-card-brake" id="card-brake-${v.id}">🛑 -15 Fren</button>
        </div>
      `;

      card.addEventListener('click', (e) => {
        if (e.target.tagName.toLowerCase() === 'button') return;
        selectVehicle(v.id);
      });

      card.querySelector(`#card-accel-${v.id}`).addEventListener('click', (e) => {
        e.stopPropagation();
        selectVehicle(v.id);
        sendAccelerateCommand(v.id, 10.0);
      });

      card.querySelector(`#card-brake-${v.id}`).addEventListener('click', (e) => {
        e.stopPropagation();
        selectVehicle(v.id);
        sendDecelerateCommand(v.id, 15.0);
      });

      fleetGridEl.appendChild(card);
    });
  }

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

    ctrlVehicleNameEl.textContent = `${v.brand_name} ${v.model}`;
    ctrlVehicleDetailsEl.textContent = `${v.plate} · ${v.engine} · Maks: ${v.max_speed} km/h`;
    targetSaTagEl.textContent = `SA: 0x${v.source_address.toString(16).toUpperCase().padStart(2, '0')}`;

    mainSpeedSliderEl.max = v.max_speed;
    mainSpeedSliderEl.value = Math.round(v.target_speed);
    targetSpeedDisplayEl.textContent = Math.round(v.target_speed);

    // Frame Preview
    const rawSpeed = Math.round(v.target_speed * 256);
    const b1 = (rawSpeed & 0xFF).toString(16).toUpperCase().padStart(2, '0');
    const b2 = ((rawSpeed >> 8) & 0xFF).toString(16).toUpperCase().padStart(2, '0');
    const saHex = v.source_address.toString(16).toUpperCase().padStart(2, '0');
    const canIdHex = `0x18FEF1${saHex}`;

    txCanFramePreviewEl.textContent = `CAN ID: ${canIdHex} | PGN: 0xFEF1 (CCVS) | SPN 84 Hız: ${v.target_speed.toFixed(2)} km/h | Data: FF ${b1} ${b2} FF FF FF FF FF`;
  }

  // Send Commands
  function sendSpeedCommand(vehicleId, speed) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        action: 'set_speed',
        vehicle_id: vehicleId,
        speed: speed
      }));
    } else {
      fetch(`/api/vehicle/${vehicleId}/speed`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ speed: speed, mode: 'manual' })
      });
    }
  }

  function sendAccelerateCommand(vehicleId, delta = 10.0) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        action: 'accelerate',
        vehicle_id: vehicleId,
        delta: delta
      }));
    }
  }

  function sendDecelerateCommand(vehicleId, delta = 15.0) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        action: 'decelerate',
        vehicle_id: vehicleId,
        delta: delta
      }));
    }
  }

  function sendScenarioCommand(scenario) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        action: 'set_scenario',
        scenario: scenario
      }));
    } else {
      fetch('/api/fleet/scenario', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario: scenario })
      });
    }
  }

  function sendMasterFleetSpeed(speed) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        action: 'set_fleet_speed',
        speed: speed
      }));
    } else {
      fetch('/api/fleet/speed', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ speed: speed })
      });
    }
  }

  // Event Listeners
  mainSpeedSliderEl.addEventListener('input', (e) => {
    const spd = parseFloat(e.target.value);
    targetSpeedDisplayEl.textContent = Math.round(spd);
    sendSpeedCommand(selectedVehicleId, spd);
  });

  document.querySelectorAll('.btn-preset').forEach(btn => {
    btn.addEventListener('click', () => {
      const spd = parseFloat(btn.dataset.speed);
      mainSpeedSliderEl.value = spd;
      targetSpeedDisplayEl.textContent = spd;
      sendSpeedCommand(selectedVehicleId, spd);
    });
  });

  btnThrottleEl.addEventListener('click', () => {
    sendAccelerateCommand(selectedVehicleId, 10.0);
  });

  btnBrakeEl.addEventListener('click', () => {
    sendDecelerateCommand(selectedVehicleId, 15.0);
  });

  document.querySelectorAll('.btn-scenario').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.btn-scenario').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const scen = btn.dataset.scenario;
      sendScenarioCommand(scen);
    });
  });

  masterSpeedSliderEl.addEventListener('input', (e) => {
    const spd = parseFloat(e.target.value);
    masterSpeedValEl.textContent = `${Math.round(spd)} KM/H`;
    sendMasterFleetSpeed(spd);
  });

  btnEmergencyStopEl.addEventListener('click', () => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: 'emergency_stop' }));
    } else {
      fetch('/api/fleet/emergency-stop', { method: 'POST' });
    }
  });

  initWebSocket();
});
