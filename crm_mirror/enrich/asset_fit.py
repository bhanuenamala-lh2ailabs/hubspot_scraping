# -*- coding: utf-8 -*-
"""
Asset-fit enrichment for the top distressed Tracxn targets.

Layers TWO new scores on top of the distress rank, because "dying + cheap" != "owns
something worth buying". We buy either a pre-2024 CODEBASE or the company's OPS DATA,
and those want almost opposite things (small clean product vs once-big data-rich scale).

Per company:
  1. Wayback CDX  -> product age (pre-2024 proof), death timing, capture count  [free]
  2. Homepage text: live domain, else LAST LIVE Wayback snapshot                 [free]
  3. Claude (Haiku) -> company_type / real-product? / sector / value reads       [anthropic key]
  4. Join funded/unfunded tab -> peak funding / revenue / employees (ex-scale)
  5. codebase_fit + opsdata_fit ; HARD-DROP services-shells from codebase list

Resumable: checkpoints to asset_scores.json after every company.
Usage: python asset_fit.py [--limit N] [--only domain1,domain2] [--model haiku|sonnet]
"""
import json, os, re, sys, time, urllib.request, urllib.error, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))      # crm_mirror/
HUB  = os.path.dirname(ROOT)                                            # project root
TRX  = os.path.join(ROOT, "sources", "tracxn")
OUTD = os.path.dirname(os.path.abspath(__file__))
OUTF = os.path.join(OUTD, "asset_scores.json")
UA   = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

env = {}
for l in open(os.path.join(HUB, ".env"), encoding="utf-8-sig"):
    if "=" in l and not l.strip().startswith("#"):
        k, v = l.split("=", 1); env[k.strip().lower()] = v.strip()
ANTHRO = env["anthropic_api_key"]
MODEL  = {"haiku": "claude-haiku-4-5-20251001", "sonnet": "claude-sonnet-5"}

# ---------- helpers ----------
def truthy(v): return str(v).strip().lower() in ("y", "yes", "true", "1")

def norm_name(n):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", (n or "").lower())).strip()

def get(url, timeout=12, tries=4):
    for a in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503, 504) and a < tries - 1:   # Wayback throttling -> back off
                time.sleep(2.5 * (a + 1)); continue
            return e.code, b""
        except Exception:
            if a == tries - 1: return None, b""
            time.sleep(1.5 * (a + 1))
    return None, b""

def html_to_text(b):
    try: t = b.decode("utf-8", "ignore")
    except Exception: t = str(b)
    t = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", t)
    # keep title + meta description explicitly
    grab = []
    m = re.search(r"(?is)<title[^>]*>(.*?)</title>", t)
    if m: grab.append("TITLE: " + re.sub(r"\s+", " ", m.group(1)).strip())
    for mm in re.finditer(r'(?is)<meta[^>]+name=["\'](?:description|keywords)["\'][^>]+content=["\'](.*?)["\']', t):
        grab.append("META: " + re.sub(r"\s+", " ", mm.group(1)).strip())
    body = re.sub(r"(?s)<[^>]+>", " ", t)
    body = re.sub(r"&[a-z#0-9]+;", " ", body)
    body = re.sub(r"\s+", " ", body).strip()
    return (" | ".join(grab) + " || " + body)[:3500]

# ---------- wayback ----------
def wayback(domain):
    """first/last capture year + count, and the list of 2xx capture timestamps (monthly)."""
    u = ("http://web.archive.org/cdx/search/cdx?url=" + urllib.parse.quote(domain) +
         "&output=json&fl=timestamp,statuscode&collapse=timestamp:6&limit=20000")
    s, b = get(u, timeout=25)
    if not b: return {}
    try: rows = json.loads(b.decode("utf-8", "ignore"))
    except Exception: return {}
    rows = rows[1:] if rows and rows[0] and rows[0][0] == "timestamp" else rows
    if not rows: return {}
    ts = [r[0] for r in rows if r and r[0]]
    ok = [r[0] for r in rows if len(r) > 1 and str(r[1]).startswith("2")]  # 2xx captures only
    return {"first": ts[0][:8], "last": ts[-1][:8], "captures": len(ts),
            "first_year": int(ts[0][:4]), "last_year": int(ts[-1][:4]),
            "ok_ts": ok or ts}

# tell-tale text of a parked / expired / for-sale / hosting-placeholder page (NOT the real product)
_DEAD_RX = re.compile(r"(?i)(domain (is )?for sale|buy this domain|parked (free|domain)|"
                      r"is for sale|godaddy|sedo\b|namecheap|hugedomains|dan\.com|porkbun|"
                      r"this domain (may be|is) for sale|renew (your )?domain|account suspended|"
                      r"default web page|website coming soon|under construction|namesilo)")
def looks_dead_page(text):
    if not text or len(text) < 140: return True
    return bool(_DEAD_RX.search(text[:1200]))

def wayback_home(snap_ts, domain):
    u = f"http://web.archive.org/web/{snap_ts}id_/http://{domain}/"
    s, b = get(u, timeout=25)
    return html_to_text(b) if b else ""

def _active_candidates(ok, founded_year):
    """snapshot timestamps within the company's OWN lifespan, newest(most mature) first.
    Bounding by founded_year avoids a previous domain-owner's site (domain reuse)."""
    if not ok: return []
    lo = (founded_year or 0)                          # not before the company existed
    hi = (founded_year + 7) if founded_year else 9999 # not long after (post-sale/parked)
    win = [t for t in ok if lo <= int(t[:4]) <= hi]
    win = win or ok                                   # fall back to all if window empty
    # newest first = most built-out product, but drop the very last capture if we have others
    order = list(reversed(win))
    if len(order) > 2: order = order[1:] + order[:1]  # push terminal capture to the back
    return order[:6]

# ---------- homepage (live if it's the real product, else an in-lifespan wayback snapshot) ----------
def homepage(domain, wb, founded_year=None, deadpooled=False):
    # a deadpooled company's live domain is unreliable (parked / sold to someone else) -> skip it
    if not deadpooled:
        for scheme in ("https://", "http://"):
            s, b = get(scheme + domain + "/", timeout=9)
            if b and s and 200 <= s < 300 and len(b) > 400:
                txt = html_to_text(b)
                if not looks_dead_page(txt): return txt, "live"
                break
    # reconstruct the product from a Wayback snapshot taken while the company was alive
    for snap in _active_candidates(wb.get("ok_ts", []), founded_year):
        txt = wayback_home(snap, domain)
        if txt and not looks_dead_page(txt):
            return txt, "wayback:" + snap[:6]
    return "", "none"

# ---------- claude classify ----------
CLS_SCHEMA = """Return ONLY minified JSON, no prose:
{"company_type":"product|infra_devtools|marketplace|services_agency|unknown",
"is_real_software_product":true|false,"matches_company":true|false,
"sector":"fintech|healthtech|logistics|ecommerce|edtech|saas|devtools|media|other",
"codebase_value":0-10,"ops_intensive":true|false,"opsdata_value":0-10,
"confidence":0.0-1.0,"reason":"<=20 words","outreach_angle":"codebase|data|both|skip"}"""

def classify(company, sector_hint, founded, text, model):
    src = (f"Homepage/last-live text:\n{text[:3200]}" if text
           else "(no page text retrieved — classify from the company name + your own knowledge)")
    prompt = (f"Company under assessment: {company}\nFounded: {founded}\nTracxn stage/sector hint: {sector_hint}\n{src}\n\n"
              f"Assess ONLY this company ('{company}') to estimate two assets IT built while operating:\n"
              "(1) a self-built software CODEBASE (its own product/app/platform), and\n"
              "(2) INTERNAL OPERATING KNOW-HOW — the reusable blueprint for RUNNING this kind of business: SOPs,\n"
              "    playbooks, process docs, internal tooling/workflows, org & vendor setup (NOT consumer/product analytics).\n"
              "The company may be defunct or struggling — that is expected; judge what IT BUILT. This company is the\n"
              "TARGET being assessed; it is NOT an acquirer/investor — never infer that from the framing.\n"
              "Definitions (read carefully):\n"
              "- company_type=product: has its OWN software product/app/platform (fintech app, SaaS, consumer app all count).\n"
              "- company_type=services_agency: ONLY a consultancy / dev-shop that builds software FOR CLIENTS with no product of its own. Do NOT use this for a company that has its own thin/simple product.\n"
              "- company_type=unknown: use when you lack enough information (no page text, thin/corrupted text, and you don't recognise the company).\n"
              "- matches_company: set FALSE ONLY if the retrieved PAGE TEXT clearly describes a specific, DIFFERENT named business than '" + str(company) + "' (domain reused/sold). If you merely lack data or the text is thin/corrupted/empty, keep matches_company=TRUE and use company_type=unknown. Never set it false just because you're unsure.\n"
              "- codebase_value 0-10: how real & self-built the software asset is (10=substantial SaaS/platform, 3=thin wrapper, 0=no software).\n"
              "- ops_intensive: TRUE if the business RUNS real operations (logistics, delivery, fulfilment, commerce/inventory, manufacturing, field-services, lending-collections, healthcare-delivery, multi-city ops) vs a pure-software/SaaS/media shop with little to run.\n"
              "- opsdata_value 0-10: how much valuable OPERATING KNOW-HOW they likely built — a function of how much real, multi-function operation they ran (scale, longevity, operational complexity). 10=large multi-city operation run for years; 3=small thin ops; 0=pre-launch or pure code, nothing to run.\n"
              "- outreach_angle: which asset to pitch (codebase | data=operating know-how | both | skip).\n" + CLS_SCHEMA)
    body = json.dumps({"model": model, "max_tokens": 400,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, method="POST",
        headers={"x-api-key": ANTHRO, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    for a in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                d = json.loads(r.read().decode())
            txt = "".join(c.get("text", "") for c in d.get("content", []))
            m = re.search(r"\{.*\}", txt, re.S)
            return json.loads(m.group(0)) if m else {"_err": "nojson", "_raw": txt[:200]}
        except urllib.error.HTTPError as e:
            if e.code in (429, 529, 503) and a < 3: time.sleep(3 * (a + 1)); continue
            return {"_err": f"http{e.code}", "_raw": e.read().decode()[:200]}
        except Exception as ex:
            if a < 3: time.sleep(2); continue
            return {"_err": str(ex)[:120]}

# ---------- scoring ----------
def money(v):
    try: return float(re.sub(r"[^0-9.\-]", "", str(v).split("(")[0])) or 0
    except Exception: return 0

def _year(v):
    m = re.search(r"(19|20)\d{2}", str(v or ""))
    return int(m.group(0)) if m else None

def years_operating(row, wb, tab):
    """how long the company actually RAN — proxy for how much operating machinery it built."""
    start = _year(row.get("founded_year")) or _year(tab.get("Founded Year"))
    # operating end = deadpooled date, else last funding, else last real Wayback capture
    end = (_year(tab.get("Deadpooled Date")) or _year(tab.get("Latest Funded Date")) or wb.get("last_year"))
    if not start or not end or end < start: return 0
    return min(15, end - start)

def _emp_pts(emp):
    for thr, pts in ((200, 35), (100, 30), (50, 24), (20, 16), (10, 9), (5, 4)):
        if emp >= thr: return pts
    return 0

def score(row, wb, cl, tab, had_text=False):
    ct = cl.get("company_type", "unknown")
    cv = float(cl.get("codebase_value") or 0)
    ov = float(cl.get("opsdata_value") or 0)
    # real domain-reuse only if we actually READ a page that names a different business;
    # with no page text a false matches_company is just a guess -> treat as low_data, not reuse.
    reuse = (cl.get("matches_company") is False) and had_text
    if reuse:
        return {"codebase_fit": 0, "opsdata_fit": 0, "services_shell": False,
                "domain_reuse": True, "best_angle": "review"}
    services = (ct == "services_agency")           # hard-drop ONLY explicit agencies, not no-data unknowns
    lowdata  = (ct == "unknown")                    # no usable read -> flag for review, don't exclude

    # ---- codebase_fit ----
    if services:
        cb = 0
    else:
        cb = cv * 6                                   # 0-60 from Claude read of the product
        fy = wb.get("first_year")
        if fy and fy <= 2023: cb += 12                # existed pre-2024 (Wayback proof)
        if fy and fy <= 2020: cb += 8                 # mature, well-aged codebase
        if ct in ("product", "infra_devtools"): cb += 12
        elif ct == "marketplace": cb += 6
        emp = money(tab.get("Total Employee Count"))
        if 2 <= emp <= 40: cb += 8                    # small real team -> clean, cheap-to-transfer code
        cb = min(100, round(cb))

    # ---- opsdata_fit = value of INTERNAL OPERATING KNOW-HOW (scale is king) ----
    # they only built real SOPs/playbooks/process/tooling if they actually RAN operations at scale.
    emp  = money(tab.get("Total Employee Count"))
    rev  = money(tab.get("Annual Revenue (USD)"))
    yrs  = years_operating(row, wb, tab)
    od  = _emp_pts(emp)                                 # 0-35  peak headcount = KING signal of real ops
    od += min(12, yrs * 2)                              # 0-12  years actually operating -> matured processes
    if rev > 0: od += min(8, math.log10(rev + 1) * 1.3) # 0-8   real revenue -> they truly operated, not just funded
    od += float(ov) * 3                                 # 0-30  Claude read of operating-machinery from the page
    if cl.get("ops_intensive"): od += 9                 # small sector bonus (ops-heavy model), secondary to scale
    od = min(100, round(od))

    return {"codebase_fit": cb, "opsdata_fit": od, "services_shell": services,
            "low_data": lowdata, "domain_reuse": False,
            "ops_intensive": bool(cl.get("ops_intensive")), "peak_employees": int(emp), "years_operating": yrs,
            "best_angle": ("review" if lowdata and max(cb, od) < 40 else
                           "skip" if services and od < 40 else
                           "data" if od > cb else "codebase" if cb > od else "both")}

# ---------- main ----------
def load_targets():
    rt = json.load(open(os.path.join(TRX, "lh2_ranked_targets.json"), encoding="utf-8"))
    fu = json.load(open(os.path.join(TRX, "funded.json"), encoding="utf-8"))
    un = json.load(open(os.path.join(TRX, "unfunded.json"), encoding="utf-8"))
    tab = {norm_name(r.get("Company Name")): r for r in fu + un}
    elig = [r for r in rt if not truthy(r.get("acquired")) and not truthy(r.get("ipo"))
            and (r.get("domain") or "").strip()]
    elig.sort(key=lambda r: int(r.get("rank") or 999999))
    return elig[:2000], tab

def main():
    global OUTF
    limit = None; only = None; model = MODEL["haiku"]; offset = 0
    for i, a in enumerate(sys.argv):
        if a == "--limit": limit = int(sys.argv[i+1])
        if a == "--offset": offset = int(sys.argv[i+1])
        if a == "--only": only = set(sys.argv[i+1].split(","))
        if a == "--model": model = MODEL.get(sys.argv[i+1], sys.argv[i+1])
        if a == "--out": OUTF = os.path.join(OUTD, sys.argv[i+1])
        if a == "--pool": globals()["_POOL"] = sys.argv[i+1]
    targets, tab = load_targets()
    if globals().get("_POOL"):                          # vet an explicit set (e.g. Shreyas 483) instead of the rank slice
        targets = json.load(open(os.path.join(OUTD, globals()["_POOL"]), encoding="utf-8"))
    if only: targets = [t for t in targets if t.get("domain") in only]
    if offset or limit: targets = targets[offset: (offset + limit) if limit else None]

    done = {}
    if os.path.exists(OUTF):
        for r in json.load(open(OUTF, encoding="utf-8")):
            # keep rows that got real page text; RETRY no-text rows on re-run (flaky Wayback self-heals)
            if r.get("text_src") and r["text_src"] != "none":
                done[r["domain"]] = r
    print(f"targets={len(targets)}  already_done={len(done)}  model={model}", flush=True)

    results = list(done.values())
    for i, t in enumerate(targets):
        dom = t["domain"].strip().lower()
        if dom in done: continue
        fy = int(t["founded_year"]) if str(t.get("founded_year")).strip().isdigit() else None
        dp = truthy(t.get("deadpooled"))
        wb = wayback(dom)
        text, src = homepage(dom, wb, fy, dp)
        cl = classify(t.get("company"), t.get("stage") or t.get("source_tab"), fy, text, model)
        sc = score(t, wb, cl, tab.get(norm_name(t.get("company")), {}), had_text=bool(text))
        rec = {"rank": t.get("rank"), "company": t.get("company"), "domain": dom,
               "tier": t.get("tier"), "composite": t.get("composite"), "deadpooled": t.get("deadpooled"),
               "text_src": src, "wb_first": wb.get("first_year"), "wb_last": wb.get("last_year"),
               "wb_captures": wb.get("captures"), "cls": cl, **sc}
        results.append(rec); done[dom] = rec
        json.dump(results, open(OUTF, "w", encoding="utf-8"), ensure_ascii=False)
        if (i + 1) % 10 == 0 or limit:
            print(f"  [{i+1}/{len(targets)}] {t.get('company')[:28]:28} "
                  f"cb={sc['codebase_fit']:3} od={sc['opsdata_fit']:3} "
                  f"{'SHELL ' if sc['services_shell'] else ''}{cl.get('company_type','?')} src={src}", flush=True)
        time.sleep(0.5)   # be polite to Wayback CDX (throttles under rapid fire)
    print(f"DONE  {len(results)} scored -> {OUTF}", flush=True)

if __name__ == "__main__":
    import urllib.parse
    main()
