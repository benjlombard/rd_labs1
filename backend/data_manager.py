import pandas as pd
import yaml
from pathlib import Path
from typing import Dict, List, Tuple
import os
import shutil
from datetime import datetime
from backend.logger import get_logger


class DataManager:
    def __init__(self, config_path: str = "config.yaml"):
        self.logger = get_logger()
        self.logger.info("Initialisation du DataManager")
        self.config = self._load_config(config_path)
        self.data_folder = Path(self.config['general']['data_folder'])
        self.logger.debug(f"Dossier de donnees: {self.data_folder}")

    def _load_config(self, config_path: str) -> dict:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _rename_common_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Renomme les colonnes communes selon le mapping défini dans config.yaml

        Args:
            df: DataFrame avec les noms de colonnes originaux des fichiers Excel

        Returns:
            DataFrame avec les noms de colonnes normalisés (cas_id, cas_name, etc.)
        """
        if 'common' not in self.config['columns']:
            self.logger.warning("Aucune colonne commune definie dans config.yaml")
            return df

        # Créer un dictionnaire de renommage inversé
        # config: cas_id: "CAS number" → rename_map: "CAS number": "cas_id"
        rename_map = {}
        for normalized_name, excel_name in self.config['columns']['common'].items():
            if excel_name in df.columns:
                rename_map[excel_name] = normalized_name
                self.logger.debug(f"Renommage colonne: '{excel_name}' -> '{normalized_name}'")
            else:
                self.logger.warning(f"Colonne '{excel_name}' non trouvee dans le fichier (attendue pour '{normalized_name}')")

        df_renamed = df.rename(columns=rename_map)
        return df_renamed

    def _rename_list_specific_columns(self, df: pd.DataFrame, list_name: str) -> pd.DataFrame:
        """
        Renomme les colonnes spécifiques à une liste selon le mapping défini dans config.yaml

        Args:
            df: DataFrame avec les noms de colonnes partiellement normalisés
            list_name: Nom de la liste (ex: "authorisation_list")

        Returns:
            DataFrame avec toutes les colonnes normalisées
        """
        if list_name not in self.config['columns']:
            self.logger.debug(f"Aucune colonne specifique definie pour la liste {list_name}")
            return df

        # Créer un dictionnaire de renommage inversé pour cette liste
        rename_map = {}
        for normalized_name, excel_name in self.config['columns'][list_name].items():
            if excel_name in df.columns:
                rename_map[excel_name] = normalized_name
                self.logger.debug(f"Renommage colonne specifique {list_name}: '{excel_name}' -> '{normalized_name}'")

        df_renamed = df.rename(columns=rename_map)
        return df_renamed

    def load_cas_source(self) -> pd.DataFrame:
        file_path = self.data_folder / "input" / self.config['source_files']['cas_source']
        df = pd.read_excel(file_path)

        # Renommer les colonnes communes selon la configuration
        df = self._rename_common_columns(df)

        return df

    def load_list_file(self, list_name: str) -> pd.DataFrame:
        self.logger.debug(f"Chargement de la liste: {list_name}")
        list_config = next((l for l in self.config['source_files']['lists'] if l['name'] == list_name), None)
        if not list_config:
            self.logger.error(f"Liste {list_name} non trouvee dans la configuration")
            raise ValueError(f"Liste {list_name} non trouvée dans la configuration")

        file_path = self.data_folder / "input" / list_config['file']
        self.logger.debug(f"Lecture du fichier: {file_path}")
        df = pd.read_excel(file_path)

        # Renommer les colonnes communes selon la configuration
        df = self._rename_common_columns(df)

        # Renommer les colonnes spécifiques à cette liste si configurées
        if list_name in self.config['columns']:
            df = self._rename_list_specific_columns(df, list_name)

        # Déduplicater par cas_id (garder la dernière occurrence)
        if 'cas_id' in df.columns:
            df = df.drop_duplicates(subset=['cas_id'], keep='last').reset_index(drop=True)
            self.logger.debug(f"Deduplication effectuee pour {list_name}")

        # Ne pas ajouter source_list ici, ce sera fait dans aggregate_all_data()
        self.logger.info(f"Liste {list_name} chargee avec succes: {len(df)} enregistrements")
        return df

    def load_all_lists(self) -> Dict[str, pd.DataFrame]:
        all_lists = {}
        for list_config in self.config['source_files']['lists']:
            list_name = list_config['name']
            all_lists[list_name] = self.load_list_file(list_name)
        return all_lists

    def aggregate_all_data(self) -> pd.DataFrame:
        self.logger.info("Debut de l'agregation de toutes les listes")
        all_lists = self.load_all_lists()

        aggregated_frames = []
        for list_name, df in all_lists.items():
            df_copy = df.copy()
            df_copy['source_list'] = list_name
            aggregated_frames.append(df_copy)
            self.logger.debug(f"Liste {list_name} ajoutee: {len(df_copy)} lignes")

        aggregated_df = pd.concat(aggregated_frames, ignore_index=True)

        # Ajouter ou mettre à jour les timestamps
        aggregated_df = self._update_timestamps(aggregated_df)

        self.logger.info(f"Agregation terminee: {len(aggregated_df)} enregistrements au total")
        return aggregated_df

    def _update_timestamps(self, new_df: pd.DataFrame) -> pd.DataFrame:
        """
        Ajoute ou met à jour les colonnes created_at et updated_at.
        - created_at: date de première apparition (conservée si substance existante)
        - updated_at: date de dernière modification (mise à jour si données changées)
        """
        self.logger.info("Début de la mise à jour des timestamps")
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Charger l'ancien fichier agrégé s'il existe
        old_df = self.load_aggregated_data()
        self.logger.info(f"Ancien DataFrame chargé: {len(old_df)} lignes")

        if old_df.empty:
            # Première agrégation: toutes les substances sont nouvelles
            self.logger.info("Première agrégation: création des timestamps pour toutes les lignes")
            new_df['created_at'] = current_time
            new_df['updated_at'] = current_time
            return new_df

        # Créer une clé unique pour identifier les substances (cas_id + source_list)
        self.logger.info(f"Nouveau DataFrame avant déduplication: {len(new_df)} lignes")
        new_df['_key'] = new_df['cas_id'].astype(str) + '|' + new_df['source_list'].astype(str)

        # Vérifier les doublons AVANT déduplication
        duplicates_before = new_df['_key'].duplicated().sum()
        self.logger.info(f"Doublons détectés dans new_df AVANT déduplication: {duplicates_before}")

        # Éliminer les doublons de clé dans le nouveau DataFrame (garder la dernière occurrence)
        new_df = new_df.drop_duplicates(subset=['_key'], keep='last').reset_index(drop=True)
        self.logger.info(f"Nouveau DataFrame après déduplication: {len(new_df)} lignes")

        if 'created_at' in old_df.columns and 'updated_at' in old_df.columns:
            self.logger.info("Ancien DataFrame contient des timestamps")
            old_df['_key'] = old_df['cas_id'].astype(str) + '|' + old_df['source_list'].astype(str)

            # Vérifier les doublons AVANT déduplication
            duplicates_before_old = old_df['_key'].duplicated().sum()
            self.logger.info(f"Doublons détectés dans old_df AVANT déduplication: {duplicates_before_old}")

            # Éliminer les doublons de clé (garder la dernière occurrence)
            old_df_unique = old_df.drop_duplicates(subset=['_key'], keep='last').reset_index(drop=True)
            self.logger.info(f"Ancien DataFrame après déduplication: {len(old_df_unique)} lignes")

            # Vérifier s'il reste des doublons
            if old_df_unique['_key'].duplicated().any():
                duplicates_remaining = old_df_unique['_key'].duplicated().sum()
                self.logger.warning(f"Doublons ENCORE présents dans _key après drop_duplicates: {duplicates_remaining}")
                # Afficher quelques exemples de doublons
                duplicated_keys = old_df_unique[old_df_unique['_key'].duplicated(keep=False)]['_key'].unique()[:5]
                self.logger.warning(f"Exemples de clés dupliquées: {list(duplicated_keys)}")
                # Forcer une deuxième déduplication
                old_df_unique = old_df_unique.drop_duplicates(subset=['_key'], keep='last').reset_index(drop=True)
                self.logger.info(f"Après 2ème déduplication: {len(old_df_unique)} lignes")

            # Créer un dictionnaire des timestamps existants
            self.logger.info("Création du dictionnaire des timestamps")
            try:
                old_timestamps = old_df_unique.set_index('_key')[['created_at', 'updated_at']].to_dict('index')
                self.logger.info(f"Dictionnaire créé avec succès: {len(old_timestamps)} entrées")
            except ValueError as e:
                self.logger.error(f"ERREUR lors de la création du dictionnaire: {str(e)}")
                # Vérifier à nouveau les doublons
                final_duplicates = old_df_unique['_key'].duplicated().sum()
                self.logger.error(f"Doublons FINAUX dans old_df_unique: {final_duplicates}")
                if final_duplicates > 0:
                    duplicated_rows = old_df_unique[old_df_unique['_key'].duplicated(keep=False)]
                    self.logger.error(f"Lignes dupliquées:\n{duplicated_rows[['cas_id', 'source_list', '_key']].to_string()}")
                raise

            # Pour chaque ligne du nouveau DataFrame
            created_at_list = []
            updated_at_list = []

            for idx, row in new_df.iterrows():
                key = row['_key']
                if key in old_timestamps:
                    # Substance existante: conserver created_at, vérifier si mise à jour nécessaire
                    created_at_list.append(old_timestamps[key]['created_at'])

                    # Comparer les données (sans les colonnes de métadonnées)
                    old_row = old_df_unique[old_df_unique['_key'] == key].iloc[0]

                    # Colonnes à comparer (exclure _key, created_at, updated_at, source_list)
                    cols_to_compare = [col for col in new_df.columns
                                      if col not in ['_key', 'created_at', 'updated_at', 'source_list']]

                    data_changed = False
                    for col in cols_to_compare:
                        if col in old_row.index:
                            old_val = old_row[col]
                            new_val = row[col]
                            # Gérer les NaN
                            if pd.isna(old_val) and pd.isna(new_val):
                                continue
                            if old_val != new_val:
                                data_changed = True
                                break

                    if data_changed:
                        updated_at_list.append(current_time)
                    else:
                        updated_at_list.append(old_timestamps[key]['updated_at'])
                else:
                    # Nouvelle substance
                    created_at_list.append(current_time)
                    updated_at_list.append(current_time)

            new_df['created_at'] = created_at_list
            new_df['updated_at'] = updated_at_list
        else:
            # L'ancien fichier n'a pas de timestamps: traiter comme première agrégation
            self.logger.debug("Ancien fichier sans timestamps: creation pour toutes les lignes")
            new_df['created_at'] = current_time
            new_df['updated_at'] = current_time

        # Supprimer la colonne temporaire _key
        new_df = new_df.drop(columns=['_key'])

        self.logger.debug(f"Timestamps mis a jour: {len(new_df)} lignes")
        return new_df

    def save_aggregated_data(self, df: pd.DataFrame, force: bool = False) -> bool:
        output_path = Path(self.config['output_files']['aggregated_data'])
        self.logger.debug(f"Tentative de sauvegarde vers: {output_path}")

        if not force and output_path.exists():
            self.logger.debug("Comparaison avec le fichier existant")
            old_df = pd.read_excel(output_path)
            if self._dataframes_are_equal(old_df, df):
                self.logger.info("Donnees identiques, pas de sauvegarde necessaire")
                return False

        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_excel(output_path, index=False)
        self.logger.info(f"Fichier sauvegarde avec succes: {output_path}")
        return True

    def _dataframes_are_equal(self, df1: pd.DataFrame, df2: pd.DataFrame) -> bool:
        if df1.shape != df2.shape:
            return False

        if list(df1.columns) != list(df2.columns):
            return False

        df1_sorted = df1.sort_values(by=list(df1.columns)).reset_index(drop=True)
        df2_sorted = df2.sort_values(by=list(df2.columns)).reset_index(drop=True)

        return df1_sorted.equals(df2_sorted)

    def load_aggregated_data(self) -> pd.DataFrame:
        output_path = Path(self.config['output_files']['aggregated_data'])
        if output_path.exists():
            self.logger.debug(f"Chargement du fichier agrégé: {output_path}")
            df = pd.read_excel(output_path)
            self.logger.debug(f"Fichier chargé: {len(df)} lignes, {len(df.columns)} colonnes")

            # Éliminer les doublons éventuels basés sur cas_id + source_list
            if not df.empty and 'cas_id' in df.columns and 'source_list' in df.columns:
                # Compter les doublons AVANT déduplication
                df['_key'] = df['cas_id'].astype(str) + '|' + df['source_list'].astype(str)
                duplicates_before = df['_key'].duplicated().sum()

                if duplicates_before > 0:
                    self.logger.warning(f"ATTENTION: {duplicates_before} doublons détectés dans le fichier agrégé !")
                    # Afficher quelques exemples
                    duplicated_keys = df[df['_key'].duplicated(keep=False)]['_key'].value_counts().head(5)
                    self.logger.warning(f"Exemples de clés dupliquées:\n{duplicated_keys}")

                # Déduplication
                df = df.drop_duplicates(subset=['_key'], keep='last').reset_index(drop=True)
                duplicates_after = df['_key'].duplicated().sum()

                self.logger.debug(f"Après déduplication: {len(df)} lignes, {duplicates_after} doublons restants")

                if duplicates_after > 0:
                    self.logger.error(f"ERREUR: {duplicates_after} doublons PERSISTENT après drop_duplicates!")
                    # Forcer une seconde déduplication
                    df = df.drop_duplicates(subset=['_key'], keep='last').reset_index(drop=True)
                    self.logger.debug(f"Après 2ème déduplication: {len(df)} lignes")

                df = df.drop(columns=['_key'])

            return df

        self.logger.debug("Aucun fichier agrégé existant")
        return pd.DataFrame()

    def get_list_description(self, list_name: str) -> str:
        list_config = next((l for l in self.config['source_files']['lists'] if l['name'] == list_name), None)
        if list_config:
            return list_config.get('description', list_name)
        return list_name

    def get_file_modification_date(self, list_name: str) -> str:
        """
        Retourne la date de modification d'un fichier Excel source.
        """
        list_config = next((l for l in self.config['source_files']['lists'] if l['name'] == list_name), None)
        if not list_config:
            return "N/A"

        file_path = self.data_folder / "input" / list_config['file']
        if not file_path.exists():
            return "Fichier non trouvé"

        mod_timestamp = os.path.getmtime(file_path)
        mod_date = datetime.fromtimestamp(mod_timestamp)
        return mod_date.strftime('%Y-%m-%d %H:%M:%S')

    def archive_source_files(self) -> int:
        """
        Archive tous les fichiers Excel sources en les déplaçant vers data/archives
        avec un timestamp dans le nom du fichier.
        Retourne le nombre de fichiers archivés.
        """
        self.logger.info("Debut de l'archivage des fichiers sources")
        archive_folder = self.data_folder / "archives"
        archive_folder.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archived_count = 0

        for list_config in self.config['source_files']['lists']:
            list_name = list_config['name']
            list_file = list_config['file']
            file_path = self.data_folder / "input" / list_file

            if file_path.exists():
                # Créer le nom du fichier archivé avec timestamp
                file_stem = file_path.stem  # Nom sans extension
                file_ext = file_path.suffix  # Extension avec le point
                archive_name = f"{file_stem}_{timestamp}{file_ext}"
                archive_path = archive_folder / archive_name

                # Copier le fichier (au lieu de déplacer pour garder l'original)
                shutil.copy2(str(file_path), str(archive_path))
                self.logger.info(f"Fichier archive (copie): {list_file} -> {archive_name}")
                archived_count += 1
            else:
                self.logger.warning(f"Fichier source non trouve: {file_path}")

        self.logger.info(f"Archivage termine: {archived_count} fichiers archives")
        return archived_count
