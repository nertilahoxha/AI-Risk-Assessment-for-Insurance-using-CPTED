import time
import os
import pandas as pd
import googlemaps

# -------- PARAMETRI --------
INPUT_CSV = r"dataset\abitazioni.csv"
OUTPUT_CSV = r"output\abitazioni_coordinate_google.csv"

ADDRESS_COLUMN = "Indirizzo"
CITY_COLUMN = "Luogo di Residenza"

GOOGLE_API_KEY = "****"

SLEEP_SECONDS = 0.2
MAX_RETRIES = 3

MAX_ROWS = None      # None = tutte le righe
# MAX_ROWS = 100     # esempio: solo prime 100 righe

REGION = "it"
COMPONENTS = {"country": "IT"}

# -------- CLIENT GOOGLE --------
gmaps = googlemaps.Client(key=GOOGLE_API_KEY)

# -------- GEOCODING --------
def geocode_google(address: str, city: str):
    address = "" if pd.isna(address) else str(address).strip()
    city = "" if pd.isna(city) else str(city).strip()

    q1 = ", ".join([x for x in [address, city, "Italia"] if x])
    q2 = ", ".join([x for x in [address, "Italia"] if x])
    q3 = ", ".join([x for x in [city, "Italia"] if x])

    for query, level in [(q1, "address_city"), (q2, "address_only"), (q3, "city_only")]:
        if not query:
            continue

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                res = gmaps.geocode(
                    query,
                    region=REGION,
                    components=COMPONENTS
                )
                if res:
                    loc = res[0]["geometry"]["location"]
                    return (
                        float(loc["lat"]),
                        float(loc["lng"]),
                        level,
                        query,
                        res[0].get("place_id", ""),
                        res[0].get("formatted_address", "")
                    )
                break
            except Exception:
                time.sleep(SLEEP_SECONDS * attempt)

        time.sleep(SLEEP_SECONDS)

    return None, None, "not_found", q1, "", ""


# -------- MAIN --------
df = pd.read_csv(INPUT_CSV)

# limite righe effettivo
total_rows = len(df)
end_row = total_rows if MAX_ROWS is None else min(MAX_ROWS, total_rows)

print(f"Righe totali CSV: {total_rows}")
print(f"Righe da processare: {end_row}")

# ripartenza
if os.path.exists(OUTPUT_CSV):
    processed_rows = sum(1 for _ in open(OUTPUT_CSV, encoding="utf-8")) - 1
    print(f"Ripartenza da riga {processed_rows}")
else:
    processed_rows = 0
    out_header = list(df.columns) + [
        "lat", "lon",
        "geocode_level",
        "geocode_query_used",
        "google_place_id",
        "google_formatted_address"
    ]
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    pd.DataFrame(columns=out_header).to_csv(
        OUTPUT_CSV,
        index=False,
        encoding="utf-8"
    )

# ciclo principale
for i in range(processed_rows, end_row):
    row = df.iloc[i]

    address = row.get(ADDRESS_COLUMN, "")
    city = row.get(CITY_COLUMN, "")

    lat, lon, level, used_query, place_id, formatted = geocode_google(address, city)

    out_row = row.to_dict()
    out_row["lat"] = lat
    out_row["lon"] = lon
    out_row["geocode_level"] = level
    out_row["geocode_query_used"] = used_query
    out_row["google_place_id"] = place_id
    out_row["google_formatted_address"] = formatted

    pd.DataFrame([out_row]).to_csv(
        OUTPUT_CSV,
        mode="a",
        header=False,
        index=False,
        encoding="utf-8"
    )

    status = "OK" if lat is not None else "NON TROVATO"
    print(f"Riga {i+1}/{end_row} → {status} ({level})")

    time.sleep(SLEEP_SECONDS)

print("Geocoding completato.")
