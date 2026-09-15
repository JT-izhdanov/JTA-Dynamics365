# Customer Service pack

**$5,000** · Dynamics 365 Customer Service · **Status: planned** (second in the build sequence)

## What it covers

Case performance, SLA attainment, and — the differentiating part — **backlog and aging
history**, which Dataverse cannot provide.

| Area | Questions answered |
|---|---|
| Volume | Cases created, resolved, and open, by type, priority, channel, product |
| Responsiveness | First-response time, resolution time, SLA attainment |
| Backlog | Open backlog over time, aging buckets, queue dwell time |
| Quality | Reopen rate, escalation rate, first-contact resolution |
| Workload | Cases per agent, per team, per business unit |
| Knowledge | Knowledge article usage and deflection |

## Be honest about the competitive position

**Dynamics 365 Customer Service ships respectable first-party embedded historical
analytics.** A prospect using them will know, and claiming otherwise costs more credibility
than the point wins.

Differentiate where first-party genuinely cannot follow:

- **Custom fields and tables** — not available in first-party analytics
- **Backlog history beyond first-party retention**, unlimited and snapshot-based
- **Cross-app** — cases alongside sales history and field service work orders
- **Blending external data** — CSAT surveys, telephony systems, product telemetry
- **Full drill to detail** and unlimited tailoring
- **Customer owns the model**

The honest framing: *first-party analytics are fine for standard questions about Customer
Service; this pack is for non-standard questions, questions spanning apps, and questions
about the past.*

## Why second in the build sequence

Second-largest installed base, and case aging exercises the **same snapshot framework**
built for Sales — so it de-risks cheaply rather than introducing new architecture.

## Depends on

- The full [conformance layer](../../docs/architecture/conformance-layer.md)
- [Conformed dimensions](../_shared/conformed-dimensions.md): `dim_date`, `dim_owner`,
  `dim_customer`, `dim_contact`, `bridge_activity`, `lkp_choice_label`
- `fact_case_snapshot` from
  [`30_silver_snapshot_facts.py`](../../platform/notebooks/30_silver_snapshot_facts.py)

## Known limitations

1. **Business-hours metrics are calendar-hours until the holiday calendar exists.** This
   is the pack's most significant limitation: first-response time, resolution time, and
   SLA attainment are all normally measured in business hours. A metric that silently
   ignores weekends is wrong in a way customers notice immediately. See the TODO in
   [notebook 24](../../platform/notebooks/24_silver_conformance_date.py) — **this should
   be resolved before the pack goes GA.**
2. **Snapshot history begins at Sprint 1.** Backlog trends look short at go-live.
3. **SLA data depends on SLAs being configured.** Many customers do not use Dataverse SLA
   features, in which case SLA metrics must be derived from timestamps instead, or excluded.
4. **Omnichannel / conversation analytics are limited.** Session and conversation data
   depends on which Omnichannel tables the customer has and whether they surface through
   Link to Fabric. Deep conversation analytics is a roadmap candidate, not this pack.
5. **CSAT is not included** — it typically lives outside Dataverse. Blending it is
   additional development.
6. **Custom fields are not included.**

## Open questions for the first build

- Are Dataverse SLAs configured, or is SLA tracked another way?
- What are the customer's business hours, and do they vary by region or queue?
- Is `casetypecode` used meaningfully, or left at default?
- Does the customer use queues? Queue dwell time depends on it.
- How is "reopened" identified — a status reason, a custom field, or inferred from state
  transitions in snapshots?
- Is Omnichannel in use, and which channels?
