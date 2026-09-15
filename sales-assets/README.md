# Sales assets

Customer-facing material for the offering. **Nothing committed yet.**

## Planned assets

| Asset | Purpose | Source of truth |
|---|---|---|
| Extended deck | Full offering presentation, sibling to the Business Central deck | [`deck-outline.md`](deck-outline.md) |
| One-pager | Leave-behind summary | `docs/offering/overview.md` |
| Demo script | Guided demo against JourneyTeam demo data | — |
| Architecture diagram | Portfolio and edition-level | `docs/architecture/reference-architecture.md` |
| Proposal template | With the standard exclusions pre-filled | `docs/offering/pricing-and-packaging.md` |

## Rules

1. **Never restate prices here.** Reference
   [`../docs/offering/pricing-and-packaging.md`](../docs/offering/pricing-and-packaging.md).
   A price that exists in two places will eventually disagree — which is exactly what
   happened to the Business Central deck, where the platform fee appears as both $7,500 and
   $10,000.
2. **Never quote a pack that is not GA.** Check
   [`../docs/offering/roadmap.md`](../docs/offering/roadmap.md) before every proposal.
3. **Microsoft licensing figures are dated snapshots**, re-verified from Microsoft's
   published pricing before each use. See
   [`../docs/architecture/licensing-and-capacity.md`](../docs/architecture/licensing-and-capacity.md).
4. **No customer data in any asset.** Demo material uses JourneyTeam demo data only. No
   screenshots containing real customer records.
5. **Carry the edition name in every filename** to avoid ambiguity with Business Central
   material — see [ADR 0002](../docs/decisions/0002-offering-naming.md).
6. **Do not claim first-party analytics are bad.** Customer Service and Field Service ship
   respectable embedded analytics. The honest framing in
   [`../docs/offering/positioning.md`](../docs/offering/positioning.md) is more persuasive
   and does not lose credibility with a prospect who uses them.

## Standard proposal exclusions

Every proposal states these. Each is defensible in advance and damaging when discovered
later:

- Microsoft Fabric capacity and Power BI licensing
- Custom Dataverse tables and columns
- Non-Dataverse data sources
- Dynamics 365 Finance & Operations data — **including F&O-resident Project Operations
  financials** ([ADR 0003](../docs/decisions/0003-project-operations-scope.md))
- Dataverse security parity in Power BI ([RLS scope](../docs/architecture/security-and-rls.md))
- Snapshot history prior to deployment — not backfillable
- Business-hours-based metrics, until the working-day calendar ships
- Post-go-live support and enhancement (no annuity exists yet)
