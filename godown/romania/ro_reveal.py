# -*- coding: utf-8 -*-
"""Reveal Romanian founders from LinkedIn URLs scraped off their own leadership pages.

Uses the CREDITS pool (/candidate/search). The profile SEARCH endpoint is permanently retired,
and the Anthropic key is spent, so a scraped profile URL is the only enrichment key available.

Reveal returns the person's NAME and TITLE as well as their contacts, which matters here: for
these 13 firms we never had a founder name, and this single call supplies it. No separate
name-lookup step is needed.

NO COUNTRY GATE — these are Romanian firms, so +91 cannot apply and any dialable number counts.
romania_number.py is used to LABEL what came back (mobile / landline / freephone / foreign) so a
caller knows whether they are ringing a personal handset or a switchboard, never to reject it.

Usage: python3 ro_reveal.py [--limit 0]
"""
import os, re, sys, json, time, collections, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HUB, "crm_mirror", "enrich"))
from romania_number import to_e164 as ro_e164, classify as ro_class

env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
SH = env["signal_hire"]
SRC = os.path.join(HERE, "ro50_people.json")
OUT = os.path.join(HERE, "ro50_revealed.json")
LIMIT = 0
for i, a in enumerate(sys.argv):
    if a == "--limit": LIMIT = int(sys.argv[i+1])

SENIOR = re.compile(r"\b(founder|co[- ]?founder|ceo|chief executive|managing director|\bmd\b|"
                    r"chairman|president|owner|partner|director|chief technology|\bcto\b|"
                    r"\bcoo\b|head of|managing partner|general manager)\b", re.I)


def credits():
    try:
        r = urllib.request.Request("https://www.signalhire.com/api/v1/credits", headers={"apikey": SH})
        return json.loads(urllib.request.urlopen(r, timeout=20).read().decode()).get("credits")
    except Exception:
        return None


def reveal(url):
    body = {"items": [url], "withoutWaterfall": True}
    r = urllib.request.Request("https://www.signalhire.com/api/v1/candidate/search",
                               data=json.dumps(body).encode(), method="POST",
                               headers={"apikey": SH, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(r, timeout=60) as x:
            d = json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        return None, ("CREDITS" if e.code == 402 else f"http{e.code}")
    except Exception as e:
        return None, type(e).__name__
    for it in (d if isinstance(d, list) else d.get("results", [])) or []:
        if not isinstance(it, dict) or it.get("status") != "success": continue
        c = it.get("candidate") or {}
        exp = c.get("experience") or []
        cur = next((e for e in exp if e.get("current")), (exp[0] if exp else {}))
        return {"person": c.get("fullName"),
                "title": (cur.get("position") or c.get("headLine") or "").strip(),
                "company": (cur.get("company") or "").strip(),
                "phones": [x.get("value") for x in (c.get("contacts") or [])
                           if "phone" in str(x.get("type", "")).lower() and isinstance(x.get("value"), str)],
                "emails": [x.get("value") for x in (c.get("contacts") or [])
                           if "email" in str(x.get("type", "")).lower() and isinstance(x.get("value"), str)],
                "linkedins": [s.get("link") for s in (c.get("social") or [])
                              if "linkedin.com/in/" in str(s.get("link") or "")]}, ""
    return None, "not_found"


def main():
    rows = [r for r in json.load(open(SRC, encoding="utf-8")) if r.get("linkedin_profiles")]
    if LIMIT: rows = rows[:LIMIT]
    state = {}
    if os.path.exists(OUT):
        state = {r["domain"]: r for r in json.load(open(OUT, encoding="utf-8"))}
    c0 = credits()
    print(f"{len(rows)} firms with a scraped profile URL | {len(state)} done | credits {c0}\n", flush=True)

    for i, r in enumerate(rows, 1):
        if r["domain"] in state: continue
        got = None
        for p in r["linkedin_profiles"][:3]:
            g, note = reveal(p["url"])
            if note == "CREDITS":
                print("!! credits exhausted", flush=True)
                json.dump(list(state.values()), open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                return
            if g and SENIOR.search(g["title"] or ""): got = g; break
            if g and not got: got = g
        rec = {"name": r["name"], "domain": r["domain"]}
        if got:
            ph = ""
            for x in got["phones"]:
                e = ro_e164(x)
                if e and ro_class(e) == "mobile": ph = e; break
                if e and not ph: ph = e
            if not ph and got["phones"]:
                ph = got["phones"][0]          # foreign number: still dialable, still recorded
            rec |= {"person": got["person"], "title": got["title"],
                    "phone": ph, "phone_kind": ro_class(ph) or ("foreign" if ph else ""),
                    "email": got["emails"][0] if got["emails"] else "",
                    "linkedin": (got["linkedins"] or [r["linkedin_profiles"][0]["url"]])[0],
                    "senior": bool(SENIOR.search(got["title"] or "")), "source": "signalhire reveal"}
        else:
            rec |= {"person": "", "phone": "", "senior": False, "source": "reveal failed"}
        state[r["domain"]] = rec
        json.dump(list(state.values()), open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f'  [{i}/{len(rows)}] {r["name"][:28]:<30}{(rec.get("person") or "-")[:22]:<24}'
              f'{(rec.get("title") or "")[:24]:<26}{rec.get("phone") or "-":<17}{rec.get("phone_kind","")}',
              flush=True)
        time.sleep(0.25)

    fin = list(state.values())
    print(f"\ncredits {c0} -> {credits()}")
    ok = [r for r in fin if r.get("person")]
    ph = [r for r in ok if r.get("phone")]
    print(f"named   : {len(ok)}/{len(fin)}")
    print(f"with a phone : {len(ph)}   ({sum(1 for r in ph if r.get('phone_kind')=='mobile')} Romanian mobiles)")
    print(f"senior  : {sum(1 for r in ok if r.get('senior'))}")


main()
