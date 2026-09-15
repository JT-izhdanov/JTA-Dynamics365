"""
22 — Silver conformance: ownership hierarchy

Produces silver.dim_owner — users, teams, and business units flattened, with the business
unit path and manager hierarchy resolved. SCD2.

WHY THIS MATTERS: records are owned by a user or a team; users and teams sit in
hierarchical business units. That hierarchy is BOTH a reporting dimension (performance by
region or manager) AND the source of the security model. Building it once serves both —
which is why it lives in the conformance layer rather than in each pack.

SCD2 is required here, not optional: territory and manager reassignment is constant in
sales organizations, and attributing last year's results to this year's manager is wrong.
Snapshot facts must join the owner as-of the snapshot date.

See docs/architecture/conformance-layer.md#5-ownership-hierarchy
See docs/architecture/security-and-rls.md

DRAFT — never executed. See platform/README.md.
"""

# ---- CELL ----

from pyspark.sql import functions as F

from _common import assert_unique, bronze, fail_if_empty, load_config, spark_session, surrogate_key, write_silver

CONFIG_PATH = "/lakehouse/default/Files/config/customer.yaml"

spark = spark_session()
config = load_config(CONFIG_PATH)

# Business unit depth is configuration — organizations differ, and a fixed assumption
# either truncates a deep hierarchy or pads a shallow one with nulls.
BU_LEVELS = config["hierarchy"]["business_unit_levels"]
MANAGER_LEVELS = config["hierarchy"]["manager_levels"]

# ---- CELL ----
# Business unit hierarchy.
#
# businessunit.parentbusinessunitid is self-referencing. Flatten to fixed levels by
# iterative self-join — Spark has no recursive CTE, and the depth is bounded and known
# from config.
#
# VERIFY: column names, and whether the customer's BU hierarchy actually reaches
# BU_LEVELS deep. Notebook 10 should report observed depth.

bu = bronze(spark, "businessunit").select(
    F.col("businessunitid").alias("business_unit_guid"),
    F.col("name").alias("business_unit_name"),
    F.col("parentbusinessunitid").alias("parent_business_unit_guid"),
)

bu_path = bu.select(
    "business_unit_guid",
    "business_unit_name",
    "parent_business_unit_guid",
    F.col("business_unit_name").alias("bu_level_1"),
)

current = bu_path
for level in range(2, BU_LEVELS + 1):
    parent = bu.select(
        F.col("business_unit_guid").alias("_parent_guid"),
        F.col("business_unit_name").alias(f"bu_level_{level}"),
        F.col("parent_business_unit_guid").alias("_next_parent_guid"),
    )
    current = current.join(
        parent,
        current["parent_business_unit_guid"] == parent["_parent_guid"],
        how="left",
    ).drop("_parent_guid", "parent_business_unit_guid").withColumnRenamed(
        "_next_parent_guid", "parent_business_unit_guid"
    )

bu_flat = current.drop("parent_business_unit_guid")

# ---- CELL ----
# Manager hierarchy.
#
# systemuser.parentsystemuserid gives the manager chain, where populated. Many customers
# do not maintain it — if it is sparse, manager-based RLS is not viable and that is a
# scoping finding to raise, not something to work around silently.

users = bronze(spark, "systemuser").select(
    F.col("systemuserid").alias("owner_guid"),
    F.col("fullname").alias("owner_name"),
    F.col("internalemailaddress").alias("owner_email"),
    F.col("businessunitid").alias("business_unit_guid"),
    F.col("parentsystemuserid").alias("manager_guid"),
    F.col("isdisabled").alias("is_disabled"),
    F.col("territoryid").alias("territory_guid"),
    F.lit("User").alias("owner_type"),
)

manager_populated = users.where(F.col("manager_guid").isNotNull()).count()
total_users = users.count()
print(f"Manager chain populated on {manager_populated} of {total_users} users")
if total_users and manager_populated / total_users < 0.5:
    print(
        "  WARNING manager hierarchy is sparse. Manager-based RLS and manager rollup "
        "reporting are not viable on this data. Raise with the project lead as a scoping "
        "item before promising either."
    )

# Flatten the manager chain to fixed levels.
managers = users.select(
    F.col("owner_guid").alias("_mgr_guid"),
    F.col("owner_name").alias("manager_name"),
    F.col("manager_guid").alias("_mgr_parent_guid"),
)

user_mgr = users
for level in range(1, MANAGER_LEVELS + 1):
    step = managers.select(
        F.col("_mgr_guid"),
        F.col("manager_name").alias(f"manager_level_{level}"),
        F.col("_mgr_parent_guid"),
    )
    user_mgr = (
        user_mgr.join(step, user_mgr["manager_guid"] == step["_mgr_guid"], how="left")
        .drop("_mgr_guid", "manager_guid")
        .withColumnRenamed("_mgr_parent_guid", "manager_guid")
    )

user_mgr = user_mgr.drop("manager_guid")

# ---- CELL ----
# Teams.
#
# Records can be owned by a team as well as a user, so dim_owner must cover both or
# team-owned records lose their owner attribution entirely.

teams = bronze(spark, "team").select(
    F.col("teamid").alias("owner_guid"),
    F.col("name").alias("owner_name"),
    F.lit(None).cast("string").alias("owner_email"),
    F.col("businessunitid").alias("business_unit_guid"),
    F.lit(None).cast("boolean").alias("is_disabled"),
    F.lit(None).cast("string").alias("territory_guid"),
    F.lit("Team").alias("owner_type"),
)

for level in range(1, MANAGER_LEVELS + 1):
    teams = teams.withColumn(f"manager_level_{level}", F.lit(None).cast("string"))

# ---- CELL ----
# Union, attach the business unit path, key.

owners = user_mgr.unionByName(teams, allowMissingColumns=True)

dim_owner = (
    owners.join(bu_flat, on="business_unit_guid", how="left")
    .withColumn("owner_key", surrogate_key("owner_guid"))
    .withColumn("effective_from", F.current_date())
    .withColumn("effective_to", F.lit(None).cast("date"))
    .withColumn("is_current", F.lit(True))
)

dim_owner = fail_if_empty(dim_owner, "dim_owner")
dim_owner = assert_unique(dim_owner, ["owner_guid"], "dim_owner (initial load)")

write_silver(dim_owner, "dim_owner")
print(f"dim_owner written — {dim_owner.count()} rows")

# ---- CELL ----
# TODO — SCD2 merge, required before the first customer go-live.
#
# The write above is an INITIAL LOAD ONLY. It overwrites, which destroys history the
# moment anything changes — exactly what SCD2 exists to prevent.
#
# Implement as a Delta MERGE:
#   - detect change on the tracked attributes (business unit path, manager chain,
#     territory, name, disabled status)
#   - close the current row: effective_to = today - 1 day, is_current = false
#   - insert a new row: effective_from = today, is_current = true
#   - leave unchanged rows untouched
#   - generate owner_key per VERSION, not per owner, so snapshot facts can join the owner
#     as-of the snapshot date
#
# The last point is the one that is easy to get wrong and expensive to fix: if owner_key
# is per-owner rather than per-version, historical snapshots silently re-attribute to
# today's org structure as people change jobs, and the numbers change retroactively.
#
# See docs/architecture/snapshot-and-history.md#scd2-on-key-dimensions
