"""
Composant de sélection de colonnes
Module autonome pour gérer l'affichage des colonnes dans un DataFrame
"""

import streamlit as st
import pandas as pd
from typing import List, Optional


def render_column_selector(
    df: pd.DataFrame,
    preferences_manager,
    key_prefix: str = "col_selector",
    enabled: bool = True
) -> List[str]:
    """
    Affiche un sélecteur de colonnes pour un DataFrame
    
    Args:
        df: DataFrame dont on veut sélectionner les colonnes
        preferences_manager: Instance de PreferencesManager
        key_prefix: Préfixe pour les clés Streamlit (pour éviter les conflits)
        enabled: Si False, retourne toutes les colonnes sans afficher le sélecteur
        
    Returns:
        Liste des colonnes sélectionnées à afficher
    """
    
    # Si le sélecteur est désactivé, retourner toutes les colonnes
    if not enabled:
        return list(df.columns)
    
    # Récupérer toutes les colonnes disponibles
    all_columns = list(df.columns)
    
    # Récupérer la sélection actuelle
    current_selection = preferences_manager.get_column_selection()
    current_profile = current_selection.get('profile', 'essentials')
    
    # Afficher le sélecteur dans un expander
    with st.expander("⚙️ Configuration de l'Affichage des Colonnes", expanded=False):
        
        # Description
        st.markdown("📋 **Choisissez les colonnes à afficher dans le tableau**")
        st.divider()
        
        # Récupérer les profils disponibles
        profiles = preferences_manager.get_available_profiles()
        
        # Radio buttons pour les profils
        profile_options = {
            key: f"{value['name']} - {value['description']}" 
            for key, value in profiles.items()
        }
        
        selected_profile = st.radio(
            "Profil d'affichage",
            options=list(profile_options.keys()),
            format_func=lambda x: profile_options[x],
            index=list(profile_options.keys()).index(current_profile) if current_profile in profile_options else 0,
            key=f"{key_prefix}_profile_radio"
        )
        
        # Si profil "custom", afficher le multiselect
        if selected_profile == 'custom':
            st.divider()
            st.markdown("**🎨 Sélection Personnalisée**")
            
            # Récupérer les colonnes actuellement sélectionnées pour custom
            current_custom = current_selection.get('custom_columns')
            if not current_custom or not set(current_custom).issubset(set(all_columns)):
                # Si pas de sélection custom ou colonnes invalides, utiliser essentials
                current_custom = preferences_manager.get_columns_for_profile('essentials', all_columns)
            
            # Multiselect pour la sélection personnalisée
            custom_columns = st.multiselect(
                "Colonnes à afficher",
                options=all_columns,
                default=current_custom,
                key=f"{key_prefix}_custom_multiselect",
                help="Sélectionnez les colonnes que vous souhaitez afficher"
            )
            
            selected_columns = custom_columns
            
        else:
            # Pour les profils prédéfinis, récupérer les colonnes
            selected_columns = preferences_manager.get_columns_for_profile(selected_profile, all_columns)
            
            # Afficher un aperçu des colonnes qui seront affichées
            st.divider()
            st.markdown(f"**📊 Colonnes affichées** ({len(selected_columns)}/{len(all_columns)})")
            
            # Afficher les colonnes dans des colonnes Streamlit (max 3 par ligne)
            num_cols_per_row = 3
            for i in range(0, len(selected_columns), num_cols_per_row):
                cols = st.columns(num_cols_per_row)
                for j, col in enumerate(selected_columns[i:i+num_cols_per_row]):
                    with cols[j]:
                        st.caption(f"• {col}")
        
        # Vérifier si la sélection a changé
        if selected_profile == 'custom':
            has_changed = (
                selected_profile != current_profile or 
                selected_columns != current_selection.get('custom_columns')
            )
        else:
            has_changed = selected_profile != current_profile
        
        # Boutons d'action
        st.divider()
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            if st.button(
                "💾 Sauvegarder ma sélection",
                use_container_width=True,
                key=f"{key_prefix}_save_btn",
                disabled=not has_changed,
                help="Sauvegarder cette configuration pour les prochaines sessions"
            ):
                preferences_manager.set_column_selection(
                    profile=selected_profile,
                    custom_columns=selected_columns if selected_profile == 'custom' else None
                )
                if preferences_manager.save_preferences():
                    st.success("✅ Configuration sauvegardée !")
                    st.rerun()
                else:
                    st.error("❌ Erreur lors de la sauvegarde")
        
        with col2:
            if st.button(
                "🔄 Réinitialiser",
                use_container_width=True,
                key=f"{key_prefix}_reset_btn",
                help="Revenir aux paramètres par défaut"
            ):
                preferences_manager.reset_to_default()
                st.success("✅ Configuration réinitialisée !")
                st.rerun()
        
        with col3:
            # Indicateur de changements non sauvegardés
            if has_changed:
                st.warning("⚠️")
        
        # Avertissement si aucune colonne n'est sélectionnée
        if not selected_columns:
            st.error("⚠️ Aucune colonne sélectionnée ! Le tableau sera vide.")
    
    return selected_columns


def render_column_selector_simple(
    df: pd.DataFrame,
    default_columns: Optional[List[str]] = None,
    key_prefix: str = "simple_col_selector",
    enabled: bool = True
) -> List[str]:
    """
    Version simplifiée du sélecteur de colonnes sans persistence
    Utilise uniquement st.session_state
    
    Args:
        df: DataFrame dont on veut sélectionner les colonnes
        default_columns: Colonnes à afficher par défaut (si None, toutes les colonnes)
        key_prefix: Préfixe pour les clés Streamlit
        enabled: Si False, retourne toutes les colonnes
        
    Returns:
        Liste des colonnes sélectionnées
    """
    
    if not enabled:
        return list(df.columns)
    
    all_columns = list(df.columns)
    
    # Initialiser session_state si nécessaire
    session_key = f"{key_prefix}_selected_columns"
    if session_key not in st.session_state:
        st.session_state[session_key] = default_columns if default_columns else all_columns
    
    with st.expander("⚙️ Sélection des Colonnes", expanded=False):
        selected = st.multiselect(
            "Colonnes à afficher",
            options=all_columns,
            default=st.session_state[session_key],
            key=f"{key_prefix}_multiselect"
        )
        
        st.session_state[session_key] = selected
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Toutes", key=f"{key_prefix}_all_btn", use_container_width=True):
                st.session_state[session_key] = all_columns
                st.rerun()
        
        with col2:
            if st.button("Essentielles", key=f"{key_prefix}_essential_btn", use_container_width=True):
                essentials = ['cas_id', 'cas_name', 'source_list', 'ec_number']
                st.session_state[session_key] = [col for col in essentials if col in all_columns]
                st.rerun()
    
    return st.session_state[session_key]