import logging
from typing import Optional

import pandas as pd # type: ignore


class TransactionProcessor:
    """gérer les étapes de transformation et d'analyse des données après le nettoyage initial."""

    """Initialise le processeur de transactions avec un DataFrame propre."""
    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df.copy()
        self.logger = logging.getLogger(self.__class__.__name__)


    """ creation du montant total par ligne pour servir de base pour les analyses suivantes."""
    def calculate_total_amount(self) -> pd.DataFrame:
        self.df["TotalAmount"] = self.df["Quantity"] * self.df["UnitPrice"]
        self.logger.info("Colonne TotalAmount calculée.")
        return self.df
    

    """ calcul du total des ventes par pays, en groupant par la colonne Country et en sommant les montants totaux."""
    def group_by_country(self) -> pd.DataFrame:
        country_sales = (
            self.df.groupby("Country", as_index=False)["TotalAmount"]
            .sum()
            .sort_values(by="TotalAmount", ascending=False)
        )
        self.logger.info("Ventes groupées par pays.")
        return country_sales
    

    """ calcul des statistiques de ventes mensuelles """
    def aggregate_monthly_data(self) -> pd.DataFrame:
        monthly_df = self.df.copy()
        monthly_df["InvoiceMonth"] = monthly_df["InvoiceDate"].dt.to_period("M").astype(str)
        monthly_stats = (
            monthly_df.groupby("InvoiceMonth", as_index=False)
            .agg(
                TotalSales = ("TotalAmount", "sum"),
                TransactionCount = ("InvoiceNo", "nunique"),
            )
            .sort_values(by="InvoiceMonth")
        )
        self.logger.info("Statistiques de ventes mensuelles calculées.")
        return monthly_stats
    
    """ calcul des deux analyse statistiques demandées : le produit qui rapporte le plus en France et l'heure ou le nombre de transaction est le plus élevé."""
    def calcul_stat_data(self) -> dict:

        """ le produit qui rapporte le plus en France """
        france_sales = self.df[self.df["Country"].str.lower() == "france"].copy()
        best_product_france: Optional[str] = None
        if not france_sales.empty:
            best_product_france = (
                france_sales.groupby("Description", as_index=False)["TotalAmount"]
                .sum()
                .sort_values(by="TotalAmount", ascending=False)
                .iloc[0]["Description"]
            )


        """ l'heure ou le nombre de transaction est le plus élevé """
        hour_df = self.df.copy()
        hour_df["InvoiceHour"] = hour_df["InvoiceDate"].dt.hour
        transaction_by_hour = (
            hour_df.groupby("InvoiceHour", as_index=False)["InvoiceNo"]
            .nunique()
            .sort_values(by="InvoiceNo", ascending=False)
        )
        peak_hour = None
        if not transaction_by_hour.empty:
            peak_hour = transaction_by_hour.iloc[0]["InvoiceHour"]

        self.logger.info("Statistiques de ventes calculées.")
        return {
            "best_product_france": best_product_france,
            "transaction_peak_hour": transaction_by_hour,
            "peak_hour": peak_hour,
        }
    

    """ calcul du classement global des fournisseurs selon le total des ventes de leurs produits"""
    def aggregate_supplier_data(self, supplier_df: pd.DataFrame) -> pd.DataFrame:
        merged_df = self.df.copy()
        merged_df["InvoiceNo"] = merged_df["InvoiceNo"].astype(str)
        supplier_df = supplier_df.copy()
        supplier_df["InvoiceNo"] = supplier_df["InvoiceNo"].astype(str)
        supplier_df = supplier_df.rename(columns = {"Fournisseur": "SupplierID"})

        merged_df = merged_df.merge(supplier_df, on="InvoiceNo", how="left")

        supplier_sales = (
            merged_df.groupby("SupplierID", as_index=False)["TotalAmount"]
            .sum()
            .sort_values(by="TotalAmount", ascending=False)
        )
        self.logger.info("Ventes groupées par fournisseur.")
        return supplier_sales
    
    
    """ calcul du classement des fournisseurs uniquement pour le Royaume-uni en 2011 """
    def aggregate_supplier_uk_2011(self, supplier_df: pd.DataFrame) -> pd.DataFrame:
        filtered_df = self.df.copy()
        filtered_df = filtered_df[
            (filtered_df["Country"] == "United Kingdom") 
            & (filtered_df["InvoiceDate"].dt.year == 2011)
            ]
        filtered_df["InvoiceNo"] = filtered_df["InvoiceNo"].astype(str)
        supplier_df = supplier_df.copy()
        supplier_df["InvoiceNo"] = supplier_df["InvoiceNo"].astype(str)
        supplier_df = supplier_df.rename(columns = {"Fournisseur": "SupplierID"})   

        filtered_df = filtered_df.merge(supplier_df, on="InvoiceNo", how="left")

        supplier_sales_uk_2011 = (
            filtered_df.groupby("SupplierID", as_index=False)["TotalAmount"]
            .sum()
            .sort_values(by="TotalAmount", ascending=False)
        )
        self.logger.info("Ventes groupées par fournisseur pour le Royaume-Uni en 2011.")
        return supplier_sales_uk_2011
    

    """ analyser a l'échelle mondiale : classer les continents selon les dépenses et trouver le continent qui a le plus d'opération annulées"""
    def aggregate_world_data(
            self,
            mapping_df: pd.DataFrame,
            raw_df: Optional[pd.DataFrame] = None,
            ) -> dict:
        world_df = self.df.copy()
        mapping_df = mapping_df.copy()
        mapping_df.columns = [column.strip() for column in mapping_df.columns]

        rename_map = {}
        if "country" in {c.lower() for c in mapping_df.columns}:
            source = next(c for c in mapping_df.columns if c.lower() == "country")
            rename_map[source] = "Country"
        if "continent" in {c.lower() for c in mapping_df.columns}:
            source = next(c for c in mapping_df.columns if c.lower() == "continent")
            rename_map[source] = "Continent"
        mapping_df = mapping_df.rename(columns=rename_map)

        world_df = world_df.merge(mapping_df[["Country", "Continent"]], on="Country", how="left")
        continent_sales = (
            world_df.groupby("Continent", as_index=False)["TotalAmount"]
            .sum()
            .sort_values(by="TotalAmount", ascending=False)
        )

        cancellations_by_continent = None
        top_cancelled_continent = None
        if raw_df is not None:
            cancellations_df = raw_df.copy()
            cancellations_df["InvoiceNo"] = cancellations_df["InvoiceNo"].astype(str)
            cancellations_df["Country"] = cancellations_df["Country"].astype(str).str.strip()
            cancellations_df = cancellations_df[cancellations_df["InvoiceNo"].str.startswith("C", na=False)]
            cancellations_df = cancellations_df.merge(
                mapping_df[["Country", "Continent"]],
                on = "Country",
                how = "left"
            )
            cancellations_by_continent = (
                cancellations_df.groupby("Continent", as_index=False)["InvoiceNo"]
                .nunique()
                .rename(columns={"InvoiceNo": "CancelledOperations"})
                .sort_values(by="CancelledOperations", ascending=False)
            )
            if not cancellations_by_continent.empty:
                top_cancelled_continent = cancellations_by_continent.iloc[0]["Continent"]

        self.logger.info("Agrégations monde calculées.")
        return {
            "continent_sales": continent_sales,
            "cancellations_by_continent": cancellations_by_continent,
            "top_cancelled_continent": top_cancelled_continent,
            "world_df": world_df,
        }
