# -*- coding: utf-8 -*-
"""Ops-data 500, rebuilt for LEAST-DISTRESSED + ACTIVE companies.

Why this supersedes select_opsdata_500.py: that script scored for an *acquisition* cold
call, where a dead company is the ideal seller (no board, nothing to protect) — so it
awarded a bonus for deadpooled/acquired. The brief is now the opposite: healthy, operating
companies only. A dead company also has a dead inbox, which is fatal for an email campaign.

So the distress bonus is removed and inverted into a hard gate + a ranking term:
  * Is Deadpooled = No, Is Acquired = No           (hard)
  * Website Status 2xx/3xx                         (hard — "website down" is itself a
                                                    +10 distress signal in our own model)
  * Tracxn distress `composite` <= --max-distress  (hard, default 10 of a 0-50 scale)
  * ranked by composite ASC (healthiest first), then ops fit DESC

Everything else is unchanged: 180-500 headcount, India, not a big corporate, not listed,
founded <= 2022, and net-new against both HubSpot portals + the pulled-back Tracxn pool.

Usage: python select_opsdata_healthy.py [--n 500] [--max-distress 10]
"""
import os, re, csv, sys, json, argparse, collections
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from select_opsdata_500 import (num, norm, yes, is_big, hubspot_deal_keys, OPS_HEAVY, SRC, HUB)

OUT = os.path.join(HUB, "exports", "opsdata")
os.makedirs(OUT, exist_ok=True)


def ops_fit(r, emp, age, rev):
    """Same as before MINUS the distress/willingness bonus — we now want healthy firms."""
    s = 30 * (emp - 180) / 320 + 10
    s += min(25, max(0, age - 3) * 2.5)
    if rev: s += 20 if rev >= 10_000_000 else 14 if rev >= 1_000_000 else 8
    blob = (str(r.get("Sector (Pratice Area & Feed)", "")) + " " +
            str(r.get("Business Models", "")) + " " + str(r.get("Description", ""))).lower()
    if any(k in blob for k in OPS_HEAVY): s += 12
    return round(min(100, s), 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=500)
    ap.add_argument("--lo", type=int, default=180); ap.add_argument("--hi", type=int, default=500)
    ap.add_argument("--max-distress", type=int, default=10)
    a = ap.parse_args()

    rows = []
    for f in ("funded", "unfunded"):
        rows += [dict(r, _tab=f) for r in json.load(open(os.path.join(SRC, f + ".json"), encoding="utf-8"))]
    dist = {}
    for r in json.load(open(os.path.join(SRC, "lh2_ranked_targets.json"), encoding="utf-8")):
        c = str(r.get("composite", "")).strip()
        if c.replace(".", "", 1).isdigit(): dist[norm(r.get("company"))] = float(c)

    step = collections.OrderedDict(); step["tracxn rows"] = len(rows)
    sel = [r for r in rows if num(r.get("Total Employee Count")) is not None]
    sel = [r for r in sel if a.lo <= num(r["Total Employee Count"]) <= a.hi]
    step[f"headcount {a.lo}-{a.hi}"] = len(sel)
    sel = [r for r in sel if norm(r.get("Country")) in ("india", "")]; step["India"] = len(sel)
    sel = [r for r in sel if not is_big(r.get("Company Name"), num(r.get("Annual Revenue (USD)")))]
    step["not a big corporate"] = len(sel)
    sel = [r for r in sel if not yes(r.get("Is IPO"))]; step["not listed"] = len(sel)
    sel = [r for r in sel if (num(r.get("Founded Year")) or 9999) <= 2022]
    step["founded <= 2022"] = len(sel)

    sel = [r for r in sel if not yes(r.get("Is Deadpooled"))]; step["ACTIVE — not deadpooled"] = len(sel)
    sel = [r for r in sel if not yes(r.get("Is Acquired"))];   step["ACTIVE — not acquired"] = len(sel)
    live = []
    for r in sel:
        ws = str(r.get("Website Status") or "").strip()
        if ws.startswith("2") or ws.startswith("3"): live.append(r)
    sel = live; step["website reachable (2xx/3xx)"] = len(sel)

    keep = []
    for r in sel:
        d = dist.get(norm(r.get("Company Name")))
        if a.max_distress >= 50 or d is None or d <= a.max_distress: keep.append((r, d))
    step[(f"distress composite <= {a.max_distress}" if a.max_distress < 50
          else "distress used as RANKING, not a cut")] = len(keep)

    hs_names, hs_doms = hubspot_deal_keys()
    pool = {norm(x["company"]) for x in json.load(open(
        os.path.join(HUB, "crm_mirror", "holding", "tracxn_pool_2026-08-04.json"), encoding="utf-8"))}
    seen, net = set(), []
    for r, d in keep:
        n = norm(r.get("Company Name")); dom = str(r.get("Domain Name") or "").lower().strip()
        if n in seen: continue
        if n in hs_names or (dom and dom in hs_doms): continue
        if n in pool: continue
        seen.add(n); net.append((r, d))
    step["NET-NEW available"] = len(net)

    out = []
    for r, d in net:
        emp = num(r["Total Employee Count"]); rev = num(r.get("Annual Revenue (USD)"))
        y = num(r.get("Founded Year")); age = 2026 - y if y else 0
        out.append({"distress": d if d is not None else "", "ops_fit": ops_fit(r, emp, age, rev),
                    "company": r.get("Company Name"), "domain": r.get("Domain Name") or "",
                    "employees": emp, "founded": y, "age_years": age, "city": r.get("City") or "",
                    "state": r.get("State") or "", "revenue_usd": rev or "",
                    "net_profit_usd": num(r.get("Annual Net Profit (USD)")) or "",
                    "sector": (r.get("Sector (Pratice Area & Feed)") or "").split(">")[0].strip(),
                    "business_model": (r.get("Business Models") or "")[:120],
                    "stage": r.get("Company Stage") or "", "website_status": r.get("Website Status") or "",
                    "funding_usd": num(r.get("Total Funding (USD)")) or "",
                    "key_people": r.get("Key People Info") or "",
                    "key_people_emails": r.get("Key People Email Ids") or "",
                    "key_people_profiles": r.get("Links to Key People Profiles") or "",
                    "company_emails": r.get("Company Emails") or "",
                    "company_phones": r.get("Company Phone Numbers") or "",
                    "linkedin": r.get("LinkedIn") or "", "website": r.get("Website") or "",
                    "tracxn_url": r.get("Tracxn URL") or "", "source_tab": r["_tab"], "engage_score": 0})
    # healthiest first, then best operating fit
    # "willing to engage" — reachable by a named human, and not a well-funded company that
    # has no reason to talk to us. Used to break ties between equally-healthy companies.
    for x in out:
        eng = 0
        if x["key_people_emails"].strip(): eng += 30
        if x["key_people_profiles"].strip(): eng += 20
        if x["company_emails"].strip(): eng += 10
        if x["linkedin"].strip(): eng += 10
        if x["company_phones"].strip(): eng += 10
        f = x["funding_usd"]
        if not f: eng += 20                      # unfunded -> founder decides, no board
        elif isinstance(f, int) and f < 5_000_000: eng += 10
        x["engage_score"] = eng
    out.sort(key=lambda x: ((x["distress"] if x["distress"] != "" else 99),
                            -x["engage_score"], -x["ops_fit"]))
    pick = out[:a.n]

    jp = os.path.join(OUT, "opsdata_healthy_500.json")
    json.dump(pick, open(jp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("=== FUNNEL (least-distressed + active) ===")
    for k, v in step.items(): print(f"  {v:>6}  {k}")
    print(f"\n  {len(pick):>6}  DELIVERED")
    if len(pick) < a.n:
        print(f"\n  !! only {len(pick)} available — short of {a.n}. "
              f"Raise --max-distress or widen the headcount band.")
    print(f"-> {jp}")
    return pick


if __name__ == "__main__":
    main()
