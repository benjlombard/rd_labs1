"""
Gestionnaire des préférences utilisateur
Gère la sauvegarde et le chargement des préférences (colonnes, filtres, etc.)
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from backend.logger import get_logger


class PreferencesManager:
    def __init__(self, preferences_file: str = "data/user_preferences.json"):
        self.logger = get_logger()
        self.preferences_file = Path(preferences_file)
        self.preferences = self._load_preferences()
        
        # Profils de colonnes prédéfinis
        self.COLUMN_PROFILES = {
            'essentials': {
                'name': '🎯 Essentielles',
                'description': 'Colonnes de base pour identification',
                'columns': ['cas_id', 'cas_name', 'source_list', 'ec_number', 'description']
            },
            'regulatory': {
                'name': '⚖️ Réglementaire',
                'description': 'Focus sur les aspects réglementaires',
                'columns': ['cas_id', 'cas_name', 'source_list', 'regulatory_outcome', 
                           'regulatory_outcome_date', 'reason_for_inclusion', 'status']
            },
            'dates': {
                'name': '📅 Dates',
                'description': 'Toutes les dates importantes',
                'columns': ['cas_id', 'cas_name', 'source_list', 'created_at', 'updated_at',
                           'date_of_inclusion', 'sunset_date', 'expiry_date']
            },
            'complete': {
                'name': '📋 Toutes',
                'description': 'Afficher toutes les colonnes',
                'columns': []  # Sera rempli dynamiquement
            }
        }
    
    def _load_preferences(self) -> dict:
        """Charge les préférences depuis le fichier JSON"""
        if self.preferences_file.exists():
            try:
                with open(self.preferences_file, 'r', encoding='utf-8') as f:
                    prefs = json.load(f)
                self.logger.debug("Préférences chargées depuis le fichier")
                return prefs
            except Exception as e:
                self.logger.warning(f"Erreur lors du chargement des préférences: {e}")
                return self._get_default_preferences()
        else:
            self.logger.debug("Aucun fichier de préférences trouvé, utilisation des valeurs par défaut")
            return self._get_default_preferences()
    
    def _get_default_preferences(self) -> dict:
        """Retourne les préférences par défaut"""
        return {
            'column_selection': {
                'profile': 'essentials',
                'custom_columns': None
            },
            'filters': {},
            'display_options': {
                'rows_per_page': 50,
                'show_index': False
            }
        }
    
    def save_preferences(self):
        """Sauvegarde les préférences dans le fichier JSON"""
        try:
            self.preferences_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.preferences_file, 'w', encoding='utf-8') as f:
                json.dump(self.preferences, f, indent=2, ensure_ascii=False)
            self.logger.info("Préférences sauvegardées avec succès")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde des préférences: {e}")
            return False
    
    def get_column_selection(self) -> Dict:
        """Récupère la sélection de colonnes actuelle"""
        return self.preferences.get('column_selection', {
            'profile': 'essentials',
            'custom_columns': None
        })
    
    def set_column_selection(self, profile: str = None, custom_columns: List[str] = None):
        """
        Définit la sélection de colonnes
        
        Args:
            profile: Nom du profil ('essentials', 'regulatory', etc.)
            custom_columns: Liste personnalisée de colonnes (si profile='custom')
        """
        self.preferences['column_selection'] = {
            'profile': profile or 'essentials',
            'custom_columns': custom_columns
        }
    
    def get_columns_for_profile(self, profile: str, all_columns: List[str]) -> List[str]:
        """
        Retourne les colonnes pour un profil donné
        
        Args:
            profile: Nom du profil
            all_columns: Liste de toutes les colonnes disponibles
            
        Returns:
            Liste des colonnes à afficher
        """
        if profile == 'complete':
            return all_columns
        
        if profile == 'custom':
            custom = self.preferences.get('column_selection', {}).get('custom_columns')
            if custom:
                # Filtrer pour ne garder que les colonnes qui existent encore
                return [col for col in custom if col in all_columns]
            else:
                # Fallback sur essentials si pas de custom défini
                return self.get_columns_for_profile('essentials', all_columns)
        
        if profile in self.COLUMN_PROFILES:
            profile_cols = self.COLUMN_PROFILES[profile]['columns']
            # Filtrer pour ne garder que les colonnes qui existent
            return [col for col in profile_cols if col in all_columns]
        
        # Fallback sur essentials
        return self.get_columns_for_profile('essentials', all_columns)
    
    def get_available_profiles(self) -> Dict:
        """Retourne tous les profils disponibles"""
        return self.COLUMN_PROFILES
    
    def reset_to_default(self):
        """Réinitialise les préférences aux valeurs par défaut"""
        self.preferences = self._get_default_preferences()
        self.save_preferences()
        self.logger.info("Préférences réinitialisées aux valeurs par défaut")
    
    def get_display_options(self) -> Dict:
        """Récupère les options d'affichage"""
        return self.preferences.get('display_options', {
            'rows_per_page': 50,
            'show_index': False
        })
    
    def set_display_options(self, **kwargs):
        """
        Définit les options d'affichage
        
        Args:
            **kwargs: Options à définir (rows_per_page, show_index, etc.)
        """
        if 'display_options' not in self.preferences:
            self.preferences['display_options'] = {}
        
        self.preferences['display_options'].update(kwargs)