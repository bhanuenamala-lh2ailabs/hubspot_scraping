# -*- coding: utf-8 -*-
"""Assemble the Romanian ranking and cut the best 50.

Only 38 firms reach Priority or Secondary, so the last 12 come from Skip. That selection is NOT
"the next 12 by score" — it is the next 12 whose score was suppressed by MISSING EVIDENCE rather
than by a disqualifying fact. A firm capped at 30 for bundling SEO with development is a
different proposition from one capped at 45 because its .ro domain has no RDAP record and its
snapshot would not load. The first is a judgement about the business; the second is a limit of
what could be collected.

Every promoted row is marked `promoted_from_skip` with the reason, so the 50 is auditable and
nobody mistakes row 42 for row 2.

Also flags the duplicate listings the graders caught: XCODES appears twice, Nearshore Romania is
ROPARDO's brand site, and Berg Software carries AROBS acquisition text on its own pages.

Usage: python3 assemble_ro50.py
"""
import os, re, csv, json, glob, collections

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_ALL = os.path.join(HERE, "ROMANIA_RANKED.csv")
OUT_50 = os.path.join(HERE, "ROMANIA_BEST_50.csv")

graded = {}
for f in sorted(glob.glob(os.path.join(HERE, "grade", "graded_*.json"))):
    for r in json.load(open(f, encoding="utf-8")):
        r.setdefault("graded_by", "agent"); graded[r["domain"]] = r
pool = {r["domain"]: r for r in json.load(open(os.path.join(HERE, "ro_pool.json"), encoding="utf-8"))}
seed = {r["domain"]: r for r in csv.DictReader(open(os.path.join(HERE, "romania_candidates.csv"),
                                                    encoding="utf-8-sig"))}

# disqualified for a REASON about the business, vs merely unevidenced
DISQ = re.compile(r"(agency|seo|marketing bundl|bpo|call cent|staffing|training|course|template|"
                  r"website.builder|giant|1200|listed|captive|wholly-owned|delivery centre|"
                  r"support bundl|helpdesk)", re.I)
MISSING = re.compile(r"(no careers|missing|not absent|unknown|could not|unreadable|thin|"
                     r"suppress|rdap|snapshot|crawl|no jd|no process language)", re.I)

rows = []
for d, g in graded.items():
    p = pool.get(d, {}); s = seed.get(d, {})
    j = p.get("jd", {})
    rows.append({
        "band": g.get("band", ""), "score": g.get("score", 0), "confidence": g.get("confidence", ""),
        "name": g.get("name") or p.get("name", ""), "domain": d,
        "website": p.get("website") or s.get("website", ""),
        "seed_lead_score": s.get("lead_score", ""),
        "GOLD_pts": g.get("tier_gold_awarded", ""), "TierA_pts": g.get("tier_a_points", ""),
        "TierB_pts": g.get("tier_b_points", ""), "TierC_pts": g.get("tier_c_points", ""),
        "raw_before_caps": g.get("raw_before_caps", ""),
        "caps_applied": "; ".join(g.get("caps_applied") or []),
        "pre2024_basis": g.get("pre2024_basis", ""),
        "has_careers_page": "yes" if j.get("has_careers_page") else "",
        "jd_chars": j.get("jd_chars", 0),
        "public_repo": "; ".join(p.get("public_vcs_links") or [])[:60],
        "evidence": " | ".join(g.get("evidence") or []),
        "why_this_rank": g.get("why_this_rank", ""),
        "_disq": bool(DISQ.search((g.get("caps_applied") and " ".join(g["caps_applied"]) or "") +
                                  " " + (g.get("why_this_rank") or ""))),
        "_missing": bool(MISSING.search(g.get("why_this_rank") or "")),
    })

BAND = {"Priority": 0, "Secondary": 1, "Skip": 2}
rows.sort(key=lambda r: (BAND.get(r["band"], 3), -(r["score"] if isinstance(r["score"], int) else 0),
                         r["name"].lower()))
for i, r in enumerate(rows, 1): r["rank"] = i

cols = ["rank", "band", "score", "confidence", "name", "domain", "website", "seed_lead_score",
        "GOLD_pts", "TierA_pts", "TierB_pts", "TierC_pts", "raw_before_caps", "caps_applied",
        "pre2024_basis", "has_careers_page", "jd_chars", "public_repo", "evidence", "why_this_rank"]
with open(OUT_ALL, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
    for r in rows: w.writerow({k: r.get(k, "") for k in cols})

# ---- the 50 ----
qual = [r for r in rows if r["band"] in ("Priority", "Secondary")]
skip_ok = [r for r in rows if r["band"] == "Skip" and not r["_disq"] and r["_missing"]]
skip_ok.sort(key=lambda r: -r["score"])
need = 50 - len(qual)
promoted = skip_ok[:max(0, need)]
for r in promoted:
    r["promoted_from_skip"] = "score suppressed by missing evidence, not by a disqualifying fact"
best = qual + promoted
with open(OUT_50, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=cols + ["promoted_from_skip"]); w.writeheader()
    for i, r in enumerate(best, 1):
        r2 = {k: r.get(k, "") for k in cols + ["promoted_from_skip"]}; r2["rank"] = i
        w.writerow(r2)

print(f"wrote {os.path.basename(OUT_ALL)} ({len(rows)}) and {os.path.basename(OUT_50)} ({len(best)})\n")
print(f"   Priority  {sum(1 for r in rows if r['band']=='Priority')}")
print(f"   Secondary {sum(1 for r in rows if r['band']=='Secondary')}")
print(f"   Skip      {sum(1 for r in rows if r['band']=='Skip')}")
print(f"\nqualified outright   : {len(qual)}")
print(f"promoted from Skip   : {len(promoted)}  (evidence-limited only)")
print(f"disqualified Skips left alone: {sum(1 for r in rows if r['band']=='Skip' and r['_disq'])}")
print(f"\nVerified in the 50   : {sum(1 for r in best if r['confidence']=='Verified')}")
print(f"reason written       : {sum(1 for r in best if r['why_this_rank'])}/{len(best)}")
DUP = ("xcodes", "nearshore", "ropardo", "berg", "arobs")
dups = [r for r in best if any(k in r["name"].lower() or k in r["domain"].lower() for k in DUP)]
if dups:
    print("\n!! possible duplicate / parent-subsidiary rows in the 50 — check before outreach:")
    for r in dups: print(f"   {r['name'][:40]:<42}{r['domain']}")
print("\nTOP 20:")
for r in best[:20]:
    print(f"   {r['score']:>3} {r['band']:<10}{r['name'][:36]:<38}{r['confidence']:<9}"
          f"{'repo' if r['public_repo'] else '':<5}{r['pre2024_basis'][:22]}")
