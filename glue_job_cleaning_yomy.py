from __future__ import annotations

from dataclasses import dataclass
import sys
from urllib.parse import urlparse

from awsglue.context import GlueContext  # type: ignore
from awsglue.job import Job  # type: ignore
from awsglue.utils import getResolvedOptions  # type: ignore
from pyspark.context import SparkContext  # type: ignore
from pyspark.sql import DataFrame  # type: ignore
from pyspark.sql import functions as F  # type: ignore


@dataclass
class CleaningJobConfig:
    job_name: str
    catalog_database: str
    retail_table: str
    cleaned_output_path: str

    @classmethod
    def from_args(cls) -> "CleaningJobConfig":
        args = getResolvedOptions(
            sys.argv,
            [
                "JOB_NAME",
                "catalog_database",
                "retail_table",
                "cleaned_output_path",
            ],
        )
        return cls(
            job_name=args["JOB_NAME"],
            catalog_database=args["catalog_database"],
            retail_table=args["retail_table"],
            cleaned_output_path=args["cleaned_output_path"],
        )


class DataCleaner:
    """Job Glue 1: nettoyage et standardisation du dataset retail."""

    def __init__(
        self,
        df: DataFrame,
        quantity_bounds: tuple[int, int] = (1, 10_000),
        unit_price_bounds: tuple[float, float] = (0.01, 10_000.0),
    ) -> None:
        self.df = df
        self.quantity_bounds = quantity_bounds
        self.unit_price_bounds = unit_price_bounds
        self.debug_counts: list[tuple[str, int]] = []

    def log_row_count(self, label: str) -> None:
        row_count = self.df.count()
        self.debug_counts.append((label, row_count))
        print(f"[DataCleaner] {label}: {row_count} rows")

    def get_debug_counts(self) -> list[tuple[str, int]]:
        return self.debug_counts

    def normalize_types(self) -> DataFrame:
        self.df = (
            self.df.withColumn("InvoiceNo", F.trim(F.col("InvoiceNo").cast("string")))
            .withColumn("StockCode", F.trim(F.col("StockCode").cast("string")))
            .withColumn("Description", F.trim(F.col("Description").cast("string")))
            .withColumn("Country", F.trim(F.col("Country").cast("string")))
            .withColumn(
                "Quantity",
                F.regexp_replace(F.col("Quantity").cast("string"), ",", ".").cast("double").cast("int"),
            )
            .withColumn(
                "UnitPrice",
                F.regexp_replace(F.col("UnitPrice").cast("string"), ",", ".").cast("double"),
            )
            .withColumn("CustomerID", F.col("CustomerID").cast("long"))
            .withColumn(
                "InvoiceDate",
                F.coalesce(
                    F.to_timestamp(F.col("InvoiceDate"), "M/d/yyyy H:mm"),
                    F.to_timestamp(F.col("InvoiceDate"), "MM/dd/yyyy HH:mm"),
                    F.to_timestamp(F.col("InvoiceDate"), "M/d/yyyy H:mm:ss"),
                    F.to_timestamp(F.col("InvoiceDate")),
                ),
            )
        )
        self.log_row_count("after normalize_types")
        return self.df

    def remove_duplicates(self) -> DataFrame:
        self.df = self.df.dropDuplicates()
        self.log_row_count("after remove_duplicates")
        return self.df

    def handle_missing_values(self) -> DataFrame:
        critical_columns = ["Description", "Quantity", "UnitPrice", "Country", "InvoiceDate"]
        for column_name in critical_columns:
            missing_count = self.df.filter(F.col(column_name).isNull()).count()
            self.debug_counts.append((f"missing_{column_name}", missing_count))
            print(f"[DataCleaner] missing_{column_name}: {missing_count} rows")

        self.df = self.df.dropna(
            subset=critical_columns
        )
        self.df = self.df.filter(
            (F.col("Description") != "") & (F.col("Country") != "")
        ).fillna({"CustomerID": -1})
        self.log_row_count("after handle_missing_values")
        return self.df

    def filter_valid_transactions(self) -> DataFrame:
        self.df = self.df.filter(~F.upper(F.col("InvoiceNo")).startswith("C"))
        self.log_row_count("after filter_valid_transactions")
        return self.df

    def filter_outliers(self) -> DataFrame:
        min_quantity, max_quantity = self.quantity_bounds
        min_unit_price, max_unit_price = self.unit_price_bounds
        self.df = self.df.filter(
            F.col("Quantity").between(min_quantity, max_quantity)
            & F.col("UnitPrice").between(min_unit_price, max_unit_price)
        )
        self.log_row_count("after filter_outliers")
        return self.df

    def clean(self) -> DataFrame:
        self.log_row_count("initial dataset")
        self.normalize_types()
        self.remove_duplicates()
        self.handle_missing_values()
        self.filter_valid_transactions()
        self.filter_outliers()
        return self.df


def build_debug_output_path(cleaned_output_path: str) -> str:
    parsed = urlparse(cleaned_output_path)
    cleaned_path = parsed.path.rstrip("/")
    if cleaned_path.endswith("/cleaned"):
        debug_path = cleaned_path[: -len("/cleaned")] + "/debug_counts_cleaning_job"
    else:
        debug_path = cleaned_path + "_debug_cleaning_job"
    return f"s3://{parsed.netloc}{debug_path}/"


def main() -> None:
    config = CleaningJobConfig.from_args()

    sc = SparkContext.getOrCreate()
    glue_context = GlueContext(sc)
    job = Job(glue_context)
    job.init(config.job_name, vars(config))

    retail_df = glue_context.create_dynamic_frame.from_catalog(
        database=config.catalog_database,
        table_name=config.retail_table,
    ).toDF()

    print(f"[CleaningJob] raw retail rows: {retail_df.count()}")

    cleaner = DataCleaner(retail_df)
    cleaned_df = cleaner.clean()
    print(f"[CleaningJob] final cleaned rows: {cleaned_df.count()}")
    debug_counts = [
        ("raw_retail", retail_df.count()),
        *cleaner.get_debug_counts(),
        ("cleaned", cleaned_df.count()),
    ]
    debug_output_path = build_debug_output_path(config.cleaned_output_path)
    print(f"[CleaningJob] writing debug counts to: {debug_output_path}")
    glue_context.spark_session.createDataFrame(debug_counts, ["step", "row_count"]).write.mode("overwrite").json(
        debug_output_path
    )
    cleaned_df.write.mode("overwrite").parquet(config.cleaned_output_path)

    job.commit()


if __name__ == "__main__":
    main()