# -*- coding: utf-8 -*-
"""Bangladeshi mobile validation, the +880 counterpart to indian_number.py.

The standing rule is that nothing reaches HubSpot without a dialable mobile. For the Bangladesh
batch the country gate moves from +91 to +880, but the RIGOUR does not move: a landline or a
malformed string is just as useless to a caller in Dhaka as in Delhi, so both are still rejected.

Bangladesh mobile numbering (BTRC):
    country code 880, then a 10-digit national number beginning 1, then an operator digit:
        013 Grameenphone   014 Banglalink   015 Teletalk   016 Airtel
        017 Grameenphone   018 Robi         019 Banglalink
    so a full number is +8801XXXXXXXXX — 13 digits including the country code.
Anything starting 02 (Dhaka landline) or another area code is a landline and is rejected, which
is the same call indian_number.py makes for Indian landlines when a mobile is required.

A leading 0 is the domestic trunk prefix and is dropped: 01712345678 -> +8801712345678.

Usage:
    from bangladesh_number import to_e164, classify
    to_e164("01712-345678")  -> "+8801712345678"
    to_e164("+8802...")      -> ""            (landline)
"""
import re

OPERATOR = {"3": "Grameenphone", "4": "Banglalink", "5": "Teletalk",
            "6": "Airtel", "7": "Grameenphone", "8": "Robi", "9": "Banglalink"}


def _digits(s):
    return re.sub(r"\D", "", str(s or ""))


def to_e164(raw):
    """-> '+880XXXXXXXXXX' for a valid BD mobile, else ''. Never guesses."""
    s = str(raw or "").strip()
    if not s:
        return ""
    d = _digits(s)
    # explicit foreign numbers are not ours to rescue
    if s.startswith("+") and not s.startswith("+880"):
        return ""
    if d.startswith("880"):
        nat = d[3:]
    elif d.startswith("0"):
        nat = d.lstrip("0")            # domestic trunk prefix
    else:
        nat = d
    # a national mobile number is exactly 10 digits and starts 1
    if len(nat) != 10 or not nat.startswith("1"):
        return ""
    if nat[1] not in OPERATOR:         # 010/011/012 are not allocated to mobile
        return ""
    return "+880" + nat


def classify(e164):
    """-> 'mobile:<operator>' or ''. Only ever called on a to_e164 result."""
    if not e164 or not e164.startswith("+880"):
        return ""
    nat = e164[4:]
    return "mobile:" + OPERATOR.get(nat[1], "unknown") if len(nat) == 10 else ""


def is_valid(raw):
    return bool(to_e164(raw))


if __name__ == "__main__":
    cases = [
        ("+8801712345678", "+8801712345678"),   # canonical
        ("01712345678",    "+8801712345678"),   # domestic trunk prefix
        ("01712-345678",   "+8801712345678"),   # punctuation
        ("8801912345678",  "+8801912345678"),   # no plus
        ("+880 1611 234567", "+8801611234567"), # spaced
        ("+88029876543",   ""),                 # Dhaka landline
        ("+8801012345678", ""),                 # 010 not allocated
        ("+919845116391",  ""),                 # Indian number
        ("+14155551234",   ""),                 # US number
        ("017123456",      ""),                 # too short
        ("",               ""),
    ]
    bad = 0
    for raw, want in cases:
        got = to_e164(raw)
        ok = got == want
        bad += not ok
        print(f"{'ok ' if ok else 'FAIL'} {raw!r:<22}-> {got!r:<18}{classify(got)}")
    print(f"\n{len(cases)-bad}/{len(cases)} correct")
