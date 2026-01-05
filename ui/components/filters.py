"""
Composants de filtrage réutilisables
Contient des fonctions pour créer des filtres standard dans l'application
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple


def create_text_filters(
    prefix: str = "",
    include_cas_name: bool = True,
    include_cas_id: bool = True,
    include_source_list: bool = True,
    source_lists: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Crée un ensemble de filtres texte standard
    
    Args:
        prefix: Préfixe pour les clés de session_state (pour éviter les conflits)
        include_cas_name: Inclure le filtre nom de substance
        include_cas_id: Inclure le filtre CAS ID
        include_source_list: Inclure le filtre liste source
        source_lists: Liste des listes sources disponibles (None = pas de filtre)
    
    Returns:
        Dict contenant les valeurs des filtres
    """
    filters = {}
    columns = []
    
    # Déterminer le nombre de colonnes
    num_cols = sum([include_cas_name, include_cas_id, include_source_list])
    if num_cols > 0:
        columns = st.columns(num_cols)
    
    col_idx = 0
    
    # Filtre nom de substance
    if include_cas_name:
        with columns[col_idx]:
            filters['cas_name'] = st.text_input(
                "Filtrer par nom de substance",
                key=f"{prefix}_cas_name_filter"
            )
        col_idx += 1
    
    # Filtre CAS ID
    if include_cas_id:
        with columns[col_idx]:
            filters['cas_id'] = st.text_input(
                "Filtrer par CAS ID",
                key=f"{prefix}_cas_id_filter"
            )
        col_idx += 1
    
    # Filtre liste source
    if include_source_list and source_lists:
        with columns[col_idx]:
            all_lists = ['Toutes'] + sorted(source_lists)
            filters['source_list'] = st.selectbox(
                "Filtrer par liste source",
                all_lists,
                key=f"{prefix}_source_list_filter"
            )
    
    return filters


def create_date_filters(
    prefix: str = "",
    include_updated: bool = True,
    include_created: bool = True
) -> Dict[str, bool]:
    """
    Crée des filtres de date (mis à jour aujourd'hui / créé aujourd'hui)
    
    Args:
        prefix: Préfixe pour les clés de session_state
        include_updated: Inclure le filtre "mis à jour aujourd'hui"
        include_created: Inclure le filtre "créé aujourd'hui"
    
    Returns:
        Dict contenant les valeurs des filtres de date
    """
    filters = {}
    columns = []
    
    num_cols = sum([include_updated, include_created])
    if num_cols > 0:
        columns = st.columns(num_cols + 1)  # +1 pour un espace vide
    
    col_idx = 0
    
    if include_updated:
        with columns[col_idx]:
            filters['updated_today'] = st.checkbox(
                "📅 Mis à jour aujourd'hui",
                key=f"{prefix}_updated_today_filter"
            )
        col_idx += 1
    
    if include_created:
        with columns[col_idx]:
            filters['created_today'] = st.checkbox(
                "🆕 Créé aujourd'hui",
                key=f"{prefix}_created_today_filter"
            )
    
    return filters


def create_reset_button(
    prefix: str = "",
    callback: Optional[callable] = None
) -> bool:
    """
    Crée un bouton de réinitialisation des filtres
    
    Args:
        prefix: Préfixe pour identifier les filtres à réinitialiser
        callback: Fonction callback optionnelle
    
    Returns:
        True si le bouton a été cliqué
    """
    if callback:
        return st.button("🔄 Réinitialiser les filtres", on_click=callback)
    else:
        return st.button("🔄 Réinitialiser les filtres")


def apply_text_filters(
    df: pd.DataFrame,
    filters: Dict[str, str]
) -> pd.DataFrame:
    """
    Applique les filtres texte à un DataFrame
    
    Args:
        df: DataFrame à filtrer
        filters: Dict des valeurs de filtres (retour de create_text_filters)
    
    Returns:
        DataFrame filtré
    """
    filtered = df.copy()
    
    # Filtre par nom
    if filters.get('cas_name'):
        filtered = filtered[
            filtered['cas_name'].astype(str).str.contains(
                filters['cas_name'], case=False, na=False
            )
        ]
    
    # Filtre par CAS ID
    if filters.get('cas_id'):
        filtered = filtered[
            filtered['cas_id'].astype(str).str.contains(
                filters['cas_id'], case=False, na=False
            )
        ]
    
    # Filtre par liste source
    if filters.get('source_list') and filters['source_list'] != 'Toutes':
        filtered = filtered[filtered['source_list'] == filters['source_list']]
    
    return filtered


def apply_date_filters(
    df: pd.DataFrame,
    filters: Dict[str, bool]
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Applique les filtres de date à un DataFrame
    
    Args:
        df: DataFrame à filtrer
        filters: Dict des valeurs de filtres (retour de create_date_filters)
    
    Returns:
        Tuple (DataFrame filtré, Liste des warnings)
    """
    filtered = df.copy()
    warnings = []
    today = datetime.now().date()
    
    # Filtre "mis à jour aujourd'hui"
    if filters.get('updated_today', False):
        if 'updated_at' in filtered.columns:
            filtered['_temp_updated'] = pd.to_datetime(filtered['updated_at'], errors='coerce')
            filtered = filtered[filtered['_temp_updated'].dt.date == today]
            filtered = filtered.drop(columns=['_temp_updated'])
        else:
            warnings.append("⚠️ La colonne 'updated_at' n'existe pas dans les données.")
    
    # Filtre "créé aujourd'hui"
    if filters.get('created_today', False):
        if 'created_at' in filtered.columns:
            filtered['_temp_created'] = pd.to_datetime(filtered['created_at'], errors='coerce')
            filtered = filtered[filtered['_temp_created'].dt.date == today]
            filtered = filtered.drop(columns=['_temp_created'])
        else:
            warnings.append("⚠️ La colonne 'created_at' n'existe pas dans les données.")
    
    return filtered, warnings


def create_combined_filters(
    prefix: str,
    aggregated_df: pd.DataFrame,
    include_date_filters: bool = True
) -> Dict:
    """
    Crée un ensemble complet de filtres (texte + date + reset)
    
    Args:
        prefix: Préfixe pour les session_state keys
        aggregated_df: DataFrame pour extraire les listes sources
        include_date_filters: Inclure les filtres de date
    
    Returns:
        Dict contenant toutes les valeurs de filtres
    """
    st.subheader("Filtres")
    
    # Filtres texte (première ligne)
    source_lists = list(aggregated_df['source_list'].unique()) if 'source_list' in aggregated_df.columns else None
    text_filters = create_text_filters(
        prefix=prefix,
        source_lists=source_lists
    )
    
    # Filtres de date (deuxième ligne)
    date_filters = {}
    if include_date_filters:
        date_filters = create_date_filters(prefix=prefix)
    
    # Bouton reset
    def reset_callback():
        """Réinitialise tous les filtres"""
        for key in list(st.session_state.keys()):
            if key.startswith(prefix):
                if 'filter' in key:
                    if 'today' in key:
                        st.session_state[key] = False
                    elif 'source_list' in key:
                        st.session_state[key] = 'Toutes'
                    else:
                        st.session_state[key] = ""
    
    create_reset_button(prefix=prefix, callback=reset_callback)
    
    # Combiner tous les filtres
    all_filters = {**text_filters, **date_filters}
    return all_filters


def display_filter_summary(filtered_count: int, total_count: int):
    """
    Affiche un résumé des filtres appliqués
    
    Args:
        filtered_count: Nombre d'éléments après filtrage
        total_count: Nombre total d'éléments
    """
    if filtered_count < total_count:
        st.info(f"📊 Affichage de {filtered_count} sur {total_count} éléments (filtré)")
    else:
        st.info(f"📊 Affichage de {total_count} éléments")


# =============================================================================
# FILTRES AVANCÉS
# =============================================================================

def create_range_filter(
    column_name: str,
    min_value: float,
    max_value: float,
    prefix: str = "",
    step: float = 1.0,
    format_string: str = "%.1f"
) -> Tuple[float, float]:
    """
    Crée un filtre de plage avec slider
    
    Args:
        column_name: Nom de la colonne
        min_value: Valeur minimale
        max_value: Valeur maximale
        prefix: Préfixe pour session_state
        step: Pas du slider
        format_string: Format d'affichage
    
    Returns:
        Tuple (min_selected, max_selected)
    
    Example:
        >>> min_score, max_score = create_range_filter("Score", 0, 100, "risk")
    """
    return st.slider(
        f"Plage de {column_name}",
        min_value=min_value,
        max_value=max_value,
        value=(min_value, max_value),
        step=step,
        format=format_string,
        key=f"{prefix}_range_{column_name}"
    )


def create_multiselect_filter(
    label: str,
    options: List[str],
    prefix: str = "",
    default: Optional[List[str]] = None,
    help_text: Optional[str] = None
) -> List[str]:
    """
    Crée un filtre multi-sélection
    
    Args:
        label: Label du filtre
        options: Liste des options disponibles
        prefix: Préfixe pour session_state
        default: Valeurs par défaut sélectionnées
        help_text: Texte d'aide
    
    Returns:
        Liste des valeurs sélectionnées
    
    Example:
        >>> selected_lists = create_multiselect_filter(
        ...     "Listes sources",
        ...     ['testa', 'testb', 'testc'],
        ...     prefix="agg"
        ... )
    """
    return st.multiselect(
        label,
        options=options,
        default=default if default is not None else [],
        help=help_text,
        key=f"{prefix}_multiselect_{label}"
    )


def create_search_filter(
    label: str = "Recherche",
    prefix: str = "",
    placeholder: str = "Tapez pour rechercher...",
    help_text: Optional[str] = None
) -> str:
    """
    Crée un champ de recherche générique
    
    Args:
        label: Label du champ
        prefix: Préfixe pour session_state
        placeholder: Texte placeholder
        help_text: Texte d'aide
    
    Returns:
        Texte de recherche
    
    Example:
        >>> search_term = create_search_filter("Recherche globale", "global")
    """
    return st.text_input(
        label,
        placeholder=placeholder,
        help=help_text,
        key=f"{prefix}_search"
    )


def create_radio_filter(
    label: str,
    options: List[str],
    prefix: str = "",
    default_index: int = 0,
    horizontal: bool = False
) -> str:
    """
    Crée un filtre radio button
    
    Args:
        label: Label du filtre
        options: Liste des options
        prefix: Préfixe pour session_state
        default_index: Index de l'option par défaut
        horizontal: Affichage horizontal
    
    Returns:
        Option sélectionnée
    
    Example:
        >>> view_mode = create_radio_filter(
        ...     "Mode d'affichage",
        ...     ["Tableau", "Graphique", "Carte"],
        ...     horizontal=True
        ... )
    """
    return st.radio(
        label,
        options=options,
        index=default_index,
        horizontal=horizontal,
        key=f"{prefix}_radio_{label}"
    )


# =============================================================================
# APPLICATION DE FILTRES AVANCÉS
# =============================================================================

def apply_range_filter(
    df: pd.DataFrame,
    column: str,
    min_value: float,
    max_value: float
) -> pd.DataFrame:
    """
    Applique un filtre de plage à un DataFrame
    
    Args:
        df: DataFrame à filtrer
        column: Colonne à filtrer
        min_value: Valeur minimale
        max_value: Valeur maximale
    
    Returns:
        DataFrame filtré
    """
    if column not in df.columns:
        return df
    
    return df[(df[column] >= min_value) & (df[column] <= max_value)]


def apply_multiselect_filter(
    df: pd.DataFrame,
    column: str,
    selected_values: List[str]
) -> pd.DataFrame:
    """
    Applique un filtre multi-sélection à un DataFrame
    
    Args:
        df: DataFrame à filtrer
        column: Colonne à filtrer
        selected_values: Valeurs sélectionnées
    
    Returns:
        DataFrame filtré
    """
    if not selected_values or column not in df.columns:
        return df
    
    return df[df[column].isin(selected_values)]


def apply_search_filter(
    df: pd.DataFrame,
    search_term: str,
    search_columns: List[str]
) -> pd.DataFrame:
    """
    Applique une recherche textuelle sur plusieurs colonnes
    
    Args:
        df: DataFrame à filtrer
        search_term: Terme de recherche
        search_columns: Colonnes dans lesquelles chercher
    
    Returns:
        DataFrame filtré
    
    Example:
        >>> filtered = apply_search_filter(df, "benzene", ["cas_name", "cas_id"])
    """
    if not search_term:
        return df
    
    # Créer un masque combiné pour toutes les colonnes
    mask = pd.Series([False] * len(df), index=df.index)
    
    for col in search_columns:
        if col in df.columns:
            mask |= df[col].astype(str).str.contains(search_term, case=False, na=False)
    
    return df[mask]


# =============================================================================
# FILTRES PERSONNALISÉS
# =============================================================================

def create_risk_level_filter(
    prefix: str = "",
    default: Optional[List[str]] = None
) -> List[str]:
    """
    Crée un filtre spécifique pour les niveaux de risque
    
    Args:
        prefix: Préfixe pour session_state
        default: Niveaux par défaut sélectionnés
    
    Returns:
        Liste des niveaux sélectionnés
    """
    risk_levels = ["Faible", "Moyen", "Élevé", "Critique"]
    
    return st.multiselect(
        "Niveaux de risque",
        options=risk_levels,
        default=default if default is not None else [],
        help="Sélectionnez un ou plusieurs niveaux de risque",
        key=f"{prefix}_risk_levels"
    )


def create_change_type_filter(
    prefix: str = "",
    include_all: bool = True
) -> str:
    """
    Crée un filtre pour les types de changements
    
    Args:
        prefix: Préfixe pour session_state
        include_all: Inclure l'option "Tous"
    
    Returns:
        Type de changement sélectionné
    """
    options = ['Tous', 'insertion', 'deletion', 'modification'] if include_all else ['insertion', 'deletion', 'modification']
    
    return st.selectbox(
        "Type de changement",
        options=options,
        key=f"{prefix}_change_type"
    )


def create_time_period_filter(
    prefix: str = "",
    default_period: str = "all"
) -> str:
    """
    Crée un filtre de période temporelle
    
    Args:
        prefix: Préfixe pour session_state
        default_period: Période par défaut
    
    Returns:
        Période sélectionnée
    """
    periods = {
        "all": "Tout",
        "today": "Aujourd'hui",
        "week": "Cette semaine",
        "month": "Ce mois",
        "year": "Cette année"
    }
    
    return st.selectbox(
        "Période",
        options=list(periods.keys()),
        format_func=lambda x: periods[x],
        index=list(periods.keys()).index(default_period),
        key=f"{prefix}_time_period"
    )


def apply_time_period_filter(
    df: pd.DataFrame,
    period: str,
    date_column: str = "timestamp"
) -> pd.DataFrame:
    """
    Applique un filtre de période temporelle
    
    Args:
        df: DataFrame à filtrer
        period: Période ('today', 'week', 'month', 'year', 'all')
        date_column: Nom de la colonne de date
    
    Returns:
        DataFrame filtré
    """
    if period == "all" or date_column not in df.columns:
        return df
    
    # Convertir en datetime
    df_copy = df.copy()
    df_copy[date_column] = pd.to_datetime(df_copy[date_column], errors='coerce')
    
    now = datetime.now()
    
    if period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start_date = now - timedelta(days=now.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "month":
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "year":
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        return df
    
    return df_copy[df_copy[date_column] >= start_date]


# =============================================================================
# COMPOSANTS COMBINÉS
# =============================================================================

def create_advanced_filter_panel(
    data: pd.DataFrame,
    prefix: str = "advanced"
) -> Dict:
    """
    Crée un panneau complet de filtres avancés
    
    Args:
        data: DataFrame pour extraire les options
        prefix: Préfixe pour session_state
    
    Returns:
        Dict de tous les filtres sélectionnés
    """
    st.subheader("🔍 Filtres Avancés")
    
    with st.expander("Afficher les filtres avancés", expanded=False):
        filters = {}
        
        # Recherche globale
        filters['search'] = create_search_filter("Recherche globale", prefix)
        
        st.divider()
        
        # Filtres en colonnes
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Filtre de période
            filters['period'] = create_time_period_filter(prefix)
        
        with col2:
            # Filtre de niveau de risque
            if 'risk_level' in data.columns:
                filters['risk_levels'] = create_risk_level_filter(prefix)
        
        with col3:
            # Filtre de type de changement
            if 'change_type' in data.columns:
                filters['change_type'] = create_change_type_filter(prefix)
        
        # Filtre de plage (si applicable)
        if 'risk_score' in data.columns:
            st.divider()
            filters['risk_range'] = create_range_filter(
                "Score de Risque",
                float(data['risk_score'].min()),
                float(data['risk_score'].max()),
                prefix
            )
    
    return filters


def apply_all_filters(
    df: pd.DataFrame,
    filters: Dict,
    search_columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Applique tous les filtres d'un coup
    
    Args:
        df: DataFrame à filtrer
        filters: Dict de filtres à appliquer
        search_columns: Colonnes pour la recherche textuelle
    
    Returns:
        DataFrame filtré
    
    Example:
        >>> filters = create_advanced_filter_panel(df)
        >>> filtered = apply_all_filters(df, filters, ['cas_name', 'cas_id'])
    """
    result = df.copy()
    
    # Recherche globale
    if 'search' in filters and filters['search'] and search_columns:
        result = apply_search_filter(result, filters['search'], search_columns)
    
    # Période
    if 'period' in filters and filters['period'] != 'all':
        result = apply_time_period_filter(result, filters['period'])
    
    # Niveaux de risque
    if 'risk_levels' in filters and filters['risk_levels']:
        result = apply_multiselect_filter(result, 'risk_level', filters['risk_levels'])
    
    # Type de changement
    if 'change_type' in filters and filters['change_type'] != 'Tous':
        result = result[result['change_type'] == filters['change_type']]
    
    # Plage de risque
    if 'risk_range' in filters:
        min_risk, max_risk = filters['risk_range']
        result = apply_range_filter(result, 'risk_score', min_risk, max_risk)
    
    return result