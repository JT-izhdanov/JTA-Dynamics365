# Extended deck outline

Source of truth for the customer-facing deck. Mirrors the Business Central extended deck's
structure so the two read as one portfolio, with the changes the CE edition requires.

Each slide names where its content comes from, so the deck never becomes an independent
source of facts that can drift.

| # | Slide | Content source |
|---|---|---|
| 1 | Title — *Your Path to Improved Data & Analytics, for Microsoft Dynamics 365 Customer Engagement* | [ADR 0002](../docs/decisions/0002-offering-naming.md) |
| 2 | Agenda | — |
| 3 | Executive summary | `docs/offering/overview.md` |
| 4 | Problem statement — barriers to buying analytics | `docs/offering/positioning.md#problem-statement` |
| 5 | **Architecture overview** | `docs/architecture/reference-architecture.md` |
| 6 | 1: Link to Microsoft Fabric | `docs/architecture/ingestion-link-to-fabric.md` |
| 7 | 2: Medallion data architecture | `docs/architecture/medallion-design.md` |
| 8 | **3: The Dataverse conformance layer** | `docs/architecture/conformance-layer.md` |
| 9 | **4: History — questions Dataverse cannot answer** | `docs/architecture/snapshot-and-history.md` |
| 10 | 5: Power BI semantic model layer | `packs/_shared/conformed-dimensions.md` |
| 11 | 6: Power BI report layer | `packs/*/README.md` |
| 12 | Report pack detail — Sales | `packs/sales/` |
| 13 | Report pack detail — Customer Service | `packs/customer-service/` |
| 14 | Report pack detail — Project Operations | `packs/project-operations/` |
| 15 | Report pack detail — Field Service | `packs/field-service/` |
| 16 | **Revenue-to-Delivery — the cross-app pack** | `packs/revenue-to-delivery/` |
| 17 | Sample report screenshots | JourneyTeam demo data only |
| 18 | Value statement | `docs/offering/positioning.md#value-statement` |
| 19 | Business outcomes | `docs/offering/positioning.md#business-outcomes` |
| 20 | **First-party analytics vs. JourneyTeam Analytics** | `docs/offering/positioning.md#competitive-frame` |
| 21 | Pricing — à la carte | `docs/offering/pricing-and-packaging.md` |
| 22 | Pricing — packages | `docs/offering/pricing-and-packaging.md` |
| 23 | Fabric licensing (dated snapshot) | `docs/architecture/licensing-and-capacity.md` |
| 24 | Power BI licensing (dated snapshot) | `docs/architecture/licensing-and-capacity.md` |
| 25 | **One platform, every Dynamics app** — portfolio | `docs/offering/positioning.md#cross-sell-the-portfolio-play` |
| 26 | Delivery timeline — 3 sprints, 6 weeks | `docs/delivery/playbook.md` |
| 27 | Next steps — no-cost 1-hour consultation | — |

## Where this deck must differ from the Business Central deck

### 1. Ingestion gets less airtime, not more

The BC deck can dwell on the BC2Fabric extension as proprietary IP. **This one cannot** —
Link to Fabric is first-party and anyone can enable it
([ADR 0001](../docs/decisions/0001-use-link-to-fabric-for-ingestion.md)).

Slide 6 states that ingestion is first-party, frames it as *reduced risk and faster
delivery*, and moves on. Then slides 8 and 9 — the conformance layer and history — carry
the value narrative.

Framing that works: *"Getting the data into Fabric is the easy part, and Microsoft gives
it to you. Making it answer questions is the part you're buying."*

### 2. Two slides the BC deck does not have

- **Slide 8, the conformance layer.** The core IP. Show a raw Dataverse table next to the
  conformed version: integer status codes and ambiguous currency becoming readable labels
  and unambiguous amounts. This lands better than any architecture diagram.
- **Slide 9, history.** Lead with the questions: *"What did the pipeline look like on the
  last day of Q2?"* Then state plainly that Dataverse cannot answer it, no first-party
  report can, and that this is what the platform adds.

### 3. Slide 16 — the cross-app pack

The strongest single proof point in the offering, and the thing no first-party Dynamics 365
analytics does at all. Give it a full slide even while it is a roadmap item — clearly
marked as such ([ADR 0004](../docs/decisions/0004-cross-app-pack-packaging.md)).

### 4. Slide 20 — an honest comparison

The BC deck compares against Microsoft's BC Power BI apps and wins easily. **This
comparison is harder and must be honest.** Customer Service and Field Service ship
respectable first-party analytics; a prospect using them will know.

Use the table in `positioning.md#competitive-frame`, and the framing: *first-party
analytics are fine for standard questions about one app; this is for non-standard
questions, questions spanning apps, and questions about the past.*

### 5. Slide 25 — the portfolio

The BC deck has no equivalent, and it is the most valuable slide in either deck. One Fabric
platform, every Dynamics app. Sets up the second engagement, which is the cheapest sale in
the portfolio.

## Rules

- **No prices in this outline or in the deck's own notes.** Slides 21–22 render from
  `pricing-and-packaging.md`. One source, so the $7,500-versus-$10,000 contradiction in
  the BC deck cannot repeat here.
- **Licensing slides are dated snapshots**, refreshed from Microsoft's published pricing
  before each use.
- **Mark roadmap items as roadmap.** Do not present a non-GA pack as available.
- **JourneyTeam demo data only** in screenshots.

## Known issue to avoid repeating

The BC deck's sample report screenshots show visibly broken sign handling — net income
negative, expense ratio 300%, "PY: -725.84%". It is a demo data artifact on a
customer-facing slide. **Check every screenshot's numbers are plausible before it ships.**
