import sys
from pathlib import Path

import pandas as pd  # type: ignore

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from Classe_TransactionProcessor import TransactionProcessor


def test_aggregate_monthly_data_computes_sales_and_unique_transactions() -> None:
    df = pd.DataFrame(
        {
            "InvoiceDate": pd.to_datetime(
                [
                    "2011-01-10 08:00:00",
                    "2011-01-10 08:05:00",
                    "2011-02-03 09:30:00",
                    "2011-02-20 16:10:00",
                ]
            ),
            "InvoiceNo": ["1001", "1001", "1002", "1003"],
            "TotalAmount": [10.0, 5.0, 20.0, 15.0],
        }
    )

    processor = TransactionProcessor(df)
    result = processor.aggregate_monthly_data()

    assert result["InvoiceMonth"].tolist() == ["2011-01", "2011-02"]
    assert result["TotalSales"].tolist() == [15.0, 35.0]
    assert result["TransactionCount"].tolist() == [1, 2]
