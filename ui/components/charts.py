"""
Composants de graphiques réutilisables
Contient des fonctions pour créer des visualisations standard dans l'application
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime


# =============================================================================
# GRAPHIQUES EN BARRES
# =============================================================================

def create_bar_chart(
    data: pd.DataFrame,
    x_column: str,
    y_column: str,
    title: str = "",
    x_label: str = "",
    y_label: str = "",
    color: str = "#1f77b4",
    horizontal: bool = False,
    show_values: bool = True,
    height: int = 400
) -> go.Figure:
    """
    Crée un graphique en barres simple
    
    Args:
        data: DataFrame contenant les données
        x_column: Nom de la colonne pour l'axe X
        y_column: Nom de la colonne pour l'axe Y
        title: Titre du graphique
        x_label: Label de l'axe X
        y_label: Label de l'axe Y
        color: Couleur des barres
        horizontal: Si True, barres horizontales
        show_values: Afficher les valeurs sur les barres
        height: Hauteur du graphique en pixels
    
    Returns:
        Figure Plotly
    
    Example:
        >>> fig = create_bar_chart(df, 'source_list', 'count', 'Répartition par liste')
        >>> st.plotly_chart(fig, use_container_width=True)
    """
    if horizontal:
        fig = go.Figure(data=[
            go.Bar(
                x=data[y_column],
                y=data[x_column],
                orientation='h',
                marker_color=color,
                text=data[y_column] if show_values else None,
                textposition='auto'
            )
        ])
        fig.update_layout(
            xaxis_title=y_label or y_column,
            yaxis_title=x_label or x_column
        )
    else:
        fig = go.Figure(data=[
            go.Bar(
                x=data[x_column],
                y=data[y_column],
                marker_color=color,
                text=data[y_column] if show_values else None,
                textposition='auto'
            )
        ])
        fig.update_layout(
            xaxis_title=x_label or x_column,
            yaxis_title=y_label or y_column
        )
    
    fig.update_layout(
        title=title,
        height=height,
        showlegend=False,
        template='plotly_white'
    )
    
    return fig


def create_grouped_bar_chart(
    data: pd.DataFrame,
    x_column: str,
    y_columns: List[str],
    title: str = "",
    colors: Optional[List[str]] = None,
    height: int = 400
) -> go.Figure:
    """
    Crée un graphique en barres groupées
    
    Args:
        data: DataFrame contenant les données
        x_column: Nom de la colonne pour l'axe X
        y_columns: Liste des colonnes pour les différentes séries
        title: Titre du graphique
        colors: Liste de couleurs pour chaque série
        height: Hauteur du graphique
    
    Returns:
        Figure Plotly
    """
    if colors is None:
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    fig = go.Figure()
    
    for idx, col in enumerate(y_columns):
        fig.add_trace(go.Bar(
            name=col,
            x=data[x_column],
            y=data[col],
            marker_color=colors[idx % len(colors)]
        ))
    
    fig.update_layout(
        title=title,
        barmode='group',
        height=height,
        template='plotly_white',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig


# =============================================================================
# GRAPHIQUES CIRCULAIRES
# =============================================================================

def create_pie_chart(
    data: pd.DataFrame,
    values_column: str,
    names_column: str,
    title: str = "",
    colors: Optional[List[str]] = None,
    hole: float = 0,
    show_legend: bool = True,
    height: int = 400
) -> go.Figure:
    """
    Crée un graphique circulaire (pie chart ou donut)
    
    Args:
        data: DataFrame contenant les données
        values_column: Colonne contenant les valeurs
        names_column: Colonne contenant les labels
        title: Titre du graphique
        colors: Liste de couleurs personnalisées
        hole: Taille du trou au centre (0 = pie, 0.4 = donut)
        show_legend: Afficher la légende
        height: Hauteur du graphique
    
    Returns:
        Figure Plotly
    
    Example:
        >>> # Pie chart standard
        >>> fig = create_pie_chart(df, 'count', 'category', 'Distribution')
        >>> 
        >>> # Donut chart
        >>> fig = create_pie_chart(df, 'count', 'category', 'Distribution', hole=0.4)
    """
    fig = go.Figure(data=[go.Pie(
        labels=data[names_column],
        values=data[values_column],
        hole=hole,
        marker=dict(colors=colors) if colors else None,
        textinfo='label+percent',
        textposition='outside'
    )])
    
    fig.update_layout(
        title=title,
        height=height,
        showlegend=show_legend,
        template='plotly_white'
    )
    
    if show_legend:
        fig.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            )
        )
    
    return fig


# =============================================================================
# GRAPHIQUES DE TENDANCES
# =============================================================================

def create_line_chart(
    data: pd.DataFrame,
    x_column: str,
    y_columns: Union[str, List[str]],
    title: str = "",
    x_label: str = "",
    y_label: str = "",
    colors: Optional[List[str]] = None,
    markers: bool = True,
    height: int = 400
) -> go.Figure:
    """
    Crée un graphique en ligne pour montrer les tendances
    
    Args:
        data: DataFrame contenant les données
        x_column: Colonne pour l'axe X (généralement temps)
        y_columns: Colonne(s) pour l'axe Y (str ou liste)
        title: Titre du graphique
        x_label: Label de l'axe X
        y_label: Label de l'axe Y
        colors: Couleurs pour chaque ligne
        markers: Afficher les marqueurs sur les points
        height: Hauteur du graphique
    
    Returns:
        Figure Plotly
    """
    if isinstance(y_columns, str):
        y_columns = [y_columns]
    
    if colors is None:
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    fig = go.Figure()
    
    for idx, col in enumerate(y_columns):
        mode = 'lines+markers' if markers else 'lines'
        fig.add_trace(go.Scatter(
            x=data[x_column],
            y=data[col],
            mode=mode,
            name=col,
            line=dict(color=colors[idx % len(colors)]),
            marker=dict(size=8)
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title=x_label or x_column,
        yaxis_title=y_label,
        height=height,
        template='plotly_white',
        hovermode='x unified'
    )
    
    return fig


def create_area_chart(
    data: pd.DataFrame,
    x_column: str,
    y_columns: Union[str, List[str]],
    title: str = "",
    stacked: bool = True,
    colors: Optional[List[str]] = None,
    height: int = 400
) -> go.Figure:
    """
    Crée un graphique en aires
    
    Args:
        data: DataFrame contenant les données
        x_column: Colonne pour l'axe X
        y_columns: Colonne(s) pour l'axe Y
        title: Titre du graphique
        stacked: Si True, aires empilées
        colors: Couleurs personnalisées
        height: Hauteur du graphique
    
    Returns:
        Figure Plotly
    """
    if isinstance(y_columns, str):
        y_columns = [y_columns]
    
    if colors is None:
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    fig = go.Figure()
    
    for idx, col in enumerate(y_columns):
        fig.add_trace(go.Scatter(
            x=data[x_column],
            y=data[col],
            mode='lines',
            name=col,
            fill='tonexty' if idx > 0 and stacked else 'tozeroy',
            line=dict(color=colors[idx % len(colors)])
        ))
    
    fig.update_layout(
        title=title,
        height=height,
        template='plotly_white',
        hovermode='x unified'
    )
    
    if stacked:
        fig.update_layout(yaxis=dict(title='Cumul'))
    
    return fig


# =============================================================================
# GRAPHIQUES DE DISTRIBUTION
# =============================================================================

def create_histogram(
    data: pd.DataFrame,
    column: str,
    title: str = "",
    bins: int = 30,
    color: str = "#1f77b4",
    show_curve: bool = True,
    height: int = 400
) -> go.Figure:
    """
    Crée un histogramme de distribution
    
    Args:
        data: DataFrame contenant les données
        column: Colonne à analyser
        title: Titre du graphique
        bins: Nombre de barres
        color: Couleur de l'histogramme
        show_curve: Afficher la courbe de distribution
        height: Hauteur du graphique
    
    Returns:
        Figure Plotly
    """
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=data[column],
        nbinsx=bins,
        marker_color=color,
        name='Distribution',
        opacity=0.7
    ))
    
    if show_curve:
        # Ajouter une courbe de densité
        hist_values, bin_edges = pd.cut(data[column], bins=bins, retbins=True)
        counts = hist_values.value_counts().sort_index()
        
        fig.add_trace(go.Scatter(
            x=[(bin_edges[i] + bin_edges[i+1])/2 for i in range(len(bin_edges)-1)],
            y=counts.values,
            mode='lines',
            name='Tendance',
            line=dict(color='red', width=2)
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title=column,
        yaxis_title='Fréquence',
        height=height,
        template='plotly_white',
        showlegend=show_curve
    )
    
    return fig


# =============================================================================
# GRAPHIQUES SPÉCIALISÉS
# =============================================================================

def create_gauge_chart(
    value: float,
    title: str = "",
    max_value: float = 100,
    color_ranges: Optional[Dict[str, Tuple[float, float, str]]] = None,
    height: int = 300
) -> go.Figure:
    """
    Crée un graphique jauge (gauge)
    
    Args:
        value: Valeur actuelle
        title: Titre du graphique
        max_value: Valeur maximale
        color_ranges: Dict de plages de couleurs
            Format: {'nom': (min, max, couleur)}
        height: Hauteur du graphique
    
    Returns:
        Figure Plotly
    
    Example:
        >>> ranges = {
        ...     'Faible': (0, 25, '#2ecc71'),
        ...     'Moyen': (25, 50, '#f39c12'),
        ...     'Élevé': (50, 75, '#e67e22'),
        ...     'Critique': (75, 100, '#e74c3c')
        ... }
        >>> fig = create_gauge_chart(67, "Score de Risque", 100, ranges)
    """
    if color_ranges is None:
        color_ranges = {
            'Faible': (0, 25, '#2ecc71'),
            'Moyen': (25, 50, '#f39c12'),
            'Élevé': (50, 75, '#e67e22'),
            'Critique': (75, 100, '#e74c3c')
        }
    
    # Déterminer la couleur actuelle
    current_color = '#1f77b4'
    for name, (min_val, max_val, color) in color_ranges.items():
        if min_val <= value < max_val:
            current_color = color
            break
    
    # Créer les steps pour le gauge
    steps = []
    for name, (min_val, max_val, color) in color_ranges.items():
        steps.append({'range': [min_val, max_val], 'color': color})
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        title={'text': title},
        delta={'reference': max_value / 2},
        gauge={
            'axis': {'range': [None, max_value]},
            'bar': {'color': current_color},
            'steps': steps,
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': max_value * 0.8
            }
        }
    ))
    
    fig.update_layout(
        height=height,
        template='plotly_white'
    )
    
    return fig


def create_heatmap(
    data: pd.DataFrame,
    x_column: str,
    y_column: str,
    value_column: str,
    title: str = "",
    colorscale: str = "RdYlGn_r",
    height: int = 500
) -> go.Figure:
    """
    Crée une carte de chaleur (heatmap)
    
    Args:
        data: DataFrame contenant les données
        x_column: Colonne pour l'axe X
        y_column: Colonne pour l'axe Y
        value_column: Colonne contenant les valeurs
        title: Titre du graphique
        colorscale: Échelle de couleurs
        height: Hauteur du graphique
    
    Returns:
        Figure Plotly
    """
    # Pivoter les données pour la heatmap
    pivot_data = data.pivot(index=y_column, columns=x_column, values=value_column)
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot_data.values,
        x=pivot_data.columns,
        y=pivot_data.index,
        colorscale=colorscale,
        text=pivot_data.values,
        texttemplate='%{text:.1f}',
        textfont={"size": 10},
        colorbar=dict(title=value_column)
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title=x_column,
        yaxis_title=y_column,
        height=height,
        template='plotly_white'
    )
    
    return fig


def create_scatter_plot(
    data: pd.DataFrame,
    x_column: str,
    y_column: str,
    color_column: Optional[str] = None,
    size_column: Optional[str] = None,
    title: str = "",
    height: int = 500
) -> go.Figure:
    """
    Crée un nuage de points (scatter plot)
    
    Args:
        data: DataFrame contenant les données
        x_column: Colonne pour l'axe X
        y_column: Colonne pour l'axe Y
        color_column: Colonne pour la couleur des points
        size_column: Colonne pour la taille des points
        title: Titre du graphique
        height: Hauteur du graphique
    
    Returns:
        Figure Plotly
    """
    if color_column:
        fig = px.scatter(
            data,
            x=x_column,
            y=y_column,
            color=color_column,
            size=size_column,
            title=title,
            height=height,
            template='plotly_white'
        )
    else:
        fig = go.Figure(data=go.Scatter(
            x=data[x_column],
            y=data[y_column],
            mode='markers',
            marker=dict(
                size=data[size_column] if size_column else 8,
                color='#1f77b4'
            )
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title=x_column,
            yaxis_title=y_column,
            height=height,
            template='plotly_white'
        )
    
    return fig


# =============================================================================
# UTILITAIRES
# =============================================================================

def display_chart(
    fig: go.Figure,
    use_container_width: bool = True,
    key: Optional[str] = None
):
    """
    Affiche un graphique Plotly dans Streamlit
    
    Args:
        fig: Figure Plotly à afficher
        use_container_width: Utiliser toute la largeur du conteneur
        key: Clé unique pour le composant Streamlit
    """
    st.plotly_chart(fig, use_container_width=use_container_width, key=key)


def get_color_palette(name: str = "default") -> List[str]:
    """
    Retourne une palette de couleurs prédéfinie
    
    Args:
        name: Nom de la palette
            - 'default': Palette par défaut
            - 'risk': Pour les niveaux de risque
            - 'change': Pour les types de changements
            - 'pastel': Couleurs pastels
    
    Returns:
        Liste de couleurs en format hex
    """
    palettes = {
        'default': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                   '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'],
        'risk': ['#2ecc71', '#f39c12', '#e67e22', '#e74c3c'],
        'change': ['#2ecc71', '#e74c3c', '#f39c12'],
        'pastel': ['#a8e6cf', '#ffd3b6', '#ffaaa5', '#ff8b94', '#dcedc1'],
        'blue_scale': ['#08519c', '#3182bd', '#6baed6', '#9ecae1', '#c6dbef'],
        'red_scale': ['#67000d', '#a50f15', '#cb181d', '#ef3b2c', '#fb6a4a']
    }
    
    return palettes.get(name, palettes['default'])