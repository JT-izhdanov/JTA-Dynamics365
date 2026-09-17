"""
24 — Silver conformance: date dimension

Produces silver.dim_date with the CUSTOMER'S fiscal calendar.

WHY THIS MATTERS: a calendar-year date dimension is useless to a business that closes in
June. Fiscal period is a per-customer configuration input, not a constant, and getting it
wrong invalidates every period-over-period metric in every pack.

THE OTHER TRAP: Dataverse stores datetimes in UTC, but behavior differs by column —
user-local, date-only, and timezone-independent columns all exist. Time zone handling is a
PER-COLUMN decision, not a global one. Getting it wrong shifts a day's activity into the
wrong day and surfaces as reports that "don't tie" around month boundaries.

See docs/architecture/conformance-layer.md#7-deterministic-keys-and-conformed-dates

DRAFT — never executed. See platform/README.md.
"""

# ---- CELL ----

from pyspark.sql import functions as F

from _common import assert_unique, load_config, spark_session, write_silver

CONFIG_PATH = "/lakehouse/default/Files/config/customer.yaml"

spark = spark_session()
config = load_config(CONFIG_PATH)

fiscal = config["fiscal_calendar"]
START_DATE = fiscal["dimension_start_date"]        # e.g. "2018-01-01"
END_DATE = fiscal["dimension_end_date"]            # e.g. "2032-12-31"
FISCAL_YEAR_START_MONTH = fiscal["year_start_month"]  # 1 = January, 7 = July
FISCAL_YEAR_NAMING = fiscal["year_naming"]         # "starting" or "ending"
REPORTING_TIME_ZONE = config["locale"]["reporting_time_zone"]

print(
    f"dim_date {START_DATE} to {END_DATE} | fiscal year starts month "
    f"{FISCAL_YEAR_START_MONTH} | named by year {FISCAL_YEAR_NAMING} | "
    f"reporting time zone {REPORTING_TIME_ZONE}"
)

# ---- CELL ----
# Calendar spine.

days = spark.sql(
    f"SELECT explode(sequence(to_date('{START_DATE}'), to_date('{END_DATE}'), interval 1 day)) AS date"
)

# ---- CELL ----
# Fiscal attributes.
#
# Fiscal year offset: months on or after the start month belong to the fiscal year that
# begins in this calendar year.

offset_month = ((F.month("date") - F.lit(FISCAL_YEAR_START_MONTH)) % F.lit(12)) + F.lit(1)

fiscal_year_starting = F.when(
    F.month("date") >= F.lit(FISCAL_YEAR_START_MONTH), F.year("date")
).otherwise(F.year("date") - F.lit(1))

# A July-start fiscal year spanning 2025-2026 is called "FY2025" by some organizations and
# "FY2026" by others. Both are common; neither is inferable. Hence the config value.
fiscal_year = (
    fiscal_year_starting
    if FISCAL_YEAR_NAMING == "starting"
    else fiscal_year_starting + F.lit(1)
)

dim_date = (
    days.withColumn("date_key", F.date_format("date", "yyyyMMdd").cast("int"))
    .withColumn("calendar_year", F.year("date"))
    .withColumn("calendar_quarter", F.quarter("date"))
    .withColumn("calendar_month", F.month("date"))
    .withColumn("calendar_month_name", F.date_format("date", "MMMM"))
    .withColumn("calendar_year_month", F.date_format("date", "yyyy-MM"))
    .withColumn("day_of_month", F.dayofmonth("date"))
    .withColumn("day_of_week", F.dayofweek("date"))
    .withColumn("day_name", F.date_format("date", "EEEE"))
    .withColumn("week_of_year", F.weekofyear("date"))
    .withColumn("is_weekend", F.dayofweek("date").isin(1, 7))
    .withColumn("fiscal_year", fiscal_year)
    .withColumn("fiscal_month_number", offset_month)
    .withColumn("fiscal_quarter", ((offset_month - F.lit(1)) / F.lit(3)).cast("int") + F.lit(1))
    .withColumn("fiscal_year_label", F.concat(F.lit("FY"), F.col("fiscal_year").cast("string")))
    .withColumn(
        "fiscal_period_label",
        F.concat(
            F.col("fiscal_year_label"),
            F.lit("-P"),
            F.lpad(F.col("fiscal_month_number").cast("string"), 2, "0"),
        ),
    )
    .withColumn("month_start_date", F.trunc("date", "month"))
    .withColumn("month_end_date", F.last_day("date"))
    .withColumn("is_month_end", F.col("date") == F.last_day("date"))
    # Relative flags support "current period" report defaults without DAX gymnastics.
    .withColumn("is_today", F.col("date") == F.current_date())
    .withColumn("is_past", F.col("date") < F.current_date())
    .withColumn("days_from_today", F.datediff("date", F.current_date()))
)

dim_date = assert_unique(dim_date, ["date_key"], "dim_date")
write_silver(dim_date, "dim_date")
print(f"dim_date written — {dim_date.count()} rows")

# ---- CELL ----
# TODO — holiday and working-day calendar.
#
# Required by any metric measured in BUSINESS hours or working days. For Sales that is
# time-in-stage, days-to-close, and activity response time — a velocity metric that
# silently counts weekends is wrong in a way sales managers notice immediately.
#
# Holidays are customer-specific and often regional. Options:
#   - source from the customer's HR or scheduling system
#   - source from Dataverse calendar/holiday configuration if maintained
#     (# VERIFY: whether the customer actually maintains it — many do not)
#   - accept a configured list in customer.yaml
#
# Until this exists, business-hours metrics must either be calendar-hours (and labelled as
# such in metrics.yaml) or deferred. Do not quietly present calendar hours as business
# hours — an SLA metric that ignores weekends is wrong in a way customers notice
# immediately.

# ---- CELL ----
# NOTE — time zone handling is per-column, not global.
#
# Dataverse datetime columns come in several behaviors (user-local, date-only,
# timezone-independent), and the correct handling differs for each. There is deliberately
# no global conversion applied here.
#
# Each Silver fact build decides, per date column, whether to convert from UTC to
# REPORTING_TIME_ZONE before deriving date_key. Document the decision per column in the
# pack's source-tables.md.
#
# Symptom of getting this wrong: totals that tie for a month but not for its first or last
# day. It is the most common cause of "the numbers don't match" in UAT.
