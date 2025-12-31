# Tableau de Bord - Suivi des Substances Chimiques ECHA

Application Streamlit pour le suivi et la gestion des substances chimiques référencées par l'Agence Européenne des Substances Chimiques (ECHA).

## Fonctionnalités

- **Agrégation des données** : Centralisation de plusieurs listes ECHA dans un tableau unique
- **Détection des changements** : Identification automatique des insertions, suppressions et modifications
- **Historisation** : Suivi complet de l'évolution des données
- **Tableau de bord interactif** : Visualisation et filtrage des substances chimiques
- **Architecture modulaire** : Code Python simple et maintenable

## Structure du Projet

```
rd_labs1/
├── app.py                      # Application Streamlit principale
├── config.yaml                 # Fichier de configuration
├── requirements.txt            # Dépendances Python
├── backend/                    # Modules Python
│   ├── data_manager.py         # Gestion des données
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

## Installation

### Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)

### Étapes d'Installation

1. Cloner ou télécharger le projet

2. Installer les dépendances :
```bash
pip install -r requirements.txt
```

3. Vérifier que les fichiers Excel sont bien présents dans `data/input/`

## Configuration

Le fichier `config.yaml` permet de configurer :

- **Fréquence de mise à jour** : `daily`, `weekly`, ou `monthly`
- **Gestion des archives** : `true` pour archiver, `false` pour supprimer
- **Noms des colonnes** : Modifiables pour s'adapter aux vrais fichiers ECHA
- **Noms des fichiers** : Chemins vers les fichiers Excel

### Exemple de modification des noms de colonnes

Si les colonnes réelles diffèrent, modifiez la section `columns` dans `config.yaml` :

```yaml
columns:
  common:
    cas_id: "CAS_Number"      # Nom réel de la colonne
    cas_name: "Substance_Name"

  testa:
    info_1: "Authorization_Date"
    info_2: "Expiry_Date"
    # ...
```

## Utilisation

### 1. Lancer l'Application

```bash
streamlit run app.py
```

L'application s'ouvrira automatiquement dans votre navigateur par défaut à l'adresse `http://localhost:8501`

### 2. Interface Utilisateur

L'application comporte 3 onglets :

#### Onglet 1 : Données Agrégées

- Visualisation de toutes les substances chimiques
- Filtrage par nom de substance (`cas_name`)
- Filtrage par identifiant CAS (`cas_id`)
- Tableau agrégé avec colonne `source_list` indiquant la provenance
- Statistiques globales et répartition par liste
- Téléchargement des données filtrées en CSV

#### Onglet 2 : Historique des Changements

- Visualisation de tous les changements détectés
- Filtrage par type de changement (insertion, suppression, modification)
- Filtrage par liste source
- Recherche par CAS ID
- Statistiques des changements
- Téléchargement de l'historique en CSV

#### Onglet 3 : Mise à Jour

- Bouton "Charger et Agréger les Données"
- Détection automatique des changements
- Aperçu des changements détectés
- Vérification de la présence des fichiers sources

### 3. Workflow Recommandé

1. **Première utilisation** :
   - Aller dans l'onglet "Mise à Jour"
   - Cliquer sur "Charger et Agréger les Données"
   - Les données sont chargées et agrégées

2. **Mise à jour régulière** :
   - Remplacer les fichiers Excel dans `data/input/` par les nouvelles versions
   - Aller dans l'onglet "Mise à Jour"
   - Cliquer sur "Charger et Agréger les Données"
   - Les changements sont automatiquement détectés et historisés

3. **Consultation** :
   - Onglet "Données Agrégées" pour voir l'état actuel
   - Onglet "Historique des Changements" pour voir les évolutions

## Modules Backend

### data_manager.py

Gère le chargement et l'agrégation des fichiers Excel :
- `load_cas_source()` : Charge la base principale
- `load_list_file(list_name)` : Charge un fichier de liste spécifique
- `aggregate_all_data()` : Agrège toutes les listes
- `save_aggregated_data()` : Sauvegarde les données agrégées
- `load_aggregated_data()` : Charge les données agrégées existantes

### change_detector.py

Détecte les changements entre deux versions :
- `detect_changes_for_list()` : Détecte les changements pour une liste
- `detect_all_changes()` : Détecte les changements pour toutes les listes
- Identifie les insertions, suppressions et modifications
- Enregistre les champs modifiés pour chaque changement

### history_manager.py

Gère l'historique des changements :
- `load_history()` : Charge l'historique existant
- `save_changes()` : Ajoute de nouveaux changements à l'historique
- `archive_files()` : Archive les anciennes versions des fichiers
- `get_recent_changes()` : Récupère les changements récents
- Méthodes de filtrage par type, liste, ou CAS ID

## Évolution vers SharePoint

Pour adapter l'application à des fichiers sur SharePoint :

1. Modifier `data_manager.py` pour utiliser l'API SharePoint
2. Installer les dépendances SharePoint :
   ```bash
   pip install Office365-REST-Python-Client
   ```
3. Configurer les credentials dans `config.yaml`
4. Remplacer `pd.read_excel(file_path)` par des appels API SharePoint

## Maintenance

### Changer la Fréquence de Mise à Jour

Modifier dans `config.yaml` :
```yaml
general:
  update_frequency: "daily"  # ou "weekly", "monthly"
```

### Ajouter une Nouvelle Liste

1. Ajouter le fichier Excel dans `data/input/`
2. Mettre à jour `config.yaml` :
   ```yaml
   source_files:
     lists:
       - name: "teste"
         file: "teste.xlsx"
         description: "Nouvelle liste"

   columns:
     teste:
       info_1: "info_e_1"
       # ...
   ```

### Nettoyer l'Historique

Dans l'onglet "Mise à Jour", un bouton pourrait être ajouté pour appeler :
```python
history_manager.clear_history()
```

## Support

Pour toute question ou problème, consultez la documentation ECHA ou contactez l'équipe de développement.

## Licence

Projet interne - Tous droits réservés
