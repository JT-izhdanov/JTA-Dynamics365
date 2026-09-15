# Field Service pack — source tables

> **DRAFT — NOT VALIDATED.** Correct from what notebook 10 observes during the first
> build. Items marked `VERIFY` are explicitly unconfirmed. Logical names, lowercase.

## Core tables

| Table | Role | Grain | Status |
|---|---|---|---|
| `msdyn_workorder` | Work order fact + snapshot source | one row per work order | `VERIFY` |
| `msdyn_workorderproduct` | Parts used | one row per product line | `VERIFY` |
| `msdyn_workorderservice` | Services performed | one row per service line | `VERIFY` |
| `msdyn_workordertype` | Work order type | configuration | `VERIFY` |
| `bookableresourcebooking` | Booking | one row per booking | **Second grain — see below** |
| `bookableresourcebookingheader` | Booking header | | `VERIFY` |
| `bookableresource` | Resource | one row per resource | Shared with Project Ops |
| `msdyn_agreement` | Service agreement | one row per agreement | `VERIFY` |
| `msdyn_agreementbookingdate` | PM schedule | | `VERIFY` |
| `msdyn_customerasset` | Customer asset | one row per asset | `VERIFY` |
| `msdyn_incidenttype` | Incident type taxonomy | configuration | `VERIFY` |
| `msdyn_resourcerequirement` | Requirement | | `VERIFY` |
| `msdyn_timeoffrequest` | Time off | | `VERIFY` — affects capacity |

## Inspections

`VERIFY` availability — inspections data shape and table names vary by Field Service
version, and some customers do not use them at all. Treat as optional and confirm per
engagement before promising inspection analytics.

## Dimension sources

| Table | Produces | Note |
|---|---|---|
| `bookableresource` | `dim_resource` | **Conformed.** Created by Project Ops if that pack is present; otherwise created here, still conformed |
| `msdyn_customerasset` | `dim_asset` | Pack-specific but built to conformed conventions |
| `account`, `contact` | `dim_customer`, `dim_contact` | Conformed |
| `product` | `dim_product` | Conformed |
| `territory` | `dim_territory` | Conformed |
| `systemuser`, `team`, `businessunit` | `dim_owner` | Conformance layer |
| `transactioncurrency` | `dim_currency` | Conformance layer |

## The grain problem

**The single most important modeling decision in this pack.**

One work order can have **many bookings** — multiple visits, multiple technicians, travel
plus on-site segments. So there are two legitimate fact grains:

| Grain | Answers | Risk |
|---|---|---|
| **Work order** | Throughput, first-time fix, cost, SLA | Loses technician-level detail |
| **Booking** | Utilization, travel time, adherence | **Double-counts** work order metrics if used carelessly |

The pack must build **both facts explicitly** — `fs__fact_workorder` and
`fs__fact_booking` — and each metric must declare which grain it uses. Mixing them is how
"our completed work order count is triple the real number" happens, and it is very hard to
spot because both numbers look plausible in isolation.

Confirm at kickoff which grain the customer thinks in. Most think in work orders; their
technicians' metrics live in bookings.

## msdyn_workorder — columns

| Column | Purpose | Notes |
|---|---|---|
| `msdyn_workorderid` | Key | |
| `msdyn_name` | Work order number | What the business quotes |
| `statecode` / `statuscode` | Lifecycle | |
| `msdyn_systemstatus` | **System status** | Usually the meaningful lifecycle column — Unscheduled, Scheduled, In Progress, Completed, Posted, Canceled. `VERIFY` values |
| `msdyn_workordertype` | → work order type | |
| `msdyn_priority` | Priority | |
| `msdyn_serviceaccount` | → `dim_customer` | Service location account |
| `msdyn_billingaccount` | → `dim_customer` | May differ from service account |
| `msdyn_primaryincidenttype` | → incident type | Problem taxonomy |
| `msdyn_customerasset` | → `dim_asset` | |
| `msdyn_agreement` | → `msdyn_agreement` | Populated for PM work orders |
| `msdyn_totalamount` / `_base` | Total value | |
| `msdyn_totalestimatedduration` | Estimated duration | `VERIFY` unit |
| `msdyn_timefrompromised` / `msdyn_timetopromised` | Promised window | **Appointment adherence** |
| `msdyn_datewindowstart` / `msdyn_datewindowend` | Date window | `VERIFY` |
| `msdyn_completedon` | Completion timestamp | `VERIFY` |
| `msdyn_firsttimefix` | First-time fix flag | `VERIFY` — **often unpopulated; see below** |
| `msdyn_territory` | → `dim_territory` | |
| `ownerid` / `owningbusinessunit` | → `dim_owner` / RLS | |
| `createdon` / `modifiedon` | Audit | |

**`msdyn_systemstatus` usually matters more than `statecode`** for Field Service lifecycle
analytics. Confirm which reflects the customer's process before building status metrics or
the snapshot `open_predicate` in
[notebook 30](../../platform/notebooks/30_silver_snapshot_facts.py).

**`msdyn_firsttimefix`:** if a flag exists but is unpopulated, first-time fix must be
derived — typically as "work order completed with exactly one booking and no follow-up
work order for the same asset within N days." That definition must be agreed with the
customer, not assumed.

## bookableresourcebooking — columns

| Column | Purpose | Notes |
|---|---|---|
| `bookableresourcebookingid` | Key | |
| `resource` | → `dim_resource` | |
| `starttime` / `endtime` | Scheduled window | |
| `msdyn_workorder` | → work order | `VERIFY` column name |
| `bookingstatus` | → booking status | Drives travel vs. on-site |
| `duration` | Duration | `VERIFY` unit |
| `msdyn_estimatedarrivaltime` | Estimated arrival | `VERIFY` |
| `msdyn_traveldurationinbound` / `outbound` | Travel duration | `VERIFY` — **key for travel vs. wrench time** |
| `actualarrivaltime` / `actualdeparturetime` | Actual timestamps | `VERIFY` — **requires field discipline** |

**Travel vs. on-site time depends entirely on booking timestamps being maintained in the
field.** If technicians do not update booking status on their devices, the data is absent
and the metric is not viable. Check the actual fill rate during the first build rather than
discovering it at UAT.

## Choice columns requiring labels

| Table | Columns |
|---|---|
| `msdyn_workorder` | `statecode`, `statuscode`, `msdyn_systemstatus`, `msdyn_priority` |
| `bookableresourcebooking` | `bookingstatus`, `statecode` |
| `msdyn_agreement` | `statecode`, `statuscode` |
| `msdyn_customerasset` | `statecode`, `statuscode` |

## Not in scope

- IoT / connected field service telemetry
- Telematics and vehicle tracking systems
- Inventory and warehouse detail beyond work order product lines
- Custom fields and tables
