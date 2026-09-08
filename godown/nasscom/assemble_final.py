# -*- coding: utf-8 -*-
"""Merge rubric scores + founders + all upstream evidence into the deliverable CSV.

Sources, each produced by a step that can fail independently:
  score_batches/scored_*.json   rubric verdict per company
  people_batches/found_*.json   founder / CEO, with LinkedIn where checkable
  score_bundles.json            the evidence the score was computed from
  pre2024.json                  Tier GOLD raw result
  headcounts_*.json             SignalHire size, where the company has been sized yet

Rows are ordered by band then score, so the callable ones sit at the top. A company missing from
a source gets an empty cell, never a guessed one — an unscored firm and a firm scored zero are
different facts and the CSV has to keep them apart.

Usage: python3 assemble_final.py [--out nasscom_200_scored.csv]
"""
import os, sys, csv, json, glob, collections

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "nasscom_200_scored.csv")
for i, a in enumerate(sys.argv):
    if a == "--out": OUT = os.path.join(HERE, sys.argv[i+1])


def load_glob(pat):
    rows = []
    for f in sorted(glob.glob(os.path.join(HERE, pat))):
        try:
            rows += json.load(open(f, encoding="utf-8"))
        except Exception as e:
            print(f"   !! could not read {os.path.basename(f)}: {e}")
    return rows


scored = {r["domain"]: r for r in load_glob("score_batches/scored_*.json") if r.get("domain")}
found = {r["domain"]: r for r in load_glob("people_batches/found_*.json") if r.get("domain")}
bundles = json.load(open(os.path.join(HERE, "score_bundles.json"), encoding="utf-8"))
try:
    pre = {r["domain"]: r for r in json.load(open(os.path.join(HERE, "pre2024.json"), encoding="utf-8"))}
except Exception:
    pre = {}
hc = {}
for f in ("headcounts_all.json", "headcounts_pilot.json"):
    p = os.path.join(HERE, f)
    if os.path.exists(p):
        for r in json.load(open(p, encoding="utf-8")):
            hc.setdefault(r["domain"], r)

BANDS = {"Priority": 0, "Secondary": 1, "Skip": 2}
cols = ["band", "score", "confidence", "name", "city", "domain", "website",
        "headcount", "founder_or_ceo", "title", "linkedin", "founder_confidence",
        "pre2024_status", "tier_gold_pts", "tier_a_pts", "tier_b_pts", "tier_c_pts",
        "caps_applied", "own_vcs_org", "merged_prs", "human_authors", "first_merge",
        "pages_reached", "why", "evidence", "founder_evidence"]

rows = []
for b in bundles:
    d = b.get("domain", "")
    s = scored.get(d, {}); f = found.get(d, {}); p = pre.get(d, {}); h = hc.get(d, {})
    org = (b.get("own_vcs_orgs") or [{}])[0] if b.get("own_vcs_orgs") else {}
    if b.get("UNREACHABLE"):
        rows.append({"band": "Skip", "score": "", "confidence": "",
                     "name": b["name"], "domain": d, "website": b.get("website", ""),
                     "why": f'website unreachable ({b.get("error","")}) — not scored',
                     "pre2024_status": "site unreachable"})
        continue
    rows.append({
        "band": s.get("band", ""), "score": s.get("score", ""),
        "confidence": s.get("confidence", ""),
        "name": b["name"], "city": b.get("city", ""), "domain": d, "website": b.get("website", ""),
        "headcount": h.get("total", ""),
        "founder_or_ceo": f.get("person") or "", "title": f.get("title") or "",
        "linkedin": f.get("linkedin") or "", "founder_confidence": f.get("confidence", ""),
        "pre2024_status": s.get("pre2024_status") or (p.get("note") or
                          ("pre-2024 software evidence" if p.get("pre2024_software") else "")),
        "tier_gold_pts": s.get("tier_gold_awarded", ""), "tier_a_pts": s.get("tier_a_points", ""),
        "tier_b_pts": s.get("tier_b_points", ""), "tier_c_pts": s.get("tier_c_points", ""),
        "caps_applied": "; ".join(s.get("caps_applied") or []),
        "own_vcs_org": org.get("org", ""), "merged_prs": org.get("merged_prs", ""),
        "human_authors": org.get("human_authors", ""), "first_merge": org.get("first_merge", ""),
        "pages_reached": ", ".join(b.get("pages_reached") or []),
        "why": s.get("why", ""), "evidence": " | ".join(s.get("evidence") or []),
        "founder_evidence": f.get("evidence", ""),
    })

rows.sort(key=lambda r: (BANDS.get(r["band"], 3), -(r["score"] if isinstance(r["score"], int) else 0)))
with open(OUT, "w", newline="", encoding="utf-8-sig") as fh:
    w = csv.DictWriter(fh, fieldnames=cols); w.writeheader()
    for r in rows: w.writerow({k: r.get(k, "") for k in cols})

print(f"wrote {os.path.basename(OUT)}  ({len(rows)} rows)")
print(f"\nscored by agents: {len(scored)} | founders resolved: {sum(1 for v in found.values() if v.get('person'))}")
print("\nBAND:")
for k, n in collections.Counter(r["band"] for r in rows).most_common():
    print(f"   {n:>4}  {k or '(unscored)'}")
print("\nCONFIDENCE:")
for k, n in collections.Counter(r["confidence"] for r in rows if r["confidence"]).most_common():
    print(f"   {n:>4}  {k}")
pri = [r for r in rows if r["band"] == "Priority"]
sec = [r for r in rows if r["band"] == "Secondary"]
print(f"\nPRIORITY (>=70): {len(pri)}")
for r in pri:
    print(f"   {r['score']:>3}  {r['name'][:42]:<44}{(r['founder_or_ceo'] or '-')[:22]:<24}{r['pre2024_status'][:30]}")
print(f"\nSECONDARY (50-69): {len(sec)}")
for r in sec[:20]:
    print(f"   {r['score']:>3}  {r['name'][:42]:<44}{(r['founder_or_ceo'] or '-')[:22]:<24}{r['pre2024_status'][:30]}")
