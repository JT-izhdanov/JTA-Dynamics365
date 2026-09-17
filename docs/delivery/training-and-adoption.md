# Training and adoption

Coaching hours are included in the offering and priced in
[`../offering/pricing-and-packaging.md`](../offering/pricing-and-packaging.md) — **do not
restate the hours or the prices here.** The tier ladder they used to belong to was built on
choosing among four packs and no longer applies; the single-pack proposal includes a small
base allocation with add-on blocks above it.

Copilot enablement is included.

## Why this is in the offering at all

A deployed platform nobody uses is a renewal that does not happen and a reference that does
not exist. Adoption is the difference between a delivered project and a customer who comes back.

It is also the cheapest part of the offering to deliver and the most visible to the
customer, which makes it disproportionately valuable per hour spent.

With one pack it carries more weight than it used to: there is no second pack to sell at
handoff, so coaching hours and platform extension are the upsell.

## Audiences

Coaching hours are finite, so spend them by audience rather than delivering one generic
session.

| Audience | Needs | Typical share |
|---|---|---|
| **Executives / sponsors** | Where to look, what the headline numbers mean, how to ask for more | Small — one short session |
| **Business users** | Navigating the report packs, filters, drill-down, export, subscriptions | Largest share |
| **Power users / analysts** | Semantic model structure, building their own reports, Analyze in Excel, Copilot | Significant — these people create ongoing value |
| **IT / data owners** | Refresh schedules, snapshot monitoring, RLS administration, what to do when something breaks | Essential — they own it after handoff |

**At the included base allocation, prioritize business users and IT.** Power-user
enablement is where the compounding value is, and it is the most common reason a customer
buys more hours.

## Content

### Business users

- What the platform is, and how it differs from reports inside Dynamics
- Walkthrough of each purchased report pack
- Filters, slicers, cross-filtering, bookmarks
- Drill to detail
- Export and subscriptions
- **What "as of date" means** — the single most valuable and least intuitive concept in the
  platform, and the one worth spending real time on
- Where to go when a number looks wrong

### Power users

- Semantic model structure and conformed dimensions
- Why not to rebuild a dimension that already exists
- Building a new report against an existing model
- Analyze in Excel
- Copilot: useful prompts, and its limits
- When to ask JourneyTeam versus when to self-serve

### IT / data owners

- Architecture walkthrough: Bronze / Silver / Gold and what lives where
- Refresh schedules and dependencies
- **Snapshot job monitoring** — what failure looks like and why silent failure matters
- RLS administration and adding users to roles
- Escalation path

## Copilot enablement

Included. Practical scope:

- Confirm the customer's Fabric SKU actually supports Copilot **before promising it** —
  see [`../architecture/licensing-and-capacity.md`](../architecture/licensing-and-capacity.md)
- Verify the semantic models are Copilot-ready: clear table and column names, descriptions
  on measures, hidden technical columns
- Demonstrate effective prompting against the models
- Be explicit about limits — Copilot answers from the model, so anything outside the model
  is outside its reach, and it does not replace the reconciliation discipline

The semantic model preparation is the part that actually determines whether Copilot is
useful. A model with cryptic column names and no measure descriptions produces poor Copilot
results regardless of the SKU. Treat model readability as a Copilot deliverable.

## Adoption practices worth recommending

Not billable, but they raise the odds of a reference customer:

- Publish the report packs as a Power BI app with a clear landing page
- Embed the relevant reports inside Dynamics 365 so users find them where they already work
- Name an internal owner for the semantic model and report pack
- Set up subscriptions for recurring reviews so the reports appear without being sought
- Schedule a 30-day check-in

## Handoff

Training completion, hours consumed, and remaining hours are recorded at close — see
[`support-handoff.md`](support-handoff.md). Unused hours are a natural reason for a
follow-up conversation rather than something to let lapse silently.
