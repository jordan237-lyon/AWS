from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
from pathlib import Path
import re

import pandas as pd  # type: ignore


RUN_ID_PATTERN = re.compile(
    r"^part-\d{5}-(?P<run_id>[0-9a-f-]+)-c\d+\.snappy\.parquet$",
    re.IGNORECASE,
)


@dataclass
class ParquetGroup:
    run_id: str
    files: list[Path]
    columns: tuple[str, ...]
    total_rows: int
    latest_mtime: float


def extract_run_id(file_path: Path) -> str:
    match = RUN_ID_PATTERN.match(file_path.name)
    if match:
        return match.group("run_id")
    return file_path.stem


def classify_columns(columns: tuple[str, ...]) -> str:
    schema_map = {
        (
            "InvoiceNo",
            "StockCode",
            "Description",
            "Quantity",
            "InvoiceDate",
            "UnitPrice",
            "CustomerID",
            "Country",
        ): "cleaned",
        (
            "InvoiceNo",
            "StockCode",
            "Description",
            "Quantity",
            "InvoiceDate",
            "UnitPrice",
            "CustomerID",
            "Country",
            "TotalAmount",
        ): "enriched",
        ("Country", "TotalAmount", "TransactionCount"): "country_sales",
        ("InvoiceMonth", "TotalSales", "TransactionCount"): "monthly_sales",
        ("Continent", "TotalAmount"): "continent_sales",
        ("Continent", "CancelledOperations"): "cancellations_by_continent",
        ("SupplierID", "TotalAmount"): "supplier_sales_family",
    }
    return schema_map.get(columns, "unknown")


def build_groups(output_dir: Path) -> list[ParquetGroup]:
    grouped_files: dict[str, list[Path]] = {}
    for parquet_file in sorted(output_dir.glob("*.parquet")):
        run_id = extract_run_id(parquet_file)
        grouped_files.setdefault(run_id, []).append(parquet_file)

    groups: list[ParquetGroup] = []
    for run_id, files in grouped_files.items():
        first_df = pd.read_parquet(files[0])
        columns = tuple(first_df.columns.tolist())
        total_rows = len(first_df)
        latest_mtime = files[0].stat().st_mtime

        for extra_file in files[1:]:
            extra_df = pd.read_parquet(extra_file)
            if tuple(extra_df.columns.tolist()) != columns:
                raise ValueError(
                    f"Le lot {run_id} contient des schemas differents: {files[0].name} et {extra_file.name}"
                )
            total_rows += len(extra_df)
            latest_mtime = max(latest_mtime, extra_file.stat().st_mtime)

        groups.append(
            ParquetGroup(
                run_id=run_id,
                files=files,
                columns=columns,
                total_rows=total_rows,
                latest_mtime=latest_mtime,
            )
        )

    return groups


def resolve_destinations(groups: list[ParquetGroup]) -> dict[str, str]:
    destinations: dict[str, str] = {}
    supplier_groups = [
        group for group in groups if classify_columns(group.columns) == "supplier_sales_family"
    ]

    for group in groups:
        base_classification = classify_columns(group.columns)
        if group.total_rows == 0:
            destinations[group.run_id] = "legacy_empty"
        elif base_classification == "supplier_sales_family":
            continue
        elif base_classification == "unknown":
            destinations[group.run_id] = "unknown_schema"
        else:
            destinations[group.run_id] = base_classification

    supplier_groups.sort(key=lambda group: (-group.total_rows, -group.latest_mtime))
    if supplier_groups:
        destinations[supplier_groups[0].run_id] = "supplier_sales"
    if len(supplier_groups) > 1:
        destinations[supplier_groups[1].run_id] = "supplier_sales_uk_2011"
    for group in supplier_groups[2:]:
        destinations[group.run_id] = "legacy_supplier_extra"

    return destinations


def move_group(group: ParquetGroup, destination_dir: Path) -> None:
    destination_dir.mkdir(parents=True, exist_ok=True)
    for parquet_file in group.files:
        shutil.move(str(parquet_file), str(destination_dir / parquet_file.name))


def print_plan(groups: list[ParquetGroup], destinations: dict[str, str], output_dir: Path) -> None:
    print("=" * 100)
    print(f"PLAN DE RANGEMENT POUR: {output_dir}")
    for group in sorted(groups, key=lambda item: item.latest_mtime):
        destination_name = destinations[group.run_id]
        print("-" * 100)
        print(f"RUN ID: {group.run_id}")
        print(f"FILES: {len(group.files)}")
        print(f"ROWS: {group.total_rows}")
        print(f"COLUMNS: {', '.join(group.columns)}")
        print(f"DESTINATION: {destination_name}")
        for parquet_file in group.files:
            print(f"  - {parquet_file.name}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Range les sorties Parquet du projet par type de dataset et isole les anciens fichiers vides."
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Dossier contenant les fichiers Parquet a organiser.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Applique reellement le rangement. Sans cette option, le script reste en mode apercu.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    if not output_dir.exists():
        raise FileNotFoundError(f"Dossier introuvable: {output_dir}")

    groups = build_groups(output_dir)
    if not groups:
        print(f"Aucun fichier .parquet trouve dans {output_dir}")
        return

    destinations = resolve_destinations(groups)
    print_plan(groups, destinations, output_dir)

    if not args.apply:
        print("=" * 100)
        print("Mode apercu uniquement. Relance avec --apply pour deplacer les fichiers.")
        return

    for group in groups:
        destination_name = destinations[group.run_id]
        destination_dir = output_dir / destination_name
        move_group(group, destination_dir)

    print("=" * 100)
    print("Rangement termine.")


if __name__ == "__main__":
    main()