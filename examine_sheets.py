"""
Script pour examiner les feuilles du fichier eu_positive_list
"""
import pandas as pd
import yaml
from pathlib import Path

# Charger la config
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# Trouver le fichier eu_positive_list
eu_list_config = next((l for l in config['source_files']['lists'] if l['name'] == 'eu_positive_list'), None)
file_path = Path(config['general']['data_folder']) / "input" / eu_list_config['file']

print(f"📁 Fichier: {file_path}")
print(f"📂 Existe: {file_path.exists()}\n")

if not file_path.exists():
    print(f"❌ Le fichier n'existe pas!")
    exit(1)

# Lire toutes les feuilles
print("📊 Examen de toutes les feuilles du fichier Excel...\n")
excel_file = pd.ExcelFile(file_path)

print(f"📋 Nombre de feuilles: {len(excel_file.sheet_names)}\n")
print("=" * 80)

for i, sheet_name in enumerate(excel_file.sheet_names, 1):
    print(f"\n🔷 Feuille {i}: '{sheet_name}'")
    print("-" * 80)
    
    # Lire la feuille
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    
    print(f"   📏 Dimensions: {len(df)} lignes × {len(df.columns)} colonnes")
    print(f"   📋 Colonnes (10 premières):")
    for j, col in enumerate(df.columns[:10], 1):
        print(f"      {j}. {col}")
    
    if len(df.columns) > 10:
        print(f"      ... et {len(df.columns) - 10} autres colonnes")
    
    # Vérifier si cette feuille contient les colonnes attendues
    has_cas = 'CAS number' in df.columns or 'CAS Number' in df.columns
    has_substance = 'Substance name' in df.columns or 'Substance Name' in df.columns
    
    if has_cas and has_substance:
        print(f"   ✅ Cette feuille contient 'CAS number' et 'Substance name'")
    elif has_cas:
        print(f"   ⚠️ Cette feuille contient 'CAS number' mais pas 'Substance name'")
    elif has_substance:
        print(f"   ⚠️ Cette feuille contient 'Substance name' mais pas 'CAS number'")
    else:
        print(f"   ❌ Cette feuille ne contient ni 'CAS number' ni 'Substance name'")
    
    # Afficher les 3 premières lignes
    print(f"\n   📄 Aperçu des 3 premières lignes:")
    if not df.empty:
        # Sélectionner les premières colonnes pour l'aperçu
        cols_to_show = df.columns[:5]
        print(df[cols_to_show].head(3).to_string(index=False))

print("\n" + "=" * 80)
print("\n✅ Analyse terminée")
print("\n💡 Recommandation:")
print("   Si la bonne feuille n'est pas la première, modifiez le code pour spécifier")
print("   le nom ou l'index de la bonne feuille lors du chargement.")