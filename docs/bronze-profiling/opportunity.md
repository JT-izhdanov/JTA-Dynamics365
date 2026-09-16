# Bronze profile — `opportunity`

Profiled from a live Link to Fabric export of the JTP `opportunity` table.

| | |
|---|---|
| Entity | `opportunity` |
| Columns as exported | **343** |
| Approximate row count | ~870 (spanning 2010–2026) |
| Open rows | ~265 |
| Profiled | 2026-09-16 |
| Sample | [`samples/opportunity.sample.tsv`](samples/opportunity.sample.tsv) — de-identified, 12 rows |
| Status | **Observed, not exhaustively measured.** Fill rates in §8 still need full-table counts |

---

## 1. How Link to Fabric shapes this table

Four platform-level patterns, all confirmed in the export. They apply to every Dataverse
entity, so this section is reusable beyond Sales.

### 1.1 Fabric sink columns

| Column | Meaning |
|---|---|
| `Id` | Present alongside `opportunityid`. **`<!-- VERIFY -->` whether they are always identical** |
| `SinkCreatedOn`, `SinkModifiedOn` | When the row landed in Fabric — *not* business timestamps |
| `PartitionId` | **The `createdon` year** (`2026`, `2017`, …). The table is year-partitioned |
| `IsDelete` | Soft-delete flag. NULL on live rows |
| `versionnumber` | Dataverse row version |
| `msft_datastate` | NULL throughout; purpose unconfirmed |

**Two hard requirements follow:**

1. **Every Bronze read must filter `IsDelete`.** Omitting it silently includes deleted
   records in every metric.
2. **`PartitionId` is the cheap filter.** Queries scoped to recent created-years hit few
   partitions; anything spanning the full history scans all of them.

### 1.2 Lookups arrive as `<column>` + `<column>_entitytype` pairs

```
customerid              = <guid>
customerid_entitytype   = "account"
```

**This solves polymorphic lookups inline.** The design assumed a join to `TargetMetadata`
to resolve `customerid` and `regardingobjectid`; the discriminator is on the row instead.
Observed entity type values on this table:

`account` · `contact` · `systemuser` · `lead` · `campaign` · `pricelevel` ·
`transactioncurrency` · `businessunit` · `bookableresource` ·
`msdyn_organizationalunit` · `msdyn_predictivescore` · `msdyn_opportunitykpiitem`

### 1.3 Lookup names arrive denormalized

`accountidname`, `owneridname`, `customeridname`, `jt_presalesresourcename`,
`originatingleadidname`, `transactioncurrencyidname`, `pricelevelidname`,
`createdbyname`, `modifiedbyname`, and a `…yominame` twin for each (phonetic; NULL
throughout — ignore).

**Labels for lookups are therefore free**, which removes a whole class of joins from a
first cut. But they are snapshots taken at last write, and they carry no hierarchy — so
`dim_owner` is still required for manager chain, team, and RLS.

### 1.4 Choices are raw integers, with no labels

`jt_backlogtype` = `206360000`. `statecode` = `2`. `msdyn_forecastcategory` = `100000001`.

**The `OptionsetMetadata` dependency stands.** Nothing in the data table resolves a choice
label, so the metadata tables (or the Dataverse Web API fallback) remain a hard
prerequisite for the conformance layer.

Value ranges seen: `2063600xx` for JT custom choices, `1000000xx` for Microsoft Sales
choices, plus isolated `192350001` (`msdyn_ordertype`) and `299600000`
(`msft_coselltype`).

---

## 2. Questions this resolves

| ID | Question | Answer |
|---|---|---|
| — | Polymorphic lookup resolution | **`_entitytype` companion column.** No metadata join |
| — | Choice label source | **Still `OptionsetMetadata`.** Not in the data table |
| — | Soft deletes | **`IsDelete` exists**, must be filtered |
| **J1** | Multi-practice attribution | **Confirmed.** `jt_interests` is semicolon-delimited and **populated on open opportunities** |
| **D2** | Close probability maintained? | **Yes**, but see §5.3 — two fields, and the historic range differs |
| **D4** | Stage from `salesstagecode` or BPF? | **Neither.** `jt_sales_stage` (custom). `salesstagecode` = `1` on every row; `stageid` / `processid` / `traversedpath` all NULL |
| **D5** | Loss reason populated? | **Yes**, as custom `statuscode` values under `statecode = 2` |
| **D7** | Multi-currency? | **No.** `exchangerate` = 1.0, currency = US Dollar throughout |
| **D8** | Opportunity products used? | **Load-bearing** — see §5.1 |
| — | Forecast category in Dataverse? | **Yes, two fields** — see §5.2 |

---

## 3. Column inventory by role

### 3.1 Identity and lifecycle

`opportunityid` · `Id` · `name` · `statecode` · `statuscode` · `versionnumber` ·
`createdon` · `modifiedon` · `overriddencreatedon` · `importsequencenumber`

**`statecode`** — `0` Open · `1` Won · `2` Lost/Closed. Confirmed by `actualvalue` being
populated only on `1`.

**`statuscode`** carries both OOB and JT custom values, and the split is
analytically important — see §5.4.

### 3.2 Practice and classification (JT custom)

| Column | Status | Note |
|---|---|---|
| `jt_primaryproduct_1` | **Populated** | The live practice field |
| `jt_interests` | **Populated** | Multi-select, semicolon-delimited. Additional practices |
| `jt_primaryproduct` | NULL throughout | Superseded by `_1` |
| `jt_salesproduct` | NULL throughout | |
| `jt_technologiesinvolved` | NULL throughout | |
| `jt_backlogtype` | **Populated** | The revenue-type dimension (J2) |
| `jt_opportunitytypeoptions` | **Populated** | Distinct from backlog type |
| `jt_contracttype` | Populated, single value | Little analytic use currently |
| `jt_quotedrateoptions` | Populated | Rate card as a choice |

Three of five product-ish fields are dead. The `_1` suffix on the live one is the trace of
a field rebuild — consistent with the 22-value / 17-legacy mess seen in the Excel report.

### 3.3 Stage and forecast

`jt_sales_stage` (**live**) · `salesstagecode` (`1` always — dead) · `salesstage`
(sparse) · `stepname` (legacy BPF text, inconsistent) · `stageid` / `processid` /
`traversedpath` (**all NULL**) · `jt_forecastcategory` (**live judgment field**) ·
`msdyn_forecastcategory` (state-derived) · `opportunityratingcode` · `prioritycode`

### 3.4 Money — every column is a `_txn` / `_base` pair

**Revenue:** `estimatedvalue` · `actualvalue` · `totalamount` · `totalamountlessfreight` ·
`totallineitemamount` · `totaldiscountamount` · `totallineitemdiscountamount` ·
`totaltax` · `freightamount` · `discountamount`

**Customer budget:** `budgetamount` (OOB) · `jt_budget` (custom) — **both populated, and
they are different fields**

**Estimating:** `jt_roughorderofmagnitudeprovidedamount` · `jt_opportunityquotedrate`

**Quantified customer pain — NOT revenue:** `jt_issue_1_cost` · `jt_issue_2_cost` ·
`jt_additional_issues_costs`

> These last three are the cost of the customer's *problem*, captured as part of the sales
> methodology. They sit in the money block and will be aggregated into pipeline by
> accident. **Never sum them into a revenue measure.**

### 3.5 Milestone dates — the accumulating-snapshot payload

`createdon` · `estimatedclosedate` · `actualclosedate` · `finaldecisiondate` ·
`jt_discoverycompleteddate` · `jt_proofcompleteddate` · `jt_eowsignedon` ·
`jt_docusignsent` · `jt_docusignsigned` · `jt_customeragreeddatetosign` ·
`jt_estimatedprojectstartdate` · `jt_flagplantgradedon` · `jt_presalesdate` ·
`jt_actiondate` · `jt_followupdate` · `jt_leadnextstepdate` · `jt_lastactivitydate`

**This is the most valuable discovery on the entity.** These are genuine process
milestones — discovery → proof → EOW signed → DocuSign → agreed-to-sign → project start.
They make a real accumulating snapshot possible **without stage history**, which is
otherwise unavailable (§5.5).

`jt_estimatedprojectstartdate` minus `actualclosedate` is sales-to-delivery handover
latency — a Revenue-to-Delivery metric available from the Sales pack alone.

**They appear sparsely populated.** Fill rates decide which lags ship (§8).

### 3.6 Rollup field with calculation metadata

```
jt_lastactivitydate        the rolled-up value
jt_lastactivitydate_date   when it was last calculated
jt_lastactivitydate_state  calculation state
```

A Dataverse rollup, and the `_date` / `_state` twins make **staleness of the rollup itself
detectable**. Better input for Stalled Pipeline than `bridge_activity`, and far cheaper —
see §5.6.

### 3.7 Relationships

`customerid` (+`_entitytype`) · `parentaccountid` · `parentcontactid` · `accountid` ·
`contactid` · `ownerid` · `owninguser` · `owningteam` · `owningbusinessunit` ·
`originatingleadid` · `campaignid` · `jt_presalesresource` · `jt_accountmanager` ·
`jt_championname` · `jt_decisionmakerid` · `jt_microsoftcontactid` ·
`transactioncurrencyid` · `pricelevelid` · `createdby` / `modifiedby` (+ `onbehalfby`) ·
`msdyn_contractorganizationalunitid` · `msdyn_predictivescoreid` · `bcbi_companyid`

Notes:

- **The OOB `accountid` / `contactid` pair is unused.** Customer resolution runs through
  `customerid` + `_entitytype`, with `parentaccountid` / `parentcontactid` for the split.
- **`jt_presalesresource_entitytype` = `bookableresource`, not `systemuser`** — see §5.7.
- `bcbi_companyid` is NULL throughout; the prefix suggests a Business Central
  integration. `<!-- VERIFY -->` whether it is live.

### 3.8 Microsoft partner fields

**Populated:** `msft_coselltype` (recent rows) · `campaignid` / `campaignidname`

**Present but NULL:** `msa_partnerid` · `msa_partneroppid` · `msft_partnerrole` ·
`msft_solutionarea` · `msft_solutionplay` · `msft_customerpurchaseintent` ·
`msft_microsoftpartnercenterreferralidentifier` · `…referrallink` · `…referralprogram` ·
`…referralsyncaudit` · `…partnercentersolutions` · `msft_microsoftcrmidentifier` ·
`jt_microsoftcontactid`

**J4 answer:** partner-sourced pipeline is trackable from `msft_coselltype`, `campaignid`
and `jt_marketingsource`. But the structured Partner Center referral fields are empty — the
referral detail (referral ID, partner ID, deal name, Microsoft contact) arrives as
**pasted text inside `description`**. Structured partner reporting would need those fields
populated, or text parsing. Do not promise the latter.

### 3.9 Sales Insights / predictive

`msdyn_predictivescoreid` is populated, but `msdyn_opportunityscore`,
`msdyn_opportunitygrade`, `msdyn_opportunityscoretrend`, `msdyn_scorehistory`,
`msdyn_scorereasons` are **all NULL**. Scoring is provisioned but produces no values in
the export. **Do not build or promise AI-score visuals.**

### 3.10 Booleans — present, largely unused

The OOB sales-process checkboxes (`captureproposalfeedback`, `developproposal`,
`presentproposal`, `identifycompetitors`, …) and the JT stage-completion flags
(`jt_qualifyformcomplete`, `jt_estimatestagecomplete`, `jt_closestagecomplete`, …) are
`0` throughout. No analytic value.

The exception: **`isrevenuesystemcalculated` = 1**, which is load-bearing — §5.1.

### 3.11 Long free text — a model-size and parsing problem

`description` · `jt_problemstatement` · `customerneed` · `customerpainpoints` ·
`currentsituation` · `proposedsolution` · `jt_nextsteps` ·
`jt_negotiationnextsteps` · `jt_nextstepsfordiscovery` · `jt_estimatenextsteps` ·
`jt_resolveconcerns` · `jt_flagplantdescription` · `jt_flagplantsuccesscriteria` ·
`jt_presalesdescription` · `jt_solutionplaynotes` · `jt_lostdetails` ·
`jt_customerpainpointsimpact` / `…who` / `…why` · `jt_issue_1` · `jt_issue_2` ·
`need` · `qualificationcomments` · `quotecomments` · `jt_primarydriver`

Observed characteristics:

- Values run to **thousands of characters**
- They contain **embedded newlines and markdown** (`**bold**`)
- `jt_nextsteps` holds **dated call logs** accumulated in one cell
  (`9/21 FU · 9/3 cld · 8/24 sent email …`)
- `description` on co-sell deals holds a **pasted Partner Center referral block**,
  including contact phone numbers and email addresses

**Consequences:**

1. Most of these must stay **out of the semantic model**. They add size and no analytic value.
2. **Direct Lake rejects strings over 32,764 characters.** Max lengths need measuring (§8).
3. Embedded newlines mean any TSV/CSV extract of this table is **not line-delimited** —
   relevant to anyone re-exporting it.
4. They contain **PII** (customer contact details). Treat as sensitive wherever they land.

---

## 4. Observed choice values

Integers only — labels require `OptionsetMetadata`. **Not exhaustive**; from a 20-row read.

| Column | Values seen |
|---|---|
| `statecode` | `0` `1` `2` |
| `statuscode` | `1` `3` `4` `206360000` `206360002` `206360006` |
| `jt_sales_stage` | `206360003` `206360004` `206360005` |
| `jt_backlogtype` | `206360000` `206360001` `206360002` `206360003` |
| `jt_primaryproduct_1` | `206360000` `206360001` `206360002` `206360003` `206360005` `206360007` `206360011` `206360014` `206360016` `206360020` `206360021` |
| `jt_interests` | `206360002` `206360004` `206360005` `206360007` `206360008` `206360009` `206360010` `206360011` `206360012` `206360015` (as `;`-joined lists) |
| `jt_forecastcategory` | `206360001` `206360004` `206360005` |
| `msdyn_forecastcategory` | `100000001` `100000005` `100000006` |
| `jt_marketingsource` | `206360004` `206360017` `206360018` `206360019` |
| `jt_opportunitytypeoptions` | `206360000` `206360001` `206360003` |
| `jt_contracttype` | `206360000` |
| `jt_quotedrateoptions` | `206360002` `206360003` `206360007` `206360011` `206360021` |
| `jt_iscontactdecisionmaker` | `206360000` |
| `jt_opptybpftobrtrigger` | `206360000` |
| `msdyn_ordertype` | `192350001` |
| `msft_coselltype` | `299600000` |
| `opportunityratingcode` | `1` `2` |
| `closeprobability` / `jt_close_probability` | `50` `75` `95` (modern) · `20` `35` `100` (legacy) |

---

## 5. Findings that change the design

### 5.1 Opportunity products are the revenue source

`isrevenuesystemcalculated` = `1` on effectively every row, and `estimatedvalue` equals
`totallineitemamount` wherever both are populated. **The header value is derived from the
lines.**

**Effect:** decision **D8** flips from *"opportunity products optional, omit the Products
page if unused"* to **`opportunityproduct` is mandatory** — it is the source of the
headline number, and probably the cleanest route to line-level practice attribution.

**Confidence:** strong signal from 20 rows. Confirm with the variance count in §8.

### 5.2 Forecast category exists in Dataverse — in two fields

| Field | Behaviour |
|---|---|
| `msdyn_forecastcategory` (OOB) | Tracks **state**: `100000001` open, `100000005` won, `100000006` lost. No Committed / Best Case anywhere. Not a judgment field here |
| `jt_forecastcategory` (custom) | **The judgment field.** `206360001`, `206360004`, `206360005`. Partially populated |

**Effect:** the Commit / Strong Upside / Upside taxonomy from the Excel report maps to
`jt_forecastcategory`. **No Dynamics change is needed and the Forecast page is
unblocked** — subject to the fill rate in §8.

### 5.3 Two probability fields, and the historic range differs

`closeprobability` (OOB) and `jt_close_probability` (custom) agree on every modern row.
On legacy rows the custom field is NULL while the OOB one shows `20`, `35`, `100`.

**Effect:** use `COALESCE(jt_close_probability, closeprobability)`, and treat weighted
pipeline as **not comparable across the cutover** — the modern 3-band judgment and the
historic wider range are different instruments.

### 5.4 `statecode = 2` mixes Lost and Cancelled

Under `statecode = 2` the export shows `statuscode` = `4` (OOB *Canceled*) alongside JT
custom values `206360000`, `206360002`, `206360006` (loss reasons).

**Effect:** **D1** is answerable, but only by enumerating `statuscode` with labels and
classifying each value. The conformed status grouping in Silver must map at
`statuscode` grain, not `statecode`.

### 5.5 Stage history has no source in this table

`stageid`, `processid` and **`traversedpath` are all NULL** — the BPF path is dead.
`stepname` has values but they are inconsistent across eras (`1-Qualify`, `2-Qualify`,
`4-Close`, `6-Close`, `3-Proof- Credibility`, `4-Proof/Credibility`) and not trustworthy.

**Effect:** stage history comes from **daily snapshots** going forward, or from **audit**
retroactively if auditing is enabled on `jt_sales_stage` and retention reaches back far
enough. That audit check is now the only route to backfilled velocity analytics.

### 5.6 `modifiedon` is polluted by automation

Last-modifier values include service and system accounts, and `modifiedon` clusters on
recent dates across records created years earlier — automation touches rows.

**Effect:** the Excel report's **"Days since last mod"** staleness metric is unreliable.
Use `jt_lastactivitydate` instead, and use `jt_lastactivitydate_date` to detect a stale
rollup. Also: **exclude system and service accounts from any rep-level attribution.**

### 5.7 Pre-sales resource is a `bookableresource`

Not a `systemuser`.

**Effect:** `dim_resource` is needed by the **Sales** pack, earlier than the build sequence
assumed — it was scheduled with Project Operations and Field Service. Build it conformed
from the start.

Useful side effect: the pre-sales engineers are practice-aligned, so pre-sales resource is
an independent cross-check on practice attribution.

### 5.8 One flat business unit, and no owning team

`owningbusinessunit` is a single GUID across every row. **`owningteam` is NULL
throughout.**

**Effects:**

1. **BU-path RLS and the business-unit hierarchy have nothing to build on at JTP.** This
   confirms the build plan's caveat: RLS must be validated against synthetic roles in JT
   Dev, not here.
2. **Team (AE / SAM / SDR) does not come from this table.** It is the primary reporting
   segment for the whole pack, and its source is unknown — probably `systemuser` or
   `teammembership`. **Blocking question.**

### 5.9 The custom schema does not exist for most of the history

On pre-cutover rows, `jt_backlogtype`, `jt_primaryproduct_1`, `jt_sales_stage`,
`jt_forecastcategory` and `jt_interests` are **all NULL**. The table spans 2010–2026; the
custom analytic schema spans a fraction of it.

**This is the single largest analytic constraint on the entity.** Practice, revenue-type,
stage and forecast trends can only reach back to the cutover date. That date must be
measured (§8) and stated plainly on every affected report page.

### 5.10 Test data lives in production

At least one test account with a placeholder value and a service-account owner. **Silver
must exclude test records**, and the exclusion rule needs agreeing with sales ops rather
than pattern-guessed.

---

## 6. Column selection for the Sales facts

### 6.1 Mandatory Silver filters

```
IsDelete IS NULL OR IsDelete = false      -- soft deletes
exclude agreed test-account / test-owner patterns
exclude system and service accounts from rep-level attribution
```

### 6.2 `fact_opportunity` — accumulating snapshot, one row per opportunity

| Group | Columns |
|---|---|
| Keys | `opportunityid` · `Id` · `versionnumber` |
| Descriptive | `name` · `jt_lostdetails` · `jt_nextsteps` *(truncated)* |
| Status | `statecode` · `statuscode` · `jt_sales_stage` · `jt_forecastcategory` · `msdyn_forecastcategory` · `opportunityratingcode` · `prioritycode` |
| Practice / type | `jt_primaryproduct_1` · `jt_backlogtype` · `jt_opportunitytypeoptions` · `jt_contracttype` · `jt_quotedrateoptions` |
| Money | `estimatedvalue` · `actualvalue` · `totalamount` · `totallineitemamount` · `budgetamount` · `jt_budget` · `jt_roughorderofmagnitudeprovidedamount` · `jt_opportunityquotedrate` — all with `_base` |
| Pain (not revenue) | `jt_issue_1_cost` · `jt_issue_2_cost` · `jt_additional_issues_costs` |
| Probability | `COALESCE(jt_close_probability, closeprobability)` |
| Milestones | `createdon` · `estimatedclosedate` · `actualclosedate` · `finaldecisiondate` · `jt_discoverycompleteddate` · `jt_proofcompleteddate` · `jt_eowsignedon` · `jt_docusignsent` · `jt_docusignsigned` · `jt_customeragreeddatetosign` · `jt_estimatedprojectstartdate` · `jt_presalesdate` · `jt_lastactivitydate` (+ `_date`, `_state`) |
| Relationships | `customerid` (+`_entitytype`) · `parentaccountid` · `parentcontactid` · `ownerid` · `owninguser` · `originatingleadid` · `campaignid` · `jt_presalesresource` · `jt_accountmanager` · `transactioncurrencyid` · `pricelevelid` · `createdby` · `modifiedby` |
| Partner | `msft_coselltype` · `campaignidname` · `jt_marketingsource` |
| Fabric | `PartitionId` · `IsDelete` · `SinkModifiedOn` |

Excluded: `jt_primaryproduct`, `jt_salesproduct`, `jt_technologiesinvolved`,
`salesstagecode`, `stageid`, `processid`, `traversedpath`, all `…yominame`, the unused
boolean blocks, and most long text.

### 6.3 `fact_opportunity_practice` — one row per opportunity × practice

Built by splitting **`jt_interests`** on `;`, unioned with `jt_primaryproduct_1` as the
primary, each value resolved through `OptionsetMetadata`.

Carries `is_primary` and an allocation factor. See the allocation discussion in the
[technical design](../../packs/sales/technical-design.md) — the model shape is settled, the
**allocation rule is a business decision that is still open**.

### 6.4 `fact_opportunity_snapshot` — opportunity × day

Narrow by design. From this entity: `opportunityid` · `statecode` · `statuscode` ·
`jt_sales_stage` · `jt_forecastcategory` · `jt_primaryproduct_1` · `jt_backlogtype` ·
`estimatedvalue_base` · `actualvalue_base` · `estimatedclosedate` · probability ·
`ownerid` · `customerid` · `createdon`.

Plus, computed at snapshot time so rolling windows remain answerable historically:
`days_to_est_close` **relative to `snapshot_date`, not today**.

---

## 7. Data quality issues

| # | Issue | Consequence |
|---|---|---|
| 1 | Custom schema NULL pre-cutover (§5.9) | Caps every practice / type / stage trend |
| 2 | Test records in production (§5.10) | Inflates counts; distorts averages |
| 3 | `modifiedon` touched by automation (§5.6) | Staleness metrics unreliable |
| 4 | Three dead product fields | Wrong-field risk during build |
| 5 | Pain-cost columns sit in the money block | Will be summed into pipeline by accident |
| 6 | Long text with newlines, markdown and PII | Model size, Direct Lake limits, re-export breakage, confidentiality |
| 7 | Co-sell referral detail only in `description` text | No structured partner reporting |
| 8 | Predictive score fields provisioned but empty | Cannot promise AI scoring |
| 9 | `statecode = 2` mixes Lost and Cancelled | Win-rate denominator ambiguity |
| 10 | Two probability fields, different historic ranges | Weighted pipeline not comparable across eras |
| 11 | `estimatedvalue` = 0 on some live open rows | Pipeline understated, or line items absent |

---

## 8. Still to measure — full-table counts

Each one decides a design choice. Sampled reads are not sufficient.

| Measure | Decides |
|---|---|
| `jt_interests` fill rate and practice-count distribution, open rows only | Whether the practice fact is worth building; informs the allocation rule |
| `jt_forecastcategory` fill rate by `statecode` | Whether the Forecast page ships |
| Earliest `createdon` where `jt_primaryproduct_1` / `jt_backlogtype` / `jt_sales_stage` are non-NULL | How far back every affected trend can reach |
| Distinct `statuscode` by `statecode`, with labels | **D1** — Lost vs Cancelled classification |
| `customerid_entitytype` distribution | **D10** — contact-owned share (all `account` in the sample) |
| Fill rate on each milestone date in §3.5 | Which lag measures exist |
| Rows where `estimatedvalue ≠ totallineitemamount` | Whether lines are genuinely authoritative (§5.1) |
| `MAX(LEN())` on each long-text column | Direct Lake 32,764-character limit |
| `IsDelete = true` count | Soft-delete volume |
| Rows owned by system / service accounts | Size of the exclusion |
| `Id` vs `opportunityid` equality | Key selection |

---

## 9. Open questions

| # | Question | Blocks |
|---|---|---|
| 1 | **Where does Team (AE / SAM / SDR) come from?** Not on this table | The primary report segment, and the whole pack's layout |
| 2 | Is `Id` always identical to `opportunityid`? | Key selection |
| 3 | What is the test-record exclusion rule? | Every metric |
| 4 | Is auditing enabled on `jt_sales_stage`, and what is the retention? | Whether stage history can be backfilled |
| 5 | What is `bcbi_companyid`? | Possible Business Central linkage |
| 6 | Which `statuscode` values mean Lost vs Cancelled? | **D1** |
| 7 | Are `jt_budget` and `budgetamount` used for different purposes? | Whether both belong in the model |
