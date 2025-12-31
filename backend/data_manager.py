import pandas as pd
import yaml
from pathlib import Path
from typing import Dict, List, Tuple
import os


class DataManager:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.data_folder = Path(self.config['general']['data_folder'])

    def _load_config(self, config_path: str) -> dict:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def load_cas_source(self) -> pd.DataFrame:
        file_path = self.data_folder / "input" / self.config['source_files']['cas_source']
        df = pd.read_excel(file_path)
        return df

    def load_list_file(self, list_name: str) -> pd.DataFrame:
        list_config = next((l for l in self.config['source_files']['lists'] if l['name'] == list_name), None)
        if not list_config:
            raise ValueError(f"Liste {list_name} non trouvée dans la configuration")

        file_path = self.data_folder / "input" / list_config['file']
        df = pd.read_excel(file_path)
        df['source_list'] = list_name
        return df

    def load_all_lists(self) -> Dict[str, pd.DataFrame]:
        all_lists = {}
        for list_config in self.config['source_files']['lists']:
            list_name = list_config['name']
            all_lists[list_name] = self.load_list_file(list_name)
        return all_lists

    def aggregate_all_data(self) -> pd.DataFrame:
        all_lists = self.load_all_lists()

        aggregated_frames = []
        for list_name, df in all_lists.items():
            df_copy = df.copy()
            df_copy['source_list'] = list_name
            aggregated_frames.append(df_copy)

        aggregated_df = pd.concat(aggregated_frames, ignore_index=True)
        return aggregated_df

    def save_aggregated_data(self, df: pd.DataFrame) -> None:
        output_path = Path(self.config['output_files']['aggregated_data'])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_excel(output_path, index=False)

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
