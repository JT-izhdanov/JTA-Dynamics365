# Roadmap

**Repository scope: Dynamics 365 Sales only** — this repository is the working space for
the Sales pack. Everything else on this page is **deferred, not cancelled**; cross-app
functionality in particular is intended and will be built. Nothing deferred is documented,
priced, or positioned here until it exists.

A pack is **GA** only when its source mapping is validated, its metrics are implemented,
its model and reports are built, and it has been delivered successfully at least once.

## In scope

| Component | Status | Gate to GA |
|---|---|---|
| Platform (conformance layer) | In build | Validated against a live Dataverse environment |
| **Sales pack** | **In build** | Source mapping corrected from Bronze profiling, snapshot fact proven, model + reports built, reconciled |

## Deferred

Designed and analysed, then removed from this repository so that it has one subject. **Not
cancelled** — when one returns, recover the analysis from git history rather than starting
over; the drafts included source mappings and metric definitions worth reusing.

| Deferred | Why it was worth having | Recover from |
|---|---|---|
| Customer Service pack | Second-largest installed base; case aging reuses the snapshot framework | `packs/customer-service/` before `fd0e436` |
| Project Operations pack | Carried a real scope trap — F&O-resident financials — recorded in [ADR 0003](../decisions/0003-project-operations-scope.md) | `packs/project-operations/` |
| Field Service pack | Work-order vs booking grain problem documented | `packs/field-service/` |
| **Revenue-to-Delivery (cross-app)** — **intended, not cancelled** | The strongest differentiator in the design; no first-party equivalent. Needs at least one delivery-side pack before it has anything to span. Packaging logic in [ADR 0004](../decisions/0004-cross-app-pack-packaging.md) | `packs/revenue-to-delivery/` |
| Customer Insights – Journeys pack | Marketing analytics; Dataverse-native, same architecture | never drafted |
| Finance & Operations edition | Different ingestion path — a separate edition, not a pack | never drafted |

## What narrowing costs now, and what it does not

Cross-app analytics is one of three stated differentiators and the only one with no
first-party equivalent. It is **planned** — but planned is not sellable.

**What it costs today.** Differentiation rests on the conformance layer and snapshot
history. Both are real; the competitive story is narrower. Against a prospect who already
has first-party Sales analytics, lead with history and custom fields — see
[`positioning.md`](positioning.md#competitive-frame). Do not put cross-app on a slide, even
marked roadmap, until a second pack exists.

**What it does not cost.** The architecture. Cross-app will be built on the conformed
dimensions, the polymorphic activity bridge, and the pack-prefixed Gold schema that the
Sales build produces — which is why those stay general even though one pack does not need
them to be. That is a deliberate cost carried now to keep the second pack cheap, and it is
the main thing to protect while working in here:

| Keep general | Because cross-app needs it | Where |
|---|---|---|
| Conformed dimensions, unprefixed — no `sales_dim_customer` | A second pack must point at the same `dim_customer` and `dim_owner`, or the models cannot join | [`../../packs/_shared/conformed-dimensions.md`](../../packs/_shared/conformed-dimensions.md) |
| `sales__` prefix on Gold objects | A second pack lands without renaming anything | [`../architecture/medallion-design.md`](../architecture/medallion-design.md#schema-and-naming) |
| `bridge_activity` resolving all polymorphic targets | Activities span apps; re-solving polymorphism per pack is the expensive version | [`../../platform/notebooks/23_silver_conformance_activities.py`](../../platform/notebooks/23_silver_conformance_activities.py) |
| `dim_owner` as SCD2, and the RLS model derived from it | Ownership and security are org-wide, not per app | [`../architecture/security-and-rls.md`](../architecture/security-and-rls.md) |
| `quote` / `salesorder` in the Bronze set | The project contract is built on `salesorder` — the join point from pipeline into delivery | [`../../packs/sales/source-tables.md`](../../packs/sales/source-tables.md) |

**Cheapest route back to cross-app** is a delivery-side pack — Project Operations or Field
Service — since Revenue-to-Delivery has nothing to span on its own. ADR 0004 holds the
packaging reasoning; ADR 0003 holds the Project Operations scope trap that has to be
answered first.

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
