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

Status is one of **Proposed**, **Accepted**, **Rejected**, or **Superseded by NNNN**. An
ADR is never edited after acceptance except to change its status; a changed decision gets
a new ADR that supersedes the old one.

## Index

| # | Title | Status |
|---|---|---|
| [0001](0001-use-link-to-fabric-for-ingestion.md) | Use Link to Microsoft Fabric for ingestion | Accepted |
| [0002](0002-offering-naming.md) | Offering and portfolio naming | **Proposed** |
| [0003](0003-project-operations-scope.md) | Project Operations pack deployment scope | **Proposed** |
| [0004](0004-cross-app-pack-packaging.md) | Revenue-to-Delivery pack packaging | **Proposed** |

Three of four are Proposed and need an owner decision before the first customer quote.
