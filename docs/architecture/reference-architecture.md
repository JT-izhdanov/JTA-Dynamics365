# Reference architecture

## Layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ SOURCES                                                                     │
│   Dynamics 365 CE (Dataverse)        Other sources (optional, later)        │
│   ├─ Sales                            ├─ On-premises databases              │
│   ├─ Customer Service                 ├─ Cloud / SaaS app data              │
│   ├─ Project Operations               ├─ File data                          │
│   └─ Field Service                    └─ Streaming data                     │
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
│   Sales │ Customer Service │ Project Operations │ Field Service             │
│                    Revenue-to-Delivery (cross-app)                          │
│   Shared conformed dimensions · RLS applied · certified endorsement         │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────────────┐
│ REPORT LAYER              │  SELF-SERVICE LAYER                             │
│   Report packs per app    │    Power BI · Query in SQL · Analyze in Excel   │
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
| 3 | **Power BI semantic model layer** — shared, certified models | `packs/*/model/` |
| 4 | **Power BI report layer** — pre-built report packs | `packs/*/reports/` |

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
3. **Conformance before subject areas.** A pack may not define its own Date, Customer,
   Owner, or Currency dimension. It consumes the conformed ones. This is what makes
   cross-app analytics possible at all.
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

Separating platform from reporting keeps report consumers out of the engineering
workspace and makes Power BI app distribution straightforward. Both workspaces attach to
the same Fabric capacity.

## Constraints to check before every engagement

- **Region alignment.** The Fabric capacity and the Dataverse environment must be in
  compatible regions for Link to Fabric. Confirm before quoting, not during Sprint 1.
- **Fabric capacity.** A trial can start the build, but production needs a paid SKU. F64
  changes the Power BI licensing picture materially.
- **Which apps are installed.** Dataverse schema varies by installed solution. The pack
  set that can be delivered depends on what is actually there.
- **Project Operations deployment type.** See
  [ADR 0003](../decisions/0003-project-operations-scope.md). This one can silently drag
  Finance & Operations into scope.
- **Privileges.** Enabling Link to Fabric and creating Fabric workspaces need specific
  admin roles. See [`../delivery/prerequisites-and-access.md`](../delivery/prerequisites-and-access.md).

## Validation status

**Nothing in this repository has been validated against a live Dataverse environment.**

| Artifact class | Status | What validation requires |
|---|---|---|
| Architecture and design docs | Reviewed, not proven | First build confirms the shape holds |
| Source table mappings (`packs/*/source-tables.md`) | **Draft** | Confirm every table and column exists in a real environment at the customer's solution version |
| Notebooks (`platform/notebooks/`) | **Draft, never executed** | Run end to end in a JourneyTeam Dev environment |
| Metric definitions (`packs/*/metrics.yaml`) | **Draft** | Business review, then implementation in the model |
| Semantic models and reports | Not started | — |
| Microsoft licensing and pricing figures | **Must be re-verified** | See [`licensing-and-capacity.md`](licensing-and-capacity.md) |

Dataverse schema differs by solution version and by which apps are installed, so mappings
written from general knowledge will contain errors. Treat the first engagement — or better,
a JourneyTeam internal Dev environment — as the validation pass, and correct these files
from what is actually observed. Until then, items marked `<!-- VERIFY -->` in source files
are explicitly unconfirmed.

Per JourneyTeam change control, that validation happens in Dev or Sandbox. Never in
Production.
