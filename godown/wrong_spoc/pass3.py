# -*- coding: utf-8 -*-
"""Pass 3 — no search engines left (all four walled this IP), so: guess the obvious domain
slugs and VERIFY by requiring the company's own name in the fetched homepage. A guess that
verifies is evidence; a guess that doesn't is discarded. Then scrape /team|/about|/leadership
on verified domains for founder names + linkedin links, same as pass 1.
"""
import os, re, sys, json, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from find_right_spoc import fetch, site_people, SENIOR
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "right_spoc_found.json")

GUESS = {
 "AllysAI": ["allysai.com", "allys.ai", "allysai.in"],
 "GTT Data Solutions Ltd": ["gttdata.com", "gttdatasolutions.com", "gttdata.in"],
 "TeamLease Regtech Pvt. Ltd.": ["teamleaseregtech.com"],
 "Qualitrix": ["qualitrix.com"],
 "Cloud Certitude": ["cloudcertitude.com"],
 "Technocolabs Softwares Inc.": ["technocolabs.com", "technocolabs.in"],
 "Airdit Software Services": ["airdit.com", "airdit.in"],
 "VIEH Group": ["viehgroup.com", "vieh.in"],
 "NetAnalytiks": ["netanalytiks.com"],
 "Enzigma": ["enzigma.com", "enzigma.in"],
 "Novastrid": ["novastrid.com", "novastrid.in"],
 "Caizin": ["caizin.com"],
}
def key(nm):  # first distinctive token of the company name, for homepage verification
    t = re.sub(r"[^a-z0-9 ]", " ", nm.lower()).split()
    return next((x for x in t if x not in ("the", "pvt", "ltd", "data", "cloud", "software",
                                           "solutions", "services", "group", "inc")), t[0])

rows = json.load(open(OUT))
for r in rows:
    if not (r["action"].startswith("not") or (r["name"] == "Caizin")): continue
    dom_ok = ""
    for g in GUESS.get(r["name"], []):
        h = fetch(f"https://{g}") or fetch(f"http://{g}")
        if h and key(r["name"]) in h.lower():
            dom_ok = g; break
    if not dom_ok:
        print(f'{r["name"][:30]:<32}no verified domain', flush=True); continue
    r["domain_resolved"] = dom_ok
    person = title = li = ""
    for nm, tt, lk in site_people(dom_ok):
        if nm and SENIOR.search(tt): person, title, li = nm, tt, lk; break
        if lk and not li: li = lk
    r["person"] = person or r.get("person", "")
    r["title"] = title or r.get("title", "")
    r["linkedin"] = li or r.get("linkedin", "")
    r["source"] = f"verified domain guess {dom_ok} + site scrape"
    r["action"] = ("reveal-candidate" if li else "name-only" if person else
                   "domain-found — team page empty")
    print(f'{r["name"][:30]:<32}{dom_ok:<26}{(person or "-")[:22]:<24}{"LI" if li else ""}', flush=True)
    json.dump(rows, open(OUT, "w"), indent=1, ensure_ascii=False)
json.dump(rows, open(OUT, "w"), indent=1, ensure_ascii=False)
acts = {}
for r in rows: acts[r["action"].split(" ")[0]] = acts.get(r["action"].split(" ")[0], 0) + 1
print("\nfinal:", acts)
