"""
Shared helpers for the JourneyTeam Analytics conformance notebooks.

DRAFT — never executed. See platform/README.md.

Loaded by the other notebooks. In Fabric this is attached via %run or imported from a
resources folder; the mechanism is a first-build decision.

# VERIFY: how the Link to Fabric shortcut surfaces in the lakehouse (schema name, table
# naming, direct Delta queryability). Every Bronze read below depends on it.
"""

# ---- CELL ----

import datetime as _dt
from typing import Any

import yaml
from pyspark.sql import DataFrame, SparkSession, functions as F

LAKEHOUSE = "jta_lakehouse"
BRONZE = "bronze"
SILVER = "silver"
GOLD = "gold"


# ---- CELL ----


def load_config(path: str) -> dict[str, Any]:
    """Load the per-customer configuration.

    Nothing in these notebooks is hard-coded per customer. See platform/config/ for the
    schema and platform/config/customer.example.yaml for the template.
    """
    with open(path) as fh:
        config = yaml.safe_load(fh)

    required = ["customer", "locale", "fiscal_calendar", "currency", "tables", "snapshots"]
    missing = [key for key in required if key not in config]
    if missing:
        raise ValueError(f"customer config is missing required keys: {missing}")
    return config


def spark_session() -> SparkSession:
    """The Fabric runtime provides `spark`; this keeps the helpers importable elsewhere."""
    return SparkSession.builder.getOrCreate()


# ---- CELL ----


def bronze(spark: SparkSession, table: str) -> DataFrame:
    """Read a Dataverse table from the Bronze shortcut.

    Bronze is the Link to Fabric shortcut: Microsoft-managed and READ-ONLY. Never write
    to it. All JourneyTeam logic must be reproducible from Bronze by re-running notebooks,
    so that recreating the shortcut loses nothing but time.

    `table` is the Dataverse *logical* name, lowercase (account, opportunity, incident,
    msdyn_workorder). Never a display name.
    """
    return spark.read.table(f"{LAKEHOUSE}.{BRONZE}.{table}")


def silver(spark: SparkSession, table: str) -> DataFrame:
    return spark.read.table(f"{LAKEHOUSE}.{SILVER}.{table}")


def write_silver(df: DataFrame, table: str, mode: str = "overwrite") -> None:
    """Write a Silver table. Conformance output is idempotent; snapshots append."""
    (
        df.write.format("delta")
        .mode(mode)
        .option("overwriteSchema", "true" if mode == "overwrite" else "false")
        .saveAsTable(f"{LAKEHOUSE}.{SILVER}.{table}")
    )


def write_gold(df: DataFrame, table: str, mode: str = "overwrite") -> None:
    (
        df.write.format("delta")
        .mode(mode)
        .option("overwriteSchema", "true" if mode == "overwrite" else "false")
        .saveAsTable(f"{LAKEHOUSE}.{GOLD}.{table}")
    )


def table_exists(spark: SparkSession, schema: str, table: str) -> bool:
    return spark.catalog.tableExists(f"{LAKEHOUSE}.{schema}.{table}")


# ---- CELL ----


def surrogate_key(*columns: str) -> "F.Column":
    """Deterministic surrogate key from one or more natural key columns.

    Dataverse GUIDs work as natural keys but perform poorly at volume in a Power BI model
    and are unreadable when debugging. Generate a surrogate and retain the GUID as a
    documented attribute (suffixed `_guid`), per the medallion naming convention.
    """
    parts = [F.coalesce(F.col(c).cast("string"), F.lit("~")) for c in columns]
    return F.sha2(F.concat_ws("||", *parts), 256)


def fail_if_empty(df: DataFrame, description: str) -> DataFrame:
    """Fail loudly.

    A silent partial success in the conformance layer becomes a wrong number in a report
    three weeks later, by which point it costs far more to find. Raise, never
    warn-and-continue.
    """
    if df.isEmpty():
        raise ValueError(f"{description} produced zero rows — refusing to continue")
    return df


def assert_unique(df: DataFrame, keys: list[str], description: str) -> DataFrame:
    """Guard a dimension's grain. Duplicate keys fan out fact joins silently."""
    total = df.count()
    distinct = df.select(*keys).distinct().count()
    if total != distinct:
        raise ValueError(
            f"{description} is not unique on {keys}: {total} rows, {distinct} distinct"
        )
    return df


# ---- CELL ----


def utc_today() -> _dt.date:
    """Snapshot date.

    Snapshots run on a fixed UTC schedule. Inconsistent local timing produces jagged
    trends that look like real business variation and are very hard to diagnose later.
    """
    return _dt.datetime.now(_dt.timezone.utc).date()
