# cpted_osm_master_features_poi_flags.py
# Unico codice: rete stradale (drive) multi-raggio + gerarchia strade + LANDUSE + POI FLAG (0/1)
# Output: output/cpted_osm_master_features.csv

from __future__ import annotations

import math
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

import numpy as np
import pandas as pd

import osmnx as ox
import networkx as nx

import geopandas as gpd
from shapely.geometry import Point
from pyproj import CRS


# ===================== PARAMETRI =====================

CSV_PATH = r"output\abitazioni_coordinate_google.csv"
OUT_CSV = Path(r"output\cpted_osm_features.csv")

MAX_ROWS = 501  # None = tutte

RADII_M: List[int] = [100, 300, 500]
CONTEXT_RADIUS_M = 500

NETWORK_TYPE = "drive"
SIMPLIFY = True

SLEEP_SECONDS = 0.15

ox.settings.use_cache = True
ox.settings.log_console = False


# ===================== STRADE =====================

HIGHWAY_TYPES: List[str] = [
    "motorway", "trunk", "primary", "secondary", "tertiary",
    "residential", "service", "unclassified", "living_street"
]


# ===================== POI (FLAGS 0/1) =====================
# Facciamo una sola chiamata OSM per POI "strutturali" (controllo / sorveglianza / attrattori)
POI_TAGS_FLAGS = {
    # controllo formale
    "amenity": [
        "police", "fire_station",
        # presidio sociale / routine
        "place_of_worship", "school", "university",
        "hospital", "clinic", "pharmacy",
        # attrattori / night-life
        "bar", "pub", "restaurant", "cafe", "nightclub",
        # logistica / opportunità
        "parking",
        # finanza / ATM (spesso vicino ad assi e flussi)
        "bank", "atm",
    ],
    # trasporti (stazioni) -> spesso generatori forti di flusso
    "railway": ["station"],
    "public_transport": ["station"],
    # commercio generico (se vuoi un indicatore “commerciale”)
    "shop": True,
    "tourism": True,
    "leisure": True,
}


# ===================== UTILS GENERALI =====================

def safe_float(x) -> Optional[float]:
    try:
        if pd.isna(x):
            return None
        return float(x)
    except Exception:
        return None


def utm_crs_from_latlon(lat: float, lon: float) -> CRS:
    zone = int((lon + 180) // 6) + 1
    epsg = (32600 + zone) if lat >= 0 else (32700 + zone)
    return CRS.from_epsg(epsg)


def make_point_gdf(lat: float, lon: float, crs_epsg: int = 4326) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame({"geometry": [Point(lon, lat)]}, crs=f"EPSG:{crs_epsg}")


def ensure_edge_lengths(G: nx.MultiDiGraph) -> nx.MultiDiGraph:
    for _, _, _, data in G.edges(keys=True, data=True):
        if "length" in data and data["length"] is not None:
            return G
        break

    for u, v, k, data in G.edges(keys=True, data=True):
        geom = data.get("geometry", None)
        if geom is not None:
            data["length"] = float(geom.length)
        else:
            xu = G.nodes[u].get("x", None)
            yu = G.nodes[u].get("y", None)
            xv = G.nodes[v].get("x", None)
            yv = G.nodes[v].get("y", None)
            if None not in (xu, yu, xv, yv):
                data["length"] = float(math.hypot(xu - xv, yu - yv))
            else:
                data["length"] = np.nan
    return G


def make_undirected_graph(G: nx.MultiDiGraph) -> nx.MultiGraph:
    Gu = G.to_undirected()
    if not isinstance(Gu, nx.MultiGraph):
        Gu = nx.MultiGraph(Gu)
    return Gu


def features_from_point_safe(lat: float, lon: float, dist_m: int, tags: Dict[str, Any]) -> gpd.GeoDataFrame:
    if hasattr(ox, "features_from_point"):
        return ox.features_from_point((lat, lon), tags=tags, dist=dist_m)
    if hasattr(ox, "geometries_from_point"):
        return ox.geometries_from_point((lat, lon), tags=tags, dist=dist_m)
    raise AttributeError("OSMnx non espone né features_from_point né geometries_from_point.")


def _contains_any(text: str, needles: List[str]) -> bool:
    t = (text or "").lower()
    return any(n.lower() in t for n in needles)


# ===================== BLOCCO 1: RETE STRADALE (CORE) =====================

def core_network_features_drive(lat: float, lon: float, radius_m: int) -> Dict[str, Any]:
    G = ox.graph_from_point(
        (lat, lon),
        dist=radius_m,
        network_type=NETWORK_TYPE,
        simplify=SIMPLIFY,
        retain_all=False,
        truncate_by_edge=True,
    )

    if len(G.nodes) < 2 or len(G.edges) < 1:
        return {
            "graph_ok": 0,
            "node_density_per_km2": np.nan,
            "edge_density_per_km2": np.nan,
            "avg_degree": np.nan,
            "culdesac_ratio": np.nan,
            "intersection_ratio_deg_ge_3": np.nan,
            "intersection_density_deg_ge_3_per_km2": np.nan,
            "total_street_length_m": np.nan,
            "street_length_density_km_per_km2": np.nan,
            "avg_edge_length_m": np.nan,
            "n_connected_components": np.nan,
            "largest_component_ratio": np.nan,
        }

    Gp = ox.project_graph(G)
    Gp = ensure_edge_lengths(Gp)
    Gu = make_undirected_graph(Gp)

    n_nodes = Gu.number_of_nodes()
    n_edges = Gu.number_of_edges()

    area_km2 = (math.pi * (radius_m ** 2)) / 1e6

    node_density_per_km2 = (n_nodes / area_km2) if area_km2 > 0 else np.nan
    edge_density_per_km2 = (n_edges / area_km2) if area_km2 > 0 else np.nan

    degrees = np.array([d for _, d in Gu.degree()], dtype=float)
    avg_degree = float(np.mean(degrees)) if len(degrees) else np.nan
    culdesac_ratio = float(np.mean(degrees == 1)) if len(degrees) else np.nan

    intersection_ratio = float(np.mean(degrees >= 3)) if len(degrees) else np.nan
    intersection_density = (float(np.sum(degrees >= 3)) / area_km2) if area_km2 > 0 else np.nan

    edge_lengths = np.array([data.get("length", np.nan) for _, _, _, data in Gu.edges(keys=True, data=True)], dtype=float)
    total_street_length_m = float(np.nansum(edge_lengths))
    street_length_density_km_per_km2 = (total_street_length_m / 1000.0) / area_km2 if area_km2 > 0 else np.nan
    avg_edge_length_m = float(np.nanmean(edge_lengths)) if len(edge_lengths) else np.nan

    try:
        n_components = nx.number_connected_components(Gu)
        largest_cc_size = len(max(nx.connected_components(Gu), key=len))
        largest_cc_ratio = largest_cc_size / n_nodes if n_nodes else np.nan
    except Exception:
        n_components, largest_cc_ratio = np.nan, np.nan

    return {
        "graph_ok": 1,
        "node_density_per_km2": node_density_per_km2,
        "edge_density_per_km2": edge_density_per_km2,
        "avg_degree": avg_degree,
        "culdesac_ratio": culdesac_ratio,
        "intersection_ratio_deg_ge_3": intersection_ratio,
        "intersection_density_deg_ge_3_per_km2": intersection_density,
        "total_street_length_m": total_street_length_m,
        "street_length_density_km_per_km2": street_length_density_km_per_km2,
        "avg_edge_length_m": avg_edge_length_m,
        "n_connected_components": n_components,
        "largest_component_ratio": largest_cc_ratio,
    }


# ===================== BLOCCO 2: STRADE PER TIPO + DISTANZE =====================

def roads_type_features(lat: float, lon: float, radius_m: int) -> Dict[str, Any]:
    point_wgs = make_point_gdf(lat, lon)
    crs_utm = utm_crs_from_latlon(lat, lon)
    p = point_wgs.to_crs(crs_utm).geometry.iloc[0]

    tags = {"highway": HIGHWAY_TYPES}
    try:
        gdf = features_from_point_safe(lat, lon, dist_m=radius_m, tags=tags)
    except Exception:
        out = {}
        for t in HIGHWAY_TYPES:
            out[f"km_{t}"] = np.nan
            out[f"dist_{t}_m"] = np.nan
        return out

    if gdf is None or len(gdf) == 0:
        out = {}
        for t in HIGHWAY_TYPES:
            out[f"km_{t}"] = 0.0
            out[f"dist_{t}_m"] = np.nan
        return out

    gdf = gdf.reset_index()
    if "highway" not in gdf.columns:
        out = {}
        for t in HIGHWAY_TYPES:
            out[f"km_{t}"] = np.nan
            out[f"dist_{t}_m"] = np.nan
        return out

    gdf = gdf[gdf.geometry.notna()].copy()
    if len(gdf) == 0:
        out = {}
        for t in HIGHWAY_TYPES:
            out[f"km_{t}"] = 0.0
            out[f"dist_{t}_m"] = np.nan
        return out

    gdf = gpd.GeoDataFrame(gdf, geometry="geometry", crs="EPSG:4326").to_crs(crs_utm)

    out: Dict[str, Any] = {}
    for t in HIGHWAY_TYPES:
        sub = gdf[gdf["highway"].astype(str) == t]
        if len(sub) == 0:
            out[f"km_{t}"] = 0.0
            out[f"dist_{t}_m"] = np.nan
            continue

        lengths = []
        for geom in sub.geometry:
            if geom is None:
                continue
            if geom.geom_type in ("LineString", "MultiLineString"):
                lengths.append(geom.length)
        out[f"km_{t}"] = float(np.sum(lengths) / 1000.0) if lengths else 0.0

        try:
            out[f"dist_{t}_m"] = float(sub.geometry.distance(p).min())
        except Exception:
            out[f"dist_{t}_m"] = np.nan

    return out


# ===================== BLOCCO 3: LANDUSE MODE =====================

def landuse_mode(lat: float, lon: float, radius_m: int) -> str:
    tags = {"landuse": True}
    try:
        gdf = features_from_point_safe(lat, lon, dist_m=radius_m, tags=tags)
    except Exception:
        return "unknown"

    if gdf is None or len(gdf) == 0:
        return "unknown"

    gdf = gdf.reset_index()
    if "landuse" not in gdf.columns:
        return "unknown"

    vals = gdf["landuse"].dropna().astype(str)
    if len(vals) == 0:
        return "unknown"

    return vals.value_counts().idxmax()


# ===================== BLOCCO 4: POI FLAGS (0/1) =====================

def poi_flags(lat: float, lon: float, radius_m: int) -> Dict[str, int]:
    """
    Output binario 0/1 per POI "strutturali" con struttura:
      - has_bar_pub: bar OR pub
      - has_restaurant: restaurant
      - has_nightlife: nightclub (NOTA: solo nightclub, versione "pulita")
    Nota: per 'carabinieri' usiamo euristica su name/operator.
    """

    # default tutti 0 (struttura richiesta)
    out: Dict[str, int] = {
        "has_police": 0,
        "has_carabinieri": 0,
        "has_fire_station": 0,
        "has_place_of_worship": 0,
        "has_school_university": 0,
        "has_hospital_clinic": 0,
        "has_pharmacy": 0,
        "has_bank_atm": 0,
        "has_bar_pub": 0,
        "has_nightlife": 0,
        "has_restaurant": 0,
        "has_parking": 0,
        "has_station": 0,
        "has_commercial": 0,  # shop/tourism/leisure -> indicatore "area attiva"
    }

    try:
        gdf = features_from_point_safe(lat, lon, dist_m=radius_m, tags=POI_TAGS_FLAGS)
    except Exception:
        return out  # se fallisce: lascia 0 (robusto)

    if gdf is None or len(gdf) == 0:
        return out

    gdf = gdf.reset_index()

    # --- AMENITY flags ---
    if "amenity" in gdf.columns:
        am = gdf["amenity"].dropna().astype(str).str.lower()

        out["has_police"] = int((am == "police").any())
        out["has_fire_station"] = int((am == "fire_station").any())
        out["has_place_of_worship"] = int((am == "place_of_worship").any())
        out["has_school_university"] = int(((am == "school") | (am == "university")).any())
        out["has_hospital_clinic"] = int(((am == "hospital") | (am == "clinic")).any())
        out["has_pharmacy"] = int((am == "pharmacy").any())
        out["has_bank_atm"] = int(((am == "bank") | (am == "atm")).any())

        # separazioni richieste
        out["has_bar_pub"] = int(((am == "bar") | (am == "pub")).any())
        out["has_restaurant"] = int((am == "restaurant").any())

        # nightlife "pulita": solo nightclub (più stabile e meno ambiguo)
        out["has_nightlife"] = int((am == "nightclub").any())

        out["has_parking"] = int((am == "parking").any())

        # carabinieri: amenity=police ma name/operator contengono "carabinieri"
        if out["has_police"] == 1:
            names = []
            for col in ("name", "operator", "brand", "official_name"):
                if col in gdf.columns:
                    names.extend(gdf[col].dropna().astype(str).tolist())
            out["has_carabinieri"] = int(any(_contains_any(x, ["carabinieri"]) for x in names))

    # --- STATION flags ---
    station_hit = False
    if "railway" in gdf.columns:
        station_hit = station_hit or (gdf["railway"].dropna().astype(str).str.lower() == "station").any()
    if "public_transport" in gdf.columns:
        station_hit = station_hit or (gdf["public_transport"].dropna().astype(str).str.lower() == "station").any()
    out["has_station"] = int(station_hit)

    # --- COMMERCIAL/ACTIVE AREA flags ---
    commercial_hit = False
    for col in ("shop", "tourism", "leisure"):
        if col in gdf.columns:
            commercial_hit = commercial_hit or gdf[col].notna().any()
    out["has_commercial"] = int(commercial_hit)

    return out



# ===================== HELPERS =====================

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

        base: Dict[str, Any] = {
            "codice_cliente": codice,
            "lat": lat,
            "lon": lon,
            "network_type": NETWORK_TYPE,
        }

        try:
            # ---- multi-raggio: rete core + strade per tipo + distanze ----
            for r in RADII_M:
                base.update(suffix(core_network_features_drive(lat, lon, radius_m=r), f"_r{r}"))
                base.update(suffix(roads_type_features(lat, lon, radius_m=r), f"_r{r}"))
                time.sleep(SLEEP_SECONDS)

            # ---- contesto (una volta sola) ----
            base[f"landuse_mode_r{CONTEXT_RADIUS_M}"] = landuse_mode(lat, lon, radius_m=CONTEXT_RADIUS_M)

            flags = poi_flags(lat, lon, radius_m=CONTEXT_RADIUS_M)
            base.update(suffix(flags, f"_r{CONTEXT_RADIUS_M}"))

            rows_out.append(base)
            ok += 1

        except Exception as e:
            failed += 1
            base["error"] = str(e)[:300]
            rows_out.append(base)
            print(f"[ERRORE] {codice} ({lat},{lon}) -> {e}")

    out_df = pd.DataFrame(rows_out)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUT_CSV, index=False, encoding="utf-8")

    print(f"FATTO. OK={ok} | Skipped={skipped} | Failed={failed}")
    print(f"Output: {OUT_CSV.resolve()}")


if __name__ == "__main__":
    main()
