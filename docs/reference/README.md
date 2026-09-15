# Reference

Analysis of existing artifacts that inform the offering — what a system does today, what
its business rules are, and what a replacement has to reproduce.

| Document | Source artifact |
|---|---|
| [`jtp-excel-pipeline-report.md`](jtp-excel-pipeline-report.md) | JourneyTeam's Sales Weekly Pipeline Report (Excel, macro-enabled) — the report the Sales pack dashboard replaces |

## Rules for this folder

1. **Structure, not data.** These documents record schemas, taxonomies, metric
   definitions, business rules, and report layouts. They do **not** reproduce customer
   names, employee names, or actual figures.
2. **Source binaries stay out of the repository.** Spreadsheets, extracts, and exports
   containing real data live in their own controlled location and are referenced here by
   filename and date. Git history is permanent and this repository is pushed to GitHub, so
   a committed file cannot be cleanly withdrawn.
3. **A redacted structural copy is acceptable** where the layout itself is worth
   preserving — field names, taxonomies, and reference tables retained, data tabs emptied.
4. **Record the business rules, especially the undocumented ones.** The rules encoded in a
   working spreadsheet are usually the most valuable thing in it and the hardest to
   recover by interview. Capturing them is the point of this folder.

## Why analyse a spreadsheet at all

An operational report that people actually use every week is a better requirements
statement than any interview. It shows which metrics survived contact with the business,
which business rules were worth the effort to encode, and — from what has broken in it —
what the users wanted and could not sustain by hand.
