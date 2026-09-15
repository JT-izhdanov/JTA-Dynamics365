# Roadmap

Availability drives what sales is allowed to quote. A pack is **GA** only when its source
mapping is validated, its metrics are implemented, its model and reports are built, and it
has been delivered successfully at least once.

## Pack availability

| Pack | Status | Target | Gate to GA |
|---|---|---|---|
| Platform (conformance layer) | In build | — | Validated against a live Dataverse environment |
| Sales | In build | — | Source mapping validated, snapshot fact proven, model + reports built |
| Customer Service | Planned | After Sales | Source mapping validated, SLA/KPI instance modeling confirmed |
| Project Operations | Planned — **scope gated** | After Customer Service | [ADR 0003](../decisions/0003-project-operations-scope.md) resolved |
| Field Service | Planned | After Project Operations | Source mapping validated, booking vs. work order grain resolved |
| Revenue-to-Delivery | Planned | Requires Sales + Project Ops + Field Service | Two or more packs GA |

**Do not quote a pack that is not GA** without an explicit exception from the offering
owner and a written caveat in the proposal. The Business Central edition's PREMIUM tier
currently sells "choose 5" against suites still marked TBD; that is the mistake this
table exists to prevent.

## Build sequence and rationale

1. **Platform / conformance layer first.** Every pack depends on it. Building it against
   one real environment before any pack is what makes the rest repeatable.
2. **Sales second.** Largest installed base, clearest metric set, and the pipeline snapshot
   proves the history capability that the whole offering is differentiated on.
3. **Customer Service third.** Second-largest installed base. Case aging exercises the same
   snapshot framework, which de-risks it.
4. **Project Operations fourth**, and only once its deployment scope is settled. It is the
   only pack with a genuine architectural fork (see ADR 0003), so it should not be first.
5. **Field Service fifth.** Rich data, but the smallest installed base of the four and the
   most variation between customers in how work orders are used.
6. **Revenue-to-Delivery last**, because it is composed from the others.

## Candidate future scope

Not committed. Listed so the architecture leaves room for them.

| Candidate | Note |
|---|---|
| **Customer Insights – Journeys pack** | Marketing analytics. Dataverse-native, so it fits the same architecture. Natural fifth pack and would let CE PREMIUM mirror BC's "choose 5" framing |
| **Finance & Operations edition** | Different ingestion path than Dataverse Link to Fabric. A separate edition, not a pack. Would complete the portfolio |
| **Contact Center / Omnichannel depth** | Conversation and session analytics. Partly dependent on which Omnichannel tables a customer has |
| **Managed service / support annuity** | The offering currently ends at support handoff. A recurring-revenue wrapper is the largest untapped commercial opportunity |
| **Benchmark pack** | Anonymized cross-customer benchmarks. Commercially attractive, but needs a data rights and privacy review before it is even scoped |

## Known gaps in the offering as currently defined

Carried here so they are not forgotten once delivery starts:

- **No post-go-live annuity.** Delivery ends at support handoff. Every customer will need
  ongoing model changes, and there is no packaged way to sell that yet.
- **No defined upgrade path.** When Microsoft changes Dataverse schema or a customer
  upgrades an app solution, there is no versioning or re-deployment story for packs already
  delivered. This is the single biggest risk to repeatable delivery at scale.
- **RLS depth is unscoped.** The platform fee includes an RLS *scaffold*. Customers with
  complex business unit or team hierarchies will need more, and it is not priced.
- **No multi-environment story.** Customers with separate Dataverse Dev/Test/Prod
  environments will ask how the packs promote between them.

Each of these should become an ADR before the first customer delivery, not after.
