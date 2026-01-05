"""
Onglet Vue Réglementaire
Vue synthétique par substance avec niveau d'attention réglementaire
"""

import streamlit as st
import pandas as pd
from typing import Dict
import plotly.express as px
from datetime import datetime


def calculate_attention_level(row):
    """
    Calcule le niveau d'attention réglementaire selon la règle "worst status wins"
    
    Returns:
        tuple: (niveau, emoji, couleur)
    """
    # Vérifier les présences dans chaque liste
    sources = str(row.get('sources', '')).lower()
    
    # 🔴 CRITICAL: Annexe XIV (Authorisation List)
    if 'authorisation_list' in sources:
        return ('CRITICAL', '🔴', '#dc3545')
    
    # 🟠 HIGH: SVHC uniquement (Candidate List sans être dans Authorisation)
    elif 'candidate_list' in sources:
        return ('HIGH', '🟠', '#fd7e14')
    
    # 🟡 MEDIUM: Restriction
    elif 'restriction_list' in sources:
        return ('MEDIUM', '🟡', '#ffc107')
    
    # 🔵 LOW: Process en cours
    elif 'restriction_process' in sources or 'clh_process' in sources:
        return ('LOW', '🔵', '#0dcaf0')
    
    # ⚪ INFO: Rien de spécial
    else:
        return ('INFO', '⚪', '#6c757d')


def aggregate_by_substance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrège les données par substance (1 ligne = 1 substance)
    """
    if df.empty:
        return pd.DataFrame()
    
    # Grouper par CAS ID (ou substance name si pas de CAS)
    agg_data = []
    
    # Grouper par cas_id
    for cas_id, group in df.groupby('cas_id', dropna=False):
        # Prendre le premier nom de substance (ils devraient être identiques)
        substance_name = group['cas_name'].iloc[0] if 'cas_name' in group.columns else 'N/A'
        ec_number = group['ec_number'].iloc[0] if 'ec_number' in group.columns else 'N/A'
        
        # Listes de sources (où la substance apparaît)
        sources = group['source_list'].unique().tolist()
        sources_str = ', '.join(sources)
        
        # Vérifier présence dans chaque liste clé
        in_authorisation = 'authorisation_list' in sources
        in_candidate = 'candidate_list' in sources
        in_restriction = 'restriction_list' in sources
        in_restriction_process = 'restriction_process' in sources
        in_clh_process = 'clh_process' in sources
        
        # Dates importantes (prendre la plus récente si plusieurs)
        sunset_date = None
        latest_app_date = None
        
        if 'sunset_date' in group.columns:
            sunset_dates = group['sunset_date'].dropna()
            if not sunset_dates.empty:
                sunset_date = sunset_dates.iloc[-1]
        
        if 'latest_application_date' in group.columns:
            app_dates = group['latest_application_date'].dropna()
            if not app_dates.empty:
                latest_app_date = app_dates.iloc[-1]
        
        # Date d'inclusion candidate list
        candidate_date = None
        if in_candidate and 'date_of_inclusion' in group.columns:
            dates = group[group['source_list'] == 'candidate_list']['date_of_inclusion'].dropna()
            if not dates.empty:
                candidate_date = dates.iloc[0]
        
        agg_data.append({
            'cas_id': cas_id,
            'substance_name': substance_name,
            'ec_number': ec_number,
            'sources': sources_str,
            'in_authorisation': in_authorisation,
            'in_candidate': in_candidate,
            'in_restriction': in_restriction,
            'in_restriction_process': in_restriction_process,
            'in_clh_process': in_clh_process,
            'sunset_date': sunset_date,
            'latest_application_date': latest_app_date,
            'candidate_inclusion_date': candidate_date,
            'nb_sources': len(sources)
        })
    
    agg_df = pd.DataFrame(agg_data)
    
    # Calculer le niveau d'attention
    attention_data = agg_df.apply(calculate_attention_level, axis=1)
    agg_df['attention_level'] = attention_data.apply(lambda x: x[0])
    agg_df['attention_emoji'] = attention_data.apply(lambda x: x[1])
    agg_df['attention_color'] = attention_data.apply(lambda x: x[2])
    
    return agg_df


def render_status_badges(row):
    """
    Génère les badges de statut pour une substance
    """
    badges = []
    
    if row['in_authorisation']:
        badges.append('🟥 A14')
    if row['in_candidate']:
        badges.append('🟠 SVHC')
    if row['in_restriction']:
        badges.append('🟡 R')
    if row['in_restriction_process']:
        badges.append('🔵 RP')
    if row['in_clh_process']:
        badges.append('🔵 CLH')
    
    return ' · '.join(badges) if badges else '⚪ Aucun'


def render_substance_timeline(cas_id: str, original_df: pd.DataFrame):
    """
    Affiche la timeline réglementaire d'une substance
    """
    substance_data = original_df[original_df['cas_id'] == cas_id].sort_values('created_at')
    
    if substance_data.empty:
        st.warning("Aucune donnée trouvée pour cette substance")
        return
    
    st.subheader(f"📅 Timeline Réglementaire")
    
    # Créer la timeline
    timeline_events = []
    
    for _, row in substance_data.iterrows():
        source = row['source_list']
        
        # Déterminer la date et le label
        event_date = None
        event_label = source.replace('_', ' ').title()
        
        if source == 'candidate_list' and 'date_of_inclusion' in row and pd.notna(row['date_of_inclusion']):
            event_date = row['date_of_inclusion']
            event_label += " - Inclusion"
        elif source == 'authorisation_list':
            if 'sunset_date' in row and pd.notna(row['sunset_date']):
                event_date = row['sunset_date']
                event_label += " - Sunset Date"
            elif 'latest_application_date' in row and pd.notna(row['latest_application_date']):
                event_date = row['latest_application_date']
                event_label += " - Latest Application"
        
        if event_date:
            timeline_events.append({
                'date': event_date,
                'event': event_label,
                'source': source
            })
    
    if timeline_events:
        timeline_df = pd.DataFrame(timeline_events).sort_values('date')
        
        for _, event in timeline_df.iterrows():
            date_str = pd.to_datetime(event['date']).strftime('%Y-%m-%d') if pd.notna(event['date']) else 'Date inconnue'
            
            # Emoji selon la source
            emoji = '🟥' if 'authorisation' in event['source'] else '🟠' if 'candidate' in event['source'] else '🟡'
            
            st.markdown(f"{emoji} **{date_str}** — {event['event']}")
    
    # Afficher les détails complets
    with st.expander("📋 Détails Complets"):
        st.dataframe(substance_data, use_container_width=True, hide_index=True)


def render(managers: Dict):
    """
    Affiche l'onglet Vue Réglementaire
    """
    from backend.logger import get_logger
    logger = get_logger()
    
    st.header("🎯 Vue Réglementaire - Radar Substances")
    
    st.info("Vue synthétique par substance avec niveau d'attention réglementaire basé sur la règle **'Worst Status Wins'**")
    
    try:
        # Charger les données agrégées
        original_df = managers['data'].load_aggregated_data()
        
        if original_df.empty:
            st.warning("⚠️ Aucune donnée disponible. Veuillez charger les données dans l'onglet 'Mise à Jour'.")
            return
        
        # Agréger par substance
        with st.spinner("Agrégation par substance..."):
            agg_df = aggregate_by_substance(original_df)
        
        if agg_df.empty:
            st.warning("⚠️ Impossible d'agréger les données")
            return
        
        logger.info(f"Vue réglementaire: {len(agg_df)} substances uniques")
        
        # Section Filtres
        st.subheader("🎛️ Filtres Métier")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            filter_critical = st.checkbox("🔴 Annexe XIV uniquement", value=False)
        
        with col2:
            filter_high = st.checkbox("🟠 SVHC sans autorisation", value=False)
        
        with col3:
            filter_restriction = st.checkbox("🟡 Restriction", value=False)
        
        with col4:
            filter_process = st.checkbox("🔵 Process en cours", value=False)
        
        # Filtres de recherche par CAS ID et nom
        st.markdown("**🔍 Recherche par Substance**")
        col_search1, col_search2 = st.columns(2)
        
        with col_search1:
            cas_search = st.text_input(
                "Recherche par CAS ID",
                placeholder="Ex: 101-14-4",
                key="cas_search_regulatory"
            )
        
        with col_search2:
            name_search = st.text_input(
                "Recherche par Nom",
                placeholder="Ex: MOCA",
                key="name_search_regulatory"
            )
        
        # Appliquer les filtres
        filtered_df = agg_df.copy()
        
        # Filtres métier (checkboxes)
        if filter_critical:
            filtered_df = filtered_df[filtered_df['attention_level'] == 'CRITICAL']
        elif filter_high:
            filtered_df = filtered_df[
                (filtered_df['in_candidate'] == True) & 
                (filtered_df['in_authorisation'] == False)
            ]
        elif filter_restriction:
            filtered_df = filtered_df[filtered_df['in_restriction'] == True]
        elif filter_process:
            filtered_df = filtered_df[
                (filtered_df['in_restriction_process'] == True) | 
                (filtered_df['in_clh_process'] == True)
            ]
        
        # Filtres de recherche (appliqués en complément)
        if cas_search:
            filtered_df = filtered_df[
                filtered_df['cas_id'].astype(str).str.contains(cas_search, case=False, na=False)
            ]
        
        if name_search:
            filtered_df = filtered_df[
                filtered_df['substance_name'].astype(str).str.contains(name_search, case=False, na=False)
            ]
        
        # Métriques
        st.divider()
        st.subheader("📊 Statistiques")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            critical_count = len(agg_df[agg_df['attention_level'] == 'CRITICAL'])
            st.metric("🔴 CRITICAL", critical_count)
        
        with col2:
            high_count = len(agg_df[agg_df['attention_level'] == 'HIGH'])
            st.metric("🟠 HIGH", high_count)
        
        with col3:
            medium_count = len(agg_df[agg_df['attention_level'] == 'MEDIUM'])
            st.metric("🟡 MEDIUM", medium_count)
        
        with col4:
            low_count = len(agg_df[agg_df['attention_level'] == 'LOW'])
            st.metric("🔵 LOW", low_count)
        
        with col5:
            st.metric("Total Substances", len(agg_df))
        
        # Graphique de répartition
        st.divider()
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.subheader("📈 Répartition par Niveau d'Attention")
            
            attention_counts = agg_df['attention_level'].value_counts()
            
            # Ordre des niveaux
            level_order = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']
            level_colors = {
                'CRITICAL': '#dc3545',
                'HIGH': '#fd7e14',
                'MEDIUM': '#ffc107',
                'LOW': '#0dcaf0',
                'INFO': '#6c757d'
            }
            
            # Créer le graphique
            fig = px.bar(
                x=attention_counts.index,
                y=attention_counts.values,
                labels={'x': 'Niveau', 'y': 'Nombre de substances'},
                color=attention_counts.index,
                color_discrete_map=level_colors
            )
            fig.update_layout(showlegend=False, height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        with col_chart2:
            st.subheader("📊 Répartition par Liste")
            
            list_counts = {
                'Authorisation': agg_df['in_authorisation'].sum(),
                'Candidate': agg_df['in_candidate'].sum(),
                'Restriction': agg_df['in_restriction'].sum(),
                'R. Process': agg_df['in_restriction_process'].sum(),
                'CLH Process': agg_df['in_clh_process'].sum()
            }
            
            fig2 = px.pie(
                values=list(list_counts.values()),
                names=list(list_counts.keys()),
                hole=0.4
            )
            fig2.update_layout(height=300)
            st.plotly_chart(fig2, use_container_width=True)
        
        # Tableau principal
        st.divider()
        st.subheader("📋 Radar Réglementaire")
        
        # Préparer le tableau d'affichage
        display_df = filtered_df.copy()
        
        # Ajouter les badges
        display_df['Statuts'] = display_df.apply(render_status_badges, axis=1)
        
        # Formater les dates
        if 'sunset_date' in display_df.columns:
            display_df['Sunset Date'] = pd.to_datetime(display_df['sunset_date'], errors='coerce').dt.strftime('%Y-%m-%d')
        else:
            display_df['Sunset Date'] = 'N/A'
        
        # Sélectionner et renommer les colonnes
        display_cols = {
            'substance_name': 'Substance',
            'cas_id': 'CAS ID',
            'ec_number': 'EC Number',
            'Statuts': 'Statuts',
            'attention_emoji': '⚠️',
            'attention_level': 'Niveau',
            'Sunset Date': 'Sunset Date',
            'nb_sources': '# Sources'
        }
        
        final_display = display_df[[col for col in display_cols.keys() if col in display_df.columns]]
        final_display = final_display.rename(columns={k: v for k, v in display_cols.items() if k in final_display.columns})
        
        # Trier par niveau d'attention (CRITICAL en premier)
        level_priority = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3, 'INFO': 4}
        final_display['_sort'] = final_display['Niveau'].map(level_priority)
        final_display = final_display.sort_values('_sort').drop('_sort', axis=1)
        
        # Afficher avec style
        st.dataframe(
            final_display,
            use_container_width=True,
            hide_index=True,
            height=500
        )
        
        st.caption(f"Affichage de {len(filtered_df)} substances sur {len(agg_df)} total")
        
        # Section Drill-down
        st.divider()
        st.subheader("🔍 Drill-Down par Substance")
        
        # Sélecteur de substance
        substance_options = agg_df.apply(
            lambda row: f"{row['substance_name']} ({row['cas_id']})",
            axis=1
        ).tolist()
        
        selected_substance = st.selectbox(
            "Sélectionnez une substance pour voir sa timeline",
            options=['-- Sélectionner --'] + substance_options
        )
        
        if selected_substance != '-- Sélectionner --':
            # Extraire le CAS ID
            cas_id = selected_substance.split('(')[-1].strip(')')
            
            # Afficher la timeline
            render_substance_timeline(cas_id, original_df)
        
        # Export
        st.divider()
        st.subheader("💾 Export")
        
        csv = final_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger Vue Réglementaire (CSV)",
            data=csv,
            file_name=f"vue_reglementaire_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
    except FileNotFoundError:
        st.error("❌ Fichier de données non trouvé. Veuillez d'abord charger les données.")
        logger.error("Fichier aggregated_data.xlsx non trouvé pour la vue réglementaire")
    
    except Exception as e:
        st.error(f"❌ Erreur: {str(e)}")
        logger.error(f"Erreur dans la vue réglementaire: {str(e)}")
        st.exception(e)