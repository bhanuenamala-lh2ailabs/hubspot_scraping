# -*- coding: utf-8 -*-
"""The deliverable: every NASSCOM firm, ranked high to low, with its working shown.

Merges the three grading passes plus the computed pool, and joins back the evidence each score
was derived from so a rank can be audited rather than trusted.

COLUMN ORDER IS DELIBERATE. Numbers first — band, score, then each tier's contribution, the raw
total before caps, and which cap fired. `why_this_rank` sits at the END and is populated ONLY
where those numbers do not account for the placement: a cap overrode real merit, evidence was
missing rather than absent, a judgement call was made about substantive-versus-decorative
language, or the crawl captured too little. A blank reason means the arithmetic already explains
the row.

`graded_by` separates agent judgement from rubric arithmetic. The 1,262 computed rows had zero
Tier A and zero Tier B evidence, which under the corroboration rule caps them at 25 — they were
Skip before anyone read them, so no model time was spent restating that 1,262 times.

Usage: python3 assemble_ranked.py
"""
import os, csv, json, glob, collections

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "NASSCOM_RANKED.csv")

graded = {}
for f in (sorted(glob.glob(os.path.join(HERE, "grade_batches", "graded_*.json"))) +
          sorted(glob.glob(os.path.join(HERE, "grade_v2", "graded_v2_*.json"))) +
          sorted(glob.glob(os.path.join(HERE, "grade_v3", "graded_v3_*.json")))):
    for r in json.load(open(f, encoding="utf-8")):
        r.setdefault("graded_by", "agent")
        graded[r["domain"]] = r
for r in json.load(open(os.path.join(HERE, "graded_computed.json"), encoding="utf-8")):
    graded.setdefault(r["domain"], r)

pool = {r["domain"]: r for r in json.load(open(os.path.join(HERE, "grade_pool.json"), encoding="utf-8"))}
jd = {r["domain"]: r for r in json.load(open(os.path.join(HERE, "jd_evidence.json"), encoding="utf-8"))}
hc = {}
for f in ("bulk_revealed.json", "above20_revealed.json"):
    try:
        for r in json.load(open(os.path.join(HERE, f), encoding="utf-8")):
            if r.get("staff_count") or r.get("staff"):
                hc[r["domain"]] = r.get("staff_count") or r.get("staff")
            # only surface a contact that actually cleared the seniority + phone gate. The reveal
            # pool also holds people who failed it — an Assistant Manager whose LinkedIn happened
            # to sit on the team page is not a decision-maker, and showing them here would imply
            # this firm is ready to call when it is not.
            if r.get("person") and (r.get("gate") == "PASS" or r.get("is_senior")):
                hc.setdefault("_p" + r["domain"], (r["person"], r.get("title", ""), r.get("indian_phone", "")))
    except Exception:
        pass
pushed = {}
try:
    pushed = json.load(open(os.path.join(HERE, "pushed_batches.json"), encoding="utf-8"))
except Exception:
    pass

BAND = {"Priority": 0, "Secondary": 1, "Skip": 2}
cols = ["rank", "band", "score", "confidence", "name", "city", "domain", "website",
        "headcount", "already_in_hubspot", "contact_known",
        "GOLD_pts", "TierA_pts", "TierB_pts", "TierC_pts", "raw_before_caps", "caps_applied",
        "pre2024_basis", "private_repo_host_hits", "review_gate_hits", "cicd_hits", "jd_chars",
        "evidence", "graded_by", "why_this_rank"]

rows = []
for d, g in graded.items():
    p = pool.get(d, {}); j = jd.get(d, {}); js = (j.get("signals") or {})
    per = hc.get("_p" + d)
    rows.append({
        "band": g.get("band", ""), "score": g.get("score", 0),
        "confidence": g.get("confidence", ""),
        "name": g.get("name") or p.get("name", ""), "city": p.get("city", ""),
        "domain": d, "website": p.get("website", ""),
        "headcount": hc.get(d, ""),
        "already_in_hubspot": "yes" if d in pushed else "",
        "contact_known": f"{per[0]} ({per[1]})" if per else "",
        "GOLD_pts": g.get("tier_gold_awarded", ""), "TierA_pts": g.get("tier_a_points", ""),
        "TierB_pts": g.get("tier_b_points", ""), "TierC_pts": g.get("tier_c_points", ""),
        "raw_before_caps": g.get("raw_before_caps", ""),
        "caps_applied": "; ".join(g.get("caps_applied") or []),
        "pre2024_basis": g.get("pre2024_basis", ""),
        "private_repo_host_hits": js.get("private_repo_host", 0),
        "review_gate_hits": js.get("review_gate", 0),
        "cicd_hits": js.get("cicd", 0),
        "jd_chars": j.get("jd_chars", 0),
        "evidence": " | ".join(g.get("evidence") or []),
        "graded_by": g.get("graded_by", "agent"),
        "why_this_rank": g.get("why_this_rank", ""),
    })

rows.sort(key=lambda r: (BAND.get(r["band"], 3), -(r["score"] if isinstance(r["score"], int) else 0),
                         r["name"].lower()))
for i, r in enumerate(rows, 1): r["rank"] = i
with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
    for r in rows: w.writerow({k: r.get(k, "") for k in cols})

print(f"wrote {os.path.basename(OUT)}  ({len(rows)} firms)\n")
b = collections.Counter(r["band"] for r in rows)
for k in ("Priority", "Secondary", "Skip"): print(f"   {b[k]:>5}  {k}")
print(f"\ngraded by agent   : {sum(1 for r in rows if r['graded_by']=='agent')}")
print(f"graded by rubric  : {sum(1 for r in rows if r['graded_by']=='computed')}")
print(f"reason written for: {sum(1 for r in rows if r['why_this_rank'])}")
print(f"Verified          : {sum(1 for r in rows if r['confidence']=='Verified')}")
print(f"already in HubSpot: {sum(1 for r in rows if r['already_in_hubspot'])}")
print(f"contact already known: {sum(1 for r in rows if r['contact_known'])}")
print("\nTOP 30:")
for r in rows[:30]:
    print(f'  {r["rank"]:>3}. {r["score"]:>3} {r["band"]:<10}{r["name"][:40]:<42}'
          f'{r["confidence"]:<9}{"HS" if r["already_in_hubspot"] else "":<3}{(r["contact_known"] or "")[:26]}')
