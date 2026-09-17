# 0004 — Revenue-to-Delivery pack packaging

**Status:** **Deferred** — the cross-app pack is out of scope for this repository

> **Deferred with the pack, 2026-09-17.** The repository was narrowed to Dynamics 365 Sales
> only, so this decision is not live. The body below is unedited — it holds reasoning worth
> keeping if the pack returns. See
> [`../offering/roadmap.md`](../offering/roadmap.md).


## Context

The four Dynamics 365 CE apps share Dataverse. Once the
[conformance layer](../architecture/conformance-layer.md) exists and two or more packs are
built, a cross-app model spanning **Sales → Project Operations → Field Service** is
architecturally cheap: opportunity → contract → project → work order → realized margin,
end to end on conformed dimensions.

It is also the one thing in the offering that **no first-party Dynamics 365 analytics
does at all.** Not "does worse" — does not do. Customer Service and Field Service ship
respectable embedded analytics, but nothing spans apps.

That makes it the strongest single proof point in the offering, and the question is how to
package it.

## Options

1. **PREMIUM-only** — the reason to buy the top tier.
2. **Add-on, available to any customer with 2+ packs**, at $7,500, and included in PREMIUM.
3. **Included free with any multi-pack purchase** — pure differentiation, no separate revenue.
4. **Fold it into the per-pack price** — every pack contributes its slice of the cross-app
   model.

## Recommendation

**Option 2 — priced add-on at $7,500, requiring 2+ packs, and included in PREMIUM.**

This is how it is already modelled in
[`../offering/pricing-and-packaging.md`](../offering/pricing-and-packaging.md).

Rationale:

- **It creates the upsell path that the offering otherwise lacks.** A BASE or PLUS
  customer who is live and happy has, today, nothing obvious to buy next except more
  packs. Revenue-to-Delivery is a natural, high-value second conversation with an
  installed customer — the cheapest sale in the portfolio.
- **It still anchors PREMIUM.** Including it in PREMIUM is what justifies the $30,000 tier
  and the 25% discount, so Option 1's benefit is retained without Option 1's cost.
- **Option 3 gives away the best proof point.** Something demonstrably unavailable
  elsewhere should not be free. It can be *demonstrated* freely — that is what the demo is
  for — without being *given* freely.
- **Option 4 is dishonest pricing.** It raises the entry price for single-pack customers to
  fund something they cannot use, which undercuts the $15,000 entry point that the whole
  offering depends on.

## Consequences

**If accepted:**

- Pricing stands as documented. No changes needed.
- The prerequisite must be enforced in quoting: the cross-app pack requires 2+ packs, and
  specifically requires the packs whose data it spans. Selling it alongside Sales +
  Customer Service — neither of which is in the revenue-to-delivery chain — would not
  deliver the promised model. **The dependency is on specific packs, not on any two.**
- It builds last ([`../offering/roadmap.md`](../offering/roadmap.md)), so it cannot be
  quoted for some time. Until then it is a roadmap item in the deck, clearly marked, not a
  line in a proposal.
- The demo needs it even before it is GA, because it is the most persuasive thing to show.
  Worth building against JourneyTeam demo data ahead of customer availability.

**Open sub-question:** what is the minimum viable version? Sales → Project Operations
(quote-to-project-margin) is a complete, sellable story on its own and needs only two
packs. Adding Field Service makes it broader but is not required for it to be valuable.

**Recommendation on that:** ship Sales → Project Operations first as the v1 of the pack,
and extend to Field Service in v2 rather than waiting for all three. It reaches
sellability considerably sooner, and the extension is additive rather than a rebuild.

## Naming note

"Revenue-to-Delivery" is the working name. Alternatives considered: "Lead-to-Cash" (implies
finance data this pack does not have, and invites an F&O expectation — see
[ADR 0003](0003-project-operations-scope.md)), "Cross-App Analytics" (accurate, describes
the mechanism rather than the value), "Customer Lifecycle" (vague). Revenue-to-Delivery
describes the business process the customer recognizes and avoids promising financial
posting data. Keep it unless marketing has a strong objection.
