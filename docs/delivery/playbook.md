# Delivery playbook

> This is the **customer** delivery playbook. The first build, against JourneyTeam's own
> Dynamics 365 Sales system, is a different shape — one developer, validation-focused, and
> change-controlled as an internal JT Production change. It has its own plan:
> [`jtp-first-build-plan.md`](jtp-first-build-plan.md). The 6-week timeline below is
> predicated on that build having happened first.

**Three sprints, six weeks.** Assumes no additional customizations and no extra support
beyond the coaching hours in the purchased tier. Anything beyond the packaged scope is
additional development, quoted separately.

Faster than the Business Central edition's eight weeks because there is no extension to
build, register, and deploy — [ADR 0001](../decisions/0001-use-link-to-fabric-for-ingestion.md).

## Before Sprint 1 — preparation

Runs in parallel with contracting; does not consume sprint time.

- Project lead sends the welcome email and the access request list
  ([`prerequisites-and-access.md`](prerequisites-and-access.md))
- Customer creates accounts and grants access
- Customer confirms Fabric capacity status (trial or paid SKU) and **region alignment with
  the Dataverse environment**
- Project lead confirms which Dynamics 365 CE apps are installed, and for Project
  Operations, **which deployment type** ([ADR 0003](../decisions/0003-project-operations-scope.md))
- Project lead confirms readiness and schedules kickoff

**Do not start Sprint 1 without confirmed access and confirmed region alignment.** Both are
capable of stopping the engagement dead, and both are cheap to check beforehand.

---

## Sprint 1 (Weeks 1–2) — Access, kickoff, and platform foundation

### Kickoff call

- Introductions
- Scope, expectations, timeline
- Support plan and coaching hours
- Fabric capacity confirmation and sizing conversation
- **Set the history expectation:** snapshots begin now, history cannot be backfilled, and
  every day of delay is a day of history permanently lost. This is the most important
  thing said on the kickoff call
- **Set the security expectation:** Dataverse security does not follow data into Fabric.
  Agree the RLS pattern per pack ([`../architecture/security-and-rls.md`](../architecture/security-and-rls.md))
- Agree the fiscal calendar, base currency, language, and snapshot retention policy —
  these are configuration inputs, not assumptions
- Share sample report screenshots so the customer sees the destination

### Platform build

1. Create the `JTA-<Customer>-Platform` and `JTA-<Customer>-Reporting` workspaces
2. Enable **Link to Microsoft Fabric** for the required Dataverse tables
3. Confirm the Bronze shortcut has landed
4. Run `10_bronze_shortcut_validation` and **resolve every mapping discrepancy now**
5. Populate `platform/config/` for this customer from `customer.example.yaml`
6. Run the conformance notebooks (`20`–`23`) and validate outputs
7. **Deploy and schedule the snapshot job (`30`)** — daily, fixed UTC time
8. Run `40_gold_conformed_dimensions`
9. Configure monitoring and the snapshot completeness check

### Sprint 1 exit criteria

- [ ] Bronze validation passes with zero unresolved discrepancies
- [ ] Conformance layer built and spot-checked against Dynamics records
- [ ] **Snapshot job running on a schedule and verified to have written at least one day**
- [ ] Conformed dimensions published to Gold
- [ ] Customer configuration recorded and stored in the engagement's secure location
- [ ] RLS pattern agreed in writing per pack

The snapshot criterion is non-negotiable. Everything else can slip a few days and be
recovered; snapshot history cannot —
[`../architecture/snapshot-and-history.md`](../architecture/snapshot-and-history.md).

---

## Sprint 2 (Weeks 3–4) — Packs, models, and reports

For each purchased pack:

1. Build the pack's Silver layer
2. Build the pack's Gold star schema
3. Deploy the semantic model, implementing `packs/<pack>/metrics.yaml`
4. Apply and test RLS with named test users
5. Deploy the report pack and apply customer branding
6. Configure the semantic model refresh, orchestrated to follow Gold completion
7. Set up the Power BI app and workspace access
8. Reconcile headline metrics against Dynamics 365 — see below

### Metric reconciliation

**Every pack reconciles its headline metrics against the source app before UAT.** Open
pipeline total, case counts by status, work order counts by status — whatever the customer
will check first. A number that does not tie is the fastest way to lose confidence in the
whole platform, and it is nearly always a conformance issue (currency, status decoding,
time zone) rather than a report issue.

Document the reconciliation and any legitimate variances, with reasons, before UAT starts.
Walking into UAT with a known and explained variance is fine. Discovering one during UAT
is not.

### Sprint 2 exit criteria

- [ ] All purchased packs deployed and refreshing
- [ ] RLS validated with test users against expected row counts
- [ ] Headline metrics reconciled and documented
- [ ] Reports branded
- [ ] Customer branding and workspace access configured
- [ ] UAT plan shared with the customer

---

## Sprint 3 (Weeks 5–6) — UAT, training, and handoff

### UAT

- Present the solution with walkthrough training
- Customer conducts UAT against [`uat-plan.md`](uat-plan.md)
- Customer logs issues in an agreed single place
- JourneyTeam provides UAT support within the purchased coaching allotment
- Triage: defect (fix now), configuration (fix now), or change request (scope and quote)

**Triage discipline matters.** UAT is where fixed-price engagements lose margin, because
reasonable-sounding requests that are actually new scope get absorbed. Classify every item
explicitly and say which bucket it is in.

### Training and adoption

- End-user training per [`training-and-adoption.md`](training-and-adoption.md)
- Copilot enablement
- Self-service enablement: SQL endpoint and Analyze in Excel for the agreed audience

### Close

- Support transition per [`support-handoff.md`](support-handoff.md)
- Confirm snapshot job monitoring is owned going forward
- Document the conformance layer version deployed — needed for any future upgrade
- Close the project

### Sprint 3 exit criteria

- [ ] UAT signed off
- [ ] All defects resolved; change requests documented and quoted
- [ ] Training delivered and coaching hours accounted for
- [ ] Support handoff complete with monitoring ownership assigned
- [ ] Conformance layer version recorded

---

## Roles

| Role | Responsibility |
|---|---|
| Project lead | Schedule, communication, scope control, exit criteria |
| Data engineer | Link to Fabric, notebooks, medallion, snapshots, monitoring |
| BI developer | Semantic models, reports, RLS, reconciliation |
| Customer sponsor | Access, decisions, UAT participation |
| Customer data owner | Confirms metric definitions and reconciliation variances |

## Where engagements go wrong

Carried forward from the Business Central edition and from the risks in this architecture:

1. **Access delays.** The single most common cause of slippage. Start the access request
   before contracting completes.
2. **Snapshot started late.** Unrecoverable. Sprint 1 exit criterion for this reason.
3. **Region misalignment discovered in Sprint 1.** Qualify pre-sales.
4. **Project Operations F&O surprise.** See [ADR 0003](../decisions/0003-project-operations-scope.md).
5. **Numbers that do not tie.** Reconcile in Sprint 2, not in UAT.
6. **Security expectations.** Dataverse parity in Power BI is not achievable. Say so at
   kickoff.
7. **Scope creep in UAT.** Triage explicitly.
8. **Fabric capacity not procured.** A trial expiring mid-engagement stops delivery.
