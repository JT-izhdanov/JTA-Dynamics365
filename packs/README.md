# Report packs

One directory per pack. Each is a sellable component at $5,000 (Revenue-to-Delivery at
$7,500) — see [`../docs/offering/pricing-and-packaging.md`](../docs/offering/pricing-and-packaging.md).

| Pack | Dynamics 365 app | Status |
|---|---|---|
| [`sales/`](sales/) | Sales | In build |
| [`customer-service/`](customer-service/) | Customer Service | Planned |
| [`project-operations/`](project-operations/) | Project Operations | Planned — **scope gated**, see [ADR 0003](../docs/decisions/0003-project-operations-scope.md) |
| [`field-service/`](field-service/) | Field Service | Planned |
| [`revenue-to-delivery/`](revenue-to-delivery/) | cross-app | Planned — composed from the others |

Build order and GA gates: [`../docs/offering/roadmap.md`](../docs/offering/roadmap.md).
**Do not quote a pack that is not GA.**

## Structure of a pack

```
packs/<pack>/
├── README.md             What it covers, what it does not, known limitations
├── technical-design.md   How the pack is built — Silver/Gold design, model, RLS, build sequence
├── source-tables.md      Dataverse tables and columns consumed (DRAFT until validated)
├── metrics.yaml          Metric definitions — THE SOURCE OF TRUTH
├── model/                Power BI semantic model (see below)
└── reports/              Power BI reports (see below)
```

A pack gets its `technical-design.md` before implementation starts.
[`sales/technical-design.md`](sales/technical-design.md) is the reference example and the
template to follow — it covers scope and assumptions, the Bronze table set, Silver and Gold
table designs with grains and keys, the semantic model (storage mode, relationships,
measure patterns), RLS, report pages, orchestration, sizing, reconciliation, open
decisions, and a numbered build sequence.

## The rule that matters most

**A pack never defines its own conformed dimension.**

If Sales needs a Customer dimension, it consumes `dim_customer`. It does not create
`sales_dim_customer`. Same for Date, Owner, Currency, Product, Territory, Project, and
Resource — see [`_shared/conformed-dimensions.md`](_shared/conformed-dimensions.md).

This is what makes cross-app analytics possible at all: Revenue-to-Delivery works only
because Sales, Project Operations, and Field Service point at the *same* dimensions. It is
also the rule most likely to be broken under delivery pressure, when duplicating a
dimension looks like the fast fix. It is not — it is how the offering's main differentiator
gets quietly destroyed.

If a pack needs an attribute a conformed dimension lacks, **extend the conformed
dimension**. If two packs genuinely need incompatible versions of one, that is an
architecture question deserving an ADR.

## Metric definitions

`metrics.yaml` is the definition of record. The semantic model *implements* it; it does not
*define* it.

If the model and the YAML disagree, **the YAML is right and the model is a bug.**

Each metric carries:

```yaml
- name: Win Rate
  description: Share of closed opportunities that were won.
  grain: opportunity
  numerator: count of opportunities where conformed_status = 'Won'
  denominator: count of opportunities where conformed_status in ('Won', 'Lost')
  currency_basis: n/a          # base | transaction | n/a — see notebook 21's trap
  time_basis: actual_close_date
  business_hours: false        # true metrics need the holiday calendar (notebook 24 TODO)
  snapshot_dependent: false    # true = requires snapshot history
  notes: >
    Excludes cancelled opportunities. Confirm with the customer whether their process
    uses Cancelled meaningfully — some treat it as Lost.
```

`currency_basis`, `time_basis`, and `snapshot_dependent` are the fields that prevent the
three most common classes of wrong number. Fill them in on every metric, including the
obvious ones.

## Model and report artifacts

`model/` and `reports/` are landing zones. **Nothing is committed there yet** — the format
is a first-build decision.

**Intended:** Power BI Project format (PBIP) with TMDL, which is text-based and
diff-reviewable, so semantic models and reports can actually be code-reviewed and versioned.
Binary `.pbix` files defeat that and should not be committed.

Record the choice as an ADR once made, alongside the Fabric git integration decision
([`../platform/README.md`](../platform/README.md#future-fabric-git-integration)).

## Before a pack is GA

- [ ] `source-tables.md` validated against a live Dataverse environment
- [ ] `metrics.yaml` reviewed and signed off by the offering owner
- [ ] Semantic model implements every metric in `metrics.yaml`
- [ ] Conformed dimensions consumed, none duplicated
- [ ] RLS applied and tested fail-closed with named test users
- [ ] Headline metrics reconciled against the source app, variances documented
- [ ] Reports built and branded
- [ ] Known limitations written plainly into the pack README
- [ ] Delivered successfully at least once
