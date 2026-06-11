import sys
from pathlib import Path

import pandas as pd  # type: ignore

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from Classe_DataCleaner import DataCleaner


def test_remove_duplicates_removes_exact_duplicate_rows() -> None:
    df = pd.DataFrame(
        {
            "InvoiceNo": ["1001", "1001", "1002"],
            "Description": ["Lamp", "Lamp", "Mug"],
            "Quantity": [2, 2, 1],
        }
    )

    cleaner = DataCleaner(df)
    result = cleaner.remove_duplicates()

    assert len(result) == 2
    assert result["InvoiceNo"].tolist() == ["1001", "1002"]
