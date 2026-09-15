"""
10 — Bronze shortcut validation

Gate for the entire run. If this fails, nothing downstream executes.

Dataverse schema varies by solution version and by which apps are installed, so source
mappings written from general knowledge WILL contain errors. This notebook exists to
surface every one of them here, where the fix is cheap, rather than in UAT, where a wrong
number costs confidence in the whole platform.

DRAFT — never executed. See platform/README.md.
"""

# ---- CELL ----

from pyspark.sql import functions as F

from _common import BRONZE, LAKEHOUSE, bronze, load_config, spark_session, table_exists

CONFIG_PATH = "/lakehouse/default/Files/config/customer.yaml"  # parameterized at runtime

spark = spark_session()
config = load_config(CONFIG_PATH)

# ---- CELL ----
# Expected tables come from config, which is assembled from the packs sold.
# See packs/*/source-tables.md for the per-pack mappings.

expected = config["tables"]["required"]
optional = config["tables"].get("optional", [])

print(f"Validating {len(expected)} required and {len(optional)} optional Bronze tables")

# ---- CELL ----
# Check 1 — presence

missing = [t for t in expected if not table_exists(spark, BRONZE, t)]
missing_optional = [t for t in optional if not table_exists(spark, BRONZE, t)]

if missing_optional:
    print(f"NOTE optional tables absent (packs depending on them cannot build): {missing_optional}")

if missing:
    raise ValueError(
        "Required Bronze tables are absent from the Link to Fabric shortcut: "
        f"{missing}. Either the tables were not selected into the link, the apps are not "
        "installed, or the source mapping in packs/*/source-tables.md is wrong. "
        "Resolve before running any downstream notebook."
    )

print("Check 1 (presence): PASS")

# ---- CELL ----
# Check 2 — rows present
#
# A table that exists but is empty usually means the app is installed but unused. That is
# a scoping finding, not a technical failure: a pack built against it will produce empty
# reports, and the customer needs to know before UAT.

empty = []
for table in expected:
    if bronze(spark, table).limit(1).isEmpty():
        empty.append(table)

if empty:
    print(
        f"WARNING required tables are present but EMPTY: {empty}\n"
        "  The app is likely installed but unused. Raise with the project lead as a "
        "scoping item before building packs against these tables."
    )
else:
    print("Check 2 (rows): PASS")

# ---- CELL ----
# Check 3 — expected columns
#
# The most valuable check here. Column-level drift is what silently produces wrong
# numbers rather than obvious errors.

column_expectations: dict[str, list[str]] = config["tables"].get("columns", {})

column_failures: dict[str, list[str]] = {}
for table, columns in column_expectations.items():
    if not table_exists(spark, BRONZE, table):
        continue
    actual = {f.name.lower() for f in bronze(spark, table).schema.fields}
    absent = [c for c in columns if c.lower() not in actual]
    if absent:
        column_failures[table] = absent

if column_failures:
    for table, absent in column_failures.items():
        print(f"  {table}: missing {absent}")
    raise ValueError(
        "Expected columns are absent. Correct packs/*/source-tables.md from what is "
        "actually present, then re-run. Do not work around this downstream."
    )

print("Check 3 (columns): PASS")

# ---- CELL ----
# Check 4 — conformance prerequisites
#
# VERIFY: this is the single most important unresolved item in the whole platform.
#
# Choice/option-set labels live in metadata, not in the data tables. Synapse Link for
# Dataverse exposed `OptionsetMetadata` and `GlobalOptionsetMetadata`; Dataverse also has
# a `stringmap` table. Which of these Link to Fabric actually surfaces, and in what shape,
# determines how 20_silver_conformance_choice_labels is written.
#
# Resolve this against a live environment FIRST. Do not assume the Synapse Link shape
# carries over unchanged.

metadata_candidates = ["stringmap", "optionsetmetadata", "globaloptionsetmetadata"]
available_metadata = [t for t in metadata_candidates if table_exists(spark, BRONZE, t)]

print(f"Choice-label metadata sources available in Bronze: {available_metadata or 'NONE'}")

if not available_metadata:
    print(
        "WARNING no recognized choice-label metadata source found.\n"
        "  Choice labels cannot be resolved without one, and integer status codes in "
        "reports are the first thing a customer notices.\n"
        "  Investigate how this environment exposes option-set metadata before "
        "proceeding to notebook 20."
    )

# ---- CELL ----
# Check 5 — row counts for the record
#
# Recorded so that reconciliation in Sprint 2 has a baseline, and so that an unexpected
# drop in a later run is detectable.

counts = [(t, bronze(spark, t).count()) for t in expected if table_exists(spark, BRONZE, t)]
summary = spark.createDataFrame(counts, "table_name string, row_count long").withColumn(
    "validated_at_utc", F.current_timestamp()
)

summary.orderBy("table_name").show(truncate=False)

# Persisted for trend comparison across runs.
(
    summary.write.format("delta")
    .mode("append")
    .saveAsTable(f"{LAKEHOUSE}.silver.ops_bronze_validation_log")
)

print("Bronze validation complete — downstream notebooks may run.")
