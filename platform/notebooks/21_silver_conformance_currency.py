"""
21 — Silver conformance: currency normalization

Produces silver.dim_currency and the helpers Silver fact builds use to expose money
unambiguously.

WHY THIS MATTERS: Dataverse stores money twice — in the transaction currency and in the
organization's base currency — with the exchange rate captured ON THE RECORD at write
time. Reporting across currencies without understanding this produces wrong numbers that
look entirely plausible, which is the worst kind of wrong.

THE TRAP: the rate on the record is the rate at write time, not today's rate. That is
usually correct for financial reporting and usually wrong for pipeline comparison. The
choice must be deliberate per metric and documented in packs/<pack>/metrics.yaml.

See docs/architecture/conformance-layer.md#2-currency-normalization

DRAFT — never executed. See platform/README.md.
"""

# ---- CELL ----

from pyspark.sql import DataFrame, functions as F

from _common import assert_unique, bronze, fail_if_empty, load_config, spark_session, surrogate_key, write_silver

CONFIG_PATH = "/lakehouse/default/Files/config/customer.yaml"

spark = spark_session()
config = load_config(CONFIG_PATH)

BASE_CURRENCY = config["currency"]["base_iso_code"]
IS_MULTI_CURRENCY = config["currency"]["multi_currency"]

print(f"Base currency: {BASE_CURRENCY} | multi-currency: {IS_MULTI_CURRENCY}")

# ---- CELL ----
# dim_currency
#
# VERIFY column names against a live environment.

currency = bronze(spark, "transactioncurrency").select(
    F.col("transactioncurrencyid").alias("currency_guid"),
    F.col("isocurrencycode").alias("currency_iso_code"),
    F.col("currencyname").alias("currency_name"),
    F.col("currencysymbol").alias("currency_symbol"),
    F.col("exchangerate").alias("current_exchange_rate"),
    F.col("currencyprecision").alias("currency_precision"),
)

dim_currency = (
    currency.withColumn("currency_key", surrogate_key("currency_guid"))
    .withColumn("is_base_currency", F.col("currency_iso_code") == F.lit(BASE_CURRENCY))
)

dim_currency = fail_if_empty(dim_currency, "dim_currency")
dim_currency = assert_unique(dim_currency, ["currency_guid"], "dim_currency")

write_silver(dim_currency, "dim_currency")
print(f"dim_currency written — {dim_currency.count()} rows")

if dim_currency.where(F.col("is_base_currency")).isEmpty():
    raise ValueError(
        f"No currency matches the configured base ISO code '{BASE_CURRENCY}'. "
        "Correct customer config before continuing — every money metric depends on it."
    )

# ---- CELL ----
# Normalization helper for Silver fact builds.


def normalize_money(df: DataFrame, columns: list[str]) -> DataFrame:
    """Expose transaction and base amounts explicitly and unambiguously.

    Dataverse convention: `estimatedvalue` is the transaction-currency amount and
    `estimatedvalue_base` is the base-currency amount, maintained by the platform.

    Rules applied here:
      - Both are surfaced, named `_txn` and `_base`. Never one without the other.
      - NEVER silently convert. If a base amount is absent, it stays NULL and surfaces as
        a gap rather than being computed from a rate that may not apply.
      - The report packs default to BASE amounts. A report that is explicitly about a
        single market may use transaction amounts, and must say so.

    # VERIFY: the `_base` suffix convention holds for standard money columns. Custom money
    # columns and some solution-specific columns may differ — confirm per column rather
    # than assuming.
    """
    for column in columns:
        base_column = f"{column}_base"
        df = df.withColumnRenamed(column, f"{column}_txn")
        if base_column in df.columns:
            df = df.withColumnRenamed(base_column, f"{column}_base")
        else:
            print(
                f"  NOTE no base-currency column for '{column}'. Leaving NULL rather than "
                "converting — investigate during the first build."
            )
            df = df.withColumn(f"{column}_base", F.lit(None).cast("decimal(38,4)"))
    return df


# ---- CELL ----
# Single-currency shortcut check.
#
# Most customers are single-currency. Confirming it early removes a large class of
# reconciliation risk — and confirming the opposite raises the care required in Sprint 2
# metric reconciliation considerably.

distinct_in_use = (
    bronze(spark, "opportunity")
    .select("transactioncurrencyid")
    .distinct()
    .count()
)
print(f"Distinct currencies in use on opportunity: {distinct_in_use}")

if distinct_in_use > 1 and not IS_MULTI_CURRENCY:
    raise ValueError(
        "Config declares single-currency but multiple transaction currencies are in use. "
        "Correct the config — proceeding would produce money metrics that silently mix "
        "currencies."
    )

# ---- CELL ----
# TODO — exchange rate history, if required.
#
# Dataverse keeps the CURRENT rate on transactioncurrency and the AT-WRITE-TIME rate on
# each record. Neither gives a rate-as-of-any-date series.
#
# If a customer needs constant-currency comparison ("what would last year look like at
# today's rates?"), that needs a rate history table, which Dataverse does not provide.
# It would have to be sourced externally and is ADDITIONAL DEVELOPMENT, not packaged
# scope. Do not promise constant-currency reporting without scoping it.
