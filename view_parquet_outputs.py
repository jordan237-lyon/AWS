from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd  # type: ignore


def describe_parquet_file(file_path: Path, preview_rows: int, export_csv: bool, export_dir: Path) -> None:
    df = pd.read_parquet(file_path)

    print("=" * 100)
    print(f"FILE: {file_path.name}")
    print(f"ROWS: {len(df)}")
    print(f"COLUMNS: {len(df.columns)}")
    print("COLUMN NAMES:")
    for column in df.columns.tolist():
        print(f"  - {column}")

    print("DTYPES:")
    for column_name, dtype in df.dtypes.items():
        print(f"  - {column_name}: {dtype}")

    print(f"PREVIEW ({min(preview_rows, len(df))} rows):")
    if df.empty:
        print("  DataFrame vide.")
    else:
        print(df.head(preview_rows).to_string(index=False))

    if export_csv:
        export_dir.mkdir(parents=True, exist_ok=True)
        csv_path = export_dir / f"{file_path.stem}_preview.csv"
        df.head(preview_rows).to_csv(csv_path, index=False)
        print(f"CSV preview exported to: {csv_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspecte les sorties Parquet du dossier output et affiche un apercu lisible."
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Dossier contenant les fichiers ou sous-dossiers Parquet.",
    )
    parser.add_argument(
        "--preview-rows",
        type=int,
        default=10,
        help="Nombre de lignes a afficher pour chaque sortie.",
    )
    parser.add_argument(
        "--export-csv",
        action="store_true",
        help="Exporte aussi un CSV d'apercu pour chaque sortie.",
    )
    parser.add_argument(
        "--export-dir",
        default="output_previews",
        help="Dossier de destination des CSV d'apercu.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    if not output_dir.exists():
        raise FileNotFoundError(f"Dossier introuvable: {output_dir}")

    parquet_files = sorted(output_dir.rglob("*.parquet"))
    if not parquet_files:
        print(f"Aucun fichier .parquet trouve dans {output_dir}")
        return

    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 240)

    export_dir = Path(args.export_dir)
    for parquet_file in parquet_files:
        describe_parquet_file(
            parquet_file,
            preview_rows=args.preview_rows,
            export_csv=args.export_csv,
            export_dir=export_dir,
        )


if __name__ == "__main__":
    main()