# Sales pack — source tables

> **DRAFT — NOT VALIDATED.** Written from general Dataverse knowledge. Dataverse schema
> varies by solution version and installed apps, so this contains errors. Correct it from
> what notebook 10 actually observes during the first build, and commit the corrections —
> that feedback loop is how this becomes real IP rather than an assumption.
>
> Items marked `VERIFY` are explicitly unconfirmed.

All names are Dataverse **logical names**, lowercase.

## Core tables

| Table | Role | Grain |
|---|---|---|
| `lead` | Lead fact | one row per lead |
| `opportunity` | Opportunity fact + snapshot source | one row per opportunity |
| `opportunityproduct` | Opportunity line fact | one row per opportunity product line |
| `quote` | Quote fact | one row per quote |
| `quotedetail` | Quote line fact | one row per quote line |
| `salesorder` | Order fact | one row per order |
| `salesorderdetail` | Order line fact | one row per order line |

## Dimension sources

| Table | Produces | Note |
|---|---|---|
| `account` | `dim_customer` | **Conformed.** SCD2 |
| `contact` | `dim_contact` | **Conformed** |
| `product` | `dim_product` | **Conformed.** SCD2 |
| `territory` | `dim_territory` | **Conformed.** Often unpopulated — check |
| `systemuser`, `team`, `businessunit` | `dim_owner` | Built by notebook 22 |
| `transactioncurrency` | `dim_currency` | Built by notebook 21 |
| `activitypointer` | `bridge_activity` | Built by notebook 23 |
| `pricelevel` | price list attributes | `VERIFY` whether needed |

**These dimensions are built as conformed dimensions in Silver, not as pack-local tables.**
Every later pack depends on this pack getting that right — see
[`../README.md`](../README.md#the-rule-that-matters-most).

## opportunity — columns

The most important mapping in the pack. Also the snapshot source
([notebook 30](../../platform/notebooks/30_silver_snapshot_facts.py)).

| Column | Purpose | Notes |
|---|---|---|
| `opportunityid` | Key | → `opportunity_guid` / `_key` |
| `name` | Label | |
| `statecode` | Lifecycle state | 0 = Open, 1 = Won, 2 = Lost — `VERIFY` |
| `statuscode` | Status reason | Customer-extensible. Labels via `lkp_choice_label` |
| `salesstagecode` | Sales stage | May disagree with business process flow — see below |
| `stepname` | BPF step name | `VERIFY` availability |
| `estimatedvalue` | Pipeline value (txn) | → `estimatedvalue_txn` |
| `estimatedvalue_base` | Pipeline value (base) | **Reports default to base** |
| `actualvalue` / `actualvalue_base` | Closed value | |
| `budgetamount` / `budgetamount_base` | Customer budget | Often unpopulated |
| `transactioncurrencyid` | → `dim_currency` | |
| `estimatedclosedate` | Forecast date | Slippage analysis compares this across snapshots |
| `actualclosedate` | Close date | `time_basis` for win/loss metrics |
| `closeprobability` | Probability % | Weighted pipeline is meaningless if unmaintained |
| `opportunityratingcode` | Rating | |
| `customerid` | → `dim_customer` | Polymorphic: account **or** contact. `VERIFY` handling |
| `parentaccountid` / `parentcontactid` | Customer resolution | `VERIFY` which is reliably populated |
| `ownerid` | → `dim_owner` | Snapshots join the **as-of** owner version |
| `owningbusinessunit` | → `dim_owner` / RLS | |
| `territoryid`ᐩ | → `dim_territory` | `VERIFY` — may live on account rather than opportunity |
| `createdon` | Created (UTC) | Time zone handling is **per-column** |
| `modifiedon` | Modified (UTC) | |
| `actualdurationminutes` | | `VERIFY` relevance |

**`customerid` is polymorphic** (account or contact), like `regardingobjectid` on
activities. Resolve it explicitly in Silver rather than assuming account — B2C-shaped
customers will break the assumption.

## lead — columns

| Column | Purpose | Notes |
|---|---|---|
| `leadid` | Key | |
| `subject` | Label | |
| `statecode` / `statuscode` | Lifecycle | Includes Qualified / Disqualified |
| `leadqualitycode` | Rating | |
| `leadsourcecode` | Source | Key conversion dimension |
| `createdon` | Created | |
| `ownerid` / `owningbusinessunit` | → `dim_owner` | |
| `parentaccountid` / `parentcontactid` | Linkage | |
| `qualifyingopportunityid` | → `opportunity` | **Essential** for lead-to-opportunity conversion |
| `estimatedvalue` / `_base` | Estimated value | |

## opportunityproduct — columns

| Column | Purpose | Notes |
|---|---|---|
| `opportunityproductid` | Key | |
| `opportunityid` | → `opportunity` | |
| `productid` | → `dim_product` | Null for write-in products |
| `productdescription` | Write-in label | Used when `productid` is null |
| `quantity` | Quantity | |
| `priceperunit` / `_base` | Unit price | |
| `extendedamount` / `_base` | Line total | |
| `ispriceoverridden` | Override flag | |

**Line totals may not sum to the opportunity header value.** This is normal Dynamics
behavior, not a defect, and it will be questioned during reconciliation. Document the
relationship rather than forcing agreement.

## quote / salesorder

Follow the same header/detail shape. Needed for quote-to-order conversion and for the
Revenue-to-Delivery pack.

> **Important for Project Operations:** in Project Operations, the **project contract is
> built on `salesorder`** and contract lines on `salesorderdetail`. So these tables serve
> both packs and are a key join point for
> [Revenue-to-Delivery](../revenue-to-delivery/). `VERIFY` this against the customer's
> Project Operations version and deployment type — see
> [ADR 0003](../../docs/decisions/0003-project-operations-scope.md).

## Choice columns requiring labels

Add to `tables.choice_columns` in the customer configuration:

| Table | Columns |
|---|---|
| `opportunity` | `statecode`, `statuscode`, `salesstagecode`, `opportunityratingcode` |
| `lead` | `statecode`, `statuscode`, `leadqualitycode`, `leadsourcecode` |
| `quote` | `statecode`, `statuscode` |
| `salesorder` | `statecode`, `statuscode` |

## Stage tracking — decide during the first build

Dynamics 365 Sales tracks stage two ways, and they can disagree:

1. **`salesstagecode`** on the opportunity — a simple choice column.
2. **Business process flow** — stage held in a separate BPF table instance.

Customers using BPFs often leave `salesstagecode` at its default, in which case stage
analytics built on it are wrong while looking plausible.

**Determine which the customer actually uses before building stage analytics.** If BPF, the
relevant BPF table must be added to the linked table set.
`VERIFY` the BPF instance table name and whether it is available through Link to Fabric.

## Not in scope

- Custom tables and columns — additional development
- First-party Dynamics 365 Sales forecasting tables — see pack README limitation 6
- Conversation intelligence / Sales Premium AI data
- Marketing / Customer Insights – Journeys data — a roadmap candidate pack
