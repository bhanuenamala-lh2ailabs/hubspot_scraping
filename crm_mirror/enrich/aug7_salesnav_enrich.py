# -*- coding: utf-8 -*-
"""Find a founder + Indian mobile for the ranked Sales-Navigator firms.

Draws down aug7_salesnav_ranked.json in rank order until --target CALLABLE leads exist.
Callable means a real +91 number: the standing rule is that nothing reaches HubSpot without
one, so a firm whose founder reveals only a US number or an email is a miss, not a lead.

Cost per company: 1 SignalHire SEARCH (founder lookup) + 1 CREDIT only when a profile is
actually revealed. The headcount pre-check from enrich_and_push_it.py is DELIBERATELY SKIPPED
here — that check exists to correct GoodFirms size bands, and this list carries LinkedIn's own
headcount, which is the better number. Skipping it saves one search per company.

Writes after EVERY company. The daily search quota is the usual reason a run like this dies,
and losing 300 reveals to a crash would cost real credits to redo.

Usage: python aug7_salesnav_enrich.py [--target 200] [--limit 500]
"""
import os, re, sys, json, time, collections, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
SH = env["signal_hire"]
RANKED = os.path.join(HERE, "aug7_salesnav_ranked.json")
STATE  = os.path.join(HERE, "aug7_salesnav_enriched.json")

TARGET = 200; LIMIT = 10000
for i, a in enumerate(sys.argv):
    if a == "--target": TARGET = int(sys.argv[i+1])
    if a == "--limit":  LIMIT  = int(sys.argv[i+1])

try: from rapidfuzz import fuzz
except Exception: fuzz = None

FOUNDER_TITLES = ("Founder OR Co-Founder OR Cofounder OR CEO OR Owner OR Managing Director OR "
                  "Director OR Proprietor OR Partner")


def sh_post(path, body, timeout=60):
    req = urllib.request.Request("https://www.signalhire.com/api/v1" + path,
        data=json.dumps(body).encode(), method="POST",
        headers={"apikey": SH, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def credits():
    try:
        req = urllib.request.Request("https://www.signalhire.com/api/v1/credits", headers={"apikey": SH})
        return json.loads(urllib.request.urlopen(req, timeout=20).read().decode()).get("credits")
    except Exception:
        return None


def india_phone(p):
    """+91 mobiles/landlines only. A US number on an Indian firm's founder is still a miss."""
    raw = str(p or "").strip(); d = re.sub(r"[^\d]", "", raw)
    if raw.startswith("+1") or (len(d) == 11 and d.startswith("1")): return ""
    if raw.startswith("+91") or (d.startswith("91") and len(d) == 12):
        d = d[-10:]; return "+91" + d if len(d) == 10 and d[0] in "23456789" else ""
    if len(d) == 10 and d[0] in "23456789": return "+91" + d
    return ""


def find_founder(company):
    """1 search. -> (profile|None, note). Fuzzy-matches the employer so we don't reveal
    someone who merely mentions the company in an old role."""
    try:
        d = sh_post("/candidate/searchByQuery",
                    {"currentCompany": company, "currentTitle": FOUNDER_TITLES, "size": 6})
    except urllib.error.HTTPError as e:
        return None, ("QUOTA" if e.code == 402 else f"http{e.code}")
    except Exception as e:
        return None, type(e).__name__
    cl = company.lower(); best = None; bs = 0
    for p in (d.get("profiles") or []):
        if not isinstance(p, dict): continue
        cs = 0
        for e in (p.get("experience") or []):
            c = str(e.get("company") or "").lower()
            cs = max(cs, fuzz.token_set_ratio(cl, c) if fuzz else (90 if (cl in c or c in cl) else 0))
        if cs >= 82 and cs > bs: bs = cs; best = p
    return best, ("" if best else "no_match")


def reveal(uid):
    """1 credit on success. -> (indian_phone, email, linkedin, note)

    The LinkedIn URL lives on the REVEAL payload at candidate.social[].link — NOT on the
    search profile, and the key is `link`, not `url`. An earlier version of this file read
    `profile.social[].url` and silently produced "" for all 300 rows; 200 deals were pushed
    with no profile link and had to be repaired afterwards by re-revealing on email.
    push_deadpool.py had it right the whole time.
    """
    try:
        d = sh_post("/candidate/search", {"items": [uid], "withoutWaterfall": True})
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
                if "phone" in t: ph.append(v)
                elif "email" in t and "@" in v: em.append(v)
    ind = next((india_phone(x) for x in ph if india_phone(x)), "")
    return ind, next((x for x in em if "@" in x), ""), li, ("" if ph else "no_phone_at_all")


def main():
    pool = json.load(open(RANKED, encoding="utf-8"))
    state = json.load(open(STATE, encoding="utf-8")) if os.path.exists(STATE) else []
    done = {r["company"] for r in state}
    callable_n = sum(1 for r in state if r.get("phone"))
    c0 = credits()
    print(f"pool {len(pool)} | already processed {len(state)} | callable so far {callable_n} "
          f"| credits {c0} | target {TARGET}", flush=True)

    tally = collections.Counter(r["status"] for r in state)
    scanned = 0
    for c in pool:
        if callable_n >= TARGET: print("target reached", flush=True); break
        if scanned >= LIMIT: print("scan limit reached", flush=True); break
        if c["company"] in done: continue
        scanned += 1

        prof, note = find_founder(c["company"])
        if note == "QUOTA":
            print("!! SignalHire SEARCH quota exhausted — stopping cleanly", flush=True); break
        rec = {k: c[k] for k in ("company", "rank", "pri", "headcount", "li_company_url")}
        if not prof:
            rec |= {"status": "no_founder:" + note, "founder": "", "title": "", "phone": "", "email": ""}
        else:
            uid = prof.get("uid") or prof.get("id")
            ind, em, li, pnote = reveal(uid) if uid else ("", "", "", "no_uid")
            if pnote == "QUOTA":
                print("!! SignalHire CREDITS exhausted — stopping cleanly", flush=True); break
            rec |= {"founder": (prof.get("fullName") or prof.get("name") or "").strip(),
                    "title": ((prof.get("experience") or [{}])[0].get("title") or "").strip(),
                    "li": li,
                    "phone": ind, "email": em,
                    "status": "ok" if ind else ("no_indian_phone" if not pnote else pnote)}
        state.append(rec); done.add(c["company"]); tally[rec["status"]] += 1
        if rec.get("phone"): callable_n += 1
        json.dump(state, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        if scanned % 10 == 0 or rec.get("phone"):
            print(f'  [{callable_n:>3}/{TARGET}] scanned {scanned} | rank {rec["rank"]:>4} '
                  f'{rec["company"][:34]:<36}{rec["status"]:<18}{rec.get("phone","")}', flush=True)
        time.sleep(0.25)

    print(f"\nprocessed this run: {scanned} | CALLABLE total: {callable_n}", flush=True)
    print("outcomes:", flush=True)
    for k, v in tally.most_common(): print(f"   {v:>4}  {k}", flush=True)
    print(f"credits: {c0} -> {credits()}", flush=True)
    print(f"state: {os.path.basename(STATE)} ({len(state)} rows)", flush=True)


main()
