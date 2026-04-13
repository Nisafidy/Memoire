# ml/scripts/enrichir.py
import pandas as pd
import requests
import time
import os
import re

def creer_dossiers():
    """Crée les dossiers data/enriched s'il n'existe pas"""
    dossier = './data/enriched'
    if not os.path.exists(dossier):
        os.makedirs(dossier)
        print(f"📁 Dossier créé: {dossier}")

def extraire_lieu_precis(lieu):
    """Extrait la partie la plus précise du lieu"""
    if pd.isna(lieu):
        return None
    
    lieu = str(lieu).strip()
    
    if lieu.startswith('- '):
        lieu = lieu[2:]
    
    if '-' in lieu:
        parties = lieu.split('-')
        return parties[-1].strip()
    
    if 'Antananarivo' in lieu and len(lieu) > len('Antananarivo'):
        reste = lieu.replace('Antananarivo', '').strip()
        if reste:
            return reste
    
    return lieu

def geocoder_lieu(lieu):
    """Convertit un lieu en coordonnées"""
    if not lieu:
        return None, None
    
    query = f"{lieu}, Madagascar"
    
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': query,
        'format': 'json',
        'limit': 1,
        'countrycodes': 'mg'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10, headers={
            'User-Agent': 'EnergyMadagascarApp/1.0'
        })
        
        if response.status_code != 200:
            return None, None
        
        data = response.json()
        
        if data and len(data) > 0:
            lat = float(data[0]['lat'])
            lon = float(data[0]['lon'])
            return lat, lon
        else:
            return None, None
    except Exception:
        return None, None

def get_pvgis_production(lat, lon):
    """Récupère uniquement la production PVGIS"""
    if lat is None or lon is None:
        return None
    
    url = "https://re.jrc.ec.europa.eu/api/v5_2/PVcalc"
    params = {
        'lat': lat,
        'lon': lon,
        'peakpower': 1,
        'loss': 14,
        'outputformat': 'json'
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        
        if 'outputs' in data and 'totals' in data['outputs']:
            totals = data['outputs']['totals']['fixed']
            production = totals.get('E_y', None)
            return production
        else:
            return None
    except Exception:
        return None

def main():
    print("=" * 50)
    print("🌞 ENRICHISSEMENT AVEC PVGIS")
    print("=" * 50)
    
    creer_dossiers()
    
    input_path = './data/cleaned/enquete_nettoyee.csv'
    
    if not os.path.exists(input_path):
        print(f"❌ Fichier non trouvé: {input_path}")
        return None
    
    df = pd.read_csv(input_path)
    print(f"✅ {len(df)} lignes chargées")
    
    # Extraire le lieu précis
    df['lieu_precis'] = df['lieu'].apply(extraire_lieu_precis)
    
    print("\n📋 Exemple d'extraction des lieux:")
    for i in range(min(5, len(df))):
        print(f"   '{df.iloc[i]['lieu']}' → '{df.iloc[i]['lieu_precis']}'")
    
    # Colonnes pour les résultats
    df['latitude'] = None
    df['longitude'] = None
    df['production'] = None
    
    lieux_uniques = df['lieu_precis'].dropna().unique()
    print(f"\n📍 {len(lieux_uniques)} lieux uniques à traiter")
    
    cache = {}
    
    for i, lieu in enumerate(lieux_uniques):
        print(f"\n[{i+1}/{len(lieux_uniques)}] '{lieu}'")
        
        if lieu in cache:
            print(f"   ↳ Utilisation du cache")
            lat, lon, prod = cache[lieu]
        else:
            lat, lon = geocoder_lieu(lieu)
            if lat:
                print(f"   📍 Coordonnées: {lat:.4f}, {lon:.4f}")
                prod = get_pvgis_production(lat, lon)
                if prod:
                    print(f"   ⚡ Production: {prod:.0f} kWh/kWc/an")
                else:
                    print(f"   ⚠️ Production non disponible")
            else:
                print(f"   ❌ Lieu non trouvé")
                prod = None
            
            cache[lieu] = (lat, lon, prod)
        
        # Appliquer à toutes les lignes
        mask = df['lieu_precis'] == lieu
        df.loc[mask, 'latitude'] = lat
        df.loc[mask, 'longitude'] = lon
        df.loc[mask, 'production'] = prod
        
        time.sleep(1)
    
    # Sauvegarder
    output_path = './data/enriched/enquete_enrichie.csv'
    df.to_csv(output_path, index=False, encoding='utf-8')
    print(f"\n✅ Données enrichies sauvegardées: {output_path}")
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ")
    print("=" * 50)
    
    nb_geocodes = df['latitude'].notna().sum()
    nb_prod = df['production'].notna().sum()
    
    print(f"Lignes géocodées: {nb_geocodes}/{len(df)}")
    print(f"Lignes avec production: {nb_prod}/{len(df)}")
    
    if nb_prod > 0:
        print(f"\nProduction moyenne: {df['production'].mean():.0f} kWh/kWc/an")
        print(f"Production min: {df['production'].min():.0f}")
        print(f"Production max: {df['production'].max():.0f}")
    
    print("\n📋 Aperçu:")
    cols = ['lieu', 'lieu_precis', 'latitude', 'longitude', 'production', 'consommation_kwh']
    print(df[cols].head(10).to_string())
    
    return df

if __name__ == "__main__":
    df = main()