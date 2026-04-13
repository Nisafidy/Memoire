import pandas as pd
import numpy as np
import os

# Chemins (adapte si besoin)
epm_path = '../data/raw/menages_epm_fusionnes.csv'          # ton fichier EPM nettoyé
enrichie_path = '../data/enriched/enquete_enrichie.csv'    # ton fichier des 75+ réponses
output_dir = '../data/cleaned/'
os.makedirs(output_dir, exist_ok=True)

print("Chargement des données...")

# 1. Charger EPM (adapte les noms de colonnes si nécessaire)
epm = pd.read_csv(epm_path)

# Nettoyage basique EPM
epm['has_electricite'] = epm['depense_moyenne_Ar'].apply(lambda x: 1 if x > 0 else 0)
epm['profession'] = epm['profession'].fillna('autre').astype(str)
epm['categorie_conso'] = epm['categorie_conso'].fillna('aucune')

# 2. Charger ton enquête enrichie
enrichie = pd.read_csv(enrichie_path)

# Nettoyage enrichie
enrichie['timestamp'] = pd.to_datetime(enrichie['timestamp'], errors='coerce')
enrichie['nb_personnes'] = pd.to_numeric(enrichie['personnes'], errors='coerce')
enrichie['nb_enfants'] = pd.to_numeric(enrichie['enfants'], errors='coerce')
enrichie['distance_terrain_km'] = pd.to_numeric(enrichie['distance_terrain_km'], errors='coerce')
enrichie['consommation_kwh'] = pd.to_numeric(enrichie['consommation_kwh'], errors='coerce')
enrichie['potentiel_solaire'] = pd.to_numeric(enrichie['production'], errors='coerce')

# Créer features utiles
enrichie['total_actifs'] = enrichie['autres_actifs'].fillna(0)  # à améliorer selon ton parsing
enrichie['profession_pere'] = enrichie['cat_pere'].fillna('autre')
enrichie['profession_mere'] = enrichie['cat_mere'].fillna('autre')
enrichie['acces_electricite_actuel'] = enrichie['acces_electricite'].fillna('inconnu')

# 3. Standardiser les noms de colonnes pour fusion
epm_renamed = epm.rename(columns={
    'nb_personnes': 'nb_personnes',
    'profession': 'profession_pere',   # on approxime
    'consommation_kwh': 'consommation_kwh',
    'production': 'potentiel_solaire'
})

enrichie_renamed = enrichie.rename(columns={
    'nb_personnes': 'nb_personnes',
    'profession_pere': 'profession_pere',
    'consommation_kwh': 'consommation_kwh',
    'potentiel_solaire': 'potentiel_solaire',
    'distance_terrain_km': 'distance_terrain_km'
})

# 4. Concaténer (on garde toutes les lignes)
dataset_final = pd.concat([epm_renamed, enrichie_renamed], ignore_index=True, sort=False)

# 5. Features supplémentaires
dataset_final['ratio_enfants'] = dataset_final['nb_enfants'] / dataset_final['nb_personnes'].replace(0, 1)
dataset_final['rural_score'] = dataset_final['distance_terrain_km'].apply(lambda x: min(100, x * 2) if pd.notna(x) else 30)

# Remplir les valeurs manquantes
numeric_cols = ['nb_personnes', 'nb_enfants', 'consommation_kwh', 'potentiel_solaire', 
                'distance_terrain_km', 'ratio_enfants', 'rural_score']
for col in numeric_cols:
    if col in dataset_final.columns:
        dataset_final[col] = dataset_final[col].fillna(dataset_final[col].median())

categorical_cols = ['profession_pere', 'profession_mere', 'acces_electricite_actuel', 'activite']
for col in categorical_cols:
    if col in dataset_final.columns:
        dataset_final[col] = dataset_final[col].fillna('autre')

print(f"Dataset final créé : {dataset_final.shape[0]} lignes, {dataset_final.shape[1]} colonnes")
print("\nColonnes disponibles :", list(dataset_final.columns))

# Sauvegarder
dataset_final.to_csv(f'{output_dir}dataset_final_ready.csv', index=False)
dataset_final.to_csv(f'{output_dir}dataset_final_ready.pkl', index=False)  # aussi en pickle pour plus rapide

print("\n✅ Fichiers sauvegardés dans ml/data/cleaned/")
print("   - dataset_final_ready.csv")
print("   - dataset_final_ready.pkl")
print("\nProchaine étape : Entraînement du modèle (dis-moi quand tu es prêt)")