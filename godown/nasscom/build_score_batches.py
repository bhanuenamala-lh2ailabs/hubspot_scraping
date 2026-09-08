# -*- coding: utf-8 -*-
"""Merge every evidence source into one bundle per company, then split into agent batches.

Three sources, deliberately kept separate until now because they fail in different ways:
  scoring_evidence.json  pages reached + excerpted prose per rubric signal family
  vcs_verified.json      merged-PR counts, human authors, first/last merge — the only Tier A facts
  pre2024.json           Wayback evidence for Tier GOLD

WHAT THE AGENT MUST NOT HAVE TO GUESS. Each bundle states, explicitly:
  * which pages were actually reached, and which were absent — the rubric caps at 40 for
    "no careers AND no blog AND no team", so a missing page has to be a fact, not an inference
  * whether a VCS org is the FIRM'S OWN (vendor links are dropped before this point)
  * whether a Tier GOLD lookup succeeded, failed, or genuinely found nothing — "lookup failed"
    must never be scored as "no evidence", because the rubric caps hard on the latter

Usage: python3 build_score_batches.py [--per 25]
"""
import os, sys, json, math

HERE = os.path.dirname(os.path.abspath(__file__))
PER = 25
for i, a in enumerate(sys.argv):
    if a == "--per": PER = int(sys.argv[i+1])

ev = json.load(open(os.path.join(HERE, "scoring_evidence.json"), encoding="utf-8"))
vcs = json.load(open(os.path.join(HERE, "vcs_verified.json"), encoding="utf-8"))
try:
    pre = {r["domain"]: r for r in json.load(open(os.path.join(HERE, "pre2024.json"), encoding="utf-8"))}
except Exception:
    pre = {}

gh = vcs.get("gh", {}); npm = vcs.get("npm", {})
# org -> the domains it was accepted for (attribution already filtered in verify_vcs.py)
own = {}
for r in ev:
    for u in r.get("vcs", []):
        o = u.rsplit("/", 1)[-1].lower()
        if o in gh: own.setdefault(r["domain"], []).append(gh[o])

out = []
for r in ev:
    d = r.get("domain", "")
    if r.get("error"):
        out.append({"name": r["name"], "domain": d, "website": r.get("website"),
                    "UNREACHABLE": True, "error": r["error"]})
        continue
    p = pre.get(d, {})
    gold = {"wayback_first_snapshot": p.get("first_snapshot"),
            "pre2024_software_evidence": p.get("pre2024_software"),
            "snapshot_checked": p.get("snapshot_used"),
            "snapshot_quote": p.get("evidence"),
            "lookup_note": p.get("note") or ""}
    orgs = own.get(d, [])
    out.append({
        "name": r["name"], "city": r.get("city"), "domain": d,
        "website": r.get("final_url") or r.get("website"),
        "pages_reached": r.get("pages_reached", []),
        "pages_absent": r.get("pages_missing", []),
        "has_no_careers_blog_or_team": not ({"careers", "blog", "team"} & set(r.get("pages_reached", []))),
        "own_vcs_orgs": [{"org": g.get("org"), "merged_prs": g.get("merged_prs"),
                          "human_authors": g.get("human_authors"),
                          "first_merge": g.get("first_merge"), "last_merge": g.get("last_merge"),
                          "bot_prs_excluded_from_sample": g.get("bot_prs_in_sample"),
                          "meets_tier_a": g.get("tier_a_vcs"),
                          "meets_tier_gold": g.get("tier_gold_vcs")} for g in orgs],
        "npm_packages_on_own_domain": npm.get(d, []),
        "external_blogs": r.get("external_blogs") or r.get("blogs", []),
        "tier_gold_wayback": gold,
        "signal_counts": r.get("signal_counts", {}),
        "evidence_excerpts": r.get("evidence", {}),
    })

os.makedirs(os.path.join(HERE, "score_batches"), exist_ok=True)
live = [r for r in out if not r.get("UNREACHABLE")]
dead = [r for r in out if r.get("UNREACHABLE")]
json.dump(out, open(os.path.join(HERE, "score_bundles.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
n = 0
for i in range(0, len(live), PER):
    n += 1
    json.dump(live[i:i+PER],
              open(os.path.join(HERE, "score_batches", f"sb_{n}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
print(f"bundles: {len(out)}  (scoreable {len(live)}, unreachable {len(dead)})")
print(f"wrote {n} batches of {PER} -> score_batches/")
gl = sum(1 for r in live if r["tier_gold_wayback"].get("pre2024_software_evidence"))
lf = sum(1 for r in live if "FAILED" in (r["tier_gold_wayback"].get("lookup_note") or ""))
print(f"tier GOLD via wayback: {gl} | lookup failed (must NOT be scored as absent): {lf}")
print(f"own VCS orgs attached: {sum(1 for r in live if r['own_vcs_orgs'])}")
print(f"no careers/blog/team (rubric cap 40): {sum(1 for r in live if r['has_no_careers_blog_or_team'])}")
