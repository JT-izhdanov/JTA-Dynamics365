/* ============================================================================
   Bronze profiling — `opportunity` outstanding measures
   ============================================================================

   Closes the open items in docs/bronze-profiling/opportunity.md §8.

   RUN AGAINST : the Fabric SQL analytics endpoint over the lakehouse carrying the
                 Link to Fabric shortcut.
   PRIVILEGE   : read-only. Nothing here writes.
   DIALECT     : T-SQL (Fabric SQL analytics endpoint).

   BEFORE RUNNING
     Replace {{SCHEMA}} with the schema the shortcut lands in (e.g. `dbo` or
     `bronze`). Confirm the table name is `opportunity` — Link to Fabric preserves
     Dataverse logical names, so it should be.

   OUTPUT
     Each block prints one labelled result set. Paste them back in the order
     below; they map one-to-one onto the §8 table and the decision table in
     packs/sales/technical-design.md.

   NOTE ON `IsDelete`
     Every query filters it. Omitting the filter silently counts deleted rows —
     see opportunity.md §1.1.
   ============================================================================ */


/* ---------------------------------------------------------------- 1 of 11
   THE CUTOVER DATE — the largest analytic constraint on the entity.

   The JT custom analytic schema is NULL on pre-cutover rows, so every practice,
   revenue-type, stage and forecast trend can only reach back to whenever each
   field started being populated. This establishes that floor per field.
   -> opportunity.md §5.9
*/
SELECT '1. cutover dates' AS measure;

SELECT
    'jt_primaryproduct_1'          AS column_name,
    MIN(createdon)                  AS first_populated_createdon,
    MAX(createdon)                  AS last_populated_createdon,
    COUNT_BIG(*)                    AS populated_rows
FROM {{SCHEMA}}.opportunity
WHERE (IsDelete IS NULL OR IsDelete = 0) AND jt_primaryproduct_1 IS NOT NULL
UNION ALL
SELECT 'jt_backlogtype',     MIN(createdon), MAX(createdon), COUNT_BIG(*)
FROM {{SCHEMA}}.opportunity
WHERE (IsDelete IS NULL OR IsDelete = 0) AND jt_backlogtype IS NOT NULL
UNION ALL
SELECT 'jt_sales_stage',     MIN(createdon), MAX(createdon), COUNT_BIG(*)
FROM {{SCHEMA}}.opportunity
WHERE (IsDelete IS NULL OR IsDelete = 0) AND jt_sales_stage IS NOT NULL
UNION ALL
SELECT 'jt_forecastcategory', MIN(createdon), MAX(createdon), COUNT_BIG(*)
FROM {{SCHEMA}}.opportunity
WHERE (IsDelete IS NULL OR IsDelete = 0) AND jt_forecastcategory IS NOT NULL
UNION ALL
SELECT 'jt_interests',        MIN(createdon), MAX(createdon), COUNT_BIG(*)
FROM {{SCHEMA}}.opportunity
WHERE (IsDelete IS NULL OR IsDelete = 0) AND jt_interests IS NOT NULL
UNION ALL
SELECT 'jt_close_probability', MIN(createdon), MAX(createdon), COUNT_BIG(*)
FROM {{SCHEMA}}.opportunity
WHERE (IsDelete IS NULL OR IsDelete = 0) AND jt_close_probability IS NOT NULL;


/* ---------------------------------------------------------------- 2 of 11
   J1 — MULTI-PRACTICE. Fill rate and practice-count distribution on OPEN rows.

   Decides whether fact_opportunity_practice is worth building, and informs the
   allocation rule. The earlier 20-row read showed jt_interests populated on open
   opportunities; this measures how often.
   -> opportunity.md §5 / J1
*/
SELECT '2. jt_interests fill + practice count, open rows' AS measure;

SELECT
    CASE
        WHEN jt_interests IS NULL OR jt_interests = '' THEN 0
        ELSE LEN(jt_interests) - LEN(REPLACE(jt_interests, ';', '')) + 1
    END                             AS practice_count,
    COUNT_BIG(*)                    AS opportunities,
    SUM(estimatedvalue_base)        AS est_value_base
FROM {{SCHEMA}}.opportunity
WHERE (IsDelete IS NULL OR IsDelete = 0)
  AND statecode = 0                          -- open only
GROUP BY
    CASE
        WHEN jt_interests IS NULL OR jt_interests = '' THEN 0
        ELSE LEN(jt_interests) - LEN(REPLACE(jt_interests, ';', '')) + 1
    END
ORDER BY practice_count;

/* Same, all states, so the open-vs-closed difference is visible. */
SELECT
    statecode,
    COUNT_BIG(*)                                                   AS total_rows,
    SUM(CASE WHEN jt_interests IS NOT NULL AND jt_interests <> ''
             THEN 1 ELSE 0 END)                                    AS with_interests
FROM {{SCHEMA}}.opportunity
WHERE (IsDelete IS NULL OR IsDelete = 0)
GROUP BY statecode
ORDER BY statecode;


/* ---------------------------------------------------------------- 3 of 11
   FORECAST CATEGORY fill rate by state — decides whether the Forecast page ships.

   Both fields, side by side. msdyn_forecastcategory looked state-derived in the
   sample; jt_forecastcategory looked like the judgment field.
   -> opportunity.md §5.2
*/
SELECT '3. forecast category fill by state' AS measure;

SELECT
    statecode,
    COUNT_BIG(*)                                                       AS rows_total,
    SUM(CASE WHEN jt_forecastcategory    IS NOT NULL THEN 1 ELSE 0 END) AS jt_populated,
    SUM(CASE WHEN msdyn_forecastcategory IS NOT NULL THEN 1 ELSE 0 END) AS msdyn_populated
FROM {{SCHEMA}}.opportunity
WHERE (IsDelete IS NULL OR IsDelete = 0)
GROUP BY statecode
ORDER BY statecode;

/* Value cross-tab: confirms whether msdyn_forecastcategory is just tracking state. */
SELECT statecode, msdyn_forecastcategory, jt_forecastcategory, COUNT_BIG(*) AS rows_
FROM {{SCHEMA}}.opportunity
WHERE (IsDelete IS NULL OR IsDelete = 0)
GROUP BY statecode, msdyn_forecastcategory, jt_forecastcategory
ORDER BY statecode, msdyn_forecastcategory, jt_forecastcategory;


/* ---------------------------------------------------------------- 4 of 11
   D1 — LOST vs CANCELLED. Enumerate statuscode within statecode.

   statecode = 2 mixes the OOB `4` (Canceled) with JT custom loss reasons. The
   conformed status grouping has to map at statuscode grain, and this is the list
   to classify. Labels need OptionsetMetadata — block 11 pulls them if available.
   -> opportunity.md §5.4
*/
SELECT '4. statuscode within statecode' AS measure;

SELECT
    statecode,
    statuscode,
    COUNT_BIG(*)                    AS rows_,
    MIN(createdon)                  AS first_seen,
    MAX(createdon)                  AS last_seen,
    SUM(actualvalue_base)           AS actual_value_base
FROM {{SCHEMA}}.opportunity
WHERE (IsDelete IS NULL OR IsDelete = 0)
GROUP BY statecode, statuscode
ORDER BY statecode, statuscode;


/* ---------------------------------------------------------------- 5 of 11
   D8 — ARE THE LINES AUTHORITATIVE? estimatedvalue vs totallineitemamount.

   The sample showed isrevenuesystemcalculated = 1 with the two equal, which is
   why opportunityproduct moved from optional to load-bearing. This is the check.
   -> opportunity.md §5.1
*/
SELECT '5. header vs line revenue' AS measure;

SELECT
    isrevenuesystemcalculated,
    COUNT_BIG(*)                                                      AS rows_,
    SUM(CASE WHEN estimatedvalue = totallineitemamount
             THEN 1 ELSE 0 END)                                       AS header_equals_lines,
    SUM(CASE WHEN estimatedvalue <> totallineitemamount
             THEN 1 ELSE 0 END)                                       AS header_differs,
    SUM(CASE WHEN estimatedvalue IS NULL OR totallineitemamount IS NULL
             THEN 1 ELSE 0 END)                                       AS either_null
FROM {{SCHEMA}}.opportunity
WHERE (IsDelete IS NULL OR IsDelete = 0)
GROUP BY isrevenuesystemcalculated;

/* Zero-value open rows — flagged as issue 11 in the profile. */
SELECT
    COUNT_BIG(*)                                                      AS open_rows,
    SUM(CASE WHEN estimatedvalue = 0      THEN 1 ELSE 0 END)          AS est_value_zero,
    SUM(CASE WHEN estimatedvalue IS NULL  THEN 1 ELSE 0 END)          AS est_value_null
FROM {{SCHEMA}}.opportunity
WHERE (IsDelete IS NULL OR IsDelete = 0) AND statecode = 0;


/* ---------------------------------------------------------------- 6 of 11
   D10 — CUSTOMER PARTY TYPE. Contact-owned share.

   All 20 sampled rows were `account`. If the contact share is material, the
   account-only dim_customer needs replacing with a party dimension — which is a
   conformed-dimension change affecting every pack, so it needs an ADR.
   -> opportunity.md §3.7
*/
SELECT '6. customer party type' AS measure;

SELECT
    customerid_entitytype,
    COUNT_BIG(*)                    AS rows_,
    SUM(CASE WHEN statecode = 0 THEN 1 ELSE 0 END) AS open_rows
FROM {{SCHEMA}}.opportunity
WHERE (IsDelete IS NULL OR IsDelete = 0)
GROUP BY customerid_entitytype
ORDER BY rows_ DESC;


/* ---------------------------------------------------------------- 7 of 11
   MILESTONE DATE FILL RATES — decides which lag measures exist.

   These are what make a real accumulating snapshot possible without stage
   history. They looked sparse in the sample; this is how sparse.
   -> opportunity.md §3.5
*/
SELECT '7. milestone date fill rates' AS measure;

SELECT
    COUNT_BIG(*)                                                                AS rows_total,
    SUM(CASE WHEN jt_discoverycompleteddate   IS NOT NULL THEN 1 ELSE 0 END)    AS discovery_completed,
    SUM(CASE WHEN jt_proofcompleteddate       IS NOT NULL THEN 1 ELSE 0 END)    AS proof_completed,
    SUM(CASE WHEN jt_eowsignedon              IS NOT NULL THEN 1 ELSE 0 END)    AS eow_signed,
    SUM(CASE WHEN jt_docusignsent             IS NOT NULL THEN 1 ELSE 0 END)    AS docusign_sent,
    SUM(CASE WHEN jt_docusignsigned           IS NOT NULL THEN 1 ELSE 0 END)    AS docusign_signed,
    SUM(CASE WHEN jt_customeragreeddatetosign IS NOT NULL THEN 1 ELSE 0 END)    AS agreed_to_sign,
    SUM(CASE WHEN jt_estimatedprojectstartdate IS NOT NULL THEN 1 ELSE 0 END)   AS est_project_start,
    SUM(CASE WHEN jt_presalesdate             IS NOT NULL THEN 1 ELSE 0 END)    AS presales_date,
    SUM(CASE WHEN finaldecisiondate           IS NOT NULL THEN 1 ELSE 0 END)    AS final_decision,
    SUM(CASE WHEN actualclosedate             IS NOT NULL THEN 1 ELSE 0 END)    AS actual_close,
    SUM(CASE WHEN jt_lastactivitydate         IS NOT NULL THEN 1 ELSE 0 END)    AS last_activity
FROM {{SCHEMA}}.opportunity
WHERE (IsDelete IS NULL OR IsDelete = 0) AND statecode IN (1, 2);   -- closed rows only:
                                                                    -- a milestone is only
                                                                    -- "missing" if it should
                                                                    -- have happened by now


/* ---------------------------------------------------------------- 8 of 11
   LONG-TEXT MAX LENGTHS — Direct Lake rejects strings over 32,764 characters.

   Decides D7 (Direct Lake vs Import) and which text columns can enter the model
   at all. -> opportunity.md §3.11
*/
SELECT '8. long text max lengths' AS measure;

SELECT 'description'                AS column_name, MAX(LEN(description))                AS max_len FROM {{SCHEMA}}.opportunity WHERE IsDelete IS NULL OR IsDelete = 0
UNION ALL SELECT 'jt_problemstatement',      MAX(LEN(jt_problemstatement))      FROM {{SCHEMA}}.opportunity WHERE IsDelete IS NULL OR IsDelete = 0
UNION ALL SELECT 'customerneed',             MAX(LEN(customerneed))             FROM {{SCHEMA}}.opportunity WHERE IsDelete IS NULL OR IsDelete = 0
UNION ALL SELECT 'customerpainpoints',       MAX(LEN(customerpainpoints))       FROM {{SCHEMA}}.opportunity WHERE IsDelete IS NULL OR IsDelete = 0
UNION ALL SELECT 'currentsituation',         MAX(LEN(currentsituation))         FROM {{SCHEMA}}.opportunity WHERE IsDelete IS NULL OR IsDelete = 0
UNION ALL SELECT 'proposedsolution',         MAX(LEN(proposedsolution))         FROM {{SCHEMA}}.opportunity WHERE IsDelete IS NULL OR IsDelete = 0
UNION ALL SELECT 'jt_nextsteps',             MAX(LEN(jt_nextsteps))             FROM {{SCHEMA}}.opportunity WHERE IsDelete IS NULL OR IsDelete = 0
UNION ALL SELECT 'jt_flagplantdescription',  MAX(LEN(jt_flagplantdescription))  FROM {{SCHEMA}}.opportunity WHERE IsDelete IS NULL OR IsDelete = 0
UNION ALL SELECT 'jt_lostdetails',           MAX(LEN(jt_lostdetails))           FROM {{SCHEMA}}.opportunity WHERE IsDelete IS NULL OR IsDelete = 0
UNION ALL SELECT 'need',                     MAX(LEN(need))                     FROM {{SCHEMA}}.opportunity WHERE IsDelete IS NULL OR IsDelete = 0
ORDER BY max_len DESC;


/* ---------------------------------------------------------------- 9 of 11
   PLATFORM HYGIENE — soft deletes, key equality, partition spread.
   -> opportunity.md §1.1
*/
SELECT '9. platform hygiene' AS measure;

/* Soft-delete volume. */
SELECT
    COUNT_BIG(*)                                              AS all_rows,
    SUM(CASE WHEN IsDelete = 1 THEN 1 ELSE 0 END)             AS deleted_rows,
    SUM(CASE WHEN IsDelete IS NULL THEN 1 ELSE 0 END)         AS isdelete_null
FROM {{SCHEMA}}.opportunity;

/* Is `Id` always `opportunityid`? Decides key selection. Expect 0 mismatches. */
SELECT COUNT_BIG(*) AS id_mismatches
FROM {{SCHEMA}}.opportunity
WHERE CAST(Id AS varchar(64)) <> CAST(opportunityid AS varchar(64));

/* Partition spread — PartitionId should equal the createdon year. */
SELECT
    PartitionId,
    COUNT_BIG(*)                    AS rows_,
    MIN(createdon)                  AS min_createdon,
    MAX(createdon)                  AS max_createdon
FROM {{SCHEMA}}.opportunity
WHERE IsDelete IS NULL OR IsDelete = 0
GROUP BY PartitionId
ORDER BY PartitionId;


/* --------------------------------------------------------------- 10 of 11
   EXCLUSIONS — system/service accounts and test data.

   Rep-level metrics must exclude automation identities, and test records live in
   production. This sizes both. The exclusion RULE still needs agreeing with
   sales ops rather than pattern-guessing.
   -> opportunity.md §5.6, §5.10
*/
SELECT '10. owners and probable test data' AS measure;

/* Every owner by volume. Service and automation identities will stand out. */
SELECT
    owneridname,
    COUNT_BIG(*)                                        AS rows_,
    SUM(CASE WHEN statecode = 0 THEN 1 ELSE 0 END)      AS open_rows,
    MIN(createdon)                                      AS first_row,
    MAX(createdon)                                      AS last_row
FROM {{SCHEMA}}.opportunity
WHERE IsDelete IS NULL OR IsDelete = 0
GROUP BY owneridname
ORDER BY rows_ DESC;

/* Who last modified rows — expected to be dominated by automation, which is why
   modifiedon is unusable as a staleness signal. */
SELECT modifiedbyname, COUNT_BIG(*) AS rows_
FROM {{SCHEMA}}.opportunity
WHERE IsDelete IS NULL OR IsDelete = 0
GROUP BY modifiedbyname
ORDER BY rows_ DESC;

/* Probable test rows. A STARTING POINT for the conversation, not the rule. */
SELECT
    COUNT_BIG(*)                                                          AS probable_test_rows
FROM {{SCHEMA}}.opportunity
WHERE (IsDelete IS NULL OR IsDelete = 0)
  AND (   LOWER(name)          LIKE '%test%'
       OR LOWER(customeridname) LIKE '%test%'
       OR estimatedvalue IN (0, 1)
      );


/* --------------------------------------------------------------- 11 of 11
   CHOICE LABELS — confirm the metadata tables actually materialised.

   This is the platform's single most important unresolved dependency: the
   business tables can sync while the OptionsetMetadata folder silently does not.
   If these fail, the Dataverse Web API fallback is required.
   -> opportunity.md §1.4, platform/notebooks/20_silver_conformance_choice_labels.py

   Table names and column names are UNCONFIRMED — adjust to what the metadata
   folder actually exposes, then record the shape back into the profile.
*/
SELECT '11. choice label metadata availability' AS measure;

/* Does the metadata table exist at all? */
SELECT TABLE_SCHEMA, TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE LOWER(TABLE_NAME) IN (
    'optionsetmetadata', 'globaloptionsetmetadata',
    'statemetadata', 'statusmetadata', 'targetmetadata', 'stringmap'
)
ORDER BY TABLE_NAME;

/* If OptionsetMetadata is present, this resolves the labels behind every choice
   value recorded in opportunity.md §4. Adjust column names as needed. */
-- SELECT EntityName, OptionSetName, Option, LocalizedLabel
-- FROM {{SCHEMA}}.OptionsetMetadata
-- WHERE LOWER(EntityName) = 'opportunity'
--   AND LOWER(OptionSetName) IN (
--       'statecode','statuscode','jt_sales_stage','jt_backlogtype',
--       'jt_primaryproduct_1','jt_interests','jt_forecastcategory',
--       'msdyn_forecastcategory','jt_marketingsource','jt_opportunitytypeoptions'
--   )
-- ORDER BY OptionSetName, Option;
