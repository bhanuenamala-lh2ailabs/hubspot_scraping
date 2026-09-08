# AI Labs founder-research batches (preserved 2026-07-31)

Salvaged from the older `ITserviceCompLeadQ/` project folder before it was deleted.
Everything else in that folder was superseded by the current `lh2-pipeline/`
(identical `buildInstructions.md`; newer PROJECT_CONTEXT/TARGETING_CRITERIA/README;
3 CI workflows vs 1; DB 5,369 companies vs 2,753).

## Why this was kept — the one measured insight

An LLM was asked to research founders for a batch of **funded / deadpooled Indian startups**:

| Metric | Result |
|---|---|
| Companies researched | **80** |
| Founder found | **59 (74%)** |
| Confidence | 31 high · 26 medium · 23 low |
| With LinkedIn URL | 44 |

**This contradicts the 0/12 result we measured on obscure IT-services SMEs on 2026-07-31.**
The difference is **notability, not method**:

- **Funded / venture-backed / notable startups** → the model knows them → **~74% hit rate**
- **Small unfunded IT-services agencies** (WebOsmotic, V2Soft, Teknotrait…) → not in training data → **~0%**, and the model correctly declines to guess

### How to use this
- For the **distressed-startup line** (Tracxn-sourced, funded companies): LLM founder-research is a
  legitimate, cheap first pass — but **keep the confidence field** and treat `low` as unverified.
- For the **IT-services line**: do **not** rely on it. Those founders must come from a people
  database (Apollo/SignalHire) — see `LEAD_SOURCING_PROBLEM_BRIEF.md`.
- Always verify before outreach: a `high` confidence guess is still a guess.

## Files
| File | What |
|---|---|
| `batch_*.json` | input batches (company lists) |
| `results_batch_*.json`, `results_pilot.json` | output: `{company, founder, role, linkedin, confidence}` |
| `ailabs_research_results.csv` | consolidated results (80 rows) |
| `ailabs_todo_filled.csv` | 108 deadpooled companies — sector, funding, revenue, employees, founder, LinkedIn, phone, year founded/deadpooled |
| `indian_it_services_firms.csv` | 97 IT-services firms with founder + verified LinkedIn + phone |

No script in the old repo generated these (`grep ailabs src/` → nothing) — it was an ad-hoc batch run.
