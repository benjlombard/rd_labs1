import pandas as pd
import yaml
from pathlib import Path
from typing import Dict, List, Tuple
import os
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

    def load_cas_source(self) -> pd.DataFrame:
        file_path = self.data_folder / "input" / self.config['source_files']['cas_source']
        df = pd.read_excel(file_path)
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
        df['source_list'] = list_name
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
        self.logger.info(f"Agregation terminee: {len(aggregated_df)} enregistrements au total")
        return aggregated_df

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
            return pd.read_excel(output_path)
        return pd.DataFrame()

    def get_list_description(self, list_name: str) -> str:
        list_config = next((l for l in self.config['source_files']['lists'] if l['name'] == list_name), None)
        if list_config:
            return list_config.get('description', list_name)
        return list_name
