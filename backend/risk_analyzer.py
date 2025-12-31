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

    def generate_substance_timeline(self,
                                     cas_id: str,
                                     history_df: pd.DataFrame,
                                     aggregated_df: pd.DataFrame,
                                     event_type_filter: str = None) -> go.Figure:
        """
        Génère une timeline interactive pour retracer l'historique complet d'une substance

        Args:
            cas_id: CAS ID de la substance
            history_df: DataFrame de l'historique des changements
            aggregated_df: DataFrame des données agrégées
            event_type_filter: Filtrer par type d'événement (optionnel)

        Returns:
            Figure plotly avec la timeline interactive
        """
        try:
            # Récupérer le nom de la substance
            substance_data = aggregated_df[aggregated_df['cas_id'] == cas_id]
            if substance_data.empty:
                cas_name = cas_id
            else:
                cas_name = substance_data.iloc[0]['cas_name']

            # Gérer le cas d'un historique vide
            if history_df.empty:
                logger.warning(f"Historique vide pour {cas_id}")
                fig = go.Figure()
                fig.add_annotation(
                    text=f"Aucun historique disponible pour {cas_name}",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=16)
                )
                return fig

            # Filtrer l'historique pour cette substance
            substance_history = history_df[history_df['cas_id'] == cas_id].copy()

            if substance_history.empty:
                logger.warning(f"Aucun historique trouvé pour {cas_id}")
                fig = go.Figure()
                fig.add_annotation(
                    text=f"Aucun événement enregistré pour {cas_name}",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=16)
                )
                return fig

            # Convertir timestamp en datetime
            substance_history['timestamp'] = pd.to_datetime(substance_history['timestamp'])

            # Appliquer le filtre par type d'événement
            if event_type_filter and event_type_filter != "Tous":
                substance_history = substance_history[substance_history['change_type'] == event_type_filter]

            if substance_history.empty:
                fig = go.Figure()
                fig.add_annotation(
                    text=f"Aucun événement de type '{event_type_filter}' pour {cas_name}",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=14)
                )
                return fig

            # Trier par date
            substance_history = substance_history.sort_values('timestamp')

            # Définir les couleurs et symboles par type d'événement
            event_colors = {
                'insertion': '#2ecc71',      # Vert
                'suppression': '#e74c3c',    # Rouge
                'modification': '#f39c12'    # Orange
            }

            event_symbols = {
                'insertion': 'circle',
                'suppression': 'x',
                'modification': 'diamond'
            }

            event_labels = {
                'insertion': '✅ Insertion',
                'suppression': '❌ Suppression',
                'modification': '✏️ Modification'
            }

            # Créer la figure
            fig = go.Figure()

            # Ajouter les événements par type
            for event_type in ['insertion', 'suppression', 'modification']:
                events = substance_history[substance_history['change_type'] == event_type]

                if not events.empty:
                    # Créer les tooltips
                    hover_texts = []
                    for idx, row in events.iterrows():
                        hover_text = f"<b>{row['timestamp'].strftime('%Y-%m-%d %H:%M')}</b><br>"
                        hover_text += f"Type: {event_labels[event_type]}<br>"
                        hover_text += f"Liste: {row['source_list']}<br>"
                        if 'modified_fields' in row and pd.notna(row['modified_fields']) and row['modified_fields']:
                            hover_text += f"Champs modifiés: {row['modified_fields']}"
                        hover_texts.append(hover_text)

                    # Ajouter la trace
                    fig.add_trace(go.Scatter(
                        x=events['timestamp'],
                        y=[1] * len(events),  # Tous sur la même ligne
                        mode='markers+text',
                        marker=dict(
                            size=15,
                            color=event_colors[event_type],
                            symbol=event_symbols[event_type],
                            line=dict(width=2, color='white')
                        ),
                        name=event_labels[event_type],
                        text=[event_labels[event_type].split()[0]] * len(events),
                        textposition="top center",
                        textfont=dict(size=10),
                        hovertemplate='%{hovertext}<extra></extra>',
                        hovertext=hover_texts
                    ))

            # Ajouter une ligne de base
            if not substance_history.empty:
                min_date = substance_history['timestamp'].min()
                max_date = substance_history['timestamp'].max()

                fig.add_trace(go.Scatter(
                    x=[min_date, max_date],
                    y=[1, 1],
                    mode='lines',
                    line=dict(color='lightgray', width=2),
                    showlegend=False,
                    hoverinfo='skip'
                ))

            # Mise en page
            fig.update_layout(
                title=dict(
                    text=f"🕐 Timeline de {cas_name} ({cas_id})",
                    x=0.5,
                    xanchor='center',
                    font=dict(size=18, weight='bold')
                ),
                xaxis=dict(
                    title="Date",
                    showgrid=True,
                    gridcolor='lightgray',
                    tickformat='%Y-%m-%d',
                    type='date'
                ),
                yaxis=dict(
                    title="",
                    showticklabels=False,
                    showgrid=False,
                    range=[0.5, 1.5]
                ),
                height=400,
                hovermode='closest',
                plot_bgcolor='white',
                hoverlabel=dict(
                    bgcolor="white",
                    font_size=12,
                    font_family="Arial"
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center",
                    x=0.5
                )
            )

            logger.info(f"Timeline générée pour {cas_id} avec {len(substance_history)} événements")
            return fig

        except Exception as e:
            logger.error(f"Erreur lors de la génération de la timeline pour {cas_id}: {e}", exc_info=True)
            fig = go.Figure()
            fig.add_annotation(
                text=f"Erreur: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color='red')
            )
            return fig

    def generate_risk_score_evolution(self,
                                       cas_id: str,
                                       history_df: pd.DataFrame,
                                       aggregated_df: pd.DataFrame) -> go.Figure:
        """
        Génère un graphique d'évolution du score de risque dans le temps

        Args:
            cas_id: CAS ID de la substance
            history_df: DataFrame de l'historique des changements
            aggregated_df: DataFrame des données agrégées

        Returns:
            Figure plotly avec l'évolution du score
        """
        try:
            # Récupérer le nom de la substance
            substance_data = aggregated_df[aggregated_df['cas_id'] == cas_id]
            if substance_data.empty:
                cas_name = cas_id
            else:
                cas_name = substance_data.iloc[0]['cas_name']

            # Filtrer l'historique pour cette substance
            substance_history = history_df[history_df['cas_id'] == cas_id].copy()

            if substance_history.empty:
                fig = go.Figure()
                fig.add_annotation(
                    text=f"Aucun historique pour calculer l'évolution du score",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=14)
                )
                return fig

            # Convertir timestamp en datetime
            substance_history['timestamp'] = pd.to_datetime(substance_history['timestamp'])
            substance_history = substance_history.sort_values('timestamp')

            # Calculer le score à chaque point dans le temps
            # Simulation: le score augmente avec les modifications, baisse avec suppressions
            scores = []
            dates = []
            base_score = 50  # Score de départ

            for idx, row in substance_history.iterrows():
                if row['change_type'] == 'insertion':
                    base_score += 10
                elif row['change_type'] == 'modification':
                    base_score += 5
                elif row['change_type'] == 'suppression':
                    base_score -= 15

                # Limiter entre 0 et 100
                base_score = max(0, min(100, base_score))

                scores.append(base_score)
                dates.append(row['timestamp'])

            # Créer la figure
            fig = go.Figure()

            # Ajouter la ligne de score
            fig.add_trace(go.Scatter(
                x=dates,
                y=scores,
                mode='lines+markers',
                name='Score de Risque',
                line=dict(color='#3498db', width=3),
                marker=dict(size=8, color='#3498db'),
                fill='tozeroy',
                fillcolor='rgba(52, 152, 219, 0.2)',
                hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Score: %{y:.0f}<extra></extra>'
            ))

            # Ajouter des zones de risque
            fig.add_hrect(y0=0, y1=25, fillcolor="green", opacity=0.1, line_width=0, annotation_text="Faible", annotation_position="right")
            fig.add_hrect(y0=25, y1=50, fillcolor="yellow", opacity=0.1, line_width=0, annotation_text="Moyen", annotation_position="right")
            fig.add_hrect(y0=50, y1=75, fillcolor="orange", opacity=0.1, line_width=0, annotation_text="Élevé", annotation_position="right")
            fig.add_hrect(y0=75, y1=100, fillcolor="red", opacity=0.1, line_width=0, annotation_text="Critique", annotation_position="right")

            # Mise en page
            fig.update_layout(
                title=dict(
                    text=f"📈 Évolution du Score de Risque - {cas_name}",
                    x=0.5,
                    xanchor='center',
                    font=dict(size=16, weight='bold')
                ),
                xaxis=dict(
                    title="Date",
                    showgrid=True,
                    gridcolor='lightgray',
                    tickformat='%Y-%m-%d'
                ),
                yaxis=dict(
                    title="Score de Risque",
                    showgrid=True,
                    gridcolor='lightgray',
                    range=[0, 100]
                ),
                height=350,
                plot_bgcolor='white',
                hovermode='x unified'
            )

            logger.info(f"Graphique d'évolution du score généré pour {cas_id}")
            return fig

        except Exception as e:
            logger.error(f"Erreur lors de la génération du graphique d'évolution pour {cas_id}: {e}", exc_info=True)
            fig = go.Figure()
            fig.add_annotation(
                text=f"Erreur: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color='red')
            )
            return fig

    def generate_network_graph(self,
                                aggregated_df: pd.DataFrame,
                                history_df: pd.DataFrame = None,
                                min_risk_score: float = 0,
                                selected_lists: List[str] = None,
                                graph_mode: str = "bipartite") -> go.Figure:
        """
        Génère un graphe de réseau interactif montrant les relations entre substances et listes

        Args:
            aggregated_df: DataFrame des données agrégées
            history_df: DataFrame de l'historique (optionnel, pour scores de risque)
            min_risk_score: Score de risque minimum pour filtrer (0-100)
            selected_lists: Listes sources à inclure (None = toutes)
            graph_mode: Mode de visualisation ("bipartite" ou "substances_only")

        Returns:
            Figure plotly avec le graphe de réseau
        """
        try:
            if aggregated_df.empty:
                logger.warning("DataFrame agrégé vide pour le graphe de réseau")
                fig = go.Figure()
                fig.add_annotation(
                    text="Aucune donnée disponible",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=16)
                )
                return fig

            # Copier le DataFrame pour éviter les modifications
            df = aggregated_df.copy()

            # Filtrer par listes sélectionnées
            if selected_lists:
                df = df[df['source_list'].isin(selected_lists)]

            if df.empty:
                fig = go.Figure()
                fig.add_annotation(
                    text="Aucune donnée après filtrage",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=14)
                )
                return fig

            # Calculer les scores de risque pour chaque substance
            substance_scores = {}
            if history_df is not None and not history_df.empty:
                unique_cas_ids = df['cas_id'].unique()
                for cas_id in unique_cas_ids:
                    score_data = self.calculate_risk_score(cas_id, df, history_df)
                    substance_scores[cas_id] = score_data['total_score']
            else:
                # Scores par défaut si pas d'historique
                for cas_id in df['cas_id'].unique():
                    substance_scores[cas_id] = 50

            # Filtrer par score de risque
            filtered_cas_ids = [cas_id for cas_id, score in substance_scores.items() if score >= min_risk_score]
            df = df[df['cas_id'].isin(filtered_cas_ids)]

            if df.empty:
                fig = go.Figure()
                fig.add_annotation(
                    text=f"Aucune substance avec un score ≥ {min_risk_score}",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=14)
                )
                return fig

            # Créer le graphe selon le mode
            if graph_mode == "bipartite":
                fig = self._create_bipartite_graph(df, substance_scores)
            else:  # substances_only
                fig = self._create_substances_only_graph(df, substance_scores)

            logger.info(f"Graphe de réseau généré en mode {graph_mode} avec {len(filtered_cas_ids)} substances")
            return fig

        except Exception as e:
            logger.error(f"Erreur lors de la génération du graphe de réseau: {e}", exc_info=True)
            fig = go.Figure()
            fig.add_annotation(
                text=f"Erreur: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color='red')
            )
            return fig

    def _create_bipartite_graph(self, df: pd.DataFrame, substance_scores: Dict) -> go.Figure:
        """Crée un graphe bipartite substances-listes"""
        import math

        # Obtenir les substances et listes uniques
        substances = df[['cas_id', 'cas_name']].drop_duplicates()
        lists = df['source_list'].unique()

        # Positions des nœuds (layout circulaire)
        # Substances à gauche, listes à droite
        substance_positions = {}
        list_positions = {}

        num_substances = len(substances)
        num_lists = len(lists)

        # Substances sur un demi-cercle à gauche
        for i, (_, row) in enumerate(substances.iterrows()):
            angle = math.pi * (i / max(num_substances - 1, 1)) + math.pi/2
            x = -1 + 0.3 * math.cos(angle)
            y = 0.5 * math.sin(angle)
            substance_positions[row['cas_id']] = (x, y)

        # Listes sur un demi-cercle à droite
        for i, list_name in enumerate(lists):
            angle = math.pi * (i / max(num_lists - 1, 1)) + math.pi/2
            x = 1 - 0.3 * math.cos(angle)
            y = 0.5 * math.sin(angle)
            list_positions[list_name] = (x, y)

        # Créer les liens (edges)
        edge_x = []
        edge_y = []

        for _, row in df.iterrows():
            cas_id = row['cas_id']
            list_name = row['source_list']

            x0, y0 = substance_positions[cas_id]
            x1, y1 = list_positions[list_name]

            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        # Créer la figure
        fig = go.Figure()

        # Ajouter les liens
        fig.add_trace(go.Scatter(
            x=edge_x, y=edge_y,
            mode='lines',
            line=dict(width=0.5, color='lightgray'),
            hoverinfo='none',
            showlegend=False
        ))

        # Ajouter les nœuds substances
        substance_x = []
        substance_y = []
        substance_text = []
        substance_colors = []
        substance_sizes = []

        for _, row in substances.iterrows():
            cas_id = row['cas_id']
            x, y = substance_positions[cas_id]
            substance_x.append(x)
            substance_y.append(y)

            score = substance_scores.get(cas_id, 50)
            level, badge = self._get_risk_level(score)

            substance_text.append(
                f"<b>{row['cas_name']}</b><br>"
                f"CAS: {cas_id}<br>"
                f"Score: {score:.1f}<br>"
                f"Niveau: {badge} {level}"
            )

            # Couleur selon le niveau de risque
            color_map = {
                'Faible': '#2ecc71',
                'Moyen': '#f39c12',
                'Élevé': '#e67e22',
                'Critique': '#e74c3c'
            }
            substance_colors.append(color_map.get(level, '#95a5a6'))

            # Taille proportionnelle au score (10-40)
            substance_sizes.append(10 + (score / 100) * 30)

        fig.add_trace(go.Scatter(
            x=substance_x, y=substance_y,
            mode='markers',
            marker=dict(
                size=substance_sizes,
                color=substance_colors,
                line=dict(width=2, color='white'),
                symbol='circle'
            ),
            text=substance_text,
            hovertemplate='%{text}<extra></extra>',
            name='Substances'
        ))

        # Ajouter les nœuds listes
        list_x = []
        list_y = []
        list_text = []
        list_sizes = []

        list_colors = {
            'testa': '#3498db',
            'testb': '#9b59b6',
            'testc': '#e67e22',
            'testd': '#1abc9c'
        }

        for list_name in lists:
            x, y = list_positions[list_name]
            list_x.append(x)
            list_y.append(y)

            # Compter le nombre de substances dans cette liste
            count = len(df[df['source_list'] == list_name]['cas_id'].unique())

            list_text.append(
                f"<b>Liste: {list_name}</b><br>"
                f"Substances: {count}"
            )

            # Taille proportionnelle au nombre de substances (15-50)
            list_sizes.append(15 + min(count * 3, 35))

        fig.add_trace(go.Scatter(
            x=list_x, y=list_y,
            mode='markers',
            marker=dict(
                size=list_sizes,
                color=[list_colors.get(l, '#95a5a6') for l in lists],
                line=dict(width=2, color='white'),
                symbol='square'
            ),
            text=list_text,
            hovertemplate='%{text}<extra></extra>',
            name='Listes ECHA'
        ))

        # Mise en page
        fig.update_layout(
            title=dict(
                text="🕸️ Graphe de Réseau Substances-Listes",
                x=0.5,
                xanchor='center',
                font=dict(size=18, weight='bold')
            ),
            showlegend=True,
            hovermode='closest',
            height=700,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            )
        )

        return fig

    def _create_substances_only_graph(self, df: pd.DataFrame, substance_scores: Dict) -> go.Figure:
        """Crée un graphe montrant uniquement les substances (co-occurrence dans listes)"""
        import math

        # Obtenir les substances uniques
        substances = df[['cas_id', 'cas_name']].drop_duplicates()

        # Calculer la matrice de co-occurrence (substances partageant des listes)
        substance_lists = {}
        for _, row in df.iterrows():
            cas_id = row['cas_id']
            list_name = row['source_list']
            if cas_id not in substance_lists:
                substance_lists[cas_id] = set()
            substance_lists[cas_id].add(list_name)

        # Positions des nœuds (layout circulaire)
        positions = {}
        num_substances = len(substances)

        for i, (_, row) in enumerate(substances.iterrows()):
            angle = 2 * math.pi * i / num_substances
            x = math.cos(angle)
            y = math.sin(angle)
            positions[row['cas_id']] = (x, y)

        # Créer les liens (substances partageant au moins une liste)
        edge_x = []
        edge_y = []
        edge_weights = []

        cas_ids = list(substance_lists.keys())
        for i, cas_id1 in enumerate(cas_ids):
            for cas_id2 in cas_ids[i+1:]:
                # Nombre de listes partagées
                shared = len(substance_lists[cas_id1] & substance_lists[cas_id2])
                if shared > 0:
                    x0, y0 = positions[cas_id1]
                    x1, y1 = positions[cas_id2]

                    edge_x.extend([x0, x1, None])
                    edge_y.extend([y0, y1, None])
                    edge_weights.append(shared)

        # Créer la figure
        fig = go.Figure()

        # Ajouter les liens
        if edge_x:
            fig.add_trace(go.Scatter(
                x=edge_x, y=edge_y,
                mode='lines',
                line=dict(width=1, color='lightgray'),
                hoverinfo='none',
                showlegend=False
            ))

        # Ajouter les nœuds substances
        substance_x = []
        substance_y = []
        substance_text = []
        substance_colors = []
        substance_sizes = []

        for _, row in substances.iterrows():
            cas_id = row['cas_id']
            x, y = positions[cas_id]
            substance_x.append(x)
            substance_y.append(y)

            score = substance_scores.get(cas_id, 50)
            level, badge = self._get_risk_level(score)

            lists_str = ", ".join(sorted(substance_lists.get(cas_id, [])))

            substance_text.append(
                f"<b>{row['cas_name']}</b><br>"
                f"CAS: {cas_id}<br>"
                f"Score: {score:.1f}<br>"
                f"Niveau: {badge} {level}<br>"
                f"Listes: {lists_str}"
            )

            # Couleur selon le niveau de risque
            color_map = {
                'Faible': '#2ecc71',
                'Moyen': '#f39c12',
                'Élevé': '#e67e22',
                'Critique': '#e74c3c'
            }
            substance_colors.append(color_map.get(level, '#95a5a6'))

            # Taille proportionnelle au nombre de listes
            num_lists = len(substance_lists.get(cas_id, []))
            substance_sizes.append(10 + num_lists * 8)

        fig.add_trace(go.Scatter(
            x=substance_x, y=substance_y,
            mode='markers+text',
            marker=dict(
                size=substance_sizes,
                color=substance_colors,
                line=dict(width=2, color='white'),
                symbol='circle'
            ),
            text=substance_text,
            hovertemplate='%{text}<extra></extra>',
            name='Substances',
            showlegend=False
        ))

        # Mise en page
        fig.update_layout(
            title=dict(
                text="🕸️ Graphe de Réseau des Substances (Co-occurrence)",
                x=0.5,
                xanchor='center',
                font=dict(size=18, weight='bold')
            ),
            showlegend=False,
            hovermode='closest',
            height=700,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white'
        )

        return fig

    def calculate_dashboard_metrics(self,
                                      aggregated_df: pd.DataFrame,
                                      history_df: pd.DataFrame) -> Dict:
        """
        Calcule toutes les métriques nécessaires pour le dashboard analytique

        Args:
            aggregated_df: DataFrame des données agrégées
            history_df: DataFrame de l'historique des changements

        Returns:
            Dictionnaire avec toutes les métriques du dashboard
        """
        try:
            metrics = {}

            # Métriques de base
            metrics['total_substances'] = aggregated_df['cas_id'].nunique() if not aggregated_df.empty else 0
            metrics['total_lists'] = aggregated_df['source_list'].nunique() if not aggregated_df.empty else 0
            metrics['total_connections'] = len(aggregated_df) if not aggregated_df.empty else 0

            # Métriques de changements
            if not history_df.empty:
                metrics['total_changes'] = len(history_df)

                # Changements par type
                metrics['insertions'] = len(history_df[history_df['change_type'] == 'insertion'])
                metrics['deletions'] = len(history_df[history_df['change_type'] == 'suppression'])
                metrics['modifications'] = len(history_df[history_df['change_type'] == 'modification'])

                # Changements récents (7 derniers jours)
                history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
                now = datetime.now()
                seven_days_ago = now - timedelta(days=7)
                recent_changes = history_df[history_df['timestamp'] >= seven_days_ago]
                metrics['changes_7d'] = len(recent_changes)

                # Changements 30 jours
                thirty_days_ago = now - timedelta(days=30)
                changes_30d = history_df[history_df['timestamp'] >= thirty_days_ago]
                metrics['changes_30d'] = len(changes_30d)

                # Période précédente pour comparaison (7j précédents)
                fourteen_days_ago = now - timedelta(days=14)
                prev_period = history_df[(history_df['timestamp'] >= fourteen_days_ago) &
                                        (history_df['timestamp'] < seven_days_ago)]
                metrics['changes_prev_7d'] = len(prev_period)

                # Tendance
                if metrics['changes_prev_7d'] > 0:
                    metrics['trend_7d'] = ((metrics['changes_7d'] - metrics['changes_prev_7d']) /
                                          metrics['changes_prev_7d']) * 100
                else:
                    metrics['trend_7d'] = 100 if metrics['changes_7d'] > 0 else 0

            else:
                metrics['total_changes'] = 0
                metrics['insertions'] = 0
                metrics['deletions'] = 0
                metrics['modifications'] = 0
                metrics['changes_7d'] = 0
                metrics['changes_30d'] = 0
                metrics['changes_prev_7d'] = 0
                metrics['trend_7d'] = 0

            # Scores de risque
            if not aggregated_df.empty and not history_df.empty:
                scores = []
                risk_distribution = {'Faible': 0, 'Moyen': 0, 'Élevé': 0, 'Critique': 0}

                for cas_id in aggregated_df['cas_id'].unique():
                    score_data = self.calculate_risk_score(cas_id, aggregated_df, history_df)
                    scores.append(score_data['total_score'])
                    risk_distribution[score_data['level']] += 1

                metrics['avg_risk_score'] = sum(scores) / len(scores) if scores else 0
                metrics['max_risk_score'] = max(scores) if scores else 0
                metrics['risk_distribution'] = risk_distribution

                # Top 5 substances critiques
                top_substances = []
                for cas_id in aggregated_df['cas_id'].unique():
                    score_data = self.calculate_risk_score(cas_id, aggregated_df, history_df)
                    substance_data = aggregated_df[aggregated_df['cas_id'] == cas_id].iloc[0]
                    top_substances.append({
                        'cas_id': cas_id,
                        'cas_name': substance_data['cas_name'],
                        'score': score_data['total_score'],
                        'level': score_data['level'],
                        'badge': score_data['badge']
                    })

                top_substances = sorted(top_substances, key=lambda x: x['score'], reverse=True)[:5]
                metrics['top_critical'] = top_substances

            else:
                metrics['avg_risk_score'] = 0
                metrics['max_risk_score'] = 0
                metrics['risk_distribution'] = {'Faible': 0, 'Moyen': 0, 'Élevé': 0, 'Critique': 0}
                metrics['top_critical'] = []

            # Health Score global (0-100)
            # Formule: pondération de plusieurs facteurs
            health_components = []

            # 1. Moins de changements récents = mieux (inverse)
            if metrics['total_substances'] > 0:
                change_ratio = min(metrics['changes_7d'] / metrics['total_substances'], 1.0)
                health_components.append((1 - change_ratio) * 100)
            else:
                health_components.append(100)

            # 2. Score de risque moyen faible = mieux (inverse)
            health_components.append((100 - metrics['avg_risk_score']))

            # 3. Peu de suppressions = mieux
            if metrics['total_changes'] > 0:
                deletion_ratio = metrics['deletions'] / metrics['total_changes']
                health_components.append((1 - deletion_ratio) * 100)
            else:
                health_components.append(100)

            metrics['health_score'] = sum(health_components) / len(health_components) if health_components else 50

            # Répartition par liste
            if not aggregated_df.empty:
                list_distribution = aggregated_df.groupby('source_list')['cas_id'].nunique().to_dict()
                metrics['list_distribution'] = list_distribution
            else:
                metrics['list_distribution'] = {}

            logger.info("Métriques du dashboard calculées avec succès")
            return metrics

        except Exception as e:
            logger.error(f"Erreur lors du calcul des métriques dashboard: {e}", exc_info=True)
            # Retourner des métriques par défaut en cas d'erreur
            return {
                'total_substances': 0,
                'total_lists': 0,
                'total_connections': 0,
                'total_changes': 0,
                'insertions': 0,
                'deletions': 0,
                'modifications': 0,
                'changes_7d': 0,
                'changes_30d': 0,
                'changes_prev_7d': 0,
                'trend_7d': 0,
                'avg_risk_score': 0,
                'max_risk_score': 0,
                'risk_distribution': {'Faible': 0, 'Moyen': 0, 'Élevé': 0, 'Critique': 0},
                'top_critical': [],
                'health_score': 0,
                'list_distribution': {}
            }

    def generate_gauge_chart(self, value: float, title: str, max_value: float = 100) -> go.Figure:
        """
        Génère un graphique de type gauge (jauge) pour le dashboard

        Args:
            value: Valeur actuelle
            title: Titre de la jauge
            max_value: Valeur maximale de l'échelle

        Returns:
            Figure plotly avec la jauge
        """
        try:
            # Déterminer la couleur selon la valeur
            if value >= 75:
                color = "#2ecc71"  # Vert
            elif value >= 50:
                color = "#f39c12"  # Orange
            elif value >= 25:
                color = "#e67e22"  # Orange foncé
            else:
                color = "#e74c3c"  # Rouge

            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=value,
                title={'text': title, 'font': {'size': 16}},
                number={'suffix': "", 'font': {'size': 24}},
                gauge={
                    'axis': {'range': [None, max_value], 'tickwidth': 1},
                    'bar': {'color': color},
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "gray",
                    'steps': [
                        {'range': [0, 25], 'color': '#ffebee'},
                        {'range': [25, 50], 'color': '#fff3e0'},
                        {'range': [50, 75], 'color': '#fff9c4'},
                        {'range': [75, max_value], 'color': '#e8f5e9'}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': max_value * 0.9
                    }
                }
            ))

            fig.update_layout(
                height=250,
                margin=dict(l=20, r=20, t=40, b=20),
                paper_bgcolor="white",
                font={'color': "darkblue", 'family': "Arial"}
            )

            return fig

        except Exception as e:
            logger.error(f"Erreur lors de la génération de la jauge: {e}", exc_info=True)
            return go.Figure()
