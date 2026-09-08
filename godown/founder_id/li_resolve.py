# -*- coding: utf-8 -*-
"""name+company -> linkedin.com/in URL, via server-side search APIs. Implements
SOLVE_LINKEDIN_URL.md: Exa (primary) -> Jina -> Serper -> PDL cascade, all running on the
vendor's IPs so this host's engine wall never applies. DDG is intentionally omitted — it is
the walled surface the whole doc exists to escape.

INPUT is the resolver's own state: every status='name_only' row already carries the MCA-cited
founder name + company + website + city. A verified URL flips the row to status='full', which
is exactly what enrich_push.py consumes — so this feeds the existing reveal->+91-gate->push
chain with no glue. Nothing here spends a SignalHire credit.

VERIFICATION (never fetch LinkedIn, never trust model memory):
  regex ^https?://([a-z]{2,3}\\.)?linkedin\\.com/in/[^/?#]+/?$
  + the /in/ slug shares a name token with the person
  + the result co-mentions the company OR the city (checked across ALL string fields the API
    returned, so it is robust to each vendor's schema)
Confidence HIGH (company match) / MED (city or title only). LOW is dropped, not revealed.

KEYS: read from .env (lowercased), any subset. With only exa_api_key present, Stage A runs
alone. Absent keys skip their stage cleanly. Hard per-source caps stop before any paid spend.

Usage: python3 li_resolve.py [--limit N] [--apply-to-state]   (default writes CSV only;
       --apply-to-state also flips resolved rows to 'full' so enrich_push picks them up)
"""
import os, re, sys, csv, json, time, sqlite3, urllib.request, urllib.error, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
DBP = os.path.join(HERE, "resolver.sqlite")
OUT = os.path.join(HERE, "linkedin_resolved.csv")
QUOTA = os.path.join(HERE, "li_quota.json")
env = {l.split('=', 1)[0].strip().lower(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
EXA = env.get("exa_api_key", ""); JINA = env.get("jina_api_key", "")
SERPER = env.get("serper_api_key", ""); PDL = env.get("pdl_api_key", "")

LIMIT = 0; APPLY = "--apply-to-state" in sys.argv
for i, a in enumerate(sys.argv):
    if a == "--limit": LIMIT = int(sys.argv[i + 1])

LI_RX = re.compile(r"^https?://([a-z]{2,3}\.)?linkedin\.com/in/[^/?#]+/?$")
LI_FIND = re.compile(r"https?://([a-z]{2,3}\.)?linkedin\.com/in/[^\s\"'<>?#]+")
BAD = ("/company/", "/school/", "/jobs/", "/posts/", "/pulse/")
CAPS = {"exa_usd": 30.0, "jina_calls": 1000, "serper_calls": 2500, "pdl_calls": 100}
COST_EXA = 0.007


def load_quota():
    q = json.load(open(QUOTA)) if os.path.exists(QUOTA) else {}
    return {**{"exa_usd": 0.0, "jina_calls": 0, "serper_calls": 0, "pdl_calls": 0}, **q}


def save_quota(q): json.dump(q, open(QUOTA, "w"), indent=1)


def post(url, headers, body, timeout=30):
    try:
        r = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                   headers={**headers, "Content-Type": "application/json"})
        with urllib.request.urlopen(r, timeout=timeout) as x:
            return json.loads(x.read().decode()), 200
    except urllib.error.HTTPError as e:
        return {"raw": e.read().decode()[:200]}, e.code
    except Exception as e:
        return {"err": type(e).__name__}, 0


def get(url, headers, timeout=30):
    try:
        r = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(r, timeout=timeout) as x:
            return json.loads(x.read().decode()), 200
    except urllib.error.HTTPError as e:
        return {"raw": e.read().decode()[:200]}, e.code
    except Exception as e:
        return {"err": type(e).__name__}, 0


def all_strings(obj):
    """Every string value anywhere in a nested dict/list — the co-mention haystack."""
    out = []
    if isinstance(obj, str): out.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values(): out += all_strings(v)
    elif isinstance(obj, list):
        for v in obj: out += all_strings(v)
    return out


def tokens(s):
    return {t for t in re.sub(r"[^a-z0-9 ]", " ", (s or "").lower()).split() if len(t) > 2}


GENERIC = {"pvt", "private", "limited", "ltd", "llp", "technologies", "technology", "tech",
           "solutions", "software", "softwares", "systems", "services", "infotech", "india",
           "labs", "global", "consulting", "digital", "inc", "the", "and"}


def verify(url, person, company, city, haystack):
    if not LI_RX.match(url) or any(b in url for b in BAD): return None
    slug = url.rstrip("/").rsplit("/in/", 1)[-1].lower()
    ptok = tokens(person)
    if not (ptok & set(re.split(r"[^a-z0-9]+", slug))): return None      # slug names a different person
    hay = " ".join(haystack).lower()
    ctok = tokens(company) - GENERIC
    comp_hit = any(t in hay for t in ctok) if ctok else False
    city_hit = bool(city) and city.lower().split(",")[0].strip() in hay
    if comp_hit: return "HIGH"
    if city_hit: return "MED"
    return None


def exa(person, company, city, q):
    body = {"query": f"{person}, {company}, {city}, India", "category": "people",
            "type": "auto", "numResults": 5, "includeDomains": ["linkedin.com"]}
    d, code = post("https://api.exa.ai/search", {"Authorization": "Bearer " + EXA}, body)
    q["exa_usd"] = round(q["exa_usd"] + COST_EXA, 4)
    if code != 200: return None, f"exa http{code}", []
    for r in d.get("results", []):
        u = (r.get("url") or "").split("?")[0].rstrip("/")
        conf = verify(u, person, company, city, all_strings(r))
        if conf: return u, conf, all_strings(r)[:1]
    return None, "exa no-match", []


def jina(person, company, city, q):
    query = f'"{person}" "{company}" site:linkedin.com/in'
    d, code = get("https://s.jina.ai/" + urllib.parse.quote(query),
                  {"Authorization": "Bearer " + JINA, "Accept": "application/json", "X-Site": "linkedin.com"})
    q["jina_calls"] += 1
    if code != 200: return None, f"jina http{code}", []
    for r in (d.get("data") or d.get("results") or []):
        u = (r.get("url") or "").split("?")[0].rstrip("/")
        conf = verify(u, person, company, city, all_strings(r))
        if conf: return u, conf, [r.get("content", "")[:120]]
    return None, "jina no-match", []


def serper(person, company, city, q):
    body = {"q": f'"{person}" "{company}" site:linkedin.com/in', "gl": "in", "num": 10}
    d, code = post("https://google.serper.dev/search", {"X-API-KEY": SERPER}, body)
    q["serper_calls"] += 1
    if code != 200: return None, f"serper http{code}", []
    for r in d.get("organic", []):
        u = (r.get("link") or "").split("?")[0].rstrip("/")
        conf = verify(u, person, company, city, [r.get("title", ""), r.get("snippet", ""), u])
        if conf: return u, conf, [r.get("snippet", "")[:120]]
    return None, "serper no-match", []


def pdl(person, company, city, q):
    p = urllib.parse.urlencode({"name": person, "company": company, "locality": city, "min_likelihood": 6})
    d, code = get("https://api.peopledatalabs.com/v5/person/enrich?" + p, {"X-Api-Key": PDL})
    q["pdl_calls"] += 1
    if code != 200: return None, f"pdl http{code}", []
    u = ((d.get("data") or {}).get("linkedin_url") or "")
    if u and not u.startswith("http"): u = "https://" + u
    u = u.split("?")[0].rstrip("/")
    conf = verify(u, person, company, city, all_strings(d.get("data") or {}))
    if conf: return u, conf, ["pdl structured match"]
    return None, "pdl no-match", []


def main():
    if not any([EXA, JINA, SERPER, PDL]):
        sys.exit("No API keys in .env. Add at least exa_api_key (see SOLVE_LINKEDIN_URL.md §1).")
    stages = [("exa", exa, EXA, "exa_usd", CAPS["exa_usd"]),
              ("jina", jina, JINA, "jina_calls", CAPS["jina_calls"]),
              ("serper", serper, SERPER, "serper_calls", CAPS["serper_calls"]),
              ("pdl", pdl, PDL, "pdl_calls", CAPS["pdl_calls"])]
    active = [s for s in stages if s[2]]
    print("active stages:", [s[0] for s in active] or "NONE", flush=True)

    con = sqlite3.connect(DBP)
    rows = [(dom, json.loads(data)) for dom, data in
            con.execute("SELECT domain, data FROM companies WHERE status='name_only'")]
    rows = [(d, r) for d, r in rows if not r.get("li_checked_api")]
    if LIMIT: rows = rows[:LIMIT]
    q = load_quota()
    print(f"{len(rows)} names to resolve | quota so far {q}", flush=True)

    results, found = [], 0
    for i, (dom, r) in enumerate(rows, 1):
        person, company, city = r["founder_name"], r["company"], r.get("city", "")
        url = conf = src = ""; note = "no-match"; snip = []
        for name, fn, key, ctr, cap in active:
            if q[ctr] >= cap: continue
            u, n, sn = fn(person, company, city, q)
            note = n
            if u: url, conf, src, snip = u, n if n in ("HIGH", "MED") else conf, name, sn; break
            time.sleep(1.2)
        save_quota(q)
        rec = {"name": person, "company": company, "domain": dom, "city": city,
               "linkedin_url": url, "url_source": src, "confidence": conf,
               "url_snippet": (snip or [""])[0], "note": note}
        results.append(rec)
        if url:
            found += 1
            r["linkedin_url"] = url; r["li_source"] = src; r["li_confidence"] = conf
            r["li_checked_api"] = True
            new_status = "full" if (APPLY and conf in ("HIGH", "MED")) else "name_only"
            con.execute("UPDATE companies SET status=?, data=? WHERE domain=?",
                        (new_status, json.dumps(r), dom))
        else:
            r["li_checked_api"] = True
            con.execute("UPDATE companies SET data=? WHERE domain=?", (json.dumps(r), dom))
        con.commit()
        print(f'[{i}/{len(rows)}] {company[:26]:<28}{person[:20]:<22}'
              f'{(url or note)[:44]:<46}{conf}', flush=True)
        if q["exa_usd"] >= CAPS["exa_usd"]:
            print("exa budget cap reached — stopping"); break

    exists = os.path.exists(OUT)
    with open(OUT, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        if not exists: w.writeheader()
        w.writerows(results)
    hi = sum(1 for r in results if r["confidence"] == "HIGH")
    md = sum(1 for r in results if r["confidence"] == "MED")
    print(f"\nresolved {found}/{len(rows)} ({hi} HIGH, {md} MED) | quota {q}")
    print(f"{'FLIPPED to full for enrich_push' if APPLY else 'CSV only — rerun with --apply-to-state to feed reveals'}")


main()
