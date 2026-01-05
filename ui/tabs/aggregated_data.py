"""
Onglet Données Agrégées
Affichage et filtrage des données agrégées de toutes les sources
"""

import streamlit as st
import pandas as pd
from typing import Dict
import os
from pathlib import Path
import time

# Feature flag pour activer/désactiver le sélecteur de colonnes
ENABLE_COLUMN_SELECTOR = True

# Import conditionnel du sélecteur de colonnes
if ENABLE_COLUMN_SELECTOR:
    try:
        from ui.components.column_selector import render_column_selector
        COLUMN_SELECTOR_AVAILABLE = True
    except ImportError:
        COLUMN_SELECTOR_AVAILABLE = False
else:
    COLUMN_SELECTOR_AVAILABLE = False


def render(managers: Dict):
    """
    Affiche l'onglet Données Agrégées
    
    Args:
        managers: Dictionnaire contenant tous les managers
    """
    from backend.logger import get_logger
    logger = get_logger()
    
    # Header avec bouton de rafraîchissement
    col1, col2 = st.columns([6, 1])
    with col1:
        st.header("📊 Données Agrégées")
    with col2:
        st.write("")  # Espacement pour alignement vertical
        if st.button("🔄", key="refresh_aggregated", help="Recharger les données"):
            st.cache_data.clear()
            logger.info("Rafraîchissement manuel des données agrégées")
            st.rerun()
    
    # Détection automatique de changement du fichier
    aggregated_file = Path("data/aggregated_data.xlsx")
    
    if aggregated_file.exists():
        file_mtime = os.path.getmtime(aggregated_file)
        
        # Vérifier si le fichier a changé depuis la dernière visite de cet onglet
        if 'last_aggregated_mtime' not in st.session_state:
            st.session_state.last_aggregated_mtime = file_mtime
            logger.info("Première visite de l'onglet Données Agrégées")
        elif st.session_state.last_aggregated_mtime != file_mtime:
            # Fichier modifié, recharger automatiquement
            logger.info(f"Changement détecté dans aggregated_data.xlsx (ancien: {st.session_state.last_aggregated_mtime}, nouveau: {file_mtime})")
            st.cache_data.clear()
            st.session_state.last_aggregated_mtime = file_mtime
            st.info("🔄 Nouvelles données détectées, rechargement automatique...")
            time.sleep(1)
            st.rerun()
    
    st.divider()
    
    st.info("Cette section affiche toutes les substances agrégées de toutes les listes sources.")
    
    try:
        # Charger les données agrégées
        aggregated_df = managers['data'].load_aggregated_data()
        
        if aggregated_df.empty:
            st.warning("⚠️ Aucune donnée agrégée disponible. Veuillez d'abord charger les données dans l'onglet 'Mise à Jour'.")
            return
        
        logger.info(f"Données agrégées chargées: {len(aggregated_df)} enregistrements")
        
        # Sélecteur de colonnes (si activé et disponible)
        selected_columns = None
        if ENABLE_COLUMN_SELECTOR and COLUMN_SELECTOR_AVAILABLE:
            selected_columns = render_column_selector(
                aggregated_df,  # Passer le DataFrame complet
                managers['preferences']
            )
        
        # Filtrer les colonnes si un profil est sélectionné
        if selected_columns:
            # Garder unique_substance_id et source_list même si pas dans la sélection
            essential_cols = ['unique_substance_id', 'source_list']
            cols_to_keep = list(set(selected_columns + essential_cols))
            
            # Filtrer uniquement les colonnes qui existent
            cols_to_keep = [col for col in cols_to_keep if col in aggregated_df.columns]
            
            aggregated_df_display = aggregated_df[cols_to_keep].copy()
            logger.info(f"Colonnes filtrées: {len(cols_to_keep)} sur {len(aggregated_df.columns)}")
        else:
            aggregated_df_display = aggregated_df.copy()
        
        # Section des filtres
        st.subheader("🔍 Filtres")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Filtre par liste source
            all_sources = ['Toutes'] + sorted(aggregated_df['source_list'].unique().tolist())
            selected_source = st.selectbox(
                "Liste Source",
                all_sources,
                key="source_filter"
            )
        
        with col2:
            # Filtre par CAS ID (recherche)
            cas_search = st.text_input(
                "Recherche CAS ID",
                placeholder="Ex: 50-00-0",
                key="cas_search"
            )
        
        # Filtre par nom de substance
        substance_search = st.text_input(
            "Recherche Substance",
            placeholder="Ex: formaldehyde",
            key="substance_search"
        )
        
        # Appliquer les filtres
        filtered_df = aggregated_df_display.copy()
        
        if selected_source != 'Toutes':
            filtered_df = filtered_df[filtered_df['source_list'] == selected_source]
        
        if cas_search:
            if 'cas_id' in filtered_df.columns:
                filtered_df = filtered_df[
                    filtered_df['cas_id'].astype(str).str.contains(cas_search, case=False, na=False)
                ]
        
        if substance_search:
            if 'cas_name' in filtered_df.columns:
                filtered_df = filtered_df[
                    filtered_df['cas_name'].astype(str).str.contains(substance_search, case=False, na=False)
                ]
        
        # Afficher les métriques
        st.divider()
        st.subheader("📊 Statistiques")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Substances", len(aggregated_df))
        
        with col2:
            st.metric("Résultats Filtrés", len(filtered_df))
        
        with col3:
            unique_sources = aggregated_df['source_list'].nunique()
            st.metric("Sources Uniques", unique_sources)
        
        with col4:
            if 'cas_id' in aggregated_df.columns:
                unique_cas = aggregated_df['cas_id'].nunique()
                st.metric("CAS Uniques", unique_cas)
            else:
                st.metric("CAS Uniques", "N/A")
        
        # Afficher le tableau
        st.divider()
        st.subheader("📋 Données")
        
        # Options d'affichage
        show_all = st.checkbox("Afficher toutes les lignes (peut être lent)", value=False)
        
        if show_all:
            st.dataframe(
                filtered_df,
                use_container_width=True,
                hide_index=True
            )
        else:
            # Limiter à 1000 lignes pour la performance
            display_limit = min(1000, len(filtered_df))
            st.dataframe(
                filtered_df.head(display_limit),
                use_container_width=True,
                hide_index=True
            )
            
            if len(filtered_df) > display_limit:
                st.info(f"ℹ️ Affichage limité aux {display_limit} premières lignes. "
                       f"Cochez 'Afficher toutes les lignes' pour voir les {len(filtered_df)} résultats.")
        
        # Boutons d'export
        st.divider()
        st.subheader("💾 Export")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Export CSV
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Télécharger CSV",
                data=csv,
                file_name=f"donnees_agregees_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            # Export Excel
            from io import BytesIO
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                filtered_df.to_excel(writer, index=False, sheet_name='Données Agrégées')
            
            st.download_button(
                label="📥 Télécharger Excel",
                data=output.getvalue(),
                file_name=f"donnees_agregees_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
    except FileNotFoundError:
        st.error("❌ Fichier de données agrégées non trouvé. Veuillez d'abord charger les données dans l'onglet 'Mise à Jour'.")
        logger.error("Fichier aggregated_data.xlsx non trouvé")
    
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement des données: {str(e)}")
        logger.error(f"Erreur dans l'onglet Données Agrégées: {str(e)}")
        st.exception(e)