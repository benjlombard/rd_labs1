"""
Onglet Données Agrégées
Affiche les données agrégées avec filtres avancés et options de visualisation
"""

import streamlit as st
import pandas as pd
from typing import Dict
from datetime import datetime
import time


def render(managers: Dict):
    """
    Affiche l'onglet Données Agrégées
    
    Args:
        managers: Dictionnaire contenant tous les managers
                 - 'data': DataManager
                 - 'watchlist': WatchlistManager
                 - 'risk': RiskAnalyzer
                 - 'history': HistoryManager
    """
    st.header("Visualisation des Substances Chimiques")
    
    try:
        aggregated_df = managers['data'].load_aggregated_data()
        
        if aggregated_df.empty:
            st.info("Aucune donnée agrégée disponible. Veuillez effectuer une mise à jour dans l'onglet 'Mise à Jour'.")
            return
        
        # Section Watchlist Management
        st.subheader("🔖 Gestion des Watchlists")
        with st.expander("Ajouter des substances à une watchlist", expanded=False):
            watchlists = managers['watchlist'].load_watchlists()
            
            if not watchlists:
                st.info("Aucune watchlist créée. Créez-en une dans l'onglet 'Ma Surveillance'.")
            else:
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    selected_watchlist = st.selectbox(
                        "Sélectionner une watchlist",
                        options=[wl['name'] for wl in watchlists],
                        key="watchlist_select_agg"
                    )
                
                with col2:
                    cas_id_to_add = st.text_input(
                        "CAS ID à ajouter",
                        key="cas_id_to_add_agg"
                    )
                
                with col3:
                    st.write("")  # Spacer
                    st.write("")  # Spacer
                    if st.button("➕ Ajouter", key="add_to_watchlist_btn"):
                        if cas_id_to_add:
                            # Trouver l'ID de la watchlist
                            wl_id = next((wl['id'] for wl in watchlists if wl['name'] == selected_watchlist), None)
                            if wl_id:
                                success = managers['watchlist'].add_cas_to_watchlist(wl_id, cas_id_to_add)
                                if success:
                                    st.success(f"✅ {cas_id_to_add} ajouté à '{selected_watchlist}'")
                                    time.sleep(2)
                                    st.rerun()
                                else:
                                    st.warning(f"⚠️ {cas_id_to_add} est déjà dans '{selected_watchlist}'")
                        else:
                            st.error("Veuillez entrer un CAS ID")
        
        st.divider()
        
        st.subheader("Filtres")
        
        # Initialiser session_state si nécessaire
        if 'cas_name_filter_agg' not in st.session_state:
            st.session_state.cas_name_filter_agg = ""
        if 'cas_id_filter_agg' not in st.session_state:
            st.session_state.cas_id_filter_agg = ""
        if 'source_list_filter_agg' not in st.session_state:
            st.session_state.source_list_filter_agg = "Toutes"
        if 'updated_today_filter_agg' not in st.session_state:
            st.session_state.updated_today_filter_agg = False
        if 'created_today_filter_agg' not in st.session_state:
            st.session_state.created_today_filter_agg = False
        
        # Créer une ligne pour les filtres et le bouton
        col1, col2, col3, col_btn = st.columns([2, 2, 2, 1])
        
        with col1:
            st.text_input(
                "Filtrer par nom de substance (cas_name)",
                key="cas_name_filter_agg"
            )
        
        with col2:
            st.text_input(
                "Filtrer par identifiant CAS (cas_id)",
                key="cas_id_filter_agg"
            )
        
        with col3:
            source_lists = ['Toutes'] + sorted(list(aggregated_df['source_list'].unique()))
            st.selectbox(
                "Filtrer par liste source",
                source_lists,
                key="source_list_filter_agg",
                index=source_lists.index(st.session_state.source_list_filter_agg) if st.session_state.source_list_filter_agg in source_lists else 0
            )
        
        # Deuxième ligne pour les filtres de date
        col1_date, col2_date, col3_date, col_btn_space = st.columns([2, 2, 2, 1])
        
        with col1_date:
            st.checkbox(
                "📅 Mis à jour aujourd'hui",
                key="updated_today_filter_agg",
                help="Afficher uniquement les substances mises à jour aujourd'hui"
            )
        
        with col2_date:
            st.checkbox(
                "🆕 Créé aujourd'hui",
                key="created_today_filter_agg",
                help="Afficher uniquement les substances créées aujourd'hui"
            )
        
        # Définir le callback pour réinitialiser les filtres
        def reset_filters_callback():
            st.session_state.cas_name_filter_agg = ""
            st.session_state.cas_id_filter_agg = ""
            st.session_state.source_list_filter_agg = "Toutes"
            st.session_state.updated_today_filter_agg = False
            st.session_state.created_today_filter_agg = False
        
        with col_btn:
            st.write("")  # Spacer for vertical alignment
            st.write("")  # Spacer for vertical alignment
            st.button("🔄 Reset Filtres", on_click=reset_filters_callback)
        
        filtered_df = aggregated_df.copy()
        
        # Utiliser directement st.session_state pour filtrer
        if st.session_state.cas_name_filter_agg:
            filtered_df = filtered_df[
                filtered_df['cas_name'].astype(str).str.contains(st.session_state.cas_name_filter_agg, case=False, na=False)
            ]
        
        if st.session_state.cas_id_filter_agg:
            filtered_df = filtered_df[
                filtered_df['cas_id'].astype(str).str.contains(st.session_state.cas_id_filter_agg, case=False, na=False)
            ]
        
        if st.session_state.source_list_filter_agg != 'Toutes':
            filtered_df = filtered_df[filtered_df['source_list'] == st.session_state.source_list_filter_agg]
        
        # Filtrer par date de mise à jour (aujourd'hui)
        if st.session_state.updated_today_filter_agg:
            if 'updated_at' in filtered_df.columns:
                today = datetime.now().date()
                # Convertir updated_at en datetime si c'est une chaîne
                filtered_df['_temp_updated'] = pd.to_datetime(filtered_df['updated_at'], errors='coerce')
                filtered_df = filtered_df[filtered_df['_temp_updated'].dt.date == today]
                filtered_df = filtered_df.drop(columns=['_temp_updated'])
            else:
                st.warning("⚠️ La colonne 'updated_at' n'existe pas dans les données.")
        
        # Filtrer par date de création (aujourd'hui)
        if st.session_state.created_today_filter_agg:
            if 'created_at' in filtered_df.columns:
                today = datetime.now().date()
                # Convertir created_at en datetime si c'est une chaîne
                filtered_df['_temp_created'] = pd.to_datetime(filtered_df['created_at'], errors='coerce')
                filtered_df = filtered_df[filtered_df['_temp_created'].dt.date == today]
                filtered_df = filtered_df.drop(columns=['_temp_created'])
            else:
                st.warning("⚠️ La colonne 'created_at' n'existe pas dans les données.")
        
        st.subheader(f"Tableau Agrégé ({len(filtered_df)} substances)")
        
        if not filtered_df.empty:
            st.dataframe(
                filtered_df,
                use_container_width=True,
                height=500
            )
            
            st.download_button(
                label="Télécharger les données filtrées (CSV)",
                data=filtered_df.to_csv(index=False).encode('utf-8'),
                file_name='substances_filtrees.csv',
                mime='text/csv',
            )
        else:
            st.warning("Aucune substance ne correspond aux filtres appliqués.")
        
        st.subheader("Statistiques")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total de substances", len(aggregated_df))
        
        with col2:
            st.metric("Substances uniques (CAS ID)", aggregated_df['cas_id'].nunique())
        
        with col3:
            st.metric("Nombre de listes sources", aggregated_df['source_list'].nunique())
        
        if 'source_list' in aggregated_df.columns:
            st.subheader("Répartition par liste source")
            source_counts = aggregated_df['source_list'].value_counts()
            st.bar_chart(source_counts)
    
    except Exception as e:
        st.error(f"Erreur lors du chargement des données: {str(e)}")