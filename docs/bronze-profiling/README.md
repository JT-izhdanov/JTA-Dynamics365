# Bronze data profiling

Per-entity profiles of Dataverse tables **as Link to Fabric actually exports them**,
observed against a live environment.

This folder is the evidence layer beneath the pack design. `packs/*/source-tables.md` says
what a pack *consumes*; these profiles say what is *actually there* — column inventory,
observed choice values, NULL patterns, platform quirks, data quality issues, and the
findings that change the design.

## Profiled entities

| Entity | Profile | Sample | Status |
|---|---|---|---|
| `opportunity` | [`opportunity.md`](opportunity.md) | [`samples/opportunity.sample.tsv`](samples/opportunity.sample.tsv) | Observed; fill rates outstanding |

Next, in order: `opportunityproduct` (now load-bearing — see
[`opportunity.md` §5.1](opportunity.md#51-opportunity-products-are-the-revenue-source)),
then `systemuser` (to resolve the Team question), then `lead`, `account`, `contact`.

## Platform patterns confirmed so far

These apply to every Dataverse entity, not just Sales. Recorded once here so each new
profile does not re-derive them.

| Pattern | Detail |
|---|---|
| **Sink columns** | `Id` · `SinkCreatedOn` · `SinkModifiedOn` · `PartitionId` · `IsDelete` · `versionnumber` · `msft_datastate` |
| **`PartitionId`** | The `createdon` **year**. The cheap filter; full-history queries scan every partition |
| **`IsDelete`** | Soft-delete flag. **Must be filtered on every Bronze read** |
| **Lookups** | Arrive as `<column>` + **`<column>_entitytype`** pairs — polymorphism resolved inline, no `TargetMetadata` join needed |
| **Lookup labels** | Arrive denormalized as `<column>name` (and a NULL `…yominame` twin). Free labels; no hierarchy |
| **Choices** | **Raw integers, no labels.** `OptionsetMetadata` remains a hard prerequisite |
| **Money** | `_txn` / `_base` column pairs throughout |
| **Rollup fields** | Ship with `_date` (last calculated) and `_state` twins — rollup staleness is detectable |

## Why profile before building

Every mapping in `packs/*/source-tables.md` was written from general Dataverse knowledge.
Profiling is how those drafts become fact. On `opportunity` it changed four design
decisions and surfaced eleven data quality issues that would otherwise have been found in
UAT — including a whole class of dimension that does not exist for most of the history.

Profiling is cheap: read-only, no change control beyond least-privilege read access.
Reworking a semantic model is not.

## Method

1. Export or query the entity from Bronze. **Read-only** — profiling never writes.
2. Record the **full column inventory** grouped by role, with what is populated and what
   is dead.
3. Record **observed choice integers** per column. Labels need `OptionsetMetadata`, so the
   integers are what a profile can honestly state.
4. Note the **platform quirks** — anything Link to Fabric adds or reshapes.
5. Separate **findings that change the design** from **data quality issues**.
6. List what still needs **full-table measurement**. A sampled read cannot establish a
   fill rate; say so rather than implying coverage.
7. Generate a **de-identified sample** (see [`samples/README.md`](samples/README.md)).
8. Feed the corrections back into `packs/*/source-tables.md` and the technical design.

## Rules

1. **No real data in this folder.** Profiles record structure, observed choice integers,
   counts and patterns — never customer names, employee names, deal values, contact
   details, URLs or record GUIDs. Samples are synthesised, not masked exports
   ([`samples/README.md`](samples/README.md)).
2. **Distinguish observed from assumed.** If a claim comes from a 20-row read, say so.
   `<!-- VERIFY -->` marks anything unconfirmed.
3. **Integers, not guessed labels.** Never invent a label for a choice value.
4. **Every profile ends with what is still unmeasured.** A profile that implies
   completeness it does not have is worse than a short one.
5. **Findings flow outward.** A profile that changes a design decision must be
   cross-referenced from the document it changes, or the finding is lost.
