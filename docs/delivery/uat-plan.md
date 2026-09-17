# UAT plan

Template for the customer-facing UAT plan. Copy into the engagement, fill in the packs
purchased and the named testers.

## Purpose and boundaries

UAT confirms that the delivered packs are **correct, complete against the packaged scope,
and usable**. It is not a design phase.

Every item raised is classified into exactly one bucket, and the classification is stated
back to the customer:

| Bucket | Definition | Handled |
|---|---|---|
| **Defect** | Delivered behavior does not match the documented pack definition | Fixed within the engagement |
| **Configuration** | Correct behavior, wrong parameter — fiscal calendar, branding, RLS assignment | Fixed within the engagement |
| **Change request** | New scope — a metric, field, report, or source not in the pack definition | Documented, scoped, and quoted separately |

Classify explicitly and promptly. UAT is where fixed-price engagements lose margin,
because reasonable-sounding requests that are genuinely new scope get quietly absorbed.
Saying "that's a change request, here's what it would take" is a normal, professional
answer.

## Entry criteria

- [ ] The Sales pack is deployed and refreshing on schedule
- [ ] Headline metrics reconciled against Dynamics 365, with variances documented and explained
- [ ] RLS deployed and validated by the delivery team with test users
- [ ] Reports branded
- [ ] Named customer testers identified, with access confirmed
- [ ] This plan reviewed with the customer

**Reconciliation must be complete before UAT opens.** Discovering a variance during UAT
costs far more in confidence than it does in effort.

## Test areas

### 1. Data accuracy

| Test | Expected |
|---|---|
| Headline totals tie to Dynamics 365 Sales within documented variance | Match, or documented reason |
| Record counts by status tie to the source app | Match |
| Choice / option-set labels display correctly, never as integers | Labels everywhere |
| Currency amounts are correct and the currency basis is clear | Correct and unambiguous |
| Date attribution matches the source app, including around month boundaries | Match — catches time zone errors |
| Drill to detail returns the expected underlying records | Match |

### 2. History and snapshots

| Test | Expected |
|---|---|
| Snapshot history is present for every day since the job started | No gaps |
| As-of-date views return the state as of that date | Correct |
| Aging buckets calculate correctly | Correct |
| Trend visuals show no unexplained discontinuities | Smooth, or explained |

Snapshot depth at UAT is limited to the days elapsed since Sprint 1. Set this expectation:
trends will look short at go-live and lengthen. This is normal and is exactly why the job
started in Sprint 1.

### 3. Security / RLS

| Test | Expected |
|---|---|
| Each test user sees only their permitted scope | Per the agreed pattern |
| A user with no assignment sees nothing, not everything | Fail-closed |
| Snapshot data respects the **historical** owner, not today's | Historical attribution |
| SQL endpoint access is limited to the agreed audience | Per agreement |

Fail-closed is the important one. An RLS misconfiguration that shows everything is a data
exposure, not a cosmetic defect.

### 4. Usability and performance

| Test | Expected |
|---|---|
| Reports render within an acceptable time on the agreed capacity | Agreed threshold |
| Filters, slicers, and cross-filtering behave as expected | Correct |
| Reports are usable on the intended devices | Usable |
| Analyze in Excel works for the agreed audience | Works |
| Copilot responds usefully against the semantic models | Reasonable answers |

### 5. Operations

| Test | Expected |
|---|---|
| Scheduled refresh completes reliably | Completes |
| Snapshot completeness check reports correctly | Detects gaps |
| Failure alerting reaches the right people | Delivered |

## Process

1. **Duration:** one week within Sprint 3, unless agreed otherwise.
2. **Logging:** all items in one agreed location. Each needs the report, the filter state,
   the expected value, the observed value, and the source-app comparison.
3. **Triage:** daily during UAT. Each item classified and communicated.
4. **Support:** JourneyTeam support during UAT draws on the purchased coaching allotment.

## Exit criteria

- [ ] All defects resolved and retested
- [ ] All configuration items applied
- [ ] All change requests documented, scoped, and quoted
- [ ] RLS validated by the customer, fail-closed confirmed
- [ ] Customer sponsor sign-off recorded

## Sign-off

| | Name | Date |
|---|---|---|
| Customer sponsor | | |
| Customer data owner | | |
| JourneyTeam project lead | | |

Sign-off covers the packaged scope as documented. Open change requests are listed
separately and do not block sign-off.
