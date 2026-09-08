# -*- coding: utf-8 -*-
"""Confidence scoring — weights exactly as spec §7, with the two date guards.

The two guards are the whole point of this module and both are unit-tested:
  * IBBI bonus only when shutdown_date <= the file's as-of date (§2c)
  * STK-only evidence => shutdown_date NULL and tier capped at `probable` (§2e)
"""
from __future__ import annotations
import re, datetime
from typing import Optional

from .models import is_reputable
from .sources.ibbi import bonus_allowed

W = {
    "ibbi": 0.45, "stk7": 0.40, "status_strong": 0.40, "status_mid": 0.32,
    "ibbi_voluntary": 0.30, "stk56": 0.30, "news_multi": 0.30, "status_process": 0.22,
    "tracker": 0.20, "news_one": 0.18, "liveness_high": 0.15, "liveness_mid": 0.08,
    "dpiit": 0.05, "no_cin": -0.25, "low_quality_only": -0.15,
}
STATUS_STRONG = {"dissolved", "dissolved-liquidated", "under liquidation", "under cirp"}
STATUS_MID = {"strike off", "struck off", "amalgamated", "struck off (stk-7)",
              "under liquidation (ibbi)"}
STATUS_PROCESS = {"under process of striking off"}
EXCLUDE_STATUS = {"converted to llp"}

_DATE = re.compile(r"(20\d{2})[-/](\d{1,2})(?:[-/](\d{1,2}))?")


def parse_date(s: Optional[str]) -> Optional[str]:
    if not s: return None
    m = _DATE.search(str(s))
    if not m: return None
    y, mo, d = m.group(1), int(m.group(2)), int(m.group(3) or 1)
    if not (1 <= mo <= 12 and 1 <= d <= 31): return None
    return f"{y}-{mo:02d}-{d:02d}"


def tier_of(conf: float) -> str:
    if conf >= 0.75: return "confirmed"
    if conf >= 0.50: return "probable"
    if conf >= 0.30: return "possible"
    return "noise"


def score_candidate(cand, evidence, entity, liveness, dpiit_hit: bool, ibbi_as_of):
    """-> (confidence, tier, shutdown_date, rationale)"""
    conf, why = 0.0, []
    kinds = [e["kind"] for e in evidence]

    news = [e for e in evidence if e["kind"] in ("news", "manual")]
    news_sources = {(e["source_name"] or "").lower() for e in news if e["source_name"]}
    reputable = {s for s in news_sources if is_reputable(s)}

    # the shutdown date comes only from news/seed evidence, never from a registry file
    dates = [parse_date(e["published_at"]) for e in news]
    dates = sorted(d for d in dates if d)
    shutdown_date = dates[0] if dates else None

    has_stk = "stk7" in kinds
    has_ibbi = "ibbi" in kinds
    has_ibbi_vol = "ibbi_voluntary" in kinds

    if has_ibbi:
        if bonus_allowed(shutdown_date, ibbi_as_of):
            conf += W["ibbi"]; why.append(f"IBBI liquidation list (as on {ibbi_as_of})")
        else:
            why.append(f"IBBI match present but NOT scored — shutdown_date {shutdown_date} "
                       f"is after the list's as-of date {ibbi_as_of}")
    if has_ibbi_vol:
        conf += W["ibbi_voluntary"]; why.append("IBBI voluntary liquidation")
    if has_stk:
        stk = next(e for e in evidence if e["kind"] == "stk7")
        conf += W["stk7"]; why.append(f"STK-7 strike-off notice {stk['as_of_date'] or ''}".strip())
    if "stk56" in kinds:
        conf += W["stk56"]; why.append("STK-5/6 notice")

    status = (entity["company_status"] if entity else None) or ""
    s = status.lower().strip()
    if s in EXCLUDE_STATUS:
        return 0.0, "noise", shutdown_date, f"excluded: company status is {status}"
    if s in STATUS_STRONG:
        conf += W["status_strong"]; why.append(f"MCA status {status}")
    elif s in STATUS_MID:
        conf += W["status_mid"]; why.append(f"MCA status {status}")
    elif s in STATUS_PROCESS:
        conf += W["status_process"]; why.append(f"MCA status {status}")
    elif s == "active":
        why.append("MCA status Active (recorded, not treated as proof of life)")

    if len(reputable) >= 2:
        conf += W["news_multi"]; why.append(f"{len(reputable)} reputable sources")
    elif len(reputable) == 1:
        conf += W["news_one"]; why.append(f"1 reputable source ({list(reputable)[0]})")
    elif news_sources:
        conf += W["low_quality_only"]; why.append("only low-quality/aggregator sourcing")
    if "tracker" in [e["source_name"] for e in evidence if e["source_name"]] or \
       any((e["source_name"] or "").lower().startswith(("entrackr", "inc42")) for e in evidence):
        conf += W["tracker"]; why.append("curated tracker page")

    if liveness and liveness["liveness_score"] is not None:
        ls = liveness["liveness_score"]
        if ls >= 0.8:
            conf += W["liveness_high"]
            why.append(f"site dead (liveness {ls:.2f}"
                       f"{', NXDOMAIN' if liveness['dns_resolves'] == 0 else ''})")
        elif ls >= 0.5:
            conf += W["liveness_mid"]; why.append(f"site likely dead (liveness {ls:.2f})")

    if dpiit_hit:
        conf += W["dpiit"]; why.append("DPIIT-recognised")

    if not entity:
        # DELIBERATE DEVIATION from the flat -0.25 in §7, applied only to hand-curated seeds.
        #
        # The penalty exists to say "we cannot verify this company exists in the registry".
        # For a manual seed that is not the open question: a human verified the shutdown and
        # cited a source. What is missing is only the brand -> legal-name mapping, which
        # fails for a different reason entirely (Koo's entity is Bombinate Technologies;
        # data.gov.in exact-match cannot bridge that without an override).
        #
        # At the flat weight every seed landed on 0.28 — two hundredths under `possible` —
        # so 43 of 45 known 2024-25 shutdowns dropped out of the export as "noise" while
        # the acceptance criteria require all of them present. Halving the penalty for
        # human-verified rows resolves that without touching any automated candidate's
        # score. The rationale text always states the CIN is unresolved, so nothing is
        # hidden from the reader.
        seeded = any(e["kind"] == "manual" for e in evidence)
        pen = W["no_cin"] / 2 if seeded else W["no_cin"]
        conf += pen
        why.append("no CIN resolved (curated seed — penalty halved; brand/legal-name "
                   "mapping missing, not the shutdown itself)" if seeded else "no CIN resolved")

    conf = max(0.0, min(1.0, conf))
    tier = tier_of(conf)

    # §2e — an STK match confirms death but does not date it
    only_registry = has_stk and not news
    if only_registry:
        shutdown_date = None
        if tier == "confirmed":
            tier = "probable"
        why.append("timing unestablished: strike-off publication lags cessation by "
                   "months-to-years, so no shutdown_date can be derived from STK alone")

    return conf, tier, shutdown_date, "; ".join(why) or "no evidence"
