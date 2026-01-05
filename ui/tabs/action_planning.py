"""
Onglet Planning d'Actions Réglementaires
Vue centralisée de toutes les deadlines avec priorisation automatique
Phase 1 : MVP - Extraction dates, calcul urgence, liste triée, filtres basiques
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import plotly.express as px


def extract_all_deadlines(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extrait toutes les deadlines de toutes les listes et les unifie
    
    Returns:
        DataFrame avec colonnes:
        - substance_name
        - cas_id
        - deadline_date
        - deadline_type
        - source_list
        - days_remaining
        - urgency_level
        - action_required
    """
    all_deadlines = []
    today = pd.Timestamp.now()
    
    # Mapping des colonnes de dates par liste source
    deadline_mappings = {
        'authorisation_list': {
            'sunset_date': {
                'type': 'Sunset Date',
                'criticality': 'CRITICAL',
                'emoji': '🔴',
                'action': 'Substituer la substance ou demander exemption d\'urgence'
            },
            'latest_application_date': {
                'type': 'Latest Application Date',
                'criticality': 'HIGH',
                'emoji': '🟠',
                'action': 'Finaliser et soumettre le dossier d\'autorisation'
            }
        },
        'candidate_list': {
            'date_of_inclusion': {
                'type': 'SVHC Inclusion',
                'criticality': 'INFO',
                'emoji': '🔵',
                'action': 'Surveiller l\'évolution réglementaire'
            }
        },
        'restriction_process': {
            'expected_date_of_submission': {
                'type': 'Expected Submission',
                'criticality': 'MEDIUM',
                'emoji': '🟡',
                'action': 'Préparer les commentaires ou l\'analyse d\'impact'
            },
            'first_deadline_for_comments_annex_xv_report': {
                'type': '1st Comments Deadline',
                'criticality': 'MEDIUM',
                'emoji': '🟡',
                'action': 'Soumettre commentaires préliminaires'
            },
            'final_deadline_for_comments_annex_xv_report': {
                'type': 'Final Comments Deadline',
                'criticality': 'HIGH',
                'emoji': '🟠',
                'action': 'Soumettre commentaires finaux à l\'ECHA'
            },
            'deadline_for_comments_seac_draft_option': {
                'type': 'SEAC Comments Deadline',
                'criticality': 'MEDIUM',
                'emoji': '🟡',
                'action': 'Soumettre commentaires sur l\'avis SEAC'
            },
            'timeline_date': {
                'type': 'Process Timeline',
                'criticality': 'INFO',
                'emoji': '🔵',
                'action': 'Suivre l\'avancement du processus'
            }
        },
        'clh_process': {
            'expected_submission_date': {
                'type': 'CLH Expected Submission',
                'criticality': 'MEDIUM',
                'emoji': '🟡',
                'action': 'Anticiper la classification harmonisée'
            },
            'legal_deadline_opinion_adoption': {
                'type': 'Legal Deadline Opinion',
                'criticality': 'HIGH',
                'emoji': '🟠',
                'action': 'Préparer adaptation à la nouvelle classification'
            },
            'deadline_comments_start': {
                'type': 'Comments Start',
                'criticality': 'MEDIUM',
                'emoji': '🟡',
                'action': 'Débuter la consultation publique'
            },
            'deadline_comments_targeted': {
                'type': 'Targeted Comments Deadline',
                'criticality': 'HIGH',
                'emoji': '🟠',
                'action': 'Soumettre commentaires ciblés'
            }
        },
        'eu_positive_list': {
            'expiry_date': {
                'type': 'Expiry Date',
                'criticality': 'HIGH',
                'emoji': '🟠',
                'action': 'Renouveler la demande ou cesser l\'usage'
            }
        }
    }
    
    # Parcourir chaque ligne du DataFrame
    for _, row in df.iterrows():
        source_list = row.get('source_list', '')
        substance_name = row.get('cas_name', 'N/A')
        cas_id = row.get('cas_id', 'N/A')
        
        # Vérifier si cette source a des deadlines configurées
        if source_list in deadline_mappings:
            deadlines_config = deadline_mappings[source_list]
            
            # Pour chaque type de deadline
            for col_name, config in deadlines_config.items():
                if col_name in row and pd.notna(row[col_name]):
                    deadline_value = row[col_name]
                    
                    # Convertir en datetime
                    try:
                        deadline_date = pd.to_datetime(deadline_value)
                        
                        # Calculer jours restants
                        days_remaining = (deadline_date - today).days
                        
                        # Déterminer le niveau d'urgence
                        if days_remaining < 0:
                            urgency = 'OVERDUE'
                            urgency_emoji = '⚠️'
                            urgency_color = '#8b0000'
                        elif days_remaining <= 30:
                            urgency = 'URGENT'
                            urgency_emoji = '🔴'
                            urgency_color = '#dc3545'
                        elif days_remaining <= 90:
                            urgency = 'HIGH'
                            urgency_emoji = '🟠'
                            urgency_color = '#fd7e14'
                        elif days_remaining <= 180:
                            urgency = 'MEDIUM'
                            urgency_emoji = '🟡'
                            urgency_color = '#ffc107'
                        else:
                            urgency = 'LOW'
                            urgency_emoji = '🔵'
                            urgency_color = '#0dcaf0'
                        
                        # Ajuster l'action selon l'urgence et le type
                        base_action = config['action']
                        if days_remaining < 0:
                            action = f"⚠️ EN RETARD : {base_action}"
                        elif days_remaining <= 7:
                            action = f"🚨 URGENT ({days_remaining}j) : {base_action}"
                        elif days_remaining <= 30:
                            action = f"⚡ IMMINENT ({days_remaining}j) : {base_action}"
                        else:
                            action = base_action
                        
                        all_deadlines.append({
                            'substance_name': substance_name,
                            'cas_id': cas_id,
                            'deadline_date': deadline_date,
                            'deadline_type': config['type'],
                            'deadline_emoji': config['emoji'],
                            'source_list': source_list,
                            'days_remaining': days_remaining,
                            'urgency_level': urgency,
                            'urgency_emoji': urgency_emoji,
                            'urgency_color': urgency_color,
                            'criticality': config['criticality'],
                            'action_required': action
                        })
                    
                    except Exception as e:
                        # Ignorer les dates invalides
                        pass
    
    if not all_deadlines:
        return pd.DataFrame()
    
    deadlines_df = pd.DataFrame(all_deadlines)
    
    # Trier par urgence (jours restants croissant)
    deadlines_df = deadlines_df.sort_values('days_remaining')
    
    return deadlines_df


def render_kpi_section(deadlines_df: pd.DataFrame):
    """
    Affiche les KPIs des deadlines
    """
    st.subheader("📊 Vue d'Ensemble")
    
    if deadlines_df.empty:
        st.info("Aucune deadline détectée dans les données")
        return
    
    # Compter par niveau d'urgence
    overdue = len(deadlines_df[deadlines_df['urgency_level'] == 'OVERDUE'])
    urgent = len(deadlines_df[deadlines_df['urgency_level'] == 'URGENT'])
    high = len(deadlines_df[deadlines_df['urgency_level'] == 'HIGH'])
    medium = len(deadlines_df[deadlines_df['urgency_level'] == 'MEDIUM'])
    low = len(deadlines_df[deadlines_df['urgency_level'] == 'LOW'])
    
    # Afficher les métriques
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        if overdue > 0:
            st.metric("⚠️ EN RETARD", overdue, delta=f"-{overdue}", delta_color="inverse")
        else:
            st.metric("⚠️ EN RETARD", 0)
    
    with col2:
        st.metric("🔴 URGENT", urgent, help="< 30 jours")
    
    with col3:
        st.metric("🟠 PROCHE", high, help="30-90 jours")
    
    with col4:
        st.metric("🟡 MOYEN", medium, help="90-180 jours")
    
    with col5:
        st.metric("🔵 LOINTAIN", low, help="> 180 jours")
    
    with col6:
        st.metric("📋 TOTAL", len(deadlines_df))


def render_filters(deadlines_df: pd.DataFrame) -> pd.DataFrame:
    """
    Affiche les filtres et retourne le DataFrame filtré
    """
    st.subheader("🎛️ Filtres")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Filtre par urgence
        urgency_options = ['Tous'] + sorted(deadlines_df['urgency_level'].unique().tolist())
        selected_urgency = st.multiselect(
            "Niveau d'Urgence",
            urgency_options,
            default=['Tous']
        )
    
    with col2:
        # Filtre par type de deadline
        type_options = ['Tous'] + sorted(deadlines_df['deadline_type'].unique().tolist())
        selected_types = st.multiselect(
            "Type de Deadline",
            type_options,
            default=['Tous']
        )
    
    with col3:
        # Filtre par source
        source_options = ['Tous'] + sorted(deadlines_df['source_list'].unique().tolist())
        selected_sources = st.multiselect(
            "Liste Source",
            source_options,
            default=['Tous']
        )
    
    # Checkboxes pour filtres rapides
    col_a, col_b, col_c, col_d = st.columns(4)
    
    with col_a:
        show_overdue = st.checkbox("⚠️ Uniquement en retard", value=False)
    
    with col_b:
        show_urgent = st.checkbox("🔴 < 30 jours", value=False)
    
    with col_c:
        show_sunset = st.checkbox("🔴 Sunset dates uniquement", value=False)
    
    with col_d:
        show_comments = st.checkbox("✍️ Consultations publiques", value=False)
    
    # Appliquer les filtres
    filtered_df = deadlines_df.copy()
    
    # Filtre urgence
    if 'Tous' not in selected_urgency and selected_urgency:
        filtered_df = filtered_df[filtered_df['urgency_level'].isin(selected_urgency)]
    
    # Filtre type
    if 'Tous' not in selected_types and selected_types:
        filtered_df = filtered_df[filtered_df['deadline_type'].isin(selected_types)]
    
    # Filtre source
    if 'Tous' not in selected_sources and selected_sources:
        filtered_df = filtered_df[filtered_df['source_list'].isin(selected_sources)]
    
    # Filtres rapides
    if show_overdue:
        filtered_df = filtered_df[filtered_df['urgency_level'] == 'OVERDUE']
    
    if show_urgent:
        filtered_df = filtered_df[filtered_df['days_remaining'] <= 30]
    
    if show_sunset:
        filtered_df = filtered_df[filtered_df['deadline_type'] == 'Sunset Date']
    
    if show_comments:
        filtered_df = filtered_df[filtered_df['deadline_type'].str.contains('Comments', case=False, na=False)]
    
    return filtered_df


def render_urgent_section(deadlines_df: pd.DataFrame):
    """
    Affiche la section des deadlines urgentes (< 30 jours)
    """
    urgent_deadlines = deadlines_df[deadlines_df['days_remaining'] <= 30]
    
    if urgent_deadlines.empty:
        st.success("✅ Aucune deadline urgente dans les 30 prochains jours")
        return
    
    st.subheader(f"🚨 URGENT - Prochains 30 Jours ({len(urgent_deadlines)} deadlines)")
    
    for _, row in urgent_deadlines.iterrows():
        # Créer une carte pour chaque deadline urgente
        with st.container():
            col1, col2, col3, col4 = st.columns([1, 3, 2, 4])
            
            with col1:
                # Jours restants
                if row['days_remaining'] < 0:
                    st.error(f"⚠️ J{row['days_remaining']}")
                else:
                    st.warning(f"J-{row['days_remaining']}")
            
            with col2:
                # Substance
                st.markdown(f"**{row['substance_name']}**")
                st.caption(f"CAS: {row['cas_id']}")
            
            with col3:
                # Type de deadline
                st.markdown(f"{row['deadline_emoji']} {row['deadline_type']}")
                st.caption(row['deadline_date'].strftime('%Y-%m-%d'))
            
            with col4:
                # Action requise
                st.info(row['action_required'])
            
            st.divider()


def render_planning_section(deadlines_df: pd.DataFrame):
    """
    Affiche la section de planning (30-90 jours)
    """
    planning_deadlines = deadlines_df[
        (deadlines_df['days_remaining'] > 30) & 
        (deadlines_df['days_remaining'] <= 90)
    ]
    
    if planning_deadlines.empty:
        return
    
    with st.expander(f"⚠️ À PLANIFIER - 30-90 Jours ({len(planning_deadlines)} deadlines)", expanded=False):
        for _, row in planning_deadlines.iterrows():
            col1, col2, col3 = st.columns([1, 4, 5])
            
            with col1:
                st.metric("J-", row['days_remaining'])
            
            with col2:
                st.markdown(f"**{row['substance_name']}** ({row['cas_id']})")
                st.caption(f"{row['deadline_type']} - {row['deadline_date'].strftime('%Y-%m-%d')}")
            
            with col3:
                st.text(row['action_required'])


def render_full_table(deadlines_df: pd.DataFrame):
    """
    Affiche le tableau complet de toutes les deadlines
    """
    st.subheader("📋 Toutes les Deadlines")
    
    # Préparer le tableau d'affichage
    display_df = deadlines_df.copy()
    
    # Formater la date
    display_df['Date'] = display_df['deadline_date'].dt.strftime('%Y-%m-%d')
    
    # Formater les jours restants
    display_df['Échéance'] = display_df.apply(
        lambda row: f"J-{row['days_remaining']}" if row['days_remaining'] >= 0 else f"J{row['days_remaining']}",
        axis=1
    )
    
    # Sélectionner les colonnes à afficher
    display_cols = {
        'urgency_emoji': '⚠️',
        'substance_name': 'Substance',
        'cas_id': 'CAS ID',
        'deadline_type': 'Type Deadline',
        'Date': 'Date',
        'Échéance': 'Dans',
        'source_list': 'Source',
        'action_required': 'Action Requise'
    }
    
    final_display = display_df[[col for col in display_cols.keys() if col in display_df.columns]]
    final_display = final_display.rename(columns=display_cols)
    
    # Afficher avec style
    st.dataframe(
        final_display,
        use_container_width=True,
        hide_index=True,
        height=500
    )
    
    st.caption(f"Affichage de {len(final_display)} deadlines")


def render_charts(deadlines_df: pd.DataFrame):
    """
    Affiche les graphiques de répartition
    """
    st.subheader("📊 Analyse des Deadlines")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Graphique par urgence
        st.markdown("**Répartition par Urgence**")
        
        urgency_counts = deadlines_df['urgency_level'].value_counts()
        urgency_order = ['OVERDUE', 'URGENT', 'HIGH', 'MEDIUM', 'LOW']
        urgency_colors = {
            'OVERDUE': '#8b0000',
            'URGENT': '#dc3545',
            'HIGH': '#fd7e14',
            'MEDIUM': '#ffc107',
            'LOW': '#0dcaf0'
        }
        
        fig = px.bar(
            x=urgency_counts.index,
            y=urgency_counts.values,
            labels={'x': 'Urgence', 'y': 'Nombre'},
            color=urgency_counts.index,
            color_discrete_map=urgency_colors
        )
        fig.update_layout(showlegend=False, height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Graphique par type
        st.markdown("**Répartition par Type**")
        
        type_counts = deadlines_df['deadline_type'].value_counts().head(10)
        
        fig2 = px.pie(
            values=type_counts.values,
            names=type_counts.index,
            hole=0.4
        )
        fig2.update_layout(height=300)
        st.plotly_chart(fig2, use_container_width=True)


def render(managers: Dict):
    """
    Affiche l'onglet Planning d'Actions Réglementaires
    """
    from backend.logger import get_logger
    logger = get_logger()
    
    st.header("📅 Planning d'Actions Réglementaires")
    
    st.info("Vue centralisée de toutes les deadlines réglementaires avec priorisation automatique")
    
    try:
        # Charger les données agrégées
        aggregated_df = managers['data'].load_aggregated_data()
        
        if aggregated_df.empty:
            st.warning("⚠️ Aucune donnée disponible. Veuillez charger les données dans l'onglet 'Mise à Jour'.")
            return
        
        # Extraire toutes les deadlines
        with st.spinner("Extraction des deadlines en cours..."):
            deadlines_df = extract_all_deadlines(aggregated_df)
        
        if deadlines_df.empty:
            st.warning("⚠️ Aucune deadline détectée dans les données")
            return
        
        logger.info(f"Planning: {len(deadlines_df)} deadlines extraites")
        
        # Section KPIs
        render_kpi_section(deadlines_df)
        
        st.divider()
        
        # Section Filtres
        filtered_df = render_filters(deadlines_df)
        
        st.divider()
        
        # Section Urgent
        render_urgent_section(filtered_df)
        
        # Section Planning
        render_planning_section(filtered_df)
        
        st.divider()
        
        # Graphiques
        render_charts(filtered_df)
        
        st.divider()
        
        # Tableau complet
        render_full_table(filtered_df)
        
        # Export
        st.divider()
        st.subheader("💾 Export")
        
        # Export CSV
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger Planning (CSV)",
            data=csv,
            file_name=f"planning_reglementaire_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
    except FileNotFoundError:
        st.error("❌ Fichier de données non trouvé. Veuillez charger les données dans l'onglet 'Mise à Jour'.")
        logger.error("Fichier aggregated_data.xlsx non trouvé pour le planning")
    
    except Exception as e:
        st.error(f"❌ Erreur: {str(e)}")
        logger.error(f"Erreur dans le planning: {str(e)}")
        st.exception(e)