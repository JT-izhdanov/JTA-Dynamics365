# Architecture decision records

Decisions that shape the offering — architectural, scope, or commercial — are recorded
here so that the reasoning survives the people who were in the room.

## When to write one

Write an ADR when a choice:

- Changes the architecture or the delivery model
- Changes what is in or out of scope for a fixed price
- Changes pricing, packaging, or naming
- Commits the offering to a Microsoft capability or rules one out
- Will otherwise be re-argued in six months by someone who was not present

Do not write one for implementation detail that the code already documents.

## Format

One file, `NNNN-short-title.md`, numbered sequentially. Keep it short — context, decision,
consequences, and enough of the alternatives to show the choice was considered.

Status is one of **Proposed**, **Accepted**, **Rejected**, **Deferred**, or **Superseded
by NNNN**. An ADR is never edited after acceptance except to change its status; a changed
decision gets a new ADR that supersedes the old one.

**Deferred** means the decision is sound but its subject left scope — the body is kept
unedited because the reasoning is what makes the pack cheap to bring back.

## Index

| # | Title | Status |
|---|---|---|
| [0001](0001-use-link-to-fabric-for-ingestion.md) | Use Link to Microsoft Fabric for ingestion | Accepted |
| [0002](0002-offering-naming.md) | Offering and portfolio naming | **Proposed** |
| [0003](0003-project-operations-scope.md) | Project Operations pack deployment scope | **Deferred** |
| [0004](0004-cross-app-pack-packaging.md) | Revenue-to-Delivery pack packaging | **Deferred** |

0003 and 0004 were deferred when the repository narrowed to Sales only. **Deferred means
not live, not cancelled** — cross-app functionality is still intended, and 0003 is the
first question to answer on the way back to it. 0002 is still Proposed and is now partly
overtaken by that narrowing.

## ADRs this repository still owes

Open questions currently tracked in prose rather than as decisions. Each should be an ADR
before the first customer delivery:

| Subject | Currently tracked in |
|---|---|
| **Pricing for a single-pack offering** — the tier ladder priced by pack count and no longer works | [`../offering/pricing-and-packaging.md`](../offering/pricing-and-packaging.md) |
| **Medallion topology** — one lakehouse with three schemas (reference) vs. three lakehouses across two workspaces (deployed) | [`../architecture/jt-medallion-topology.md`](../architecture/jt-medallion-topology.md) |
| **D9** — whether Gold publishes all SCD2 versions rather than current rows only; the current filter breaks as-of ownership on snapshot facts | [`../../packs/sales/technical-design.md`](../../packs/sales/technical-design.md) |
| **Choice-label metadata source** — the most important unresolved technical item in the platform | [`../../platform/notebooks/20_silver_conformance_choice_labels.py`](../../platform/notebooks/20_silver_conformance_choice_labels.py) |
| **No post-go-live annuity and no upgrade path** | [`../offering/roadmap.md`](../offering/roadmap.md#known-gaps) |
