# Bronze samples

Structurally faithful, **de-identified** samples of Bronze tables, for developing and
testing the platform notebooks without touching real data.

| Sample | Generator | Rows | Columns |
|---|---|---|---|
| [`opportunity.sample.tsv`](opportunity.sample.tsv) | [`generate_opportunity_sample.py`](generate_opportunity_sample.py) | 12 | 343 |

## These are synthesised, not masked

The generators take **no real data as input**. They encode the *patterns* recorded in the
profiles (`../opportunity.md`) and emit rows matching them. Re-running a generator cannot
leak anything, because there is nothing real inside it.

That is deliberate. Masking a real export leaves you reasoning about whether the masking
was complete — on a 343-column table with long free-text fields containing pasted email
threads, phone numbers and SharePoint URLs, that is not a question worth betting on.
Synthesising from a documented profile removes the question.

## Why a sample is committable and the export is not

The real JTP `opportunity` export contains customer and account names, employee names,
deal values, customer contact phone numbers and email addresses, SharePoint URLs, and
record GUIDs. Git history is permanent and this repository is pushed to GitHub, so a
commit cannot be withdrawn — and `CLAUDE.md` prohibits committing customer data.

What the build actually needs from a sample is the **shape**. All of it survives
de-identification.

**The real export belongs in the engagement's own controlled location** — the sales
operations or delivery SharePoint site, under its existing access controls — referenced
from a profile by name and date, never committed here.

## What is faithful

- Column names and exact column **order**, as exported
- Every `<lookup>` / `<lookup>_entitytype` pair, with the real entity type names
  (`account`, `contact`, `systemuser`, `lead`, `campaign`, `bookableresource`, …)
- **Raw choice integers exactly as observed** — `206360xxx`, `100000xxx`, `192350001`,
  `299600000`. These are real option values and are not confidential
- `jt_interests` as a semicolon-delimited multi-select
- Money as `_txn` / `_base` pairs, base equal to txn (single-currency org)
- NULL density per column, including the legacy-row pattern where every `jt_*` column is NULL
- `PartitionId` = `createdon` year · `IsDelete` · the `Sink*` columns
- Rollup `_date` / `_state` companion columns

## What is not

- All GUIDs are synthetic but internally consistent — the same account referenced twice
  gets the same GUID
- Names are placeholders: `Account R01`, `Rep A`, `Presales B`, `Contact R03`
- Money values are invented and rounded
- Dates are invented but internally consistent (close after create, partition matches year)
- Long free text is replaced with a marker recording the observed length class, e.g.
  `<long-text-redacted:~1200chars-with-newlines>`

**One deliberate divergence:** real values in the long-text columns contain embedded
newlines, so a real export of this table is *not* line-delimited. The sample contains no
newlines, so it stays valid TSV. Anything that parses a real export must handle this —
it is recorded in [`../opportunity.md` §3.11](../opportunity.md#311-long-free-text--a-model-size-and-parsing-problem).

## Shapes covered by `opportunity.sample.tsv`

Chosen so the notebooks meet every case that needs handling:

| Row | Shape |
|---|---|
| R01 | Open, single practice, forecast category populated |
| R02 | Open, **three practices** in `jt_interests` |
| R03 | Open, **two practices** |
| R04 | **Won** — `actualvalue` populated, `msdyn_forecastcategory` = won |
| R05 | **Lost with a JT custom `statuscode`** (loss reason) |
| R06 | Closed with **OOB `statuscode` = 4** (Canceled) under the same `statecode` = 2 |
| R07 | Open, **Microsoft co-sell** sourced |
| R08 | **`customerid_entitytype` = `contact`** — exercises polymorphism |
| R09 | **Test data in production** — exercises the exclusion filter |
| R10 | **`IsDelete` = 1** — exercises the soft-delete filter |
| R11–R12 | **Pre-cutover legacy** — every `jt_*` column NULL, legacy probability range, old `PartitionId` |

R08's contact-party shape was **not observed** in the profiled rows (all were `account`)
but is included because the schema permits it and D10 depends on it.

## Regenerating

```bash
cd docs/bronze-profiling/samples
python3 generate_opportunity_sample.py > opportunity.sample.tsv
```

No dependencies beyond the standard library. The generator asserts row width and rejects
any value containing a tab or newline, so a malformed sample fails loudly.

## Adding a sample for a new entity

1. Profile the entity first — the generator encodes the profile, so the profile comes first.
2. Copy the generator pattern: header list, a `row()` builder defaulting everything to
   NULL, and one function per row archetype.
3. Cover the shapes that need *handling*, not a representative distribution. A soft-deleted
   row and a legacy row matter more than ten typical ones.
4. Keep the width and tab/newline assertions.
5. Add the entity to the table at the top of this file and to `../README.md`.
