# -*- coding: utf-8 -*-
"""Fill the gaps on the Bangladesh 100 via SignalHire, then hand off a push-ready file.

The website sweep already got a company phone for 74 of 100 and a person's name for 40. This
covers what is left, and it is written to be re-runnable: it skips anything already resolved,
so a quota cut-off costs nothing but time.

TWO DIFFERENT JOBS, and the cheaper one runs first:
  1. companies with NO phone at all (26)      -> must find a founder and reveal, or they cannot
                                                 be called at all
  2. companies with a phone but NO name (34)  -> a company mainline is dialable, but "may I speak
                                                 to the founder" is a much weaker open than using
                                                 their name, so this is worth a search each

A search costs quota; a reveal costs a credit. Reveal only fires when the search actually
matched, so a company with no SignalHire presence costs one search and nothing more.

NUMBER RULE FOR THIS BATCH: any dialable number qualifies, not just +880 — that is a deliberate
exception granted for Bangladesh. bangladesh_number.py is used to LABEL what we got (BD mobile
vs landline vs foreign), never to reject it.

Usage: python3 bd_enrich.py [--limit 0]
"""
import os, re, sys, json, time, collections, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HUB, "crm_mirror", "enrich"))
from bangladesh_number import to_e164 as bd_e164, classify as bd_class

env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
SH = env["signal_hire"]
SRC = os.path.join(HERE, "bd_consolidated.json")
OUT = os.path.join(HERE, "bd_enriched.json")
LIMIT = 0
for i, a in enumerate(sys.argv):
    if a == "--limit": LIMIT = int(sys.argv[i+1])

try: from rapidfuzz import fuzz
except Exception: fuzz = None

TITLES = ("Founder OR Co-Founder OR Cofounder OR CEO OR Chief Executive OR Managing Director OR "
          "Director OR Chairman OR Owner OR Proprietor")


def post(path, body, t=60):
    r = urllib.request.Request("https://www.signalhire.com/api/v1" + path,
                               data=json.dumps(body).encode(), method="POST",
                               headers={"apikey": SH, "Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=t) as x:
        return json.loads(x.read().decode())


def credits():
    try:
        r = urllib.request.Request("https://www.signalhire.com/api/v1/credits", headers={"apikey": SH})
        return json.loads(urllib.request.urlopen(r, timeout=20).read().decode()).get("credits")
    except Exception:
        return None


def find(company, known_name=""):
    """1 search. Fuzzy-confirms the employer so we never reveal someone who merely mentions
    the firm in an old role. If we already scraped a name, prefer the profile that matches it."""
    try:
        d = post("/candidate/searchByQuery",
                 {"currentCompany": company, "currentTitle": TITLES, "size": 8})
    except urllib.error.HTTPError as e:
        return None, ("QUOTA" if e.code == 402 else f"http{e.code}")
    except Exception as e:
        return None, type(e).__name__
    cl = company.lower(); best = None; bs = 0
    for p in (d.get("profiles") or []):
        if not isinstance(p, dict): continue
        cs = 0
        for x in (p.get("experience") or []):
            c = str(x.get("company") or "").lower()
            cs = max(cs, fuzz.token_set_ratio(cl, c) if fuzz else (90 if (cl in c or c in cl) else 0))
        if known_name and fuzz:
            # a scraped name is strong corroboration — let it break ties
            cs = max(cs, fuzz.token_set_ratio(known_name.lower(), str(p.get("fullName") or "").lower()))
        if cs >= 80 and cs > bs: bs = cs; best = p
    return best, ("" if best else "no_match")


def reveal(uid):
    """1 credit. -> (phone, email, linkedin, note). Phone is taken as-is; this batch accepts
    any country, so the only filtering is 'is it long enough to be a phone number'."""
    try:
        d = post("/candidate/search", {"items": [uid], "withoutWaterfall": True})
    except urllib.error.HTTPError as e:
        return "", "", "", ("QUOTA" if e.code == 402 else f"http{e.code}")
    except Exception as e:
        return "", "", "", type(e).__name__
    res = d if isinstance(d, list) else d.get("results", [])
    ph, em, li = [], [], ""
    for it in res or []:
        if isinstance(it, dict) and it.get("status") == "success":
            cand = it.get("candidate", {}) or {}
            for s in cand.get("social") or []:
                l = str(s.get("link") or "")
                if "linkedin.com/in/" in l and not li: li = l
            for c in cand.get("contacts", []) or []:
                t = str(c.get("type", "")).lower(); v = c.get("value")
                if not isinstance(v, str): continue
                if "phone" in t and len(re.sub(r"\D", "", v)) >= 9: ph.append(v)
                elif "email" in t and "@" in v: em.append(v)
    return (ph[0] if ph else ""), (em[0] if em else ""), li, ("" if ph else "no_phone")


def main():
    rows = json.load(open(SRC, encoding="utf-8"))
    state = {r["domain"]: r for r in json.load(open(OUT, encoding="utf-8"))} if os.path.exists(OUT) else {}
    # cheapest-first: firms with no phone at all are the only ones that are UNCALLABLE today
    need_phone = [r for r in rows if not r["phone"] and r["domain"] not in state]
    need_name = [r for r in rows if r["phone"] and not r["founder"] and r["domain"] not in state]
    todo = need_phone + need_name
    if LIMIT: todo = todo[:LIMIT]
    c0 = credits()
    print(f"{len(rows)} firms | {len(state)} already enriched | credits {c0}")
    print(f"  no phone at all (priority) : {len(need_phone)}")
    print(f"  phone but no name          : {len(need_name)}")
    print(f"  to process this run        : {len(todo)}\n", flush=True)

    tally = collections.Counter()
    for i, r in enumerate(todo, 1):
        prof, note = find(r["name"], r.get("founder") or r.get("name_guess_from_email") or "")
        if note == "QUOTA":
            print("!! SignalHire SEARCH quota exhausted — stopping cleanly", flush=True); break
        rec = dict(r); rec["sh_status"] = note or "found"
        if prof:
            uid = prof.get("uid") or prof.get("id")
            ph, em, li, pn = reveal(uid) if uid else ("", "", "", "no_uid")
            if pn == "QUOTA":
                print("!! SignalHire CREDITS exhausted — stopping cleanly", flush=True); break
            rec["sh_person"] = (prof.get("fullName") or "").strip()
            rec["sh_title"] = ((prof.get("experience") or [{}])[0].get("title") or "").strip()
            rec["sh_phone"] = ph; rec["sh_email"] = em; rec["sh_linkedin"] = li
            if ph and not rec["phone"]:
                bd = bd_e164(ph)
                rec["phone"] = bd or ph
                rec["phone_kind"] = bd_class(bd) if bd else "other/foreign"
                rec["is_bd_mobile"] = bool(bd)
            if not rec["founder"] and rec["sh_person"]:
                rec["founder"] = rec["sh_person"]; rec["title"] = rec["sh_title"]
                rec["founder_confidence"] = "signalhire"
            if li and not rec["linkedin"]: rec["linkedin"] = li
        tally[rec["sh_status"]] += 1
        state[r["domain"]] = rec
        json.dump(list(state.values()), open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        if i % 5 == 0 or rec.get("sh_phone"):
            print(f'  [{i}/{len(todo)}] {r["name"][:30]:<32}{rec["sh_status"]:<12}'
                  f'{rec.get("sh_person","")[:22]:<24}{rec.get("phone","")}', flush=True)
        time.sleep(0.3)

    allr = {r["domain"]: r for r in rows}
    allr.update(state)
    fin = list(allr.values())
    json.dump(fin, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ph = sum(1 for r in fin if r.get("phone"))
    nm = sum(1 for r in fin if r.get("founder"))
    print(f"\noutcomes: {dict(tally)}")
    print(f"credits {c0} -> {credits()}")
    print(f"\nFINAL: {ph}/{len(fin)} have a phone (PUSHABLE) | {nm} have a founder name")
    print(f"       {sum(1 for r in fin if r.get('phone') and r.get('founder'))} have both")


main()
