# Project Operations pack — source tables

> **DRAFT — NOT VALIDATED, AND SCOPE GATED.** Read
> [ADR 0003](../../docs/decisions/0003-project-operations-scope.md) and the
> [pack README](README.md) first. Scoped to **Dataverse tables only**; Finance &
> Operations-resident data is out of scope.
>
> Project Operations schema varies more between versions and deployment types than any
> other pack in this offering. Treat **everything** here as `VERIFY`.

Logical names, lowercase.

## Core tables

| Table | Role | Grain | Status |
|---|---|---|---|
| `msdyn_project` | Project fact + snapshot source | one row per project | `VERIFY` |
| `msdyn_projecttask` | Task / WBS | one row per task | `VERIFY` |
| `msdyn_estimateline` | Estimate line | one row per estimate line | `VERIFY` |
| `msdyn_actual` | Actuals | one row per actual | `VERIFY` — **critical, see below** |
| `msdyn_timeentry` | Time entry | one row per time entry | `VERIFY` |
| `msdyn_expense` | Expense | one row per expense | `VERIFY` |
| `msdyn_resourceassignment` | Assignment | one row per assignment | `VERIFY` |
| `bookableresource` | Resource | one row per resource | Shared with Field Service |
| `msdyn_projectteam` | Project team member | one row per member | `VERIFY` |
| `msdyn_invoice` / `msdyn_invoicelinedetail` | Project invoice | | `VERIFY` |
| `msdyn_milestone` | Contract milestone | | `VERIFY` |

## The contract is a salesorder

**Important and easy to miss:** in Project Operations the **project contract is built on
`salesorder`**, and contract lines on `salesorderdetail`.

| Table | Role in this pack |
|---|---|
| `salesorder` | Project contract |
| `salesorderdetail` | Contract line |
| `msdyn_orderlinetransaction` | Contract line detail | `VERIFY` |

Consequences:

- These tables are **shared with the Sales pack**, so the conformed treatment must satisfy
  both. Do not build a Project Operations-local version.
- They are the **key join point for [Revenue-to-Delivery](../revenue-to-delivery/)** —
  opportunity → quote → contract (`salesorder`) → project → work order.
- `VERIFY` this against the customer's Project Operations version and deployment type. It
  has held across versions but should not be assumed.

## Dimension sources

| Table | Produces | Note |
|---|---|---|
| `msdyn_project` | `dim_project` | **Conformed** — created by this pack, also used by Revenue-to-Delivery |
| `bookableresource` | `dim_resource` | **Conformed** — shared with Field Service |
| `account`, `contact` | `dim_customer`, `dim_contact` | Conformed, from the Sales pack build |
| `systemuser`, `team`, `businessunit` | `dim_owner` | Conformance layer |
| `transactioncurrency` | `dim_currency` | Conformance layer |
| `msdyn_transactioncategory` | transaction category | `VERIFY` |
| `msdyn_role` | resource role | `VERIFY` — needed for role-based rate and utilization |

`dim_project` and `dim_resource` are created here **as conformed dimensions in Silver**, not
as pack-local tables. Field Service depends on `dim_resource`; Revenue-to-Delivery depends
on `dim_project`.

## msdyn_project — columns

| Column | Purpose | Notes |
|---|---|---|
| `msdyn_projectid` | Key | |
| `msdyn_subject` | Label | |
| `statecode` / `statuscode` | Lifecycle | |
| `msdyn_projectstage` | Stage | `VERIFY` |
| `msdyn_scheduledstart` / `msdyn_scheduledend` | Planned dates | Schedule variance baseline |
| `msdyn_actualstart` / `msdyn_actualend` | Actual dates | `VERIFY` |
| `msdyn_totalbudgetcost` / `msdyn_totalactualcost` | Cost | **Partial for F&O-backed deployments** |
| `msdyn_totalbudgetsales` / `msdyn_totalactualsales` | Revenue | **Partial for F&O-backed deployments** |
| `msdyn_customer` | → `dim_customer` | `VERIFY` polymorphic handling |
| `msdyn_contractorganizationalunitid` | Org unit | `VERIFY` |
| `ownerid` / `owningbusinessunit` | → `dim_owner` / RLS | |
| `msdyn_projectmanager` | Project manager | `VERIFY` — distinct from ownerid |
| `createdon` / `modifiedon` | Audit | |

## msdyn_actual — the critical unknown

`msdyn_actual` is intended as the unified actuals table — cost and sales amounts for time,
expense, and material transactions.

**Whether it is complete depends on the deployment type.** For F&O-backed deployments,
posted financial detail lives in F&O and `msdyn_actual` may carry only part of the picture.

**This is the single most important thing to establish during the first build.** It
determines whether margin metrics in this pack are complete or approximate, and therefore
what the pack can honestly claim.

Expected columns — all `VERIFY`:

| Column | Purpose |
|---|---|
| `msdyn_actualid` | Key |
| `msdyn_project` | → `dim_project` |
| `msdyn_projecttask` | → task |
| `msdyn_bookableresource` | → `dim_resource` |
| `msdyn_transactiontypecode` | Cost vs. sales vs. unbilled |
| `msdyn_transactionclassification` | Time / expense / material |
| `msdyn_amount` / `msdyn_amount_base` | Amount |
| `msdyn_quantity` | Quantity (hours for time) |
| `msdyn_transactiondate` | `time_basis` |
| `msdyn_billingtype` | Billable / non-billable / complimentary |
| `msdyn_contractlineid` | → `salesorderdetail` |

`msdyn_transactiontypecode` and `msdyn_billingtype` carry most of the analytic weight —
cost vs. revenue and billable vs. non-billable both depend on them. Resolve their values
precisely before building any margin or utilization metric.

## msdyn_timeentry — columns

| Column | Purpose | Notes |
|---|---|---|
| `msdyn_timeentryid` | Key | |
| `msdyn_date` | Entry date | `time_basis` |
| `msdyn_duration` | Duration | `VERIFY` unit — minutes or hours |
| `msdyn_project` / `msdyn_projecttask` | Linkage | |
| `msdyn_bookableresource` | → `dim_resource` | |
| `msdyn_entrystatus` | Approval state | **Filter decision required** — see below |
| `msdyn_type` | Type | `VERIFY` |
| `msdyn_billingtype` | Billable flag | |

**Approval state matters.** Unapproved time entries will distort actuals and utilization.
Agree the treatment at kickoff — include all, approved only, or report both — and apply it
consistently across every metric.

## Choice columns requiring labels

| Table | Columns |
|---|---|
| `msdyn_project` | `statecode`, `statuscode`, `msdyn_projectstage` |
| `msdyn_actual` | `msdyn_transactiontypecode`, `msdyn_transactionclassification`, `msdyn_billingtype` |
| `msdyn_timeentry` | `msdyn_entrystatus`, `msdyn_type`, `msdyn_billingtype` |
| `salesorder` | `statecode`, `statuscode` |

## Explicitly not in scope

- **Anything resident in Dynamics 365 Finance & Operations** — posted financials, full cost
  detail, GL-tied revenue. See [ADR 0003](../../docs/decisions/0003-project-operations-scope.md)
- Subcontracting and procurement detail where it lives in F&O
- Stocked / production-order deployment scenarios
- Custom fields and tables
