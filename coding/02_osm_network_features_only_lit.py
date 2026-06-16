# cpted_osm_lit_features.py
# Estrae statistiche del tag OSM "lit=*" sulle strade (highway=*) per 3 raggi.
# Output: output/cpted_osm_lit_features.csv
#
# Colonne in output:
# - codice_cliente
# - lit_mode_r{r}
# - lit_pct_yes_r{r}
# - lit_pct_no_r{r}
# - lit_pct_sunset_sunrise_r{r}
# - lit_pct_automatic_r{r}
# - lit_pct_missing_r{r}
# - lit_n_edges_r{r}

from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, Any, Optional, List

import numpy as np
import pandas as pd
import osmnx as ox
import geopandas as gpd


# ===================== PARAMETRI =====================

CSV_PATH = r"output\abitazioni_coordinate_google.csv"
OUT_CSV = Path(r"output\cpted_osm_features_lit.csv")

MAX_ROWS = 501  # None = tutte

RADII_M: List[int] = [100, 300, 500]

SLEEP_SECONDS = 0.15

ox.settings.use_cache = True
ox.settings.log_console = False


# ===================== UTILS GENERALI =====================

def safe_float(x) -> Optional[float]:
    try:
        if pd.isna(x):
            return None
        return float(x)
    except Exception:
        return None


def features_from_point_safe(lat: float, lon: float, dist_m: int, tags: Dict[str, Any]) -> gpd.GeoDataFrame:
    """
    Wrapper compatibile tra versioni OSMnx:
    - OSMnx >= 1.6: features_from_point
    - OSMnx <  1.6: geometries_from_point
    """
    if hasattr(ox, "features_from_point"):
        return ox.features_from_point((lat, lon), tags=tags, dist=dist_m)
    if hasattr(ox, "geometries_from_point"):
        return ox.geometries_from_point((lat, lon), tags=tags, dist=dist_m)
    raise AttributeError("OSMnx non espone né features_from_point né geometries_from_point.")


def _norm_lit_value(x: Optional[str]) -> Optional[str]:
    """
    Normalizza alcune varianti sporche/eterogenee di lit.
    Mantiene valori sconosciuti come stringa pulita.
    """
    if x is None:
        return None
    s = str(x).strip().lower()
    if s == "" or s in ("nan", "none", "null"):
        return None

    # normalizzazioni comuni
    if s in ("true", "1"):
        return "yes"
    if s in ("false", "0"):
        return "no"
    if s in ("sunset to sunrise", "sunset_sunrise", "sunset-sunrise;yes"):
        return "sunset-sunrise"
    return s


# ===================== BLOCCO LIT =====================

def lit_stats(lat: float, lon: float, radius_m: int) -> Dict[str, Any]:
    """
    Estrae statistiche sul tag lit=* per strade (highway=*) entro radius_m.
    Ritorna un dict con mode + percentuali dei valori più interessanti + missing.
    """
    out: Dict[str, Any] = {
        "lit_mode": "unknown",
        "lit_pct_yes": np.nan,
        "lit_pct_no": np.nan,
        "lit_pct_sunset_sunrise": np.nan,
        "lit_pct_automatic": np.nan,
        "lit_pct_missing": np.nan,
        "lit_n_edges": 0,
    }

    tags = {"highway": True}

    try:
        gdf = features_from_point_safe(lat, lon, dist_m=radius_m, tags=tags)
    except Exception:
        return out

    if gdf is None or len(gdf) == 0:
        return out

    gdf = gdf.reset_index()

    # Manteniamo solo geometrie lineari (strade)
    if "geometry" not in gdf.columns:
        return out

    gdf = gdf[gdf.geometry.notna()].copy()
    if len(gdf) == 0:
        return out

    geom_types = gdf.geometry.geom_type.astype(str)
    gdf = gdf[geom_types.isin(["LineString", "MultiLineString"])].copy()
    if len(gdf) == 0:
        return out

    out["lit_n_edges"] = int(len(gdf))
    n = len(gdf)

    if "lit" not in gdf.columns:
        # tutto missing
        out["lit_mode"] = "unknown"
        out["lit_pct_missing"] = 1.0
        return out

    lit = gdf["lit"].apply(_norm_lit_value)

    n_missing = int(lit.isna().sum())
    out["lit_pct_missing"] = n_missing / n if n > 0 else np.nan

    lit_non_missing = lit.dropna()
    if len(lit_non_missing) == 0:
        out["lit_mode"] = "unknown"
        return out

    # mode (valore più frequente tra i non-missing)
    out["lit_mode"] = lit_non_missing.value_counts().idxmax()

    # percentuali su TUTTE le strade scaricate (missing incluso), più comparabile tra aree
    def pct(val: str) -> float:
        return float((lit == val).sum() / n) if n > 0 else np.nan

    out["lit_pct_yes"] = pct("yes")
    out["lit_pct_no"] = pct("no")
    out["lit_pct_sunset_sunrise"] = pct("sunset-sunrise")
    out["lit_pct_automatic"] = pct("automatic")

    return out


def suffix(d: Dict[str, Any], suff: str) -> Dict[str, Any]:
    return {f"{k}{suff}": v for k, v in d.items()}


# ===================== MAIN =====================

def main():
    df = pd.read_csv(CSV_PATH)

    required = {"codice_cliente", "lat", "lon"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"Colonne mancanti nel CSV: {missing}. Colonne presenti: {list(df.columns)}")

    if MAX_ROWS is not None:
        df = df.head(int(MAX_ROWS)).copy()

    rows_out = []
    ok = skipped = failed = 0

    for _, row in df.iterrows():
        codice = str(row["codice_cliente"]).strip()
        lat = safe_float(row["lat"])
        lon = safe_float(row["lon"])

        if not codice or lat is None or lon is None:
            skipped += 1
            continue

        base: Dict[str, Any] = {"codice_cliente": codice}

        try:
            for r in RADII_M:
                stats = lit_stats(lat, lon, radius_m=r)
                base.update(suffix(stats, f"_r{r}"))
                time.sleep(SLEEP_SECONDS)

            rows_out.append(base)
            ok += 1

        except Exception as e:
            failed += 1
            # manteniamo comunque la riga con solo codice_cliente
            rows_out.append(base)
            print(f"[ERRORE] {codice} ({lat},{lon}) -> {e}")

    out_df = pd.DataFrame(rows_out)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUT_CSV, index=False, encoding="utf-8")

    print(f"FATTO. OK={ok} | Skipped={skipped} | Failed={failed}")
    print(f"Output: {OUT_CSV.resolve()}")


if __name__ == "__main__":
    main()
