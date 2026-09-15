"""
20 — Silver conformance: choice / option-set labels

Produces silver.lkp_choice_label — one conformed lookup keyed by (table, column, value)
resolving Dataverse choice integers to labels.

WHY THIS MATTERS: Dataverse stores choices as integers. `opportunity.statuscode = 3` is
meaningless in a report, and the labels live in metadata rather than in the data table.
This is the first thing a customer notices and the first thing they cannot fix themselves
cleanly. In-house attempts start as hard-coded CASE statements and become unmaintainable.
Solving it once, as a lookup every Silver table joins to, is core IP.

See docs/architecture/conformance-layer.md#1-choice--option-set-labels

DRAFT — never executed, and the metadata source is UNRESOLVED. See the VERIFY block below.
"""

# ---- CELL ----

from pyspark.sql import DataFrame, functions as F

from _common import BRONZE, assert_unique, bronze, fail_if_empty, load_config, spark_session, table_exists, write_silver

CONFIG_PATH = "/lakehouse/default/Files/config/customer.yaml"

spark = spark_session()
config = load_config(CONFIG_PATH)

# Language is configuration, not a constant. Dataverse metadata is per-language, and a
# multi-language tenant will have several.
LANGUAGE_CODE = config["locale"]["language_code"]  # e.g. 1033 for en-US

# ---- CELL ----
# VERIFY — UNRESOLVED, RESOLVE BEFORE USING THIS NOTEBOOK
#
# How Link to Fabric exposes option-set metadata is not confirmed. Three candidate shapes,
# in rough order of likelihood:
#
#   1. `stringmap` — the Dataverse table itself. Columns approximately:
#        objecttypecode (entity), attributename, attributevalue, value (label), langid
#   2. `optionsetmetadata` — as exposed by Synapse Link for Dataverse. Columns approximately:
#        EntityName, OptionSetName, Option, LocalizedLabel, LocalizedLabelLanguageCode
#   3. `globaloptionsetmetadata` — as above, for global option sets shared across tables
#
# Column names and casing below are ASSUMPTIONS. Inspect the real schema first
# (notebook 10 reports which of these are present) and correct this notebook from what is
# actually there. Do not guess further — a wrong label mapping is worse than no mapping,
# because it looks right.

TARGET_SCHEMA = "table_name string, column_name string, option_value int, option_label string"

# ---- CELL ----


def from_stringmap(spark) -> DataFrame:
    """Candidate 1 — the Dataverse `stringmap` table.

    # VERIFY: column names, and whether objecttypecode is the entity logical name or the
    # numeric type code. If numeric, it needs resolving against entity metadata.
    """
    df = bronze(spark, "stringmap")
    return (
        df.where(F.col("langid") == F.lit(LANGUAGE_CODE))
        .select(
            F.lower(F.col("objecttypecode").cast("string")).alias("table_name"),
            F.lower(F.col("attributename")).alias("column_name"),
            F.col("attributevalue").cast("int").alias("option_value"),
            F.col("value").alias("option_label"),
        )
    )


def from_optionset_metadata(spark, table: str) -> DataFrame:
    """Candidates 2 and 3 — Synapse Link-style metadata tables.

    # VERIFY: exact column names and casing.
    """
    df = bronze(spark, table)
    return (
        df.where(F.col("LocalizedLabelLanguageCode") == F.lit(LANGUAGE_CODE))
        .select(
            F.lower(F.col("EntityName")).alias("table_name"),
            F.lower(F.col("OptionSetName")).alias("column_name"),
            F.col("Option").cast("int").alias("option_value"),
            F.col("LocalizedLabel").alias("option_label"),
        )
    )


# ---- CELL ----
# Resolve whichever source this environment actually provides.

sources: list[DataFrame] = []

if table_exists(spark, BRONZE, "stringmap"):
    print("Using stringmap")
    sources.append(from_stringmap(spark))

for metadata_table in ("optionsetmetadata", "globaloptionsetmetadata"):
    if table_exists(spark, BRONZE, metadata_table):
        print(f"Using {metadata_table}")
        sources.append(from_optionset_metadata(spark, metadata_table))

if not sources:
    raise ValueError(
        "No choice-label metadata source found in Bronze. Choice labels cannot be "
        "resolved, which means integer status codes in reports. Investigate how this "
        "environment exposes option-set metadata — see the VERIFY block above."
    )

# ---- CELL ----
# Union, deduplicate, and guard the grain.
#
# Global option sets can appear in more than one source, so dedupe rather than assuming
# disjointness. Duplicate keys here would fan out every join in Silver.

labels = sources[0]
for extra in sources[1:]:
    labels = labels.unionByName(extra)

labels = (
    labels.where(F.col("option_label").isNotNull())
    .dropDuplicates(["table_name", "column_name", "option_value"])
)

labels = fail_if_empty(labels, "lkp_choice_label")
labels = assert_unique(
    labels, ["table_name", "column_name", "option_value"], "lkp_choice_label"
)

write_silver(labels, "lkp_choice_label")

print(f"lkp_choice_label written — {labels.count()} rows")

# ---- CELL ----
# Usage pattern for downstream Silver notebooks.
#
# Join to the lookup; never hard-code a CASE statement. A hard-coded mapping is invisible
# when the customer adds a status reason, and that is exactly when it starts being wrong.
#
#     labels = silver(spark, "lkp_choice_label")
#
#     opportunity = (
#         bronze(spark, "opportunity")
#         .join(
#             labels.where(
#                 (F.col("table_name") == "opportunity")
#                 & (F.col("column_name") == "statuscode")
#             ).select(
#                 F.col("option_value").alias("statuscode"),
#                 F.col("option_label").alias("status_reason"),
#             ),
#             on="statuscode",
#             how="left",
#         )
#     )
#
# Left join deliberately: an unmapped value must surface as NULL and be investigated,
# not silently drop the fact row.

# ---- CELL ----
# Coverage check — which choice columns in scope have no labels.
#
# Worth running during the first build. Every gap is either a metadata source problem or
# a mapping error, and both are cheaper to find now than in UAT.

choice_columns_in_scope = config["tables"].get("choice_columns", {})

gaps = []
for table, columns in choice_columns_in_scope.items():
    for column in columns:
        covered = labels.where(
            (F.col("table_name") == table.lower()) & (F.col("column_name") == column.lower())
        ).limit(1)
        if covered.isEmpty():
            gaps.append((table, column))

if gaps:
    print("Choice columns in scope with NO labels resolved:")
    for table, column in gaps:
        print(f"  {table}.{column}")
    print("  Investigate each before building packs that use them.")
else:
    print("All in-scope choice columns have labels.")
