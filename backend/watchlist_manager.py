"""
Module de gestion des watchlists (listes de surveillance personnalisées)
Permet de créer, modifier, supprimer et gérer des watchlists de substances chimiques
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import uuid
from backend.logger import get_logger

logger = get_logger()


class WatchlistManager:
    """Gestionnaire des watchlists de substances chimiques"""

    def __init__(self, watchlists_file: str = "data/watchlists.json"):
        """
        Initialise le gestionnaire de watchlists

        Args:
            watchlists_file: Chemin du fichier JSON des watchlists
        """
        self.watchlists_file = watchlists_file
        self._ensure_file_exists()
        logger.info(f"WatchlistManager initialisé avec le fichier: {watchlists_file}")

    def _ensure_file_exists(self):
        """Crée le fichier de watchlists s'il n'existe pas"""
        if not os.path.exists(self.watchlists_file):
            os.makedirs(os.path.dirname(self.watchlists_file), exist_ok=True)
            initial_data = {"watchlists": []}
            with open(self.watchlists_file, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Fichier watchlists créé: {self.watchlists_file}")

    def load_watchlists(self) -> List[Dict]:
        """
        Charge toutes les watchlists depuis le fichier

        Returns:
            Liste des watchlists
        """
        try:
            with open(self.watchlists_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.debug(f"{len(data.get('watchlists', []))} watchlists chargées")
            return data.get('watchlists', [])
        except Exception as e:
            logger.error(f"Erreur lors du chargement des watchlists: {e}", exc_info=True)
            return []

    def save_watchlists(self, watchlists: List[Dict]):
        """
        Sauvegarde les watchlists dans le fichier

        Args:
            watchlists: Liste des watchlists à sauvegarder
        """
        try:
            data = {"watchlists": watchlists}
            with open(self.watchlists_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"{len(watchlists)} watchlists sauvegardées")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des watchlists: {e}", exc_info=True)

    def create_watchlist(self, name: str, description: str = "", tags: List[str] = None) -> Dict:
        """
        Crée une nouvelle watchlist

        Args:
            name: Nom de la watchlist
            description: Description optionnelle
            tags: Tags optionnels

        Returns:
            La watchlist créée
        """
        watchlist = {
            "id": str(uuid.uuid4()),
            "name": name,
            "description": description,
            "cas_ids": [],
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        watchlists = self.load_watchlists()
        watchlists.append(watchlist)
        self.save_watchlists(watchlists)

        logger.info(f"Watchlist créée: {name} (ID: {watchlist['id']})")
        return watchlist

    def get_watchlist(self, watchlist_id: str) -> Optional[Dict]:
        """
        Récupère une watchlist par son ID

        Args:
            watchlist_id: ID de la watchlist

        Returns:
            La watchlist ou None si non trouvée
        """
        watchlists = self.load_watchlists()
        for wl in watchlists:
            if wl['id'] == watchlist_id:
                return wl
        return None

    def update_watchlist(self, watchlist_id: str, name: str = None, description: str = None,
                        tags: List[str] = None) -> bool:
        """
        Met à jour les métadonnées d'une watchlist

        Args:
            watchlist_id: ID de la watchlist
            name: Nouveau nom (optionnel)
            description: Nouvelle description (optionnel)
            tags: Nouveaux tags (optionnel)

        Returns:
            True si mise à jour réussie, False sinon
        """
        watchlists = self.load_watchlists()
        for wl in watchlists:
            if wl['id'] == watchlist_id:
                if name is not None:
                    wl['name'] = name
                if description is not None:
                    wl['description'] = description
                if tags is not None:
                    wl['tags'] = tags
                wl['updated_at'] = datetime.now().isoformat()
                self.save_watchlists(watchlists)
                logger.info(f"Watchlist mise à jour: {watchlist_id}")
                return True
        logger.warning(f"Watchlist non trouvée pour mise à jour: {watchlist_id}")
        return False

    def delete_watchlist(self, watchlist_id: str) -> bool:
        """
        Supprime une watchlist

        Args:
            watchlist_id: ID de la watchlist à supprimer

        Returns:
            True si suppression réussie, False sinon
        """
        watchlists = self.load_watchlists()
        initial_count = len(watchlists)
        watchlists = [wl for wl in watchlists if wl['id'] != watchlist_id]

        if len(watchlists) < initial_count:
            self.save_watchlists(watchlists)
            logger.info(f"Watchlist supprimée: {watchlist_id}")
            return True

        logger.warning(f"Watchlist non trouvée pour suppression: {watchlist_id}")
        return False

    def add_cas_to_watchlist(self, watchlist_id: str, cas_id: str) -> bool:
        """
        Ajoute un CAS ID à une watchlist

        Args:
            watchlist_id: ID de la watchlist
            cas_id: CAS ID à ajouter

        Returns:
            True si ajout réussi, False sinon
        """
        watchlists = self.load_watchlists()
        for wl in watchlists:
            if wl['id'] == watchlist_id:
                if cas_id not in wl['cas_ids']:
                    wl['cas_ids'].append(cas_id)
                    wl['updated_at'] = datetime.now().isoformat()
                    self.save_watchlists(watchlists)
                    logger.info(f"CAS ID {cas_id} ajouté à la watchlist {watchlist_id}")
                    return True
                else:
                    logger.debug(f"CAS ID {cas_id} déjà dans la watchlist {watchlist_id}")
                    return False
        logger.warning(f"Watchlist non trouvée: {watchlist_id}")
        return False

    def remove_cas_from_watchlist(self, watchlist_id: str, cas_id: str) -> bool:
        """
        Retire un CAS ID d'une watchlist

        Args:
            watchlist_id: ID de la watchlist
            cas_id: CAS ID à retirer

        Returns:
            True si retrait réussi, False sinon
        """
        watchlists = self.load_watchlists()
        for wl in watchlists:
            if wl['id'] == watchlist_id:
                if cas_id in wl['cas_ids']:
                    wl['cas_ids'].remove(cas_id)
                    wl['updated_at'] = datetime.now().isoformat()
                    self.save_watchlists(watchlists)
                    logger.info(f"CAS ID {cas_id} retiré de la watchlist {watchlist_id}")
                    return True
                else:
                    logger.debug(f"CAS ID {cas_id} non trouvé dans la watchlist {watchlist_id}")
                    return False
        logger.warning(f"Watchlist non trouvée: {watchlist_id}")
        return False

    def is_cas_in_any_watchlist(self, cas_id: str) -> bool:
        """
        Vérifie si un CAS ID est dans au moins une watchlist

        Args:
            cas_id: CAS ID à vérifier

        Returns:
            True si le CAS ID est surveillé, False sinon
        """
        watchlists = self.load_watchlists()
        for wl in watchlists:
            if cas_id in wl['cas_ids']:
                return True
        return False

    def get_watchlists_for_cas(self, cas_id: str) -> List[Dict]:
        """
        Récupère toutes les watchlists contenant un CAS ID

        Args:
            cas_id: CAS ID recherché

        Returns:
            Liste des watchlists contenant ce CAS ID
        """
        watchlists = self.load_watchlists()
        return [wl for wl in watchlists if cas_id in wl['cas_ids']]

    def get_all_watched_cas_ids(self) -> List[str]:
        """
        Récupère tous les CAS IDs surveillés (toutes watchlists confondues)

        Returns:
            Liste unique de tous les CAS IDs surveillés
        """
        watchlists = self.load_watchlists()
        all_cas_ids = set()
        for wl in watchlists:
            all_cas_ids.update(wl['cas_ids'])
        return list(all_cas_ids)

    def export_watchlist(self, watchlist_id: str, export_path: str) -> bool:
        """
        Exporte une watchlist en JSON

        Args:
            watchlist_id: ID de la watchlist à exporter
            export_path: Chemin du fichier d'export

        Returns:
            True si export réussi, False sinon
        """
        watchlist = self.get_watchlist(watchlist_id)
        if watchlist:
            try:
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(watchlist, f, indent=2, ensure_ascii=False)
                logger.info(f"Watchlist exportée: {export_path}")
                return True
            except Exception as e:
                logger.error(f"Erreur lors de l'export de la watchlist: {e}", exc_info=True)
                return False
        return False

    def import_watchlist(self, import_path: str) -> Optional[Dict]:
        """
        Importe une watchlist depuis un fichier JSON

        Args:
            import_path: Chemin du fichier à importer

        Returns:
            La watchlist importée ou None si erreur
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                watchlist = json.load(f)

            # Générer un nouvel ID pour éviter les conflits
            watchlist['id'] = str(uuid.uuid4())
            watchlist['updated_at'] = datetime.now().isoformat()

            watchlists = self.load_watchlists()
            watchlists.append(watchlist)
            self.save_watchlists(watchlists)

            logger.info(f"Watchlist importée: {import_path}")
            return watchlist
        except Exception as e:
            logger.error(f"Erreur lors de l'import de la watchlist: {e}", exc_info=True)
            return None

    def get_statistics(self) -> Dict:
        """
        Récupère des statistiques sur les watchlists

        Returns:
            Dictionnaire de statistiques
        """
        watchlists = self.load_watchlists()
        all_cas_ids = self.get_all_watched_cas_ids()

        stats = {
            "total_watchlists": len(watchlists),
            "total_watched_substances": len(all_cas_ids),
            "watchlists_details": []
        }

        for wl in watchlists:
            stats["watchlists_details"].append({
                "name": wl['name'],
                "substances_count": len(wl['cas_ids']),
                "tags": wl['tags'],
                "created_at": wl['created_at']
            })

        return stats
