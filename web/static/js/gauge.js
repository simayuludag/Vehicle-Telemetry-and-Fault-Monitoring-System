/**
 * High-Performance HTML5 Canvas J1939 Speedometer Gauge
 * Cyber-Automotive Hypercar Instrument Cluster HUD
 */

class SpeedGauge {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');

    this.currentSpeed = 0.0;
    this.targetSpeed = 0.0;
    this.maxSpeed = 220.0;

    // Canvas boyutlarını yüksek çözünürlük (HiDPI) için uyarla
    this.setupHiDPI();

    // Animasyon döngüsünü başlat
    this.animate = this.animate.bind(this);
    requestAnimationFrame(this.animate);
  }

  setupHiDPI() {
    const dpr = window.devicePixelRatio || 1;
    const rect = this.canvas.getBoundingClientRect();
    const width = rect.width || 320;
    const height = rect.height || 190;

    this.canvas.width = width * dpr;
    this.canvas.height = height * dpr;
    this.ctx.scale(dpr, dpr);
    this.width = width;
    this.height = height;
  }

  setSpeed(speed, max = 220.0) {
    const numSpeed = parseFloat(speed) || 0.0;
    const numMax = parseFloat(max) || 220.0;
    this.targetSpeed = Math.max(0, Math.min(numMax, numSpeed));
    this.maxSpeed = numMax;
  }

  animate() {
    // Yumuşak ve akıcı hız geçişi (lerp)
    const diff = this.targetSpeed - this.currentSpeed;
    if (Math.abs(diff) > 0.05) {
      this.currentSpeed += diff * 0.22;
    } else {
      this.currentSpeed = this.targetSpeed;
    }

    this.draw();
    requestAnimationFrame(this.animate);
  }

  draw() {
    const ctx = this.ctx;
    const w = this.width;
    const h = this.height;
    const cx = w / 2;
    const cy = h * 0.74;
    const radius = Math.min(w * 0.40, 115);

    ctx.clearRect(0, 0, w, h);

    const startAngle = Math.PI * 0.80;
    const endAngle = Math.PI * 2.20;
    const totalAngle = endAngle - startAngle;

    // 0. Ambient Arka Plan Işıması (Subtle Radial Glow)
    ctx.save();
    const bgGlow = ctx.createRadialGradient(cx, cy, radius * 0.2, cx, cy, radius * 1.2);
    bgGlow.addColorStop(0, 'rgba(0, 210, 255, 0.06)');
    bgGlow.addColorStop(0.7, 'rgba(0, 210, 255, 0.015)');
    bgGlow.addColorStop(1, 'rgba(0, 0, 0, 0)');
    ctx.fillStyle = bgGlow;
    ctx.beginPath();
    ctx.arc(cx, cy, radius * 1.25, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();

    // 1. Dış İnce Kılavuz Çerçeve (Outer Dial Ring)
    ctx.save();
    ctx.beginPath();
    ctx.arc(cx, cy, radius + 12, startAngle, endAngle);
    ctx.lineWidth = 1.5;
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
    ctx.stroke();
    ctx.restore();

    // 2. Arka Plan Kavisli Ray (Track Base)
    ctx.save();
    ctx.beginPath();
    ctx.arc(cx, cy, radius, startAngle, endAngle);
    ctx.lineWidth = 10;
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.06)';
    ctx.lineCap = 'round';
    ctx.stroke();

    // 3. Aktif Hız Kavisli İlerleme (Glow Progress Arc)
    const speedRatio = Math.max(0, Math.min(1.0, this.currentSpeed / (this.maxSpeed || 220)));
    const currentAngle = startAngle + totalAngle * speedRatio;

    if (this.currentSpeed > 0.1) {
      // Dinamik Çok Kademeli Gradient (Cyan -> Emerald -> Amber -> Crimson)
      const grad = ctx.createLinearGradient(0, cy - radius, w, cy + radius);
      grad.addColorStop(0, '#00d2ff');
      grad.addColorStop(0.45, '#10b981');
      grad.addColorStop(0.75, '#f59e0b');
      grad.addColorStop(1, '#f43f5e');

      // Glow arkası
      ctx.beginPath();
      ctx.arc(cx, cy, radius, startAngle, currentAngle);
      ctx.lineWidth = 10;
      ctx.strokeStyle = grad;
      ctx.lineCap = 'round';
      ctx.shadowColor = speedRatio > 0.75 ? '#f43f5e' : (speedRatio > 0.45 ? '#10b981' : '#00d2ff');
      ctx.shadowBlur = 14;
      ctx.stroke();
    }
    ctx.restore();

    // 4. Kadran Çizgileri ve Hız Rakamları (Precision Cyber Ticks)
    ctx.save();
    const tickSteps = 10;
    for (let i = 0; i <= tickSteps; i++) {
      const val = (this.maxSpeed / tickSteps) * i;
      const angle = startAngle + (totalAngle / tickSteps) * i;

      const isMajor = (i % 2 === 0);
      const innerR = radius - (isMajor ? 16 : 10);
      const outerR = radius - 4;
      const x1 = cx + Math.cos(angle) * innerR;
      const y1 = cy + Math.sin(angle) * innerR;
      const x2 = cx + Math.cos(angle) * outerR;
      const y2 = cy + Math.sin(angle) * outerR;

      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.lineWidth = isMajor ? 2.2 : 1.2;
      ctx.strokeStyle = isMajor ? 'rgba(255, 255, 255, 0.45)' : 'rgba(255, 255, 255, 0.18)';
      ctx.stroke();

      // Sayısal Etiketler (Major Ticks)
      if (isMajor) {
        const textR = radius - 26;
        const tx = cx + Math.cos(angle) * textR;
        const ty = cy + Math.sin(angle) * textR;
        ctx.fillStyle = (val <= this.currentSpeed) ? '#f0f4fc' : 'rgba(255, 255, 255, 0.4)';
        ctx.font = '700 9.5px "JetBrains Mono", monospace';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(Math.round(val), tx, ty);
      }
    }
    ctx.restore();

    // 5. Lazer İbre (Futuristic Laser Needle)
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(currentAngle);

    // İbre gövdesi
    ctx.beginPath();
    ctx.moveTo(0, -3.5);
    ctx.lineTo(radius - 6, 0);
    ctx.lineTo(0, 3.5);
    ctx.closePath();
    ctx.fillStyle = speedRatio > 0.75 ? '#f43f5e' : (speedRatio > 0.45 ? '#10b981' : '#00d2ff');
    ctx.shadowColor = ctx.fillStyle;
    ctx.shadowBlur = 12;
    ctx.fill();

    // İbre merkez halkası ve göbek taşı
    ctx.beginPath();
    ctx.arc(0, 0, 10, 0, Math.PI * 2);
    ctx.fillStyle = '#0a0f1d';
    ctx.strokeStyle = ctx.fillStyle === '#0a0f1d' ? '#00d2ff' : ctx.fillStyle;
    ctx.lineWidth = 2.5;
    ctx.fill();
    ctx.stroke();

    // Küçük merkez göbek parıltısı
    ctx.beginPath();
    ctx.arc(0, 0, 4, 0, Math.PI * 2);
    ctx.fillStyle = '#00d2ff';
    ctx.shadowColor = '#00d2ff';
    ctx.shadowBlur = 8;
    ctx.fill();
    ctx.restore();

    // 6. Merkez Holografik Hız Değeri
    ctx.save();
    ctx.textAlign = 'center';
    
    // Hız Rakamı
    ctx.fillStyle = '#ffffff';
    ctx.font = '700 36px "Chakra Petch", sans-serif';
    ctx.shadowColor = 'rgba(0, 210, 255, 0.6)';
    ctx.shadowBlur = 12;
    ctx.fillText(Math.round(this.currentSpeed), cx, cy - 28);

    // Birim Pill (KM/H)
    ctx.fillStyle = '#00d2ff';
    ctx.font = '700 11px "JetBrains Mono", monospace';
    ctx.shadowColor = 'rgba(0, 210, 255, 0.8)';
    ctx.shadowBlur = 6;
    ctx.fillText('KM / H', cx, cy - 12);

    // SPN 84 Telematik Alt Etiketi
    ctx.fillStyle = '#94a3b8';
    ctx.font = '500 9.5px "JetBrains Mono", monospace';
    ctx.shadowBlur = 0;
    const mph = Math.round(this.currentSpeed * 0.621371);
    ctx.fillText(`${mph} MPH · SPN 84 (CCVS)`, cx, cy + 2);
    ctx.restore();
  }
}

window.SpeedGauge = SpeedGauge;
