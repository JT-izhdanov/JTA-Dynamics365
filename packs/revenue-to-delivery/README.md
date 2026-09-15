# Revenue-to-Delivery pack

**$7,500** · cross-app · **Status: planned — composed from the other packs**

Requires 2+ packs, and specifically the packs whose data it spans. Packaging rationale:
[ADR 0004](../../docs/decisions/0004-cross-app-pack-packaging.md).

## Why this pack exists

**It is the one thing no first-party Dynamics 365 analytics does at all.** Not "does
worse" — does not do.

Customer Service and Field Service ship respectable embedded analytics, and Sales has its
own. **None of them span apps.** Nothing in the Dynamics 365 product set answers "what did
this opportunity actually earn us once we delivered it?"

The four CE apps share Dataverse, so once the
[conformance layer](../../docs/architecture/conformance-layer.md) exists and the component
packs are built, this model is architecturally cheap for JourneyTeam and impossible for the
first-party apps. That asymmetry is the whole point.

## The chain

```
Opportunity ──► Quote ──► Contract ──► Project ──► Work Order ──► Realized Margin
(Sales)        (Sales)   (salesorder)  (Project Ops)  (Field Service)

              won value   contracted    delivered      serviced        what we
                          value         cost/revenue   cost            actually kept
```

**The join that makes it work:** in Project Operations, the **project contract is built on
`salesorder`** — the same table the Sales pack uses for orders. That single fact is what
links the sales chain to the delivery chain without any custom bridging. See
[`../project-operations/source-tables.md`](../project-operations/source-tables.md#the-contract-is-a-salesorder).

Field Service attaches through the customer, the asset, and — where used — the work order's
link to a project or agreement originating from the sale.

## Questions it answers

| Question | Why it cannot be answered elsewhere |
|---|---|
| What margin did we realize on this deal, after delivery? | Spans Sales and Project Operations |
| Which deal types consistently lose money in delivery? | Requires won value against delivered cost |
| How accurate is our sales estimate versus delivered reality? | Spans quote and actuals |
| Which customers cost the most to serve relative to what they buy? | Spans all three |
| What is the true lifetime value of a customer, net of service cost? | Spans all three |
| Do discounted deals deliver worse margin? | Requires quote discount against project margin |
| Which products generate the most post-sale service burden? | Spans Sales and Field Service |

The last two are the ones that tend to change how a business sells, which is why this pack
is worth more than the sum of its inputs.

## Minimum viable version

**Ship Sales → Project Operations first (v1); extend to Field Service in v2.**

Quote-to-project-margin is a complete, sellable story requiring only two packs, and it
reaches sellability considerably sooner. Adding Field Service broadens it but is not
required for it to be valuable, and the extension is additive rather than a rebuild.

Recommended in [ADR 0004](../../docs/decisions/0004-cross-app-pack-packaging.md).

## Prerequisites

- **Sales pack** (GA)
- **Project Operations pack** (GA) — and therefore
  [ADR 0003](../../docs/decisions/0003-project-operations-scope.md) resolved
- **Field Service pack** (GA) for v2
- The full conformance layer, with genuinely shared conformed dimensions

**The dependency is on specific packs, not on any two.** Selling this alongside Sales +
Customer Service would not deliver the promised model — neither Customer Service nor its
data sits in the revenue-to-delivery chain. Enforce this in quoting.

## The rule this pack depends on absolutely

**Conformed dimensions must be genuinely shared, not copied.**

This pack works only because Sales, Project Operations, and Field Service all point at the
*same* `dim_customer`, `dim_owner`, `dim_date`, and `dim_currency`. If any pack was built
with a local copy of a dimension, this model cannot be assembled without rework.

That is why [`../README.md`](../README.md#the-rule-that-matters-most) states the rule so
firmly, and why
[`40_gold_conformed_dimensions.py`](../../platform/notebooks/40_gold_conformed_dimensions.py)
publishes views rather than copies. **This pack is the reason the rule exists.**

## Known limitations

1. **Margin is PARTIAL for F&O-backed Project Operations deployments** — inherited directly
   from the Project Operations pack's scope boundary. For those customers, realized margin
   is an approximation from Dataverse-side actuals, not GL-tied financials. State this
   explicitly; it is the most likely source of disappointment in this pack.
2. **The chain requires the customer to actually use it.** If they do not create project
   contracts from won opportunities, the link is broken. Some organizations re-key work
   between apps, which severs it entirely.
3. **Attribution is a judgment call.** When one contract spans several opportunities, or one
   project serves several contracts, margin attribution requires an agreed rule. There is
   no technically correct answer — agree it with the customer and document it.
4. **Snapshot-dependent metrics** inherit each component pack's snapshot start date.
5. **Field Service linkage is the weakest.** Work orders often have no direct path back to
   an originating sale; asset and customer are usually the only reliable bridges.

## Open questions for the first build

- Does the customer create project contracts from won opportunities, or re-key?
- How should margin be attributed when contracts and opportunities are not one-to-one?
- Is there a reliable path from a work order back to an originating sale or project?
- Which grain does leadership want to see this at — deal, contract, customer, or product?

Question 1 is qualifying: if the answer is "we re-key," this pack should not be sold to
that customer until the process changes.
