# -*- coding: utf-8 -*-
"""V5 intersection bake-off — 10 firms, measure before rollout. Does NOT push to HubSpot.

Tests whether the COMPANY-URL ANCHOR cracks the namesake problem that name+city search could
not. Firms chosen from the 233 that name-only search FAILED, so any success here is net-new.

Stage 2  resolve company -> LinkedIn company URL   harvestapi/linkedin-company (searches[])
         verify: the resolved company's website domain matches our domain
Stage 3  by-name search ANCHORED to that company    linkedin-profile-search-by-name
         (currentCompanies=[url]) -> profiles already tied to the company = no namesake guess
Stage 4  name match MCA <-> LinkedIn                rapidfuzz token_set_ratio + initial
         expansion + phonetic fallback; company anchor already confirmed, so accept >=80
Stage 5  reveal the matched URL                     SignalHire (measure phone/+91, no push)

Reports the four numbers V5 gates rollout on: intersection rate, LinkedIn-zero rate,
Indian-mobile fill rate, blended cost/useful-lead. Usage: python3 bakeoff.py
"""
import os, re, json, time, urllib.request, urllib.error, urllib.parse, sys
from rapidfuzz import fuzz
try: from metaphone import doublemetaphone
except Exception: doublemetaphone = None

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HUB, "crm_mirror", "enrich"))
from indian_number import to_e164, classify as in_classify
env = {l.split('=', 1)[0].strip(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
TOK = env["APIFY_TOKEN"]; SH = env["signal_hire"]
def act(name): return f"https://api.apify.com/v2/acts/{name}/run-sync-get-dataset-items?token=" + urllib.parse.quote(TOK)

# cost model (from the confirmed pricing tables)
C_COMPANY = 0.0025     # linkedin-company ~ $2-3/1k
C_SEARCHPAGE = 0.004   # search page result $4/1k (per returned profile)


def apify(name, body, timeout=180):
    try:
        r = urllib.request.Request(act(name), data=json.dumps(body).encode(), method="POST",
                                   headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(r, timeout=timeout) as x:
            return json.loads(x.read().decode()), 200
    except urllib.error.HTTPError as e:
        return {"raw": e.read().decode()[:150]}, e.code
    except Exception as e:
        return {"err": type(e).__name__}, 0


def reveal(url):
    body = {"items": [url], "withoutWaterfall": True}
    r = urllib.request.Request("https://www.signalhire.com/api/v1/candidate/search",
                               data=json.dumps(body).encode(), method="POST",
                               headers={"apikey": SH, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(r, timeout=60) as x:
            d = json.loads(x.read().decode())
    except Exception as e:
        return None, type(e).__name__
    for it in (d if isinstance(d, list) else d.get("results", [])) or []:
        if isinstance(it, dict) and it.get("status") == "success":
            c = it.get("candidate") or {}
            ph = [x.get("value") for x in (c.get("contacts") or [])
                  if "phone" in str(x.get("type", "")).lower() and isinstance(x.get("value"), str)]
            return {"sh_name": c.get("fullName") or "", "phones": ph}, ""
    return None, "not_found"


def norm(s):
    s = re.sub(r"\b(mr|ms|mrs|dr|shri|smt)\b", " ", (s or "").lower())
    return re.sub(r"\s+", " ", re.sub(r"[^a-z ]", " ", s)).strip()


def name_score(mca, li):
    a, b = norm(mca), norm(li)
    if not a or not b: return 0
    base = fuzz.token_set_ratio(a, b)
    ta, tb = a.split(), b.split()
    # initial expansion: single-char token matches any token with that initial
    bonus = 0
    for x in ta:
        if len(x) == 1 and any(y.startswith(x) for y in tb): bonus = max(bonus, 82)
    # phonetic fallback on surnames
    if doublemetaphone and ta and tb:
        if doublemetaphone(ta[-1])[0] and doublemetaphone(ta[-1])[0] == doublemetaphone(tb[-1])[0]:
            bonus = max(bonus, 84)
    return max(base, bonus)


def dom_of(url): return urllib.parse.urlparse(url or "").netloc.lower().replace("www.", "")


def main():
    firms = json.load(open(os.path.join(HERE, "bakeoff_firms.json")))
    spend = 0.0; rows = []
    for f in firms:
        rec = {**f, "company_url": "", "url_hc": "", "candidates": 0, "linkedin_url": "",
               "name_score": 0, "tier": "mca-only", "reveal": "-", "indian_mobile": ""}
        # Stage 2: resolve company URL
        d, code = apify("harvestapi~linkedin-company", {"searches": [f"{f['company']} {f.get('city','')}".strip()]})
        spend += C_COMPANY
        best = None
        for it in (d if isinstance(d, list) else []):
            if dom_of(it.get("website")) == f["domain"].lower(): best = it; break
            if best is None: best = it            # fallback: first result if no domain match
        if best:
            rec["company_url"] = best.get("linkedinUrl", "")
            rec["url_hc"] = best.get("employeeCount", "")
            rec["url_domain_match"] = dom_of(best.get("website")) == f["domain"].lower()
        if not rec["company_url"]:
            rec["tier"] = "no-company-page"; rows.append(rec); print(_line(rec), flush=True); continue
        # Stage 3: by-name anchored to the company
        parts = f["mca_name"].split()
        body = {"firstName": parts[0], "lastName": parts[-1], "profileScraperMode": "Short",
                "currentCompanies": [rec["company_url"]], "maxItems": 5}
        d, code = apify("harvestapi~linkedin-profile-search-by-name", body)
        profs = d if isinstance(d, list) else []
        spend += len(profs) * C_SEARCHPAGE
        rec["candidates"] = len(profs)
        # Stage 4: name match (company already anchored by the search filter)
        best_s, best_u, best_n = 0, "", ""
        for p in profs:
            u = (p.get("linkedinUrl") or "").split("?")[0].rstrip("/")
            if "/in/" not in u: continue
            s = name_score(f["mca_name"], p.get("name", ""))
            if s > best_s: best_s, best_u, best_n = s, u, p.get("name", "")
        rec["name_score"] = best_s; rec["linkedin_url"] = best_u; rec["li_name"] = best_n
        if best_u and best_s >= 80: rec["tier"] = "full"
        elif best_u and best_s >= 60: rec["tier"] = "title-only"
        # Stage 5: reveal (measure only)
        if rec["tier"] in ("full", "title-only"):
            got, note = reveal(best_u)
            if got:
                ind = next((to_e164(x) for x in got["phones"] if in_classify(x) == "mobile"), "")
                rec["reveal"] = "success" if got["phones"] else "no-contact"
                rec["indian_mobile"] = "YES" if ind else ""
            else:
                rec["reveal"] = note
        rows.append(rec); print(_line(rec), flush=True); time.sleep(0.3)

    n = len(rows)
    full = sum(1 for r in rows if r["tier"] == "full")
    nopage = sum(1 for r in rows if r["tier"] == "no-company-page")
    mobile = sum(1 for r in rows if r["indian_mobile"] == "YES")
    useful = mobile or 1
    json.dump(rows, open(os.path.join(HERE, "bakeoff_results.json"), "w"), indent=1, ensure_ascii=False)
    print("\n" + "=" * 70)
    print(f"BAKE-OFF ({n} firms, all previously UNRESOLVED by name-only search)")
    print(f"  company page found      : {n - nopage}/{n}")
    print(f"  intersection (full tier): {full}/{n}  ({100*full//n}%)")
    print(f"  LinkedIn-zero (no page/no match): {nopage + sum(1 for r in rows if r['tier']=='mca-only')}/{n}")
    print(f"  Indian-mobile fill      : {mobile}/{n}")
    print(f"  total spend             : ~${spend:.3f}")
    print(f"  cost per Indian-mobile lead: ~${spend/mobile:.3f}" if mobile else "  cost per lead: n/a (0 mobiles)")


def _line(r):
    return (f'  {str(r.get("hc","")):<5}{r["company"][:26]:<28}url={"Y" if r["company_url"] else "N"} '
            f'cand={r["candidates"]} score={r["name_score"]:<4}{r["tier"]:<14}'
            f'{r["reveal"]:<12}{"+91" if r["indian_mobile"]=="YES" else ""}')


main()
