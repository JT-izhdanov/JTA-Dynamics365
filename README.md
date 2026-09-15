# JourneyTeam Analytics for Dynamics 365 Customer Engagement

Everything concerning the **JourneyTeam Analytics for Dynamics 365 CE** offering: the
commercial definition, the reference architecture, the reusable Fabric and Power BI IP,
and the delivery playbook used to deploy it into a customer tenant.

This is the Customer Engagement edition of the JourneyTeam Analytics portfolio. It is a
sibling to the Business Central edition and is designed to land in the same OneLake, so a
customer running both Dynamics families gets one analytics platform rather than two.

> **Internal JourneyTeam repository.** Contains offering pricing, margin logic, and
> delivery IP. Do not share outside JourneyTeam. Customer-specific configuration must
> never be committed here — see [Customer configuration](#customer-configuration).

## What the offering is

A packaged Microsoft Fabric and Power BI solution for Dynamics 365 Customer Engagement.
Dataverse data is shortcut into OneLake via **Link to Microsoft Fabric** (no ETL, no copy),
refined through a medallion architecture, and surfaced through pre-built semantic models
and report packs for four apps:

| Report pack | Dynamics 365 app |
|---|---|
| Sales | Dynamics 365 Sales |
| Customer Service | Dynamics 365 Customer Service |
| Project Operations | Dynamics 365 Project Operations |
| Field Service | Dynamics 365 Field Service |
| Revenue-to-Delivery | cross-app (Sales → Project Operations → Field Service) |

Because ingestion is first-party and effectively free, **the defensible IP in this offering
is not ingestion.** It is the Silver conformance layer, the snapshot history model, and the
cross-app semantic models. See [`docs/architecture/conformance-layer.md`](docs/architecture/conformance-layer.md).

## Repository layout

```
docs/
  offering/       Commercial definition — overview, positioning, pricing, roadmap
  architecture/   Reference architecture, medallion design, conformance layer, RLS, licensing
  decisions/      Architecture decision records (ADRs)
  delivery/       Prerequisites, sprint playbook, UAT, training, support handoff
  reference/      Analysis of existing artifacts that inform the offering
platform/
  notebooks/      Fabric notebooks — Bronze validation, Silver conformance, snapshots, Gold
  pipelines/      Fabric pipeline and scheduling definitions
  config/         Deployment configuration schema and example
packs/
  _shared/        Conformed dimensions and shared metric definitions
  sales/          Per-pack: source table mapping, metric definitions, model, reports
  customer-service/
  project-operations/
  field-service/
  revenue-to-delivery/
sales-assets/     Customer-facing deck, one-pagers, demo script
```

## Start here

| If you are... | Read |
|---|---|
| Selling this | [`docs/offering/overview.md`](docs/offering/overview.md), [`pricing-and-packaging.md`](docs/offering/pricing-and-packaging.md), [`positioning.md`](docs/offering/positioning.md) |
| Scoping an engagement | [`docs/delivery/prerequisites-and-access.md`](docs/delivery/prerequisites-and-access.md), [`docs/decisions/0003-project-operations-scope.md`](docs/decisions/0003-project-operations-scope.md) |
| Delivering an engagement | [`docs/delivery/playbook.md`](docs/delivery/playbook.md) |
| Working on the JTP first build | [`docs/delivery/jtp-first-build-plan.md`](docs/delivery/jtp-first-build-plan.md) |
| Building or extending the IP | [`docs/architecture/reference-architecture.md`](docs/architecture/reference-architecture.md), [`platform/README.md`](platform/README.md) |
| Building a report pack | [`packs/README.md`](packs/README.md) |

## Status

The offering is in **definition and initial build**. Nothing in `platform/` or `packs/` has
been validated against a live Dataverse environment yet. Every source table mapping and
notebook in this repository is a **draft pending first-build validation** — see
[Validation status](docs/architecture/reference-architecture.md#validation-status) for what
that means and what has to happen before customer delivery.

## Customer configuration

Deployment is parameterized per customer. `platform/config/customer.example.yaml` is the
template; real customer configuration lives in the engagement's own secure location, never
in this repository. No tenant IDs, workspace IDs, environment URLs, connection strings,
secrets, or customer data belong in any commit here.

## Contributing

- One change per pull request, scoped to a single pack or platform concern.
- Architectural or commercial choices get an ADR in `docs/decisions/` — see that folder's README.
- Changes to pricing, packaging, or the competitive comparison require offering-owner sign-off.
- Keep `CHANGELOG.md` current for anything that changes what gets delivered to a customer.
