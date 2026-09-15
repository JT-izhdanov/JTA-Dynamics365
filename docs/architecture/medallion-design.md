# Medallion design

Component 2 of the customer-facing architecture narrative. The conformance rules
themselves are in [`conformance-layer.md`](conformance-layer.md); this document covers
layout, naming, and orchestration.

## Layers

| Layer | Contents | Written by | Customer-facing description |
|---|---|---|---|
| **Bronze** | Link to Fabric shortcut — raw Dataverse tables, as-is | Microsoft | Raw ingestion of key Dynamics 365 tables and fields |
| **Silver** | Conformed dimensions, cleansed facts, snapshots, SCD2 | JourneyTeam notebooks | Transformed and optimized for BI |
| **Gold** | Subject-area star schemas, aggregates, semantic-model sources | JourneyTeam notebooks | Aggregated and modeled for business-level consumption |

## Schema and naming

One lakehouse, `jta_lakehouse`, with three schemas:

```
jta_lakehouse
├── bronze/     (shortcut — read-only, Dataverse logical names preserved)
│     account, contact, lead, opportunity, incident, msdyn_workorder, ...
├── silver/
│     dim_date, dim_customer, dim_owner, dim_currency, ...
│     lkp_choice_label, bridge_activity
│     fact_opportunity_snapshot, fact_case_snapshot, ...
└── gold/
      sales__fact_opportunity, sales__dim_customer, ...
      cs__fact_case, ...
      po__fact_actual, ...
      fs__fact_workorder, ...
      r2d__fact_revenue_to_delivery, ...
```

Conventions:

- **Bronze keeps Dataverse logical names unchanged.** They are Microsoft's, not ours, and
  the shortcut defines them.
- **Silver is prefixed by role:** `dim_`, `fact_`, `lkp_`, `bridge_`.
- **Gold is prefixed by pack:** `sales__`, `cs__`, `po__`, `fs__`, `r2d__`. Double
  underscore separates pack from object so the object name keeps its own `dim_`/`fact_`
  reading.
- **Conformed dimensions are shared, not copied.** A Gold pack schema exposes a *view* over
  the Silver conformed dimension where it needs one. It does not duplicate it. This is the
  rule that makes cross-app models possible, and the one most likely to be broken under
  delivery pressure.
- Columns are `snake_case`. Dataverse GUID keys are retained and suffixed `_guid`;
  surrogate keys are suffixed `_key`.

## Orchestration

Notebooks are numbered by stage and run in that order:

| Order | Notebook | Purpose |
|---|---|---|
| 10 | `10_bronze_shortcut_validation` | Confirm expected tables, rows, and columns exist before anything downstream runs |
| 20 | `20_silver_conformance_choice_labels` | Build `lkp_choice_label` |
| 21 | `21_silver_conformance_currency` | Currency normalization and `dim_currency` |
| 22 | `22_silver_conformance_ownership` | `dim_owner` with business unit and manager hierarchies |
| 23 | `23_silver_conformance_activities` | `bridge_activity` — resolve polymorphic `regardingobjectid` |
| 30 | `30_silver_snapshot_facts` | Append daily snapshot rows |
| 40 | `40_gold_conformed_dimensions` | Publish conformed dimensions into Gold |
| 5x | *(per pack, future)* | Pack-specific Silver and Gold builds |

Rules:

- **Validation gates the run.** If `10_` fails, nothing downstream executes. A mapping
  error caught here is cheap; the same error caught in UAT is expensive and damages trust.
- **Snapshots run before Gold, and run every day regardless of whether Gold is rebuilt.**
  Losing a Gold rebuild costs a rerun. Losing a snapshot costs a day of history
  permanently — see [`snapshot-and-history.md`](snapshot-and-history.md).
- **Conformance runs before any pack logic.** No exceptions.
- **Idempotency:** everything except snapshot appends must be safely re-runnable. Snapshot
  writes are append-only and guarded against double-writing the same date.

## Refresh cadence

| Layer | Cadence | Note |
|---|---|---|
| Bronze | Continuous | Managed by Link to Fabric; not ours to schedule |
| Silver conformance | Configurable, typically daily | Cheap to run more often if a customer needs it |
| Silver snapshots | **Daily, fixed UTC time** | Must not drift — jagged snapshot timing produces jagged trends |
| Gold | Configurable, typically daily after conformance | |
| Semantic models | After Gold completes | Orchestrated, not independently scheduled, to avoid refreshing against a half-built Gold |

Cadence is a per-customer configuration value, not a constant. See `platform/config/`.

## Separation of concerns

- **Silver answers "is this data correct and complete?"** Conformance, history, keys,
  cleansing. Pack-agnostic.
- **Gold answers "is this data shaped for this business question?"** Star schemas,
  aggregation, pack-specific denormalization.
- **The semantic model answers "how is this measured?"** DAX measures implementing
  `metrics.yaml`. No business logic belongs in Gold that the model should own, and no data
  correction belongs in the model that Silver should own.

When a defect appears, that hierarchy decides where it gets fixed. Wrong labels or missing
rows are Silver bugs. Wrong grain or an unusable shape is a Gold bug. A wrong number from
correct data is a model bug.
