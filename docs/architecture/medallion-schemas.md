# Medallion schema reference — Bronze, Silver, Gold

The physical schema contract for the JourneyTeam Analytics platform: every table, its
grain, its columns, and its keys, across all three medallion layers.

**Audience:** the data engineer building the notebooks, the BI developer building the
semantic model, and the reviewer approving either.

---

## 0. What this document is, and is not

| | |
|---|---|
| **This document owns** | Physical table and column names, grain, keys, data types, nullability |
| **It does not own** | *Why* the layer exists, naming conventions, orchestration, refresh cadence, measure definitions |

Rationale lives elsewhere and is not restated here:

| For | Read |
|---|---|
| Why the conformance layer is the IP | [`conformance-layer.md`](conformance-layer.md) |
| Layer naming, orchestration, refresh | [`medallion-design.md`](medallion-design.md) |
| Why snapshots exist and cannot be backfilled | [`snapshot-and-history.md`](snapshot-and-history.md) |
| Dimension inventory and SCD rationale | [`../../packs/_shared/conformed-dimensions.md`](../../packs/_shared/conformed-dimensions.md) |
| Sales pack design decisions | [`../../packs/sales/technical-design.md`](../../packs/sales/technical-design.md) |
| What each measure means | [`../../packs/sales/metrics.yaml`](../../packs/sales/metrics.yaml) |

### Status legend

Every table below carries one of these. **Read it before building against the table.**

| Marker | Meaning |
|---|---|
| **BUILT** | A notebook emits these columns today. Names below are read from the notebook source, so they are accurate to the code — but the code has never been executed |
| **SPECIFIED** | Designed but no notebook exists. Column names are a design proposal |
| **VERIFY** | Depends on a Dataverse or Link to Fabric behaviour that has not been confirmed |

**Nothing in this document has been executed against a live Fabric workspace.** Only the
Bronze `opportunity` table has been profiled against real data
([`../bronze-profiling/opportunity.md`](../bronze-profiling/opportunity.md)).

---

## 1. Conventions

### 1.1 Naming

| Layer | Rule |
|---|---|
| Bronze | Dataverse logical names, unchanged. They are Microsoft's, and the shortcut defines them |
| Silver | `snake_case`, prefixed by role: `dim_`, `fact_`, `lkp_`, `bridge_` |
| Gold | Conformed dimensions keep their Silver name; pack objects prefixed `sales__` |

The double underscore in `sales__fact_opportunity` separates pack from object so the
object name keeps its own `dim_` / `fact_` reading.

### 1.2 Column suffixes

| Suffix | Meaning | Type |
|---|---|---|
| `_guid` | The Dataverse GUID, retained for traceability | `string` |
| `_key` | Surrogate key, used for model relationships | `string` — see §6.1 |
| `_txn` | Money in the transaction currency | `decimal(38,4)` |
| `_base` | Money in the organization's base currency | `decimal(38,4)` |
| `_utc` | Timestamp left in UTC, not converted | `timestamp` |
| `_date_key` | Foreign key into `dim_date` | `int`, `yyyyMMdd` |
| `is_` | Boolean flag | `boolean` |

### 1.3 Types

Spark / Delta types throughout. Money is `decimal(38,4)` and never `double` — floating
point money produces totals that disagree with the source app by pennies, which is worse
than disagreeing by thousands because nobody believes the explanation.

### 1.4 Rules that apply to every Silver table

Enforced by helpers in [`_common.py`](../../platform/notebooks/_common.py):

1. **Grain asserted before write** — `assert_unique(df, keys, description)`. A duplicate
   dimension key fans out every fact join silently.
2. **Empty output fails the run** — `fail_if_empty(df, description)`. A silent partial
   success becomes a wrong number in a report three weeks later.
3. **Choice labels joined from `lkp_choice_label`**, left join, never a hard-coded `CASE`.
4. **Money exposed as `_txn` and `_base` pairs**, never silently converted.
5. **Idempotent writes** — overwrite mode, except snapshot appends.

---

## 2. Bronze

**Status: BUILT (validation only).** Bronze is a Link to Fabric shortcut. Microsoft
defines the schema; JourneyTeam only validates it.

### 2.1 Contract

| | |
|---|---|
| Schema | `jta_lakehouse.bronze` |
| Written by | Microsoft (Link to Fabric) |
| Writable by us | **No.** Never write to Bronze |
| Naming | Dataverse logical names, lowercase |
| Validated by | [`10_bronze_shortcut_validation.py`](../../platform/notebooks/10_bronze_shortcut_validation.py) |

All JourneyTeam logic must be reproducible from Bronze by re-running notebooks, so that
recreating the shortcut loses nothing but time.

### 2.2 Table inventory

21 Dataverse tables. Grouped and conditioned in
[`../../packs/sales/source-tables.md`](../../packs/sales/source-tables.md) and configured
in `platform/config/customer.example.yaml` under `tables.required` / `tables.optional`.

| Group | Tables |
|---|---|
| Conformance layer | `account`, `contact`, `systemuser`, `team`, `businessunit`, `transactioncurrency`, `activitypointer` |
| Sales pack | `lead`, `opportunity`, `opportunityproduct`, `quote`, `quotedetail`, `salesorder`, `salesorderdetail` |
| Choice-label metadata | `optionsetmetadata`, `globaloptionsetmetadata`, `stringmap` — link all three, expect one |
| Conditional | `product`, `territory`, `pricelevel`, `bookableresource` |

> `quotedetail` and `salesorderdetail` are in the source mapping but missing from both
> config lists, so notebook 10 does not currently gate on them. `pricelevel` is in the
> mapping but in neither list; `bookableresource` is in config but not the mapping. See
> §8.6.

### 2.3 Sink columns present on every Bronze table

**Status: BUILT — confirmed in the live JTP export.** These are added by Link to Fabric,
not by Dataverse, and they appear on every entity.

| Column | Type | Meaning |
|---|---|---|
| `Id` | `string` | Present alongside the entity's own `<entity>id`. `VERIFY` whether always identical |
| `SinkCreatedOn` | `timestamp` | When the row landed in Fabric — **not** a business timestamp |
| `SinkModifiedOn` | `timestamp` | As above |
| `PartitionId` | `string` | The `createdon` **year**. The table is year-partitioned |
| `IsDelete` | `boolean` | Soft-delete flag. NULL on live rows |
| `versionnumber` | `bigint` | Dataverse row version |
| `msft_datastate` | `string` | NULL throughout; purpose unconfirmed |

**Two read rules follow, and they are not optional:**

1. **Every Bronze read filters `IsDelete`.** Omitting it silently includes deleted records
   in every metric. *No notebook currently does this* — see §8.1.
2. **`PartitionId` is the cheap filter.** Queries scoped to recent created-years hit few
   partitions; anything spanning full history scans all of them.

### 2.4 Lookup column shape

**Status: BUILT — confirmed in the live JTP export.** Every lookup arrives as a triple:

| Pattern | Example | Purpose |
|---|---|---|
| `<column>` | `customerid` | The target GUID |
| `<column>_entitytype` | `customerid_entitytype` = `"account"` | **The polymorphic discriminator** |
| `<column>name` | `customeridname` | Denormalized display name, as of last write |

This resolves polymorphic lookups inline. The original design assumed a join to
`TargetMetadata`; that join is not needed.

Denormalized names make labels free for a first cut, but they are snapshots taken at last
write and carry no hierarchy — `dim_owner` is still required for manager chain, team and
RLS.

A `<column>yominame` phonetic twin exists for each and is NULL throughout. Ignore it.

### 2.5 Choices

**Status: BUILT — confirmed.** Choices arrive as raw integers with no labels.
`statecode` = `2`. `jt_backlogtype` = `206360000`. Value ranges observed at JTP:
`2063600xx` for JT custom choices, `1000000xx` for Microsoft Sales choices.

Nothing in a data table resolves a label, which is why §3.2 exists and why its metadata
source is the platform's largest open item.

---

## 3. Silver

| | |
|---|---|
| Schema | `jta_lakehouse.silver` |
| Written by | JourneyTeam notebooks `2x` (conformance), `3x` (snapshots), `5x` (pack) |
| Purpose | **"Is this data correct and complete?"** Conformance, history, keys, cleansing |
| Pack-aware | No. Silver is pack-agnostic, including the dimensions a pack notebook happens to build |

### 3.1 Inventory

| Table | Status | Built by | Grain | SCD |
|---|---|---|---|---|
| `lkp_choice_label` | **BUILT** | `20_` | table × column × value | n/a |
| `dim_currency` | **BUILT** | `21_` | currency | Type 1 |
| `dim_owner` | **BUILT** (initial load only) | `22_` | owner version | **SCD2** — not yet implemented |
| `bridge_activity` | **BUILT** | `23_` | activity | n/a |
| `dim_date` | **BUILT** | `24_` | day | n/a |
| `fact_opportunity_snapshot` | **BUILT** | `30_` | opportunity × snapshot_date | append-only |
| `ops_bronze_validation_log` | **BUILT** | `10_` | table × validation run | append-only |
| `dim_customer` | SPECIFIED | `5x_` | account version | **SCD2** |
| `dim_contact` | SPECIFIED | `5x_` | contact | Type 1 |
| `dim_product` | SPECIFIED | `5x_` | product version | **SCD2** |
| `dim_territory` | SPECIFIED | `5x_` | territory | Type 1 |
| `dim_resource` | SPECIFIED | `5x_` | resource | Type 1 |
| `dim_opportunity` | SPECIFIED | `50_` | opportunity | Type 1 |
| `fact_opportunity` | SPECIFIED | `50_` | opportunity | transaction |
| `fact_opportunity_product` | SPECIFIED | `50_` | opportunity line | transaction |
| `fact_lead` | SPECIFIED | `50_` | lead | transaction |
| `fact_quote` | SPECIFIED | `50_` | quote | transaction |
| `fact_order` | SPECIFIED | `50_` | order | transaction |
| `fact_stage_duration` | SPECIFIED | `51_` | opportunity × stage entry | derived |
| `fact_forecast_movement` | SPECIFIED | `51_` | opportunity × snapshot_date | derived |

---

### 3.2 `lkp_choice_label` — BUILT

One conformed lookup resolving Dataverse choice integers to labels. Every Silver build
joins to it.

**Grain:** `table_name` × `column_name` × `option_value`, asserted unique.
**Source:** whichever of `stringmap`, `optionsetmetadata`, `globaloptionsetmetadata`
Bronze provides. Multiple sources are unioned and deduplicated.

| Column | Type | Null | Note |
|---|---|---|---|
| `table_name` | `string` | No | Lowercased Dataverse logical name |
| `column_name` | `string` | No | Lowercased column logical name |
| `option_value` | `int` | No | The raw Dataverse integer |
| `option_label` | `string` | No | Rows with a NULL label are dropped at build |

**Join rule:** always a **left** join. An unmapped value must surface as NULL and be
investigated, never silently drop the fact row.

> **VERIFY — the platform's largest open item.** The column names notebook 20 reads from
> each candidate source are assumptions, documented in the notebook's own VERIFY block.
> Inspect the real schema before running it. A wrong label mapping is worse than no
> mapping, because it looks right.

---

### 3.3 `dim_date` — BUILT

Built from the customer's fiscal calendar, which is configuration, not a constant.

**Grain:** one row per day, `date_key` asserted unique.
**Range:** `fiscal_calendar.dimension_start_date` to `dimension_end_date` from config.

| Column | Type | Note |
|---|---|---|
| `date` | `date` | The day itself |
| `date_key` | `int` | `yyyyMMdd`. The FK every fact carries |
| `calendar_year` | `int` | |
| `calendar_quarter` | `int` | 1–4 |
| `calendar_month` | `int` | 1–12 |
| `calendar_month_name` | `string` | Full month name |
| `calendar_year_month` | `string` | `yyyy-MM` |
| `day_of_month` | `int` | |
| `day_of_week` | `int` | Spark `dayofweek`: 1 = Sunday |
| `day_name` | `string` | |
| `week_of_year` | `int` | |
| `is_weekend` | `boolean` | Saturday or Sunday |
| `fiscal_year` | `int` | Respects `year_start_month` and `year_naming` |
| `fiscal_year_label` | `string` | `FY2026` |
| `fiscal_quarter` | `int` | 1–4, offset from the fiscal start month |
| `fiscal_month_number` | `int` | 1–12, offset from the fiscal start month |
| `fiscal_period_label` | `string` | `FY2026-P07` |
| `month_start_date` | `date` | |
| `month_end_date` | `date` | |
| `is_month_end` | `boolean` | |
| `is_today` | `boolean` | **Computed at build time** — stale unless rebuilt daily |
| `is_past` | `boolean` | As above |
| `days_from_today` | `int` | As above |

**`year_naming` is not inferable.** A July-start fiscal year spanning 2025–2026 is
"FY2025" to some organizations and "FY2026" to others. Both are common. Ask at kickoff.

**Not yet built: the holiday and working-day calendar.** Any metric measured in business
hours — time-in-stage, days-to-close, activity response time — is calendar-hours until it
exists, and must be labelled as such via `business_hours` in `metrics.yaml`. A velocity
metric that silently counts weekends is wrong in a way sales managers notice immediately.

---

### 3.4 `dim_currency` — BUILT

**Grain:** one row per currency, `currency_guid` asserted unique.
**Source:** `bronze.transactioncurrency`.

| Column | Type | Source | Note |
|---|---|---|---|
| `currency_key` | `string` | derived | `surrogate_key(currency_guid)` |
| `currency_guid` | `string` | `transactioncurrencyid` | |
| `currency_iso_code` | `string` | `isocurrencycode` | |
| `currency_name` | `string` | `currencyname` | |
| `currency_symbol` | `string` | `currencysymbol` | Used for model formatting |
| `current_exchange_rate` | `decimal` | `exchangerate` | **Today's rate, not the rate at write time** |
| `currency_precision` | `int` | `currencyprecision` | |
| `is_base_currency` | `boolean` | derived | `currency_iso_code == currency.base_iso_code` |

**The build fails** if no currency matches the configured base ISO code, and fails if
config declares single-currency while `opportunity` shows multiple transaction currencies.

**The trap:** the rate stored on a Dataverse *record* is the rate at write time, not the
rate in `current_exchange_rate`. Usually correct for financial reporting; usually wrong
for pipeline comparison. Every money metric declares its `currency_basis` in
`metrics.yaml` for this reason.

**Not available:** a rate-as-of-any-date series. Dataverse has the current rate here and
the at-write-time rate on each record, and neither gives a history. Constant-currency
comparison would need an external rate source and is additional development, not packaged
scope.

---

### 3.5 `dim_owner` — BUILT (initial load only)

Covers **both users and teams** — records can be owned by either, and omitting teams loses
owner attribution on team-owned records entirely.

**Grain (intended):** one row per owner *version*.
**Grain (as built):** one row per owner. `assert_unique(["owner_guid"])` in notebook 22 is
labelled "initial load" and will fail once SCD2 lands.
**Source:** `bronze.systemuser` ∪ `bronze.team`, joined to flattened `bronze.businessunit`.

| Column | Type | Source | Note |
|---|---|---|---|
| `owner_key` | `string` | derived | `surrogate_key(owner_guid)`. **Must become per-version** — §8.2 |
| `owner_guid` | `string` | `systemuserid` / `teamid` | |
| `owner_name` | `string` | `fullname` / `name` | The slicer column. Spans a person's versions |
| `owner_email` | `string` | `internalemailaddress` | NULL for teams |
| `owner_type` | `string` | literal | `'User'` or `'Team'` |
| `is_disabled` | `boolean` | `isdisabled` | NULL for teams |
| `territory_guid` | `string` | `systemuser.territoryid` | NULL for teams |
| `business_unit_guid` | `string` | `businessunitid` | Join key to the BU hierarchy |
| `business_unit_name` | `string` | `businessunit.name` | |
| `bu_level_1` … `bu_level_N` | `string` | derived | N = `hierarchy.business_unit_levels`. **Leaf-to-root** — §8.3 |
| `manager_level_1` … `manager_level_N` | `string` | derived | N = `hierarchy.manager_levels`. NULL for teams |
| `effective_from` | `date` | derived | SCD2 |
| `effective_to` | `date` | derived | SCD2. NULL on the current row |
| `is_current` | `boolean` | derived | SCD2 |

This one artifact serves two purposes — the reporting dimension and the source of the RLS
model. That is deliberate; see [`security-and-rls.md`](security-and-rls.md).

**The manager chain requires `systemuser.parentsystemuserid` to be maintained.** Notebook
22 reports the fill rate and warns below 50%. If sparse, manager-based RLS and manager
rollup reporting are **not viable**, and that is a scoping finding to raise, not something
to engineer around.

**At JTP there is one flat business unit and no owning team**, so `bu_level_2` and above
will be NULL and the BU path carries no information. The AE / SAM / SDR segment the
business actually reports on is not on `opportunity` and not in `owningteam` — sourcing it
is open decision **D11**, and it blocks the Performance, Leaderboard and Scorecard pages.

---

### 3.6 `bridge_activity` — BUILT

One row per activity with a typed nullable key per target entity, resolving the
polymorphic `regardingobjectid`. Lets a model join activities with a normal relationship
instead of re-solving polymorphism in DAX.

**Grain:** one row per activity, `activity_guid` asserted unique.
**Source:** `bronze.activitypointer`, the base table for every activity type.

| Column | Type | Source | Note |
|---|---|---|---|
| `activity_key` | `string` | derived | `surrogate_key(activity_guid)` |
| `activity_guid` | `string` | `activityid` | |
| `activity_subject` | `string` | `subject` | |
| `activity_type_code` | `int` | `activitytypecode` | Raw integer, retained |
| `activity_type` | `string` | `lkp_choice_label` | Resolved label |
| `regarding_guid` | `string` | `regardingobjectid` | NULL where the activity relates to nothing |
| `regarding_type` | `string` | `regardingobjecttypecode` | **VERIFY** — §8.4 |
| `is_regarding_resolved` | `boolean` | derived | `regarding_guid IS NOT NULL` |
| `opportunity_guid` | `string` | derived | Populated where `regarding_type = 'opportunity'` |
| `lead_guid` | `string` | derived | |
| `account_guid` | `string` | derived | |
| `contact_guid` | `string` | derived | |
| `salesorder_guid` | `string` | derived | |
| `quote_guid` | `string` | derived | |
| `owner_guid` | `string` | `ownerid` | |
| `owner_key` | `string` | derived | `surrogate_key(owner_guid)`. **Breaks under SCD2** — §8.2 |
| `state_code` | `int` | `statecode` | Raw, unlabelled |
| `status_code` | `int` | `statuscode` | Raw, unlabelled |
| `is_outgoing` | `int` | `directioncode` | **Misnamed** — carries the raw code, not a boolean |
| `created_on_utc` | `timestamp` | `createdon` | Not converted |
| `modified_on_utc` | `timestamp` | `modifiedon` | Not converted |
| `scheduled_start_utc` | `timestamp` | `scheduledstart` | |
| `scheduled_end_utc` | `timestamp` | `scheduledend` | |
| `actual_start_utc` | `timestamp` | `actualstart` | |
| `actual_end_utc` | `timestamp` | `actualend` | |
| `actual_duration_minutes` | `int` | `actualdurationminutes` | |

**One typed key column per target, not a single generic key.** The target list is Sales
scope. Add a target only when the table is actually in the Bronze set — a column for an
entity that is not shortcut is dead weight in the bridge.

Notebook 23 reports activity target types *not* covered. During the first build, every
unhandled type with meaningful volume is a decision: add it, or document it as out of
scope.

**The bridge stays polymorphic on purpose.** Cross-app packs will be built on exactly this
artifact, so collapsing it to a Sales-only shape now is a rebuild later.

---

### 3.7 `fact_opportunity_snapshot` — BUILT

The differentiating capability of the offering. Dataverse is a current-state store; this
table is the only reason point-in-time pipeline exists.

**Grain:** opportunity × `snapshot_date`.
**Write mode:** append-only, partitioned by `snapshot_date`, `mergeSchema` enabled to
tolerate columns added mid-history.
**Idempotency:** enforced by *refusal*. If the date is already present the run skips it —
writing a date twice double-counts every trend, and restating it destroys the record.

**Capture rule, and the reason growth stays bounded:** open records are snapshotted daily;
closed records are captured once and then excluded. A closed opportunity will not change
again.

| Column | Type | Note |
|---|---|---|
| `snapshot_date` | `date` | Partition column. Fixed UTC date from `utc_today()` |
| `snapshot_loaded_at_utc` | `timestamp` | When the row was written |
| *…Dataverse columns* | *as source* | **Raw logical names, not conformed** — §8.5 |

Columns captured from `opportunity`, deliberately narrow: `opportunityid`, `name`,
`statecode`, `statuscode`, `salesstagecode`, `stepname`, `estimatedvalue`,
`estimatedvalue_base`, `actualvalue`, `actualvalue_base`, `transactioncurrencyid`,
`estimatedclosedate`, `actualclosedate`, `closeprobability`, `ownerid`,
`owningbusinessunit`, `customerid`, `createdon`, `modifiedon`.

A column absent at a customer's solution version is omitted with a note rather than
failing the run — history accumulating for the rest matters more.

> **`salesstagecode` and `stepname` carry no stage at JTP.** `salesstagecode` is `1` on
> every row and `stageid` / `processid` / `traversedpath` are all NULL, so BPF stage
> history does not exist. Stage lives on the custom `jt_sales_stage` column, which **is
> not in the snapshot spec**. Until it is added, `fact_stage_duration` has no source.
> Decision D4.

**Completeness checking is part of the build.** Notebook 30 compares distinct snapshot
dates against elapsed days and alerts on a gap. A snapshot job that silently stops loses
history without surfacing any error in any report — the failure mode is invisible until
someone asks a trend question months later.

---

### 3.8 `ops_bronze_validation_log` — BUILT

Operational, not analytical. Written by notebook 10 so reconciliation has a baseline and
an unexpected row-count drop is detectable across runs.

| Column | Type |
|---|---|
| `table_name` | `string` |
| `row_count` | `bigint` |
| `validated_at_utc` | `timestamp` |

---

### 3.9 Conformed dimensions — SPECIFIED

Built by the `5x` notebooks, which do not exist. **They are conformed, written to
`silver.dim_*`, and consumed by later packs — never `sales_dim_*`.** Reusability is
decided when a dimension is built, not when a second consumer appears.

#### `dim_customer` — SCD2, grain: account version

| Column | Source | Note |
|---|---|---|
| `customer_key` | derived | **Per version** |
| `customer_guid` | `account.accountid` | |
| `customer_name` | `account.name` | |
| `customer_number` | `account.accountnumber` | |
| `industry` | `account.industrycode` | Label via `lkp_choice_label` |
| `customer_type` | `account.customertypecode` | Label via lookup |
| `revenue_band` | derived from `account.revenue` | Bands are config |
| `employee_count` | `account.numberofemployees` | |
| `owner_key` | `account.ownerid` | |
| `territory_key` | `account.territoryid` | `VERIFY` — territory often lives here, not on opportunity |
| `parent_customer_guid` | `account.parentaccountid` | Hierarchy |
| `city`, `state`, `country` | address columns | `VERIFY` which address is authoritative |
| `effective_from`, `effective_to`, `is_current` | derived | SCD2 |

SCD2 tracked attributes: `customer_name`, `industry`, `owner_key`, `territory_key`,
`revenue_band`. An address change alone does not create a version.

#### `dim_contact` — Type 1, grain: contact

`contact_key`, `contact_guid`, `full_name`, `job_title`, `email_domain`,
`parent_customer_guid`, `owner_key`.

**`email_domain` is derived, and the full address is deliberately not carried.** Contact
email is PII with no analytic purpose in this pack.

#### `dim_product` — SCD2, grain: product version

`product_key`, `product_guid`, `product_number`, `product_name`, `product_category`
(`VERIFY` source — `product.subjectid` or a custom hierarchy), `product_type`,
`unit_group`, `default_price`, `is_active`, plus SCD2 columns.

**Write-in products have no `productid`.** `dim_product` carries a single
`product_key = -1` "Write-in / Unspecified" member and the line fact points at it, with
the free-text description as a degenerate attribute. Without this member, write-in lines
disappear from product analysis silently.

#### `dim_territory` — Type 1, grain: territory

`territory_key`, `territory_guid`, `territory_name`, `manager_key`, parent hierarchy if
maintained. **Frequently unpopulated** — if the fill rate is low, territory pages are
removed from the pack for that customer rather than shipped empty.

#### `dim_resource` — Type 1, grain: resource

Source is `bronze.bookableresource`. Exists because `jt_presalesresource` resolves to a
`bookableresource`, not a `systemuser` — a lookup that would otherwise join to `dim_owner`
and find nothing.

---

### 3.10 `dim_opportunity` — SPECIFIED

Opportunity *attributes*, separated from opportunity *measures*.

**Grain:** one row per opportunity. Type 1.

`opportunity_key`, `opportunity_guid`, `opportunity_name`, `conformed_status`,
`state_label`, `status_reason_label`, `sales_stage_label`, `rating_label`, `is_open`,
`is_won`, `is_lost`, `is_cancelled`, `created_date_key`, `estimated_close_date_key`,
`actual_close_date_key`, `customer_account_key`, `customer_contact_key`,
`customer_display_name`, `customer_party_type`, `owner_key`, `territory_key`,
`currency_key`.

**Why a dimension and not degenerate columns on the fact:** `fact_opportunity_product`
needs to slice by opportunity attributes. Without `dim_opportunity` the line fact would
join to the header *fact*, and fact-to-fact relationships are harder to reason about and
to secure. One dimension, two facts pointing at it, costs one small table.

#### Conformed status grouping

`statecode` and `statuscode` are both decoded and retained, plus a derived
`conformed_status` that every metric uses. **Raw integers are never exposed to Gold or the
semantic model.**

| `conformed_status` | Opportunity source |
|---|---|
| `Open` | `statecode` = 0 `VERIFY` |
| `Won` | `statecode` = 1 `VERIFY` |
| `Lost` | `statecode` = 2 with a loss status reason |
| `Cancelled` | `statecode` = 2 with a cancellation status reason — **decision D1** |

**At JTP, grouping must happen at `statuscode` grain, not `statecode`.** `statecode = 2`
mixes the out-of-the-box *Canceled* (`statuscode = 4`) with JourneyTeam's custom loss
reasons. Decision D1 — whether `Cancelled` is a form of `Lost` — changes the Win Rate
denominator materially and lives in one place in notebook 50 so the answer is a one-line
change.

#### Polymorphic customer resolution

`opportunity.customerid` points at **either an account or a contact**, discriminated by
`customerid_entitytype`:

```
customer_account_key   ← where customerid_entitytype = 'account'    (nullable)
customer_contact_key   ← where customerid_entitytype = 'contact'    (nullable)
customer_display_name  ← resolved name from whichever is populated
customer_party_type    ← 'Account' | 'Contact'
```

Reports slice on `dim_customer` and therefore **exclude contact-owned opportunities**.
Immaterial for a B2B customer; a significant hole for a B2C-shaped one. At JTP every
profiled row was `account`, so the risk is low — confirm with a full-table count.

If contact-owned opportunities exceed a few percent, the fix is a unified **party
dimension**, which is a conformed-dimension change affecting every pack and needs an ADR.
Do not solve it locally in the pack.

---

### 3.11 Fact tables — SPECIFIED

| Table | Grain | Key measures |
|---|---|---|
| `fact_opportunity` | one row per opportunity | `estimated_value_txn/_base`, `actual_value_txn/_base`, `budget_amount_txn/_base`, `close_probability`, `weighted_value_base`, `sales_cycle_days`, `days_since_last_activity`, `activity_count`, `age_bucket` |
| `fact_opportunity_product` | one row per line | `quantity`, `price_per_unit_txn/_base`, `extended_amount_txn/_base`, `is_price_overridden` |
| `fact_lead` | one row per lead | `estimated_value_base`, `is_qualified`, `days_to_qualify`, `qualifying_opportunity_key` |
| `fact_quote` | one row per quote | `total_amount_base`, `discount_amount_base`, `discount_percent`, `has_order` |
| `fact_order` | one row per order | `total_amount_base` |

Every fact also carries the dimension foreign keys in §5.3 and its own `_date_key`
columns.

**`weighted_value_base`, `sales_cycle_days`, `activity_count`, `days_since_last_activity`
and `age_bucket` are precomputed here, not in DAX.** Direct Lake does not support
calculated columns, and the architecture's own rule already puts shaping in Gold. Direct
Lake enforces it.

**Line totals may not sum to the header value.** Normal Dynamics behaviour, not a defect.
The two facts are kept in separate stars against `dim_opportunity`, and reports never
place header and line measures in the same visual without a note. At JTP
`isrevenuesystemcalculated` = 1 and `estimatedvalue` = `totallineitemamount`, so the lines
*are* the revenue source — `opportunityproduct` is load-bearing, not optional (decision
D8).

#### Time zone handling is per column

Dataverse stores datetimes in UTC and column behaviour varies (user-local, date-only,
timezone-independent), so there is deliberately **no global conversion**.

| Column | Treatment | Rationale |
|---|---|---|
| `createdon`, `modifiedon` | Convert UTC → `reporting_time_zone`, then derive `date_key` | User-local behaviour; users expect "created today" to match Dynamics |
| `estimatedclosedate` | Date-only, **no conversion** | `VERIFY` — if date-only, converting shifts it a day |
| `actualclosedate` | Date-only, **no conversion** | `VERIFY` — same |

Getting this wrong produces totals that tie for a month but not for its first or last day.
It is the most common cause of "the numbers don't match" in UAT.

---

### 3.12 Derived history — SPECIFIED

Built by notebook 51 from the snapshot fact. Precomputed rather than left to DAX because
comparing a row to its own prior snapshot in DAX is expensive and hard to read.

#### `fact_stage_duration`

**Grain:** one row per opportunity × stage entry. Built by comparing consecutive snapshot
rows per opportunity and emitting a row when the stage label changes.

`opportunity_key`, `stage_label`, `stage_sequence`, `entered_date_key`, `exited_date_key`,
`days_in_stage`, `is_current_stage`, `owner_key_asof`, `estimated_value_base_at_entry`.

Two limitations, both stated at handoff: daily granularity means two stage changes in one
day are indistinguishable, and the table is only as deep as snapshot history.

**Blocked at JTP until the stage column is added to the snapshot spec** (§3.7).

#### `fact_forecast_movement`

**Grain:** opportunity × snapshot_date, open opportunities only.

`snapshot_date_key`, `opportunity_key`, `estimated_close_date_key`,
`prior_estimated_close_date_key`, `close_date_moved_days`, `estimated_value_base`,
`prior_estimated_value_base`, `value_change_base`, `owner_key_asof`.

`close_date_moved_days > 0` is slippage.

#### As-of ownership

Notebook 51 stamps the **as-of owner version key** onto each snapshot row, resolving
`owner_guid` against `dim_owner` where `snapshot_date` falls between `effective_from` and
`effective_to`. **Resolved in Silver, never in DAX.**

A snapshot of last quarter's pipeline must respect who owned the record *then*.
`dim_owner` is SCD2 for exactly this reason, and RLS on historical rows falls out of it for
free.

---

## 4. Gold

| | |
|---|---|
| Schema | `jta_lakehouse.gold` |
| Written by | Notebook `40_` (conformed dimensions), `52_` (pack objects, not yet written) |
| Purpose | **"Is this data shaped for this business question?"** Star schemas, pack denormalization |

### 4.1 The rule Gold enforces

**Conformed dimensions are shared, not copied.** Gold exposes a **view** over the Silver
dimension. A pack never gets a physical copy.

A view cannot drift from its Silver source. A copy can, and a pack reading a stale
`dim_owner` produces numbers that disagree with another pack reading the live one — a
defect that is very hard to diagnose because both reports look internally consistent.

This is the rule most likely to be broken under delivery pressure, which is why notebook
40 enforces it in code rather than leaving it to discipline.

### 4.2 Inventory

| Gold object | Type | Status | Source |
|---|---|---|---|
| `dim_date` | view | **BUILT** | `silver.dim_date` |
| `dim_owner` | view | **BUILT** | `silver.dim_owner` — currently filtered, see §8.2 |
| `dim_currency` | view | **BUILT** | `silver.dim_currency` |
| `lkp_choice_label` | view | **BUILT** | `silver.lkp_choice_label` |
| `bridge_activity` | view | **BUILT** | `silver.bridge_activity` |
| `dim_customer` | view | BUILT, source SPECIFIED | `silver.dim_customer` |
| `dim_contact` | view | BUILT, source SPECIFIED | `silver.dim_contact` |
| `dim_product` | view | optional in `40_` | `silver.dim_product` |
| `dim_territory` | view | optional in `40_` | `silver.dim_territory` |
| `dim_resource` | view | optional in `40_` | `silver.dim_resource` |
| `dim_snapshot_date` | view | SPECIFIED | `silver.dim_date` filtered to dates where a snapshot exists |
| `sales__dim_opportunity` | table | SPECIFIED | `silver.dim_opportunity` |
| `sales__dim_lead_source` | table | SPECIFIED | Derived from `lead.leadsourcecode` labels |
| `sales__dim_age_bucket` | table | SPECIFIED | Bucket labels with an explicit sort order |
| `sales__fact_opportunity` | table | SPECIFIED | `silver.fact_opportunity` |
| `sales__fact_opportunity_product` | table | SPECIFIED | `silver.fact_opportunity_product` |
| `sales__fact_lead` | table | SPECIFIED | `silver.fact_lead` |
| `sales__fact_quote` | table | SPECIFIED | `silver.fact_quote` |
| `sales__fact_order` | table | SPECIFIED | `silver.fact_order` |
| `sales__fact_opportunity_snapshot` | table | SPECIFIED | `silver.fact_opportunity_snapshot` |
| `sales__fact_stage_duration` | table | SPECIFIED | `silver.fact_stage_duration` |
| `sales__fact_forecast_movement` | table | SPECIFIED | `silver.fact_forecast_movement` |
| `sales__sec_owner_scope` | table | SPECIFIED | RLS bridge, §4.4 |

`40_` fails the run if a required conformed dimension is absent from Silver, and skips a
pack-specific one with a note.

### 4.3 `dim_snapshot_date` — SPECIFIED

A **second date table**: a view over `dim_date` restricted to dates where a snapshot
exists, with an `asof_` prefix on display names.

The model needs two independent date pickers — "as of" (snapshot date) and "close date" or
"created date" (transaction dates). One `dim_date` related to both creates ambiguity and
forces `USERELATIONSHIP` into every measure.

Deliberately **not** marked as the model date table; time intelligence over it is not
needed, and marking it would create ambiguity. Because it contains only dates that exist,
the empty-date problem disappears.

### 4.4 `sales__sec_owner_scope` — SPECIFIED

The RLS bridge. **Grain: user × permitted owner version key.**

| Column | Type | Note |
|---|---|---|
| `user_principal_name` | `string` | Matched against `USERPRINCIPALNAME()` |
| `owner_key` | `string` | A `dim_owner` version the user may see |

Populated by expanding the configured security pattern over `dim_owner`. **Expansion
happens in Gold because it is inspectable, testable, and cheap to refresh.** Equivalent
DAX would be none of those, and complex DAX RLS is the usual cause of RLS performance
problems.

**Dataverse security does not follow data into OneLake.** Default visibility is
everything, so RLS is a build deliverable, not an option. The pattern **fails closed**: a
user with no bridge rows sees nothing.

**The SQL endpoint bypasses RLS entirely.** Anyone with Gold access reads unfiltered.
`sql_endpoint_audience` in config governs who gets it; it is not a substitute for a viewer
role.

---

## 5. Cross-layer contracts

### 5.1 Key flow

```
Bronze                    Silver                         Gold
─────────────────────     ────────────────────────       ──────────────────────
opportunityid        →    opportunity_guid          →    (hidden)
                          opportunity_key           →    opportunity_key   ← relationships
ownerid              →    owner_guid
                          owner_key (per version)   →    owner_key
createdon (UTC)      →    created_date_key (int)    →    created_date_key  → dim_date
estimatedvalue       →    estimated_value_txn
estimatedvalue_base  →    estimated_value_base
statecode (int)      →    conformed_status (string) →    conformed_status
```

Raw integers never reach Gold. GUIDs reach Gold but are hidden in the model.

### 5.2 What belongs in which layer

| Layer | Answers | A defect here looks like |
|---|---|---|
| Silver | "Is this data correct and complete?" | Wrong labels, missing rows, wrong currency |
| Gold | "Is this data shaped for this question?" | Wrong grain, unusable shape |
| Semantic model | "How is this measured?" | A wrong number from correct data |

When a defect appears, that hierarchy decides where it gets fixed. No business logic
belongs in Gold that the model should own, and no data correction belongs in the model
that Silver should own.

### 5.3 Semantic model relationships

All single-direction. **No bidirectional filtering anywhere** — it is the usual cause of
ambiguous-path errors and of RLS leaking across tables.

| Fact | Column | To | Active |
|---|---|---|---|
| `sales__fact_opportunity` | `opportunity_key` | `sales__dim_opportunity` | Yes |
| | `created_date_key` | `dim_date` | **Yes** |
| | `estimated_close_date_key` | `dim_date` | No |
| | `actual_close_date_key` | `dim_date` | No |
| | `owner_key` | `dim_owner` | Yes |
| | `customer_key` | `dim_customer` | Yes |
| | `currency_key` | `dim_currency` | Yes |
| | `territory_key` | `dim_territory` | Yes |
| `sales__fact_opportunity_product` | `opportunity_key` | `sales__dim_opportunity` | Yes |
| | `product_key` | `dim_product` | Yes |
| `sales__fact_opportunity_snapshot` | `snapshot_date_key` | `dim_snapshot_date` | Yes |
| | `opportunity_key` | `sales__dim_opportunity` | Yes |
| | `owner_key_asof` | `dim_owner` | Yes |
| | `estimated_close_date_key` | `dim_date` | No |
| `sales__fact_stage_duration` | `opportunity_key` | `sales__dim_opportunity` | Yes |
| | `entered_date_key` | `dim_date` | Yes |
| `sales__fact_forecast_movement` | `snapshot_date_key` | `dim_snapshot_date` | Yes |
| | `opportunity_key` | `sales__dim_opportunity` | Yes |
| `sales__fact_lead` | `created_date_key` | `dim_date` | Yes |
| | `owner_key` | `dim_owner` | Yes |
| | `lead_source_key` | `sales__dim_lead_source` | Yes |
| `sales__fact_quote` | `created_date_key` | `dim_date` | Yes |
| `sales__fact_order` | `created_date_key` | `dim_date` | Yes |

`created_date_key` is the **active** date relationship on `fact_opportunity`. Close-date
roles are inactive and activated per measure with `USERELATIONSHIP`, because metrics
declare different `time_basis` values in `metrics.yaml`.

---

## 6. Key strategy

### 6.1 Surrogate keys

Generated by `surrogate_key(*columns)` in `_common.py`:

```python
F.sha2(F.concat_ws("||", *[F.coalesce(F.col(c).cast("string"), F.lit("~")) for c in columns]), 256)
```

Deterministic, so a rebuild produces the same keys. NULL components collapse to `~` rather
than propagating NULL.

**Output type is `string` — 64 hex characters.** See §8.7; this is worth revisiting before
the first model is built.

### 6.2 SCD2 keys are per *version*, not per entity

**The single easiest thing to get wrong here, and the most expensive to fix.**

If `owner_key` identified the owner rather than the owner-version, historical snapshots
would silently re-attribute to today's org structure as people change jobs — and last
quarter's published numbers would change retroactively.

- Transaction facts carry the **current** version key.
- Snapshot facts carry the **as-of** version key.
- Slicers use `owner_name`, which naturally spans a person's versions, so the user
  experience is unchanged.

---

## 7. Validation

| Gate | Where | Behaviour |
|---|---|---|
| Bronze table presence | `10_` | **Fails the run** |
| Bronze table non-empty | `10_` | Warns — a scoping finding, not a technical failure |
| Bronze column presence | `10_` | **Fails the run.** The most valuable check — column drift produces wrong numbers rather than errors |
| Choice metadata source present | `10_` | Warns |
| Grain uniqueness | every Silver build | **Fails the run** |
| Zero-row output | every Silver build | **Fails the run** |
| Base currency resolves | `21_` | **Fails the run** |
| Config currency matches data | `21_` | **Fails the run** |
| Snapshot date already captured | `30_` | Skips — refusal, not overwrite |
| Snapshot completeness | `30_` | **Alerts** — missing days are unrecoverable |
| Required Silver dimensions exist | `40_` | **Fails the run** |

Report but do not fail, because these are scoping findings for the project lead:
`closeprobability` fill rate, loss reason fill rate, territory fill rate, contact-owned
opportunity share, opportunity product usage, manager chain fill rate, unmapped choice
values, unhandled activity target types.

---

## 8. Open issues affecting the schema

Each of these is a discrepancy between this document's sources. They are listed so the
first build resolves them rather than rediscovering them.

### 8.1 No notebook filters `IsDelete`

The live profile establishes that `IsDelete` is present on every Bronze table and flags
soft-deleted rows. **No notebook currently filters it**, so deleted records are included
in `dim_currency`, `dim_owner`, `bridge_activity` and every snapshot row. The fix belongs
in `bronze()` in `_common.py`, applied once, rather than in each caller.

### 8.2 `owner_key` is per-owner, and Gold filters `dim_owner`

Two related problems that must be fixed together:

- `22_` generates `owner_key` **per owner**, not per version. Its own TODO says so, and
  `assert_unique(["owner_guid"])` will fail once SCD2 lands.
- `23_` independently computes `owner_key = surrogate_key(owner_guid)` on
  `bridge_activity`. When `dim_owner` becomes per-version, that key stops matching.
- `40_` publishes `gold.dim_owner` with `WHERE is_current = true`. Correct for a
  current-state model; **wrong once a snapshot fact joins the same dimension** — a snapshot
  row carrying an as-of key finds no Gold row and loses its owner entirely.

**Decision D9** proposes publishing all versions in Gold with `is_current`,
`effective_from` and `effective_to` as attributes. It changes a platform notebook and
affects every pack, so it is a platform decision, not a pack-local one. The same applies to
`dim_customer` and `dim_product`, which `40_` also filters.

### 8.3 `bu_level_N` runs leaf-to-root

Notebook 22 sets `bu_level_1` to the owner's **own** business unit and walks *up* the
parent chain for levels 2…N. The usual convention is the opposite — level 1 as the root —
and every hierarchy visual and `own_business_unit_and_below` RLS expansion depends on
which it is. Either reverse the numbering or document it prominently; do not leave it
implicit.

### 8.4 The activity discriminator may not exist

Notebook 23 reads `regardingobjecttypecode` and assumes it carries the entity **logical
name**. The live profile shows Link to Fabric exposing lookups as
`<column>_entitytype` pairs instead. If `regardingobjecttypecode` is absent, or carries a
numeric type code, every typed key in `bridge_activity` is NULL and the bridge silently
resolves nothing. Confirm before the first build.

### 8.5 The snapshot fact is not conformed

Notebook 30 writes **raw Dataverse column names** (`estimatedvalue`, `statecode`,
`ownerid`) plus `snapshot_date`. The Sales pack design consumes conformed names
(`estimated_value_base`, `conformed_status`, `owner_guid`).

This is deliberate and defensible — the snapshot must capture state *before* conformance
so a conformance change cannot retroactively alter history — but it means **notebook 51
must apply conformance at read time**, and that step is currently unwritten. Whichever way
it is resolved, say so in the notebook: a reader will otherwise assume the snapshot is
already conformed.

### 8.6 Bronze table lists disagree across three files

`quotedetail` and `salesorderdetail` are in `source-tables.md` but in neither config list,
so notebook 10 does not gate on them. `pricelevel` is in the mapping but in neither list.
`bookableresource` is in config but not the mapping.

### 8.7 SHA-256 keys may not serve their stated purpose

The documented reason for surrogate keys is that Dataverse GUIDs "perform poorly at volume
in a Power BI model." `surrogate_key()` returns a 64-character hex string, which is larger
than a 36-character GUID and compresses no better. If model performance is the goal, an
integer surrogate is the usual answer; if determinism and reproducibility are the goal — and
they are genuine benefits here — the rationale should say so instead. Worth settling during
the Direct Lake spike, when the cost becomes measurable.

### 8.8 `dim_date.is_today` is computed at build time

`is_today`, `is_past` and `days_from_today` are materialized with `F.current_date()`. They
are wrong from the day after the build unless `24_` runs daily. Either schedule it daily
or move these to DAX — but not to a Direct Lake calculated column, which is unsupported.

---

## 9. What is not in any layer

- Custom tables and columns beyond those listed — additional development
- First-party Dynamics 365 Sales forecasting tables
- Conversation intelligence / Sales Premium AI data
- Marketing / Customer Insights – Journeys data — a roadmap candidate pack
- Exchange rate history — Dataverse does not provide it; constant-currency reporting needs
  an external source and is not packaged scope
- A holiday / working-day calendar — required by any business-hours metric
- Sales targets — not in Dataverse (decision D3); a spreadsheet source at JTP

---

## 10. Cross-app note

The platform is built app-agnostic where that costs nothing now, because cross-app
semantic models are the offering's long-term differentiator and would otherwise be a
rebuild rather than an addition. Three schema choices exist for that reason and should not
be "simplified" while Sales is the only pack:

| Choice | Why it stays |
|---|---|
| Conformed dimensions unprefixed in Silver | A `sales_dim_customer` would have to be rebuilt |
| Gold keeps the `sales__` pack prefix | A second pack lands without renaming anything |
| `bridge_activity` stays polymorphic | Cross-app activity analytics is built on exactly this artifact |

Adding Customer Service, Project Operations, Field Service, or cross-app *content* is the
offering owner's call. Keeping the platform able to accept them is not.
