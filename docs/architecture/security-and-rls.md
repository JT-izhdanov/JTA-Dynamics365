# Security and row-level security

## The gap customers will notice immediately

Dataverse has a rich, mature security model: business units, teams, roles, record-level
sharing, hierarchy security, field-level security. **None of it follows the data into
OneLake.** Once the shortcut lands in Fabric, the Dataverse security model is gone.

This is the most common surprise in a Dataverse-to-lakehouse project, and the most
dangerous one. A salesperson who could only see their own territory in Dynamics can, by
default, see the entire pipeline in Power BI.

Raise this in the sales conversation, not at UAT. It affects what the customer needs to
buy and how long delivery takes.

## What the platform fee includes

The platform fee (see
[`../offering/pricing-and-packaging.md`](../offering/pricing-and-packaging.md)) includes an
**RLS scaffold**:

- `dim_owner` built with the business unit path and manager hierarchy resolved (a
  by-product of the [conformance layer](conformance-layer.md#5-ownership-hierarchy))
- A user-to-permitted-scope mapping table in Silver
- RLS roles defined in the semantic models implementing the common patterns below
- Validation that the roles behave as intended, tested with named test users

## What it does not include

Anything beyond these patterns is additional development and is **not currently priced** —
a known gap tracked in [`../offering/roadmap.md`](../offering/roadmap.md#known-gaps).

| Pattern | In scope | Note |
|---|---|---|
| Everyone sees everything | Yes | Default where the customer accepts it |
| Own records only | Yes | Owner-based filter |
| Own business unit | Yes | |
| Own business unit and below | Yes | Uses the resolved BU path |
| Manager hierarchy (own reports and below) | Yes | Requires `parentsystemuserid` populated |
| Team membership | Yes | Where team membership drives access |
| Dataverse record sharing (`principalobjectaccess`) | **No** | Record-by-record sharing does not translate cleanly to RLS and is expensive to replicate |
| Field-level security | **No** | Requires column-level decisions per table, per role |
| Full Dataverse security parity | **No** | Not achievable in practice; do not promise it |

**Never promise Dataverse security parity in Power BI.** It is not achievable, and
promising it converts a design conversation into a defect.

## Design approach

1. **`dim_owner` is the single source of scope.** The hierarchy built for reporting is the
   same one that drives security. One artifact, two uses — this is why the conformance
   layer resolves it once rather than the pack doing its own.
2. **Map users to scope in Silver, not in DAX.** A mapping table is inspectable,
   testable, and refreshable. Complex DAX RLS expressions are none of those things and
   are the usual cause of RLS performance problems.
3. **Filter facts through dimensions.** Apply RLS on the dimension and let relationships
   propagate, rather than filtering large fact tables directly.
4. **Snapshot facts need the *historical* owner.** A snapshot of last quarter's pipeline
   should respect who owned the record then, which is why `dim_owner` is SCD2. Applying
   today's ownership to last year's snapshot silently changes historical numbers as people
   change jobs.
5. **Test with real role assignments.** Every delivery validates RLS with named test users
   against expected row counts. This is a UAT exit criterion, not a nice-to-have.

## Other security considerations

- **Workspace access.** Separating `JTA-<Customer>-Platform` from
  `JTA-<Customer>-Reporting` keeps report consumers out of the lakehouse and notebooks. Only
  the delivery team and designated customer engineers get platform workspace access.
- **The SQL endpoint bypasses semantic model RLS.** A user with SQL endpoint access reads
  Gold directly, unfiltered. The offering sells "Query in SQL" as a feature, so decide
  deliberately who gets it — it is not a substitute for a Power BI viewer role.
- **Sensitivity labels.** Microsoft Purview labels applied in Dataverse do not
  automatically carry to Fabric items. If the customer relies on labels, that is a scoping
  conversation.
- **Least privilege in delivery.** Delivery accounts get the minimum roles needed for the
  tasks in [`../delivery/prerequisites-and-access.md`](../delivery/prerequisites-and-access.md),
  scoped to the engagement and removed at handoff.
- **Never connect to a customer environment with a personal account for automation.**
  Scheduled and automated connections use a registered application with defined
  permissions, not an interactive user identity.
- **No customer data leaves the customer tenant.** Nothing — no extract, no screenshot
  with real records, no sample file — is committed to this repository or copied into
  JourneyTeam systems. Demo material uses JourneyTeam demo data only.

## Open item for the first engagement

Decide and document, per customer, at kickoff:

- Which of the supported patterns applies
- Whether the customer expects Dataverse parity (and reset that expectation immediately if so)
- Who gets SQL endpoint access
- Who owns RLS changes after handoff

Record the answers in the engagement's own documentation, not here.
