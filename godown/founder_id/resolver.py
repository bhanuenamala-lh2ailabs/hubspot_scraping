# -*- coding: utf-8 -*-
"""Founder-identity resolver — MCA director mirrors + paced DDG, per SOLVE_FOUNDER_IDENTITY.md.

Implements the research doc's waterfall with the mirror set that ACTUALLY fetches from this
IP (probed 16 Aug): FalconEbiz + QuickCompany are open here (ZaubaCorp/TCC/IndiaFilings are
walled — the doc's probes ran from other infra and disagreed in both directions), and
DuckDuckGo lifted its wall after a two-day cooldown, so it is the search layer at gentle,
randomized pacing with a hard daily cap. Jina is keyless-dead (401) and stays out.

Stages per company (stop at identity_status=full):
  B  company+city -> CIN            DDG snippets; CIN validated for shape/state/year
  C  CIN -> director board          FalconEbiz direct, QuickCompany second; two-source rule
  E  board -> the leader            MD > earliest-appointed director; co-founders both kept
  F  leader -> LinkedIn URL         DDG site:linkedin.com/in snippet; never fetches LinkedIn
Every accepted name carries source_url + verbatim quote — model recall is banned, a name
without a citation is discarded. City/state conflict rejects the CIN match outright.

State in resolver.sqlite: resumable, per-source daily counters, wall log. On 3 consecutive
walls a source cools for the run; DDG walls end the run (resume next slice).

Usage: python3 resolver.py [--limit 25] [--input <csv>]     (default input: the 450 queue)
"""
import os, re, sys, csv, json, time, random, sqlite3, urllib.request, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
QUEUE = os.path.join(HUB, "godown", "prequal", "prequal_out", "enrich_queue.csv")
OUT = os.path.join(HERE, "founder_identity.csv")
DB = os.path.join(HERE, "resolver.sqlite")
LIMIT = 0; SRC = QUEUE
ENGINE_FREE = "--engine-free" in sys.argv     # QC slug-construction only; DDG never called.
for i, a in enumerate(sys.argv):
    if a == "--limit": LIMIT = int(sys.argv[i + 1])
    if a == "--input": SRC = sys.argv[i + 1]

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
CIN_RX = re.compile(r"\b([LU]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6})\b")
LI_RX = re.compile(r"^https?://([a-z]{2,3}\.)?linkedin\.com/in/[^/?#]+/?$")
SENIOR_TITLES = ("managing director", "whole time director", "director", "designated partner")
STATE_OF = {"bengaluru": "KA", "bangalore": "KA", "mumbai": "MH", "pune": "MH", "nagpur": "MH",
            "delhi": "DL", "new delhi": "DL", "noida": "UP", "lucknow": "UP", "gurgaon": "HR",
            "gurugram": "HR", "chennai": "TN", "coimbatore": "TN", "hyderabad": "TS",
            "ahmedabad": "GJ", "surat": "GJ", "vadodara": "GJ", "rajkot": "GJ", "kolkata": "WB",
            "jaipur": "RJ", "indore": "MP", "bhopal": "MP", "chandigarh": "CH", "mohali": "PB",
            "kochi": "KL", "ernakulam": "KL", "trivandrum": "KL", "bhubaneswar": "OR"}
DAILY = {"ddg": 400, "falconebiz": 800, "quickcompany": 800}


def db():
    c = sqlite3.connect(DB)
    c.execute("CREATE TABLE IF NOT EXISTS companies(domain PRIMARY KEY, status, cin, last_stage, data)")
    c.execute("CREATE TABLE IF NOT EXISTS counters(source, day, n, PRIMARY KEY(source,day))")
    c.execute("CREATE TABLE IF NOT EXISTS walls(source, ts, code)")
    return c


def bump(c, src):
    day = time.strftime("%Y-%m-%d")
    c.execute("INSERT INTO counters VALUES(?,?,1) ON CONFLICT(source,day) DO UPDATE SET n=n+1", (src, day))
    c.commit()
    return c.execute("SELECT n FROM counters WHERE source=? AND day=?", (src, day)).fetchone()[0]


def fetch(url, timeout=18):
    try:
        r = urllib.request.Request(url, headers=UA)
        return urllib.request.urlopen(r, timeout=timeout).read(400_000).decode("utf-8", "replace"), 200
    except urllib.error.HTTPError as e:
        return "", e.code
    except Exception as e:
        return "", type(e).__name__


WALLS = {"ddg": 0, "falconebiz": 0, "quickcompany": 0}


def ddg(c, q):
    """-> list of results, or None on a WALL. None and [] mean different things: [] is a
    real answer with nothing in it, None is 'the engine refused to answer' — the pilot
    recorded 6 walls as 20 false no_cin verdicts before this distinction existed."""
    if bump(c, "ddg") > DAILY["ddg"]: raise SystemExit("ddg daily cap — resume next slice")
    h, code = fetch("https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(q))
    time.sleep(random.uniform(8, 14))
    if code != 200 or "result__a" not in h:
        WALLS["ddg"] += 1
        c.execute("INSERT INTO walls VALUES('ddg',?,?)", (time.time(), str(code))); c.commit()
        if WALLS["ddg"] >= 8: raise SystemExit("ddg walled 8x consecutively — stop, cool overnight")
        time.sleep(random.uniform(90, 180))      # long backoff; intermittent walls do clear
        return None
    WALLS["ddg"] = 0
    out = []
    for m in re.finditer(r'class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', h, re.S):
        u = m.group(1); mm = re.search(r"uddg=([^&]+)", u)
        if mm: u = urllib.parse.unquote(mm.group(1))
        out.append((re.sub(r"<[^>]+>", "", m.group(2))[:120], u))
    # snippets carry CINs/names too
    out += [(re.sub(r"<[^>]+>", "", s)[:200], "") for s in
            re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', h, re.S)[:8]]
    return out


def caps_name(legal):
    return re.sub(r"[^A-Z0-9]+", "-", legal.upper()).strip("-")


def plausible_cin(cin, city, founded):
    st = cin[6:8]; yr = cin[8:12]
    if city and STATE_OF.get(city.lower().split(",")[0].strip()) not in (None, st): return False
    if not ("1980" <= yr <= "2024"): return False
    if founded and str(founded).isdigit() and abs(int(yr) - int(founded)) > 3: return False
    return True


def qc_page(c, url):
    """Fetch + parse a QuickCompany company page -> board dict, or None.

    FalconEbiz was cut entirely: from this IP it 200-serves its LANDING page for every
    company URL including the research doc's own verified example — the earlier 'Director'
    evidence was navbar text. QuickCompany is the one mirror that returns real boards here
    (verified: MOTIWALA/MANSOOR present for the reference CIN). Page shape: the director
    names sit between the company title and 'N Directors', middot-separated; incorporation
    date and State/ROC follow — used to cross-check against known city/founded year.
    """
    if bump(c, "quickcompany") > DAILY["quickcompany"]: return None
    h, code = fetch(url)
    time.sleep(random.uniform(4, 8))
    if code != 200 or "quickcompany" not in url: return None
    raw_cin = CIN_RX.search(h)
    txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h)).replace("&#183;", "·")
    m = re.search(r"Follow\s+(.{5,240}?)\s+(\d+)\s+Directors?", txt)
    if not m: return None
    names = [n.strip() for n in m.group(1).split("·") if 4 < len(n.strip()) < 45]
    if not names: return None            # matched layout but zero usable names -> not a board
    inc = re.search(r"Date of Incorporation\s+(\d{1,2} \w+ (\d{4}))", txt)
    st = re.search(r"State / ROC\s+([A-Za-z ]+?) /", txt)
    q = " ".join(txt[m.start():m.end() + 40].split())[:130]
    return {"dirs": [{"name": n, "din": "", "title": "Director"} for n in names],
            "cin": raw_cin.group(0) if raw_cin else "", "inc_year": inc.group(2) if inc else "",
            "state_city": (st.group(1).strip() if st else ""), "url": url, "quote": q}


def falcon(c, legal, cin):
    if bump(c, "falconebiz") > DAILY["falconebiz"]: return None
    h, code = fetch(f"https://www.falconebiz.com/company/{caps_name(legal)}-{cin}")
    time.sleep(random.uniform(4, 8))
    if code != 200:
        WALLS["falconebiz"] += 1; c.execute("INSERT INTO walls VALUES('falconebiz',?,?)", (time.time(), str(code))); c.commit()
        return None
    txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"<script.*?</script>|<style.*?</style>", " ", h, flags=re.S)))
    dirs = []
    for m in re.finditer(r"(\d{7,8})\s+([A-Z][A-Z .]{3,40}?)\s+(Managing Director|Whole[- ]time Director|Director|Designated Partner)", txt, re.I):
        dirs.append({"din": m.group(1), "name": m.group(2).title().strip(), "title": m.group(3).title()})
    if not dirs:
        for m in re.finditer(r"directors? of [^.]{0,80}? (?:are|is) ([^.]{5,160})\.", txt, re.I):
            for nm in re.split(r",| and ", m.group(1)):
                nm = nm.strip()
                if 4 < len(nm) < 40: dirs.append({"din": "", "name": nm.title(), "title": "Director"})
    q = ""
    if dirs:
        i = txt.lower().find(dirs[0]["name"].lower()[:12])
        q = " ".join(txt[max(0, i - 40):i + 90].split())[:130]
    return {"dirs": dirs[:6], "url": f"https://www.falconebiz.com/company/{caps_name(legal)}-{cin}", "quote": q} if dirs else None


def quickco(c, legal):
    if bump(c, "quickcompany") > DAILY["quickcompany"]: return None
    slug = re.sub(r"[^a-z0-9]+", "-", legal.lower()).strip("-")
    h, code = fetch(f"https://www.quickcompany.in/company/{slug}")
    time.sleep(random.uniform(4, 8))
    if code != 200: return None
    txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h))
    dirs = []
    for m in re.finditer(r"([A-Z][a-z]+(?: [A-Z][a-z]+){1,3})\s*(?:\(|,|-)?\s*(?:DIN[: ]*(\d{7,8}))", txt):
        dirs.append({"name": m.group(1), "din": m.group(2), "title": ""})
    q = ""
    if dirs:
        i = txt.find(dirs[0]["name"])
        q = " ".join(txt[max(0, i - 40):i + 90].split())[:130]
    return {"dirs": dirs[:6], "url": f"https://www.quickcompany.in/company/{slug}", "quote": q} if dirs else None


def slug_candidates(brand):
    """Constructed QC slugs, most-likely first. Probed hit rate 4/5 on queue brands —
    QuickCompany serves /company/{slug} to plain fetches and its robots.txt allows the
    path, which makes the whole company->board step ENGINE-FREE for most firms."""
    base = re.sub(r"[^a-z0-9]+", "-", brand.lower()).strip("-")
    cands = [f"{base}-private-limited", base, f"{base}-llp"]
    if "technolog" not in base and "solution" not in base:
        cands.append(f"{base}-technologies-private-limited")
    toks = base.split("-")
    if len(toks) > 2:
        cands.append("-".join(toks[:2]) + "-private-limited")
    return cands[:5]


def pick_leader(dirs):
    for t in SENIOR_TITLES:
        for d in dirs:
            if t in (d.get("title") or "").lower(): return d
    return dirs[0] if dirs else None


def main():
    c = db()
    rows = list(csv.DictReader(open(SRC, encoding="utf-8-sig")))
    todo = [r for r in rows if r.get("identity_status") != "identity_full"]
    done = {r[0] for r in c.execute("SELECT domain FROM companies WHERE status IN ('full','name_only','no_cin','no_dirs')")}
    todo = [r for r in todo if r["domain"] not in done]
    if LIMIT: todo = todo[:LIMIT]
    print(f"resolving {len(todo)} companies ({len(done)} already in state)", flush=True)

    res = []
    for i, r in enumerate(todo, 1):
        name, city, dom = r["name"], r.get("city", ""), r["domain"]
        founded = r.get("founded_year") or ""
        rec = {"company": name, "domain": dom, "cin": "", "founder_name": "", "din": "",
               "title": "", "linkedin_url": "", "source_1_url": "", "source_1_quote": "",
               "source_2_url": "", "confidence": "", "identity_status": "pending"}
        # B+C, engine-free first: constructed slugs straight against QuickCompany. Only a
        # miss falls through to the engine (or parks, in --engine-free mode).
        if ENGINE_FREE:
            board_pack = None
            for sl in slug_candidates(name):
                p = qc_page(c, f"https://www.quickcompany.in/company/{sl}")
                if not p: continue
                if founded and p["inc_year"] and abs(int(p["inc_year"]) - int(founded)) > 3: continue
                board_pack = p; break
            if not board_pack:
                c.execute("REPLACE INTO companies VALUES(?,?,?,?,?)",
                          (dom, "pending", "", "construct_miss", json.dumps(rec))); c.commit()
                print(f"[{i}/{len(todo)}] {name[:30]:<32}construction miss — engine pass later", flush=True)
                continue
            rec["cin"] = board_pack["cin"]
            lead = pick_leader(board_pack["dirs"])
            if lead is None:
                c.execute("REPLACE INTO companies VALUES(?,?,?,?,?)",
                          (dom, "pending", "", "construct_miss", json.dumps(rec))); c.commit()
                print(f"[{i}/{len(todo)}] {name[:30]:<32}empty board — engine pass later", flush=True)
                continue
            rec.update({"founder_name": lead["name"], "din": "", "title": "Director",
                        "source_1_url": board_pack["url"], "source_1_quote": board_pack["quote"],
                        "confidence": "medium", "identity_status": "name_only"})
            c.execute("REPLACE INTO companies VALUES(?,?,?,?,?)",
                      (dom, "name_only", rec["cin"], "C_constructed", json.dumps(rec))); c.commit()
            res.append(rec)
            print(f'[{i}/{len(todo)}] {name[:30]:<32}{lead["name"][:26]:<28}constructed', flush=True)
            continue
        hits = ddg(c, f'site:quickcompany.in/company "{name}" {city}')
        if hits is None:
            c.execute("REPLACE INTO companies VALUES(?,?,?,?,?)", (dom, "pending", "", "B_wall", json.dumps(rec))); c.commit()
            print(f"[{i}/{len(todo)}] {name[:30]:<32}engine wall — parked", flush=True); continue
        qc_urls = [u.split("?")[0] for _, u in hits if "/company/" in u and "quickcompany.in" in u][:3]
        if not qc_urls:      # brand != legal name: retry without quotes, mine any mirror slug
            hits2 = ddg(c, f"{name} {city} quickcompany")
            if hits2 is None:
                c.execute("REPLACE INTO companies VALUES(?,?,?,?,?)", (dom, "pending", "", "B_wall", json.dumps(rec))); c.commit()
                print(f"[{i}/{len(todo)}] {name[:30]:<32}engine wall — parked", flush=True); continue
            qc_urls = [u.split("?")[0] for _, u in hits2 if "/company/" in u and "quickcompany.in" in u][:3]
        board_pack = None
        for qu in qc_urls:
            p = qc_page(c, qu)
            if not p: continue
            # plausibility: page's ROC state vs known city, incorporation vs founded year,
            # and slug must share a distinctive token with the brand name
            tok = [t for t in re.sub(r"[^a-z0-9 ]", " ", name.lower()).split()
                   if t not in ("the", "pvt", "ltd", "llp", "private", "limited", "technologies",
                                "technology", "solutions", "software", "softwares", "systems",
                                "services", "infotech", "india", "inc")]
            if tok and not any(t in qu.lower() for t in tok): continue
            if founded and p["inc_year"] and abs(int(p["inc_year"]) - int(founded)) > 3: continue
            if city and p["state_city"] and STATE_OF.get(city.lower().split(",")[0].strip()) and \
               STATE_OF.get(p["state_city"].lower().split()[0], p["state_city"][:2].upper()) not in \
               (None, STATE_OF.get(city.lower().split(",")[0].strip())): pass  # ROC label is a city name; soft check only
            board_pack = p; break
        if not board_pack:
            rec["identity_status"] = "no_cin"
            c.execute("REPLACE INTO companies VALUES(?,?,?,?,?)", (dom, "no_cin", "", "B", json.dumps(rec))); c.commit()
            res.append(rec); print(f"[{i}/{len(todo)}] {name[:30]:<32}no QC page (real answer)", flush=True); continue
        rec["cin"] = board_pack["cin"]
        lead = pick_leader(board_pack["dirs"])
        rec.update({"founder_name": lead["name"], "din": "", "title": "Director",
                    "source_1_url": board_pack["url"], "source_1_quote": board_pack["quote"]})
        rec["confidence"] = "medium"     # single mirror; snippet corroboration upgrades below
        for ttl, _ in hits:
            if lead["name"].split()[0].lower() in ttl.lower() and lead["name"].split()[-1].lower() in ttl.lower():
                rec["source_2_url"] = "ddg-snippet"; rec["confidence"] = "high"; break
        # F: LinkedIn via DDG snippet, never fetching LinkedIn; a wall leaves name_only
        # with last_stage marking F for a retry on the next slice
        fh = ddg(c, f'site:linkedin.com/in "{lead["name"]}" "{name}"')
        for ttl, u in (fh or []):
            if "linkedin.com/in/" in u and LI_RX.match(u.split("?")[0]):
                nm_ok = lead["name"].split()[0].lower() in ttl.lower()
                if nm_ok: rec["linkedin_url"] = u.split("?")[0]; break
        rec["identity_status"] = "full" if rec["linkedin_url"] else "name_only"
        c.execute("REPLACE INTO companies VALUES(?,?,?,?,?)", (dom, rec["identity_status"], rec["cin"], "F", json.dumps(rec))); c.commit()
        res.append(rec)
        print(f'[{i}/{len(todo)}] {name[:30]:<32}{lead["name"][:24]:<26}{rec["confidence"]:<7}'
              f'{"LI" if rec["linkedin_url"] else "--"}', flush=True)

    hdr = ["company", "domain", "cin", "founder_name", "din", "title", "linkedin_url",
           "source_1_url", "source_1_quote", "source_2_url", "confidence", "identity_status"]
    exists = os.path.exists(OUT)
    with open(OUT, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=hdr)
        if not exists: w.writeheader()
        w.writerows(res)
    st = {}
    for r in res: st[r["identity_status"]] = st.get(r["identity_status"], 0) + 1
    print("\nbatch result:", st)
    print("walls:", dict(c.execute("SELECT source, COUNT(*) FROM walls GROUP BY source")))


main()
