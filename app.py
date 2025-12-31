import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime
import time

sys.path.append(str(Path(__file__).parent / "backend"))

from backend.data_manager import DataManager
from backend.change_detector import ChangeDetector
from backend.history_manager import HistoryManager
from backend.pdf_exporter import PDFExporter


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
    return data_manager, change_detector, history_manager


def main():
    st.title("Tableau de Bord - Substances Chimiques ECHA")

    data_manager, change_detector, history_manager = initialize_managers()

    st.divider()
    display_pdf_export_section(data_manager, history_manager)
    st.divider()

    tabs = st.tabs(["Données Agrégées", "Historique des Changements", "Tendances", "Mise à Jour"])

    with tabs[0]:
        display_aggregated_data(data_manager)

    with tabs[1]:
        display_change_history(history_manager, data_manager)

    with tabs[2]:
        display_trends(data_manager, history_manager)

    with tabs[3]:
        display_update_section(data_manager, change_detector, history_manager)


def display_aggregated_data(data_manager):
    st.header("Visualisation des Substances Chimiques")

    try:
        aggregated_df = data_manager.load_aggregated_data()

        if aggregated_df.empty:
            st.info("Aucune donnée agrégée disponible. Veuillez effectuer une mise à jour dans l'onglet 'Mise à Jour'.")
            return

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


def display_update_section(data_manager, change_detector, history_manager):
    st.header("Mise à Jour des Données")

    st.info("Cette section permet de charger les nouvelles données et de détecter les changements.")

    if st.button("Charger et Agréger les Données", type="primary"):
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

                        if not changes_df.empty:
                            history_manager.save_changes(changes_df)
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


if __name__ == "__main__":
    main()
