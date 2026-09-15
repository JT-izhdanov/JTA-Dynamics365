# The Dataverse conformance layer

**This is the offering's core IP.** Read this before building anything in `platform/` or
`packs/`.

## Why it exists

Link to Microsoft Fabric is first-party, free, and takes minutes. Any partner can enable
it. So ingestion cannot be what JourneyTeam sells.

What Link to Fabric delivers is *raw Dataverse*, and raw Dataverse is hostile to BI in
consistent, well-known, repeatable ways. Every customer hits the same problems. Solving
them once — as versioned, parameterized, reusable notebooks — is the product.

A customer who enables Link to Fabric themselves gets a lakehouse full of tables where
status is an integer, currency is ambiguous, and yesterday is unknowable. The conformance
layer is the distance between that and an answer.

## The problems it solves

### 1. Choice / option-set labels

Dataverse stores choices as integers. `opportunity.statuscode = 3` is meaningless in a
report. The labels live in metadata, not in the data table.

**Approach:** resolve integers to labels from the metadata tables that Link to Fabric
surfaces, producing a single conformed choice-label lookup keyed by table, column, and
value, for the appropriate language. Every Silver table joins to it rather than hard-coding
`CASE` statements.

**Why this matters commercially:** it is the first thing a customer notices and the first
thing they cannot fix themselves cleanly. Hard-coded `CASE` mappings are how most in-house
attempts start and why they become unmaintainable.

> `<!-- VERIFY -->` The exact metadata table names and shapes exposed by Link to Fabric
> must be confirmed against a live environment. Synapse Link for Dataverse exposed
> `OptionsetMetadata` and `GlobalOptionsetMetadata`; Dataverse also has a `stringmap`
> table. Which of these is available, and in what form, is a first-build validation item.
> Do not assume the Synapse Link shape carries over unchanged.

### 2. Currency normalization

Dataverse stores money in two forms: the transaction currency and the organization's base
currency, with the rate captured per record at write time. Reporting across currencies
without understanding this produces wrong numbers that look plausible.

**Approach:** expose both transaction and base amounts explicitly, name them
unambiguously, join `transactioncurrency` for codes and symbols, and document which the
report packs use by default (base, unless a report is explicitly about a single market).
Never silently convert.

**Trap:** the rate on the record is the rate at write time, not today's rate. That is
usually correct for financial reporting and usually wrong for pipeline comparison. The
choice must be deliberate and documented per metric in `metrics.yaml`.

### 3. Polymorphic activities

`activitypointer` is the base table for all activity types, and `regardingobjectid` points
at *any* table — Lead, Opportunity, Case, Work Order. There is no clean foreign key.

**Approach:** resolve `regardingobjectid` plus its type discriminator into an explicit
bridge with one row per activity and one typed key column per target entity. Downstream
models then join activities to the subject area without re-solving polymorphism.

Activity analytics — touches per opportunity, response time on a case — is one of the
highest-value question sets and one of the most annoying to build. Doing it once is worth
disproportionately more than it costs.

### 4. State versus status

Dataverse has two related columns on most tables: `statecode` (the coarse lifecycle state)
and `statuscode` (the specific reason within it). Their meaning differs per table, and
using one without the other is a common source of wrong counts — an Opportunity that is
`statecode = 1` (Won) is a very different claim from one that is merely closed.

**Approach:** decode both, keep both, and add an explicit conformed status grouping per
table (`Open` / `Won` / `Lost` / `Cancelled` and equivalents) so cross-app reports can
reason about lifecycle consistently. Never expose the raw integers to the semantic model.

### 5. Ownership hierarchy

Records are owned by a user or a team; users and teams sit in business units, which are
hierarchical. This hierarchy is both a reporting dimension (performance by region or
manager) and the source of the security model.

**Approach:** flatten `systemuser`, `team`, and `businessunit` into a conformed Owner
dimension with the business unit path resolved to fixed levels, plus a manager hierarchy
where `parentsystemuserid` is populated. This one artifact serves both the reporting
dimension and the RLS rules — see [`security-and-rls.md`](security-and-rls.md).

### 6. Soft deletes and current-state-only storage

Dataverse is a current-state store. A record that is updated overwrites its prior values,
and depending on configuration, deletion may or may not be visible downstream.

**Approach:** SCD2 on key dimensions and daily snapshot facts, so change is observable.
This is important enough that it has its own document —
[`snapshot-and-history.md`](snapshot-and-history.md).

### 7. Deterministic keys and conformed dates

- Dataverse GUIDs are natural keys and work, but are poor for model performance at volume
  and unreadable when debugging. Generate surrogate keys in Silver and keep the GUID as a
  documented attribute.
- Every date column needs a conformed Date dimension with the customer's fiscal calendar,
  not just a calendar year. Fiscal period is a per-customer configuration input, not a
  constant.
- Dataverse stores datetimes in UTC. Behavior differs by column (user-local vs.
  date-only vs. timezone-independent), so time zone handling is a per-column decision, not
  a global one. Getting this wrong shifts a day's activity into the wrong day and shows up
  as reports that "don't tie."

## What Silver produces

| Conformed artifact | Serves |
|---|---|
| `dim_date` (with fiscal calendar) | every pack |
| `dim_customer` (account) | every pack |
| `dim_contact` | every pack |
| `dim_owner` (user / team / business unit, hierarchies resolved) | every pack, and RLS |
| `dim_currency` | every pack with money |
| `dim_product` | Sales, Field Service, Project Operations |
| `dim_territory` | Sales, Field Service |
| `dim_project` | Project Operations, Revenue-to-Delivery |
| `dim_resource` | Field Service, Project Operations |
| `lkp_choice_label` | every Silver table |
| `bridge_activity` | every pack |

Definitions live in [`../../packs/_shared/conformed-dimensions.md`](../../packs/_shared/conformed-dimensions.md).

## Rules

1. **A pack never defines its own conformed dimension.** If Sales needs a Customer
   dimension, it consumes `dim_customer`. A pack-local copy defeats the entire
   cross-app premise and is the failure mode most likely to creep in under delivery
   pressure.
2. **Every conformance rule is a notebook, not a one-off fix.** If it was worth fixing for
   one customer it is worth fixing for all of them.
3. **Nothing is hard-coded per customer.** Fiscal calendar, language, base currency,
   business unit depth, and table selection are configuration. See `platform/config/`.
4. **Conformance logic is versioned.** A customer on version 1.2 of the conformance layer
   must be identifiable, because the upgrade path depends on it. See the known gap in
   [`../offering/roadmap.md`](../offering/roadmap.md#known-gaps-in-the-offering-as-currently-defined).
5. **Document the trap, not just the fix.** The traps above are why this layer has value.
   Anyone can write the transformation once they know the problem exists.
