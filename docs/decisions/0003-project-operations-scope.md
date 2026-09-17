# 0003 — Project Operations pack deployment scope

**Status:** **Deferred** — Project Operations is out of scope for this repository

> **Deferred, not cancelled — 2026-09-17.** The repository was narrowed to Dynamics 365
> Sales as its working space, so this decision is not live. It is the **first thing to
> answer if a delivery-side pack returns**, which is the cheapest route back to the
> cross-app functionality that is still intended — see
> [`../offering/roadmap.md`](../offering/roadmap.md#what-narrowing-costs-now-and-what-it-does-not).
> The body below is unedited.


## Context

Every other pack in this offering reads from Dataverse and nothing else. Project
Operations is the exception, and it is the single largest scope risk in the offering.

Dynamics 365 Project Operations has multiple deployment types:

| Deployment type | Where the data lives |
|---|---|
| **Lite** — deal to proforma invoice | Dataverse only |
| **Resource / non-stocked** | Dataverse **plus Dynamics 365 Finance & Operations** for actuals, costing, and financial posting |
| **Stocked / production order** | Dataverse plus F&O, with deeper supply chain involvement |

> `<!-- VERIFY -->` Confirm the current deployment type names and exactly which data
> resides where at the customer's version before scoping any Project Operations engagement.
> Microsoft has revised this model over time.

The problem: **only Lite is purely Dataverse.** The other types put precisely the data a
project analytics pack is most wanted for — actual cost, revenue, margin, financial
posting — partly in F&O. And F&O does not ingest through Dataverse Link to Fabric the way
CE apps do ([ADR 0001](0001-use-link-to-fabric-for-ingestion.md)).

So a $5,000 fixed-price pack, sold without qualifying the deployment type, can quietly
commit JourneyTeam to building an entire second ingestion path. That is not a scope
overrun; it is a different project.

It is also not obvious to a salesperson. A customer says "we have Project Operations," and
nothing about that sentence signals the difference.

## Options

1. **Scope the pack to Lite plus Dataverse-side data only**, at $5,000. Anything F&O-backed
   is qualified out and scoped as additional development.
2. **Build both**, and price an F&O-backed variant higher (perhaps $10,000–$12,500).
3. **Two distinct packs** — "Project Operations (Dataverse)" and "Project Operations
   (F&O-backed)."
4. **Defer the pack entirely** until a Finance & Operations edition exists.

## Recommendation

**Option 1.**

- Project Operations is fourth in the build sequence
  ([`../offering/roadmap.md`](../offering/roadmap.md#sales-pack-build-order)) — so
  taking on an F&O ingestion path now would delay three packs that have no such problem.
- F&O ingestion is a **separate edition**, not a pack. Building it as a pack side effect
  would be the wrong place to solve it and would produce an ingestion path nobody owns.
- Option 1 keeps the pack honest at $5,000 and keeps the qualification question where it
  belongs: pre-sales.
- The F&O demand is real, and the right response is a scoped Finance & Operations edition
  with its own ingestion architecture — already a roadmap candidate.

**If Option 1 is accepted, three things must follow:**

1. **A pre-sales qualification question**, mandatory before quoting the pack: *"Which
   Project Operations deployment type is in use?"* Added to
   [`../delivery/prerequisites-and-access.md`](../delivery/prerequisites-and-access.md).
2. **An explicit proposal exclusion** stating that F&O-resident financial data is out of
   scope. A customer who discovers this at UAT has a legitimate grievance.
3. **`packs/project-operations/source-tables.md` scoped to Dataverse tables only**, with a
   clearly marked section listing what is *not* covered and why.

## Consequences

**If accepted:**

- The pack stays deliverable at a fixed price and on the 6-week timeline.
- Some Project Operations customers will be told the pack covers less than they hoped.
  Better a narrow honest scope than a wide one that cannot be delivered.
- Margin analysis for resource/non-stocked customers will be partial — sourced from
  Dataverse-side estimates and actuals rather than F&O posted financials. This limitation
  must be stated plainly in the pack README, not buried.
- PREMIUM remains fully deliverable, which is a deliberate advantage over the BC edition.

**If rejected in favor of Option 2 or 3:**

- Project Operations moves to last in the build sequence.
- An F&O ingestion ADR becomes a prerequisite.
- The pricing table in [`../offering/pricing-and-packaging.md`](../offering/pricing-and-packaging.md)
  needs a second Project Operations line, and PREMIUM's contents need restating.

## Open question for the decision-maker

What share of JourneyTeam's Project Operations installed base is Lite versus F&O-backed?
If it is overwhelmingly F&O-backed, Option 1 scopes the pack down to something few
customers can use, and Option 4 — defer until the F&O edition exists — becomes the better
answer. **This should be checked against the actual customer base before deciding.**
