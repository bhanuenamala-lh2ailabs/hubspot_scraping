# -*- coding: utf-8 -*-
"""Fill missing emails on the ops-data 500 via SignalHire, for the email campaign.

NO PATTERN GUESSING. We never invent an address from a domain: a guessed address bounces,
and bounce rate on a cold campaign is what gets a sending domain blacklisted. Every address
here is one SignalHire actually holds.

Three resolution routes, best first:
  1. key-people LinkedIn profile URL from Tracxn  -> reveal directly (most reliable)
  2. named key person + company                   -> searchByQuery to find them, then reveal
  3. company only                                 -> searchByQuery for a leader at that company
Route 1 costs a credit. Routes 2/3 also spend the daily SEARCH quota (no credit) to find the
uid first.

Modes:
  --missing   (default) only the companies with NO email at all
  --upgrade   also replace generic info@/contact@ with a named person's address
Resumable; checkpoints after every company. Usage:
  python fill_opsdata_emails.py --max-credits 150
"""
import os, re, sys, json, time, argparse, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(HUB, "exports", "opsdata")
SRC = os.path.join(OUT, "opsdata_net_new_500.json")
CKPT = os.path.join(HERE, "opsdata_email_fill.json")
env = {l.split('=', 1)[0].strip().lower(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
SH = env["signal_hire"]

EM = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
GENERIC = ("info@", "contact@", "support@", "hello@", "sales@", "admin@", "enquiry@",
           "inquiry@", "care@", "help@", "office@", "team@", "mail@", "connect@")
LEADER = re.compile(r"(?i)\b(founder|co[\-\s]?founder|ceo|chief|managing\s+director|owner|"
                    r"proprietor|president|director|head|vp|vice\s+president|partner)\b")
LI = re.compile(r"https?://[^\s,;]*linkedin\.com/in/[^\s,;]+", re.I)


def sh(path, body):
    req = urllib.request.Request("https://www.signalhire.com/api/v1" + path,
        data=json.dumps(body).encode(), method="POST",
        headers={"apikey": SH, "Content-Type": "application/json"})
    for a in range(3):
        try:
            with urllib.request.urlopen(req, timeout=90) as r: return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 402: return {"_quota": True}
            if e.code in (429, 502, 503, 504) and a < 2: time.sleep(4 * (a + 1)); continue
            return {"_err": e.code}
        except Exception:
            if a < 2: time.sleep(3); continue
            return {"_err": "net"}
    return {"_err": "retries"}


def credits():
    try:
        r = urllib.request.Request("https://www.signalhire.com/api/v1/credits", headers={"apikey": SH})
        return json.loads(urllib.request.urlopen(r, timeout=30).read().decode()).get("credits", -1)
    except Exception: return -1


def _flag(d, k):
    """SignalHire returns a LIST on a successful reveal and a DICT on error/quota."""
    return isinstance(d, dict) and d.get(k)


def reveal(ident):
    d = sh("/candidate/search", {"items": [ident], "withoutWaterfall": True})
    if _flag(d, "_quota") or _flag(d, "_err"): return d, [], [], "", ""
    res = d if isinstance(d, list) else d.get("results", [])
    em, ph, name, title = [], [], "", ""
    for it in res or []:
        if not (isinstance(it, dict) and it.get("status") == "success"): continue
        c = it.get("candidate") or {}
        name = name or c.get("fullName") or ""
        exp = c.get("experience") or []
        if exp and not title: title = (exp[0].get("title") or "")
        for x in c.get("contacts") or []:
            t = str(x.get("type", "")).lower(); v = x.get("value")
            if not isinstance(v, str): continue
            if "email" in t and "@" in v: em.append(v)
            elif "phone" in t: ph.append(v)
    return d, em, ph, name, title


def find_uid(person, company):
    q = {"size": 8}
    if person: q["fullName"] = person
    if company: q["currentPastCompany"] = company
    d = sh("/candidate/searchByQuery", q)
    if not isinstance(d, dict) or d.get("_quota") or d.get("_err"): return None, d
    best = None
    for p in d.get("profiles", []) or []:
        exp = p.get("experience", []) or []
        titles = " ".join((e.get("title") or "") for e in exp[:3])
        if person or LEADER.search(titles):
            best = p; break
    return (best or {}).get("uid"), d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-credits", type=int, default=200)
    ap.add_argument("--upgrade", action="store_true")
    ap.add_argument("--limit", type=int, default=10**9)
    a = ap.parse_args()

    rows = json.load(open(SRC, encoding="utf-8"))
    done = json.load(open(CKPT, encoding="utf-8")) if os.path.exists(CKPT) else {}

    def person_emails(r):
        return [e for e in EM.findall(r.get("key_people_emails") or "")
                if not any(e.lower().startswith(g) for g in GENERIC)]

    todo = []
    for r in rows:
        if r["company"] in done: continue
        has_any = bool(EM.findall(r.get("key_people_emails") or "") or
                       EM.findall(r.get("company_emails") or ""))
        if not has_any: todo.append(("missing", r))
        elif a.upgrade and not person_emails(r): todo.append(("upgrade", r))
    todo = todo[:a.limit]

    c0 = credits()
    print(f"SignalHire credits: {c0} | ceiling this run: {a.max_credits}")
    print(f"companies to work: {len(todo)} "
          f"({sum(1 for m,_ in todo if m=='missing')} missing, "
          f"{sum(1 for m,_ in todo if m=='upgrade')} upgrade)\n")

    quota = False
    for i, (mode, r) in enumerate(todo, 1):
        if c0 - credits() >= a.max_credits:
            print(f"  !! credit ceiling {a.max_credits} reached — stopping"); break
        rec = {"mode": mode, "route": "", "emails": [], "phones": [], "person": "", "title": ""}

        prof = LI.findall(r.get("key_people_profiles") or "")
        if prof:
            d, em, ph, nm, ti = reveal(prof[0])
            if _flag(d, "_quota"): quota = True; break
            rec.update(route="linkedin_profile", emails=em, phones=ph, person=nm, title=ti)

        if not rec["emails"]:
            names = [n.strip() for n in re.split(r"[,;|]", (r.get("key_people") or ""))
                     if len(n.strip()) > 4][:1]
            uid, d = find_uid(names[0] if names else "", r["company"])
            if _flag(d, "_quota"): quota = True; break
            if uid:
                d2, em, ph, nm, ti = reveal(uid)
                if _flag(d2, "_quota"): quota = True; break
                rec.update(route="search_" + ("name" if names else "company"),
                           emails=em, phones=ph, person=nm, title=ti)

        rec["emails"] = [e for e in dict.fromkeys(rec["emails"]) if "@" in e]
        done[r["company"]] = rec
        json.dump(done, open(CKPT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        flag = "OK " if rec["emails"] else " - "
        print(f"[{i:>3}/{len(todo)}] {flag} {r['company'][:26]:28} {rec['route'] or 'no route':18} "
              f"{(rec['person'] or '')[:20]:22} {(rec['emails'][0] if rec['emails'] else '')}", flush=True)
        time.sleep(0.6)

    if quota: print("\n!! SignalHire quota hit — rerun later, it resumes.")
    got = sum(1 for v in done.values() if v["emails"])
    print(f"\nworked {len(done)} companies | emails found for {got} | credits {c0} -> {credits()}")

    # merge back into the deliverable
    add = 0
    for r in rows:
        v = done.get(r["company"])
        if v and v["emails"]:
            r["enriched_email"] = v["emails"][0]
            r["enriched_email_all"] = "; ".join(v["emails"])
            r["enriched_person"] = v["person"]; r["enriched_title"] = v["title"]
            r["enriched_phone"] = "; ".join(v["phones"][:2]); r["email_source"] = "SignalHire"
            add += 1
    json.dump(rows, open(SRC, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"merged {add} enriched emails back into {SRC}")


if __name__ == "__main__":
    main()
