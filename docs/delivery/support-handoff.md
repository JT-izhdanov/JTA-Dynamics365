# Support handoff

The engagement ends here. This document makes the ending deliberate rather than an
absence.

## The gap this document sits in

**The offering currently has no post-go-live annuity.** Delivery ends at handoff, and every
customer will subsequently need model changes, new metrics, and support when something
breaks. There is no packaged way to sell that yet.

This is tracked as a known gap in
[`../offering/roadmap.md`](../offering/roadmap.md#known-gaps)
and is the largest untapped commercial opportunity in the offering. Until it is closed,
handoff is a hard boundary, and the conversation about what happens next needs to be had
explicitly rather than left to the customer to discover.

## Handoff checklist

### Operational ownership

- [ ] **Snapshot job monitoring owner named.** A snapshot job that stops silently loses
      history permanently and surfaces no error in any report. This is the single most
      important item on this list
- [ ] Refresh failure alerting routed to a named customer contact
- [ ] Fabric capacity monitoring and sizing ownership confirmed
- [ ] Escalation path agreed and documented

### Access and identity

- [ ] JourneyTeam delivery accounts removed or reduced to the agreed level
- [ ] App registration ownership transferred to the customer
- [ ] Workspace admin rights confirmed for the customer's named owners
- [ ] RLS role administration ownership confirmed

### Documentation delivered to the customer

- [ ] Architecture summary — what was deployed and where
- [ ] Sales pack documentation, including metric definitions
- [ ] Reconciliation results and any documented variances, with reasons
- [ ] RLS pattern implemented
- [ ] Refresh and snapshot schedules
- [ ] **Conformance layer version deployed** — required for any future upgrade
- [ ] Configuration values used (fiscal calendar, base currency, retention policy)
- [ ] Known limitations, stated plainly

### Commercial close

- [ ] Coaching hours consumed and remaining, recorded
- [ ] Change requests from UAT, documented and quoted
- [ ] Next-step recommendations (see below)
- [ ] 30-day check-in scheduled
- [ ] Reference conversation raised, if the engagement went well

## Known limitations to state plainly at handoff

Do not let these be discovered later. Each is legitimate and defensible when stated in
advance, and damaging when found independently.

1. **Snapshot history begins at Sprint 1.** Nothing earlier exists and it cannot be
   backfilled.
2. **RLS is not Dataverse parity.** The implemented pattern is documented; record-level
   sharing and field-level security are not replicated.
3. **The SQL endpoint bypasses semantic model RLS.** Whoever has it reads Gold unfiltered.
4. **The pack covers standard schema.** Custom tables and columns are not included.
5. **There is no automatic upgrade path.** If Microsoft changes Dataverse schema or the
   customer upgrades the Sales solution, the pack may need work, and that work is not
   pre-arranged.
6. **Only Dynamics 365 Sales is covered.** No other Dynamics app is in scope, and no
   packaged pack exists for one — see
   [`../offering/roadmap.md`](../offering/roadmap.md).
7. **Fabric capacity is the customer's to size and pay for**, and snapshot storage grows.

## Next-step recommendations

Handoff is the best-timed sales conversation in the engagement: the platform works, the
users are trained, and goodwill is at its peak.

| Opportunity | When it fits |
|---|---|
| **Additional coaching hours** | Power users are asking questions — the strongest signal of real adoption |
| **Additional data sources** | Customer has asked to see non-Dynamics data alongside this |
| **Custom reports or metrics** | UAT change requests already scoped and quoted |
| **Another edition** | Customer also runs Business Central or Finance & Operations. The platform is already paid for, making this the cheapest engagement they will ever buy from us |
| **Deeper RLS** | Complex hierarchy needs beyond the scaffold |
| **Custom development on the platform** | Additional Dataverse tables, other data sources, additional models. The landing zone exists; there is no second packaged pack to sell — see [`../offering/roadmap.md`](../offering/roadmap.md) |

The portfolio play is the one to lead with where it applies — see
[`../offering/positioning.md`](../offering/positioning.md#cross-sell-the-portfolio-play).

## 30-day check-in

Short, and worth doing on every engagement:

- Is the snapshot job still running? Any gaps?
- Are refreshes completing?
- Who is actually using the reports? Which ones?
- What are people asking for that the packs do not cover?
- Any numbers that stopped tying?

The answers are both service quality and pipeline. A customer whose snapshot job failed in
week two and who found out from JourneyTeam rather than from a wrong report will buy
again.
