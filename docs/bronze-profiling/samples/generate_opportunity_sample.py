"""
Generate a structurally faithful, DE-IDENTIFIED sample of the Bronze `opportunity`
table as Link to Fabric exports it.

WHY THIS EXISTS
    The real JTP export contains customer names, employee names, deal values, contact
    phone numbers and email addresses, and SharePoint URLs. None of that can be committed
    (see ../README.md). What the build actually needs from a sample is the SHAPE — column
    order, data types, the `_entitytype` companion pattern, the raw choice integers, the
    semicolon-delimited multi-select, and the NULL patterns. This script synthesises that
    shape from the observed profile in ../opportunity.md.

    No real data is used as input. The script encodes observed PATTERNS, not values, so
    it is safe to commit and safe to re-run.

WHAT IS FAITHFUL
    - Column names and exact column ORDER, as exported
    - Every `<lookup>` / `<lookup>_entitytype` pair, with the real entity type names
    - Raw choice integers exactly as observed (206360xxx, 100000xxx, 192350001, 299600000)
    - `jt_interests` as a semicolon-delimited list of choice integers
    - Money as `_txn` / `_base` pairs, with base == txn (single-currency org)
    - NULL density per column, and the legacy-row pattern where all jt_* are NULL
    - `PartitionId` = createdon year; `IsDelete`; Sink* columns

WHAT IS NOT
    - All GUIDs are synthetic
    - All names are placeholders (Account 001, Rep A, Presales A, ...)
    - Money values are invented and rounded
    - Dates are invented but internally consistent
    - Long free text is replaced with a marker recording the observed length class.
      REAL VALUES CONTAIN EMBEDDED NEWLINES AND MARKDOWN — see ../opportunity.md.
      This sample deliberately contains none, so it stays valid TSV.

USAGE
    python generate_opportunity_sample.py > opportunity.sample.tsv
"""

import sys
import uuid

# --------------------------------------------------------------------------- header
# Exact column order as exported by Link to Fabric.
HEADER = """Id SinkCreatedOn SinkModifiedOn statecode statuscode budgetstatus
initialcommunication jt_backlogtype jt_championjobtitle jt_close_probability
jt_contracttype jt_customerintenttosign jt_flagplantgrade jt_forecastcategory
jt_fundingprogram jt_iscontactdecisionmaker jt_lostdetails jt_marketingsource
jt_methodofproof jt_opportunitytypeoptions jt_opptybpftobrtrigger jt_presentationmethod
jt_primaryproduct_1 jt_probability jt_quotedrateoptions jt_referenceused jt_sales_stage
msdyn_forecastcategory msdyn_opportunitygrade msdyn_opportunityscoretrend msdyn_ordertype
msft_coselltype msft_customerpurchaseintent msft_microsoftpartnercenterhelp need
opportunityratingcode pricingerrorcode prioritycode purchaseprocess purchasetimeframe
salesstage salesstagecode skippricecalculation timeline jt_interests jt_primaryproduct
jt_salesproduct jt_technologiesinvolved captureproposalfeedback completefinalproposal
completeinternalreview confirminterest decisionmaker developproposal evaluatefit
filedebrief identifycompetitors identifycustomercontacts identifypursuitteam isprivate
isrevenuesystemcalculated jt_closestagecomplete jt_discoveryformcomplete
jt_estimatestagecomplete jt_negotiationstagecomplete jt_progressing jt_qualifyformcomplete
msdyn_gdproptout msft_microsoftpartnercenterreferralsync
msft_microsoftpartnercenterreferralvisible new_csplicensing participatesinworkflow
presentfinalproposal presentproposal pursuitdecision resolvefeedback sendthankyounote
accountid accountid_entitytype bcbi_companyid bcbi_companyid_entitytype campaignid
campaignid_entitytype contactid contactid_entitytype createdby createdby_entitytype
createdonbehalfby createdonbehalfby_entitytype jt_accountmanager
jt_accountmanager_entitytype jt_championname jt_championname_entitytype jt_decisionmakerid
jt_decisionmakerid_entitytype jt_microsoftcontactid jt_microsoftcontactid_entitytype
jt_presalesresource jt_presalesresource_entitytype jt_quotedrate jt_quotedrate_entitytype
jt_resourcingunitid jt_resourcingunitid_entitytype modifiedby modifiedby_entitytype
modifiedonbehalfby modifiedonbehalfby_entitytype msa_partnerid msa_partnerid_entitytype
msa_partneroppid msa_partneroppid_entitytype msdyn_accountmanagerid
msdyn_accountmanagerid_entitytype msdyn_contractorganizationalunitid
msdyn_contractorganizationalunitid_entitytype msdyn_opportunitykpiid
msdyn_opportunitykpiid_entitytype msdyn_predictivescoreid
msdyn_predictivescoreid_entitytype msdyn_segmentid msdyn_segmentid_entitytype
msdynci_lookupfield_customerprofile msdynci_lookupfield_customerprofile_entitytype
msdynmkt_journeyid msdynmkt_journeyid_entitytype msft_partnerrole
msft_partnerrole_entitytype msft_solutionarea msft_solutionarea_entitytype
msft_solutionplay msft_solutionplay_entitytype originatingleadid
originatingleadid_entitytype owningbusinessunit owningbusinessunit_entitytype owningteam
owningteam_entitytype owninguser owninguser_entitytype parentaccountid
parentaccountid_entitytype parentcontactid parentcontactid_entitytype pricelevelid
pricelevelid_entitytype slaid slaid_entitytype slainvokedid slainvokedid_entitytype
transactioncurrencyid transactioncurrencyid_entitytype ownerid ownerid_entitytype
customerid customerid_entitytype actualvalue actualvalue_base budgetamount
budgetamount_base discountamount discountamount_base estimatedvalue estimatedvalue_base
freightamount freightamount_base jt_additional_issues_costs
jt_additional_issues_costs_base jt_budget jt_budget_base jt_issue_1_cost
jt_issue_1_cost_base jt_issue_2_cost jt_issue_2_cost_base jt_opportunityquotedrate
jt_opportunityquotedrate_base jt_roughorderofmagnitudeprovidedamount
jt_roughorderofmagnitudeprovidedamount_base totalamount totalamount_base
totalamountlessfreight totalamountlessfreight_base totaldiscountamount
totaldiscountamount_base totallineitemamount totallineitemamount_base
totallineitemdiscountamount totallineitemdiscountamount_base totaltax totaltax_base
accountidname accountidyominame actualclosedate bcbi_companyidname campaignidname
closeprobability contactidname contactidyominame createdbyname createdbyyominame createdon
createdonbehalfbyname createdonbehalfbyyominame currentsituation customeridname
customeridtype customeridyominame customerneed customerpainpoints description
discountpercentage emailaddress estimatedclosedate exchangerate finaldecisiondate
importsequencenumber jt_accountmanagername jt_accountmanageryominame jt_acmeffort
jt_actiondate jt_additionalissues jt_championnamename jt_championnameyominame
jt_customeragreeddatetosign jt_customeronenoteurl jt_customerpainpointsimpact
jt_customerpainpointswho jt_customerpainpointswhy jt_decisionmakeridname
jt_decisionmakeridyominame jt_decisionphase jt_discoverycompleteddate jt_docusignsent
jt_docusignsigned jt_eowsignedon jt_estimatedprojectstartdate jt_estimatenextsteps
jt_estimatepresentedtocustomer jt_estimatereadyforsales jt_estimaterevisionsneeded
jt_finalestimatedeliveredtocustomer jt_flagplantdescription jt_flagplantgradedetail
jt_flagplantgradedon jt_flagplantsuccesscriteria jt_followupdate
jt_fundingintrotosalesopsmade jt_fundingsowsigned jt_issue_1 jt_issue_2
jt_lastactivitydate jt_lastactivitydate_date jt_lastactivitydate_state
jt_leadnextstepdate jt_microsoftcontactidname jt_microsoftcontactidyominame
jt_needestimate jt_negotiationnextsteps jt_nextsteps jt_nextstepsfordiscovery
jt_presalesdate jt_presalesdescription jt_presalesresourcename jt_primarydriver
jt_problemstatement jt_proofcompleteddate jt_quotedratename jt_resolveconcerns
jt_resourcingunitidname jt_resourcingunitidyominame
jt_roughorderofmagnitudeprovidedtocustomer jt_solutionplaynotes jt_timeframeexpected
lastonholdtime modifiedbyname modifiedbyyominame modifiedon modifiedonbehalfbyname
modifiedonbehalfbyyominame msa_partneridname msa_partneridyominame msa_partneroppidname
msa_partneroppidyominame msdyn_accountmanageridname msdyn_accountmanageridyominame
msdyn_contractorganizationalunitidname msdyn_copysourceid msdyn_opportunitykpiidname
msdyn_opportunityscore msdyn_predictivescoreidname msdyn_scorehistory msdyn_scorereasons
msdyn_segmentidname msdyn_similaropportunities msdynci_lookupfield_customerprofilename
msdynci_lookupfield_customerprofilepid msdynmkt_journeyactionid msdynmkt_journeyidname
msft_microsoftcrmidentifier msft_microsoftpartnercenterreferralidentifier
msft_microsoftpartnercenterreferrallink msft_microsoftpartnercenterreferralprogram
msft_microsoftpartnercenterreferralsyncaudit msft_microsoftpartnercentersolutions
msft_partnerrolename msft_solutionareaname msft_solutionplayname name onholdtime
opportunityid originatingleadidname originatingleadidyominame overriddencreatedon
owneridname owneridtype owneridyominame owningbusinessunitname parentaccountidname
parentaccountidyominame parentcontactidname parentcontactidyominame pricelevelidname
processid proposedsolution qualificationcomments quotecomments schedulefollowup_prospect
schedulefollowup_qualify scheduleproposalmeeting slainvokedidname slaname stageid stepid
stepname teamsfollowed timespentbymeonemailandmeetings timezoneruleversionnumber
transactioncurrencyidname traversedpath utcconversiontimezonecode versionnumber
msft_datastate PartitionId IsDelete""".split()

NULL = "NULL"

# Stable synthetic GUIDs so rows reference each other consistently.
_seed = 0


def guid(tag: str) -> str:
    """Deterministic synthetic GUID, keyed by tag so references are stable."""
    return str(uuid.uuid5(uuid.NAMESPACE_OID, f"jta-sample::{tag}"))


# Fixed org-level references (observed as constant across the real export).
BU = guid("businessunit")
ORG_UNIT = guid("orgunit")
CURRENCY = guid("currency")
PRICELEVEL = guid("pricelevel")


def row(**over) -> list:
    """Build a row: everything NULL unless overridden."""
    values = {c: NULL for c in HEADER}

    # Columns that are non-NULL on essentially every row.
    values.update(
        {
            "owningbusinessunit": BU,
            "owningbusinessunit_entitytype": "businessunit",
            "owningbusinessunitname": "JourneyTeam",
            "msdyn_contractorganizationalunitid": ORG_UNIT,
            "msdyn_contractorganizationalunitid_entitytype": "msdyn_organizationalunit",
            "msdyn_contractorganizationalunitidname": "JourneyTEAM",
            "transactioncurrencyid": CURRENCY,
            "transactioncurrencyid_entitytype": "transactioncurrency",
            "transactioncurrencyidname": "US Dollar",
            "exchangerate": "1.0000000000",
            "pricelevelid": PRICELEVEL,
            "pricelevelid_entitytype": "pricelevel",
            "pricelevelidname": "JTP Products Pricing",
            "salesstagecode": "1",          # OOB, always 1 — unused
            "skippricecalculation": "0",
            "prioritycode": "1",
            "pricingerrorcode": "0",
            "isprivate": "0",
            "isrevenuesystemcalculated": "1",
            "msdyn_forecastcategory": "100000001",
            "msdyn_ordertype": "192350001",
            "opportunityratingcode": "2",
            "timezoneruleversionnumber": "0",
        }
    )
    # OOB sales-process checkboxes and jt_* stage flags: present but unused (0).
    for c in (
        "captureproposalfeedback completefinalproposal completeinternalreview "
        "confirminterest decisionmaker developproposal evaluatefit filedebrief "
        "identifycompetitors identifycustomercontacts identifypursuitteam "
        "jt_closestagecomplete jt_discoveryformcomplete jt_estimatestagecomplete "
        "jt_negotiationstagecomplete jt_progressing jt_qualifyformcomplete "
        "msdyn_gdproptout msft_microsoftpartnercenterreferralsync "
        "msft_microsoftpartnercenterreferralvisible new_csplicensing "
        "participatesinworkflow presentfinalproposal presentproposal pursuitdecision "
        "resolvefeedback sendthankyounote"
    ).split():
        values[c] = "0"

    values.update(over)
    return [values[c] for c in HEADER]


def money(txn: str) -> dict:
    """A money column pair. Base == txn: single-currency org."""
    return {"txn": txn, "base": f"{float(txn):.4f}"}


def modern(
    tag,
    statecode,
    statuscode,
    practice,
    backlog,
    stage,
    prob,
    est,
    created,
    est_close,
    *,
    actual=None,
    actual_close=NULL,
    interests=NULL,
    forecast_cat=NULL,
    msdyn_fc="100000001",
    marketing="206360019",
    opp_type="206360003",
    campaign=None,
    campaign_name=NULL,
    cosell=NULL,
    customer_type="account",
    owner="A",
    presales="A",
    is_delete=NULL,
    name="Opportunity",
):
    """A post-cutover row, where the jt_* custom schema is populated."""
    year = created[:4]
    est_m = money(est)
    act_m = money(actual) if actual is not None else {"txn": NULL, "base": NULL}
    total = money(actual if actual is not None else est)
    over = {
        "Id": guid(tag),
        "opportunityid": guid(tag),
        "SinkCreatedOn": "2026-09-16 15:47:34.000000",
        "SinkModifiedOn": "2026-09-16 15:47:34.000000",
        "statecode": statecode,
        "statuscode": statuscode,
        "jt_backlogtype": backlog,
        "jt_primaryproduct_1": practice,
        "jt_sales_stage": stage,
        "jt_close_probability": prob,
        "closeprobability": prob,
        "jt_contracttype": "206360000",
        "jt_marketingsource": marketing,
        "jt_opportunitytypeoptions": opp_type,
        "jt_opptybpftobrtrigger": "206360000",
        "jt_iscontactdecisionmaker": "206360000",
        "jt_quotedrateoptions": "206360007",
        "jt_interests": interests,
        "jt_forecastcategory": forecast_cat,
        "msdyn_forecastcategory": msdyn_fc,
        "msft_coselltype": cosell,
        "estimatedvalue": est_m["txn"],
        "estimatedvalue_base": est_m["base"],
        "actualvalue": act_m["txn"],
        "actualvalue_base": act_m["base"],
        "totalamount": total["txn"],
        "totalamount_base": total["base"],
        "totalamountlessfreight": total["txn"],
        "totalamountlessfreight_base": total["base"],
        # System-calculated revenue: header == sum of lines.
        "totallineitemamount": total["txn"],
        "totallineitemamount_base": total["base"],
        "totaldiscountamount": "0.00",
        "totaldiscountamount_base": "0.0000",
        "totallineitemdiscountamount": "0.00",
        "totallineitemdiscountamount_base": "0.0000",
        "totaltax": "0.00",
        "totaltax_base": "0.0000",
        "jt_budget": "50000.00",
        "jt_budget_base": "50000.00",
        # Quantified customer pain — NOT our revenue. Never aggregate into pipeline.
        "jt_issue_1_cost": "250000.00",
        "jt_issue_1_cost_base": "250000.00",
        "createdon": created,
        "modifiedon": "2026-09-16 15:46:10.000000",
        "estimatedclosedate": est_close,
        "actualclosedate": actual_close,
        "customerid": guid(f"account-{tag}"),
        "customerid_entitytype": customer_type,
        "customeridname": f"Account {tag.upper()}",
        "parentaccountid": guid(f"account-{tag}"),
        "parentaccountid_entitytype": "account",
        "parentaccountidname": f"Account {tag.upper()}",
        "parentcontactid": guid(f"contact-{tag}"),
        "parentcontactid_entitytype": "contact",
        "parentcontactidname": f"Contact {tag.upper()}",
        "ownerid": guid(f"user-{owner}"),
        "ownerid_entitytype": "systemuser",
        "owneridname": f"Rep {owner}",
        "owninguser": guid(f"user-{owner}"),
        "owninguser_entitytype": "systemuser",
        "createdby": guid(f"user-{owner}"),
        "createdby_entitytype": "systemuser",
        "createdbyname": f"Rep {owner}",
        "modifiedby": guid(f"user-{owner}"),
        "modifiedby_entitytype": "systemuser",
        "modifiedbyname": f"Rep {owner}",
        "originatingleadid": guid(f"lead-{tag}"),
        "originatingleadid_entitytype": "lead",
        "originatingleadidname": f"Contact {tag.upper()}",
        # NOTE: pre-sales resource is a bookableresource, NOT a systemuser.
        "jt_presalesresource": guid(f"resource-{presales}"),
        "jt_presalesresource_entitytype": "bookableresource",
        "jt_presalesresourcename": f"Presales {presales}",
        "msdyn_predictivescoreid": guid(f"score-{tag}"),
        "msdyn_predictivescoreid_entitytype": "msdyn_predictivescore",
        "jt_lastactivitydate": "2026-09-16 15:40:55.000000",
        "jt_lastactivitydate_date": "1",
        "jt_customeronenoteurl": "<url-redacted>",
        "jt_problemstatement": "<long-text-redacted:~1200chars-with-newlines>",
        "jt_nextsteps": "<long-text-redacted:~400chars-dated-call-log>",
        "customerneed": "<long-text-redacted:~200chars>",
        "name": f"{name} {tag.upper()}",
        "stepname": "2-Qualify",
        "versionnumber": "4210832387",
        "PartitionId": year,
        "IsDelete": is_delete,
    }
    if campaign:
        over.update(
            {
                "campaignid": guid(f"campaign-{campaign}"),
                "campaignid_entitytype": "campaign",
                "campaignidname": campaign_name,
            }
        )
    return row(**over)


def legacy(tag, statecode, statuscode, prob, actual, created, est_close, actual_close):
    """A pre-cutover row: the jt_* custom schema did not exist yet, so it is all NULL.

    This is the single largest analytic constraint on the entity — see ../opportunity.md.
    """
    year = created[:4]
    act = money(actual)
    return row(
        Id=guid(tag),
        opportunityid=guid(tag),
        SinkCreatedOn="2026-09-14 04:34:29.000000",
        SinkModifiedOn="2026-09-14 04:34:29.000000",
        statecode=statecode,
        statuscode=statuscode,
        closeprobability=prob,          # historic range is wider than the modern 3 bands
        jt_close_probability=NULL,      # custom field did not exist
        jt_backlogtype=NULL,
        jt_primaryproduct_1=NULL,
        jt_sales_stage=NULL,
        jt_forecastcategory=NULL,
        jt_interests=NULL,
        actualvalue=act["txn"],
        actualvalue_base=act["base"],
        estimatedvalue=NULL,
        estimatedvalue_base=NULL,
        totalamount="0.00",
        totalamount_base="0.0000",
        totallineitemamount="0.00",
        totallineitemamount_base="0.0000",
        createdon=created,
        modifiedon="2019-08-05 22:15:17.000000",
        estimatedclosedate=est_close,
        actualclosedate=actual_close,
        importsequencenumber="35",
        customerid=guid(f"account-{tag}"),
        customerid_entitytype="account",
        customeridname=f"Account {tag.upper()}",
        parentaccountid=guid(f"account-{tag}"),
        parentaccountid_entitytype="account",
        parentaccountidname=f"Account {tag.upper()}",
        ownerid=guid("user-L"),
        ownerid_entitytype="systemuser",
        owneridname="Rep L",
        owninguser=guid("user-L"),
        owninguser_entitytype="systemuser",
        createdby=guid("user-SYS1"),
        createdby_entitytype="systemuser",
        createdbyname="Legacy Import User",
        # Automation as last modifier — why modifiedon is unreliable for staleness.
        modifiedby=guid("user-SYS2"),
        modifiedby_entitytype="systemuser",
        modifiedbyname="RI AppUser",
        msdyn_opportunitykpiid=guid(tag),
        msdyn_opportunitykpiid_entitytype="msdyn_opportunitykpiitem",
        name=f"Legacy Opportunity {tag.upper()}",
        stepname="4-Close",
        overriddencreatedon="2019-05-30 21:08:52.000000",
        versionnumber="19632947",
        PartitionId=year,
    )


ROWS = [
    # 1 — open, single practice, forecast category populated
    modern("r01", "0", "1", "206360000", "206360000", "206360003", "75", "70000.00",
           "2026-09-10 21:19:32.000000", "2026-11-30 00:00:00.000000",
           forecast_cat="206360004"),
    # 2 — open, MULTI-PRACTICE: three practices, semicolon-delimited
    modern("r02", "0", "1", "206360000", "206360000", "206360003", "50", "114000.00",
           "2026-09-14 16:58:38.000000", "2026-10-09 00:00:00.000000",
           interests="206360004;206360007;206360009", owner="B", presales="B"),
    # 3 — open, MULTI-PRACTICE: two practices
    modern("r03", "0", "1", "206360002", "206360001", "206360003", "75", "50000.00",
           "2026-09-10 17:48:51.000000", "2026-09-30 00:00:00.000000",
           interests="206360004;206360009", owner="C", presales="C"),
    # 4 — won
    modern("r04", "1", "3", "206360002", "206360000", "206360005", "95", "44000.00",
           "2026-08-21 19:28:18.000000", "2026-09-18 00:00:00.000000",
           actual="44000.00", actual_close="2026-09-14 00:00:00.000000",
           forecast_cat="206360004", msdyn_fc="100000005", owner="D", presales="D"),
    # 5 — lost, with a JT CUSTOM status reason under statecode 2
    modern("r05", "2", "206360002", "206360000", "206360000", "206360003", "50",
           "23305.00", "2026-03-13 00:29:58.000000", "2026-09-30 00:00:00.000000",
           actual_close="2026-09-16 00:00:00.000000", forecast_cat="206360005",
           msdyn_fc="100000006", owner="E", presales="E"),
    # 6 — closed with OOB statuscode 4 (Canceled) under the same statecode 2
    modern("r06", "2", "4", "206360000", "206360000", "206360003", "75", "30000.00",
           "2026-06-10 19:08:01.000000", "2026-09-30 00:00:00.000000",
           actual="0.00", actual_close="2026-09-15 00:00:00.000000",
           forecast_cat="206360005", msdyn_fc="100000006", owner="F", presales="F"),
    # 7 — open, Microsoft co-sell sourced
    modern("r07", "0", "1", "206360000", "206360000", "206360005", "75", "63684.00",
           "2026-06-04 15:44:18.000000", "2026-12-31 00:00:00.000000",
           marketing="206360017", campaign="cosell",
           campaign_name="MSFT Co-sell Inbound", cosell="299600000",
           owner="G", presales="G"),
    # 8 — open, contact as the customer party (B2C shape; exercises polymorphism)
    modern("r08", "0", "1", "206360003", "206360000", "206360004", "50", "8850.00",
           "2026-08-31 15:05:27.000000", "2026-09-30 00:00:00.000000",
           customer_type="contact", owner="H", presales="H"),
    # 9 — TEST DATA living in production; must be excluded in Silver
    modern("r09", "0", "1", "206360000", "206360014", "206360004", "95", "1.00",
           "2025-04-29 15:43:20.000000", NULL,
           actual="0.00", owner="SVC", presales="I", name="Test"),
    # 10 — soft-deleted row; must be filtered on every Bronze read
    modern("r10", "0", "1", "206360000", "206360000", "206360003", "50", "12000.00",
           "2026-05-02 10:15:00.000000", "2026-10-31 00:00:00.000000",
           owner="J", presales="J", is_delete="1"),
    # 11 & 12 — pre-cutover legacy rows: no practice, no backlog type, no stage
    legacy("r11", "1", "3", "20", "2000.00", "2017-05-25 06:00:00.000000",
           "2017-05-26 00:00:00.000000", "2017-05-26 00:00:00.000000"),
    legacy("r12", "2", "4", "100", "14800.00", "2016-07-27 06:00:00.000000",
           "2016-08-19 00:00:00.000000", "2016-09-02 00:00:00.000000"),
]


def main() -> None:
    out = sys.stdout
    out.write("\t".join(HEADER) + "\n")
    for r in ROWS:
        assert len(r) == len(HEADER), f"row width {len(r)} != header {len(HEADER)}"
        assert not any("\t" in v or "\n" in v for v in r), "value contains tab/newline"
        out.write("\t".join(r) + "\n")


if __name__ == "__main__":
    main()
