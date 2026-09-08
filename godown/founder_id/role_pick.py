# -*- coding: utf-8 -*-
"""Discovery by ROLE, not by MCA name (user steer 2026-08-17).

The reachability test proved the MCA-named director is usually NOT the findable person on a
small firm's LinkedIn — but the company's employee dump reliably returns 20-25 real people
with titles + URLs. So: pull the company's people, rank them by how able they are to
authorise selling the codebase the company owns, and pick the best APPROACHABLE one.

DECISION-MAKER LADDER (who can sell a codebase / dormant IP), best first. Sales/HR/marketing/
recruiting/junior titles score to zero — reaching them wastes a dial. Tech-controlling roles
(CTO, VP-Eng, Delivery Head) rank high because for a codebase sale they are often the most
useful voice even above a non-technical CEO.

Pipeline per firm:
  company name -> LinkedIn company URL   (linkedin-company, searches[])
  -> employee dump Full mode             (linkedin-company-employees)
  -> score every person by role, pick highest
  -> that person's URL -> SignalHire reveal -> +91 gate
MCA name becomes a soft CONFIRM (if the picked person matches it, extra confidence), never a gate.

Usage: python3 role_pick.py [--firms bakeoff_firms.json] [--reveal]
"""
import os, re, sys, json, time, urllib.request, urllib.error, urllib.parse
from rapidfuzz import fuzz

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HUB, "crm_mirror", "enrich"))
from indian_number import to_e164, classify as in_classify
env = {l.split('=', 1)[0].strip(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
TOK = env["APIFY_TOKEN"]; SH = env["signal_hire"]
FIRMS = os.path.join(HERE, "bakeoff_firms.json"); REVEAL = "--reveal" in sys.argv
for i, a in enumerate(sys.argv):
    if a == "--firms": FIRMS = os.path.join(HERE, sys.argv[i + 1])

# ---------------------------------------------------------------- role ladder
# (regex, score). First match wins per title. Higher = better able to sell the codebase.
LADDER = [
    (r"\b(founder|co[-\s]?founder|co[-\s]?founded|founding (member|partner|engineer)|promoter)\b", 100),
    (r"\b(owner|proprietor|managing partner)\b", 96),
    (r"\b(chief executive|ceo)\b", 94),
    (r"\b(managing director|\bmd\b|director & ceo|ceo & director)\b", 90),
    (r"\b(chairman|chairperson|president)\b", 86),
    (r"\b(chief technology|\bcto\b|chief technical|co[-\s]?founder & cto)\b", 88),   # tech IP owner: high
    (r"\b(chief operating|\bcoo\b|chief product|\bcpo\b|chief information|\bcio\b)\b", 80),
    (r"\b(partner)\b", 74),
    (r"\b(executive director|whole[-\s]?time director|\bdirector\b)\b", 72),
    (r"\b(vp|vice president|head)\s+(of\s+)?(engineering|technology|technical|delivery|products?|software|development)\b", 70),
    (r"\b(engineering manager|technical director|delivery (head|manager|director)|technical (head|lead architect)|principal (engineer|architect)|technical architect)\b", 64),
    (r"\b(general manager|business head|country head)\b", 58),
]
# titles that DISQUALIFY even if a good word appears (a "Sales Director" is not our person)
DISQ = re.compile(r"\b(sales|marketing|hr|human resource|recruit|talent|business development|"
                  r"account manager|customer success|support|intern|trainee|junior|associate consultant|"
                  r"art director|creative director|content|design(er)?|seo|social media)\b", re.I)


def role_score(title):
    t = (title or "").lower()
    if not t: return 0, ""
    for rx, sc in LADDER:
        m = re.search(rx, t, re.I)
        if m:
            # a founder is a founder even if also "& Head of Sales"; but a pure sales/HR title with
            # only a weak 'director'/'head' match is disqualified
            if sc <= 72 and DISQ.search(t): return 0, "disqualified role"
            return sc, m.group(0)
    return 0, ""


def apify(actor, body, timeout=240):
    ep = f"https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items?token=" + urllib.parse.quote(TOK)
    try:
        r = urllib.request.Request(ep, data=json.dumps(body).encode(), method="POST",
                                   headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(r, timeout=timeout) as x:
            return json.loads(x.read().decode()), 200
    except urllib.error.HTTPError as e:
        return {"raw": e.read().decode()[:150]}, e.code
    except Exception as e:
        return {"err": type(e).__name__}, 0


def reveal(url):
    body = {"items": [url], "withoutWaterfall": True}
    try:
        r = urllib.request.Request("https://www.signalhire.com/api/v1/candidate/search",
                                   data=json.dumps(body).encode(), method="POST",
                                   headers={"apikey": SH, "Content-Type": "application/json"})
        d = json.loads(urllib.request.urlopen(r, timeout=60).read().decode())
    except Exception as e:
        return None, type(e).__name__
    for it in (d if isinstance(d, list) else d.get("results", [])) or []:
        if isinstance(it, dict) and it.get("status") == "success":
            c = it.get("candidate") or {}
            ph = [x.get("value") for x in (c.get("contacts") or [])
                  if "phone" in str(x.get("type", "")).lower() and isinstance(x.get("value"), str)]
            return {"name": c.get("fullName"), "phones": ph}, ""
    return None, "not_found"


def dom_of(u): return urllib.parse.urlparse(u or "").netloc.lower().replace("www.", "")
def nm(s): return re.sub(r"[^a-z ]", " ", (s or "").lower()).strip()


def main():
    firms = json.load(open(FIRMS)); spend = 0.0; out = []
    for f in firms:
        rec = {**f, "company_url": "", "picked": "", "picked_title": "", "role_score": 0,
               "picked_url": "", "mca_match": "", "reveal": "-", "indian_mobile": ""}
        d, _ = apify("harvestapi~linkedin-company", {"searches": [f"{f['company']} {f.get('city','')}".strip()]})
        spend += 0.0025
        # STRICT domain match: only accept a company whose website == our domain. No fallback to
        # the first result — that grafted a non-Indian namesake ("Dqot -> Charles Oliveira") on.
        best_co = next((it for it in (d if isinstance(d, list) else [])
                        if dom_of(it.get("website")) == f["domain"].lower()), None)
        if not best_co or not best_co.get("linkedinUrl"):
            rec["reveal"] = "no matching company page"; out.append(rec); print(_l(rec), flush=True); continue
        rec["company_url"] = best_co["linkedinUrl"]
        # RETRY on empty: the employee dump intermittently returns [] on a transient actor error
        # (Rheal came back 0 here but had a findable founder in the first bake-off). Retry twice.
        emps = []
        for attempt in range(3):
            r, code = apify("harvestapi~linkedin-company-employees",
                            {"companies": [rec["company_url"]], "profileScraperMode": "Full ($8 per 1k)", "maxItems": 40})
            emps = r if isinstance(r, list) else []
            if emps: break
            time.sleep(4 * (attempt + 1))
        spend += len(emps) * 0.008
        ranked = []
        for e in emps:
            name = e.get("name") or f"{e.get('firstName','')} {e.get('lastName','')}".strip()
            title = e.get("position") or e.get("headline") or ""
            sc, why = role_score(title)
            url = (e.get("linkedinUrl") or "").split("?")[0]
            if sc > 0 and url: ranked.append((sc, name, title, url))
        ranked.sort(key=lambda x: -x[0])
        if ranked:
            sc, name, title, url = ranked[0]
            rec.update({"picked": name, "picked_title": title[:50], "role_score": sc, "picked_url": url})
            rec["mca_match"] = "Y" if fuzz.token_set_ratio(nm(f["mca_name"]), nm(name)) >= 80 else ""
            rec["alt"] = [(r[1], r[2][:28]) for r in ranked[1:4]]
            if REVEAL:
                got, note = reveal(url)
                if got:
                    ind = next((to_e164(x) for x in got["phones"] if in_classify(x) == "mobile"), "")
                    rec["reveal"] = "success" if got["phones"] else "no-contact"
                    rec["indian_mobile"] = "YES" if ind else ""
                else: rec["reveal"] = note
        else:
            rec["reveal"] = f"{len(emps)} emps, no decision-maker role"
        out.append(rec); print(_l(rec), flush=True); time.sleep(0.3)

    json.dump(out, open(os.path.join(HERE, "role_pick_results.json"), "w"), indent=1, ensure_ascii=False)
    n = len(out); picked = sum(1 for r in out if r["picked_url"])
    mob = sum(1 for r in out if r["indian_mobile"] == "YES")
    print("\n" + "=" * 72)
    print(f"ROLE-PICK ({n} firms, all previously UNRESOLVED)")
    print(f"  decision-maker found on LinkedIn : {picked}/{n}")
    print(f"  picked person == MCA director    : {sum(1 for r in out if r['mca_match']=='Y')}/{picked}")
    if REVEAL:
        print(f"  Indian-mobile fill               : {mob}/{n}   cost/mobile ~${spend/mob:.3f}" if mob else f"  Indian-mobile: 0")
    print(f"  total spend                      : ~${spend:.2f}")


def _l(r):
    a = " | alt: " + ", ".join(f"{n}({t})" for n, t in r.get("alt", [])[:2]) if r.get("alt") else ""
    return (f'  {r["company"][:24]:<26}{("["+str(r["role_score"])+"] "+r["picked"][:20]) if r["picked"] else r["reveal"]:<28}'
            f'{r["picked_title"][:34]:<36}{"MCA✓" if r["mca_match"]=="Y" else ""}{" +91" if r["indian_mobile"]=="YES" else ""}')


main()
