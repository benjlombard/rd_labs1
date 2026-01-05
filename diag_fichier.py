"""
Script de diagnostic pour vérifier la détection des fichiers
"""

import sys
from pathlib import Path
import yaml

# Ajouter le backend au path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from data_manager import DataManager

def diagnose():
    print("=" * 80)
    print("DIAGNOSTIC DE DÉTECTION DES FICHIERS")
    print("=" * 80)
    
    # Initialiser le DataManager
    dm = DataManager()
    
    # Vérifier le dossier data/input
    input_folder = Path("data/input")
    print(f"\n1. Vérification du dossier: {input_folder.absolute()}")
    print(f"   Existe: {input_folder.exists()}")
    
    if input_folder.exists():
        all_files = list(input_folder.glob("*.xlsx"))
        print(f"   Fichiers .xlsx trouvés: {len(all_files)}")
        for f in all_files:
            print(f"     - {f.name}")
    
    # Charger le config.yaml
    print(f"\n2. Configuration des listes:")
    for list_config in dm.config['source_files']['lists']:
        name = list_config['name']
        enabled = list_config.get('enabled', True)
        pattern = list_config.get('file_pattern', list_config.get('file_prefix', list_config.get('file', 'N/A')))
        
        print(f"\n   Liste: {name}")
        print(f"   - Enabled: {enabled}")
        print(f"   - Pattern: {pattern}")
        
        if enabled:
            # Essayer de trouver le fichier
            try:
                file_path = dm._find_file_by_pattern(list_config)
                print(f"   - ✅ Fichier trouvé: {file_path.name}")
            except FileNotFoundError as e:
                print(f"   - ❌ Erreur: {e}")
            except Exception as e:
                print(f"   - ❌ Erreur inattendue: {e}")
        else:
            print(f"   - ⏸️ Liste désactivée, pas de recherche")
    
    # Tester load_all_lists
    print(f"\n3. Test de load_all_lists():")
    try:
        all_lists = dm.load_all_lists()
        print(f"   ✅ Chargement réussi: {len(all_lists)} listes")
        for name, df in all_lists.items():
            print(f"     - {name}: {len(df)} enregistrements")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    # Tester get_detected_files_info
    print(f"\n4. Test de get_detected_files_info():")
    try:
        files_info = dm.get_detected_files_info()
        print(f"   ✅ Récupération réussie: {len(files_info)} entrées")
        for info in files_info:
            print(f"     - {info['list_name']}: {info['status']}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("FIN DU DIAGNOSTIC")
    print("=" * 80)

if __name__ == "__main__":
    diagnose()