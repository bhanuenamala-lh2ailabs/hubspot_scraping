# -*- coding: utf-8 -*-
"""Score how likely a dead company owned a real codebase, and flag whether it was VC-funded.

Why this module exists: filtering by NIC alone does not work. NIC is a filing category, not
a fact about the business. Two failures in opposite directions:

  * TOO NARROW — NIC 62/63/72 ("software") captures IT-services firms and misses the entire
    consumer-tech universe. Dunzo files as courier, a fintech as financial services, an
    edtech as education. Those are exactly the big codebases.
  * TOO WIDE  — NIC 74 "other professional/technical" is India's junk-drawer code and the
    single largest division among struck-off companies (1,324). Accepting it wholesale buys
    volume by buying noise: JHAJJBAD PROJECTS, VEMRI INDIA OVERSEAS, APRIL INDUSTRIES.

So the score combines independent weak signals instead of trusting one strong-looking one,
and every row records WHY it scored what it did.

VC-funded is a FLAG, never a filter — both populations are wanted, they just get worked
differently. A funded shutdown carries 8-30M LOC; a bootstrapped dev shop carries far less
but is still a real asset.
"""
from __future__ import annotations
import re
from typing import Optional

# --- NIC divisions, graded by how strongly they imply a software product -----------------
NIC_STRONG = {          # unambiguously software
    "62": "computer programming / consultancy",
    "63": "information services",
    "72": "computer & related activities (older NIC vintage)",
    "58": "publishing, incl. software publishing",
}
NIC_SECTOR = {          # tech-ENABLED sector: the product is software even if the NIC is not
    "64": "financial services (fintech)", "65": "insurance (insurtech)",
    "66": "auxiliary financial (fintech)", "85": "education (edtech)",
    "86": "human health (healthtech)", "47": "retail (e-commerce)",
    "46": "wholesale (B2B marketplace)", "53": "postal & courier (delivery)",
    "49": "land transport (mobility)", "55": "accommodation (traveltech)",
    "56": "food service (foodtech)", "68": "real estate (proptech)",
    "79": "travel agency (traveltech)", "78": "employment (HRtech)",
    "61": "telecommunications", "59": "media production", "73": "advertising (adtech)",
}
NIC_WEAK = {            # junk-drawer codes: only counted if the NAME also says tech
    "74": "other professional/technical", "70": "management consultancy",
    "69": "legal/accounting", "82": "business support",
}
NAME_TECH = re.compile(
    r"(?i)\b(tech|technolog|soft|softwar|digital|labs?|online|app|web|data|ai|cloud|net|"
    r"info|system|solution|analytic|cyber|robot|smart|mobil|commerce|platform|innovat|"
    r"logic|byte|code|compu|interactive|studio|media|telecom|comput|infotech|sys)")
# names that look techy but are not — avoid false positives on these
NAME_TRAP = re.compile(r"(?i)\b(techn?o\s*(steel|pack|plast|chem|weav|fab)|infra|"
                       r"construct|realt|estate|mining|textile|agro|steel|cement)")


def nic_of(cin: str) -> Optional[str]:
    m = re.match(r"[LU](\d{5})", (cin or "").upper())
    return m.group(1)[:2] if m else None


def class_of(cin: str) -> Optional[str]:
    m = re.match(r"[LU]\d{5}[A-Z]{2}\d{4}([A-Z]{3})", (cin or "").upper())
    return m.group(1) if m else None


def inc_year_of(cin: str) -> Optional[int]:
    m = re.match(r"[LU]\d{5}[A-Z]{2}(\d{4})", (cin or "").upper())
    return int(m.group(1)) if m else None


def score(cin: str, legal_name: str, died_year: Optional[int] = None) -> dict:
    """-> {codebase_score 0-100, codebase_band, reasons[]}"""
    pts, why = 0, []
    nic = nic_of(cin)
    name = legal_name or ""
    name_tech = bool(NAME_TECH.search(name)) and not NAME_TRAP.search(name)

    if nic in NIC_STRONG:
        pts += 40; why.append(f"NIC {nic}: {NIC_STRONG[nic]}")
    elif nic in NIC_SECTOR:
        pts += 22; why.append(f"NIC {nic}: {NIC_SECTOR[nic]} — sector runs on software")
    elif nic in NIC_WEAK:
        # a junk-drawer code counts for nothing on its own
        if name_tech:
            pts += 10; why.append(f"NIC {nic} ({NIC_WEAK[nic]}) — generic, but the name reads tech")
        else:
            why.append(f"NIC {nic} ({NIC_WEAK[nic]}) — generic filing code, no signal")
    elif nic:
        why.append(f"NIC {nic}: not a software-producing sector")

    if name_tech:
        pts += 25; why.append("company name carries a technology marker")
    elif NAME_TRAP.search(name):
        why.append("name looks techy but reads as industrial/infra — discounted")

    iy = inc_year_of(cin)
    if iy:
        if iy <= 2022:
            pts += 12; why.append(f"incorporated {iy} — pre-2024 code is in scope")
        else:
            pts -= 15; why.append(f"incorporated {iy} — too new to hold pre-2024 code")
        if died_year and died_year - iy >= 3:
            pts += 13; why.append(f"operated ~{died_year - iy} years — long enough to build something")
        elif died_year and died_year - iy < 2:
            pts -= 8; why.append(f"operated under 2 years — little time to build")

    cls = class_of(cin)
    if cls in ("PTC", "PLC"):
        pts += 10; why.append(f"{cls}: a real company, not a one-person shell")
    elif cls == "OPC":
        pts -= 12; why.append("OPC: one-person company — rarely ships a product")

    pts = max(0, min(100, pts))
    band = ("likely" if pts >= 60 else "possible" if pts >= 35 else
            "unlikely" if pts >= 15 else "no")
    return {"codebase_score": pts, "codebase_band": band, "codebase_reasons": "; ".join(why)}


# ------------------------------------------------------------------ VC funding flag
_SUF = re.compile(r"\b(private|limited|pvt|ltd|llp|technologies|technology|solutions|"
                  r"india|services|labs|ventures|enterprises|company|co)\b")


def match_key(s: str) -> str:
    s = re.sub(r"[^a-z0-9 ]", " ", str(s or "").lower())
    s = _SUF.sub(" ", s)
    return re.sub(r"\s+", " ", s).strip()


def build_funding_index(tracxn_rows) -> dict:
    """key -> {funded: bool, amount, investors, sector, deadpooled_date}"""
    out = {}
    for r in tracxn_rows:
        k = match_key(r.get("Company Name"))
        if not k or len(k) < 3: continue
        raw = str(r.get("Total Funding (USD)") or "").replace(",", "")
        m = re.match(r"[\d.]+", raw)
        amt = float(m.group(0)) if m else 0.0
        out[k] = {"funded": amt > 0, "amount": amt,
                  "investors": (r.get("Institutional Investors") or "")[:160],
                  "sector": (r.get("Sector (Pratice Area & Feed)") or "").split(">")[0].strip(),
                  "stage": r.get("Company Stage") or "",
                  "deadpooled": r.get("Deadpooled Date") or ""}
    return out


def _hit(h, how):
    return {"vc_funded": "yes" if h["funded"] else "checked_not_funded",
            "funding_usd": int(h["amount"]) if h["amount"] else "",
            "investors": h["investors"], "tracxn_sector": h["sector"],
            "tracxn_stage": h["stage"], "funding_source": how}


def vc_flag(legal_name: str, brand: str, idx: dict, keys=None, fuzz_min: int = 90) -> dict:
    """VC-funded is recorded, never used to include or exclude.

    Exact key matching alone under-reports badly. A registry legal name carries words the
    startup never used: "Wegilant Net Solutions Private Limited" reduces to `wegilant net`
    while Tracxn lists plain `Wegilant`; "Notion Ink Design Labs" vs `Notion Ink`. Both are
    genuinely VC-funded, and an exact match calls them unknown. So: exact, then leading-word
    prefixes, then a tight fuzzy pass. `unknown` must mean "no record found", not "our
    string handling was brittle".
    """
    for cand in (brand, legal_name):
        k = match_key(cand)
        if k and k in idx:
            return _hit(idx[k], "Tracxn exact")
    # progressive prefixes: "wegilant net" -> "wegilant"
    for cand in (legal_name, brand):
        parts = match_key(cand).split()
        for n in range(len(parts) - 1, 0, -1):
            k = " ".join(parts[:n])
            if len(k) >= 4 and k in idx:
                return _hit(idx[k], f"Tracxn prefix '{k}'")
    if keys:
        try:
            from rapidfuzz import process, fuzz as _f
            for cand in (brand, legal_name):
                k = match_key(cand)
                if len(k) < 5: continue
                m = process.extractOne(k, keys, scorer=_f.token_sort_ratio,
                                       score_cutoff=fuzz_min)
                if m:
                    return _hit(idx[m[0]], f"Tracxn fuzzy {m[1]:.0f}% -> '{m[0]}'")
        except ImportError:
            pass
    # STEP 2 — "unknown" was doing two jobs and hiding the answer to "would buying a fuller
    # Tracxn export even help?". Split it:
    #   checked_not_funded          present in Tracxn, no funding recorded -> a real NO
    #   unknown_no_tracxn_coverage  absent from our export entirely -> coverage gap
    # If the second bucket dominates, more Tracxn coverage would move the needle. If the
    # first does, it would not.
    return {"vc_funded": "unknown_no_tracxn_coverage", "funding_usd": "", "investors": "",
            "tracxn_sector": "", "tracxn_stage": "",
            "funding_source": "company absent from our Tracxn export — coverage gap, "
                              "not evidence of being bootstrapped"}

# ---------------------------------------------------------------- title cleanliness
"""Can the person we call actually SIGN a transfer of the repo?

Deliberately kept OUT of codebase_score. Codebase plausibility asks "is there an asset";
this asks "is the asset transferable by the person answering the phone". They are
independent, and at a $5-20k ticket the second one decides whether a deal closes at all.

The ranking is the inverse of prestige:

  voluntary_clean   the company APPLIED to be struck off (form STK-2 under s.248(2)) and is
                    a small private/one-person company with no institutional investors.
                    One or two owners, no board, no liquidator. Verified: every STK file we
                    hold cites STK-2, so our whole strike-off set took the voluntary route.
  clean             struck off, no insolvency proceeding, but larger or public class.
  consent_risk      institutional investors on the cap table. Their consent rights and
                    liquidation preferences frequently survive the operating company, and
                    IP was assigned to the entity, not the founder.
  encumbered        IBBI CIRP / liquidation. A liquidator controls the estate; the founder
                    legally CANNOT sell the repo however willing they are. Hardest to close
                    despite often being the most recognisable name.
"""
CLEANLINESS_RANK = {"voluntary_clean": 0, "clean": 1, "consent_risk": 2, "encumbered": 3}

# PROVENANCE for `voluntary_clean` — verified 2026-08-05, recorded so it is never treated
# as an unexamined assumption:
#
#   All source notices are issued by ROC/C-PACE and cite s.248(5) of the Companies Act 2013
#   with a Form STK-2 reference in each per-state notice. Exhaustive scan of every page of
#   all 12 PDFs: 1,626 occurrences of 248(5)/sub-section (5), 1,017 of STK-2, and ZERO of
#   248(1), 248(2) or any suo-motu / own-motion language. The operative sentence — "this is
#   with respect to this Office Notice Nos and application (Form STK 2) vide SRNs as
#   mentioned in the Annexure-A" — appears in 329 separate per-state notices, so it is an
#   operative per-notice statement, not template preamble. C-PACE exists specifically to
#   process voluntary exits, so these batches are not a random sample of Indian strike-offs.
#
#   UNVERIFIED INFERENCE: the Annexure-A column labelled "Work Item" is ASSUMED to be the
#   STK-2 SRN. The PDFs never state this. Not confirmed against an MCA SRN lookup.
#   OPEN ITEM: sample ~20 Work Item numbers against MCA SRN lookup to close this. Logged
#   in RESUME_HERE.md; not blocking, but the assumption should not be forgotten.
VOLUNTARY_CLEAN_BASIS = (
    "voluntary_clean basis: all source notices issued by ROC/C-PACE citing s.248(5) with "
    "Form STK-2 reference per notice (329 notices); zero s.248(1) or suo motu language in "
    "corpus. Unverified inference: Annexure-A 'Work Item' assumed to be the STK-2 SRN. "
    "Not confirmed against MCA SRN lookup.")


def title_cleanliness(*, death_status: str, cin: str, investors: str = "",
                      vc_funded: str = "", via_stk2: bool = True) -> dict:
    st = (death_status or "").lower()
    cls = class_of(cin)
    why = []
    if "ibbi" in st or "liquidat" in st or "cirp" in st:
        why.append("IBBI CIRP/liquidation — a liquidator controls the estate, the founder "
                   "cannot transfer the repo")
        return {"title_cleanliness": "encumbered", "title_rank": 3,
                "title_reasons": "; ".join(why)}
    if (investors or "").strip():
        why.append(f"institutional investors on record ({investors[:60]}) — consent rights "
                   f"and liquidation preferences may survive the entity")
        return {"title_cleanliness": "consent_risk", "title_rank": 2,
                "title_reasons": "; ".join(why)}
    if vc_funded == "yes":
        why.append("VC-funded — cap-table consent risk even though no investor is named")
        return {"title_cleanliness": "consent_risk", "title_rank": 2,
                "title_reasons": "; ".join(why)}
    if "struck off" in st or "strike off" in st:
        if via_stk2: why.append("voluntary strike-off via form STK-2 (the company applied)")
        else: why.append("strike-off, no insolvency proceeding")
        if cls in ("PTC", "OPC"):
            why.append(f"{cls}: small private company — one or two owners can sign")
            return {"title_cleanliness": "voluntary_clean", "title_rank": 0,
                    "title_reasons": "; ".join(why)}
        why.append(f"class {cls or '?'} — larger/public, expect more signatories")
        return {"title_cleanliness": "clean", "title_rank": 1, "title_reasons": "; ".join(why)}
    why.append("no registry death evidence — title route unknown")
    return {"title_cleanliness": "unknown", "title_rank": 4, "title_reasons": "; ".join(why)}
