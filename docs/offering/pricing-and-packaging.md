# Pricing and packaging

**This file is the single source of truth for prices and package contents.** Reference it
from other documents; do not restate numbers elsewhere. Changes require offering-owner
sign-off.

Pricing mirrors the Business Central edition's structure and discount ladder so the two
sell as one portfolio.

## À la carte

| Component | Price | Includes |
|---|---|---|
| **Platform** | **$7,500** fixed | Link to Fabric configuration, Bronze shortcut validation, **Dataverse conformance layer**, conformed Date / Currency / Owner / Team / Business Unit dimensions, snapshot framework, RLS scaffold, SQL endpoint enablement |
| **Report pack** | **$5,000** each | Silver and Gold layers for the subject area, Power BI semantic model, Power BI report pack. Available: Sales, Customer Service, Project Operations, Field Service |
| **Revenue-to-Delivery pack** | **$7,500** | Cross-app semantic model and reports spanning Sales → Project Operations → Field Service. Requires 2 or more report packs |
| **Coaching** | **$3,150** / **$6,000** | +10 hours or +20 hours of personalized coaching and adoption, including Copilot enablement |

**Not included in any fixed price:** Microsoft Fabric SKU licensing, Power BI licensing,
and any Dataverse capacity implications. See
[`../architecture/licensing-and-capacity.md`](../architecture/licensing-and-capacity.md).

## Packages

| Tier | Contents | List value | Discount | **Price** |
|---|---|---|---|---|
| **BASE** | Platform + **2** report packs + 4 hrs coaching | $18,760 | 20% | **$15,000** |
| **PLUS** | Platform + **3** report packs + 10 hrs coaching | $25,650 | 22% | **$20,000** |
| **PREMIUM** | Platform + **all 4** report packs + Revenue-to-Delivery + 20 hrs coaching | $41,000 | 25% | **$30,000** |

All tiers include Copilot enablement as part of coaching. All tiers exclude Fabric and
Power BI licensing.

### Package math

Kept explicit so the discount ladder stays defensible in a negotiation.

```
BASE     7,500 + (2 × 5,000) + 1,260  = 18,760  × 0.80 = 15,008  → $15,000
PLUS     7,500 + (3 × 5,000) + 3,150  = 25,650  × 0.78 = 20,007  → $20,000
PREMIUM  7,500 + (4 × 5,000) + 7,500 + 6,000 = 41,000  × 0.75 = 30,750  → $30,000
```

The 4-hour coaching allotment in BASE is priced at the $315/hr coaching rate implied by the
+10 hour block.

PREMIUM rounds down $750 below the 25% line. That is deliberate — a clean $30,000 number
is worth more in a conversation than the extra $750, and it makes PREMIUM the obvious
anchor.

## Additional development (scoped separately)

Quoted per engagement, outside the fixed price:

- Extract additional Dataverse tables or custom tables and columns
- Bring additional data sources into the Fabric platform (on-prem, cloud, file, streaming)
- Ingest Dynamics 365 Finance & Operations data (different ingestion path — see
  [ADR 0003](../decisions/0003-project-operations-scope.md))
- Develop additional semantic models
- Develop additional Power BI reports and dashboards
- Build and deliver a custom training plan

## Positioning notes for the pricing conversation

- **Hold the platform fee at $7,500.** The Business Central edition needed a custom
  extension and the CE edition does not, so there is an obvious temptation to discount.
  Do not. The effort moved into the conformance layer, which is the harder and more
  valuable work, and a lower anchor undercuts the BC package it sits beside.
- **PREMIUM is fully deliverable.** Unlike the BC edition's PREMIUM tier, every component
  of CE PREMIUM exists once the four packs ship. Nothing is sold as "available later."
  Confirm against [`roadmap.md`](roadmap.md) before quoting it.
- **The 6-week timeline is part of the price.** Faster than the BC edition, because there
  is no extension to build and deploy.
- **Licensing is the customer's line item, not ours.** Fabric SKU comes out of a different
  budget than services. Surface it early so it does not surface late.

## Differences from the Business Central edition

| | BC edition | CE edition |
|---|---|---|
| Platform fee | $7,500 | $7,500 |
| Per-suite | $5,000 | $5,000 |
| Cross-app pack | none | $7,500 |
| BASE / PLUS | $15,000 / $20,000 | $15,000 / $20,000 |
| Top tier | $29,000 (5 suites, some TBD) | $30,000 (4 packs + cross-app, all deliverable) |
| Delivery | 8 weeks | 6 weeks |

> The BC extended deck currently shows the platform at **$10,000** on its Microsoft-comparison
> slide and **$7,500** on its pricing slide. $7,500 is the correct number and the BC deck
> needs correcting. Do not propagate the $10,000 figure into CE material.
