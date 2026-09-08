# Service-Account Google Access

Service account: `lh2-bot-351@lh2-pipeline.iam.gserviceaccount.com` (key `lh2-pipeline-9982aa4422f5.json`).
_Last verified **2026-07-31** — access re-tested live._

## ✅ Currently accessible (2)

| Name | Type | Write? | ID |
|---|---|---|---|
| **Tracxn** | Sheet | ✅ | `12BLV3nv1d9Is4UHN113YVhiTBNilHe-9phIMMCEKS4A` |
| **Private Codebase Tracker** | Sheet | read-only | `1B9in9qK1V3IyjoyjYSqwn0gGRyoP9qVlMBGKKheoEhM` |

## ❌ Access REVOKED since 2026-07-29 (3)

Previously shared, now returning **HTTP 403 "caller does not have permission"**:

| Name | Type | ID |
|---|---|---|
| **Supply Funnel SoP** | Doc | `1aj-d_IlHFyHOUdnrgHYc5mb6gpAnIijORZt8Vyna5j4` |
| **Outflo Reachout** | Sheet | `1CDgrOx72H9b9uw_A2OdzDWKAJMF-KwnFSOETbDoTtP0` |
| **ITservices_ScrapedLeads** | Sheet | `19PE9VroacFFaeATFgEqmj0jDuU2PRJSzxZyVypBPjLo` |

**The key is still valid** — it authenticates and reads the two sheets above. This is a **sharing change on those three files**, not a dead credential. `drive.files().list()` now returns only the 2 files above.

**To restore:** share each file with `lh2-bot-351@lh2-pipeline.iam.gserviceaccount.com` (Editor for the SoP doc / Outflo Reachout if we need to write back).

## Notes
- The SA **cannot create new Drive files** (no Drive storage of its own) — it only reads/writes files explicitly shared with it.
- Quick re-test: list Drive files for the SA — anything not in that list is inaccessible.
- The **OutFlo "Calling Guide" section was appended to the Supply Funnel SoP on 2026-07-29**, while access still worked. That content is in the doc; we just can't read or update it now.
