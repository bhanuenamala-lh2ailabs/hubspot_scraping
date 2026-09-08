# -*- coding: utf-8 -*-
"""Note classification — the single source of truth for note buckets.

WHY THIS LIVES HERE AND NOT IN crm_mirror/enrich/.
These rules were originally defined in crm_mirror/enrich/daily_activity_report.py. That file is
NOT in the git repo — `lh2-pipeline` is the repo, crm_mirror is a local-only sibling directory.
So when build_dashboard.py imported the rules from there, it worked on this laptop and failed
silently on GitHub Actions, leaving the note KPIs permanently empty on the deployed dashboard.

Moving the definition into the deployed repo and importing it back into the local script points
the dependency the right way: the thing that must run in CI owns the definition, and the thing
that only ever runs locally borrows it. Copying instead of importing was not an option — an
earlier hand-copy of the KPI definitions drifted and inflated dial counts 2.7x.

ORDER MATTERS — first match wins. Read off the real 6-7 Aug notes.
Rules were extended after the first run surfaced 12 unmatched notes — every gap below was a real
note somebody wrote, not a hypothetical. Kept ordered: "Not interested" must be tested before
"Interested", and bad-number before no-pickup, or the wrong bucket wins.
"""
import re, html

NOTE_RULES = [
    # "Received script" must be tested FIRST and before "Script shared": it restates the
    # `rr` KPI, and the caller of this module maps it to None so the same act is not counted
    # once as a KPI and again as note-only activity.
    # Machine-written notes first: the deadpool/relevance-check/test-deal/lead-gen blocks are
    # emitted by our own scripts, not typed by anyone. They are normally unowned and filtered
    # out upstream, but catching them here means they can never be counted as somebody's work.
    ("System note",     r"^(deadpool wave lead|relevance check|test deal|linkedin lead-?gen form|"
                        r"inbound linkedin|\[pipeline tracker)"),
    ("Script received", r"(received (the )?script|script received|got (the )?script (back|output))"),
    ("Bad number",      r"(wrong ?n+o\b|wrong number|number\s+(is\s+)?(wrong|invalid)|invalid ?n(o|umber)\b|"
                        r"inv[al]+id ?no\b|numbers?\b[^.]{0,30}?\b(are|is)\s+(incorrect|invalid|wrong)|"
                        r"number\s+(does\s*not|doesn'?t)\s+exist|does\s*not\s+exist|"
                        r"only international number|no longer associated|"
                        r"out of service|not in service|incoming call not allowed|"
                        r"cannot receive incoming|cannot be reached)"),
    ("Vetted - out",    r"^\s*(irrelevant|not relevant|non[- ]relevant)"),
    ("Vetted - in",     r"^\s*(relevant|maybe relevant)"),
    ("Not interested",  r"(not interested|was ?n'?t interested|were ?n'?t interested|"
                        r"no bandwidth|no interest|not looking for)"),
    ("Disqualified",    r"(still operating|sold the compan|does ?n'?o?t? own|no codebase|no dormant|"
                        r"(does|do)\s*n'?o?t?\s*have\s+(a\s+)?(dormant\s+)?codebase|"
                        r"not a founder|post 20\d\d founder|non tech|no assets|"
                        r"would ?n'?o?t? be able to share|"
                        r"(don'?t|do not|dont)\s+do\s+any\s+development|"
                        r"not a relevant poc|is irrelevant|"
                        r"based out of\s+(?!india|bangalore|bengaluru|mumbai|delhi|pune|chennai|"
                        r"hyderabad|kolkata|ahmedabad|noida|gurgaon)|"
                        r"nothing to sell|codebase is deleted|active company|still active|"
                        r"still operates|(don'?t|do ?n'?t|doesn'?t)\s+have\s+(any\s+)?"
                        r"(inactive\s+|dormant\s+)?(codebases?|ip\b)|no ip\b)"),
    ("No pickup",       r"(did not pick|didn'?t pick|no response|no resposne|not pick(ing)? up|"
                        r"hung up|\bdnp\b|switched off|call(ed)? (done )?no re[sp]|"
                        r"left a (voice|vm)|voicemail|voice note|no answer)"),
    ("Callback booked", r"(call ?back at|asked to call|call me back|called back|get(ting)? back|"
                        r"will call ?back|in a meeting|will lmk|check with|busy|"
                        r"check back on|connect back|asked for a call|reschedul)"),
    ("Meeting fixed",   r"(gmeet fixed|call fixed|meeting fixed|scheduled for|slots)"),
    ("Script shared",   r"(shared? (the )?script|sent (the )?script|calendly)"),
    ("Chase sent",      r"(sent (a )?message|followed up|whats ?app|\bwa\b|over (mail|text)|"
                        r"left a message|closed loop|asked to mail|share details by mail|"
                        r"send a mail|mail again)"),
    ("Interested",      r"^\s*interested|is interested"),
]
BUCKETS = [b for b, _ in NOTE_RULES] + ["Other"]


def plain(s):
    """HubSpot note bodies are HTML. Strip tags and collapse whitespace before matching."""
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s or "")).split())


def classify(t):
    s = t.lower()
    for name, rx in NOTE_RULES:
        if re.search(rx, s): return name
    return "Other"


if __name__ == "__main__":
    # Each case is a note somebody actually wrote, kept as a regression guard: these are the
    # exact pairs the ordering rules exist for.
    cases = [
        ("Did not pick up",                              "No pickup"),
        ("wrong no",                                     "Bad number"),
        ("Not interested, no bandwidth",                 "Not interested"),
        ("Interested, wants to know more",               "Interested"),
        ("received the script",                          "Script received"),
        ("shared the script over mail",                  "Script shared"),
        ("Relevance check: passed",                      "System note"),
        ("irrelevant - still operating",                 "Vetted - out"),
        ("relevant",                                     "Vetted - in"),
        ("asked to call back at 4pm",                    "Callback booked"),
        ("<p>GMeet fixed for tomorrow</p>",              "Meeting fixed"),
        ("still operating, no dormant codebase",         "Disqualified"),
        ("followed up on whatsapp",                      "Chase sent"),
        ("random unmatched text here",                   "Other"),
    ]
    bad = 0
    for raw, want in cases:
        got = classify(plain(raw).lower())
        ok = got == want; bad += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {raw[:42]:<44}-> {got}" + ("" if ok else f"   (want {want})"))
    print(f"\n{len(cases)-bad}/{len(cases)} correct")
