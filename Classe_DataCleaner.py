import logging
import pandas as pd  # type: ignore

class DataCleaner:
    """Gère toutes les étapes de nettoyage et de préparation des données brutes."""

    # stockage d'une copie du DataFrame dans l'objet initialisé
    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df.copy()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    # supression des doublons
    def remove_duplicates(self) -> pd.DataFrame:
        before_count = len(self.df)
        self.df = self.df.drop_duplicates()
        after_count = len(self.df)
        self.logger.info(f"Doublons supprimés : {before_count - after_count}")
        return self.df
    
    # traitement des valeurs manquantes
    def handle_missing_values(self) -> pd.DataFrame:
        critical_columns = ["Description", "Quantity", "UnitPrice", "Country", "InvoiceDate"]
        self.df = self.df.dropna(subset=critical_columns)

        self.df = self.df[(self.df["UnitPrice"] > 0) & (self.df["Quantity"] != 0)]

        if "CustomerID" in self.df.columns: 
            self.df["CustomerID"] = self.df["CustomerID"].fillna(-1).astype("int64")

        self.logger.info("Valeurs manquantes tra'té.")
        return self.df
    
    # ici on garde uniquement les transactions valides, c'est à dire celles qui ont un InvoiceNo qui ne commence pas par 'C' (indiquant une annulation)
    def filter_valid_transactions(self) -> pd.DataFrame:
        
        self.df["InvoiceNo"] = self.df["InvoiceNo"].astype(str)

        self.df = self.df[~self.df["InvoiceNo"].str.startswith("C", na=False)]
        self.logger.info("Transactions valides filtrées/Transactions annulées exclues/valeur manquantes remplacées.")
        return self.df
    
    # harmonisation des formats de données
    def normalize_types(self) -> pd.DataFrame:
        self.df["InvoiceDate"] = pd.to_datetime(self.df["InvoiceDate"], errors="coerce")
        self.df["StockCode"] = self.df["StockCode"].astype(str)
        self.df["Country"] = self.df["Country"].astype(str).str.strip()
        self.df["Description"] = self.df["Description"].astype(str).str.strip()
        self.df = self.df.dropna(subset=["InvoiceDate"])
        self.logger.info("Formats de données harmonisés.")
        return self.df
    
    # lancement de toutes les étapes de nettoyage dans l'ordre logique
    def clean(self) -> pd.DataFrame:
        self.remove_duplicates()
        self.handle_missing_values()
        self.filter_valid_transactions()
        self.normalize_types()
        self.logger.info("Nettoyage des données terminé.")
        return self.df.reset_index(drop=True)
