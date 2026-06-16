
# 1) Folium 2D con Esri World Imagery
# 2) CesiumJS 3D viewer centrato sulle stesse coordinate


from pathlib import Path

# --- Parametri  ---
LAT = 41.9028
LON = 12.4964

ZOOM_FOLIUM = 12

# Camera Cesium: altezza in metri
CESIUM_HEIGHT_M = 1000.0
CESIUM_PITCH_DEG = -90  # inclinazione camera (negativo = guarda verso il basso) # -45

# Token per Cesium World Terrain (terrain 3D reale)
# vuoto, terreno "liscio" ma sempre visibile)
CESIUM_ION_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiIzNTM1ZGRkMS02NmYxLTQ4ZmEtOWMwOC1kZGMyMDA1MWYwOWYiLCJpZCI6MzcwOTYzLCJpYXQiOjE3NjYwNjkyNTJ9.PqDjNdge1spJSXJdVppGgiee7AV1Nse_kW_s22acXf4"  

OUT_DIR = Path(__file__).resolve().parent

# ---------------------------
# 1) Folium 2D (Esri Imagery)
# ---------------------------

import folium

m = folium.Map(location=[LAT, LON], zoom_start=ZOOM_FOLIUM, tiles=None)

folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Esri",
    name="Esri World Imagery",
).add_to(m)

folium.Marker([LAT, LON], popup="Roma").add_to(m)

folium_path = OUT_DIR / "folium_mappa_satellite_esri.html"
m.save(str(folium_path))

# ---------------------------------------
# 2) CesiumJS 3D viewer
# ---------------------------------------
use_token = bool(CESIUM_ION_TOKEN.strip())

token_js = (
    f'Cesium.Ion.defaultAccessToken = "{CESIUM_ION_TOKEN}";'
    if use_token
    else "// Nessun token Cesium ion: uso terreno ellissoidale (terra liscia)."
)

terrain_js = (
    "Cesium.Terrain.fromWorldTerrain()"
    if use_token
    else "new Cesium.EllipsoidTerrainProvider()"
)

# Nota: baseLayerPicker true va bene per test, "pulizia" UI, False

cesium_html = f"""<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="utf-8" />
  <title>CesiumJS – Roma 3D</title>

  <!-- CesiumJS via CDN -->
  <script src="https://cesium.com/downloads/cesiumjs/releases/1.114/Build/Cesium/Cesium.js"></script>
  <link href="https://cesium.com/downloads/cesiumjs/releases/1.114/Build/Cesium/Widgets/widgets.css" rel="stylesheet" />

  <style>
    html, body, #cesiumContainer {{
      width: 100%;
      height: 100%;
      margin: 0;
      padding: 0;
      overflow: hidden;
    }}
  </style>
</head>

<body>
  <div id="cesiumContainer"></div>

  <script>
    {token_js}

    const viewer = new Cesium.Viewer("cesiumContainer", {{
      terrain: {terrain_js},
      timeline: false,
      animation: false,
      baseLayerPicker: true
    }});

    const lon = {LON};
    const lat = {LAT};

    // Zoom e tilt iniziali
    viewer.camera.flyTo({{
      destination: Cesium.Cartesian3.fromDegrees(lon, lat, {CESIUM_HEIGHT_M}),
      orientation: {{
        heading: Cesium.Math.toRadians(0),
        pitch: Cesium.Math.toRadians({CESIUM_PITCH_DEG}),
        roll: 0.0
      }}
    }});

    // Marker + label
    viewer.entities.add({{
      position: Cesium.Cartesian3.fromDegrees(lon, lat),
      point: {{
        pixelSize: 12,
        color: Cesium.Color.RED,
        outlineColor: Cesium.Color.WHITE,
        outlineWidth: 2
      }},
      label: {{
        text: "Roma",
        font: "14pt sans-serif",
        verticalOrigin: Cesium.VerticalOrigin.TOP,
        pixelOffset: new Cesium.Cartesian2(0, -15),
        disableDepthTestDistance: Number.POSITIVE_INFINITY
      }}
    }});

    // Debug semplice: se qualcosa non carica, lo vedi in console
    // Apri DevTools (F12) -> Console/Network
  </script>
</body>
</html>
"""

cesium_path = OUT_DIR / "cesium_mappa_satellite_3dterrain.html"
cesium_path.write_text(cesium_html, encoding="utf-8")

# ---------------------------
# Output & istruzioni d'uso
# ---------------------------
print("File generati:")
print(f"- {folium_path.name}")
print(f"- {cesium_path.name}")

print("\n Come aprire correttamente Cesium:")
print("1) Apri PowerShell nella cartella dei file generati")
print("2) Esegui:  python -m http.server 8000")
print("3) Apri nel browser:")
print(f"   http://localhost:8000/{cesium_path.name}")

if not use_token:
    print("\n Nota: CESIUM_ION_TOKEN è vuoto. Terrain liscio (ellissoide).")
    print("   Se vuoi Cesium World Terrain (rilievi 3D), crea un token su Cesium ion e incollalo in CESIUM_ION_TOKEN.")
else:
    print("\n Token presente, Cesium World Terrain abilitato.")
