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
│   ├── data_manager.py         # Gestion des données Excel
│   ├── change_detector.py      # Détection des changements
│   └── history_manager.py      # Gestion de l'historique
└── data/                       # Dossier des données
    ├── input/                  # Fichiers Excel sources
    │   ├── cas_source.xlsx     # Base principale des substances
    │   ├── testa.xlsx          # Liste d'autorisation
    │   ├── testb.xlsx          # Liste CHLS
    │   ├── testc.xlsx          # Liste restriction
    │   └── testd.xlsx          # Liste complémentaire
    ├── archives/               # Archives des anciennes versions
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

**Méthodes principales** :
- `load_cas_source()` : Charge la base principale
- `load_list_file(list_name)` : Charge un fichier spécifique
- `load_all_lists()` : Charge tous les fichiers
- `aggregate_all_data()` : Agrège toutes les listes
- `save_aggregated_data(df, force=False)` : Sauvegarde optimisée (retourne True/False)
- `_dataframes_are_equal(df1, df2)` : Compare deux DataFrames

**Optimisation implémentée** :
- Ne réécrit le fichier agrégé QUE si les données ont changé
- Évite les I/O disque inutiles
- Préserve la date de modification si aucun changement
- Paramètre `force=True` pour forcer la sauvegarde

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

## Application Streamlit (app.py)

### 3 Onglets Principaux

#### Onglet 1 : Données Agrégées
- Tableau complet de toutes les substances
- Colonne `source_list` indiquant la provenance
- Filtres :
  - Par nom de substance (cas_name)
  - Par identifiant CAS (cas_id)
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

#### Onglet 3 : Mise à Jour
- Bouton "Charger et Agréger les Données"
- Messages adaptatifs :
  - **Vert** : "Données sauvegardées avec succès" (fichier modifié)
  - **Bleu** : "Aucun changement détecté, fichier non modifié" (optimisé)
- Détection automatique des changements
- Aperçu des changements détectés
- Vérification de la présence des fichiers sources

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

### ✅ Qualité du Code
- Architecture modulaire (3 modules backend)
- Faible complexité cyclomatique
- Documentation complète
- Tests unitaires possibles

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
- [ ] Corriger le warning `use_container_width` (remplacer par `width`)
- [ ] Ajouter des tests unitaires complets
- [ ] Créer un script de téléchargement automatique ECHA

### Moyen Terme
- [ ] Intégration SharePoint
- [ ] Notifications par email lors de changements
- [ ] Export PDF des rapports
- [ ] Graphiques d'évolution des substances

### Long Terme
- [ ] API REST pour accès externe
- [ ] Authentification utilisateurs
- [ ] Multi-tenancy (plusieurs organisations)
- [ ] Machine Learning pour prédire les changements

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
   - `mkdir -p backend data/input data/archives`
3. **Créer config.yaml** avec la structure décrite ci-dessus
4. **Créer les 3 modules backend** :
   - `data_manager.py` avec optimisation de sauvegarde
   - `change_detector.py` avec comparaison colonnes communes
   - `history_manager.py` avec archivage optionnel
5. **Créer app.py** avec 3 onglets Streamlit
6. **Créer requirements.txt** avec versions >= flexibles
7. **Créer .gitignore** excluant venv/, .claude/, test_*.py
8. **Créer README.md** avec documentation utilisateur
9. **Initialiser git** et pousser sur GitHub
10. **Créer environnement virtuel** et installer dépendances
11. **Tester** l'application

**IMPORTANT** : Ne pas oublier les optimisations et corrections de bugs mentionnées ci-dessus