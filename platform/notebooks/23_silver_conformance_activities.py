"""
23 — Silver conformance: activity bridge

Produces silver.bridge_activity — one row per activity with typed keys per target entity,
resolving Dataverse's polymorphic `regardingobjectid`.

WHY THIS MATTERS: `activitypointer` is the base table for all activity types, and
`regardingobjectid` points at ANY table — Lead, Opportunity, Case, Work Order. There is no
clean foreign key, so every model that wants activity analytics has to solve polymorphism
itself.

Activity analytics — touches per opportunity, response time on a case, contact cadence — is
one of the highest-value question sets and one of the most annoying to build. Solving it
once in the conformance layer is worth disproportionately more than it costs.

See docs/architecture/conformance-layer.md#3-polymorphic-activities

DRAFT — never executed. See platform/README.md.
"""

# ---- CELL ----

from pyspark.sql import functions as F

from _common import assert_unique, bronze, fail_if_empty, silver, spark_session, surrogate_key, write_silver

spark = spark_session()

# ---- CELL ----
# activitypointer carries every activity type.
#
# VERIFY: column names, and specifically how the target entity type is exposed.
# Dataverse has `regardingobjecttypecode` alongside `regardingobjectid`; whether the
# shortcut surfaces it as the entity LOGICAL NAME or as a NUMERIC type code determines
# whether it needs resolving against entity metadata. Confirm before relying on it.

activities = bronze(spark, "activitypointer").select(
    F.col("activityid").alias("activity_guid"),
    F.col("subject").alias("activity_subject"),
    F.col("activitytypecode").alias("activity_type_code"),
    F.col("regardingobjectid").alias("regarding_guid"),
    F.col("regardingobjecttypecode").alias("regarding_type"),
    F.col("statecode").alias("state_code"),
    F.col("statuscode").alias("status_code"),
    F.col("createdon").alias("created_on_utc"),
    F.col("modifiedon").alias("modified_on_utc"),
    F.col("scheduledstart").alias("scheduled_start_utc"),
    F.col("scheduledend").alias("scheduled_end_utc"),
    F.col("actualstart").alias("actual_start_utc"),
    F.col("actualend").alias("actual_end_utc"),
    F.col("actualdurationminutes").alias("actual_duration_minutes"),
    F.col("ownerid").alias("owner_guid"),
    F.col("directioncode").alias("is_outgoing"),
)

# ---- CELL ----
# Resolve labels for activity type and status via the conformed lookup.
# Never hard-code a CASE statement — see notebook 20.

labels = silver(spark, "lkp_choice_label")


def attach_label(df, table_name: str, column_name: str, source_col: str, target_col: str):
    lookup = labels.where(
        (F.col("table_name") == table_name) & (F.col("column_name") == column_name)
    ).select(
        F.col("option_value").alias("_value"),
        F.col("option_label").alias(target_col),
    )
    # Left join deliberately: an unmapped value must surface as NULL and be investigated,
    # never silently drop the activity row.
    return df.join(lookup, df[source_col] == lookup["_value"], how="left").drop("_value")


activities = attach_label(
    activities, "activitypointer", "activitytypecode", "activity_type_code", "activity_type"
)

# ---- CELL ----
# Typed keys per target entity.
#
# One nullable key column per target rather than a single generic key. This is what lets a
# downstream model join activities to its subject area with a normal relationship, instead
# of re-solving polymorphism in DAX — which is slow and error-prone.
#
# VERIFY: the `regarding_type` values below assume logical entity names. If the shortcut
# exposes numeric type codes, map them first.

TARGETS = {
    "opportunity": "opportunity_guid",
    "lead": "lead_guid",
    "incident": "incident_guid",
    "account": "account_guid",
    "contact": "contact_guid",
    "msdyn_workorder": "workorder_guid",
    "msdyn_project": "project_guid",
    "salesorder": "salesorder_guid",
    "quote": "quote_guid",
}

bridge = activities
for logical_name, key_column in TARGETS.items():
    bridge = bridge.withColumn(
        key_column,
        F.when(F.col("regarding_type") == F.lit(logical_name), F.col("regarding_guid")),
    )

bridge = (
    bridge.withColumn("activity_key", surrogate_key("activity_guid"))
    .withColumn("owner_key", surrogate_key("owner_guid"))
    .withColumn("is_regarding_resolved", F.col("regarding_guid").isNotNull())
)

bridge = fail_if_empty(bridge, "bridge_activity")
bridge = assert_unique(bridge, ["activity_guid"], "bridge_activity")

write_silver(bridge, "bridge_activity")
print(f"bridge_activity written — {bridge.count()} rows")

# ---- CELL ----
# Coverage report.
#
# Activities regarding an entity type not in TARGETS are unreachable from any pack model.
# During the first build, every unhandled type with meaningful volume is a decision: add
# it, or document that it is out of scope.

unhandled = (
    activities.where(F.col("regarding_guid").isNotNull())
    .where(~F.col("regarding_type").isin(list(TARGETS.keys())))
    .groupBy("regarding_type")
    .count()
    .orderBy(F.desc("count"))
)

if not unhandled.isEmpty():
    print("Activity target types NOT handled by the bridge:")
    unhandled.show(truncate=False)
    print("  Decide per type during the first build: add to TARGETS, or document as out of scope.")

orphan_count = activities.where(F.col("regarding_guid").isNull()).count()
print(f"Activities with no regarding record: {orphan_count} (expected — not all activities relate to a record)")
