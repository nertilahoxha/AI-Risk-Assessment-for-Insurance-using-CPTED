import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import recall_score
from sklearn.ensemble import AdaBoostClassifier
import joblib

def create_derived_features(df):
    # converti tutte le lunghezze in metri prima del calcolo dei rapporti
    df['residential_ratio'] = (df['km_residential_r500'] * 1000) / (df['total_street_length_m_r500'] + 1e-6)
    df.drop(columns=['km_residential_r500'], inplace=True)

    df['primary_ratio'] = (df['km_primary_r500'] * 1000) / (df['total_street_length_m_r500'] + 1e-6)
    df.drop(columns=['km_primary_r500'], inplace=True)

    df['secondary_ratio'] = (df['km_secondary_r500'] * 1000) / (df['total_street_length_m_r500'] + 1e-6)
    df.drop(columns=['km_secondary_r500'], inplace=True)

    df['tertiary_ratio'] = (df['km_tertiary_r500'] * 1000) / (df['total_street_length_m_r500'] + 1e-6)
    df.drop(columns=['km_tertiary_r500'], inplace=True)

    df['living_ratio'] = (df['km_living_street_r500'] * 1000) / (df['total_street_length_m_r500'] + 1e-6)
    df.drop(columns=['km_living_street_r500'], inplace=True)

    df['service_ratio'] = (df['km_service_r500'] * 1000) / (df['total_street_length_m_r500'] + 1e-6)
    df.drop(columns=['km_service_r500'], inplace=True)

    return df

df_abitazioni = pd.read_csv(r'output\abitazioni_coordinate_google.csv')
cols_to_keep = ['codice_cliente', 'Sistema_Allarme']
df_abitazioni = df_abitazioni[cols_to_keep]

df_sinistri = pd.read_csv(r'dataset\sinistri.csv')
cols_to_keep = ['codice_cliente', 'Prodotto', 'Sinistro']
df_sinistri = df_sinistri[cols_to_keep]
df_sinistri['is_furto'] = df_sinistri['Sinistro'].str.strip().str.lower() == 'furto'
df_sinistri_sorted = df_sinistri.sort_values('is_furto', ascending=False)
df_sinistri_unique = df_sinistri_sorted.drop_duplicates(subset='codice_cliente', keep='first')
df_sinistri_unique = df_sinistri_unique.drop(columns='is_furto')
df_sinistri_unique['Sinistro'] = df_sinistri_unique['Sinistro'].apply(
    lambda x: 'Furto' if str(x).strip().lower() == 'furto' else 'Non Furto'
)

df_mappe_satellitari = pd.read_csv(r'output\cpted_master.v1i.yolov8\dataset_summary.csv')
cols_to_drop = ['split']
df_mappe_satellitari = df_mappe_satellitari.drop(columns=cols_to_drop).rename(columns={'image': 'codice_cliente'})

df = pd.read_csv(r'output\cpted_osm_features.csv')
cols_to_drop = df.columns[df.columns.str.contains(r'_r100|_r300')].tolist()
cols_to_drop += ['error', 'network_type', 'graph_ok_r500', 'km_motorway_r500', 'dist_motorway_m_r500', 'lat', 'lon', 'landuse_mode_r500']
cols_to_drop += ['km_trunk_r500', 'dist_trunk_m_r500', 'km_unclassified_r500', 'dist_unclassified_m_r500']
df = df.drop(columns=cols_to_drop)

# imputazione mediana per tutte le colonne numeriche
df_imputed = df.copy()
df_imputed[df_imputed.select_dtypes(include='number').columns] = \
    df_imputed.select_dtypes(include='number').fillna(df_imputed.median())

def create_derived_features(df):
    # converti tutte le lunghezze in metri prima del calcolo dei rapporti
    df['residential_ratio'] = (df['km_residential_r500'] * 1000) / (df['total_street_length_m_r500'] + 1e-6)
    df.drop(columns=['km_residential_r500'], inplace=True)

    df['primary_ratio'] = (df['km_primary_r500'] * 1000) / (df['total_street_length_m_r500'] + 1e-6)
    df.drop(columns=['km_primary_r500'], inplace=True)

    df['secondary_ratio'] = (df['km_secondary_r500'] * 1000) / (df['total_street_length_m_r500'] + 1e-6)
    df.drop(columns=['km_secondary_r500'], inplace=True)

    df['tertiary_ratio'] = (df['km_tertiary_r500'] * 1000) / (df['total_street_length_m_r500'] + 1e-6)
    df.drop(columns=['km_tertiary_r500'], inplace=True)

    df['living_ratio'] = (df['km_living_street_r500'] * 1000) / (df['total_street_length_m_r500'] + 1e-6)
    df.drop(columns=['km_living_street_r500'], inplace=True)

    df['service_ratio'] = (df['km_service_r500'] * 1000) / (df['total_street_length_m_r500'] + 1e-6)
    df.drop(columns=['km_service_r500'], inplace=True)

    return df

df_derivate = create_derived_features(df_imputed)
df_cleaned = df_derivate.drop(columns=['edge_density_per_km2_r500', 'intersection_density_deg_ge_3_per_km2_r500', 'total_street_length_m_r500',
                            'street_length_density_km_per_km2_r500', 'culdesac_ratio_r500', 'intersection_ratio_deg_ge_3_r500'])
df_osmnx = df_cleaned.copy()

df_final = df_abitazioni.merge(df_sinistri_unique, on='codice_cliente', how='inner')
df_final = df_final.merge(df_mappe_satellitari, on='codice_cliente', how='inner')
df_final = df_final.merge(df_osmnx, on='codice_cliente', how='inner')

df_final.to_csv(r'output\final_dataset.csv', index=False)
    
# -----------------------------
# Preprocessing
# -----------------------------
df_final['target'] = df_final['Sinistro'].apply(
    lambda x: 1 if str(x).strip().lower() == 'furto' else 0
)

df_final['Sistema_Allarme'] = df_final['Sistema_Allarme'].apply(
    lambda x: 1 if str(x).strip().lower() == 'true' else 0
)

for col in [
    'area_open', 'built', 'vegetation_high',
    'vegetation_low', 'water', 'unknown'
]:
    df_final[col] = (
        df_final[col]
        .astype(str)
        .str.replace('%', '', regex=False)
        .astype(float)
    )

# -----------------------------
# Aggiungi colonna train/test
# -----------------------------
df_final['dataset_split'] = 'unassigned'
indices = df_final.index
train_idx, test_idx = train_test_split(
    indices,
    test_size=0.3,
    random_state=42,
    stratify=df_final['target']
)
df_final.loc[train_idx, 'dataset_split'] = 'train'
df_final.loc[test_idx, 'dataset_split'] = 'test'

# -----------------------------
# Feature / Target
# -----------------------------
X = df_final.drop(columns=['codice_cliente', 'Sinistro', 'target', 'Prodotto', 'dataset_split'])
y = df_final['target']

# -----------------------------
# Train / Test split
# -----------------------------

X_train = X.loc[train_idx]
X_test = X.loc[test_idx]
y_train = y.loc[train_idx]
y_test = y.loc[test_idx]

# -----------------------------
# Sample weights (classi sbilanciate)
# -----------------------------
class_weights = {
    0: 1.0,
    1: (y_train == 0).sum() / (y_train == 1).sum()
}

sample_weight = y_train.map(class_weights)

# -----------------------------
# Modello AdaBoost
# -----------------------------
ada = AdaBoostClassifier(
    n_estimators=300,
    learning_rate=0.05,
    algorithm='SAMME',
    random_state=42
)

ada.fit(X_train, y_train, sample_weight=sample_weight)

# -----------------------------
# Predizioni e recall
# -----------------------------
y_prob = ada.predict_proba(X_test)[:, 1]
y_pred = (y_prob >= 0.3).astype(int)

recall = recall_score(y_test, y_pred)
print(f"Recall (Sensibilità dei Furti): {recall:.3f}")

joblib.dump(ada, r'output\adaboost_furti_model.pkl')
print("Modello AdaBoost salvato correttamente")
