# preparation des données pour le projet
import logging
from pathlib import Path
from typing import Optional
import pandas as pd  # type: ignore
from Classe_DataCleaner import DataCleaner
from Classe_TransactionProcessor import TransactionProcessor

"""Orchestre le chargement, le nettoyage, les traitements et la sauvegarde."""
class ETLPipeline:
    

    # prépare le pipeline avant exécution en stockant les chemins d'accès aux données et en initialisant les structures nécessaires.
    def __init__(
        self,
        retail_path: str,
        supplier_path: str,
        mapping_path: Optional[str] = None,
    ) -> None:
        self.retail_path = Path(retail_path)
        self.supplier_path = Path(supplier_path)
        self.mapping_path = Path(mapping_path) if mapping_path else None
        self.logger = logging.getLogger(self.__class__.__name__)
        self.df = pd.DataFrame()
        self.results: dict = {}


    # charger les fichiers de données nécessaires au pipeline, et gestion les formats et les erreurs potentielles.
    def load_data(self) -> tuple[pd.DataFrame, pd.DataFrame, Optional[pd.DataFrame]]:
        retail_df = pd.read_excel(self.retail_path)
        supplier_df = pd.read_csv(self.supplier_path)
        mapping_df = None
        if self.mapping_path and self.mapping_path.exists():
            if self.mapping_path.suffix.lower() == ".csv":
                mapping_df = pd.read_csv(self.mapping_path)
            else:
                mapping_df = pd.read_excel(self.mapping_path)
        self.logger.info("Données chargées avec succès.")
        return retail_df, supplier_df, mapping_df


    # exécute toutes les étapes du pipeline dans l'ordre logique, gestion des dépendances entre les étapes, et stockage des résultats.
    def run_pipeline(self) -> dict:
        retail_df, supplier_df, mapping_df = self.load_data()
        cleaner = DataCleaner(retail_df)
        cleaned_df = cleaner.clean()

        processor = TransactionProcessor(cleaned_df)
        self.df = processor.calculate_total_amount()

        processor = TransactionProcessor(self.df)
        country_sales = processor.group_by_country()
        monthly_stats = processor.aggregate_monthly_data()
        stat_results = processor.calcul_stat_data()
        supplier_sales = processor.aggregate_supplier_data(supplier_df)
        supplier_sales_uk_2011 = processor.aggregate_supplier_uk_2011(supplier_df)

        # Les analyses monde ne sont lancées que si un fichier de mapping est disponible.
        world_results = None
        if mapping_df is not None:
            world_results = processor.aggregate_world_data(mapping_df, raw_df=retail_df)
        self.results = {
            "cleaned_df": self.df,
            "country_sales": country_sales,
            "monthly_stats": monthly_stats,
            "stat_results": stat_results,
            "supplier_sales": supplier_sales,
            "supplier_sales_uk_2011": supplier_sales_uk_2011,
            "world_results": world_results,
        }
        self.logger.info("Pipeline ETL exécuté avec succès.")
        return self.results


    # enregistrement du DataFrame final du pipeline au format Parquet.
    def save_as_parquet(self, path: str) -> None:
        if self.df.empty:
            raise ValueError("Le DataFrame final est vide. Exécutez run_pipeline() d'abord.")

        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.df.to_parquet(output_path, index=False)
        self.logger.info("Fichier parquet enregistré : %s", output_path)
