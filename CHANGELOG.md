# Changelog

Anything that changes what gets delivered to a customer belongs here — pack contents,
metric definitions, pricing, conformance layer behavior, delivery process.

The **conformance layer version** recorded here is what gets written into a customer's
handoff documentation, and it is what any future upgrade path will depend on. Keep it
accurate.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning is per
offering release, not per commit.

## [Unreleased]

### Added — JTP first build project plan

- `docs/delivery/jtp-first-build-plan.md` — development plan for the Sales pack's first
  build against JourneyTeam's own Dynamics 365 Sales system, with one developer. Two
  releases, ~124 developer-days including contingency, calendar scenarios by allocation,
  critical path, single-developer risks, and definition of done
- Change control classification: JTP is JT **Production**, so development routes through
  JT Dev and the Link to Fabric enablement is a change request with a documented promotion
  path and rollback
- `docs/delivery/playbook.md` — notes that the 6-week customer timeline presumes the JTP
  build has happened first

### New findings from planning the JTP build

JourneyTeam sells professional services by technology practice as a Microsoft Partner, and
that shape was not what the Sales pack was drafted against:

- **J1** — practice does not exist in stock Dynamics 365 Sales and may be **line-level**, if
  one opportunity can span practices. That flips technical design decision **D8**
  (opportunity products) from optional to mandatory, and risks mis-attributing
  multi-practice deals
- **J2** — revenue type mix (project services, managed services annuity, licensing resale,
  Microsoft-funded) means a single summed pipeline value is misleading
- **J3** — whether `estimatedvalue` is total contract value or annualised, and whether it is
  consistent. If mixed, pipeline totals are meaningless regardless of report design
- **J4** — whether Microsoft-sourced / co-sell pipeline is tracked in Dynamics at all
- These apply to **any professional-services or Microsoft Partner customer**, so the build
  may yield a reusable professional-services variant of the pack rather than a JT-specific one
- **Confidentiality**: the reports contain JourneyTeam's real pipeline, win rates and
  margins, which conflicts with using JTP as the demo environment. A synthetic dataset is
  recommended, doubling as the performance test bed JTP is too small to provide

### Added — Sales pack technical design

- `packs/sales/technical-design.md` — technical design document for the Dynamics 365 Sales
  solution: scope and assumptions, Bronze table set, Silver design (conformed dimensions,
  `dim_opportunity`, five facts, polymorphic customer resolution, per-column time zone
  treatment), snapshot and derived history design, Gold star schema, semantic model
  (storage mode, 23 relationships, model hygiene), measure patterns, RLS, 8 report pages,
  orchestration, sizing, reconciliation, 10 open decisions, and a 14-step build sequence
- `packs/README.md` — technical design documents are now part of the pack structure, with
  the Sales document as the reference example

### Changed

- `platform/notebooks/40_gold_conformed_dimensions.py` — documented **open decision D9**
  against the SCD2 current-rows-only filter. The Sales design shows the filter breaks
  as-of ownership on snapshot facts, which affects every pack. Needs a platform decision
  before the first semantic model is built over a snapshot fact

### New findings requiring a decision beyond the Sales pack

- **D9** — whether `gold.dim_owner` (and `dim_customer`, `dim_product`) should publish all
  SCD2 versions rather than current rows only. Affects snapshot ownership in every pack
- **D10** — whether contact-owned opportunities require a unified party dimension in place
  of an account-only `dim_customer`. Would change a conformed dimension, so it needs an ADR
  if the contact share proves material

### Added — initial repository definition

**Offering definition**
- Offering overview, positioning, competitive frame, and business outcomes
- Pricing and packaging: platform $7,500, packs $5,000, cross-app pack $7,500;
  BASE $15,000 / PLUS $20,000 / PREMIUM $30,000, with the discount ladder made explicit
- Roadmap with per-pack GA gates, build sequence, and known gaps in the offering

**Architecture**
- Reference architecture and validation status
- Link to Fabric ingestion, and the strategic consequence that ingestion is not the IP
- Medallion design: schema layout, naming, orchestration order
- **The Dataverse conformance layer** — the seven problems it solves, documented as the
  offering's core IP
- **Snapshots and history** — the second IP pillar, and why the job must start in Sprint 1
- Security and RLS scope, including what is explicitly not achievable
- Licensing and capacity verification checklist (deliberately not a price list)

**Decisions**
- ADR 0001 — use Link to Microsoft Fabric for ingestion (Accepted)
- ADR 0002 — offering and portfolio naming (Proposed)
- ADR 0003 — Project Operations deployment scope (Proposed) — **blocks quoting that pack**
- ADR 0004 — Revenue-to-Delivery packaging (Proposed)

**Delivery**
- Three-sprint, six-week playbook with per-sprint exit criteria
- Pre-sales qualification questions and the customer access request list
- UAT plan with defect / configuration / change-request triage
- Training and adoption guidance by audience
- Support handoff checklist and known limitations to state plainly

**Platform (drafts, never executed)**
- Shared notebook helpers
- `10` Bronze shortcut validation — the gate for the whole run
- `20` choice label conformance — metadata source **unresolved**, see its VERIFY block
- `21` currency normalization
- `22` ownership hierarchy — SCD2 merge still TODO
- `23` activity bridge — polymorphic `regardingobjectid` resolution
- `24` date dimension with fiscal calendar — holiday calendar still TODO
- `30` snapshot facts with completeness checking
- `40` Gold conformed dimension publication as views, not copies
- Per-customer configuration template and pipeline design notes

**Report packs (definitions only)**
- Conformed dimension specification
- Sales — README, source tables, 20 metric definitions
- Customer Service — README, source tables, 20 metric definitions
- Project Operations — README, source tables, 16 metric definitions (scope gated)
- Field Service — README, source tables, 20 metric definitions
- Revenue-to-Delivery — README and 11 metric definitions, v1/v2 split

**Sales assets**
- Extended deck outline with the five slides where it must differ from the BC deck

### Known state

- **No artifact in `platform/` or `packs/` has been validated against a live Dataverse
  environment.** All source table mappings and notebooks are drafts and contain errors.
  See `docs/architecture/reference-architecture.md#validation-status`
- Three of four ADRs are **Proposed** and need an owner decision before the first quote
- The choice-label metadata source is the **most important unresolved technical item**
- The holiday / working-day calendar does not exist, so all business-hours metrics are
  currently calendar-hours
- No semantic models or reports have been built
- Conformance layer version: **0.1.0-draft**
