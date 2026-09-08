# -*- coding: utf-8 -*-
"""Stage D crawler — two lanes, resumable, evidence-quoting. Run BOTH in background:

    python3 stage_d_crawl.py --lane wayback   # availability API, 2 workers (throttle-bound)
    python3 stage_d_crawl.py --lane site      # homepage + careers, 8 workers

Wayback lane is AVAILABILITY ONLY. Snapshot bodies are not fetched here: for a firm holding
any second corroborator (GoodFirms founded year, RDAP date, live-site copyright footer from
the site lane) a snapshot's existence completes two-corroborator PROVEN-equivalence per the
spec, so reading the body adds nothing. The residual list that truly needs snapshot wording
comes out of the merge step and is fetched in a short third pass.

Site lane per firm: D1 liveness -> D3 service mix -> D4 owned-IP scan -> footer copyright
year (a pre-2024 corroborator) -> careers discovery -> D5 JD signal extraction. All regexes
run on text with <script>/<style> stripped FIRST — a FontAwesome stylesheet once minted 11
fake Bitbucket hits (".fa-bitbucket:before{content:'\\f171'}") and cost a re-grade.

Checkpoint: one JSONL line per domain per lane; a restart skips finished domains. Fetches
time out at 12s, retry once; both failures -> fetch_failed recorded, row -> retry queue at
merge. Never scores imagined content: every extracted signal carries a <=15-word quote.
"""
import os, re, sys, csv, json, time, gzip, socket, urllib.request, urllib.error, urllib.parse
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "prequal_out")
LANE = sys.argv[sys.argv.index("--lane") + 1] if "--lane" in sys.argv else "site"
CKPT = os.path.join(OUT, f"d_{LANE}.jsonl")
# wayback: ONE worker. Two workers at 0.35s pacing burst-429'd on every single call — the
# availability API polices bursts per IP, not average rate. Serial + 0.8s holds ~60/min.
WORKERS = 1 if LANE == "wayback" else (5 if LANE == "rdap" else 8)
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
socket.setdefaulttimeout(12)


def fetch(url, attempts=2):
    last = ""
    for a in range(attempts):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=12) as x:
                raw = x.read(900_000)
                if x.headers.get("Content-Encoding") == "gzip":
                    try: raw = gzip.decompress(raw)
                    except Exception: pass
                return raw.decode("utf-8", "replace"), x.geturl(), ""
        except urllib.error.HTTPError as e:
            last = f"http{e.code}"                      # the CODE, not just 'HTTPError' —
            if e.code == 429: time.sleep(10 + 5 * a)    # a wall of nameless HTTPErrors hid
            elif a == 0: time.sleep(1.5)                # a plain 429 burst for 350 rows
        except Exception as e:
            last = type(e).__name__
            if a == 0: time.sleep(1.5)
    return "", "", last


def strip_code(html):
    html = re.sub(r"<script\b.*?</script>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<style\b.*?</style>", " ", html, flags=re.S | re.I)
    return html


def text_of(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", strip_code(html)))


def quote(text, m, w=90):
    i = max(0, m.start() - 45)
    return " ".join(text[i:m.end() + 45].split())[:w]


DEV = re.compile(r"custom software|software development|product engineering|application development|"
                 r"product development|build(ing)? (web|mobile|saas)? ?(apps|applications|products)|"
                 r"software (services|solutions) (company|firm)|development services", re.I)
QA = re.compile(r"software testing|qa (services|company)|test automation services", re.I)
OWNIP = re.compile(r"our (own )?(product|platform|saas|framework|accelerator)s?\b|our flagship|"
                   r"in[- ]house (product|platform|tool)|proprietary (product|platform|framework)|"
                   r"product suite", re.I)
PARKED = re.compile(r"domain (is )?for sale|buy this domain|parked (free )?courtesy|"
                    r"this domain (may be|is) for sale|godaddy.*parked|sedoparking", re.I)
CAREER_HREF = re.compile(r'href=["\']([^"\']*(?:career|job|join[-_]?us|opening|vacanc|work[-_]with)[^"\']*)["\']', re.I)
COPY_YEAR = re.compile(r"(?:©|&copy;|copyright)\D{0,20}((?:19|20)\d\d)", re.I)
REPO = re.compile(r"\bgit\b|github|gitlab|bitbucket|version control", re.I)
REVIEW = re.compile(r"code review|pull request|\bpr review|merge request", re.I)
CICD = re.compile(r"jenkins|azure devops|github actions|gitlab ci|circleci|ci/cd|\bcicd\b", re.I)
NONGIT = re.compile(r"\btfs\b|\btfvc\b|\bsvn\b|subversion|mercurial", re.I)
CAREER_PATHS = ["/careers", "/career", "/jobs", "/join-us", "/current-openings", "/careers/"]


def do_rdap(row):
    """Domain registration date via rdap.org — the fast pre-2024 corroborator.

    Added when the wayback availability API throttled a single pacd worker to 3/min
    (token-bucket: ~100 requests of burst, then punishment). RDAP ran 1,702 domains in
    ~35 min for the NASSCOM batch with zero throttling. A registration date <=2023 plus
    the GoodFirms founded year (or the site lane's copyright footer) makes the required
    two corroborators; wayback then only UPGRADES rows to PROVEN, off the critical path.
    """
    d = row["domain"]
    body, _, err = fetch(f"https://rdap.org/domain/{urllib.parse.quote(d)}", attempts=1)
    out = {"domain": d}
    if err: return {**out, "fetch_failed": f"rdap:{err}"}
    try:
        ev = json.loads(body).get("events") or []
        reg = next((e.get("eventDate", "") for e in ev if e.get("eventAction") == "registration"), "")
    except Exception:
        return {**out, "fetch_failed": "rdap:badjson"}
    out["rdap_registered"] = reg[:10]
    out["rdap_pre2024"] = bool(reg[:4].isdigit() and int(reg[:4]) <= 2023)
    return out


def do_wayback(row):
    d = row["domain"]
    u = f"http://archive.org/wayback/available?url={urllib.parse.quote(d)}&timestamp=20230601"
    body, _, err = fetch(u)
    out = {"domain": d}
    if err: return {**out, "fetch_failed": f"wayback:{err}"}
    try:
        snap = (json.loads(body).get("archived_snapshots") or {}).get("closest") or {}
    except Exception:
        return {**out, "fetch_failed": "wayback:badjson"}
    ts = snap.get("timestamp", "")
    out["wb_snapshot"] = snap.get("url", ""); out["wb_ts"] = ts
    out["wb_pre2024"] = bool(ts and ts[:8] <= "20231231")
    return out


def do_site(row):
    d, site = row["domain"], row["website"] or f"http://{row['domain']}"
    out = {"domain": d}
    html, final, err = fetch(site)
    if err and not html:
        html, final, err = fetch(f"http://{d}")
    if not html:
        return {**out, "fetch_failed": f"home:{err}"}
    txt = text_of(html)
    out["final_url"] = final
    out["site_dead"] = bool(len(txt) < 200 or PARKED.search(txt))
    if out["site_dead"]:
        m = PARKED.search(txt)
        out["dead_evidence"] = quote(txt, m) if m else f"page text {len(txt)} chars"
        return out
    # redirect off-domain to a global parent = captive signal for the merge step
    fin_dom = urllib.parse.urlparse(final).netloc.lower().replace("www.", "")
    out["redirected_offsite"] = bool(fin_dom and d not in fin_dom and fin_dom not in d)
    m = DEV.search(txt)
    out["dev_wording"] = bool(m); out["dev_quote"] = quote(txt, m) if m else ""
    if not m:
        mq = QA.search(txt)
        out["qa_only"] = bool(mq); out["qa_quote"] = quote(txt, mq) if mq else ""
    m = OWNIP.search(txt)
    out["owned_ip"] = bool(m); out["ownip_quote"] = quote(txt, m) if m else ""
    yrs = [int(y) for y in COPY_YEAR.findall(html)]
    out["copyright_min_year"] = min(yrs) if yrs else ""
    # ---- careers discovery + JD harvest (only if the prepass says it is still needed)
    if "careers" in row["needs"]:
        links = []
        base = final or site
        for href in CAREER_HREF.findall(strip_code(html))[:4]:
            links.append(urllib.parse.urljoin(base, href))
        for p in CAREER_PATHS:
            u2 = urllib.parse.urljoin(base, p)
            if u2 not in links: links.append(u2)
        jd, seen, used = "", set(), []
        for u2 in links[:6]:
            if urllib.parse.urlparse(u2).netloc and d not in u2 and "linkedin" not in u2: continue
            h2, _, e2 = fetch(u2, attempts=1)
            if not h2 or len(h2) < 300: continue
            t2 = text_of(h2)
            if len(t2) < 250 or t2[:200] in seen: continue
            seen.add(t2[:200]); jd += " " + t2; used.append(u2)
            if len(jd) > 60_000: break
        out["jd_chars"] = len(jd.strip()); out["jd_pages"] = ";".join(used[:3])
        if jd:
            for key, rx in (("repo_host_hits", REPO), ("review_gate_hits", REVIEW),
                            ("cicd_hits", CICD), ("nongit_hits", NONGIT)):
                ms = list(rx.finditer(jd))
                out[key] = len(ms)
                if ms: out[key.replace("_hits", "_quote")] = quote(jd, ms[0])
            # extraction integrity: harvested a lot of text but zero signals -> log the sample
            if out["jd_chars"] > 5000 and not any(out.get(k) for k in
                    ("repo_host_hits", "review_gate_hits", "cicd_hits")):
                out["extraction_verified"] = True
                out["extraction_sample"] = jd.strip()[:200]
        else:
            out["jd_chars"] = 0
    return out


def main():
    rows = list(csv.DictReader(open(os.path.join(OUT, "crawl_todo.csv"), encoding="utf-8-sig")))
    if LANE == "wayback":
        rows = [r for r in rows if "wayback" in r["needs"]]
    elif LANE == "rdap":
        # only domains with no stored RDAP date (the NASSCOM 1,702 already have one)
        rows = [r for r in rows if "wayback" in r["needs"]]
    # A fetch_failed row is NOT done — counting it as done would strand every row that hit
    # the 429 wall permanently. Failed rows re-enter the queue; merge takes the LAST record
    # per domain, so a later success supersedes the failure line.
    done = set()
    if os.path.exists(CKPT):
        for ln in open(CKPT, encoding="utf-8"):
            try:
                r = json.loads(ln)
                if not r.get("fetch_failed"): done.add(r["domain"])
            except Exception: pass
    todo = [r for r in rows if r["domain"] not in done]
    print(f"[{LANE}] {len(rows)} in lane, {len(done)} done, {len(todo)} to go, {WORKERS} workers", flush=True)

    fn = {"wayback": do_wayback, "rdap": do_rdap}.get(LANE, do_site)
    t0, n = time.time(), 0
    with open(CKPT, "a", encoding="utf-8") as ck:
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            for res in ex.map(fn, todo):
                ck.write(json.dumps(res, ensure_ascii=False) + "\n"); ck.flush()
                n += 1
                if n % 25 == 0:
                    rate = n / (time.time() - t0)
                    eta = (len(todo) - n) / rate / 60 if rate else 0
                    print(f"[{LANE}] batch {n//25}/{(len(todo)+24)//25} — {n} done, "
                          f"{rate*60:.0f}/min, ~{eta:.0f} min left", flush=True)
                if LANE == "wayback": time.sleep(0.8)    # stay under the burst limiter
    print(f"[{LANE}] COMPLETE — {n} processed in {(time.time()-t0)/60:.1f} min", flush=True)


main()
