"""
ml/scripts/nettoyer.py
"""
import pandas as pd
import numpy as np
import re
import sys
import os

# Créer les dossiers si besoin
def creer_dossiers():
    """Crée les dossiers data/cleaned et data/enriched s'ils n'existent pas"""
    dossiers = [
        './data/cleaned',
        './data/enriched'
    ]
    for dossier in dossiers:
        if not os.path.exists(dossier):
            os.makedirs(dossier)
            print(f"📁 Dossier créé: {dossier}")

def extraire_nombre_texte(valeur):
    """Extrait le premier nombre d'une chaîne comme '- 10 personnes ou plus' -> 10"""
    if pd.isna(valeur):
        return None
    valeur = str(valeur)
    
    chiffres = re.findall(r'\d+', valeur)
    if chiffres:
        return int(chiffres[0])
    
    if 'un' in valeur.lower() or 'une' in valeur.lower():
        return 1
    
    return None

def extraire_premiere_profession(prof):
    """Prend la première profession quand il y en a plusieurs"""
    if pd.isna(prof):
        return None
    prof = str(prof)
    if ',' in prof:
        prof = prof.split(',')[0]
    if '- ' in prof:
        prof = prof.replace('- ', '')
    return prof.strip()

def extraire_consommation(conso):
    """Convertit la consommation en kWh"""
    if pd.isna(conso):
        return None
    
    conso = str(conso).lower().replace(' ', '')
    
    chiffres = re.findall(r'\d+', conso)
    if not chiffres:
        return None
    
    valeur = int(chiffres[0])
    
    if 'kwh' in conso or 'khw' in conso:
        return valeur
    
    if 'ar' in conso:
        return valeur / 500
    
    if valeur > 500:
        return valeur / 500
    else:
        return valeur

def extraire_oui_non(valeur):
    """Pour les questions oui/non avec plusieurs options"""
    if pd.isna(valeur):
        return 'non'
    valeur = str(valeur).lower()
    if 'oui' in valeur:
        return 'oui'
    return 'non'

def extraire_distance(valeur):
    """Extrait la distance en km"""
    if pd.isna(valeur):
        return None
    valeur = str(valeur).lower()
    chiffres = re.findall(r'\d+', valeur)
    if chiffres:
        return int(chiffres[0])
    
    if 'moins de 50' in valeur:
        return 25
    if '50 à 200' in valeur:
        return 125
    if '200 à 500' in valeur:
        return 350
    if 'plus de 500' in valeur:
        return 600
    
    return None

def categoriser_profession(prof):
    """Catégorise les professions"""
    if pd.isna(prof):
        return 'inconnu'
    prof = str(prof).lower()
    
    if 'fonctionnaire' in prof:
        return 'fonctionnaire'
    if 'enseignant' in prof or 'instituteur' in prof:
        return 'enseignement'
    if 'médecin' in prof or 'infirmier' in prof or 'santé' in prof:
        return 'sante'
    if 'commerce' in prof or 'commerçant' in prof or 'vendeur' in prof:
        return 'commerce'
    if 'agriculture' in prof or 'paysan' in prof or 'élevage' in prof:
        return 'agriculture'
    if 'btp' in prof or 'construction' in prof or 'maçon' in prof or 'charpentier' in prof:
        return 'btp'
    if 'artisan' in prof or 'couturier' in prof or 'menuisier' in prof:
        return 'artisanat'
    if 'transport' in prof or 'chauffeur' in prof or 'taxi' in prof:
        return 'transport'
    if 'retraité' in prof:
        return 'retraite'
    if 'sans emploi' in prof:
        return 'sans_emploi'
    if 'assistant virtuel' in prof:
        return 'it_freelance'
    if 'receptioniste' in prof:
        return 'service'
    return 'autre'

def standardiser_acces(acces):
    """Standardise l'accès à l'électricité"""
    if pd.isna(acces):
        return 'inconnu'
    acces = str(acces).lower()
    if '24h' in acces and 'coupure' not in acces:
        return 'jir_24h'
    if 'coupure' in acces:
        return 'jir_coupures'
    if 'pas tous les jours' in acces:
        return 'jir_irregulier'
    if 'solaire' in acces:
        return 'solaire'
    if 'groupe' in acces:
        return 'groupe'
    return 'jir_24h'

def enlever_tiret(valeur):
    if pd.isna(valeur):
        return valeur
    valeur = str(valeur)
    if valeur.startswith('- '):
        return valeur[2:]
    return valeur

def main():
    print("=" * 50)
    print("🧹 NETTOYAGE DES DONNÉES - VERSION ADAPTÉE")
    print("=" * 50)
    
    # Créer les dossiers si besoin
    creer_dossiers()
    
    input_path = './data/raw/enquete_extraite.csv'
    
    # Détection automatique du séparateur
    with open(input_path, 'r', encoding='utf-8') as f:
        first_line = f.readline()
        if '\t' in first_line:
            sep = '\t'
        else:
            sep = ','
    
    type_sep = 'TAB' if sep == '\t' else 'VIRGULE'
    print(f"📂 Chargement avec séparateur: {type_sep}")
    
    df = pd.read_csv(input_path, sep=sep)
    print(f"✅ {len(df)} lignes chargées")
    
    col_names = list(df.columns)
    
    # Vérifier que nous avons assez de colonnes
    if len(col_names) < 20:
        print(f"⚠️ Attention: Seulement {len(col_names)} colonnes trouvées")
        print(f"Colonnes: {col_names}")
    
    mapping = {
        col_names[0]: 'timestamp',
        col_names[1]: 'lieu',
        col_names[2]: 'lieu_precis',
        col_names[3]: 'personnes_raw',
        col_names[4]: 'enfants_raw',
        col_names[5]: 'profession_pere_raw',
        col_names[6]: 'profession_pere_autre',
        col_names[7]: 'profession_mere_raw',
        col_names[8]: 'profession_mere_autre',
        col_names[9]: 'autres_actifs',
        col_names[10]: 'projet_terrain_raw',
        col_names[11]: 'lieu_terrain',
        col_names[12]: 'distance_terrain_raw',
        col_names[13]: 'usages',
        col_names[14]: 'activite',
        col_names[15]: 'consommation_raw',
        col_names[16]: 'acces_electricite_raw',
        col_names[17]: 'age',
        col_names[18]: 'statut',
        col_names[19]: 'occupation'
    }
    
    df = df.rename(columns=mapping)
    
    # Appliquer les transformations
    df['personnes'] = df['personnes_raw'].apply(extraire_nombre_texte)
    df['enfants'] = df['enfants_raw'].apply(extraire_nombre_texte)
    
    df['profession_pere'] = df['profession_pere_raw'].apply(extraire_premiere_profession)
    df['profession_mere'] = df['profession_mere_raw'].apply(extraire_premiere_profession)
    
    df['cat_pere'] = df['profession_pere'].apply(categoriser_profession)
    df['cat_mere'] = df['profession_mere'].apply(categoriser_profession)
    
    df['consommation_kwh'] = df['consommation_raw'].apply(extraire_consommation)
    
    df['projet_terrain'] = df['projet_terrain_raw'].apply(extraire_oui_non)
    
    df['distance_terrain_km'] = df['distance_terrain_raw'].apply(extraire_distance)
    
    df['acces_electricite'] = df['acces_electricite_raw'].apply(standardiser_acces)
    
    df['nb_usages'] = df['usages'].apply(lambda x: len(str(x).split(',')) if pd.notna(x) else 0)
    
    # Appliquer enlever_tiret après le renommage
    df['age'] = df['age'].apply(enlever_tiret)
    df['statut'] = df['statut'].apply(enlever_tiret)
    df['occupation'] = df['occupation'].apply(enlever_tiret)
    
    colonnes_finales = [
        'timestamp', 'lieu', 'lieu_precis',
        'personnes', 'enfants',
        'cat_pere', 'cat_mere',
        'autres_actifs',
        'projet_terrain', 'lieu_terrain', 'distance_terrain_km',
        'nb_usages',
        'consommation_kwh',
        'acces_electricite',
        'age', 'statut', 'occupation', 'activite'
    ]    

    # Vérifier que toutes les colonnes existent
    colonnes_existantes = [col for col in colonnes_finales if col in df.columns]
    if len(colonnes_existantes) < len(colonnes_finales):
        manquantes = set(colonnes_finales) - set(colonnes_existantes)
        print(f"⚠️ Colonnes manquantes: {manquantes}")
    
    df_clean = df[colonnes_existantes]
    
    output_path = './data/cleaned/enquete_nettoyee.csv'
    df_clean.to_csv(output_path, index=False, encoding='utf-8')
    print(f"\n✅ Données nettoyées sauvegardées: {output_path}")
    
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ")
    print("=" * 50)
    print(f"Réponses: {len(df_clean)}")
    
    # Afficher les stats avec gestion des valeurs NaN
    personnes_mean = df_clean['personnes'].mean()
    if not pd.isna(personnes_mean):
        print(f"Personnes moyennes: {personnes_mean:.1f}")
    
    conso_mean = df_clean['consommation_kwh'].mean()
    if not pd.isna(conso_mean):
        print(f"Consommation moyenne: {conso_mean:.1f} kWh/mois")
    
    conso_median = df_clean['consommation_kwh'].median()
    if not pd.isna(conso_median):
        print(f"Consommation médiane: {conso_median:.1f} kWh/mois")
    
    print(f"Réponses avec consommation: {df_clean['consommation_kwh'].notna().sum()}")
    
    print("\n🏷️ Professions père:")
    print(df_clean['cat_pere'].value_counts())
    
    print("\n🔌 Accès électricité:")
    print(df_clean['acces_electricite'].value_counts())
    
    return df_clean

if __name__ == "__main__":
    df = main()