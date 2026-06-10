import sys
from pathlib import Path

import pandas as pd  # type: ignore

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from Classe_DataCleaner import DataCleaner


def test_filter_valid_transactions_excludes_cancelled_invoice_numbers() -> None:
    df = pd.DataFrame(
        {
            "InvoiceNo": ["1001", "C1002", "c1003", "1004"],
            "StockCode": ["A", "B", "C", "D"],
            "Description": ["Lamp", "Mug", "Tray", "Chair"],
            "Quantity": [1, 2, 3, 4],
            "InvoiceDate": ["2011-01-10", "2011-01-11", "2011-01-12", "2011-01-13"],
            "UnitPrice": [10.0, 5.0, 7.0, 12.0],
            "Country": ["France", "France", "Spain", "Germany"],
        }
    )

    cleaner = DataCleaner(df)
    cleaner.normalize_types()
    result = cleaner.filter_valid_transactions()

    assert result["InvoiceNo"].tolist() == ["1001", "1004"]