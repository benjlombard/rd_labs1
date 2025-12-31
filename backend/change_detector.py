import pandas as pd
from typing import Dict, List, Tuple
from datetime import datetime
from backend.logger import get_logger


class ChangeDetector:
    def __init__(self):
        self.logger = get_logger()
        self.change_types = ['insertion', 'deletion', 'modification']
        self.logger.debug("ChangeDetector initialise")

    def detect_changes_for_list(self, old_df: pd.DataFrame, new_df: pd.DataFrame, list_name: str) -> pd.DataFrame:
        changes = []

        if old_df.empty:
            for _, row in new_df.iterrows():
                changes.append(self._create_change_record('insertion', list_name, row, None))
            return pd.DataFrame(changes)

        old_df = old_df.copy()
        new_df = new_df.copy()

        cas_id_col = 'cas_id'
        old_ids = set(old_df[cas_id_col].values)
        new_ids = set(new_df[cas_id_col].values)

        inserted_ids = new_ids - old_ids
        deleted_ids = old_ids - new_ids
        common_ids = old_ids & new_ids

        for cas_id in inserted_ids:
            new_row = new_df[new_df[cas_id_col] == cas_id].iloc[0]
            changes.append(self._create_change_record('insertion', list_name, new_row, None))

        for cas_id in deleted_ids:
            old_row = old_df[old_df[cas_id_col] == cas_id].iloc[0]
            changes.append(self._create_change_record('deletion', list_name, None, old_row))

        for cas_id in common_ids:
            old_row = old_df[old_df[cas_id_col] == cas_id].iloc[0]
            new_row = new_df[new_df[cas_id_col] == cas_id].iloc[0]

            if not old_row.equals(new_row):
                modified_fields = self._get_modified_fields(old_row, new_row)
                if modified_fields:
                    changes.append(self._create_change_record('modification', list_name, new_row, old_row, modified_fields))

        return pd.DataFrame(changes)

    def _create_change_record(self, change_type: str, list_name: str, new_row: pd.Series = None,
                            old_row: pd.Series = None, modified_fields: List[str] = None) -> dict:
        record = {
            'change_type': change_type,
            'source_list': list_name,
            'timestamp': datetime.now().isoformat(),
            'cas_id': new_row['cas_id'] if new_row is not None else old_row['cas_id'],
            'cas_name': new_row['cas_name'] if new_row is not None else old_row['cas_name']
        }

        if change_type == 'insertion' and new_row is not None:
            record['new_values'] = new_row.to_dict()
            record['old_values'] = None

        elif change_type == 'deletion' and old_row is not None:
            record['new_values'] = None
            record['old_values'] = old_row.to_dict()

        elif change_type == 'modification':
            record['modified_fields'] = ', '.join(modified_fields) if modified_fields else ''
            record['new_values'] = new_row.to_dict() if new_row is not None else None
            record['old_values'] = old_row.to_dict() if old_row is not None else None

        return record

    def _get_modified_fields(self, old_row: pd.Series, new_row: pd.Series) -> List[str]:
        modified = []
        common_columns = old_row.index.intersection(new_row.index)

        for col in common_columns:
            old_val = old_row[col]
            new_val = new_row[col]

            if pd.isna(old_val) and pd.isna(new_val):
                continue

            if old_val != new_val:
                modified.append(col)

        return modified

    def detect_all_changes(self, old_lists: Dict[str, pd.DataFrame],
                          new_lists: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        self.logger.info(f"Detection des changements pour {len(new_lists)} listes")
        all_changes = []

        for list_name in new_lists.keys():
            old_df = old_lists.get(list_name, pd.DataFrame())
            new_df = new_lists[list_name]

            self.logger.debug(f"Detection pour {list_name}: {len(old_df)} -> {len(new_df)} enregistrements")
            changes_df = self.detect_changes_for_list(old_df, new_df, list_name)
            if not changes_df.empty:
                all_changes.append(changes_df)
                self.logger.info(f"{len(changes_df)} changements detectes pour {list_name}")

        if all_changes:
            total_changes = pd.concat(all_changes, ignore_index=True)
            self.logger.info(f"Total: {len(total_changes)} changements detectes")
            return total_changes
        self.logger.info("Aucun changement detecte")
        return pd.DataFrame()
