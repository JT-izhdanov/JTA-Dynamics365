# JTP first build — development project plan

The Sales pack's first build, delivered against **JourneyTeam's own Dynamics 365 Sales
system (JTP)**, with one developer.

This is the validation pass described in
[`../architecture/reference-architecture.md`](../architecture/reference-architecture.md#validation-status).
Read [`../../packs/sales/technical-design.md`](../../packs/sales/technical-design.md)
first — this plan schedules that design; it does not restate it.

---

## 1. Two objectives, and the second one is the product

| # | Objective | Deliverable |
|---|---|---|
| 1 | A working Sales analytics solution on JourneyTeam's own data | Deployed Fabric platform, semantic model, report pack |
| 2 | **Corrected, hardened, repeatable IP** | Every draft in `platform/` and `packs/sales/` replaced with what was actually observed |

**Objective 2 is why this build exists.** Objective 1 alone is an internal BI project.
Objective 2 is what makes the next engagement a 6-week fixed-price delivery instead of
another first-of-a-kind build.

The practical consequence: **time spent correcting the repository is not overhead, it is
the deliverable.** A build that produces working reports and leaves the drafts untouched
has failed, however good the reports are.

---

## 2. Change control classification

**JT-internal system. JTP is Production.**

| Activity | Environment | Route |
|---|---|---|
| Dataverse schema discovery | **JTP, read-only** | Read/observe in Prod is fine via an approved service principal with least-privilege read roles |
| Notebook, model, and report development | **JT Dev** | All build and iteration happens here |
| Link to Fabric enablement | **JT Dev first, then JTP by change request** | Environment configuration, not a solution artifact — see below |
| Fabric workspace and lakehouse creation | Production tenant | M365/Fabric has no sandbox; treat as Production. Least privilege, named owners |
| Repository changes | Feature branch → PR into `main` | Branch protection, review |

### Link to Fabric on JTP — the promotion path

Link to Fabric is **environment configuration**, not a managed solution component, so the
normal Dev → UAT → Prod solution pipeline does not carry it. The path is:

1. Enable and validate in **JT Dev**, documenting the exact configuration and the table
   selection.
2. Raise a **change request** for JTP naming: the table selection, the target Fabric
   workspace and capacity, the service principal used, and the rollback (disable the link;
   Bronze is a shortcut, so nothing is copied and nothing is destroyed).
3. Obtain approval from the designated approver / CAB, with a deployment window.
4. Apply to JTP, then re-run Bronze validation against it.

Rollback is genuinely clean here — disabling the link removes the shortcut without
touching Dataverse — and that is worth stating in the change request, because it makes
this a low-risk approval.

### Access

- **A service principal, scoped to the task, with secrets in Key Vault.** Never the
  developer's own account, and never interactive or device-code sign-in as a person — not
  even once, not for a quick test.
- Read-only roles for discovery. Write scope only where the build actually writes.
- Access removed or reduced when the build closes.

### Risks to flag up front

| Risk | Why it needs calling out before, not after |
|---|---|
| **JT's confidential sales data** | Pipeline, win rates, margins, and named customer opportunities all land in Fabric and in reports. See §4 |
| **Security roles** | RLS design touches who can see whose pipeline — an internal policy question, not just a technical one |
| **Shared service** | Fabric capacity is shared; snapshot growth and query load affect anything else on it |
| **Production configuration change** | Enabling the link changes JTP environment configuration, however low-risk the rollback |

---

## 3. What JTP changes about the design

JourneyTeam sells **professional services by technology practice**, as a **Microsoft
Partner**. That shape is not what the Sales pack was drafted against, and it raises
modelling questions that must be answered in discovery rather than assumed.

These are the highest-value findings to come out of planning this build.

### 3.1 Practice is the primary dimension, and it may be line-level

Practice (D365 CE, Business Central, Azure, Data & AI, Security, M365, Power Platform)
does not exist in stock Dynamics 365 Sales. It could live on a custom opportunity column,
the business unit, territory, the product catalogue, or opportunity product lines.

**The question that matters: can one opportunity span multiple practices?** For a partner
selling a combined engagement, almost certainly yes.

If so, **practice is a line-level attribute**, and:

- `opportunityproduct` becomes **mandatory**, flipping technical design decision **D8**
  from "optional, omit the page if unused" to "required, the pack does not work without it".
- Header-level practice reporting will **mis-attribute multi-practice deals** — the whole
  deal value credited to one practice, or double-counted across several. This is the
  classic way practice pipeline numbers end up wrong while looking plausible.
- `dim_product` needs a practice hierarchy, and practice becomes a conformed dimension
  candidate rather than a Sales-local attribute — which would need an ADR.

**This is the single most important discovery item.** Everything about practice reporting
depends on the answer.

### 3.2 Revenue type mix

A Microsoft Partner pipeline typically blends:

| Revenue type | Character |
|---|---|
| Project services (fixed fee or T&M) | One-time, margin-bearing |
| Managed services / support | **Annuity**, recurring |
| Licensing resale (CSP) | High revenue, thin margin |
| Microsoft-funded (ECIF, assessments, workshops) | Funded, often fixed, strategically significant |

These have materially different margins and sales cycles. **A single "pipeline value"
summed across all of them is misleading** — a $500k CSP deal and a $500k services deal are
not comparable pipeline.

Needs a revenue-type dimension and, most likely, separate pipeline views per type.

### 3.3 TCV versus ACV — a known partner-reporting trap

For annuity and managed-services deals, is `estimatedvalue` the **total contract value** or
the **annualised** figure?

If the two are mixed across records — which is common where nobody defined it — **pipeline
totals are meaningless** and no amount of report design fixes it. Normalisation belongs in
Silver, with the rule documented in `metrics.yaml`.

Ask this explicitly in discovery. It is the kind of thing an organisation discovers it has
never decided.

### 3.4 Microsoft-sourced versus self-sourced pipeline

Co-sell registration, Microsoft referrals, and incentive-linked deals. JourneyTeam
leadership almost certainly wants partner-sourced pipeline as a metric — it is a core
partner KPI.

Discovery item: **is it tracked in Dynamics at all?** If it is only in Partner Center, it
is out of scope for this pack and becomes a candidate additional source.

### 3.5 Practice pipeline to delivery capacity

"Pipeline by practice by expected start date" is the question a services organisation
actually asks, because it drives staffing. It is partly a Sales question — expected close
date and practice get most of the way there — and fully answered only with delivery data,
which is not in scope.

**Scope it as Sales-only and say so.** Deliver pipeline by practice by expected close date,
and state plainly that the conversion to booked capacity is not in this release. Do not
approximate delivery data from Sales fields; a staffing number that is quietly wrong is
worse than one that is absent.

If JourneyTeam wants the full question answered, that is the argument for bringing a
delivery pack back into scope — see
[`../offering/roadmap.md`](../offering/roadmap.md).

### 3.6 The upside — JTP is representative, not idiosyncratic

Every item above applies to **any professional-services or Microsoft Partner customer**, not
just JourneyTeam. So this build may yield a reusable **professional-services variant** of
the Sales pack: practice hierarchy, revenue-type dimension, TCV/ACV normalisation,
partner-sourced attribution.

That is a genuine product outcome from an internal build. Worth capturing deliberately
rather than as a side effect — and worth an ADR if practice becomes a conformed dimension.

---

## 4. Confidentiality — decide before the first report renders

The reports will contain JourneyTeam's **actual pipeline, win rates, loss reasons, deal
sizes, margins, and named customer opportunities.** All of it confidential business
information.

**JTP is also the natural demo environment.** Those two facts conflict, and the decision
needs making now rather than when someone screenshots a real win rate into a prospect deck.

| Option | Trade-off |
|---|---|
| **Masked demo copy** — separate workspace, obfuscated customer names and scaled values | Extra build effort; demo stays safe and shareable |
| **Real data, internal only** — demo by guided screen-share, never exported | No extra effort; relies on discipline and constrains who can demo |
| **Synthetic demo dataset** — purpose-built, not JT data at all | Most effort; best demo control; also solves the volume gap in §6 |

**Recommendation: real data internally for the build, plus a synthetic demo dataset** built
during Release 2. The synthetic set does double duty — it is also the performance test bed
JTP cannot provide (§6).

Until that decision is made and implemented: **no report screenshots from JTP leave
JourneyTeam**, and nothing from this build goes into `sales-assets/`.

---

## 5. Plan

Two releases. Release 1 proves the differentiator and burns down the unknowns; Release 2
completes the pack.

### Release 1 — thin slice: pipeline, with history

**Goal:** the pipeline-as-of-date capability working on real JourneyTeam data, and every
platform unknown resolved.

| # | Phase | Work | Dev-days | Exit criterion |
|---|---|---|---|---|
| 0 | Change control and access | Change request for JTP; service principal and Key Vault; Fabric capacity; JT Dev prep | 3 | CR approved; SP working; capacity available |
| 0b | **Discovery** | Read-only schema inspection on JTP; answer §3.1–3.4 with sales leadership; resolve D1–D6, D8 | 4 | Practice model understood; decisions recorded |
| 1 | **Link to Fabric and snapshots live** | Enable in Dev, validate; adapt notebook 10 to real schema; correct `source-tables.md`; deploy snapshot job and monitoring; apply to JTP after approval | 7 | **Snapshots running on JTP with monitoring** |
| 2 | Direct Lake spike | Resolve **D7** on evidence, with RLS applied | 2 | D7 decided |
| 3 | Conformance layer | Resolve the choice-label metadata source; notebooks 20, 21, 22 (**including the SCD2 merge, which is unwritten**), 23, 24 | 13 | Conformance output spot-checked against JTP records |
| 4 | D9 and Gold conformed | Implement all-versions publication; change and retest notebook 40 | 3 | Snapshot rows resolve to as-of owner versions |
| 5 | Sales Silver | Four conformed dimensions; `dim_opportunity`; polymorphic customer resolution; facts; **practice and revenue-type modelling**; quality checks and fill-rate reporting | 13 | Quality checks pass; fill-rate report reviewed |
| 6 | Gold and RLS bridge | Star schema; scope bridge | 4 | Star queryable |
| 7 | Semantic model — thin | Tables, relationships, hygiene; pipeline and as-of measures only | 5 | As-of measures verified not to sum across dates |
| 8 | RLS | Implement and test fail-closed | 3 | §9.3 of the TDD passes |
| 9 | **Reconciliation** | Open pipeline and closed-won tie exactly to JTP | 4 | Ties exactly, or variances documented |
| 10 | Reports — 2 pages | Pipeline Overview, **Pipeline History** | 4 | Pages render; no empty visuals |
| 11 | **IP hardening** | Correct `source-tables.md`, `metrics.yaml`, the TDD; write ADRs for what changed | 4 | Corrections committed |
| | **Release 1 subtotal** | | **69** | |

### Release 2 — complete the pack

| # | Phase | Work | Dev-days | Exit criterion |
|---|---|---|---|---|
| 12 | Derived history | As-of stamping refinements; `fact_stage_duration`; `fact_forecast_movement` | 5 | Validated against accumulated snapshot history |
| 13 | Semantic model — full | Remaining measures; practice and revenue-type additions; descriptions and folders | 6 | All in-scope measures present and described |
| 14 | Reports — 6 pages | Forecast, Win/Loss, Velocity, Leads, Performance, Products + paginated detail | 10 | Pages render; conditional pages dropped per §8.7 |
| 15 | Synthetic demo dataset | Masked or generated data; doubles as the volume test bed | 5 | Demo safe to show externally; performance measured at realistic volume |
| 16 | **Packaging for repeatability** | Deployment runbook; config template from what JTP actually needed; known-issues list | 4 | A second engagement can follow the runbook |
| | **Release 2 subtotal** | | **30** | |

### Effort summary

| | Dev-days |
|---|---|
| Release 1 | 69 |
| Release 2 | 30 |
| Core total | **99** |
| Contingency at 25% | 25 |
| **Planned total** | **~124** |

25% contingency is not padding. This is first-of-a-kind work with a **known unresolved
unknown** (the choice-label metadata source), an **unwritten component** (the SCD2 merge in
notebook 22), a **pending platform decision** (D9), and a data model nobody has looked at
yet (§3).

### Calendar, by developer allocation

| Allocation | Release 1 | Both releases |
|---|---|---|
| 100% (5 days/week) | ~17 weeks | ~25 weeks |
| 60% (3 days/week) | ~29 weeks | ~41 weeks |
| 40% (2 days/week) | ~43 weeks | ~62 weeks |

**Recommendation: 80–100% through phases 1–9.** Below roughly 60%, the conformance layer
work fragments badly — it is the most context-heavy part of the build, and re-establishing
context each week is real waste.

**Set expectations on this number.** ~124 dev-days is a substantial investment against a
6-week fixed-price delivery promise. That is the correct relationship and worth stating
plainly: the first build is expensive **because** subsequent builds are cheap. The
offering's economics depend on this investment being made once, properly, and captured in
the repository.

---

## 6. JTP's limits as a validation environment

Honest scope of what this build does and does not prove.

| Validates | Does **not** validate |
|---|---|
| Correctness of the conformance layer against real Dataverse | **Performance at customer scale** |
| Repeatability of the deployment procedure | Multi-currency conformance, if JourneyTeam is single-currency |
| Metric definitions and reconciliation approach | Complex business unit / territory hierarchies, if JourneyTeam's is flat |
| The snapshot and as-of history capability | Deep RLS patterns, if the sales org sees everything |
| That the professional-services shape works | Other industry shapes |

### The volume gap is the one that matters

JourneyTeam's own Sales org is likely **hundreds to low thousands of opportunities**. That
makes snapshot sizing trivial and correctness testing easy — and makes JTP **useless as a
performance test bed**. A customer with 50,000 opportunities will hit problems this build
cannot reveal, including the `MEDIANX` and Direct Lake fallback concerns in the technical
design.

**Mitigation: the synthetic dataset in Release 2 phase 15** is sized to a realistic
customer, so it serves as both the safe demo and the performance test. Do not skip it and
then quote a 6-week delivery to a large customer.

### If the sales org is small enough that RLS is trivial

If everyone at JourneyTeam sees all pipeline, RLS cannot be meaningfully validated here.
In that case build synthetic roles and a test hierarchy in **JT Dev** and validate against
those — do not let RLS reach a paying customer unvalidated, since an RLS failure that
shows everything is a data exposure.

---

## 7. Who is needed besides the developer

One developer does the build. These are the dependencies that will block them.

| Role | Needed for | Front-load |
|---|---|---|
| **Offering owner** | D1–D10 decisions, metric sign-off, D9 platform decision | **Yes — phase 0b** |
| **Sales leadership** | Practice model (§3.1), revenue types (§3.2), TCV/ACV (§3.3), metric definitions, reconciliation sign-off | **Yes — phase 0b** |
| **Dynamics administrator** | Link to Fabric change request and enablement | **Yes — phase 0** |
| **IT / security** | Service principal, Key Vault, Fabric capacity, RLS policy | **Yes — phase 0** |
| **Designated approver / CAB** | Production change approval | **Yes — phase 0** |
| **A technical reviewer** | Reviewing the developer's work at phase boundaries | Ongoing |

**Front-loading these is the main scheduling lever available.** A single developer
blocked waiting for a decision has no parallel work to switch to — that is the difference
between a one-person build and a two-person one, and it is why phase 0b buys down more risk
than its four days suggest.

### The single-developer risks

| Risk | Mitigation |
|---|---|
| **No peer review** | A named reviewer at each phase exit. Not optional on the conformance layer — a silent error there becomes a wrong number in every pack |
| **Single point of knowledge** | The IP hardening phases are the mitigation. They are also the deliverable, which is convenient |
| **Context switching** between PySpark data engineering and Power BI development | Phase boundaries are deliberately drawn on that seam; keep allocation high through phases 3–5 |
| **No parallel path when blocked** | Front-load every decision (above) |
| **Estimate concentration** | All 124 days rest on one person's availability. Any absence moves the date one-for-one |

---

## 8. Critical path and day-one actions

### The critical path runs through the change request, not the code

Phase 1 cannot complete on JTP until the change request is approved. Approval is calendar
time the developer cannot compress, and **everything downstream that needs real data waits
behind it.**

### Start the snapshot job as early as possible — this is genuinely urgent

**History cannot be backfilled.** Every week the snapshot job is not running on JTP is a
week of pipeline history JourneyTeam will never have.

For this build that cost is doubled, because the snapshot history **is** the demo. Release 2
phase 12 cannot be validated at all without accumulated history, and the Pipeline History
page is unimpressive with two weeks of data.

**Therefore, in order, on day one:**

1. **Raise the JTP change request.** Before any development. It is the longest-lead item
   and nothing about it depends on the rest of the plan.
2. **Request the service principal and Key Vault entries.**
3. **Confirm Fabric capacity** and region alignment with the Dataverse environment.
4. **Book the discovery session with sales leadership** for §3.1–3.4.

Then begin read-only schema discovery, which needs none of the above beyond read access.

### The wall-clock dependency, used deliberately

Phase 12 needs weeks of accumulated snapshots regardless of effort spent. That is not
purely a constraint — it means the gap between Release 1 and Release 2 is **useful** time,
and a part-time allocation is less wasteful across that boundary than within phases 3–5.
Plan the allocation unevenly: heavy through Release 1, lighter after.

---

## 9. Decisions required

Beyond technical design decisions **D1–D10**, this build needs:

| # | Decision | Owner | Needed by |
|---|---|---|---|
| J1 | **Where practice lives, and is it header or line level?** (§3.1) | Sales leadership | Phase 0b — blocks phase 5 |
| J2 | Revenue types, and whether pipeline is reported separately per type (§3.2) | Sales leadership | Phase 0b |
| J3 | **Is `estimatedvalue` TCV or annualised, and is it consistent?** (§3.3) | Sales leadership | Phase 0b — money metrics depend on it |
| J4 | Is Microsoft-sourced pipeline tracked in Dynamics? (§3.4) | Sales leadership | Phase 0b |
| J5 | **Demo data approach** (§4) | Offering owner | Before any report is shown outside JourneyTeam |
| J6 | RLS policy for JourneyTeam's own pipeline | Sales leadership + IT | Phase 8 |
| J7 | Developer allocation percentage | Delivery management | **Now** — it sets the date |
| J8 | Named technical reviewer | Delivery management | Phase 0 |
| J9 | Whether a delivery pack returns to scope, which §3.5 depends on | Offering owner | After Release 1 |

**J1, J3, and J7 are the consequential ones.** J1 and J3 can invalidate model work already
done if answered late. J7 is the only input needed to turn this plan into a date.

---

## 10. Definition of done

Release 1 is done when all of the following hold:

- [ ] Link to Fabric live on JTP through an approved change, with a documented configuration
- [ ] Snapshot job running with monitoring and a named owner
- [ ] Conformance layer built and spot-checked against JTP records
- [ ] Open Pipeline Value and Closed Won Value **tie exactly** to JTP
- [ ] RLS deployed and confirmed fail-closed
- [ ] Pipeline Overview and Pipeline History pages in use by JourneyTeam sales leadership
- [ ] **`source-tables.md`, `metrics.yaml`, and the technical design corrected from what was
      observed, and committed**
- [ ] ADRs written for D9, D10, and any practice-dimension change
- [ ] Every `VERIFY` marker in the Sales pack either resolved or restated with what is now known

The last three are the ones that will feel optional under schedule pressure and are not.
Without them this was an internal BI project, and the next customer engagement starts from
drafts again.
