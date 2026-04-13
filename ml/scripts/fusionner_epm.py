# ml/scripts/fusionner_epm.py
import pandas as pd
import numpy as np
import os

print("=" * 70)
print("🔗 FUSION IMPO + EMPL")
print("=" * 70)

# Chemin des fichiers
dossier_data = '../data/raw'  # Assurez-vous que ce chemin est correct selon votre structure de dossiers
fichier_impo = os.path.join(dossier_data, '21_MDG_EPM2122_IMPO.dta')
fichier_empl = os.path.join(dossier_data, '04_MDG_EPM2122_EMPL.dta')

# 1. Charger IMPO (dépenses électricité)
print("\n1. Chargement de IMPO...")
df_impo = pd.read_stata(fichier_impo)
print(f"   ✅ {len(df_impo)} ménages")
print(f"   Colonnes: {list(df_impo.columns)}")

# 2. Charger EMPL (emploi)
print("\n2. Chargement de EMPL...")
df_empl = pd.read_stata(fichier_empl)
print(f"   ✅ {len(df_empl)} individus")
print(f"   Colonnes (premières): {list(df_empl.columns)[:15]}")

# 3. Fusionner sur idHH (identifiant ménage)
print("\n3. Fusion sur idHH...")
df_merged = pd.merge(df_impo, df_empl, on=['idHH', 'hhgrap', 'hhnum'], how='left')
print(f"   ✅ {len(df_merged)} lignes après fusion")
print(f"   Ménages uniques: {df_merged['idHH'].nunique()}")

# 4. Sauvegarder
output_path = './data/enriched/epm_fusionne.csv'
df_merged.to_csv(output_path, index=False)
print(f"\n✅ Fichier sauvegardé: {output_path}")
print(f"   Taille: {df_merged.shape[0]} lignes, {df_merged.shape[1]} colonnes")

print("\n✅ Fusion terminée")