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

    tabs = st.tabs(["📊 Dashboard", "Données Agrégées", "Historique des Changements", "Tendances", "Ma Surveillance", "Timeline", "Calendrier", "Réseau", "Matrice de Chaleur", "Mise à Jour"])

    with tabs[0]:
        display_dashboard(data_manager, history_manager, risk_analyzer, alert_system)

    with tabs[1]:
        display_aggregated_data(data_manager, watchlist_manager, risk_analyzer, history_manager)

    with tabs[2]:
        display_change_history(history_manager, data_manager)

    with tabs[3]:
        display_trends(data_manager, history_manager)

    with tabs[4]:
        display_watchlist_surveillance(watchlist_manager, risk_analyzer, alert_system, data_manager, history_manager)

    with tabs[5]:
        display_substance_timeline(data_manager, history_manager, risk_analyzer)

    with tabs[6]:
        display_calendar_heatmap(history_manager, data_manager, risk_analyzer)

    with tabs[7]:
        display_network_graph(data_manager, history_manager, risk_analyzer)

    with tabs[8]:
        display_risk_heatmap(data_manager, history_manager, risk_analyzer)

    with tabs[9]:
        display_update_section(data_manager, change_detector, history_manager, watchlist_manager, risk_analyzer, alert_system)


def display_dashboard(data_manager, history_manager, risk_analyzer, alert_system):
    """Affiche le dashboard analytique exécutif"""
    st.header("📊 Dashboard Analytique Exécutif")
    st.markdown("Vue d'ensemble des indicateurs clés de performance et métriques essentielles")

    # Charger les données
    aggregated_df = data_manager.load_aggregated_data()
    history_df = history_manager.load_history()

    if aggregated_df.empty:
        st.info("Aucune donnée disponible. Veuillez charger les données dans l'onglet 'Mise à Jour'.")
        return

    # Calculer toutes les métriques
    with st.spinner("Calcul des métriques du dashboard..."):
        metrics = risk_analyzer.calculate_dashboard_metrics(aggregated_df, history_df)

    # Section 1: Health Score Global
    st.divider()
    col1, col2 = st.columns([1, 2])

    with col1:
        # Jauge Health Score
        health_fig = risk_analyzer.generate_gauge_chart(
            metrics['health_score'],
            "Health Score Global",
            100
        )
        st.plotly_chart(health_fig, use_container_width=True)

    with col2:
        st.markdown("### 🎯 Indicateurs Clés")
        # 4 KPIs principaux
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)

        with kpi1:
            trend_icon = "↗️" if metrics['trend_7d'] > 0 else ("↘️" if metrics['trend_7d'] < 0 else "→")
            st.metric(
                "Substances",
                metrics['total_substances'],
                help="Nombre total de substances chimiques suivies"
            )

        with kpi2:
            st.metric(
                "Changements (7j)",
                metrics['changes_7d'],
                f"{metrics['trend_7d']:+.1f}%",
                help="Évolution vs 7 jours précédents"
            )

        with kpi3:
            st.metric(
                "Score Risque Moyen",
                f"{metrics['avg_risk_score']:.1f}",
                help="Score de risque moyen de toutes les substances"
            )

        with kpi4:
            unread = alert_system.get_unread_count() if alert_system else 0
            st.metric(
                "Alertes",
                unread,
                help="Nombre d'alertes non lues"
            )

    # Section 2: Top 5 Substances Critiques
    st.divider()
    st.subheader("🚨 Top 5 Substances Critiques")

    if metrics['top_critical']:
        for idx, substance in enumerate(metrics['top_critical'], 1):
            col1, col2, col3 = st.columns([0.5, 3, 1])

            with col1:
                st.markdown(f"**#{idx}**")

            with col2:
                st.markdown(f"{substance['badge']} **{substance['cas_name']}** ({substance['cas_id']})")

            with col3:
                st.markdown(f"**Score: {substance['score']:.1f}**")

        st.divider()
    else:
        st.info("Aucune donnée de risque disponible.")

    # Section 3: Graphiques de Répartition
    st.subheader("📈 Répartitions et Tendances")

    col1, col2 = st.columns(2)

    with col1:
        # Donut chart - Répartition par niveau de risque
        if metrics['risk_distribution']:
            labels = list(metrics['risk_distribution'].keys())
            values = list(metrics['risk_distribution'].values())
            colors = ['#2ecc71', '#f39c12', '#e67e22', '#e74c3c']

            fig_risk = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                marker=dict(colors=colors),
                textinfo='label+value+percent',
                textposition='outside'
            )])

            fig_risk.update_layout(
                title="Répartition par Niveau de Risque",
                height=350,
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )

            st.plotly_chart(fig_risk, use_container_width=True)

    with col2:
        # Donut chart - Répartition par liste source
        if metrics['list_distribution']:
            labels = list(metrics['list_distribution'].keys())
            values = list(metrics['list_distribution'].values())
            list_colors_map = {
                'testa': '#3498db',
                'testb': '#9b59b6',
                'testc': '#e67e22',
                'testd': '#1abc9c'
            }
            colors = [list_colors_map.get(l, '#95a5a6') for l in labels]

            fig_lists = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                marker=dict(colors=colors),
                textinfo='label+value+percent',
                textposition='outside'
            )])

            fig_lists.update_layout(
                title="Répartition par Liste Source",
                height=350,
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )

            st.plotly_chart(fig_lists, use_container_width=True)

    # Section 4: Métriques de Changements
    st.divider()
    st.subheader("🔄 Activité et Changements")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Total Changements",
            metrics['total_changes'],
            help="Nombre total de changements enregistrés"
        )

    with col2:
        st.metric(
            "Changements (30j)",
            metrics['changes_30d'],
            help="Changements des 30 derniers jours"
        )

    with col3:
        if metrics['total_changes'] > 0:
            activity_rate = (metrics['changes_30d'] / metrics['total_changes']) * 100
            st.metric(
                "Taux d'activité",
                f"{activity_rate:.1f}%",
                help="Part des changements sur les 30 derniers jours"
            )
        else:
            st.metric("Taux d'activité", "0%")

    # Bar chart - Types de changements
    st.divider()
    col1, col2 = st.columns([2, 1])

    with col1:
        fig_changes = go.Figure(data=[
            go.Bar(
                name='Insertions',
                x=['Insertions'],
                y=[metrics['insertions']],
                marker_color='#2ecc71'
            ),
            go.Bar(
                name='Suppressions',
                x=['Suppressions'],
                y=[metrics['deletions']],
                marker_color='#e74c3c'
            ),
            go.Bar(
                name='Modifications',
                x=['Modifications'],
                y=[metrics['modifications']],
                marker_color='#f39c12'
            )
        ])

        fig_changes.update_layout(
            title="Répartition des Types de Changements",
            height=300,
            showlegend=False,
            xaxis_title="",
            yaxis_title="Nombre"
        )

        st.plotly_chart(fig_changes, use_container_width=True)

    with col2:
        st.markdown("### 📋 Résumé")
        st.success(f"✅ **{metrics['insertions']}** Insertions")
        st.error(f"❌ **{metrics['deletions']}** Suppressions")
        st.warning(f"✏️ **{metrics['modifications']}** Modifications")

    # Section 5: Statistiques Globales
    st.divider()
    st.subheader("📊 Statistiques Globales")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Listes ECHA",
            metrics['total_lists'],
            help="Nombre de listes sources actives"
        )

    with col2:
        st.metric(
            "Connexions",
            metrics['total_connections'],
            help="Nombre total de connexions substance-liste"
        )

    with col3:
        if metrics['total_substances'] > 0:
            avg_conn = metrics['total_connections'] / metrics['total_substances']
            st.metric(
                "Moy. Connexions",
                f"{avg_conn:.1f}",
                help="Nombre moyen de listes par substance"
            )
        else:
            st.metric("Moy. Connexions", "0")

    with col4:
        st.metric(
            "Score Max",
            f"{metrics['max_risk_score']:.1f}",
            help="Score de risque le plus élevé"
        )

    # Footer avec timestamp
    st.divider()
    from datetime import datetime
    st.caption(f"📅 Dernière mise à jour: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


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
            st.write("") # Spacer for vertical alignment
            st.write("") # Spacer for vertical alignment
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
        logger.info("=" * 80)
        logger.info("DÉBUT DU PROCESSUS DE CHARGEMENT ET AGRÉGATION")
        logger.info("=" * 80)

        with st.spinner("Archivage des fichiers sources..."):
            try:
                logger.info("ÉTAPE 1: Archivage des fichiers sources")
                # Archiver les fichiers sources avant le chargement
                archived_count = data_manager.archive_source_files()
                if archived_count > 0:
                    st.info(f"📦 {archived_count} fichiers archivés dans data/archives/")
                    logger.info(f"Archivage réussi: {archived_count} fichiers archivés")
                else:
                    logger.info("Aucun fichier à archiver")

            except Exception as e:
                logger.error(f"Erreur lors de l'archivage: {str(e)}", exc_info=True)
                st.warning(f"Avertissement lors de l'archivage: {str(e)}")

        with st.spinner("Chargement des données en cours..."):
            try:
                logger.info("ÉTAPE 2: Chargement de l'ancien fichier agrégé")
                old_aggregated = data_manager.load_aggregated_data()
                logger.info(f"Ancien fichier agrégé chargé: {len(old_aggregated)} enregistrements")
                if not old_aggregated.empty:
                    logger.info(f"Colonnes: {list(old_aggregated.columns)}")
                    if 'unique_substance_id' in old_aggregated.columns:
                        duplicates = old_aggregated['unique_substance_id'].duplicated().sum()
                        logger.info(f"Doublons détectés dans l'ancien fichier (via unique_substance_id): {duplicates}")
                    else:
                        logger.warning("unique_substance_id manquant dans l'ancien fichier")

                logger.info("ÉTAPE 3: Agrégation des nouvelles données")
                aggregated_df = data_manager.aggregate_all_data()
                logger.info(f"Nouvelles données agrégées: {len(aggregated_df)} enregistrements")

                logger.info("ÉTAPE 4: Sauvegarde du fichier agrégé")
                was_saved = data_manager.save_aggregated_data(aggregated_df)
                logger.info(f"Résultat de la sauvegarde: was_saved={was_saved}")

                # Créer des placeholders pour les messages temporaires
                message_placeholder1 = st.empty()
                message_placeholder2 = st.empty()

                if was_saved:
                    message_placeholder1.success(f"Données agrégées et sauvegardées avec succès! {len(aggregated_df)} enregistrements chargés.")
                else:
                    message_placeholder1.info(f"Données agrégées ({len(aggregated_df)} enregistrements). Aucun changement détecté, fichier non modifié.")

                # La détection des changements est maintenant exécutée de manière inconditionnelle.
                # Lors du premier chargement, old_aggregated est vide, et le ChangeDetector
                # classifiera correctement tous les enregistrements comme des insertions.
                with st.spinner("Détection des changements..."):
                    logger.info("ÉTAPE 5: Détection des changements")
                    
                    # Charger les nouvelles listes à partir des fichiers sources
                    new_lists = data_manager.load_all_lists()
                    logger.info(f"Nouvelles listes chargées: {list(new_lists.keys())}")

                    # Préparer le dictionnaire des anciennes listes. Il sera vide lors du premier chargement.
                    old_lists = {}
                    if not old_aggregated.empty:
                        for list_name in old_aggregated['source_list'].unique():
                            old_lists[list_name] = old_aggregated[old_aggregated['source_list'] == list_name]
                    
                    logger.info("ÉTAPE 6: Détection des changements pour toutes les listes")
                    changes_df = change_detector.detect_all_changes(old_lists, new_lists)
                    logger.info(f"Changements détectés: {len(changes_df)} enregistrements")

                    # Créer le tableau récapitulatif par liste source
                    st.subheader("📋 Récapitulatif des Changements par Liste")

                    summary_data = []
                    all_list_names = set(old_lists.keys()) | set(new_lists.keys())
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

                    summary_df = pd.DataFrame(summary_data)
                    
                    # Sauvegarder le résumé actuel dans l'historique
                    history_manager.save_summary(summary_df)
                    
                    # Charger et afficher l'historique complet des résumés
                    summary_history_df = history_manager.load_summary_history()
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
                        logger.info("ÉTAPE 7: Sauvegarde des changements dans l'historique")
                        history_manager.save_changes(changes_df)
                        logger.info(f"Historique mis à jour avec {len(changes_df)} changements")

                        # Créer les alertes pour les substances watchlistées
                        logger.info("ÉTAPE 8: Création des alertes")
                        alert_system.create_alerts_from_changes(
                            changes_df,
                            watchlist_manager,
                            risk_analyzer,
                            aggregated_df,
                            history_manager.load_history()
                        )
                        logger.info("Alertes créées avec succès")

                        message_placeholder2.success(f"{len(changes_df)} changements détectés et enregistrés!")

                        st.subheader("Aperçu des Changements")
                        st.dataframe(changes_df.head(10), use_container_width=True)
                    else:
                        logger.info("Aucun changement détecté")
                        message_placeholder2.info("Aucun changement détecté.")

                logger.info("=" * 80)
                logger.info("FIN DU PROCESSUS DE CHARGEMENT ET AGRÉGATION - SUCCÈS")
                logger.info("=" * 80)

                # Faire disparaître les messages après 5 secondes
                time.sleep(5)
                message_placeholder1.empty()
                message_placeholder2.empty()

            except Exception as e:
                logger.error("=" * 80)
                logger.error("FIN DU PROCESSUS DE CHARGEMENT ET AGRÉGATION - ERREUR")
                logger.error(f"Exception: {str(e)}")
                logger.error("=" * 80)
                logger.exception("Traceback complet:")
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


def display_substance_timeline(data_manager, history_manager, risk_analyzer):
    """Affiche la timeline interactive d'une substance"""
    st.header("🕐 Timeline des Substances")
    st.markdown("""
    Visualisez l'historique complet d'une substance avec tous ses événements chronologiques.
    Chaque point représente un changement (insertion, modification, suppression).
    """)

    # Charger les données
    aggregated_df = data_manager.load_aggregated_data()
    history_df = history_manager.load_history()

    if aggregated_df.empty:
        st.info("Aucune donnée de substances disponible.")
        return

    if history_df.empty:
        st.info("Aucun historique de changements disponible.")
        return

    # Sélection de la substance
    st.subheader("🔍 Sélection de la Substance")

    # Obtenir la liste des substances avec leur nom
    substances_with_names = aggregated_df[['cas_id', 'cas_name']].drop_duplicates()
    substances_with_names = substances_with_names.sort_values('cas_name')

    # Créer un dictionnaire pour le mapping
    substance_options = {
        f"{row['cas_id']} - {row['cas_name']}": row['cas_id']
        for _, row in substances_with_names.iterrows()
    }

    # Selectbox avec recherche
    selected_display = st.selectbox(
        "Rechercher une substance par CAS ID ou nom",
        options=list(substance_options.keys()),
        help="Tapez pour rechercher une substance"
    )

    selected_cas_id = substance_options[selected_display]

    # Filtre par type d'événement
    col1, col2 = st.columns([2, 1])

    with col1:
        event_filter = st.selectbox(
            "Filtrer par type d'événement",
            options=["Tous", "insertion", "suppression", "modification"],
            index=0
        )

    with col2:
        # Compter le nombre d'événements pour cette substance
        substance_events = history_df[history_df['cas_id'] == selected_cas_id]
        st.metric("Événements Totaux", len(substance_events))

    # Générer la timeline
    st.divider()
    st.subheader("📅 Timeline Chronologique")

    with st.spinner("Génération de la timeline..."):
        try:
            fig = risk_analyzer.generate_substance_timeline(
                selected_cas_id,
                history_df,
                aggregated_df,
                event_type_filter=event_filter if event_filter != "Tous" else None
            )

            # Afficher le graphique
            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Erreur lors de la génération de la timeline: {str(e)}")
            logger.error(f"Erreur timeline: {e}", exc_info=True)

    # Graphique d'évolution du score de risque
    st.divider()
    st.subheader("📈 Évolution du Score de Risque")

    with st.spinner("Calcul de l'évolution du score..."):
        try:
            fig_score = risk_analyzer.generate_risk_score_evolution(
                selected_cas_id,
                history_df,
                aggregated_df
            )

            # Afficher le graphique
            st.plotly_chart(fig_score, use_container_width=True)

            # Note explicative
            st.info("""
            **Note**: Le score de risque est calculé de manière cumulative :
            - **Insertion** dans une nouvelle liste : +10 points
            - **Modification** des données : +5 points
            - **Suppression** d'une liste : -15 points

            Le score est limité entre 0 (aucun risque) et 100 (risque maximum).
            """)

        except Exception as e:
            st.error(f"Erreur lors de la génération du graphique d'évolution: {str(e)}")
            logger.error(f"Erreur évolution score: {e}", exc_info=True)

    # Tableau détaillé des événements
    st.divider()
    st.subheader("📋 Détails des Événements")

    if not substance_events.empty:
        # Préparer le DataFrame pour l'affichage
        events_display = substance_events.copy()
        events_display['timestamp'] = pd.to_datetime(events_display['timestamp'])
        events_display = events_display.sort_values('timestamp', ascending=False)

        # Sélectionner et renommer les colonnes
        columns_to_display = ['timestamp', 'change_type', 'source_list']
        if 'modified_fields' in events_display.columns:
            columns_to_display.append('modified_fields')

        events_display = events_display[columns_to_display]
        events_display.columns = ['Date/Heure', 'Type', 'Liste Source', 'Champs Modifiés'] if 'modified_fields' in columns_to_display else ['Date/Heure', 'Type', 'Liste Source']

        # Appliquer le filtre si nécessaire
        if event_filter != "Tous":
            events_display = events_display[events_display['Type'] == event_filter]

        # Afficher le tableau
        st.dataframe(
            events_display,
            use_container_width=True,
            hide_index=True
        )

        # Statistiques par type
        st.divider()
        st.subheader("📊 Statistiques par Type d'Événement")

        col1, col2, col3 = st.columns(3)

        insertions = len(substance_events[substance_events['change_type'] == 'insertion'])
        suppressions = len(substance_events[substance_events['change_type'] == 'suppression'])
        modifications = len(substance_events[substance_events['change_type'] == 'modification'])

        with col1:
            st.success(f"**✅ Insertions**")
            st.metric("", insertions)

        with col2:
            st.error(f"**❌ Suppressions**")
            st.metric("", suppressions)

        with col3:
            st.warning(f"**✏️ Modifications**")
            st.metric("", modifications)

        # Première et dernière occurrence
        if not substance_events.empty:
            substance_events['timestamp'] = pd.to_datetime(substance_events['timestamp'])
            first_event = substance_events['timestamp'].min()
            last_event = substance_events['timestamp'].max()

            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**Premier événement** : {first_event.strftime('%Y-%m-%d %H:%M')}")
            with col2:
                st.info(f"**Dernier événement** : {last_event.strftime('%Y-%m-%d %H:%M')}")

    else:
        st.info("Aucun événement enregistré pour cette substance.")


def display_network_graph(data_manager, history_manager, risk_analyzer):
    """Affiche le graphe de réseau des substances et listes"""
    st.header("🕸️ Graphe de Réseau")
    st.markdown("""
    Visualisez les relations entre substances et listes ECHA sous forme de réseau interactif.
    Les nœuds représentent les substances (cercles) et les listes (carrés), reliés par des liens.
    """)

    # Charger les données
    aggregated_df = data_manager.load_aggregated_data()
    history_df = history_manager.load_history()

    if aggregated_df.empty:
        st.info("Aucune donnée de substances disponible.")
        return

    # Section de filtres
    st.subheader("🎯 Filtres et Options")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Mode de visualisation
        graph_mode = st.selectbox(
            "Mode de visualisation",
            options=["bipartite", "substances_only"],
            format_func=lambda x: "Substances-Listes" if x == "bipartite" else "Substances uniquement",
            help="Bipartite: montre substances et listes. Substances uniquement: montre les co-occurrences."
        )

    with col2:
        # Filtre par score de risque
        min_score = st.slider(
            "Score de risque minimum",
            min_value=0,
            max_value=100,
            value=0,
            step=5,
            help="Filtrer les substances ayant un score ≥ à cette valeur"
        )

    with col3:
        # Filtre par listes sources
        all_lists = sorted(aggregated_df['source_list'].unique().tolist())
        selected_lists = st.multiselect(
            "Listes sources",
            options=all_lists,
            default=all_lists,
            help="Sélectionner les listes à inclure dans le graphe"
        )

    # Générer le graphe
    st.divider()

    if not selected_lists:
        st.warning("⚠️ Veuillez sélectionner au moins une liste source.")
        return

    with st.spinner("Génération du graphe de réseau..."):
        try:
            fig = risk_analyzer.generate_network_graph(
                aggregated_df,
                history_df,
                min_risk_score=min_score,
                selected_lists=selected_lists if selected_lists != all_lists else None,
                graph_mode=graph_mode
            )

            # Afficher le graphique
            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Erreur lors de la génération du graphe: {str(e)}")
            logger.error(f"Erreur graphe de réseau: {e}", exc_info=True)

    # Statistiques du réseau
    st.divider()
    st.subheader("📊 Statistiques du Réseau")

    # Filtrer les données selon les filtres appliqués
    filtered_df = aggregated_df.copy()
    if selected_lists and selected_lists != all_lists:
        filtered_df = filtered_df[filtered_df['source_list'].isin(selected_lists)]

    # Calculer les scores pour filtrer
    if not history_df.empty:
        cas_with_score = []
        for cas_id in filtered_df['cas_id'].unique():
            score_data = risk_analyzer.calculate_risk_score(cas_id, filtered_df, history_df)
            if score_data['total_score'] >= min_score:
                cas_with_score.append(cas_id)
        filtered_df = filtered_df[filtered_df['cas_id'].isin(cas_with_score)]

    if not filtered_df.empty:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            num_substances = filtered_df['cas_id'].nunique()
            st.metric("Substances", num_substances)

        with col2:
            num_lists = filtered_df['source_list'].nunique()
            st.metric("Listes", num_lists)

        with col3:
            num_connections = len(filtered_df)
            st.metric("Connexions", num_connections)

        with col4:
            avg_connections = num_connections / num_substances if num_substances > 0 else 0
            st.metric("Moy. Connexions/Substance", f"{avg_connections:.1f}")

        # Détails par liste
        st.divider()
        st.subheader("📋 Répartition par Liste Source")

        list_stats = filtered_df.groupby('source_list')['cas_id'].nunique().reset_index()
        list_stats.columns = ['Liste', 'Nombre de Substances']
        list_stats = list_stats.sort_values('Nombre de Substances', ascending=False)

        col1, col2 = st.columns([2, 1])

        with col1:
            st.dataframe(
                list_stats,
                use_container_width=True,
                hide_index=True
            )

        with col2:
            # Substances dans plusieurs listes
            substance_counts = filtered_df.groupby('cas_id').size()
            multi_list_count = len(substance_counts[substance_counts > 1])

            st.metric(
                "Substances multi-listes",
                multi_list_count,
                help="Nombre de substances présentes dans plusieurs listes"
            )

            if num_substances > 0:
                percentage = (multi_list_count / num_substances) * 100
                st.info(f"**{percentage:.1f}%** des substances sont dans plusieurs listes")

        # Légende des couleurs
        st.divider()
        st.subheader("🎨 Légende")

        if graph_mode == "bipartite":
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Substances (cercles)** :")
                st.markdown("- 🟢 Vert : Faible risque (0-25)")
                st.markdown("- 🟡 Jaune : Moyen risque (25-50)")
                st.markdown("- 🟠 Orange : Élevé risque (50-75)")
                st.markdown("- 🔴 Rouge : Critique risque (75-100)")

            with col2:
                st.markdown("**Listes (carrés)** :")
                st.markdown("- 🔵 Bleu : testa")
                st.markdown("- 🟣 Violet : testb")
                st.markdown("- 🟠 Orange : testc")
                st.markdown("- 🟢 Vert : testd")
        else:
            st.markdown("**Substances (cercles)** :")
            st.markdown("- 🟢 Vert : Faible risque (0-25)")
            st.markdown("- 🟡 Jaune : Moyen risque (25-50)")
            st.markdown("- 🟠 Orange : Élevé risque (50-75)")
            st.markdown("- 🔴 Rouge : Critique risque (75-100)")
            st.markdown("- **Taille** : Proportionnelle au nombre de listes")
            st.markdown("- **Liens** : Substances partageant au moins une liste commune")

    else:
        st.info("Aucune donnée après application des filtres.")


def display_risk_heatmap(data_manager, history_manager, risk_analyzer):
    """
    Affiche la matrice de chaleur 2D interactive (substances × listes)
    """
    st.header("🔥 Matrice de Chaleur Interactive")
    st.markdown("""
    Visualisez toutes les substances et leurs scores de risque dans une matrice interactive.
    - **Lignes** : Substances (CAS ID + Nom)
    - **Colonnes** : Listes sources
    - **Couleur** : Score de risque (vert = faible, rouge = critique, gris = absent)
    """)

    # Charger les données
    try:
        aggregated_df = data_manager.load_aggregated_data()
        history_df = history_manager.load_history()
    except FileNotFoundError:
        st.warning("⚠️ Aucune donnée agrégée trouvée. Veuillez charger les données depuis l'onglet 'Mise à Jour'.")
        return

    if aggregated_df.empty:
        st.info("Aucune donnée disponible.")
        return

    # Contrôles et filtres
    st.divider()
    st.subheader("⚙️ Options d'Affichage")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Mode d'affichage
        mode = st.selectbox(
            "Mode de visualisation",
            options=["all", "top50", "multi_lists"],
            format_func=lambda x: {
                "all": "📊 Toutes les substances",
                "top50": "🔝 Top 50 critiques",
                "multi_lists": "🔗 Substances multi-listes"
            }[x],
            help="Sélectionnez le mode d'affichage de la matrice"
        )

    with col2:
        # Filtre par niveau de risque
        risk_levels = ["Faible", "Moyen", "Élevé", "Critique"]
        selected_risks = st.multiselect(
            "Filtrer par niveau de risque",
            options=risk_levels,
            default=[],
            help="Sélectionnez un ou plusieurs niveaux (vide = tous)"
        )

    with col3:
        # Filtre par liste source
        available_lists = aggregated_df['source_list'].unique().tolist()
        selected_lists = st.multiselect(
            "Filtrer par liste source",
            options=available_lists,
            default=[],
            help="Sélectionnez une ou plusieurs listes (vide = toutes)"
        )

    # Bouton de réinitialisation des filtres
    if st.button("🔄 Réinitialiser les filtres"):
        st.rerun()

    # Générer la heatmap
    st.divider()

    with st.spinner("Génération de la matrice de chaleur..."):
        fig = risk_analyzer.generate_risk_heatmap(
            aggregated_df=aggregated_df,
            history_df=history_df,
            mode=mode,
            risk_filter=selected_risks if selected_risks else None,
            list_filter=selected_lists if selected_lists else None
        )

    if fig.data:
        st.plotly_chart(fig, use_container_width=True)

        # Informations supplémentaires
        st.divider()
        st.subheader("ℹ️ Informations")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            **Comment lire la matrice** :
            - Passez la souris sur une cellule pour voir les détails
            - Les cellules **grises** indiquent que la substance est absente de cette liste
            - Les cellules **colorées** indiquent la présence avec le score de risque
            - Les substances sont triées par score de risque décroissant (critiques en haut)
            """)

        with col2:
            st.markdown("""
            **Légende des couleurs** :
            - 🟢 **Vert** : Risque faible (0-25)
            - 🟡 **Jaune** : Risque moyen (25-50)
            - 🟠 **Orange** : Risque élevé (50-75)
            - 🔴 **Rouge** : Risque critique (75-100)
            - ⬜ **Gris** : Absent de cette liste
            """)

        # Statistiques
        st.divider()
        st.subheader("📊 Statistiques de la Matrice")

        # Calculer quelques statistiques
        total_substances = len(aggregated_df['cas_id'].unique())
        total_lists = len(aggregated_df['source_list'].unique())

        # Calculer les scores
        scores = []
        for _, row in aggregated_df.iterrows():
            result = risk_analyzer.calculate_risk_score(row['cas_id'], aggregated_df, history_df)
            scores.append(result['total_score'])

        import numpy as np
        avg_score = np.mean(scores) if scores else 0
        max_score = np.max(scores) if scores else 0

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Substances", total_substances)

        with col2:
            st.metric("Total Listes", total_lists)

        with col3:
            st.metric("Score Moyen", f"{avg_score:.1f}")

        with col4:
            st.metric("Score Maximum", f"{max_score:.1f}")

        # Conseils d'utilisation
        st.divider()
        st.info("""
        💡 **Conseils d'utilisation** :
        - Utilisez le mode **Top 50 critiques** pour une vue plus lisible des substances à risque
        - Utilisez le mode **Substances multi-listes** pour identifier les substances présentes dans plusieurs réglementations
        - Les filtres vous permettent de créer des vues personnalisées pour vos analyses
        - La hauteur de la matrice s'adapte automatiquement au nombre de substances affichées
        """)

    else:
        st.warning("Aucune donnée à afficher avec les filtres sélectionnés.")


if __name__ == "__main__":
    main()
