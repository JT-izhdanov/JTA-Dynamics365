# Licensing and capacity

> **Read this first.** Microsoft licensing, pricing, SKU behavior, and capacity terms
> change frequently. **Nothing in this document may be quoted to a customer without
> re-verifying it against current Microsoft documentation at the time of quoting.** This
> file records *what to check and why it matters*, deliberately not a price list — a stale
> price list in a repository is worse than none, because someone will trust it.

## What the customer buys separately

Fixed prices in [`../offering/pricing-and-packaging.md`](../offering/pricing-and-packaging.md)
cover JourneyTeam services only. The customer licenses the platform directly from
Microsoft:

| Item | Who buys it | Note |
|---|---|---|
| Microsoft Fabric capacity (F SKU) | Customer | Required for production. Sized per customer |
| Power BI licensing | Customer | Requirement depends on the Fabric SKU — see below |
| Dynamics 365 CE licensing | Customer | Already owned; prerequisite, not a new purchase |
| OneLake storage | Customer | Consumption-based, and the line item snapshots affect |

Surface these early. Services and licensing usually come from different budgets, and a
licensing surprise late in the cycle stalls an otherwise-closed deal.

## Items to verify before every quote

| # | Item | Why it matters |
|---|---|---|
| 1 | Current F SKU list prices, and pay-as-you-go vs. reservation pricing and the reservation discount | The customer's largest recurring cost; drives the whole TCO conversation |
| 2 | **The F SKU threshold at which Power BI Pro licenses are no longer required per viewer** | Materially changes total cost. Historically F64; confirm the current threshold and exactly which rights it confers |
| 3 | Copilot availability by SKU | Coaching in every tier includes Copilot enablement — confirm the customer's SKU actually supports it before promising it |
| 4 | OneLake storage, cache, and BCDR storage rates | Needed to size the snapshot cost conversation |
| 5 | Dataverse capacity implications of Link to Fabric | Microsoft positions the shortcut as not duplicating storage. Confirm current terms before making any cost claim |
| 6 | Region availability and alignment requirements for Link to Fabric | A hard blocker if misaligned — see [`ingestion-link-to-fabric.md`](ingestion-link-to-fabric.md) |
| 7 | Fabric trial terms and duration | Whether a build can start before a paid SKU is in place |
| 8 | Power BI per-user license tiers and what each permits | Report distribution model depends on it |

Where a JourneyTeam customer-facing deck includes a licensing table, that table is a
**snapshot with a date on it**, refreshed from Microsoft's published pricing before each
use. Do not carry figures forward between opportunities.

## Capacity sizing

No general formula. Drivers to assess per customer:

- **Dataverse data volume** across the linked tables
- **Snapshot volume and retention** — the one factor this architecture adds, and the one
  that grows. See [`snapshot-and-history.md`](snapshot-and-history.md#sizing-and-cost)
- **Refresh frequency** of Silver, Gold, and semantic models
- **Concurrent report users** and query complexity
- **Whether the Power BI viewer threshold is being crossed anyway** — if the customer is
  near it, the larger SKU may be cheaper than the per-user licenses it replaces, which is
  often the deciding argument

Practical guidance:

- Start a build on a trial or a small SKU; size production from observed usage rather than
  estimated usage.
- Capacity can be scaled after go-live. Say so — it removes a common objection about
  committing to a number before anyone knows the answer.
- If the customer is anywhere near the Power BI viewer threshold, model both sides. It
  frequently changes the recommendation.

## Cost conversation framing

The honest version, which holds up better than an optimistic one:

1. **Services are fixed and known** — from $15,000, published contents, 6 weeks.
2. **Capacity is recurring and variable**, sized to their data and users, and can start
   small.
3. **Snapshots are the one growing cost**, they are what makes history possible, and
   retention is a dial the customer controls.
4. **The Fabric platform is reusable.** The next Dynamics app, and any non-Dynamics source,
   lands on capacity already paid for. That is what makes the second engagement cheap and
   is the strongest long-term argument.

## Do not

- Quote any figure from this repository without re-verifying it.
- Restate licensing behavior from memory into a proposal or deck.
- Imply that Fabric capacity is included in any fixed price.
- Promise Copilot functionality without confirming the customer's SKU supports it.
- Size a production capacity before seeing the customer's actual data volumes.
