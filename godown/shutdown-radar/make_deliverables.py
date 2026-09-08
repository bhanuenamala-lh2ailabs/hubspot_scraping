# -*- coding: utf-8 -*-
"""Write the four deliverables off the finished Wayback pass.

  1. LH2_buy_list.csv        voluntary_clean AND likely AND (verified|probable), best first
  2. LH2_secondary_list.csv  voluntary_clean AND likely, brochure_only + domain_not_found
  3. run_report.md           the full cross-tab, rates, caveats and open items
  4. RESUME_HERE.md          honest read on whether more MCA volume is worth chasing

`error` rows are kept OUT of both lists and reported separately: they are the rows CDX never
answered for, and shipping them in either list would state something we did not learn.
"""
import os, csv, json, collections, datetime

SRC="data/out/LH2_dead_companies_with_codebases.csv"
FULL="data/out/_wayback_allrows.csv"           # the all-rows file run_wayback.py writes
OUT_BUY="data/out/LH2_buy_list.csv"
OUT_SEC="data/out/LH2_secondary_list.csv"
OUT_ERR="data/out/LH2_unresolved_errors.csv"

rows=list(csv.DictReader(open(FULL,encoding="utf-8-sig")))
FIELDS=list(rows[0].keys())

def n(r,k,d=0):
    try: return int(float(r.get(k) or d))
    except Exception: return d

vc_likely=[r for r in rows if r["title_cleanliness"]=="voluntary_clean" and r["codebase_band"]=="likely"]
buy=[r for r in vc_likely if r["product_evidence"] in ("verified_product","probable_product")]
sec=[r for r in vc_likely if r["product_evidence"] in ("brochure_only","domain_not_found")]
err=[r for r in rows if r["product_evidence"]=="error"]

RANKP={"verified_product":0,"probable_product":1}
buy.sort(key=lambda r:(RANKP.get(r["product_evidence"],9), -n(r,"codebase_score"), -n(r,"product_score")))
sec.sort(key=lambda r:({"brochure_only":0,"domain_not_found":1}.get(r["product_evidence"],9), -n(r,"codebase_score")))
err.sort(key=lambda r:-n(r,"codebase_score"))

def write(path, rs):
    with open(path,"w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS,extrasaction="ignore")
        w.writeheader(); w.writerows(rs)
    return path

write(OUT_SEC,sec); write(OUT_ERR,err); write(OUT_BUY,buy)   # buy last: overwrites the all-rows file
print(f"1. {OUT_BUY:<42}{len(buy):>6} rows")
print(f"2. {OUT_SEC:<42}{len(sec):>6} rows")
print(f"   {OUT_ERR:<42}{len(err):>6} rows  (unresolved — in neither list)")

# ---------------- report ----------------
ct=collections.Counter((r["title_cleanliness"],r["codebase_band"],r["product_evidence"]) for r in rows)
EVS=["verified_product","probable_product","brochure_only","domain_not_found","error"]
pe=collections.Counter(r["product_evidence"] for r in rows)
resolved=sum(pe[k] for k in ("verified_product","probable_product","brochure_only"))
rej=[r for r in rows if r.get("domains_rejected")]
vcf=collections.Counter(r.get("vc_funded") or "(blank)" for r in buy)
sect=collections.Counter(r.get("sector") or "(unknown)" for r in buy)
states=collections.Counter(r.get("state") or "(unknown)" for r in buy)
yrs=collections.Counter(r.get("shutdown_year") or r.get("incorporated") or "?" for r in buy)
app=collections.Counter(s for r in buy for s in (r.get("app_signals") or "").split(",") if s)

L=[]; A=L.append
A("# shutdown-radar — Wayback pass, final report\n")
A(f"Generated {datetime.datetime.now().isoformat(timespec='seconds')}\n")

A("## Headline\n")
A(f"- **Buy list: {len(buy)} companies** — `voluntary_clean` AND `likely` AND real product evidence")
A(f"  - {sum(1 for r in buy if r['product_evidence']=='verified_product')} verified_product, "
  f"{sum(1 for r in buy if r['product_evidence']=='probable_product')} probable_product")
A(f"- Secondary list: {len(sec)} — same title/codebase quality, no product evidence yet")
A(f"- Unresolved (`error`): {len(err)} — CDX never answered; in neither list")
A(f"- Domain resolved for **{resolved:,} / {len(rows):,} = {100*resolved//len(rows)}%**\n")

A("## Cross-tab — title_cleanliness × codebase_band × product_evidence\n")
A("| title | codebase | verified | probable | brochure_only | domain_not_found | error |")
A("|---|---|---:|---:|---:|---:|---:|")
for t in ("voluntary_clean","clean","consent_risk","encumbered"):
    for b in ("likely","possible"):
        if not any(ct[(t,b,e)] for e in EVS): continue
        A(f"| {t} | {b} | " + " | ".join(str(ct[(t,b,e)]) for e in EVS) + " |")
A("")
A("The buy list is the top-left cell pair: `voluntary_clean` × `likely` × (verified + probable).\n")

A("## The floor caveat — read this before trusting any negative\n")
A(f"Only 2 of the {len(rows):,} rows carry a **known** domain. For every other row the domain is")
A("GUESSED from the legal name. Therefore a hit is strong positive evidence, but a miss is")
A("**ambiguous** — wrong guess, or genuinely no site, and we cannot tell which. That is why the")
A("negative verdict is named `domain_not_found` and never \"no web presence\".")
A(f"\n**Consequence: {len(buy)} is a floor, not a ceiling.** Companies that shipped real software but")
A("whose domain we failed to guess are sitting in the secondary list, indistinguishable from")
A("companies that never had a site.\n")

A("## Guard rejections — domains thrown out as belonging to someone else\n")
A(f"- {len(rej):,} rows had at least one candidate domain rejected because its first archive")
A("  capture predates the company's incorporation by more than a year.")
A("- This guard exists because the first run hit a **100% domain-match rate** — `swift.com`")
A("  matched \"Swift Shipping and Freight Logistics\" with a 28.5-year capture span. A 100% hit")
A("  rate on guessed domains is not a result, it is a bug. Post-guard the rate is 27%.")
A("- A generic-stem blocklist does the same job earlier: single dictionary words (`apex`,")
A("  `swift`, `data`, `prime`…) are never guessed, because someone else owns them.\n")

A("## The `error` bucket — a bug found and fixed mid-run\n")
A("`cdx()` returns `None` on any network failure, and `check()` was reporting that as")
A("`domain_not_found` — identical, in the checkpoint, to archive.org genuinely having nothing.")
A("Because the runner skips anything already checkpointed, those rows would have been")
A("**permanently** written off as \"no site\".")
A("\nDetection: `cdx()` only writes its disk cache on a *successful* fetch, so a genuine miss")
A("leaves a cached empty answer while a network failure leaves nothing. Splitting the miss")
A("bucket that way exposed **429 rows that had never been answered**. They were purged from the")
A("checkpoint and re-queried against fixed code that now reports `error`, not `domain_not_found`.")
A(f"\nRecovered by the re-query: buy list 114 → **{len(buy)}**, domain resolution 21% → "
  f"**{100*resolved//len(rows)}%**. {len(err)} rows remain genuinely unanswered.\n")

A("## Buy-list composition\n")
A("| VC funded | Companies |\n|---|---:|")
for k,v in vcf.most_common(): A(f"| {k} | {v} |")
A("\n| Top sectors | Companies |\n|---|---:|")
for k,v in sect.most_common(8): A(f"| {k} | {v} |")
A("\n| Top states | Companies |\n|---|---:|")
for k,v in states.most_common(8): A(f"| {k} | {v} |")
A("\n| Product signal archived | Companies |\n|---|---:|")
for k,v in app.most_common(): A(f"| `{k}` | {v} |")
A("")

A("## Top 25 of the buy list\n")
A("| Company | CIN | Codebase | Product | Signals | Span |")
A("|---|---|---:|---|---|---:|")
for r in buy[:25]:
    A(f"| {r['company'][:38]} | {r['cin'] or '—'} | {r['codebase_score']} | "
      f"{r['product_evidence'].replace('_product','')} | {r.get('app_signals','')[:34]} | "
      f"{r.get('capture_span_years','')}y |")
A("")

A("## Open items — not blockers, but not done\n")
A("1. **`Work Item ≡ STK-2 SRN` is INFERRED, not proven.** The `voluntary_clean` basis rests on")
A("   1,626 × s.248(5) + 1,017 × STK-2 and **zero** suo-motu s.248(1) rows across 329 operative")
A("   per-state notices. The remaining gap is that the Work Item number is *assumed* to be the")
A("   STK-2 SRN. A ~20-row sample against MCA SRN lookup would close it. Deferred by decision,")
A("   not by oversight.")
A(f"2. **{len(err)} `error` rows** never got a CDX answer even after re-query. Worth one more pass")
A("   on a different day before treating them as anything.")
A("3. **Domain guessing is the binding constraint at 27%.** More MCA volume does not help until")
A("   this improves — see RESUME_HERE.md.")
A("4. RSS is a forward monitor only: feeds carry 1–2 days of items, so they contribute nothing")
A("   retrospectively. The earlier User-Agent hypothesis was wrong; the feeds work fine.\n")

open("data/out/run_report.md","w",encoding="utf-8").write("\n".join(L))
print("3. data/out/run_report.md")

# ---------------- resume ----------------
R=[]; B=R.append
B("# RESUME_HERE — shutdown-radar\n")
B(f"Last run {datetime.date.today().isoformat()}. Wayback pass complete over {len(rows):,} companies.\n")
B("## Where it stands\n")
B(f"- **{len(buy)} companies** on the buy list ({OUT_BUY})")
B(f"- **{len(sec)}** on the secondary list ({OUT_SEC})")
B(f"- **{len(err)}** unresolved ({OUT_ERR})")
B(f"- Domain resolution **{100*resolved//len(rows)}%**\n")
B("## Is more MCA volume worth chasing? — honest read: NO, not yet\n")
B("The instinct is to widen the funnel: pull the 2022–2023 MCA back-catalogue and double the")
B("candidate count. The numbers say that is the wrong next move.\n")
B(f"**The binding constraint is domain resolution, not candidate supply.** We resolve a domain")
B(f"for {100*resolved//len(rows)}% of companies. Of {len(rows):,} candidates, only {resolved:,} produced any web")
B(f"evidence at all, and only {len(buy)} cleared the title and codebase filters on top of it.")
B("Doubling the input at a fixed 27% resolution buys roughly another 120 buy-list rows while")
B("doubling every downstream cost — and leaves the same 73% blind spot.\n")
B("**What actually moves the number**, in order of expected return:\n")
B("1. **Fix domain resolution.** Today we guess from the legal name and try `.com`/`.in`. Real")
B("   sources exist: MCA filings carry an email domain; DPIIT records carry websites; Tracxn")
B("   and the deadpool sheets carry domains for companies we already hold. Joining those in")
B("   converts guesses into knowns, and every converted row is one where a miss finally means")
B("   something. This is the single highest-leverage change available.")
B("2. **Re-run the `error` rows on a different day.** Cheap, already scripted, may add a few.")
B("3. **Close the STK-2 SRN inference** with a 20-row sample. It is the one load-bearing")
B("   assumption under `voluntary_clean`, which every list here is filtered on.")
B("4. **Only then** widen to the MCA back-catalogue — with better domain resolution, the same")
B("   crawl yields materially more per candidate.\n")
B("## What NOT to do\n")
B("- Do not treat `domain_not_found` as \"no web presence\". It is ambiguous by construction.")
B("- Do not remove the incorporation-year guard or the generic-stem blocklist. Without them the")
B("  hit rate goes to 100% and every one of those hits is a different company.")
B("- Do not let a 100% success rate anywhere in this pipeline pass without investigation.\n")
open("data/out/RESUME_HERE.md","w",encoding="utf-8").write("\n".join(R))
print("4. data/out/RESUME_HERE.md")
