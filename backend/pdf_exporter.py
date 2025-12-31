import pandas as pd
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from io import BytesIO
import base64
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from backend.logger import get_logger


class PDFExporter:
    def __init__(self):
        self.logger = get_logger()
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            spaceBefore=12
        )

    def generate_report(self, aggregated_df: pd.DataFrame, history_df: pd.DataFrame, output_path: str) -> bool:
        self.logger.info(f"Generation du rapport PDF: {output_path}")

        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=30,
                leftMargin=30,
                topMargin=30,
                bottomMargin=30
            )

            story = []

            story.append(Paragraph("Rapport de Suivi ECHA", self.title_style))
            story.append(Paragraph(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}", self.styles['Normal']))
            story.append(Spacer(1, 20))

            story.extend(self._add_statistics_section(aggregated_df, history_df))
            story.append(PageBreak())

            if not aggregated_df.empty:
                story.extend(self._add_distribution_chart(aggregated_df))
                story.append(Spacer(1, 20))

            if not history_df.empty:
                story.extend(self._add_changes_chart(history_df))
                story.append(PageBreak())

            if not history_df.empty:
                story.extend(self._add_recent_changes_table(history_df))
                story.append(PageBreak())

            if not aggregated_df.empty:
                story.extend(self._add_substances_table(aggregated_df))

            doc.build(story)
            self.logger.info(f"Rapport PDF genere avec succes: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Erreur lors de la generation du PDF: {str(e)}", exc_info=True)
            return False

    def _add_statistics_section(self, aggregated_df: pd.DataFrame, history_df: pd.DataFrame):
        elements = []
        elements.append(Paragraph("Statistiques Generales", self.heading_style))

        stats_data = [
            ['Metrique', 'Valeur'],
            ['Total substances', str(len(aggregated_df)) if not aggregated_df.empty else '0'],
            ['Substances uniques (CAS ID)', str(aggregated_df['cas_id'].nunique()) if not aggregated_df.empty else '0'],
            ['Listes sources', str(aggregated_df['source_list'].nunique()) if not aggregated_df.empty else '0'],
            ['Total changements', str(len(history_df)) if not history_df.empty else '0'],
        ]

        if not history_df.empty and 'change_type' in history_df.columns:
            insertions = len(history_df[history_df['change_type'] == 'insertion'])
            deletions = len(history_df[history_df['change_type'] == 'deletion'])
            modifications = len(history_df[history_df['change_type'] == 'modification'])
            stats_data.extend([
                ['Insertions', str(insertions)],
                ['Suppressions', str(deletions)],
                ['Modifications', str(modifications)]
            ])

        stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))

        elements.append(stats_table)
        elements.append(Spacer(1, 20))
        return elements

    def _add_distribution_chart(self, aggregated_df: pd.DataFrame):
        elements = []
        elements.append(Paragraph("Repartition par Liste Source", self.heading_style))

        try:
            fig, ax = plt.subplots(figsize=(8, 5))
            source_counts = aggregated_df['source_list'].value_counts()

            colors_list = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
            ax.bar(range(len(source_counts)), source_counts.values, color=colors_list[:len(source_counts)])
            ax.set_xlabel('Liste Source', fontsize=12)
            ax.set_ylabel('Nombre de Substances', fontsize=12)
            ax.set_title('Distribution des Substances par Liste', fontsize=14, fontweight='bold')
            ax.set_xticks(range(len(source_counts)))
            ax.set_xticklabels(source_counts.index, rotation=45, ha='right')
            ax.grid(axis='y', alpha=0.3)

            plt.tight_layout()

            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()

            img = Image(img_buffer, width=6*inch, height=3.75*inch)
            elements.append(img)

        except Exception as e:
            self.logger.error(f"Erreur lors de la creation du graphique de distribution: {str(e)}")
            elements.append(Paragraph("Erreur lors de la generation du graphique", self.styles['Normal']))

        return elements

    def _add_changes_chart(self, history_df: pd.DataFrame):
        elements = []
        elements.append(Paragraph("Repartition des Changements", self.heading_style))

        try:
            if 'change_type' not in history_df.columns:
                elements.append(Paragraph("Donnees de changements non disponibles", self.styles['Normal']))
                return elements

            fig, ax = plt.subplots(figsize=(8, 5))
            change_counts = history_df['change_type'].value_counts()

            colors_map = {
                'insertion': '#2ca02c',
                'deletion': '#d62728',
                'modification': '#ff7f0e'
            }
            colors_list = [colors_map.get(ct, '#1f77b4') for ct in change_counts.index]

            ax.pie(change_counts.values, labels=change_counts.index, autopct='%1.1f%%',
                   colors=colors_list, startangle=90)
            ax.set_title('Repartition des Types de Changements', fontsize=14, fontweight='bold')

            plt.tight_layout()

            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()

            img = Image(img_buffer, width=6*inch, height=3.75*inch)
            elements.append(img)

        except Exception as e:
            self.logger.error(f"Erreur lors de la creation du graphique des changements: {str(e)}")
            elements.append(Paragraph("Erreur lors de la generation du graphique", self.styles['Normal']))

        return elements

    def _add_recent_changes_table(self, history_df: pd.DataFrame, limit: int = 20):
        elements = []
        elements.append(Paragraph(f"Derniers Changements (max {limit})", self.heading_style))

        try:
            recent_changes = history_df.head(limit)

            table_data = [['Date', 'Type', 'Liste', 'CAS ID', 'CAS Name']]

            for _, row in recent_changes.iterrows():
                timestamp = row.get('timestamp', 'N/A')
                if isinstance(timestamp, str):
                    try:
                        dt = datetime.fromisoformat(timestamp)
                        timestamp = dt.strftime('%d/%m/%Y %H:%M')
                    except:
                        pass

                table_data.append([
                    str(timestamp)[:16],
                    str(row.get('change_type', 'N/A')),
                    str(row.get('source_list', 'N/A')),
                    str(row.get('cas_id', 'N/A'))[:20],
                    str(row.get('cas_name', 'N/A'))[:30]
                ])

            changes_table = Table(table_data, colWidths=[1.3*inch, 1*inch, 0.8*inch, 1.2*inch, 2.2*inch])
            changes_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.beige, colors.white]),
            ]))

            elements.append(changes_table)

        except Exception as e:
            self.logger.error(f"Erreur lors de la creation du tableau des changements: {str(e)}")
            elements.append(Paragraph("Erreur lors de la generation du tableau", self.styles['Normal']))

        return elements

    def _add_substances_table(self, aggregated_df: pd.DataFrame, limit: int = 30):
        elements = []
        elements.append(Paragraph(f"Substances (max {limit})", self.heading_style))

        try:
            substances = aggregated_df.head(limit)

            table_data = [['CAS ID', 'CAS Name', 'Liste Source']]

            for _, row in substances.iterrows():
                table_data.append([
                    str(row.get('cas_id', 'N/A'))[:20],
                    str(row.get('cas_name', 'N/A'))[:40],
                    str(row.get('source_list', 'N/A'))
                ])

            substances_table = Table(table_data, colWidths=[1.5*inch, 3.5*inch, 1.5*inch])
            substances_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.beige, colors.white]),
            ]))

            elements.append(substances_table)

        except Exception as e:
            self.logger.error(f"Erreur lors de la creation du tableau des substances: {str(e)}")
            elements.append(Paragraph("Erreur lors de la generation du tableau", self.styles['Normal']))

        return elements
