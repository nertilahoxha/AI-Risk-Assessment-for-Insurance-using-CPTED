import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import random
from PIL import Image
import pandas as pd
import os
import joblib

# -----------------------------
# COLORI
# -----------------------------
PRIMARY_RED = "#C6291E"
LIGHT_BG = "#F8F8F8"
TEXT_COLOR = "#202020"

# -----------------------------
# Configurazione pagina
# -----------------------------
st.set_page_config(
    page_title="Generali — Sicurezza Area",
    page_icon="🛡️",
    layout="wide"
)

# -----------------------------
# CSS personalizzato
# -----------------------------
st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {LIGHT_BG};
    }}
    .header-text {{
        color: {PRIMARY_RED};
        font-size:40px;
        font-weight:bold;
        display: inline-block;
        vertical-align: middle;
        margin-left: 15px;
    }}
    .metric-value {{
        color: {PRIMARY_RED};
        font-size:32px;
        font-weight:bold;
    }}
    .metric-label {{
        color:{TEXT_COLOR};
        font-size:20px;
    }}
    </style>
    """,
    unsafe_allow_html=True
)
st.markdown(
    """
    <style>
    /* Forza altezza minima uguale per colonne img e features */
    .streamlit-expanderHeader {
        margin-top: 0 !important;
    }
    .stColumn {
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
    }
    </style>
    """,
    unsafe_allow_html=True
)


st.markdown(
    """
    <style>
    /* Allinea testo a sinistra in tutte le tabelle di Streamlit */
    .dataframe tbody tr th, 
    .dataframe tbody tr td {
        text-align: left !important;
        vertical-align: top;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# -----------------------------
# HEADER
# -----------------------------
col1, col2 = st.columns([1, 8])
with col1:
    st.image("Generali_logo.png", width=80)
with col2:
    st.markdown(
        '<div class="header-text">Assicurazioni Generali — Risk Assessment KPIs</div>',
        unsafe_allow_html=True
    )

st.write("Inserisci l'indirizzo per stimare il rischio e visualizzare la heatmap dei crimini.")

# -----------------------------
# INPUT UTENTE
# -----------------------------
st.subheader("📍 Dati dell'abitazione")

col1, col2, col3, col6 = st.columns([3, 1, 1, 1])

with col1:
    via_piazza = st.text_input("Via / Piazza", placeholder="Es. Via Roma")
with col2:
    numero_civico = st.text_input("Numero civico", placeholder="Es. 12/A")
with col3:
    cap = st.text_input("CAP", placeholder="Es. 20100", max_chars=5)
with col6:
    città = st.text_input("Città", placeholder="Es. Milano")

col4, col5 = st.columns([1, 3])

with col4:
    metri_quadrati = st.text_input("Metri quadrati", placeholder="200")
with col5:
    sistema_allarme = st.radio("Sistema di allarme", ["Sì", "No"])

# -----------------------------
# CARICAMENTO CSV
# -----------------------------
@st.cache_data
def load_abitazioni():
    return pd.read_csv("abitazioni_coordinate_google.csv")

@st.cache_data
def load_finaldataset():
    return pd.read_csv("final_dataset.csv")

df_abitazioni = load_abitazioni()
df_final = load_finaldataset()

# -----------------------------
# RICERCA CLIENTE
# -----------------------------
codice_cliente = None
if via_piazza and numero_civico and città:
    indirizzo_input = f"{via_piazza.strip()}, {numero_civico.strip()}"
    match = df_abitazioni[
        df_abitazioni["Indirizzo"].str.lower().str.contains(indirizzo_input.lower()) &
        df_abitazioni["Luogo di Residenza"].str.lower().str.contains(città.lower())
    ]
    if not match.empty:
        codice_cliente = match.iloc[0]["codice_cliente"]
    else:
        st.warning(f"Nessun cliente trovato per l'indirizzo: {indirizzo_input} in {città}")

# -----------------------------
# MOSTRA INDIRIZZO
# -----------------------------
if via_piazza and numero_civico and città:
    st.write("Indirizzo completo:", f"{via_piazza}, {numero_civico}, {città}")

# -----------------------------
# PREPROCESSING
# -----------------------------
df_final["target"] = df_final["Sinistro"].apply(lambda x: 1 if str(x).strip().lower() == "furto" else 0)
df_final["Sistema_Allarme"] = df_final["Sistema_Allarme"].apply(lambda x: 1 if str(x).strip().lower() == "true" else 0)

for col in ["area_open", "built", "vegetation_high", "vegetation_low", "water", "unknown"]:
    df_final[col] = df_final[col].astype(str).str.replace("%", "", regex=False).astype(float)

# -----------------------------
# IMMAGINE + TABELLE FEATURES
# -----------------------------
if codice_cliente is not None:

    image_folder = "output_satellite_maps_zoom"
    image_path = os.path.join(image_folder, f"{codice_cliente}.png")

    #st.markdown("## 🛰️ Vista satellitare dell’abitazione")

    col_img, col_features = st.columns([3, 2])

    with col_img:
        st.markdown("## 🛰️ Vista satellitare dell’abitazione")
        if os.path.exists(image_path):
            st.image(image_path, caption="Immagine satellitare", width=600)
        else:
            st.error("Immagine satellitare non disponibile.")

    cliente_row = df_final[df_final["codice_cliente"] == codice_cliente]

    if not cliente_row.empty:
        row = cliente_row.iloc[0]

        # --- Territorial Features
        edifici = row["built"]
        vegetazione = row["vegetation_high"]
        spazi_pubblici = row["area_open"] + row["vegetation_low"]
        val_edifici = f"{edifici:.2f}"
        val_vegetazione = f"{vegetazione:.2f}"
        val_spazi = f"{spazi_pubblici:.2f}"

        features_df = pd.DataFrame({
            "Feature": ["Edifici", "Vegetazione Alta", "Spazi Pubblici"],
            "Valore (%)": [val_edifici, val_vegetazione, val_spazi]
        })

     # Street Features - trasforma in stringa
        street_features_df = pd.DataFrame({
                "Feature": ["Node Density (per km²)", "Average Degree", "Primary Road Ratio"],
                "Valore": [
                    f"{round(row['node_density_per_km2_r500'], 2)}",
                    f"{round(row['avg_degree_r500'], 2)}",
                    f"{round(row['primary_ratio'], 2)}"
                ]
        })

        # --- Point of Interest
        school_univ = "Yes" if row["has_school_university_r500"] == 1 else "No"
        security_structures = []
        if row["has_police_r500"] == 1: security_structures.append("Police")
        if row["has_carabinieri_r500"] == 1: security_structures.append("Carabinieri")
        if row["has_fire_station_r500"] == 1: security_structures.append("Fire Station")
        security_str = ", ".join(security_structures) if security_structures else "None"
        nightlife = "Yes" if row["has_nightlife_r500"] == 1 else "No"
        station = "Yes" if row["has_station_r500"] == 1 else "No"

        poi_df = pd.DataFrame({
            "Feature": [
                "School / University",
                "Security Structure Nearby",
                "Nightlife",
                "Train / Metro Station"
            ],
            "Valore": [
                school_univ,
                security_str,
                nightlife,
                station
            ]
        })

        # --- Mostra tutte le tabelle nella stessa colonna a destra della mappa
        with col_features:
             st.markdown("### 🏘️ Territorial Features")
             st.dataframe(features_df, use_container_width=True, hide_index=True)

             st.markdown("### 🛣️ Street Features")
             st.dataframe(street_features_df, use_container_width=True, hide_index=True)

             st.markdown("### 📍 Points of Interest")
             st.dataframe(poi_df, use_container_width=True, hide_index=True)

# -----------------------------
# MODELLO
# -----------------------------
if codice_cliente is not None and not cliente_row.empty:
    @st.cache_resource
    def load_model():
        return joblib.load("adaboost_furti_model.pkl")

    model = load_model()
    X_cliente = cliente_row[model.feature_names_in_]
    prediction = model.predict(X_cliente)[0]
    probability = model.predict_proba(X_cliente)[0][1]

    st.markdown("## 🔐 Valutazione rischio furto")
    if prediction == 1:
        st.error(f"⚠️ **RISCHIO ALTO DI FURTO**\n\nProbabilità stimata: **{probability:.2%}**")
    else:
        st.success(f"✅ **RISCHIO BASSO DI FURTO**\n\nProbabilità stimata: **{probability:.2%}**")
