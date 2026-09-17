# Changelog

Anything that changes what gets delivered to a customer belongs here — pack contents,
metric definitions, pricing, conformance layer behavior, delivery process.

The **conformance layer version** recorded here is what gets written into a customer's
handoff documentation, and it is what any future upgrade path will depend on. Keep it
accurate.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning is per
offering release, not per commit.

## [Unreleased]

### Changed — repository narrowed to Dynamics 365 Sales only

**Scope decision: this repository is the working space for the Sales pack.** The offering
was defined around four Customer Engagement report packs plus a cross-app pack. The other
four are **deferred, not cancelled** — cross-app functionality is intended and will be
built; it needs a second pack before it has anything to span.

- **Removed** `packs/customer-service/`, `packs/project-operations/`, `packs/field-service/`
  and `packs/revenue-to-delivery/` — 11 files, 67 metric definitions and four source-table
  mappings. Recoverable from git history; `docs/offering/roadmap.md` records where from and
  what each was worth keeping
- **Re-scoped** the offering to *JourneyTeam Analytics for Dynamics 365 Sales*: README,
  `CLAUDE.md`, offering overview, positioning, roadmap, packs README, reference
  architecture, medallion design, conformance layer, RLS, playbook, UAT, training, support
  handoff, prerequisites, config template, deck outline
- **ADR 0003** (Project Operations scope) and **ADR 0004** (Revenue-to-Delivery packaging)
  re-statused **Deferred**, bodies unedited — the reasoning is what would make either pack
  cheap to bring back. `Deferred` added to the allowed ADR statuses
- **ADR 0002** (naming) flagged as partly overtaken: it named the edition *for Customer
  Engagement* on a four-pack premise
- `docs/decisions/README.md` now lists the five decisions the repository owes but tracks in
  prose — pricing, medallion topology, D9, the choice-label metadata source, and the
  missing annuity/upgrade path
- Platform trimmed rather than rewritten: `30_silver_snapshot_facts` keeps only the
  opportunity snapshot spec, `23_silver_conformance_activities` keeps only Sales activity
  targets, `40_gold_conformed_dimensions` no longer justifies conformance by cross-app
  reuse, `customer.example.yaml` drops the tier and the Customer Service tables and gains
  `opportunityproduct`
- `dim_project` dropped from the conformed dimension inventory; every other conformed
  dimension stays conformed and unprefixed

### Commercial consequences of narrowing — both need an owner decision

- **The package structure no longer works.** BASE / PLUS / PREMIUM priced by *how many of
  four packs* the customer chose. With one pack there is nothing to choose between and the
  discount ladder has nothing to reward. `pricing-and-packaging.md` carries a **proposed
  $12,500 single fixed price** (platform $7,500 + Sales $5,000 + 4 hours coaching; list
  value $13,760) — **proposed, not agreed.** Nothing is quotable and no sales asset stating
  a price can be produced until it is signed off
- **The offering is a differentiator short until cross-app ships.** Cross-app analytics is
  one of three stated defensible pillars and **the only one with no first-party
  equivalent**. It is **deferred, not cancelled** — it is intended and will be built, but
  it needs a second, delivery-side pack before it has anything to span. Until then
  differentiation rests on the conformance layer and snapshot history — both real, both
  narrower. `positioning.md` and the deck outline lead with history and custom fields, and
  deliberately do **not** carry cross-app as a roadmap item: a differentiator that cannot
  be demoed costs more credibility than one never raised
- **Timeline inconsistency flagged, not silently resolved.** The playbook is three sprints
  over six weeks; the offering now quotes 4–5 weeks. The saving is entirely in Sprint 2
  (one pack, not two to four), so Sprint 2 is marked as one week pending a real number from
  the first delivery

### Kept general on purpose, so cross-app stays cheap to add

The repository is a working space for Sales, not a Sales-shaped product, and the platform
carries generality one pack does not need:

- Conformed dimensions stay conformed and unprefixed — a second pack that cannot point at
  the same `dim_customer` and `dim_owner` cannot be joined to this one at all
- Gold keeps its `sales__` pack prefix, so a second pack lands without renaming anything
- `bridge_activity` keeps resolving polymorphic targets rather than hard-coding Sales
- `dim_owner` stays SCD2 and remains the source of the RLS model
- `quote` / `salesorder` stay in the Bronze set — the project contract is built on
  `salesorder`, which is the join point from pipeline into delivery

`roadmap.md` now carries this as a table with the reason and the file for each, plus the
cheapest route back: a delivery-side pack, since Revenue-to-Delivery has nothing to span on
its own. ADR 0003 is the first question to answer on that route.

### Added — Bronze data profiling

- `docs/bronze-profiling/` — per-entity profiles of Dataverse **as Link to Fabric actually
  exports it**, observed against the live JTP environment. Folder rules, method, and the
  platform patterns that apply to every entity
- `docs/bronze-profiling/opportunity.md` — full profile of `opportunity`: **343 columns**
  as exported, column inventory by role, observed choice integers, ten findings that change
  the design, eleven data quality issues, the fact column selection, and eleven measures
  still needing full-table counts
- `docs/bronze-profiling/samples/` — de-identified sample plus its generator. The generator
  takes **no real data as input**; it synthesises from the documented profile, so it cannot
  leak. 12 rows × 343 columns covering multi-practice, won, lost-with-custom-status,
  OOB-cancelled, co-sell, contact-party, test-data, soft-deleted and pre-cutover shapes

### Platform patterns confirmed (apply to every Dataverse entity)

- Lookups arrive as `<column>` + **`<column>_entitytype`** pairs — **polymorphism is
  resolved inline**, so no `TargetMetadata` join is needed
- Lookup labels arrive denormalized as `<column>name` — free labels, but no hierarchy
- **Choices are raw integers with no labels** — the `OptionsetMetadata` dependency stands
- `PartitionId` is the `createdon` **year**; `IsDelete` **must be filtered on every Bronze
  read**; rollup fields ship with `_date` / `_state` staleness twins

### Changed — decisions resolved or narrowed by the profile

- **D4 answered: neither `salesstagecode` nor BPF.** Stage is `jt_sales_stage`;
  `traversedpath` / `stageid` / `processid` are all NULL, so **BPF stage history does not
  exist**. Snapshots or audit are the only routes
- **D8 answered: opportunity products are mandatory.** `isrevenuesystemcalculated` = 1 and
  `estimatedvalue` = `totallineitemamount` — the lines are the revenue source, not an
  optional Products page
- **D1 narrowed** — `statecode = 2` mixes OOB Canceled with JT custom loss reasons;
  grouping must be at `statuscode` grain
- **D2 answered yes**, with two fields and an incomparable historic range
- **D5 answered yes**; **D10 de-risked**; **D6 source changed** to the
  `jt_lastactivitydate` rollup, because `modifiedon` is polluted by automation
- **Forecast category is in Dataverse** (`jt_forecastcategory`), so the Forecast page needs
  no Dynamics change — subject to its fill rate
- `dim_resource` is now needed by the **Sales** pack: `jt_presalesresource` is a
  `bookableresource`, not a `systemuser`

### New blocking question

- **D11 — where does Team (AE / SAM / SDR) come from?** It is the primary segment for every
  report page and it is **not on `opportunity`**: `owningteam` is NULL throughout and there
  is a single flat business unit. That also means BU-based RLS cannot be validated at JTP

### Largest analytic constraint found

The JT custom analytic schema (`jt_primaryproduct_1`, `jt_backlogtype`, `jt_sales_stage`,
`jt_forecastcategory`, `jt_interests`) is **NULL on pre-cutover rows**. The table spans
2010–2026; practice, revenue-type, stage and forecast trends can only reach back to the
cutover date, which still needs measuring.

### Added — analysis of the existing Excel pipeline report

- `docs/reference/jtp-excel-pipeline-report.md` — structural analysis of JourneyTeam's
  Sales Weekly Pipeline Report (29 sheets, 50 pivots, 6 manual Dynamics exports). Captures
  the sales model taxonomies, the full metric inventory, the goal model, and the business
  rules that cannot be inferred from Dataverse
- `docs/reference/README.md` — folder rules: structure not data, source binaries stay out
  of the repository

### Settled by that analysis

- **J1** — practice is **both** header (`Primary Product (New)`) and a multi-value
  additional-practices field, so attribution is many-to-many and needs a bridge table
- **J2** — revenue type confirmed as `Backlog Type` (6 values); PS and Licensing already
  separated
- **J4** — Microsoft-sourced pipeline is tracked, across 5+ overlapping fields, and needs
  consolidating into one conformed grouping
- **D2** — close probability is maintained, but in three bands with no sub-50% floor
- **D3** — targets exist and are rich (rep × quarter × lead source, including funnel
  conversion targets) but live in a spreadsheet, not Dataverse, so they are a new source
- **D4** — stage appears to come from `Sales Stage` directly, not a business process flow
- **D5** — loss reason is populated and usable
- **J3 remains open** and is now the most important unanswered question: whether
  `Est. Revenue` on annuity backlog types is total contract value or annualised

### New requirements for the Sales pack

18 requirements not in the pack as drafted, notably:

- A **three-factor weighting model** (stage × relationship × backlog weight) that
  **replaces** the drafted `Weighted Pipeline Value` definition
- **Rolling 30/60/90-day pipeline windows**, which are the primary pipeline view rather
  than fiscal periods
- **Cohort win rate with maturation gating**, alongside the drafted win rate
- Forecast categories, practice mapping for 17 legacy values, relationship type,
  pre-sales resource, mega-deal handling, outlier exclusion variants, and exclusion of
  system-generated activity types
- Report pack grows from 8 pages to **11** — Practice Performance, Attainment, and SDR are
  central to how JourneyTeam operates and were absent
- **Quota retirement rules** recommended **out of scope for Release 1**; they currently
  exist as spreadsheet precedent rather than written policy

### Note on the source file

The workbook was **not committed**. It holds real customer names, deal values, and
named-employee quota and ranking data; git history is permanent and this repository is
pushed to GitHub. The analysis captures the design intelligence with no names, customers,
or figures. A structurally redacted copy would be committable if one is wanted.

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
