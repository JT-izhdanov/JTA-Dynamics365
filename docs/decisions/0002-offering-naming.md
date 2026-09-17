# 0002 — Offering and portfolio naming

**Status:** Proposed — **and now partly overtaken.** This ADR named the edition *for
Customer Engagement* on the premise of four report packs. The repository covers **Sales
only**, and the offering is titled *JourneyTeam Analytics for Dynamics 365 Sales*. The
portfolio reasoning below still holds; the edition boundary needs a new ADR if Sales-only
is permanent. See [`../offering/roadmap.md`](../offering/roadmap.md).

## Context

The Business Central offering is titled *"JourneyTeam Analytics for Microsoft Dynamics 365
Business Central."*

Naming this one *"JourneyTeam Analytics for Dynamics 365"* collides with it, because
**Business Central is also Dynamics 365.** A customer holding both titles cannot tell what
either covers, and internally there is no unambiguous way to refer to one edition.

There is also a third edition on the horizon — Finance & Operations
([`../offering/roadmap.md`](../offering/roadmap.md#deferred)) — so this needs
solving as a portfolio, not as a one-off title fix.

Complicating factor: "Customer Engagement" is accurate Microsoft terminology and is
understood by partners and IT, but it is *not* how most business buyers describe
themselves. A sales director says "we use Dynamics for sales," not "we use Dynamics 365
Customer Engagement."

## Options

1. **Portfolio umbrella with editions** — *JourneyTeam Analytics*, with *for Business
   Central*, *for Customer Engagement*, *for Finance & Operations*.
2. **Name by app** — *JourneyTeam Analytics for Dynamics 365 Sales*, *for Customer
   Service*, and so on. Four names for this edition alone.
3. **Distinct product names per edition** — e.g. separate brands.
4. **Name by function** — *JourneyTeam CRM Analytics* vs. *ERP Analytics*.

## Recommendation

**Option 1 — portfolio umbrella with editions.**

```
JourneyTeam Analytics
├── for Business Central          (ERP — existing)
├── for Customer Engagement       (CRM — this repository)
└── for Finance & Operations      (ERP — roadmap candidate)
```

Within the CE edition, the four report packs (Sales, Customer Service, Project Operations,
Field Service) are *components*, not separate products. That keeps one architecture story,
one pricing ladder, and one delivery playbook per edition.

Rationale:

- Option 2 fragments the offering into four products with one architecture, quadrupling
  the sales material for no benefit, and has no place to put the cross-app pack.
- Option 3 loses the portfolio cross-sell, which is the strongest long-term motion in the
  whole offering ([`../offering/positioning.md`](../offering/positioning.md#cross-sell-the-portfolio-play)).
- Option 4 uses vocabulary that does not match Microsoft's, which works against the
  Microsoft-alignment value proposition.
- Option 1 makes "one Fabric platform, every Dynamics app" a natural sentence, and that
  sentence is the portfolio's best argument.

**On the "Customer Engagement" wording:** keep it as the formal edition name for internal
use, proposals, and SOWs where precision matters. In first-contact sales material, lead
with the app the customer actually named — *"JourneyTeam Analytics for Dynamics 365 —
Sales report pack"* — and let the edition name appear in the architecture and pricing
sections. Precision where it is contractual; the customer's own vocabulary where it is
persuasive.

## Consequences

**If accepted:**

- The BC deck's title and any existing BC collateral need a light rename to sit under the
  umbrella. Low cost now; higher the longer both editions exist under mismatched names.
- This repository stays named for the CE edition. A future F&O edition gets its own
  repository following the same structure, so the layout here is effectively the template.
- Shared assets — the portfolio architecture diagram, the cross-sell narrative — need a
  home neither edition owns. Worth deciding where before the second edition ships.
- `sales-assets/` in this repository should carry the edition name in every filename to
  avoid ambiguity with BC material.

**Cost of not deciding:** two decks with confusingly similar titles reach the same
customer, and the portfolio story — the most valuable part — never gets told because
nothing names it.
