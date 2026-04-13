import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb
import pickle
import os
import warnings
warnings.filterwarnings('ignore')

# Chemins
data_path = '../data/cleaned/dataset_final_ready.csv'
model_dir = '../models/'
os.makedirs(model_dir, exist_ok=True)

print("Chargement du dataset final...")

df = pd.read_csv(data_path)

# ==================== FEATURES & TARGET ====================
target = 'consommation_kwh'

# Features sélectionnées (tu peux en ajouter/retirer plus tard)
features = [
    'nb_personnes',
    'nb_enfants',
    'ratio_enfants',
    'distance_terrain_km',
    'rural_score',
    'potentiel_solaire',
    'has_electricite'          # si la colonne existe dans ton dataset
]

# Variables catégorielles à encoder (one-hot)
cat_features = ['profession_pere', 'profession_mere', 'acces_electricite_actuel', 'activite']

# Si ces colonnes existent, on les encode
for col in cat_features:
    if col in df.columns:
        df = pd.get_dummies(df, columns=[col], prefix=col, drop_first=True)

# Mise à jour de la liste des features numériques + dummies
feature_cols = [f for f in features if f in df.columns]
feature_cols += [col for col in df.columns if any(c in col for c in cat_features)]

X = df[feature_cols]
y = df[target]

print(f"Features utilisées ({len(feature_cols)}) : {feature_cols}")
print(f"Nombre d'observations : {len(df)}")

# ==================== SPLIT TRAIN/TEST ====================
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# ==================== ENTRAÎNEMENT XGBoost ====================
print("\nEntraînement du modèle XGBoost...")

model = xgb.XGBRegressor(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    objective='reg:squarederror'
)

model.fit(X_train, y_train)

# ==================== ÉVALUATION ====================
y_pred = model.predict(X_test)

mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)

print("\n" + "="*50)
print("RÉSULTATS DU MODÈLE")
print("="*50)
print(f"MAE  : {mae:.2f} kWh/mois")
print(f"RMSE : {rmse:.2f} kWh/mois")
print(f"R²   : {r2:.4f} ({r2*100:.1f}%)")
print("="*50)

# Feature importance
importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print("\nTop 10 features les plus importantes :")
print(importance.head(10))

# ==================== SAUVEGARDE ====================
model_path = f'{model_dir}modele_consommation.pkl'
with open(model_path, 'wb') as f:
    pickle.dump(model, f)

print(f"\n✅ Modèle sauvegardé : {model_path}")
print("Tu peux maintenant passer à l'Étape 3 (script de prédiction)")

# Optionnel : sauvegarder aussi le scaler ou les colonnes si besoin plus tard
with open(f'{model_dir}feature_cols.pkl', 'wb') as f:
    pickle.dump(feature_cols, f)