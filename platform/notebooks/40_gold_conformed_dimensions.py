"""
40 — Gold: publish conformed dimensions

Exposes the Silver conformed dimensions into the `gold` schema for semantic models.

THE RULE THIS NOTEBOOK ENFORCES: conformed dimensions are SHARED, not copied. Gold exposes
a VIEW over the Silver dimension. A pack never gets its own physical copy.

That rule is what keeps the conformance layer reusable IP rather than one customer's Sales
model: reusability is decided when a dimension is built, not when a second consumer shows
up. It is also the rule most likely to be broken under delivery pressure ("just duplicate
it for this one pack"), which is why it is enforced here in code rather than left to
discipline.

See docs/architecture/medallion-design.md
See docs/architecture/conformance-layer.md

DRAFT — never executed. See platform/README.md.
"""

# ---- CELL ----

from _common import GOLD, LAKEHOUSE, SILVER, spark_session, table_exists

spark = spark_session()

# ---- CELL ----
# Conformed dimensions consumed by every pack.
#
# dim_product, dim_territory, dim_project, and dim_resource are built by pack-specific
# notebooks (5x) and published here once they exist.

CONFORMED = [
    "dim_date",
    "dim_owner",
    "dim_currency",
    "dim_customer",
    "dim_contact",
    "lkp_choice_label",
    "bridge_activity",
]

OPTIONAL_CONFORMED = [
    "dim_product",
    "dim_territory",
    "dim_project",
    "dim_resource",
]

# ---- CELL ----
# Publish as views over Silver — deliberately not CTAS.
#
# A view cannot drift from its Silver source. A copy can, and a pack reading a stale copy
# of dim_owner produces numbers that disagree with another pack reading the live one. That
# class of defect is very hard to diagnose because both reports look internally consistent.

missing = [t for t in CONFORMED if not table_exists(spark, SILVER, t)]
if missing:
    raise ValueError(
        f"Required Silver conformed dimensions are absent: {missing}. "
        "Run the conformance notebooks (2x) before this one."
    )

for table in CONFORMED + OPTIONAL_CONFORMED:
    if not table_exists(spark, SILVER, table):
        print(f"SKIP {table}: not yet built (pack-specific dimension)")
        continue

    # SCD2 dimensions publish only current rows to Gold for normal reporting. Snapshot
    # facts join the full versioned Silver dimension directly, so that history is
    # attributed to the org structure as it was — see docs/architecture/snapshot-and-history.md
    #
    # OPEN DECISION D9 — this filter is contested and needs a decision before the first
    # pack ships. See packs/sales/technical-design.md §5.2.
    #
    # The Sales pack design argues this filter is WRONG once a snapshot fact joins the same
    # dimension in a Power BI model: a snapshot row carrying an as-of owner version key
    # finds no matching Gold row and loses its owner entirely. The proposed fix is to
    # publish ALL versions here (grain = entity version, with is_current / effective_from /
    # effective_to as attributes), letting transaction facts carry the current version key
    # and snapshot facts the as-of key. Slicers use the name, which spans versions.
    #
    # It affects every pack's snapshot ownership, so it is a platform decision, not a
    # pack-local one. Resolve it before building the first semantic model over a snapshot
    # fact — changing it afterwards means reworking Gold, the model, and RLS.
    scd2_filter = " WHERE is_current = true" if table in ("dim_owner", "dim_customer", "dim_product") else ""

    spark.sql(
        f"CREATE OR REPLACE VIEW {LAKEHOUSE}.{GOLD}.{table} AS "
        f"SELECT * FROM {LAKEHOUSE}.{SILVER}.{table}{scd2_filter}"
    )
    print(f"OK published gold.{table}{' (current rows only)' if scd2_filter else ''}")

print("Conformed dimensions published to Gold.")

# ---- CELL ----
# TODO — Sales Gold build (notebooks 6x).
#
# The pack publishes its own fact tables into Gold, prefixed by pack:
#   sales__fact_opportunity, sales__fact_opportunity_snapshot,
#   sales__fact_opportunity_line, sales__fact_opportunity_stage_transition
#
# The pack prefix is kept even with a single pack, so a second one can land without
# renaming anything. See packs/sales/technical-design.md for the Gold star schema.
#
# Pack facts join to the conformed dimension VIEWS published above. A pack that needs a
# dimension attribute which does not exist should extend the CONFORMED dimension in Silver
# — not create a pack-local variant. If two packs ever genuinely need incompatible versions
# of a dimension, that is an architecture question worth an ADR, not a local workaround.
