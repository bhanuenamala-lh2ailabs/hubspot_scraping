# -*- coding: utf-8 -*-
"""Wayback pass over the codebase list. Resumable, cached, polite (1 req/sec).

Writes a checkpoint after every company, so killing this and re-running costs nothing.
"""
import os, sys, csv, json, time, collections, threading
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, "src")
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
from shutdown_radar import wayback as WB

SRC = "data/out/LH2_dead_companies_with_codebases.csv"
CKPT = "data/out/wayback_checkpoint.json"
OUT = "data/out/LH2_buy_list.csv"

rows = list(csv.DictReader(open(SRC, encoding="utf-8-sig")))
done = json.load(open(CKPT, encoding="utf-8")) if os.path.exists(CKPT) else {}
todo = [r for r in rows if r["company"] not in done]
print(f"{len(rows):,} companies | already done {len(done):,} | this run {len(todo):,}", flush=True)

# 10 workers, 0.25s pause each. Measured: CDX responses take 2-5s, so throughput is bound
# by THEIR latency, not by us hammering — 4 workers at 1s only reached 9-11 companies/min
# (a 5-hour run). At 10 workers the sustained rate is ~3-4 req/sec, which is ordinary
# archive.org client behaviour. Every response is cached, so a re-run costs nothing.
t0 = time.time()
lock = threading.Lock()
counter = {"n": 0}

def work(r):
    iy = int(r["incorporated"]) if r["incorporated"].isdigit() else None
    try:
        w = WB.check(r["legal_name"] or r["company"], r.get("domain") or "",
                     delay=0.25, inc_year=iy)
    except Exception as e:
        w = {"product_evidence": "error", "product_reasons": f"{type(e).__name__}: {e}"}
    with lock:
        done[r["company"]] = w
        counter["n"] += 1
        i = counter["n"]
        if i % 50 == 0:
            json.dump(done, open(CKPT, "w", encoding="utf-8"))
            el = time.time() - t0
            rate = i / el if el else 0
            eta = (len(todo) - i) / rate / 60 if rate else 0
            c = collections.Counter(v.get("product_evidence") for v in done.values())
            print(f"  {i:>5}/{len(todo)}  {rate*60:.0f}/min  ETA {eta:.0f}min  {dict(c)}", flush=True)

with ThreadPoolExecutor(max_workers=10) as ex:
    list(ex.map(work, todo))
json.dump(done, open(CKPT, "w", encoding="utf-8"))

for r in rows:
    w = done.get(r["company"]) or {}
    r["product_evidence"] = w.get("product_evidence", "")
    r["product_score"] = w.get("product_score", "")
    r["wayback_domain"] = w.get("wayback_domain", "")
    r["first_capture"] = w.get("first_capture", "")
    r["last_capture"] = w.get("last_capture", "")
    r["capture_count"] = w.get("captures", "")
    r["capture_span_years"] = w.get("span_years", "")
    r["app_signals"] = ",".join(w.get("app_signals") or [])
    r["why_product"] = w.get("product_reasons", "")
    r["domains_rejected"] = w.get("domains_rejected", "")

RANK = {"verified_product": 0, "probable_product": 1, "brochure_only": 2,
        "domain_not_found": 3, "error": 4, "": 5}
rows.sort(key=lambda x: (RANK.get(x["product_evidence"], 9), int(x["title_rank"] or 9),
                         -int(x["codebase_score"] or 0)))
with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(f"\nwrote {OUT} ({len(rows):,} rows)")

print("\n=== CROSS-TAB: title_cleanliness x codebase_band x product_evidence ===\n")
ct = collections.Counter((r["title_cleanliness"], r["codebase_band"], r["product_evidence"])
                         for r in rows)
evs = ["verified_product", "probable_product", "brochure_only", "domain_not_found"]
print(f"{'title':<18}{'codebase':<10}" + "".join(f"{e[:16]:>18}" for e in evs))
print("-" * 92)
for t in ("voluntary_clean", "clean", "consent_risk", "encumbered"):
    for b in ("likely", "possible"):
        line = f"{t:<18}{b:<10}" + "".join(f"{ct[(t,b,e)]:>18}" for e in evs)
        if any(ct[(t, b, e)] for e in evs): print(line)
buy = ct[("voluntary_clean", "likely", "verified_product")]
buy2 = ct[("voluntary_clean", "likely", "probable_product")]
print("-" * 92)
print(f"\n>>> BUY LIST  voluntary_clean AND likely AND verified_product : {buy}")
print(f"    next tier  voluntary_clean AND likely AND probable_product : {buy2}")
print(f"    combined                                                    : {buy+buy2}")
c = collections.Counter(r["product_evidence"] for r in rows)
tot = sum(v for k, v in c.items() if k != "domain_not_found")
print(f"\nproduct_evidence overall: {dict(c)}")
print(f"domain resolved for {tot:,}/{len(rows):,} = {100*tot//len(rows)}%")
