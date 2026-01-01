import pandas as pd
from pathlib import Path
import yaml
from datetime import datetime
import shutil
from backend.logger import get_logger


class HistoryManager:
    def __init__(self, config_path: str = "config.yaml"):
        self.logger = get_logger()
        self.logger.info("Initialisation du HistoryManager")
        self.config = self._load_config(config_path)
        self.history_file = Path(self.config['output_files']['change_history'])
        self.summary_history_file = Path(self.config['output_files']['summary_history'])
        self.archive_folder = Path(self.config['general']['archive_folder'])
        self.archive_old_files = self.config['general']['archive_old_files']
        self.logger.debug(f"Fichier historique: {self.history_file}")

    def _load_config(self, config_path: str) -> dict:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def load_history(self) -> pd.DataFrame:
        if self.history_file.exists():
            return pd.read_excel(self.history_file)
        return pd.DataFrame()

    def save_changes(self, changes_df: pd.DataFrame) -> None:
        if changes_df.empty:
            return

        existing_history = self.load_history()

        if existing_history.empty:
            updated_history = changes_df
        else:
            updated_history = pd.concat([existing_history, changes_df], ignore_index=True)

        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        updated_history.to_excel(self.history_file, index=False)

    def archive_files(self, list_name: str, file_path: Path) -> None:
        if not self.archive_old_files:
            return

        if not file_path.exists():
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"{list_name}_{timestamp}.xlsx"
        archive_path = self.archive_folder / archive_name

        self.archive_folder.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, archive_path)

    def get_recent_changes(self, limit: int = 100) -> pd.DataFrame:
        history = self.load_history()
        if history.empty:
            return history

        if 'timestamp' in history.columns:
            history = history.sort_values('timestamp', ascending=False)

        return history.head(limit)

    def get_changes_by_type(self, change_type: str) -> pd.DataFrame:
        history = self.load_history()
        if history.empty:
            return history

        return history[history['change_type'] == change_type]

    def get_changes_by_list(self, list_name: str) -> pd.DataFrame:
        history = self.load_history()
        if history.empty:
            return history

        return history[history['source_list'] == list_name]

    def get_changes_by_cas(self, cas_id: str) -> pd.DataFrame:
        history = self.load_history()
        if history.empty:
            return history

        return history[history['cas_id'] == cas_id]

    def clear_history(self) -> None:
        if self.history_file.exists():
            self.history_file.unlink()

    def save_summary(self, summary_df: pd.DataFrame) -> None:
        """
        Sauvegarde le résumé d'un chargement avec un timestamp.
        """
        if summary_df.empty:
            return

        summary_with_ts = summary_df.copy()
        summary_with_ts['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        existing_summary = self.load_summary_history()

        if existing_summary.empty:
            updated_summary = summary_with_ts
        else:
            updated_summary = pd.concat([existing_summary, summary_with_ts], ignore_index=True)

        self.summary_history_file.parent.mkdir(parents=True, exist_ok=True)
        updated_summary.to_excel(self.summary_history_file, index=False)

    def load_summary_history(self) -> pd.DataFrame:
        """
        Charge l'historique complet des résumés de chargement.
        """
        if self.summary_history_file.exists():
            df = pd.read_excel(self.summary_history_file)
            if 'timestamp' in df.columns:
                return df.sort_values('timestamp', ascending=False)
            return df
        return pd.DataFrame()
