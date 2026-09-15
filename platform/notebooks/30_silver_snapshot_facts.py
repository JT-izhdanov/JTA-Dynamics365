"""
30 — Silver snapshot facts

Appends one row per tracked record per day to silver.fact_*_snapshot.

WHY THIS MATTERS MOST: Dataverse is a current-state store. When an opportunity moves
stage, the prior stage is gone. So "what did the pipeline look like at quarter close?",
"how has case backlog trended?", and "is deal age getting worse?" cannot be answered from
Dataverse — and are not answerable by any first-party Dynamics 365 analytics either. The
data does not exist until someone starts capturing it.

HISTORY CANNOT BE BACKFILLED. A day not captured is lost permanently. This notebook is
deployed and scheduled in Sprint 1, before any semantic model or report exists — it is a
Sprint 1 exit criterion.

See docs/architecture/snapshot-and-history.md

DRAFT — never executed. See platform/README.md.
"""

# ---- CELL ----

from pyspark.sql import DataFrame, functions as F

from _common import (
    LAKEHOUSE,
    SILVER,
    bronze,
    load_config,
    spark_session,
    table_exists,
    utc_today,
)

CONFIG_PATH = "/lakehouse/default/Files/config/customer.yaml"

spark = spark_session()
config = load_config(CONFIG_PATH)

# Fixed UTC date. Snapshots must run on a consistent schedule — inconsistent local timing
# produces jagged trends that look like real business variation and are hard to diagnose.
SNAPSHOT_DATE = utc_today()
print(f"Snapshot date (UTC): {SNAPSHOT_DATE}")

# ---- CELL ----
# Snapshot definitions.
#
# Deliberately NARROW. Snapshots grow as records x days, and this is the one part of the
# architecture with an open-ended storage cost. Capture what changes and what is asked
# about — not every column of every table.
#
# `open_predicate` is the key cost control: open records are snapshotted daily, closed
# records once. A closed opportunity will not change again, so capture its final state and
# stop. This alone removes most of the growth.
#
# VERIFY every table and column name below against a live environment. statecode values in
# particular differ per table and are a common source of wrong results.

SNAPSHOT_SPECS: dict[str, dict] = {
    "fact_opportunity_snapshot": {
        "source": "opportunity",
        "key": "opportunityid",
        "columns": [
            "opportunityid",
            "name",
            "statecode",
            "statuscode",
            "salesstagecode",
            "stepname",
            "estimatedvalue",
            "estimatedvalue_base",
            "actualvalue",
            "actualvalue_base",
            "transactioncurrencyid",
            "estimatedclosedate",
            "actualclosedate",
            "closeprobability",
            "ownerid",
            "owningbusinessunit",
            "customerid",
            "createdon",
            "modifiedon",
        ],
        # statecode 0 = Open for opportunity. VERIFY.
        "open_predicate": F.col("statecode") == 0,
    },
    "fact_case_snapshot": {
        "source": "incident",
        "key": "incidentid",
        "columns": [
            "incidentid",
            "title",
            "ticketnumber",
            "statecode",
            "statuscode",
            "prioritycode",
            "casetypecode",
            "ownerid",
            "owningbusinessunit",
            "customerid",
            "createdon",
            "modifiedon",
            "resolveby",
            "firstresponseslastatus",
            "resolvebyslastatus",
        ],
        # statecode 0 = Active for incident. VERIFY.
        "open_predicate": F.col("statecode") == 0,
    },
    "fact_workorder_snapshot": {
        "source": "msdyn_workorder",
        "key": "msdyn_workorderid",
        "columns": [
            "msdyn_workorderid",
            "msdyn_name",
            "statecode",
            "statuscode",
            "msdyn_systemstatus",
            "msdyn_workordertype",
            "msdyn_priority",
            "msdyn_totalamount",
            "msdyn_totalestimatedduration",
            "ownerid",
            "owningbusinessunit",
            "msdyn_serviceaccount",
            "createdon",
            "modifiedon",
        ],
        # VERIFY: msdyn_systemstatus drives work order lifecycle more meaningfully than
        # statecode. Confirm which values represent "still open" before relying on this.
        "open_predicate": F.col("statecode") == 0,
    },
    "fact_project_snapshot": {
        "source": "msdyn_project",
        "key": "msdyn_projectid",
        "columns": [
            "msdyn_projectid",
            "msdyn_subject",
            "statecode",
            "statuscode",
            "msdyn_projectstage",
            "msdyn_scheduledstart",
            "msdyn_scheduledend",
            "msdyn_totalactualcost",
            "msdyn_totalbudgetcost",
            "ownerid",
            "owningbusinessunit",
            "msdyn_customer",
            "createdon",
            "modifiedon",
        ],
        "open_predicate": F.col("statecode") == 0,
    },
}

# Only snapshot what the purchased packs need.
enabled = config["snapshots"]["enabled"]
print(f"Enabled snapshots: {enabled}")

# ---- CELL ----


def already_snapshotted(target: str) -> bool:
    """Guard against double-writing a date.

    Snapshot writes are append-only and a snapshot is a statement about a day. Writing the
    same date twice double-counts every trend; restating it destroys the record. This is
    the one place idempotency is enforced by refusal rather than by overwrite.
    """
    if not table_exists(spark, SILVER, target):
        return False
    existing = spark.read.table(f"{LAKEHOUSE}.{SILVER}.{target}").where(
        F.col("snapshot_date") == F.lit(SNAPSHOT_DATE)
    )
    return not existing.isEmpty()


def build_snapshot(spec: dict) -> DataFrame:
    source = spec["source"]
    available = {f.name.lower() for f in bronze(spark, source).schema.fields}

    # Tolerate schema variation rather than failing the whole run: a column absent at this
    # customer's solution version should not stop history accumulating for the rest.
    selected = [c for c in spec["columns"] if c.lower() in available]
    absent = [c for c in spec["columns"] if c.lower() not in available]
    if absent:
        print(f"  NOTE {source}: columns absent at this version, omitted: {absent}")

    df = bronze(spark, source).select(*selected)

    # Snapshot open records daily; closed records once.
    if already_snapshotted_any(spec, source):
        closed_keys = closed_already_captured(spec)
        df = df.where(spec["open_predicate"] | ~F.col(spec["key"]).isin(closed_keys))

    return df.withColumn("snapshot_date", F.lit(SNAPSHOT_DATE)).withColumn(
        "snapshot_loaded_at_utc", F.current_timestamp()
    )


def already_snapshotted_any(spec: dict, source: str) -> bool:
    return table_exists(spark, SILVER, target_for(source))


def target_for(source: str) -> str:
    for target, spec in SNAPSHOT_SPECS.items():
        if spec["source"] == source:
            return target
    raise KeyError(source)


def closed_already_captured(spec: dict) -> list:
    """Keys of closed records whose final state is already captured.

    # VERIFY: at scale this list becomes large and an isin() filter is the wrong shape —
    # replace with an anti-join against a persisted `closed_captured` table during the
    # first build. Kept simple here to make the intent readable.
    """
    target = target_for(spec["source"])
    captured = (
        spark.read.table(f"{LAKEHOUSE}.{SILVER}.{target}")
        .where(F.col("statecode") != 0)
        .select(spec["key"])
        .distinct()
    )
    return [row[0] for row in captured.collect()]


# ---- CELL ----
# Run.

for target in enabled:
    spec = SNAPSHOT_SPECS.get(target)
    if spec is None:
        raise KeyError(f"snapshot '{target}' enabled in config but not defined here")

    if not table_exists(spark, "bronze", spec["source"]):
        print(f"SKIP {target}: source table {spec['source']} not present in Bronze")
        continue

    if already_snapshotted(target):
        print(f"SKIP {target}: {SNAPSHOT_DATE} already captured")
        continue

    snapshot = build_snapshot(spec)
    (
        snapshot.write.format("delta")
        .mode("append")
        .partitionBy("snapshot_date")
        .option("mergeSchema", "true")  # tolerate columns added mid-history
        .saveAsTable(f"{LAKEHOUSE}.{SILVER}.{target}")
    )
    print(f"OK {target}: appended {snapshot.count()} rows for {SNAPSHOT_DATE}")

# ---- CELL ----
# Completeness check.
#
# A snapshot job that silently stops loses history without surfacing any error in any
# report — the failure mode is invisible until someone asks a trend question months later.
# Gaps must be detectable, and this check is what makes them so. Monitoring the snapshot
# job is not optional; it is named as an owned responsibility at support handoff.

for target in enabled:
    if not table_exists(spark, SILVER, target):
        continue

    dates = (
        spark.read.table(f"{LAKEHOUSE}.{SILVER}.{target}")
        .select("snapshot_date")
        .distinct()
        .orderBy("snapshot_date")
    )
    first = dates.first()[0]
    captured = dates.count()
    expected = (SNAPSHOT_DATE - first).days + 1

    if captured != expected:
        print(
            f"ALERT {target}: {captured} snapshot dates captured but {expected} days "
            f"elapsed since {first} — {expected - captured} DAY(S) MISSING AND "
            "UNRECOVERABLE. Investigate the schedule immediately."
        )
    else:
        print(f"OK {target}: complete, {captured} consecutive days from {first}")
