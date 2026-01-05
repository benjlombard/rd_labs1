"""
Composant d'affichage des fichiers sources détectés
Module optionnel pour visualiser quels fichiers sont utilisés
"""

import streamlit as st
import pandas as pd
from typing import Dict


def render_detected_files_section(data_manager, expanded: bool = False):
    """
    Affiche une section montrant les fichiers sources détectés
    
    Args:
        data_manager: Instance de DataManager
        expanded: Si True, l'expander est ouvert par défaut
    """
    
    with st.expander("📁 Fichiers Sources Détectés", expanded=expanded):
        st.markdown("Liste des fichiers Excel utilisés pour l'agrégation des données")
        
        # Bouton de rafraîchissement en haut à droite
        col_title, col_refresh = st.columns([4, 1])
        with col_refresh:
            if st.button("🔄", key="refresh_files_detection", help="Rafraîchir la détection"):
                st.rerun()
        
        try:
            # Récupérer les informations sur les fichiers (SANS cache)
            files_info = data_manager.get_detected_files_info()
            
            if not files_info:
                st.warning("⚠️ Aucun fichier détecté")
                return
            
            # Convertir en DataFrame pour affichage
            df = pd.DataFrame(files_info)
            
            # Compter les statuts (corriger pour matcher les nouveaux statuts avec émojis)
            ok_count = sum(1 for f in files_info if '✅' in f['status'] or f['status'] == 'OK')
            disabled_count = sum(1 for f in files_info if '⏸️' in f['status'] or 'DÉSACTIVÉE' in f['status'])
            error_count = len(files_info) - ok_count - disabled_count
            
            # Afficher les métriques
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Listes", len(files_info))
            
            with col2:
                st.metric("✅ Actives", ok_count)
            
            with col3:
                st.metric("⏸️ Désactivées", disabled_count)
            
            with col4:
                st.metric("❌ Erreurs", error_count)
            
            st.divider()
            
            # Afficher le tableau
            # Sélectionner les colonnes à afficher
            display_columns = ['description', 'file_name', 'last_modified', 'size_mb', 'status']
            
            # Renommer pour affichage
            df_display = df[display_columns].copy()
            df_display.columns = ['Liste', 'Fichier', 'Dernière Modification', 'Taille (MB)', 'Statut']
            
            # Styliser le tableau
            def highlight_status(row):
                status = row['Statut']
                if '✅' in status or status == 'OK':
                    # Vert pour OK
                    return ['background-color: #d4edda'] * len(row)
                elif '⏸️' in status or 'DÉSACTIVÉE' in status:
                    # Gris pour désactivé
                    return ['background-color: #e2e3e5'] * len(row)
                else:
                    # Rouge pour erreur
                    return ['background-color: #f8d7da'] * len(row)
            
            styled_df = df_display.style.apply(highlight_status, axis=1)
            
            st.dataframe(
                styled_df,
                use_container_width=True,
                hide_index=True,
                height=400
            )
            
            # Afficher les erreurs détaillées si présentes
            errors = [f for f in files_info if '❌' in f['status'] or ('OK' not in f['status'] and 'DÉSACTIVÉE' not in f['status'])]
            if errors:
                st.divider()
                st.error("❌ Détails des Erreurs")
                
                for error_info in errors:
                    with st.expander(f"⚠️ {error_info['description']} ({error_info['list_name']})"):
                        st.code(error_info.get('error', 'Erreur inconnue'))
                        
                        # Suggestions
                        st.markdown("**💡 Suggestions:**")
                        st.markdown("- Vérifiez que le fichier existe dans `data/input/`")
                        st.markdown("- Vérifiez le pattern dans `config.yaml`")
                        st.markdown("- Vérifiez les permissions du fichier")
        
        except Exception as e:
            st.error(f"❌ Erreur lors de la détection des fichiers: {str(e)}")
            st.exception(e)


def render_file_mapping_help():
    """
    Affiche une aide sur la configuration des fichiers
    """
    with st.expander("ℹ️ Aide - Configuration des Fichiers"):
        st.markdown("""
        ### 📝 Comment Configurer les Fichiers Sources
        
        Dans `config.yaml`, vous avez 3 options pour spécifier les fichiers :
        
        #### Option 1 : Pattern avec Wildcard (Recommandé) ⭐
        ```yaml
        - name: "authorisation_list"
          file_pattern: "authorisation_list_full-*.xlsx"
        ```
        - ✅ Trouve automatiquement le fichier le plus récent
        - ✅ Pas besoin de modifier le config à chaque nouveau fichier
        - ✅ Supporte `*` comme wildcard
        
        #### Option 2 : Préfixe
        ```yaml
        - name: "authorisation_list"
          file_prefix: "authorisation_list_full"
        ```
        - ✅ Trouve tous les fichiers commençant par ce préfixe
        - ✅ Sélectionne automatiquement le plus récent
        
        #### Option 3 : Nom Exact (Legacy)
        ```yaml
        - name: "authorisation_list"
          file: "authorisation_list_full-2025-09-13.xlsx"
        ```
        - ⚠️ Nécessite de modifier le config à chaque nouveau fichier
        - ✅ Contrôle précis sur quel fichier est utilisé
        
        ### 🔍 Ordre de Priorité
        
        Si plusieurs options sont spécifiées, l'ordre de priorité est :
        1. `file_pattern` (si présent)
        2. `file_prefix` (si présent)
        3. `file` (fallback)
        
        ### 📂 Emplacement des Fichiers
        
        Tous les fichiers doivent être placés dans :
        ```
        data/input/
        ```
        
        ### 🎯 Exemple Complet
        
        ```yaml
        source_files:
          lists:
            - name: "authorisation_list"
              file_pattern: "authorisation_list_full-*.xlsx"
              description: "Liste d'autorisation"
            
            - name: "restriction_list"
              file_prefix: "restriction_list_full"
              description: "Liste restriction"
            
            - name: "candidate_list"
              file: "candidate_list_full-2025-09-15.xlsx"
              description: "Liste candidate (version spécifique)"
        ```
        
        ### ⚡ Conseils
        
        - Utilisez `file_pattern` pour les fichiers qui changent souvent
        - Gardez une structure de nommage cohérente
        - Le système prend toujours le fichier **le plus récent** si plusieurs correspondent
        """)


def render_compact_files_info(data_manager):
    """
    Version compacte pour afficher dans la sidebar ou en en-tête
    
    Args:
        data_manager: Instance de DataManager
    """
    try:
        files_info = data_manager.get_detected_files_info()
        
        if not files_info:
            st.caption("⚠️ Aucun fichier source détecté")
            return
        
        ok_count = sum(1 for f in files_info if f['status'] == 'OK')
        error_count = len(files_info) - ok_count
        
        if error_count > 0:
            st.warning(f"📁 Fichiers: {ok_count}/{len(files_info)} OK - {error_count} erreur(s)")
        else:
            st.success(f"📁 Fichiers: {ok_count}/{len(files_info)} détectés")
        
    except Exception as e:
        st.caption(f"⚠️ Erreur détection fichiers: {str(e)}")