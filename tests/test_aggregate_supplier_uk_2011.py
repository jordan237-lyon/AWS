import sys
from pathlib import Path

import pandas as pd  # type: ignore

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from Classe_TransactionProcessor import TransactionProcessor


def test_aggregate_supplier_uk_2011_filters_merges_and_sums() -> None:
    df = pd.DataFrame(
        {
            "InvoiceNo": ["1001", "1002", "1003", "1004"],
            "Country": ["United Kingdom", "France", "United Kingdom", "United Kingdom"],
            "InvoiceDate": pd.to_datetime(
                [
                    "2011-01-10 08:00:00",
                    "2011-01-10 08:00:00",
                    "2010-12-20 09:00:00",
                    "2011-06-01 12:00:00",
                ]
            ),
            "TotalAmount": [100.0, 200.0, 300.0, 50.0],
        }
    )

    supplier_df = pd.DataFrame(
        {
            "InvoiceNo": ["1001", "1002", "1003", "1004"],
            "Fournisseur": ["F100", "F200", "F300", "F100"],
        }
    )

    processor = TransactionProcessor(df)
    result = processor.aggregate_supplier_uk_2011(supplier_df)

    assert result["SupplierID"].tolist() == ["F100"]
    assert result["TotalAmount"].tolist() == [150.0]
