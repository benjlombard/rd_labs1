"""
Module d'analyse de risque et de scoring des substances chimiques
Calcule des scores de criticité basés sur l'historique et fait des prédictions simples
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from backend.logger import get_logger

logger = get_logger()


class RiskAnalyzer:
    """Analyseur de risque pour les substances chimiques"""

    def __init__(self):
        """Initialise l'analyseur de risque"""
        # Poids pour le calcul du score (total = 100%)
        self.weights = {
            'modification_frequency': 0.30,  # Fréquence des modifications
            'list_presence': 0.20,           # Nombre de listes
            'recent_change_type': 0.30,      # Type de changement récent
            'recency': 0.20                  # Ancienneté
        }
        logger.info("RiskAnalyzer initialisé")

    def calculate_risk_score(self, cas_id: str, aggregated_df: pd.DataFrame,
                            history_df: pd.DataFrame) -> Dict:
        """
        Calcule le score de risque pour une substance

        Args:
            cas_id: CAS ID de la substance
            aggregated_df: DataFrame des données agrégées
            history_df: DataFrame de l'historique des changements

        Returns:
            Dictionnaire avec le score et les détails
        """
        try:
            # Filtrer les données pour cette substance
            substance_data = aggregated_df[aggregated_df['cas_id'] == cas_id]

            # Gérer le cas d'un historique vide
            if history_df.empty or 'cas_id' not in history_df.columns:
                substance_history = pd.DataFrame()
            else:
                substance_history = history_df[history_df['cas_id'] == cas_id].copy()

            if substance_data.empty:
                logger.warning(f"Aucune donnée trouvée pour CAS ID: {cas_id}")
                return self._default_score()

            # Calcul des composantes du score
            mod_freq_score = self._calculate_modification_frequency_score(substance_history)
            list_presence_score = self._calculate_list_presence_score(substance_data)
            recent_change_score = self._calculate_recent_change_score(substance_history)
            recency_score = self._calculate_recency_score(substance_data, substance_history)

            # Score total (pondéré)
            total_score = (
                mod_freq_score * self.weights['modification_frequency'] +
                list_presence_score * self.weights['list_presence'] +
                recent_change_score * self.weights['recent_change_type'] +
                recency_score * self.weights['recency']
            )

            # Déterminer le niveau et le badge
            level, badge = self._get_risk_level(total_score)

            result = {
                'cas_id': cas_id,
                'total_score': round(total_score, 2),
                'level': level,
                'badge': badge,
                'components': {
                    'modification_frequency': round(mod_freq_score, 2),
                    'list_presence': round(list_presence_score, 2),
                    'recent_change_type': round(recent_change_score, 2),
                    'recency': round(recency_score, 2)
                },
                'metadata': {
                    'total_modifications': len(substance_history),
                    'lists_count': len(substance_data),
                    'last_change': substance_history['timestamp'].max() if not substance_history.empty else None
                }
            }

            logger.debug(f"Score calculé pour {cas_id}: {total_score} ({level})")
            return result

        except Exception as e:
            logger.error(f"Erreur lors du calcul du score pour {cas_id}: {e}", exc_info=True)
            return self._default_score()

    def _calculate_modification_frequency_score(self, history_df: pd.DataFrame) -> float:
        """
        Calcule le score basé sur la fréquence de modification

        Plus il y a de modifications, plus le score est élevé
        """
        if history_df.empty:
            return 0.0

        modification_count = len(history_df[history_df['change_type'] == 'modification'])

        # Échelle: 0 modif = 0, 1-2 modifs = 25, 3-5 modifs = 50, 6-10 modifs = 75, 10+ = 100
        if modification_count == 0:
            return 0.0
        elif modification_count <= 2:
            return 25.0
        elif modification_count <= 5:
            return 50.0
        elif modification_count <= 10:
            return 75.0
        else:
            return 100.0

    def _calculate_list_presence_score(self, substance_df: pd.DataFrame) -> float:
        """
        Calcule le score basé sur le nombre de listes où la substance apparaît

        Plus elle est présente dans de listes, plus c'est important
        """
        lists_count = len(substance_df)

        # Échelle: 1 liste = 25, 2 listes = 50, 3 listes = 75, 4+ listes = 100
        if lists_count == 1:
            return 25.0
        elif lists_count == 2:
            return 50.0
        elif lists_count == 3:
            return 75.0
        else:
            return 100.0

    def _calculate_recent_change_score(self, history_df: pd.DataFrame) -> float:
        """
        Calcule le score basé sur le type de changement le plus récent

        Suppression = critique, Modification = élevé, Insertion = moyen
        """
        if history_df.empty:
            return 0.0

        # Trier par timestamp décroissant
        history_sorted = history_df.sort_values('timestamp', ascending=False)
        latest_change = history_sorted.iloc[0]['change_type']

        change_scores = {
            'suppression': 100.0,
            'modification': 60.0,
            'insertion': 30.0
        }

        return change_scores.get(latest_change, 0.0)

    def _calculate_recency_score(self, substance_df: pd.DataFrame,
                                 history_df: pd.DataFrame) -> float:
        """
        Calcule le score basé sur l'ancienneté de la substance

        Nouvellement ajoutée = score élevé, ancienne = score faible
        """
        try:
            # Utiliser created_at si disponible
            if 'created_at' in substance_df.columns:
                created_dates = pd.to_datetime(substance_df['created_at'])
                oldest_date = created_dates.min()
            elif not history_df.empty:
                # Sinon utiliser la date de première insertion dans l'historique
                insertions = history_df[history_df['change_type'] == 'insertion']
                if not insertions.empty:
                    oldest_date = pd.to_datetime(insertions['timestamp'].min())
                else:
                    return 50.0  # Score moyen par défaut
            else:
                return 50.0

            # Calculer l'âge en jours
            age_days = (datetime.now() - oldest_date).days

            # Échelle: 0-7 jours = 100, 8-30 jours = 75, 31-90 jours = 50, 91-365 jours = 25, 365+ = 0
            if age_days <= 7:
                return 100.0
            elif age_days <= 30:
                return 75.0
            elif age_days <= 90:
                return 50.0
            elif age_days <= 365:
                return 25.0
            else:
                return 0.0

        except Exception as e:
            logger.warning(f"Erreur lors du calcul du score de récence: {e}")
            return 50.0

    def _get_risk_level(self, score: float) -> Tuple[str, str]:
        """
        Détermine le niveau de risque et le badge associé

        Args:
            score: Score total (0-100)

        Returns:
            Tuple (niveau, badge)
        """
        if score >= 76:
            return "Critique", "🔴"
        elif score >= 51:
            return "Élevé", "🟠"
        elif score >= 26:
            return "Moyen", "🟡"
        else:
            return "Faible", "🟢"

    def _default_score(self) -> Dict:
        """Retourne un score par défaut en cas d'erreur"""
        return {
            'cas_id': 'unknown',
            'total_score': 0.0,
            'level': 'Faible',
            'badge': '🟢',
            'components': {
                'modification_frequency': 0.0,
                'list_presence': 0.0,
                'recent_change_type': 0.0,
                'recency': 0.0
            },
            'metadata': {
                'total_modifications': 0,
                'lists_count': 0,
                'last_change': None
            }
        }

    def calculate_scores_for_watchlist(self, cas_ids: List[str], aggregated_df: pd.DataFrame,
                                      history_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcule les scores pour une liste de CAS IDs

        Args:
            cas_ids: Liste des CAS IDs à analyser
            aggregated_df: DataFrame des données agrégées
            history_df: DataFrame de l'historique

        Returns:
            DataFrame avec les scores
        """
        scores = []
        for cas_id in cas_ids:
            score = self.calculate_risk_score(cas_id, aggregated_df, history_df)
            scores.append(score)

        logger.info(f"Scores calculés pour {len(scores)} substances")
        return pd.DataFrame(scores)

    def predict_next_change(self, cas_id: str, history_df: pd.DataFrame) -> Dict:
        """
        Prédit le prochain changement probable pour une substance

        Args:
            cas_id: CAS ID de la substance
            history_df: DataFrame de l'historique

        Returns:
            Dictionnaire avec la prédiction
        """
        try:
            # Gérer le cas d'un historique vide
            if history_df.empty or 'cas_id' not in history_df.columns:
                substance_history = pd.DataFrame()
            else:
                substance_history = history_df[history_df['cas_id'] == cas_id].copy()

            if substance_history.empty or len(substance_history) < 2:
                return {
                    'prediction': 'Données insuffisantes',
                    'confidence': 'Faible',
                    'estimated_date': None,
                    'average_interval_days': None
                }

            # Convertir les timestamps et trier
            substance_history['timestamp'] = pd.to_datetime(substance_history['timestamp'])
            substance_history = substance_history.sort_values('timestamp')

            # Calculer les intervalles entre changements
            timestamps = substance_history['timestamp'].values
            intervals = []
            for i in range(1, len(timestamps)):
                delta = pd.Timestamp(timestamps[i]) - pd.Timestamp(timestamps[i-1])
                intervals.append(delta.days)

            if not intervals:
                return {
                    'prediction': 'Données insuffisantes',
                    'confidence': 'Faible',
                    'estimated_date': None,
                    'average_interval_days': None
                }

            # Calculer l'intervalle moyen
            avg_interval_days = sum(intervals) / len(intervals)
            last_change = pd.Timestamp(timestamps[-1])
            predicted_next = last_change + timedelta(days=avg_interval_days)

            # Déterminer la confiance
            if len(intervals) >= 3:
                confidence = "Élevée"
            elif len(intervals) >= 2:
                confidence = "Moyenne"
            else:
                confidence = "Faible"

            # Vérifier si changement imminent
            days_until_predicted = (predicted_next - datetime.now()).days
            is_imminent = days_until_predicted <= 30

            result = {
                'prediction': f"Changement prévu dans ~{int(avg_interval_days)} jours",
                'confidence': confidence,
                'estimated_date': predicted_next.strftime('%Y-%m-%d'),
                'average_interval_days': int(avg_interval_days),
                'is_imminent': is_imminent,
                'days_until_predicted': days_until_predicted
            }

            logger.debug(f"Prédiction pour {cas_id}: {result['prediction']}")
            return result

        except Exception as e:
            logger.error(f"Erreur lors de la prédiction pour {cas_id}: {e}", exc_info=True)
            return {
                'prediction': 'Erreur',
                'confidence': 'Faible',
                'estimated_date': None,
                'average_interval_days': None
            }

    def detect_anomalies(self, cas_id: str, history_df: pd.DataFrame) -> Dict:
        """
        Détecte les anomalies dans l'historique d'une substance

        Args:
            cas_id: CAS ID de la substance
            history_df: DataFrame de l'historique

        Returns:
            Dictionnaire avec les anomalies détectées
        """
        try:
            # Gérer le cas d'un historique vide
            if history_df.empty or 'cas_id' not in history_df.columns:
                substance_history = pd.DataFrame()
            else:
                substance_history = history_df[history_df['cas_id'] == cas_id].copy()

            if substance_history.empty or len(substance_history) < 3:
                return {
                    'has_anomaly': False,
                    'anomaly_type': None,
                    'description': 'Historique insuffisant pour détecter des anomalies'
                }

            # Convertir les timestamps
            substance_history['timestamp'] = pd.to_datetime(substance_history['timestamp'])
            substance_history = substance_history.sort_values('timestamp')

            # Calculer les intervalles
            timestamps = substance_history['timestamp'].values
            intervals = []
            for i in range(1, len(timestamps)):
                delta = pd.Timestamp(timestamps[i]) - pd.Timestamp(timestamps[i-1])
                intervals.append(delta.days)

            avg_interval = sum(intervals) / len(intervals)
            last_interval = intervals[-1]

            # Détecter anomalie: dernier intervalle < 50% de la moyenne
            if last_interval < avg_interval * 0.5 and avg_interval > 7:
                return {
                    'has_anomaly': True,
                    'anomaly_type': 'Changement inhabituel',
                    'description': f'Changement détecté après seulement {last_interval} jours (moyenne: {int(avg_interval)} jours)',
                    'badge': '⚠️'
                }

            # Détecter anomalie: suppressions fréquentes
            recent_changes = substance_history.tail(5)
            suppression_count = len(recent_changes[recent_changes['change_type'] == 'suppression'])
            if suppression_count >= 2:
                return {
                    'has_anomaly': True,
                    'anomaly_type': 'Suppressions fréquentes',
                    'description': f'{suppression_count} suppressions dans les 5 derniers changements',
                    'badge': '⚠️'
                }

            return {
                'has_anomaly': False,
                'anomaly_type': None,
                'description': 'Aucune anomalie détectée'
            }

        except Exception as e:
            logger.error(f"Erreur lors de la détection d'anomalies pour {cas_id}: {e}", exc_info=True)
            return {
                'has_anomaly': False,
                'anomaly_type': None,
                'description': 'Erreur lors de l\'analyse'
            }

    def get_top_risk_substances(self, cas_ids: List[str], aggregated_df: pd.DataFrame,
                               history_df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
        """
        Récupère les N substances avec le score de risque le plus élevé

        Args:
            cas_ids: Liste des CAS IDs à analyser
            aggregated_df: DataFrame des données agrégées
            history_df: DataFrame de l'historique
            top_n: Nombre de substances à retourner

        Returns:
            DataFrame trié par score décroissant
        """
        scores_df = self.calculate_scores_for_watchlist(cas_ids, aggregated_df, history_df)
        top_risks = scores_df.nlargest(top_n, 'total_score')
        logger.info(f"Top {top_n} substances à risque identifiées")
        return top_risks
