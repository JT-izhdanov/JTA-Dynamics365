# Conformed dimensions

Shared across every pack. Built by the conformance notebooks in
[`../../platform/notebooks/`](../../platform/notebooks/) and published into Gold as views
by `40_gold_conformed_dimensions`.

**A pack consumes these. It never copies or redefines them.** See
[`../README.md`](../README.md#the-rule-that-matters-most).

> **Draft.** Column lists are written from general Dataverse knowledge, not validated
> against a live environment. Correct them during the first build.

## Inventory

| Dimension | Built by | Grain | SCD | Used by |
|---|---|---|---|---|
| `dim_date` | `24_` | day | n/a | all |
| `dim_owner` | `22_` | owner version | **SCD2** | all, and RLS |
| `dim_currency` | `21_` | currency | Type 1 | all with money |
| `dim_customer` | `5x_` | account version | **SCD2** | all |
| `dim_contact` | `5x_` | contact | Type 1 | all |
| `dim_product` | `5x_` | product version | **SCD2** | Sales, Field Service, Project Ops |
| `dim_territory` | `5x_` | territory | Type 1 | Sales, Field Service |
| `dim_project` | `5x_` | project | Type 1 | Project Ops, Revenue-to-Delivery |
| `dim_resource` | `5x_` | resource | Type 1 | Field Service, Project Ops |
| `lkp_choice_label` | `20_` | table × column × value | n/a | every Silver build |
| `bridge_activity` | `23_` | activity | n/a | all |

`dim_customer`, `dim_contact`, `dim_product`, `dim_territory`, `dim_project`, and
`dim_resource` are not yet built — the `5x_` notebooks do not exist. They are specified
here so the first pack build creates them as *conformed* dimensions rather than
pack-local ones.

## Why SCD2 on only some

SCD2 everywhere is a cost with no benefit. SCD2 where history is actually queried is
essential.

- **`dim_owner`** — territory and manager reassignment is constant in sales organizations.
  Attributing last year's results to this year's manager is wrong.
- **`dim_customer`** — segment, industry, and account owner change.
- **`dim_product`** — category and pricing change.

Everything else is Type 1 unless a metric in a `metrics.yaml` requires otherwise.

**Critical:** SCD2 surrogate keys are generated **per version, not per entity**. If
`owner_key` identified the owner rather than the owner-version, historical snapshots would
silently re-attribute to today's org structure as people change jobs — and last quarter's
published numbers would change. Snapshot facts join the full versioned Silver dimension;
Gold views expose current rows only for normal reporting.

## Key conventions

| Suffix | Meaning |
|---|---|
| `_guid` | The Dataverse GUID, retained and documented |
| `_key` | Surrogate key, used for model relationships |

Dataverse GUIDs work as natural keys but perform poorly at volume in a Power BI model and
are unreadable when debugging. Both are kept: `_key` for relationships, `_guid` for
traceability back to the source record.

## dim_date

Built from the customer's fiscal calendar, which is configuration, not a constant.

Calendar attributes, fiscal attributes (`fiscal_year`, `fiscal_quarter`,
`fiscal_month_number`, `fiscal_period_label`), month boundary flags, and relative flags
(`is_today`, `is_past`, `days_from_today`).

**Not yet built:** the holiday and working-day calendar. Required by any metric measured in
business hours — which includes several headline Customer Service and Field Service
metrics. Until it exists, those metrics are calendar-hours and **must be labelled as such
in `metrics.yaml`**. An SLA metric that silently ignores weekends is wrong in a way
customers notice immediately.

## dim_owner

Covers **both users and teams** — records can be owned by either, and omitting teams loses
owner attribution on team-owned records entirely.

Carries the flattened business unit path (`bu_level_1` … `bu_level_N`) and manager chain
(`manager_level_1` … `manager_level_N`), both to configured depth.

This single artifact serves two purposes: the reporting dimension, and the source of the
RLS model. That is deliberate — see
[`../../docs/architecture/security-and-rls.md`](../../docs/architecture/security-and-rls.md).

**Caveat:** the manager chain requires `systemuser.parentsystemuserid` to be maintained.
Many customers do not maintain it. Notebook 22 reports the fill rate; if it is sparse,
manager-based RLS and manager rollup reporting are not viable, and that is a scoping
finding to raise rather than work around.

## dim_currency

Currency codes, names, symbols, precision, and `is_base_currency`.

The conformance layer exposes both transaction and base amounts on every money column,
suffixed `_txn` and `_base`, and **never silently converts**. The report packs default to
base amounts.

**The trap:** the rate stored on a Dataverse record is the rate at write time, not today's
rate. Usually correct for financial reporting; usually wrong for pipeline comparison. Every
money metric declares its `currency_basis` in `metrics.yaml` for exactly this reason.

## lkp_choice_label

One conformed lookup keyed by `(table_name, column_name, option_value)` resolving
Dataverse choice integers to labels.

Every Silver build joins to it. **Never hard-code a `CASE` statement** — a hard-coded
mapping is invisible when the customer adds a status reason, which is precisely when it
starts being wrong.

Joins are left joins deliberately: an unmapped value must surface as NULL and be
investigated, not silently drop the fact row.

> The metadata source for this is the **single most important unresolved item** in the
> platform. See the VERIFY block in
> [`20_silver_conformance_choice_labels.py`](../../platform/notebooks/20_silver_conformance_choice_labels.py).

## bridge_activity

One row per activity with a typed nullable key per target entity, resolving the
polymorphic `regardingobjectid`.

Lets a pack model join activities with a normal relationship instead of re-solving
polymorphism in DAX. Activity analytics — touches per opportunity, response time on a case,
contact cadence — is among the highest-value question sets and the most annoying to build,
so it is solved once here.

## Conformed status groupings

Dataverse has two related columns on most tables: `statecode` (coarse lifecycle) and
`statuscode` (specific reason within it). Their meaning differs per table, and using one
without the other is a common source of wrong counts.

The conformance layer decodes both, keeps both, and adds a **conformed status grouping** per
table — `Open` / `Won` / `Lost` / `Cancelled` and equivalents — so cross-app reports can
reason about lifecycle consistently.

Raw integers are never exposed to the semantic model.
