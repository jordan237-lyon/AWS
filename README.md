# Online Retail ETL Pipeline

Projet Python de nettoyage, transformation et analyse de donnees e-commerce a partir du dataset `Online Retail.xlsx`.

Le projet met en place un pipeline ETL simple qui :

- charge les donnees de ventes, fournisseurs et mapping pays/continent ;
- nettoie les doublons, valeurs manquantes et transactions annulees ;
- calcule les montants de vente ;
- produit des agregations par pays, mois, fournisseur et continent ;
- exporte le resultat final au format Parquet.

## Fonctionnalites

- chargement de donnees Excel et CSV ;
- nettoyage de donnees avec une classe dediee ;
- transformations et analyses via un processeur de transactions ;
- orchestration du pipeline dans une classe `ETLPipeline` ;
- script d'execution principal dans `main.py` ;
- tests unitaires avec `pytest`.

## Structure du projet

```text
Online_Retail_repo/
|-- Classe_DataCleaner.py
|-- Classe_ETLPipeline.py
|-- Classe_TransactionProcessor.py
|-- main.py
|-- Online Retail.xlsx
|-- Supplier.csv
|-- country_continent_mapping.csv
|-- tests/
|-- requirements.txt
|-- .gitignore
```

## Analyses produites

Le pipeline genere notamment :

- le DataFrame nettoye avec la colonne `TotalAmount` ;
- le classement des ventes par pays ;
- les statistiques mensuelles de ventes ;
- le produit le plus rentable en France ;
- l'heure de pic des transactions ;
- le classement global des fournisseurs ;
- le classement des fournisseurs au Royaume-Uni en 2011 ;
- l'analyse par continent si le fichier de mapping est fourni.

## Installation

Prerequis :

- Python 3.10 ou plus
- `pip`

Installation des dependances :

```bash
pip install -r requirements.txt
```

## Execution

Pour lancer le pipeline :

```bash
python main.py
```

Le fichier de sortie est enregistre dans :

```text
output/online_retail_cleaned.parquet
```

## Tests

Pour executer les tests :

```bash
pytest
```

## Dependances principales

- pandas
- openpyxl
- pyarrow
- pytest

## Publication GitHub

Une fois le depot GitHub cree, utilise les commandes suivantes :

```bash
git init
git add .
git commit -m "Initial commit - Online Retail ETL project"
git branch -M main
git remote add origin https://github.com/<username>/online-retail.git
git push -u origin main
```
