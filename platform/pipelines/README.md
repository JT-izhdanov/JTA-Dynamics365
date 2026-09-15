# Pipelines

Orchestration and scheduling for the notebooks in [`../notebooks/`](../notebooks/).

**Nothing here yet.** Orchestration is defined during the first build, once the notebooks
are validated. This README records the intended design so it is not re-derived.

## Intended orchestration

```
┌─────────────────────────────────────────────────┐
│ Daily — conformance and Gold                    │
│                                                 │
│   10_bronze_shortcut_validation                 │
│            │ (gate — fail stops the run)        │
│            ▼                                    │
│   20 choice labels ─┐                           │
│   21 currency       ├─ parallel                 │
│   24 date          ─┘                           │
│            │                                    │
│            ▼                                    │
│   22 ownership  (needs 20)                      │
│   23 activities (needs 20)                      │
│            │                                    │
│            ▼                                    │
│   40_gold_conformed_dimensions                  │
│            │                                    │
│            ▼                                    │
│   5x pack Gold builds (future)                  │
│            │                                    │
│            ▼                                    │
│   semantic model refresh                        │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ Daily — snapshots (SEPARATE pipeline)           │
│                                                 │
│   10_bronze_shortcut_validation                 │
│            ▼                                    │
│   30_silver_snapshot_facts                      │
│            ▼                                    │
│   completeness check + alert                    │
└─────────────────────────────────────────────────┘
```

## Why snapshots are a separate pipeline

**This is the most important design decision here.**

A lost Gold rebuild costs a rerun. A lost snapshot day is gone permanently — history cannot
be backfilled from a current-state source
([`../../docs/architecture/snapshot-and-history.md`](../../docs/architecture/snapshot-and-history.md)).

So the snapshot job must not share a failure domain with the rest of the platform. If a
pack Gold build breaks, snapshots must keep running. Separate pipeline, separate schedule,
separate alerting.

## Scheduling

Driven by `refresh` and `snapshots` in the customer configuration — not hard-coded.

| Job | Cadence | Note |
|---|---|---|
| Snapshots | Daily, **fixed UTC time** | Must not drift. Inconsistent timing produces jagged trends that look like real business variation |
| Conformance | Daily, typically after snapshots | Cheap to run more often if a customer needs it |
| Gold | Daily, after conformance | |
| Semantic models | **Triggered after Gold completes** | Never independently scheduled — refreshing against a half-built Gold produces wrong numbers with no error |

## Monitoring requirements

Non-negotiable, and named as an owned responsibility at support handoff
([`../../docs/delivery/support-handoff.md`](../../docs/delivery/support-handoff.md)):

1. **Snapshot completeness alerting.** A silently stopped snapshot job surfaces no error in
   any report — the failure is invisible until someone asks a trend question months later.
   Notebook 30 reports gaps; that output has to reach a person.
2. **Refresh failure alerting** routed to a named customer contact.
3. **Bronze validation failures** raised immediately — they usually mean a schema change
   upstream.
4. **Capacity monitoring**, since snapshot volume grows.

## To define during the first build

- Whether to use Fabric Data Pipelines, notebook scheduling, or an orchestrator notebook
- Retry policy — and specifically that a snapshot retry must not double-write a date
  (notebook 30 guards this, but the pipeline should not rely solely on that)
- Alert routing and escalation
- How the `5x` pack builds attach once they exist
- Whether to adopt Fabric git integration for pipelines, as for notebooks
  ([`../README.md`](../README.md#future-fabric-git-integration))
