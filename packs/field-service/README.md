# Field Service pack

**$5,000** · Dynamics 365 Field Service · **Status: planned** (fifth in the build sequence)

## What it covers

| Area | Questions answered |
|---|---|
| Throughput | Work orders created, completed, and open, by type and priority |
| Efficiency | First-time fix rate, travel vs. on-site time, repeat visits |
| Resourcing | Technician utilization, booking adherence, overtime |
| Service levels | Appointment and SLA adherence, response time |
| Preventive maintenance | Agreement compliance, PM completion |
| Assets | Cost by asset, failure patterns, warranty exposure |
| Backlog | Open work order backlog over time, awaiting-parts trend |

## Be honest about the competitive position

Like Customer Service, **Field Service ships respectable first-party embedded analytics.**
Differentiate on what they cannot do: custom fields, cross-app (work orders alongside the
sales and project history that generated them), unlimited history, blended external data
(telematics, IoT, parts systems), full drill-down, and customer ownership of the model.

## Why fifth in the build sequence

Rich data, but the smallest installed base of the four packs and the **most variation
between customers** in how work orders are actually used. Building it after the others
means the conformance layer and snapshot framework are already proven, leaving only the
domain variability to solve.

## Depends on

- The full [conformance layer](../../docs/architecture/conformance-layer.md)
- [Conformed dimensions](../_shared/conformed-dimensions.md): `dim_date`, `dim_owner`,
  `dim_customer`, `dim_currency`, `dim_product`, `dim_territory`, `bridge_activity`
- **`dim_resource`** — created by the Project Operations pack build and shared. If Field
  Service is delivered without Project Operations, this pack creates it, still as a
  **conformed** dimension
- `fact_workorder_snapshot`

## Known limitations

1. **Work order vs. booking grain must be resolved per customer.** One work order can have
   many bookings (multiple visits, multiple technicians). Metrics measured at the wrong
   grain double-count. This is the pack's main modeling risk — see
   [`source-tables.md`](source-tables.md#the-grain-problem).
2. **First-time fix rate has no universal definition.** It depends on how the customer uses
   bookings and resolution fields, and must be agreed explicitly.
3. **Travel vs. on-site time requires booking timestamps to be maintained.** If technicians
   do not update booking status in the field, this metric is not viable.
4. **Business-hours metrics are calendar-hours until the holiday calendar exists** — see
   the TODO in [notebook 24](../../platform/notebooks/24_silver_conformance_date.py).
5. **IoT and telematics data are not included.** Blending them is additional development.
6. **Inspections data availability varies by version.** `VERIFY` per engagement.
7. **Snapshot history begins at Sprint 1.**
8. **Custom fields are not included.**

## Open questions for the first build

- Does the customer measure at work order or booking grain?
- How is "first-time fix" defined in their business?
- Are booking statuses maintained in the field reliably enough for travel/on-site split?
- Are agreements (preventive maintenance) used?
- Are customer assets tracked, and is the asset hierarchy maintained?
- Are inspections used?
- Is `msdyn_systemstatus` or `statecode` the meaningful lifecycle column for their process?
