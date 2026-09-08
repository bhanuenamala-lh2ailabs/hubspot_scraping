# -*- coding: utf-8 -*-
"""Discover Tier 2/3 Indian IT-services firms via the Google Places API (New).

Why this exists: our directory crawlers (GoodFirms/Clutch) are biased toward Tier 1 because
small-city firms don't bother listing there. Every business with a Google Business Profile
shows up on Maps regardless, so this fills the gap. Output feeds the pipeline's build phase;
canonical domain is the dedup key.

COST — the whole design is shaped by staying at $0. NOTE: the fields we need
(nationalPhoneNumber, websiteUri, rating, userRatingCount) are ENTERPRISE-tier fields in
Places API (New), not Pro as the original brief assumed — Pro covers only name/address/
location/types. So this bills at the Text Search Enterprise SKU.

Three guards, because one is never enough:
  * per-run cap      (--max-calls, default 1500)
  * MONTHLY cap      (--monthly-cap, default 4000) persisted in the cache DB and enforced
                     across runs — the free allowance is monthly, so ten polite runs can
                     still land a bill.
  * response cache   every tile stored; re-runs of covered ground cost nothing.
The only true hard stop is a quota limit set in Cloud Console; set one there too.

Auth, first that works:
  1. GOOGLE_MAPS_API_KEY in .env            <- the documented path for Places API (New)
  2. the lh2-pipeline service account       <- needs roles/serviceusage.serviceUsageConsumer

Usage:
  python gmaps_scraper.py --dry-run
  python gmaps_scraper.py --cities Mohali --max-calls 50
  python gmaps_scraper.py --priority 1 --max-calls 1000
  python gmaps_scraper.py                       # full run, inside the caps
"""
from __future__ import annotations
import os, re, sys, csv, json, time, math, glob, sqlite3, hashlib, argparse, datetime
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
import httpx, tldextract

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(HERE)
CACHE_DB = os.path.join(HERE, "data", "gmaps_cache.sqlite")
DEFAULT_OUT = os.path.join(HUB, "exports", "gmaps", "gmaps_tier2_leads.csv")
ENDPOINT = "https://places.googleapis.com/v1/places:searchText"
# Enterprise-tier field set (phone/website/rating/reviews are Enterprise in Places New).
# Never add reviews/editorialSummary/generativeSummary — those jump to the dearer
# Enterprise+Atmosphere SKU. Changing this list also invalidates nothing in the cache,
# so re-adding a field means re-paying for tiles you already fetched.
FIELD_MASK = ("places.displayName,places.formattedAddress,places.nationalPhoneNumber,"
              "places.websiteUri,places.types,places.id,places.userRatingCount,"
              "places.rating,places.location,nextPageToken")
MAX_DEPTH = 2          # 1 + 4 + 16 = up to 21 tiles per city x query
# Our fields (phone/website/rating/userRatingCount) bill at the ENTERPRISE Text Search
# SKU, not Pro as the original brief assumed. Keep the monthly ceiling well under the
# free allowance so a mistake cannot become a bill.
MONTHLY_CAP = 4000
PAGE_CAP = 3           # Google returns at most 3 pages x 20 = 60 results
QPS = 10

env = {}
_envp = os.path.join(HUB, ".env")
if os.path.exists(_envp):
    for l in open(_envp, encoding="utf-8-sig"):
        if "=" in l and not l.strip().startswith("#"):
            k, v = l.split("=", 1); env[k.strip().lower()] = v.strip()

# --------------------------------------------------------------------------- cities
CITIES = {
    # TIER 1 — proven converters + large IT hubs (all 5 queries)
    "Mohali":      {"bbox": {"low": {"lat": 30.65, "lng": 76.65}, "high": {"lat": 30.78, "lng": 76.78}}, "priority": 1, "notes": "Best converter — 27% Interested+, 1.91 avg depth"},
    "Surat":       {"bbox": {"low": {"lat": 21.10, "lng": 72.75}, "high": {"lat": 21.25, "lng": 72.90}}, "priority": 1, "notes": "0% WrongFit, 100% Called+"},
    "Indore":      {"bbox": {"low": {"lat": 22.65, "lng": 75.80}, "high": {"lat": 22.80, "lng": 75.95}}, "priority": 1, "notes": "20% Interested+, growing ecosystem"},
    "Coimbatore":  {"bbox": {"low": {"lat": 10.95, "lng": 76.90}, "high": {"lat": 11.10, "lng": 77.05}}, "priority": 1, "notes": "TIDEL Park cluster"},
    "Kochi":       {"bbox": {"low": {"lat":  9.92, "lng": 76.22}, "high": {"lat": 10.07, "lng": 76.37}}, "priority": 1, "notes": "Infopark + SmartCity"},
    "Mysuru":      {"bbox": {"low": {"lat": 12.25, "lng": 76.58}, "high": {"lat": 12.38, "lng": 76.72}}, "priority": 1, "notes": "Infosys hometown"},
    # TIER 2 — known IT presence, untested in sales (3 queries)
    "Nagpur":            {"bbox": {"low": {"lat": 21.10, "lng": 79.00}, "high": {"lat": 21.20, "lng": 79.15}}, "priority": 2, "notes": "MIHAN IT SEZ"},
    "Vizag":             {"bbox": {"low": {"lat": 17.68, "lng": 83.18}, "high": {"lat": 17.78, "lng": 83.35}}, "priority": 2, "notes": "AP IT capital"},
    "Thiruvananthapuram":{"bbox": {"low": {"lat":  8.45, "lng": 76.90}, "high": {"lat":  8.58, "lng": 77.03}}, "priority": 2, "notes": "Technopark"},
    "Lucknow":           {"bbox": {"low": {"lat": 26.78, "lng": 80.88}, "high": {"lat": 26.92, "lng": 81.05}}, "priority": 2, "notes": "UP IT push"},
    "Bhubaneswar":       {"bbox": {"low": {"lat": 20.22, "lng": 85.78}, "high": {"lat": 20.35, "lng": 85.90}}, "priority": 2, "notes": "Infocity"},
    "Bhopal":            {"bbox": {"low": {"lat": 23.20, "lng": 77.35}, "high": {"lat": 23.32, "lng": 77.48}}, "priority": 2, "notes": "33% Interested+ (small sample)"},
    "Mangaluru":         {"bbox": {"low": {"lat": 12.83, "lng": 74.82}, "high": {"lat": 12.93, "lng": 74.92}}, "priority": 2, "notes": "Growing services hub"},
    "Vadodara":          {"bbox": {"low": {"lat": 22.27, "lng": 73.15}, "high": {"lat": 22.37, "lng": 73.25}}, "priority": 2, "notes": "IT park growing"},
    # TIER 3 — exploratory (2 queries)
    "Rajkot":      {"bbox": {"low": {"lat": 22.27, "lng": 70.75}, "high": {"lat": 22.35, "lng": 70.85}}, "priority": 3, "notes": "Under-targeted"},
    "Vijayawada":  {"bbox": {"low": {"lat": 16.48, "lng": 80.58}, "high": {"lat": 16.55, "lng": 80.68}}, "priority": 3, "notes": "AP startup hub"},
    "Hubli":       {"bbox": {"low": {"lat": 15.33, "lng": 75.08}, "high": {"lat": 15.42, "lng": 75.18}}, "priority": 3, "notes": "Emerging Karnataka T3"},
    "Trichy":      {"bbox": {"low": {"lat": 10.78, "lng": 78.65}, "high": {"lat": 10.87, "lng": 78.75}}, "priority": 3, "notes": "IT corridor developing"},
    "Chandigarh":  {"bbox": {"low": {"lat": 30.70, "lng": 76.74}, "high": {"lat": 30.78, "lng": 76.82}}, "priority": 3, "notes": "Overlaps Mohali — dedup matters"},
    "Kolkata":     {"bbox": {"low": {"lat": 22.45, "lng": 88.28}, "high": {"lat": 22.62, "lng": 88.45}}, "priority": 3, "notes": "29% WrongFit — testing Maps coverage"},
}
QUERIES = ["software development company in {city}", "IT company in {city}",
           "web development company in {city}", "mobile app development company in {city}",
           "custom software company in {city}"]
QUERIES_FOR = {1: 5, 2: 3, 3: 2}

# --------------------------------------------------------------------------- filters
REJECT_TYPES = {
    "electronics_store", "hardware_store", "computer_repair_service", "computer_store",
    "electrical_repair_service", "locksmith", "education", "school", "university",
    "training_center", "telecommunications_service_provider", "cell_phone_store",
    "print_shop", "accounting", "insurance_agency", "real_estate_agency",
    "shopping_mall", "convenience_store",
}
REJECT_NAME_PATTERNS = [
    "computer repair", "laptop service", "cctv", "surveillance", "coaching",
    "training institute", "academy", "classes", "tcs", "infosys", "wipro", "hcl tech",
    "tech mahindra", "cognizant", "accenture", "capgemini", "xerox", "printer",
    "toner", "cartridge",
]
MIN_REVIEWS, MAX_REVIEWS = 3, 200
SUFFIXES = re.compile(r"(?i)[\s,]*\b(pvt\.?\s*ltd\.?|private\s+limited|p\.?\s*ltd\.?|"
                      r"llp|ltd\.?|inc\.?|limited|opc)\b\.?\s*$")


def clean_name(n):
    n = re.sub(r"\s+", " ", (n or "")).strip(" .,-")
    for _ in range(3):
        m = SUFFIXES.sub("", n).strip(" .,-")
        if m == n: break
        n = m
    return n


def domain_of(url):
    if not url: return ""
    e = tldextract.extract(url)
    return f"{e.domain}.{e.suffix}".lower() if e.domain and e.suffix else ""


def keep(p):
    """-> (True, '') or (False, reason). Order matters: cheapest reject first."""
    name = (p.get("displayName", {}) or {}).get("text", "")
    low = name.lower()
    if set(p.get("types") or []) & REJECT_TYPES:
        return False, "rejected_type"
    for pat in REJECT_NAME_PATTERNS:
        if pat in low: return False, f"name:{pat}"
    if not p.get("websiteUri"): return False, "no_website"
    rc = p.get("userRatingCount")
    if rc is None or rc < MIN_REVIEWS: return False, "too_few_reviews"
    if rc > MAX_REVIEWS: return False, "too_many_reviews"
    if not domain_of(p.get("websiteUri")): return False, "unparseable_domain"
    return True, ""


# --------------------------------------------------------------------------- budget
class BudgetTracker:
    """Two ceilings, because one is not enough.

    A per-run cap stops a single runaway invocation. But Google's free allowance is
    MONTHLY, so ten well-behaved runs can still land a bill. Every call is therefore also
    written to a persistent per-month ledger in the cache DB, and the monthly cap is
    enforced across runs. Whichever ceiling is hit first stops the crawl.
    """
    def __init__(self, max_calls, monthly_cap, db):
        self.max_calls = max_calls; self.monthly_cap = monthly_cap; self.db = db
        self.calls_made = 0
        self.month = datetime.date.today().strftime("%Y-%m")
        db.execute("CREATE TABLE IF NOT EXISTS usage(month TEXT PRIMARY KEY, calls INT)")
        db.commit()
        r = db.execute("SELECT calls FROM usage WHERE month=?", (self.month,)).fetchone()
        self.month_start = r[0] if r else 0

    @property
    def month_total(self): return self.month_start + self.calls_made

    def can_call(self):
        return self.calls_made < self.max_calls and self.month_total < self.monthly_cap

    def record_call(self):
        self.calls_made += 1
        self.db.execute(
            "INSERT INTO usage(month,calls) VALUES(?,?) "
            "ON CONFLICT(month) DO UPDATE SET calls=calls+1", (self.month, 1))
        self.db.commit()
        if self.calls_made % 100 == 0:
            print(f"    ... run {self.calls_made}/{self.max_calls} | "
                  f"{self.month} total {self.month_total}/{self.monthly_cap}", flush=True)

    @property
    def remaining(self): return min(self.max_calls - self.calls_made,
                                    self.monthly_cap - self.month_total)

    def stop_reason(self):
        if self.month_total >= self.monthly_cap: return "MONTHLY cap"
        if self.calls_made >= self.max_calls: return "per-run cap"
        return ""


# --------------------------------------------------------------------------- cache
class Cache:
    def __init__(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute("CREATE TABLE IF NOT EXISTS tiles("
                        "k TEXT PRIMARY KEY, query TEXT, bbox TEXT, places TEXT, "
                        "calls INT, at TEXT)")
        self.db.commit()
    @staticmethod
    def key(q, bbox):
        return hashlib.sha256(f"{q}|{json.dumps(bbox, sort_keys=True)}".encode()).hexdigest()
    def get(self, q, bbox):
        r = self.db.execute("SELECT places FROM tiles WHERE k=?", (self.key(q, bbox),)).fetchone()
        return json.loads(r[0]) if r else None
    def put(self, q, bbox, places, calls):
        self.db.execute("INSERT OR REPLACE INTO tiles VALUES(?,?,?,?,?,?)",
                        (self.key(q, bbox), q, json.dumps(bbox, sort_keys=True),
                         json.dumps(places), calls,
                         datetime.datetime.now().isoformat(timespec="seconds")))
        self.db.commit()


# --------------------------------------------------------------------------- auth
def auth_headers():
    """-> (headers, how). Raises if neither credential works."""
    key = env.get("google_maps_api_key") or os.environ.get("GOOGLE_MAPS_API_KEY")
    if key:
        return {"X-Goog-Api-Key": key, "X-Goog-FieldMask": FIELD_MASK,
                "Content-Type": "application/json"}, "api_key"
    sa = glob.glob(os.path.join(HUB, "lh2-pipeline-*.json"))
    if sa:
        try:
            from google.oauth2 import service_account
            import google.auth.transport.requests as tr
            pid = json.load(open(sa[0], encoding="utf-8"))["project_id"]
            c = service_account.Credentials.from_service_account_file(
                sa[0], scopes=["https://www.googleapis.com/auth/cloud-platform"])
            c.refresh(tr.Request())
            # Deliberately NO X-Goog-User-Project header. Sending it makes Places demand
            # roles/serviceusage.serviceUsageConsumer on the project, which this SA lacks
            # (403). Without it the call bills to the SA's own project and works.
            return {"Authorization": "Bearer " + c.token, "X-Goog-FieldMask": FIELD_MASK,
                    "Content-Type": "application/json"}, "service_account"
        except Exception:
            pass
    raise SystemExit(
        "No usable Google Maps credential.\n\n"
        "Add an API key to .env (the documented path for Places API (New)):\n"
        "  1. console.cloud.google.com -> project lh2-pipeline\n"
        "  2. APIs & Services -> Credentials -> Create credentials -> API key\n"
        "  3. Restrict it to the 'Places API (New)' and paste into .env as:\n"
        "       GOOGLE_MAPS_API_KEY=AIza...\n\n"
        "Or grant the service account roles/serviceusage.serviceUsageConsumer on the project.")


# --------------------------------------------------------------------------- search
class Searcher:
    def __init__(self, budget, cache, headers, verbose=True):
        self.b = budget; self.c = cache; self.h = headers; self.verbose = verbose
        self.http = httpx.Client(timeout=60)
        self._last = 0.0
        self.stopped = False
        self.quota_exhausted = ""

    def _throttle(self):
        gap = 1.0 / QPS
        d = time.monotonic() - self._last
        if d < gap: time.sleep(gap - d)
        self._last = time.monotonic()

    def _pages(self, query, bbox):
        """All pages for one tile. -> (places, calls_used, ok).

        `ok` is False if anything went wrong. It matters enormously: a failed tile must
        NEVER reach the cache. A 429 returns zero places, and caching that would make the
        city look permanently empty on every future run — the cache would lock in a lie.
        """
        places, token, calls, ok = [], None, 0, True
        for _ in range(PAGE_CAP):
            if not self.b.can_call():
                self.stopped = True; ok = False; break
            body = {"textQuery": query, "maxResultCount": 20, "languageCode": "en",
                    "locationRestriction": {"rectangle": {
                        "low": {"latitude": bbox["low"]["lat"], "longitude": bbox["low"]["lng"]},
                        "high": {"latitude": bbox["high"]["lat"], "longitude": bbox["high"]["lng"]}}}}
            if token: body["pageToken"] = token
            self._throttle()
            r = self.http.post(ENDPOINT, json=body, headers=self.h)
            self.b.record_call(); calls += 1
            if r.status_code == 429:
                # Distinguish a burst (per-minute, worth retrying) from an exhausted
                # DAILY quota, which retrying cannot fix — it just burns the loop and
                # returns an empty tile that looks like "this city has no companies".
                lim = ""
                try:
                    for det in r.json().get("error", {}).get("details", []):
                        lim = det.get("metadata", {}).get("quota_limit", "") or lim
                except Exception: pass
                if "PerDay" in lim:
                    self.quota_exhausted = lim; self.stopped = True; ok = False; break
                time.sleep(2); ok = False; continue
            if r.status_code != 200:
                print(f"    HTTP {r.status_code}: {r.text[:200]}", flush=True)
                if r.status_code in (401, 403): self.stopped = True
                ok = False; break
            d = r.json()
            places += d.get("places", []) or []
            token = d.get("nextPageToken")
            if not token: break
            time.sleep(1.2)          # a fresh page token is not valid immediately
        return places, calls, ok

    def tile(self, query, bbox, depth=0):
        """Recursive grid search. Subdivides only when a tile saturates at 60 results."""
        cached = self.c.get(query, bbox)
        if cached is None:
            if not self.b.can_call():
                self.stopped = True; return []
            cached, calls, ok = self._pages(query, bbox)
            if ok:
                self.c.put(query, bbox, cached, calls)   # only ever cache a clean fetch
        out = list(cached)
        if len(cached) >= 60 and depth < MAX_DEPTH and not self.stopped:
            if self.verbose:
                print(f"    tile saturated ({len(cached)}) -> subdividing at depth {depth+1}", flush=True)
            for sub in subdivide_bbox(bbox):
                out += self.tile(query, sub, depth + 1)
        return out


def subdivide_bbox(b):
    """Split into 4 quadrants. (The draft spec had the NW quadrant's high-lat wrong —
    it reused mid_lat for both corners, producing a zero-height box.)"""
    ml = (b["low"]["lat"] + b["high"]["lat"]) / 2
    mg = (b["low"]["lng"] + b["high"]["lng"]) / 2
    lo, hi = b["low"], b["high"]
    return [
        {"low": {"lat": lo["lat"], "lng": lo["lng"]}, "high": {"lat": ml,      "lng": mg}},
        {"low": {"lat": lo["lat"], "lng": mg},        "high": {"lat": ml,      "lng": hi["lng"]}},
        {"low": {"lat": ml,        "lng": lo["lng"]}, "high": {"lat": hi["lat"], "lng": mg}},
        {"low": {"lat": ml,        "lng": mg},        "high": {"lat": hi["lat"], "lng": hi["lng"]}},
    ]


# --------------------------------------------------------------------------- exclusions
def load_exclusions(extra_path=None):
    ex, src = set(), []
    p = os.path.join(HERE, "data", "pipeline.sqlite")
    if os.path.exists(p):
        try:
            db = sqlite3.connect(p)
            n = 0
            for (d,) in db.execute("SELECT DISTINCT domain FROM companies WHERE domain IS NOT NULL"):
                if d: ex.add(d.lower().strip()); n += 1
            src.append(f"pipeline.sqlite:{n}")
        except Exception: pass
    p = os.path.join(HUB, "crm_mirror", "data", "index", "by_domain.json")
    if os.path.exists(p):
        try:
            j = json.load(open(p, encoding="utf-8"))
            for d in (j.keys() if isinstance(j, dict) else j):
                if d: ex.add(str(d).lower().strip())
            src.append(f"by_domain:{len(j)}")
        except Exception: pass
    if extra_path and os.path.exists(extra_path):
        n = 0
        for l in open(extra_path, encoding="utf-8"):
            l = l.strip().lower()
            if l: ex.add(l); n += 1
        src.append(f"{os.path.basename(extra_path)}:{n}")
    return ex, src


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--cities", default="")
    ap.add_argument("--priority", type=int, default=0)
    ap.add_argument("--max-calls", type=int, default=1500,
                    help="cap for THIS run (default 1500)")
    ap.add_argument("--monthly-cap", type=int, default=MONTHLY_CAP,
                    help="cap across ALL runs this calendar month")
    ap.add_argument("--exclude-file", default="")
    ap.add_argument("--output", default=DEFAULT_OUT)
    a = ap.parse_args()

    sel = dict(CITIES)
    if a.cities:
        want = {c.strip().lower() for c in a.cities.split(",")}
        sel = {k: v for k, v in sel.items() if k.lower() in want}
        unknown = want - {k.lower() for k in CITIES}
        if unknown: print(f"unknown cities ignored: {sorted(unknown)}")
    if a.priority:
        sel = {k: v for k, v in sel.items() if v["priority"] == a.priority}
    if not sel: raise SystemExit("no cities selected")

    combos = [(c, m, q.format(city=c))
              for c, m in sorted(sel.items(), key=lambda x: (x[1]["priority"], x[0]))
              for q in QUERIES[:QUERIES_FOR[m["priority"]]]]

    print("=== Google Maps Tier 2/3 IT Company Discovery ===\n")
    if a.dry_run:
        print(f"cities {len(sel)} | city x query combos {len(combos)}")
        print(f"estimated calls: {len(combos)}–{len(combos)*PAGE_CAP} without tiling, "
              f"up to ~{len(combos)*PAGE_CAP*3} if tiles saturate")
        print(f"budget cap: {a.max_calls}\n")
        by = {}
        for c, m, q in combos: by.setdefault((m["priority"], c), []).append(q)
        for (pr, c), qs in sorted(by.items()):
            print(f"  P{pr} {c:20} {len(qs)} queries   {sel[c]['notes']}")
        ex, src = load_exclusions(a.exclude_file or None)
        print(f"\nexclusion set: {len(ex)} domains ({', '.join(src) or 'none'})")
        print("\nNo API calls made.")
        return

    headers, how = auth_headers()
    print(f"auth: {how}")
    cache = Cache(CACHE_DB)
    budget = BudgetTracker(a.max_calls, a.monthly_cap, cache.db)
    print(f"budget: {a.max_calls} this run | {a.monthly_cap} for {budget.month} "
          f"(already used {budget.month_start})")
    if not budget.can_call():
        raise SystemExit(f"MONTHLY cap already reached "
                         f"({budget.month_start}/{a.monthly_cap}) — no calls made.")
    s = Searcher(budget, cache, headers)

    raw, per_city = {}, {}
    for city, meta, q in combos:
        if not budget.can_call():
            print("\n!! budget cap reached — stopping"); break
        got = s.tile(q, meta["bbox"])
        new = 0
        for p in got:
            pid = p.get("id")
            if pid and pid not in raw:
                raw[pid] = (p, city); new += 1
        per_city[city] = per_city.get(city, 0) + new
        print(f"  {city:20} {q[:44]:46} {len(got):>3} results (+{new} new)", flush=True)
        if s.stopped:
            print("\n!! stopped early (budget or API error)"); break

    # ---- filter ----
    kept, reasons = [], {}
    for pid, (p, city) in raw.items():
        ok, why = keep(p)
        if not ok:
            reasons[why.split(":")[0]] = reasons.get(why.split(":")[0], 0) + 1
            continue
        kept.append((p, city))

    # ---- dedup by domain, then against what we already have ----
    by_dom, dom_dupes = {}, 0
    for p, city in kept:
        d = domain_of(p.get("websiteUri"))
        if d in by_dom: dom_dupes += 1; continue
        by_dom[d] = (p, city)
    ex, exsrc = load_exclusions(a.exclude_file or None)
    net = {d: v for d, v in by_dom.items() if d not in ex}
    excluded = len(by_dom) - len(net)

    # ---- write ----
    os.makedirs(os.path.dirname(a.output), exist_ok=True)
    now = datetime.datetime.now().isoformat(timespec="seconds")
    with open(a.output, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["company_name", "domain", "office_phone", "address", "city",
                    "rating", "review_count", "place_id", "source", "discovered_at"])
        for d, (p, city) in sorted(net.items()):
            w.writerow([clean_name((p.get("displayName", {}) or {}).get("text", "")), d,
                        p.get("nationalPhoneNumber", "") or "", p.get("formattedAddress", "") or "",
                        city, p.get("rating", "") or "", p.get("userRatingCount", "") or "",
                        p.get("id", ""), "google_maps", now])

    print(f"\nAPI calls this run:  {budget.calls_made:,} / {a.max_calls:,}")
    print(f"Calls in {budget.month}:     {budget.month_total:,} / {a.monthly_cap:,} monthly cap")
    if budget.stop_reason(): print(f"Stopped on:          {budget.stop_reason()}")
    print(f"Cities searched:     {len(per_city)}")
    print(f"Queries executed:    {len(combos)}")
    print(f"Raw results:         {len(raw):,}")
    print(f"After noise filter:  {len(kept):,}")
    print(f"After domain dedup:  {len(by_dom):,}  (-{dom_dupes} same-domain)")
    print(f"After exclusions:    {len(net):,} net-new  (-{excluded} already known)")
    if reasons:
        print("\nDropped by filter:")
        for k, v in sorted(reasons.items(), key=lambda x: -x[1]): print(f"  {v:>5}  {k}")
    print(f"\nOutput: {a.output} ({len(net)} rows)")
    if per_city:
        print("\nTop cities by yield:")
        cnt = {}
        for d, (p, city) in net.items(): cnt[city] = cnt.get(city, 0) + 1
        for c, n in sorted(cnt.items(), key=lambda x: -x[1])[:12]: print(f"  {c:20} {n:>4} firms")


if __name__ == "__main__":
    main()
