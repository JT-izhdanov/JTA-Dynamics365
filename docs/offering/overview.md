# Offering overview

**JourneyTeam Analytics for Dynamics 365 Customer Engagement**

## Executive summary

| | |
|---|---|
| **Offer** | JourneyTeam Analytics for Dynamics 365 Customer Engagement |
| **Description** | Packaged Microsoft Fabric and Power BI solution for Dynamics 365 CE — Dataverse shortcut into OneLake, medallion data layer, pre-built multi-dimensional semantic models, and ready-to-use report packs |
| **Target market** | New and existing Dynamics 365 CE customers running Sales, Customer Service, Project Operations, or Field Service |
| **Entry price** | $15,000 fixed (BASE package) |
| **Delivery** | 6 weeks, three sprints |

## High-level goals

- Offer a low-cost, high-impact data and analytics architecture to Dynamics 365 CE customers.
- Drive Fabric and Power BI adoption by removing the technical barriers to a self-service BI
  experience.
- Align customers to the Microsoft data and analytics roadmap and vision.
- Create a repeatable, high-margin delivery motion for JourneyTeam rather than bespoke
  project work.
- Establish the Fabric platform as the landing zone for *every* Dynamics app a customer
  runs, making the second and third engagement easier to sell than the first.

## What the customer gets

1. **Link to Microsoft Fabric configured** — Dataverse data in OneLake, near-real-time, zero copy.
2. **A medallion data platform** — Bronze raw shortcut, Silver conformance and history,
   Gold business-ready models.
3. **The Dataverse conformance layer** — choice labels resolved, currency normalized,
   ownership hierarchy flattened, dates conformed, RLS scaffolded.
4. **Snapshot history** — point-in-time pipeline, case aging, and backlog trend that
   Dataverse itself cannot provide.
5. **Pre-built Power BI semantic models and report packs** for the apps they selected.
6. **A SQL endpoint and Excel connectivity** for self-service analysis.
7. **Coaching and Copilot enablement** so the platform is actually used.

## The four report packs

| Pack | Dynamics 365 app | Headline metrics |
|---|---|---|
| **Sales** | Sales | Pipeline by stage as-of-date, win rate, sales cycle, velocity, forecast vs. actual |
| **Customer Service** | Customer Service | First-response and resolution time, SLA attainment, backlog aging, reopen rate, agent load |
| **Project Operations** | Project Operations | Estimate vs. actual, margin by project, utilization vs. target, WIP, unbilled revenue |
| **Field Service** | Field Service | First-time fix rate, travel vs. wrench time, technician utilization, SLA adherence, PM compliance |
| **Revenue-to-Delivery** | cross-app | Opportunity → contract → project → work order → realized margin, end to end |

Full metric definitions live in `packs/<pack>/metrics.yaml`.

## Why this is defensible

Ingestion is first-party and free, so ingestion cannot be the differentiator. The offering
is defensible on three things Microsoft's own analytics do not do:

1. **The conformance layer.** Dataverse is hostile to BI in consistent, repeatable ways.
   Solving that once as versioned IP is the product. See
   [`../architecture/conformance-layer.md`](../architecture/conformance-layer.md).
2. **History.** Dataverse is a current-state store. Nothing first-party gives point-in-time
   pipeline or case aging. See [`../architecture/snapshot-and-history.md`](../architecture/snapshot-and-history.md).
3. **Cross-app.** The four apps share Dataverse, so a revenue-to-delivery model is
   architecturally cheap for us and does not exist in any first-party app.

## Relationship to the Business Central offering

| | Business Central edition | Customer Engagement edition |
|---|---|---|
| Ingestion | Custom BC2Fabric AL extension (JT-built, JT-maintained) | Link to Fabric (first-party, zero-copy) |
| Bronze layer | Real work — table selection, delta scheduling | Near-free — shortcut lands raw tables |
| Primary effort | Extension plus medallion | Silver conformance layer |
| Ingestion upgrade risk | JourneyTeam owns the lifecycle | Microsoft owns the lifecycle |
| Time to first data | Days | Hours |
| Delivery timeline | 8 weeks | 6 weeks |

Both editions land in the same OneLake. For a customer running BC and CE, the combined
platform is a materially larger deal than either package sold alone, and the second
edition carries far less setup cost.

## Open decisions

Tracked as ADRs in [`../decisions/`](../decisions/):

- [0002](../decisions/0002-offering-naming.md) — portfolio naming across editions
- [0003](../decisions/0003-project-operations-scope.md) — Project Operations deployment scope
- [0004](../decisions/0004-cross-app-pack-packaging.md) — whether Revenue-to-Delivery is add-on or PREMIUM-only
