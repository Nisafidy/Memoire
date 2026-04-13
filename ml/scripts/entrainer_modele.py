# ml/scripts/entrainer_modele.py
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler

def main():
    print("=" * 60)
    print("🤖 ENTRAÎNEMENT DU PREMIER MODÈLE ML")
    print("=" * 60)
    
    # Charger le dataset
    input_path = './data/enriched/dataset_ml.csv'
    
    if not os.path.exists(input_path):
        print(f"❌ Fichier non trouvé: {input_path}")
        return None
    
    df = pd.read_csv(input_path)
    print(f"✅ {len(df)} lignes chargées")
    
    # Séparer features et target
    target = 'consommation_kwh'

    # Liste des features à exclure (colonnes texte)
    colonnes_a_exclure = ['projet_terrain']  # On garde projet_terrain_code à la place

    features = [col for col in df.columns if col != target and col not in colonnes_a_exclure]
    
    X = df[features]
    y = df[target]
    
    print(f"\n📊 Features ({len(features)}):")
    for f in features:
        print(f"   - {f}")
    
    # Split train/test (80% / 20%)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print(f"\n📊 Split des données:")
    print(f"   Train: {len(X_train)} lignes")
    print(f"   Test: {len(X_test)} lignes")
    
    # Entraîner un Random Forest (robuste avec peu de données)
    print("\n🌳 Entraînement du modèle Random Forest...")
    
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=5,
        random_state=42
    )
    
    model.fit(X_train, y_train)
    
    # Prédictions
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    
    # Évaluation
    print("\n📊 PERFORMANCES:")
    print("-" * 40)
    
    train_mae = mean_absolute_error(y_train, y_pred_train)
    test_mae = mean_absolute_error(y_test, y_pred_test)
    
    train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
    test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
    
    train_r2 = r2_score(y_train, y_pred_train)
    test_r2 = r2_score(y_test, y_pred_test)
    
    print(f"Train MAE: {train_mae:.1f} kWh/mois")
    print(f"Test MAE:  {test_mae:.1f} kWh/mois")
    print(f"Train RMSE: {train_rmse:.1f} kWh")
    print(f"Test RMSE:  {test_rmse:.1f} kWh")
    print(f"Train R²: {train_r2:.2f}")
    print(f"Test R²:  {test_r2:.2f}")
    
    # Importance des features
    print("\n📊 IMPORTANCE DES FEATURES:")
    print("-" * 40)
    
    importance = pd.DataFrame({
        'feature': features,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    for i, row in importance.iterrows():
        barre = '█' * int(row['importance'] * 50)
        print(f"   {row['feature']:25} {barre} {row['importance']:.3f}")
    
    # Visualisation de l'importance
    plt.figure(figsize=(10, 8))
    plt.barh(importance['feature'], importance['importance'])
    plt.xlabel('Importance')
    plt.title('Importance des features')
    plt.tight_layout()
    plt.savefig('./data/enriched/feature_importance.png')
    print("\n✅ Graphique sauvegardé: ./data/enriched/feature_importance.png")
    
    # Afficher les prédictions vs réalité pour les données test
    print("\n📊 PRÉDICTIONS VS RÉALITÉ (données test):")
    print("-" * 40)
    
    results = pd.DataFrame({
        'Réel': y_test.values,
        'Prédit': y_pred_test,
        'Erreur': np.abs(y_test.values - y_pred_test)
    })
    print(results.to_string())
    
    # Analyse par groupe (projet terrain)
    print("\n📊 ANALYSE PAR GROUPE:")
    print("-" * 40)
    
    df_test = X_test.copy()
    df_test['reel'] = y_test
    df_test['pred'] = y_pred_test
    
    # Vérifier si projet_terrain_code est dans les features
    if 'projet_terrain_code' in df_test.columns:
        for code in [0, 1]:
            mask = df_test['projet_terrain_code'] == code
            if mask.sum() > 0:
                mae_groupe = mean_absolute_error(
                    df_test.loc[mask, 'reel'],
                    df_test.loc[mask, 'pred']
                )
                label = "Avec projet" if code == 1 else "Sans projet"
                print(f"   {label}: MAE = {mae_groupe:.1f} kWh/mois ({mask.sum()} échantillons)")
    
    # Sauvegarder le modèle
    import joblib
    model_path = './models/modele_consommation.pkl'
    joblib.dump(model, model_path)
    print(f"\n✅ Modèle sauvegardé: {model_path}")
    
    # Sauvegarder aussi les features utilisées
    with open('./models/features.txt', 'w') as f:
        for feat in features:
            f.write(f"{feat}\n")
    
    return model, importance

if __name__ == "__main__":
    model, importance = main()