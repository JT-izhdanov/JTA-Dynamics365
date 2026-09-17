# Report packs

**This repository covers the Dynamics 365 Sales pack only.** Other packs are deferred, and
cross-app functionality is still intended — see
[`../docs/offering/roadmap.md`](../docs/offering/roadmap.md#what-narrowing-costs-now-and-what-it-does-not)
for what is deliberately kept general so a second pack stays cheap to add.

| Pack | Dynamics 365 app | Status |
|---|---|---|
| [`sales/`](sales/) | Sales | **In build** |

## Structure

```
packs/
├── _shared/              Conformed dimensions — shared by construction, not by convention
└── sales/
    ├── README.md         What it covers, what it does not, known limitations
    ├── technical-design.md  How it is built — Silver/Gold design, model, RLS, build sequence
    ├── source-tables.md  Dataverse tables consumed
    ├── metrics.yaml      Metric definitions — THE SOURCE OF TRUTH
    ├── model/            Power BI semantic model (see below)
    └── reports/          Power BI reports (see below)
```

The `packs/<pack>/` nesting is kept with one pack in it deliberately. A second pack is
expected eventually; flattening now and re-nesting then is churn for one path segment.

## Conformed dimensions still matter with one pack

`_shared/conformed-dimensions.md` describes dimensions built **conformed** — one
`dim_date`, one `dim_owner`, one `dim_customer` — rather than Sales-local.

With a single pack that looks like over-engineering. It isn't, for two reasons:

1. **The conformance layer is the offering's IP.** Its value is that it is reusable, and
   reusability is decided when the dimension is built, not when a second consumer appears.
   A `sales_dim_customer` would have to be rebuilt — and a second pack that cannot point at
   the same `dim_customer` and `dim_owner` cannot be joined to this one at all, which is
   the whole cross-app premise.
2. **Snapshot history depends on it.** `dim_owner` is SCD2 so that historical pipeline is
   attributed to the owner at the time. That design has nothing to do with multiple packs
   and everything to do with correctness.

So: build them conformed, name them conformed, and do not prefix them `sales_`.

## Metric definitions

[`sales/metrics.yaml`](sales/metrics.yaml) is the definition of record. The semantic model
*implements* it; it does not *define* it. If the model and the YAML disagree, **the YAML is
right and the model is a bug.**

Each metric carries `currency_basis`, `time_basis`, `business_hours` and
`snapshot_dependent` — the four fields that prevent the most common classes of wrong
number. Fill them in on every metric, including the obvious ones.

## Model and report artifacts

`model/` and `reports/` are landing zones. **Nothing is committed there yet** — the format
is a first-build decision.

**Intended:** Power BI Project format (PBIP) with TMDL, which is text-based and
diff-reviewable, so models and reports can be code-reviewed and versioned. Binary `.pbix`
defeats that and should not be committed.

## Before the pack is GA

- [ ] `source-tables.md` corrected from [Bronze profiling](../docs/bronze-profiling/)
- [ ] `metrics.yaml` reviewed and signed off by the offering owner
- [ ] Semantic model implements every metric in `metrics.yaml`
- [ ] Dimensions built conformed, none prefixed `sales_`
- [ ] RLS applied and tested fail-closed with named test users
- [ ] Headline metrics reconciled against Dynamics, variances documented
- [ ] Reports built and branded
- [ ] Known limitations written plainly into the pack README
- [ ] Delivered successfully at least once
