# Reference architecture

## Layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ SOURCES                                                                     │
│   Dynamics 365 Sales (Dataverse)     Other sources (optional, later)        │
│                                       ├─ On-premises databases              │
│   Targets, quota and goal data        ├─ Cloud / SaaS app data              │
│   (spreadsheet today — see            ├─ File data                          │
│    packs/sales/technical-design.md)   └─ Streaming data                     │
└──────────────┬──────────────────────────────────┬───────────────────────────┘
               │                                  │
     Link to Microsoft Fabric              Fabric pipelines /
     (first-party, zero-copy shortcut)     shortcuts / eventstreams
               │                                  │
┌──────────────▼──────────────────────────────────▼───────────────────────────┐
│ MICROSOFT FABRIC — OneLake                                                  │
│                                                                             │
│  BRONZE            SILVER                        GOLD                       │
│  Raw shortcut  →   Conformed + historized    →   Business-ready             │
│  Dataverse         • choice labels resolved      • conformed dimensions     │
│  tables, as-is     • currency normalized         • subject-area fact tables │
│  (no copy)         • ownership flattened         • aggregated for BI        │
│                    • state/status decoded                                   │
│                    • daily snapshot facts                                   │
│                    • SCD2 on key dimensions                                 │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────────────┐
│ SEMANTIC LAYER — Power BI                                                   │
│   Sales                                                                     │
│   Conformed dimensions · RLS applied · certified endorsement                │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────────────┐
│ REPORT LAYER              │  SELF-SERVICE LAYER                             │
│   Sales report pack       │    Power BI · Query in SQL · Analyze in Excel   │
│   Dashboards · Metrics    │    Copilot                                      │
│   Paginated · Embedded    │                                                 │
│   in-app (D365)           │                                                 │
└───────────────────────────┴─────────────────────────────────────────────────┘
```

## The four numbered components (sales narrative)

The customer-facing deck walks these in order. They map to this repository as follows.

| # | Component | Repo location |
|---|---|---|
| 1 | **Link to Microsoft Fabric** — Dataverse into OneLake, no ETL | [`ingestion-link-to-fabric.md`](ingestion-link-to-fabric.md) |
| 2 | **Medallion data architecture** — Bronze / Silver / Gold | [`medallion-design.md`](medallion-design.md), [`conformance-layer.md`](conformance-layer.md) |
| 3 | **Power BI semantic model layer** — conformed, certified model | `packs/sales/model/` |
| 4 | **Power BI report layer** — the pre-built report pack | `packs/sales/reports/` |

Note the difference from the Business Central edition, where component 1 is a custom AL
extension that JourneyTeam builds and maintains. Here it is a first-party feature. That
makes component 1 nearly free to deliver — and means components 2 through 4 carry all the
differentiation.

## Design principles

1. **Never transform in Bronze.** Bronze is the Link to Fabric shortcut. It is read-only,
   Microsoft-managed, and must stay untouched so the shortcut can be recreated at any time
   without losing work.
2. **All IP lives in Silver and Gold.** Everything JourneyTeam adds is reproducible from
   Bronze by re-running notebooks.
3. **Conformance before subject areas.** The pack may not define its own Date, Customer,
   Owner, or Currency dimension. It consumes the conformed ones. With one pack this looks
   like over-engineering; it is not — the conformance layer is the offering's IP, and
   reusability is decided when a dimension is built, not when a second consumer appears.
   See [`../../packs/README.md`](../../packs/README.md#conformed-dimensions-still-matter-with-one-pack).
4. **Snapshot early.** Snapshot facts start accumulating on day one of the engagement, not
   at go-live. History cannot be backfilled from a current-state source, so a day not
   captured is a day lost forever.
5. **Metrics are defined in YAML, implemented in the model.** `packs/<pack>/metrics.yaml`
   is the definition of record. If the model and the YAML disagree, the YAML is right and
   the model is a bug.
6. **Everything is parameterized per customer.** No environment identifier, workspace
   name, or table selection is hard-coded in a notebook. See `platform/config/`.
7. **Prefer first-party.** Where Microsoft ships a capability, use it rather than building
   one. That is what keeps delivery cheap and the maintenance burden on Microsoft.

## Deployment topology per customer

| Fabric item | Purpose | Naming convention |
|---|---|---|
| Workspace (platform) | Lakehouse, notebooks, pipelines | `JTA-<Customer>-Platform` |
| Workspace (reporting) | Semantic models, reports, apps | `JTA-<Customer>-Reporting` |
| Lakehouse | Bronze shortcut, Silver, Gold schemas | `jta_lakehouse` |

**JourneyTeam's own deployment does not follow this.** It uses three lakehouses across two
workspaces — see [`jt-medallion-topology.md`](jt-medallion-topology.md), which also carries
the open question of which shape the product should ship.

Separating platform from reporting keeps report consumers out of the engineering
workspace and makes Power BI app distribution straightforward. Both workspaces attach to
the same Fabric capacity.

## Constraints to check before every engagement

- **Region alignment.** The Fabric capacity and the Dataverse environment must be in
  compatible regions for Link to Fabric. Confirm before quoting, not during Sprint 1.
- **Fabric capacity.** A trial can start the build, but production needs a paid SKU. F64
  changes the Power BI licensing picture materially.
- **Dynamics 365 Sales solution version and customizations.** Dataverse schema varies by
  solution version and by customization. Custom tables and columns are explicitly outside
  the fixed price — see
  [`../offering/pricing-and-packaging.md`](../offering/pricing-and-packaging.md).
- **Privileges.** Enabling Link to Fabric and creating Fabric workspaces need specific
  admin roles. See [`../delivery/prerequisites-and-access.md`](../delivery/prerequisites-and-access.md).

## Validation status

**Nothing in this repository has been validated against a live Dataverse environment.**

| Artifact class | Status | What validation requires |
|---|---|---|
| Architecture and design docs | Reviewed, not proven | First build confirms the shape holds |
| Source table mappings (`packs/sales/source-tables.md`) | **Draft** | Confirm every table and column exists in a real environment at the customer's solution version |
| Notebooks (`platform/notebooks/`) | **Draft, never executed** | Run end to end in a JourneyTeam Dev environment |
| Metric definitions (`packs/sales/metrics.yaml`) | **Draft** | Business review, then implementation in the model |
| Semantic models and reports | Not started | — |
| Microsoft licensing and pricing figures | **Must be re-verified** | See [`licensing-and-capacity.md`](licensing-and-capacity.md) |

Dataverse schema differs by solution version and by customization, so mappings written from
general knowledge will contain errors — the `opportunity` profile in
[`../bronze-profiling/opportunity.md`](../bronze-profiling/opportunity.md) is the worked
example of how far off they can be. Treat the first engagement — or better,
a JourneyTeam internal Dev environment — as the validation pass, and correct these files
from what is actually observed. Until then, items marked `<!-- VERIFY -->` in source files
are explicitly unconfirmed.

Per JourneyTeam change control, that validation happens in Dev or Sandbox. Never in
Production.
