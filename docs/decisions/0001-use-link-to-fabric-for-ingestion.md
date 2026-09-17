# 0001 — Use Link to Microsoft Fabric for ingestion

**Status:** Accepted

## Context

The Business Central edition of JourneyTeam Analytics ingests via a custom AL extension
(BC2Fabric) that JourneyTeam built and maintains. When designing the Customer Engagement
edition, the obvious instinct was to mirror that approach.

Dynamics 365 CE is different in a way that matters: Sales, Customer Service, Project
Operations, and Field Service all sit on **Dataverse**, and Microsoft ships a first-party
capability — **Link to Microsoft Fabric** — that shortcuts Dataverse tables into OneLake
with no copy, no pipeline, and no ETL.

Options considered:

1. **Link to Microsoft Fabric** — first-party, zero-copy shortcut.
2. **Azure Synapse Link for Dataverse** — the predecessor, exporting to ADLS Gen2.
3. **A custom extension or pipeline**, mirroring the BC pattern.
4. **Dataverse Web API / OData extraction** via Fabric pipelines.

## Decision

**Use Link to Microsoft Fabric as the sole ingestion mechanism for new engagements.**

Bronze *is* the shortcut. JourneyTeam builds nothing in the ingestion layer and maintains
nothing there.

Synapse Link is accepted only where a customer already has it and migrating is
impractical; that is a documented deviation requiring its own ADR and separate scoping.
Options 3 and 4 are rejected outright for Dataverse sources.

## Consequences

**Good:**

- Time to first data drops from days to hours, and the delivery timeline from 8 weeks to 6.
- Microsoft owns the ingestion lifecycle. Schema changes, delta logic, and scheduling stop
  being JourneyTeam maintenance liabilities — which is a real ongoing cost in the BC
  edition.
- No JourneyTeam code in the customer's Dynamics environment, so no solution to install,
  version, or upgrade, and a materially easier security conversation.
- Near-real-time data availability without engineering for it.

**Bad, and consequential:**

- **Ingestion stops being a differentiator.** Anyone — any partner, any competent customer
  IT team — can enable Link to Fabric in an afternoon. The BC edition could point at the
  extension as proprietary IP. This edition cannot.
- We inherit Microsoft's constraints without recourse: region alignment requirements, table
  eligibility rules, and whatever changes in future releases.
- A customer can reasonably ask "why am I paying you for this step?" The answer must be
  ready and honest.

**Therefore — the decision that follows from this one:** the offering's defensible value
must sit entirely in the layers above ingestion:

1. The [Dataverse conformance layer](../architecture/conformance-layer.md)
2. [Snapshot history](../architecture/snapshot-and-history.md)
3. Cross-app semantic models — **no longer in scope**; see
   [ADR 0004](0004-cross-app-pack-packaging.md), deferred with the packs it spanned. It was
   the only one of the three with no first-party equivalent, so losing it narrows the
   competitive story, not the architecture.

Every pricing, positioning, and build-sequence decision in this repository follows from
that. Sales material must move past ingestion quickly and land on the conformance layer —
see [`../offering/positioning.md`](../offering/positioning.md).

## Notes

- Dataverse capacity and billing implications of the shortcut must be verified against
  current Microsoft terms before any cost claim — see
  [`../architecture/licensing-and-capacity.md`](../architecture/licensing-and-capacity.md).
- This ADR covers Dataverse sources only. **Dynamics 365 Finance & Operations does not
  ingest this way** and is a separate edition rather than a pack — which is exactly the
  problem raised in [ADR 0003](0003-project-operations-scope.md).
