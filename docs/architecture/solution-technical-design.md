# End-to-end solution — technical design document

**Scope:** the whole Fabric solution, from Dataverse to the answer a user gets — ingestion,
transformation, semantic model, Power BI, and the Data Agent.

**Audience:** the data engineer and BI developer building it, the reviewer approving it,
and the offering owner deciding what is in the package.

**Status:** design draft. **Nothing in this document has been built or validated against a
live Dataverse environment or a live Fabric capacity.** Items marked `VERIFY` are
explicitly unconfirmed. Items marked **DECISION Sn** need an answer before the work they
gate starts.

**What this document is.** The spine: the five components, the contract between each pair,
and the cross-cutting concerns that belong to no single component — identity,
orchestration, ALM, monitoring, cost, and acceptance.

**What it deliberately does not restate.** Sales-specific design — the star schema, the
measures, the report pages, RLS role DAX — lives in
[`../../packs/sales/technical-design.md`](../../packs/sales/technical-design.md). Metric
semantics live in [`../../packs/sales/metrics.yaml`](../../packs/sales/metrics.yaml).
Prices live in [`../offering/pricing-and-packaging.md`](../offering/pricing-and-packaging.md).
Each is referenced, never duplicated: a number that exists in two places will eventually
disagree.

| Section | |
|---|---|
| 1 | [Scope, context and assumptions](#1-scope-context-and-assumptions) |
| 2 | [End-to-end architecture](#2-end-to-end-architecture) |
| 3 | [Layer contracts](#3-layer-contracts) |
| 4 | [Component 1 — Ingestion](#4-component-1--ingestion) |
| 5 | [Component 2 — Transformation (medallion)](#5-component-2--transformation-medallion) |
| 6 | [Component 3 — Semantic model](#6-component-3--semantic-model) |
| 7 | [Component 4 — Power BI](#7-component-4--power-bi) |
| 8 | [Component 5 — Data Agent](#8-component-5--data-agent) |
| 9 | [Identity and security end to end](#9-identity-and-security-end-to-end) |
| 10 | [Orchestration](#10-orchestration) |
| 11 | [Environments and ALM](#11-environments-and-alm) |
| 12 | [Monitoring and operations](#12-monitoring-and-operations) |
| 13 | [Capacity, sizing and cost drivers](#13-capacity-sizing-and-cost-drivers) |
| 14 | [Testing and acceptance](#14-testing-and-acceptance) |
| 15 | [Open decisions](#15-open-decisions) |
| 16 | [Build sequence](#16-build-sequence) |

---

## 1. Scope, context and assumptions

### In scope

- Dataverse → OneLake ingestion via **Link to Microsoft Fabric**
- Bronze / Silver / Gold transformation, including the conformance layer and snapshot history
- One Power BI semantic model over Gold
- The Sales report pack and self-service access (SQL endpoint, Analyze in Excel)
- **A Fabric Data Agent** over the certified model, for natural-language questions
- Orchestration, monitoring, security, and the promotion path between environments

### Out of scope

- Any Dynamics 365 app other than Sales — see
  [`../offering/roadmap.md`](../offering/roadmap.md)
- Non-Dataverse sources (on-prem, file, streaming). They land in OneLake through normal
  Fabric mechanisms and are additional development
- Write-back of any kind. **The solution is read-only with respect to Dataverse.** Nothing
  in this design writes to, or triggers action in, the source system
- Dataverse security parity in Power BI — see
  [`security-and-rls.md`](security-and-rls.md)
- Custom Dataverse tables and columns beyond the agreed set

### Assumptions

| # | Assumption | If wrong |
|---|---|---|
| A1 | Fabric capacity and the Dataverse environment are in compatible regions | Link to Fabric may not be configurable at all. Pre-sales qualification item, not a Sprint 1 discovery |
| A2 | A paid Fabric SKU is available for production | A trial can start a build but cannot carry a delivery |
| A3 | The tables in `platform/config/` are eligible for the link and have change tracking | Bronze is incomplete and every downstream mapping fails at the validation gate |
| A4 | Choice-label metadata is obtainable — either as `OptionsetMetadata` tables in the link or via the Dataverse Web API | **The single most important unresolved item in the platform.** Reports show integers. See the VERIFY block in [`../../platform/notebooks/20_silver_conformance_choice_labels.py`](../../platform/notebooks/20_silver_conformance_choice_labels.py) |
| A5 | Snapshots begin on day one of the engagement | History is not backfillable from a current-state source. A day not captured is gone |
| A6 | The querying user's identity flows to the Data Agent, and the semantic model's RLS applies to it | The agent becomes an RLS bypass. See §8.7 — this is the decision that gates whether the agent ships at all |

---

## 2. End-to-end architecture

```
┌── DATAVERSE ────────────────────────────────────────────────────────────────┐
│  Dynamics 365 Sales — current state only, no history                       │
└───────────────────────────────┬────────────────────────────────────────────┘
                                │  Link to Microsoft Fabric
                                │  first-party · zero-copy · near-real-time
                                ▼
┌── 1  BRONZE — the shortcut ─────────────────────────────────────────────────┐
│  Dataverse logical names, unchanged. READ-ONLY, Microsoft-managed.         │
│  Gate: 10_bronze_shortcut_validation — nothing runs if this fails          │
└───────────────────────────────┬────────────────────────────────────────────┘
                                ▼
┌── 2  SILVER — conformance + history ────────────────────────────────────────┐
│  20 choice labels   21 currency   22 ownership (SCD2)                      │
│  23 activity bridge 24 date/fiscal                                         │
│  50 sales dimensions + facts    51 derived history                         │
│  ─────────────────────────────────────────────────────────────────────────  │
│  30 snapshot facts  ← SEPARATE PIPELINE, fixed UTC time, append-only       │
└───────────────────────────────┬────────────────────────────────────────────┘
                                ▼
┌──    GOLD — business-ready ─────────────────────────────────────────────────┐
│  40 conformed dimension views    52 sales__ star schemas                   │
│  Every derived value materialised here. No calculated columns downstream.  │
└───────────────────────────────┬────────────────────────────────────────────┘
                                ▼
┌── 3  SEMANTIC MODEL — "JTA Sales" ──────────────────────────────────────────┐
│  Direct Lake (D7) · conformed dimensions · RLS · certified                 │
│  Measures implement metrics.yaml. THE definition of every number.          │
└──────────┬─────────────────────────┬──────────────────────┬────────────────┘
           ▼                         ▼                      ▼
┌── 4  POWER BI ────────┐  ┌── SELF-SERVICE ─────┐  ┌── 5  DATA AGENT ──────┐
│  8 report pages       │  │  Analyze in Excel   │  │  NL → DAX over the    │
│  + paginated detail   │  │  SQL endpoint       │  │  certified model      │
│  Power BI app         │  │  ⚠ bypasses RLS     │  │  Copilot / Teams      │
│  Embedded in D365     │  │                     │  │  ⚠ RLS gates release  │
└───────────────────────┘  └─────────────────────┘  └───────────────────────┘
```

**The sales narrative has four numbered components; this design has five.** The Data Agent
is new and is not in
[`reference-architecture.md`](reference-architecture.md#the-four-numbered-components-sales-narrative)
or the deck outline. Whether it becomes component 5 of the offering — and what that does to
the price — is **DECISION S6**, and it is the offering owner's, not this document's.

### Fabric artifact inventory

Per the reference topology. The deployed JT topology differs — see §5 and **DECISION S1**.

| # | Artifact | Type | Layer | Notes |
|---|---|---|---|---|
| 1 | `JTA-<Customer>-Platform` | Workspace | 1–2 | Engineering. Report consumers never enter it |
| 2 | `JTA-<Customer>-Reporting` | Workspace | 3–5 | Models, reports, app, agent |
| 3 | `jta_lakehouse` | Lakehouse | 1–2 | `bronze` / `silver` / `gold` schemas |
| 4 | Dataverse link shortcut | Shortcut | 1 | Created by Link to Fabric, not by us |
| 5 | `10` … `52` | Notebooks | 1–2 | Plain `.py` authoring drafts in [`../../platform/notebooks/`](../../platform/notebooks/) |
| 6 | `JTA Daily Build` | Pipeline | 2 | Validation → conformance → Gold → pack |
| 7 | `JTA Daily Snapshot` | Pipeline | 2 | Separate failure domain. See §10 |
| 8 | `JTA Sales` | Semantic model | 3 | Direct Lake, certified |
| 9 | `JTA Sales — Reports` | Report set | 4 | PBIP/TMDL in source control, not `.pbix` |
| 10 | `JTA Sales — Opportunity Detail` | Paginated report | 4 | `VERIFY` licensing against the customer's SKU |
| 11 | `JourneyTeam Analytics — Sales` | Power BI app | 4 | The distribution boundary |
| 12 | `JTA Sales Agent` | Data Agent | 5 | Grounded on artifact 8. See §8 |
| 13 | SQL analytics endpoint | Endpoint | 2 | **Bypasses model RLS.** Audience is a named decision |

---

## 3. Layer contracts

The part of an end-to-end design that is usually missing, and the reason integration
defects appear late. Each layer **guarantees** something to the next and **forbids** itself
something. A defect is then attributable: whichever contract was broken owns it.

| Boundary | The layer above guarantees | It is forbidden from | Enforced by |
|---|---|---|---|
| Dataverse → **Bronze** | Tables in the configured set exist, carry expected columns, and have rows | Nothing — we do not control it | `10_bronze_shortcut_validation`, which **gates the whole run** |
| Bronze → **Silver** | Raw Dataverse semantics, unaltered | Any write, any in-place transform, any "cleaned copy" beside the raw tables | Code review; Bronze treated as read-only territory |
| Silver → **Gold** | Choice integers resolved to labels; money exposed as `_txn` and `_base` with no silent conversion; `IsDelete` filtered; UTC handled per column; SCD2 versions intact | Exposing a raw choice integer; inventing a value to fill a NULL | `50`, plus the data quality checks in the pack TDD §13.2 |
| Gold → **Semantic model** | A star schema with every derived value already materialised — flags, buckets, weighted values, cycle days | A calculated column or calculated table downstream | Direct Lake, which **cannot** create them (D7). The constraint is desirable |
| Semantic model → **Power BI / Agent** | One certified definition per metric, implementing `metrics.yaml`; RLS applied; non-additive columns hidden | Two measures that answer the same question differently | Model hygiene (pack TDD §7.3); `metrics.yaml` is the source of truth |
| Semantic model → **Data Agent** | Only measures are summable; every exposed field carries a description; synonyms resolve business vocabulary | Letting the agent aggregate raw columns | §8.3 and §8.5 |

**The contract that carries the most weight is Gold → model.** "Every derived value is
materialised in Gold" is what lets three different consumers — reports, Excel, and an
agent — get the same number. Break it once with a convenient calculated column and the
agent and the report begin to disagree, with no error anywhere.

---

## 4. Component 1 — Ingestion

Design detail: [`ingestion-link-to-fabric.md`](ingestion-link-to-fabric.md). Only the
solution-level design is here.

### 4.1 Mechanism

**Link to Microsoft Fabric**, configured from the Power Apps maker portal against a Fabric
workspace. First-party, zero-copy, near-real-time. There is no pipeline to build and no
ETL to maintain.

**Consequence for this document:** ingestion is a *configuration step with a validation
gate*, not a build. The engineering effort is in confirming what actually arrived, which is
§4.3.

### 4.2 Table set

Driven by configuration, not chosen during delivery:
[`../../platform/config/customer.example.yaml`](../../platform/config/customer.example.yaml)
→ `tables.required`, `tables.optional`, `tables.columns`, `tables.choice_columns`.

Two categories, and they fail differently:

- **Conformance layer tables** — `businessunit`, `systemuser`, `team`,
  `transactioncurrency`, `activitypointer`, `account`, `contact`. Missing one breaks the
  platform for every pack.
- **Sales pack tables** — `lead`, `opportunity`, `opportunityproduct`, `quote`,
  `salesorder`, and the detail tables. Missing one breaks a page.

`opportunityproduct` is **mandatory, not optional**: `estimatedvalue` is
system-calculated from the lines, so the lines are the revenue source. Pack TDD decision D8.

### 4.3 The validation gate

`10_bronze_shortcut_validation` runs first in every pipeline and **stops the run on
failure**. It confirms tables are present, have rows, and carry the columns the mappings
assume.

This is the highest-value check in the solution, because Dataverse schema varies by
solution version and by customization, and **column drift produces wrong numbers rather
than errors**. A mapping error caught here is cheap; the same error caught in UAT is
expensive and damages trust for the rest of the engagement.

Evidence that the gate is not theoretical:
[`../bronze-profiling/opportunity.md`](../bronze-profiling/opportunity.md) profiles a real
`opportunity` export at **343 columns**, with ten findings that changed the design —
including that the analytically important columns are all custom, and that stage history
does not exist because `traversedpath` / `stageid` / `processid` are NULL.

### 4.4 Failure modes and who owns them

| Failure | Owner | Response |
|---|---|---|
| Region mismatch blocks the link | Pre-sales | Qualify before quoting (A1) |
| A required table is not eligible or lacks change tracking | Customer IT | Blocks the run at the gate |
| A column in `tables.columns` is absent | Us | Correct the mapping; do not work around it in Gold |
| Choice metadata absent | Us | Fall back to the Dataverse Web API (A4) |
| Bronze is shared infrastructure and adding a table is a change request | Customer / JT change control | Never alter a shared link inside a build. See §5 |

### 4.5 Bronze rules

1. **Never write to Bronze.** No transforms in place, no added columns, no cleaned copy
   beside the raw tables.
2. **Assume the shortcut can be recreated.** All logic must be reproducible from Bronze by
   re-running notebooks, so dropping and recreating the link loses nothing but time.
3. **Validate, do not trust.**
4. **Filter `IsDelete` on every Bronze read.** Confirmed platform pattern; omitting it
   counts soft-deleted records.

---

## 5. Component 2 — Transformation (medallion)

Design detail: [`medallion-design.md`](medallion-design.md),
[`conformance-layer.md`](conformance-layer.md),
[`snapshot-and-history.md`](snapshot-and-history.md). Sales specifics: pack TDD §3–§6.

### 5.1 Why this layer is the product

Ingestion is first-party and free, so it cannot be the differentiator. The defensible value
is here: the **conformance layer** that makes Dataverse usable for BI, and **snapshot
history** that a current-state source cannot provide. Everything in this section exists to
protect those two.

### 5.2 Silver — conformance

Seven problems solved once, as versioned notebooks rather than per-customer fixes:

| # | Problem | Notebook | Output |
|---|---|---|---|
| 1 | Choices are raw integers | `20` | `lkp_choice_label`, keyed `(table, column, value)` |
| 2 | Money is ambiguous | `21` | `dim_currency`; `_txn` / `_base` on every money column |
| 3 | Ownership is a hierarchy in three tables | `22` | `dim_owner` — **SCD2**, users *and* teams, BU path and manager chain flattened |
| 4 | Activities are polymorphic | `23` | `bridge_activity` — typed nullable key per target |
| 5 | `statecode` vs `statuscode` | `20`, `50` | Conformed status grouping per table |
| 6 | No fiscal calendar | `24` | `dim_date`. **Holiday calendar still missing** — business-hours metrics are calendar-hours and must say so |
| 7 | Current state only | `30` | Snapshot facts |

Two rules that are not negotiable:

- **Never hard-code a `CASE` for choice labels.** A hard-coded mapping is invisible when
  the customer adds a status reason, which is precisely when it starts being wrong.
- **Choice joins are left joins.** An unmapped value must surface as NULL and be
  investigated, not silently drop the fact row.

### 5.3 Silver — history

**Snapshots start on day one of the engagement, not at go-live.** History cannot be
backfilled from a current-state source, so every day of delay is a day permanently lost.
This is the single most important sentence said on the kickoff call, and it is a Sprint 1
exit criterion for that reason.

`fact_opportunity_snapshot` is an append-only daily write at a fixed UTC time. Derived
history — `fact_stage_duration`, `fact_forecast_movement` — is computed from it, which is
the only available route: at JourneyTeam, BPF stage history does not exist in Dataverse at
all.

### 5.4 Gold

Conformed dimensions are published as **views over Silver, not copies** — enforced in code
in `40_gold_conformed_dimensions`, not left to discipline. Pack facts are prefixed
`sales__`, and the prefix is kept with one pack so a second lands without renaming
anything.

Gold materialises every derived value, because the Direct Lake contract in §3 forbids
calculated columns downstream.

### 5.5 Topology — **DECISION S1**

The reference design is **one lakehouse, three schemas, one platform workspace**. The
deployed JourneyTeam topology is **three lakehouses across two workspaces**, with Bronze
being the shared *production* Dynamics Link — see
[`jt-medallion-topology.md`](jt-medallion-topology.md).

Both are legitimate. The deployed shape is arguably better where Bronze is shared
infrastructure serving several practices; the per-customer shape is almost certainly right
for a customer delivery, where a customer has no reason to share Bronze with anyone.

**Two consequences to resolve before the first build, not after:**

1. **An ADR is owed.** A reference architecture that describes a single lakehouse while
   every build uses something else becomes fiction.
2. **`LAKEHOUSE = "jta_lakehouse"` is hard-coded** in
   [`../../platform/notebooks/_common.py`](../../platform/notebooks/_common.py) and must
   become per-layer configuration. This is a real code change and the right one regardless:
   a single hard-coded name was always going to break on the first customer whose naming
   convention differed.

**Where Bronze is shared and production-owned, it is not this build's to change.** Adding a
table to the link affects other consumers and is a change-controlled action on a production
asset.

---

## 6. Component 3 — Semantic model

Design detail: pack TDD §7–§8. Solution-level design only here.

### 6.1 One model, and why not several

**One model, `JTA Sales`, in the reporting workspace.** It is the definition of every number
the solution produces — reports, Excel, and the Data Agent all read it.

That single model is what makes §3's contract hold. Three consumers reading three different
models is three answers to the same question, and the offering's promise is reconciled
numbers.

When a second pack arrives, the decision to face is one model per pack sharing conformed
dimensions versus one model spanning both. Not this document's to answer, but the
conformed-dimension discipline in §5.4 is what keeps the option open.

### 6.2 Storage mode — Direct Lake (pack TDD **D7**)

Recommended, with an Import fallback decided by a first-build spike. Direct Lake matches
the Fabric narrative, removes the refresh failure mode, and suits an append-only snapshot
fact.

**Its main limitation is a feature here:** no calculated columns means every derived value
must exist in Gold, which is already the architecture's rule. Direct Lake enforces it.

`VERIFY` current Direct Lake capabilities and limits — particularly RLS behavior, fallback
triggers, and relationship constraints — against current Microsoft documentation. Direct
Lake has changed materially over time; **run the spike in Sprint 1 with realistic snapshot
volume and RLS applied before building reports on it.**

### 6.3 Model obligations to the layers above

Three things the model owes its consumers, and the third is new with the Data Agent:

1. **Every measure implements `metrics.yaml`.** If the model and the YAML disagree, the
   YAML is right and the model is a bug.
2. **RLS is applied and tested fail-closed** with named test users.
3. **The model is self-describing.** Every visible table, column and measure carries a
   description; non-additive and key columns are hidden; business synonyms are populated.
   For a report author that is a nicety. For an agent it is the grounding — see §8.3.

### 6.4 Certification

The model is endorsed as **certified** before the app is published, and it is the only
certified Sales model in the tenant. An agent or a report author picking up an
uncertified copy is how a second version of the truth starts.

---

## 7. Component 4 — Power BI

Design detail: pack TDD §10.

### 7.1 Distribution

| Surface | Audience | Notes |
|---|---|---|
| **Power BI app** | All report consumers | The distribution boundary. Consumers never get workspace access |
| **Embedded in Dynamics 365** | Sellers, in-context | Where the customer wants numbers next to the record |
| **Paginated report** | Anyone needing an export | `VERIFY` licensing against the customer's SKU |
| **Analyze in Excel** | Power users | Respects model RLS |
| **SQL analytics endpoint** | Platform team only, by default | **Bypasses model RLS entirely** |

### 7.2 The SQL endpoint is a security decision, not a feature toggle

The offering sells "Query in SQL" as a capability, and a user with endpoint access reads
Gold unfiltered. It is **not** a substitute for a Power BI viewer role. Default
`sql_endpoint_audience` is `platform_team_only`, and widening it is an explicit,
recorded decision — not a convenience granted during UAT.

### 7.3 Reports

Eight pages plus paginated detail; pack TDD §10 has the page-by-page design. Three
solution-level rules:

- **Page 2, Pipeline History, is the demo.** It is the capability no first-party Dynamics
  365 analytics offers, and it is the reason the snapshot job matters.
- **Snapshot-dependent pages carry a visible note** on the snapshot start date and that
  history is not backfillable. Customers otherwise read a short trend as a defect.
- **PBIP/TMDL in source control, never `.pbix`.** Binary defeats review and versioning.

---

## 8. Component 5 — Data Agent

**New to this design.** No part of it has been built, and the Fabric Data Agent capability
itself must be re-verified before any of this is committed to: `VERIFY` its current
availability, preview or GA status, supported data sources, regional availability,
capacity/SKU requirements, and consumption surfaces against current Microsoft
documentation. **Do not restate any of those from memory into customer-facing material.**

### 8.1 What it is for, and what it is not

A Fabric Data Agent answers natural-language questions by generating queries against data
sources it has been grounded on and configured with instructions and example queries.

**The job it does here:** answer the long tail. Eight report pages cover the questions worth
a page. "How does Q3 pipeline in the Data & AI practice compare with the same point last
year, excluding the two mega-deals?" is not worth a page and is exactly what a seller asks.

**What it is not:**

- **Not a replacement for the report pack.** The reports are the reconciled, reviewed
  surface. The agent is for questions nobody anticipated.
- **Not a data-modelling shortcut.** An agent over an unconformed lakehouse produces
  fluent, confident, wrong answers. It is the *last* component built, and it depends on
  every layer above being right.
- **Not deterministic.** Two phrasings of one question can produce two answers. §8.8 is
  about bounding that, not eliminating it.

### 8.2 Grounding source — **DECISION S5**

The single most consequential choice in this component.

| | Semantic model (`JTA Sales`) | Lakehouse / SQL endpoint (Gold) |
|---|---|---|
| Generates | DAX over certified measures | SQL over tables |
| Metric fidelity | Uses the definitions from `metrics.yaml` | **Re-derives its own**, ignoring `metrics.yaml` |
| RLS | Model RLS applies `VERIFY` | **Bypasses it — §7.2** |
| Business vocabulary | Descriptions and synonyms in the model | Column names only |
| Snapshot grain | Measures encode the as-of pattern | Agent must infer it. See §8.4 |
| Flexibility | Bounded by the model | Anything in Gold |

**Recommendation: ground the agent on the semantic model, not the lakehouse.** Both reasons
are load-bearing:

1. **Security.** A lakehouse-grounded agent inherits the SQL endpoint's unfiltered read. An
   agent that will answer "what is Jane's pipeline?" to anyone who asks is not shippable
   into a sales organization, and no prompt instruction fixes it — instructions are not a
   security boundary.
2. **Metric fidelity.** `metrics.yaml` is the source of truth precisely so that "win rate"
   means one thing. An agent computing its own win rate from raw columns breaks that in the
   most damaging possible way: plausibly, and without an error.

The cost is real — the agent can only answer what the model exposes, so a question needing
a column that is not in the model fails. That is the correct failure. Widening the model is
a reviewed change; widening the agent's reach is not.

`VERIFY` before committing: whether a Fabric Data Agent can be grounded on a Power BI
semantic model, **whether model RLS is honored**, and **which identity the generated query
executes under** — the querying user, or a fixed service identity. **If RLS is not honored
under the consuming user's identity, the agent does not ship to a sales audience.** That is
assumption A6, and it is the one that gates the component.

### 8.3 Making the model agent-ready

The agent's accuracy is mostly a function of model metadata, which is the cheapest work in
this document and the most often skipped.

| Do this | Because |
|---|---|
| Hide every key, GUID and non-additive column | If it is visible and numeric, the agent will sum it. Hiding it is the only reliable prevention |
| Leave only measures summable | Forces the agent through certified definitions rather than raw aggregation |
| Write a description on every visible field | This is the agent's grounding, not documentation |
| Populate synonyms for JourneyTeam's vocabulary | "Practice", "backlog type", "AE / SAM / SDR", "co-sell". None of these are Dataverse column names — see [`../reference/jtp-excel-pipeline-report.md`](../reference/jtp-excel-pipeline-report.md) |
| Mark the snapshot fact's date columns unambiguously | `snapshot_date` versus `estimatedclosedate` is the error with the worst consequences. See §8.4 |
| Name measures as the business names them | `Open Pipeline Value`, not `Sum of EstValue`. The agent matches on names |

Model hygiene was already required for report authors (pack TDD §7.3). With an agent it
stops being hygiene and becomes the interface.

### 8.4 The snapshot trap

The hardest thing about this model for an agent, and it must be handled explicitly rather
than hoped about.

`fact_opportunity_snapshot` has one row **per opportunity per day**. Therefore:

- **Summing `pipeline value` across the snapshot fact without fixing a single
  `snapshot_date` multiplies the answer by the number of days.** A year of history returns
  roughly 365× the real number — a plausible-looking figure that is catastrophically wrong.
- "What is the pipeline?" means today's snapshot, or current state.
- "What was the pipeline at the end of Q2?" means the snapshot on that date — the as-of
  pattern in pack TDD §8.2.
- "How has pipeline moved?" means one point per snapshot date, never a sum.

Mitigations, in order of reliability:

1. **Expose as-of behavior through measures**, so the correct filter is inside the measure
   rather than something the agent must construct. Most reliable.
2. **State the grain in the AI instructions** in the plainest possible language (§8.5).
3. **Include an as-of example query** among the few-shot examples (§8.6).
4. **Put the double-counting case in the evaluation set** (§8.8) so a regression is caught
   rather than reported by a customer.

### 8.5 AI instructions

Instructions are configuration and belong in source control alongside the model, not typed
into a portal and forgotten. Content, in priority order:

1. **Grain and time semantics.** The snapshot rule from §8.4, stated bluntly. Which date
   column means what. That `estimatedclosedate` is the default time basis for pipeline
   questions and `actualclosedate` for won/lost.
2. **Currency rule.** Default to `_base`. Never mix `_txn` and `_base` in one answer. The
   rate on a Dataverse record is the rate at write time — correct for financial reporting,
   wrong for pipeline comparison.
3. **Business vocabulary.** Practice, backlog type, relationship type, forecast category,
   team. Map each to the model field.
4. **Lifecycle.** Use the conformed status grouping, never raw `statecode` / `statuscode`.
   Specifically: `statecode = 2` mixes the out-of-the-box *Canceled* with JourneyTeam's
   custom loss reasons, so "lost" is a `statuscode`-grain question.
5. **Known limits, stated as limits.** Snapshot history starts on the deployment date and
   is not backfillable. The custom analytic schema is NULL on pre-cutover rows, so
   practice, stage and forecast trends cannot reach back past the cutover date.
   Business-hours metrics are calendar-hours until the holiday calendar exists.
6. **Refusal behavior.** When the model cannot answer a question, say so and name what is
   missing. **Do not approximate.** A wrong number delivered fluently is the worst output
   this solution can produce, and it is the one an agent is most inclined toward.

### 8.6 Example queries

Few-shot examples are the highest-leverage tuning available. Cover, at minimum, one of
each:

| Example | Teaches |
|---|---|
| Open pipeline by practice, current | Default measure and the practice bridge |
| Pipeline as of a stated past date | **The as-of pattern** — the one to get right |
| Win rate by owner over a period | Ratio with an explicit denominator |
| Pipeline movement between two dates | One point per snapshot date, not a sum |
| Weighted versus unweighted pipeline | That weighting is a defined measure, not a guess |
| Average deal size excluding outliers | That an outlier-excluded variant exists and is defined |

Each example is a question with its correct query, so the agent learns the *shape* of a
correct answer in this model.

### 8.7 Security

The agent inherits the security posture of whatever it is grounded on. Nothing about it is
a new security model, and that is exactly why S5 matters.

| Concern | Design |
|---|---|
| RLS | Model RLS must apply under the **consuming user's** identity (A6, `VERIFY`). If it does not, the agent does not ship to a sales audience |
| Audience | Agent access is granted like report access, through the same audience decision — not to everyone with a Fabric licence |
| Confidentiality | At JourneyTeam this data is real pipeline, win rates and margins. An agent that aggregates across owners is a disclosure surface even with RLS applied |
| Prompts and logging | `VERIFY` where prompts and generated queries are retained and who can read them. Questions themselves are sensitive: *"why did we lose to X"* is confidential |
| Instructions are not a boundary | Anything the grounding source permits, the agent can eventually be made to do. Restrict the source, not the prompt |
| Sensitivity labels | Purview labels applied in Dataverse do not automatically carry to Fabric items. If the customer relies on labels, that is a scoping item |

### 8.8 Evaluation and acceptance

An agent without an evaluation set is not testable, and an untestable component cannot be
handed to a customer.

- **A golden question set**, versioned with the model: 30–50 questions with agreed correct
  answers, drawn from the report pages, the metric list, and the failure cases in §8.4.
- **Run it before every release** of the model or the instructions. A model change can
  silently change an agent answer, and the agent is the consumer most likely to notice last.
- **Record per question:** correct / wrong / refused. **Wrong is far worse than refused**,
  and the acceptance criterion must say so explicitly rather than tracking a single
  accuracy score. A refusal costs a user thirty seconds; a confident wrong number can reach
  a forecast review.
- **Publish the limits** in handoff documentation, with the honest framing: the agent
  answers questions about what is in the model, and says so when it cannot.

### 8.9 Consumption

`VERIFY` current surfaces. Design intent: available where the question is actually asked —
in Fabric, and in Teams if supported, since a seller asking about their pipeline is in Teams
and not in a BI tool. Programmatic access is out of scope for the packaged offering.

### 8.10 Commercial implication — **DECISION S6**

The Data Agent is **not in the packaged offering as priced**. It adds build effort (model
metadata, instructions, examples, the evaluation set), an ongoing obligation (the evaluation
set is re-run on every model change), and a support surface that behaves unlike a report.

Three options, for the offering owner:

1. **In the fixed price**, as component 5. Strongest differentiation; adds cost and an
   ongoing obligation to every delivery.
2. **A priced add-on.** Keeps the base price and lets the capability be sold where the
   customer wants it.
3. **Not sold; used internally on the JTP build** to learn what it costs before committing.
   Most conservative, and it produces the evidence the other two options need.

**Recommendation: option 3 first, then decide.** The JTP build is exactly the place to find
out whether an agent over this model is genuinely useful or merely demonstrable, and the
answer changes which of options 1 and 2 is right. Whichever is chosen, pricing changes go
in [`../offering/pricing-and-packaging.md`](../offering/pricing-and-packaging.md) and
nowhere else.

**Until S6 is decided, do not put the Data Agent in a customer-facing deck, proposal, or
statement of work** — including as a roadmap item.

---

## 9. Identity and security end to end

| Boundary | Identity | Notes |
|---|---|---|
| Dataverse → Bronze | The link's own configuration | Configured by a privileged Dataverse and Fabric role. Not a runtime identity |
| Notebook execution | **A service principal**, never a person | A personal token is tenant-wide, carries the person's full permission set into every workspace they can reach, and attributes every automated action to them in the audit log |
| Gold → model | The model's connection | Direct Lake specifics `VERIFY` |
| Model → report consumer | The consuming user | RLS applies |
| Model → Data Agent | **The consuming user, required** | A6. If it is a fixed identity, RLS does not protect the answer |
| Gold → SQL endpoint | The endpoint user | **Unfiltered.** §7.2 |

Three rules:

1. **Least privilege, and a service principal for automation.** Route production
   connections through an app registration with set permissions, never an interactive
   personal sign-in.
2. **RLS is tested fail-closed** with named test users, against expected row counts, before
   UAT — not demonstrated on a happy path.
3. **Dataverse security parity is not achievable.** Record sharing and field-level security
   are not replicated. Say so at kickoff, not at UAT.

**The two RLS bypasses in this solution are the SQL endpoint (known, deliberate, restricted)
and a badly grounded Data Agent (avoidable, and the reason for S5).** Everything else
filters.

---

## 10. Orchestration

Two pipelines. The separation is the design decision.

```
DAILY BUILD                              DAILY SNAPSHOT  (separate pipeline)
  10 bronze validation   ← gate            10 bronze validation   ← gate
  20, 21, 24  (parallel)                   30 snapshot facts      ← fixed UTC time
  22, 23                                   completeness check + alert
  40 gold conformed dims
  50 silver sales
  51 silver derived history  ← after 30
  52 gold sales
  model refresh (Import only)
  agent evaluation set (on release)
```

- **Snapshots get their own pipeline and their own failure domain.** A failed Gold build
  costs a rerun. A missed snapshot day is gone permanently. They must not share a fate.
- **Validation gates both.** Nothing downstream runs if Bronze is not as expected.
- **`51` runs after `30`**, since derived history reads the snapshot written that day.
- **Under Import, the model refresh is triggered by pipeline completion, never scheduled
  independently.** Refreshing against a half-built Gold produces wrong numbers with no
  error. Under Direct Lake the step disappears, which removes the failure mode.
- **Everything except the snapshot append is idempotent.** Snapshot writes are append-only
  and guarded against double-writing the same date.
- **The agent evaluation set runs on model release**, not daily.

---

## 11. Environments and ALM

**A gap in the offering, recorded here rather than left implicit.** There is no versioning
or re-deployment story for a pack already delivered, and it is the biggest risk to
repeatable delivery at scale.

Design intent:

| Concern | Position |
|---|---|
| Source of truth | This repository. Notebooks as `.py`, models and reports as PBIP/TMDL, config as YAML |
| Promotion | Fabric deployment pipelines between Dev → Test → Prod workspaces `VERIFY` current capability for each item type |
| Customer environments | Customers with separate Dataverse Dev/Test/Prod will ask how the solution promotes between them. **No answer exists yet** |
| Conformance layer version | Recorded at handoff and required for any future upgrade. Currently `0.1.0-draft` |
| Binary artifacts | Never committed. No `.pbix` |
| JourneyTeam's own build | JTP is JT **Production**. Development happens in JT Dev; enabling Link to Fabric is a change request with a documented promotion path and rollback |

**DECISION S4:** the promotion path and the upgrade story both need an ADR before the first
customer delivery, not after. A customer on conformance layer 1.2 must be identifiable and
upgradable.

---

## 12. Monitoring and operations

| Signal | Why | Alert to |
|---|---|---|
| **Snapshot completeness** | The only unrecoverable failure in the solution | Named contact, daily |
| Bronze validation failure | Everything downstream is invalid | Named contact, on failure |
| Pipeline failure | Standard | Named contact |
| Model refresh failure (Import only) | Silent staleness otherwise | Named contact |
| Choice values resolving to NULL | Customer added a status reason; reports show blanks | Build report |
| Agent evaluation regression | A model change broke an answer | Reviewer, on release |
| Capacity utilisation | Snapshot growth and Direct Lake behavior both consume | Platform team |

**Snapshot completeness is the one that cannot wait for someone to notice.** Every other
failure in this list is recoverable by re-running something.

At handoff, monitoring ownership is assigned by name — see
[`../delivery/support-handoff.md`](../delivery/support-handoff.md).

---

## 13. Capacity, sizing and cost drivers

**No Microsoft pricing, capacity, or licensing figure is restated here.** They change, and
[`licensing-and-capacity.md`](licensing-and-capacity.md) carries the verification checklist
that must be worked before any cost claim reaches a customer.

The architecture's own cost drivers, which are ours to design:

| Driver | Behavior | Control |
|---|---|---|
| **Snapshot growth** | Open opportunities × days. The one recurring storage cost the architecture adds | `daily_retention_days`, then month-end rollup. Agree at kickoff, not at handoff |
| Bronze | Shortcut, no copy | `VERIFY` current Dataverse capacity terms — Microsoft positions it as not duplicating storage, but terms change |
| Silver / Gold | Full rebuild frequency | Refresh cadence is configuration |
| Direct Lake | Memory behavior under load; fallback to DirectQuery | The Sprint 1 spike must measure this with realistic volume |
| Power BI licensing | Depends on the Fabric SKU | `VERIFY`. Report distribution model depends on it |
| **Data Agent** | Per-question consumption `VERIFY` | Unlike a report, cost scales with *questions asked* — a different cost shape from everything else here, and one to understand before S6 |

That last row is worth naming: every other component in this solution costs what it costs
regardless of how much it is used. An agent does not. **Establish the cost shape on the JTP
build before pricing it.**

---

## 14. Testing and acceptance

| Layer | Test | Gate |
|---|---|---|
| Ingestion | `10` passes with zero unresolved discrepancies | Sprint 1 exit |
| Conformance | Spot-check against Dynamics records; zero unmapped choice values in reporting scope | Sprint 1 exit |
| Snapshots | Job scheduled and **verified to have written at least one day** | Sprint 1 exit — non-negotiable |
| Gold | Data quality checks (pack TDD §13.2) | Before model build |
| Model | Every metric in `metrics.yaml` implemented; RLS fail-closed with named test users | Before reports |
| **Reconciliation** | Headline metrics tie to Dynamics 365 Sales, variances documented **with reasons** | **Before UAT opens** |
| Reports | Branded, snapshot notes visible, drill-through works | Before UAT |
| Data Agent | Golden question set run; wrong answers at zero; refusals documented | Before the agent is exposed to anyone |
| End to end | One question traced from a report page back to the Dataverse record | Handoff |

**Reconciliation happens before UAT, not during.** A number that does not tie is the fastest
way to lose confidence in the whole platform, and it is nearly always a conformance issue —
currency, status decoding, time zone — rather than a report issue. Walking into UAT with a
known, explained variance is fine. Discovering one during UAT is not.

---

## 15. Open decisions

Solution-level. Pack-level decisions D1–D11 are in the pack TDD §14 and are not repeated.

| # | Decision | Owner | Blocks | Status |
|---|---|---|---|---|
| **S1** | **Medallion topology** — does the reference design adopt the split-workspace shape, support both, or stay single-lakehouse? | Architecture | `medallion-design.md` credibility; notebook structure | **Open.** ADR owed. See §5.5 |
| **S2** | Parameterise lakehouse names per layer in `platform/config/` | Data engineer | Every notebook | **Open.** Code change, right regardless |
| **S3** | **Choice-label metadata source** — link tables or Dataverse Web API | Data engineer | The entire conformance layer | **Open.** Most important unresolved technical item (A4) |
| **S4** | Promotion path and upgrade story between environments | Architecture + delivery | Repeatable delivery at scale | **Open.** §11 |
| **S5** | **Data Agent grounding source** — semantic model or lakehouse | Architecture | Whether the agent is shippable to a sales audience | **Open.** Recommendation: semantic model. §8.2 |
| **S6** | **Is the Data Agent in the offering, an add-on, or internal only?** | **Offering owner** | Pricing, deck, proposals | **Open.** Recommendation: internal on JTP first. §8.10 |
| **S7** | SQL endpoint audience beyond the platform team | Customer + JT | Security posture | Per engagement. Default `platform_team_only` |
| **S8** | Whether the Data Agent's prompt and query logs are acceptable to the customer | Customer | Whether the agent can be deployed at all in some tenants | **Open.** `VERIFY` retention first. §8.7 |

Two of these are more urgent than the rest. **S3 blocks the conformance layer, which blocks
everything.** **S5 decides whether component 5 exists**, and it needs a `VERIFY` against
Microsoft documentation rather than a debate.

---

## 16. Build sequence

Order is not arbitrary — each step is either a gate or unrecoverable if delayed.

| # | Step | Why here |
|---|---|---|
| 1 | Confirm region alignment, capacity, privileges | Can stop the engagement dead; cheap to check |
| 2 | Enable Link to Fabric for the configured table set | Everything depends on it |
| 3 | Run `10`; resolve **every** discrepancy | A mapping error here is cheap, in UAT it is not |
| 4 | Resolve **S3** — choice-label metadata | Blocks all conformance |
| 5 | Build conformance (`20`–`24`) | Blocks everything above Silver |
| 6 | **Deploy and schedule the snapshot job (`30`)** | **Unrecoverable if delayed.** Every day of delay is a day of history permanently lost |
| 7 | Direct Lake spike with realistic volume and RLS applied | Decides D7 before reports are built on it |
| 8 | `40`, `50`, `51`, `52` — Gold and pack | Standard |
| 9 | Semantic model, measures, RLS | Implements `metrics.yaml` |
| 10 | Reconcile headline metrics; document variances | **Before UAT** |
| 11 | Reports, branding, app | The delivered surface |
| 12 | Model metadata pass — descriptions, synonyms, hidden columns | Report authors benefit; the agent depends on it |
| 13 | Data Agent: instructions, examples, golden question set | **Last.** It is only as good as everything above it |
| 14 | Monitoring, handoff, record the conformance layer version | Required for any future upgrade |

**Step 6 comes before anything is visible.** It produces nothing a customer can see and
cannot be caught up later — which is exactly why it is the step most at risk of slipping.

**Step 13 is last for a reason.** An agent built over an unfinished model produces confident
wrong answers, and those are much harder to walk back than a missing feature.
