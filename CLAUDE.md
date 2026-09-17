# Context for AI sessions in this repository

## What this repository is

The home of the **JourneyTeam Analytics for Dynamics 365 Sales** offering — a packaged
Fabric + Power BI solution sold to Dynamics 365 Sales customers. It holds the commercial
definition of the offering, the reference architecture, the reusable Fabric and Power BI IP,
and the delivery playbook.

It is a sibling to the JourneyTeam Analytics for Business Central offering. Keep the two
consistent in structure, pricing ladder, and naming — they are sold as one portfolio.

## Scope

**This repository is the working space for Dynamics 365 Sales.** The offering was
originally designed around four Customer Engagement report packs (Sales, Customer Service,
Project Operations, Field Service) plus a cross-app Revenue-to-Delivery pack. Those are
**deferred, not abandoned** — cross-app functionality is intended and will be built. Their
drafts were removed from this repository and are recoverable from git history; see
`docs/offering/roadmap.md`.

Two rules follow, and they pull in different directions on purpose:

- **Do not document, price, quote, or position a pack that does not exist here.** Sales is
  the only pack. "Coming later" on a slide is the same mistake as claiming it today.
- **Do not make cross-app harder to add later.** Keep the platform app-agnostic where that
  costs nothing now: conformed dimensions stay conformed and unprefixed, Gold keeps its
  `sales__` pack prefix, and the activity bridge stays polymorphic. Cross-app will be built
  on top of exactly these artifacts, so a Sales-local shortcut taken today is a rebuild
  later. Where a choice is cheap now and expensive to reverse, take the general one and say
  why in the file.

Adding Customer Service, Project Operations, Field Service, or cross-app *content* back is
the offering owner's call, not a drive-by.

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

A third — **cross-app semantic models** spanning several Dynamics apps — is central to the
offering's long-term story and is planned, but does not exist yet. It is the only one of
the three with no first-party equivalent, which makes it the most valuable and the most
tempting to over-claim. Two consequences:

- **Positioning:** do not claim it, imply it, or show it as a roadmap slide until a second
  pack exists. Sell the conformance layer and history, which are real today.
- **Design:** protect it anyway. Point 3 is the reason the platform is built app-agnostic
  rather than Sales-shaped.

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
