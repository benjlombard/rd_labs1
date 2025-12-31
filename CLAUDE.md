j'ai 4 fichiers excel nommés : testa.xlsx, testb.xlsx, testc.xlsx et testd.xlsx dans un dossier actuellement. Plus tard les fichiers excel seront
probablement sur un sharepoint et donc la location doit être générique pour pouvoir
facilement prendre depuis un sharepoint plus tard.
Chaque fichier excel correspond à une liste de l'agence européenne des substances chimiques : 
 - liste d'authorisation
 - liste chls
 - liste restriction
 - ...

Le fichier testa.xlsx a pour structure :
cas_id,cas_name,info_a_1,info_a_2,info_a_3,info_a_4,info_a_5,info_a_6,info_a_7,info_a_8,info_a_9

le fichier testb.xlsx a pour structure : 
cas_id,cas_name,info_b_1,info_b_2,info_b_3,info_b_4,info_b_5,info_b_6,info_b_7,info_b_8,info_b_9

Le fichier testc.xlsx a pour structure : 
cas_id,cas_name,info_c_1,info_c_2,info_c_3,info_c_4,info_c_5,info_c_6,info_c_7,info_c_8,info_c_9

Le fichier testd.xlsx a pour structure : 
cas_id,cas_name,info_d_1,info_d_2,info_d_3,info_d_4,info_d_5,info_d_6,info_d_7,info_d_8,info_d_9

Tous les jours ou toutes les semaines (la fréquence n'est pas définie encore donc cela doit être facilement modifiable)
Les 4 fichiers excel sont retéléchargés depuis le site ECHA (agence européenne des substances chimiques) et les anciens fichiers sont archivés ou supprimés (à voir ce qui est le mieux).

A chaque mis à jour des 4 fichiers excel on peut avoir plusieurs situations : 
	- Une substance chimique est supprimé d'une liste
	- Une substance chimique est insérée dans une liste
	- Une substance chimique voit ses informations mises à jour

Il faudrait donc peut être créé un fichier excel aggrégeant toutes les données et un autre fichier excel contenant l'historique des modifications / suppressions / insertions.
Je te laisse voir ce qui est le mieux à faire.

L'utilisateur veut un tableau de bord steamlit où
	- Il peut visualiser chaque substance chimique avec toutes les informations disponibles dans les listes. L'idéal serait d'avoir un tableau aggrégeant les 15 listes et une colonne liste source pour savoir à quelle liste appartient une ligne). En sachant qu'une substance chimique peut être dans plusieurs liste.
	- Il veut pouvoir filtrer sur les noms de susbstance chimique et sur le col_cas (identifiant unique)
	- Il veut être alerté dans le tableau de bord (peut être un tableau à part) pour chaque insertion / suppression / modification de chaque liste)

En plus de ces 4 fichiers correspondant à chaque liste, on a une base principale des substances chimiques avec les colonnes cas_id et cas_name. Cette base principale
se trouve dans un fichier excel à part nommé cas_source.xlsx) et on part du principe qu'elle est statique.
On suppose que chaque substance dans les 15 fichiers excels des listes ECHA existent dans la base principale (fichier cas_source.xlsx).

Il faudrait faire un script python pour répondre à ce besoin. Ce script python doit être modulaire (plusieurs fichiers pythons) et le code doit être simple en terme de complexité cyclomatique.
Est-ce que tu penses que la librairie DLT est bien dans ce cas ?
Et explique moi en détail comment tu comptes t'y prendre pour répondre à ce besoin (sans me donner de code).

Une contrainte supplémentaire est la suivante : les noms de colonnes de tous les fichiers excel sont fictifs actuellement. Il faut donc créér un fichier de config contenant les noms de colonnes pour pouvoir les changer plus tard facilement si besoin. Ou bien je te laisse voir ce qui est le mieux à faire pour répondre à cette contrainte.


# Mode de travail : AUTONOME

## Règles d'autonomie

Claude doit travailler en TOTALE AUTONOMIE :
- ❌ NE PAS demander de confirmation
- ❌ NE PAS attendre l'approbation
- ✅ Prendre des décisions seul
- ✅ Exécuter toutes les étapes
- ✅ Corriger les erreurs automatiquement

## Workflow autonome

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

## Décisions autonomes autorisées

✅ Choix d'architecture
✅ Choix de technologies
✅ Structure de code
✅ Noms de variables/fonctions
✅ Organisation des fichiers
✅ Corrections de bugs
✅ Optimisations

## Quand DEMANDER confirmation

Uniquement pour :
- Suppression de données importantes
- Changements de sécurité critiques
- Dépenses financières (API payantes)
- Modifications de production

## Style de communication

Format de réponse :
```
[ACTION] Je crée le module X
[ACTION] J'installe les dépendances
[ACTION] Je configure le système
[ACTION] Je teste
[RÉSULTAT] ✅ Terminé avec succès
```

Pas de questions inutiles type :
❌ "Voulez-vous que je crée le fichier ?"
❌ "Dois-je installer cette dépendance ?"
❌ "Faut-il que je continue ?"

Juste FAIRE.
```

---

## 🚀 Utilisation pratique

### Prompt type pour mode autonome

Au lieu de :
```
"Peux-tu créer un module de logging ?"
```

Utilise :
```
"Crée un module de logging complet avec rotation de fichiers 
et niveaux DEBUG/INFO/ERROR. Implémente tout, teste, et 
confirme quand c'est fait. Ne demande rien."
```

Ou plus court :
```
"/auto Crée un module de logging complet"
```

---

# 📋 SOLUTION IMPLÉMENTÉE

## Architecture de l'Application

### Stack Technique
- **Backend** : Python 3.8+ avec modules modulaires
- **Frontend** : Streamlit (interface web interactive)
- **Configuration** : YAML (config.yaml)
- **Données** : Pandas + openpyxl pour Excel
- **Versionning** : Git + GitHub

### Structure du Projet
```
rd_labs1/
├── app.py                      # Application Streamlit principale
├── config.yaml                 # Configuration (colonnes, fichiers, fréquence)
├── requirements.txt            # Dépendances Python
├── README.md                   # Documentation utilisateur
├── CLAUDE.md                   # Ce fichier - instructions pour Claude
├── .gitignore                  # Fichiers à ignorer par git
├── backend/                    # Modules Python
│   ├── __init__.py
│   ├── logger.py               # Module de logging avec rotation
│   ├── data_manager.py         # Gestion des données Excel
│   ├── change_detector.py      # Détection des changements
│   ├── history_manager.py      # Gestion de l'historique
│   └── pdf_exporter.py         # Export de rapports PDF
├── logs/                       # Logs de l'application (généré, gitignored)
│   ├── echa_app_debug.log      # Logs DEBUG et plus
│   ├── echa_app_info.log       # Logs INFO et plus
│   └── echa_app_error.log      # Logs ERROR et CRITICAL
└── data/                       # Dossier des données
    ├── input/                  # Fichiers Excel sources
    │   ├── cas_source.xlsx     # Base principale des substances
    │   ├── testa.xlsx          # Liste d'autorisation
    │   ├── testb.xlsx          # Liste CHLS
    │   ├── testc.xlsx          # Liste restriction
    │   └── testd.xlsx          # Liste complémentaire
    ├── archives/               # Archives des anciennes versions
    ├── reports/                # Rapports PDF générés (gitignored)
    ├── aggregated_data.xlsx    # Données agrégées (généré)
    └── change_history.xlsx     # Historique des changements (généré)
```

## Modules Backend Implémentés

### 1. data_manager.py
**Responsabilités** :
- Charger les fichiers Excel sources
- Agréger les données de toutes les listes
- Sauvegarder le fichier agrégé (avec optimisation)
- Comparer les DataFrames pour éviter les réécritures inutiles
- Gérer les timestamps de création et modification

**Méthodes principales** :
- `load_cas_source()` : Charge la base principale
- `load_list_file(list_name)` : Charge un fichier spécifique
- `load_all_lists()` : Charge tous les fichiers
- `aggregate_all_data()` : Agrège toutes les listes avec timestamps
- `save_aggregated_data(df, force=False)` : Sauvegarde optimisée (retourne True/False)
- `_dataframes_are_equal(df1, df2)` : Compare deux DataFrames
- `_update_timestamps(new_df)` : Ajoute ou met à jour created_at et updated_at
- `get_file_modification_date(list_name)` : Retourne la date de modification du fichier source

**Optimisation implémentée** :
- Ne réécrit le fichier agrégé QUE si les données ont changé
- Évite les I/O disque inutiles
- Préserve la date de modification si aucun changement
- Paramètre `force=True` pour forcer la sauvegarde

**Gestion des Timestamps** :
- **created_at** : Date de première apparition de la substance (conservée lors des mises à jour)
- **updated_at** : Date de dernière modification des données (mise à jour si changement détecté)
- Clé unique : `cas_id + source_list` pour identifier les substances
- Comparaison intelligente : exclut les colonnes de métadonnées lors de la comparaison

### 2. change_detector.py
**Responsabilités** :
- Détecter les insertions de substances
- Détecter les suppressions de substances
- Détecter les modifications de données
- Identifier les champs modifiés

**Méthodes principales** :
- `detect_changes_for_list(old_df, new_df, list_name)` : Détecte pour une liste
- `detect_all_changes(old_lists, new_lists)` : Détecte pour toutes les listes
- `_create_change_record()` : Crée un enregistrement de changement
- `_get_modified_fields(old_row, new_row)` : Identifie les champs modifiés

**Corrections appliquées** :
- Comparaison uniquement des colonnes communes entre ancienne et nouvelle version
- Évite l'erreur KeyError lors de la comparaison

### 3. history_manager.py
**Responsabilités** :
- Sauvegarder l'historique des changements
- Archiver les anciens fichiers (optionnel)
- Récupérer l'historique avec filtres
- Nettoyer l'historique si nécessaire

**Méthodes principales** :
- `load_history()` : Charge l'historique existant
- `save_changes(changes_df)` : Ajoute des changements
- `archive_files(list_name, file_path)` : Archive un fichier
- `get_recent_changes(limit)` : Récupère les N derniers changements
- `get_changes_by_type(change_type)` : Filtre par type
- `get_changes_by_list(list_name)` : Filtre par liste
- `get_changes_by_cas(cas_id)` : Filtre par CAS ID

### 4. logger.py
**Responsabilités** :
- Gestion centralisée du logging de l'application
- Rotation automatique des fichiers de logs
- Séparation des logs par niveau de criticité
- Affichage console en temps réel

**Caractéristiques** :
- **Niveaux supportés** : DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Rotation** : 10MB max par fichier, 5 fichiers de backup
- **Fichiers séparés** :
  - `echa_app_debug.log` : tous les messages (DEBUG et plus)
  - `echa_app_info.log` : messages INFO, WARNING, ERROR, CRITICAL
  - `echa_app_error.log` : uniquement ERROR et CRITICAL
- **Console** : affiche INFO et plus en temps réel
- **Format** : `YYYY-MM-DD HH:MM:SS - nom - NIVEAU - fichier:ligne - message`
- **Encodage** : UTF-8 pour support caractères spéciaux

**Méthodes principales** :
- `debug(message)` : Log niveau DEBUG
- `info(message)` : Log niveau INFO
- `warning(message)` : Log niveau WARNING
- `error(message, exc_info=False)` : Log niveau ERROR (avec traceback optionnel)
- `critical(message, exc_info=False)` : Log niveau CRITICAL
- `exception(message)` : Log exception avec traceback complet
- `get_logger()` : Fonction singleton pour obtenir l'instance unique

**Intégration** :
- Tous les modules backend utilisent le même logger via `get_logger()`
- Logs détaillés pour chaque opération :
  - DataManager : chargement, agrégation, sauvegarde
  - ChangeDetector : détection des changements par liste
  - HistoryManager : initialisation, sauvegarde historique

**Configuration** :
```python
from backend.logger import get_logger

# Dans chaque module
logger = get_logger()
logger.info("Message d'information")
logger.debug("Message de debug")
logger.error("Message d'erreur", exc_info=True)
```

**Emplacement des logs** :
- Dossier : `logs/`
- Exclus de Git via `.gitignore`
- Rotation automatique quand fichier > 10MB

### 5. pdf_exporter.py
**Responsabilités** :
- Génération de rapports PDF professionnels
- Création de graphiques (matplotlib)
- Mise en page avec tableaux et statistiques
- Export automatique et téléchargement

**Caractéristiques** :
- **Format** : A4, marges optimisées
- **Sections du rapport** :
  - Page titre avec date/heure
  - Statistiques générales (substances, listes, changements)
  - Graphiques (bar chart répartition, pie chart changements)
  - Tableaux (derniers changements, substances)
- **Graphiques** : Matplotlib pour génération, conversion PNG → PDF
- **Mise en page** : ReportLab avec styles personnalisés
- **Encodage** : UTF-8 pour caractères spéciaux
- **Pagination** : Automatique avec PageBreak

**Contenu du rapport** :
1. **Statistiques** :
   - Total substances
   - Substances uniques (CAS ID)
   - Listes sources
   - Total changements (insertions, suppressions, modifications)

2. **Graphiques** :
   - Bar chart : Répartition des substances par liste source
   - Pie chart : Types de changements (insertion, suppression, modification)

3. **Tableaux** :
   - Derniers changements (20 max) : timestamp, type, liste, CAS ID, nom
   - Substances (30 max) : CAS ID, nom, liste source

**Méthodes principales** :
- `generate_report(aggregated_df, history_df, output_path)` : Génère le rapport complet
- `_add_statistics_section()` : Ajoute les statistiques
- `_add_distribution_chart()` : Graphique répartition par liste
- `_add_changes_chart()` : Graphique répartition des changements
- `_add_recent_changes_table()` : Tableau des derniers changements
- `_add_substances_table()` : Tableau des substances

**Styles et couleurs** :
- En-têtes : bleu (#1f77b4)
- Texte : noir (#2c3e50)
- Tableaux : fond beige/blanc alterné
- Graphiques : palette professionnelle

**Intégration** :
- Bouton "Générer Rapport PDF" en haut de l'application
- Téléchargement direct via Streamlit
- Sauvegarde automatique dans `data/reports/rapport_echa_YYYYMMDD_HHMMSS.pdf`
- Logging de toutes les opérations

**Configuration** :
```python
from backend.pdf_exporter import PDFExporter

pdf_exporter = PDFExporter()
success = pdf_exporter.generate_report(aggregated_df, history_df, "rapport.pdf")
```

**Dépendances** :
- `reportlab>=4.0.0` : génération PDF
- `matplotlib>=3.8.0` : graphiques

## Application Streamlit (app.py)

### 4 Onglets Principaux

#### Onglet 1 : Données Agrégées
- Tableau complet de toutes les substances
- Colonnes `source_list`, `created_at`, `updated_at`
- Filtres :
  - Par nom de substance (cas_name)
  - Par identifiant CAS (cas_id)
  - **Par liste source (source_list)**
- Statistiques :
  - Total de substances
  - Substances uniques
  - Répartition par liste
- Export CSV des données filtrées

#### Onglet 2 : Historique des Changements
- Tableau de tous les changements détectés
- Filtres :
  - Par type (insertion, suppression, modification)
  - Par liste source
  - Par CAS ID
- Statistiques des changements
- Export CSV de l'historique

#### Onglet 3 : Tendances
- **Graphique d'évolution du nombre de substances** :
  - Ligne temporelle montrant l'accumulation de substances
  - Basé sur la colonne `created_at`
  - Statistiques : total, première et dernière date
- **Graphique de tendances des changements** :
  - Bar chart des insertions/suppressions/modifications par date
  - Basé sur l'historique avec `timestamp`
  - Statistiques par type de changement
- **Tableau des derniers changements** (10 plus récents)
- **Filtre par liste source** pour analyser une liste spécifique

#### Onglet 4 : Mise à Jour
- Bouton "Charger et Agréger les Données"
- Messages adaptatifs :
  - **Vert** : "Données sauvegardées avec succès" (fichier modifié)
  - **Bleu** : "Aucun changement détecté, fichier non modifié" (optimisé)
  - **Disparition automatique après 5 secondes**
- Détection automatique des changements
- Aperçu des changements détectés
- Vérification de la présence des fichiers sources
- **Affichage de la date de modification des fichiers Excel** (4ème colonne)

## Configuration (config.yaml)

### Sections
```yaml
general:
  update_frequency: "weekly"  # daily, weekly, monthly
  archive_old_files: true     # true = archiver, false = supprimer
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
  # ... autres listes

output_files:
  aggregated_data: "data/aggregated_data.xlsx"
  change_history: "data/change_history.xlsx"
```

### Flexibilité
- Noms de colonnes modifiables facilement
- Fréquence de mise à jour paramétrable
- Noms de fichiers configurables
- Ajout de nouvelles listes simple

## Installation et Lancement

### Étape 1 : Environnement Virtuel
```bash
# Créer l'environnement virtuel
python -m venv venv

# Activer (Windows Git Bash)
source venv/Scripts/activate
```

### Étape 2 : Dépendances
```bash
pip install -r requirements.txt
```

Dépendances installées :
- streamlit >= 1.31.0
- pandas >= 2.2.0
- openpyxl >= 3.1.0
- PyYAML >= 6.0.0
- reportlab >= 4.0.0 (pour export PDF)
- matplotlib >= 3.8.0 (pour graphiques PDF)

### Étape 3 : Lancement
```bash
# Avec l'environnement virtuel activé
streamlit run app.py

# Ou directement
venv/Scripts/python.exe -m streamlit run app.py
```

Application accessible sur :
- Local : http://localhost:8501
- Réseau : http://192.168.1.23:8501

## Workflow Git Utilisé

### Initialisation
```bash
git init
git add .
git commit -m "Initial commit"
```

### GitHub CLI
```bash
# Installation
winget install --id GitHub.cli --silent

# Authentification
gh auth login --web

# Création du dépôt et push
gh repo create rd_labs1 --public --source=. --remote=origin --push
```

### Workflow Feature Branch
```bash
# Créer une branche de feature
git checkout -b feature/optimize-aggregation-save

# Modifications...

# Commit
git add .
git commit -m "Message descriptif"

# Merge sur master
git checkout master
git merge --no-ff feature/optimize-aggregation-save

# Push
git push origin master
git push origin feature/optimize-aggregation-save
```

## Problèmes Rencontrés et Solutions

### Problème 1 : KeyError lors de la comparaison
**Symptôme** : Erreur `KeyError: 'info_b_1'` lors de la 2ème exécution de "Charger et Agréger"

**Cause** : Lors de l'agrégation, toutes les colonnes de toutes les listes sont combinées. En filtrant par liste, on obtenait des colonnes d'autres listes remplies de NaN.

**Solution** :
1. Dans `change_detector.py` : Comparer uniquement les colonnes communes
2. Dans `app.py` : Filtrer les colonnes avant de comparer

### Problème 2 : Fichier réécrit inutilement
**Symptôme** : Le fichier `aggregated_data.xlsx` était réécrit même sans changements

**Cause** : La méthode `save_aggregated_data()` écrivait toujours le fichier

**Solution** :
- Ajout de la méthode `_dataframes_are_equal()` pour comparer les données
- Modification de `save_aggregated_data()` pour retourner True/False
- Ne réécrit que si les données ont changé
- Paramètre `force=True` pour forcer la sauvegarde

### Problème 3 : Erreur Unicode dans les tests
**Symptôme** : `UnicodeEncodeError` avec les caractères ✓ et ✗

**Cause** : Encodage Windows cp1252 qui ne supporte pas les caractères Unicode

**Solution** : Remplacement par `[OK]` et `[ERREUR]`

## Fonctionnalités Clés Implémentées

### ✅ Gestion des Données
- Chargement de fichiers Excel multiples
- Agrégation avec colonne source_list
- Sauvegarde optimisée (évite réécritures inutiles)
- Support de multiples listes (extensible)

### ✅ Détection de Changements
- Insertions détectées
- Suppressions détectées
- Modifications détectées avec champs modifiés
- Comparaison intelligente (colonnes communes uniquement)

### ✅ Historisation
- Enregistrement de tous les changements
- Horodatage automatique
- Archivage optionnel des anciens fichiers
- Filtres multiples (type, liste, CAS ID)

### ✅ Interface Streamlit
- 3 onglets fonctionnels
- Filtres interactifs
- Messages adaptatifs selon les actions
- Statistiques visuelles
- Export CSV

### ✅ Configuration
- Fichier YAML pour tous les paramètres
- Noms de colonnes modifiables
- Fréquence paramétrable
- Ajout de listes simple

### ✅ Logging et Monitoring
- Module de logging centralisé avec rotation de fichiers
- Niveaux DEBUG/INFO/WARNING/ERROR/CRITICAL
- Fichiers séparés par niveau de criticité
- Rotation automatique (10MB max, 5 backups)
- Logs détaillés de toutes les opérations
- Format standardisé avec timestamps et contexte
- Console handler pour suivi temps réel
- Singleton pour instance unique partagée

### ✅ Export PDF et Rapports
- Génération automatique de rapports PDF professionnels
- Statistiques complètes (substances, listes, changements)
- Graphiques intégrés (bar charts, pie charts)
- Tableaux formatés (changements récents, substances)
- Mise en page A4 avec styles personnalisés
- Téléchargement direct depuis l'interface Streamlit
- Sauvegarde automatique dans data/reports/
- Nom de fichier avec timestamp (rapport_echa_YYYYMMDD_HHMMSS.pdf)

### ✅ Tableau de Bord de Tendances (Nouvel Onglet)
- Graphique d'évolution temporelle du nombre de substances
- Graphique de tendances des changements (insertions/suppressions/modifications)
- Analyse par liste source avec filtre dédié
- Statistiques cumulatives et par période
- Visualisation des 10 derniers changements
- Graphiques interactifs avec Streamlit charts

### ✅ Gestion des Timestamps
- Colonnes `created_at` et `updated_at` dans le tableau agrégé
- Tracking automatique de la date de première apparition
- Mise à jour conditionnelle basée sur les changements de données
- Affichage dans l'interface Streamlit
- Persistance entre les mises à jour

### ✅ Améliorations UX
- Filtre par liste source dans l'onglet Données Agrégées
- Affichage des dates de modification des fichiers Excel sources
- Disparition automatique des messages de succès (5 secondes)
- Meilleure visibilité sur l'état des fichiers

### ✅ Qualité du Code
- Architecture modulaire (5 modules backend)
- Faible complexité cyclomatique
- Documentation complète
- Tests unitaires et intégration
- Logging intégré dans tous les modules

## Migration vers SharePoint (Prévu)

Pour adapter l'application à SharePoint :

1. **Installer dépendances SharePoint** :
```bash
pip install Office365-REST-Python-Client
```

2. **Modifier config.yaml** :
```yaml
sharepoint:
  enabled: true
  site_url: "https://company.sharepoint.com/sites/site"
  folder_path: "/Shared Documents/ECHA"
  credentials_file: "sharepoint_credentials.json"
```

3. **Modifier data_manager.py** :
- Remplacer `pd.read_excel(file_path)` par appels API SharePoint
- Ajouter méthodes de connexion SharePoint
- Téléchargement automatique des fichiers

## Tests à Effectuer

### Test 1 : Première utilisation
1. Ouvrir http://localhost:8501
2. Onglet "Mise à Jour"
3. Cliquer "Charger et Agréger les Données"
4. Vérifier : Message vert de succès
5. Onglet "Données Agrégées" : voir les données

### Test 2 : Pas de changements
1. Cliquer à nouveau "Charger et Agréger les Données"
2. Vérifier : Message bleu "fichier non modifié"
3. Vérifier : Date de modification de `data/aggregated_data.xlsx` inchangée

### Test 3 : Avec changements
1. Modifier un fichier Excel dans `data/input/`
2. Cliquer "Charger et Agréger les Données"
3. Vérifier : Message vert + aperçu des changements
4. Onglet "Historique" : voir les changements

### Test 4 : Filtres
1. Onglet "Données Agrégées"
2. Tester filtres par cas_name et cas_id
3. Tester export CSV
4. Vérifier statistiques

### Test 5 : Export PDF
1. En haut de l'application, cliquer "Générer Rapport PDF"
2. Vérifier : Message de succès avec bouton de téléchargement
3. Télécharger le PDF et ouvrir
4. Vérifier le contenu :
   - Page 1 : Titre, date, statistiques générales
   - Page 2 : Graphique bar chart (répartition) + pie chart (changements)
   - Page 3 : Tableau des derniers changements (20 max)
   - Page 4 : Tableau des substances (30 max)
5. Vérifier : Fichier sauvegardé dans `data/reports/rapport_echa_*.pdf`

### Test 6 : Timestamps et Filtres
1. Onglet "Données Agrégées"
2. Vérifier : Présence des colonnes `created_at` et `updated_at`
3. Tester le nouveau filtre "Par liste source"
4. Vérifier : Filtrage correct des données
5. Modifier un fichier Excel et recharger
6. Vérifier : `created_at` conservée, `updated_at` mise à jour

### Test 7 : Onglet Tendances
1. Onglet "Tendances"
2. Vérifier : Graphique d'évolution du nombre de substances (ligne)
3. Vérifier : Graphique de tendances des changements (bar chart)
4. Tester le filtre par liste source
5. Vérifier : Statistiques affichées (total, insertions, suppressions, modifications)
6. Vérifier : Tableau des 10 derniers changements

### Test 8 : Dates des Fichiers
1. Onglet "Mise à Jour"
2. Section "Informations sur les Fichiers"
3. Vérifier : 4ème colonne affiche la date de modification (📅 YYYY-MM-DD HH:MM:SS)
4. Modifier un fichier Excel
5. Recharger la page
6. Vérifier : Date mise à jour

### Test 9 : Disparition des Messages
1. Onglet "Mise à Jour"
2. Cliquer "Charger et Agréger les Données"
3. Observer les messages de succès/info
4. Vérifier : Messages disparaissent automatiquement après 5 secondes
5. Vérifier : Aperçu des changements reste affiché

## Commandes Utiles

### Git
```bash
# Voir l'historique
git log --oneline --graph --all

# Statut
git status

# Voir les différences
git diff

# Créer une branche
git checkout -b feature/nom-feature

# Push
git push origin master
```

### Python
```bash
# Activer environnement
source venv/Scripts/activate

# Installer nouvelle dépendance
pip install nom-package
pip freeze > requirements.txt

# Lancer tests
python test_optimization.py
```

### Streamlit
```bash
# Lancer
streamlit run app.py

# Sur un port spécifique
streamlit run app.py --server.port 8502

# En mode développement (auto-reload)
streamlit run app.py --server.fileWatcherType auto
```

## Points d'Attention pour Recréation

### 1. Structure des Fichiers Excel
- Tous doivent avoir `cas_id` et `cas_name`
- Les autres colonnes doivent être configurées dans config.yaml
- Respecter la structure décrite

### 2. Configuration
- Adapter les noms de colonnes dans config.yaml AVANT de lancer
- Vérifier les chemins de fichiers
- Ajuster la fréquence de mise à jour

### 3. Environnement Virtuel
- TOUJOURS utiliser l'environnement virtuel
- Ne pas commiter le dossier venv/
- Tenir requirements.txt à jour

### 4. Git
- Utiliser des branches pour les features
- Faire des commits atomiques
- Messages de commit descriptifs
- Toujours tester avant de merger

### 5. Optimisations
- La comparaison de DataFrames est activée par défaut
- Pour forcer la sauvegarde : `save_aggregated_data(df, force=True)`
- Les colonnes communes sont automatiquement détectées

## Évolutions Futures Possibles

### Court Terme
- [ ] Ajouter des tests unitaires complets
- [ ] Créer un script de téléchargement automatique ECHA
- [ ] Export Excel enrichi avec mise en forme
- [ ] Comparaison de versions côte à côte

### Moyen Terme
- [ ] Intégration SharePoint
- [ ] Notifications par email lors de changements
- [ ] Personnalisation des rapports PDF (choix des sections)
- [ ] Recherche avancée multi-critères avec opérateurs logiques
- [ ] Annotations et notes utilisateur sur les substances

### Long Terme
- [ ] API REST pour accès externe
- [ ] Authentification utilisateurs
- [ ] Multi-tenancy (plusieurs organisations)
- [ ] Machine Learning pour prédire les changements
- [ ] Gestion de favoris et watchlists

## Références

- **GitHub** : https://github.com/benjlombard/rd_labs1
- **Streamlit Docs** : https://docs.streamlit.io
- **Pandas Docs** : https://pandas.pydata.org/docs/
- **ECHA** : https://echa.europa.eu

---

## 🔄 Pour Recréer le Projet de Zéro

Si tu dois recréer ce projet, voici les étapes EXACTES :

1. **Lire CLAUDE.md** (ce fichier)
2. **Créer la structure** :
   - `mkdir -p backend data/input data/archives data/reports logs`
3. **Créer config.yaml** avec la structure décrite ci-dessus
4. **Créer les 5 modules backend** :
   - `logger.py` avec rotation de fichiers et niveaux DEBUG/INFO/ERROR
   - `data_manager.py` avec optimisation de sauvegarde et logging
   - `change_detector.py` avec comparaison colonnes communes et logging
   - `history_manager.py` avec archivage optionnel et logging
   - `pdf_exporter.py` avec génération de rapports PDF (statistiques, graphiques, tableaux)
5. **Créer app.py** avec 3 onglets Streamlit + section export PDF
6. **Créer requirements.txt** avec versions >= flexibles (streamlit, pandas, openpyxl, PyYAML, reportlab, matplotlib)
7. **Créer .gitignore** excluant venv/, .claude/, test_*.py, logs/, data/reports/
8. **Créer README.md** avec documentation utilisateur
9. **Initialiser git** et pousser sur GitHub
10. **Créer environnement virtuel** et installer dépendances
11. **Tester** l'application et vérifier les logs

**IMPORTANT** :
- Ne pas oublier les optimisations et corrections de bugs mentionnées ci-dessus
- S'assurer que le module logger est créé EN PREMIER (les autres modules en dépendent)
- Intégrer `get_logger()` dans tous les modules backend pour le logging centralisé
- Implémenter la gestion des timestamps (created_at, updated_at) dans data_manager.py
- Créer l'onglet "Tendances" avec les graphiques d'évolution temporelle
- Ajouter le filtre source_list et l'affichage des dates de modification
- Implémenter la disparition automatique des messages après 5 secondes