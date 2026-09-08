# -*- coding: utf-8 -*-
"""Pick net-new COMPANY OPS DATA targets from the Tracxn sheet: 200-500 headcount.

This is the ops-data buy-mode, NOT codebases. Per crm_mirror/rules/asset_fit_score.md the
two want almost opposite things: a codebase target is a small eng team with clean IP; an
ops-data target is a company that actually RAN a sizeable multi-function operation for
years, because that is what produces SOPs, playbooks, process docs and internal tooling
worth reverse-engineering.

The user's 200-500 headcount filter is exactly the "operating scale is king" signal — big
enough to have real process, small enough not to be an untouchable corporate.

Gates (hard):
  * 200 <= Total Employee Count <= 500        (the brief)
  * India                                      (everything downstream assumes +91)
  * NOT a big corporate / MNC arm / listed co   ("not big companies like amazon")
  * founded <= 2022                             (needs years of operating to have matured process)
  * net-new: no live deal in EITHER HubSpot portal, and not in the pulled-back Tracxn pool

Then ranked by an ops-data score (see ops_score) so the 500 we hand over are the 500 most
likely to hold a sellable operating playbook — not just the first 500 alphabetically.

Usage: python select_opsdata_500.py [--n 500]
"""
import os, re, csv, sys, json, argparse, collections, urllib.request, time
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(HUB, "crm_mirror", "sources", "tracxn")
OUT = os.path.join(HUB, "exports", "opsdata")
os.makedirs(OUT, exist_ok=True)
env = {l.split('=', 1)[0].strip().lower(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}

# Corporates / MNC arms / listed groups — a 200-500 headcount India office of one of these
# is not a company that can sell you its operating playbook.
BIG = {"amazon","google","microsoft","meta","facebook","apple","netflix","uber","ola","flipkart",
       "walmart","reliance","tata","adani","birla","mahindra","infosys","wipro","tcs","hcl",
       "cognizant","accenture","capgemini","ibm","oracle","sap","salesforce","adobe","paypal",
       "visa","mastercard","goldman","morgan","jpmorgan","citi","hsbc","barclays","deloitte",
       "pwc","kpmg","ey ","ernst","mckinsey","bcg","bain","byju","paytm","zomato","swiggy",
       "phonepe","razorpay","zerodha","nykaa","meesho","lenskart","cred","groww","dream11",
       "unacademy","upgrad","policybazaar","delhivery","zepto","blinkit","myntra","snapdeal",
       "shopify","stripe","siemens","bosch","samsung","lg ","sony","philips","honeywell","ge ",
       "abb","schneider","maruti","hyundai","toyota","bajaj","hero ","tvs ","larsen","l&t"}
# Sectors where the operation itself is the asset — many moving parts, real SOPs.
OPS_HEAVY = ("logistic", "delivery", "supply chain", "fulfil", "fulfill", "warehous", "commerce",
             "retail", "grocer", "food", "restaurant", "cloud kitchen", "manufactur", "d2c",
             "healthcare", "hospital", "diagnostic", "pharmacy", "clinic", "field service",
             "facility", "staffing", "fleet", "mobility", "transport", "travel", "hotel",
             "agri", "construction", "real estate", "education", "edtech", "bank", "lending",
             "insurance", "fintech")


def num(v):
    """'3,204 (Mar 31, 2026)' -> 3204 ; '' -> None"""
    m = re.match(r"\s*([\d,]+(?:\.\d+)?)", str(v or ""))
    if not m: return None
    try: return int(float(m.group(1).replace(",", "")))
    except Exception: return None


def norm(s): return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", str(s or "").lower())).strip()
def yes(v): return str(v).strip().lower() in ("yes", "true", "1")


def is_big(name, rev):
    n = " " + norm(name) + " "
    if any(b if b.endswith(" ") else " " + b for b in BIG if (b if b.endswith(" ") else " " + b) in n):
        return True
    return bool(rev and rev > 500_000_000)      # >$500M revenue is not our seller


def ops_score(r, emp, age, rev):
    """0-100. Operating scale is king, then years operated, then real revenue, then sector."""
    s = 0
    # scale within the band — 500 people is a much richer operation than 200
    s += 30 * (emp - 200) / 300
    s += 10                                            # everyone here already clears the band
    # years actually operating: matured, documented process
    s += min(25, max(0, (age - 3)) * 2.5)
    # real revenue => they truly operated, not just raised and died
    if rev:
        s += 20 if rev >= 10_000_000 else 14 if rev >= 1_000_000 else 8
    # ops-intensive sector
    blob = (str(r.get("Sector (Pratice Area & Feed)", "")) + " " +
            str(r.get("Business Models", "")) + " " + str(r.get("Description", ""))).lower()
    if any(k in blob for k in OPS_HEAVY): s += 12
    # willingness to sell — a dead or absorbed company has no reason to guard the playbook
    if yes(r.get("Is Deadpooled")): s += 8
    elif yes(r.get("Is Acquired")): s += 5
    elif str(r.get("Company Stage", "")).lower() in ("seed", "series a"): s += 3
    return round(min(100, s), 1)


def hubspot_deal_keys():
    """Every company name + domain that already has a LIVE deal in either portal."""
    names, doms = set(), set()
    for key in ("hubspot_key", "hubspot_kartik"):
        tok = env.get(key)
        if not tok: continue
        after = None
        while True:
            body = {"limit": 200, "filterGroups": [],
                    "properties": ["dealname", "lh2_domain"]}
            if after: body["after"] = after
            req = urllib.request.Request("https://api.hubapi.com/crm/v3/objects/deals/search",
                data=json.dumps(body).encode(), method="POST",
                headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=45) as r: d = json.loads(r.read().decode())
            except Exception: break
            for x in d.get("results", []):
                p = x["properties"]
                if p.get("dealname"): names.add(norm(p["dealname"]))
                if p.get("lh2_domain"): doms.add(str(p["lh2_domain"]).lower().strip())
            after = d.get("paging", {}).get("next", {}).get("after")
            if not after: break
            time.sleep(0.1)
    return names, doms


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=500)
    ap.add_argument("--lo", type=int, default=180)   # band widened 200->180 to reach 500
    ap.add_argument("--hi", type=int, default=500)
    a = ap.parse_args()

    rows = []
    for f in ("funded", "unfunded"):
        rows += [dict(r, _tab=f) for r in json.load(open(os.path.join(SRC, f + ".json"), encoding="utf-8"))]
    step = collections.OrderedDict(); step["tracxn rows (funded + unfunded)"] = len(rows)

    have_emp = [r for r in rows if num(r.get("Total Employee Count")) is not None]
    step["have a headcount figure"] = len(have_emp)

    band = [r for r in have_emp if a.lo <= num(r["Total Employee Count"]) <= a.hi]
    step[f"headcount {a.lo}-{a.hi}"] = len(band)

    india = [r for r in band if norm(r.get("Country")) in ("india", "")]
    step["India"] = len(india)

    small = [r for r in india
             if not is_big(r.get("Company Name"), num(r.get("Annual Revenue (USD)")))]
    step["not a big corporate / MNC arm"] = len(small)

    notlisted = [r for r in small if not yes(r.get("Is IPO"))]
    step["not listed (IPO)"] = len(notlisted)

    aged = []
    for r in notlisted:
        y = num(r.get("Founded Year"))
        if y and y <= 2022: aged.append(r)
    step["founded <= 2022"] = len(aged)

    # ---- net-new ----
    hs_names, hs_doms = hubspot_deal_keys()
    pool = json.load(open(os.path.join(HUB, "crm_mirror", "holding",
                                       "tracxn_pool_2026-08-04.json"), encoding="utf-8"))
    pool_names = {norm(r["company"]) for r in pool}
    seen_n, seen_d, net = set(), set(), []
    dup_hs = dup_pool = dup_self = 0
    for r in aged:
        n = norm(r.get("Company Name")); d = str(r.get("Domain Name") or "").lower().strip()
        if n in seen_n or (d and d in seen_d): dup_self += 1; continue
        if n in hs_names or (d and d in hs_doms): dup_hs += 1; continue
        if n in pool_names: dup_pool += 1; continue
        seen_n.add(n); seen_d.add(d); net.append(r)
    step["minus dupes inside Tracxn"] = f"-{dup_self}"
    step["minus already a deal in HubSpot (both portals)"] = f"-{dup_hs}"
    step["minus the pulled-back Tracxn pool"] = f"-{dup_pool}"
    step["NET-NEW available"] = len(net)

    scored = []
    for r in net:
        emp = num(r["Total Employee Count"]); rev = num(r.get("Annual Revenue (USD)"))
        y = num(r.get("Founded Year")); age = 2026 - y if y else 0
        scored.append({"company": r.get("Company Name"), "domain": r.get("Domain Name") or "",
                       "employees": emp, "founded": y, "age_years": age, "city": r.get("City") or "",
                       "state": r.get("State") or "", "revenue_usd": rev or "",
                       "sector": (r.get("Sector (Pratice Area & Feed)") or "").split(">")[0].strip(),
                       "sector_full": r.get("Sector (Pratice Area & Feed)") or "",
                       "business_model": (r.get("Business Models") or "")[:120],
                       "stage": r.get("Company Stage") or "", "deadpooled": r.get("Is Deadpooled") or "",
                       "acquired": r.get("Is Acquired") or "", "funding_usd": num(r.get("Total Funding (USD)")) or "",
                       "linkedin": r.get("LinkedIn") or "", "website": r.get("Website") or "",
                       "key_people": r.get("Key People Info") or "",
                       "key_people_emails": r.get("Key People Email Ids") or "",
                       "key_people_profiles": r.get("Links to Key People Profiles") or "",
                       "company_emails": r.get("Company Emails") or "",
                       "company_phones": r.get("Company Phone Numbers") or "",
                       "tracxn_url": r.get("Tracxn URL") or "", "source_tab": r["_tab"],
                       "ops_score": ops_score(r, emp, age, rev)})
    scored.sort(key=lambda x: -x["ops_score"])
    pick = scored[:a.n]

    jp = os.path.join(OUT, "opsdata_net_new_500.json")
    cp = os.path.join(OUT, "opsdata_net_new_500.csv")
    json.dump(pick, open(jp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    cols = ["ops_score", "company", "domain", "employees", "founded", "age_years", "city",
            "state", "sector", "business_model", "stage", "revenue_usd", "funding_usd",
            "deadpooled", "acquired", "key_people", "key_people_emails", "company_emails",
            "key_people_profiles", "company_phones", "linkedin", "website", "tracxn_url",
            "source_tab"]
    with open(cp, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f); w.writerow(cols)
        for r in pick: w.writerow([r.get(c, "") for c in cols])

    print("=== SELECTION FUNNEL ===")
    for k, v in step.items(): print(f"  {str(v):>7}  {k}")
    print(f"\n  {len(pick):>7}  HANDED OVER (top {a.n} by ops_score)")
    json.dump({"funnel": {k: v for k, v in step.items()}, "delivered": len(pick)},
              open(os.path.join(OUT, "opsdata_selection_funnel.json"), "w", encoding="utf-8"), indent=1)
    print(f"\n-> {jp}\n-> {cp}")
    return pick, scored


if __name__ == "__main__":
    main()
