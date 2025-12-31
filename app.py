import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import sys
from pathlib import Path
from datetime import datetime
import time

sys.path.append(str(Path(__file__).parent / "backend"))

from backend.data_manager import DataManager
from backend.change_detector import ChangeDetector
from backend.history_manager import HistoryManager
from backend.pdf_exporter import PDFExporter
from backend.watchlist_manager import WatchlistManager
from backend.risk_analyzer import RiskAnalyzer
from backend.alert_system import AlertSystem
from backend.logger import get_logger

logger = get_logger()


st.set_page_config(
    page_title="Suivi des Substances Chimiques ECHA",
    page_icon=":test_tube:",
    layout="wide"
)


@st.cache_resource
def initialize_managers():
    data_manager = DataManager()
    change_detector = ChangeDetector()
    history_manager = HistoryManager()
    watchlist_manager = WatchlistManager()
    risk_analyzer = RiskAnalyzer()
    alert_system = AlertSystem()
    return data_manager, change_detector, history_manager, watchlist_manager, risk_analyzer, alert_system


def main():
    st.title("Tableau de Bord - Substances Chimiques ECHA")

    data_manager, change_detector, history_manager, watchlist_manager, risk_analyzer, alert_system = initialize_managers()

    st.divider()
    display_pdf_export_section(data_manager, history_manager)
    st.divider()

    # Afficher le badge d'alertes non lues en haut
    unread_count = alert_system.get_unread_count()
    if unread_count > 0:
        st.warning(f"🔔 {unread_count} alerte(s) non lue(s) - Consultez l'onglet 'Ma Surveillance'")

    tabs = st.tabs(["Données Agrégées", "Historique des Changements", "Tendances", "Ma Surveillance", "Calendrier", "Mise à Jour"])

    with tabs[0]:
        display_aggregated_data(data_manager, watchlist_manager, risk_analyzer, history_manager)

    with tabs[1]:
        display_change_history(history_manager, data_manager)

    with tabs[2]:
        display_trends(data_manager, history_manager)

    with tabs[3]:
        display_watchlist_surveillance(watchlist_manager, risk_analyzer, alert_system, data_manager, history_manager)

    with tabs[4]:
        display_calendar_heatmap(history_manager, data_manager, risk_analyzer)

    with tabs[5]:
        display_update_section(data_manager, change_detector, history_manager, watchlist_manager, risk_analyzer, alert_system)


def display_aggregated_data(data_manager, watchlist_manager, risk_analyzer, history_manager):
    st.header("Visualisation des Substances Chimiques")

    try:
        aggregated_df = data_manager.load_aggregated_data()

        if aggregated_df.empty:
            st.info("Aucune donnée agrégée disponible. Veuillez effectuer une mise à jour dans l'onglet 'Mise à Jour'.")
            return

        # Section Watchlist Management
        st.subheader("🔖 Gestion des Watchlists")
        with st.expander("Ajouter des substances à une watchlist", expanded=False):
            watchlists = watchlist_manager.load_watchlists()

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
                                success = watchlist_manager.add_cas_to_watchlist(wl_id, cas_id_to_add)
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

        # Bouton Reset Filtres
        col_reset1, col_reset2 = st.columns([6, 1])
        with col_reset2:
            if st.button("🔄 Reset Filtres"):
                st.session_state.cas_name_filter_agg = ""
                st.session_state.cas_id_filter_agg = ""
                st.session_state.source_list_filter_agg = "Toutes"
                st.rerun()

        # Initialiser session_state si nécessaire
        if 'cas_name_filter_agg' not in st.session_state:
            st.session_state.cas_name_filter_agg = ""
        if 'cas_id_filter_agg' not in st.session_state:
            st.session_state.cas_id_filter_agg = ""
        if 'source_list_filter_agg' not in st.session_state:
            st.session_state.source_list_filter_agg = "Toutes"

        col1, col2, col3 = st.columns(3)

        with col1:
            cas_name_filter = st.text_input(
                "Filtrer par nom de substance (cas_name)",
                value=st.session_state.cas_name_filter_agg,
                key="cas_name_input_agg"
            )
            st.session_state.cas_name_filter_agg = cas_name_filter

        with col2:
            cas_id_filter = st.text_input(
                "Filtrer par identifiant CAS (cas_id)",
                value=st.session_state.cas_id_filter_agg,
                key="cas_id_input_agg"
            )
            st.session_state.cas_id_filter_agg = cas_id_filter

        with col3:
            source_lists = ['Toutes'] + sorted(list(aggregated_df['source_list'].unique()))
            selected_source_list = st.selectbox(
                "Filtrer par liste source",
                source_lists,
                index=source_lists.index(st.session_state.source_list_filter_agg) if st.session_state.source_list_filter_agg in source_lists else 0,
                key="source_list_select_agg"
            )
            st.session_state.source_list_filter_agg = selected_source_list

        filtered_df = aggregated_df.copy()

        if cas_name_filter:
            filtered_df = filtered_df[
                filtered_df['cas_name'].astype(str).str.contains(cas_name_filter, case=False, na=False)
            ]

        if cas_id_filter:
            filtered_df = filtered_df[
                filtered_df['cas_id'].astype(str).str.contains(cas_id_filter, case=False, na=False)
            ]

        if selected_source_list != 'Toutes':
            filtered_df = filtered_df[filtered_df['source_list'] == selected_source_list]

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


def display_change_history(history_manager, data_manager):
    st.header("Historique des Changements")

    try:
        history_df = history_manager.load_history()

        if history_df.empty:
            st.info("Aucun changement enregistré pour le moment.")
            return

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

        filtered_history = history_df.copy()

        if selected_type != 'Tous':
            filtered_history = filtered_history[filtered_history['change_type'] == selected_type]

        if selected_list != 'Toutes':
            filtered_history = filtered_history[filtered_history['source_list'] == selected_list]

        if cas_search:
            filtered_history = filtered_history[
                filtered_history['cas_id'].astype(str).str.contains(cas_search, case=False, na=False)
            ]

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


def display_update_section(data_manager, change_detector, history_manager, watchlist_manager, risk_analyzer, alert_system):
    st.header("Mise à Jour des Données")

    st.info("Cette section permet de charger les nouvelles données et de détecter les changements.")

    if st.button("Charger et Agréger les Données", type="primary"):
        with st.spinner("Archivage des fichiers sources..."):
            try:
                # Archiver les fichiers sources avant le chargement
                archived_count = data_manager.archive_source_files()
                if archived_count > 0:
                    st.info(f"📦 {archived_count} fichiers archivés dans data/archives/")

            except Exception as e:
                st.warning(f"Avertissement lors de l'archivage: {str(e)}")

        with st.spinner("Chargement des données en cours..."):
            try:
                old_aggregated = data_manager.load_aggregated_data()

                aggregated_df = data_manager.aggregate_all_data()
                was_saved = data_manager.save_aggregated_data(aggregated_df)

                # Créer des placeholders pour les messages temporaires
                message_placeholder1 = st.empty()
                message_placeholder2 = st.empty()

                if was_saved:
                    message_placeholder1.success(f"Données agrégées et sauvegardées avec succès! {len(aggregated_df)} enregistrements chargés.")
                else:
                    message_placeholder1.info(f"Données agrégées ({len(aggregated_df)} enregistrements). Aucun changement détecté, fichier non modifié.")

                if not old_aggregated.empty:
                    with st.spinner("Détection des changements..."):
                        old_lists = {}
                        new_lists = data_manager.load_all_lists()

                        for list_name in new_lists.keys():
                            old_list_data = old_aggregated[old_aggregated['source_list'] == list_name]
                            if not old_list_data.empty:
                                # Exclure les colonnes de timestamp lors de la comparaison
                                cols_to_drop = ['source_list', 'created_at', 'updated_at']
                                old_list_data = old_list_data.drop(columns=[col for col in cols_to_drop if col in old_list_data.columns])
                                common_cols = [col for col in new_lists[list_name].columns if col in old_list_data.columns]
                                old_lists[list_name] = old_list_data[common_cols]

                        changes_df = change_detector.detect_all_changes(old_lists, new_lists)

                        # Créer le tableau récapitulatif par liste source
                        st.subheader("📋 Récapitulatif des Changements par Liste")

                        summary_data = []
                        for list_config in data_manager.config['source_files']['lists']:
                            list_name = list_config['name']

                            # Filtrer les changements pour cette liste
                            if not changes_df.empty:
                                list_changes = changes_df[changes_df['source_list'] == list_name]

                                if not list_changes.empty:
                                    insertions = len(list_changes[list_changes['change_type'] == 'insertion'])
                                    modifications = len(list_changes[list_changes['change_type'] == 'modification'])
                                    deletions = len(list_changes[list_changes['change_type'] == 'deletion'])

                                    summary_data.append({
                                        'Liste Source': list_name,
                                        'Insertions': insertions,
                                        'Modifications': modifications,
                                        'Suppressions': deletions,
                                        'Statut': '✅ Changements détectés'
                                    })
                                else:
                                    summary_data.append({
                                        'Liste Source': list_name,
                                        'Insertions': 0,
                                        'Modifications': 0,
                                        'Suppressions': 0,
                                        'Statut': '⚪ Pas de changement'
                                    })
                            else:
                                summary_data.append({
                                    'Liste Source': list_name,
                                    'Insertions': 0,
                                    'Modifications': 0,
                                    'Suppressions': 0,
                                    'Statut': '⚪ Pas de changement'
                                })

                        summary_df = pd.DataFrame(summary_data)
                        st.dataframe(summary_df, use_container_width=True, hide_index=True)

                        if not changes_df.empty:
                            history_manager.save_changes(changes_df)

                            # Créer les alertes pour les substances watchlistées
                            alert_system.create_alerts_from_changes(
                                changes_df,
                                watchlist_manager,
                                risk_analyzer,
                                aggregated_df,
                                history_manager.load_history()
                            )

                            message_placeholder2.success(f"{len(changes_df)} changements détectés et enregistrés!")

                            st.subheader("Aperçu des Changements")
                            st.dataframe(changes_df.head(10), use_container_width=True)
                        else:
                            message_placeholder2.info("Aucun changement détecté.")

                # Faire disparaître les messages après 5 secondes
                time.sleep(5)
                message_placeholder1.empty()
                message_placeholder2.empty()

            except Exception as e:
                st.error(f"Erreur lors de la mise à jour: {str(e)}")
                st.exception(e)

    st.divider()

    st.subheader("Informations sur les Fichiers")

    try:
        lists_config = data_manager.config['source_files']['lists']
        for list_config in lists_config:
            list_name = list_config['name']
            list_file = list_config['file']
            description = list_config.get('description', 'N/A')

            file_path = Path(data_manager.data_folder) / "input" / list_file
            exists = file_path.exists()

            col1, col2, col3, col4 = st.columns([2, 3, 2, 2])
            with col1:
                st.write(f"**{list_name}**")
            with col2:
                st.write(description)
            with col3:
                if exists:
                    st.success("Fichier présent")
                else:
                    st.error("Fichier manquant")
            with col4:
                if exists:
                    mod_date = data_manager.get_file_modification_date(list_name)
                    st.write(f"📅 {mod_date}")
                else:
                    st.write("")

    except Exception as e:
        st.error(f"Erreur lors de la lecture des informations: {str(e)}")


def display_trends(data_manager, history_manager):
    st.header("Tendances et Évolution Temporelle")

    try:
        aggregated_df = data_manager.load_aggregated_data()
        history_df = history_manager.load_history()

        if aggregated_df.empty:
            st.info("Aucune donnée disponible. Veuillez effectuer une mise à jour dans l'onglet 'Mise à Jour'.")
            return

        # Filtre par liste source pour l'historique
        st.subheader("Filtres")

        # Filtre multiselect pour le graphique d'évolution
        available_lists = sorted(list(aggregated_df['source_list'].unique()))

        st.markdown("**Sélectionner les listes sources à afficher dans le graphique d'évolution:**")
        selected_lists_evolution = st.multiselect(
            "Listes sources",
            options=available_lists,
            default=available_lists,
            key="trends_multiselect_evolution"
        )

        # Filtre pour l'historique des changements (selectbox classique)
        st.markdown("**Filtre pour les tendances des changements:**")
        col1, col2 = st.columns(2)
        with col1:
            source_lists_hist = ['Toutes'] + available_lists
            selected_list_hist = st.selectbox("Filtrer par liste source", source_lists_hist, key="trends_source_filter_hist")

        # Filtrer les données de l'historique
        filtered_hist_df = history_df.copy()
        if selected_list_hist != 'Toutes':
            if not filtered_hist_df.empty:
                filtered_hist_df = filtered_hist_df[filtered_hist_df['source_list'] == selected_list_hist]

        st.divider()

        # Graphique 1: Évolution du nombre de substances dans le temps (multi-lignes)
        st.subheader("📈 Évolution du Nombre de Substances par Liste Source")

        if 'created_at' in aggregated_df.columns and len(selected_lists_evolution) > 0:
            # Filtrer seulement pour les listes sélectionnées
            filtered_agg_df = aggregated_df[aggregated_df['source_list'].isin(selected_lists_evolution)].copy()

            # Convertir created_at en datetime
            filtered_agg_df['created_at_dt'] = pd.to_datetime(filtered_agg_df['created_at'], errors='coerce')

            # Obtenir toutes les dates uniques
            all_dates = sorted(filtered_agg_df['created_at_dt'].dt.date.unique())

            # Créer un DataFrame pour le graphique avec toutes les dates
            chart_data_dict = {'date': all_dates}

            # Calculer l'évolution cumulée pour chaque liste source
            for source_list in selected_lists_evolution:
                list_data = filtered_agg_df[filtered_agg_df['source_list'] == source_list]
                daily_counts = list_data.groupby(list_data['created_at_dt'].dt.date).size()

                # Créer une série complète avec toutes les dates
                cumulative_counts = []
                cumul = 0
                for date in all_dates:
                    if date in daily_counts.index:
                        cumul += daily_counts[date]
                    cumulative_counts.append(cumul)

                chart_data_dict[source_list] = cumulative_counts

            # Calculer le total cumulé (somme de toutes les listes)
            total_cumulative = [0] * len(all_dates)
            for i in range(len(all_dates)):
                for source_list in selected_lists_evolution:
                    total_cumulative[i] += chart_data_dict[source_list][i]

            chart_data_dict['TOTAL'] = total_cumulative

            # Créer le DataFrame final
            evolution_df = pd.DataFrame(chart_data_dict)
            evolution_df['date_str'] = evolution_df['date'].astype(str)

            # Colonnes à afficher (toutes sauf 'date')
            columns_to_plot = [col for col in evolution_df.columns if col not in ['date', 'date_str']]

            # Afficher le graphique
            chart_data = evolution_df.set_index('date_str')[columns_to_plot]
            st.line_chart(chart_data, use_container_width=True)

            # Afficher les statistiques
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total substances", len(filtered_agg_df))
            with col2:
                if len(all_dates) > 0:
                    st.metric("Date première substance", str(min(all_dates)))
            with col3:
                if len(all_dates) > 0:
                    st.metric("Date dernière substance", str(max(all_dates)))
        elif len(selected_lists_evolution) == 0:
            st.warning("Veuillez sélectionner au moins une liste source pour afficher le graphique.")
        else:
            st.warning("Les colonnes de timestamp ne sont pas disponibles. Effectuez une mise à jour des données.")

        st.divider()

        # Graphique 2: Tendances des changements
        st.subheader("📊 Tendances des Changements")

        if not filtered_hist_df.empty and 'timestamp' in filtered_hist_df.columns:
            # Convertir timestamp en datetime
            filtered_hist_df['timestamp_dt'] = pd.to_datetime(filtered_hist_df['timestamp'], errors='coerce')
            filtered_hist_df['date'] = filtered_hist_df['timestamp_dt'].dt.date

            # Grouper par date et type de changement
            changes_by_date = filtered_hist_df.groupby(['date', 'change_type']).size().reset_index(name='count')

            # Pivoter pour avoir les types de changements en colonnes
            changes_pivot = changes_by_date.pivot(index='date', columns='change_type', values='count').fillna(0)

            # Afficher le graphique
            st.bar_chart(changes_pivot, use_container_width=True)

            # Statistiques des changements
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total changements", len(filtered_hist_df))

            with col2:
                if 'insertion' in changes_pivot.columns:
                    st.metric("Insertions", int(changes_pivot['insertion'].sum()))
                else:
                    st.metric("Insertions", 0)

            with col3:
                if 'deletion' in changes_pivot.columns:
                    st.metric("Suppressions", int(changes_pivot['deletion'].sum()))
                else:
                    st.metric("Suppressions", 0)

            with col4:
                if 'modification' in changes_pivot.columns:
                    st.metric("Modifications", int(changes_pivot['modification'].sum()))
                else:
                    st.metric("Modifications", 0)

            # Tableau des changements récents
            st.subheader("Derniers Changements")
            recent_changes = filtered_hist_df.sort_values('timestamp_dt', ascending=False).head(10)

            if not recent_changes.empty:
                display_cols = ['timestamp', 'change_type', 'source_list', 'cas_id', 'cas_name']
                available_cols = [col for col in display_cols if col in recent_changes.columns]
                st.dataframe(recent_changes[available_cols], use_container_width=True)

        else:
            st.info("Aucun changement enregistré pour le moment. Les tendances apparaîtront après la première mise à jour.")

    except Exception as e:
        st.error(f"Erreur lors de l'affichage des tendances: {str(e)}")
        st.exception(e)


def display_watchlist_surveillance(watchlist_manager, risk_analyzer, alert_system, data_manager, history_manager):
    st.header("🎯 Ma Surveillance - Watchlists Intelligentes")

    try:
        aggregated_df = data_manager.load_aggregated_data()
        history_df = history_manager.load_history()

        # Section 1: Gestion des Watchlists
        st.subheader("📋 Gestion des Watchlists")

        col1, col2 = st.columns([3, 1])

        with col1:
            with st.expander("➕ Créer une nouvelle watchlist", expanded=False):
                new_wl_name = st.text_input("Nom de la watchlist", key="new_wl_name")
                new_wl_desc = st.text_area("Description (optionnel)", key="new_wl_desc")
                new_wl_tags = st.text_input("Tags (séparés par des virgules)", key="new_wl_tags")

                if st.button("Créer la Watchlist", key="create_wl_btn"):
                    if new_wl_name:
                        tags = [tag.strip() for tag in new_wl_tags.split(",")] if new_wl_tags else []
                        watchlist_manager.create_watchlist(new_wl_name, new_wl_desc, tags)
                        st.success(f"✅ Watchlist '{new_wl_name}' créée avec succès!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Le nom de la watchlist est requis")

        with col2:
            watchlists = watchlist_manager.load_watchlists()
            st.metric("Total Watchlists", len(watchlists))

        # Afficher les watchlists existantes
        if watchlists:
            st.markdown("#### Watchlists Existantes")

            for wl in watchlists:
                with st.expander(f"📁 {wl['name']} ({len(wl['cas_ids'])} substances)", expanded=False):
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.write(f"**Description:** {wl['description'] or 'N/A'}")
                        st.write(f"**Tags:** {', '.join(wl['tags']) if wl['tags'] else 'N/A'}")
                        st.write(f"**Créée le:** {wl['created_at'][:10]}")
                        st.write(f"**Substances surveillées:** {len(wl['cas_ids'])}")

                        if wl['cas_ids']:
                            st.write(f"**CAS IDs:** {', '.join(wl['cas_ids'][:5])}")
                            if len(wl['cas_ids']) > 5:
                                st.write(f"... et {len(wl['cas_ids']) - 5} autres")

                    with col2:
                        if st.button("🗑️ Supprimer", key=f"delete_wl_{wl['id']}"):
                            watchlist_manager.delete_watchlist(wl['id'])
                            st.success(f"Watchlist '{wl['name']}' supprimée")
                            time.sleep(1)
                            st.rerun()

        st.divider()

        # Section 2: Alertes
        st.subheader("🔔 Alertes et Notifications")

        unread_alerts = alert_system.get_unread_alerts()
        high_priority_alerts = alert_system.get_high_priority_alerts()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Alertes non lues", len(unread_alerts))

        with col2:
            st.metric("Alertes haute priorité", len(high_priority_alerts))

        with col3:
            if st.button("✅ Tout marquer comme lu", key="mark_all_read_btn"):
                count = alert_system.mark_all_as_read()
                st.success(f"{count} alertes marquées comme lues")
                time.sleep(1)
                st.rerun()

        # Afficher les alertes haute priorité
        if high_priority_alerts:
            st.warning("⚠️ Alertes Haute Priorité")
            alerts_df = alert_system.to_dataframe(high_priority_alerts)
            if not alerts_df.empty:
                st.dataframe(alerts_df, use_container_width=True, height=200)

        # Afficher toutes les alertes non lues
        if unread_alerts:
            with st.expander(f"📬 Toutes les alertes non lues ({len(unread_alerts)})", expanded=True):
                alerts_df = alert_system.to_dataframe(unread_alerts)
                if not alerts_df.empty:
                    st.dataframe(alerts_df, use_container_width=True, height=300)

        st.divider()

        # Section 3: Tableau des Substances Surveillées avec Scores
        st.subheader("📊 Substances Surveillées - Analyse de Risque")

        if watchlists and not aggregated_df.empty:
            # Sélectionner une watchlist
            selected_wl_name = st.selectbox(
                "Sélectionner une watchlist à analyser",
                options=[wl['name'] for wl in watchlists],
                key="analyze_wl_select"
            )

            selected_wl = next((wl for wl in watchlists if wl['name'] == selected_wl_name), None)

            if selected_wl and selected_wl['cas_ids']:
                # Calculer les scores pour toutes les substances de cette watchlist
                with st.spinner("Calcul des scores de risque..."):
                    scores_df = risk_analyzer.calculate_scores_for_watchlist(
                        selected_wl['cas_ids'],
                        aggregated_df,
                        history_df
                    )

                if not scores_df.empty:
                    # Ajouter les noms de substances
                    cas_names = {}
                    for cas_id in selected_wl['cas_ids']:
                        substance_data = aggregated_df[aggregated_df['cas_id'] == cas_id]
                        if not substance_data.empty:
                            cas_names[cas_id] = substance_data.iloc[0]['cas_name']
                        else:
                            cas_names[cas_id] = 'Unknown'

                    scores_df['cas_name'] = scores_df['cas_id'].map(cas_names)

                    # Ajouter les prédictions et anomalies
                    predictions = []
                    anomalies = []

                    for cas_id in scores_df['cas_id']:
                        pred = risk_analyzer.predict_next_change(cas_id, history_df)
                        anom = risk_analyzer.detect_anomalies(cas_id, history_df)

                        predictions.append(pred.get('prediction', 'N/A'))
                        anomalies.append(anom.get('badge', '') if anom.get('has_anomaly') else '')

                    scores_df['prediction'] = predictions
                    scores_df['anomalie'] = anomalies

                    # Réorganiser les colonnes pour l'affichage
                    display_cols = ['badge', 'cas_id', 'cas_name', 'total_score', 'level', 'prediction', 'anomalie']
                    available_cols = [col for col in display_cols if col in scores_df.columns]

                    # Trier par score décroissant
                    scores_df_sorted = scores_df.sort_values('total_score', ascending=False)

                    # Afficher le tableau
                    st.dataframe(
                        scores_df_sorted[available_cols],
                        use_container_width=True,
                        height=400
                    )

                    # Statistiques
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric("Substances surveillées", len(scores_df))

                    with col2:
                        avg_score = scores_df['total_score'].mean()
                        st.metric("Score moyen", f"{avg_score:.1f}")

                    with col3:
                        critical_count = len(scores_df[scores_df['level'] == 'Critique'])
                        st.metric("🔴 Critiques", critical_count)

                    with col4:
                        high_count = len(scores_df[scores_df['level'] == 'Élevé'])
                        st.metric("🟠 Élevés", high_count)

                    # Graphique de répartition des scores
                    st.subheader("📈 Répartition des Niveaux de Risque")
                    risk_counts = scores_df['level'].value_counts()
                    st.bar_chart(risk_counts)

                    # Section Graphiques Radar
                    st.divider()
                    st.subheader("📊 Graphiques Radar des Scores")

                    # Tabs pour vue individuelle et comparaison
                    radar_tabs = st.tabs(["Vue Individuelle", "Mode Comparaison"])

                    with radar_tabs[0]:
                        st.markdown("#### Visualiser le profil de risque d'une substance")

                        # Sélection de la substance
                        selected_cas_for_radar = st.selectbox(
                            "Sélectionner une substance",
                            options=selected_wl['cas_ids'],
                            key="radar_cas_select",
                            format_func=lambda x: f"{x} - {aggregated_df[aggregated_df['cas_id'] == x].iloc[0]['cas_name'] if not aggregated_df[aggregated_df['cas_id'] == x].empty else 'Unknown'}"
                        )

                        if st.button("📊 Générer Graphique Radar", key="generate_radar_btn"):
                            with st.spinner("Génération du graphique radar..."):
                                try:
                                    # Calculer le score
                                    score = risk_analyzer.calculate_risk_score(
                                        selected_cas_for_radar,
                                        aggregated_df,
                                        history_df
                                    )

                                    # Obtenir le nom
                                    substance_data = aggregated_df[aggregated_df['cas_id'] == selected_cas_for_radar]
                                    cas_name = substance_data.iloc[0]['cas_name'] if not substance_data.empty else selected_cas_for_radar

                                    # Générer le graphique
                                    fig = risk_analyzer.generate_radar_chart(score, cas_name)
                                    st.pyplot(fig)
                                    plt.close(fig)

                                    # Afficher les détails
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.info(f"**Score Total:** {score['total_score']}")
                                        st.info(f"**Niveau:** {score['badge']} {score['level']}")
                                    with col2:
                                        pred = risk_analyzer.predict_next_change(selected_cas_for_radar, history_df)
                                        st.info(f"**Prédiction:** {pred['prediction']}")
                                        anom = risk_analyzer.detect_anomalies(selected_cas_for_radar, history_df)
                                        if anom.get('has_anomaly'):
                                            st.warning(f"⚠️ **Anomalie:** {anom['description']}")

                                except Exception as e:
                                    st.error(f"Erreur: {str(e)}")

                    with radar_tabs[1]:
                        st.markdown("#### Comparer les profils de risque (2-3 substances)")

                        # Sélection multiple
                        selected_cas_for_comparison = st.multiselect(
                            "Sélectionner 2 ou 3 substances à comparer",
                            options=selected_wl['cas_ids'],
                            max_selections=3,
                            key="radar_comparison_select",
                            format_func=lambda x: f"{x} - {aggregated_df[aggregated_df['cas_id'] == x].iloc[0]['cas_name'] if not aggregated_df[aggregated_df['cas_id'] == x].empty else 'Unknown'}"
                        )

                        if len(selected_cas_for_comparison) >= 2:
                            if st.button("📊 Comparer les Graphiques", key="compare_radar_btn"):
                                with st.spinner("Génération du graphique comparatif..."):
                                    try:
                                        # Calculer les scores pour toutes les substances sélectionnées
                                        scores_list = []
                                        names_list = []

                                        for cas_id in selected_cas_for_comparison:
                                            score = risk_analyzer.calculate_risk_score(
                                                cas_id,
                                                aggregated_df,
                                                history_df
                                            )
                                            scores_list.append(score)

                                            substance_data = aggregated_df[aggregated_df['cas_id'] == cas_id]
                                            cas_name = substance_data.iloc[0]['cas_name'] if not substance_data.empty else cas_id
                                            names_list.append(f"{cas_id}\n{cas_name}")

                                        # Générer le graphique comparatif
                                        fig = risk_analyzer.generate_comparison_radar_chart(scores_list, names_list)
                                        st.pyplot(fig)
                                        plt.close(fig)

                                        # Tableau comparatif
                                        st.markdown("#### 📋 Tableau Comparatif")
                                        comparison_data = []
                                        for idx, score in enumerate(scores_list):
                                            comparison_data.append({
                                                'Substance': names_list[idx].replace('\n', ' - '),
                                                'Score Total': score['total_score'],
                                                'Niveau': f"{score['badge']} {score['level']}",
                                                'Fréq. Modif.': score['components']['modification_frequency'],
                                                'Présence Listes': score['components']['list_presence'],
                                                'Type Changement': score['components']['recent_change_type'],
                                                'Récence': score['components']['recency']
                                            })

                                        comparison_df = pd.DataFrame(comparison_data)
                                        st.dataframe(comparison_df, use_container_width=True)

                                    except Exception as e:
                                        st.error(f"Erreur: {str(e)}")
                        else:
                            st.info("Veuillez sélectionner au moins 2 substances pour effectuer une comparaison.")

                    # Option de retirer une substance de la watchlist
                    st.divider()
                    st.markdown("#### ➖ Retirer une substance de cette watchlist")

                    col1, col2 = st.columns([3, 1])

                    with col1:
                        cas_to_remove = st.selectbox(
                            "Sélectionner un CAS ID à retirer",
                            options=selected_wl['cas_ids'],
                            key="remove_cas_select"
                        )

                    with col2:
                        st.write("")
                        st.write("")
                        if st.button("➖ Retirer", key="remove_cas_btn"):
                            success = watchlist_manager.remove_cas_from_watchlist(selected_wl['id'], cas_to_remove)
                            if success:
                                st.success(f"✅ {cas_to_remove} retiré de '{selected_wl_name}'")
                                time.sleep(1)
                                st.rerun()

            else:
                st.info(f"Aucune substance dans la watchlist '{selected_wl_name}'. Ajoutez des substances depuis l'onglet 'Données Agrégées'.")

        elif not watchlists:
            st.info("Créez d'abord une watchlist pour commencer la surveillance.")
        else:
            st.info("Aucune donnée agrégée disponible. Effectuez une mise à jour dans l'onglet 'Mise à Jour'.")

        # Section 4: Statistiques générales
        st.divider()
        st.subheader("📊 Statistiques Générales")

        stats = watchlist_manager.get_statistics()
        alert_stats = alert_system.get_statistics()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total watchlists", stats['total_watchlists'])
            st.metric("Substances surveillées", stats['total_watched_substances'])

        with col2:
            st.metric("Total alertes", alert_stats['total_alerts'])
            st.metric("Alertes non lues", alert_stats['unread_count'])

        with col3:
            st.metric("Alertes haute priorité", alert_stats['high_priority_unread'])

    except Exception as e:
        st.error(f"Erreur lors de l'affichage de la surveillance: {str(e)}")
        st.exception(e)


def display_pdf_export_section(data_manager, history_manager):
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.markdown("### 📄 Export Rapport PDF")

    with col3:
        if st.button("Générer Rapport PDF", type="primary"):
            with st.spinner("Génération du rapport PDF en cours..."):
                try:
                    aggregated_df = data_manager.load_aggregated_data()
                    history_df = history_manager.load_history()

                    pdf_exporter = PDFExporter()

                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_dir = Path("data/reports")
                    output_dir.mkdir(parents=True, exist_ok=True)
                    output_path = output_dir / f"rapport_echa_{timestamp}.pdf"

                    success = pdf_exporter.generate_report(aggregated_df, history_df, str(output_path))

                    if success:
                        st.success(f"✅ Rapport PDF généré avec succès!")

                        with open(output_path, "rb") as pdf_file:
                            pdf_bytes = pdf_file.read()
                            st.download_button(
                                label="📥 Télécharger le Rapport",
                                data=pdf_bytes,
                                file_name=f"rapport_echa_{timestamp}.pdf",
                                mime="application/pdf"
                            )

                        st.info(f"📁 Fichier sauvegardé: {output_path}")
                    else:
                        st.error("❌ Erreur lors de la génération du rapport PDF")

                except Exception as e:
                    st.error(f"Erreur: {str(e)}")
                    st.exception(e)


def display_calendar_heatmap(history_manager, data_manager, risk_analyzer):
    """Affiche le calendrier heatmap des changements"""
    st.header("📅 Calendrier des Changements")
    st.markdown("""
    Visualisez l'intensité de l'activité au fil du temps avec ce calendrier interactif.
    Plus une case est foncée, plus il y a eu de changements ce jour-là.
    """)

    # Charger l'historique
    history_df = history_manager.load_history()

    if history_df.empty:
        st.info("Aucun historique de changements disponible.")
        return

    # Convertir timestamp en datetime
    history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])

    # Section de filtres
    st.subheader("🎯 Filtres")
    col1, col2, col3 = st.columns(3)

    with col1:
        # Filtre par année
        available_years = sorted(history_df['timestamp'].dt.year.unique(), reverse=True)
        selected_year = st.selectbox(
            "Année",
            options=available_years,
            index=0 if available_years else None
        )

    with col2:
        # Filtre par liste source
        source_lists = ["Toutes"] + sorted(history_df['source_list'].unique().tolist())
        selected_source = st.selectbox(
            "Liste Source",
            options=source_lists,
            index=0
        )

    with col3:
        # Filtre par type de changement
        change_types = ["Tous", "insertion", "suppression", "modification"]
        selected_type = st.selectbox(
            "Type de Changement",
            options=change_types,
            index=0
        )

    # Générer le heatmap
    st.divider()
    with st.spinner("Génération du calendrier heatmap..."):
        try:
            fig = risk_analyzer.generate_calendar_heatmap(
                history_df,
                year=selected_year,
                source_list_filter=selected_source if selected_source != "Toutes" else None,
                change_type_filter=selected_type if selected_type != "Tous" else None
            )

            # Afficher le graphique
            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Erreur lors de la génération du calendrier: {str(e)}")
            logger.error(f"Erreur calendrier heatmap: {e}", exc_info=True)

    # Statistiques
    st.divider()
    st.subheader("📊 Statistiques")

    # Filtrer les données selon les filtres appliqués
    filtered_df = history_df[history_df['timestamp'].dt.year == selected_year]
    if selected_source != "Toutes":
        filtered_df = filtered_df[filtered_df['source_list'] == selected_source]
    if selected_type != "Tous":
        filtered_df = filtered_df[filtered_df['change_type'] == selected_type]

    if not filtered_df.empty:
        # Calculer les statistiques
        filtered_df['date'] = filtered_df['timestamp'].dt.date
        daily_counts = filtered_df.groupby('date').size()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Changements",
                len(filtered_df)
            )

        with col2:
            st.metric(
                "Jour le Plus Actif",
                daily_counts.max() if not daily_counts.empty else 0
            )

        with col3:
            avg_per_day = len(filtered_df) / 365 if selected_year else 0
            st.metric(
                "Moyenne Jour",
                f"{avg_per_day:.1f}"
            )

        with col4:
            days_with_changes = len(daily_counts[daily_counts > 0])
            st.metric(
                "Jours Actifs",
                days_with_changes
            )

        # Jour le plus actif avec détails
        if not daily_counts.empty:
            busiest_day = daily_counts.idxmax()
            busiest_count = daily_counts.max()

            st.info(f"📅 **Jour le plus actif**: {busiest_day} avec {busiest_count} changement(s)")

            # Détails du jour le plus actif
            busiest_day_data = filtered_df[filtered_df['date'] == busiest_day]
            insertions = len(busiest_day_data[busiest_day_data['change_type'] == 'insertion'])
            deletions = len(busiest_day_data[busiest_day_data['change_type'] == 'suppression'])
            modifications = len(busiest_day_data[busiest_day_data['change_type'] == 'modification'])

            col1, col2, col3 = st.columns(3)
            with col1:
                st.success(f"✅ Insertions: {insertions}")
            with col2:
                st.error(f"❌ Suppressions: {deletions}")
            with col3:
                st.warning(f"✏️ Modifications: {modifications}")

        # Tableau des 10 jours les plus actifs
        st.divider()
        st.subheader("🔥 Top 10 des Jours les Plus Actifs")

        if not daily_counts.empty:
            top_days = daily_counts.nlargest(10).reset_index()
            top_days.columns = ['Date', 'Nombre de Changements']
            top_days['Rang'] = range(1, len(top_days) + 1)
            top_days = top_days[['Rang', 'Date', 'Nombre de Changements']]

            st.dataframe(
                top_days,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Aucune donnée à afficher pour cette période.")
    else:
        st.info("Aucun changement trouvé pour les filtres sélectionnés.")


if __name__ == "__main__":
    main()
