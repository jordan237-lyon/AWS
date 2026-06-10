import sys
from pathlib import Path

import pandas as pd  # type: ignore
import pytest

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from Classe_ETLPipeline import ETLPipeline


def test_save_as_parquet_raises_error_when_dataframe_is_empty(tmp_path: Path) -> None:
    pipeline = ETLPipeline(
        retail_path=str(tmp_path / "retail.xlsx"),
        supplier_path=str(tmp_path / "supplier.csv"),
    )

    with pytest.raises(ValueError, match="DataFrame final est vide"):
        pipeline.save_as_parquet(str(tmp_path / "output.parquet"))
