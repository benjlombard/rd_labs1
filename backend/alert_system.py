"""
Module de gestion des alertes pour les substances surveillées
Crée et gère les notifications lors de changements sur les watchlists
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import uuid
import pandas as pd
from backend.logger import get_logger

logger = get_logger()


class AlertSystem:
    """Système de gestion des alertes pour les watchlists"""

    def __init__(self, alerts_file: str = "data/alerts.json"):
        """
        Initialise le système d'alertes

        Args:
            alerts_file: Chemin du fichier JSON des alertes
        """
        self.alerts_file = alerts_file
        self._ensure_file_exists()
        logger.info(f"AlertSystem initialisé avec le fichier: {alerts_file}")

    def _ensure_file_exists(self):
        """Crée le fichier d'alertes s'il n'existe pas"""
        if not os.path.exists(self.alerts_file):
            os.makedirs(os.path.dirname(self.alerts_file), exist_ok=True)
            initial_data = {"alerts": []}
            with open(self.alerts_file, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Fichier alertes créé: {self.alerts_file}")

    def load_alerts(self) -> List[Dict]:
        """
        Charge toutes les alertes depuis le fichier

        Returns:
            Liste des alertes
        """
        try:
            with open(self.alerts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.debug(f"{len(data.get('alerts', []))} alertes chargées")
            return data.get('alerts', [])
        except Exception as e:
            logger.error(f"Erreur lors du chargement des alertes: {e}", exc_info=True)
            return []

    def save_alerts(self, alerts: List[Dict]):
        """
        Sauvegarde les alertes dans le fichier

        Args:
            alerts: Liste des alertes à sauvegarder
        """
        try:
            data = {"alerts": alerts}
            with open(self.alerts_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug(f"{len(alerts)} alertes sauvegardées")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des alertes: {e}", exc_info=True)

    def create_alert(self, cas_id: str, cas_name: str, watchlist_id: str,
                    watchlist_name: str, change_type: str, source_list: str,
                    risk_score: float = None, risk_level: str = None,
                    modified_fields: str = None) -> Dict:
        """
        Crée une nouvelle alerte

        Args:
            cas_id: CAS ID de la substance
            cas_name: Nom de la substance
            watchlist_id: ID de la watchlist concernée
            watchlist_name: Nom de la watchlist
            change_type: Type de changement (insertion, suppression, modification)
            source_list: Liste source du changement
            risk_score: Score de risque (optionnel)
            risk_level: Niveau de risque (optionnel)
            modified_fields: Champs modifiés (optionnel)

        Returns:
            L'alerte créée
        """
        # Générer le message
        message = self._generate_alert_message(cas_name, change_type, source_list, modified_fields)

        alert = {
            "id": str(uuid.uuid4()),
            "cas_id": cas_id,
            "cas_name": cas_name,
            "watchlist_id": watchlist_id,
            "watchlist_name": watchlist_name,
            "change_type": change_type,
            "source_list": source_list,
            "timestamp": datetime.now().isoformat(),
            "is_read": False,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "modified_fields": modified_fields,
            "message": message
        }

        alerts = self.load_alerts()
        alerts.append(alert)
        self.save_alerts(alerts)

        logger.info(f"Alerte créée: {change_type} pour {cas_id} dans watchlist {watchlist_name}")
        return alert

    def _generate_alert_message(self, cas_name: str, change_type: str,
                               source_list: str, modified_fields: str = None) -> str:
        """
        Génère un message descriptif pour l'alerte

        Args:
            cas_name: Nom de la substance
            change_type: Type de changement
            source_list: Liste source
            modified_fields: Champs modifiés (optionnel)

        Returns:
            Message formaté
        """
        messages = {
            'insertion': f"🆕 {cas_name} a été ajouté à la liste {source_list}",
            'suppression': f"🗑️ {cas_name} a été supprimé de la liste {source_list}",
            'modification': f"✏️ {cas_name} a été modifié dans la liste {source_list}"
        }

        base_message = messages.get(change_type, f"{cas_name} - {change_type}")

        if modified_fields and change_type == 'modification':
            base_message += f" (champs: {modified_fields})"

        return base_message

    def create_alerts_from_changes(self, changes_df: pd.DataFrame, watchlist_manager,
                                   risk_analyzer=None, aggregated_df=None, history_df=None):
        """
        Crée des alertes pour tous les changements concernant des substances watchlistées

        Args:
            changes_df: DataFrame des changements détectés
            watchlist_manager: Instance du WatchlistManager
            risk_analyzer: Instance du RiskAnalyzer (optionnel)
            aggregated_df: DataFrame des données agrégées (pour scoring)
            history_df: DataFrame de l'historique (pour scoring)
        """
        if changes_df.empty:
            logger.info("Aucun changement à traiter pour les alertes")
            return

        created_count = 0
        for _, change in changes_df.iterrows():
            cas_id = change['cas_id']

            # Vérifier si cette substance est dans une watchlist
            watchlists = watchlist_manager.get_watchlists_for_cas(cas_id)

            for wl in watchlists:
                # Calculer le score si risk_analyzer est fourni
                risk_score = None
                risk_level = None
                if risk_analyzer and aggregated_df is not None and history_df is not None:
                    try:
                        score_data = risk_analyzer.calculate_risk_score(cas_id, aggregated_df, history_df)
                        risk_score = score_data.get('total_score')
                        risk_level = score_data.get('level')
                    except Exception as e:
                        logger.warning(f"Impossible de calculer le score pour {cas_id}: {e}")

                # Créer l'alerte
                self.create_alert(
                    cas_id=cas_id,
                    cas_name=change.get('cas_name', 'Unknown'),
                    watchlist_id=wl['id'],
                    watchlist_name=wl['name'],
                    change_type=change['change_type'],
                    source_list=change['source_list'],
                    risk_score=risk_score,
                    risk_level=risk_level,
                    modified_fields=change.get('modified_fields', '')
                )
                created_count += 1

        logger.info(f"{created_count} alertes créées depuis les changements")

    def get_unread_alerts(self) -> List[Dict]:
        """
        Récupère toutes les alertes non lues

        Returns:
            Liste des alertes non lues
        """
        alerts = self.load_alerts()
        unread = [alert for alert in alerts if not alert.get('is_read', False)]
        logger.debug(f"{len(unread)} alertes non lues")
        return unread

    def get_unread_count(self) -> int:
        """
        Compte le nombre d'alertes non lues

        Returns:
            Nombre d'alertes non lues
        """
        return len(self.get_unread_alerts())

    def mark_as_read(self, alert_id: str) -> bool:
        """
        Marque une alerte comme lue

        Args:
            alert_id: ID de l'alerte

        Returns:
            True si succès, False sinon
        """
        alerts = self.load_alerts()
        for alert in alerts:
            if alert['id'] == alert_id:
                alert['is_read'] = True
                self.save_alerts(alerts)
                logger.info(f"Alerte marquée comme lue: {alert_id}")
                return True
        return False

    def mark_all_as_read(self) -> int:
        """
        Marque toutes les alertes comme lues

        Returns:
            Nombre d'alertes marquées
        """
        alerts = self.load_alerts()
        count = 0
        for alert in alerts:
            if not alert.get('is_read', False):
                alert['is_read'] = True
                count += 1
        self.save_alerts(alerts)
        logger.info(f"{count} alertes marquées comme lues")
        return count

    def get_alerts_by_watchlist(self, watchlist_id: str) -> List[Dict]:
        """
        Récupère les alertes pour une watchlist spécifique

        Args:
            watchlist_id: ID de la watchlist

        Returns:
            Liste des alertes
        """
        alerts = self.load_alerts()
        filtered = [alert for alert in alerts if alert['watchlist_id'] == watchlist_id]
        return filtered

    def get_alerts_by_cas(self, cas_id: str) -> List[Dict]:
        """
        Récupère les alertes pour un CAS ID spécifique

        Args:
            cas_id: CAS ID

        Returns:
            Liste des alertes
        """
        alerts = self.load_alerts()
        filtered = [alert for alert in alerts if alert['cas_id'] == cas_id]
        return filtered

    def get_alerts_by_type(self, change_type: str) -> List[Dict]:
        """
        Récupère les alertes par type de changement

        Args:
            change_type: Type de changement (insertion, suppression, modification)

        Returns:
            Liste des alertes
        """
        alerts = self.load_alerts()
        filtered = [alert for alert in alerts if alert['change_type'] == change_type]
        return filtered

    def get_recent_alerts(self, limit: int = 10) -> List[Dict]:
        """
        Récupère les N alertes les plus récentes

        Args:
            limit: Nombre d'alertes à retourner

        Returns:
            Liste des alertes récentes
        """
        alerts = self.load_alerts()
        # Trier par timestamp décroissant
        sorted_alerts = sorted(alerts, key=lambda x: x['timestamp'], reverse=True)
        return sorted_alerts[:limit]

    def get_high_priority_alerts(self) -> List[Dict]:
        """
        Récupère les alertes de haute priorité (risque élevé ou critique)

        Returns:
            Liste des alertes haute priorité
        """
        alerts = self.load_alerts()
        high_priority = [
            alert for alert in alerts
            if alert.get('risk_level') in ['Élevé', 'Critique'] and not alert.get('is_read', False)
        ]
        logger.debug(f"{len(high_priority)} alertes haute priorité")
        return high_priority

    def delete_alert(self, alert_id: str) -> bool:
        """
        Supprime une alerte

        Args:
            alert_id: ID de l'alerte à supprimer

        Returns:
            True si suppression réussie, False sinon
        """
        alerts = self.load_alerts()
        initial_count = len(alerts)
        alerts = [alert for alert in alerts if alert['id'] != alert_id]

        if len(alerts) < initial_count:
            self.save_alerts(alerts)
            logger.info(f"Alerte supprimée: {alert_id}")
            return True

        logger.warning(f"Alerte non trouvée pour suppression: {alert_id}")
        return False

    def clear_old_alerts(self, days: int = 30) -> int:
        """
        Supprime les alertes lues de plus de X jours

        Args:
            days: Nombre de jours de rétention

        Returns:
            Nombre d'alertes supprimées
        """
        alerts = self.load_alerts()
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)

        initial_count = len(alerts)
        alerts = [
            alert for alert in alerts
            if not alert.get('is_read', False) or
            datetime.fromisoformat(alert['timestamp']).timestamp() > cutoff_date
        ]

        deleted_count = initial_count - len(alerts)
        if deleted_count > 0:
            self.save_alerts(alerts)
            logger.info(f"{deleted_count} anciennes alertes supprimées")

        return deleted_count

    def get_statistics(self) -> Dict:
        """
        Récupère des statistiques sur les alertes

        Returns:
            Dictionnaire de statistiques
        """
        alerts = self.load_alerts()

        stats = {
            "total_alerts": len(alerts),
            "unread_count": len([a for a in alerts if not a.get('is_read', False)]),
            "by_type": {
                "insertion": len([a for a in alerts if a['change_type'] == 'insertion']),
                "suppression": len([a for a in alerts if a['change_type'] == 'suppression']),
                "modification": len([a for a in alerts if a['change_type'] == 'modification'])
            },
            "by_risk_level": {
                "Critique": len([a for a in alerts if a.get('risk_level') == 'Critique']),
                "Élevé": len([a for a in alerts if a.get('risk_level') == 'Élevé']),
                "Moyen": len([a for a in alerts if a.get('risk_level') == 'Moyen']),
                "Faible": len([a for a in alerts if a.get('risk_level') == 'Faible'])
            },
            "high_priority_unread": len(self.get_high_priority_alerts())
        }

        return stats

    def to_dataframe(self, alerts: List[Dict] = None) -> pd.DataFrame:
        """
        Convertit les alertes en DataFrame pour affichage

        Args:
            alerts: Liste d'alertes (si None, charge toutes les alertes)

        Returns:
            DataFrame des alertes
        """
        if alerts is None:
            alerts = self.load_alerts()

        if not alerts:
            return pd.DataFrame()

        df = pd.DataFrame(alerts)

        # Réorganiser les colonnes pour l'affichage
        display_columns = ['timestamp', 'message', 'risk_level', 'risk_score',
                          'watchlist_name', 'is_read', 'change_type', 'cas_id']
        existing_columns = [col for col in display_columns if col in df.columns]

        return df[existing_columns]
