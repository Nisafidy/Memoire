# ml/scripts/preparer_ml.py
import pandas as pd
import numpy as np
import os
import re

def extraire_lieu_terrain(lieu):
    """Nettoie le lieu terrain"""
    if pd.isna(lieu):
        return None
    lieu = str(lieu).strip()
    if lieu.startswith('- '):
        lieu = lieu[2:]
    return lieu

def main():
    print("=" * 60)
    print("🤖 PRÉPARATION DU DATASET - VERSION PROJET TERRAIN")
    print("=" * 60)
    
    # Charger les données enrichies
    input_path = './data/enriched/enquete_enrichie.csv'
    
    if not os.path.exists(input_path):
        print(f"❌ Fichier non trouvé: {input_path}")
        return None
    
    df = pd.read_csv(input_path)
    print(f"✅ {len(df)} lignes chargées")
    
    # =========================================================
    # 1. NETTOYAGE DES TEXTES
    # =========================================================
    def nettoyer_texte(valeur):
        if pd.isna(valeur):
            return valeur
        valeur = str(valeur)
        if valeur.startswith('- '):
            valeur = valeur[2:]
        return valeur
    
    df['age'] = df['age'].apply(nettoyer_texte)
    df['statut'] = df['statut'].apply(nettoyer_texte)
    df['occupation'] = df['occupation'].apply(nettoyer_texte)
    
    # =========================================================
    # 2. TRAITEMENT DU PROJET TERRAIN (LE CŒUR)
    # =========================================================
    print("\n📍 TRAITEMENT DU PROJET TERRAIN")
    
    # Nettoyer le lieu terrain
    df['lieu_terrain_nettoye'] = df['lieu_terrain'].apply(extraire_lieu_terrain)
    
    # Compter les projets
    nb_projets = df['projet_terrain'].value_counts()
    print(f"   Projet terrain 'oui': {nb_projets.get('oui', 0)}")
    print(f"   Projet terrain 'non': {nb_projets.get('non', 0)}")
    
    # Créer une colonne qui indique si on a un lieu terrain précis
    df['a_lieu_terrain'] = df['lieu_terrain_nettoye'].notna().astype(int)
    
    # Pour ceux qui ont un projet, on va utiliser la production du TERRAIN
    # Pour l'instant, on garde la production du lieu actuel (à améliorer plus tard)
    # TODO: géocoder lieu_terrain et récupérer sa production PVGIS
    
    # =========================================================
    # 3. ESTIMATION DU REVENU
    # =========================================================
    base_salaire = {
        'fonctionnaire': 400000,
        'enseignement': 350000,
        'sante': 500000,
        'commerce': 300000,
        'agriculture': 200000,
        'btp': 250000,
        'artisanat': 250000,
        'transport': 300000,
        'retraite': 200000,
        'sans_emploi': 0,
        'it_freelance': 600000,
        'service': 250000,
        'autre': 250000
    }
    
    df['revenu_pere'] = df['cat_pere'].map(base_salaire).fillna(250000)
    df['revenu_mere'] = df['cat_mere'].map(base_salaire).fillna(250000)
    df['revenu_total'] = df['revenu_pere'] + df['revenu_mere']
    
    # =========================================================
    # 4. ENCODAGE DES CATÉGORIES
    # =========================================================
    from sklearn.preprocessing import LabelEncoder
    
    encoders = {}
    colonnes_encoder = ['cat_pere', 'cat_mere', 'acces_electricite', 'age', 'statut']
    
    print("\n🏷️ ENCODAGE:")
    for col in colonnes_encoder:
        le = LabelEncoder()
        df[col + '_code'] = le.fit_transform(df[col].astype(str))
        encoders[col] = le
        print(f"   {col}: {len(le.classes_)} catégories")
    
    # =========================================================
    # 5. FEATURES POUR LE ML
    # =========================================================
    
    # Features de base
    features_base = [
        'personnes',
        'enfants',
        'nb_usages',
        'revenu_total',
        'production',
        'cat_pere_code',
        'cat_mere_code',
        'acces_electricite_code',
        'age_code',
        'statut_code'
    ]
    
    # Features du projet terrain (LE CŒUR)
    features_projet = [
        'projet_terrain',      # oui/non
        'a_lieu_terrain',      # a-t-on un lieu précis ?
        'distance_terrain_km'  # distance en km
    ]
    
    # Toutes les features
    all_features = features_base + features_projet
    
    target = 'consommation_kwh'
    
    # =========================================================
    # 6. CRÉATION DU DATASET
    # =========================================================
    
    # Garder les colonnes utiles
    df_ml = df[all_features + [target]].copy()
    
    # Encoder 'projet_terrain' en binaire
    df_ml['projet_terrain_code'] = (df_ml['projet_terrain'] == 'oui').astype(int)
    
    # Remplacer les valeurs manquantes dans distance_terrain_km par 0
    df_ml['distance_terrain_km'] = df_ml['distance_terrain_km'].fillna(0)
    
    # Supprimer les lignes sans consommation
    df_ml = df_ml.dropna(subset=[target])
    
    print(f"\n📊 DATASET ML FINAL:")
    print(f"   Lignes: {len(df_ml)}")
    print(f"   Features: {len(all_features) + 1}")  # +1 pour projet_terrain_code
    print(f"   Target: {target}")
    
    # Afficher la répartition projet terrain
    print(f"\n   Répartition projet terrain:")
    print(f"   - Oui: {(df_ml['projet_terrain_code'] == 1).sum()}")
    print(f"   - Non: {(df_ml['projet_terrain_code'] == 0).sum()}")
    
    # =========================================================
    # 7. SAUVEGARDE
    # =========================================================
    output_path = './data/enriched/dataset_ml.csv'
    df_ml.to_csv(output_path, index=False, encoding='utf-8')
    print(f"\n✅ Dataset sauvegardé: {output_path}")
    
    # =========================================================
    # 8. APERÇU
    # =========================================================
    print("\n📋 APERÇU DES DONNÉES:")
    cols_afficher = ['personnes', 'enfants', 'revenu_total', 'production', 
                     'projet_terrain_code', 'distance_terrain_km', target]
    print(df_ml[cols_afficher].head(15).to_string())
    
    # =========================================================
    # 9. STATISTIQUES PAR GROUPE
    # =========================================================
    print("\n📊 STATISTIQUES:")
    print(f"Consommation moyenne (total): {df_ml[target].mean():.1f} kWh/mois")
    
    # Consommation selon projet terrain
    conso_oui = df_ml[df_ml['projet_terrain_code'] == 1][target].mean()
    conso_non = df_ml[df_ml['projet_terrain_code'] == 0][target].mean()
    print(f"Consommation moyenne (avec projet): {conso_oui:.1f} kWh/mois" if conso_oui > 0 else "   (pas assez de données avec projet)")
    print(f"Consommation moyenne (sans projet): {conso_non:.1f} kWh/mois")
    
    return df_ml

if __name__ == "__main__":
    df = main()

