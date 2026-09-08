# -*- coding: utf-8 -*-
"""Reveal contacts for founders we already identified, using the CREDITS pool, not search.

SignalHire meters two things separately and only one of them is empty:
    /candidate/searchByQuery   profile SEARCH   -> daily quota, currently exhausted (402)
    /candidate/search          REVEAL           -> credits, 2,380 remaining, working

Reveal accepts a LinkedIn profile URL directly as an item, so for anyone whose profile URL we
already scraped off their company's own leadership page, we can skip the search entirely. That
is the whole point of having collected those URLs rather than just names.

Costs 1 credit per person, 0 searches. `withoutWaterfall: True` is required — without it the API
demands a callback URL and returns 406.

THE +91 GATE STILL APPLIES HERE. These are Indian companies and the standing rule is unchanged:
no Indian mobile, no push. The reveal returns whatever numbers exist, including foreign ones —
a founder whose only number is +1 is recorded honestly as blocked rather than pushed anyway.

Usage: python3 reveal_by_linkedin.py [--apply]
"""
import os, re, sys, json, glob, time, collections, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HUB, "crm_mirror", "enrich"))
from indian_number import to_e164, classify

env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
SH = env["signal_hire"]
OUT = os.path.join(HERE, "above20_revealed.json")
MINSCORE = 20


def credits():
    try:
        r = urllib.request.Request("https://www.signalhire.com/api/v1/credits", headers={"apikey": SH})
        return json.loads(urllib.request.urlopen(r, timeout=20).read().decode()).get("credits")
    except Exception:
        return None


def reveal(item):
    """1 credit, 0 searches. item may be a LinkedIn URL, a uid or an email."""
    body = {"items": [item], "withoutWaterfall": True}
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
    res = d if isinstance(d, list) else d.get("results", [])
    for it in res or []:
        if isinstance(it, dict) and it.get("status") == "success":
            c = it.get("candidate") or {}
            ph = [x.get("value") for x in (c.get("contacts") or [])
                  if "phone" in str(x.get("type", "")).lower() and isinstance(x.get("value"), str)]
            em = [x.get("value") for x in (c.get("contacts") or [])
                  if "email" in str(x.get("type", "")).lower() and isinstance(x.get("value"), str)]
            li = [s.get("link") for s in (c.get("social") or [])
                  if "linkedin.com/in/" in str(s.get("link") or "")]
            return {"full_name": c.get("fullName"), "phones": ph, "emails": em, "linkedins": li}, ""
    return None, "not_found"


def main():
    sc = {}
    for f in glob.glob(os.path.join(HERE, "score_batches", "scored_*.json")):
        for r in json.load(open(f, encoding="utf-8")): sc[r["domain"]] = r
    for r in json.load(open(os.path.join(HERE, "inrange_scored.json"), encoding="utf-8")):
        sc[r["domain"]] = r
    fo = {}
    for f in glob.glob(os.path.join(HERE, "people_batches", "found_*.json")):
        for r in json.load(open(f, encoding="utf-8")): fo[r["domain"]] = r
    for r in json.load(open(os.path.join(HERE, "inrange_founders.json"), encoding="utf-8")):
        fo[r["domain"]] = r
    bun = {}
    for f in ("score_bundles.json", "inrange_bundles.json"):
        for r in json.load(open(os.path.join(HERE, f), encoding="utf-8")): bun[r.get("domain")] = r

    above = [r for r in sc.values() if isinstance(r.get("score"), int) and r["score"] > MINSCORE]
    todo = []
    for r in above:
        f = fo.get(r["domain"]) or {}
        if f.get("person") and f.get("linkedin"):
            todo.append((r, f))
    todo.sort(key=lambda x: -x[0]["score"])

    state = {r["domain"]: r for r in json.load(open(OUT, encoding="utf-8"))} if os.path.exists(OUT) else {}
    c0 = credits()
    print(f"above score {MINSCORE}: {len(above)} | with name+LinkedIn: {len(todo)} | "
          f"already revealed: {len(state)} | credits {c0}\n", flush=True)

    tally = collections.Counter()
    for i, (r, f) in enumerate(todo, 1):
        d = r["domain"]
        if d in state: continue
        got, note = reveal(f["linkedin"])
        if note == "CREDITS":
            print("!! credits exhausted — stopping cleanly", flush=True); break
        rec = {"domain": d, "name": r["name"], "score": r["score"], "band": r["band"],
               "website": (bun.get(d) or {}).get("website", ""), "city": (bun.get(d) or {}).get("city", ""),
               "person": f["person"], "title": f.get("title", ""), "linkedin": f["linkedin"],
               "reveal_status": note or "ok"}
        if got:
            ind = next((to_e164(p) for p in got["phones"] if to_e164(p)), "")
            rec |= {"sh_name": got["full_name"], "all_phones": got["phones"],
                    "emails": got["emails"], "email": got["emails"][0] if got["emails"] else "",
                    "indian_phone": ind, "phone_kind": classify(ind) if ind else "",
                    "linkedin_confirmed": got["linkedins"][0] if got["linkedins"] else ""}
            rec["gate"] = "PASS +91" if ind else ("BLOCKED - foreign number only" if got["phones"]
                                                 else "BLOCKED - no phone at all")
        else:
            rec |= {"all_phones": [], "emails": [], "email": "", "indian_phone": "",
                    "gate": f"BLOCKED - {note}"}
        tally[rec["gate"]] += 1
        state[d] = rec
        json.dump(list(state.values()), open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f'  [{i}/{len(todo)}] {r["score"]:>3} {r["name"][:30]:<32}{f["person"][:20]:<22}'
              f'{rec.get("indian_phone") or "-":<16}{rec["gate"]}', flush=True)
        time.sleep(0.3)

    fin = list(state.values())
    print(f"\ncredits {c0} -> {credits()}")
    print("\ngate outcome:")
    for k, v in collections.Counter(r["gate"] for r in fin).most_common(): print(f"   {v:>4}  {k}")
    ok = [r for r in fin if r.get("indian_phone")]
    print(f"\nPUSHABLE ({len(ok)}):")
    for r in sorted(ok, key=lambda x: -x["score"]):
        print(f'   {r["score"]:>3}  {r["name"][:34]:<36}{r["person"][:20]:<22}'
              f'{r["indian_phone"]:<16}{r.get("email","")[:30]}')


main()
