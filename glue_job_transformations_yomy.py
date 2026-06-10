from __future__ import annotations

from dataclasses import dataclass
import sys
from urllib.parse import urlparse

from awsglue.context import GlueContext  # type: ignore
from awsglue.job import Job  # type: ignore
from awsglue.utils import getResolvedOptions  # type: ignore
from pyspark.context import SparkContext  # type: ignore
from pyspark.sql import DataFrame, SparkSession  # type: ignore
from pyspark.sql import functions as F  # type: ignore


@dataclass
class TransformationJobConfig:
    job_name: str
    cleaned_input_path: str
    enriched_output_path: str

    @classmethod
    def from_args(cls) -> "TransformationJobConfig":
        args = getResolvedOptions(
            sys.argv,
            [
                "JOB_NAME",
                "cleaned_input_path",
                "enriched_output_path",
            ],
        )
        return cls(
            job_name=args["JOB_NAME"],
            cleaned_input_path=args["cleaned_input_path"],
            enriched_output_path=args["enriched_output_path"],
        )


class TransactionProcessor:
    """Job Glue 2: enrichissement du dataset nettoye."""

    def __init__(self, df: DataFrame) -> None:
        self.df = df

    def calculate_total_amount(self) -> DataFrame:
        self.df = self.df.withColumn(
            "TotalAmount",
            F.round(F.col("Quantity") * F.col("UnitPrice"), 2),
        )
        return self.df


def build_debug_output_path(enriched_output_path: str) -> str:
    parsed = urlparse(enriched_output_path)
    enriched_path = parsed.path.rstrip("/")
    if enriched_path.endswith("/enriched"):
        debug_path = enriched_path[: -len("/enriched")] + "/debug_counts_transformations_job"
    else:
        debug_path = enriched_path + "_debug_transformations_job"
    return f"s3://{parsed.netloc}{debug_path}/"


def main() -> None:
    config = TransformationJobConfig.from_args()

    sc = SparkContext.getOrCreate()
    glue_context = GlueContext(sc)
    spark = glue_context.spark_session
    job = Job(glue_context)
    job.init(config.job_name, vars(config))

    cleaned_df = spark.read.parquet(config.cleaned_input_path)
    print(f"[TransformationsJob] cleaned input rows: {cleaned_df.count()}")
    enriched_df = TransactionProcessor(cleaned_df).calculate_total_amount()
    print(f"[TransformationsJob] enriched output rows: {enriched_df.count()}")
    debug_counts = [
        ("cleaned_input", cleaned_df.count()),
        ("enriched_output", enriched_df.count()),
    ]
    debug_output_path = build_debug_output_path(config.enriched_output_path)
    print(f"[TransformationsJob] writing debug counts to: {debug_output_path}")
    spark.createDataFrame(debug_counts, ["step", "row_count"]).write.mode("overwrite").json(debug_output_path)
    enriched_df.write.mode("overwrite").parquet(config.enriched_output_path)

    job.commit()


if __name__ == "__main__":
    main()