import sys
from pathlib import Path

import pandas as pd  # type: ignore

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from Classe_ETLPipeline import ETLPipeline


def test_load_data_reads_excel_csv_and_mapping(tmp_path: Path) -> None:
    retail_df = pd.DataFrame(
        {
            "InvoiceNo": ["1001"],
            "StockCode": ["A1"],
            "Description": ["Lamp"],
            "Quantity": [2],
            "InvoiceDate": ["2011-01-10 08:00:00"],
            "UnitPrice": [10.0],
            "CustomerID": [12345],
            "Country": ["France"],
        }
    )
    supplier_df = pd.DataFrame({"InvoiceNo": ["1001"], "Fournisseur": ["F100"]})
    mapping_df = pd.DataFrame({"Country": ["France"], "Continent": ["Europe"]})

    retail_path = tmp_path / "retail.xlsx"
    supplier_path = tmp_path / "supplier.csv"
    mapping_path = tmp_path / "mapping.csv"

    retail_df.to_excel(retail_path, index=False)
    supplier_df.to_csv(supplier_path, index=False)
    mapping_df.to_csv(mapping_path, index=False)

    pipeline = ETLPipeline(str(retail_path), str(supplier_path), str(mapping_path))
    loaded_retail_df, loaded_supplier_df, loaded_mapping_df = pipeline.load_data()

    assert loaded_retail_df.shape == (1, 8)
    assert loaded_supplier_df["Fournisseur"].tolist() == ["F100"]
    assert loaded_mapping_df is not None
    assert loaded_mapping_df["Continent"].tolist() == ["Europe"]
