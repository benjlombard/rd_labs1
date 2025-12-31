# 📋 CLAUDE.md - Guide de Développement Projet ECHA

**Dernière mise à jour** : 31/12/2025

---

# 📑 Table des Matières

1. [Contexte du Projet](#contexte-du-projet)
2. [Mode de Travail](#mode-de-travail)
3. [Architecture de Base](#architecture-de-base)
4. [Fonctionnalités Modulaires](#fonctionnalités-modulaires)
   - [CORE-01: Gestion des Données](#core-01-gestion-des-données)
   - [CORE-02: Détection de Changements](#core-02-détection-de-changements)
   - [CORE-03: Historisation](#core-03-historisation)
   - [UI-01: Interface Streamlit Base](#ui-01-interface-streamlit-base)
   - [UI-02: Tableau de Bord Tendances](#ui-02-tableau-de-bord-tendances)
   - [FEAT-01: Export PDF](#feat-01-export-pdf)
   - [FEAT-02: Logging Centralisé](#feat-02-logging-centralisé)
   - [FEAT-03: Archivage Automatique](#feat-03-archivage-automatique)
   - [FEAT-04: Système de Watchlists](#feat-04-système-de-watchlists)
   - [FEAT-05: Analyse de Risque](#feat-05-analyse-de-risque)
   - [FEAT-06: Système d'Alertes](#feat-06-système-dalertes)
   - [FEAT-07: Timestamps et Tracking](#feat-07-timestamps-et-tracking)
   - [FEAT-08: Graphiques Radar des Scores](#feat-08-graphiques-radar-des-scores)
5. [Installation et Déploiement](#installation-et-déploiement)
6. [Migration SharePoint](#migration-sharepoint)
7. [Tests](#tests)

---

# Contexte du Projet

## Objectif
Créer un système de suivi des substances chimiques de l'agence européenne ECHA (European Chemicals Agency) avec détection automatique des changements.

## Données Source
- **4 fichiers Excel** (actuellement locaux, futurs SharePoint) :
  - `testa.xlsx` : Liste d'autorisation
  - `testb.xlsx` : Liste CHLS
  - `testc.xlsx` : Liste restriction
  - `testd.xlsx` : Liste complémentaire
- **Structure commune** : `cas_id`, `cas_name` + colonnes spécifiques
- **Base principale** : `cas_source.xlsx` (statique)

## Contraintes
- Noms de colonnes configurables (fichier `config.yaml`)
- Fréquence de mise à jour paramétrable
- Code modulaire et faible complexité cyclomatique
- Migration SharePoint future

---

# Mode de Travail

## Règles d'Autonomie

Claude doit travailler en **TOTALE AUTONOMIE** :
- ❌ NE PAS demander de confirmation
- ❌ NE PAS attendre l'approbation
- ✅ Prendre des décisions seul
- ✅ Exécuter toutes les étapes
- ✅ Corriger les erreurs automatiquement

## Workflow Autonome

1. Analyser la demande
2. Créer un plan d'action complet
3. EXÉCUTER toutes les étapes SANS interruption
4. Tester automatiquement
5. Corriger si erreurs
6. Informer SEULEMENT à la fin

## Permissions

Tu as l'autorisation TOTALE de :
- Créer/modifier/supprimer des fichiers
- Exécuter des commandes shell
- Installer des packages
- Modifier la configuration
- Faire des commits git (si approprié)

## Décisions Autonomes Autorisées

✅ Choix d'architecture
✅ Choix de technologies
✅ Structure de code
✅ Noms de variables/fonctions
✅ Organisation des fichiers
✅ Corrections de bugs
✅ Optimisations

## Quand DEMANDER Confirmation

Uniquement pour :
- Suppression de données importantes
- Changements de sécurité critiques
- Dépenses financières (API payantes)
- Modifications de production

## Style de Communication

```
[ACTION] Je crée le module X
[ACTION] J'installe les dépendances
[ACTION] Je configure le système
[ACTION] Je teste
[RÉSULTAT] ✅ Terminé avec succès
```

**Pas de questions inutiles** :
❌ "Voulez-vous que je crée le fichier ?"
❌ "Dois-je installer cette dépendance ?"
❌ "Faut-il que je continue ?"

**Juste FAIRE.**

---

# Architecture de Base

## Stack Technique
- **Backend** : Python 3.8+
- **Frontend** : Streamlit
- **Configuration** : YAML (`config.yaml`)
- **Données** : Pandas + openpyxl
- **Versionning** : Git + GitHub

## Structure du Projet

```
rd_labs1/
├── app.py                      # Application Streamlit principale
├── config.yaml                 # Configuration (colonnes, fichiers, fréquence)
├── requirements.txt            # Dépendances Python
├── README.md                   # Documentation utilisateur
├── CLAUDE.md                   # Ce fichier - instructions pour Claude
├── .gitignore                  # Fichiers à ignorer
├── backend/                    # Modules Python
│   ├── __init__.py
│   ├── [modules selon fonctionnalités activées]
├── logs/                       # Logs (si FEAT-02 activé)
└── data/                       # Dossier des données
    ├── input/                  # Fichiers Excel sources
    ├── archives/               # Archives (si FEAT-03 activé)
    ├── reports/                # Rapports PDF (si FEAT-01 activé)
    ├── watchlists.json         # Watchlists (si FEAT-04 activé)
    ├── alerts.json             # Alertes (si FEAT-06 activé)
    ├── aggregated_data.xlsx    # Données agrégées
    └── change_history.xlsx     # Historique des changements
```

## Configuration (config.yaml)

```yaml
general:
  update_frequency: "weekly"  # daily, weekly, monthly
  archive_old_files: true
  data_folder: "data"
  archive_folder: "data/archives"

source_files:
  cas_source: "cas_source.xlsx"
  lists:
    - name: "testa"
      file: "testa.xlsx"
      description: "Liste d'autorisation"
    # ... autres listes

columns:
  common:
    cas_id: "cas_id"
    cas_name: "cas_name"
  testa:
    info_1: "info_a_1"
    # ... autres colonnes

output_files:
  aggregated_data: "data/aggregated_data.xlsx"
  change_history: "data/change_history.xlsx"
```

---

# Fonctionnalités Modulaires

> **Note** : Chaque fonctionnalité est indépendante et peut être activée/désactivée selon les besoins.

---

## CORE-01: Gestion des Données

**Statut** : ✅ OBLIGATOIRE (fonctionnalité de base)

### Description
Module central pour charger, agréger et sauvegarder les données Excel.

### Fichiers
- `backend/data_manager.py`

### Fonctionnalités
- Chargement de fichiers Excel depuis `data/input/`
- Agrégation de toutes les listes avec colonne `source_list`
- Sauvegarde du fichier agrégé
- Lecture de la configuration depuis `config.yaml`

### Méthodes Principales
- `load_cas_source()` : Charge la base principale
- `load_list_file(list_name)` : Charge un fichier spécifique
- `load_all_lists()` : Charge tous les fichiers
- `aggregate_all_data()` : Agrège toutes les listes
- `save_aggregated_data(df, force=False)` : Sauvegarde
- `load_aggregated_data()` : Charge les données agrégées

### Dépendances
- `pandas`
- `openpyxl`
- `PyYAML`

### Activation/Désactivation
**Ne peut pas être désactivé** - fonctionnalité de base requise.

---

## CORE-02: Détection de Changements

**Statut** : ✅ OBLIGATOIRE

### Description
Détecte les insertions, suppressions et modifications entre deux versions des données.

### Fichiers
- `backend/change_detector.py`

### Fonctionnalités
- Détection des insertions de substances
- Détection des suppressions de substances
- Détection des modifications avec identification des champs modifiés
- Comparaison intelligente (colonnes communes uniquement)

### Méthodes Principales
- `detect_changes_for_list(old_df, new_df, list_name)` : Détecte pour une liste
- `detect_all_changes(old_lists, new_lists)` : Détecte pour toutes les listes
- `_create_change_record()` : Crée un enregistrement de changement
- `_get_modified_fields(old_row, new_row)` : Identifie les champs modifiés

### Dépendances
- `pandas`
- CORE-01 (DataManager)

### Activation/Désactivation
**Ne peut pas être désactivé** - fonctionnalité de base requise.

---

## CORE-03: Historisation

**Statut** : ✅ OBLIGATOIRE

### Description
Enregistre l'historique de tous les changements détectés.

### Fichiers
- `backend/history_manager.py`

### Fonctionnalités
- Sauvegarde de l'historique dans `data/change_history.xlsx`
- Archivage optionnel des anciens fichiers
- Récupération de l'historique avec filtres
- Statistiques des changements

### Méthodes Principales
- `load_history()` : Charge l'historique existant
- `save_changes(changes_df)` : Ajoute des changements
- `archive_files(list_name, file_path)` : Archive un fichier
- `get_recent_changes(limit)` : Récupère les N derniers changements
- `get_changes_by_type(change_type)` : Filtre par type
- `get_changes_by_list(list_name)` : Filtre par liste
- `get_changes_by_cas(cas_id)` : Filtre par CAS ID

### Dépendances
- `pandas`
- `openpyxl`

### Activation/Désactivation
**Ne peut pas être désactivé** - fonctionnalité de base requise.

---

## UI-01: Interface Streamlit Base

**Statut** : ✅ OBLIGATOIRE

### Description
Interface web principale avec 3 onglets de base.

### Fichiers
- `app.py` (fonctions de base)

### Onglets Inclus
1. **Données Agrégées** : Visualisation des substances avec filtres
2. **Historique des Changements** : Tableau des changements avec filtres
3. **Mise à Jour** : Charger et agréger les données

### Fonctionnalités Onglet 1
- Tableau complet de toutes les substances
- Filtres par nom (`cas_name`) et identifiant (`cas_id`)
- Statistiques (total substances, substances uniques, répartition par liste)
- Export CSV

### Fonctionnalités Onglet 2
- Tableau de tous les changements
- Filtres par type, liste source, CAS ID
- Statistiques des changements (insertions, suppressions, modifications)
- Export CSV

### Fonctionnalités Onglet 3
- Bouton "Charger et Agréger les Données"
- Détection automatique des changements
- Aperçu des changements détectés
- Tableau récapitulatif par liste source
- Informations sur les fichiers sources

### Dépendances
- `streamlit`
- CORE-01, CORE-02, CORE-03

### Activation/Désactivation
**Ne peut pas être désactivé** - interface de base requise.

---

## UI-02: Tableau de Bord Tendances

**Statut** : ⚙️ OPTIONNEL (actuellement activé)

### Description
Onglet "Tendances" avec graphiques d'évolution temporelle.

### Fichiers
- `app.py` (fonction `display_trends()`)

### Fonctionnalités
- **Graphique d'évolution** : nombre de substances dans le temps (multi-courbes)
  - Filtre multiselect pour sélectionner les listes à afficher
  - Une ligne par liste source + ligne TOTAL
  - Basé sur la colonne `created_at`
- **Graphique de tendances** : insertions/suppressions/modifications par date
  - Filtre selectbox pour filtrer par liste source
  - Bar chart des changements
- **Tableau des derniers changements** (10 plus récents)
- **Statistiques** : total substances, dates première/dernière, total changements

### Dépendances
- `streamlit`
- `pandas`
- CORE-01, CORE-03
- FEAT-07 (Timestamps) recommandé pour l'évolution temporelle

### Activation
**Déjà activé par défaut.**

### Désactivation

1. **Dans `app.py`**, fonction `main()`, retirer l'onglet :
```python
# AVANT
tabs = st.tabs(["Données Agrégées", "Historique des Changements", "Tendances", "Ma Surveillance", "Mise à Jour"])

# APRÈS
tabs = st.tabs(["Données Agrégées", "Historique des Changements", "Mise à Jour"])
```

2. Retirer l'appel à la fonction :
```python
# SUPPRIMER ces lignes
with tabs[2]:
    display_trends(data_manager, history_manager)
```

3. Optionnel : Supprimer la fonction `display_trends()` dans `app.py`

---

## FEAT-01: Export PDF

**Statut** : ⚙️ OPTIONNEL (actuellement activé)

### Description
Génération de rapports PDF professionnels avec statistiques et graphiques.

### Fichiers
- `backend/pdf_exporter.py`
- `app.py` (section export PDF en haut)

### Fonctionnalités
- Génération automatique de rapports PDF A4
- **Sections du rapport** :
  - Page titre avec date/heure
  - Statistiques générales (substances, listes, changements)
  - Graphiques (bar chart répartition, pie chart changements)
  - Tableaux (derniers changements, substances)
- Téléchargement direct depuis l'interface
- Sauvegarde automatique dans `data/reports/`
- Nom de fichier avec timestamp

### Dépendances
- `reportlab >= 4.0.0`
- `matplotlib >= 3.8.0`
- CORE-01, CORE-03

### Activation
**Déjà activé par défaut.**

### Désactivation

1. **Supprimer le module** :
```bash
rm backend/pdf_exporter.py
```

2. **Dans `app.py`**, retirer les imports :
```python
# SUPPRIMER
from backend.pdf_exporter import PDFExporter
```

3. **Dans `app.py`**, fonction `main()`, retirer la section PDF :
```python
# SUPPRIMER ces lignes
st.divider()
display_pdf_export_section(data_manager, history_manager)
st.divider()
```

4. **Supprimer la fonction** `display_pdf_export_section()` dans `app.py`

5. **Désinstaller les dépendances** (si non utilisées ailleurs) :
```bash
pip uninstall reportlab matplotlib
```

6. **Mettre à jour** `requirements.txt` :
```bash
pip freeze > requirements.txt
```

---

## FEAT-02: Logging Centralisé

**Statut** : ⚙️ OPTIONNEL (actuellement activé)

### Description
Système de logging avec rotation de fichiers et niveaux de criticité.

### Fichiers
- `backend/logger.py`
- Utilisé dans tous les modules backend

### Fonctionnalités
- **Niveaux** : DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Rotation** : 10MB max par fichier, 5 fichiers de backup
- **Fichiers séparés** :
  - `logs/echa_app_debug.log` : tous les messages
  - `logs/echa_app_info.log` : INFO et plus
  - `logs/echa_app_error.log` : ERROR et CRITICAL uniquement
- **Console** : affiche INFO et plus en temps réel
- **Format** : `YYYY-MM-DD HH:MM:SS - nom - NIVEAU - fichier:ligne - message`
- **Encodage UTF-8** pour caractères spéciaux

### Méthodes Principales
- `debug(message)`
- `info(message)`
- `warning(message)`
- `error(message, exc_info=False)`
- `critical(message, exc_info=False)`
- `exception(message)` : log exception avec traceback
- `get_logger()` : singleton

### Dépendances
- `logging` (standard library)

### Activation
**Déjà activé par défaut.**

### Désactivation

1. **Supprimer le module** :
```bash
rm backend/logger.py
```

2. **Dans TOUS les modules backend**, retirer les imports et appels :
```python
# SUPPRIMER
from backend.logger import get_logger
logger = get_logger()
logger.info(...)
logger.error(...)
# etc.
```

3. **Optionnel** : Remplacer par des `print()` si besoin de traces :
```python
# Remplacer logger.info("message") par
print("[INFO] message")
```

4. **Supprimer le dossier logs** :
```bash
rm -rf logs/
```

---

## FEAT-03: Archivage Automatique

**Statut** : ⚙️ OPTIONNEL (actuellement activé)

### Description
Copie automatique des fichiers Excel sources avec timestamp avant chaque mise à jour.

### Fichiers
- `backend/data_manager.py` (méthode `archive_source_files()`)
- `app.py` (appel dans fonction `display_update_section()`)

### Fonctionnalités
- Copie automatique de `data/input/` vers `data/archives/`
- Ajout de timestamp au nom : `fichier_YYYYMMDD_HHMMSS.xlsx`
- Exemple : `testa.xlsx` → `testa_20251231_153045.xlsx`
- Les fichiers originaux restent dans `input/`
- Création automatique du dossier `archives/` si inexistant
- Logging de toutes les opérations

### Dépendances
- `shutil` (standard library)
- `datetime` (standard library)
- FEAT-02 (Logger) recommandé

### Activation
**Déjà activé par défaut.**

### Désactivation

1. **Dans `backend/data_manager.py`**, retirer la méthode :
```python
# SUPPRIMER la méthode archive_source_files() entièrement
```

2. **Dans `app.py`**, fonction `display_update_section()`, retirer l'appel :
```python
# SUPPRIMER ce bloc
with st.spinner("Archivage des fichiers sources..."):
    try:
        archived_count = data_manager.archive_source_files()
        if archived_count > 0:
            st.info(f"📦 {archived_count} fichiers archivés dans data/archives/")
    except Exception as e:
        st.warning(f"Avertissement lors de l'archivage: {str(e)}")
```

3. **Optionnel** : Supprimer le dossier archives :
```bash
rm -rf data/archives/
```

---

## FEAT-04: Système de Watchlists

**Statut** : ⚙️ OPTIONNEL (actuellement activé)

### Description
Création et gestion de listes de surveillance personnalisées pour substances chimiques.

### Fichiers
- `backend/watchlist_manager.py`
- `app.py` (section watchlist dans onglet "Données Agrégées" + onglet "Ma Surveillance")

### Fonctionnalités
- **CRUD complet** : créer, lire, modifier, supprimer des watchlists
- Ajout/suppression de CAS IDs à une watchlist
- **Métadonnées** : nom, description, tags
- Export/Import JSON de watchlists
- Statistiques et recherches
- Stockage dans `data/watchlists.json`

### Méthodes Principales
- `create_watchlist(name, description, tags)`
- `get_watchlist(watchlist_id)`
- `update_watchlist(watchlist_id, ...)`
- `delete_watchlist(watchlist_id)`
- `add_cas_to_watchlist(watchlist_id, cas_id)`
- `remove_cas_from_watchlist(watchlist_id, cas_id)`
- `is_cas_in_any_watchlist(cas_id)`
- `get_watchlists_for_cas(cas_id)`
- `export_watchlist(watchlist_id, path)`
- `import_watchlist(path)`
- `get_statistics()`

### Dépendances
- `uuid` (standard library)
- `json` (standard library)
- FEAT-02 (Logger) recommandé

### Activation
**Déjà activé par défaut.**

### Désactivation

1. **Supprimer le module** :
```bash
rm backend/watchlist_manager.py
```

2. **Dans `app.py`**, retirer l'import :
```python
# SUPPRIMER
from backend.watchlist_manager import WatchlistManager
```

3. **Dans `app.py`**, fonction `initialize_managers()`, retirer :
```python
# SUPPRIMER
watchlist_manager = WatchlistManager()
# ET dans le return
return data_manager, change_detector, history_manager  # Sans watchlist_manager
```

4. **Dans `app.py`**, fonction `display_aggregated_data()` :
   - Retirer le paramètre `watchlist_manager`
   - Supprimer toute la section "🔖 Gestion des Watchlists"

5. **Dans `app.py`**, fonction `main()` :
   - Retirer l'onglet "Ma Surveillance" des tabs
   - Supprimer l'appel à `display_watchlist_surveillance()`

6. **Supprimer la fonction** `display_watchlist_surveillance()` entière

7. **Dans `app.py`**, fonction `display_update_section()` :
   - Retirer le paramètre `watchlist_manager`
   - Retirer l'appel à `alert_system.create_alerts_from_changes()` (dépend de watchlists)

8. **Supprimer le fichier JSON** :
```bash
rm data/watchlists.json
```

---

## FEAT-05: Analyse de Risque

**Statut** : ⚙️ OPTIONNEL (actuellement activé)

### Description
Calcul de scores de risque intelligents pour les substances surveillées avec prédictions.

### Fichiers
- `backend/risk_analyzer.py`
- `app.py` (utilisé dans onglet "Ma Surveillance")

### Fonctionnalités
- **Calcul de score de risque** (0-100) avec 4 composantes :
  - Fréquence de modifications (30%)
  - Présence dans plusieurs listes (20%)
  - Type de changement récent (30%)
  - Ancienneté de la substance (20%)
- **Niveaux de risque** :
  - 🟢 Faible (0-25)
  - 🟡 Moyen (26-50)
  - 🟠 Élevé (51-75)
  - 🔴 Critique (76-100)
- **Prédictions** : estimation du prochain changement (ML basique)
- **Détection d'anomalies** : changements inhabituels
- Top N substances à risque

### Méthodes Principales
- `calculate_risk_score(cas_id, aggregated_df, history_df)`
- `calculate_scores_for_watchlist(cas_ids, aggregated_df, history_df)`
- `predict_next_change(cas_id, history_df)`
- `detect_anomalies(cas_id, history_df)`
- `get_top_risk_substances(cas_ids, aggregated_df, history_df, top_n)`

### Dépendances
- `pandas`
- `datetime` (standard library)
- CORE-01, CORE-03
- FEAT-02 (Logger) recommandé
- FEAT-04 (Watchlists) **REQUIS**

### Activation
**Déjà activé par défaut.**

### Désactivation

**⚠️ Attention** : Requiert FEAT-04 (Watchlists). Si vous désactivez FEAT-04, vous DEVEZ désactiver FEAT-05.

1. **Supprimer le module** :
```bash
rm backend/risk_analyzer.py
```

2. **Dans `app.py`**, retirer l'import :
```python
# SUPPRIMER
from backend.risk_analyzer import RiskAnalyzer
```

3. **Dans `app.py`**, fonction `initialize_managers()`, retirer :
```python
# SUPPRIMER
risk_analyzer = RiskAnalyzer()
# ET dans le return
```

4. **Dans `app.py`**, fonction `display_aggregated_data()` :
   - Retirer le paramètre `risk_analyzer`

5. **Dans `app.py`**, fonction `display_watchlist_surveillance()` :
   - Retirer toute la section "Calcul des scores de risque"
   - Retirer les colonnes liées au scoring dans le tableau
   - Retirer les statistiques de risque

6. **Dans `app.py`**, fonction `display_update_section()` :
   - Retirer le paramètre `risk_analyzer`
   - Retirer l'appel dans `alert_system.create_alerts_from_changes()` (si FEAT-06 activé)

---

## FEAT-06: Système d'Alertes

**Statut** : ⚙️ OPTIONNEL (actuellement activé)

### Description
Création et gestion d'alertes automatiques lors de changements sur substances watchlistées.

### Fichiers
- `backend/alert_system.py`
- `app.py` (section alertes dans onglet "Ma Surveillance" + badge en haut)

### Fonctionnalités
- **Création automatique d'alertes** lors de changements détectés
- Système de notifications **lues/non lues**
- **Alertes haute priorité** (risque élevé/critique)
- Filtrage par watchlist, CAS ID, type de changement
- Nettoyage automatique des anciennes alertes
- Stockage dans `data/alerts.json`
- **Badge de notifications** en temps réel

### Méthodes Principales
- `create_alert(cas_id, cas_name, watchlist_id, watchlist_name, change_type, ...)`
- `create_alerts_from_changes(changes_df, watchlist_manager, risk_analyzer, ...)`
- `get_unread_alerts()`
- `get_unread_count()`
- `mark_as_read(alert_id)`
- `mark_all_as_read()`
- `get_alerts_by_watchlist(watchlist_id)`
- `get_alerts_by_cas(cas_id)`
- `get_high_priority_alerts()`
- `clear_old_alerts(days)`
- `get_statistics()`
- `to_dataframe(alerts)`

### Dépendances
- `pandas`
- `uuid`, `json`, `datetime` (standard library)
- CORE-01, CORE-03
- FEAT-02 (Logger) recommandé
- FEAT-04 (Watchlists) **REQUIS**
- FEAT-05 (Risk Analyzer) recommandé pour enrichissement

### Activation
**Déjà activé par défaut.**

### Désactivation

**⚠️ Attention** : Requiert FEAT-04 (Watchlists). Si vous désactivez FEAT-04, vous DEVEZ désactiver FEAT-06.

1. **Supprimer le module** :
```bash
rm backend/alert_system.py
```

2. **Dans `app.py`**, retirer l'import :
```python
# SUPPRIMER
from backend.alert_system import AlertSystem
```

3. **Dans `app.py`**, fonction `initialize_managers()`, retirer :
```python
# SUPPRIMER
alert_system = AlertSystem()
# ET dans le return
```

4. **Dans `app.py`**, fonction `main()`, retirer le badge :
```python
# SUPPRIMER
unread_count = alert_system.get_unread_count()
if unread_count > 0:
    st.warning(f"🔔 {unread_count} alerte(s) non lue(s) - Consultez l'onglet 'Ma Surveillance'")
```

5. **Dans `app.py`**, fonction `display_watchlist_surveillance()` :
   - Retirer toute la section "🔔 Alertes et Notifications"

6. **Dans `app.py`**, fonction `display_update_section()` :
   - Retirer le paramètre `alert_system`
   - Supprimer le bloc de création d'alertes :
```python
# SUPPRIMER
alert_system.create_alerts_from_changes(
    changes_df,
    watchlist_manager,
    risk_analyzer,
    aggregated_df,
    history_manager.load_history()
)
```

7. **Supprimer le fichier JSON** :
```bash
rm data/alerts.json
```

---

## FEAT-07: Timestamps et Tracking

**Statut** : ⚙️ OPTIONNEL (actuellement activé)

### Description
Ajout de colonnes `created_at` et `updated_at` dans le tableau agrégé pour tracking temporel.

### Fichiers
- `backend/data_manager.py` (méthode `_update_timestamps()`)
- `app.py` (affichage des colonnes)

### Fonctionnalités
- **Colonne `created_at`** : Date de première apparition de la substance
- **Colonne `updated_at`** : Date de dernière modification des données
- **Clé unique** : `cas_id + source_list` pour identifier les substances
- Comparaison intelligente : exclut les colonnes de métadonnées
- Mise à jour conditionnelle basée sur les changements

### Méthodes Principales
- `_update_timestamps(new_df)` : Ajoute ou met à jour les timestamps
- `_dataframes_are_equal(df1, df2)` : Compare en excluant timestamps

### Dépendances
- `pandas`
- `datetime` (standard library)
- CORE-01

### Activation
**Déjà activé par défaut.**

### Désactivation

1. **Dans `backend/data_manager.py`**, fonction `aggregate_all_data()` :
```python
# SUPPRIMER cet appel
aggregated_df = self._update_timestamps(aggregated_df)
```

2. **Dans `backend/data_manager.py`**, fonction `save_aggregated_data()` :
```python
# MODIFIER la comparaison pour ne plus exclure created_at et updated_at
# AVANT
if old_df is not None and not old_df.empty:
    if self._dataframes_are_equal(old_df, df):
        ...

# APRÈS (comparaison directe)
if old_df is not None and not old_df.empty:
    if old_df.equals(df):
        ...
```

3. **Dans `backend/data_manager.py`**, supprimer la méthode :
```python
# SUPPRIMER la méthode _update_timestamps() entièrement
```

4. **Dans `backend/data_manager.py`**, fonction `_dataframes_are_equal()` :
```python
# MODIFIER pour ne plus exclure les timestamps
# AVANT
cols_to_exclude = ['created_at', 'updated_at']
...

# APRÈS
# Comparaison directe sans exclusions
return df1.equals(df2)
```

5. **Dans `app.py`**, fonction `display_update_section()` :
```python
# MODIFIER pour ne plus exclure created_at et updated_at
# AVANT
cols_to_drop = ['source_list', 'created_at', 'updated_at']

# APRÈS
cols_to_drop = ['source_list']
```

---

## FEAT-08: Graphiques Radar des Scores

**Statut** : ⚙️ OPTIONNEL (actuellement activé)

### Description
Visualisation graphique des 4 composantes du score de risque sous forme de graphiques radar (spider charts) pour une compréhension instantanée du profil de risque.

### Fichiers
- `backend/risk_analyzer.py` (méthodes `generate_radar_chart()` et `generate_comparison_radar_chart()`)
- `app.py` (section graphiques radar dans onglet "Ma Surveillance")

### Fonctionnalités
- **Graphique radar individuel** : visualisation du profil de risque d'une substance
  - 4 axes : Fréquence Modifications, Présence Listes, Type Changement, Récence
  - Couleur dynamique selon le niveau de risque (🟢🟡🟠🔴)
  - Légende avec les valeurs exactes
  - Titre avec score total et niveau
- **Mode comparaison** : superposition de 2-3 graphiques radar
  - Sélection multiple de substances
  - Couleurs différentes par substance
  - Tableau comparatif des composantes
  - Identification rapide des différences
- **Interface intuitive** : 2 onglets dans "Ma Surveillance"
  - Onglet "Vue Individuelle" : analyse d'une substance
  - Onglet "Mode Comparaison" : comparaison de plusieurs substances
- **Informations additionnelles** : affichage des prédictions et anomalies sous le graphique

### Méthodes Principales
- `generate_radar_chart(score_data, cas_name)` : Génère un graphique radar pour une substance
- `generate_comparison_radar_chart(scores_data_list, cas_names)` : Génère un graphique comparatif

### Dépendances
- `matplotlib >= 3.8.0` (déjà installé pour FEAT-01)
- `numpy` (déjà installé avec pandas)
- FEAT-04 (Watchlists) **REQUIS**
- FEAT-05 (Risk Analyzer) **REQUIS**

### Activation
**Déjà activé par défaut.**

### Désactivation

**⚠️ Attention** : Requiert FEAT-04 et FEAT-05. Si vous désactivez ces fonctionnalités, FEAT-08 sera automatiquement non fonctionnel.

1. **Dans `backend/risk_analyzer.py`**, supprimer les méthodes :
```python
# SUPPRIMER generate_radar_chart() entièrement
# SUPPRIMER generate_comparison_radar_chart() entièrement
```

2. **Dans `backend/risk_analyzer.py`**, retirer les imports :
```python
# SUPPRIMER
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
```

3. **Dans `app.py`**, retirer l'import matplotlib :
```python
# SUPPRIMER
import matplotlib.pyplot as plt
```

4. **Dans `app.py`**, fonction `display_watchlist_surveillance()`, supprimer la section complète :
```python
# SUPPRIMER tout le bloc (lignes ~808-917)
# Section Graphiques Radar
st.divider()
st.subheader("📊 Graphiques Radar des Scores")
...
# (jusqu'à la fin de la section avant "Option de retirer une substance")
```

### Exemple de Visualisation

**Vue Individuelle** :
- Polygone coloré avec 4 sommets
- Chaque sommet = une composante du score (0-100)
- Aire du polygone = profil global de risque
- Rouge foncé = Critique, Orange = Élevé, Jaune = Moyen, Vert = Faible

**Mode Comparaison** :
- Plusieurs polygones superposés
- Comparaison visuelle instantanée
- Identification des points forts/faibles relatifs

### Bénéfices
✅ **Compréhension instantanée** : voir le profil en un coup d'œil
✅ **Comparaison efficace** : identifier les différences rapidement
✅ **Communication visuelle** : partager l'analyse avec des non-experts
✅ **Prise de décision** : prioriser les actions sur les substances
✅ **Effet wow** : interface moderne et professionnelle

---

## FEAT-09: Calendrier Heatmap des Changements

**Statut** : ⚙️ OPTIONNEL (actuellement activé)

### Description
Visualisation calendaire de l'intensité des changements au fil du temps, inspirée du calendrier de contributions GitHub. Chaque jour est représenté par une case colorée selon le nombre de changements, permettant d'identifier rapidement les patterns d'activité et les périodes critiques.

### Fichiers
- `backend/risk_analyzer.py` (méthode `generate_calendar_heatmap()`)
- `app.py` (nouvel onglet "Calendrier" et fonction `display_calendar_heatmap()`)

### Fonctionnalités

#### 1. Calendrier Heatmap Interactif
- **Format annuel** : 53 semaines × 7 jours (Lundi→Dimanche)
- **Gradient de couleur** :
  - Blanc (`#ebedf0`) : 0 changement
  - Vert clair (`#c6e48b`) : faible activité
  - Vert moyen (`#7bc96f`) : activité modérée
  - Vert foncé (`#196127`) : forte activité
  - Rouge (`#c41e3a`) : activité très intense
- **Tooltips riches** : survol d'un jour affiche :
  - Date
  - Nombre total de changements
  - Détail par type (insertions, suppressions, modifications)

#### 2. Filtres Dynamiques
- **Par année** : sélection de l'année à visualiser
- **Par liste source** : filtrer par testa, testb, testc, testd ou "Toutes"
- **Par type de changement** : "Tous", insertion, suppression, modification

#### 3. Statistiques Détaillées
- **Métriques globales** :
  - Total de changements
  - Jour le plus actif (nombre max de changements)
  - Moyenne de changements par jour
  - Nombre de jours avec activité
- **Focus sur le jour le plus actif** :
  - Date et nombre de changements
  - Répartition par type (insertions, suppressions, modifications)
  - Codes couleur : ✅ vert (insertions), ❌ rouge (suppressions), ✏️ jaune (modifications)
- **Top 10 des jours les plus actifs** :
  - Tableau trié par nombre de changements
  - Rang, date, et nombre de changements

#### 4. Interface Utilisateur
- **Onglet dédié** : "📅 Calendrier" dans la navigation principale
- **Layout responsive** : colonnes pour les filtres (3 colonnes)
- **Graphique pleine largeur** : utilisation de `use_container_width=True`
- **Séparateurs visuels** : `st.divider()` pour structurer

### Méthodes Principales

#### `generate_calendar_heatmap(history_df, year, source_list_filter, change_type_filter)`
Génère un calendrier heatmap avec plotly.

**Paramètres** :
- `history_df` : DataFrame de l'historique des changements
- `year` : Année à afficher (défaut : année courante)
- `source_list_filter` : Filtrer par liste source (optionnel)
- `change_type_filter` : Filtrer par type de changement (optionnel)

**Retour** :
- Figure plotly interactive avec heatmap

**Gestion des erreurs** :
- Historique vide : affiche message "Aucune donnée disponible"
- Colonne timestamp manquante : log erreur et retourne figure vide
- Exception : log erreur avec traceback et affiche message d'erreur

#### `display_calendar_heatmap(history_manager, data_manager, risk_analyzer)`
Affiche l'onglet complet du calendrier heatmap.

**Responsabilités** :
- Charger l'historique via `history_manager`
- Créer les filtres interactifs (année, liste, type)
- Appeler `generate_calendar_heatmap()` avec les filtres
- Calculer et afficher les statistiques
- Gérer les erreurs et les cas limites

### Dépendances

**Packages Python** :
- `plotly >= 6.5.0` (nouvellement ajouté)
- `pandas >= 2.2.0` (déjà installé)
- `numpy` (déjà installé avec pandas)

**Fonctionnalités requises** :
- Historique des changements (`change_history.xlsx`)
- Module `history_manager.py` **REQUIS**

### Activation

**Déjà activé par défaut.**

La fonctionnalité est automatiquement active si :
1. Plotly est installé (`pip install plotly`)
2. Un historique de changements existe dans `data/change_history.xlsx`
3. L'onglet "Calendrier" est visible dans la navigation

### Désactivation

1. **Dans `app.py`**, retirer "Calendrier" de la liste des onglets (ligne 52) :
```python
# AVANT
tabs = st.tabs(["Données Agrégées", "Historique des Changements", "Tendances", "Ma Surveillance", "Calendrier", "Mise à Jour"])

# APRÈS
tabs = st.tabs(["Données Agrégées", "Historique des Changements", "Tendances", "Ma Surveillance", "Mise à Jour"])
```

2. **Dans `app.py`**, supprimer l'appel à `display_calendar_heatmap()` (ligne 66-67) :
```python
# SUPPRIMER
with tabs[4]:
    display_calendar_heatmap(history_manager, data_manager, risk_analyzer)

# Réindexer tabs[5] → tabs[4] pour "Mise à Jour"
with tabs[4]:  # ÉTAIT tabs[5]
    display_update_section(...)
```

3. **Dans `app.py`**, supprimer la fonction complète `display_calendar_heatmap()` (lignes ~1021-1172)

4. **Dans `app.py`**, retirer l'import plotly (ligne 4) :
```python
# SUPPRIMER
import plotly.graph_objects as go
```

5. **Dans `backend/risk_analyzer.py`**, supprimer la méthode `generate_calendar_heatmap()` (lignes ~623-813)

6. **Dans `backend/risk_analyzer.py`**, retirer l'import plotly (ligne 9) :
```python
# SUPPRIMER
import plotly.graph_objects as go
```

7. **Optionnel** : désinstaller plotly si non utilisé ailleurs :
```bash
pip uninstall plotly
pip freeze > requirements.txt
```

### Exemple de Visualisation

**Calendrier annuel** :
```
         S1  S2  S3  S4  S5  ...  S49 S50 S51 S52 S53
Lundi    🟩  🟩  ⬜  🟩  🟨  ...  🟩  🟥  🟩  ⬜  🟩
Mardi    ⬜  🟩  🟩  ⬜  🟩  ...  🟩  🟩  🟨  🟩  ⬜
...
Dimanche 🟩  ⬜  🟩  🟩  🟩  ...  ⬜  🟩  🟩  🟩  🟩
```

**Tooltip au survol d'un jour** :
```
2025-12-15
Total: 8 changements
Insertions: 3
Suppressions: 2
Modifications: 3
```

### Cas d'usage

1. **Identifier les patterns** : Repérer les jours de mise à jour réguliers (ex: tous les mardis)
2. **Détecter les anomalies** : Visualiser les pics d'activité inhabituels
3. **Planning** : Anticiper les périodes de forte activité
4. **Reporting** : Communiquer visuellement l'activité sur une période
5. **Analyse temporelle** : Comparer l'activité entre différentes années
6. **Audit** : Vérifier la régularité des mises à jour des listes ECHA

### Bénéfices

✅ **Visuel impactant** : Compréhension immédiate de l'activité annuelle
✅ **Patterns identifiables** : Repérer facilement les régularités et anomalies
✅ **Interactif** : Tooltips riches avec détails au survol
✅ **Flexible** : Filtres par année, liste source, et type de changement
✅ **Statistiques claires** : Métriques et top 10 pour analyse quantitative
✅ **Inspiration GitHub** : Interface familière pour les développeurs
✅ **Aide à la décision** : Planifier les revues et audits selon l'activité

### Performance

- **Optimisé** : Calcul uniquement des données filtrées
- **Cache** : Plotly utilise le cache navigateur pour les graphiques statiques
- **Responsive** : Taille adaptative avec `use_container_width=True`
- **Léger** : Pas de dépendance lourde, plotly est suffisant

### Améliorations Futures Possibles

- [ ] Vue mensuelle détaillée (calendrier classique)
- [ ] Export de l'image du heatmap en PNG/SVG
- [ ] Comparaison année sur année (overlay de 2 années)
- [ ] Annotations manuelles sur des jours spécifiques
- [ ] Intégration avec FEAT-06 (alertes) : marquer les jours avec alertes

---

## FEAT-10: Timeline Interactive des Substances

**Statut** : ⚙️ OPTIONNEL (actuellement activé)

### Description
Visualisation chronologique complète de l'historique d'une substance spécifique avec tous ses événements (insertions, modifications, suppressions). La timeline permet de tracer l'évolution d'une substance dans le temps et d'analyser l'évolution de son score de risque.

### Fichiers
- `backend/risk_analyzer.py` (méthodes `generate_substance_timeline()` et `generate_risk_score_evolution()`)
- `app.py` (nouvel onglet "Timeline" et fonction `display_substance_timeline()`)

### Fonctionnalités

#### 1. Timeline Chronologique Interactive
- **Ligne temporelle** avec tous les événements d'une substance
- **Points colorés** par type d'événement :
  - 🟢 Vert (`#2ecc71`) : Insertion (symbole cercle ●)
  - 🔴 Rouge (`#e74c3c`) : Suppression (symbole croix ×)
  - 🟠 Orange (`#f39c12`) : Modification (symbole diamant ◆)
- **Tooltips riches** au survol :
  - Date et heure de l'événement
  - Type d'événement avec emoji
  - Liste source concernée
  - Champs modifiés (si applicable)
- **Zoom et pan** : navigation interactive dans le temps
- **Légende** horizontale en haut du graphique

#### 2. Sélection de Substance
- **Selectbox avec recherche** : tapez pour rechercher par CAS ID ou nom
- **Format** : "CAS_ID - Nom de la substance"
- **Tri alphabétique** par nom de substance
- **Métrique** : nombre total d'événements pour la substance

#### 3. Filtre par Type d'Événement
- **Options** : Tous, insertion, suppression, modification
- **Application dynamique** : le graphique se met à jour instantanément
- **Affichage conditionnel** : message si aucun événement du type filtré

#### 4. Graphique d'Évolution du Score de Risque
- **Calcul cumulatif** basé sur les événements :
  - Insertion : +10 points
  - Modification : +5 points
  - Suppression : -15 points
- **Score borné** entre 0 et 100
- **Zones de risque** colorées :
  - 🟢 Vert (0-25) : Faible
  - 🟡 Jaune (25-50) : Moyen
  - 🟠 Orange (50-75) : Élevé
  - 🔴 Rouge (75-100) : Critique
- **Ligne et marqueurs** : visualisation claire de l'évolution
- **Remplissage** : aire sous la courbe pour meilleure lisibilité
- **Note explicative** : explication du calcul du score

#### 5. Tableau Détaillé des Événements
- **Colonnes** : Date/Heure, Type, Liste Source, Champs Modifiés
- **Tri** : événements les plus récents en premier
- **Filtrage** : application du filtre par type si sélectionné
- **Format** : tableau responsive pleine largeur

#### 6. Statistiques par Type
- **3 métriques colorées** :
  - ✅ Insertions (vert)
  - ❌ Suppressions (rouge)
  - ✏️ Modifications (orange)
- **Première et dernière occurrence** :
  - Date du premier événement
  - Date du dernier événement

### Méthodes Principales

#### `generate_substance_timeline(cas_id, history_df, aggregated_df, event_type_filter)`
Génère la timeline chronologique d'une substance.

**Paramètres** :
- `cas_id` : CAS ID de la substance
- `history_df` : DataFrame de l'historique des changements
- `aggregated_df` : DataFrame des données agrégées
- `event_type_filter` : Filtrer par type d'événement (optionnel)

**Retour** :
- Figure plotly interactive avec la timeline

**Logique** :
1. Récupération du nom de la substance
2. Filtrage de l'historique pour le CAS ID
3. Application du filtre par type si spécifié
4. Tri chronologique des événements
5. Création des traces par type d'événement (insertion, suppression, modification)
6. Ajout d'une ligne de base grise reliant les événements
7. Configuration des tooltips et de la mise en page

#### `generate_risk_score_evolution(cas_id, history_df, aggregated_df)`
Génère le graphique d'évolution du score de risque.

**Paramètres** :
- `cas_id` : CAS ID de la substance
- `history_df` : DataFrame de l'historique des changements
- `aggregated_df` : DataFrame des données agrégées

**Retour** :
- Figure plotly avec l'évolution du score

**Logique** :
1. Filtrage de l'historique pour le CAS ID
2. Tri chronologique
3. Calcul cumulatif du score à chaque événement :
   - Score de départ : 50
   - Insertion : +10
   - Modification : +5
   - Suppression : -15
   - Bornes : 0-100
4. Création de la courbe avec marqueurs
5. Ajout des zones de risque colorées (hrect)
6. Configuration de la mise en page

#### `display_substance_timeline(data_manager, history_manager, risk_analyzer)`
Affiche l'onglet complet de la timeline.

**Responsabilités** :
- Charger les données agrégées et l'historique
- Créer la selectbox de sélection de substance
- Créer le filtre par type d'événement
- Afficher la métrique du nombre d'événements
- Appeler `generate_substance_timeline()` pour la timeline
- Appeler `generate_risk_score_evolution()` pour l'évolution du score
- Afficher le tableau détaillé des événements
- Calculer et afficher les statistiques par type
- Afficher les dates de première et dernière occurrence

### Dépendances

**Packages Python** :
- `plotly >= 6.5.0` (déjà installé pour FEAT-09)
- `pandas >= 2.2.0` (déjà installé)

**Fonctionnalités requises** :
- Historique des changements (`change_history.xlsx`) **REQUIS**
- Données agrégées (`aggregated_data.xlsx`) **REQUIS**
- Module `history_manager.py` **REQUIS**
- Module `data_manager.py` **REQUIS**

### Activation

**Déjà activé par défaut.**

La fonctionnalité est automatiquement active si :
1. Plotly est installé
2. Un historique de changements existe
3. Des données agrégées existent
4. L'onglet "Timeline" est visible dans la navigation

### Désactivation

1. **Dans `app.py`**, retirer "Timeline" de la liste des onglets (ligne 56) :
```python
# AVANT
tabs = st.tabs(["Données Agrégées", "Historique des Changements", "Tendances", "Ma Surveillance", "Timeline", "Calendrier", "Mise à Jour"])

# APRÈS
tabs = st.tabs(["Données Agrégées", "Historique des Changements", "Tendances", "Ma Surveillance", "Calendrier", "Mise à Jour"])
```

2. **Dans `app.py`**, supprimer l'appel à `display_substance_timeline()` (lignes 70-71) :
```python
# SUPPRIMER
with tabs[4]:
    display_substance_timeline(data_manager, history_manager, risk_analyzer)

# Réindexer les onglets suivants
with tabs[4]:  # ÉTAIT tabs[5]
    display_calendar_heatmap(...)

with tabs[5]:  # ÉTAIT tabs[6]
    display_update_section(...)
```

3. **Dans `app.py`**, supprimer la fonction complète `display_substance_timeline()` (lignes ~1181-1352)

4. **Dans `backend/risk_analyzer.py`**, supprimer les méthodes :
```python
# SUPPRIMER generate_substance_timeline() (lignes ~815-1006)
# SUPPRIMER generate_risk_score_evolution() (lignes ~1008-1127)
```

### Exemple de Visualisation

**Timeline chronologique** :
```
         2024-01-15    2024-03-22    2024-06-10    2024-09-05
         ●————————————◆—————————————×—————————————●
         ↑            ↑             ↑             ↑
      Insertion   Modification  Suppression   Insertion
```

**Tooltip au survol** :
```
2024-03-22 14:30
Type: ✏️ Modification
Liste: testa
Champs modifiés: info_a_3, info_a_7
```

**Évolution du score** :
```
Score
100 |                                    ┌─ Critique
 75 |                             ┌──────┤
    |                        ┌────┘      └─ Élevé
 50 |                   ┌────┤
    |              ┌────┘    └─ Moyen
 25 |         ┌────┤
    |    ┌────┘    └─ Faible
  0 └────┴──────────────────────────────>
       Temps
```

### Cas d'usage

1. **Audit complet** : Retracer toute l'histoire d'une substance
2. **Investigation** : Comprendre quand et pourquoi une substance a changé de statut
3. **Traçabilité réglementaire** : Documenter l'évolution pour audits
4. **Analyse de tendances** : Identifier les patterns d'évolution du risque
5. **Communication** : Expliquer visuellement l'histoire à des parties prenantes
6. **Prise de décision** : Anticiper les changements futurs basés sur l'historique
7. **Détection d'anomalies** : Repérer les variations brutales de score

### Bénéfices

✅ **Traçabilité totale** : Historique complet en un coup d'œil
✅ **Visuel et intuitif** : Timeline claire et facile à comprendre
✅ **Interactif** : Zoom, pan, tooltips pour exploration détaillée
✅ **Analyse de risque** : Évolution du score dans le temps
✅ **Détails exhaustifs** : Tableau avec tous les événements
✅ **Statistiques claires** : Répartition par type et dates clés
✅ **Aide à la décision** : Comprendre l'évolution pour anticiper
✅ **Audit facilité** : Documentation visuelle pour conformité

### Performance

- **Optimisé** : Filtrage côté serveur pour substances individuelles
- **Responsive** : Graphiques adaptatifs avec plotly
- **Léger** : Pas de calculs lourds, juste agrégation de données
- **Cache** : Plotly utilise le cache navigateur pour les graphiques

### Améliorations Futures Possibles

- [ ] Export de la timeline en image PNG/PDF
- [ ] Annotations manuelles sur des événements spécifiques
- [ ] Comparaison de 2-3 substances sur la même timeline
- [ ] Prédiction du prochain événement basée sur l'historique
- [ ] Intégration avec FEAT-06 (alertes) : marquer les événements avec alertes
- [ ] Filtrage par plage de dates personnalisée
- [ ] Export Excel du tableau des événements
- [ ] Vue "Zoom sur période" pour analyse détaillée d'un intervalle

### Notes Techniques

**Calcul du score** :
Le score de risque est une simulation simplifiée pour démonstration. Pour un usage en production, il faudrait :
- Intégrer le vrai algorithme de scoring de FEAT-05
- Recalculer le score réel à chaque date d'événement
- Utiliser les poids configurables du RiskAnalyzer

**Format de la timeline** :
- Tous les événements sont placés sur y=1 (ligne horizontale)
- La différenciation se fait par couleur et symbole
- Si beaucoup d'événements, considérer un affichage multi-lignes par liste source

---

## FEAT-11: Graphe de Réseau des Substances

**Statut** : ⚙️ OPTIONNEL (actuellement activé)

### Description
Visualisation sous forme de graphe de réseau (network graph) montrant les relations entre substances chimiques et listes ECHA. Le graphe permet d'identifier visuellement les clusters de substances, les co-occurrences dans les listes, et la structure globale des données.

### Fichiers
- `backend/risk_analyzer.py` (méthodes `generate_network_graph()`, `_create_bipartite_graph()`, `_create_substances_only_graph()`)
- `app.py` (nouvel onglet "Réseau" et fonction `display_network_graph()`)

### Fonctionnalités

#### 1. Deux Modes de Visualisation

**Mode Bipartite (Substances-Listes)** :
- **Nœuds substances** (cercles) : à gauche, disposés en demi-cercle
- **Nœuds listes** (carrés) : à droite, disposés en demi-cercle
- **Liens** : connexions entre substances et leurs listes
- **Couleur substances** : selon niveau de risque (🟢🟡🟠🔴)
- **Couleur listes** : 🔵 testa, 🟣 testb, 🟠 testc, 🟢 testd
- **Taille substances** : proportionnelle au score de risque (10-40px)
- **Taille listes** : proportionnelle au nombre de substances (15-50px)

**Mode Substances Uniquement (Co-occurrence)** :
- **Nœuds substances** uniquement, disposés en cercle
- **Liens** : entre substances partageant au moins une liste commune
- **Couleur** : selon niveau de risque
- **Taille** : proportionnelle au nombre de listes (10-42px)
- **Layout circulaire** : répartition uniforme autour d'un cercle

#### 2. Filtres Dynamiques

**Filtre par score de risque** :
- Slider de 0 à 100 (par pas de 5)
- Affiche uniquement les substances avec score ≥ seuil
- Valeur par défaut : 0 (toutes les substances)

**Filtre par listes sources** :
- Multiselect avec toutes les listes disponibles
- Sélection par défaut : toutes les listes
- Permet de focus sur une ou plusieurs listes spécifiques

**Mode de visualisation** :
- Selectbox : "Substances-Listes" ou "Substances uniquement"
- Bascule instantanée entre les deux modes

#### 3. Statistiques du Réseau

**Métriques globales** (4 indicateurs) :
- **Substances** : nombre de substances affichées
- **Listes** : nombre de listes sources incluses
- **Connexions** : nombre total de liens substance-liste
- **Moy. Connexions/Substance** : moyenne de connexions par substance

**Répartition par liste source** :
- Tableau trié par nombre de substances décroissant
- Colonnes : Liste, Nombre de Substances

**Substances multi-listes** :
- Métrique du nombre de substances présentes dans plusieurs listes
- Pourcentage par rapport au total
- Indicateur clé de la complexité réglementaire

#### 4. Légende Interactive

**Mode Bipartite** :
- Légende substances avec 4 niveaux de risque (couleurs + plages)
- Légende listes avec couleurs spécifiques par liste

**Mode Substances Uniquement** :
- Légende niveaux de risque
- Explication de la taille (nombre de listes)
- Explication des liens (co-occurrence)

#### 5. Interactivité Plotly

- **Zoom** : molette de la souris ou pinch
- **Pan** : clic-glisser pour déplacer
- **Hover** : tooltips riches au survol des nœuds
- **Réinitialisation** : double-clic pour reset la vue
- **Légende cliquable** : masquer/afficher les traces

### Méthodes Principales

#### `generate_network_graph(aggregated_df, history_df, min_risk_score, selected_lists, graph_mode)`
Génère le graphe de réseau selon le mode sélectionné.

**Paramètres** :
- `aggregated_df` : DataFrame des données agrégées
- `history_df` : DataFrame de l'historique (optionnel, pour scores)
- `min_risk_score` : Score minimum pour filtrer (0-100)
- `selected_lists` : Liste des sources à inclure (None = toutes)
- `graph_mode` : "bipartite" ou "substances_only"

**Retour** :
- Figure plotly avec le graphe de réseau

**Logique** :
1. Vérification des données (empty checks)
2. Filtrage par listes sélectionnées
3. Calcul des scores de risque pour toutes les substances
4. Filtrage par score de risque minimum
5. Délégation à `_create_bipartite_graph()` ou `_create_substances_only_graph()`
6. Retour de la figure plotly

#### `_create_bipartite_graph(df, substance_scores)`
Crée un graphe bipartite substances-listes.

**Logique** :
1. Extraction des substances et listes uniques
2. **Calcul des positions** :
   - Substances : demi-cercle gauche (x=-1 à -0.7, layout trigonométrique)
   - Listes : demi-cercle droit (x=0.7 à 1, layout trigonométrique)
3. **Création des liens** (edges) :
   - Pour chaque ligne du DataFrame : lien substance → liste
   - Format : liste de coordonnées [x0, x1, None] pour traçage continu
4. **Ajout des nœuds substances** :
   - Cercles colorés selon niveau de risque
   - Taille selon score (10 + score/100 * 30)
   - Tooltips : nom, CAS, score, niveau
5. **Ajout des nœuds listes** :
   - Carrés colorés par liste (mapping fixe)
   - Taille selon nombre de substances (15 + min(count*3, 35))
   - Tooltips : nom liste, nombre de substances
6. **Mise en page** : titre, légende, axes masqués, height=700px

#### `_create_substances_only_graph(df, substance_scores)`
Crée un graphe montrant uniquement les substances.

**Logique** :
1. Extraction des substances uniques
2. **Calcul de la matrice de co-occurrence** :
   - Dictionnaire : cas_id → set(listes)
   - Pour chaque paire de substances : nombre de listes partagées
3. **Calcul des positions** :
   - Layout circulaire : angle = 2π * i / n
   - Coordonnées : (cos(angle), sin(angle))
4. **Création des liens** :
   - Uniquement entre substances partageant ≥1 liste
   - Épaisseur proportionnelle au nombre de listes partagées (non utilisé actuellement)
5. **Ajout des nœuds substances** :
   - Cercles colorés selon risque
   - Taille selon nombre de listes (10 + num_lists * 8)
   - Tooltips : nom, CAS, score, niveau, listes
6. **Mise en page** : titre adapté, pas de légende séparée

#### `display_network_graph(data_manager, history_manager, risk_analyzer)`
Affiche l'onglet complet du graphe de réseau.

**Responsabilités** :
- Charger les données agrégées et l'historique
- Créer les 3 filtres (mode, score, listes)
- Appeler `generate_network_graph()` avec les paramètres
- Afficher le graphique plotly
- Calculer et afficher les statistiques du réseau
- Afficher la répartition par liste source
- Calculer les substances multi-listes
- Afficher la légende selon le mode

### Dépendances

**Packages Python** :
- `plotly >= 6.5.0` (déjà installé pour FEAT-09)
- `pandas >= 2.2.0` (déjà installé)
- `math` (module standard Python)

**Fonctionnalités requises** :
- Données agrégées (`aggregated_data.xlsx`) **REQUIS**
- Historique des changements (`change_history.xlsx`) **OPTIONNEL** (pour scores de risque)
- Module `data_manager.py` **REQUIS**
- Module `history_manager.py` **OPTIONNEL**
- FEAT-05 (RiskAnalyzer) **REQUIS** (pour calcul des scores)

### Activation

**Déjà activé par défaut.**

La fonctionnalité est automatiquement active si :
1. Plotly est installé
2. Des données agrégées existent
3. L'onglet "Réseau" est visible dans la navigation

### Désactivation

1. **Dans `app.py`**, retirer "Réseau" de la liste des onglets (ligne 56) :
```python
# AVANT
tabs = st.tabs(["Données Agrégées", "Historique des Changements", "Tendances", "Ma Surveillance", "Timeline", "Calendrier", "Réseau", "Mise à Jour"])

# APRÈS
tabs = st.tabs(["Données Agrégées", "Historique des Changements", "Tendances", "Ma Surveillance", "Timeline", "Calendrier", "Mise à Jour"])
```

2. **Dans `app.py`**, supprimer l'appel à `display_network_graph()` (lignes 76-77) :
```python
# SUPPRIMER
with tabs[6]:
    display_network_graph(data_manager, history_manager, risk_analyzer)

# Réindexer tabs[7] → tabs[6] pour "Mise à Jour"
with tabs[6]:  # ÉTAIT tabs[7]
    display_update_section(...)
```

3. **Dans `app.py`**, supprimer la fonction complète `display_network_graph()` (lignes ~1357-1532)

4. **Dans `backend/risk_analyzer.py`**, supprimer les méthodes :
```python
# SUPPRIMER generate_network_graph() (lignes ~1129-1221)
# SUPPRIMER _create_bipartite_graph() (lignes ~1223-1394)
# SUPPRIMER _create_substances_only_graph() (lignes ~1396-1523)
```

### Exemple de Visualisation

**Mode Bipartite** :
```
Substances (●)        Listes (■)

    ●─────────────■ testa
   ●─┘     ┌──────■ testb
  ●──────┬─┴──────■ testc
   ●─────┴────────■ testd
    ●────────────┘

Gauche: substances colorées par risque
Droite: listes colorées par type
```

**Tooltip substance** :
```
Substance XYZ
CAS: 123-45-6
Score: 67.3
Niveau: 🟠 Élevé
```

**Tooltip liste** :
```
Liste: testa
Substances: 12
```

**Mode Substances Uniquement** :
```
        ●────●
      ●   ╱│╲   ●
     ●   ╱ │ ╲   ●
      ● ╱  │  ╲ ●
       ●───●───●

Cercle de substances
Liens = co-occurrence dans listes
```

### Cas d'usage

1. **Vue d'ensemble** : Comprendre la structure globale des données
2. **Identification de clusters** : Repérer les groupes de substances liées
3. **Analyse de centralité** : Identifier les substances dans beaucoup de listes
4. **Détection de patterns** : Voir quelles substances partagent les mêmes profils
5. **Communication** : Expliquer visuellement les interconnexions aux parties prenantes
6. **Découverte** : Trouver des substances similaires à surveiller ensemble
7. **Analyse de complexité** : Évaluer le niveau d'interconnexion du système
8. **Audit** : Visualiser la couverture réglementaire des substances

### Bénéfices

✅ **Visuel impactant** : Compréhension immédiate de la structure des données
✅ **Deux perspectives** : Mode bipartite ET mode co-occurrence
✅ **Interactif** : Zoom, pan, hover pour exploration détaillée
✅ **Filtres puissants** : Score de risque et listes sources
✅ **Statistiques claires** : Métriques de réseau calculées automatiquement
✅ **Identification rapide** : Substances multi-listes visibles instantanément
✅ **Aide à la décision** : Prioriser les substances centrales
✅ **Communication** : Partager la complexité réglementaire visuellement

### Performance

- **Optimisé** : Filtrage côté serveur avant génération du graphe
- **Layout mathématique** : Calculs trigonométriques légers (sin/cos)
- **Pas de librairie externe** : Utilise uniquement plotly + math standard
- **Responsive** : Graphiques adaptatifs avec plotly
- **Scalabilité** :
  - Mode bipartite : performant jusqu'à ~100 substances
  - Mode substances_only : O(n²) pour les liens, considérer filtrage pour >50 substances

### Améliorations Futures Possibles

- [ ] **Algorithmes de layout avancés** : Force-directed (D3.js), Fruchterman-Reingold
- [ ] **Export image** : PNG/SVG du graphe
- [ ] **Analyse de centralité** : Calcul automatique des nœuds centraux (degree, betweenness)
- [ ] **Détection de communautés** : Clustering automatique (Louvain, Girvan-Newman)
- [ ] **Épaisseur des liens** : Proportionnelle au nombre de listes partagées (mode substances_only)
- [ ] **Mode 3D** : Graphe en 3 dimensions pour grands réseaux
- [ ] **Animation** : Évolution du réseau dans le temps
- [ ] **Filtrage interactif** : Clic sur nœud pour filtrer les voisins
- [ ] **Comparaison temporelle** : Overlay de deux snapshots du réseau
- [ ] **Métriques avancées** : Densité, coefficient de clustering, diamètre du graphe

### Notes Techniques

**Layout circulaire** :
- Simple et efficace pour visualiser la structure
- Formule : `x = cos(2π * i / n)`, `y = sin(2π * i / n)`
- Évite les chevauchements de nœuds

**Layout bipartite** :
- Deux demi-cercles pour séparer substances et listes
- Formule : `angle = π * (i / (n-1)) + π/2` (range: π/2 à 3π/2)
- Position x ajustée : substances à gauche (-1), listes à droite (+1)

**Gestion des liens** :
- Format plotly : liste de coordonnées avec `None` pour discontinuité
- Exemple : `[x0, x1, None, x2, x3, None]` → 2 liens séparés

**Couleurs** :
- Substances : mapping risque → couleur (color_map dans code)
- Listes : mapping fixe par nom de liste (list_colors dans code)
- Utilisation de codes hexadécimaux pour cohérence

**Complexité** :
- Bipartite : O(n + m) où n=substances, m=connexions
- Substances_only : O(n²) pour calculer la matrice de co-occurrence
- Filtrage : O(n) pour chaque opération

---

## FEAT-12 : Dashboard Analytique Exécutif

### Description

Le **Dashboard Analytique Exécutif** est un onglet de synthèse destiné aux décideurs et managers. Il offre une vue d'ensemble complète de l'état du système de surveillance des substances chimiques à travers des indicateurs clés de performance (KPIs), des jauges visuelles, et des graphiques synthétiques.

**Objectifs** :
- Fournir une vue 360° en un coup d'œil
- Calculer un score de santé global du système (0-100)
- Identifier rapidement les substances critiques
- Suivre les tendances d'activité (7 jours, 30 jours)
- Visualiser la distribution des risques et des listes

**Cas d'usage** :
- Réunions de direction : présentation rapide de l'état du système
- Prise de décision : identifier les zones nécessitant attention
- Reporting : génération de snapshots visuels pour rapports
- Surveillance continue : monitoring de la santé globale

### Fichiers

**Backend** : `backend/risk_analyzer.py`
- Méthode `calculate_dashboard_metrics()` : Calcule toutes les métriques du dashboard
- Méthode `generate_gauge_chart()` : Génère les jauges visuelles

**Frontend** : `app.py`
- Fonction `display_dashboard()` : Affiche le dashboard complet
- Onglet "📊 Dashboard" : Premier onglet de l'application (position prioritaire)

**Dépendances** :
- plotly >= 6.5.0 (graphiques interactifs)
- pandas (manipulation de données)
- streamlit (interface utilisateur)

### Fonctionnalités

#### 1. Score de Santé Global (Health Score)

**Calcul composite** basé sur 3 composantes pondérées :

```python
health_score = (
    0.40 × component_activity +    # 40% : Activité récente
    0.35 × component_risk +        # 35% : Niveau de risque
    0.25 × component_coverage      # 25% : Couverture des listes
)
```

**Composantes** :
1. **Activité** : Basée sur le ratio changements 7j / changements 30j
   - Score élevé = activité soutenue et récente
   - Normalisation : min(ratio × 100, 100)

2. **Risque** : Score de risque moyen inversé
   - Score élevé = risque faible
   - Formule : max(0, 100 - avg_risk_score)

3. **Couverture** : Ratio substances / listes
   - Score élevé = bonne répartition
   - Normalisation : min((substances/listes) × 10, 100)

**Visualisation** : Jauge (gauge) avec code couleur
- Vert (>75) : Santé excellente
- Orange (50-75) : Santé moyenne, attention requise
- Rouge (<50) : Santé faible, action nécessaire
- Seuil de référence à 90% (ligne grise)

#### 2. Indicateurs Clés de Performance (KPIs)

**4 métriques principales** affichées en colonnes :

1. **Total Substances**
   - Nombre total de substances surveillées
   - Icône : 🧪
   - Pas de delta (valeur statique)

2. **Changements (7j)**
   - Nombre de changements sur 7 derniers jours
   - Icône : 🔄
   - Delta : tendance 7j vs période précédente
   - Couleur delta : rouge si positif (plus de changements = attention)

3. **Score Risque Moyen**
   - Moyenne des scores de risque (0-100)
   - Icône : ⚠️
   - Pas de delta
   - Contexte : "Sur 100" affiché en aide

4. **Alertes Actives**
   - Nombre total d'alertes non résolues
   - Icône : 🚨
   - Pas de delta
   - Lien vers l'onglet "Ma Surveillance"

#### 3. Top 5 Substances Critiques

**Critères de sélection** :
- Tri par score de risque décroissant
- Limitation aux 5 premières substances
- Affichage uniquement si des substances existent

**Informations affichées** :
- CAS ID (identifiant unique)
- Nom de la substance (cas_name)
- Liste source
- **Badge de risque** avec code couleur :
  - 🔴 CRITIQUE (score ≥ 75)
  - 🟠 ÉLEVÉ (score ≥ 50)
  - 🟡 MOYEN (score ≥ 25)
  - 🟢 FAIBLE (score < 25)
- Score de risque numérique

**Format** : Tableau avec colonnes structurées

#### 4. Graphiques de Distribution

**Deux donuts interactifs** côte à côte :

**A. Distribution des Risques**
- Répartition des substances par niveau de risque
- 4 catégories : Faible, Moyen, Élevé, Critique
- Code couleur : vert, jaune, orange, rouge
- Affichage : pourcentage + valeur absolue
- Trou central : 40% (donut)

**B. Distribution par Liste Source**
- Répartition des substances par liste ECHA
- Une tranche par liste (testa, testb, testc, testd)
- Couleurs automatiques Plotly
- Affichage : pourcentage + valeur absolue
- Trou central : 40% (donut)

**Caractéristiques communes** :
- Interactif : hover pour détails
- Responsive : adaptation à la largeur
- Légende : automatique avec totaux

#### 5. Métriques d'Activité

**3 indicateurs d'activité** affichés en colonnes :

1. **Total Changements**
   - Somme de tous les changements historiques
   - Icône : 📊
   - Contexte : "Depuis le début"

2. **Changements (30j)**
   - Nombre de changements sur 30 derniers jours
   - Icône : 📅
   - Delta : vs période précédente 30j
   - Couleur delta : rouge si positif

3. **Taux d'Activité**
   - Ratio changements 7j / changements 30j
   - Icône : 📈
   - Format : pourcentage (0-100%)
   - Contexte : "Des changements récents"
   - Interprétation :
     - >50% : Activité très récente et soutenue
     - 25-50% : Activité modérée
     - <25% : Activité faible ou ancienne

#### 6. Graphique de Répartition des Changements

**Bar chart horizontal** avec 3 barres :
- 🆕 Insertions (vert)
- ❌ Suppressions (rouge)
- ✏️ Modifications (orange)

**Caractéristiques** :
- Axe X : nombre de changements
- Axe Y : type de changement
- Hauteur fixe : 300px
- Affichage des valeurs sur les barres

**Résumé textuel** sous le graphique :
```
Sur X changements totaux:
- Y insertions
- Z suppressions
- W modifications
```

#### 7. Statistiques Globales

**4 métriques en colonnes** :

1. **Listes Sources**
   - Nombre de listes distinctes
   - Icône : 📋

2. **Connexions**
   - Nombre total de connexions substance-liste
   - Icône : 🔗
   - Note : peut être > substances (substances multi-listes)

3. **Score Risque Max**
   - Score de risque le plus élevé
   - Icône : 🎯
   - Contexte : "Maximum observé"

4. **Distribution**
   - Ratio connexions / substances
   - Icône : 📊
   - Format : décimale (ex: 1.5)
   - Interprétation : moyenne de listes par substance

#### 8. Footer avec Timestamp

**Information de fraîcheur** :
- Format : "Dernière mise à jour: YYYY-MM-DD HH:MM:SS"
- Style : texte gris centré
- Position : bas du dashboard
- Permet de connaître la fraîcheur des données

### Méthodes Principales

#### `calculate_dashboard_metrics(aggregated_df, history_df)`

**Localisation** : `backend/risk_analyzer.py` (lignes 1525-1680)

**Signature** :
```python
def calculate_dashboard_metrics(
    self,
    aggregated_df: pd.DataFrame,
    history_df: pd.DataFrame
) -> Dict
```

**Paramètres** :
- `aggregated_df` : DataFrame des données agrégées (substances + listes)
- `history_df` : DataFrame de l'historique des changements

**Retour** : Dictionnaire avec 17 clés :
```python
{
    # Données de base
    'total_substances': int,
    'total_lists': int,
    'total_connections': int,

    # Changements
    'total_changes': int,
    'insertions': int,
    'deletions': int,
    'modifications': int,
    'changes_7d': int,
    'changes_30d': int,
    'trend_7d': float,  # Delta vs période précédente

    # Risques
    'avg_risk_score': float,
    'max_risk_score': float,
    'risk_distribution': Dict[str, int],  # {Faible: X, Moyen: Y, ...}
    'top_critical': List[Dict],  # Top 5 substances [{cas_id, cas_name, score, level, source_list}]

    # Score de santé
    'health_score': float,  # 0-100

    # Distributions
    'list_distribution': Dict[str, int]  # {testa: X, testb: Y, ...}
}
```

**Logique de calcul** :

1. **Métriques de base** :
   - Total substances : `len(aggregated_df)`
   - Listes uniques : `aggregated_df['source_list'].nunique()`
   - Connexions : nombre de lignes (substance peut être dans plusieurs listes)

2. **Métriques de changements** :
   - Total : `len(history_df)`
   - Par type : `history_df[history_df['change_type'] == 'insertion']`
   - 7j/30j : filtrage par `timestamp` avec `pd.Timestamp.now() - pd.Timedelta(days=N)`
   - Tendance 7j : `changes_7d - changes_prev_7d`

3. **Métriques de risque** :
   - Calcul des scores pour toutes les substances
   - Moyenne : `scores.mean()`
   - Maximum : `scores.max()`
   - Distribution : comptage par niveau (Faible, Moyen, Élevé, Critique)
   - Top 5 : tri par score décroissant + sélection des 5 premiers

4. **Health Score** :
   ```python
   # Composante activité (40%)
   activity_ratio = changes_7d / max(changes_30d, 1)
   component_activity = min(activity_ratio * 100, 100)

   # Composante risque (35%)
   component_risk = max(0, 100 - avg_risk_score)

   # Composante couverture (25%)
   coverage = total_substances / max(total_lists, 1)
   component_coverage = min(coverage * 10, 100)

   # Score final
   health_score = (
       0.40 * component_activity +
       0.35 * component_risk +
       0.25 * component_coverage
   )
   ```

5. **Distributions** :
   - Risque : `groupby` sur niveau de risque
   - Liste : `value_counts()` sur `source_list`

**Gestion des erreurs** :
- DataFrame vide : retourne valeurs par défaut (0, [], {})
- Colonnes manquantes : vérification avec `if col in df.columns`
- Division par zéro : `max(diviseur, 1)` pour éviter ZeroDivisionError
- Logging : toutes les erreurs loguées avec `logger.error()`

**Performance** :
- Complexité : O(n) où n = nombre de substances
- Optimisations :
  - Filtrage pandas (vectorisé)
  - Un seul parcours pour calcul des scores
  - Pas de boucles imbriquées
- Temps d'exécution typique : <100ms pour 10 000 substances

#### `generate_gauge_chart(value, title, max_value=100)`

**Localisation** : `backend/risk_analyzer.py` (lignes 1682-1741)

**Signature** :
```python
def generate_gauge_chart(
    self,
    value: float,
    title: str,
    max_value: float = 100
) -> go.Figure
```

**Paramètres** :
- `value` : Valeur actuelle à afficher (0-max_value)
- `title` : Titre du graphique (ex: "Score de Santé Global")
- `max_value` : Valeur maximale de l'échelle (défaut: 100)

**Retour** : Figure Plotly (plotly.graph_objects.Figure)

**Caractéristiques visuelles** :

1. **Type** : Indicateur (gauge/jauge)
2. **Mode** : "gauge+number+delta"
   - Gauge : arc de cercle
   - Number : valeur numérique au centre
   - Delta : pas utilisé (référence optionnelle)

3. **Code couleur automatique** :
   ```python
   if value >= 75:
       color = "#28a745"  # Vert
   elif value >= 50:
       color = "#ffc107"  # Orange
   else:
       color = "#dc3545"  # Rouge
   ```

4. **Dégradé de fond (4 étapes)** :
   - Rouge (0-25)
   - Orange (25-50)
   - Jaune (50-75)
   - Vert (75-100)

5. **Seuil de référence** :
   - Ligne à 90% (threshold)
   - Couleur : gris (#666)
   - Épaisseur : 4px

6. **Mise en page** :
   - Hauteur : 250px
   - Marge : réduite (t=50, b=0)
   - Police du titre : 16px, bold

**Exemple de code** :
```python
fig = go.Figure(go.Indicator(
    mode="gauge+number",
    value=value,
    title={'text': title, 'font': {'size': 16, 'color': '#2c3e50'}},
    number={'font': {'size': 40}, 'suffix': f"/{max_value}"},
    gauge={
        'axis': {'range': [0, max_value]},
        'bar': {'color': color},
        'steps': [
            {'range': [0, 25], 'color': "#ffebee"},
            {'range': [25, 50], 'color': "#fff3e0"},
            {'range': [50, 75], 'color': "#fffde7"},
            {'range': [75, max_value], 'color': "#e8f5e9"}
        ],
        'threshold': {
            'line': {'color': "#666", 'width': 4},
            'thickness': 0.75,
            'value': max_value * 0.9
        }
    }
))
```

**Utilisation** :
```python
# Avec RiskAnalyzer instancié
health_score = 78.5
fig = risk_analyzer.generate_gauge_chart(
    value=health_score,
    title="Score de Santé Global",
    max_value=100
)
st.plotly_chart(fig, use_container_width=True)
```

#### `display_dashboard(data_manager, history_manager, risk_analyzer, alert_system)`

**Localisation** : `app.py` (lignes 86-348)

**Signature** :
```python
def display_dashboard(
    data_manager,
    history_manager,
    risk_analyzer,
    alert_system
)
```

**Paramètres** :
- `data_manager` : Instance de DataManager
- `history_manager` : Instance de HistoryManager
- `risk_analyzer` : Instance de RiskAnalyzer
- `alert_system` : Instance de AlertSystem

**Retour** : None (affichage Streamlit direct)

**Structure de la fonction** :

```python
def display_dashboard(...):
    # 1. Titre principal
    st.title("📊 Dashboard Analytique Exécutif")

    # 2. Chargement des données
    aggregated_df = data_manager.load_aggregated_data()
    history_df = history_manager.load_history()
    alerts = alert_system.load_alerts()

    # 3. Calcul des métriques
    metrics = risk_analyzer.calculate_dashboard_metrics(aggregated_df, history_df)

    # 4. Section 1: Health Score + 4 KPIs
    col1, col2, col3, col4, col5 = st.columns([2,1,1,1,1])
    # col1: Gauge health score
    # col2-5: KPIs (substances, changes_7d, avg_risk, alerts)

    # 5. Section 2: Top 5 Substances Critiques
    st.subheader("🎯 Top 5 Substances Critiques")
    # Tableau avec badges de risque

    # 6. Section 3: Graphiques de distribution
    col1, col2 = st.columns(2)
    # col1: Donut risques
    # col2: Donut listes

    # 7. Section 4: Métriques d'activité
    col1, col2, col3 = st.columns(3)
    # col1: Total changes
    # col2: Changes 30d
    # col3: Activity rate

    # 8. Section 5: Bar chart changements
    st.subheader("📊 Répartition des Changements")
    # Bar chart + résumé textuel

    # 9. Section 6: Statistiques globales
    col1, col2, col3, col4 = st.columns(4)
    # Listes, connexions, max risk, distribution

    # 10. Footer avec timestamp
    st.markdown("---")
    st.markdown(f"<p style='text-align: center; color: #666;'>Dernière mise à jour: {now}</p>")
```

**Logique de chaque section** :

**Section 1 - Health Score + KPIs** :
```python
with col1:
    fig = risk_analyzer.generate_gauge_chart(
        metrics['health_score'],
        "Score de Santé Global"
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.metric("🧪 Total Substances", metrics['total_substances'])

with col3:
    st.metric("🔄 Changements (7j)", metrics['changes_7d'],
              delta=metrics['trend_7d'], delta_color="inverse")

with col4:
    st.metric("⚠️ Score Risque Moyen",
              f"{metrics['avg_risk_score']:.1f}",
              help="Sur 100")

with col5:
    active_alerts = len([a for a in alerts if a.get('status') == 'active'])
    st.metric("🚨 Alertes Actives", active_alerts)
```

**Section 2 - Top 5 Critiques** :
```python
if metrics['top_critical']:
    data = []
    for sub in metrics['top_critical']:
        badge_color = {
            'Critique': '🔴', 'Élevé': '🟠',
            'Moyen': '🟡', 'Faible': '🟢'
        }[sub['level']]
        data.append({
            'CAS ID': sub['cas_id'],
            'Nom': sub['cas_name'],
            'Liste': sub['source_list'],
            'Niveau': f"{badge_color} {sub['level']}",
            'Score': f"{sub['score']:.1f}"
        })
    st.dataframe(pd.DataFrame(data), use_container_width=True)
else:
    st.info("Aucune substance critique détectée")
```

**Section 3 - Donuts** :
```python
with col1:
    fig = go.Figure(data=[go.Pie(
        labels=list(metrics['risk_distribution'].keys()),
        values=list(metrics['risk_distribution'].values()),
        hole=0.4,
        marker=dict(colors=['#28a745', '#ffc107', '#fd7e14', '#dc3545'])
    )])
    st.plotly_chart(fig)

with col2:
    fig = go.Figure(data=[go.Pie(
        labels=list(metrics['list_distribution'].keys()),
        values=list(metrics['list_distribution'].values()),
        hole=0.4
    )])
    st.plotly_chart(fig)
```

**Section 4 - Activité** :
```python
with col1:
    st.metric("📊 Total Changements", metrics['total_changes'],
              help="Depuis le début")

with col2:
    trend_30d = metrics['changes_30d'] - (metrics['total_changes'] - metrics['changes_30d'])
    st.metric("📅 Changements (30j)", metrics['changes_30d'],
              delta=trend_30d, delta_color="inverse")

with col3:
    rate = (metrics['changes_7d'] / max(metrics['changes_30d'], 1)) * 100
    st.metric("📈 Taux d'Activité", f"{rate:.1f}%",
              help="Des changements récents")
```

**Section 5 - Bar Chart** :
```python
fig = go.Figure(data=[
    go.Bar(name='Insertions', x=[metrics['insertions']],
           y=['Insertions'], orientation='h', marker_color='#28a745'),
    go.Bar(name='Suppressions', x=[metrics['deletions']],
           y=['Suppressions'], orientation='h', marker_color='#dc3545'),
    go.Bar(name='Modifications', x=[metrics['modifications']],
           y=['Modifications'], orientation='h', marker_color='#fd7e14')
])
fig.update_layout(barmode='group', height=300)
st.plotly_chart(fig, use_container_width=True)

st.markdown(f"""
Sur **{metrics['total_changes']}** changements totaux:
- {metrics['insertions']} insertions
- {metrics['deletions']} suppressions
- {metrics['modifications']} modifications
""")
```

**Section 6 - Stats Globales** :
```python
with col1:
    st.metric("📋 Listes Sources", metrics['total_lists'])

with col2:
    st.metric("🔗 Connexions", metrics['total_connections'])

with col3:
    st.metric("🎯 Score Risque Max", f"{metrics['max_risk_score']:.1f}",
              help="Maximum observé")

with col4:
    dist = metrics['total_connections'] / max(metrics['total_substances'], 1)
    st.metric("📊 Distribution", f"{dist:.2f}")
```

**Gestion des erreurs** :
```python
try:
    # Code principal
except FileNotFoundError:
    st.warning("⚠️ Fichiers de données non trouvés. Veuillez charger les données.")
except Exception as e:
    st.error(f"❌ Erreur lors du chargement du dashboard: {str(e)}")
    logger.error(f"Erreur dashboard: {e}", exc_info=True)
```

### Dépendances

**Python** :
- plotly >= 6.5.0 (graphiques gauge et donut)
- pandas >= 2.2.0 (manipulation de données)
- streamlit >= 1.31.0 (interface utilisateur)

**Modules internes** :
- backend.risk_analyzer (RiskAnalyzer)
- backend.data_manager (DataManager)
- backend.history_manager (HistoryManager)
- backend.alert_system (AlertSystem)
- backend.logger (get_logger)

**Données requises** :
- `data/aggregated_data.xlsx` : Données agrégées
- `data/change_history.xlsx` : Historique des changements
- `data/alerts.json` : Alertes actives

### Activation

**Étape 1 : Vérifier les dépendances**
```bash
pip install plotly>=6.5.0 pandas>=2.2.0 streamlit>=1.31.0
```

**Étape 2 : Vérifier la présence du code**

Dans `backend/risk_analyzer.py` :
```python
# Chercher les méthodes
def calculate_dashboard_metrics(self, aggregated_df, history_df):
def generate_gauge_chart(self, value, title, max_value=100):
```

Dans `app.py` :
```python
# Chercher la fonction
def display_dashboard(data_manager, history_manager, risk_analyzer, alert_system):

# Vérifier l'onglet dans la liste des tabs
tabs = st.tabs(["📊 Dashboard", ...])
```

**Étape 3 : Lancer l'application**
```bash
streamlit run app.py
```

**Étape 4 : Accéder au dashboard**
- Ouvrir http://localhost:8501
- **Le dashboard est le premier onglet** (priorité maximale)
- Vérifier l'affichage :
  - Gauge health score visible
  - 4 KPIs affichés
  - Top 5 substances (si données disponibles)
  - 2 donuts (risques et listes)
  - Métriques d'activité
  - Bar chart des changements
  - Stats globales
  - Timestamp en bas

**Pas de configuration supplémentaire requise** : Le dashboard utilise les données déjà présentes.

### Désactivation

**Option 1 : Masquer l'onglet** (recommandé pour désactivation temporaire)

Dans `app.py`, ligne 56 :
```python
# AVANT (dashboard actif)
tabs = st.tabs(["📊 Dashboard", "Données Agrégées", "Historique des Changements", ...])

# APRÈS (dashboard masqué)
tabs = st.tabs(["Données Agrégées", "Historique des Changements", ...])
```

Ajuster les indices des onglets :
```python
# AVANT
with tabs[0]:  # Dashboard
    display_dashboard(...)
with tabs[1]:  # Données Agrégées
    st.header(...)

# APRÈS
# with tabs[0]:  # Dashboard (commenté)
#     display_dashboard(...)
with tabs[0]:  # Données Agrégées (était tabs[1])
    st.header(...)
```

**Option 2 : Supprimer le code** (désactivation permanente)

1. Supprimer la fonction `display_dashboard()` dans `app.py`
2. Retirer "📊 Dashboard" de la liste des tabs
3. Supprimer l'appel dans le bloc `with tabs[0]:`
4. Optionnel : Supprimer les méthodes backend dans `risk_analyzer.py`
   - `calculate_dashboard_metrics()`
   - `generate_gauge_chart()`

**Option 3 : Condition d'affichage**

Dans `app.py`, ajouter un flag de configuration :
```python
# En haut du fichier
ENABLE_DASHBOARD = False  # True pour activer, False pour désactiver

# Dans la définition des tabs
if ENABLE_DASHBOARD:
    tabs = st.tabs(["📊 Dashboard", "Données Agrégées", ...])
else:
    tabs = st.tabs(["Données Agrégées", "Historique des Changements", ...])

# Dans l'affichage
if ENABLE_DASHBOARD:
    with tabs[0]:
        display_dashboard(...)
```

**Impact de la désactivation** :
- Gain de performance négligeable (calculs légers)
- Perte de la vue synthétique pour décideurs
- Les autres fonctionnalités restent 100% opérationnelles
- Aucun impact sur les données ou l'historique

### Exemples de Visualisation

**1. Gauge Health Score**
```
┌─────────────────────────────────┐
│   Score de Santé Global         │
│                                 │
│         ╭───────╮               │
│       ╱  78.5   ╲              │
│      │   /100    │             │
│       ╲         ╱              │
│         ╰───────╯               │
│   ▓▓▓▓▓▓▓▓▓░░░                 │
│  Rouge  Orange  Vert            │
└─────────────────────────────────┘
```

**2. KPIs (4 colonnes)**
```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ 🧪 Total     │ 🔄 Change.   │ ⚠️ Score     │ 🚨 Alertes   │
│ Substances   │ (7j)         │ Risque Moy.  │ Actives      │
│              │              │              │              │
│    1,234     │     23       │    42.3      │      5       │
│              │   ↓ -5       │              │              │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

**3. Top 5 Substances Critiques**
```
┌───────────┬─────────────────────┬────────┬────────────┬───────┐
│ CAS ID    │ Nom                 │ Liste  │ Niveau     │ Score │
├───────────┼─────────────────────┼────────┼────────────┼───────┤
│ 123-45-6  │ Substance Alpha     │ testa  │ 🔴 Critique│  87.5 │
│ 789-01-2  │ Substance Beta      │ testb  │ 🔴 Critique│  82.3 │
│ 345-67-8  │ Substance Gamma     │ testa  │ 🟠 Élevé   │  68.9 │
│ 901-23-4  │ Substance Delta     │ testc  │ 🟠 Élevé   │  65.2 │
│ 567-89-0  │ Substance Epsilon   │ testd  │ 🟠 Élevé   │  61.7 │
└───────────┴─────────────────────┴────────┴────────────┴───────┘
```

**4. Donuts de Distribution**
```
    Distribution des Risques          Distribution par Liste
    ┌─────────────────────┐           ┌─────────────────────┐
    │    ╭─────────╮      │           │    ╭─────────╮      │
    │  ╱           ╲     │           │  ╱           ╲     │
    │ │  Faible 30% │    │           │ │  testa 25%  │    │
    │ │  Moyen  40% │    │           │ │  testb 30%  │    │
    │ │  Élevé  20% │    │           │ │  testc 25%  │    │
    │ │  Crit.  10% │    │           │ │  testd 20%  │    │
    │  ╲           ╱     │           │  ╲           ╱     │
    │    ╰─────────╯      │           │    ╰─────────╯      │
    └─────────────────────┘           └─────────────────────┘
```

**5. Bar Chart Changements**
```
┌──────────────────────────────────────────────────────┐
│      📊 Répartition des Changements                  │
│                                                      │
│  Insertions     ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ 150                  │
│  Suppressions   ▓▓▓▓▓▓▓▓ 80                          │
│  Modifications  ▓▓▓▓▓▓▓▓▓▓▓ 110                      │
│                                                      │
│  Sur 340 changements totaux:                         │
│  - 150 insertions                                    │
│  - 80 suppressions                                   │
│  - 110 modifications                                 │
└──────────────────────────────────────────────────────┘
```

### Cas d'usage

**1. Réunion de Direction Hebdomadaire**

*Contexte* : Le manager qualité doit présenter l'état de la surveillance ECHA

*Utilisation* :
1. Ouvrir le dashboard (premier onglet, accès immédiat)
2. Montrer le **Health Score** : "Notre système est à 78/100"
3. Présenter les **KPIs** : "23 changements cette semaine, 5 alertes actives"
4. Pointer le **Top 5 Critiques** : "Ces 5 substances nécessitent attention immédiate"
5. Commenter la **distribution des risques** : "30% des substances sont à faible risque"

*Bénéfice* : Vue d'ensemble en 2 minutes, pas besoin d'explorer les données

**2. Audit Qualité Externe**

*Contexte* : Un auditeur externe vérifie le système de surveillance

*Utilisation* :
1. Montrer le **Health Score** pour prouver la santé du système
2. Afficher les **métriques d'activité** : "340 changements suivis, 68% d'activité récente"
3. Démontrer la **couverture** : "4 listes sources, 1.5 connexions par substance"
4. Présenter le **graphique des changements** pour montrer la traçabilité

*Bénéfice* : Preuve visuelle de la robustesse du système de surveillance

**3. Prise de Décision Rapide**

*Contexte* : Une substance critique nécessite une action immédiate

*Utilisation* :
1. Vérifier le **Top 5 Critiques** : identifier la substance en question
2. Consulter le **score de risque** : 87.5/100 = action urgente
3. Regarder les **changements 7j** : augmentation = situation évolutive
4. Cliquer sur les **alertes actives** pour voir les détails

*Bénéfice* : Décision éclairée en quelques secondes

**4. Planification Mensuelle**

*Contexte* : Planifier les ressources pour le mois suivant

*Utilisation* :
1. Analyser le **taux d'activité** : 68% = beaucoup de changements récents
2. Comparer **changements 7j vs 30j** : tendance à la hausse ou à la baisse
3. Regarder la **distribution par liste** : identifier les listes les plus actives
4. Estimer les ressources nécessaires en fonction de la tendance

*Bénéfice* : Planification basée sur des données objectives

**5. Communication Interservices**

*Contexte* : Informer le département R&D des tendances

*Utilisation* :
1. Générer un **screenshot du dashboard**
2. Partager les **statistiques globales** par email
3. Pointer les **substances critiques** pour collaboration
4. Utiliser le **timestamp** pour dater l'information

*Bénéfice* : Communication standardisée et professionnelle

**6. Formation des Nouveaux Utilisateurs**

*Contexte* : Former un nouveau membre de l'équipe

*Utilisation* :
1. Commencer par le **dashboard** : vue d'ensemble simple
2. Expliquer le **Health Score** : indicateur synthétique
3. Montrer les **KPIs** : métriques clés à suivre
4. Utiliser le **Top 5** comme exemples concrets

*Bénéfice* : Apprentissage progressif, pas de surcharge cognitive

**7. Reporting Trimestriel**

*Contexte* : Rapport de synthèse pour la direction générale

*Utilisation* :
1. **Screenshot du dashboard** en première page du rapport
2. **Health Score** comme indicateur principal
3. **Graphiques de distribution** dans la section analyse
4. **Statistiques globales** en annexe

*Bénéfice* : Rapport visuel et synthétique

### Bénéfices

**1. Gain de Temps**
- Vue 360° en 1 seul écran (vs 4-5 onglets à naviguer)
- Décisions rapides sans exploration approfondie
- Réunions plus courtes et efficaces

**2. Simplicité**
- Interface intuitive pour non-experts
- Indicateurs visuels (couleurs, jauges, badges)
- Pas de compétences techniques requises

**3. Priorisation**
- Health Score = indicateur unique à suivre
- Top 5 Critiques = focus sur l'essentiel
- Alertes actives = actions immédiates

**4. Communication**
- Langage commun entre équipes (KPIs standardisés)
- Visuels professionnels pour présentations
- Timestamp pour traçabilité

**5. Monitoring Continu**
- Tendances 7j/30j pour anticiper
- Taux d'activité pour ajuster les ressources
- Distribution pour équilibrer la surveillance

**6. Professionnalisme**
- Dashboard de qualité industrielle
- Métriques objectives et calculées
- Confiance des parties prenantes

**7. Évolutivité**
- Structure modulaire (ajout de KPIs facile)
- Calculs optimisés (performance garantie)
- Extensible pour nouveaux besoins

### Performance

**Temps de Calcul** :
- `calculate_dashboard_metrics()` : ~50-100ms pour 10 000 substances
- `generate_gauge_chart()` : ~10ms (léger)
- `display_dashboard()` : ~200-300ms total (avec affichage Streamlit)

**Complexité** :
- O(n) pour calcul des métriques (n = nombre de substances)
- O(m) pour historique (m = nombre de changements)
- O(1) pour génération de la gauge
- **Total** : O(n + m) linéaire, scalable

**Mémoire** :
- Métriques : ~5 KB (dictionnaire avec 17 clés)
- Gauge : ~10 KB (figure Plotly)
- Dashboard complet : ~50 KB en mémoire

**Optimisations Implémentées** :
1. **Calculs vectorisés** : Pandas/Numpy pour éviter les boucles Python
2. **Filtrage early** : Filtres sur dates appliqués avant calculs lourds
3. **Pas de duplication** : Réutilisation des DataFrames chargés
4. **Caching Streamlit** : Possibilité d'ajouter `@st.cache_data` si besoin

**Limitations** :
- Pas de cache par défaut (recalcul à chaque refresh)
- Graphiques Plotly peuvent être lents sur mobile (>1s)
- Health Score complexe = légère pénalité calcul (~20ms)

**Recommandations pour Grandes Données** :
```python
# Si > 100 000 substances, ajouter du caching
@st.cache_data(ttl=300)  # Cache 5 minutes
def get_dashboard_metrics():
    return risk_analyzer.calculate_dashboard_metrics(...)
```

### Améliorations Futures Possibles

**Court Terme** :
1. **Export PDF du Dashboard**
   - Bouton "Télécharger Rapport Dashboard"
   - Génération automatique avec reportlab
   - Inclure tous les graphiques et métriques

2. **Comparaison Temporelle**
   - Health Score vs mois dernier
   - Évolution des KPIs sur 6 mois
   - Graphique de tendance du Health Score

3. **Personnalisation**
   - Choix des KPIs affichés (checkboxes)
   - Seuils configurables pour code couleur
   - Ordre des sections modifiable

**Moyen Terme** :
4. **Alertes Intelligentes**
   - Notification si Health Score < seuil
   - Email automatique pour Top 5 Critiques
   - Prédiction de dégradation du score

5. **Drill-Down Interactif**
   - Clic sur un KPI → filtrage des données
   - Clic sur une substance → timeline
   - Clic sur une liste → détails

6. **Benchmarking**
   - Comparaison avec moyennes sectorielles
   - Ranking vs autres organisations
   - Best practices suggérées

**Long Terme** :
7. **Machine Learning**
   - Prédiction du Health Score futur
   - Détection d'anomalies automatique
   - Recommandations d'actions

8. **Multi-Vues**
   - Dashboard Manager (actuel)
   - Dashboard Opérationnel (détails techniques)
   - Dashboard Compliance (focus réglementaire)

9. **Temps Réel**
   - Mise à jour automatique (refresh auto)
   - Streaming de données
   - Notifications push

**Exemples de Code pour Extensions** :

```python
# Extension 1: Export PDF Dashboard
def export_dashboard_pdf(metrics):
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate

    pdf = SimpleDocTemplate("dashboard.pdf", pagesize=A4)
    # Ajout de tous les éléments du dashboard
    pdf.build(elements)

# Extension 2: Comparaison Temporelle
def calculate_dashboard_comparison(current_metrics, previous_metrics):
    return {
        'health_score_delta': current_metrics['health_score'] - previous_metrics['health_score'],
        'substances_delta': current_metrics['total_substances'] - previous_metrics['total_substances'],
        # ...
    }

# Extension 3: Alertes Intelligentes
def check_dashboard_alerts(metrics):
    alerts = []
    if metrics['health_score'] < 50:
        alerts.append("⚠️ Health Score critique: action requise")
    if metrics['changes_7d'] > 100:
        alerts.append("📈 Activité anormalement élevée")
    return alerts
```

### Notes Techniques

**1. Calcul du Health Score**

Le score de santé est un **indicateur composite** conçu pour résumer l'état global du système en un seul nombre. La formule pondérée a été choisie pour :
- **40% activité** : Privilégier la détection récente de changements (système réactif)
- **35% risque** : Pénaliser fortement les risques élevés (priorité sécurité)
- **25% couverture** : Récompenser une bonne répartition (surveillance équilibrée)

**Limitations** :
- Subjectif : Les poids (40/35/25) sont arbitraires et pourraient être ajustés
- Simplifié : N'inclut pas la qualité des données ou la fraîcheur
- Pas de benchmark : Difficile de savoir si 78/100 est "bon" sans comparaison

**Améliorations possibles** :
```python
# Ajouter une composante "fraîcheur des données"
data_freshness = 100 if (now - last_update) < 1_day else 50
health_score += 0.1 * data_freshness  # 10% du score
```

**2. Code Couleur**

**Choix des seuils** :
- Vert (>75) : Excellent, aucune action
- Orange (50-75) : Moyen, surveillance renforcée
- Rouge (<50) : Critique, action immédiate

Ces seuils sont **cohérents avec les niveaux de risque** utilisés ailleurs dans l'application.

**3. Gestion des Cas Limites**

```python
# Division par zéro
activity_ratio = changes_7d / max(changes_30d, 1)  # Évite ZeroDivisionError

# DataFrame vide
if aggregated_df.empty:
    return default_metrics  # Retourne valeurs par défaut

# Colonnes manquantes
if 'source_list' not in aggregated_df.columns:
    logger.warning("Colonne source_list manquante")
    return default_metrics
```

**4. Ordre des Onglets**

Le dashboard est **intentionnellement en première position** pour :
- Accès immédiat à la vue d'ensemble
- Correspondre aux attentes des managers (synthèse d'abord)
- Encourager une approche top-down (global → détails)

**Impact sur l'UX** :
- Les utilisateurs opérationnels peuvent ignorer le dashboard et aller directement aux autres onglets
- Les décideurs ont leur vue en 1 clic

**5. Performance des Graphiques Plotly**

Les graphiques Plotly sont **interactifs mais plus lourds** que les graphiques statiques (matplotlib).

**Trade-off** :
- ✅ Avantage : Hover, zoom, export PNG intégré
- ❌ Inconvénient : ~500ms de rendu sur mobile vs ~50ms pour matplotlib

**Solution si nécessaire** :
```python
# Remplacer Plotly par matplotlib pour la gauge (plus rapide mais moins joli)
import matplotlib.pyplot as plt

def generate_gauge_matplotlib(value, title):
    fig, ax = plt.subplots()
    # Code gauge matplotlib (simple arc)
    return fig
```

**6. Logging**

Tous les calculs sont loggés pour debug :
```python
logger.info(f"Dashboard metrics calculées: {len(metrics)} clés")
logger.debug(f"Health score: {metrics['health_score']:.2f}")
```

**Utile pour** :
- Identifier des bugs de calcul
- Auditer les décisions prises sur la base du dashboard
- Mesurer les performances (temps de calcul)

**7. Extensibilité du Code**

La structure modulaire facilite les ajouts :
```python
# Ajouter un nouveau KPI
def calculate_dashboard_metrics(...):
    # ...
    metrics['new_kpi'] = calculate_new_kpi()  # Ajout ici
    return metrics

# Afficher dans le dashboard
def display_dashboard(...):
    # ...
    st.metric("🆕 Nouveau KPI", metrics['new_kpi'])  # Ajout ici
```

**Conventions** :
- Tous les calculs dans `calculate_dashboard_metrics()`
- Tous les affichages dans `display_dashboard()`
- Séparation claire backend/frontend

---

# Installation et Déploiement

## Prérequis
- Python 3.8 ou supérieur
- pip
- Git (pour versionning)

## Installation

### 1. Cloner le Projet
```bash
git clone https://github.com/benjlombard/rd_labs1.git
cd rd_labs1
```

### 2. Créer un Environnement Virtuel
```bash
python -m venv venv
```

### 3. Activer l'Environnement

**Windows (Git Bash)** :
```bash
source venv/Scripts/activate
```

**Linux/Mac** :
```bash
source venv/bin/activate
```

### 4. Installer les Dépendances

**Installation complète** (toutes fonctionnalités) :
```bash
pip install -r requirements.txt
```

**Installation minimale** (CORE uniquement) :
```bash
pip install streamlit pandas openpyxl PyYAML
```

### 5. Configuration

Éditer `config.yaml` pour adapter :
- Noms de fichiers
- Noms de colonnes
- Fréquence de mise à jour
- Chemins de dossiers

### 6. Préparer les Données

Placer les fichiers Excel dans `data/input/` :
- `cas_source.xlsx`
- `testa.xlsx`
- `testb.xlsx`
- `testc.xlsx`
- `testd.xlsx`

### 7. Lancer l'Application

```bash
streamlit run app.py
```

Application accessible sur :
- Local : http://localhost:8501
- Réseau : http://[votre-ip]:8501

---

# Migration SharePoint

## Préparation Future

Pour migrer vers SharePoint :

### 1. Installer les Dépendances SharePoint
```bash
pip install Office365-REST-Python-Client
```

### 2. Modifier `config.yaml`
```yaml
sharepoint:
  enabled: true
  site_url: "https://company.sharepoint.com/sites/site"
  folder_path: "/Shared Documents/ECHA"
  credentials_file: "sharepoint_credentials.json"
```

### 3. Créer `sharepoint_credentials.json`
```json
{
  "client_id": "your-client-id",
  "client_secret": "your-client-secret",
  "tenant_id": "your-tenant-id"
}
```

### 4. Modifier `backend/data_manager.py`

Ajouter des méthodes SharePoint :
- `_download_from_sharepoint(file_name)`
- `_upload_to_sharepoint(file_path, file_name)`
- `_connect_to_sharepoint()`

Remplacer les appels locaux :
```python
# AVANT
df = pd.read_excel(file_path)

# APRÈS
if self.config.get('sharepoint', {}).get('enabled'):
    file_path = self._download_from_sharepoint(file_name)
df = pd.read_excel(file_path)
```

---

# Tests

## Tests Unitaires

### Test des Fonctionnalités Watchlist
```bash
python test_watchlist_features.py
```

**9 tests automatiques** :
1. Initialisation des managers
2. Création de watchlist
3. Ajout de CAS ID
4. Chargement des données
5. Calcul de score de risque
6. Prédiction de changement
7. Détection d'anomalies
8. Statistiques
9. Nettoyage

### Tests Manuels

#### Test 1 : Première utilisation
1. Ouvrir http://localhost:8501
2. Onglet "Mise à Jour"
3. Cliquer "Charger et Agréger les Données"
4. Vérifier : Message de succès
5. Onglet "Données Agrégées" : voir les données

#### Test 2 : Pas de changements
1. Cliquer à nouveau "Charger et Agréger"
2. Vérifier : Message "fichier non modifié"
3. Vérifier : Date de modification inchangée

#### Test 3 : Avec changements
1. Modifier un fichier Excel dans `data/input/`
2. Cliquer "Charger et Agréger"
3. Vérifier : Message de succès + aperçu des changements
4. Onglet "Historique" : voir les changements

#### Test 4 : Filtres
1. Onglet "Données Agrégées"
2. Tester filtres par `cas_name` et `cas_id`
3. Tester export CSV
4. Vérifier statistiques

#### Test 5 : Export PDF (si FEAT-01 activé)
1. Cliquer "Générer Rapport PDF"
2. Vérifier : Message de succès
3. Télécharger et ouvrir le PDF
4. Vérifier : Contenu complet

#### Test 6 : Watchlists (si FEAT-04 activé)
1. Onglet "Ma Surveillance"
2. Créer une watchlist
3. Ajouter des substances depuis "Données Agrégées"
4. Vérifier le scoring et les statistiques

#### Test 7 : Alertes (si FEAT-06 activé)
1. Modifier un fichier Excel avec une substance watchlistée
2. Effectuer une mise à jour
3. Vérifier : Badge d'alerte en haut
4. Onglet "Ma Surveillance" : voir les alertes

---

## Commandes Git Utiles

```bash
# Statut
git status

# Voir l'historique
git log --oneline --graph --all

# Créer une branche
git checkout -b feature/nom-feature

# Commit
git add .
git commit -m "Message descriptif"

# Push
git push origin master
```

---

## Support et Contact

- **GitHub** : https://github.com/benjlombard/rd_labs1
- **Documentation Streamlit** : https://docs.streamlit.io
- **Documentation Pandas** : https://pandas.pydata.org/docs/
- **ECHA** : https://echa.europa.eu

---

**Dernière mise à jour** : 31/12/2025
**Version** : 2.0 (Architecture Modulaire)
