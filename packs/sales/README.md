# Sales pack

**$5,000** · Dynamics 365 Sales · **Status: in build** (first in the build sequence)

## What it covers

Pipeline, forecasting, and sales performance analytics — including **point-in-time pipeline
history**, which Dataverse cannot provide and no first-party Dynamics 365 analytics offers.

| Area | Questions answered |
|---|---|
| Pipeline | What is in the pipeline, by stage, owner, territory, product? What did it look like on any past date? |
| Conversion | Win rate, loss reasons, lead-to-opportunity conversion |
| Velocity | Sales cycle length, time in stage, where deals stall |
| Forecast | Forecast vs. actual, slippage, coverage against target |
| Activity | Touches per opportunity, activity-to-outcome correlation |
| Performance | Attainment by owner, team, business unit, territory |

## Why this pack is first

Largest installed base, clearest metric set, and — most importantly — the **pipeline
snapshot proves the history capability the whole offering is differentiated on**. Getting
it right here de-risks every pack that follows.

## Files

| File | Purpose |
|---|---|
| [`source-tables.md`](source-tables.md) | Dataverse tables and columns consumed — **draft** |
| [`metrics.yaml`](metrics.yaml) | Metric definitions — **the source of truth** |
| `model/` | Semantic model — not yet built |
| `reports/` | Reports — not yet built |

## Depends on

- The full [conformance layer](../../docs/architecture/conformance-layer.md)
- [Conformed dimensions](../_shared/conformed-dimensions.md): `dim_date`, `dim_owner`,
  `dim_customer`, `dim_contact`, `dim_currency`, `dim_product`, `dim_territory`,
  `bridge_activity`, `lkp_choice_label`
- `fact_opportunity_snapshot` from
  [`30_silver_snapshot_facts.py`](../../platform/notebooks/30_silver_snapshot_facts.py)

`dim_customer`, `dim_contact`, `dim_product`, and `dim_territory` do not exist yet. This
pack's build creates them — **as conformed dimensions in Silver, not as pack-local
tables.** Every later pack depends on that being done correctly here.

## Known limitations

State these plainly; each is defensible in advance and damaging when discovered later.

1. **Snapshot history begins at Sprint 1 deployment.** Pipeline-as-of-date is only
   available from that day forward, and cannot be backfilled. Trends look short at go-live
   and lengthen over time.
2. **Forecast vs. actual depends on snapshot depth.** Comparing January's forecast to
   what closed requires January to have been captured.
3. **Time-in-stage is derived from snapshots**, so it is only as granular as the snapshot
   cadence — daily. Multiple stage changes within one day are not distinguishable.
4. **Custom fields are not included.** Standard schema only; custom columns are additional
   development.
5. **Loss reason analysis depends on the customer populating it.** Many do not, or use it
   inconsistently. Check during the first build rather than shipping an empty report page.
6. **Dynamics 365 Sales forecasting (the first-party forecast feature) is not consumed.**
   This pack derives forecast from opportunity data and snapshots.
   `<!-- VERIFY -->` Whether first-party forecast tables are available through Link to
   Fabric, and whether consuming them is worthwhile, is an open question for the first
   build.
7. **Territory analytics require territories to be in use.** Many customers leave
   `territoryid` unpopulated.

## Open questions for the first build

- Does the customer use business process flows for stages, or `salesstagecode`? The two
  can disagree, and the answer determines how stage analytics are built.
- Is `closeprobability` maintained, or left at defaults? Weighted pipeline is meaningless
  if it is not.
- Are opportunity products used, or are opportunities headline-value only? Product-level
  pipeline depends on it.
- How does the customer treat `Cancelled` — as a form of Lost, or genuinely separate? It
  changes win-rate denominators.

Each of these changes what the reports should show. Ask at kickoff, not at UAT.
