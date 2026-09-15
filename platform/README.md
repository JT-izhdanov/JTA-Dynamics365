# Platform

The reusable Fabric IP: notebooks that build the Silver conformance layer, snapshot facts,
and Gold conformed dimensions on top of the Link to Fabric Bronze shortcut.

> **Nothing here has been executed.** Every notebook is an authoring draft written from
> general Dataverse knowledge, not from a validated environment. Dataverse schema varies by
> solution version and installed apps, so these contain errors. They are a starting point
> for the first build, not a deployable artifact. See
> [Validation status](../docs/architecture/reference-architecture.md#validation-status).

## Layout

```
platform/
├── notebooks/     Fabric notebooks, numbered by medallion stage
├── pipelines/     Orchestration and scheduling definitions
└── config/        Per-customer configuration schema and example
```

## Read first

| Document | Why |
|---|---|
| [`../docs/architecture/conformance-layer.md`](../docs/architecture/conformance-layer.md) | What these notebooks are solving and why it is the IP |
| [`../docs/architecture/medallion-design.md`](../docs/architecture/medallion-design.md) | Schema layout, naming, orchestration order |
| [`../docs/architecture/snapshot-and-history.md`](../docs/architecture/snapshot-and-history.md) | Why snapshots run from day one |
| [`notebooks/README.md`](notebooks/README.md) | Authoring conventions |

## Non-negotiable rules

1. **Never write to Bronze.** It is the Link to Fabric shortcut — Microsoft-managed and
   read-only. All JourneyTeam logic must be reproducible from Bronze by re-running
   notebooks, so that recreating the shortcut loses nothing.
2. **Nothing is hard-coded per customer.** Environment identifiers, fiscal calendar,
   language, base currency, table selection, retention — all configuration. See
   [`config/`](config/).
3. **Validation gates the run.** If `10_bronze_shortcut_validation` fails, nothing
   downstream executes.
4. **Snapshots are append-only and run daily regardless.** A lost Gold rebuild costs a
   rerun; a lost snapshot day is gone permanently.
5. **Everything except snapshot appends is idempotent.**
6. **No secrets, tenant IDs, workspace IDs, environment URLs, or customer data** in any
   file here — including notebook output. Notebooks are committed with output cleared.

## Getting the first build right

The first engagement (or better, a JourneyTeam internal Dev environment) is the validation
pass. Expect to correct these notebooks and the pack source mappings from what is actually
observed, and commit those corrections — that is how this becomes real IP rather than a
sketch.

Work through it in this order:

1. Enable Link to Fabric and confirm Bronze lands.
2. Run `10_bronze_shortcut_validation`. **Expect failures.** Every one is a mapping
   correction to make in `packs/*/source-tables.md`.
3. Resolve the `<!-- VERIFY -->` items — particularly how choice-label metadata is actually
   exposed, which determines the shape of `20_silver_conformance_choice_labels`.
4. Build conformance notebooks one at a time, spot-checking output against real Dynamics
   records.
5. Get the snapshot job scheduled before doing anything else.
6. Only then move to Gold and packs.

Per JourneyTeam change control, all of this happens in Dev or Sandbox — never directly in
Production, and never in a customer's Production environment outside their own change
process.

## Future: Fabric git integration

These notebooks are plain `.py` authoring drafts. Fabric's git integration stores notebooks
in its own folder format (a `.Notebook` directory containing `notebook-content.py` with
cell markers).

Once the first build stabilizes, migrate to Fabric git integration so the workspace and
this repository stay in sync automatically. Until then, notebooks are imported into Fabric
manually and this repository is the source of truth. Do not mix the two conventions —
decide, and record it as an ADR.
