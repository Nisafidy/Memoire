import pandas as pd
import pickle
import sys
import json

model_path = '../models/modele_consommation.pkl'
feature_cols_path = '../models/feature_cols.pkl'

def load_model():
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    with open(feature_cols_path, 'rb') as f:
        feature_cols = pickle.load(f)
    return model, feature_cols

# Lecture des données depuis stdin (envoyées par Node.js)
input_json = sys.stdin.read().strip()
input_data = json.loads(input_json)

model, feature_cols = load_model()

# Création du DataFrame
df_input = pd.DataFrame([input_data])

# One-hot encoding
cat_features = ['profession_pere', 'profession_mere', 'acces_electricite_actuel']
for col in cat_features:
    if col in df_input.columns:
        df_input = pd.get_dummies(df_input, columns=[col], prefix=col, drop_first=True)

# Alignement des colonnes
for col in feature_cols:
    if col not in df_input.columns:
        df_input[col] = 0

df_input = df_input[feature_cols]

# Prédiction
prediction = model.predict(df_input)[0]
prediction = max(0, round(float(prediction), 2))

print(json.dumps({
    "consommation_kwh_predite": prediction,
    "message": f"Consommation mensuelle estimée : {prediction} kWh"
}, ensure_ascii=False))