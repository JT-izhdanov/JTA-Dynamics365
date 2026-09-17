# JourneyTeam Analytics for Dynamics 365 Sales

Everything concerning the **JourneyTeam Analytics for Dynamics 365 Sales** offering: the
commercial definition, the reference architecture, the reusable Fabric and Power BI IP,
and the delivery playbook used to deploy it into a customer tenant.

This is the Dynamics 365 Sales edition of the JourneyTeam Analytics portfolio. It is a
sibling to the Business Central edition and is designed to land in the same OneLake, so a
customer running both Dynamics families gets one analytics platform rather than two.

> **Repository scope: Dynamics 365 Sales only.** The offering was originally designed
> around four Customer Engagement report packs (Sales, Customer Service, Project
> Operations, Field Service) plus a cross-app pack. Those are **deferred** and no longer
> documented here — see [`docs/offering/roadmap.md`](docs/offering/roadmap.md) for what was
> removed and where to recover it from git history.

> **Internal JourneyTeam repository.** Contains offering pricing, margin logic, and
> delivery IP. Do not share outside JourneyTeam. Customer-specific configuration must
> never be committed here — see [Customer configuration](#customer-configuration).

## What the offering is

A packaged Microsoft Fabric and Power BI solution for Dynamics 365 Sales. Dataverse data is
shortcut into OneLake via **Link to Microsoft Fabric** (no ETL, no copy), refined through a
medallion architecture, and surfaced through a pre-built semantic model and report pack:

| Report pack | Dynamics 365 app | Status |
|---|---|---|
| Sales | Dynamics 365 Sales | **In build** |

Because ingestion is first-party and effectively free, **the defensible IP in this offering
is not ingestion.** It is the Silver conformance layer and the snapshot history model. See
[`docs/architecture/conformance-layer.md`](docs/architecture/conformance-layer.md).

## Repository layout

```
docs/
  offering/       Commercial definition — overview, positioning, pricing, roadmap
  architecture/   Reference architecture, medallion design, conformance layer, RLS, licensing
  decisions/      Architecture decision records (ADRs)
  delivery/       Prerequisites, sprint playbook, UAT, training, support handoff
  reference/      Analysis of existing artifacts that inform the offering
  bronze-profiling/  Per-entity profiles of Dataverse as Link to Fabric exports it
platform/
  notebooks/      Fabric notebooks — Bronze validation, Silver conformance, snapshots, Gold
  pipelines/      Fabric pipeline and scheduling definitions
  config/         Deployment configuration schema and example
packs/
  _shared/        Conformed dimensions and shared metric definitions
  sales/          Source table mapping, metric definitions, technical design, model, reports
sales-assets/     Customer-facing deck, one-pagers, demo script
```

## Start here

| If you are... | Read |
|---|---|
| Selling this | [`docs/offering/overview.md`](docs/offering/overview.md), [`pricing-and-packaging.md`](docs/offering/pricing-and-packaging.md), [`positioning.md`](docs/offering/positioning.md) |
| Scoping an engagement | [`docs/delivery/prerequisites-and-access.md`](docs/delivery/prerequisites-and-access.md) |
| Delivering an engagement | [`docs/delivery/playbook.md`](docs/delivery/playbook.md) |
| Working on the JTP first build | [`docs/delivery/jtp-first-build-plan.md`](docs/delivery/jtp-first-build-plan.md) |
| Building or extending the IP | [`docs/architecture/reference-architecture.md`](docs/architecture/reference-architecture.md), [`platform/README.md`](platform/README.md) |
| Mapping a Dataverse entity | [`docs/bronze-profiling/`](docs/bronze-profiling/) — what is **actually** in the export |
| Building the report pack | [`packs/README.md`](packs/README.md), [`packs/sales/technical-design.md`](packs/sales/technical-design.md) |

## Working against Fabric

`.mcp.json` registers Microsoft's Fabric MCP server for this repository, so a **local**
Claude Code session opened here has both the repo and Fabric in one place — which the
hosted/web sessions cannot, because their egress policy blocks the Fabric endpoints.

```bash
git clone https://github.com/JT-izhdanov/JTA-Dynamics365 && cd JTA-Dynamics365
az login --tenant <tenant-id>     # or: az login --service-principal -u <appId> -p "$SECRET" --tenant <tenant-id>
claude
```

Requires Node.js and the Azure CLI. The MCP server uses the Azure identity chain, so
whatever `az` is signed in as is what it acts as.

Two things to know:

- **`DefaultAzureCredential` reads environment variables before the Azure CLI.** A stale
  `AZURE_CLIENT_ID` / `AZURE_TENANT_ID` / `AZURE_CLIENT_SECRET` in your shell silently wins
  over your `az login`. Check with `env | grep -i AZURE` if the server authenticates as
  something unexpected.
- **Prefer a service principal over a personal sign-in** for anything touching a
  production workspace — a personal token is tenant-wide, carries your full permission set
  into every workspace you can reach, and attributes every agent action to you in the audit
  log. See [`docs/delivery/jtp-first-build-plan.md`](docs/delivery/jtp-first-build-plan.md)
  for the setup and its change-control route.

**On Windows, skip `az … --query`.** PowerShell mangles JMESPath strings containing `?`,
`|`, `[]` and quotes. Pipe to `ConvertFrom-Json` and filter in PowerShell instead.

Workspace and capacity IDs are **not** recorded in this repository — see `CLAUDE.md`. Pass
them per session. The deployed layer topology (without identifiers) is in
[`docs/architecture/jt-medallion-topology.md`](docs/architecture/jt-medallion-topology.md).

## Status

The offering is in **definition and initial build**. Nothing in `platform/` or `packs/` has
been validated against a live Dataverse environment yet. Every source table mapping and
notebook in this repository is a **draft pending first-build validation** — see
[Validation status](docs/architecture/reference-architecture.md#validation-status) for what
that means and what has to happen before customer delivery.

## Customer configuration

Deployment is parameterized per customer. `platform/config/customer.example.yaml` is the
template; real customer configuration lives in the engagement's own secure location, never
in this repository. No tenant IDs, workspace IDs, environment URLs, connection strings,
secrets, or customer data belong in any commit here.

## Contributing

- One change per pull request, scoped to a single concern.
- Architectural or commercial choices get an ADR in `docs/decisions/` — see that folder's README.
- Changes to pricing, packaging, or the competitive comparison require offering-owner sign-off.
- Keep `CHANGELOG.md` current for anything that changes what gets delivered to a customer.
