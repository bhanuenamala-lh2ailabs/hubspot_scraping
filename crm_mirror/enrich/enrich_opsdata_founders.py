# -*- coding: utf-8 -*-
"""Get a real personal email for every ops-data founder we can, then drop the unusable.

Works the list produced by build_opsdata_founder_list.py. Targets any row without a
*personal* founder email — an info@ is technically deliverable but converts badly, and a
row with no address at all is dead weight in a campaign.

Routes, cheapest and most reliable first:
  1. the founder's own LinkedIn URL from Tracxn  -> reveal (credit only, no search quota)
  2. founder name + company                      -> searchByQuery, then reveal
  3. company only                                -> searchByQuery for a leader, then reveal

Still never guesses an address from a domain.

Usage: python enrich_opsdata_founders.py [--max-credits 200] [--limit N]
"""
import os, re, sys, json, time, argparse, collections, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(HUB, "exports", "opsdata")
SRC = os.path.join(OUT, "opsdata_founders.json")
CKPT = os.path.join(HERE, "opsdata_founder_enrich.json")
env = {l.split('=', 1)[0].strip().lower(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
SH = env["signal_hire"]

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
GENERIC = ("info@", "contact@", "support@", "hello@", "sales@", "admin@", "enquiry@",
           "inquiry@", "care@", "help@", "office@", "team@", "mail@", "connect@",
           "careers@", "hr@", "wecare@", "reachus@")
LI = re.compile(r"https?://[^\s,;|]*linkedin\.com/in/[^\s,;|]+", re.I)
LEADER = re.compile(r"(?i)\b(founder|co[- ]?founder|ceo|chief|managing\s+director|owner|"
                    r"proprietor|president|director|partner)\b")


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


def flag(d, k): return isinstance(d, dict) and d.get(k)


def credits():
    try:
        r = urllib.request.Request("https://www.signalhire.com/api/v1/credits",
                                   headers={"apikey": SH})
        return json.loads(urllib.request.urlopen(r, timeout=30).read().decode()).get("credits", -1)
    except Exception: return -1


def reveal(ident):
    d = sh("/candidate/search", {"items": [ident], "withoutWaterfall": True})
    if flag(d, "_quota") or flag(d, "_err"): return d, [], "", ""
    res = d if isinstance(d, list) else d.get("results", [])
    em, name, title = [], "", ""
    for it in res or []:
        if not (isinstance(it, dict) and it.get("status") == "success"): continue
        c = it.get("candidate") or {}
        name = name or c.get("fullName") or ""
        exp = c.get("experience") or []
        if exp and not title: title = exp[0].get("title") or ""
        for x in c.get("contacts") or []:
            if "email" in str(x.get("type", "")).lower() and isinstance(x.get("value"), str) \
                    and "@" in x["value"]:
                em.append(x["value"])
    return d, em, name, title


def find_uid(person, company):
    q = {"size": 8}
    if person: q["fullName"] = person
    if company: q["currentPastCompany"] = company
    d = sh("/candidate/searchByQuery", q)
    if not isinstance(d, dict) or d.get("_quota") or d.get("_err"): return None, d
    for p in d.get("profiles", []) or []:
        exp = p.get("experience", []) or []
        titles = " ".join((e.get("title") or "") for e in exp[:3])
        if person or LEADER.search(titles):
            return p.get("uid"), d
    return None, d


def personal(emails):
    for e in emails:
        if not any(e.lower().startswith(g) for g in GENERIC): return e
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-credits", type=int, default=250)
    ap.add_argument("--limit", type=int, default=10**9)
    a = ap.parse_args()

    rows = json.load(open(SRC, encoding="utf-8"))
    done = json.load(open(CKPT, encoding="utf-8")) if os.path.exists(CKPT) else {}
    todo = [r for r in rows if not r["founder_email"] and r["company"] not in done][:a.limit]

    c0 = credits()
    print(f"credits {c0} | ceiling {a.max_credits}")
    print(f"rows lacking a personal founder email: "
          f"{sum(1 for r in rows if not r['founder_email'])} | to work now: {len(todo)}\n")

    quota = False
    for i, r in enumerate(todo, 1):
        if c0 - credits() >= a.max_credits:
            print(f"  !! credit ceiling reached"); break
        rec = {"route": "", "email": "", "person": "", "title": ""}

        prof = LI.findall(r.get("key_people_profiles") or "")
        if prof:
            d, em, nm, ti = reveal(prof[0])
            if flag(d, "_quota"): quota = True; break
            p = personal(em)
            if p: rec = {"route": "linkedin", "email": p, "person": nm or r["founder_name"],
                         "title": ti or r["founder_title"]}

        if not rec["email"] and r["founder_name"]:
            uid, d = find_uid(r["founder_name"], r["company"])
            if flag(d, "_quota"): quota = True; break
            if uid:
                d2, em, nm, ti = reveal(uid)
                if flag(d2, "_quota"): quota = True; break
                p = personal(em)
                if p: rec = {"route": "name+company", "email": p, "person": nm, "title": ti}

        if not rec["email"]:
            uid, d = find_uid("", r["company"])
            if flag(d, "_quota"): quota = True; break
            if uid:
                d2, em, nm, ti = reveal(uid)
                if flag(d2, "_quota"): quota = True; break
                p = personal(em)
                if p: rec = {"route": "company", "email": p, "person": nm, "title": ti}

        done[r["company"]] = rec
        json.dump(done, open(CKPT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        mark = "OK " if rec["email"] else " - "
        print(f"[{i:>3}/{len(todo)}] {mark} {r['company'][:24]:26} {rec['route'] or '-':14} "
              f"{(rec['person'] or '')[:20]:22} {rec['email'][:34]}", flush=True)
        time.sleep(0.5)

    if quota: print("\n!! SignalHire quota hit — rerun to continue (resumable)")

    # merge + decide who survives
    kept, dropped = [], []
    for r in rows:
        v = done.get(r["company"]) or {}
        if v.get("email"):
            r["founder_email"] = v["email"]
            r["founder_name"] = r["founder_name"] or v.get("person") or ""
            r["founder_title"] = r["founder_title"] or v.get("title") or ""
            r["email_source"] = f"SignalHire ({v['route']})"
        r["campaign_email"] = r["founder_email"] or r["company_email"]
        r["campaign_email_type"] = ("founder" if r["founder_email"]
                                    else "company generic" if r["company_email"] else "")
        (kept if r["campaign_email"] else dropped).append(r)

    json.dump(rows, open(SRC, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(dropped, open(os.path.join(OUT, "opsdata_dropped_no_email.json"), "w",
                            encoding="utf-8"), ensure_ascii=False, indent=1)

    import csv
    cols = ["company", "founder_name", "founder_title", "campaign_email",
            "campaign_email_type", "email_source", "other_people", "employees", "founded",
            "age_years", "city", "state", "sector", "stage", "revenue_usd", "funding_usd",
            "distress", "engage_score", "domain", "linkedin", "website", "tracxn_url"]
    p = os.path.join(OUT, "LH2_OpsData_Founders_CampaignReady.csv")
    with open(p, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in sorted(kept, key=lambda x: (x["campaign_email_type"] != "founder",
                                             -x["engage_score"])):
            w.writerow(r)

    st = collections.Counter(r["campaign_email_type"] for r in kept)
    print(f"\ncredits {c0} -> {credits()}")
    print(f"\nCAMPAIGN-READY: {len(kept)}")
    for k, v in st.most_common(): print(f"   {v:>4}  {k} email")
    print(f"DROPPED (no usable email): {len(dropped)}")
    for r in dropped[:12]:
        print(f"   {r['company'][:28]:30} founder={r['founder_name'][:20] or '(none)'}")
    print(f"\n-> {p}")


if __name__ == "__main__":
    main()
