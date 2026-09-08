# -*- coding: utf-8 -*-
"""LH2 pre-qualification scorecard (filterCriteria.md) — 6 criteria, max 66 points.

Purpose: stop spending Discovery calls on leads that were never going to clear the LOC/PR
gate. Everything here is answerable from public sources BEFORE any outreach.

    Criterion                        Max   Automatable here?
    Total funding raised              12   yes  — seeds/Tracxn funding figure
    Years operated before shutdown    12   yes  — CIN incorporation year -> shutdown_date
    Peak engineering headcount        12   NO   — LinkedIn alumni search, forbidden by §10
    Sector / product type             10   yes  — sector text classifier
    Code location & git history       15   yes  — GitHub org/repo search (public API)
    Legal status confirmation          5   yes  — MCA status we already hold

UNSCORED IS NOT ZERO. The scorecard is explicit that "unscored" and "disqualifying" must
not collapse into the same bucket, so every row carries `prequal_unscored` (which criteria
had no data) and `prequal_max_possible` (66 minus the unscored weights). A lead sitting at
20/36 with headcount and GitHub unknown is a research gap, not a rejection — the routing
column says so in words.
"""
from __future__ import annotations
import re, json
from typing import Optional

MAX_TOTAL = 66
WEIGHTS = {"funding": 12, "years": 12, "eng_headcount": 12, "sector": 10,
           "code_location": 15, "legal_status": 5}

# Backend-heavy: real server-side systems worth buying. Frontend-thin: a brochure site.
BACKEND_HEAVY = (
    "fintech", "payments", "lending", "insurtech", "banking", "logistics", "supply chain",
    "freight", "warehous", "healthtech", "health tech", "diagnostic", "telemedicine",
    "b2b saas", "saas", "enterprise", "infrastructure", "infra", "devtools", "developer",
    "api", "cloud", "data", "analytics", "marketplace", "aggregator", "erp", "crm",
    "hrtech", "proptech", "agritech", "mobility", "ride", "delivery", "commerce platform",
    "cybersecurity", "security", "blockchain", "iot",
)
MIXED = ("food delivery", "ride-hailing", "quick commerce", "grocery", "consumer app",
         "social", "gaming", "edtech", "e-commerce", "ecommerce", "travel", "fitness")
FRONTEND_THIN = ("d2c", "direct to consumer", "brand", "apparel", "fashion label",
                 "agency", "marketing", "listing", "booking site", "directory",
                 "content", "media", "blog", "cosmetics", "jewellery", "jewelry")

DISTRESS_STATUSES = ("struck off", "strike off", "under liquidation", "dissolved",
                     "under cirp", "dissolved-liquidated", "under process of striking off")


def score_funding(usd) -> Optional[int]:
    """0-12. Bootstrapped genuinely scores 0 — that is a real signal, not missing data."""
    if usd in (None, "", "unknown"): return None
    try: v = float(str(usd).replace(",", "").replace("$", ""))
    except Exception: return None
    if v <= 0: return 0
    if v < 500_000: return 2
    if v < 2_000_000: return 5
    if v < 10_000_000: return 10
    return 12


def score_years(inc_year: Optional[int], shutdown_year: Optional[int]) -> Optional[int]:
    if not inc_year or not shutdown_year: return None
    yrs = shutdown_year - inc_year
    if yrs < 0: return None
    if yrs < 1.5: return 0
    if yrs < 3: return 4
    if yrs < 5: return 9
    return 12


def score_eng_headcount(n: Optional[int]) -> Optional[int]:
    """Only scores if a headcount was supplied MANUALLY. We do not scrape LinkedIn (§10)."""
    if n in (None, ""): return None
    n = int(n)
    if n <= 0: return None
    if n <= 4: return 1
    if n <= 14: return 6
    if n <= 30: return 10
    return 12


def score_sector(text: str) -> Optional[int]:
    """Order matters: the MIXED and FRONTEND_THIN lists hold the more specific phrases.

    "Food delivery" must score 6, not 10 — but bare "delivery" is in BACKEND_HEAVY because
    B2B logistics genuinely is backend-heavy. Testing the specific phrases first is what
    keeps a consumer food app from being scored like a freight platform.
    """
    if not text or not text.strip(): return None
    t = text.lower()
    if any(k in t for k in MIXED): return 6
    if any(k in t for k in FRONTEND_THIN): return 0
    if any(k in t for k in BACKEND_HEAVY): return 10
    return None


def score_code_location(gh: Optional[dict]) -> Optional[int]:
    """gh from github_lookup(). None => never looked; {} => looked, found nothing."""
    if gh is None: return None
    if not gh.get("found"): return 0
    if gh.get("history_deep"): return 15
    if gh.get("history_shallow"): return 5
    return 3


def score_legal(status: Optional[str]) -> int:
    """Not-checked is 0 and explicitly NEUTRAL, never a penalty."""
    s = (status or "").lower()
    return 5 if any(d in s for d in DISTRESS_STATUSES) else 0


def route(total: int, unscored: list) -> tuple[str, str]:
    if total >= 45:
        return ("fast_track", "Fast-track straight to Discovery call — skip the cold-call gate.")
    if total >= 25:
        return ("cold_call_first",
                "GTM cold-call first. The PR-process gate question is MANDATORY: 'did your "
                "team use pull requests and code review, or mostly direct commits?' A bad "
                "answer is a same-call disqualification.")
    if unscored:
        return ("dont_pursue_but_unscored",
                f"Below 25, BUT {len(unscored)} criteria were unscored ({', '.join(unscored)}). "
                f"This is a research gap, not a weak lead — resolve those before deprioritising.")
    return ("dont_pursue", "Deprioritise — genuinely weak across scored criteria.")


def score(*, funding_usd=None, inc_year=None, shutdown_year=None, eng_headcount=None,
          sector_text=None, github=None, company_status=None) -> dict:
    parts = {
        "funding": score_funding(funding_usd),
        "years": score_years(inc_year, shutdown_year),
        "eng_headcount": score_eng_headcount(eng_headcount),
        "sector": score_sector(sector_text),
        "code_location": score_code_location(github),
        "legal_status": score_legal(company_status),
    }
    unscored = [k for k, v in parts.items() if v is None]
    total = sum(v for v in parts.values() if v is not None)
    max_possible = MAX_TOTAL - sum(WEIGHTS[k] for k in unscored)
    r, why = route(total, unscored)
    return {"prequal_total": total, "prequal_max_possible": max_possible,
            "prequal_pct": round(100 * total / max_possible, 1) if max_possible else 0.0,
            "prequal_routing": r, "prequal_note": why,
            "prequal_unscored": ",".join(unscored),
            **{f"pq_{k}": ("" if v is None else v) for k, v in parts.items()}}


# ------------------------------------------------------------------ GitHub
_BAD_ORG = re.compile(r"(?i)\b(test|demo|sample|awesome|tutorial)\b")


async def github_lookup(http, company: str, token: Optional[str] = None) -> Optional[dict]:
    """Public GitHub search. Returns {} shape; never raises.

    'history_deep' is inferred from repo count + age, not from cloning — we are not going
    to clone hundreds of repos to score a lead. It is a pre-call proxy, and the scorecard
    treats it as one.
    """
    q = re.sub(r"[^A-Za-z0-9 ]", " ", company or "").strip()
    if len(q) < 3: return {"found": False}
    url = f"https://api.github.com/search/users?q={q.replace(' ', '+')}+type:org&per_page=5"
    d = await http.get_json(url)
    # CRITICAL: distinguish "searched, found nothing" from "could not search".
    # GitHub's unauthenticated search API allows ~10 req/min; a rate-limited call returns
    # nothing, and scoring that as 0 would brand a company as having no public code when
    # we simply never looked. Returning None keeps the criterion UNSCORED, which the
    # scorecard insists must not collapse into "disqualifying".
    if d is None:
        return None
    if not d.get("items"):
        return {"found": False}
    org = None
    for it in d["items"]:
        login = it.get("login") or ""
        if _BAD_ORG.search(login): continue
        if q.lower().replace(" ", "") in login.lower().replace("-", "").replace("_", ""):
            org = it; break
    if not org:
        return {"found": False}
    repos = await http.get_json(
        f"https://api.github.com/orgs/{org['login']}/repos?per_page=100&sort=pushed")
    if repos is None:
        # org found but repo listing rate-limited: we know code exists, not how deep
        return {"found": True, "org": org["login"], "repos": None,
                "history_shallow": False, "history_deep": False,
                "url": f"https://github.com/{org['login']}"}
    if not isinstance(repos, list) or not repos:
        return {"found": True, "org": org["login"], "repos": 0,
                "history_shallow": True, "history_deep": False}
    n = len(repos)
    # a real engineering org has several repos with a spread of creation dates
    years = {(r.get("created_at") or "")[:4] for r in repos if r.get("created_at")}
    deep = n >= 3 and len(years) >= 2
    return {"found": True, "org": org["login"], "repos": n,
            "years_span": len(years), "history_deep": deep,
            "history_shallow": not deep,
            "url": f"https://github.com/{org['login']}"}
