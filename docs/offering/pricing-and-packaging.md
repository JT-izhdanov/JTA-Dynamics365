# Pricing and packaging

**This file is the single source of truth for prices and package contents.** Reference it
from other documents; do not restate numbers elsewhere. Changes require offering-owner
sign-off.

---

## ⚠ The package structure no longer works

The original structure priced three tiers by **how many of four report packs** the customer
chose:

| Tier | Contents | Price |
|---|---|---|
| BASE | Platform + **2** packs + 4 hrs coaching | $15,000 |
| PLUS | Platform + **3** packs + 10 hrs coaching | $20,000 |
| PREMIUM | Platform + **all 4** packs + cross-app pack + 20 hrs coaching | $30,000 |

With Sales as the only pack, **none of these tiers is sellable.** There is nothing to
choose between, and the discount ladder existed to reward buying more packs.

**This needs an owner decision before anything is quoted.** The recommendation below is a
proposal, not an agreed price.

---

## Components that still stand

| Component | Price | Includes |
|---|---|---|
| **Platform** | **$7,500** | Link to Fabric configuration, Bronze validation, **Dataverse conformance layer**, conformed Date / Currency / Owner / Customer dimensions, snapshot framework, RLS scaffold, SQL endpoint |
| **Sales report pack** | **$5,000** | Silver and Gold for Sales, Power BI semantic model, report pack |
| **Coaching** | **$3,150** / **$6,000** | +10 or +20 hours, including Copilot enablement |

**Not included in any fixed price:** Microsoft Fabric SKU licensing, Power BI licensing, and
any Dataverse capacity implications. See
[`../architecture/licensing-and-capacity.md`](../architecture/licensing-and-capacity.md).

## Recommended single-offer price

> **PROPOSED — needs offering-owner sign-off.**

| | |
|---|---|
| **JourneyTeam Analytics for Dynamics 365 Sales** | **$12,500 fixed** |
| Contents | Platform + Sales report pack + 4 hours coaching and Copilot enablement |
| Delivery | 4–5 weeks |
| Excludes | Fabric SKU and Power BI licensing |

Reasoning:

- **Component list value is $13,760** ($7,500 + $5,000 + 4 hrs at the $315/hr implied
  coaching rate). $12,500 is a clean number just under it.
- **No discount ladder.** A ladder rewards buying more; with one pack there is nothing more
  to buy, so a tier structure would be theatre. One price, published contents.
- **Keep the components visible.** When a second pack ships it is a clean **+$5,000**
  increment, and the tier structure can return without repricing the platform.
- **It lowers the entry point** from $15,000 to $12,500, which suits a single-pack offer
  aimed at a broader Sales installed base.

**Hold the platform at $7,500** if the components are ever quoted separately. It matches the
Business Central edition, and discounting it would undercut the sibling offering.

## Additional development (scoped separately)

- Extract additional Dataverse tables, or custom tables and columns
- Bring additional data sources into the platform (on-prem, cloud, file, streaming)
- Develop additional semantic models, reports or dashboards
- Build and deliver a custom training plan
- Deeper RLS beyond the scaffold — see [`../architecture/security-and-rls.md`](../architecture/security-and-rls.md)

## Positioning notes

- **Licensing is the customer's line item, not ours.** Fabric SKU comes out of a different
  budget than services. Surface it early so it does not surface late.
- **The timeline is part of the price.** 4–5 weeks for a single pack, against 8 weeks for
  the Business Central edition.
- **Nothing is sold as "available later."** One pack, GA, no TBD components — which the
  Business Central edition's top tier cannot currently claim.

## Note on the Business Central edition

Its extended deck shows the platform at **$10,000** on the Microsoft-comparison slide and
**$7,500** on the pricing slide. $7,500 is correct and that deck needs fixing. Do not
propagate $10,000.
