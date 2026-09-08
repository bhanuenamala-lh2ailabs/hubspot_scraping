# -*- coding: utf-8 -*-
"""Filter and rank the NASSCOM member list, and cut a 200-row slice for manual checking.

WHAT THIS CAN AND CANNOT DO. Our proven IT filter is built on HEADCOUNT — band 250-999 is
priority 1 (74% useful-lead rate) and 50-249 in a top-10 city is priority 2 (55%). The NASSCOM
directory carries name, city and website only. There is no size anywhere on the listing, so the
strongest signal we have is simply unavailable here and nothing below is a substitute for it.

So this applies only what the data supports:
  * dedup on DOMAIN first (the reliable key — SalesNav had no website column and had to fall
    back to company name), then on normalised name
  * drop firms already in HubSpot or already called in the tracker sheet
  * drop entries that are not prospectable companies: coworking, staffing/recruitment, edtech,
    BPO/KPO, enterprise and captive arms of large groups
  * city is recorded but NOT ranked on — it never excluded anyone, and measured on this pool it
    predicts nothing once relevance, headcount and pre-2024 evidence are applied

Everything surviving is a CANDIDATE, not a qualified lead. Judging "does this firm do proper
software development" needs the website read, which is the agent step and is not done here.

Usage: python3 filter_nasscom.py [--slice 200]
"""
import os, re, sys, csv, json, time, collections, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
H = {"Authorization": "Bearer " + env["hubspot_key"], "Content-Type": "application/json"}
SRC = os.path.join(HERE, "nasscom_members.csv")
SLICE = 200
for i, a in enumerate(sys.argv):
    if a == "--slice": SLICE = int(sys.argv[i+1])

TOP_CITIES = ("mohali", "surat", "chennai", "indore", "gurgaon", "gurugram", "bengaluru",
              "bangalore", "mumbai", "ahmedabad", "kolkata", "coimbatore", "pune", "hyderabad",
              "noida", "delhi")

# Not prospectable for a codebase acquisition, whatever their website says.
NOT_A_TARGET = [
    ("coworking/office",  r"\b(coworking|co-working|office space|workspace|namma office|avant|spaces)\b"),
    ("staffing/recruit",  r"\b(staffing|recruit|manpower|placement|hiring|talent solutions|outsourcing services|hr services)\b"),
    ("edtech/training",   r"\b(education technolog|edtech|academy|institute of|training|e-?learning|university|school)\b"),
    ("bpo/kpo",           r"\b(bpo|kpo|call cent|business process|transcription|back ?office)\b"),
    ("consulting only",   r"\b(management consult|advisory services|chartered account|legal services)\b"),
    ("non-software",      r"\b(logistics|shipping|freight|hospitality|hotel|realty|real estate|construction|"
                          r"pharma|diagnostic|clinic|hospital|agri|textile|apparel|jewel)\b"),
]
# Enterprise / captive arms — same class the SalesNav pass had to strip out after
# Thomson Reuters India and Tata Motors Global Services reached rank 4 and 8.
BIG_BRANDS = ["tata", "adani", "reliance", "thomson reuters", "infosys", "wipro", "hcl", "tcs",
              "accenture", "cognizant", "capgemini", "deloitte", "kpmg", "ibm", "oracle", "sap",
              "siemens", "bosch", "honeywell", "schneider", "mahindra", "godrej", "larsen",
              "vedanta", "icici", "hdfc", "kotak", "bharti", "airtel", "vodafone", "hitachi",
              "zuora", "microsoft", "amazon", "google", "adobe", "salesforce", "dell", "cisco",
              "ericsson", "nokia", "samsung", "lg ", "philips", "abb", "ge ", "jio"]


def hs(u, m="GET", b=None):
    d = json.dumps(b).encode() if b is not None else None
    for a in range(6):
        try:
            r = urllib.request.Request("https://api.hubapi.com" + u, data=d, method=m, headers=H)
            with urllib.request.urlopen(r, timeout=60) as x:
                t = x.read().decode(); return x.status, (json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and a < 5: time.sleep(2*(a+1)); continue
            return e.code, {}
        except Exception:
            if a == 5: raise
            time.sleep(3*(a+1))


def domain(u):
    u = (u or "").strip().lower()
    if not u or "@" in u.split("/")[0]: return ""
    u = re.sub(r"^https?://", "", u).split("/")[0].split("?")[0]
    u = re.sub(r"^www\.", "", u)
    return u if "." in u else ""


def nm(s):
    """Same normaliser the IT push uses, so both agree on 'already have it'."""
    s = (s or "").lower(); s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r"\b(pvt|private|ltd|limited|llp|inc|technologies|technology|solutions|software|"
               r"systems|labs|services|consulting|infotech|it|the|india|global|group)\b", " ", s)
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


def reason_out(name, site):
    t = f"{name} {site}".lower()
    toks = set(re.findall(r"[a-z]+", name.lower()))
    for lbl, rx in NOT_A_TARGET:
        if re.search(rx, t): return lbl
    for b in BIG_BRANDS:
        if all(x in toks for x in b.split()): return f"enterprise brand: {b.strip()}"
    return ""


def main():
    rows = list(csv.DictReader(open(SRC, encoding="utf-8-sig")))
    print(f"scraped members: {len(rows)}")

    # ---- dedup inside the list, on domain then name ----
    seen_d, seen_n, uniq, dup = set(), set(), [], 0
    for r in rows:
        d, k = domain(r["website"]), nm(r["name"])
        if (d and d in seen_d) or (not d and k and k in seen_n): dup += 1; continue
        if d: seen_d.add(d)
        if k: seen_n.add(k)
        r["domain"] = d
        uniq.append(r)
    print(f"after in-list dedup: {len(uniq)}  ({dup} duplicates)")

    nosite = [r for r in uniq if not r["domain"]]
    uniq = [r for r in uniq if r["domain"]]
    print(f"dropped, no usable website: {len(nosite)}")

    # ---- not-a-target ----
    keep, out = [], collections.Counter()
    for r in uniq:
        why = reason_out(r["name"], r["website"])
        if why: out[why] += 1; continue
        keep.append(r)
    print(f"\ndropped as not prospectable: {sum(out.values())}")
    for k, v in out.most_common(): print(f"   {v:>4}  {k}")

    # ---- already ours ----
    after, deals = None, []
    while True:
        b = {"limit": 200, "properties": ["dealname", "lh2_domain"], "filterGroups": []}
        if after: b["after"] = after
        _, d = hs("/crm/v3/objects/deals/search", "POST", b)
        deals += d.get("results", [])
        after = (d.get("paging") or {}).get("next", {}).get("after")
        if not after: break
    hdom = {(x["properties"].get("lh2_domain") or "").lower().strip() for x in deals}; hdom.discard("")
    hnm = {nm(x["properties"].get("dealname")) for x in deals}; hnm.discard("")
    # Company domains, but ONLY for companies that actually carry a deal. The standing dedup
    # rule is deals-only: a company record with no deal is not a worked lead. HubSpot auto-creates
    # company records from email domains and from earlier imports, so treating a bare company as
    # "already ours" silently buries leads nobody has ever called. An earlier version of this file
    # excluded on any company domain and dropped 18 firms that had no deal at all.
    after, comp = None, {}
    while True:
        b = {"limit": 200, "properties": ["domain", "name"], "filterGroups": []}
        if after: b["after"] = after
        _, d = hs("/crm/v3/objects/companies/search", "POST", b)
        for x in d.get("results", []):
            if x["properties"].get("domain"): comp[x["id"]] = x["properties"]["domain"].lower().strip()
        after = (d.get("paging") or {}).get("next", {}).get("after")
        if not after: break
    with_deal = set()
    dids = [x["id"] for x in deals]
    for i in range(0, len(dids), 100):
        _, a = hs("/crm/v4/associations/deals/companies/batch/read", "POST",
                  {"inputs": [{"id": x} for x in dids[i:i+100]]})
        for r in a.get("results", []):
            # toObjectId comes back as an INT here while object ids everywhere else in the v3
            # API are STRINGS — without str() this set never intersects `comp` and the whole
            # check silently passes everything.
            for t in r.get("to", []): with_deal.add(str(t.get("toObjectId")))
    cdom = {comp[c] for c in with_deal if c in comp}
    print(f"   company records: {len(comp)} with a domain, {len(cdom)} of those carry a deal")
    try:
        sheet = set(json.load(open(os.path.join(HUB, "crm_mirror", "data", "index",
                                                "sheet_worked_exclude.json"), encoding="utf-8")).get("names", []))
    except Exception:
        sheet = set()
    print(f"\nHubSpot: {len(deals)} deals ({len(hdom)} domains), {len(cdom)} company domains, "
          f"{len(sheet)} tracker-sheet names")

    fresh, hit = [], collections.Counter()
    for r in keep:
        if r["domain"] in hdom: hit["deal already has this domain"] += 1; continue
        if r["domain"] in cdom: hit["company record has this domain"] += 1; continue
        if nm(r["name"]) in hnm: hit["deal name matches"] += 1; continue
        if nm(r["name"]) in sheet: hit["already called in tracker sheet"] += 1; continue
        fresh.append(r)
    for k, v in hit.most_common(): print(f"   -{v:<5} {k}")
    print(f"\nNET-NEW CANDIDATES: {len(fresh)}")

    # ---- city is recorded but NO LONGER RANKED ON ----
    # It never excluded anyone; it only ordered the list. Measured on this pool, it does not
    # predict anything once the real filters are applied: tier-2 firms are 70% plausible-software
    # vs 67% for tier-1, equally reachable, and at least as likely to land in the 250-600 band.
    # Kept as a column because callers still want to know where a firm is.
    for r in fresh:
        c = (r["city"] or "").lower()
        r["city_tier"] = 1 if any(t in c for t in TOP_CITIES) else 2
    fresh.sort(key=lambda r: r["name"].lower())
    for i, r in enumerate(fresh, 1): r["rank"] = i
    print(f"   (city recorded, not ranked)  tier-1: {sum(1 for r in fresh if r['city_tier']==1)}   "
          f"tier-2: {sum(1 for r in fresh if r['city_tier']==2)}")
    print("   top cities:", dict(collections.Counter(r["city"] for r in fresh).most_common(10)))

    cols = ["rank", "name", "city", "city_tier", "website", "domain",
            "RELEVANT? (Yes/No/Maybe)", "does proper software dev?", "product or service?", "NOTES"]
    def write(path, rs):
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
            for r in rs:
                w.writerow({**{k: r.get(k, "") for k in ("rank", "name", "city", "city_tier", "website", "domain")},
                            "RELEVANT? (Yes/No/Maybe)": "", "does proper software dev?": "",
                            "product or service?": "", "NOTES": ""})
    write(os.path.join(HERE, "nasscom_candidates_ALL.csv"), fresh)
    # Slice is EVERY Nth, not the top N: the top of the list is alphabetical inside tier 1 and
    # would hand back a sample of companies whose names start with A.
    step = max(1, len(fresh) // SLICE)
    sample = fresh[::step][:SLICE]
    write(os.path.join(HERE, "nasscom_sample_200.csv"), sample)
    print(f"\nwrote nasscom_candidates_ALL.csv  ({len(fresh)} rows)")
    print(f"wrote nasscom_sample_200.csv      ({len(sample)} rows, every {step}th — representative, not the top)")


main()
