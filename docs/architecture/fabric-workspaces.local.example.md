# Fabric workspace deep links — TEMPLATE

Copy to `fabric-workspaces.local.md` (gitignored) and fill in from your tenant.

**Why this file is not committed:** workspace, lakehouse and capacity IDs identify
JourneyTeam's internal data platform topology. `CLAUDE.md` keeps them out of the
repository. They are not credentials — the links are useless without authentication — but
they are internal infrastructure detail with no reason to be in version control.

Get the IDs with:

```powershell
az rest --method get --url "https://api.fabric.microsoft.com/v1/workspaces" --resource "https://api.fabric.microsoft.com" | ConvertFrom-Json | Select-Object -ExpandProperty value | Select-Object displayName, id, capacityId
```

```powershell
az rest --method get --url "https://api.fabric.microsoft.com/v1/workspaces/<workspaceId>/lakehouses" --resource "https://api.fabric.microsoft.com" -o json
```

On Windows, avoid `az … --query`; PowerShell mangles JMESPath. Pipe to
`ConvertFrom-Json` instead.

---

## Bronze — shared, read-only

| | |
|---|---|
| Workspace | `Data Hub` |
| Folder | `1-Bronze` |
| Lakehouse | `LH_BRONZE_DynamicsLink_PROD` |
| Workspace ID | `<fill in>` |
| Lakehouse ID | `<fill in>` |
| Link | `https://app.powerbi.com/groups/<workspaceId>/lakehouses/<lakehouseId>?experience=power-bi` |
| SQL endpoint | `<fill in>` |

> **Production Dynamics Link, shared with other consumers.** Read-only. Changing its table
> set or configuration is a change-controlled action on shared Production infrastructure —
> see [`jt-medallion-topology.md`](jt-medallion-topology.md) §2.

## Silver

| | |
|---|---|
| Workspace | `DAI Data Hub` |
| Lakehouse | `DAI_Silver_LH` |
| Workspace ID | `<fill in>` |
| Lakehouse ID | `<fill in>` |
| Link | `https://app.powerbi.com/groups/<workspaceId>/lakehouses/<lakehouseId>?experience=power-bi` |
| SQL endpoint | `<fill in>` |

## Gold

| | |
|---|---|
| Workspace | `DAI Data Hub` |
| Lakehouse | `DAI_Gold_LH` |
| Workspace ID | `<fill in>` |
| Lakehouse ID | `<fill in>` |
| Link | `https://app.powerbi.com/groups/<workspaceId>/lakehouses/<lakehouseId>?experience=power-bi` |
| SQL endpoint | `<fill in>` |

## Capacity

| | |
|---|---|
| Capacity ID | `<fill in>` |
| Region | West US |
| Shared with | Several other practice and delivery workspaces — size notebook runs accordingly |
