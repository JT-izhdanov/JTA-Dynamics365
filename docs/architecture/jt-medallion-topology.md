# JourneyTeam's deployed medallion topology

The actual Fabric layout the JTP first build works in, as distinct from the product's
reference design in [`medallion-design.md`](medallion-design.md).

> **Identifiers are deliberately absent.** Workspace, lakehouse and capacity IDs are not
> recorded here — see `CLAUDE.md`. Deep links live in
> `docs/architecture/fabric-workspaces.local.md`, which is gitignored; the committed
> template is [`fabric-workspaces.local.example.md`](fabric-workspaces.local.example.md).

## Layout

| Layer | Workspace | Folder | Lakehouse |
|---|---|---|---|
| **Bronze** | `Data Hub` | `1-Bronze` | `LH_BRONZE_DynamicsLink_PROD` |
| **Silver** | `DAI Data Hub` | — | `DAI_Silver_LH` |
| **Gold** | `DAI Data Hub` | — | `DAI_Gold_LH` |

Both workspaces sit on the same Fabric capacity, in the same region (West US), which makes
cross-workspace shortcuts between Bronze and Silver straightforward.

## Three observations that matter

### 1. This diverges from the product's reference design

[`medallion-design.md`](medallion-design.md) specifies **one lakehouse** (`jta_lakehouse`)
with three schemas (`bronze` / `silver` / `gold`) in a single platform workspace. The
deployed reality is **three lakehouses across two workspaces**.

Both are legitimate. The trade-offs:

| | One lakehouse, three schemas | Three lakehouses, two workspaces |
|---|---|---|
| Cross-layer queries | Trivial — same SQL endpoint | Need shortcuts or cross-database references |
| Layer-level access control | Schema grants only | **Workspace and item-level permissions per layer** |
| Bronze reuse across practices | Not designed for it | **Bronze is shared infrastructure** |
| Deployment pipelines | One workspace to promote | Per-workspace promotion |
| Capacity attribution | Single workspace | Per-workspace visibility |

**The deployed shape is arguably better for JourneyTeam**, because Bronze is a shared
asset — a central `Data Hub` Dynamics Link that several practices can consume, rather than
one copy per project. That is a real argument for changing the product design rather than
treating JT as a special case.

**This needs an ADR.** Either the reference design adopts the split-workspace shape, or it
documents both as supported topologies with guidance on when to pick which. Leaving
`medallion-design.md` describing a single lakehouse while every build uses something else
is how a reference architecture becomes fiction.

### 2. Bronze is the **production** Dynamics Link

The lakehouse name says `_PROD`. So Silver and Gold are being built in a practice
workspace, sourced from the **production** Dataverse link.

Consequences:

- **Reads are production reads.** Fine — read-only observation of Production is the
  expected pattern, and profiling is exactly that.
- **Bronze is not ours to change.** It is shared infrastructure serving other consumers.
  Adding tables to the Link to Fabric table set, or altering its configuration, affects
  them and is a change-controlled action on a Production asset — not a decision to take
  inside this build.
- **The "sandbox" framing applies to Silver and Gold, not Bronze.** Work in
  `DAI Data Hub` freely; treat `Data Hub` as read-only.
- **Profiling results describe production data**, which is what makes them valid for the
  offering — and also why the outputs carry the same confidentiality as the source.

### 3. Bronze in a shared workspace changes the offering's deployment topology

The reference design assumes a per-customer `JTA-<Customer>-Platform` workspace holding
everything. If Bronze is instead a shared, centrally-owned Dynamics Link, then for a
*customer* engagement the equivalent question is whether Bronze lives in the customer's own
platform workspace or in a shared one they already have.

For customer deliveries the per-customer shape is almost certainly right — a customer has
no reason to share Bronze with anyone. But the JT internal build will *not* exercise that
shape, which means **the deployment procedure validated here is not quite the procedure a
customer engagement follows.** Worth naming now rather than discovering it on the first
paid delivery.

## Implications for the platform notebooks

The notebooks in [`../../platform/notebooks/`](../../platform/notebooks/) currently assume
`jta_lakehouse` with three schemas. Against this topology they need:

- **Bronze reads** pointed at the `Data Hub` lakehouse — via a shortcut into
  `DAI_Silver_LH`, or a cross-workspace reference
- **Silver writes** into `DAI_Silver_LH`
- **Gold writes** into `DAI_Gold_LH`
- **Lakehouse names parameterised** in `platform/config/`, not hard-coded — the current
  `LAKEHOUSE = "jta_lakehouse"` constant in `_common.py` needs to become configuration,
  with separate entries per layer

That last point is a real code change, and it is the right one regardless: a single
hard-coded lakehouse name was always going to break on the first customer whose naming
convention differed.

## Open items

| # | Item | Blocks |
|---|---|---|
| 1 | **ADR on topology** — does the reference design adopt the split-workspace shape, support both, or stay single-lakehouse? | `medallion-design.md` credibility; notebook structure |
| 2 | Parameterise lakehouse names per layer in `platform/config/` | Every notebook |
| 3 | Confirm which Dataverse tables the shared Bronze link already carries | Whether the Sales pack's table set is already present or needs a change request against shared infrastructure |
| 4 | Confirm read access to `Data Hub` for the build identity | Everything downstream |
| 5 | Shortcut vs cross-workspace reference for Bronze → Silver | Notebook 10 and all Silver builds |
