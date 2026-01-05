"""
Composants de métriques réutilisables
Contient des fonctions pour afficher des KPIs et métriques dans l'application
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta


# =============================================================================
# MÉTRIQUES SIMPLES
# =============================================================================

def display_metric(
    label: str,
    value: Union[int, float, str],
    delta: Optional[Union[int, float, str]] = None,
    delta_color: str = "normal",
    help_text: Optional[str] = None,
    prefix: str = "",
    suffix: str = ""
):
    """
    Affiche une métrique simple avec Streamlit
    
    Args:
        label: Label de la métrique
        value: Valeur à afficher
        delta: Changement par rapport à une référence
        delta_color: Couleur du delta ('normal', 'inverse', 'off')
        help_text: Texte d'aide au survol
        prefix: Préfixe à ajouter à la valeur (ex: "$")
        suffix: Suffixe à ajouter à la valeur (ex: "%")
    
    Example:
        >>> display_metric("Total Substances", 1234, delta="+15%", help_text="Depuis hier")
    """
    formatted_value = f"{prefix}{value}{suffix}"
    st.metric(
        label=label,
        value=formatted_value,
        delta=delta,
        delta_color=delta_color,
        help=help_text
    )


def display_metrics_row(
    metrics: List[Dict],
    columns: Optional[int] = None
):
    """
    Affiche plusieurs métriques sur une ligne
    
    Args:
        metrics: Liste de dict avec les clés 'label', 'value', 'delta', etc.
        columns: Nombre de colonnes (None = auto)
    
    Example:
        >>> metrics = [
        ...     {'label': 'Total', 'value': 100, 'delta': '+10'},
        ...     {'label': 'Actifs', 'value': 80, 'delta': '+5'},
        ...     {'label': 'Inactifs', 'value': 20, 'delta': '+5'}
        ... ]
        >>> display_metrics_row(metrics)
    """
    if columns is None:
        columns = len(metrics)
    
    cols = st.columns(columns)
    
    for idx, metric in enumerate(metrics):
        with cols[idx % columns]:
            display_metric(
                label=metric.get('label', ''),
                value=metric.get('value', 0),
                delta=metric.get('delta'),
                delta_color=metric.get('delta_color', 'normal'),
                help_text=metric.get('help'),
                prefix=metric.get('prefix', ''),
                suffix=metric.get('suffix', '')
            )


# =============================================================================
# MÉTRIQUES AVEC ICÔNES
# =============================================================================

def display_metric_with_icon(
    label: str,
    value: Union[int, float, str],
    icon: str,
    color: str = "#1f77b4",
    delta: Optional[str] = None
):
    """
    Affiche une métrique avec une icône emoji
    
    Args:
        label: Label de la métrique
        value: Valeur à afficher
        icon: Emoji à afficher
        color: Couleur de fond (hex)
        delta: Variation optionnelle
    
    Example:
        >>> display_metric_with_icon("Substances", 1234, "🧪", "#3498db", "+10%")
    """
    st.markdown(f"""
        <div style="
            background-color: {color}20;
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid {color};
        ">
            <div style="font-size: 40px; margin-bottom: 5px;">{icon}</div>
            <div style="font-size: 14px; color: #666;">{label}</div>
            <div style="font-size: 28px; font-weight: bold; margin: 5px 0;">{value}</div>
            {f'<div style="font-size: 12px; color: #2ecc71;">{delta}</div>' if delta else ''}
        </div>
    """, unsafe_allow_html=True)


def display_icon_metrics_grid(
    metrics: List[Dict],
    columns: int = 4
):
    """
    Affiche une grille de métriques avec icônes
    
    Args:
        metrics: Liste de dict avec 'label', 'value', 'icon', 'color', 'delta'
        columns: Nombre de colonnes
    
    Example:
        >>> metrics = [
        ...     {'label': 'Total', 'value': '1,234', 'icon': '📊', 'color': '#3498db'},
        ...     {'label': 'Nouveaux', 'value': '156', 'icon': '🆕', 'color': '#2ecc71', 'delta': '+12%'},
        ...     {'label': 'Modifiés', 'value': '89', 'icon': '✏️', 'color': '#f39c12'},
        ...     {'label': 'Critiques', 'value': '23', 'icon': '⚠️', 'color': '#e74c3c'}
        ... ]
        >>> display_icon_metrics_grid(metrics, columns=4)
    """
    cols = st.columns(columns)
    
    for idx, metric in enumerate(metrics):
        with cols[idx % columns]:
            display_metric_with_icon(
                label=metric.get('label', ''),
                value=metric.get('value', ''),
                icon=metric.get('icon', '📊'),
                color=metric.get('color', '#1f77b4'),
                delta=metric.get('delta')
            )


# =============================================================================
# MÉTRIQUES DE COMPARAISON
# =============================================================================

def display_comparison_metric(
    label: str,
    current_value: Union[int, float],
    previous_value: Union[int, float],
    format_string: str = "{:.0f}",
    show_percentage: bool = True,
    inverse_colors: bool = False
):
    """
    Affiche une métrique avec comparaison automatique
    
    Args:
        label: Label de la métrique
        current_value: Valeur actuelle
        previous_value: Valeur précédente
        format_string: Format d'affichage des nombres
        show_percentage: Afficher le pourcentage de variation
        inverse_colors: Inverser les couleurs (baisse = bon)
    
    Example:
        >>> display_comparison_metric("Ventes", 1500, 1200, "${:,.0f}")
    """
    # Calculer la variation
    if previous_value != 0:
        change = current_value - previous_value
        change_pct = (change / previous_value) * 100
        
        if show_percentage:
            delta_text = f"{change_pct:+.1f}%"
        else:
            delta_text = f"{change:+.0f}"
    else:
        delta_text = "N/A"
    
    # Déterminer la couleur
    if inverse_colors:
        delta_color = "inverse"
    else:
        delta_color = "normal"
    
    formatted_value = format_string.format(current_value)
    
    st.metric(
        label=label,
        value=formatted_value,
        delta=delta_text,
        delta_color=delta_color
    )


def display_period_comparison(
    label: str,
    current_period: Dict,
    previous_period: Dict,
    metric_key: str = "value"
):
    """
    Compare deux périodes
    
    Args:
        label: Label de la métrique
        current_period: Dict avec les données de la période actuelle
        previous_period: Dict avec les données de la période précédente
        metric_key: Clé dans les dicts contenant la valeur
    
    Example:
        >>> current = {'value': 1500, 'label': 'Cette semaine'}
        >>> previous = {'value': 1200, 'label': 'Semaine dernière'}
        >>> display_period_comparison("Ventes", current, previous)
    """
    current_val = current_period.get(metric_key, 0)
    previous_val = previous_period.get(metric_key, 0)
    
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col1:
        st.metric(
            label=current_period.get('label', 'Période actuelle'),
            value=current_val
        )
    
    with col2:
        if previous_val != 0:
            change_pct = ((current_val - previous_val) / previous_val) * 100
            st.markdown(f"""
                <div style="text-align: center; padding-top: 30px;">
                    <div style="font-size: 24px; font-weight: bold; 
                                color: {'#2ecc71' if change_pct > 0 else '#e74c3c'};">
                        {change_pct:+.1f}%
                    </div>
                </div>
            """, unsafe_allow_html=True)
    
    with col3:
        st.metric(
            label=previous_period.get('label', 'Période précédente'),
            value=previous_val
        )


# =============================================================================
# MÉTRIQUES STATISTIQUES
# =============================================================================

def display_stats_summary(
    data: pd.Series,
    title: str = "Statistiques",
    show_quartiles: bool = True
):
    """
    Affiche un résumé statistique d'une série
    
    Args:
        data: Série de données
        title: Titre de la section
        show_quartiles: Afficher les quartiles
    
    Example:
        >>> display_stats_summary(df['risk_score'], "Scores de Risque")
    """
    st.subheader(title)
    
    stats = [
        {'label': 'Moyenne', 'value': f"{data.mean():.2f}"},
        {'label': 'Médiane', 'value': f"{data.median():.2f}"},
        {'label': 'Min', 'value': f"{data.min():.2f}"},
        {'label': 'Max', 'value': f"{data.max():.2f}"}
    ]
    
    if show_quartiles:
        stats.extend([
            {'label': 'Q1 (25%)', 'value': f"{data.quantile(0.25):.2f}"},
            {'label': 'Q3 (75%)', 'value': f"{data.quantile(0.75):.2f}"}
        ])
    
    display_metrics_row(stats)


def display_distribution_metrics(
    data: pd.DataFrame,
    column: str,
    categories: List[str],
    title: str = "Répartition"
):
    """
    Affiche la distribution d'une colonne par catégories
    
    Args:
        data: DataFrame
        column: Colonne à analyser
        categories: Liste des catégories à compter
        title: Titre de la section
    
    Example:
        >>> categories = ['Faible', 'Moyen', 'Élevé', 'Critique']
        >>> display_distribution_metrics(df, 'risk_level', categories)
    """
    st.subheader(title)
    
    metrics = []
    for cat in categories:
        count = len(data[data[column] == cat])
        percentage = (count / len(data) * 100) if len(data) > 0 else 0
        
        metrics.append({
            'label': cat,
            'value': count,
            'delta': f"{percentage:.1f}%"
        })
    
    display_metrics_row(metrics)


# =============================================================================
# CARTES DE SCORE
# =============================================================================

def display_score_card(
    score: float,
    max_score: float = 100,
    title: str = "Score",
    thresholds: Optional[Dict[str, Tuple[float, str]]] = None,
    show_bar: bool = True
):
    """
    Affiche une carte de score avec barre de progression
    
    Args:
        score: Score actuel
        max_score: Score maximum
        title: Titre de la carte
        thresholds: Seuils avec format {'label': (min_value, color)}
        show_bar: Afficher la barre de progression
    
    Example:
        >>> thresholds = {
        ...     'Faible': (0, '#2ecc71'),
        ...     'Moyen': (25, '#f39c12'),
        ...     'Élevé': (50, '#e67e22'),
        ...     'Critique': (75, '#e74c3c')
        ... }
        >>> display_score_card(67, 100, "Score de Risque", thresholds)
    """
    if thresholds is None:
        thresholds = {
            'Faible': (0, '#2ecc71'),
            'Moyen': (25, '#f39c12'),
            'Élevé': (50, '#e67e22'),
            'Critique': (75, '#e74c3c')
        }
    
    # Déterminer le niveau et la couleur
    level = "Inconnu"
    color = "#1f77b4"
    
    sorted_thresholds = sorted(thresholds.items(), key=lambda x: x[1][0], reverse=True)
    for label, (threshold, threshold_color) in sorted_thresholds:
        if score >= threshold:
            level = label
            color = threshold_color
            break
    
    percentage = (score / max_score) * 100
    
    st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {color}10 0%, {color}30 100%);
            padding: 20px;
            border-radius: 15px;
            border: 2px solid {color};
        ">
            <div style="font-size: 16px; color: #666; margin-bottom: 5px;">{title}</div>
            <div style="font-size: 48px; font-weight: bold; color: {color}; margin: 10px 0;">
                {score:.1f}
            </div>
            <div style="font-size: 18px; color: {color}; margin-bottom: 10px;">
                {level}
            </div>
            {f'''
            <div style="background-color: #e0e0e0; height: 20px; border-radius: 10px; overflow: hidden;">
                <div style="
                    width: {percentage}%;
                    height: 100%;
                    background-color: {color};
                    transition: width 0.5s ease;
                "></div>
            </div>
            ''' if show_bar else ''}
        </div>
    """, unsafe_allow_html=True)


# =============================================================================
# TABLEAUX DE BORD COMPACTS
# =============================================================================

def display_kpi_dashboard(
    kpis: Dict[str, Dict],
    title: str = "Tableau de Bord",
    columns: int = 4
):
    """
    Affiche un tableau de bord complet de KPIs
    
    Args:
        kpis: Dict de KPIs avec format:
            {
                'kpi_name': {
                    'value': 123,
                    'delta': '+10%',
                    'icon': '📊',
                    'color': '#3498db',
                    'help': 'Description'
                }
            }
        title: Titre du tableau de bord
        columns: Nombre de colonnes
    
    Example:
        >>> kpis = {
        ...     'total': {'value': 1234, 'icon': '📊', 'color': '#3498db'},
        ...     'new': {'value': 156, 'delta': '+12%', 'icon': '🆕', 'color': '#2ecc71'},
        ...     'modified': {'value': 89, 'icon': '✏️', 'color': '#f39c12'},
        ...     'critical': {'value': 23, 'icon': '⚠️', 'color': '#e74c3c'}
        ... }
        >>> display_kpi_dashboard(kpis, "KPIs Principaux", columns=4)
    """
    if title:
        st.subheader(title)
    
    metrics = []
    for name, kpi_data in kpis.items():
        metrics.append({
            'label': kpi_data.get('label', name.title()),
            'value': kpi_data.get('value', 0),
            'icon': kpi_data.get('icon', '📊'),
            'color': kpi_data.get('color', '#1f77b4'),
            'delta': kpi_data.get('delta')
        })
    
    display_icon_metrics_grid(metrics, columns=columns)


# =============================================================================
# MÉTRIQUES DE PROGRESSION
# =============================================================================

def display_progress_metric(
    label: str,
    current: Union[int, float],
    target: Union[int, float],
    format_string: str = "{:.0f}",
    show_percentage: bool = True
):
    """
    Affiche une métrique avec progression vers un objectif
    
    Args:
        label: Label de la métrique
        current: Valeur actuelle
        target: Valeur cible
        format_string: Format d'affichage
        show_percentage: Afficher le pourcentage
    
    Example:
        >>> display_progress_metric("Objectif Mensuel", 750, 1000, "${:,.0f}")
    """
    percentage = (current / target * 100) if target > 0 else 0
    remaining = target - current
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"**{label}**")
        st.progress(min(percentage / 100, 1.0))
        
        if show_percentage:
            st.caption(f"{percentage:.1f}% de l'objectif atteint")
    
    with col2:
        current_formatted = format_string.format(current)
        target_formatted = format_string.format(target)
        
        st.metric(
            label="Actuel",
            value=current_formatted,
            delta=f"{remaining:+.0f} pour objectif"
        )


def display_multi_progress(
    items: List[Dict],
    title: str = "Progression"
):
    """
    Affiche plusieurs barres de progression
    
    Args:
        items: Liste de dict avec 'label', 'current', 'target', 'color'
        title: Titre de la section
    
    Example:
        >>> items = [
        ...     {'label': 'Objectif A', 'current': 75, 'target': 100, 'color': '#2ecc71'},
        ...     {'label': 'Objectif B', 'current': 120, 'target': 100, 'color': '#3498db'},
        ...     {'label': 'Objectif C', 'current': 45, 'target': 100, 'color': '#e74c3c'}
        ... ]
        >>> display_multi_progress(items, "Objectifs du Mois")
    """
    st.subheader(title)
    
    for item in items:
        label = item.get('label', '')
        current = item.get('current', 0)
        target = item.get('target', 100)
        color = item.get('color', '#1f77b4')
        
        percentage = (current / target * 100) if target > 0 else 0
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"**{label}**")
            st.markdown(f"""
                <div style="background-color: #e0e0e0; height: 25px; border-radius: 5px; overflow: hidden;">
                    <div style="
                        width: {min(percentage, 100)}%;
                        height: 100%;
                        background-color: {color};
                        transition: width 0.5s ease;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: white;
                        font-size: 12px;
                        font-weight: bold;
                    ">
                        {percentage:.0f}%
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.metric("Actuel", current)
        
        with col3:
            st.metric("Cible", target)
        
        st.markdown("---")


# =============================================================================
# UTILITAIRES
# =============================================================================

def format_number(
    value: Union[int, float],
    decimals: int = 0,
    thousands_sep: str = " ",
    decimal_sep: str = ","
) -> str:
    """
    Formate un nombre avec séparateurs
    
    Args:
        value: Nombre à formater
        decimals: Nombre de décimales
        thousands_sep: Séparateur des milliers
        decimal_sep: Séparateur décimal
    
    Returns:
        Nombre formaté
    
    Example:
        >>> format_number(1234567.89, decimals=2)
        '1 234 567,89'
    """
    if decimals == 0:
        formatted = f"{int(value):,}".replace(",", thousands_sep)
    else:
        formatted = f"{value:,.{decimals}f}"
        formatted = formatted.replace(",", "TEMP")
        formatted = formatted.replace(".", decimal_sep)
        formatted = formatted.replace("TEMP", thousands_sep)
    
    return formatted


def calculate_trend(
    current: Union[int, float],
    previous: Union[int, float]
) -> Tuple[float, str, str]:
    """
    Calcule la tendance entre deux valeurs
    
    Args:
        current: Valeur actuelle
        previous: Valeur précédente
    
    Returns:
        Tuple (pourcentage, icône, couleur)
    
    Example:
        >>> pct, icon, color = calculate_trend(120, 100)
        >>> # (20.0, '↗', '#2ecc71')
    """
    if previous == 0:
        return 0.0, "→", "#95a5a6"
    
    change_pct = ((current - previous) / previous) * 100
    
    if change_pct > 0:
        return change_pct, "↗", "#2ecc71"
    elif change_pct < 0:
        return change_pct, "↘", "#e74c3c"
    else:
        return 0.0, "→", "#95a5a6"