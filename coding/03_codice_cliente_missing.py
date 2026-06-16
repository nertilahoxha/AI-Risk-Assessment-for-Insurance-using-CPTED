import pandas as pd
from pathlib import Path

# =======================
# PARAMETRI
# =======================

INPUT_CSV = Path(r"output\cpted_osm_features.csv")
OUTPUT_TXT = Path(r"output\codice_cliente_missing.txt")

ID_COLUMN = "codice_cliente"        # usa nome normalizzato
CHECK_COLUMN = "graph_ok_r100"      # usa nome normalizzato

# =======================
# LETTURA CSV
# =======================

df = pd.read_csv(INPUT_CSV)

# =======================
# NORMALIZZAZIONE COLONNE
# =======================

df.columns = (
    df.columns
    .str.strip()
    .str.lower()
)

# =======================
# VALIDAZIONI
# =======================

if ID_COLUMN not in df.columns:
    raise ValueError(
        f"Colonna '{ID_COLUMN}' non trovata. Colonne disponibili:\n{list(df.columns)}"
    )

if CHECK_COLUMN not in df.columns:
    raise ValueError(
        f"Colonna '{CHECK_COLUMN}' non trovata. Colonne disponibili:\n{list(df.columns)}"
    )

# =======================
# FILTRO VALORI MANCANTI
# =======================

mask_missing = df[CHECK_COLUMN].isna()
codici = df.loc[mask_missing, ID_COLUMN]

# =======================
# SCRITTURA TXT
# =======================

with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
    for codice in codici:
        f.write(f"{codice}\n")

print(f"Trovati {len(codici)} codici cliente con valori mancanti in '{CHECK_COLUMN}'")
print(f"File generato: {OUTPUT_TXT.resolve()}")
