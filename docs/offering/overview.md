# Offering overview

**JourneyTeam Analytics for Dynamics 365 Sales**

> **Repository scope: Sales only.** The Customer Engagement offering as a whole was
> designed around four report packs. This repository covers **Sales**; the others are
> deferred and not documented here. See [`roadmap.md`](roadmap.md).

## Executive summary

| | |
|---|---|
| **Offer** | JourneyTeam Analytics for Dynamics 365 Sales |
| **Description** | Packaged Microsoft Fabric and Power BI solution for Dynamics 365 Sales — Dataverse shortcut into OneLake, medallion data layer, pre-built semantic model, and a ready-to-use report pack |
| **Target market** | New and existing Dynamics 365 Sales customers |
| **Price** | **Open** — see [`pricing-and-packaging.md`](pricing-and-packaging.md) |
| **Delivery** | 4–5 weeks |

## High-level goals

- Offer a low-cost, high-impact data and analytics architecture to Dynamics 365 Sales
  customers.
- Drive Fabric and Power BI adoption by removing the technical barriers to a self-service
  BI experience.
- Align customers to the Microsoft data and analytics roadmap.
- Create a repeatable, high-margin delivery motion rather than bespoke project work.
- Establish the Fabric platform as a landing zone that later Dynamics apps can be added to
  without rebuilding.

## What the customer gets

1. **Link to Microsoft Fabric configured** — Dataverse data in OneLake, near-real-time,
   zero copy.
2. **A medallion data platform** — Bronze raw shortcut, Silver conformance and history,
   Gold business-ready models.
3. **The Dataverse conformance layer** — choice labels resolved, currency normalised,
   ownership hierarchy flattened, dates conformed, RLS scaffolded.
4. **Snapshot history** — point-in-time pipeline and forecast movement that Dataverse
   itself cannot provide.
5. **A pre-built Power BI semantic model and report pack** for Sales.
6. **A SQL endpoint and Excel connectivity** for self-service analysis.
7. **Coaching and Copilot enablement** so the platform is actually used.

## The Sales pack

| Area | Questions answered |
|---|---|
| Pipeline | What is in the pipeline, by stage, owner, territory, product? **What did it look like on any past date?** |
| Conversion | Win rate, loss reasons, lead-to-opportunity conversion |
| Velocity | Sales cycle length, time in stage, where deals stall |
| Forecast | Forecast vs. actual, slippage, coverage against target |
| Activity | Touches per opportunity, activity-to-outcome correlation |
| Performance | Attainment by owner, team, business unit, territory |

Full metric definitions: [`../../packs/sales/metrics.yaml`](../../packs/sales/metrics.yaml).

## Why this is defensible

Ingestion is first-party and free, so it cannot be the differentiator. The offering is
defensible on two things Microsoft's own analytics do not do:

1. **The conformance layer.** Dataverse is hostile to BI in consistent, repeatable ways.
   Solving that once as versioned IP is the product. See
   [`../architecture/conformance-layer.md`](../architecture/conformance-layer.md).
2. **History.** Dataverse is a current-state store. Nothing first-party gives point-in-time
   pipeline or forecast movement. See
   [`../architecture/snapshot-and-history.md`](../architecture/snapshot-and-history.md).

A third — cross-app models spanning several Dynamics apps — is central to the offering's
longer-term story and is **intended**, but it needs a second pack before it has anything to
span. It is not in scope here and must not be sold, implied, or shown as a roadmap item
until it exists. See [`roadmap.md`](roadmap.md#what-narrowing-costs-now-and-what-it-does-not)
for what is being kept general so it stays cheap to add.

## Relationship to the Business Central offering

| | Business Central edition | This offering |
|---|---|---|
| Ingestion | Custom BC2Fabric AL extension (JT-built, JT-maintained) | Link to Fabric (first-party, zero-copy) |
| Bronze layer | Real work — table selection, delta scheduling | Near-free — shortcut lands raw tables |
| Primary effort | Extension plus medallion | Silver conformance layer |
| Ingestion upgrade risk | JourneyTeam owns the lifecycle | Microsoft owns the lifecycle |
| Time to first data | Days | Hours |

Both land in the same OneLake, so a customer running both gets one platform rather than
two — and the second engagement carries far less setup cost.

## Open decisions

Tracked as ADRs in [`../decisions/`](../decisions/):

- [0002](../decisions/0002-offering-naming.md) — portfolio naming across editions
- **Pricing** — the package structure depended on choosing among four packs and no longer
  works. See [`pricing-and-packaging.md`](pricing-and-packaging.md)
