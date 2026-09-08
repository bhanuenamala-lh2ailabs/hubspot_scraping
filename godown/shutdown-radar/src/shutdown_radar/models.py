# -*- coding: utf-8 -*-
"""Normalisation, the shutdown regex, and CIN decoding.

The CIN is the quiet win here. The spec assumed state/class/registration-year were
unavailable (data.gov.in exposes only five fields), but a CIN encodes three of them
directly:

    U 18100 AP 1992 PTC 014997
    │ │     │  │    │   └ registration number
    │ │     │  │    └──── ownership class (PTC/PLC/OPC/FTC/NPL/SGC/GAP/GOI)
    │ │     │  └───────── year of incorporation
    │ │     └──────────── STATE code          <- registered_state
    │ └────────────────── NIC industry code
    └──────────────────── listed (L) / unlisted (U)

That is decoding an identifier, not inventing data, and it restores the disambiguation
the spec expected to lose.
"""
from __future__ import annotations
import re
from typing import Optional

CIN_RE = re.compile(r"\b([LUu])(\d{5})([A-Z]{2})(\d{4})([A-Z]{3})(\d{6})\b")
LLPIN_RE = re.compile(r"\b([A-Z]{3}-\d{4})\b")

STATE = {
    "AP": "Andhra Pradesh", "AR": "Arunachal Pradesh", "AS": "Assam", "BR": "Bihar",
    "CH": "Chandigarh", "CT": "Chhattisgarh", "GA": "Goa", "GJ": "Gujarat",
    "HR": "Haryana", "HP": "Himachal Pradesh", "JK": "Jammu and Kashmir", "JH": "Jharkhand",
    "KA": "Karnataka", "KL": "Kerala", "MP": "Madhya Pradesh", "MH": "Maharashtra",
    "MN": "Manipur", "ML": "Meghalaya", "MZ": "Mizoram", "NL": "Nagaland",
    "OR": "Odisha", "OD": "Odisha", "PB": "Punjab", "PY": "Puducherry", "RJ": "Rajasthan",
    "SK": "Sikkim", "TN": "Tamil Nadu", "TG": "Telangana", "TR": "Tripura",
    "UP": "Uttar Pradesh", "UT": "Uttarakhand", "UK": "Uttarakhand", "WB": "West Bengal",
    "DL": "Delhi", "AN": "Andaman and Nicobar Islands", "DN": "Dadra and Nagar Haveli",
    "DD": "Daman and Diu", "LD": "Lakshadweep", "LA": "Ladakh", "FLC": "Foreign",
}
CLASS = {"PTC": "Private", "PLC": "Public", "OPC": "One Person Company",
         "FTC": "Subsidiary of Foreign Company", "NPL": "Not for Profit",
         "SGC": "State Govt Company", "GAP": "Govt of India / State Govt",
         "GOI": "Union Govt Company", "ULL": "Unlimited Liability",
         "ULT": "Unlimited Liability"}


def decode_cin(cin: str) -> dict:
    m = CIN_RE.search((cin or "").upper())
    if not m: return {}
    listed, nic, st, yr, cls, _num = m.groups()
    return {"cin": m.group(0), "listed": listed == "L", "nic": nic,
            "state_code": st, "registered_state": STATE.get(st),
            "inc_year": int(yr), "date_of_registration": f"{yr}-01-01",
            "class_code": cls, "company_class": CLASS.get(cls, cls)}


_SUFFIX = re.compile(
    r"\b(pvt\.?|private|ltd\.?|limited|llp|inc\.?|incorporated|corp\.?|corporation|"
    r"technologies|technology|labs|laboratories|india|solutions|services|ventures|"
    r"enterprises|industries|holdings|group|company|co\.?)\b", re.I)
_PUNCT = re.compile(r"[^a-z0-9 ]+")

GENERIC_BLOCK = {
    "", "indian startups", "indian startup", "startups", "startup", "edtech firms",
    "edtech startups", "fintech startups", "companies", "company", "firms", "the company",
    "this startup", "another startup", "many startups", "several startups", "india",
    "indian", "more startups", "these startups", "two startups", "top startups",
}


def norm_name(s: str) -> str:
    """Lowercase, strip legal suffixes and punctuation, collapse whitespace."""
    s = (s or "").lower().replace("&", " and ")
    s = _PUNCT.sub(" ", s)
    s = _SUFFIX.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


SHUTDOWN_RE = re.compile(
    r"shuts?\s+(down|shop)|shut\s+down|shutting\s+down|ceas(e|ed|es|ing)\s+operations|"
    r"winds?\s+(up|down)|wound\s+up|shutter(s|ed)?|discontinu(e|ed|ing)\s+operations|"
    r"files?\s+for\s+(insolvency|bankruptcy)|insolvency\s+proceedings|NCLT|CIRP|"
    r"liquidation|struck\s+off|strike[- ]off|voluntary\s+winding\s+up|"
    r"returns?\s+capital\s+to\s+investors|shuts?\s+operations|"
    r"lays?\s+off\s+(entire|all)\s+(team|staff)|deadpool(ed)?|"
    r"bites?\s+the\s+dust|calls?\s+it\s+quits|pulls?\s+the\s+plug|closes?\s+shop",
    re.I)

# The brand is the noun phrase immediately before the trigger verb.
_LEAD = re.compile(
    r"([A-Z][\w&.'-]*(?:\s+[A-Z][\w&.'-]*){0,3})\s+(?=(?:has\s+|is\s+|to\s+|will\s+)?"
    r"(?:shut|shuts|shutting|ceas|wind|wound|shutter|discontinu|file|files|lay|lays|"
    r"call|calls|pull|pulls|close|closes|bite|bites))")

REPUTABLE = {"inc42", "entrackr", "yourstory", "moneycontrol", "livemint", "mint",
             "vccircle", "economictimes", "et tech", "business-standard",
             "businessstandard", "financialexpress", "thehindubusinessline",
             "techcrunch", "the ken", "theken", "medianama", "bloomberg", "reuters"}


# A headline about a *category* rather than a company. "Edtech firms wind up" names no
# brand, and letting it through creates a candidate called "Edtech firms" that then fuzzy-
# matches some real company. Cheaper to reject the whole class than to clean up after it.
_GENERIC_HEAD = re.compile(
    r"\b(startups?|firms?|companies|company|ventures?|brands?|players?|unicorns?|"
    r"businesses|entities|founders?|investors?)$", re.I)


def extract_brand(title: str) -> Optional[str]:
    """Pull the brand out of a headline. None when it names a category, not a company."""
    if not title: return None
    title = re.sub(r"^(exclusive|breaking|report|update)\s*[:\-]\s*", "", title, flags=re.I)
    m = _LEAD.search(title)
    if m:
        cand = m.group(1)
    else:
        # no capitalised run before the verb — fall back to whatever precedes the trigger,
        # never to the whole headline
        t = SHUTDOWN_RE.search(title)
        cand = title[:t.start()] if t else title.split(":")[0]
    cand = cand.strip(" .,:-")
    n = norm_name(cand)
    if not n or len(n) < 3: return None
    if n in GENERIC_BLOCK: return None
    if _GENERIC_HEAD.search(cand.strip()): return None
    if len(n.split()) > 5: return None
    return cand


def is_reputable(source_name: str) -> bool:
    s = (source_name or "").lower()
    return any(r in s for r in REPUTABLE)
