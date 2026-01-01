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

    def _clean_cas_id_column(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Nettoie et standardise la colonne 'cas_id'.
        - Convertit en string
        - Supprime les espaces
        - Standardise les valeurs nulles
        - Supprime les '.0' finaux
        """
        if 'cas_id' in df.columns:
            self.logger.debug("Nettoyage de la colonne cas_id")
            # Convertir en string, en gérant les erreurs et les valeurs nulles
            df['cas_id'] = df['cas_id'].astype(str).str.strip()
            # Remplacer les variantes de "null" par une valeur standard
            df['cas_id'] = df['cas_id'].replace(['-', 'nan', '', 'None', None], pd.NA)
            # Supprimer les '.0' qui peuvent apparaître si des nombres sont lus comme des floats
            df['cas_id'] = df['cas_id'].str.replace(r'\.0$', '', regex=True)
        return df

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

        # Nettoyer la colonne cas_id pour assurer la cohérence
        df = self._clean_cas_id_column(df)

        # Créer un identifiant unique : ajouter un index de ligne pour les cas_id manquants/dupliqués
        if 'cas_id' in df.columns:
            # Compter les doublons et valeurs manquantes AVANT traitement
            total_rows = len(df)
            missing_cas = df['cas_id'].isna().sum() + (df['cas_id'] == '-').sum()
            duplicated_cas = df['cas_id'].duplicated().sum()

            self.logger.debug(f"Liste {list_name} - Lignes: {total_rows}, CAS manquants/'-': {missing_cas}, Doublons CAS: {duplicated_cas}")

            # Créer un identifiant unique combinant cas_id + index de ligne pour les cas problématiques
            df['_row_id'] = range(len(df))
            df['unique_id'] = df.apply(
                lambda row: f"{row['cas_id']}_{row['_row_id']}" if pd.isna(row['cas_id']) or row['cas_id'] == '-' or row['cas_id'] == ''
                else str(row['cas_id']),
                axis=1
            )

            # Déduplicater par unique_id (pour éliminer les vrais doublons)
            before_dedup = len(df)
            df = df.drop_duplicates(subset=['unique_id'], keep='last').reset_index(drop=True)
            after_dedup = len(df)

            if before_dedup != after_dedup:
                self.logger.info(f"Déduplication {list_name}: {before_dedup} -> {after_dedup} ({before_dedup - after_dedup} doublons supprimés)")

            # Supprimer les colonnes temporaires
            df = df.drop(columns=['_row_id', 'unique_id'])

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

        aggregated_df = pd.concat(aggregated_frames, ignore_index=True).reset_index(drop=True)

        # Créer un identifiant unique permanent pour chaque substance
        # Pour les cas_id manquants ou "-", on utilise l'index global
        aggregated_df['_global_id'] = range(len(aggregated_df))
        aggregated_df['unique_substance_id'] = aggregated_df.apply(
            lambda row: f"{row['cas_id']}|{row['source_list']}"
                if pd.notna(row['cas_id']) and row['cas_id'] != '-' and row['cas_id'] != ''
                else f"NOCASE_{row['_global_id']}|{row['source_list']}",
            axis=1
        )

        # Ajouter ou mettre à jour les timestamps
        aggregated_df = self._update_timestamps(aggregated_df)

        # Supprimer la colonne temporaire _global_id
        aggregated_df = aggregated_df.drop(columns=['_global_id'])

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

        # Utiliser unique_substance_id qui a été créé dans aggregate_all_data()
        self.logger.info(f"Nouveau DataFrame avant déduplication: {len(new_df)} lignes")

        if 'unique_substance_id' not in new_df.columns:
            self.logger.error("ERREUR: unique_substance_id manquant dans new_df!")
            return new_df

        # Vérifier les doublons AVANT déduplication
        duplicates_before = new_df['unique_substance_id'].duplicated().sum()
        self.logger.info(f"Doublons détectés dans new_df AVANT déduplication: {duplicates_before}")

        # Éliminer les doublons (garder la dernière occurrence)
        new_df = new_df.drop_duplicates(subset=['unique_substance_id'], keep='last').reset_index(drop=True)
        self.logger.info(f"Nouveau DataFrame après déduplication: {len(new_df)} lignes")

        if 'created_at' in old_df.columns and 'updated_at' in old_df.columns:
            self.logger.info("Ancien DataFrame contient des timestamps")

            # Vérifier si old_df a unique_substance_id
            if 'unique_substance_id' not in old_df.columns:
                self.logger.warning("unique_substance_id manquant dans old_df, reconstruction...")
                # Reconstruire l'identifiant pour compatibilité avec anciens fichiers
                old_df['_temp_id'] = range(len(old_df))
                old_df['unique_substance_id'] = old_df.apply(
                    lambda row: f"{row['cas_id']}|{row['source_list']}"
                        if pd.notna(row['cas_id']) and row['cas_id'] != '-' and row['cas_id'] != ''
                        else f"NOCASE_{row['_temp_id']}|{row['source_list']}",
                    axis=1
                )
                old_df = old_df.drop(columns=['_temp_id'])

            # Vérifier les doublons AVANT déduplication
            duplicates_before_old = old_df['unique_substance_id'].duplicated().sum()
            self.logger.info(f"Doublons détectés dans old_df AVANT déduplication: {duplicates_before_old}")

            # Éliminer les doublons
            old_df_unique = old_df.drop_duplicates(subset=['unique_substance_id'], keep='last').reset_index(drop=True)
            self.logger.info(f"Ancien DataFrame après déduplication: {len(old_df_unique)} lignes")

            # Vérifier s'il reste des doublons
            if old_df_unique['unique_substance_id'].duplicated().any():
                duplicates_remaining = old_df_unique['unique_substance_id'].duplicated().sum()
                self.logger.warning(f"Doublons ENCORE présents après drop_duplicates: {duplicates_remaining}")
                # Afficher quelques exemples
                duplicated_ids = old_df_unique[old_df_unique['unique_substance_id'].duplicated(keep=False)]['unique_substance_id'].unique()[:5]
                self.logger.warning(f"Exemples de IDs dupliqués: {list(duplicated_ids)}")
                # Forcer une deuxième déduplication
                old_df_unique = old_df_unique.drop_duplicates(subset=['unique_substance_id'], keep='last').reset_index(drop=True)
                self.logger.info(f"Après 2ème déduplication: {len(old_df_unique)} lignes")

            # Créer un dictionnaire des timestamps existants
            self.logger.info("Création du dictionnaire des timestamps")
            try:
                old_timestamps = old_df_unique.set_index('unique_substance_id')[['created_at', 'updated_at']].to_dict('index')
                self.logger.info(f"Dictionnaire créé avec succès: {len(old_timestamps)} entrées")
            except ValueError as e:
                self.logger.error(f"ERREUR lors de la création du dictionnaire: {str(e)}")
                # Vérifier à nouveau les doublons
                final_duplicates = old_df_unique['unique_substance_id'].duplicated().sum()
                self.logger.error(f"Doublons FINAUX dans old_df_unique: {final_duplicates}")
                if final_duplicates > 0:
                    duplicated_rows = old_df_unique[old_df_unique['unique_substance_id'].duplicated(keep=False)]
                    self.logger.error(f"Lignes dupliquées:\n{duplicated_rows[['cas_id', 'source_list', 'unique_substance_id']].to_string()}")
                raise

            # Pour chaque ligne du nouveau DataFrame
            created_at_list = []
            updated_at_list = []

            for idx, row in new_df.iterrows():
                uid = row['unique_substance_id']
                if uid in old_timestamps:
                    # Substance existante: conserver created_at, vérifier si mise à jour nécessaire
                    created_at_list.append(old_timestamps[uid]['created_at'])

                    # Comparer les données (sans les colonnes de métadonnées)
                    old_row = old_df_unique[old_df_unique['unique_substance_id'] == uid].iloc[0]

                    # Colonnes à comparer (exclure unique_substance_id, created_at, updated_at, source_list)
                    cols_to_compare = [col for col in new_df.columns
                                      if col not in ['unique_substance_id', 'created_at', 'updated_at', 'source_list']]

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
                        updated_at_list.append(old_timestamps[uid]['updated_at'])
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

            # Nettoyer la colonne cas_id pour assurer la cohérence avant toute manipulation
            df = self._clean_cas_id_column(df)

            # Éliminer les doublons éventuels
            if not df.empty and 'cas_id' in df.columns and 'source_list' in df.columns:
                # Vérifier si unique_substance_id existe déjà
                if 'unique_substance_id' not in df.columns:
                    self.logger.warning("unique_substance_id manquant, reconstruction pour compatibilité...")
                    # Reconstruire pour compatibilité avec anciens fichiers
                    df['_temp_id'] = range(len(df))
                    df['unique_substance_id'] = df.apply(
                        lambda row: f"{row['cas_id']}|{row['source_list']}"
                            if pd.notna(row['cas_id']) and row['cas_id'] != '-' and row['cas_id'] != ''
                            else f"NOCASE_{row['_temp_id']}|{row['source_list']}",
                        axis=1
                    )
                    df = df.drop(columns=['_temp_id'])

                # Compter les doublons AVANT déduplication
                duplicates_before = df['unique_substance_id'].duplicated().sum()

                if duplicates_before > 0:
                    self.logger.warning(f"ATTENTION: {duplicates_before} doublons détectés dans le fichier agrégé !")
                    # Afficher quelques exemples
                    duplicated_ids = df[df['unique_substance_id'].duplicated(keep=False)]['unique_substance_id'].value_counts().head(5)
                    self.logger.warning(f"Exemples d'IDs dupliqués:\n{duplicated_ids}")

                # Déduplication
                df = df.drop_duplicates(subset=['unique_substance_id'], keep='last').reset_index(drop=True)
                duplicates_after = df['unique_substance_id'].duplicated().sum()

                self.logger.debug(f"Après déduplication: {len(df)} lignes, {duplicates_after} doublons restants")

                if duplicates_after > 0:
                    self.logger.error(f"ERREUR: {duplicates_after} doublons PERSISTENT après drop_duplicates!")
                    # Forcer une seconde déduplication
                    df = df.drop_duplicates(subset=['unique_substance_id'], keep='last').reset_index(drop=True)
                    self.logger.debug(f"Après 2ème déduplication: {len(df)} lignes")

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
