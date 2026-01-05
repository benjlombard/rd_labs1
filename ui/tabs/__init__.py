"""
Modules des onglets de l'application
Chaque module contient une fonction render(managers) qui affiche l'onglet
"""

# Import de tous les onglets pour faciliter l'import dans main_app
# from . import dashboard
# from . import aggregated_data
# from . import change_history
# etc.

__all__ = [
    'dashboard',
    'aggregated_data',
    'change_history',
    'trends',
    'surveillance',
    'timeline',
    'calendar',
    'network',
    'heatmap',
    'update',
    'regulatory_view'
]