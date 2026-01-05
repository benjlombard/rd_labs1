# 📚 Documentation des Composants UI

## Vue d'ensemble

Les composants UI réutilisables permettent de créer rapidement des interfaces cohérentes et professionnelles dans toute l'application.

## 📦 Composants Disponibles

### 1. charts.py - Visualisations

**Fonctionnalités** : ~700 lignes de code
- Graphiques en barres (simples, groupés, horizontaux)
- Graphiques circulaires (pie, donut)
- Graphiques de tendances (lignes, aires)
- Histogrammes de distribution
- Graphiques spécialisés (gauge, heatmap, scatter)
- Palettes de couleurs prédéfinies

**Exemple d'utilisation** :
```python
from ui.components.charts import create_bar_chart, create_pie_chart, display_chart

# Graphique en barres
fig = create_bar_chart(
    data=df,
    x_column='source_list',
    y_column='count',
    title='Répartition par Liste',
    color='#3498db'
)
display_chart(fig)

# Donut chart
fig = create_pie_chart(
    data=df,
    values_column='count',
    names_column='category',
    hole=0.4,
    title='Distribution'
)
st.plotly_chart(fig, use_container_width=True)

# Gauge pour score
fig = create_gauge_chart(
    value=67.5,
    title="Score de Risque",
    max_value=100
)
st.plotly_chart(fig)
```

### 2. metrics.py - Indicateurs et KPIs

**Fonctionnalités** : ~650 lignes de code
- Métriques simples avec delta
- Métriques avec icônes et couleurs
- Métriques de comparaison
- Statistiques descriptives
- Cartes de score avec seuils
- Tableaux de bord KPI
- Barres de progression

**Exemple d'utilisation** :
```python
from ui.components.metrics import (
    display_metric,
    display_metrics_row,
    display_icon_metrics_grid,
    display_score_card,
    display_kpi_dashboard
)

# Métrique simple
display_metric(
    label="Total Substances",
    value=1234,
    delta="+15%",
    help_text="Depuis hier"
)

# Ligne de métriques
metrics = [
    {'label': 'Total', 'value': 100, 'delta': '+10'},
    {'label': 'Actifs', 'value': 80, 'delta': '+5'},
    {'label': 'Inactifs', 'value': 20, 'delta': '+5'}
]
display_metrics_row(metrics)

# Grille avec icônes
metrics = [
    {'label': 'Total', 'value': '1,234', 'icon': '📊', 'color': '#3498db'},
    {'label': 'Nouveaux', 'value': '156', 'icon': '🆕', 'color': '#2ecc71', 'delta': '+12%'},
    {'label': 'Critiques', 'value': '23', 'icon': '⚠️', 'color': '#e74c3c'}
]
display_icon_metrics_grid(metrics, columns=4)

# Carte de score
display_score_card(
    score=67.5,
    max_score=100,
    title="Score de Risque Global"
)

# Dashboard KPI complet
kpis = {
    'total': {'value': 1234, 'icon': '📊', 'color': '#3498db'},
    'new': {'value': 156, 'delta': '+12%', 'icon': '🆕', 'color': '#2ecc71'},
    'modified': {'value': 89, 'icon': '✏️', 'color': '#f39c12'},
    'critical': {'value': 23, 'icon': '⚠️', 'color': '#e74c3c'}
}
display_kpi_dashboard(kpis, "KPIs Principaux", columns=4)
```

### 3. tables.py - Tableaux

**Fonctionnalités** : ~650 lignes de code
- Tableaux de base avec options
- Tableaux avec téléchargement CSV/Excel
- Tableaux formatés et stylisés
- Tableaux de comparaison
- Tableaux éditables
- Tableaux sélectionnables
- Tableaux spécialisés (changements, risques)
- Pagination
- Utilitaires de formatage

**Exemple d'utilisation** :
```python
from ui.components.tables import (
    display_dataframe,
    display_table_with_download,
    display_changes_table,
    display_risk_table,
    display_paginated_table
)

# Tableau simple
display_dataframe(
    data=df,
    title="Liste des Substances",
    height=500
)

# Tableau avec téléchargement
display_table_with_download(
    data=filtered_df,
    title="Substances Filtrées",
    filename="substances_filtered.csv"
)

# Tableau de changements
display_changes_table(
    changes_df=history_df,
    title="Historique des Modifications",
    show_stats=True
)

# Tableau avec risques colorisés
display_risk_table(
    data=df,
    risk_column='risk_score',
    title="Substances par Risque"
)

# Tableau paginé
display_paginated_table(
    data=large_df,
    page_size=50
)
```

### 4. filters.py - Filtres

**Fonctionnalités** : ~680 lignes de code
- Filtres texte standard
- Filtres de date
- Filtres de plage (range)
- Multi-sélection
- Recherche globale
- Filtres radio
- Filtres spécialisés (risque, changement, période)
- Application automatique
- Panneau de filtres avancés
- Reset global

**Exemple d'utilisation** :
```python
from ui.components.filters import (
    create_text_filters,
    create_date_filters,
    apply_text_filters,
    apply_date_filters,
    create_combined_filters,
    create_advanced_filter_panel
)

# Filtres texte simples
filters = create_text_filters(
    prefix="mytab",
    source_lists=df['source_list'].unique()
)
filtered_df = apply_text_filters(df, filters)

# Filtres de date
date_filters = create_date_filters(prefix="mytab")
filtered_df, warnings = apply_date_filters(filtered_df, date_filters)
for warning in warnings:
    st.warning(warning)

# Filtres combinés (tout-en-un)
all_filters = create_combined_filters(
    prefix="mytab",
    aggregated_df=df,
    include_date_filters=True
)

# Panneau de filtres avancés
advanced_filters = create_advanced_filter_panel(df, prefix="advanced")
filtered_df = apply_all_filters(df, advanced_filters, ['cas_name', 'cas_id'])
```

## 🎨 Exemples Complets

### Exemple 1 : Onglet avec Dashboard KPI

```python
from ui.components.metrics import display_kpi_dashboard
from ui.components.charts import create_bar_chart, display_chart

def render(managers: Dict):
    st.header("Dashboard")
    
    data = managers['data'].load_aggregated_data()
    
    # KPIs en haut
    kpis = {
        'total': {
            'label': 'Total Substances',
            'value': len(data),
            'icon': '📊',
            'color': '#3498db'
        },
        'critical': {
            'label': 'Critiques',
            'value': len(data[data['risk_level'] == 'Critique']),
            'icon': '⚠️',
            'color': '#e74c3c',
            'delta': '+5%'
        }
    }
    display_kpi_dashboard(kpis, columns=4)
    
    # Graphiques
    st.divider()
    fig = create_bar_chart(
        data=data.groupby('source_list').size().reset_index(name='count'),
        x_column='source_list',
        y_column='count',
        title='Répartition par Liste'
    )
    display_chart(fig)
```

### Exemple 2 : Onglet avec Filtres et Tableau

```python
from ui.components.filters import create_combined_filters, apply_text_filters, apply_date_filters
from ui.components.tables import display_table_with_download

def render(managers: Dict):
    st.header("Données Filtrées")
    
    data = managers['data'].load_aggregated_data()
    
    # Créer les filtres
    filters = create_combined_filters(
        prefix="filtered",
        aggregated_df=data,
        include_date_filters=True
    )
    
    # Appliquer les filtres
    filtered = data.copy()
    filtered = apply_text_filters(filtered, filters)
    filtered, warnings = apply_date_filters(filtered, filters)
    
    # Afficher warnings
    for warning in warnings:
        st.warning(warning)
    
    # Afficher le tableau
    display_table_with_download(
        data=filtered,
        title=f"Résultats ({len(filtered)} substances)",
        filename="substances_filtered.csv"
    )
```

### Exemple 3 : Onglet avec Analyse Statistique

```python
from ui.components.metrics import display_stats_summary, display_distribution_metrics
from ui.components.charts import create_histogram, display_chart

def render(managers: Dict):
    st.header("Analyse Statistique")
    
    data = managers['data'].load_aggregated_data()
    
    if 'risk_score' in data.columns:
        # Statistiques
        display_stats_summary(
            data['risk_score'],
            title="Statistiques des Scores de Risque"
        )
        
        st.divider()
        
        # Distribution
        display_distribution_metrics(
            data=data,
            column='risk_level',
            categories=['Faible', 'Moyen', 'Élevé', 'Critique'],
            title='Répartition par Niveau'
        )
        
        st.divider()
        
        # Histogramme
        fig = create_histogram(
            data=data,
            column='risk_score',
            title='Distribution des Scores',
            bins=30
        )
        display_chart(fig)
```

## 🔧 Bonnes Pratiques

### Nommage des Clés

Toujours préfixer les clés de session_state pour éviter les conflits :

```python
# ✅ BON
create_text_filters(prefix="dashboard")
create_date_filters(prefix="trends")

# ❌ MAUVAIS
create_text_filters(prefix="")  # Risque de conflit !
```

### Réutilisabilité

Privilégier les composants aux copies de code :

```python
# ✅ BON
from ui.components.metrics import display_metrics_row

metrics = [...]
display_metrics_row(metrics)

# ❌ MAUVAIS
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(...)  # Répété partout
```

### Performance

Mettre en cache les données lourdes :

```python
@st.cache_data
def get_processed_data():
    # Calculs lourds
    return data

def render(managers: Dict):
    data = get_processed_data()
    display_dataframe(data)
```

## 📊 Comparaison Avant/Après

### Avant (Sans composants)

```python
def render(managers: Dict):
    st.header("Mon Onglet")
    
    # 50 lignes de code pour créer des filtres
    col1, col2, col3 = st.columns(3)
    with col1:
        name_filter = st.text_input(...)
    with col2:
        id_filter = st.text_input(...)
    # ... etc
    
    # 30 lignes pour filtrer
    filtered = data.copy()
    if name_filter:
        filtered = filtered[...]
    # ... etc
    
    # 20 lignes pour afficher
    st.dataframe(filtered, ...)
    csv = filtered.to_csv(...)
    st.download_button(...)
    
    # Total: ~100 lignes
```

### Après (Avec composants)

```python
def render(managers: Dict):
    st.header("Mon Onglet")
    
    data = managers['data'].load_aggregated_data()
    
    # Filtres (1 ligne)
    filters = create_combined_filters("mytab", data)
    
    # Application (2 lignes)
    filtered = apply_text_filters(data, filters)
    filtered, _ = apply_date_filters(filtered, filters)
    
    # Affichage (1 ligne)
    display_table_with_download(filtered, "Résultats")
    
    # Total: ~10 lignes
```

**Gain : -90% de code !**

## 🎯 Résumé

| Composant | Lignes | Fonctions | Use Cases |
|-----------|--------|-----------|-----------|
| **charts.py** | ~700 | 15+ | Tous types de graphiques |
| **metrics.py** | ~650 | 20+ | KPIs, scores, statistiques |
| **tables.py** | ~650 | 15+ | Affichage de données |
| **filters.py** | ~680 | 25+ | Filtrage interactif |

**Total : ~2680 lignes de code réutilisable**

## 📞 Support

Pour plus d'exemples, consultez :
- Les docstrings dans chaque fichier
- Les onglets déjà migrés (ex: `change_history.py`)
- Le template `ui/tabs/_template.py`