# AWS Glue Multi-Job Guide

Ce guide traduit l'enonce en une architecture a 3 jobs AWS Glue :

1. nettoyage
2. transformation
3. aggregations

## Vue d'ensemble

On decoupe le pipeline en trois jobs :

1. `glue_job_cleaning.py`
2. `glue_job_transformations.py`
3. `glue_job_aggregations.py`

Cette separation est simple a expliquer :

- `DataCleaner` dans le job 1 ;
- enrichissement avec `TotalAmount` dans le job 2 ;
- calcul des agregations metier dans le job 3.

## Job 1 : nettoyage

Fichier :

- [glue_job_cleaning.py](C:\Users\JordanYOMY\Documents\kuikops\AWS\online_retail\glue_job_cleaning.py)

Source :

- Glue Data Catalog
- database : `online_retail_db`
- table retail : typiquement `online_retail_online_retail`

Role :

- lire la table retail brute detectee par le crawler ;
- nettoyer les types ;
- supprimer les doublons ;
- traiter les valeurs manquantes ;
- exclure les transactions annulees ;
- filtrer les valeurs aberrantes ;
- ecrire un dataset nettoye en Parquet dans S3.

Sortie recommandee :

- `s3://online-retail03/output/cleaned/`

Arguments :

- `JOB_NAME`
- `catalog_database`
- `retail_table`
- `cleaned_output_path`

Exemple :

- `JOB_NAME = online-retail-cleaning-job`
- `catalog_database = online_retail_db`
- `retail_table = online_retail_online_retail`
- `cleaned_output_path = s3://online-retail03/output/cleaned/`

## Job 2 : transformation

Fichier :

- [glue_job_transformations.py](C:\Users\JordanYOMY\Documents\kuikops\AWS\online_retail\glue_job_transformations.py)

Source :

- le dataset nettoye produit par le job 1

Role :

- lire le dataset nettoye ;
- calculer `TotalAmount` ;
- ecrire un dataset enrichi en Parquet.

Sortie recommandee :

- `s3://online-retail03/output/enriched/`

Arguments :

- `JOB_NAME`
- `cleaned_input_path`
- `enriched_output_path`

Exemple :

- `JOB_NAME = online-retail-transformations-job`
- `cleaned_input_path = s3://online-retail03/output/cleaned/`
- `enriched_output_path = s3://online-retail03/output/enriched/`

## Job 3 : aggregations

Fichier :

- [glue_job_aggregations.py](C:\Users\JordanYOMY\Documents\kuikops\AWS\online_retail\glue_job_aggregations.py)

Sources :

- le dataset enrichi produit par le job 2
- la table supplier du Glue Data Catalog
- la table mapping du Glue Data Catalog
- la table retail brute pour recalculer les annulations par continent

Role :

- produire les agregations par pays ;
- produire les agregations mensuelles ;
- calculer les agregations fournisseurs ;
- calculer les ventes par continent ;
- calculer les annulations par continent a partir de la source brute.

Arguments :

- `JOB_NAME`
- `catalog_database`
- `retail_table`
- `supplier_table`
- `mapping_table`
- `enriched_input_path`
- `country_output_path`
- `monthly_output_path`
- `supplier_output_path`
- `supplier_uk_output_path`
- `world_output_path`
- `cancellation_output_path`

Exemple :

- `JOB_NAME = online-retail-aggregations-job`
- `catalog_database = online_retail_db`
- `retail_table = online_retail_online_retail`
- `supplier_table = online_retail_supplier`
- `mapping_table = online_retail_country_continent_mapping`
- `enriched_input_path = s3://online-retail03/output/enriched/`
- `country_output_path = s3://online-retail03/output/country_sales/`
- `monthly_output_path = s3://online-retail03/output/monthly_sales/`
- `supplier_output_path = s3://online-retail03/output/supplier_sales/`
- `supplier_uk_output_path = s3://online-retail03/output/supplier_sales_uk_2011/`
- `world_output_path = s3://online-retail03/output/continent_sales/`
- `cancellation_output_path = s3://online-retail03/output/cancellations_by_continent/`

## Enchainement

Ordre d'execution :

1. lancer le crawler ;
2. verifier les tables dans `online_retail_db` ;
3. executer `glue_job_cleaning.py` ;
4. verifier la sortie `cleaned/` ;
5. executer `glue_job_transformations.py` ;
6. verifier la sortie `enriched/` ;
7. executer `glue_job_aggregations.py`.

## Option Step Functions

Si tu veux aller plus loin, Step Functions pourra enchainer :

1. job de nettoyage
2. job de transformation
3. job d'aggregations
4. etapes de validation eventuelles