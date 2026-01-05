"""
Composant d'export PDF
Section affichée pour générer des rapports PDF personnalisés
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


def display_pdf_export_section(data_manager, history_manager):
    """
    Affiche la section d'export PDF avec options de personnalisation
    
    Args:
        data_manager: Instance de DataManager
        history_manager: Instance de HistoryManager
    """
    st.subheader("📄 Export PDF")
    
    with st.expander("Options d'export PDF", expanded=False):
        # Sélection du type de rapport
        col1, col2 = st.columns(2)
        
        with col1:
            report_type = st.selectbox(
                "Type de rapport",
                [
                    "Rapport Complet",
                    "Rapport de Synthèse",
                    "Historique des Changements",
                    "Substances à Risque",
                    "Rapport Personnalisé"
                ],
                key="pdf_report_type"
            )
        
        with col2:
            include_charts = st.checkbox(
                "Inclure les graphiques",
                value=True,
                key="pdf_include_charts"
            )
        
        # Options supplémentaires
        st.divider()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            include_summary = st.checkbox(
                "Résumé exécutif",
                value=True,
                key="pdf_summary"
            )
        
        with col2:
            include_details = st.checkbox(
                "Détails des substances",
                value=True,
                key="pdf_details"
            )
        
        with col3:
            include_stats = st.checkbox(
                "Statistiques",
                value=True,
                key="pdf_stats"
            )
        
        # Filtre de données
        st.divider()
        st.markdown("**Filtrer les données à inclure**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Charger les données pour les options
            aggregated_df = data_manager.load_aggregated_data()
            
            if not aggregated_df.empty and 'source_list' in aggregated_df.columns:
                source_lists = ['Toutes'] + sorted(aggregated_df['source_list'].unique().tolist())
                selected_lists = st.multiselect(
                    "Listes sources",
                    source_lists,
                    default=['Toutes'],
                    key="pdf_source_lists"
                )
            else:
                selected_lists = ['Toutes']
        
        with col2:
            if not aggregated_df.empty and 'risk_level' in aggregated_df.columns:
                risk_levels = aggregated_df['risk_level'].unique().tolist()
                selected_risks = st.multiselect(
                    "Niveaux de risque",
                    risk_levels,
                    key="pdf_risk_levels"
                )
            else:
                selected_risks = []
        
        # Bouton de génération
        st.divider()
        
        if st.button("🔄 Générer le rapport PDF", type="primary", use_container_width=True):
            generate_pdf_report(
                data_manager=data_manager,
                history_manager=history_manager,
                report_type=report_type,
                include_charts=include_charts,
                include_summary=include_summary,
                include_details=include_details,
                include_stats=include_stats,
                selected_lists=selected_lists,
                selected_risks=selected_risks
            )


def generate_pdf_report(
    data_manager,
    history_manager,
    report_type: str,
    include_charts: bool,
    include_summary: bool,
    include_details: bool,
    include_stats: bool,
    selected_lists: List[str],
    selected_risks: List[str]
):
    """
    Génère le rapport PDF selon les options sélectionnées
    
    Args:
        data_manager: Instance de DataManager
        history_manager: Instance de HistoryManager
        report_type: Type de rapport à générer
        include_charts: Inclure les graphiques
        include_summary: Inclure le résumé
        include_details: Inclure les détails
        include_stats: Inclure les statistiques
        selected_lists: Listes sources sélectionnées
        selected_risks: Niveaux de risque sélectionnés
    """
    try:
        from backend.pdf_exporter import PDFExporter
        
        with st.spinner("Génération du rapport PDF en cours..."):
            # Charger les données
            aggregated_df = data_manager.load_aggregated_data()
            history_df = history_manager.load_history()
            
            # Appliquer les filtres
            filtered_df = apply_pdf_filters(
                aggregated_df,
                selected_lists,
                selected_risks
            )
            
            # Créer l'exporteur PDF
            pdf_exporter = PDFExporter()
            
            # Préparer les données selon le type de rapport
            if report_type == "Rapport Complet":
                pdf_path = pdf_exporter.generate_full_report(
                    aggregated_data=filtered_df,
                    history_data=history_df,
                    include_charts=include_charts,
                    include_summary=include_summary,
                    include_details=include_details,
                    include_stats=include_stats
                )
            
            elif report_type == "Rapport de Synthèse":
                pdf_path = pdf_exporter.generate_summary_report(
                    aggregated_data=filtered_df,
                    include_charts=include_charts
                )
            
            elif report_type == "Historique des Changements":
                pdf_path = pdf_exporter.generate_changes_report(
                    history_data=history_df,
                    include_charts=include_charts
                )
            
            elif report_type == "Substances à Risque":
                high_risk_df = filtered_df[
                    filtered_df['risk_level'].isin(['Élevé', 'Critique'])
                ] if 'risk_level' in filtered_df.columns else filtered_df
                
                pdf_path = pdf_exporter.generate_risk_report(
                    risk_data=high_risk_df,
                    include_charts=include_charts
                )
            
            else:  # Rapport Personnalisé
                pdf_path = pdf_exporter.generate_custom_report(
                    aggregated_data=filtered_df,
                    history_data=history_df,
                    options={
                        'include_charts': include_charts,
                        'include_summary': include_summary,
                        'include_details': include_details,
                        'include_stats': include_stats
                    }
                )
            
            # Vérifier que le PDF a été créé
            if pdf_path and Path(pdf_path).exists():
                # Lire le fichier PDF
                with open(pdf_path, 'rb') as f:
                    pdf_bytes = f.read()
                
                # Proposer le téléchargement
                st.success("✅ Rapport PDF généré avec succès!")
                
                filename = f"rapport_{report_type.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                
                st.download_button(
                    label="📥 Télécharger le rapport PDF",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    use_container_width=True
                )
                
                # Afficher les métadonnées
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Substances", len(filtered_df))
                with col2:
                    st.metric("Pages", "~" + str(estimate_page_count(filtered_df, include_charts)))
                with col3:
                    file_size = len(pdf_bytes) / 1024  # KB
                    st.metric("Taille", f"{file_size:.1f} KB")
            
            else:
                st.error("❌ Erreur lors de la génération du PDF")
    
    except ImportError:
        st.error("❌ Le module PDFExporter n'est pas disponible. Vérifiez que backend/pdf_exporter.py existe.")
    
    except Exception as e:
        st.error(f"❌ Erreur lors de la génération du PDF: {str(e)}")
        st.exception(e)


def apply_pdf_filters(
    df: pd.DataFrame,
    selected_lists: List[str],
    selected_risks: List[str]
) -> pd.DataFrame:
    """
    Applique les filtres pour l'export PDF
    
    Args:
        df: DataFrame à filtrer
        selected_lists: Listes sources sélectionnées
        selected_risks: Niveaux de risque sélectionnés
    
    Returns:
        DataFrame filtré
    """
    if df.empty:
        return df
    
    filtered = df.copy()
    
    # Filtre par liste source
    if 'Toutes' not in selected_lists and selected_lists and 'source_list' in filtered.columns:
        filtered = filtered[filtered['source_list'].isin(selected_lists)]
    
    # Filtre par niveau de risque
    if selected_risks and 'risk_level' in filtered.columns:
        filtered = filtered[filtered['risk_level'].isin(selected_risks)]
    
    return filtered


def estimate_page_count(df: pd.DataFrame, include_charts: bool) -> int:
    """
    Estime le nombre de pages du PDF
    
    Args:
        df: DataFrame des données
        include_charts: Si des graphiques sont inclus
    
    Returns:
        Nombre estimé de pages
    """
    base_pages = 2  # Page de garde + sommaire
    
    # Pages de données (environ 30 lignes par page)
    data_pages = max(1, len(df) // 30)
    
    # Pages de graphiques
    chart_pages = 3 if include_charts else 0
    
    return base_pages + data_pages + chart_pages


def create_pdf_preview(
    data_manager,
    history_manager,
    report_type: str
):
    """
    Affiche un aperçu du contenu du rapport PDF
    
    Args:
        data_manager: Instance de DataManager
        history_manager: Instance de HistoryManager
        report_type: Type de rapport
    """
    st.subheader("📋 Aperçu du rapport")
    
    aggregated_df = data_manager.load_aggregated_data()
    history_df = history_manager.load_history()
    
    if report_type == "Rapport Complet":
        st.markdown("""
        **Contenu du rapport complet:**
        1. Page de garde
        2. Résumé exécutif
        3. Statistiques globales
        4. Liste détaillée des substances
        5. Historique des changements récents
        6. Graphiques et visualisations
        7. Annexes
        """)
    
    elif report_type == "Rapport de Synthèse":
        st.markdown("""
        **Contenu du rapport de synthèse:**
        1. Page de garde
        2. KPIs principaux
        3. Graphiques de répartition
        4. Tendances
        5. Points d'attention
        """)
    
    elif report_type == "Historique des Changements":
        st.markdown("""
        **Contenu du rapport d'historique:**
        1. Page de garde
        2. Résumé des changements
        3. Liste détaillée par type
        4. Chronologie des modifications
        5. Statistiques temporelles
        """)
    
    elif report_type == "Substances à Risque":
        st.markdown("""
        **Contenu du rapport de risque:**
        1. Page de garde
        2. Substances critiques
        3. Substances à risque élevé
        4. Analyse des risques
        5. Recommandations
        """)
    
    # Afficher des métriques d'aperçu
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Substances", len(aggregated_df))
    
    with col2:
        if not history_df.empty:
            recent_changes = len(history_df[
                pd.to_datetime(history_df['timestamp'], errors='coerce') >= 
                pd.Timestamp.now() - pd.Timedelta(days=30)
            ])
            st.metric("Changements (30j)", recent_changes)
        else:
            st.metric("Changements (30j)", 0)
    
    with col3:
        if 'risk_level' in aggregated_df.columns:
            critical = len(aggregated_df[aggregated_df['risk_level'] == 'Critique'])
            st.metric("Critiques", critical)
        else:
            st.metric("Critiques", "N/A")