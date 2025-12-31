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
