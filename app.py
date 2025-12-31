import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent / "backend"))

from backend.data_manager import DataManager
from backend.change_detector import ChangeDetector
from backend.history_manager import HistoryManager


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

    tabs = st.tabs(["Données Agrégées", "Historique des Changements", "Mise à Jour"])

    with tabs[0]:
        display_aggregated_data(data_manager)

    with tabs[1]:
        display_change_history(history_manager, data_manager)

    with tabs[2]:
        display_update_section(data_manager, change_detector, history_manager)


def display_aggregated_data(data_manager):
    st.header("Visualisation des Substances Chimiques")

    try:
        aggregated_df = data_manager.load_aggregated_data()

        if aggregated_df.empty:
            st.info("Aucune donnée agrégée disponible. Veuillez effectuer une mise à jour dans l'onglet 'Mise à Jour'.")
            return

        st.subheader("Filtres")
        col1, col2 = st.columns(2)

        with col1:
            cas_name_filter = st.text_input("Filtrer par nom de substance (cas_name)")

        with col2:
            cas_id_filter = st.text_input("Filtrer par identifiant CAS (cas_id)")

        filtered_df = aggregated_df.copy()

        if cas_name_filter:
            filtered_df = filtered_df[
                filtered_df['cas_name'].astype(str).str.contains(cas_name_filter, case=False, na=False)
            ]

        if cas_id_filter:
            filtered_df = filtered_df[
                filtered_df['cas_id'].astype(str).str.contains(cas_id_filter, case=False, na=False)
            ]

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
                data_manager.save_aggregated_data(aggregated_df)

                st.success(f"Données agrégées avec succès! {len(aggregated_df)} enregistrements chargés.")

                if not old_aggregated.empty:
                    with st.spinner("Détection des changements..."):
                        old_lists = {}
                        new_lists = data_manager.load_all_lists()

                        for list_name in new_lists.keys():
                            old_list_data = old_aggregated[old_aggregated['source_list'] == list_name]
                            if not old_list_data.empty:
                                old_list_data = old_list_data.drop(columns=['source_list'])
                                common_cols = [col for col in new_lists[list_name].columns if col in old_list_data.columns]
                                old_lists[list_name] = old_list_data[common_cols]

                        changes_df = change_detector.detect_all_changes(old_lists, new_lists)

                        if not changes_df.empty:
                            history_manager.save_changes(changes_df)
                            st.success(f"{len(changes_df)} changements détectés et enregistrés!")

                            st.subheader("Aperçu des Changements")
                            st.dataframe(changes_df.head(10), use_container_width=True)
                        else:
                            st.info("Aucun changement détecté.")

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

            col1, col2, col3 = st.columns([2, 3, 2])
            with col1:
                st.write(f"**{list_name}**")
            with col2:
                st.write(description)
            with col3:
                if exists:
                    st.success("Fichier présent")
                else:
                    st.error("Fichier manquant")

    except Exception as e:
        st.error(f"Erreur lors de la lecture des informations: {str(e)}")


if __name__ == "__main__":
    main()
