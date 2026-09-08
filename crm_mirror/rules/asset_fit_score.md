# Asset-Fit Scores — `codebase_fit` & `opsdata_fit`

A **second layer** on top of the Tracxn [distress score](tracxn_distress_score.md). Distress only answers
*"is this company dying, cheap, and reachable?"* — it says **nothing** about *"do they own a thing worth
buying?"* This layer answers that, and it does so **twice**, because LH2 buys one of two different assets:

1. a dormant **pre-2024 software codebase**, or
2. the company's **internal operating know-how** — the reusable blueprint for *running* that kind of business: SOPs, playbooks, process docs, internal tooling/workflows, org & vendor setup. **Not** consumer/product analytics — the *company's own* operational machinery.

Those two buy-modes want **almost opposite things**, so they get **two independent scores**.

```
target quality  =  distress (already ranked)  ×  asset_fit
                                                 ├─ codebase_fit   (0–100)
                                                 └─ opsdata_fit    (0–100)
```

Script: [`crm_mirror/enrich/asset_fit.py`](../enrich/asset_fit.py) → writes
[`crm_mirror/enrich/asset_scores.json`](../enrich/asset_scores.json).
Run: `python asset_fit.py --limit 100` (resumable; checkpoints after every company).

---

## Why two scores (they pull opposite ways)

`opsdata_fit` measures **internal operating know-how** (how they ran the business), and **operating scale is
king** — a company only builds real SOPs/playbooks/process/tooling if it actually *ran a sizeable operation
for years*. It is **not** about consumer/product data.

| Axis | **codebase_fit** rewards | **opsdata_fit** rewards |
|---|---|---|
| Team size | **small** eng team that shipped a clean product (cheap, simple IP transfer) | **large headcount** — a real multi-function operation to run (**KING signal**) |
| Longevity | doesn't care | **years actually operating** ⇒ matured, documented processes |
| Revenue history | modest is fine | **real revenue/transactions** ⇒ they truly operated (not just funded & died) |
| Business model | horizontal SaaS, infra, dev-tools | **ops-intensive**: logistics, delivery, fulfilment, commerce, manufacturing, field-services (secondary bonus) |
| Product type | a real **software product** (not an agency shell) | a company that **ran an operation** worth reverse-engineering |

A tiny dead dev-tools startup = great codebase, no operating know-how. A dead multi-city logistics/delivery
company = mediocre code, **gold** operating playbook. Same distress score — very different asset scores.
(Funding raised is **de-emphasised** — money raised ≠ operations run.)

---

## Inputs per company

| Source | Cost | Gives |
|---|---|---|
| **Wayback CDX** (`web.archive.org`) | free | product age (**pre-2024 proof**), death timing, capture count |
| **Homepage text** — live site, else an **in-lifespan Wayback snapshot** | free | what the product actually was |
| **Claude (Haiku)** classification | Anthropic key | company_type, real-product?, sector, codebase/ops value, domain-reuse flag, outreach angle |
| **Tracxn funded/unfunded tab** (joined by name) | free | peak **employee count**, **years operating**, revenue (operating scale for ops-data) |

### Two traps the snapshot logic handles (learned the hard way)
- **Post-death parked/sold domains.** A deadpooled company's *current* domain is usually parked or sold, so
  we **skip the live site for deadpooled companies** and reconstruct the product from Wayback.
- **Domain reuse.** `stoa.com` was a wedding-speech directory before edtech Stoa bought it; `oyerickshaw.com`
  is now a coffee shop. We **bound Wayback snapshots to `[founded_year … founded_year+7]`** so we read the
  *right* company, and Claude sets `matches_company:false` if the page is clearly a different business
  (→ `domain_reuse`, sent to manual **review**, not scored).

---

## `codebase_fit` (0–100)

Fires only if the company is **not a services agency** (hard-drop, see below).

| Component | Points | Source |
|---|---|---|
| Claude `codebase_value` (0–10 → ×6) | up to **60** | how real & self-built the software product is (10 = substantial SaaS/platform, 3 = thin wrapper, 0 = none) |
| Existed **pre-2024** (`first_capture_year ≤ 2023`) | **+12** | Wayback |
| **Mature** codebase (`first_capture_year ≤ 2020`) | **+8** | Wayback |
| Product type = `product` / `infra_devtools` | **+12** (marketplace +6) | Claude |
| **Small real team** (2–40 employees) | **+8** | Tracxn — clean, cheap-to-transfer code |

Capped at 100.

## `opsdata_fit` (0–100) — internal operating know-how

Scale-first: real operating footprint (headcount + years + revenue) dominates; the Claude read supports it;
sector is a small bonus.

| Component | Points | Source |
|---|---|---|
| **Peak headcount** — tiered (≥200→35, ≥100→30, ≥50→24, ≥20→16, ≥10→9, ≥5→4) | up to **35** (KING) | Tracxn `Total Employee Count` — a big team ⇒ a real multi-function operation |
| **Years operating** (`× 2`) | up to **12** | founded → deadpooled/last-funding/last-capture; longer ⇒ matured processes |
| **Real revenue** (log-scaled) | up to **8** | Tracxn `Annual Revenue` — they truly operated, not just raised |
| Claude `opsdata_value` (0–10 → ×3) | up to **30** | read of operating machinery from the page (multi-city ops, teams, fulfilment, complexity) |
| **Ops-intensive** business model | **+9** | Claude `ops_intensive` — logistics/delivery/commerce/manufacturing/field-services (secondary) |

Capped at 100. Extra per-row fields: `peak_employees`, `years_operating`, `ops_intensive`.
**Funding is intentionally excluded** — money raised is not operations run.

---

## Hard filter: services-agency drop

`company_type = services_agency` ⇒ **`codebase_fit = 0`** and dropped from the codebase list.
Definition is strict: a consultancy / dev-shop that builds software **for clients** with **no product of its
own**. A company with its **own** thin/simple product is `product`, **not** an agency (this is why NuShala, a
thin fee-collection fintech, scores as a product, not a shell). Agencies with real ops data can still surface
on the ops-data track.

## Status flags (per row)

| Flag | Meaning | Handling |
|---|---|---|
| `services_shell:true` | explicit agency, no own product | dropped from codebase list |
| `domain_reuse:true` | page is a different business (domain sold/reused) | → manual **review**, not scored |
| `low_data:true` | Claude returned `unknown` (no usable page text + not famous) | **not** dropped — flagged `best_angle:"review"` |
| `best_angle` | `codebase` / `data` / `both` / `skip` / `review` | which pitch to lead with |

---

## How to use the output
- **Codebase outreach:** sort by `codebase_fit` desc, exclude `services_shell`, prefer `best_angle ∈ {codebase, both}`.
- **Ops-data outreach:** sort by `opsdata_fit` desc (operating know-how) — high headcount + years operating + ops-intensive; prefer `best_angle ∈ {data, both}`.
- **Review queue:** `domain_reuse` or `low_data` rows — quick manual check before discarding.
- Both lists are already **distress-ranked**, so a high asset_fit on a high-distress row = a dying company
  with a real, buyable asset and a reachable founder = the ideal target.

## Regenerating / scaling
Currently run on the **top 100** distressed targets (Medium tier + best rank). Widen with `--limit 800`
(the full Medium + best-Low band). `--model sonnet` for a higher-accuracy classify pass on shortlists.
