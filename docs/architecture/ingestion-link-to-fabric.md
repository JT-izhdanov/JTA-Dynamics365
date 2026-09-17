# Ingestion — Link to Microsoft Fabric

Component 1 of the customer-facing architecture narrative. Its place in the end-to-end
design, and the contract it owes Silver, are in
[`solution-technical-design.md`](solution-technical-design.md#4-component-1--ingestion).

## What it is

**Link to Microsoft Fabric** is a first-party Dataverse capability that makes Dataverse
tables available in OneLake as a shortcut — no pipeline to build, no copy of the data, no
ETL to maintain, and near-real-time availability. It is configured from the Power Apps
maker portal against a Fabric workspace.

For this offering, that means **the entire ingestion layer is a configuration step**.

## Why this matters to the offering

| | Business Central edition | This offering |
|---|---|---|
| Ingestion mechanism | Custom BC2Fabric AL extension | Link to Fabric |
| Who builds it | JourneyTeam | Microsoft |
| Who maintains it | JourneyTeam | Microsoft |
| Time to first data | Days | Hours |
| Failure modes we own | Extension, scheduling, delta logic | Configuration only |

Two consequences shape the whole offering:

1. **Delivery is cheaper and faster** — the timeline advantage over the Business Central
   edition's eight weeks comes largely from here. See
   [`../offering/pricing-and-packaging.md`](../offering/pricing-and-packaging.md).
2. **Ingestion is not defensible IP.** Any partner, and any reasonably capable customer IT
   team, can do this step. Never build the pitch around it. The value narrative has to move
   immediately to the [conformance layer](conformance-layer.md) and
   [history](snapshot-and-history.md).

Sales framing that works: *"Getting the data into Fabric is the easy part, and Microsoft
gives it to you. Making it answer questions is the part you're buying."*

## Constraints to confirm before quoting

These are pre-sales qualification items, not Sprint 1 discoveries.

| Constraint | Why it matters | `<!-- VERIFY -->` |
|---|---|---|
| **Region alignment** | The Fabric capacity and the Dataverse environment must be in compatible regions. A mismatch can block the link entirely and is not something we can engineer around | Confirm current Microsoft requirements and the supported region list |
| **Fabric capacity present** | A trial can start a build; production needs a paid SKU | — |
| **Table availability** | Not every Dataverse table is eligible, and tables must be selected into the link | Confirm current eligibility rules and any table type exclusions |
| **Change tracking** | Dataverse tables generally require change tracking enabled to participate | Confirm whether the link enables this automatically or requires it in advance |
| **Privileges** | Configuring the link requires specific Dataverse and Fabric roles | See [`../delivery/prerequisites-and-access.md`](../delivery/prerequisites-and-access.md) |
| **Dataverse capacity implications** | Microsoft positions the shortcut as not duplicating storage, but capacity and billing terms change | Confirm current terms before making any cost claim to a customer |

**Do not restate Microsoft licensing, capacity, or region behavior from memory into
customer-facing material.** Verify against current Microsoft documentation each time — see
[`licensing-and-capacity.md`](licensing-and-capacity.md).

## Relationship to Synapse Link for Dataverse

**Azure Synapse Link for Dataverse** is the predecessor mechanism, exporting Dataverse
data to ADLS Gen2. Some customers will already have it configured, and some existing
JourneyTeam material may reference it.

- **New engagements use Link to Fabric.** Default position, no exceptions without a
  documented reason.
- A customer with an existing Synapse Link is not a blocker, but the two mechanisms expose
  metadata differently. This matters specifically for choice-label resolution — see the
  `<!-- VERIFY -->` note in [`conformance-layer.md`](conformance-layer.md#1-choice--option-set-labels).
- If an engagement must consume an existing Synapse Link export instead, that is a
  deviation from the packaged architecture and needs an ADR and separate scoping.

## Bronze layer rules

The shortcut *is* Bronze. Treat it as read-only, Microsoft-managed territory:

1. **Never write to Bronze.** Never transform in place, never add columns, never
   materialize a "cleaned" copy alongside the raw tables.
2. **Assume the shortcut can be recreated.** All JourneyTeam logic must be reproducible
   from Bronze by re-running notebooks, so that dropping and recreating the link loses
   nothing but time.
3. **Validate, do not trust.** Confirm on arrival that expected tables are present, have
   rows, and carry the columns the mappings assume. Schema differs by solution version and
   by which apps are installed — this is what
   `platform/notebooks/10_bronze_shortcut_validation.py` exists to catch, before a mapping
   error surfaces as a wrong number in UAT.
4. **Table selection is configuration.** Which tables are linked is recorded in
   `platform/config/`, not chosen ad hoc during delivery. Where Bronze is shared
   infrastructure, adding a table affects other consumers and is change-controlled — see
   [`jt-medallion-topology.md`](jt-medallion-topology.md).

## What is out of scope here

- **Dynamics 365 Finance & Operations** does not ingest through Dataverse Link to Fabric in
  the same way and is a separate edition, not a pack. This matters for any future
  delivery-side pack — see [ADR 0003](../decisions/0003-project-operations-scope.md).
- **Non-Dataverse sources** (on-prem, file, streaming) land in OneLake through normal
  Fabric mechanisms and are additional development, not part of any fixed price.
