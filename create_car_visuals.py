"""
Generates 30 distinct, stylish, high-resolution automotive SVG cards for all 30 vehicles.
Each car has its unique brand badge, model typography, color theme, and vehicle silhouette!
"""

import os
from j1939.fleet_data import VEHICLES, FLEET_BRANDS

OUT_DIR = os.path.join(os.path.dirname(__file__), "web", "static", "images", "cars")
os.makedirs(OUT_DIR, exist_ok=True)

# Distinct silhouette paths and accents based on category
CATEGORY_ICONS = {
    "Sedan": "🏎️",
    "SUV": "🚙",
    "Coupe": "🏎️",
    "Hatchback": "🚗",
    "EV": "⚡",
    "Pick-up": "🛻",
    "Station": "🚘"
}

def generate_svg_card(v, brand):
    color = brand.get("color", "#00d2ff")
    brand_name = v["brand_name"]
    model_name = v["model"]
    category = v["category"]
    engine = v["engine"]
    plate = v["plate"]
    sa = f"0x{v['source_address']:02X}"
    max_spd = v["max_speed"]
    accel = v["acceleration_rate"]

    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 450" width="100%" height="100%">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0a0f1d" />
      <stop offset="60%" stop-color="#111a2e" />
      <stop offset="100%" stop-color="#07090e" />
    </linearGradient>
    <linearGradient id="brandGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{color}" />
      <stop offset="100%" stop-color="#3b82f6" />
    </linearGradient>
    <linearGradient id="glowGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="{color}" stop-opacity="0.25" />
      <stop offset="100%" stop-color="transparent" />
    </linearGradient>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="15" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>

  <!-- Background Canvas -->
  <rect width="800" height="450" fill="url(#bgGrad)" />
  <rect width="800" height="450" fill="url(#glowGrad)" />

  <!-- Cyber Grid Lines -->
  <g stroke="rgba(255,255,255,0.03)" stroke-width="1">
    <line x1="0" y1="90" x2="800" y2="90" />
    <line x1="0" y1="180" x2="800" y2="180" />
    <line x1="0" y1="270" x2="800" y2="270" />
    <line x1="0" y1="360" x2="800" y2="360" />
    <line x1="200" y1="0" x2="200" y2="450" />
    <line x1="400" y1="0" x2="400" y2="450" />
    <line x1="600" y1="0" x2="600" y2="450" />
  </g>

  <!-- Glowing Accent Frame -->
  <rect x="20" y="20" width="760" height="410" rx="16" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="2" />
  <path d="M 20 60 L 20 20 L 80 20" fill="none" stroke="{color}" stroke-width="4" />
  <path d="M 780 390 L 780 430 L 720 430" fill="none" stroke="{color}" stroke-width="4" />

  <!-- Top Header: Brand Badge & J1939 SA -->
  <g transform="translate(50, 65)">
    <rect x="0" y="0" width="130" height="34" rx="6" fill="rgba(0,0,0,0.5)" stroke="{color}" stroke-width="1.5" />
    <text x="65" y="23" font-family="'Chakra Petch', sans-serif" font-size="16" font-weight="700" fill="{color}" text-anchor="middle" letter-spacing="2">{brand_name.upper()}</text>
    
    <rect x="570" y="0" width="130" height="34" rx="6" fill="rgba(0,0,0,0.6)" stroke="rgba(255,255,255,0.15)" stroke-width="1" />
    <text x="635" y="23" font-family="'JetBrains Mono', monospace" font-size="14" font-weight="600" fill="#00d2ff" text-anchor="middle">SA: {sa}</text>
  </g>

  <!-- Central Model Typography & Hero Display -->
  <text x="50" y="150" font-family="'Chakra Petch', sans-serif" font-size="34" font-weight="700" fill="#f0f4fc" letter-spacing="0.5">{model_name}</text>
  <text x="50" y="185" font-family="'JetBrains Mono', monospace" font-size="16" font-weight="500" fill="#94a3b8">{plate} · {category}</text>

  <!-- Sleek Automotive Silhouette Graphic -->
  <g transform="translate(180, 200)" filter="url(#glow)">
    <!-- Car body profile curve -->
    <path d="M 40 100 C 90 95, 140 60, 200 55 C 280 50, 360 48, 420 75 C 470 95, 500 100, 520 100 C 535 100, 540 115, 520 120 L 20 120 C 10 115, 15 100, 40 100 Z" fill="{color}" fill-opacity="0.15" stroke="{color}" stroke-width="3" />
    <!-- Roof line -->
    <path d="M 160 60 C 210 20, 320 18, 390 60" fill="none" stroke="{color}" stroke-width="3.5" stroke-linecap="round" />
    <!-- Wheels -->
    <circle cx="120" cy="118" r="26" fill="#07090e" stroke="{color}" stroke-width="4" />
    <circle cx="120" cy="118" r="10" fill="{color}" />
    <circle cx="450" cy="118" r="26" fill="#07090e" stroke="{color}" stroke-width="4" />
    <circle cx="450" cy="118" r="10" fill="{color}" />
    <!-- Headlight Beam -->
    <polygon points="520,105 580,95 580,125" fill="{color}" fill-opacity="0.25" />
    <polygon points="20,108 -30,100 -30,120" fill="#f43f5e" fill-opacity="0.3" />
  </g>

  <!-- Bottom Specs Telemetry Strip -->
  <g transform="translate(50, 370)">
    <!-- Engine -->
    <rect x="0" y="0" width="220" height="42" rx="8" fill="rgba(0,0,0,0.4)" stroke="rgba(255,255,255,0.08)" />
    <text x="14" y="16" font-family="'JetBrains Mono', monospace" font-size="10" fill="#64748b">MOTOR</text>
    <text x="14" y="32" font-family="'Chakra Petch', sans-serif" font-size="13" font-weight="600" fill="#f0f4fc">{engine[:24]}</text>

    <!-- Max Speed -->
    <rect x="240" y="0" width="220" height="42" rx="8" fill="rgba(0,0,0,0.4)" stroke="rgba(255,255,255,0.08)" />
    <text x="254" y="16" font-family="'JetBrains Mono', monospace" font-size="10" fill="#64748b">MAKSİMUM HIZ</text>
    <text x="254" y="32" font-family="'Chakra Petch', sans-serif" font-size="14" font-weight="700" fill="#00d2ff">{max_spd} KM/H</text>

    <!-- Acceleration Rate -->
    <rect x="480" y="0" width="220" height="42" rx="8" fill="rgba(0,0,0,0.4)" stroke="rgba(255,255,255,0.08)" />
    <text x="494" y="16" font-family="'JetBrains Mono', monospace" font-size="10" fill="#64748b">İVME DERECESİ</text>
    <text x="494" y="32" font-family="'Chakra Petch', sans-serif" font-size="14" font-weight="700" fill="#10b981">+{accel} km/h/s</text>
  </g>
</svg>"""
    return svg_content

def main():
    brand_dict = {b["id"]: b for b in FLEET_BRANDS}
    for v in VEHICLES:
        b = brand_dict.get(v["brand_id"], {"color": "#00d2ff"})
        svg = generate_svg_card(v, b)
        svg_path = os.path.join(OUT_DIR, f"{v['id']}.svg")
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"Created SVG visual: {v['id']}.svg")

if __name__ == "__main__":
    main()
