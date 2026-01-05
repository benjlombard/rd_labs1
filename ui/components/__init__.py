"""
Composants réutilisables de l'interface utilisateur

Ce module contient tous les composants UI réutilisables :
- charts : Graphiques et visualisations
- filters : Filtres interactifs
- metrics : Métriques et KPIs
- tables : Tableaux et grilles de données
- pdf_export : Export PDF

Utilisation :
    from ui.components.charts import create_bar_chart
    from ui.components.filters import create_text_filters
    from ui.components.metrics import display_kpi_dashboard
    from ui.components.tables import display_dataframe
"""

# Import des modules pour faciliter l'accès
from . import charts
from . import filters
from . import metrics
from . import tables
from . import pdf_export
from . import file_detection_display

__all__ = [
    'charts',
    'filters',
    'metrics',
    'tables',
    'pdf_export',
    'file_detection_display'
]

__version__ = "2.0.0"