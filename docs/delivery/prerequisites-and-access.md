# Prerequisites and access

Two purposes: the **pre-sales qualification** questions that must be answered before a
quote, and the **access request list** sent to the customer before Sprint 1.

---

## Part 1 — Pre-sales qualification

Answer all of these before quoting. Each one can change the price, the timeline, or whether
the engagement is deliverable at all.

| # | Question | Why it matters |
|---|---|---|
| 1 | Which Dynamics 365 CE apps are installed and actively used? | Determines which packs can be delivered. Installed ≠ used; a pack against an unused app produces empty reports |
| 2 | **Which Project Operations deployment type?** (Lite / resource-non-stocked / stocked) | **Can drag Finance & Operations into scope.** See [ADR 0003](../decisions/0003-project-operations-scope.md). Mandatory before quoting that pack |
| 3 | Is there an existing Fabric capacity? Which SKU? Trial or paid? | Production needs a paid SKU. SKU affects Power BI licensing and Copilot availability |
| 4 | **What region is the Dataverse environment in, and what region is / would the Fabric capacity be in?** | Region alignment is a hard requirement for Link to Fabric. A mismatch can block the engagement entirely |
| 5 | Is Azure Synapse Link for Dataverse already configured? | Not a blocker, but affects metadata handling. See [`../architecture/ingestion-link-to-fabric.md`](../architecture/ingestion-link-to-fabric.md) |
| 6 | Approximate Dataverse data volume across the relevant tables | Capacity sizing and snapshot cost |
| 7 | How many report consumers, and how many report authors? | Power BI licensing model |
| 8 | What is the fiscal calendar? | Configuration input for `dim_date`; not assumable |
| 9 | Is the organization multi-currency? What is the base currency? | Conformance configuration; multi-currency significantly raises reconciliation care |
| 10 | What row-level security is expected? Does the customer expect Dataverse parity? | Dataverse parity is not achievable. Reset that expectation pre-sales, not at UAT. See [`../architecture/security-and-rls.md`](../architecture/security-and-rls.md) |
| 11 | How heavily customized is the environment — custom tables and columns in reporting scope? | Packaged packs cover standard schema. Custom fields are additional development |
| 12 | Are there separate Dataverse Dev/Test/Prod environments, and is promotion between them expected? | No multi-environment story exists yet — a known gap in [`../offering/roadmap.md`](../offering/roadmap.md#known-gaps-in-the-offering-as-currently-defined) |
| 13 | Does the customer also run Business Central or Finance & Operations? | Portfolio cross-sell, and shapes the architecture conversation |
| 14 | Who is the executive sponsor, and who owns metric definitions? | Fixed-price delivery needs a decision-maker for metric disputes |

**A quote issued without answers to 1, 2, 3, 4, and 10 is a quote at risk.**

---

## Part 2 — Access request list

Sent by the project lead in the welcome email, before Sprint 1.

### Dynamics 365 / Dataverse

| Need | Purpose |
|---|---|
| Access to the Dataverse environment | Schema inspection, validating conformance output against source records |
| Privileges sufficient to configure **Link to Microsoft Fabric** | Enabling the shortcut. Requires elevated Dataverse privileges |
| Ability to enable change tracking on required tables, if not already enabled | Table eligibility for the link |
| A named contact who can confirm record-level questions | Reconciliation |

> `<!-- VERIFY -->` Confirm the exact Dataverse security roles and privileges currently
> required to configure Link to Fabric, and enumerate them here explicitly. Requesting
> "System Administrator" as a blanket ask is both unnecessary and likely to be refused by a
> security-conscious customer — least privilege applies to us too.

### Microsoft Fabric / Power BI

| Need | Purpose |
|---|---|
| Fabric capacity assigned and available | All platform work |
| Permission to create workspaces, or two workspaces pre-created | `JTA-<Customer>-Platform`, `JTA-<Customer>-Reporting` |
| Workspace admin on both | Deploying notebooks, lakehouse, models, reports |
| Power BI tenant settings permitting the required features | Varies by tenant; check early |
| Named test users covering each intended RLS role | RLS validation |

### Azure / identity

| Need | Purpose |
|---|---|
| An **app registration** with defined permissions for scheduled and automated connections | Automation must not run as an interactive user identity |
| Accounts for the delivery team, scoped to the engagement | Least privilege, removable at handoff |

### Business inputs

| Need | Purpose |
|---|---|
| Fiscal calendar definition | `dim_date` |
| Base currency and currencies in use | Currency conformance |
| Business unit / territory structure | `dim_owner`, RLS |
| Branding assets — logo, colors | Report branding |
| Agreed RLS pattern per pack | Security implementation |
| Snapshot retention preference | Cost and configuration |

---

## Access principles

- **Least privilege.** Request the minimum needed for the tasks in the playbook. Do not
  ask for blanket administrative access as a convenience.
- **Named, scoped, time-bound.** Delivery accounts are individual, scoped to the
  engagement, and removed at handoff.
- **Automation uses an app registration**, never a personal or interactive account.
- **No credentials in this repository.** Not in configs, not in notebooks, not in
  documentation. No tenant IDs, environment URLs, workspace IDs, or app registration IDs
  either.
- **No customer data leaves the customer tenant.** No extracts, no screenshots containing
  real records.
- **Access changes in a customer tenant follow the customer's change process**, not
  JourneyTeam's.
