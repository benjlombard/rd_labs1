"""
Onglet Historique des Changements
Affiche l'historique complet des modifications des substances chimiques
"""

import streamlit as st
import pandas as pd
from typing import Dict


def render(managers: Dict):
    """
    Affiche l'onglet Historique des Changements
    
    Args:
        managers: Dictionnaire contenant tous les managers
                 - 'history': HistoryManager
                 - 'data': DataManager
    """
    st.header("Historique des Changements")
    
    try:
        # Charger l'historique
        history_df = managers['history'].load_history()
        
        if history_df.empty:
            st.info("Aucun changement enregistré pour le moment.")
            return
        
        # Afficher les filtres
        st.subheader("Filtres")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            change_types = ['Tous'] + list(history_df['change_type'].unique())
            selected_type = st.selectbox("Type de changement", change_types)
        
        with col2:
            source_lists = ['Toutes'] + list(history_df['source_list'].unique())
            selected_list = st.selectbox("Liste source", source_lists)
        
        with col3:
            cas_search = st.text_input("Rechercher par CAS ID")
        
        # Appliquer les filtres
        filtered_history = history_df.copy()
        
        if selected_type != 'Tous':
            filtered_history = filtered_history[filtered_history['change_type'] == selected_type]
        
        if selected_list != 'Toutes':
            filtered_history = filtered_history[filtered_history['source_list'] == selected_list]
        
        if cas_search:
            filtered_history = filtered_history[
                filtered_history['cas_id'].astype(str).str.contains(cas_search, case=False, na=False)
            ]
        
        # Afficher le tableau des changements
        st.subheader(f"Changements Récents ({len(filtered_history)} enregistrements)")
        
        if not filtered_history.empty:
            display_columns = ['timestamp', 'change_type', 'source_list', 'cas_id', 'cas_name']
            if 'modified_fields' in filtered_history.columns:
                display_columns.append('modified_fields')
            
            available_columns = [col for col in display_columns if col in filtered_history.columns]
            
            st.dataframe(
                filtered_history[available_columns],
                use_container_width=True,
                height=500
            )
            
            st.download_button(
                label="Télécharger l'historique (CSV)",
                data=filtered_history.to_csv(index=False).encode('utf-8'),
                file_name='historique_changements.csv',
                mime='text/csv',
            )
        else:
            st.warning("Aucun changement ne correspond aux filtres appliqués.")
        
        # Afficher les statistiques
        st.subheader("Statistiques des Changements")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'change_type' in history_df.columns:
                insertions = len(history_df[history_df['change_type'] == 'insertion'])
                st.metric("Insertions", insertions)
        
        with col2:
            if 'change_type' in history_df.columns:
                deletions = len(history_df[history_df['change_type'] == 'deletion'])
                st.metric("Suppressions", deletions)
        
        with col3:
            if 'change_type' in history_df.columns:
                modifications = len(history_df[history_df['change_type'] == 'modification'])
                st.metric("Modifications", modifications)
    
    except Exception as e:
        st.error(f"Erreur lors du chargement de l'historique: {str(e)}")