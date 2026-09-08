# -*- coding: utf-8 -*-
"""Resolve real people behind the deadpool-wave companies via SignalHire searchByQuery.

Two passes, because the two problems are different:

  PASS 1 — named founders (the 91 people the research already names).
     Query `fullName` + `currentPastCompany` together. That pair is decisive:
     "Navneet Singh" alone is hopeless, but +PepperTap returns exactly 1 profile whose
     experience reads "PepperTap — Founder & CEO". A company-only search does NOT work —
     SignalHire returns ex-employees in arbitrary order and the founder sits past the
     page limit (TaxiForSure: 75 profiles, founder not in the first 50).
     No location filter on this query: Manu Rana (Baxi) is in Dubai and an India filter
     hides him. Geography is settled later by the +91 phone gate, not here.
     If the pair returns nothing, fall back to `fullName` + India and accept only a
     globally unique exact name (unique_name) — weaker, flagged, never auto-pushed.
     A namesake is worse than no lead, so anything below that is dropped.

  PASS 2 — "various" companies (the 25 rows with no named person).
     Search by `currentPastCompany` and keep profiles holding a founder-level title
     AT that company. This is the only way to name those founders at all.

No credits are spent here — searchByQuery consumes the daily SEARCH quota only.
Resumable: checkpoints after every lookup. Usage:
  python resolve_deadpool_founders.py [--limit N] [--pass2-only]
"""
import os, re, sys, json, time, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(HUB, "crm_mirror", "sources", "deadpool_waves")
CKPT = os.path.join(HERE, "deadpool_resolved.json")
env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
SH = env["signal_hire"]

try:
    from rapidfuzz import fuzz
except Exception:
    fuzz = None

FOUNDER_TITLE = re.compile(
    r"(?i)\b(co[\-\s]?founder|founder|founding\s+(team|member|partner)|chief\s+executive|"
    r"\bceo\b|\bcoo\b|chief\s+operating|managing\s+director|owner|proprietor|chairman|"
    r"chief\s+technology|\bcto\b|chief\s+product|\bcpo\b|vp\s+engineering|head\s+of\s+engineering)")

def norm(s): return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", (s or "").lower())).strip()

def company_tokens(c):
    """'Zigy.com (PM Health & Life Care)' -> ['zigy']; 'Roadrunnr/Runnr' -> ['roadrunnr','runnr']"""
    c = re.sub(r"\s*\([^)]*\)", "", c)
    out = []
    for p in re.split(r"[/]", c):
        p = norm(p.replace(".com", ""))
        p = re.sub(r"\b(technologies|technology|india|pvt|ltd|private|limited|labs|inc)\b", "", p).strip()
        if len(p) >= 3: out.append(p)
    return out or [norm(c)]

def name_match(a, b):
    a, b = norm(a), norm(b)
    if not a or not b: return 0
    if a == b: return 100
    if fuzz: return max(fuzz.token_sort_ratio(a, b), fuzz.partial_ratio(a, b))
    at, bt = set(a.split()), set(b.split())
    return int(100 * len(at & bt) / max(1, len(at | bt)))

def sq(body):
    req = urllib.request.Request("https://www.signalhire.com/api/v1/candidate/searchByQuery",
        data=json.dumps(body).encode(), method="POST",
        headers={"apikey": SH, "Content-Type": "application/json"})
    for a in range(3):
        try:
            with urllib.request.urlopen(req, timeout=90) as r: return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 402: return {"_quota": True}
            if e.code in (429, 502, 503, 504) and a < 2: time.sleep(4*(a+1)); continue
            return {"_err": e.code}
        except Exception:
            if a < 2: time.sleep(3); continue
            return {"_err": "net"}
    return {"_err": "retries"}

def main():
    limit = int(sys.argv[sys.argv.index("--limit")+1]) if "--limit" in sys.argv else 10**9
    p2only = "--pass2-only" in sys.argv
    q = json.load(open(os.path.join(SRC, "deadpool_queue.json"), encoding="utf-8"))
    st = json.load(open(CKPT, encoding="utf-8")) if os.path.exists(CKPT) else {"people": {}, "companies": {}}
    if "people" not in st: st = {"people": {}, "companies": {}}   # drop the old company-first shape
    quota = False; used = 0

    # ---------------- PASS 1: named founders ----------------
    if not p2only:
        todo = [p for p in q["people"] if f"{p['name']}|{p['company']}" not in st["people"]]
        print(f"PASS 1 — named founders: {len(q['people'])} total, {len(todo)} to look up\n")
        for i, p in enumerate(todo, 1):
            if used >= limit: break
            key = f"{p['name']}|{p['company']}"
            toks = company_tokens(p["company"])

            def cands_from(d):
                out = []
                for pr in d.get("profiles", []) or []:
                    sc = name_match(pr.get("fullName"), p["name"])
                    if sc < 88: continue
                    exp = pr.get("experience", []) or []
                    at_co = [e for e in exp if any(t in norm(e.get("company")) for t in toks)]
                    out.append({"uid": pr.get("uid"), "full_name": pr.get("fullName"),
                                "location": pr.get("location"), "score": sc, "at_company": bool(at_co),
                                "title_at_company": " / ".join(sorted({(e.get("title") or "") for e in at_co if e.get("title")})),
                                "current": ((exp[0].get("title") or "") + " @ " + (exp[0].get("company") or "")) if exp else ""})
                return out

            # decisive query: the person AND the dead company, no geography filter
            d = sq({"fullName": p["name"], "currentPastCompany": p["company"], "size": 10}); used += 1
            if d.get("_quota"): quota = True; break
            cands = cands_from(d)
            verified = [c for c in cands if c["at_company"]] or cands
            if verified and d.get("total", 0) >= 1:
                best = max(verified, key=lambda c: (c["at_company"], c["score"])); how = "verified_company"
            else:
                d2 = sq({"fullName": p["name"], "location": "India", "size": 10}); used += 1
                if d2.get("_quota"): quota = True; break
                c2 = cands_from(d2)
                hit_co = [c for c in c2 if c["at_company"]]
                if hit_co:
                    best = max(hit_co, key=lambda c: c["score"]); how = "verified_company"
                elif len(c2) == 1 and c2[0]["score"] >= 97:
                    best = c2[0]; how = "unique_name"
                else:
                    best = None; how = "ambiguous" if c2 else "not_found"
            st["people"][key] = {**p, "verify": how, "n_profiles": d.get("total", 0),
                                 "hit": best, "alts": len(cands)}
            json.dump(st, open(CKPT, "w", encoding="utf-8"), indent=1)
            flag = {"verified_company": "OK ", "unique_name": "ok?", "ambiguous": " ~ ", "not_found": " - "}[how]
            print(f"[{i:>3}/{len(todo)}] {flag} {p['name'][:26]:28} {p['display_company'][:24]:26} "
                  f"{(best or {}).get('current','')[:44]}")
            time.sleep(1.0)

    # ---------------- PASS 2: companies with no named founder ----------------
    if not quota:
        hold = [c for c in q["companies"] if c["gate"] == "HOLD" and c["company"] not in st["companies"]]
        print(f"\nPASS 2 — unnamed-founder companies: {len(hold)} to look up\n")
        for i, c in enumerate(hold, 1):
            if used >= limit: break
            toks = company_tokens(c["company"])
            d = sq({"currentPastCompany": c["company"], "location": "India", "size": 50}); used += 1
            if d.get("_quota"): quota = True; break
            hits = []
            for pr in d.get("profiles", []) or []:
                exp = pr.get("experience", []) or []
                at_co = [e for e in exp if any(t in norm(e.get("company")) for t in toks)]
                if not at_co: continue
                titles = " / ".join(sorted({(e.get("title") or "") for e in at_co if e.get("title")}))
                if not FOUNDER_TITLE.search(titles): continue
                hits.append({"uid": pr.get("uid"), "full_name": pr.get("fullName"),
                             "location": pr.get("location"), "title_at_company": titles,
                             "current": ((exp[0].get("title") or "") + " @ " + (exp[0].get("company") or "")) if exp else ""})
            st["companies"][c["company"]] = {"display": c["display"], "wave": c["waves"][0].split(" (")[0],
                                             "status": c["status"], "shutdown": c["shutdown"],
                                             "funding_raised": c["funding_raised"], "source": c["source"],
                                             "total": d.get("total", 0), "hits": hits}
            json.dump(st, open(CKPT, "w", encoding="utf-8"), indent=1)
            print(f"[{i:>2}/{len(hold)}] {c['display'][:30]:32} pool={d.get('total',0):>4} founders={len(hits)}")
            time.sleep(1.0)

    if quota: print("\n!! SignalHire daily SEARCH quota exhausted — rerun to continue (resumable).")
    v = {}
    for r in st["people"].values(): v[r["verify"]] = v.get(r["verify"], 0) + 1
    print(f"\nPASS1 {len(st['people'])}/{len(q['people'])} people: " +
          " ".join(f"{k}={n}" for k, n in sorted(v.items())))
    print(f"PASS2 {len(st['companies'])} companies, {sum(len(c['hits']) for c in st['companies'].values())} founders found")
    print(f"searches used this run: {used}\n-> {CKPT}")

if __name__ == "__main__":
    main()
