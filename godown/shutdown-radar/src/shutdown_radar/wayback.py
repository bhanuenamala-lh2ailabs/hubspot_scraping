# -*- coding: utf-8 -*-
"""Wayback CDX pass: did this dead company ever actually SHIP software?

The registry tells us a company existed and died. It says nothing about whether it built a
product. A site archived for four years with /login, /api and /pricing shipped something.
A site with three captures of a one-page template did not.

A HARD CONSTRAINT, stated up front because it shapes what the output means: only 2 of the
2,989 rows carry a known domain. For the rest the domain is GUESSED from the legal name
("ZILIGENCE INFOTECH PRIVATE LIMITED" -> ziligence.com / ziligence.in / ...). Therefore:

    a HIT  is strong positive evidence — that domain really was archived
    a MISS is AMBIGUOUS — wrong guess, or genuinely no site. We cannot tell which.

So the negative verdict is `domain_not_found`, never "no web presence". Treating a failed
guess as proof of absence would be the same unscored-vs-disqualifying collapse we avoid
everywhere else in this pipeline.

Polite: 1 request/sec against CDX, every response cached to disk, checkpointed per company
so a re-run resumes rather than re-querying.
"""
from __future__ import annotations
import os, re, json, time, hashlib, urllib.request, urllib.error
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CACHE = os.path.join(ROOT, ".cache", "wayback")
os.makedirs(CACHE, exist_ok=True)
UA = "shutdown-radar/1.0 (research bot; contact rahul.dhali@lh2holdings.com)"

# paths that only exist if software was actually running
APP_PATHS = {
    "login": r"/(login|signin|sign-in|auth|account/login)",
    "dashboard": r"/(dashboard|console|portal|workspace|admin)",
    "app": r"/(app|application)(/|$|\.)",
    "api": r"/(api|v1|v2|graphql|swagger)(/|$)",
    "docs": r"/(docs|documentation|developer|developers|api-docs)",
    "signup": r"/(signup|sign-up|register|get-started|onboarding)",
    "pricing": r"/(pricing|plans|subscribe|billing)",
    "careers": r"/(careers|jobs|hiring|work-with-us|join-us)",
}
# a site builder means someone bought a template, not that they built software
BUILDER = re.compile(r"(?i)(wix\.com|squarespace|godaddysites|weebly|wordpress\.com|"
                     r"blogspot|business\.site|webnode|strikingly|carrd\.co)")
PARKED = re.compile(r"(?i)(sedoparking|afternic|hugedomains|parkingcrew|bodis|"
                    r"domainmarket|buydomains|namecheap.*parking)")

# Single dictionary words are almost always owned by someone else. "Swift Shipping and
# Freight Logistics" -> swift.com is SWIFT the banking network, archived since 1997.
# Measured on a 25-row sample: guessing on these produced a 100% "hit" rate with 25-29 year
# capture spans — i.e. every hit was a different company. A stem must be distinctive.
GENERIC_STEM = {
    "swift","capital","revive","anil","ichi","vishi","arches","propack","seatel","yeta",
    "rivos","dacso","apex","alpha","beta","delta","omega","prime","global","united","royal",
    "star","sun","moon","eagle","tiger","lion","smart","super","mega","ultra","max","pro",
    "next","first","best","top","new","modern","classic","premier","elite","noble","grand",
    "shine","spark","bright","clear","pure","fresh","green","blue","red","silver","gold",
    "diamond","crystal","pearl","ruby","amber","cloud","data","tech","soft","info","system",
    "solution","service","digital","media","design","studio","labs","works","group","trust",
    "care","health","life","home","food","auto","power","energy","build","craft","trade",
}

_SUFFIX = re.compile(
    r"\b(private|limited|pvt|ltd|llp|inc|incorporated|corp|corporation|company|co|"
    r"opc|india|indian)\b", re.I)
TLDS = (".com", ".in", ".co.in", ".net", ".io", ".tech", ".org")


def candidate_domains(legal_name: str, max_n: int = 3, _stats: dict = None) -> list[str]:
    """'ZILIGENCE INFOTECH PRIVATE LIMITED' -> ziligence.com, ziligenceinfotech.com, ziligence.in"""
    n = re.sub(r"\([^)]*\)", " ", legal_name or "")
    n = re.sub(r"[^A-Za-z0-9 ]", " ", n)
    n = _SUFFIX.sub(" ", n)
    words = [w.lower() for w in n.split() if len(w) > 1]
    if not words: return []
    out = []
    joined = "".join(words)
    first = words[0]
    for stem in dict.fromkeys([joined, "".join(words[:2]), first]):
        if len(stem) < 5 or len(stem) > 28: continue
        if stem in GENERIC_STEM:                   # a word someone else owns
            if _stats is not None: _stats["generic_stem_blocked"] = stem
            continue
        for t in (".com", ".in"):
            out.append(stem + t)
    return out[:max_n]


def _cache_path(url: str) -> str:
    return os.path.join(CACHE, hashlib.sha256(url.encode()).hexdigest() + ".json")


def cdx(domain: str, limit: int = 400, delay: float = 1.0) -> Optional[list]:
    """Distinct archived URLs for a domain. None on error, [] when genuinely empty."""
    url = (f"http://web.archive.org/cdx/search/cdx?url={domain}&matchType=domain"
           f"&output=json&fl=timestamp,original,statuscode&collapse=urlkey&limit={limit}")
    cp = _cache_path(url)
    if os.path.exists(cp):
        try: return json.load(open(cp, encoding="utf-8"))
        except Exception: pass
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                rows = json.loads(r.read().decode() or "[]")
            json.dump(rows, open(cp, "w", encoding="utf-8"))
            time.sleep(delay)
            return rows
        except urllib.error.HTTPError as e:
            if e.code in (429, 503): time.sleep(8 * (attempt + 1)); continue
            time.sleep(delay); return None
        except Exception:
            if attempt < 2: time.sleep(4); continue
            return None
    return None


def analyse(rows: list) -> dict:
    """rows = CDX output incl. header. -> capture stats + product signals."""
    if not rows or len(rows) < 2:
        return {"captures": 0}
    body = rows[1:] if rows and rows[0] and rows[0][0] == "timestamp" else rows
    ts = sorted(r[0] for r in body if r and r[0] and r[0][:4].isdigit())
    urls = [r[1] for r in body if len(r) > 1 and r[1]]
    if not ts: return {"captures": 0}
    first, last = ts[0], ts[-1]
    span_days = 0
    try:
        import datetime
        d1 = datetime.datetime.strptime(first[:8], "%Y%m%d")
        d2 = datetime.datetime.strptime(last[:8], "%Y%m%d")
        span_days = (d2 - d1).days
    except Exception: pass
    blob = " ".join(urls).lower()
    hits = sorted(k for k, pat in APP_PATHS.items() if re.search(pat, blob))
    return {
        "captures": len(body),
        "distinct_urls": len(set(urls)),
        "first_capture": f"{first[:4]}-{first[4:6]}-{first[6:8]}",
        "last_capture": f"{last[:4]}-{last[4:6]}-{last[6:8]}",
        "span_days": span_days,
        "span_years": round(span_days / 365.25, 1),
        "app_signals": hits,
        "builder": bool(BUILDER.search(blob)),
        "parked": bool(PARKED.search(blob)),
    }


def verdict(a: dict) -> dict:
    """-> {product_evidence, product_score, product_reasons}"""
    if not a or not a.get("captures"):
        return {"product_evidence": "domain_not_found", "product_score": 0,
                "product_reasons": "no archived captures for any guessed domain — "
                                   "AMBIGUOUS: the guess may simply be wrong"}
    pts, why = 0, []
    sig = a.get("app_signals") or []
    strong = [s for s in sig if s in ("login", "dashboard", "app", "api", "docs", "signup")]
    if strong:
        pts += 18 * min(3, len(strong))
        why.append(f"app paths archived: {', '.join(strong)} — software was running")
    if "pricing" in sig: pts += 8; why.append("pricing page — a commercial product")
    if "careers" in sig: pts += 6; why.append("careers page — was hiring")
    yrs = a.get("span_years", 0)
    if yrs >= 3: pts += 20; why.append(f"archived across {yrs}y — a site that persisted")
    elif yrs >= 1: pts += 10; why.append(f"archived across {yrs}y")
    else: why.append(f"archived only {yrs}y — barely existed")
    du = a.get("distinct_urls", 0)
    if du >= 40: pts += 15; why.append(f"{du} distinct URLs archived — a real site")
    elif du >= 10: pts += 8; why.append(f"{du} distinct URLs")
    elif du <= 2: pts -= 10; why.append(f"only {du} URL(s) archived — single page")
    if a.get("builder"): pts -= 20; why.append("site-builder signature — template, not software")
    if a.get("parked"): pts -= 25; why.append("parked-domain pattern")
    pts = max(0, min(100, pts))
    ev = ("verified_product" if pts >= 55 else
          "probable_product" if pts >= 30 else
          "brochure_only" if a.get("captures") else "domain_not_found")
    return {"product_evidence": ev, "product_score": pts, "product_reasons": "; ".join(why)}


def plausible_owner(a: dict, inc_year: Optional[int]) -> tuple[bool, str]:
    """Reject a domain whose archive predates the company. THE critical guard.

    Indian companies incorporated in 2018-2023 did not have websites in 1997. A first
    capture materially before incorporation means the domain belongs to someone else and
    every signal read off it is about a different business.
    """
    if not inc_year or not a.get("first_capture"): return True, ""
    try: fc = int(a["first_capture"][:4])
    except Exception: return True, ""
    if fc < inc_year - 1:
        return False, (f"archive starts {fc}, company incorporated {inc_year} — the domain "
                       f"predates the company, so it belongs to a different owner")
    return True, ""


def check(legal_name: str, known_domain: str = "", delay: float = 1.0,
          inc_year: Optional[int] = None) -> dict:
    doms = [known_domain] if known_domain else []
    _st = {}
    doms += [d for d in candidate_domains(legal_name, _stats=_st) if d != known_domain]
    best, best_dom, tried, rejected = {}, "", [], []
    errors = 0
    for d in doms:
        tried.append(d)
        rows = cdx(d, delay=delay)
        if rows is None:
            errors += 1     # network failure — NOT the same as "archive.org said nothing"
            continue
        a = analyse(rows)
        ok, why = plausible_owner(a, inc_year)
        if not ok:
            rejected.append(f"{d}: {why}")
            continue
        if a.get("captures", 0) > best.get("captures", 0):
            best, best_dom = a, d
        if best.get("captures", 0) >= 50: break     # good enough, stop guessing
    out = {"wayback_domain": best_dom, "domains_tried": ";".join(tried),
           "domains_rejected": " | ".join(rejected),
           "generic_stem_blocked": _st.get("generic_stem_blocked", ""),
           "lifetime_rejected": len(rejected), **best}
    out.update(verdict(best))
    if not best and rejected:
        out["product_reasons"] = ("all candidate domains rejected as belonging to a "
                                  "different owner: " + rejected[0])
    # If we never got an ANSWER for any candidate, we learned nothing. Reporting that as
    # domain_not_found would launder a network outage into evidence of absence — and the
    # caller checkpoints the verdict, so the row would never be retried. Mark it `error`
    # so the re-query pass picks it up.
    if not best and doms and errors == len(doms):
        out["product_evidence"] = "error"
        out["product_score"] = ""
        out["product_reasons"] = (f"no response from CDX for any of {len(doms)} candidate "
                                  f"domains ({errors} network failures) — UNKNOWN, not a miss")
    return out
