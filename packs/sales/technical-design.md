# Sales pack — technical design document

**Scope:** Dynamics 365 Sales report pack only. Platform-wide design (ingestion, medallion
layout, conformance rules) is in [`docs/architecture/`](../../docs/architecture/) and is not
restated here.

**Audience:** the data engineer and BI developer building this pack, and the reviewer
approving it.

**Status:** design draft. Nothing in it has been built or validated against a live Dataverse
environment. Items marked `VERIFY` are explicitly unconfirmed, and items marked
**DECISION** need an answer before implementation starts.

| Section | |
|---|---|
| 1 | [Scope and assumptions](#1-scope-and-assumptions) |
| 2 | [Solution overview](#2-solution-overview) |
| 3 | [Bronze — linked tables](#3-bronze--linked-tables) |
| 4 | [Silver design](#4-silver-design) |
| 5 | [Snapshot and derived history design](#5-snapshot-and-derived-history-design) |
| 6 | [Gold star schema](#6-gold-star-schema) |
| 7 | [Semantic model design](#7-semantic-model-design) |
| 8 | [Measure implementation](#8-measure-implementation) |
| 9 | [Row-level security](#9-row-level-security) |
| 10 | [Report pack design](#10-report-pack-design) |
| 11 | [Orchestration and refresh](#11-orchestration-and-refresh) |
| 12 | [Sizing and performance](#12-sizing-and-performance) |
| 13 | [Reconciliation and testing](#13-reconciliation-and-testing) |
| 14 | [Open decisions](#14-open-decisions) |
| 15 | [Build sequence](#15-build-sequence) |

---

## 1. Scope and assumptions

### In scope

Pipeline, conversion, velocity, forecast, activity, and performance analytics over
Dynamics 365 Sales, including **point-in-time pipeline history** derived from daily
snapshots. The 20 metrics in [`metrics.yaml`](metrics.yaml) are the definitive scope
statement — this document describes how to implement them and nothing beyond them.

### Out of scope

Per [`source-tables.md`](source-tables.md#not-in-scope): custom tables and columns,
first-party Dynamics 365 Sales forecasting tables, conversation intelligence / Sales
Premium AI data, and marketing data.

### Assumptions

| # | Assumption | If false |
|---|---|---|
| A1 | Link to Fabric is configured and the tables in §3 are present in Bronze | Pack cannot build — notebook 10 gates this |
| A2 | The conformance layer (notebooks 20–24) is built and validated | Pack cannot build; conformed dimensions are prerequisites |
| A3 | `fact_opportunity_snapshot` has been accumulating since Sprint 1 | Snapshot-dependent metrics have no history; see §5 |
| A4 | The customer is single-currency, or multi-currency is declared in config | Money metrics silently mix currencies |
| A5 | Opportunities are owned by users and teams within a maintained business unit structure | RLS design in §9 needs revisiting |
| A6 | The seven open questions in `metrics.yaml` are answered before implementation | Several metrics are unbuildable or wrong |

A6 is the one that actually blocks. Each open question changes a metric definition, and
changing a definition after the model is built means rework in Gold, the model, and the
reports.

---

## 2. Solution overview

```
BRONZE (Link to Fabric shortcut, read-only)
  lead  opportunity  opportunityproduct  quote  quotedetail
  salesorder  salesorderdetail  account  contact  product  territory
        │
        ▼
SILVER — conformance (notebooks 20–24, platform-wide)
  lkp_choice_label   dim_date   dim_owner   dim_currency   bridge_activity
SILVER — sales pack (notebook 50)
  dim_customer  dim_contact  dim_product  dim_territory   ← CONFORMED, built here
  dim_opportunity
  fact_opportunity  fact_opportunity_product  fact_lead  fact_quote  fact_order
SILVER — history (notebook 30 platform, notebook 51 derived)
  fact_opportunity_snapshot        ← daily append, from Sprint 1
  fact_stage_duration              ← derived from snapshots
  fact_forecast_movement           ← derived from snapshots
        │
        ▼
GOLD (notebook 52)
  sales__dim_*   sales__fact_*   + views over conformed dimensions
        │
        ▼
SEMANTIC MODEL — "JTA Sales"
  two stars sharing conformed dimensions: current-state and as-of-date
        │
        ▼
REPORTS — 8 pages + paginated detail
```

Four conformed dimensions — `dim_customer`, `dim_contact`, `dim_product`,
`dim_territory` — **are created by this pack and consumed by every later pack.** They must
be built as conformed dimensions in Silver, not as `sales_*` local tables. This is the
single most consequential thing to get right here, because Customer Service, Project
Operations, Field Service, and Revenue-to-Delivery all depend on it.

---

## 3. Bronze — linked tables

Tables to select into Link to Fabric for this pack, added to `tables.required` in the
customer configuration. Draft — validate with notebook 10.

| Table | Used for | Required |
|---|---|---|
| `opportunity` | Header fact, `dim_opportunity`, snapshot source | Yes |
| `opportunityproduct` | Line fact | If products are used (open question 7) |
| `lead` | Lead fact, conversion | Yes |
| `quote`, `quotedetail` | Quote fact, quote-to-order conversion | Yes |
| `salesorder`, `salesorderdetail` | Order fact; **also the Project Ops contract** | Yes |
| `account` | `dim_customer` | Yes |
| `contact` | `dim_contact` | Yes |
| `product` | `dim_product` | If products are used |
| `territory` | `dim_territory` | If territories are used |
| `pricelevel` | Price list attributes | `VERIFY` whether needed |
| BPF instance table | Stage, if BPF-driven | **DECISION D4** — `VERIFY` table name and Link to Fabric availability |

Platform prerequisites already linked by the conformance layer: `systemuser`, `team`,
`businessunit`, `transactioncurrency`, `activitypointer`, and the choice-label metadata
source.

### Column expectations

Add to `tables.columns` in config so notebook 10 catches drift before it becomes a wrong
number. At minimum, every column named in [`source-tables.md`](source-tables.md) for
`opportunity` and `lead`.

### Choice columns

Add to `tables.choice_columns`: `opportunity` (`statecode`, `statuscode`,
`salesstagecode`, `opportunityratingcode`), `lead` (`statecode`, `statuscode`,
`leadqualitycode`, `leadsourcecode`), `quote` and `salesorder` (`statecode`,
`statuscode`).

---

## 4. Silver design

Built by **notebook 50** (`50_silver_sales.py`), after conformance, before Gold.

### 4.1 Conventions applied

Every Silver table in this pack applies, without exception:

1. **Choice labels** joined from `lkp_choice_label`, left join, never a hard-coded `CASE`.
   An unmapped value surfaces as NULL and is investigated; it never drops the fact row.
2. **Money** exposed as `_txn` and `_base` pairs, never silently converted.
3. **Surrogate keys** `_key` generated deterministically; Dataverse GUID retained as `_guid`.
4. **Conformed status grouping** added per table — see 4.2.
5. **Date keys** derived after a per-column time zone decision — see 4.3.
6. **Grain asserted** with `assert_unique` before write.

### 4.2 Conformed status grouping

`statecode` and `statuscode` both decoded and retained, plus a derived
`conformed_status` used by every metric:

| `conformed_status` | Opportunity source | Note |
|---|---|---|
| `Open` | `statecode` = 0 | `VERIFY` |
| `Won` | `statecode` = 1 | `VERIFY` |
| `Lost` | `statecode` = 2 with a loss status reason | `VERIFY` |
| `Cancelled` | `statecode` = 2 with a cancellation status reason | **DECISION D1** |

**DECISION D1 — is `Cancelled` a form of `Lost`?** It changes the Win Rate denominator
materially. The mapping lives in one place in notebook 50 so the answer is a one-line
change, not a rework. Default: `Cancelled` is separate and excluded from Win Rate.

Raw integers are never exposed to Gold or the semantic model.

### 4.3 Time zone handling

Dataverse stores datetimes in UTC and column behavior varies (user-local, date-only,
timezone-independent), so handling is **per column**, not global.

| Column | Treatment | Rationale |
|---|---|---|
| `createdon`, `modifiedon` | Convert UTC → `reporting_time_zone`, then derive `date_key` | User-local behavior; users expect "created today" to match Dynamics |
| `estimatedclosedate` | Treat as date-only, **no conversion** | `VERIFY` — if date-only, converting shifts it a day |
| `actualclosedate` | Treat as date-only, **no conversion** | `VERIFY` — same |

Getting this wrong produces totals that tie for a month but not for its first or last day.
It is the most common cause of "the numbers don't match" in UAT, so each decision is
recorded in `source-tables.md` per column as it is confirmed.

### 4.4 Conformed dimensions built here

These are **conformed**, written to `silver.dim_*`, and consumed by later packs.

#### `dim_customer` — SCD2, grain: account version

| Column | Source | Note |
|---|---|---|
| `customer_key` | surrogate, **per version** | |
| `customer_guid` | `account.accountid` | |
| `customer_name` | `account.name` | |
| `customer_number` | `account.accountnumber` | |
| `industry` | `account.industrycode` | label via lookup |
| `customer_type` | `account.customertypecode` | label via lookup |
| `revenue_band` | derived from `account.revenue` | bands are config |
| `employee_count` | `account.numberofemployees` | |
| `owner_key` | `account.ownerid` | |
| `territory_key` | `account.territoryid` | `VERIFY` — territory often lives here, not on opportunity |
| `parent_customer_guid` | `account.parentaccountid` | hierarchy |
| `city`, `state`, `country` | address columns | `VERIFY` which address is authoritative |
| `effective_from`, `effective_to`, `is_current` | SCD2 | |

SCD2 tracked attributes: `customer_name`, `industry`, `owner_key`, `territory_key`,
`revenue_band`. Changes to address alone do not create a version.

#### `dim_contact` — Type 1, grain: contact

`contact_key`, `contact_guid`, `full_name`, `job_title`, `email_domain` (derived, not the
address — see §9 note on PII), `parent_customer_guid`, `owner_key`.

#### `dim_product` — SCD2, grain: product version

`product_key`, `product_guid`, `product_number`, `product_name`, `product_category`
(`VERIFY` source — `product.subjectid` or a custom hierarchy), `product_type`,
`unit_group`, `default_price`, `is_active`, SCD2 columns.

**Write-in products** have no `productid`. `dim_product` gets a single
`product_key = -1` "Write-in / Unspecified" member, and the line fact points at it with
the free-text description carried as a degenerate attribute. Without this, write-in lines
disappear from product analysis silently.

#### `dim_territory` — Type 1, grain: territory

`territory_key`, `territory_guid`, `territory_name`, `manager_key`, parent hierarchy if
maintained.

**Frequently unpopulated.** Notebook 50 reports the fill rate. If low, territory pages are
removed from the report pack for that customer rather than shipped empty.

### 4.5 `dim_opportunity` — Type 1, grain: opportunity

Opportunity *attributes*, separated from opportunity *measures*.

`opportunity_key`, `opportunity_guid`, `opportunity_name`, `conformed_status`,
`state_label`, `status_reason_label`, `sales_stage_label`, `rating_label`,
`is_open`, `is_won`, `is_lost`, `is_cancelled`, `created_date_key`,
`estimated_close_date_key`, `actual_close_date_key`, `customer_account_key`,
`customer_contact_key`, `customer_display_name`, `owner_key`, `territory_key`,
`currency_key`.

**Why a dimension and not just degenerate columns on the fact:** `fact_opportunity_product`
needs to slice by opportunity attributes. Without `dim_opportunity` the line fact would
have to join to the header *fact*, and fact-to-fact relationships are harder to reason
about and to secure. One dimension, two facts pointing at it, is the cleaner shape and it
costs one small table.

### 4.6 Polymorphic customer resolution

`opportunity.customerid` points at **either an account or a contact**. Resolution in
Silver:

```
customer_account_key  ← where customerid type = account       (nullable)
customer_contact_key  ← where customerid type = contact       (nullable)
customer_display_name ← resolved name from whichever is populated
customer_party_type   ← 'Account' | 'Contact'
```

Reports slice on `dim_customer` and therefore **exclude contact-owned opportunities**. For
a B2B customer this is immaterial. For a B2C-shaped customer it is a significant hole.

Notebook 50 reports the account/contact split. If contact-owned opportunities are more
than a few percent, escalate: the fix is a unified **party dimension** (accounts and
contacts in one dimension with `party_type`), which is a conformed-dimension change
affecting every pack and therefore needs an ADR. Do not solve it locally in this pack.

`VERIFY` how the shortcut exposes the polymorphic type discriminator — same unknown as
`regardingobjectid` on activities (notebook 23).

### 4.7 Fact tables

| Table | Grain | Type | Key measures |
|---|---|---|---|
| `fact_opportunity` | one row per opportunity | transaction | `estimated_value_txn/_base`, `actual_value_txn/_base`, `budget_amount_txn/_base`, `close_probability`, `weighted_value_base`, `sales_cycle_days`, `days_since_last_activity`, `activity_count` |
| `fact_opportunity_product` | one row per line | transaction | `quantity`, `price_per_unit_txn/_base`, `extended_amount_txn/_base`, `is_price_overridden` |
| `fact_lead` | one row per lead | transaction | `estimated_value_base`, `is_qualified`, `days_to_qualify`, `qualifying_opportunity_key` |
| `fact_quote` | one row per quote | transaction | `total_amount_base`, `discount_amount_base`, `discount_percent`, `has_order` |
| `fact_order` | one row per order | transaction | `total_amount_base` |

Notes:

- `weighted_value_base` is precomputed in Gold rather than as a DAX calculated column,
  because Direct Lake does not support calculated columns (§7.1).
- `activity_count` and `days_since_last_activity` are precomputed from `bridge_activity`
  for the same reason, and because computing them in DAX over a large activity table is
  slow.
- **Line totals may not sum to the header value.** This is normal Dynamics behavior. The
  two facts are deliberately kept in separate stars against `dim_opportunity`, and the
  reports never place header and line measures in the same visual without a note. It will
  still be raised in reconciliation — §13 covers how to answer it.

---

## 5. Snapshot and derived history design

The differentiating capability of the pack. Platform notebook 30 writes the snapshot;
**notebook 51** derives history facts from it.

### 5.1 `fact_opportunity_snapshot`

Written by [notebook 30](../../platform/notebooks/30_silver_snapshot_facts.py). Grain:
**opportunity × snapshot_date**. Append-only, partitioned by `snapshot_date`, guarded
against double-writing a date.

Open opportunities are captured daily; closed ones captured once and then excluded. That
single rule is what keeps growth bounded — see §12.

Columns consumed by this pack: `snapshot_date`, `opportunity_guid`, `conformed_status`,
`sales_stage_label`, `estimated_value_base`, `actual_value_base`, `estimated_close_date`,
`close_probability`, `owner_guid`, `owning_business_unit`, `customer_guid`, `created_on`.

### 5.2 As-of ownership — requires a platform change

A snapshot of last quarter's pipeline must respect **who owned the record then**.
`dim_owner` is SCD2 for exactly this reason.

Two changes are needed, and they are the most important technical points in this document:

1. **Notebook 51 stamps the as-of owner version key** onto each snapshot row, resolving
   `owner_guid` against `dim_owner` where `snapshot_date` falls between `effective_from`
   and `effective_to`. The key is resolved in Silver, never in DAX.

2. **Notebook 40 must stop filtering `dim_owner` to current rows.**
   [`40_gold_conformed_dimensions.py`](../../platform/notebooks/40_gold_conformed_dimensions.py)
   currently publishes `gold.dim_owner` as `WHERE is_current = true`. That is correct for
   a current-state-only model and **wrong once a snapshot fact joins the same dimension** —
   historical rows would lose their owner entirely.

   **Design decision:** publish **all versions** in `gold.dim_owner`, grain = owner
   version, with `is_current`, `effective_from`, `effective_to` as attributes. Transaction
   facts carry the current version key; the snapshot fact carries the as-of version key.
   Slicers use `owner_name`, which naturally spans a person's versions, so the user
   experience is unchanged. Each version row also carries `current_business_unit_path` so
   "show last year's results under today's org structure" remains answerable.

   The alternative — two owner dimensions — puts two owner slicers in one model and
   invites users to pick the wrong one. Rejected.

   **This changes a platform notebook, so it needs review beyond this pack.** Same
   treatment applies to `dim_customer` and `dim_product`, which notebook 40 also filters.

### 5.3 `fact_stage_duration` — derived

Grain: **one row per opportunity × stage entry**. Built by comparing consecutive snapshot
rows per opportunity and emitting a row when `sales_stage_label` changes.

`opportunity_key`, `stage_label`, `stage_sequence`, `entered_date_key`, `exited_date_key`,
`days_in_stage`, `is_current_stage`, `owner_key_asof`, `estimated_value_base_at_entry`.

Limitations, both to be stated at handoff:

- Daily granularity, so two stage changes in one day are indistinguishable.
- Only as deep as snapshot history. An opportunity created before snapshots began has no
  observable early stages.

### 5.4 `fact_forecast_movement` — derived

Grain: **opportunity × snapshot_date**, for open opportunities only. Supports Forecast
Slippage and Forecast Accuracy.

`snapshot_date_key`, `opportunity_key`, `estimated_close_date_key`,
`prior_estimated_close_date_key`, `close_date_moved_days`, `estimated_value_base`,
`prior_estimated_value_base`, `value_change_base`, `owner_key_asof`.

`close_date_moved_days > 0` is slippage. This is precomputed rather than left to DAX
because comparing a row to its own prior snapshot in DAX is expensive and hard to read.

### 5.5 Snapshot date dimension

The model needs **two independent date pickers**: "as of" (snapshot date) and "close date"
or "created date" (transaction dates). One `dim_date` related to both creates ambiguity and
forces `USERELATIONSHIP` into every measure.

**Design decision:** a separate `dim_snapshot_date` in Gold — a view over `dim_date`
restricted to dates where a snapshot exists. It carries the same attributes with an
`asof_` prefix on its display names. Snapshot facts relate to it; transaction facts relate
to `dim_date`.

Cost: two date tables in the model, which must be explained in training. Benefit: the
as-of slicer is obvious in the UI, measures stay readable, and the empty-date problem
(picking a date with no snapshot) disappears because the dimension only contains dates
that exist.

---

## 6. Gold star schema

Built by **notebook 52**. Pack prefix `sales__`; conformed dimensions are **views** over
Silver, never copies.

```
                    ┌──────────────────┐
                    │ dim_date         │◄──── created / close dates
                    └────────┬─────────┘
                             │
  ┌────────────┐   ┌─────────▼──────────┐   ┌─────────────────┐
  │ dim_owner  │◄──┤ sales__fact_       │──►│ dim_customer    │
  │ (versioned)│   │   opportunity      │   └─────────────────┘
  └────────────┘   └─────────┬──────────┘   ┌─────────────────┐
                             │          ┌──►│ dim_currency    │
                   ┌─────────▼──────────┐   └─────────────────┘
                   │ sales__dim_        │   ┌─────────────────┐
                   │   opportunity      │──►│ dim_territory   │
                   └─────────┬──────────┘   └─────────────────┘
                             │
        ┌────────────────────┼────────────────────┬──────────────────┐
        │                    │                    │                  │
┌───────▼────────┐  ┌────────▼─────────┐ ┌────────▼──────┐ ┌─────────▼────────┐
│ sales__fact_   │  │ sales__fact_     │ │ sales__fact_  │ │ sales__fact_     │
│  opportunity_  │  │  opportunity_    │ │  stage_       │ │  forecast_       │
│  product       │  │  snapshot        │ │  duration     │ │  movement        │
└───────┬────────┘  └────────┬─────────┘ └───────────────┘ └──────────────────┘
        │                    │
┌───────▼────────┐  ┌────────▼──────────────┐
│ dim_product    │  │ dim_snapshot_date     │◄──── the "as of" picker
└────────────────┘  └───────────────────────┘

separate stars, shared dimensions:
  sales__fact_lead ──► dim_date, dim_owner, dim_customer, dim_lead_source
  sales__fact_quote, sales__fact_order ──► dim_date, dim_owner, dim_customer
```

| Gold object | Type | Source |
|---|---|---|
| `dim_date` | view | `silver.dim_date` |
| `dim_snapshot_date` | view | `silver.dim_date` filtered to snapshot dates |
| `dim_owner` | view | `silver.dim_owner` — **all versions**, per §5.2 |
| `dim_currency` | view | `silver.dim_currency` |
| `dim_customer` | view | `silver.dim_customer` |
| `dim_contact` | view | `silver.dim_contact` |
| `dim_product` | view | `silver.dim_product` |
| `dim_territory` | view | `silver.dim_territory` |
| `sales__dim_opportunity` | table | `silver.dim_opportunity` |
| `sales__dim_lead_source` | table | derived from `lead.leadsourcecode` labels |
| `sales__fact_opportunity` | table | `silver.fact_opportunity` |
| `sales__fact_opportunity_product` | table | `silver.fact_opportunity_product` |
| `sales__fact_lead` | table | `silver.fact_lead` |
| `sales__fact_quote` | table | `silver.fact_quote` |
| `sales__fact_order` | table | `silver.fact_order` |
| `sales__fact_opportunity_snapshot` | table | `silver.fact_opportunity_snapshot` |
| `sales__fact_stage_duration` | table | `silver.fact_stage_duration` |
| `sales__fact_forecast_movement` | table | `silver.fact_forecast_movement` |
| `sales__sec_owner_scope` | table | RLS bridge — §9 |

---

## 7. Semantic model design

One model, **"JTA Sales"**, in the reporting workspace.

### 7.1 Storage mode — **DECISION D7**

**Recommendation: Direct Lake**, with an Import fallback decided by a first-build spike.

| | Direct Lake | Import |
|---|---|---|
| Freshness | Reads Delta directly; no model refresh | Scheduled refresh |
| Snapshot fact at scale | Handles large append-only tables well | Memory-bound |
| Calculated columns / tables | **Not supported** | Supported |
| Complex DAX | Some patterns fall back to DirectQuery | Full |
| Fabric alignment | Native | Works, but not the Fabric story |

Direct Lake is the right default: it matches the offering's Fabric-alignment narrative,
removes a refresh failure mode, and suits an append-only snapshot fact.

**It also imposes a constraint that is actually desirable:** no calculated columns means
every derived value must exist in Gold. That is already the architecture's rule — data
correction belongs in Silver, shaping in Gold, measurement in the model. Direct Lake
enforces it.

Consequences already designed in: `weighted_value_base`, `sales_cycle_days`,
`activity_count`, `days_since_last_activity`, aging buckets, and the `is_*` flags are all
computed in Gold, not DAX.

`VERIFY` current Direct Lake capabilities and limits — particularly RLS behavior, fallback
triggers, and any relationship or cardinality constraints — against current Microsoft
documentation before committing. Direct Lake has changed materially over time and this
recommendation must not be taken on trust. **Run a spike in Sprint 1 with a realistic
snapshot volume and the RLS pattern from §9 applied**, before building reports on it.

### 7.2 Relationships

| From | To | Cardinality | Direction | Active |
|---|---|---|---|---|
| `sales__fact_opportunity[opportunity_key]` | `sales__dim_opportunity` | many→1 | single | Yes |
| `sales__fact_opportunity[created_date_key]` | `dim_date` | many→1 | single | **Yes** |
| `sales__fact_opportunity[estimated_close_date_key]` | `dim_date` | many→1 | single | No |
| `sales__fact_opportunity[actual_close_date_key]` | `dim_date` | many→1 | single | No |
| `sales__fact_opportunity[owner_key]` | `dim_owner` | many→1 | single | Yes |
| `sales__fact_opportunity[customer_key]` | `dim_customer` | many→1 | single | Yes |
| `sales__fact_opportunity[currency_key]` | `dim_currency` | many→1 | single | Yes |
| `sales__fact_opportunity[territory_key]` | `dim_territory` | many→1 | single | Yes |
| `sales__fact_opportunity_product[opportunity_key]` | `sales__dim_opportunity` | many→1 | single | Yes |
| `sales__fact_opportunity_product[product_key]` | `dim_product` | many→1 | single | Yes |
| `sales__fact_opportunity_snapshot[snapshot_date_key]` | `dim_snapshot_date` | many→1 | single | Yes |
| `sales__fact_opportunity_snapshot[opportunity_key]` | `sales__dim_opportunity` | many→1 | single | Yes |
| `sales__fact_opportunity_snapshot[owner_key_asof]` | `dim_owner` | many→1 | single | Yes |
| `sales__fact_opportunity_snapshot[estimated_close_date_key]` | `dim_date` | many→1 | single | No |
| `sales__fact_stage_duration[opportunity_key]` | `sales__dim_opportunity` | many→1 | single | Yes |
| `sales__fact_stage_duration[entered_date_key]` | `dim_date` | many→1 | single | Yes |
| `sales__fact_forecast_movement[snapshot_date_key]` | `dim_snapshot_date` | many→1 | single | Yes |
| `sales__fact_forecast_movement[opportunity_key]` | `sales__dim_opportunity` | many→1 | single | Yes |
| `sales__fact_lead[created_date_key]` | `dim_date` | many→1 | single | Yes |
| `sales__fact_lead[owner_key]` | `dim_owner` | many→1 | single | Yes |
| `sales__fact_lead[lead_source_key]` | `sales__dim_lead_source` | many→1 | single | Yes |
| `sales__fact_quote[created_date_key]` | `dim_date` | many→1 | single | Yes |
| `sales__fact_order[created_date_key]` | `dim_date` | many→1 | single | Yes |

Rules applied:

- **All relationships single-direction.** No bidirectional filtering anywhere. It is the
  usual cause of ambiguous-path errors and of RLS leaking across tables. The one place
  bidirectional filtering would be tempting — the RLS bridge — is handled with a DAX
  filter instead (§9).
- **`created_date_key` is the active date relationship** on `fact_opportunity`. Close-date
  and estimated-close-date roles are inactive and activated per measure with
  `USERELATIONSHIP`, because metrics declare different `time_basis` values in
  `metrics.yaml`.
- `dim_date` is **marked as a date table**.
- `dim_snapshot_date` is a **second date table** and is deliberately *not* marked as the
  model date table; time intelligence over it is not needed, and marking it would create
  ambiguity.

### 7.3 Model hygiene

- Every `_key` and `_guid` column **hidden**. Users never see a key.
- Every fact table hidden except where a degenerate attribute is needed.
- Measures organized into display folders matching `metrics.yaml` sections: Pipeline,
  Conversion, Velocity, Forecast, Activity, Performance.
- **Every measure carries a description copied from `metrics.yaml`**, including its
  `currency_basis` and whether it is snapshot-dependent. This is a Copilot deliverable as
  much as a documentation one — model readability determines whether Copilot answers
  usefully, per
  [`training-and-adoption.md`](../../docs/delivery/training-and-adoption.md).
- Money measures formatted with the base currency symbol from config; percentages as
  percentages; no raw decimals surfaced.
- `dim_owner` slicers use `owner_name`, never a version key.
- Model endorsed as **Certified** after reconciliation passes, not before.

---

## 8. Measure implementation

All 20 metrics in [`metrics.yaml`](metrics.yaml) are implemented. Patterns for the
non-obvious ones follow; the rest are direct aggregations.

### 8.1 Time basis via inactive relationships

`metrics.yaml` declares a `time_basis` per metric. Metrics measured on close date activate
that role:

```
Closed Won Value :=
CALCULATE (
    SUM ( sales__fact_opportunity[actual_value_base] ),
    KEEPFILTERS ( sales__dim_opportunity[conformed_status] = "Won" ),
    USERELATIONSHIP ( sales__fact_opportunity[actual_close_date_key], dim_date[date_key] )
)
```

`Open Pipeline Value` uses `estimated_close_date_key` the same way. `KEEPFILTERS` preserves
any user-applied status filter rather than overriding it.

### 8.2 The as-of pattern — the pack's key measure

`Pipeline Value As Of Date` must resolve to **exactly one** snapshot date. Without that
guard, a user who drags the measure onto a visual with no as-of slicer sums every day of
history and gets a number in the billions.

```
As Of Date :=
CALCULATE (
    MAX ( dim_snapshot_date[snapshot_date] ),
    ALLSELECTED ( dim_snapshot_date )
)

Pipeline Value As Of Date :=
VAR SelectedDate = [As Of Date]
RETURN
CALCULATE (
    SUM ( sales__fact_opportunity_snapshot[estimated_value_base] ),
    sales__fact_opportunity_snapshot[conformed_status] = "Open",
    dim_snapshot_date[snapshot_date] = SelectedDate
)
```

Behavior: with an as-of slicer set, it uses that date; with a range selected, the latest in
range; with nothing selected, the latest snapshot overall. It **never** sums across days.

Every snapshot-sourced measure follows this shape. This is a review checkpoint — a
snapshot measure written without the single-date guard is a defect even if it looks right
on the page it was built for.

### 8.3 Pipeline trend — one point per day

The trend visual needs one value *per* snapshot date, which is the opposite of §8.2:

```
Pipeline Value Trend :=
CALCULATE (
    SUM ( sales__fact_opportunity_snapshot[estimated_value_base] ),
    sales__fact_opportunity_snapshot[conformed_status] = "Open"
)
```

Correct only when `dim_snapshot_date[snapshot_date]` is on the axis. Its description must
say so, and it is the one measure that is unsafe as a card.

### 8.4 Ratio measures — explicit denominators

```
Win Rate :=
VAR Won =
    CALCULATE (
        COUNTROWS ( sales__fact_opportunity ),
        KEEPFILTERS ( sales__dim_opportunity[conformed_status] = "Won" ),
        USERELATIONSHIP ( sales__fact_opportunity[actual_close_date_key], dim_date[date_key] )
    )
VAR Closed =
    CALCULATE (
        COUNTROWS ( sales__fact_opportunity ),
        KEEPFILTERS ( sales__dim_opportunity[conformed_status] IN { "Won", "Lost" } ),
        USERELATIONSHIP ( sales__fact_opportunity[actual_close_date_key], dim_date[date_key] )
    )
RETURN
DIVIDE ( Won, Closed )
```

`DIVIDE` throughout, never `/`. The `IN { "Won", "Lost" }` denominator is where **DECISION
D1** lands — if `Cancelled` counts as `Lost`, this set changes and so does every win-rate
number in the pack.

### 8.5 Median alongside mean

`metrics.yaml` requires median for Average Sales Cycle, because the distribution is heavily
skewed and the mean alone misleads.

```
Median Sales Cycle :=
CALCULATE (
    MEDIANX ( sales__fact_opportunity, sales__fact_opportunity[sales_cycle_days] ),
    KEEPFILTERS ( sales__dim_opportunity[conformed_status] IN { "Won", "Lost" } )
)
```

Both appear on the velocity page. `VERIFY` `MEDIANX` performance under Direct Lake at
volume during the spike — it is a likely DirectQuery fallback trigger.

### 8.6 Aging buckets

Bucket boundaries are computed in **Gold**, not DAX, because Direct Lake has no calculated
columns. `sales__fact_opportunity[age_bucket]` and a `sales__dim_age_bucket` with an
explicit sort order — bucket labels sort alphabetically otherwise, putting "8-30" before
"2-7".

### 8.7 Metrics conditional on data quality

Four metrics are viable only if the customer's data supports them. Notebook 50 reports
each fill rate, and the decision is made before the model is built:

| Metric | Requires | If absent |
|---|---|---|
| Weighted Pipeline Value | `closeprobability` maintained | **Remove the measure.** Do not ship a misleading number |
| Pipeline Coverage | A target source, which is not in Dataverse | Remove, or ingest targets as additional development |
| Loss Rate By Reason | Loss reason populated consistently | Remove the page rather than ship it empty |
| Average Time In Stage | Stage source resolved (**D4**) and snapshot depth | Defer until history accumulates |

Removing a measure is the correct outcome, not a failure. A plausible-looking wrong number
costs more than an absent one.

---

## 9. Row-level security

Design per [`security-and-rls.md`](../../docs/architecture/security-and-rls.md). The
example config sets `manager_hierarchy` for this pack.

**Dataverse security does not follow data into OneLake.** Default visibility is everything,
so RLS is a build deliverable, not an option.

### 9.1 The scope bridge

`sales__sec_owner_scope`, built in Gold, grain: **user × permitted owner version key**.

| Column | |
|---|---|
| `user_principal_name` | Matched against `USERPRINCIPALNAME()` |
| `owner_key` | A `dim_owner` version the user may see |

Populated by expanding the configured pattern over `dim_owner`:

| Pattern | Expansion |
|---|---|
| `own_records` | The user's own owner versions |
| `own_business_unit` | All owners in the user's BU |
| `own_business_unit_and_below` | All owners at or below the user's BU in the resolved path |
| `manager_hierarchy` | The user, plus everyone below them in the manager chain |
| `team_membership` | Owners of teams the user belongs to |

Expansion happens in Gold because it is inspectable, testable, and cheap to refresh.
Equivalent DAX would be none of those, and complex DAX RLS is the usual cause of RLS
performance problems.

**Manager hierarchy requires `systemuser.parentsystemuserid` to be maintained.** Notebook
22 reports the fill rate; if sparse, manager-based RLS is not viable and the pattern must
change. That is a scoping finding, not something to engineer around.

### 9.2 Role definition

One role, **"Sales Scope"**, with a filter on `dim_owner`:

```
dim_owner[owner_key] IN
    CALCULATETABLE (
        VALUES ( sales__sec_owner_scope[owner_key] ),
        sales__sec_owner_scope[user_principal_name] = USERPRINCIPALNAME()
    )
```

Properties of this pattern:

- **Fails closed.** A user with no bridge rows matches nothing and sees nothing. An RLS
  misconfiguration that shows everything is a data exposure, not a cosmetic defect, so
  fail-closed is required, not preferred.
- **No bidirectional relationships needed.** The filter on `dim_owner` propagates to every
  fact through existing single-direction relationships.
- **Snapshot history is secured by as-of ownership.** Because the snapshot fact joins
  `dim_owner` on `owner_key_asof`, a user sees historical pipeline as owned *then*. This is
  the correct behavior and it falls out of the §5.2 design for free.
- `sales__sec_owner_scope` is hidden.

### 9.3 Testing

A UAT exit criterion, per [`uat-plan.md`](../../docs/delivery/uat-plan.md):

| Test | Expected |
|---|---|
| Individual contributor | Own records only |
| Manager | Own plus direct and indirect reports |
| Senior leader | Full BU subtree |
| User with no assignment | **Zero rows**, not all rows |
| Snapshot page, reassigned owner | Historical rows attributed to the owner at that time |
| Row counts per role | Match independently computed expectations |

Tested with named test users against precomputed expected counts. "Looks about right" is
not a pass.

### 9.4 Other security notes

- **The SQL endpoint bypasses this entirely.** Anyone with Gold access reads unfiltered.
  `sql_endpoint_audience` in config governs it; it is not a substitute for a viewer role.
- **No email addresses in `dim_contact`.** `email_domain` is derived instead. Full contact
  email is PII with no analytic purpose in this pack.
- Workspace separation per the platform design: report consumers never get platform
  workspace access.

---

## 10. Report pack design

Eight pages plus paginated detail. Consistent layout: filter pane left, KPI row top,
detail below; drill-through to opportunity detail from every visual.

| # | Page | Content | Depends on snapshots |
|---|---|---|---|
| 1 | **Pipeline Overview** | Open/weighted pipeline KPIs, pipeline by stage funnel, by owner, by territory, expected-close timeline | No |
| 2 | **Pipeline History** | **As-of date slicer**, pipeline value trend, stage mix over time, snapshot-vs-today comparison | **Yes** |
| 3 | **Forecast** | Forecast vs. actual by period, slippage list, forecast accuracy trend, coverage (if targets exist) | **Yes** |
| 4 | **Win/Loss** | Win rate by count and value, loss reasons, win rate by owner/product/segment, cycle length by outcome | No |
| 5 | **Velocity** | Mean and median sales cycle, average time in stage, stage conversion funnel, stalled pipeline | Partly |
| 6 | **Leads** | Lead volume by source, conversion rate, time to qualify, quality distribution | No |
| 7 | **Performance** | Attainment by owner/team/BU, deal size distribution, activity-to-outcome, leaderboard | No |
| 8 | **Products** | Pipeline and won value by product and category, write-in share, discount analysis | No |
| P | **Opportunity Detail** (paginated) | Exportable record-level listing | No |

Design rules:

- **Page 2 is the demo.** It is the capability no first-party Dynamics 365 analytics
  offers. It opens with the as-of slicer defaulted to the latest snapshot.
- **Snapshot-dependent pages carry a visible note** on snapshot start date and that history
  is not backfillable. Customers otherwise read a short trend as a defect.
- Pages 3, 5, and 8 are **conditionally shipped** per §8.7. Page 8 is removed if products
  are unused; loss-reason visuals removed if unpopulated.
- Reports are branded from config, and embedded into Dynamics 365 where the customer wants
  them in-app.
- `VERIFY` paginated report licensing requirements against the customer's SKU before
  committing to page P.

---

## 11. Orchestration and refresh

Two pipelines, per the platform design.

```
DAILY — platform then pack
  10_bronze_shortcut_validation        ← gate; failure stops everything
  20,21,24 (parallel) → 22,23          ← conformance
  40_gold_conformed_dimensions
  50_silver_sales
  51_silver_sales_history              ← needs today's snapshot
  52_gold_sales
  refresh "JTA Sales"                  ← Import only; no-op under Direct Lake

DAILY — snapshots (SEPARATE pipeline, separate failure domain)
  10_bronze_shortcut_validation
  30_silver_snapshot_facts             ← fixed UTC time, append-only
  completeness check + alert
```

- **Notebook 51 runs after 30**, since derived history reads the snapshot written that day.
- **Snapshots stay in their own pipeline.** A failed Gold build costs a rerun; a missed
  snapshot day is gone permanently. They must not share a failure domain.
- Under Direct Lake there is no model refresh step, which removes a failure mode. Under
  Import, the refresh is **triggered after notebook 52 completes**, never independently
  scheduled — refreshing against a half-built Gold produces wrong numbers with no error.
- Monitoring: snapshot completeness alerting, Bronze validation failures, and (Import only)
  refresh failures, all routed to a named contact.

---

## 12. Sizing and performance

### Snapshot growth

The only component with open-ended growth. Worked example for a mid-size Sales tenant:

| | |
|---|---|
| Total opportunities | 50,000 |
| Open at any time | 10,000 |
| Snapshot columns | ~20, narrow types |
| Open rows/day | 10,000 |
| **Rows/year** | **~3.7M** |
| Closed rows (captured once) | 40,000 |
| Estimated size/year | low single-digit GB before compression |

Comfortable for Fabric at this scale. The open/closed rule in §5.1 is what makes it so:
without it, 50,000 × 365 = 18.25M rows/year, roughly five times the volume for no
analytic gain.

Retention: `daily_retention_days` (default 730) with month-end rollup beyond it. Agreed at
kickoff, since it is the one recurring storage cost the architecture adds.

### Performance considerations

- Snapshot fact partitioned by `snapshot_date`; the §8.2 single-date guard means as-of
  queries touch one partition.
- `fact_stage_duration` and `fact_forecast_movement` are precomputed precisely so the
  reports do not scan the full snapshot fact at query time.
- Aging buckets, weighted value, cycle days, and activity aggregates all precomputed in
  Gold — required under Direct Lake, and faster regardless.
- `MEDIANX` is the most likely performance problem. Measure it in the spike.
- RLS expands in Gold, not DAX, keeping the security filter a simple `IN` over a small table.

---

## 13. Reconciliation and testing

### 13.1 Reconciliation — before UAT, not during

Per the [playbook](../../docs/delivery/playbook.md), every pack reconciles headline metrics
against the source app in Sprint 2. A number that does not tie is the fastest way to lose
confidence in the whole platform, and the cause is nearly always conformance — currency,
status decoding, or time zone — rather than the report.

| Metric | Reconcile against | Tolerance |
|---|---|---|
| Open Pipeline Value | Dynamics open-opportunity view, sum of estimated revenue | **Exact** |
| Closed Won Value, period | Dynamics won opportunities for the period | **Exact** |
| Open opportunity count | Dynamics view count | **Exact** |
| Cases by stage | Dynamics grouped view | **Exact** |
| Lead count by source | Dynamics grouped view | **Exact** |
| Line totals vs. header value | Dynamics itself | **Variance expected** — document, do not force |

Anything that does not tie exactly is investigated, not tolerated. The expected-variance
row is the exception, and it is expected in Dynamics too.

Documented variances, with reasons, are delivered at handoff. Walking into UAT with a known
explained variance is fine; discovering one during UAT is not.

### 13.2 Data quality checks in notebook 50

Fail the run, because a silent partial success becomes a wrong number weeks later:

- Grain uniqueness on every dimension and fact
- Referential integrity: no fact row with an unmatched dimension key
- No NULL `conformed_status`
- No NULL `_base` money where `_txn` is populated
- Every snapshot row resolved to an as-of owner version

Report but do not fail — these are scoping findings for the project lead:

- `closeprobability` fill rate
- Loss reason fill rate
- Territory fill rate
- Contact-owned opportunity share (§4.6)
- Opportunity product usage
- Manager chain fill rate
- Unmapped choice values

### 13.3 Model testing

- Every measure in `metrics.yaml` exists, with a description
- Snapshot measures verified not to sum across dates — deliberately tested by placing each
  on a card with no as-of slicer
- Inactive date relationships verified to activate correctly per measure
- RLS per §9.3
- Refresh or Direct Lake query performance within the agreed threshold

---

## 14. Open decisions

| ID | Decision | Blocks | Default if unanswered |
|---|---|---|---|
| **D1** | Is `Cancelled` a form of `Lost`? | Win Rate, Loss Rate | Separate; excluded from Win Rate |
| **D2** | Is `closeprobability` maintained? | Weighted Pipeline Value | Remove the measure |
| **D3** | Do sales targets exist, and where? | Pipeline Coverage | Remove the measure |
| **D4** | Stage from `salesstagecode` or BPF? | All stage metrics, `fact_stage_duration` | **Must be answered** — no safe default |
| **D5** | Is loss reason populated consistently? | Loss Rate By Reason, Win/Loss page | Remove the visuals |
| **D6** | Stalled-pipeline threshold? | Stalled Pipeline Value | 30 days |
| **D7** | Direct Lake or Import? | Model build, Gold design | Direct Lake, pending the Sprint 1 spike |
| **D8** | Are opportunity products used? | Products page, line fact | Omit the page |
| **D9** | Publish all `dim_owner` versions in Gold? (§5.2) | Snapshot ownership across **all** packs | **Yes** — needs platform review |
| **D10** | Contact-owned opportunity share, and does it need a party dimension? (§4.6) | `dim_customer` shape across all packs | Dual-key, account-only reporting; escalate if material |

**D4, D9, and D10 are the consequential ones.**

- **D4** has no safe default. Building stage analytics on `salesstagecode` when the customer
  drives stage through a business process flow produces numbers that are wrong and look
  plausible.
- **D9** changes a platform notebook and affects every pack's snapshot ownership, so it
  cannot be decided inside this pack.
- **D10** could change a conformed dimension, which would need an ADR.

D1–D8 map to the open questions already recorded in
[`metrics.yaml`](metrics.yaml) and [`README.md`](README.md); D9 and D10 are new findings
from this design pass.

---

## 15. Build sequence

Ordered so that each step is verifiable before the next depends on it.

| Step | Work | Exit criterion |
|---|---|---|
| 1 | Answer D1–D6, D8; resolve VERIFY items in `source-tables.md` against a live environment | Decisions recorded; mappings corrected and committed |
| 2 | Raise D9 for platform review; D10 if the contact share is material | Decided, or an ADR opened |
| 3 | Add Sales tables to config; run notebook 10 | Validation passes with **zero** unresolved discrepancies |
| 4 | Confirm snapshots are running (should already be, from Sprint 1) | `fact_opportunity_snapshot` has consecutive days, no gaps |
| 5 | **Direct Lake spike** — realistic snapshot volume, RLS applied, `MEDIANX` measured | D7 decided on evidence |
| 6 | Build notebook 50: conformed dimensions, `dim_opportunity`, facts | Quality checks pass; fill-rate report reviewed with the project lead |
| 7 | Build notebook 51: as-of owner keys, `fact_stage_duration`, `fact_forecast_movement` | Every snapshot row has an as-of owner version |
| 8 | Build notebook 52: Gold, including the RLS bridge | Star schema queryable; bridge populated |
| 9 | Build the semantic model: relationships, measures, descriptions, folders | All 20 in-scope measures present and described |
| 10 | Apply and test RLS | §9.3 passes, fail-closed confirmed |
| 11 | **Reconcile** per §13.1 | Headline metrics tie exactly; variances documented |
| 12 | Build reports; drop conditional pages per §8.7 | Pages render; no empty visuals |
| 13 | Brand, deploy, endorse as Certified | Deployed to the reporting workspace |
| 14 | Update `source-tables.md`, `metrics.yaml`, and this document from what was learned | Corrections committed — this is how the pack becomes reusable IP |

**Step 14 is not optional.** The first build's corrections are what turn these drafts into
the reusable asset the offering depends on. A build that delivers a working customer
solution but leaves the repository unchanged has produced a project, not a product.
