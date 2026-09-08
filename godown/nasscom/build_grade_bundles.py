# -*- coding: utf-8 -*-
"""Assemble everything known about each NASSCOM firm into one bundle per company, for grading.

Five evidence sources, each with different reliability, and the bundle keeps them DISTINCT rather
than blending them into a score the grader cannot audit:

  crawl        6 pages per firm: signal families + the sentences that triggered them
  jd           careers page AND the Greenhouse/Lever/Naukri listings behind it — the new Tier A
  wayback      their own site advertising software work pre-2024. PROOF. ~550 firms.
  rdap         domain registration date. Proves the domain existed, NOT what it was used for.
  headcount    staffCount, where a SignalHire reveal already happened (no new spend)

WHY THE TWO DATE SIGNALS ARE NOT INTERCHANGEABLE, and the grader is told so explicitly:
a 2022 snapshot headed "Custom Software Development" proves they were building then; a 2005
domain registration proves only that somebody owned the name. The oldest domains in this pool
belong to CGI, Schlumberger, Goldman Sachs and JP Morgan — multinational captives, and precisely
NOT targets. So domain age is a gate and a red-flag detector, never a ranking signal.

Priority ordering puts firms with real engineering evidence first so the top of the ranking is
produced before the long tail.

Usage: python3 build_grade_bundles.py [--per 20] [--only-signal]
"""
import os, sys, json, glob, collections

HERE = os.path.dirname(os.path.abspath(__file__))
PER, ONLY = 20, "--only-signal" in sys.argv
for i, a in enumerate(sys.argv):
    if a == "--per": PER = int(sys.argv[i+1])


def load(f, key="domain"):
    try:
        return {r[key]: r for r in json.load(open(os.path.join(HERE, f), encoding="utf-8")) if r.get(key)}
    except Exception:
        return {}


ev = load("all_evidence.json")
jd = load("jd_evidence.json")
rdap = load("domain_age.json")
way = {}
# every Wayback output file must be listed here. Omitting pre2024_tail_done.json silently
# reported 498 PROVEN when the collected data held 810 — a third of the strongest evidence
# simply not loaded, which would have under-graded hundreds of firms.
for f in ("pre2024.json", "pass106_pre2024.json", "pre2024_rest.json",
          "pre2024_prio.json", "pre2024_tail_done.json"):
    way.update(load(f))
hc = {}
for f in ("bulk_revealed.json", "above20_revealed.json"):
    for d, r in load(f).items():
        if r.get("staff_count") or r.get("staff"): hc[d] = r.get("staff_count") or r.get("staff")
pushed = set()
try:
    pushed = set(json.load(open(os.path.join(HERE, "pushed_batches.json"), encoding="utf-8")).keys())
except Exception:
    pass

out = []
for d, e in ev.items():
    if e.get("error"): continue
    j = jd.get(d, {}); w = way.get(d, {}); rd = rdap.get(d, {})
    js = j.get("signals", {})
    tier_a = bool(js.get("private_repo_host") and js.get("review_gate"))
    # pre-2024, strongest available first
    if w.get("pre2024_software"):
        gold = {"level": "PROVEN", "how": "wayback snapshot advertising software work",
                "date": w.get("snapshot_used"), "quote": (w.get("evidence") or "")[:160]}
    elif w.get("snapshot_used"):
        gold = {"level": "EXISTED_NO_SW_WORDING", "how": "site archived pre-2024 but snapshot did not mention software",
                "date": w.get("snapshot_used"), "quote": ""}
    elif rd.get("registered") and rd.get("pre2024_domain"):
        gold = {"level": "DOMAIN_ONLY", "how": "domain registered pre-2024; does NOT prove what it was used for",
                "date": rd["registered"], "quote": ""}
    elif rd.get("registered"):
        gold = {"level": "RED_FLAG_2024_PLUS", "how": "domain first registered 2024 or later",
                "date": rd["registered"], "quote": ""}
    else:
        gold = {"level": "UNKNOWN", "how": "no wayback snapshot and no RDAP record — MISSING, not absent",
                "date": "", "quote": ""}
    sig = e.get("signal_counts", {})
    prio = (100 if tier_a else 60 if (js.get("private_repo_host") or js.get("review_gate")) else 0)
    prio += min(js.get("cicd", 0), 8) * 3 + min(js.get("quality_gate", 0), 4) * 4
    prio += min(sig.get("pr_practice", 0), 6) * 4 + min(sig.get("compliance", 0), 5) * 2
    prio -= 2 * (min(sig.get("DQ_agency", 0), 6) + min(sig.get("DQ_bpo", 0), 6))
    out.append({
        "name": e["name"], "city": e.get("city", ""), "domain": d,
        "website": e.get("final_url") or e.get("website", ""),
        "already_in_hubspot": d in pushed,
        "headcount_known": hc.get(d, ""),
        "tier_gold_evidence": gold,
        "jd": {"pages_read": len(j.get("pages_read") or []),
               "external_job_boards": j.get("job_boards") or [],
               "jd_chars": j.get("jd_chars", 0),
               "signals": js, "quotes": j.get("quotes", {}),
               "meets_tier_a": tier_a},
        "site_signals": sig,
        "site_quotes": e.get("evidence", {}),
        "pages_reached": e.get("pages_reached", []),
        "has_no_careers_blog_or_team": not ({"careers", "blog", "team"} & set(e.get("pages_reached", []))),
        "_prio": prio,
    })

out.sort(key=lambda r: -r["_prio"])
sel = [r for r in out if r["_prio"] > 0] if ONLY else out
os.makedirs(os.path.join(HERE, "grade_batches"), exist_ok=True)
for f in glob.glob(os.path.join(HERE, "grade_batches", "gb_*.json")): os.remove(f)
n = 0
for i in range(0, len(sel), PER):
    n += 1
    json.dump(sel[i:i+PER], open(os.path.join(HERE, "grade_batches", f"gb_{n}.json"), "w",
                                 encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(out, open(os.path.join(HERE, "grade_pool.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

print(f"bundles built: {len(out)} firms -> {n} batches of {PER} in grade_batches/")
print(f"   selected for grading now : {len(sel)}")
g = collections.Counter(r["tier_gold_evidence"]["level"] for r in out)
print("\npre-2024 evidence quality:")
for k, v in g.most_common(): print(f"   {v:>5}  {k}")
print(f"\nTier A (private-repo host AND review gate): {sum(1 for r in out if r['jd']['meets_tier_a'])}")
print(f"firms with real JD text (>1500 chars)     : {sum(1 for r in out if r['jd']['jd_chars']>1500)}")
print(f"firms linking an external job board       : {sum(1 for r in out if r['jd']['external_job_boards'])}")
print(f"already pushed to HubSpot                 : {sum(1 for r in out if r['already_in_hubspot'])}")
