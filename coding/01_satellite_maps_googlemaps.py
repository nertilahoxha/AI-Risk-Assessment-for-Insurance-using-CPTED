# scarica_satellite_staticmaps.py
# Output: una mappa satellitare per ogni indirizzo (lat/lon) nel CSV
# Nome file: <codice_cliente>.png

from __future__ import annotations

import math
import time
from pathlib import Path

import pandas as pd
import requests


# =============== PARAMETRI UTENTE ===============

CSV_PATH = r"output\abitazioni_coordinate_google.csv"

# Per testing: None = tutte le righe, altrimenti un intero (es. 20)
MAX_ROWS = 5

# Box territoriale desiderato (circa) in metri: 100 => ~100m x 100m
MAP_SIZE_M = 100

# Dimensione immagine richiesta a Google (max 640 per lato su molti piani standard)
IMG_PX = 640

# scale=2 => immagine più definita (fino a 1280px effettivi), ma pesa di più
SCALE = 2

# Tipo mappa
MAPTYPE = "satellite"

# Marker
MARKER_COLOR = "red"
MARKER_LABEL = ""  # una lettera singola (A-Z, 0-9). Puoi mettere "" per niente.

# Ritardo tra richieste (per evitare rate limit / cortesia)
SLEEP_SECONDS = 0.15

# Cartella output
OUT_DIR = Path("output_satellite_maps")

# Inserisci qui la tua API KEY (devi avere billing attivo su Google Cloud)
GOOGLE_MAPS_API_KEY = "*****"


# =============== FUNZIONI ===============

def zoom_for_target_meters(lat: float, target_meters: float, img_px: int) -> int:
    """
    Calcola uno zoom intero per far sì che la larghezza dell'immagine (img_px)
    copra circa target_meters (approssimazione basata su Web Mercator).
    """
    # metri per pixel desiderati
    mpp = target_meters / float(img_px)

    # metri per pixel a zoom=0 all'equatore (Web Mercator)
    # formula: mpp = 156543.03392 * cos(lat) / 2^zoom
    lat_rad = math.radians(lat)
    base = 156543.03392 * math.cos(lat_rad)

    if base <= 0:
        return 18  # fallback sensato

    zoom = math.log2(base / mpp)
    zoom_int = int(round(zoom))

    # limiti tipici di Google Maps
    return max(0, min(21, zoom_int))


def download_static_map(lat: float, lon: float, zoom: int, out_path: Path) -> None:
    url = "https://maps.googleapis.com/maps/api/staticmap"

    marker = f"color:{MARKER_COLOR}|label:{MARKER_LABEL}|{lat},{lon}" if MARKER_LABEL else f"color:{MARKER_COLOR}|{lat},{lon}"

    params = {
        "center": f"{lat},{lon}",
        "zoom": str(zoom),
        "size": f"{IMG_PX}x{IMG_PX}",
        "scale": str(SCALE),
        "maptype": MAPTYPE,
        "markers": marker,
        "key": GOOGLE_MAPS_API_KEY,
    }

    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()

    # Se l'API key è errata o manca billing, Google spesso risponde 200 ma con un'immagine di errore.
    # Controlliamo un minimo il content-type.
    ctype = r.headers.get("Content-Type", "")
    if "image" not in ctype.lower():
        raise RuntimeError(f"Risposta non immagine (Content-Type={ctype}). Contenuto: {r.text[:300]}")

    out_path.write_bytes(r.content)


# =============== MAIN ===============

def main():
    if not GOOGLE_MAPS_API_KEY or "INSERISCI" in GOOGLE_MAPS_API_KEY:
        raise SystemExit("Devi inserire una GOOGLE_MAPS_API_KEY valida dentro lo script.")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(CSV_PATH)

    # Safety: colonne attese
    required_cols = {"codice_cliente", "lat", "lon"}
    missing = required_cols - set(df.columns)
    if missing:
        raise SystemExit(f"Nel CSV mancano colonne richieste: {missing}. Colonne presenti: {list(df.columns)}")

    if MAX_ROWS is not None:
        df = df.head(int(MAX_ROWS))

    ok, skipped, failed = 0, 0, 0

    for i, row in df.iterrows():
        codice = str(row["codice_cliente"]).strip()
        lat = row["lat"]
        lon = row["lon"]

        if pd.isna(lat) or pd.isna(lon) or codice == "":
            skipped += 1
            continue

        lat = float(lat)
        lon = float(lon)

        zoom = zoom_for_target_meters(lat=lat, target_meters=MAP_SIZE_M, img_px=IMG_PX)

        out_path = OUT_DIR / f"{codice}.png"

        try:
            download_static_map(lat=lat, lon=lon, zoom=zoom, out_path=out_path)
            ok += 1
        except Exception as e:
            failed += 1
            print(f"[ERRORE] codice_cliente={codice} lat={lat} lon={lon} -> {e}")

        time.sleep(SLEEP_SECONDS)

    print(f"FATTO. Salvate: {ok} | Skippate: {skipped} | Fallite: {failed}")
    print(f"Cartella output: {OUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
