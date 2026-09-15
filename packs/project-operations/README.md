# Project Operations pack

**$5,000** · Dynamics 365 Project Operations · **Status: planned — SCOPE GATED**

> ## Read this before quoting
>
> **This pack must not be quoted until [ADR 0003](../../docs/decisions/0003-project-operations-scope.md)
> is resolved.**
>
> Project Operations has multiple deployment types, and **only "Lite" is purely
> Dataverse.** Resource/non-stocked and stocked deployments put actual cost, revenue, and
> financial posting partly in **Dynamics 365 Finance & Operations** — which does not ingest
> through Dataverse Link to Fabric.
>
> A $5,000 fixed-price pack sold without qualifying the deployment type can commit
> JourneyTeam to building an entire second ingestion path. That is not a scope overrun; it
> is a different project.
>
> It is also invisible to a salesperson: a customer says "we have Project Operations," and
> nothing in that sentence signals the difference.
>
> **Mandatory pre-sales question:** *which Project Operations deployment type is in use?*
> See [`../../docs/delivery/prerequisites-and-access.md`](../../docs/delivery/prerequisites-and-access.md).

## What it covers (scoped to Dataverse, per the ADR 0003 recommendation)

| Area | Questions answered |
|---|---|
| Delivery | Estimate vs. actual, schedule variance, milestone attainment |
| Profitability | Margin by project, customer, and project manager |
| Utilization | Billable vs. non-billable, utilization against target |
| WIP | Work in progress, unbilled revenue |
| Resourcing | Assignment vs. capacity, bench time |
| Contracts | Contract value, invoiced vs. remaining |

## Why fourth in the build sequence

It is the only pack with a genuine architectural fork. Building it earlier would either
delay three packs that have no such problem, or force an F&O ingestion decision
prematurely.

## Depends on

- The full [conformance layer](../../docs/architecture/conformance-layer.md)
- [Conformed dimensions](../_shared/conformed-dimensions.md): `dim_date`, `dim_owner`,
  `dim_customer`, `dim_currency`, `bridge_activity`, plus `dim_project` and `dim_resource`
  which **this pack creates as conformed dimensions**
- `fact_project_snapshot`
- **`salesorder` / `salesorderdetail`** — in Project Operations the project contract is
  built on these, which makes them a shared join point with the Sales pack and the key
  link for [Revenue-to-Delivery](../revenue-to-delivery/)

## Known limitations

State these plainly in every proposal for this pack.

1. **Finance & Operations-resident financial data is OUT OF SCOPE.** For
   resource/non-stocked and stocked deployments, this means posted financials, full cost
   detail, and general-ledger-tied revenue are not included.
2. **Margin analysis is therefore PARTIAL for F&O-backed customers** — sourced from
   Dataverse-side estimates and actuals rather than posted financials. A customer who
   discovers this at UAT has a legitimate grievance. Say it upfront.
3. **Utilization requires capacity to be maintained.** Resource capacity and target
   utilization must exist in Dataverse or be supplied; many customers do not maintain them.
4. **Time and expense approval state matters.** Unapproved time entries will distort
   actuals unless filtered — agree the treatment at kickoff.
5. **Snapshot history begins at Sprint 1.** WIP and margin trends look short at go-live.
6. **Custom fields are not included.**

## Open questions for the first build

- **Which deployment type?** (blocking — see above)
- Are project templates and WBS used consistently, or is scheduling ad hoc?
- Is `msdyn_actual` the reliable source of actuals for this deployment, or does it only
  carry part of the picture?
- Are resource capacity and target utilization maintained?
- How is billable vs. non-billable distinguished?
- Should unapproved time entries be included in actuals?
- Are project contracts always used, or are some projects internal / non-contracted?
