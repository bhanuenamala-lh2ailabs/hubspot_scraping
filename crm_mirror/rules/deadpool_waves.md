# Source — Deadpool waves (dead Indian startups, by sector cohort)

**What it is.** A hand-researched table of Indian startups that died, organised by *wave*:
a sector, its surviving winners, and the companies that lost. Fifteen waves, 77 rows,
75 unique companies. First loaded 2026-08-04.

**Why this source is different.** Every other source finds companies that are *alive and
struggling*. This one starts from companies that are already dead, where the codebase has
been dormant for years and the founder has moved on. The founder is usually reachable at a
*new* company, has no emotional attachment left to the old asset, and there is no board or
customer to consult. That is the shortest path to a signed release we have.

Raw table: [`crm_mirror/sources/deadpool_waves/deadpool_waves.tsv`](../sources/deadpool_waves/deadpool_waves.tsv) — never edit the derived CSVs, regenerate them.

---

## The three gates

Applied by `crm_mirror/enrich/build_deadpool_waves.py`, recorded per row so any verdict can
be audited later.

| Gate | Test | Result | n |
|---|---|---|---|
| **ALIVE** | company still trades | never target | 1 |
| **IP_HELD** | a large acquirer owns the code — Google, Amazon, BYJU'S, Snapdeal, Future Group | never target: the founder cannot sell what they no longer own | 6 |
| **NO_FOUNDER** | research row says "various" / corporate | hold, then recover the founder from SignalHire (pass 2) | 25 |
| — | dead or dormant **and** a named founder | **TARGET** | 43 |

`Meru Cabs` is the only ALIVE row. The IP_HELD six are WhiteHat Jr, Toppr, Amazon Academy,
Simsim, Shopo and FabFurnish — all real deaths, but the codebase went with the acquirer.

## Resolving people — `resolve_deadpool_founders.py`

The research table has **no phone numbers at all**, so every contact detail comes from
SignalHire. Two passes, because the two problems are different:

**Pass 1 — the 91 named founders.** Query `fullName` **+** `currentPastCompany` together.
That pair is decisive: "Navneet Singh" alone is hopeless, but +PepperTap returns exactly one
profile reading *PepperTap — Founder & CEO*.

> A company-only search does **not** work here. SignalHire returns ex-employees in arbitrary
> order and the founder sits past the page limit — TaxiForSure returns 75 profiles and
> Aprameya Radhakrishna is not in the first 50. This cost a wasted first attempt; don't repeat it.

No location filter on this query — Manu Rana (Baxi) is in Dubai and an India filter hides
him. Geography is decided later by the phone gate, not here.

**Pass 2 — the 25 "various" companies.** Query `currentPastCompany` and keep profiles
holding a founder-level title *at that company* (Founder / Co-Founder / CEO / COO / MD /
CTO / VP-Eng). This is the only way to put a name to those rows; it recovered **42** people.

**Never accept a namesake.** A hit survives only if the profile's own experience lists the
dead company (`verified_company`), or the name is globally unique and exact (`unique_name`,
flagged). Anything weaker is dropped — a wrong person is worse than no lead.

Cost: **160 searches, 0 credits.** `searchByQuery` spends the daily *search* quota only.

## Pushing — `push_deadpool.py`

- **Hard gate:** SignalHire number → `indian_number.py` → must be `+91` + 10 digits.
  Mobile beats landline (a landline at a dead company reaches nobody).
- **Dedup:** company name vs *every* HubSpot deal name (`data/index/deal_names.json`).
  A deal is the dedup unit — a company record without a deal does not count.
- **Deal name is the company**, never the founder — the company is the pointer.
- **Whole companies go to one owner.** Two callers must never phone the same dead startup,
  so all of a company's founders land with the same person; companies alternate.
- Pipeline `Scraped` / stage `Cold Call` / `scraped_type = "Distressed startups"`.

## First run — 2026-08-04

| | |
|---|---|
| Companies researched | 75 |
| Targetable after gates | 43 + 25 recovered = 68 searched |
| People resolved | 106 (64 named, 42 recovered) |
| Already in HubSpot | 1 (Crejo.Fun) |
| Revealed | 103 — **0 credits**, all cached |
| **Passed the +91 gate** | **92 (100% mobile, 0 landline)** |
| Rejected — no Indian number | 11 |
| **Pushed** | **50 deals / 92 contacts — 25 deals + 46 contacts each to Ishpreet and Shobit** |
| Contacts with LinkedIn URL | 89 / 92 |
| Contacts with email | 88 / 92 |

The 100%-mobile rate is far better than any other source (IT-services runs land ~10%
switchboards). Founders who have moved on are indexed under their *personal* number.

## What is left on the table

- **38 people not pushed** — 11 failed the +91 gate (mostly now abroad), 25 could not be
  told apart from namesakes, 2 absent from SignalHire. See `3_not_pushed.csv`.
- **Companies with nobody found:** Aagar.com, Savemymeds, SpoonJoy, i-lend, 13Karat,
  Bookmeds, Coinome, BTCXIndia. Their pools are tiny or empty in SignalHire.
- **The waves themselves are the reusable asset.** Each row names the *survivors* too;
  a wave with a live winner is evidence the sector's code still has value.

## Rebuild

```bash
python crm_mirror/enrich/build_deadpool_waves.py       # table -> gates -> queue
python crm_mirror/enrich/resolve_deadpool_founders.py  # SignalHire, resumable
python crm_mirror/enrich/push_deadpool.py --dry-run
python crm_mirror/enrich/push_deadpool.py --batch 10
python crm_mirror/enrich/deadpool_sheet.py             # the working sheet
```
