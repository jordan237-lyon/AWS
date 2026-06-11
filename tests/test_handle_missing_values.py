import sys
from pathlib import Path

import pandas as pd  # type: ignore

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from Classe_DataCleaner import DataCleaner


def test_handle_missing_values_drops_invalid_rows_and_fills_customer_id() -> None:
    df = pd.DataFrame(
        {
            "Description": ["Lamp", None, "Chair", "Table"],
            "Quantity": [2, 1, 0, 4],
            "UnitPrice": [10.0, 5.0, 8.0, 12.0],
            "Country": ["France", "France", "Germany", "Spain"],
            "InvoiceDate": [
                "2011-01-10 08:00:00",
                "2011-01-11 09:00:00",
                "2011-01-12 10:00:00",
                "2011-01-13 11:00:00",
            ],
            "CustomerID": [12345, None, 22222, None],
        }
    )

    cleaner = DataCleaner(df)
    result = cleaner.handle_missing_values()

    assert len(result) == 2
    assert result["Description"].tolist() == ["Lamp", "Table"]
    assert result["CustomerID"].tolist() == [12345, -1]
