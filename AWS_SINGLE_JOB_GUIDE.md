# AWS Glue Single Job Guide

Ce document explique comment la version locale du projet est projetee vers une implementation AWS Glue avec un seul job, sans rien executer sur AWS pour le moment.

## 1. Fichier cible

Le script principal AWS est :

- [glue_job_single.py](C:\Users\JordanYOMY\Documents\kuikops\AWS\online_retail\glue_job_single.py)

Il a ete ecrit pour etre lance par AWS Glue et non en local.

## 2. Changement de logique d'entree

La version locale lit :

- `Online Retail.xlsx`
- `Supplier.csv`
- `country_continent_mapping.csv`

La version AWS la plus propre lit des tables du Glue Data Catalog creees par le crawler.

Pour ton cas, on vise :

- `catalog_database = online_retail_db`
- `retail_table = online_retail_online_retail`
- `supplier_table = online_retail_supplier`
- `mapping_table = online_retail_country_continent_mapping`

Point important :

- les noms exacts de tables peuvent varier legerement selon le crawler ;
- il faudra reprendre les noms reels visibles dans `online_retail_db` si AWS cree des variantes.

## 3. Passage de pandas vers Spark

La version locale repose sur `pandas`.

La version AWS repose sur :

- `GlueContext`
- `SparkSession`
- `pyspark.sql.DataFrame`

Pourquoi :

- Glue classique execute des jobs Spark ;
- Spark est adapte aux traitements distribues ;
- cela rend le script conforme a une implementation Glue standard.

## 4. Classes conservees

La structure POO a ete conservee :

- `DataCleaner`
- `TransactionProcessor`
- `ETLPipeline`

Cela permet de garder la meme logique metier entre :

- la version locale de preparation ;
- la version Glue de production.

## 5. Parametres attendus par le job Glue

Le script attend ces arguments :

- `JOB_NAME`
- `catalog_database`
- `retail_table`
- `supplier_table`
- `mapping_table`
- `cleaned_output_path`
- `country_output_path`
- `monthly_output_path`
- `supplier_output_path`
- `supplier_uk_output_path`
- `world_output_path`
- `cancellation_output_path`

Exemple de valeurs a renseigner dans AWS Glue :

- `JOB_NAME = online-retail-single-job`
- `catalog_database = online_retail_db`
- `retail_table = online_retail_online_retail`
- `supplier_table = online_retail_supplier`
- `mapping_table = online_retail_country_continent_mapping`
- `cleaned_output_path = s3://online-retail03/output/cleaned/`
- `country_output_path = s3://online-retail03/output/country_sales/`
- `monthly_output_path = s3://online-retail03/output/monthly_sales/`
- `supplier_output_path = s3://online-retail03/output/supplier_sales/`
- `supplier_uk_output_path = s3://online-retail03/output/supplier_sales_uk_2011/`
- `world_output_path = s3://online-retail03/output/continent_sales/`
- `cancellation_output_path = s3://online-retail03/output/cancellations_by_continent/`

Cela permet de separer clairement :

- la source de metadonnees du Data Catalog ;
- les sorties de donnees dans S3 ;
- la logique du job.

## 6. Comment le job lit les donnees

Le job lit maintenant les datasets via le Glue Data Catalog avec :

- `create_dynamic_frame.from_catalog(...)`

Puis convertit ces lectures en Spark DataFrames pour appliquer le pipeline.

Cela veut dire que le crawler devient une vraie etape utile :

- il enregistre les tables ;
- le job Glue lit ensuite ces tables au lieu de relire directement des chemins S3.

## 7. Sorties produites

Le job ecrit des fichiers Parquet dans S3 pour :

- le dataset nettoye enrichi ;
- l'agregation par pays ;
- l'agregation mensuelle ;
- les ventes par fournisseur ;
- les ventes fournisseurs UK 2011 ;
- les ventes par continent ;
- les annulations par continent.

## 8. Ressources AWS a prevoir

Quand tu voudras passer a l'execution AWS, il faudra preparer :

- un bucket S3 source ;
- un bucket S3 de sortie ;
- un role IAM pour Glue ;
- un crawler Glue ;
- un job Glue Python/Spark ;
- une database Glue `online_retail_db`.

## 9. Ordre recommande pour la suite

1. Verifier les noms reels des tables creees dans `online_retail_db`.
2. Ajuster si besoin les valeurs `retail_table`, `supplier_table` et `mapping_table`.
3. Creer le job Glue avec `glue_job_single.py`.
4. Renseigner les arguments du job.
5. Tester d'abord avec un jeu de donnees reduit si possible.
6. Ensuite seulement executer le job complet.