# Online Retail ETL + AWS Glue

Ce projet regroupe deux dimensions complementaires :

- une version locale Python du pipeline ETL sur le dataset `Online Retail.xlsx` ;
- une adaptation AWS orientee Glue, S3 et Data Catalog pour industrialiser le traitement.

L'objectif n'est donc plus seulement de nettoyer et analyser le dataset `Online Retail`, mais aussi de montrer comment ce pipeline peut etre projete dans une architecture AWS exploitable.

## Objectifs du projet

Le projet permet de :

- charger les donnees retail, fournisseur et mapping pays/continent ;
- nettoyer les donnees ;
- enrichir les transactions avec `TotalAmount` ;
- produire plusieurs agregations metier ;
- exporter les resultats en Parquet ;
- preparer une execution AWS Glue en mono-job ou en multi-jobs ;
- documenter les chemins S3, les tables Glue et l'enchainement des jobs.

## Perimetre AWS inclus

La partie AWS de ce projet couvre :

- l'utilisation de AWS Glue pour executer le pipeline ;
- la lecture des donnees via le Glue Data Catalog ;
- l'ecriture des sorties analytiques dans S3 ;
- une decomposition du pipeline en 3 jobs Glue : `cleaning`, `transformations`, `aggregations` ;
- des guides de parametrage pour une version mono-job et multi-jobs.

Scripts AWS principaux :

- `AWS_publish/glue_job_cleaning_yomy.py`
- `AWS_publish/glue_job_transformations_yomy.py`
- `AWS_publish/glue_job_aggregations_yomy.py`

Guides associes :

- `AWS_publish/AWS_SINGLE_JOB_GUIDE.md`
- `AWS_publish/AWS_MULTI_JOB_GUIDE.md`

## Fonctionnalites principales

### Version locale

- execution du pipeline via `main.py` ;
- logique metier structuree autour de `DataCleaner`, `TransactionProcessor` et `ETLPipeline` ;
- export local des resultats au format Parquet ;
- tests unitaires avec `pytest`.

### Version AWS Glue

- job 1 : nettoyage et standardisation des donnees ;
- job 2 : enrichissement avec calcul de `TotalAmount` ;
- job 3 : aggregations par pays, mois, fournisseur et continent ;
- production de comptes de controle (`debug_counts`) pour suivre les volumes intermediaires ;
- exploitation de tables Glue plutot que de simples fichiers locaux.

## Resultats produits

Le pipeline peut produire les jeux de donnees suivants :

- `cleaned`
- `enriched`
- `country_sales`
- `monthly_sales`
- `supplier_sales`
- `supplier_sales_uk_2011`
- `continent_sales`
- `cancellations_by_continent`

Le projet inclut aussi des outils pour :

- reorganiser les sorties Parquet avec `AWS_publish/organize_parquet_outputs.py` ;
- inspecter les sorties avec `AWS_publish/view_parquet_outputs.py` ;
- generer des graphes SVG avec `AWS_publish/generate_output_graphs.py`.

## Structure du projet

```text
AWS/
|-- README.md
|-- online_retail/
|-- AWS_publish/
|   |-- Classe_DataCleaner.py
|   |-- Classe_ETLPipeline.py
|   |-- Classe_TransactionProcessor.py
|   |-- main.py
|   |-- glue_job_cleaning_yomy.py
|   |-- glue_job_transformations_yomy.py
|   |-- glue_job_aggregations_yomy.py
|   |-- AWS_SINGLE_JOB_GUIDE.md
|   |-- AWS_MULTI_JOB_GUIDE.md
|   |-- generate_output_graphs.py
|   |-- organize_parquet_outputs.py
|   |-- view_parquet_outputs.py
|   |-- tests/
|   |-- logs/
|   |-- output_graphs/
|   |-- requirements.txt
```

## Installation locale

Prerequis :

- Python 3.10 ou plus
- `pip`

Installation :

```bash
pip install -r AWS_publish/requirements.txt
```

## Execution locale

Pour lancer la version locale publiee du pipeline :

```bash
python AWS_publish/main.py
```

Le pipeline :

- charge les fichiers sources locaux ;
- execute le nettoyage et les transformations ;
- sauvegarde un resultat Parquet dans `output/` ;
- affiche dans les logs les principaux resultats d'analyse.

## Execution des tests

```bash
pytest AWS_publish/tests
```

## Projection AWS recommandee

Architecture cible :

1. depot des fichiers sources dans S3 ;
2. creation d'un crawler Glue ;
3. alimentation du Glue Data Catalog ;
4. execution des jobs Glue ;
5. ecriture des sorties analytiques dans S3 au format Parquet.

ressources AWS mentionnees dans le projet :

- bucket S3 source ;
- bucket S3 de sortie ;
- Glue Data Catalog ;
- jobs AWS Glue ;
- role IAM pour Glue.

## Scenarios AWS documentes

### Option 1 : mono-job

Le guide `AWS_publish/AWS_SINGLE_JOB_GUIDE.md` decrit une version AWS centralisee dans un seul job Glue.

### Option 2 : multi-jobs

Le guide `AWS_publish/AWS_MULTI_JOB_GUIDE.md` decrit une orchestration en 3 jobs :

1. nettoyage ;
2. transformations ;
3. aggregations.

Cette approche est la plus representative de la partie AWS actuellement integree dans ce projet.

## Dependances principales

- pandas
- openpyxl
- pyarrow
- pytest

## Resume

Ce depot ne se limite plus a un simple projet `Online Retail` local. Il documente aussi une evolution vers une chaine ETL AWS basee sur Glue, S3 et le Data Catalog, avec scripts, guides et sorties analytiques adaptes a ce contexte.
