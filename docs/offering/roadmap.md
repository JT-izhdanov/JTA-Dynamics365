# Roadmap

**Repository scope: Dynamics 365 Sales only.** Everything else on this page is deferred and
not documented here.

A pack is **GA** only when its source mapping is validated, its metrics are implemented,
its model and reports are built, and it has been delivered successfully at least once.

## In scope

| Component | Status | Gate to GA |
|---|---|---|
| Platform (conformance layer) | In build | Validated against a live Dataverse environment |
| **Sales pack** | **In build** | Source mapping corrected from Bronze profiling, snapshot fact proven, model + reports built, reconciled |

## Deferred

Designed and analysed, then removed from this repository as out of scope. If any returns,
recover the analysis from git history rather than starting over — the drafts included
source mappings and metric definitions worth reusing.

| Deferred | Why it was worth having | Recover from |
|---|---|---|
| Customer Service pack | Second-largest installed base; case aging reuses the snapshot framework | `packs/customer-service/` before `fd0e436` |
| Project Operations pack | Carried a real scope trap — F&O-resident financials — recorded in [ADR 0003](../decisions/0003-project-operations-scope.md) | `packs/project-operations/` |
| Field Service pack | Work-order vs booking grain problem documented | `packs/field-service/` |
| Revenue-to-Delivery (cross-app) | The strongest differentiator in the original design; no first-party equivalent. Packaging logic in [ADR 0004](../decisions/0004-cross-app-pack-packaging.md) | `packs/revenue-to-delivery/` |
| Customer Insights – Journeys pack | Marketing analytics; Dataverse-native, same architecture | never drafted |
| Finance & Operations edition | Different ingestion path — a separate edition, not a pack | never drafted |

**What narrowing to one pack costs the offering:** cross-app analytics was one of three
stated differentiators and the only one with no first-party equivalent. With Sales alone the
differentiation rests on the conformance layer and snapshot history. Both are real, but the
competitive story is narrower — worth knowing when positioning against a prospect who
already has first-party Sales analytics.

## Sales pack build order

1. **Platform / conformance layer first.** Everything depends on it, and building it against
   one real environment is what makes the rest repeatable.
2. **Snapshots running second**, before any model or report. History cannot be backfilled,
   so every day of delay is a day permanently lost.
3. **Silver, then Gold, then the semantic model, then reports** — see
   [`../../packs/sales/technical-design.md`](../../packs/sales/technical-design.md) §15 for
   the numbered sequence.

## Known gaps

Carried here so they are not forgotten once delivery starts.

- **No post-go-live annuity.** Delivery ends at support handoff. Every customer will need
  ongoing model changes, and there is no packaged way to sell that. Largest untapped
  commercial opportunity in the offering.
- **No defined upgrade path.** When Microsoft changes Dataverse schema or a customer
  upgrades an app solution, there is no versioning or re-deployment story for a pack already
  delivered. Biggest risk to repeatable delivery at scale.
- **RLS depth is unscoped.** The platform includes an RLS *scaffold*; complex hierarchies
  need more and it is not priced.
- **No multi-environment story.** Customers with separate Dataverse Dev/Test/Prod will ask
  how packs promote between them.
- **Pricing is unresolved** — see [`pricing-and-packaging.md`](pricing-and-packaging.md).
- **Reference topology diverges from the deployed one** — see
  [ADR needed](../architecture/jt-medallion-topology.md#1-this-diverges-from-the-products-reference-design).

Each should become an ADR before the first customer delivery, not after.
