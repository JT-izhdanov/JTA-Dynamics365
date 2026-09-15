# Reference — JTP Excel weekly pipeline report

Structural analysis of JourneyTeam's existing **Sales Weekly Pipeline Report** (Excel,
macro-enabled), the report the Power BI dashboard will replace.

**Why this document exists:** the workbook is the most accurate requirements statement
available for the Sales pack as JourneyTeam actually needs it. It encodes years of
accumulated business rules, taxonomies, and metric definitions that no interview would
surface. This document captures that design intelligence so the build can reproduce it
deliberately rather than rediscover it.

> **No confidential data appears in this document.** The source workbook contains real
> customer names, opportunity values, and named-individual performance data. This analysis
> records **structure, taxonomies, metric definitions, and business rules only** — no
> customer names, no employee names, no figures. See [§14](#14-handling-of-the-source-file).

---

## 1. Source artifact

| | |
|---|---|
| File | `Sales_Weekly_Pipeline_Report_2026_Updated_1.xlsm` |
| Format | Macro-enabled workbook, ~28 MB |
| Created | 2025-08-21 |
| Last modified | 2026-09-15 |
| Author | Sales operations |
| Sensitivity label | Was applied, since removed |
| Sheets | 29 (24 visible, 5 hidden) |
| Pivot tables | 50, over 12 pivot caches |
| Slicers / timelines | 14 slicer caches, 7 timeline caches |
| Excel tables | 9 |
| VBA | `vbaProject.bin`, ~53 KB, refresh automation |

This is not a spreadsheet. It is an operational BI application built in Excel, and it
should be treated with the respect due to a working system when replacing it.

---

## 2. The current process, and what it proves

The workbook's own instruction sheet documents the weekly routine:

1. **Export raw data from JTP** and copy-replace into six input tabs
2. **Refresh all pivots** (50 of them)
3. **Spot check:** clear all filters, confirm top-level bookings / opportunity / lead
   figures match, set timeline dates to yesterday or prior week
4. If discrepancies appear, or values start returning NULL or `#N/A`, **contact one named
   person**

Two details in that instruction sheet are worth dwelling on:

- **"Only copy YESTERDAY'S activity and add to the file — lots of data so this helps
  w performance."** Someone is hand-building an incremental load, daily, because a full
  refresh is too slow. The activity table has grown past 36,000 rows this way.
- **"Ensure top level figures match"** is a manual reconciliation step, performed weekly,
  because the process has no integrity guarantee.

Several defined names in the workbook are broken: `BoM`, `BoMSept`, `Bom_Oct`, and
`booked` all resolve to `#REF!`. "BoM" is beginning-of-month — **someone was manually
capturing month-start pipeline to compare against, and those references have since
broken.** That is a hand-rolled snapshot mechanism that has failed silently.

This is the offering's value proposition stated in JourneyTeam's own operations:

| Business outcome | Evidence in this workbook |
|---|---|
| *No more export and wrangle* | Six manual exports, weekly, plus a daily manual activity append |
| *No more "where is that report?"* | One 28 MB file, one author, distributed by hand |
| *No more "why does my report not match yours?"* | Manual reconciliation is step 3 of the documented process |
| **History that cannot be backfilled** | The broken `BoM` snapshot references |
| Single point of failure | "Contact [one person]" is the documented error path |

---

## 3. Workbook architecture

The workbook is already a three-layer analytics architecture. Recognising this makes the
medallion mapping straightforward.

```
INPUT LAYER (6 tabs, manual Dynamics exports)        →  BRONZE / SILVER
  Pipe Input · Opp Input · Bookings Input
  Lead Input · Sequence Input · Activity Input

REFERENCE LAYER (3 hidden tabs)                      →  SILVER dimensions / config
  Rep Goal Reference · Forecast inputs · InterestMap

PIVOT LAYER (12 caches, 50 pivots, hidden helpers)   →  GOLD + semantic model
  Pipe pivot · Activity pivot

REPORT LAYER (16 visible report sheets)              →  POWER BI REPORT PACK
  Leaderboard · WEEKLY REPORT (All/AE/SAM)
  PIPELINE / REP / PRACTICE / SDR DEEP DIVE
  DAILY ACTIVITY · BOOKINGS · OPPORTUNITIES
  Budget Attainment · Attainment · Win rates & Deal Size
  Lead Source Performance · LEAD Summary
```

The input tabs carry `(Do Not Modify) Opportunity`, `(Do Not Modify) Row Checksum`, and
`(Do Not Modify) Modified On` columns — the signature of a Dynamics 365 **dynamic
worksheet export**. So every field in the workbook maps to a Dataverse column, which makes
the source mapping exercise considerably more tractable than starting from the schema.

---

## 4. Data volumes

| Table | Rows | Columns | Notes |
|---|---|---|---|
| `TablePipe` | 265 | 33 | Open pipeline |
| `TableOpps` | 872 | 32 | All opportunities |
| `TableBookings` | 460 | 23 | Won / booked |
| `TableLeads` | 7,150 | 59 | |
| `TableSequence` | 6,214 | 27 | Sequence targets |
| `TableActivity` | 36,517 | 23 | Manually appended daily |
| `TableTargets` | 138 | 11 | Rep × quarter × lead source goals |
| `InterestMap` | 15 | 2 | Interest → practice mapping |
| `WeeklyGoalsActuals` | 6 | 7 | Weekly scorecard |

**This confirms the volume assessment in the
[JTP build plan](../delivery/jtp-first-build-plan.md#the-volume-gap-is-the-one-that-matters):**
265 open opportunities and 872 total. Excellent for correctness testing, **useless as a
performance test bed.** Activity at 36,500 rows is the only table with any scale, and it
is the one Excel is already failing to handle.

---

## 5. The JourneyTeam sales model

Taxonomies extracted from the pivot caches. These are the real dimension members.

### 5.1 Teams — three distinct sales roles

`AE` · `SAM` · `SDR`

Each has its own report sheet and its own metric set. **AE and SAM have separate weekly
reports and separate leaderboards**, so team is not merely an attribute — it segments the
entire reporting model. `Non-Active Reps` appears as a roll-up member, so rep churn is
handled explicitly.

### 5.2 Practice — `Primary Product (New)`, 22 values, 5 current

| Current | Meaning |
|---|---|
| `CXC` | Customer Experience (Dynamics 365 CE) |
| `DAI` | Data & AI |
| `ERP` | Business Central / Finance & Operations |
| `SEC` | Security / Modern Work |
| `Licensing` | CSP licensing resale |

**Legacy and deprecated values also present on historical records:** `DS`, `PSC`, `ADM`,
`MWS`, `CRM`, `BIA`, `AZR`, `CSS`, `ACM`, `Enterprise ERP`, `Sales`, `IT`, and five
`zz_`-prefixed retired values (`zz_SP`, `zz_CSS`, `zz_AZR`, `zz_Enterprise ERP`,
`zz_ACM`).

**This is the single most important data quality finding.** Practice is the primary
analytic dimension, and 17 of its 22 values are legacy. Any multi-year practice trend
built naively on this field is wrong. The conformance layer needs a **practice grouping
dimension** mapping historical values to current practices — see
[§8.6](#86-practice-mapping).

### 5.3 Sales stage — 5 numbered stages

```
1 - Lead Outreach
2 - Strategic Alignment
3 - Strategy Session
4 - Solutions Meeting
5 - EOW Sent          (EOW = Estimate of Work)
```

Numbered prefixes mean they sort correctly as text, which is convenient. Stage is carried
on the opportunity as `Sales Stage`.

### 5.4 Backlog Type — 6 values, and this is the revenue-type dimension

| Value | Character |
|---|---|
| `Project` | One-time services |
| `Sherpa Fixed Fee` | Packaged fixed-fee services |
| `Support` | **Annuity / recurring** |
| `Change Order` | Expansion on existing work |
| `Licensing` | Resale |
| `True-Up (Completed Work)` | Retrospective billing |

This **settles J2**. JourneyTeam already separates revenue types, and already reports
"PS Bookings" (professional services) distinctly from Licensing. The offering's generic
`revenue_type` dimension maps directly onto `Backlog Type`.

Note `Licensing` appears as **both** a practice value and a backlog type — a modelling
wrinkle to resolve deliberately rather than inherit.

### 5.5 Relationship Type — partner-specific account classification

`Customer` · `Prospect` · `Suspect` · `ISV` · `Referral Partner`

Carried on both account and originating lead. It feeds the forecast weighting model
([§8.1](#81-the-three-factor-weighting-model)) and the goal grid, so it is a first-class
dimension, not a descriptive attribute.

### 5.6 Lead Source and Marketing Source

**Lead Source (8):** `Outbound` · `Referral` · `Inbound` · `Microsoft` ·
`Microsoft Relationship` · `Existing Client` · `Web` · `Cold Call (New Client)`

**Marketing Source (13):** adds `Microsoft Partner Center` · `Sales` · `Marketing` ·
`Webinar/Event` · `Sales Development`

**Three separate Microsoft-related sources**, plus `Microsoft MAL (Account)` and computed
`IS MAL?` flags on the pipeline. Goal reporting uses further groupings — `MSFT Rep`,
`MSFT Other`, `MSFT Rep Relationship`.

This **settles J4**: Microsoft-sourced pipeline *is* tracked in Dynamics, but across at
least five overlapping fields. It needs consolidating into one conformed
partner-sourced grouping, which is a genuine deliverable rather than a passthrough.

### 5.7 Activity taxonomy

**Activity Type (11):** `Email` · `Phone Call` · `Task` · `Appointment` ·
`Outbound message` · `Discovery Session` · `Reference Activity` · `Opportunity Close` ·
`Quote Close` · `Case Resolution` · `ERP Integration Failure`

**Activity Target (3):** `Lead` · `Contact` · `Customer`

The last four activity types are **system-generated, not sales touches**.
`ERP Integration Failure` in particular is an integration error record sitting in the
activity stream. Any "activities per opportunity" or "days since last activity" metric
that does not exclude system-generated types is inflated — and the offering's draft
metrics currently do not exclude them.

### 5.8 Close Probability — only three values

`50%` · `75%` · `95%`

This **settles D2**: close probability is maintained, so Weighted Pipeline Value is
viable. But note two things:

- It is a **three-band judgment**, not a continuous estimate.
- **There is no band below 50%.** Every open opportunity, including one at stage 1, counts
  at least half its value. Straight `value × probability` therefore overstates early
  pipeline — which is very likely why JourneyTeam built the three-factor model instead.

### 5.9 Status — 809 distinct values

The `Status` field in the pivot caches carries 809 distinct values: opportunity status
reasons, lead status reasons, disqualification reasons, and **marketing campaign strings**
(inquiry URLs, content-asset titles) all in one field.

Unusable as a dimension without grouping. Lead status needs a conformed grouping in
Silver, and the campaign strings belong in a separate attribute.

---

## 6. Metric inventory — the requirements baseline

Every metric the current report produces, by report sheet. **This is the functional
requirement set for the dashboard.**

### 6.1 Weekly scorecard (`WEEKLY REPORT_All` / `_AE` / `_SAM`)

Goal-versus-actual grid: **September Goal · September Actuals · % Reached MTD · YTD Goal ·
YTD Actuals · % Reached YTD**, for:

- Opps Created
- PS Bookings (total)
- PS Bookings per practice — CXC, DAI, ERP, SEC

Plus:

| Metric | Note |
|---|---|
| Last week Booked | Weekly rhythm |
| MTD Booked | |
| MTD Opps Created | |
| MTD Pipeline Created | Value, not count |
| MTD Leads Created | |
| Open Leads | |
| Open Leads in Sequence | SDR motion |
| **Current 30 / 60 / 90 day pipeline total** | **Rolling windows, not fiscal periods** |
| Current Month Practice Forecast | Per practice |
| **% of Month Elapsed** | Pacing denominator |
| Current Month Mega Deals | Listed individually |

The rolling 30/60/90-day pipeline windows are the primary pipeline view and are **not
how the drafted Sales pack presents pipeline** — that uses fiscal periods. This needs
adding.

### 6.2 Forecast model

```
Practice forecast = MTD Booked + Commit + Strong Upside
```

with variants exposed separately:

- `Commit + Strong Upside + MTD`
- `Commit + Strong Upside + Upside + MTD`

**Forecast categories:** `Commit` · `Strong Upside` · `Upside`

These are a **manual judgment overlay**, distinct from close probability. Mega deals carry
a separate `Manual Prob` and `Forecast Contribution`, and are **excluded** from the
practice forecast roll-up ("less values from Mega deals").

`VERIFY` where forecast category is stored in Dataverse. It may be a custom column, or it
may exist only in the spreadsheet — in which case it is a **gap that must be closed in
Dynamics before the dashboard can reproduce the forecast**, not something the BI layer can
invent.

### 6.3 Leaderboard

Ranked, separately for AE and SAM, with Jan–Dec columns plus YTD:

- MTD Opportunity Creation
- YTD Opportunity Creation
- MTD PS Bookings
- YTD PS Bookings
- Opps Won

### 6.4 Pipeline deep dive

Opportunity-level listing: Owner · Account · Topic · Practice · Est. close date ·
**Pre-sales Resource** · Sales Stage · Close Probability · Est. revenue · **Deal Age
(Days)** · **Days since last mod** · Weighted total

Header KPIs: Unweighted Pipeline · **Weighted Pipeline** · Average Deal Age · Average
Deal Size

`Pre-sales Resource` is notable — pipeline is analysed by which pre-sales engineer is
attached, which is a capacity-planning question, not just a sales one.

### 6.5 Practice deep dive (per practice)

Monthly Budget · Opps Created · Opps Won · Projection · Commit · Strong Upside ·
Bookings YTD vs Budget · Current Month Projection · Monthly Actuals by Lead Source ·
30 Day Pipeline · Current Open Leads · Leads Created · Commit deal list · Upside deal list

### 6.6 Win rates and deal size

Three distinct win-rate methodologies, all in use:

| Methodology | Definition |
|---|---|
| **60-day cohort win rate by month** | Of opportunities created in month *M*, the share won within 60 days — with `Cohort Matured?` flags so immature cohorts are excluded |
| **Rolling 12-month win rate** | By rep, by team, by practice, by backlog type |
| **Win rate by value** | Value-weighted rather than count |

Cohort columns on `Opp Input`: `Age Bucket` · `Aging Cohort` · `60 Day Window End` ·
`30 Day Window End` · `Resolved in 60 days?` · `Resolved in 30 days?` ·
`Won within 60 days?` · `Won within 30 days?` · `60 Day Cohort Matured?` ·
`30 Day Cohort Matured?`

**Cohort win rate with maturation gating is more sophisticated than the drafted
`Win Rate` metric** and is the methodology JourneyTeam actually manages by. It must be
added.

**Average deal size carries explicit outlier rules** — multiple variants are published
side by side: `Exclude $0, $1`, `Exclude $0 deals and >$800k`, `Exclude $0`. These are
deliberate business rules, not data cleanup.

### 6.7 SDR deep dive

Contacts Outreached · Leads Created (Inbound / Outbound split) · Opps Created
(Inbound / Outbound) · YTD Bookings · 30 Day Pipeline · Outreach Activity by Month
(Contacts / Email / Phone / Other) · MTD Sequence Initiations · Open Leads Assigned

### 6.8 Daily activity

Lead Creation by Rep by Day · Email Activity · **Email as % of activity** · Count of
deals booked · Value of deals booked · Activity by target type (Lead / Contact / Customer)

### 6.9 Attainment and budget

- **Rep attainment:** Rep · Sales · Quota · Attainment, monthly, rolled to Team AE /
  Team SAM
- **Budget attainment per practice:** Actuals · Gap to Budget · Pipeline · Budget
- **Quarterly targets to actuals:** at **Lead Source × Relationship** grain, with monthly
  target/actual, MTD % to target, quarter target, QTD actuals
- `Non-Quota Retiring Sales` as an explicit category

### 6.10 Lead source performance

YTD qualification rate by lead source (Inbound / Microsoft / Outbound / Referral) —
qualified count against total.

---

## 7. The goal model

`Rep Goal Reference` (138 rows) sets goals at **rep × quarter × lead source** grain, and
covers more than bookings:

| Goal | |
|---|---|
| Leads | Volume |
| Opps | Volume |
| **Lead/Opp Conversion** | Funnel rate target |
| Won | Volume |
| **Opp/Won Conversion** | Funnel rate target |
| **Lead/Won Conversion** | End-to-end rate target |
| Bookings | Value |

**Funnel conversion rates are targeted, not just outcomes.** Lead source groupings used
for goals — `SQL`, `MQL`, `MSFT Rep`, `MSFT Other`, `Referral`, `Change Order`,
`SBR`/`QBR`, `Renewal`, `SDR Outreach`, `Sales Development – Prospects`,
`Sales Development – Customers`, `Other` — do not match the raw `Lead Source` values, and
the spreadsheet contains mapping expressions (including `<>` exclusions) to reconcile them.

This **settles D3 / Pipeline Coverage**: targets exist and are rich, but they live **in a
spreadsheet, not in Dataverse**. They must be ingested as a source. That is a defined
piece of work, and Pipeline Coverage and every attainment metric depend on it.

---

## 8. Business rules that must be replicated

The workbook's real value. These cannot be inferred from Dataverse.

### 8.1 The three-factor weighting model

`Forecast inputs` holds three weight tables:

| Weight table | Keyed on |
|---|---|
| Stage Weight | Sales Stage (1–5) |
| Relationship Weight | Relationship Type (Customer / Prospect / Suspect / ISV / Referral Partner) |
| Backlog Weight | Backlog Type (Change Order / Support / True-Up) |

```
Weighted total = Est. revenue × Stage Weight × Relationship Weight × Backlog Weight
```

**The drafted `Weighted Pipeline Value` metric — `estimatedvalue × closeprobability / 100`
— is not what JourneyTeam uses and would produce a different number.** The metric
definition must be replaced with this model, and the three weight tables ingested as
configuration.

This is also a genuinely good model worth carrying into the product: it accounts for the
fact that a support change order for an existing customer converts very differently from a
net-new project with a suspect.

### 8.2 Quota retirement rules — the most complex logic in the workbook

Attainment is **not** bookings. The workbook documents:

- A **per-rep cap on licensing quota retirement**, with the excess above the cap deducted
  from attainment and spread into subsequent months
- `Non-Quota Retiring Sales` as a category of bookings that do not count toward quota
- **Support contracts** receiving special quota treatment, enumerated by owner and amount
- Distinct concepts: total deal value · amount allowed for quota retirement · amount to
  reduce for quota attainment · amount eligible for quota attainment

Today this is handled by **hand-written notes and manual adjustments in the spreadsheet.**

**This is a scope decision, not a design detail.** Either the rules are captured as
configuration and implemented, or attainment stays a manual process and the dashboard
reports bookings rather than quota attainment. Implementing it properly needs the rules
written down as policy first — they currently exist as precedent. Recommend treating it as
**out of scope for Release 1** and flagging it explicitly, because underestimating it will
hurt.

### 8.3 Mega deals

Large opportunities are handled separately: listed individually on the weekly report,
carrying a `Manual Prob` override and a `Forecast Contribution`, flagged by
`Is Mega Deal?`, and **excluded from practice forecast roll-ups** and from average deal
size (the `>$800k` exclusion).

`VERIFY` the mega-deal threshold and whether `Is Mega Deal?` is a Dynamics column or a
spreadsheet calculation.

### 8.4 Cohort maturation gating

Cohort win rates only count cohorts whose window has fully elapsed
(`60 Day Cohort Matured?`). Without this gate, recent months show artificially low win
rates because their deals have not had time to close — a trap worth reproducing correctly.

### 8.5 Outlier exclusions on averages

`Exclude $0`, `Exclude $0, $1`, `Exclude $0 deals and >$800k`. $0 and $1 opportunities are
placeholders; mega deals distort averages. Published as parallel variants so the reader
can see both.

### 8.6 Practice mapping

`InterestMap` (15 rows) maps lead/opportunity interest values to practices:

| Interest | Practice |
|---|---|
| ACM · CCaaS · Copilot · CRM · Power Platform | CXC |
| Azure · Data | DAI |
| BC · FSC | ERP |
| MWS · Security | SEC |
| CSP Licensing · License | Licensing |
| Advisory · Support | *unmapped* |

Two observations: `Advisory` and `Support` are **unmapped**, so those interests fall out of
practice reporting; and one target value carries a **trailing space** (`"Licensing "`),
which would create a duplicate dimension member.

This table plus a mapping for the 17 legacy `Primary Product (New)` values
([§5.2](#52-practice--primary-product-new-22-values-5-current)) becomes the conformed
**practice dimension**.

### 8.7 Multi-practice deals

`Bookings Input` carries **`Interests (Add'l Practices)`** — additional practices beyond
the primary, as a multi-value field, with a LAMBDA in the workbook to parse it.

**This settles J1, and the answer is the complicated one: practice is both.** There is a
single `Primary Product (New)` on the header **and** a multi-valued additional-practices
field. Consequences:

- Practice attribution is genuinely many-to-many with opportunity → needs a **bridge
  table**, not a foreign key.
- Header-level practice reporting (which is what the current report does) **under-counts
  multi-practice deals** for secondary practices.
- If the Dataverse field is a multi-select choice, it stores a delimited list of integers
  and needs parsing plus label resolution — a conformance-layer job.
- The drafted decision **D8** (opportunity products optional) is not the right frame:
  practice does not come from opportunity product lines here, it comes from these two
  fields. **D8 can stay "optional"; a new decision on the practice bridge replaces it.**

---

## 9. What this settles

| ID | Question | Answer from the workbook |
|---|---|---|
| **J1** | Where does practice live; header or line? | **Both.** `Primary Product (New)` header + `Interests (Add'l Practices)` multi-value. Needs a bridge |
| **J2** | Revenue type mix | **Confirmed.** `Backlog Type`, 6 values. PS vs Licensing already separated |
| **J4** | Microsoft-sourced pipeline tracked? | **Yes**, across 5+ overlapping fields. Needs consolidating |
| **D1** | Is Cancelled a form of Lost? | `Canceled` present in status values; win-rate pivots show Lost/Open/Won only → **treated as neither**. Confirm |
| **D2** | Is close probability maintained? | **Yes**, but three bands with no sub-50% floor |
| **D3** | Do targets exist? | **Yes**, rich — rep × quarter × lead source, including conversion rates. **In a spreadsheet, not Dataverse** |
| **D4** | Stage from `salesstagecode` or BPF? | `Sales Stage` used directly with 5 clean numbered values → **not BPF-driven**. Confirm against the Dataverse column |
| **D5** | Loss reason populated? | Status values include Budget, Competitor, Not a Fit, Unresponsive, No Longer Interested → **yes, and usable** |
| **D8** | Are opportunity products used? | Not for practice. **Superseded** by the practice bridge question |

**Still open: J3 (TCV vs ACV).** `Support` and `Sherpa Fixed Fee` backlog types are
annuity-shaped, but nothing in the workbook indicates whether `Est. Revenue` on those is
total contract value or annualised. **This remains the most important unanswered question**
and must go to sales leadership.

---

## 10. Requirements not in the drafted Sales pack

Gaps to close in [`packs/sales/metrics.yaml`](../../packs/sales/metrics.yaml) and the
[technical design](../../packs/sales/technical-design.md).

| # | Requirement | Impact |
|---|---|---|
| 1 | **Three-factor weighting** replacing `value × probability` | Replaces a drafted metric definition |
| 2 | **Rolling 30/60/90-day pipeline windows** | New; this is the primary pipeline view |
| 3 | **Cohort win rate with maturation gating** | New methodology alongside the drafted win rate |
| 4 | **Forecast categories** (Commit / Strong Upside / Upside) | New dimension; may not exist in Dataverse |
| 5 | **Practice bridge** for multi-practice deals | New conformed dimension, many-to-many |
| 6 | **Practice mapping** for 17 legacy values + InterestMap | Conformance-layer requirement |
| 7 | **Revenue type** (`Backlog Type`) as a dimension | Confirms the planned J2 work |
| 8 | **Relationship Type** as a dimension | New; feeds weighting and goals |
| 9 | **Goal ingestion** at rep × quarter × lead source, incl. conversion targets | New source; unblocks attainment and coverage |
| 10 | **Team (AE/SAM/SDR) as a reporting segment** | Drives separate report pages, not just a slicer |
| 11 | **Pre-sales Resource** as a dimension | New; capacity-planning angle |
| 12 | **Mega deal handling** — flag, manual override, roll-up exclusion | New business rule |
| 13 | **Outlier exclusion variants** on averages | New business rule |
| 14 | **System activity-type exclusion** | Corrects drafted activity metrics |
| 15 | **Lead + sequence facts** (SDR motion) | Sequence data is beyond the drafted lead fact |
| 16 | **`% of Month Elapsed`** pacing measure | Small but used everywhere |
| 17 | **Consolidated Microsoft-sourced grouping** | New conformed grouping |
| 18 | **Quota retirement rules** | **Recommend out of scope for Release 1** — see §8.2 |

Items 1, 2, 3, and 5 change existing metric definitions. Items 9 and 18 are new sources
and new scope. **Nothing here invalidates the architecture; all of it lands in the Silver
conformance layer and the metric definitions**, which is the design working as intended.

---

## 11. Data quality findings

| # | Finding | Consequence |
|---|---|---|
| 1 | Practice field has 22 values, 17 legacy, 5 `zz_`-prefixed | Multi-year practice trends break without mapping |
| 2 | `Status` has 809 distinct values including campaign URLs | Unusable as a dimension without grouping |
| 3 | `InterestMap` target `"Licensing "` has a trailing space | Duplicate dimension member |
| 4 | `Advisory` and `Support` interests unmapped | Those deals drop out of practice reporting |
| 5 | System activity types in the activity stream | Inflates activity metrics |
| 6 | `Licensing` is both a practice and a backlog type | Ambiguous attribution |
| 7 | Close probability has no band below 50% | Weighted pipeline overstates early stages |
| 8 | Broken `BoM` / `booked` defined names | Snapshot comparison already failing silently |
| 9 | `$0` and `$1` placeholder opportunities | Already worked around by exclusion rules |

Every one of these is a conformance-layer item. Notebook 50's fill-rate and quality
reporting should check for each.

---

## 12. Dashboard design implications

The user's framing — *"the analytics dashboard will be similar to this"* — is the right
instinct. People trust a replacement that matches what they already read. Proposed mapping
onto the drafted 8-page report pack:

| Current sheet | Power BI page | Change |
|---|---|---|
| `WEEKLY REPORT_All` / `_AE` / `_SAM` | **Weekly Scorecard** | One page, Team slicer replaces three sheets |
| `Leaderboard` | **Leaderboard** | Keep AE/SAM separation |
| `PIPELINE DEEP DIVE` | Pipeline Overview | Close to the drafted page |
| `PRACTICE DEEP DIVE` | **Practice Performance** | **New page**; practice is the primary dimension |
| `REP DEEP DIVE` | Performance | Drill-through by rep |
| `SDR DEEP DIVE` | **SDR & Sequences** | **New page** |
| `DAILY ACTIVITY` | Activity | |
| `Win rates & Deal Size` | Win/Loss | Add cohort methodology |
| `Budget Attainment` / `Attainment` | **Attainment** | **New page**; needs goal ingestion |
| `Lead Source Performance` / `LEAD Summary` | Leads | |
| `BOOKINGS` / `OPPORTUNITIES` | Paginated detail | Export-oriented |
| — | **Pipeline History** | **The new capability.** Replaces the broken `BoM` mechanism |

That is **11 pages, not 8.** Practice Performance, Attainment, and SDR are not in the
drafted pack and are central to how JourneyTeam runs. Release 1's thin slice should be
**Weekly Scorecard + Pipeline History**, because the scorecard is what leadership reads
weekly and Pipeline History is the capability Excel never had.

### Two things the dashboard should do that the workbook cannot

1. **Pipeline History** — the `BoM` references prove they wanted month-start snapshots and
   could not sustain them manually. This is the differentiator landing on a demonstrated
   need, in JourneyTeam's own operations.
2. **Kill the reconciliation step.** "Ensure top level figures match" disappears when the
   data is not hand-copied. Worth stating as a success criterion.

---

## 13. What not to carry forward

Not everything in the workbook should be reproduced.

- **The three near-duplicate weekly report sheets** — one page with a Team slicer.
- **Hidden helper pivots** (`Pipe pivot`, `Activity pivot`, `Open Leads in Sequence`) —
  these are Excel plumbing, replaced by the model.
- **Manual month-by-month sheets** (`Q2 Targets to Actuals`) — a date dimension handles
  this; do not build per-quarter pages.
- **The 809-value `Status` field as a slicer** — group it.
- **Manual quota adjustment notes** — either formalise the rules (§8.2) or leave
  attainment out and say so.
- **Trailing-space and `zz_` values** — fix in conformance, do not surface.

---

## 14. Handling of the source file

The workbook contains, for roughly 872 opportunities, 460 bookings, 7,150 leads and 36,500
activities:

- Real customer and account names, deal topics, and revenue values
- Named employees with individual quota, attainment, and ranked performance
- At least one hand-written note naming an individual, their deal, and their quota cap
- Practice-level budgets and gap-to-budget

That is **confidential business information plus personal performance data about named
employees.**

**The binary has therefore not been committed to this repository.** Git history is
permanent and this repository is pushed to GitHub, so a commit cannot be cleanly undone
later; the repository is also the offering IP repo, read by more people than should see
rep-level performance data; and `CLAUDE.md` prohibits committing customer data.

What the repository needs from the workbook is its **design intelligence**, which is what
this document captures — with no names, no customers, and no figures.

**The source workbook should live in a controlled location** (the sales operations
SharePoint or Teams site, under its existing access controls) and be referenced from here
by filename and date, as in [§1](#1-source-artifact).

If a copy must be retained alongside this analysis, the right form is a **structurally
redacted workbook** — sheet layout, field names, taxonomies, and the three weight tables
retained; all input tabs emptied. That is committable and preserves everything the build
needs.
