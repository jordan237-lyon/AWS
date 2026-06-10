import logging
from pathlib import Path

from Classe_ETLPipeline import ETLPipeline


def configure_logging() -> None:
    # Les logs permettent de suivre clairement les etapes d'execution du pipeline.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def main() -> None:
    # On construit les chemins des fichiers a partir du dossier du projet.
    current_dir = Path(__file__).resolve().parent
    retail_path = current_dir / "Online Retail.xlsx"
    supplier_path = current_dir / "Supplier.csv"
    mapping_path = current_dir / "country_continent_mapping.csv"
    output_path = current_dir / "output" / "online_retail_cleaned.parquet"

    pipeline = ETLPipeline(
        retail_path=str(retail_path),
        supplier_path=str(supplier_path),
        mapping_path=str(mapping_path) if mapping_path.exists() else None,
    )

    # On execute le pipeline puis on enregistre le DataFrame final.
    results = pipeline.run_pipeline()
    pipeline.save_as_parquet(str(output_path))

    # On affiche les sorties principales de chaque traitement de TransactionProcessor.
    logging.info("Apercu du DataFrame final avec TotalAmount :\n%s", results["cleaned_df"].head())
    logging.info("Resultat group_by_country - Top 10 pays par ventes :\n%s", results["country_sales"].head(10))
    logging.info("Resultat aggregate_monthly_data - Statistiques mensuelles :\n%s", results["monthly_stats"])

    stat_results = results["stat_results"]
    logging.info(
        "Resultat calcul_stat_data - Produit le plus rentable en France : %s",
        stat_results["best_product_france"],
    )
    logging.info(
        "Resultat calcul_stat_data - Heure de pic des transactions : %s",
        int(stat_results["peak_hour"]) if stat_results["peak_hour"] is not None else None,
    )
    logging.info(
        "Resultat calcul_stat_data - Transactions par heure :\n%s",
        stat_results["transaction_peak_hour"],
    )

    logging.info(
        "Resultat aggregate_supplier_data - Top 10 fournisseurs monde :\n%s",
        results["supplier_sales"].head(10),
    )
    logging.info(
        "Resultat aggregate_supplier_uk_2011 - Top 10 fournisseurs UK 2011 :\n%s",
        results["supplier_sales_uk_2011"].head(10),
    )

    world_results = results["world_results"]
    if world_results is not None:
        logging.info(
            "Resultat aggregate_world_data - Depenses par continent :\n%s",
            world_results["continent_sales"],
        )
        logging.info(
            "Resultat aggregate_world_data - Annulations par continent :\n%s",
            world_results["cancellations_by_continent"],
        )
        logging.info(
            "Resultat aggregate_world_data - Continent avec le plus d'annulations : %s",
            world_results["top_cancelled_continent"],
        )
    else:
        logging.info("Resultat aggregate_world_data - Analyse monde ignoree car aucun mapping n'a ete fourni.")


if __name__ == "__main__":
    configure_logging()
    main()
