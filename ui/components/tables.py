"""
Composants de tableaux réutilisables
Contient des fonctions pour afficher et formater des tableaux dans l'application
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Union, Callable, Any
from datetime import datetime


# =============================================================================
# TABLEAUX DE BASE
# =============================================================================

def display_dataframe(
    data: pd.DataFrame,
    title: Optional[str] = None,
    height: int = 400,
    use_container_width: bool = True,
    hide_index: bool = True,
    column_config: Optional[Dict] = None,
    key: Optional[str] = None
):
    """
    Affiche un DataFrame avec options de configuration
    
    Args:
        data: DataFrame à afficher
        title: Titre optionnel
        height: Hauteur du tableau
        use_container_width: Utiliser toute la largeur
        hide_index: Masquer l'index
        column_config: Configuration des colonnes
        key: Clé unique pour Streamlit
    
    Example:
        >>> display_dataframe(df, title="Liste des Substances", height=500)
    """
    if title:
        st.subheader(title)
    
    if data.empty:
        st.info("Aucune donnée à afficher")
        return
    
    st.dataframe(
        data,
        height=height,
        use_container_width=use_container_width,
        hide_index=hide_index,
        column_config=column_config,
        key=key
    )
    
    # Afficher le nombre de lignes
    st.caption(f"📊 {len(data)} ligne(s) affichée(s)")


def display_table_with_download(
    data: pd.DataFrame,
    title: str = "Données",
    filename: str = "export.csv",
    download_label: str = "📥 Télécharger (CSV)",
    height: int = 400
):
    """
    Affiche un tableau avec bouton de téléchargement
    
    Args:
        data: DataFrame à afficher
        title: Titre du tableau
        filename: Nom du fichier de téléchargement
        download_label: Label du bouton
        height: Hauteur du tableau
    
    Example:
        >>> display_table_with_download(df, "Substances Filtrées", "substances.csv")
    """
    st.subheader(title)
    
    if data.empty:
        st.info("Aucune donnée à afficher")
        return
    
    # Afficher le tableau
    st.dataframe(data, height=height, use_container_width=True)
    
    # Bouton de téléchargement
    csv = data.to_csv(index=False).encode('utf-8')
    st.download_button(
        label=download_label,
        data=csv,
        file_name=filename,
        mime='text/csv'
    )
    
    st.caption(f"📊 {len(data)} ligne(s) • {len(data.columns)} colonne(s)")


# =============================================================================
# TABLEAUX FORMATÉS
# =============================================================================

def create_styled_dataframe(
    data: pd.DataFrame,
    color_columns: Optional[Dict[str, Callable]] = None,
    format_columns: Optional[Dict[str, str]] = None,
    highlight_rows: Optional[Callable[[pd.Series], bool]] = None,
    highlight_color: str = "yellow"
) -> pd.DataFrame:
    """
    Crée un DataFrame stylisé avec mise en forme conditionnelle
    
    Args:
        data: DataFrame à styler
        color_columns: Dict {colonne: fonction_couleur}
        format_columns: Dict {colonne: format_string}
        highlight_rows: Fonction pour identifier les lignes à surligner
        highlight_color: Couleur de surlignage
    
    Returns:
        DataFrame stylisé
    
    Example:
        >>> def color_risk(val):
        ...     if val > 75: return 'background-color: #e74c3c'
        ...     elif val > 50: return 'background-color: #f39c12'
        ...     else: return 'background-color: #2ecc71'
        >>> 
        >>> styled_df = create_styled_dataframe(
        ...     df,
        ...     color_columns={'risk_score': color_risk},
        ...     format_columns={'risk_score': '{:.1f}'}
        ... )
    """
    styled = data.style
    
    # Appliquer les couleurs par colonne
    if color_columns:
        for col, color_func in color_columns.items():
            if col in data.columns:
                styled = styled.applymap(color_func, subset=[col])
    
    # Appliquer les formats
    if format_columns:
        styled = styled.format(format_columns)
    
    # Surligner certaines lignes
    if highlight_rows:
        def highlight_func(row):
            if highlight_rows(row):
                return [f'background-color: {highlight_color}'] * len(row)
            return [''] * len(row)
        styled = styled.apply(highlight_func, axis=1)
    
    return styled


def display_comparison_table(
    data1: pd.DataFrame,
    data2: pd.DataFrame,
    label1: str = "Avant",
    label2: str = "Après",
    key_column: str = "cas_id",
    compare_columns: Optional[List[str]] = None
):
    """
    Affiche deux DataFrames côte à côte pour comparaison
    
    Args:
        data1: Premier DataFrame
        data2: Deuxième DataFrame
        label1: Label du premier DataFrame
        label2: Label du deuxième DataFrame
        key_column: Colonne clé pour la jointure
        compare_columns: Colonnes à comparer
    
    Example:
        >>> display_comparison_table(old_df, new_df, "Ancien", "Nouveau", "cas_id")
    """
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**{label1}**")
        st.dataframe(data1, use_container_width=True, height=400)
        st.caption(f"{len(data1)} ligne(s)")
    
    with col2:
        st.markdown(f"**{label2}**")
        st.dataframe(data2, use_container_width=True, height=400)
        st.caption(f"{len(data2)} ligne(s)")
    
    # Calculer les différences
    if compare_columns:
        st.subheader("Différences")
        
        # Identifier les changements
        added = set(data2[key_column]) - set(data1[key_column])
        removed = set(data1[key_column]) - set(data2[key_column])
        common = set(data1[key_column]) & set(data2[key_column])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Ajoutés", len(added))
        with col2:
            st.metric("Supprimés", len(removed))
        with col3:
            st.metric("Communs", len(common))


# =============================================================================
# TABLEAUX INTERACTIFS
# =============================================================================

def display_editable_table(
    data: pd.DataFrame,
    key: str,
    num_rows: str = "dynamic",
    disabled_columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Affiche un tableau éditable
    
    Args:
        data: DataFrame à éditer
        key: Clé unique pour le composant
        num_rows: 'fixed' ou 'dynamic'
        disabled_columns: Colonnes non éditables
    
    Returns:
        DataFrame édité
    
    Example:
        >>> edited_df = display_editable_table(df, key="edit_table")
        >>> if edited_df is not None:
        ...     st.write("Modifications détectées!")
    """
    column_config = {}
    if disabled_columns:
        for col in disabled_columns:
            column_config[col] = st.column_config.TextColumn(col, disabled=True)
    
    edited_data = st.data_editor(
        data,
        use_container_width=True,
        num_rows=num_rows,
        column_config=column_config if column_config else None,
        key=key
    )
    
    return edited_data


def display_selectable_table(
    data: pd.DataFrame,
    key: str = "selectable_table",
    selection_mode: str = "multi-row"
) -> List[int]:
    """
    Affiche un tableau avec sélection de lignes
    
    Args:
        data: DataFrame à afficher
        key: Clé unique
        selection_mode: 'single-row', 'multi-row', 'single-column', 'multi-column'
    
    Returns:
        Liste des indices des lignes sélectionnées
    
    Example:
        >>> selected_indices = display_selectable_table(df)
        >>> if selected_indices:
        ...     selected_rows = df.iloc[selected_indices]
    """
    # Note: Streamlit n'a pas de sélection native dans dataframe
    # On utilise une colonne de checkbox
    data_with_select = data.copy()
    data_with_select.insert(0, '✓', False)
    
    edited = st.data_editor(
        data_with_select,
        hide_index=True,
        use_container_width=True,
        key=key,
        column_config={
            '✓': st.column_config.CheckboxColumn(
                '✓',
                help="Sélectionner cette ligne",
                default=False
            )
        }
    )
    
    selected_indices = edited[edited['✓']].index.tolist()
    return selected_indices


# =============================================================================
# TABLEAUX SPÉCIALISÉS
# =============================================================================

def display_changes_table(
    changes_df: pd.DataFrame,
    title: str = "Historique des Changements",
    show_stats: bool = True
):
    """
    Affiche un tableau optimisé pour l'historique des changements
    
    Args:
        changes_df: DataFrame des changements
        title: Titre du tableau
        show_stats: Afficher les statistiques
    
    Example:
        >>> display_changes_table(history_df)
    """
    st.subheader(title)
    
    if changes_df.empty:
        st.info("Aucun changement enregistré")
        return
    
    # Statistiques
    if show_stats and 'change_type' in changes_df.columns:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            insertions = len(changes_df[changes_df['change_type'] == 'insertion'])
            st.metric("✅ Insertions", insertions)
        
        with col2:
            deletions = len(changes_df[changes_df['change_type'] == 'deletion'])
            st.metric("❌ Suppressions", deletions)
        
        with col3:
            modifications = len(changes_df[changes_df['change_type'] == 'modification'])
            st.metric("✏️ Modifications", modifications)
        
        st.divider()
    
    # Configuration des colonnes
    column_config = {
        'change_type': st.column_config.TextColumn(
            'Type',
            help="Type de changement"
        ),
        'timestamp': st.column_config.DatetimeColumn(
            'Date',
            format="DD/MM/YYYY HH:mm"
        )
    }
    
    # Colonnes à afficher
    display_columns = ['timestamp', 'change_type', 'source_list', 'cas_id', 'cas_name']
    if 'modified_fields' in changes_df.columns:
        display_columns.append('modified_fields')
    
    available_columns = [col for col in display_columns if col in changes_df.columns]
    
    # Afficher le tableau
    st.dataframe(
        changes_df[available_columns],
        use_container_width=True,
        height=500,
        column_config=column_config
    )
    
    # Téléchargement
    csv = changes_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Télécharger l'historique (CSV)",
        data=csv,
        file_name=f'historique_changements_{datetime.now().strftime("%Y%m%d")}.csv',
        mime='text/csv'
    )


def display_risk_table(
    data: pd.DataFrame,
    risk_column: str = 'risk_score',
    title: str = "Substances par Niveau de Risque"
):
    """
    Affiche un tableau avec mise en forme des niveaux de risque
    
    Args:
        data: DataFrame contenant les substances
        risk_column: Nom de la colonne de score de risque
        title: Titre du tableau
    
    Example:
        >>> display_risk_table(df, 'risk_score')
    """
    st.subheader(title)
    
    if data.empty:
        st.info("Aucune donnée à afficher")
        return
    
    # Fonction de colorisation
    def color_risk(val):
        if pd.isna(val):
            return ''
        if val >= 75:
            return 'background-color: #e74c3c; color: white'
        elif val >= 50:
            return 'background-color: #e67e22; color: white'
        elif val >= 25:
            return 'background-color: #f39c12; color: black'
        else:
            return 'background-color: #2ecc71; color: white'
    
    # Styler le DataFrame
    if risk_column in data.columns:
        styled = data.style.applymap(color_risk, subset=[risk_column])
        styled = styled.format({risk_column: '{:.1f}'})
        
        st.dataframe(
            styled,
            use_container_width=True,
            height=500
        )
    else:
        st.dataframe(data, use_container_width=True, height=500)


def display_summary_table(
    data: pd.DataFrame,
    group_by: str,
    agg_columns: Dict[str, str],
    title: str = "Résumé"
):
    """
    Affiche un tableau résumé avec agrégations
    
    Args:
        data: DataFrame source
        group_by: Colonne de regroupement
        agg_columns: Dict {colonne: fonction} pour agrégation
        title: Titre du tableau
    
    Example:
        >>> agg_cols = {'risk_score': 'mean', 'cas_id': 'count'}
        >>> display_summary_table(df, 'source_list', agg_cols, "Par Liste")
    """
    st.subheader(title)
    
    if data.empty:
        st.info("Aucune donnée à résumer")
        return
    
    # Créer le résumé
    summary = data.groupby(group_by).agg(agg_columns).reset_index()
    
    # Renommer les colonnes
    summary.columns = [group_by] + [f"{col}_{func}" for col, func in agg_columns.items()]
    
    # Afficher
    st.dataframe(summary, use_container_width=True)
    
    st.caption(f"📊 {len(summary)} groupe(s)")


# =============================================================================
# TABLEAUX PAGINÉS
# =============================================================================

def display_paginated_table(
    data: pd.DataFrame,
    page_size: int = 50,
    key: str = "pagination"
):
    """
    Affiche un tableau avec pagination
    
    Args:
        data: DataFrame à afficher
        page_size: Nombre de lignes par page
        key: Clé unique pour le state
    
    Example:
        >>> display_paginated_table(large_df, page_size=25)
    """
    if data.empty:
        st.info("Aucune donnée à afficher")
        return
    
    # Initialiser la page dans session_state
    page_key = f"{key}_page"
    if page_key not in st.session_state:
        st.session_state[page_key] = 0
    
    # Calculer le nombre de pages
    total_pages = (len(data) - 1) // page_size + 1
    
    # Navigation
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
    
    with col1:
        if st.button("⏮️ Premier", key=f"{key}_first"):
            st.session_state[page_key] = 0
    
    with col2:
        if st.button("◀️ Précédent", key=f"{key}_prev"):
            st.session_state[page_key] = max(0, st.session_state[page_key] - 1)
    
    with col3:
        st.markdown(f"<div style='text-align: center; padding-top: 5px;'>Page {st.session_state[page_key] + 1} / {total_pages}</div>", unsafe_allow_html=True)
    
    with col4:
        if st.button("Suivant ▶️", key=f"{key}_next"):
            st.session_state[page_key] = min(total_pages - 1, st.session_state[page_key] + 1)
    
    with col5:
        if st.button("Dernier ⏭️", key=f"{key}_last"):
            st.session_state[page_key] = total_pages - 1
    
    # Afficher la page actuelle
    start_idx = st.session_state[page_key] * page_size
    end_idx = min(start_idx + page_size, len(data))
    
    page_data = data.iloc[start_idx:end_idx]
    
    st.dataframe(page_data, use_container_width=True, height=400)
    
    st.caption(f"Lignes {start_idx + 1} - {end_idx} sur {len(data)}")


# =============================================================================
# UTILITAIRES
# =============================================================================

def format_dataframe_for_display(
    data: pd.DataFrame,
    date_columns: Optional[List[str]] = None,
    number_columns: Optional[List[str]] = None,
    percent_columns: Optional[List[str]] = None,
    date_format: str = "%d/%m/%Y",
    number_decimals: int = 2
) -> pd.DataFrame:
    """
    Formate un DataFrame pour l'affichage
    
    Args:
        data: DataFrame à formater
        date_columns: Colonnes de dates à formater
        number_columns: Colonnes numériques à formater
        percent_columns: Colonnes de pourcentages
        date_format: Format des dates
        number_decimals: Nombre de décimales
    
    Returns:
        DataFrame formaté
    
    Example:
        >>> formatted = format_dataframe_for_display(
        ...     df,
        ...     date_columns=['created_at'],
        ...     number_columns=['risk_score'],
        ...     percent_columns=['completion']
        ... )
    """
    df = data.copy()
    
    # Formater les dates
    if date_columns:
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime(date_format)
    
    # Formater les nombres
    if number_columns:
        for col in number_columns:
            if col in df.columns:
                df[col] = df[col].round(number_decimals)
    
    # Formater les pourcentages
    if percent_columns:
        for col in percent_columns:
            if col in df.columns:
                df[col] = (df[col] * 100).round(1).astype(str) + '%'
    
    return df


def get_column_config_for_type(
    column_types: Dict[str, str]
) -> Dict:
    """
    Génère une configuration de colonnes Streamlit basée sur les types
    
    Args:
        column_types: Dict {colonne: type}
            Types supportés: 'text', 'number', 'date', 'checkbox', 'select'
    
    Returns:
        Dict de configuration pour st.dataframe
    
    Example:
        >>> config = get_column_config_for_type({
        ...     'cas_id': 'text',
        ...     'risk_score': 'number',
        ...     'is_active': 'checkbox',
        ...     'created_at': 'date'
        ... })
    """
    config = {}
    
    for col, col_type in column_types.items():
        if col_type == 'text':
            config[col] = st.column_config.TextColumn(col)
        elif col_type == 'number':
            config[col] = st.column_config.NumberColumn(col, format="%.2f")
        elif col_type == 'date':
            config[col] = st.column_config.DatetimeColumn(col, format="DD/MM/YYYY")
        elif col_type == 'checkbox':
            config[col] = st.column_config.CheckboxColumn(col)
        elif col_type == 'select':
            config[col] = st.column_config.SelectboxColumn(col)
    
    return config


def export_table_to_excel(
    data: pd.DataFrame,
    filename: str,
    sheet_name: str = "Data"
) -> bytes:
    """
    Exporte un DataFrame en Excel
    
    Args:
        data: DataFrame à exporter
        filename: Nom du fichier
        sheet_name: Nom de la feuille
    
    Returns:
        Bytes du fichier Excel
    
    Example:
        >>> excel_data = export_table_to_excel(df, "export.xlsx")
        >>> st.download_button("Download", excel_data, "export.xlsx")
    """
    from io import BytesIO
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        data.to_excel(writer, sheet_name=sheet_name, index=False)
    
    return output.getvalue()