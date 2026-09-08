# -*- coding: utf-8 -*-
"""Assemble grading bundles for the Romanian pool.

Same evidence model as NASSCOM, with two differences the grader is told about explicitly:

  TIER A IS EFFECTIVELY UNAVAILABLE HERE. 97 of 170 reachable firms publish no careers page at
  all, so job-description evidence — the thing the revised rubric makes decisive — exists for
  almost nobody. Exactly ONE firm names both a private-repo host and a review gate. Grading this
  pool on Tier A alone would rank 196 firms identically at zero, which tells us nothing. So the
  discriminating evidence has to be Tier GOLD plus site-level Tier B/C, and the grader is asked
  to say so in why_this_rank rather than pretend the score means what it means for NASSCOM.

  DOMAIN AGE IS MISSING FOR .ro. Those domains are not in RDAP at all (rdap.org 404s, ROTLD
  publishes no endpoint), so for 44 firms — 26% of the pool — Wayback is the ONLY pre-2024 test.
  A .ro firm with no readable snapshot is UNKNOWN, never "new".

The captive rule is also relaxed: Romania's market is nearshore delivery for Western clients, so
serving foreign clients is normal and not a disqualifier. Only a foreign parent's wholly-owned
delivery centre is rejected.

Usage: python3 build_ro_bundles.py [--per 20]
"""
import os, sys, json, csv, glob, collections

HERE = os.path.dirname(os.path.abspath(__file__))
PER = 20
for i, a in enumerate(sys.argv):
    if a == "--per": PER = int(sys.argv[i+1])


def load(f, key="domain"):
    try:
        return {r[key]: r for r in json.load(open(os.path.join(HERE, f), encoding="utf-8")) if r.get(key)}
    except Exception:
        return {}


ev = load("ro_evidence.json")
jd = load("ro_jd.json")
way = load("ro_wayback.json")
rdap = load("ro_rdap.json")
seed = {}
for r in csv.DictReader(open(os.path.join(HERE, "romania_candidates.csv"), encoding="utf-8-sig")):
    seed[r["domain"]] = r

out = []
for d, e in ev.items():
    if e.get("error"): continue
    j = jd.get(d, {}); w = way.get(d, {}); rd = rdap.get(d, {}); s = seed.get(d, {})
    js = j.get("signals", {})
    if w.get("pre2024_software"):
        gold = {"level": "PROVEN", "how": "wayback snapshot advertising software work",
                "date": w.get("snapshot_used"), "quote": (w.get("evidence") or "")[:160]}
    elif w.get("snapshot_used"):
        gold = {"level": "EXISTED_NO_SW_WORDING", "how": "archived pre-2024, snapshot did not mention software",
                "date": w.get("snapshot_used"), "quote": ""}
    elif rd.get("registered") and rd.get("pre2024_domain"):
        gold = {"level": "DOMAIN_ONLY", "how": "domain registered pre-2024; proves ownership of a name only",
                "date": rd["registered"], "quote": ""}
    elif rd.get("registered"):
        gold = {"level": "RED_FLAG_2024_PLUS", "how": "domain first registered 2024 or later",
                "date": rd["registered"], "quote": ""}
    else:
        why = ("no wayback snapshot; .ro domains are absent from RDAP entirely, so no domain age exists"
               if d.endswith(".ro") else "no wayback snapshot and no RDAP record")
        gold = {"level": "UNKNOWN", "how": why + " — MISSING, not absent", "date": "", "quote": ""}
    sig = e.get("signal_counts", {})
    prio = (100 if (js.get("private_repo_host") and js.get("review_gate")) else
            60 if (js.get("private_repo_host") or js.get("review_gate")) else 0)
    prio += min(js.get("cicd", 0), 8) * 3 + min(sig.get("pr_practice", 0), 6) * 4
    prio += min(sig.get("compliance", 0), 5) * 2 + min(sig.get("cicd", 0), 10)
    prio += min(sig.get("qa", 0), 6) * 2 + min(sig.get("owns_product", 0), 5)
    prio += int(s.get("lead_score") or 0) * 2          # the pre-scored relevance from your CSV
    prio -= 2 * (min(sig.get("DQ_agency", 0), 6) + min(sig.get("DQ_bpo", 0), 6)
                 + min(sig.get("DQ_template", 0), 6))
    out.append({
        "name": e["name"], "domain": d, "website": e.get("final_url") or e.get("website", ""),
        "seed_lead_score": s.get("lead_score", ""), "seed_reason": (s.get("qualification_reason") or "")[:180],
        "tier_gold_evidence": gold,
        "jd": {"jd_chars": j.get("jd_chars", 0), "signals": js, "quotes": j.get("quotes", {}),
               "external_job_boards": j.get("job_boards") or [],
               "meets_tier_a": bool(js.get("private_repo_host") and js.get("review_gate")),
               "has_careers_page": "careers" in (e.get("pages_reached") or [])},
        "site_signals": sig, "site_quotes": e.get("evidence", {}),
        "pages_reached": e.get("pages_reached", []),
        "has_no_careers_blog_or_team": not ({"careers", "blog", "team"} & set(e.get("pages_reached", []))),
        "public_vcs_links": e.get("vcs", []),
        "_prio": prio,
    })

out.sort(key=lambda r: -r["_prio"])
os.makedirs(os.path.join(HERE, "grade"), exist_ok=True)
for f in glob.glob(os.path.join(HERE, "grade", "rb_*.json")): os.remove(f)
n = 0
for i in range(0, len(out), PER):
    n += 1
    json.dump(out[i:i+PER], open(os.path.join(HERE, "grade", f"rb_{n}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
json.dump(out, open(os.path.join(HERE, "ro_pool.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print(f"bundles: {len(out)} firms -> {n} batches of {PER}")
g = collections.Counter(r["tier_gold_evidence"]["level"] for r in out)
print("\npre-2024 evidence:")
for k, v in g.most_common(): print(f"   {v:>4}  {k}")
print(f"\nTier A available            : {sum(1 for r in out if r['jd']['meets_tier_a'])}")
print(f"has a careers page          : {sum(1 for r in out if r['jd']['has_careers_page'])}")
print(f"no careers/blog/team (cap40): {sum(1 for r in out if r['has_no_careers_blog_or_team'])}")
print(f"has a public repo link      : {sum(1 for r in out if r['public_vcs_links'])}")
print("\ntop 10 by priority:")
for r in out[:10]:
    print(f"   {r['_prio']:>4}  {r['name'][:40]:<42}gold={r['tier_gold_evidence']['level'][:14]:<16}"
          f"seed={r['seed_lead_score']}")
