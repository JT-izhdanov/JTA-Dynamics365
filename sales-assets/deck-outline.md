# Extended deck outline

Source of truth for the customer-facing deck. Mirrors the Business Central extended deck's
structure so the two read as one portfolio, with the changes the Dynamics 365 Sales edition
requires.

Each slide names where its content comes from, so the deck never becomes an independent
source of facts that can drift.

> **Scope: Dynamics 365 Sales only.** The outline was 27 slides covering four report packs
> plus a cross-app pack. It is now 20 — four pack-detail slides and the cross-app slide are
> gone, and Sales gets the airtime instead. See
> [`../docs/offering/roadmap.md`](../docs/offering/roadmap.md).

| # | Slide | Content source |
|---|---|---|
| 1 | Title — *Your Path to Improved Data & Analytics, for Microsoft Dynamics 365 Sales* | [ADR 0002](../docs/decisions/0002-offering-naming.md) |
| 2 | Agenda | — |
| 3 | Executive summary | `docs/offering/overview.md` |
| 4 | Problem statement — barriers to buying analytics | `docs/offering/positioning.md#problem-statement` |
| 5 | **Architecture overview** | `docs/architecture/reference-architecture.md` |
| 6 | 1: Link to Microsoft Fabric | `docs/architecture/ingestion-link-to-fabric.md` |
| 7 | 2: Medallion data architecture | `docs/architecture/medallion-design.md` |
| 8 | **3: The Dataverse conformance layer** | `docs/architecture/conformance-layer.md` |
| 9 | **4: History — questions Dataverse cannot answer** | `docs/architecture/snapshot-and-history.md` |
| 10 | 5: Power BI semantic model layer | `packs/_shared/conformed-dimensions.md` |
| 11 | 6: Power BI report layer | `packs/sales/README.md` |
| 12 | **The Sales report pack — pages and questions answered** | `packs/sales/README.md`, `docs/offering/overview.md#the-sales-pack` |
| 13 | **Pipeline, velocity, and forecast in practice** | `packs/sales/metrics.yaml` |
| 14 | Sample report screenshots | JourneyTeam demo data only |
| 15 | Value statement and business outcomes | `docs/offering/positioning.md#value-statement` |
| 16 | **First-party Sales analytics vs. JourneyTeam Analytics** | `docs/offering/positioning.md#competitive-frame` |
| 17 | Pricing | `docs/offering/pricing-and-packaging.md` |
| 18 | Fabric and Power BI licensing (dated snapshot) | `docs/architecture/licensing-and-capacity.md` |
| 19 | **One platform, every Dynamics app** — portfolio | `docs/offering/positioning.md#cross-sell-the-portfolio-play` |
| 20 | Delivery timeline and next steps — no-cost 1-hour consultation | `docs/delivery/playbook.md` |

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
  and unambiguous amounts. This lands better than any architecture diagram, and
  [`docs/bronze-profiling/opportunity.md`](../docs/bronze-profiling/opportunity.md) is the
  evidence base for it — a real `opportunity` table exports as 343 columns with raw
  integers where the labels should be.
- **Slide 9, history.** Lead with the questions: *"What did the pipeline look like on the
  last day of Q2?"* Then state plainly that Dataverse cannot answer it, no first-party
  report can, and that this is what the platform adds.

### 3. Slides 12–13 replace the four pack slides

The old outline gave one slide each to Sales, Customer Service, Project Operations and
Field Service, plus a full slide to the cross-app pack. With one pack, that breadth is gone
and pretending otherwise is not an option — **do not show a pack that does not exist, even
marked as roadmap.**

Spend the reclaimed slides on depth instead: the report pages, and one worked pipeline
story from open pipeline through weighted forecast to win rate. Depth on the one pack is a
better proof point than breadth we cannot deliver.

### 4. Slide 16 — an honest comparison

The BC deck compares against Microsoft's BC Power BI apps and wins easily. **This
comparison is harder and must be honest.** Dynamics 365 Sales ships respectable first-party
analytics and Sales Premium adds forecasting; a prospect using them will know.

**The cross-app row is gone from this table** — it was the one first-party could not answer
at all. Lead instead with the two rows where the gap is not arguable: **history** and
**custom fields**. Use the table in `positioning.md#competitive-frame` and the framing:
*first-party Sales analytics are fine for standard questions about current state; this is
for non-standard questions, custom fields, and questions about the past.*

### 5. Slide 19 — the portfolio

The BC deck has no equivalent, and it is the most valuable slide in either deck. One Fabric
platform, every Dynamics app. Sets up the second engagement, which is the cheapest sale in
the portfolio.

**Word it as an architecture claim, not a catalogue.** The landing zone is real — the
conformance layer and conformed dimensions are built app-agnostic so another app adds
without a rebuild. What does not exist is a second Dynamics 365 packaged pack to point at.
The Business Central edition is a real second edition; a Customer Service pack is not.

## Rules

- **No prices in this outline or in the deck's own notes.** Slide 17 renders from
  `pricing-and-packaging.md`. One source, so the $7,500-versus-$10,000 contradiction in
  the BC deck cannot repeat here.
- **Nothing ships until pricing is signed off.** The package structure priced by pack count
  and no longer works; slide 17 has no agreed number to render yet.
- **Licensing slides are dated snapshots**, refreshed from Microsoft's published pricing
  before each use.
- **Do not present a pack that does not exist**, marked roadmap or otherwise.
- **JourneyTeam demo data only** in screenshots — and not JourneyTeam's own pipeline, which
  is real confidential data.

## Known issue to avoid repeating

The BC deck's sample report screenshots show visibly broken sign handling — net income
negative, expense ratio 300%, "PY: -725.84%". It is a demo data artifact on a
customer-facing slide. **Check every screenshot's numbers are plausible before it ships.**
