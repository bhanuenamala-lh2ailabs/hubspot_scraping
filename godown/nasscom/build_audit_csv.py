# -*- coding: utf-8 -*-
"""Audit CSV: exactly how each of the 200 firms was scored, and why anything was rejected.

The deliverable CSV shows verdicts. This one shows WORKING — every tier's contribution, the raw
sum before caps, which cap bit and what it cost, and a plain-English rejection reason. The point
is that anyone can disagree with a specific call and see precisely which line of the rubric
produced it, rather than having to trust the number.

Rejection reasons are ordered by what actually decided the outcome:
  1. website unreachable          - never scored at all
  2. a Step 3 / GOLD cap bit      - the raw sum cleared the bar but a cap pulled it under
  3. simply not enough evidence   - no cap involved, the firm just did not score

That distinction matters operationally: a capped firm was disqualified on something structural
(agency bundling, BPO core, no pre-2024 proof), while an under-scored firm may only look weak
because we could not read its site.

Usage: python3 build_audit_csv.py
"""
import os, csv, json, glob, collections

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "nasscom_200_filtering_audit.csv")

sc = {}
for f in glob.glob(os.path.join(HERE, "score_batches", "scored_*.json")):
    for r in json.load(open(f, encoding="utf-8")): sc[r["domain"]] = r
bun = json.load(open(os.path.join(HERE, "score_bundles.json"), encoding="utf-8"))
fo = {}
for f in glob.glob(os.path.join(HERE, "people_batches", "found_*.json")):
    for r in json.load(open(f, encoding="utf-8")): fo[r["domain"]] = r
try:
    pre = {r["domain"]: r for r in json.load(open(os.path.join(HERE, "pre2024.json"), encoding="utf-8"))}
except Exception:
    pre = {}

BAND = {"Priority": 0, "Secondary": 1, "Skip": 2}


def reason(r, b):
    """Plain-English: what actually decided this outcome."""
    if b.get("UNREACHABLE"):
        return f'NOT SCORED — website unreachable ({b.get("error","")})'
    if r["band"] != "Skip":
        return ""
    caps = r.get("caps_applied") or []
    raw = (r.get("tier_gold_awarded", 0) + r.get("tier_a_points", 0)
           + r.get("tier_b_points", 0) + r.get("tier_c_points", 0))
    if caps and raw >= 50:
        return f'CAPPED — raw {raw} cut to {r["score"]} by: {"; ".join(caps)}'
    if caps:
        return f'LOW SCORE ({r["score"]}) and capped by: {"; ".join(caps)}'
    if r.get("tier_a_points", 0) == 0 and r.get("tier_b_points", 0) == 0:
        return (f'NO ENGINEERING EVIDENCE — no public repo/OSS/eng-blog (Tier A) and no '
                f'code-review/CI-CD/QA/certification signal (Tier B); scored {r["score"]}')
    return f'INSUFFICIENT SCORE ({r["score"]}) — below the 50 threshold'


cols = ["band", "score", "REJECTION REASON", "name", "city", "domain", "website",
        "confidence", "raw_before_caps", "caps_applied",
        "GOLD_pre2024_pts", "pre2024_evidence",
        "TierA_pts", "TierA_what", "TierB_pts", "TierC_pts",
        "pages_reached", "pages_missing", "repo", "merged_PRs", "PR_authors", "repo_since",
        "founder", "founder_title", "founder_linkedin", "founder_confidence",
        "scoring_evidence", "why"]

rows = []
for b in bun:
    d = b.get("domain", "")
    r = sc.get(d, {}); f = fo.get(d, {}); p = pre.get(d, {})
    org = (b.get("own_vcs_orgs") or [{}])[0] if b.get("own_vcs_orgs") else {}
    raw = ((r.get("tier_gold_awarded") or 0) + (r.get("tier_a_points") or 0)
           + (r.get("tier_b_points") or 0) + (r.get("tier_c_points") or 0)) if r else ""
    ta = []
    if org.get("merged_prs"): ta.append("own repo w/ merged PRs")
    if b.get("npm_packages_on_own_domain"): ta.append("published npm package")
    if (r.get("tier_a_points") or 0) and not ta: ta.append("engineering blog")
    rows.append({
        "band": r.get("band") or ("Skip" if b.get("UNREACHABLE") else ""),
        "score": r.get("score", ""), "REJECTION REASON": reason(r, b) if r or b.get("UNREACHABLE") else "",
        "name": b.get("name", ""), "city": b.get("city", ""), "domain": d,
        "website": b.get("website", ""), "confidence": r.get("confidence", ""),
        "raw_before_caps": raw, "caps_applied": "; ".join(r.get("caps_applied") or []),
        "GOLD_pre2024_pts": r.get("tier_gold_awarded", ""),
        "pre2024_evidence": (r.get("pre2024_status") or p.get("note") or "")[:150],
        "TierA_pts": r.get("tier_a_points", ""), "TierA_what": ", ".join(ta),
        "TierB_pts": r.get("tier_b_points", ""), "TierC_pts": r.get("tier_c_points", ""),
        "pages_reached": ", ".join(b.get("pages_reached") or []),
        "pages_missing": ", ".join(b.get("pages_absent") or []),
        "repo": org.get("org", ""), "merged_PRs": org.get("merged_prs", ""),
        "PR_authors": org.get("human_authors", ""), "repo_since": (org.get("first_merge") or "")[:10],
        "founder": f.get("person") or "", "founder_title": f.get("title") or "",
        "founder_linkedin": f.get("linkedin") or "", "founder_confidence": f.get("confidence", ""),
        "scoring_evidence": " | ".join(r.get("evidence") or []), "why": r.get("why", ""),
    })

rows.sort(key=lambda x: (BAND.get(x["band"], 3), -(x["score"] if isinstance(x["score"], int) else 0)))
with open(OUT, "w", newline="", encoding="utf-8-sig") as fh:
    w = csv.DictWriter(fh, fieldnames=cols); w.writeheader()
    for x in rows: w.writerow(x)

print(f"wrote {os.path.basename(OUT)} ({len(rows)} rows)")
print("\nband:", dict(collections.Counter(x["band"] for x in rows)))
cats = collections.Counter()
for x in rows:
    rr = x["REJECTION REASON"]
    if not rr: continue
    cats[rr.split("—")[0].strip()] += 1
print("\nrejection categories:")
for k, v in cats.most_common(): print(f"   {v:>4}  {k}")
capped = [x for x in rows if x["band"] == "Skip" and x["caps_applied"]]
print(f"\nrejected BY A CAP (raw score would have passed): "
      f"{sum(1 for x in capped if isinstance(x['raw_before_caps'],int) and x['raw_before_caps']>=50)}")
allcaps = collections.Counter()
for x in rows:
    for c in (x["caps_applied"] or "").split(";"):
        c = c.strip()
        if c: allcaps[c] += 1
print("\nevery cap applied across the 200:")
for k, v in allcaps.most_common(): print(f"   {v:>4}  {k}")
