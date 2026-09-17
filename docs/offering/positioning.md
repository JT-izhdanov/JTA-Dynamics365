# Positioning

> **Scope: Dynamics 365 Sales only.** Claims below are written for a single-pack offering.
> Anything that depended on spanning several Dynamics apps has been removed rather than
> softened — see [`roadmap.md`](roadmap.md).

## Problem statement

Dynamics 365 Sales customers have operational data they cannot get real answers out of. The
barriers to buying a Microsoft data and analytics solution are many:

| Barrier | How this offering answers it |
|---|---|
| High cost / uncertain ROI | One fixed price, published package contents — see [`pricing-and-packaging.md`](pricing-and-packaging.md) |
| High risk / complex requirements | Pre-built architecture, nothing designed from scratch |
| Limited internal expertise | Coaching and Copilot enablement included |
| Slow time to value | 4–5 weeks to production, hours to first data |
| Long implementation timelines | Fixed scope, one pack |
| Customization fear | Customer owns the model and can change everything |
| Vendor dependency | Standard Fabric and Power BI artifacts, no proprietary runtime |
| Lack of strategy | Aligns to the Microsoft Fabric roadmap by construction |
| Lack of scalability | OneLake accepts any additional source later |
| Integration challenges | First-party Link to Fabric, no connector to maintain |

## Value statement

A pre-packaged BI solution for Dynamics 365 Sales is a win on both sides. It simplifies
adoption for the customer while giving JourneyTeam scalability, efficiency, and margin.

- Microsoft technology alignment
- Fast time to value
- Cost-effectiveness
- Reduced risk
- Streamlined, repeatable deployment
- Customer empowerment and faster user adoption
- Scalability beyond the initial scope
- High satisfaction

## Business outcomes

**Automation** — BI streamlines data collection, analysis, and reporting, reducing manual
work. *No more export-and-wrangle.*

**Data access and visibility** — centralized, structured, accessible data.
*No more "where is that report?"*

**Data accuracy** — one conformed model, a single source of truth.
*No more "why does my report not match yours?"*

**History** — Dataverse tells you what is true now. The platform tells you what was true
then. *No more "we can't see what the pipeline looked like at quarter close."*

**Scalability** — a well-designed data platform is independent of the operational systems
that come and go. *No more "we need a whole new reporting structure with this new system?"*

**AI readiness** — Copilot and ML need clean, structured, accessible data.
*No more "where do we start with this AI stuff?"*

## Competitive frame

Dynamics 365 Sales ships first-party analytics — out-of-the-box sales reports, pipeline
views, and Sales Premium forecasting — and they are genuinely decent for standard
questions. **Do not claim otherwise**; a prospect who uses them will know, and the
credibility loss costs more than the point wins. Differentiate where first-party genuinely
cannot follow.

| Area | First-party D365 Sales analytics | JourneyTeam Analytics for D365 Sales |
|---|---|---|
| Custom fields and tables | Not included | Fully included |
| History depth | Limited retention | Unlimited, snapshot-based |
| Point-in-time / pipeline movement | Current state only | Daily snapshots, SCD2 dimensions |
| Blend external data | No | On-prem, cloud, file, streaming |
| Drill to detail | Limited | To record level |
| Report tailoring | None to minimal | Unlimited |
| Data processing capacity | Bounded by the app | Fabric capacity, elastic |
| Model ownership | Microsoft-controlled | Customer owns the model |
| Technical expertise required | Little to none | Some IT expertise |
| Cost | Included in licensing | Services engagement plus Fabric capacity |

The honest summary: **first-party Sales analytics are fine for standard questions about
current state. This offering is for non-standard questions, questions about custom fields,
and questions about the past.** That framing is more persuasive than claiming first-party
is bad, and it is true.

**What the single-pack scope costs this slide.** Cross-app analytics — one model spanning
Sales into delivery — used to sit in this table as the row first-party cannot answer at
all. With Sales alone it is gone, and the differentiation rests on custom schema, history,
and model ownership. Those are real but narrower. Against a prospect already running
first-party Sales analytics, lead with **history and custom fields**; they are the two rows
where the gap is not arguable.

### What we are actually competing against

1. **Doing nothing / Excel exports.** The most common competitor. Counter with the
   automation and accuracy outcomes above. JourneyTeam's own weekly pipeline workbook is
   the proof point — see
   [`../reference/jtp-excel-pipeline-report.md`](../reference/jtp-excel-pipeline-report.md).
2. **First-party embedded analytics.** Counter with the table above — custom fields and
   history.
3. **A bespoke Fabric project from another partner.** Counter with fixed price, 4–5 week
   timeline, and pre-built IP. A bespoke build costs multiples of this and takes months.
4. **A non-Microsoft BI stack.** Counter with roadmap alignment, Copilot readiness, and
   the fact that the data never leaves the Microsoft tenant.

## Cross-sell: the portfolio play

The strongest motion in the portfolio is the second edition. A customer who has the Sales
edition already has a Fabric capacity, a OneLake, a conformance layer, and trained users.
Adding the Business Central edition — or a future Finance & Operations edition — reuses
all of it.

"One Fabric platform, every Dynamics app" is a materially bigger deal than either package
sold alone, and the second sale is far cheaper to deliver than the first. Lead with Sales;
make sure the architecture slide shows the other apps already have a place to land.

**Be careful how this is worded now.** The landing zone is real — the conformance layer and
conformed dimensions are built app-agnostic precisely so another app can be added without a
rebuild. What does *not* exist is a second Dynamics 365 packaged pack to add. Sell the
architecture, not a pack that is not GA.

## Call to action

Schedule a no-cost 1-hour consultation with JourneyTeam's Data & Analytics experts.
