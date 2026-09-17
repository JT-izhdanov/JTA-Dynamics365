# Notebooks

> **Draft, never executed.** Written from general Dataverse knowledge, not from a validated
> environment. Expect errors. See [`../README.md`](../README.md#getting-the-first-build-right).

## Execution order

Numbered by medallion stage. Run in numeric order.

| Order | Notebook | Produces |
|---|---|---|
| 10 | `10_bronze_shortcut_validation.py` | Pass/fail gate — expected tables, columns, and rows exist |
| 20 | `20_silver_conformance_choice_labels.py` | `silver.lkp_choice_label` |
| 21 | `21_silver_conformance_currency.py` | `silver.dim_currency` + currency normalization helpers |
| 22 | `22_silver_conformance_ownership.py` | `silver.dim_owner` (SCD2, BU + manager hierarchies) |
| 23 | `23_silver_conformance_activities.py` | `silver.bridge_activity` |
| 24 | `24_silver_conformance_date.py` | `silver.dim_date` with the customer's fiscal calendar |
| 30 | `30_silver_snapshot_facts.py` | Daily append to `silver.fact_*_snapshot` |
| 40 | `40_gold_conformed_dimensions.py` | Conformed dimensions published into `gold` |
| 5x | *(not yet written)* | Remaining conformed dimensions — dim_customer, dim_contact, dim_product, dim_territory, dim_resource |
| 6x | *(not yet written)* | Sales Silver and Gold builds |

`10` gates the run. Conformance (`2x`) precedes everything. `30` runs daily regardless of
whether Gold is rebuilt.

## Conventions

- **Numbering:** `10` Bronze, `2x` Silver conformance, `3x` snapshots, `4x` Gold, `5x` packs.
- **Configuration in, nothing hard-coded.** Every notebook reads
  [`../config/`](../config/) — no environment identifier, table list, fiscal calendar, or
  currency literal in notebook source.
- **Idempotent** except snapshot appends, which are guarded against double-writing a date.
- **Never write to Bronze.**
- **Fail loudly.** A silent partial success in the conformance layer becomes a wrong number
  in a report three weeks later. Raise, do not warn-and-continue.
- **Commit with output cleared.** Notebook output can contain customer data.
- **`<!-- VERIFY -->` / `# VERIFY:`** marks anything unconfirmed against a live environment.
  Resolve during the first build; do not delete the marker without confirming.

## Authoring format

Plain `.py`, written so cells can be pasted into a Fabric notebook. Cell boundaries are
marked with `# ---- CELL ----`.

This is deliberately not Fabric's own git-integration format yet — see
[`../README.md`](../README.md#future-fabric-git-integration). Once the first build
stabilizes, migrate and record it as an ADR.

## Spark and lakehouse assumptions

- Tables are written as Delta into the `silver` and `gold` schemas of `jta_lakehouse`.
- Bronze is read through the Link to Fabric shortcut under the `bronze` schema.
- `spark` and `notebookutils` are provided by the Fabric runtime.

> `# VERIFY:` Confirm how the Link to Fabric shortcut actually surfaces in the lakehouse —
> schema name, table naming, and whether tables are directly queryable as Delta or require
> a different access path. Every notebook's Bronze read depends on this, so resolve it
> first.
