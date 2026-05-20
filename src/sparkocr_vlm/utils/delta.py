"""Delta read/write helpers."""

from __future__ import annotations


def write_silver(df, path: str, merge_keys: list[str] | None = None) -> None:
    """Write a DataFrame to a silver Delta table.

    Uses overwrite mode for first write, merge upsert for subsequent ones if
    ``merge_keys`` is provided.
    """
    if merge_keys:
        from delta.tables import DeltaTable

        spark = df.sparkSession
        if DeltaTable.isDeltaTable(spark, path):
            target = DeltaTable.forPath(spark, path)
            condition = " AND ".join(f"t.{k} = s.{k}" for k in merge_keys)
            (
                target.alias("t")
                .merge(df.alias("s"), condition)
                .whenMatchedUpdateAll()
                .whenNotMatchedInsertAll()
                .execute()
            )
            return

    df.write.format("delta").mode("overwrite").save(path)


def read_delta(spark, path: str):
    """Read a Delta table at ``path``."""
    return spark.read.format("delta").load(path)
