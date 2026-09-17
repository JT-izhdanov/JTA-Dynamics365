# Configuration

Per-customer deployment configuration. **This is what makes delivery repeatable** — every
notebook in [`../notebooks/`](../notebooks/) reads from here, and nothing is hard-coded
per customer.

## Files

| File | Purpose |
|---|---|
| `customer.example.yaml` | Template. Placeholders only |

## Rules

1. **A real customer's configuration never lives in this repository.** Copy the template
   per engagement and store it in the engagement's own secure location.
2. **No identifiers or secrets, ever** — not in the template, not as examples, not in a
   comment. No tenant IDs, environment URLs, workspace IDs, app registration IDs,
   connection strings, or credentials. These are supplied at deployment time from the
   engagement's secure store.
3. **No customer data.** Not in configs, not in notebook output, not in screenshots.
4. **If a notebook needs a new per-customer value, it goes here** — never inline. The
   first time a value is hard-coded in a notebook, repeatable delivery starts eroding.

## Values that must be confirmed at kickoff

These are not inferable and cannot be assumed. Each appears on the kickoff agenda in
[`../../docs/delivery/playbook.md`](../../docs/delivery/playbook.md):

| Value | Why it cannot be assumed |
|---|---|
| Fiscal year start month | A calendar-year dimension is useless to a June-close business |
| Fiscal year naming (`starting` / `ending`) | A July-start FY spanning 2025–26 is "FY2025" to some organizations and "FY2026" to others. Both are common |
| Base currency and whether multi-currency | Notebook 21 fails the run if the config contradicts the data, because silently mixed currencies look plausible |
| Business unit depth | A fixed assumption truncates deep hierarchies |
| Manager chain availability | Many customers do not maintain `parentsystemuserid`, which makes manager-based RLS unviable |
| Reporting time zone | Dataverse stores UTC; wrong handling shifts activity into the wrong day |
| RLS pattern | Dataverse parity is not achievable — agree the pattern explicitly |
| Snapshot retention | The one recurring storage cost the architecture adds |
| SQL endpoint audience | It bypasses semantic model RLS |

## Table lists

`tables.required`, `tables.optional`, `tables.columns`, and `tables.choice_columns` are
assembled from `packs/sales/source-tables.md` plus the conformance layer's
own needs.

They are **drafts** until validated. Notebook 10 gates the run on them, and during the
first build its failures are the correction list — fix `packs/*/source-tables.md` from what
is actually observed and commit it. That feedback loop is how these files become real IP
rather than assumptions.

## Future: schema validation

A JSON Schema for this file would catch configuration errors before a notebook run rather
than during one. Worth adding once the shape settles after the first build — premature now,
because the shape will change.
