import sys
from pathlib import Path

import pandas as pd  # type: ignore

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from Classe_TransactionProcessor import TransactionProcessor


def test_calculate_total_amount_adds_expected_column() -> None:
    df = pd.DataFrame(
        {
            "Quantity": [2, 3, 1],
            "UnitPrice": [10.0, 4.5, 7.25],
        }
    )

    processor = TransactionProcessor(df)
    result = processor.calculate_total_amount()

    assert "TotalAmount" in result.columns
    assert result["TotalAmount"].tolist() == [20.0, 13.5, 7.25]
