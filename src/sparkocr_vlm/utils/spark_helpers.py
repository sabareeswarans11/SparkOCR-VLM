"""SparkSession builders. Use ``build_local_spark`` everywhere except on Databricks."""

from __future__ import annotations

import os
import sys


def build_local_spark(
    app_name: str = "sparkocr-vlm",
    cores: str = "*",
    memory: str = "4g",
    delta_version: str = "3.2.1",
    s3: bool = False,
):
    """Return a Delta-enabled local SparkSession.

    Tuned for a 16 GB Intel Mac. For the test suite, use ``cores="2"`` and ``memory="2g"``.
    """
    # Ensure Spark workers use the same Python as the driver (avoids 3.8 vs 3.11 mismatch).
    os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
    os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)

    from pyspark.sql import SparkSession

    builder = (
        SparkSession.builder.master(f"local[{cores}]")
        .appName(app_name)
        .config(
            "spark.jars.packages",
            f"io.delta:delta-spark_2.12:{delta_version}"
            + (",org.apache.hadoop:hadoop-aws:3.3.4" if s3 else ""),
        )
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
        .config("spark.driver.memory", memory)
        .config("spark.executor.memory", memory)
        .config("spark.sql.shuffle.partitions", "4")
    )

    if s3:
        from sparkocr_vlm.config import settings

        s = settings()
        if s.s3_endpoint_url:
            builder = (
                builder.config("spark.hadoop.fs.s3a.endpoint", s.s3_endpoint_url)
                .config("spark.hadoop.fs.s3a.path.style.access", "true")
                .config(
                    "spark.hadoop.fs.s3a.aws.credentials.provider",
                    "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider",
                )
            )
        if s.aws_access_key_id and s.aws_secret_access_key:
            builder = builder.config(
                "spark.hadoop.fs.s3a.access.key", s.aws_access_key_id
            ).config(
                "spark.hadoop.fs.s3a.secret.key",
                s.aws_secret_access_key.get_secret_value(),
            )

    return builder.getOrCreate()
