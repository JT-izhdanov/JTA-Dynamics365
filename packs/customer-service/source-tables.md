# Customer Service pack — source tables

> **DRAFT — NOT VALIDATED.** Correct from what notebook 10 observes during the first
> build. Items marked `VERIFY` are explicitly unconfirmed. Logical names, lowercase.

## Core tables

| Table | Role | Grain |
|---|---|---|
| `incident` | Case fact + snapshot source | one row per case |
| `incidentresolution` | Resolution activity | one row per resolution | `VERIFY` |
| `slakpiinstance` | SLA KPI tracking | one row per SLA KPI per case | `VERIFY` |
| `sla` / `slaitem` | SLA definitions | configuration |
| `entitlement` | Entitlement | one row per entitlement |
| `queue` / `queueitem` | Queue routing | one row per queued item |
| `knowledgearticle` | Knowledge article | one row per article |
| `activitypointer` | Activities | via `bridge_activity` |

## Dimension sources

Consumes the conformed dimensions. Adds no new ones — `dim_customer`, `dim_contact`,
`dim_owner`, and `dim_date` all come from the Sales pack build and the conformance layer.

| Table | Produces |
|---|---|
| `account`, `contact` | `dim_customer`, `dim_contact` (conformed) |
| `systemuser`, `team`, `businessunit` | `dim_owner` (conformed) |
| `product` | `dim_product` (conformed) — where cases relate to products |

## incident — columns

| Column | Purpose | Notes |
|---|---|---|
| `incidentid` | Key | |
| `ticketnumber` | Business key | What agents and customers quote |
| `title` | Label | |
| `statecode` | Lifecycle | 0 = Active, 1 = Resolved, 2 = Cancelled — `VERIFY` |
| `statuscode` | Status reason | Customer-extensible |
| `prioritycode` | Priority | |
| `casetypecode` | Case type | Often left at default — check |
| `caseorigincode` | Channel | Phone, email, web, etc. |
| `severitycode` | Severity | `VERIFY` usage |
| `customerid` | → `dim_customer` | **Polymorphic** — account or contact |
| `primarycontactid` | → `dim_contact` | |
| `ownerid` | → `dim_owner` | Snapshots join the **as-of** owner version |
| `owningbusinessunit` | → `dim_owner` / RLS | |
| `createdon` | Created (UTC) | `time_basis` for volume metrics |
| `modifiedon` | Modified (UTC) | |
| `resolveby` | SLA due | |
| `firstresponsebykpiid` | → `slakpiinstance` | `VERIFY` |
| `resolvebykpiid` | → `slakpiinstance` | `VERIFY` |
| `firstresponseslastatus` | First response SLA status | `VERIFY` |
| `resolvebyslastatus` | Resolution SLA status | `VERIFY` |
| `firstresponsesent` | First response flag | `VERIFY` |
| `entitlementid` | → `entitlement` | |
| `parentcaseid` | Parent case | Child cases affect volume counts — decide handling |
| `productid` | → `dim_product` | |
| `subjectid` | Subject taxonomy | `VERIFY` usage |
| `escalatedon` | Escalation timestamp | `VERIFY` availability |

**`customerid` is polymorphic** (account or contact) — resolve explicitly in Silver. B2C
service desks will break an account-only assumption.

**`parentcaseid`:** decide whether child cases count as cases. Both answers are defensible;
inconsistency between reports is not.

## SLA tracking — resolve before building SLA metrics

SLA data can come from two places, and the customer may use neither:

1. **`slakpiinstance`** — populated when Dataverse SLAs are configured. Carries per-KPI
   status and timestamps.
2. **Derived from timestamps** on `incident` plus activity history in `bridge_activity`.

Many customers do not configure Dataverse SLAs at all. **Confirm before promising SLA
attainment metrics.** If SLAs are not configured, either derive from timestamps (and label
the metric as derived) or exclude it — do not present a derived approximation as SLA
attainment.

`VERIFY` the `slakpiinstance` table shape and availability through Link to Fabric.

## Omnichannel — scope carefully

Conversation and session analytics depend on tables that exist only where Omnichannel is
deployed, and their availability through Link to Fabric is unconfirmed.

| Table | Purpose | Status |
|---|---|---|
| `msdyn_ocliveworkitem` | Conversation | `VERIFY` |
| `msdyn_ocsession` | Session | `VERIFY` |
| `msdyn_ocparticipant` | Participant | `VERIFY` |

**Treat all of these as optional.** Basic channel analysis uses `caseorigincode` on the
case, which is always available. Deep conversation analytics is a roadmap candidate, not
part of this pack.

## Choice columns requiring labels

| Table | Columns |
|---|---|
| `incident` | `statecode`, `statuscode`, `prioritycode`, `casetypecode`, `caseorigincode`, `severitycode` |
| `queueitem` | `statecode`, `statuscode` |

## Business hours — the blocking dependency

First-response time, resolution time, and SLA attainment are normally measured in
**business hours**. The conformed `dim_date` has **no holiday or working-day calendar yet**
(see the TODO in [notebook 24](../../platform/notebooks/24_silver_conformance_date.py)).

Until it exists, these metrics are calendar-hours and must be labelled as such in
`metrics.yaml`. **This should be resolved before the pack goes GA** — it is the pack's
largest correctness gap, and business hours are customer-specific and often regional.

## Not in scope

- Custom fields and tables
- CSAT and survey data (typically outside Dataverse)
- Telephony system data
- Deep Omnichannel conversation analytics
