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
class AggregationJobConfig:
    job_name: str
    catalog_database: str
    retail_table: str
    supplier_table: str
    mapping_table: str
    enriched_input_path: str
    country_output_path: str
    monthly_output_path: str
    supplier_output_path: str
    supplier_uk_output_path: str
    world_output_path: str
    cancellation_output_path: str

    @classmethod
    def from_args(cls) -> "AggregationJobConfig":
        args = getResolvedOptions(
            sys.argv,
            [
                "JOB_NAME",
                "catalog_database",
                "retail_table",
                "supplier_table",
                "mapping_table",
                "enriched_input_path",
                "country_output_path",
                "monthly_output_path",
                "supplier_output_path",
                "supplier_uk_output_path",
                "world_output_path",
                "cancellation_output_path",
            ],
        )
        return cls(
            job_name=args["JOB_NAME"],
            catalog_database=args["catalog_database"],
            retail_table=args["retail_table"],
            supplier_table=args["supplier_table"],
            mapping_table=args["mapping_table"],
            enriched_input_path=args["enriched_input_path"],
            country_output_path=args["country_output_path"],
            monthly_output_path=args["monthly_output_path"],
            supplier_output_path=args["supplier_output_path"],
            supplier_uk_output_path=args["supplier_uk_output_path"],
            world_output_path=args["world_output_path"],
            cancellation_output_path=args["cancellation_output_path"],
        )


class AggregationProcessor:
    """Job Glue 3: aggregations et sorties analytiques."""

    def __init__(self, df: DataFrame) -> None:
        self.df = df

    def group_by_country(self) -> DataFrame:
        return (
            self.df.groupBy("Country")
            .agg(
                F.round(F.sum("TotalAmount"), 2).alias("TotalAmount"),
                F.countDistinct("InvoiceNo").alias("TransactionCount"),
            )
            .orderBy(F.desc("TotalAmount"), F.desc("TransactionCount"))
        )

    def aggregate_monthly_data(self) -> DataFrame:
        return (
            self.df.withColumn("InvoiceMonth", F.date_format("InvoiceDate", "yyyy-MM"))
            .groupBy("InvoiceMonth")
            .agg(
                F.round(F.sum("TotalAmount"), 2).alias("TotalSales"),
                F.countDistinct("InvoiceNo").alias("TransactionCount"),
            )
            .orderBy("InvoiceMonth")
        )

    def aggregate_supplier_data(self, supplier_df: DataFrame) -> DataFrame:
        supplier_df = supplier_df.withColumn(
            "InvoiceNo", F.col("InvoiceNo").cast("string")
        ).withColumnRenamed("Fournisseur", "SupplierID")
        return (
            self.df.withColumn("InvoiceNo", F.col("InvoiceNo").cast("string"))
            .join(supplier_df, on="InvoiceNo", how="left")
            .groupBy("SupplierID")
            .agg(F.round(F.sum("TotalAmount"), 2).alias("TotalAmount"))
            .orderBy(F.desc("TotalAmount"))
        )

    def aggregate_supplier_uk_2011(self, supplier_df: DataFrame) -> DataFrame:
        supplier_df = supplier_df.withColumn(
            "InvoiceNo", F.col("InvoiceNo").cast("string")
        ).withColumnRenamed("Fournisseur", "SupplierID")
        filtered_df = self.df.filter(
            (F.col("Country") == "United Kingdom") & (F.year("InvoiceDate") == 2011)
        )
        return (
            filtered_df.withColumn("InvoiceNo", F.col("InvoiceNo").cast("string"))
            .join(supplier_df, on="InvoiceNo", how="left")
            .groupBy("SupplierID")
            .agg(F.round(F.sum("TotalAmount"), 2).alias("TotalAmount"))
            .orderBy(F.desc("TotalAmount"))
        )

    def aggregate_world_data(self, mapping_df: DataFrame) -> DataFrame:
        normalized_mapping_df = (
            mapping_df.withColumnRenamed("country", "Country")
            if "country" in mapping_df.columns
            else mapping_df
        )
        normalized_mapping_df = (
            normalized_mapping_df.withColumnRenamed("continent", "Continent")
            if "continent" in normalized_mapping_df.columns
            else normalized_mapping_df
        )
        return (
            self.df.join(
                normalized_mapping_df.select("Country", "Continent"),
                on="Country",
                how="left",
            )
            .groupBy("Continent")
            .agg(F.round(F.sum("TotalAmount"), 2).alias("TotalAmount"))
            .orderBy(F.desc("TotalAmount"))
        )


class ETLPipeline:
    """Orchestre le troisieme job Glue."""

    def __init__(self, glue_context: GlueContext, spark: SparkSession, config: AggregationJobConfig) -> None:
        self.glue_context = glue_context
        self.spark = spark
        self.config = config

    def load_catalog_table(self, table_name: str) -> DataFrame:
        return self.glue_context.create_dynamic_frame.from_catalog(
            database=self.config.catalog_database,
            table_name=table_name,
        ).toDF()

    def load_enriched_data(self) -> DataFrame:
        return self.spark.read.parquet(self.config.enriched_input_path)

    def save_parquet(self, df: DataFrame, path: str) -> None:
        df.write.mode("overwrite").parquet(path)

    def build_debug_output_path(self) -> str:
        parsed = urlparse(self.config.country_output_path)
        country_path = parsed.path.rstrip("/")
        if country_path.endswith("/country_sales"):
            debug_path = country_path[: -len("/country_sales")] + "/debug_counts_aggregations_job"
        else:
            debug_path = country_path + "_debug_aggregations_job"
        return f"s3://{parsed.netloc}{debug_path}/"

    def save_debug_counts(self, debug_counts: list[tuple[str, int]]) -> None:
        debug_output_path = self.build_debug_output_path()
        print(f"[AggregationsJob] writing debug counts to: {debug_output_path}")
        self.spark.createDataFrame(debug_counts, ["step", "row_count"]).write.mode("overwrite").json(
            debug_output_path
        )

    def build_cancellations_by_continent(self, raw_df: DataFrame, mapping_df: DataFrame) -> DataFrame:
        normalized_mapping_df = (
            mapping_df.withColumnRenamed("country", "Country")
            if "country" in mapping_df.columns
            else mapping_df
        )
        normalized_mapping_df = (
            normalized_mapping_df.withColumnRenamed("continent", "Continent")
            if "continent" in normalized_mapping_df.columns
            else normalized_mapping_df
        )
        return (
            raw_df.withColumn("InvoiceNo", F.col("InvoiceNo").cast("string"))
            .withColumn("Country", F.trim(F.col("Country").cast("string")))
            .filter(F.upper(F.col("InvoiceNo")).startswith("C"))
            .join(normalized_mapping_df.select("Country", "Continent"), on="Country", how="left")
            .groupBy("Continent")
            .agg(F.countDistinct("InvoiceNo").alias("CancelledOperations"))
            .orderBy(F.desc("CancelledOperations"))
        )

    def run_pipeline(self) -> None:
        enriched_df = self.load_enriched_data()
        raw_retail_df = self.load_catalog_table(self.config.retail_table)
        supplier_df = self.load_catalog_table(self.config.supplier_table)
        mapping_df = self.load_catalog_table(self.config.mapping_table)

        print(f"[AggregationsJob] enriched input rows: {enriched_df.count()}")
        print(f"[AggregationsJob] raw retail rows: {raw_retail_df.count()}")
        print(f"[AggregationsJob] supplier rows: {supplier_df.count()}")
        print(f"[AggregationsJob] mapping rows: {mapping_df.count()}")

        processor = AggregationProcessor(enriched_df)
        country_sales_df = processor.group_by_country()
        monthly_stats_df = processor.aggregate_monthly_data()
        supplier_sales_df = processor.aggregate_supplier_data(supplier_df)
        supplier_uk_2011_df = processor.aggregate_supplier_uk_2011(supplier_df)
        continent_sales_df = processor.aggregate_world_data(mapping_df)
        cancellations_by_continent_df = self.build_cancellations_by_continent(raw_retail_df, mapping_df)

        print(f"[AggregationsJob] country_sales rows: {country_sales_df.count()}")
        print(f"[AggregationsJob] monthly_stats rows: {monthly_stats_df.count()}")
        print(f"[AggregationsJob] supplier_sales rows: {supplier_sales_df.count()}")
        print(f"[AggregationsJob] supplier_uk_2011 rows: {supplier_uk_2011_df.count()}")
        print(f"[AggregationsJob] continent_sales rows: {continent_sales_df.count()}")
        print(f"[AggregationsJob] cancellations_by_continent rows: {cancellations_by_continent_df.count()}")

        debug_counts = [
            ("enriched_input", enriched_df.count()),
            ("raw_retail", raw_retail_df.count()),
            ("supplier", supplier_df.count()),
            ("mapping", mapping_df.count()),
            ("country_sales", country_sales_df.count()),
            ("monthly_stats", monthly_stats_df.count()),
            ("supplier_sales", supplier_sales_df.count()),
            ("supplier_uk_2011", supplier_uk_2011_df.count()),
            ("continent_sales", continent_sales_df.count()),
            ("cancellations_by_continent", cancellations_by_continent_df.count()),
        ]
        self.save_debug_counts(debug_counts)

        self.save_parquet(country_sales_df, self.config.country_output_path)
        self.save_parquet(monthly_stats_df, self.config.monthly_output_path)
        self.save_parquet(supplier_sales_df, self.config.supplier_output_path)
        self.save_parquet(supplier_uk_2011_df, self.config.supplier_uk_output_path)
        self.save_parquet(continent_sales_df, self.config.world_output_path)
        self.save_parquet(cancellations_by_continent_df, self.config.cancellation_output_path)


def main() -> None:
    config = AggregationJobConfig.from_args()

    sc = SparkContext.getOrCreate()
    glue_context = GlueContext(sc)
    spark = glue_context.spark_session
    job = Job(glue_context)
    job.init(config.job_name, vars(config))

    ETLPipeline(glue_context=glue_context, spark=spark, config=config).run_pipeline()

    job.commit()


if __name__ == "__main__":
    main()