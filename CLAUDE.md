# Context for AI sessions in this repository

## What this repository is

The home of the **JourneyTeam Analytics for Dynamics 365 Sales** offering — a packaged
Fabric + Power BI solution sold to Dynamics 365 Sales customers. It holds the commercial
definition of the offering, the reference architecture, the reusable Fabric and Power BI IP,
and the delivery playbook.

It is a sibling to the JourneyTeam Analytics for Business Central offering. Keep the two
consistent in structure, pricing ladder, and naming — they are sold as one portfolio.

## Scope

**This repository covers Dynamics 365 Sales only.** The offering was originally designed
around four Customer Engagement report packs (Sales, Customer Service, Project Operations,
Field Service) plus a cross-app Revenue-to-Delivery pack. Those are **deferred**: their
drafts were removed and the analysis is recoverable from git history — see
`docs/offering/roadmap.md`.

Do not reintroduce Customer Service, Project Operations, Field Service, or cross-app
content into this repository unless the offering owner brings a pack back into scope. Keep
the *platform* generic where that costs nothing (the conformance layer is deliberately
app-agnostic), but do not document or price a pack that does not exist here.

## The core architectural fact

Dynamics 365 Sales sits on **Dataverse**. Dataverse data reaches OneLake through **Link to
Microsoft Fabric** — a first-party, zero-copy shortcut. There is no custom extension and no
ETL for ingestion.

The consequence, which shapes everything in this repo: **ingestion is not the IP.** Anyone
can enable Link to Fabric. The defensible value is:

1. The **Silver conformance layer** that makes Dataverse usable for BI (choice labels,
   currency normalization, polymorphic activities, state/status, ownership hierarchy).
2. **Snapshot facts** — Dataverse stores current state only, so point-in-time pipeline,
   forecast movement, and aging do not exist in any first-party report. We build them.

When making design or documentation choices, protect those two things.

A third differentiator — cross-app semantic models spanning several Dynamics apps — was
central to the original design and is out of scope with one pack. It was the only
differentiator with no first-party equivalent, so note the gap when positioning; do not
quietly claim it.

## Conventions

- **Dataverse table names** are lowercase logical names (`account`, `opportunity`,
  `opportunityproduct`, `systemuser`). Always use logical names, never display names.
- **Notebooks** live in `platform/notebooks/` as plain `.py` authoring drafts, numbered by
  medallion stage (`10_` Bronze, `2x_` Silver conformance, `3x_` snapshots, `4x_` Gold).
  See `platform/notebooks/README.md` before adding one.
- **Metric definitions** are YAML in `packs/<pack>/metrics.yaml` and are the source of
  truth for what a measure means. The Power BI model implements them; it does not define them.
- **Source table mappings** are `packs/<pack>/source-tables.md`.
- **Decisions** that affect architecture, scope, or commercials get an ADR in
  `docs/decisions/`, numbered sequentially.
- Prices and package contents appear in exactly one place:
  `docs/offering/pricing-and-packaging.md`. Reference it; do not restate numbers elsewhere.

## Accuracy rules — important

Nothing in `platform/` or `packs/` has been validated against a live Dataverse
environment. Dataverse schema varies by solution version and by which apps a customer has
installed.

- Source table and column mappings are **drafts**. Do not present them as verified.
- Do not invent Dataverse table or column names. If you are not confident one exists, mark
  it `<!-- VERIFY -->` and say so in your response rather than guessing silently.
- Do not claim a notebook or model works. None have been run. Say what is untested.
- Microsoft licensing, pricing, and capacity terms change. Do not restate them from
  memory into customer-facing content — `docs/architecture/licensing-and-capacity.md`
  flags the items that must be re-verified against current Microsoft documentation.

## Security and confidentiality

- Never commit tenant IDs, environment URLs, workspace IDs, app registration IDs,
  secrets, connection strings, or any customer data — including in example configs,
  notebook output, or screenshots.
- `platform/config/customer.example.yaml` uses placeholders only.
- This repository contains internal pricing and margin logic. Do not reproduce it into
  anything customer-facing beyond what `sales-assets/` explicitly approves.

## Change control

Changes to JourneyTeam's own internal Microsoft environments follow JourneyTeam change
control — development and testing happen in Dev/Sandbox, never directly in Production.
Work inside a *customer's* tenant follows that customer's change process instead.
