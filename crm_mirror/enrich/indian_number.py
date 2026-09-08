# -*- coding: utf-8 -*-
"""THE Indian-number gate. One implementation, used by every push script.

HARD RULE (user, 2026-08-03): nothing reaches HubSpot without a valid Indian number.
Accepted forms:
    +91 followed by exactly 10 digits          e.g. +91 99162 62587
    a bare 10-digit Indian number              e.g. 9971045274
Everything else is REJECTED.

Why this is stricter than "10 digits":
  * An explicit foreign country code is rejected outright. Tracxn stores US numbers with
    no country code — `6464800503` is New York 646-480-0503, and a naive "10 digits
    starting 6-9" test stamps +91 on it and creates a bogus Indian number. So when the
    source gives us a country code we obey it; we never overwrite one.
  * Indian mobile numbering (TRAI): 10 digits beginning 6, 7, 8 or 9.
  * Landlines are 10 digits as STD-code + subscriber (11 Delhi, 22 Mumbai, 33 Kolkata,
    44 Chennai, 40 Hyderabad, 80 Bengaluru, 20 Pune, 79 Ahmedabad ...). These are valid
    Indian numbers but reach a switchboard, not a founder — `classify()` labels them so
    callers can prefer mobiles.

Use:
    from indian_number import to_e164, is_indian, classify, pick_best
    n = to_e164(raw)          # '' if it fails the gate
    if not n: skip_this_lead()
"""
import re

_MOBILE_START = "6789"
_STD_2 = {"11","22","33","44","40","80","20","79","token"}   # common metro STD codes

def _digits(s): return re.sub(r"[^\d]", "", str(s or ""))

def to_e164(raw):
    """Return '+91XXXXXXXXXX' if `raw` is a valid Indian number, else ''."""
    s = str(raw or "").strip()
    if not s: return ""
    d = _digits(s)

    # 1. explicit foreign country code -> reject, never re-stamp as +91
    if s.startswith("+") and not s.replace(" ", "").startswith("+91"):
        return ""
    if not s.startswith("+") and len(d) == 11 and d.startswith("1"):
        return ""                                  # 1-XXX-XXX-XXXX (US/Canada)
    if not s.startswith("+") and len(d) > 12:
        return ""                                  # too long to be Indian

    # 2. normalise to the 10-digit subscriber number
    if d.startswith("0091"): d = d[4:]
    elif d.startswith("091"): d = d[3:]
    elif d.startswith("91") and len(d) == 12: d = d[2:]
    elif d.startswith("0") and len(d) == 11: d = d[1:]      # STD trunk prefix

    # 3. must be exactly 10 digits
    if len(d) != 10: return ""
    # 4. first digit must be a plausible Indian mobile (6-9) or landline STD (1-5)
    if d[0] not in "123456789": return ""
    return "+91" + d

def is_indian(raw): return bool(to_e164(raw))

def classify(raw):
    """-> 'mobile' | 'landline' | '' (invalid).  Mobiles reach the founder; landlines don't."""
    n = to_e164(raw)
    if not n: return ""
    return "mobile" if n[3] in _MOBILE_START else "landline"

def pick_best(candidates):
    """From many raw numbers pick the best Indian one: mobile > landline > ''."""
    mob = land = ""
    for c in candidates or []:
        k = classify(c)
        if k == "mobile" and not mob: mob = to_e164(c)
        elif k == "landline" and not land: land = to_e164(c)
    return mob or land

# ------------------------------------------------------------------ self-test
if __name__ == "__main__":
    CASES = [
        # (input, expected_e164, expected_kind)  — drawn from real data seen in this project
        ("+91 99162 62587", "+919916262587", "mobile"),
        ("+919916262587",   "+919916262587", "mobile"),
        ("9971045274",      "+919971045274", "mobile"),
        ("09971045274",     "+919971045274", "mobile"),
        ("919971045274",    "+919971045274", "mobile"),
        ("+91 44 2573 9529","+914425739529", "landline"),   # Chennai switchboard
        ("+91 22 6630 5577","+912266305577", "landline"),   # Mumbai switchboard
        ("-9508540860",     "+919508540860", "mobile"),     # stray '-' from the Tracxn export
        ("+1 646-634-3800", "",              ""),           # explicit US -> reject
        ("+81 80-9159-2442","",              ""),           # explicit Japan -> reject
        ("+65 8655 3866",   "",              ""),           # explicit Singapore -> reject
        ("16463483800",     "",              ""),           # 11-digit US with leading 1
        ("12345",           "",              ""),           # too short
        ("",                "",              ""),
        (None,              "",              ""),
    ]
    bad = 0
    for raw, exp, kind in CASES:
        got, gk = to_e164(raw), classify(raw)
        ok = (got == exp and gk == kind)
        bad += (not ok)
        print(f"{'ok ' if ok else 'FAIL'} {str(raw)[:20]:20} -> {got or '(reject)':16} {gk or '-':9}"
              + ("" if ok else f"   expected {exp or '(reject)'} / {kind or '-'}"))
    print(f"\n{len(CASES)-bad}/{len(CASES)} passed")
    print("\nNOTE: a bare 10-digit foreign number (e.g. US 6464800503) is indistinguishable")
    print("from an Indian mobile without a country code — that is why SignalHire, which")
    print("returns country codes, is the only trusted source.")
