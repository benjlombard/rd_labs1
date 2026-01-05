"""
Onglet Mise à Jour
Gestion de la mise à jour des données et détection des changements
"""

import streamlit as st
import pandas as pd
from typing import Dict
from datetime import datetime
import time

# Import du composant d'affichage des fichiers (optionnel)
try:
    from ui.components.file_detection_display import render_detected_files_section
    FILE_DISPLAY_AVAILABLE = True
except ImportError:
    FILE_DISPLAY_AVAILABLE = False


def render(managers: Dict):
    """
    Affiche l'onglet Mise à Jour
    
    Args:
        managers: Dictionnaire contenant tous les managers
                 - 'data': DataManager
                 - 'change': ChangeDetector
                 - 'history': HistoryManager
                 - 'watchlist': WatchlistManager
                 - 'risk': RiskAnalyzer
                 - 'alert': AlertSystem
    """
    from backend.logger import get_logger
    logger = get_logger()
    
    st.header("Mise à Jour des Données")
    
    st.info("Cette section permet de charger les nouvelles données et de détecter les changements.")
    
    # Afficher les fichiers sources détectés (si le composant est disponible)
    if FILE_DISPLAY_AVAILABLE:
        render_detected_files_section(managers['data'], expanded=False)
        st.divider()
    
    if st.button("Charger et Agréger les Données", type="primary"):
        logger.info("=" * 80)
        logger.info("DÉBUT DU PROCESSUS DE CHARGEMENT ET AGRÉGATION")
        logger.info("=" * 80)

        with st.spinner("Chargement des données en cours..."):
            try:
                logger.info("ÉTAPE 1: Chargement de l'ancien fichier agrégé")
                old_aggregated = managers['data'].load_aggregated_data()
                logger.info(f"✓ Ancien fichier agrégé chargé: {len(old_aggregated)} enregistrements")
                if not old_aggregated.empty:
                    logger.info(f"  - Colonnes: {list(old_aggregated.columns)[:5]}... ({len(old_aggregated.columns)} total)")
                    if 'unique_substance_id' in old_aggregated.columns:
                        duplicates = old_aggregated['unique_substance_id'].duplicated().sum()
                        logger.info(f"  - Doublons détectés: {duplicates}")
                    else:
                        logger.warning("  - unique_substance_id manquant dans l'ancien fichier")

                logger.info("ÉTAPE 2: Chargement des nouvelles listes depuis les fichiers sources")
                # IMPORTANT: Charger AVANT l'archivage et garder en mémoire
                new_lists = managers['data'].load_all_lists()
                logger.info(f"✓ Nouvelles listes chargées et gardées en mémoire: {list(new_lists.keys())}")
                for list_name, df in new_lists.items():
                    logger.info(f"  - {list_name}: {len(df)} enregistrements, colonnes: {list(df.columns)[:3]}...")

                logger.info("ÉTAPE 3: Agrégation des nouvelles données")
                # Passer les listes déjà chargées pour éviter de recharger les fichiers
                aggregated_df = managers['data'].aggregate_all_data(preloaded_lists=new_lists)
                logger.info(f"✓ Nouvelles données agrégées: {len(aggregated_df)} enregistrements")

                logger.info("ÉTAPE 4: Sauvegarde du fichier agrégé")
                was_saved = managers['data'].save_aggregated_data(aggregated_df)
                logger.info(f"✓ Résultat de la sauvegarde: was_saved={was_saved}")

                # Invalider le cache pour forcer le rechargement des données dans les autres onglets
                st.cache_data.clear()
                logger.info("✓ Cache invalidé pour forcer le rechargement des données")

                # ARCHIVAGE ET SUPPRESSION APRÈS LA SAUVEGARDE ET LE CHARGEMENT
                logger.info("ÉTAPE 5: Archivage et suppression des fichiers sources")
                logger.info("  (Les données sont déjà en mémoire, on peut supprimer les fichiers)")
                try:
                    archived_count = managers['data'].archive_source_files()
                    if archived_count > 0:
                        st.info(f"📦 {archived_count} fichiers archivés dans data/archives/ et supprimés de data/input/")
                        logger.info(f"✓ Archivage et nettoyage réussi: {archived_count} fichiers")
                    else:
                        st.info("ℹ️ Aucun fichier à archiver (déjà archivés lors d'une exécution précédente)")
                        logger.info("  - Aucun fichier à archiver (déjà fait)")
                except FileNotFoundError as e:
                    # Fichiers déjà archivés/supprimés - ce n'est pas une erreur critique
                    logger.info(f"  - Fichiers déjà archivés: {str(e)}")
                    st.info("ℹ️ Fichiers sources déjà archivés lors d'une exécution précédente")
                except Exception as e:
                    # Erreur non critique, on continue le processus
                    logger.warning(f"⚠ Avertissement lors de l'archivage (non bloquante): {str(e)}")
                    st.warning(f"⚠️ Avertissement lors de l'archivage: {str(e)}")

                # Créer des placeholders pour les messages temporaires
                message_placeholder1 = st.empty()
                message_placeholder2 = st.empty()

                if was_saved:
                    message_placeholder1.success(f"Données agrégées et sauvegardées avec succès! {len(aggregated_df)} enregistrements chargés.")
                else:
                    message_placeholder1.info(f"Données agrégées ({len(aggregated_df)} enregistrements). Aucun changement détecté, fichier non modifié.")

                # La détection des changements utilise les données DÉJÀ EN MÉMOIRE
                # On ne recharge PAS les fichiers (ils ont été supprimés)
                with st.spinner("Détection des changements..."):
                    logger.info("ÉTAPE 6: Détection des changements")
                    logger.info("  (Utilisation des données déjà chargées en mémoire)")
                    
                    # Préparer le dictionnaire des anciennes listes. Il sera vide lors du premier chargement.
                    old_lists = {}
                    if not old_aggregated.empty:
                        # Vérifier que les colonnes nécessaires existent
                        if 'cas_id' not in old_aggregated.columns or 'cas_name' not in old_aggregated.columns:
                            logger.error(f"✗ Colonnes manquantes dans old_aggregated. Colonnes présentes: {list(old_aggregated.columns)}")
                            st.error("Erreur: Le fichier agrégé ne contient pas les colonnes attendues (cas_id, cas_name). Veuillez vérifier la configuration.")
                        else:
                            for list_name in old_aggregated['source_list'].unique():
                                old_lists[list_name] = old_aggregated[old_aggregated['source_list'] == list_name].copy()
                            logger.info(f"  - Anciennes listes préparées: {list(old_lists.keys())}")
                    else:
                        logger.info("  - Aucune ancienne liste (premier chargement)")
                    
                    logger.info("ÉTAPE 7: Comparaison des anciennes et nouvelles listes")
                    logger.info(f"  - Anciennes listes: {len(old_lists)}")
                    logger.info(f"  - Nouvelles listes: {len(new_lists)}")
                    changes_df = managers['change'].detect_all_changes(old_lists, new_lists)
                    logger.info(f"✓ Changements détectés: {len(changes_df)} enregistrements")

                    # Créer le tableau récapitulatif par liste source
                    st.subheader("📋 Récapitulatif des Changements par Liste")

                    summary_data = []
                    all_list_names = set(old_lists.keys()) | set(new_lists.keys())
                    logger.info(f"  - Traitement de {len(all_list_names)} listes pour le récapitulatif")
                    for list_name in all_list_names:
                        list_changes = changes_df[changes_df['source_list'] == list_name] if not changes_df.empty else pd.DataFrame()
                        insertions = len(list_changes[list_changes['change_type'] == 'insertion']) if not list_changes.empty else 0
                        modifications = len(list_changes[list_changes['change_type'] == 'modification']) if not list_changes.empty else 0
                        deletions = len(list_changes[list_changes['change_type'] == 'deletion']) if not list_changes.empty else 0
                        
                        status = '⚪ Pas de changement'
                        if insertions > 0 or modifications > 0 or deletions > 0:
                            status = '✅ Changements détectés'

                        summary_data.append({
                            'Liste Source': list_name,
                            'Insertions': insertions,
                            'Modifications': modifications,
                            'Suppressions': deletions,
                            'Statut': status
                        })
                        
                        logger.info(f"    • {list_name}: +{insertions} ~{modifications} -{deletions}")

                    summary_df = pd.DataFrame(summary_data)
                    
                    # Sauvegarder le résumé actuel dans l'historique
                    managers['history'].save_summary(summary_df)
                    logger.info("✓ Résumé sauvegardé dans l'historique")
                    
                    # Charger et afficher l'historique complet des résumés
                    summary_history_df = managers['history'].load_summary_history()
                    st.dataframe(summary_history_df, use_container_width=True, hide_index=True)

                    # Afficher les métriques de résumé
                    st.subheader("📊 Résumé de la Mise à Jour")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    total_substances = len(aggregated_df)
                    insertions = len(changes_df[changes_df['change_type'] == 'insertion']) if not changes_df.empty else 0
                    deletions = len(changes_df[changes_df['change_type'] == 'deletion']) if not changes_df.empty else 0
                    modifications = len(changes_df[changes_df['change_type'] == 'modification']) if not changes_df.empty else 0
                    
                    # Corriger le nombre d'insertions pour le premier chargement
                    if old_aggregated.empty and total_substances > 0:
                        insertions = total_substances

                    col1.metric("Substances Traitées", total_substances)
                    col2.metric("✅ Insertions", insertions)
                    col3.metric("❌ Suppressions", deletions)
                    col4.metric("✏️ Modifications", modifications)

                    if not changes_df.empty:
                        logger.info("ÉTAPE 8: Sauvegarde des changements dans l'historique")
                        managers['history'].save_changes(changes_df)
                        logger.info(f"✓ Historique mis à jour avec {len(changes_df)} changements")

                        # Créer les alertes pour les substances watchlistées
                        logger.info("ÉTAPE 9: Création des alertes")
                        managers['alert'].create_alerts_from_changes(
                            changes_df,
                            managers['watchlist'],
                            managers['risk'],
                            aggregated_df,
                            managers['history'].load_history()
                        )
                        logger.info("✓ Alertes créées avec succès")

                        message_placeholder2.success(f"{len(changes_df)} changements détectés et enregistrés!")

                        st.subheader("Aperçu des Changements")
                        st.dataframe(changes_df.head(10), use_container_width=True)
                    else:
                        logger.info("  - Aucun changement détecté")
                        message_placeholder2.info("Aucun changement détecté.")

                logger.info("=" * 80)
                logger.info("✓✓✓ FIN DU PROCESSUS DE CHARGEMENT ET AGRÉGATION - SUCCÈS ✓✓✓")
                logger.info("=" * 80)

                # Afficher un bouton de rafraîchissement
                st.divider()
                st.success("✅ Mise à jour terminée avec succès! Les données sont maintenant visibles dans l'onglet 'Données Agrégées'.")
                
                if st.button("🔄 Rafraîchir l'Application", type="primary", use_container_width=True):
                    st.rerun()

                # Faire disparaître les messages après 5 secondes
                time.sleep(5)
                message_placeholder1.empty()
                message_placeholder2.empty()

            except Exception as e:
                logger.error("=" * 80)
                logger.error("✗✗✗ FIN DU PROCESSUS DE CHARGEMENT ET AGRÉGATION - ERREUR ✗✗✗")
                logger.error(f"Exception: {str(e)}")
                logger.error("=" * 80)
                logger.exception("Traceback complet:")
                st.error(f"Erreur lors de la mise à jour: {str(e)}")
                st.exception(e)