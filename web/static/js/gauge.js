/**
 * High-Performance HTML5 Canvas J1939 Speedometer Gauge
 */

class SpeedGauge {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');

    this.currentSpeed = 0.0;
    this.targetSpeed = 0.0;
    this.maxSpeed = 160.0;

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
    const height = rect.height || 220;

    this.canvas.width = width * dpr;
    this.canvas.height = height * dpr;
    this.ctx.scale(dpr, dpr);
    this.width = width;
    this.height = height;
  }

  setSpeed(speed, max = 160.0) {
    const numSpeed = parseFloat(speed) || 0.0;
    const numMax = parseFloat(max) || 220.0;
    this.targetSpeed = Math.max(0, Math.min(numMax, numSpeed));
    this.maxSpeed = numMax;
  }

  animate() {
    // Yumuşak ve hızlı hız geçişi (lerp)
    const diff = this.targetSpeed - this.currentSpeed;
    if (Math.abs(diff) > 0.05) {
      this.currentSpeed += diff * 0.28;
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
    const cy = h * 0.78;
    const radius = Math.min(w * 0.42, 135);

    ctx.clearRect(0, 0, w, h);

    const startAngle = Math.PI * 0.82;
    const endAngle = Math.PI * 2.18;
    const totalAngle = endAngle - startAngle;

    // 1. Arka Plan Kavisli Ray (Track)
    ctx.save();
    ctx.beginPath();
    ctx.arc(cx, cy, radius, startAngle, endAngle);
    ctx.lineWidth = 14;
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.06)';
    ctx.lineCap = 'round';
    ctx.stroke();

    // 2. Aktif Hız Kavisli İlerleme (Glow Progress Arc)
    const speedRatio = Math.min(1.0, this.currentSpeed / this.maxSpeed);
    const currentAngle = startAngle + totalAngle * speedRatio;

    if (this.currentSpeed > 0.1) {
      const grad = ctx.createLinearGradient(0, cy, w, cy);
      grad.addColorStop(0, '#00d2ff');
      grad.addColorStop(0.6, '#10b981');
      grad.addColorStop(0.85, '#f59e0b');
      grad.addColorStop(1, '#f43f5e');

      ctx.beginPath();
      ctx.arc(cx, cy, radius, startAngle, currentAngle);
      ctx.lineWidth = 14;
      ctx.strokeStyle = grad;
      ctx.lineCap = 'round';
      ctx.shadowColor = '#00d2ff';
      ctx.shadowBlur = 12;
      ctx.stroke();
    }
    ctx.restore();

    // 3. Kadran Çizgileri ve Hız Değerleri (Ticks & Labels)
    ctx.save();
    const tickSteps = 8;
    for (let i = 0; i <= tickSteps; i++) {
      const val = (this.maxSpeed / tickSteps) * i;
      const angle = startAngle + (totalAngle / tickSteps) * i;

      const innerR = radius - 18;
      const outerR = radius - 8;
      const x1 = cx + Math.cos(angle) * innerR;
      const y1 = cy + Math.sin(angle) * innerR;
      const x2 = cx + Math.cos(angle) * outerR;
      const y2 = cy + Math.sin(angle) * outerR;

      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.lineWidth = i % 2 === 0 ? 2 : 1;
      ctx.strokeStyle = i % 2 === 0 ? 'rgba(255, 255, 255, 0.4)' : 'rgba(255, 255, 255, 0.2)';
      ctx.stroke();

      // Sayı Etiketleri
      if (i % 2 === 0) {
        const textR = radius - 30;
        const tx = cx + Math.cos(angle) * textR;
        const ty = cy + Math.sin(angle) * textR;
        ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
        ctx.font = '600 10px "JetBrains Mono", monospace';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(Math.round(val), tx, ty);
      }
    }
    ctx.restore();

    // 4. İbre (Needle)
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(currentAngle);

    // İbre gölgesi ve çizgisi
    ctx.beginPath();
    ctx.moveTo(0, -3);
    ctx.lineTo(radius - 12, 0);
    ctx.lineTo(0, 3);
    ctx.closePath();
    ctx.fillStyle = '#00d2ff';
    ctx.shadowColor = 'rgba(0, 210, 255, 0.8)';
    ctx.shadowBlur = 10;
    ctx.fill();

    // Merkez göbek halkası
    ctx.beginPath();
    ctx.arc(0, 0, 8, 0, Math.PI * 2);
    ctx.fillStyle = '#07090e';
    ctx.strokeStyle = '#00d2ff';
    ctx.lineWidth = 3;
    ctx.fill();
    ctx.stroke();
    ctx.restore();

    // 5. Merkez Dijital Hız Göstergesi
    ctx.save();
    ctx.textAlign = 'center';
    ctx.fillStyle = '#ffffff';
    ctx.font = '700 32px "Chakra Petch", sans-serif';
    ctx.shadowColor = 'rgba(0, 210, 255, 0.5)';
    ctx.shadowBlur = 8;
    ctx.fillText(Math.round(this.currentSpeed), cx, cy - 35);

    ctx.fillStyle = '#00d2ff';
    ctx.font = '600 11px "JetBrains Mono", monospace';
    ctx.shadowBlur = 0;
    ctx.fillText('KM / H', cx, cy - 18);

    const mph = Math.round(this.currentSpeed * 0.621371);
    ctx.fillStyle = '#64748b';
    ctx.font = '500 10px "JetBrains Mono", monospace';
    ctx.fillText(`${mph} MPH · SPN 84`, cx, cy - 4);
    ctx.restore();
  }
}

window.SpeedGauge = SpeedGauge;
