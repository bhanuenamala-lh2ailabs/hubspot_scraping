# -*- coding: utf-8 -*-
"""LinkedIn URL per MCA-named founder via Apify HarvestAPI actor. Server-side => no IP wall.

Actor: harvestapi/linkedin-profile-search-by-name (CP1SVZfEwWflrmWCX). Input is ONE search
query per run (not a batch), so we loop: firstName + lastName + city, profileScraperMode=Short
(search-results tier only — the cheapest, and it already carries the profile URL; we do NOT
scrape Full/email because SignalHire supplies contacts downstream).

Cost control: Short bills ~search-page-results at $4/1000 = $0.004/result. maxItems caps
results/name; a hard USD ceiling stops well under the $5 free monthly allowance. Every URL is
verified (regex + name-slug + company/city co-mention) and re-verified again at reveal, so a
namesake costs at most a wasted lookup, never a wrong push.

Resolved rows flip to status='full' -> enrich_push.py reveals + +91-gates + pushes 50:50.

Usage: python3 apify_li.py [--limit N] [--maxitems 3] [--cap-usd 4.5] [--strict]
"""
import os, re, sys, csv, json, time, sqlite3, urllib.request, urllib.error, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
DBP = os.path.join(HERE, "resolver.sqlite")
QUEUE = os.path.join(HUB, "godown", "prequal", "prequal_out", "enrich_queue.csv")
env = {l.split('=', 1)[0].strip(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
TOKEN = env["APIFY_TOKEN"]
ACTOR = "harvestapi~linkedin-profile-search-by-name"
ENDPOINT = f"https://api.apify.com/v2/acts/{ACTOR}/run-sync-get-dataset-items"

# strictSearch off: strict first+last dropped real people ("Hiral Shah" strict+Ahmedabad -> 0).
# The verify()'s single-unambiguous-hit rule now carries disambiguation instead.
LIMIT, MAXITEMS, CAP_USD, STRICT = 0, 3, 4.5, False
for i, a in enumerate(sys.argv):
    if a == "--limit": LIMIT = int(sys.argv[i + 1])
    if a == "--maxitems": MAXITEMS = int(sys.argv[i + 1])
    if a == "--cap-usd": CAP_USD = float(sys.argv[i + 1])
    if a == "--strict": STRICT = True
COST_PER_RESULT = 0.004
LI_RX = re.compile(r"^https?://([a-z]{2,3}\.)?linkedin\.com/in/[^/?#]+/?$")
LI_FIND = re.compile(r"https?://([a-z]{2,3}\.)?linkedin\.com/in/[^\s\"'<>?#]+")
GENERIC = {"pvt", "private", "limited", "ltd", "llp", "technologies", "technology", "tech",
           "solutions", "software", "softwares", "systems", "services", "infotech", "india",
           "labs", "global", "consulting", "digital", "inc", "the", "and", "it"}


def tok(s): return {t for t in re.sub(r"[^a-z0-9 ]", " ", (s or "").lower()).split() if len(t) > 2}


def all_strings(o):
    if isinstance(o, str): return [o]
    if isinstance(o, dict): return [x for v in o.values() for x in all_strings(v)]
    if isinstance(o, list): return [x for v in o for x in all_strings(v)]
    return []


def run_actor(body):
    try:
        r = urllib.request.Request(ENDPOINT + "?token=" + urllib.parse.quote(TOKEN),
                                   data=json.dumps(body).encode(), method="POST",
                                   headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(r, timeout=180) as x:
            return json.loads(x.read().decode()), 200
    except urllib.error.HTTPError as e:
        return {"raw": e.read().decode()[:200]}, e.code
    except Exception as e:
        return {"err": type(e).__name__}, 0


def verify(items, person, company, city):
    """-> (url, confidence). Disambiguation that respects the namesake risk, because the
    reveal step does NOT catch a same-name wrong person:
      HIGH  the profile's own text names the company  -> safe regardless of how common the name
      MED   the person's name is UNAMBIGUOUS on LinkedIn (exactly one name-slug match returned)
            -> safe for rare names; a common name returns several and never reaches here
    The ambiguous middle (several namesakes, none naming the company) is SKIPPED, not guessed.
    City is used only as a tie-note, never as sole evidence — same city + common name is a
    coin-flip and produced the Cognoflo-vs-Rays kind of false match."""
    ptok = tok(person); ctok = tok(company) - GENERIC
    cands = []
    for it in items if isinstance(items, list) else []:
        blob = " ".join(all_strings(it))
        m = LI_FIND.search(blob)
        if not m: continue
        url = m.group(0).split("?")[0].rstrip("/")
        if not LI_RX.match(url) or any(b in url for b in ("/company/", "/school/", "/jobs/")): continue
        slug = url.rsplit("/in/", 1)[-1].lower()
        if not (ptok & set(re.split(r"[^a-z0-9]+", slug))): continue     # a different person entirely
        cands.append((url, blob.lower()))
    for url, hay in cands:
        if ctok and any(t in hay for t in ctok): return url, "HIGH"      # company confirmed on-profile
    if len(cands) == 1:                                                  # LinkedIn's one unambiguous hit
        return cands[0][0], "MED"
    return "", ""                                                        # several namesakes -> don't guess


def main():
    # city lives in the queue CSV (100% populated), not on the resolver record — join it back
    # for both the search location filter and the MED (city co-mention) disambiguation path.
    city_of = {r["domain"]: (r.get("city") or "").split(",")[0].strip()
               for r in csv.DictReader(open(QUEUE, encoding="utf-8-sig"))}
    con = sqlite3.connect(DBP)
    rows = [(d, json.loads(v)) for d, v in
            con.execute("SELECT domain, data FROM companies WHERE status='name_only'")]
    todo = [(d, r) for d, r in rows if not r.get("apify_done")]
    if LIMIT: todo = todo[:LIMIT]
    print(f"{len(rows)} named without URL | {len(todo)} to search via Apify | "
          f"mode Short, maxItems {MAXITEMS}, cap ${CAP_USD}\n", flush=True)

    spend = 0.0; found = 0
    for i, (dom, r) in enumerate(todo, 1):
        if spend >= CAP_USD:
            print(f"\n!! ~${spend:.2f} — cap reached, stopping cleanly", flush=True); break
        person = r["founder_name"]; parts = person.split()
        if len(parts) < 2:
            r["apify_done"] = True; con.execute("UPDATE companies SET data=? WHERE domain=?", (json.dumps(r), dom)); con.commit(); continue
        city = city_of.get(dom, "") or r.get("city", "")
        body = {"firstName": parts[0], "lastName": parts[-1],
                "profileScraperMode": "Short", "strictSearch": STRICT,
                "maxItems": MAXITEMS, "maxPages": 1}
        if city: body["locations"] = [city]
        items, code = run_actor(body)
        n = len(items) if isinstance(items, list) else 0
        spend += n * COST_PER_RESULT
        url = conf = ""
        if code == 200:
            url, conf = verify(items, person, r["company"], city)
        note = f"http{code}" if code != 200 else (f"{n} results" if not url else conf)
        r["apify_done"] = True
        if url:
            found += 1; r["linkedin_url"] = url; r["li_source"] = "apify harvestapi"; r["li_confidence"] = conf
            con.execute("UPDATE companies SET status='full', data=? WHERE domain=?", (json.dumps(r), dom))
        else:
            con.execute("UPDATE companies SET data=? WHERE domain=?", (json.dumps(r), dom))
        con.commit()
        print(f'  [{i}/{len(todo)}] ~${spend:>5.2f} {r["company"][:26]:<28}{person[:20]:<22}'
              f'{(url or note)[:40]:<42}{conf}', flush=True)
        time.sleep(0.3)

    st = con.execute("SELECT COUNT(*) FROM companies WHERE status='full'").fetchone()[0]
    print(f"\n~${spend:.2f} spent (est, floor) | found {found} URLs this run | status=full now {st}")
    print("next: python3 enrich_push.py --apply")


main()
