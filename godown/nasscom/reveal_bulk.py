# -*- coding: utf-8 -*-
"""LAST STAGE: turn scraped LinkedIn profile URLs into callable leads.

Uses the CREDITS pool (/candidate/search), never the exhausted SEARCH pool. Reveal returns the
person's NAME and TITLE as well as their contacts, which is why no agent name-extraction is
needed before this: the URL alone is enough, and the API tells us who it belongs to.

CREDIT DISCIPLINE. 955 profile URLs were scraped across 182 firms — revealing all of them would
burn a third of the remaining balance on office managers and junior engineers. So per firm we
try at most MAX_PER_FIRM URLs, ordered by how founder-ish the surrounding page text looked, and
stop as soon as one reveals a senior title. A firm that lists its CEO first costs 1 credit.

Nothing is trusted from the page: seniority is judged on the title the API returns, not on the
context we guessed from. A profile whose revealed title is "Software Engineer" is discarded even
if it sat under a "Leadership" heading.

+91 GATE enforced for these Indian firms — a foreign-only number is recorded and skipped, never
pushed.

Usage: python3 reveal_bulk.py [--limit 60] [--max-per-firm 2]
"""
import os, re, sys, json, time, collections, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HUB, "crm_mirror", "enrich"))
from indian_number import to_e164, classify

env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
SH = env["signal_hire"]
SRC = os.path.join(HERE, "top600_people.json")
OUT = os.path.join(HERE, "bulk_revealed.json")
LIMIT, MAX_PER_FIRM = 0, 2
for i, a in enumerate(sys.argv):
    if a == "--src": SRC = os.path.join(HERE, sys.argv[i+1])
    if a == "--out": OUT = os.path.join(HERE, sys.argv[i+1])
    if a == "--limit": LIMIT = int(sys.argv[i+1])
    if a == "--max-per-firm": MAX_PER_FIRM = int(sys.argv[i+1])

SENIOR = re.compile(r"\b(founder|co[- ]?founder|cofounder|ceo|chief executive|managing director|"
                    r"\bmd\b|chairman|chairperson|president|owner|proprietor|partner|director|"
                    r"chief technology|\bcto\b|\bcoo\b|\bcio\b|vice president|\bvp\b|"
                    r"head of|business head|delivery head|country head)\b", re.I)
CTX = re.compile(r"\b(founder|co[- ]?founder|ceo|chief executive|managing director|chairman|"
                 r"director|president|owner|leadership|\bcto\b)\b", re.I)


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
    res = d if isinstance(d, list) else d.get("results", [])
    for it in res or []:
        if not isinstance(it, dict) or it.get("status") != "success": continue
        c = it.get("candidate") or {}
        exp = c.get("experience") or []
        # The job title lives in `position`, NOT `title` — reading the wrong key returned an
        # empty string for every person and failed 60 firms as "not senior", including a
        # founder, at ~111 credits. Prefer the role flagged `current`; fall back to the first
        # entry, then to the profile headline.
        cur = next((e for e in exp if e.get("current")), (exp[0] if exp else {}))
        pos = (cur.get("position") or "").strip()
        if not pos: pos = (c.get("headLine") or "").strip()
        return {"name": c.get("fullName"),
                "title": pos,
                "headline": (c.get("headLine") or "").strip(),
                "company": (cur.get("company") or "").strip(),
                "staff_count": cur.get("staffCount") or cur.get("companySize") or "",
                "phones": [x.get("value") for x in (c.get("contacts") or [])
                           if "phone" in str(x.get("type", "")).lower() and isinstance(x.get("value"), str)],
                "emails": [x.get("value") for x in (c.get("contacts") or [])
                           if "email" in str(x.get("type", "")).lower() and isinstance(x.get("value"), str)],
                "linkedins": [s.get("link") for s in (c.get("social") or [])
                              if "linkedin.com/in/" in str(s.get("link") or "")]}, ""
    return None, "not_found"


def main():
    rows = [r for r in json.load(open(SRC, encoding="utf-8")) if r.get("linkedin_profiles")]
    state = {r["domain"]: r for r in json.load(open(OUT, encoding="utf-8"))} if os.path.exists(OUT) else {}
    todo = [r for r in rows if r["domain"] not in state]
    if LIMIT: todo = todo[:LIMIT]
    c0 = credits()
    print(f"{len(rows)} firms with a profile URL | {len(state)} already done | "
          f"{len(todo)} this run | credits {c0}\n", flush=True)

    tally = collections.Counter(); spent = 0
    for i, r in enumerate(todo, 1):
        profs = r["linkedin_profiles"]
        # founder-ish context first; that ordering is the whole credit saving
        profs = sorted(profs, key=lambda p: not CTX.search(p.get("context") or ""))
        got = None
        for p in profs[:MAX_PER_FIRM]:
            g, note = reveal(p["url"])
            spent += 1
            if note == "CREDITS":
                print("!! credits exhausted — stopping cleanly", flush=True)
                json.dump(list(state.values()), open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                return
            if g and SENIOR.search(g["title"] or ""):
                got = g; got["source_url"] = p["url"]; break
            if g and not got:
                got = g; got["source_url"] = p["url"]      # keep as fallback, may be junior
        rec = {"domain": r["domain"], "name": r["name"]}
        if got:
            ind = next((to_e164(x) for x in got["phones"] if to_e164(x)), "")
            senior = bool(SENIOR.search(got["title"] or ""))
            rec |= {"person": got["name"], "title": got["title"], "headline": got.get("headline", ""),
                    "sh_company": got["company"], "staff_count": got.get("staff_count", ""),
                    "linkedin": (got["linkedins"] or [got["source_url"]])[0],
                    "email": got["emails"][0] if got["emails"] else "",
                    "all_phones": got["phones"], "indian_phone": ind,
                    "phone_kind": classify(ind) if ind else "", "is_senior": senior}
            rec["gate"] = ("PASS" if (ind and senior) else
                           "skip - not senior" if not senior else
                           "skip - foreign number only" if got["phones"] else "skip - no phone")
        else:
            rec |= {"person": "", "title": "", "indian_phone": "", "is_senior": False,
                    "gate": "skip - reveal failed"}
        tally[rec["gate"]] += 1
        state[r["domain"]] = rec
        json.dump(list(state.values()), open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        if rec["gate"] == "PASS" or i % 10 == 0:
            print(f'  [{i}/{len(todo)}] {r["name"][:30]:<32}{(rec.get("person") or "-")[:20]:<22}'
                  f'{(rec.get("title") or "")[:22]:<24}{rec.get("indian_phone") or "-":<15}{rec["gate"]}',
                  flush=True)
        time.sleep(0.25)

    fin = list(state.values())
    ok = [r for r in fin if r["gate"] == "PASS"]
    print(f"\ncredits {c0} -> {credits()}  (spent ~{spent} reveals)")
    print("\noutcome:")
    for k, v in collections.Counter(r["gate"] for r in fin).most_common(): print(f"   {v:>4}  {k}")
    print(f"\nPUSHABLE: {len(ok)}")
    for r in ok[:40]:
        print(f'   {r["name"][:32]:<34}{r["person"][:20]:<22}{r["title"][:24]:<26}{r["indian_phone"]}')


main()
