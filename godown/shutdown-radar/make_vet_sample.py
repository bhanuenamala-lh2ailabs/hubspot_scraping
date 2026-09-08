# -*- coding: utf-8 -*-
"""A blind sample for manual vetting, plus the answer key kept separately.

The desk vet already filled RELEVANT/WHY/PRIORITY on every judgeable row. Handing that sheet
to a human measures whether they agree with a verdict they can already see — which is worth
nothing. So the sample ships with those columns blank, and with the machine SCORES removed
too, since `product_score 97` anchors just as hard as `Yes` does.

What stays is only what a person can judge for themselves: the archive link, the app paths
found, how long the site lived, sector, state, incorporation year, MCA status.

Stratified across the desk verdicts so the sample contains disagreement candidates from every
band — a sample drawn only from the Yes rows cannot detect a false positive rate.

Usage: python make_vet_sample.py [n_per_band]   (default 20 -> 60 rows)
"""
import csv, os, sys, collections

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
HERE = os.path.dirname(os.path.abspath(__file__))
OUTD = os.path.join(HERE, "data", "out")
SRC  = os.path.join(OUTD, "LH2_vetting_sheet.csv")
N    = int(sys.argv[1]) if len(sys.argv) > 1 else 20

rows = list(csv.DictReader(open(SRC, encoding="utf-8-sig")))
# only rows a human can actually judge: there is something to open
pool = [r for r in rows if r["tier"][0] in "12" and r["archived_site"]]
print(f"{len(pool)} judgeable rows (tiers 1-2 with a working archive link)")

# deterministic spread: take every k-th row within each band rather than a random draw, so
# the sample is reproducible and covers the whole score range instead of clustering at the top
sample = []
for band in ("Yes", "Maybe", "No"):
    g = [r for r in pool if r["RELEVANT? (Yes/No/Maybe)"] == band]
    if not g: continue
    step = max(1, len(g) // N)
    picked = g[::step][:N]
    sample += picked
    print(f"  {band:<6}{len(g):>4} available -> {len(picked)} sampled (every {step}{'st' if step==1 else 'th'})")

sample.sort(key=lambda r: int(r["sr"]))

SEND = ["sr", "company", "archived_site", "all_snapshots", "live_site", "sector", "state",
        "incorporated", "site_live_for_years", "first_seen", "last_seen", "snapshots",
        "app_signals", "status_at_mca", "how_to_judge"]
BLANK = ["RELEVANT? (Yes/No/Maybe)", "WHY (one line)", "VETTED BY"]

out = os.path.join(OUTD, "LH2_vet_sample_BLIND.csv")
with open(out, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=SEND + BLANK); w.writeheader()
    for r in sample:
        w.writerow({k: r.get(k, "") for k in SEND} | {k: "" for k in BLANK})

key = os.path.join(OUTD, "LH2_vet_sample_ANSWER_KEY.csv")
with open(key, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["sr","company","tier","desk_verdict","desk_priority",
                                      "desk_why","product_score","codebase_score"])
    w.writeheader()
    for r in sample:
        w.writerow({"sr":r["sr"],"company":r["company"],"tier":r["tier"],
                    "desk_verdict":r["RELEVANT? (Yes/No/Maybe)"],
                    "desk_priority":r["PRIORITY (1=chase 5=drop)"],
                    "desk_why":r["WHY (one line)"],
                    "product_score":r["product_score"],"codebase_score":r["codebase_score"]})

print(f"\nwrote {os.path.basename(out)}        {len(sample)} rows, {len(SEND)+len(BLANK)} cols — SEND THIS")
print(f"wrote {os.path.basename(key)}   — keep this back, it is the comparison")
print("\nheld back from the sample so it cannot anchor the vetter:",
      ", ".join(["RELEVANT?", "WHY", "PRIORITY", "product_score", "codebase_score",
                 "product_proof", "evidence_*"]))
