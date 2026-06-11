import sys
from pathlib import Path

import pandas as pd  # type: ignore

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from Classe_TransactionProcessor import TransactionProcessor


def test_group_by_country_sums_and_sorts_sales() -> None:
    df = pd.DataFrame(
        {
            "Country": ["France", "Germany", "France", "Germany", "Spain"],
            "TotalAmount": [10.0, 15.0, 20.0, 5.0, 8.0],
        }
    )

    processor = TransactionProcessor(df)
    result = processor.group_by_country()

    assert result["Country"].tolist() == ["France", "Germany", "Spain"]
    assert result["TotalAmount"].tolist() == [30.0, 20.0, 8.0]
