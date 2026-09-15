# Snapshots and history

The second pillar of the offering's IP, after the [conformance layer](conformance-layer.md).

## The problem

Dataverse is a current-state store. When an opportunity moves from Qualify to Propose, the
prior stage is gone. When a case closes, the record no longer says how long it sat in the
queue.

So these questions — which are among the most commonly asked — cannot be answered from
Dataverse, and cannot be answered by any first-party Dynamics 365 analytics either:

- What did the pipeline look like on the last day of Q2?
- How has our open case backlog trended over the past six months?
- How many work orders were awaiting parts each day last quarter?
- Is average deal age getting better or worse?
- What did we forecast in January versus what we closed?

**This is the single clearest differentiator in the offering.** It is not a matter of
building better reports than Microsoft; the data required does not exist until someone
starts capturing it.

## The consequence for delivery

History cannot be backfilled from a current-state source. **A day not captured is lost
permanently.**

Therefore: **the snapshot job is configured and running in Sprint 1**, before any semantic
model or report exists. It is the first thing deployed after Bronze validation, not the
last. The [delivery playbook](../delivery/playbook.md) treats it as a Sprint 1 exit
criterion for exactly this reason.

Tell the customer this explicitly during kickoff. "Every day we wait is a day of history
you will never get" is both true and the most effective argument for starting promptly.

## Approach

### Daily snapshot facts

For each entity where lifecycle state matters, write one row per record per day, capturing
the attributes that change: state, status, stage, owner, forecast category, monetary
amount, estimated close date.

| Snapshot fact | Grain | Primary questions |
|---|---|---|
| `fact_opportunity_snapshot` | opportunity × day | pipeline as-of-date, stage movement, forecast vs. actual, slippage |
| `fact_case_snapshot` | case × day | backlog, aging buckets, queue dwell time |
| `fact_workorder_snapshot` | work order × day | backlog by status, awaiting-parts trend, schedule adherence |
| `fact_project_snapshot` | project × day | WIP, estimate-to-complete drift, margin trend |

Snapshots are partitioned by snapshot date and written append-only. They are never updated
in place — a snapshot is a statement about a day, and restating it destroys the record.

### SCD2 on key dimensions

Dimensions whose attributes are used in historical analysis get effective-dated versioning
rather than being overwritten:

- `dim_owner` — territory and manager reassignment is constant in sales organizations, and
  attributing last year's results to this year's manager is wrong
- `dim_customer` — segment, industry, and account owner changes
- `dim_product` — category and pricing changes

Other dimensions are Type 1 (overwrite) unless a metric in `metrics.yaml` requires
otherwise. SCD2 everywhere is a cost with no benefit; SCD2 where history is actually
queried is essential.

### Derived duration facts

Some history questions are better answered by deriving durations once rather than scanning
snapshots at query time:

- Time in each sales stage, from snapshot transitions
- Case first-response and resolution intervals, respecting business hours
- Work order travel versus on-site duration, from booking records

These are built from snapshot data, so they are only as deep as the snapshot history. They
are additive to snapshots, not a replacement.

## Sizing and cost

Snapshots grow linearly in records × days. This is the one part of the architecture with an
open-ended storage cost, so it is sized deliberately per customer rather than left to
grow:

- **Snapshot only what changes and what is asked about.** Do not snapshot every column of
  every table. The snapshot fact definitions above are deliberately narrow.
- **Snapshot open records daily; closed records once.** A closed opportunity will not
  change again. Capture its final state and stop snapshotting it — this alone typically
  removes most of the growth.
- **Retention is a configuration input.** Daily detail for a defined window, then roll up
  to month-end snapshots beyond it.

`platform/config/customer.example.yaml` carries these as parameters. Snapshot retention and
rollup policy should be a conversation at kickoff, because it is the one design choice that
has a recurring cost attached.

## Risks

- **Silent job failure.** A snapshot job that stops running loses history without any error
  a report would surface. Monitoring the snapshot job is not optional, and gaps must be
  detectable — a snapshot completeness check belongs in the platform notebooks.
- **Time zone drift.** A snapshot taken at an inconsistent local time produces jagged
  trends. Snapshot on a fixed UTC schedule and document it.
- **Mid-engagement schema change.** If a customer adds a column mid-history, older
  snapshots will not have it. Snapshot tables must tolerate schema evolution.
- **Customers who expect backfill.** Some will assume history is already there. Set the
  expectation in the sales conversation, not at UAT.
