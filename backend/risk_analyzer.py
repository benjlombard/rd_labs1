"""
Module d'analyse de risque et de scoring des substances chimiques
Calcule des scores de criticité basés sur l'historique et fait des prédictions simples
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from io import BytesIO
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

    def generate_radar_chart(self, score_data: Dict, cas_name: str = None) -> plt.Figure:
        """
        Génère un graphique radar pour visualiser les 4 composantes du score de risque

        Args:
            score_data: Dictionnaire retourné par calculate_risk_score()
            cas_name: Nom de la substance (optionnel, pour le titre)

        Returns:
            Figure matplotlib du graphique radar
        """
        try:
            # Extraire les composantes du score
            components = score_data['components']
            categories = [
                'Fréquence\nModifications',
                'Présence\nListes',
                'Type\nChangement',
                'Récence'
            ]
            values = [
                components['modification_frequency'],
                components['list_presence'],
                components['recent_change_type'],
                components['recency']
            ]

            # Nombre de variables
            num_vars = len(categories)

            # Calculer les angles pour chaque axe
            angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()

            # Fermer le polygone
            values += values[:1]
            angles += angles[:1]

            # Créer la figure
            fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))

            # Définir la couleur selon le niveau de risque
            level = score_data['level']
            colors = {
                'Critique': '#d32f2f',   # Rouge
                'Élevé': '#f57c00',      # Orange
                'Moyen': '#fbc02d',      # Jaune
                'Faible': '#388e3c'      # Vert
            }
            color = colors.get(level, '#1976d2')

            # Tracer le polygone
            ax.plot(angles, values, 'o-', linewidth=2, color=color, label=f'Score: {score_data["total_score"]}')
            ax.fill(angles, values, alpha=0.25, color=color)

            # Configurer les étiquettes des axes
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(categories, size=10)

            # Configurer l'échelle radiale (0-100)
            ax.set_ylim(0, 100)
            ax.set_yticks([25, 50, 75, 100])
            ax.set_yticklabels(['25', '50', '75', '100'], size=8)
            ax.set_rlabel_position(180 / num_vars)

            # Grille
            ax.grid(True, linestyle='--', alpha=0.7)

            # Titre
            title = f"Analyse de Risque"
            if cas_name:
                title += f"\n{cas_name}"
            title += f"\nScore Total: {score_data['total_score']} - {score_data['badge']} {level}"

            plt.title(title, size=14, pad=20, weight='bold')

            # Légende avec les valeurs
            legend_text = '\n'.join([
                f"Fréq. Modif.: {components['modification_frequency']:.0f}",
                f"Présence Listes: {components['list_presence']:.0f}",
                f"Type Changement: {components['recent_change_type']:.0f}",
                f"Récence: {components['recency']:.0f}"
            ])

            ax.text(1.4, 0.5, legend_text, transform=ax.transAxes,
                   fontsize=9, verticalalignment='center',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

            plt.tight_layout()

            logger.debug(f"Graphique radar généré pour {score_data.get('cas_id', 'unknown')}")
            return fig

        except Exception as e:
            logger.error(f"Erreur lors de la génération du graphique radar: {e}", exc_info=True)
            # Retourner une figure vide en cas d'erreur
            fig, ax = plt.subplots(figsize=(8, 8))
            ax.text(0.5, 0.5, 'Erreur lors de la génération du graphique',
                   ha='center', va='center', fontsize=12)
            ax.axis('off')
            return fig

    def generate_comparison_radar_chart(self, scores_data_list: List[Dict],
                                       cas_names: List[str] = None) -> plt.Figure:
        """
        Génère un graphique radar comparatif pour plusieurs substances

        Args:
            scores_data_list: Liste de dictionnaires retournés par calculate_risk_score()
            cas_names: Liste des noms de substances (optionnel)

        Returns:
            Figure matplotlib du graphique radar comparatif
        """
        try:
            if not scores_data_list or len(scores_data_list) > 3:
                raise ValueError("Comparaison possible pour 1 à 3 substances uniquement")

            # Catégories
            categories = [
                'Fréquence\nModifications',
                'Présence\nListes',
                'Type\nChangement',
                'Récence'
            ]
            num_vars = len(categories)

            # Calculer les angles
            angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
            angles += angles[:1]

            # Créer la figure
            fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))

            # Couleurs pour chaque substance
            colors_list = ['#d32f2f', '#1976d2', '#388e3c']

            # Tracer chaque substance
            for idx, score_data in enumerate(scores_data_list):
                components = score_data['components']
                values = [
                    components['modification_frequency'],
                    components['list_presence'],
                    components['recent_change_type'],
                    components['recency']
                ]
                values += values[:1]

                # Label
                label = cas_names[idx] if cas_names and idx < len(cas_names) else f"Substance {idx+1}"
                label += f" (Score: {score_data['total_score']})"

                # Tracer
                color = colors_list[idx % len(colors_list)]
                ax.plot(angles, values, 'o-', linewidth=2, color=color, label=label)
                ax.fill(angles, values, alpha=0.15, color=color)

            # Configurer les axes
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(categories, size=11)
            ax.set_ylim(0, 100)
            ax.set_yticks([25, 50, 75, 100])
            ax.set_yticklabels(['25', '50', '75', '100'], size=9)
            ax.set_rlabel_position(180 / num_vars)

            # Grille
            ax.grid(True, linestyle='--', alpha=0.7)

            # Titre et légende
            plt.title("Comparaison des Scores de Risque", size=14, pad=20, weight='bold')
            plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=10)

            plt.tight_layout()

            logger.debug(f"Graphique radar comparatif généré pour {len(scores_data_list)} substances")
            return fig

        except Exception as e:
            logger.error(f"Erreur lors de la génération du graphique radar comparatif: {e}", exc_info=True)
            fig, ax = plt.subplots(figsize=(10, 10))
            ax.text(0.5, 0.5, f'Erreur: {str(e)}',
                   ha='center', va='center', fontsize=12)
            ax.axis('off')
            return fig

    def generate_calendar_heatmap(self,
                                   history_df: pd.DataFrame,
                                   year: int = None,
                                   source_list_filter: str = None,
                                   change_type_filter: str = None) -> go.Figure:
        """
        Génère un calendrier heatmap interactif des changements (style GitHub contributions)

        Args:
            history_df: DataFrame de l'historique des changements
            year: Année à afficher (défaut: année courante)
            source_list_filter: Filtrer par liste source (optionnel)
            change_type_filter: Filtrer par type de changement (optionnel)

        Returns:
            Figure plotly avec le heatmap calendar
        """
        try:
            # Gérer le cas d'un historique vide
            if history_df.empty:
                logger.warning("Historique vide, impossible de générer le calendrier heatmap")
                fig = go.Figure()
                fig.add_annotation(
                    text="Aucune donnée disponible",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=20)
                )
                return fig

            # Année par défaut
            if year is None:
                year = datetime.now().year

            # Copier le DataFrame pour éviter les modifications
            df = history_df.copy()

            # Convertir timestamp en datetime si nécessaire
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df['date'] = df['timestamp'].dt.date
            else:
                logger.error("Colonne 'timestamp' manquante dans l'historique")
                return go.Figure()

            # Appliquer les filtres
            if source_list_filter and source_list_filter != "Toutes":
                df = df[df['source_list'] == source_list_filter]

            if change_type_filter and change_type_filter != "Tous":
                df = df[df['change_type'] == change_type_filter]

            # Filtrer par année
            df = df[df['timestamp'].dt.year == year]

            # Agréger par date
            daily_counts = df.groupby('date').size().reset_index(name='count')

            # Créer un DataFrame avec toutes les dates de l'année
            start_date = datetime(year, 1, 1).date()
            end_date = datetime(year, 12, 31).date()
            all_dates = pd.date_range(start=start_date, end=end_date, freq='D')

            # DataFrame complet avec toutes les dates
            full_calendar = pd.DataFrame({'date': all_dates.date})
            full_calendar = full_calendar.merge(daily_counts, on='date', how='left')
            full_calendar['count'] = full_calendar['count'].fillna(0).astype(int)

            # Ajouter informations de calendrier
            full_calendar['date_dt'] = pd.to_datetime(full_calendar['date'])
            full_calendar['week'] = full_calendar['date_dt'].dt.isocalendar().week
            full_calendar['weekday'] = full_calendar['date_dt'].dt.dayofweek  # 0=Lundi, 6=Dimanche
            full_calendar['month'] = full_calendar['date_dt'].dt.month
            full_calendar['day'] = full_calendar['date_dt'].dt.day

            # Préparer les données pour le heatmap
            # Format: 7 lignes (jours de la semaine) x 53 colonnes (semaines)
            weeks = sorted(full_calendar['week'].unique())
            z_data = []
            hover_data = []

            weekday_names = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']

            for weekday in range(7):
                week_counts = []
                week_hovers = []
                for week in weeks:
                    day_data = full_calendar[(full_calendar['week'] == week) &
                                             (full_calendar['weekday'] == weekday)]
                    if not day_data.empty:
                        count = day_data.iloc[0]['count']
                        date = day_data.iloc[0]['date']
                        week_counts.append(count)

                        # Détails pour le tooltip
                        if count > 0:
                            day_changes = df[df['date'] == date]
                            insertions = len(day_changes[day_changes['change_type'] == 'insertion'])
                            deletions = len(day_changes[day_changes['change_type'] == 'suppression'])
                            modifications = len(day_changes[day_changes['change_type'] == 'modification'])

                            hover_text = f"<b>{date}</b><br>"
                            hover_text += f"Total: {count} changement{'s' if count > 1 else ''}<br>"
                            hover_text += f"Insertions: {insertions}<br>"
                            hover_text += f"Suppressions: {deletions}<br>"
                            hover_text += f"Modifications: {modifications}"
                        else:
                            hover_text = f"<b>{date}</b><br>Aucun changement"

                        week_hovers.append(hover_text)
                    else:
                        week_counts.append(0)
                        week_hovers.append("")

                z_data.append(week_counts)
                hover_data.append(week_hovers)

            # Définir le gradient de couleur
            max_count = full_calendar['count'].max()
            if max_count == 0:
                max_count = 1  # Éviter division par zéro

            # Colorscale personnalisée (blanc → vert clair → vert foncé → rouge)
            colorscale = [
                [0, '#ebedf0'],      # Blanc (0 changements)
                [0.2, '#c6e48b'],    # Vert très clair
                [0.4, '#7bc96f'],    # Vert clair
                [0.6, '#239a3b'],    # Vert moyen
                [0.8, '#196127'],    # Vert foncé
                [1.0, '#c41e3a']     # Rouge (très actif)
            ]

            # Créer le heatmap
            fig = go.Figure(data=go.Heatmap(
                z=z_data,
                x=[f"S{w}" for w in weeks],
                y=weekday_names,
                colorscale=colorscale,
                hovertemplate='%{text}<extra></extra>',
                text=hover_data,
                showscale=True,
                colorbar=dict(
                    title="Changements",
                    titleside="right",
                    tickmode="linear",
                    tick0=0,
                    dtick=max(1, max_count // 5)
                )
            ))

            # Mise en page
            fig.update_layout(
                title=dict(
                    text=f"📅 Calendrier des Changements - {year}",
                    x=0.5,
                    xanchor='center',
                    font=dict(size=20, weight='bold')
                ),
                xaxis=dict(
                    title="Semaines",
                    side="bottom",
                    tickangle=0,
                    showgrid=False
                ),
                yaxis=dict(
                    title="",
                    showgrid=False,
                    autorange="reversed"  # Lundi en haut
                ),
                height=400,
                plot_bgcolor='white',
                hoverlabel=dict(
                    bgcolor="white",
                    font_size=12,
                    font_family="Arial"
                )
            )

            logger.info(f"Calendrier heatmap généré pour l'année {year} avec {len(df)} changements")
            return fig

        except Exception as e:
            logger.error(f"Erreur lors de la génération du calendrier heatmap: {e}", exc_info=True)
            fig = go.Figure()
            fig.add_annotation(
                text=f"Erreur: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color='red')
            )
            return fig
