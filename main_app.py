import streamlit as st
from ui.app_config import configure_page, initialize_managers
from ui.tabs import aggregated_data
from ui.tabs import change_history
from ui.tabs import update
from ui.tabs import regulatory_view
from ui.tabs import action_planning
from ui.components.pdf_export import display_pdf_export_section

def main():
    configure_page()
    managers = initialize_managers()
    
    st.title("Tableau de Bord - Substances Chimiques ECHA")
    
    # Section PDF
    st.divider()
    display_pdf_export_section(managers['data'], managers['history'])
    st.divider()
    
    # Badge alertes
    unread = managers['alert'].get_unread_count()
    if unread > 0:
        st.warning(f"🔔 {unread} alerte(s) non lue(s)")
    
    # Création des onglets
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Données Agrégées",
        "🎯 Vue Réglementaire",
        "📅 Planning d'Actions",
        "📜 Historique des Changements",
        "🔄 Mise à Jour"
    ])
    
    # Rendu de chaque onglet
    with tab1:
        aggregated_data.render(managers)
    
    with tab2:
        regulatory_view.render(managers)

    with tab3:
        action_planning.render(managers)
    
    with tab4:
        change_history.render(managers)
    
    with tab5:
        update.render(managers)

if __name__ == "__main__":
    main()