# -*- coding: utf-8 -*-
"""Romanian number validation and labelling (+40).

Written because the Bangladesh classifier was reused for the Romania run and labelled every
number "other/landline" — including +40 720…, +40 741…, +40 754…, which are all mobiles. A
caller reading that would assume they are dialling a switchboard when they have a personal
mobile in front of them, which changes how the call opens.

ANRCOM numbering:
    country code 40, then 9 national digits
    07x xxx xxx  -> MOBILE  (071-079; the whole 07 block is mobile)
    0Nxx ...     -> LANDLINE, geographic. 021/031 Bucharest, 026x/036x Transylvania,
                    023x/033x Moldova, 024x/034x Muntenia, 025x/035x Oltenia, 027x/037x Banat
    0800 / 0801  -> freephone / shared cost, not a person
The domestic trunk prefix 0 is dropped in E.164: 0721234567 -> +40721234567.

No country gate is applied here — that is a caller-facing policy decision made per batch, not a
property of the number. This module only says what a number IS.
"""
import re

COUNTY = {"21": "Bucharest", "31": "Bucharest", "23": "Moldova", "33": "Moldova",
          "24": "Muntenia", "34": "Muntenia", "25": "Oltenia", "35": "Oltenia",
          "26": "Transylvania", "36": "Transylvania", "27": "Banat", "37": "Banat"}


def to_e164(raw):
    """-> '+40XXXXXXXXX' for a valid Romanian number, else ''."""
    s = str(raw or "").strip()
    if not s: return ""
    d = re.sub(r"\D", "", s)
    if s.startswith("+") and not s.startswith("+40"): return ""
    if d.startswith("0040"): d = d[4:]
    elif d.startswith("40") and len(d) >= 11: d = d[2:]
    elif d.startswith("0"): d = d[1:]
    if len(d) != 9: return ""
    if not d.startswith(("2", "3", "7", "8")): return ""
    return "+40" + d


def classify(e164):
    """-> 'mobile' | 'landline:<region>' | 'freephone' | ''."""
    if not e164.startswith("+40"): return ""
    n = e164[3:]
    if len(n) != 9: return ""
    if n.startswith("7"): return "mobile"
    if n.startswith("80"): return "freephone"
    return "landline:" + COUNTY.get(n[:2], "other")


def is_mobile(raw):
    return classify(to_e164(raw)) == "mobile"


if __name__ == "__main__":
    cases = [("+40720058245", "mobile"), ("+40741131505", "mobile"), ("0040770613713", "mobile"),
             ("+40364113110", "landline:Transylvania"), ("+40213334455", "landline:Bucharest"),
             ("0721234567", "mobile"), ("+40800123456", "freephone"),
             ("+15642270652", ""), ("+8801712345678", ""), ("", "")]
    bad = 0
    for raw, want in cases:
        e = to_e164(raw); got = classify(e)
        ok = got == want; bad += not ok
        print(f"{'ok ' if ok else 'FAIL'} {raw!r:<18}-> {e or '(rejected)':<16}{got}")
    print(f"\n{len(cases)-bad}/{len(cases)} correct")
