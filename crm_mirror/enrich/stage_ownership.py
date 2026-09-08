# -*- coding: utf-8 -*-
"""Who owns a deal's follow-up — by STAGE, not by HubSpot deal owner.

Set 2026-08-18. Import band_for() anywhere a per-person follow-up list is produced so the
rule lives in exactly one place.

    Yuktha / Lamiya : Cold Call, No Pickup, Interested, and FIXING the GMeet
    Ishpreet        : GMeet Fixed (attend), Script Shared, Script Results Received
    Shobit          : Commercial Negotiation -> Contract -> Migration -> Payment -> close

THE GMEET GATE
    A deal at "GMeet Fixed" only passes to Ishpreet if gmeet1_link is populated. A note
    saying "gmeet fixed" is NOT proof — callers were moving deals on a note alone and two
    sat there 20-26 days with nobody able to tell whether a meeting existed. Without the
    link the deal stays with whoever fixed it, whose job is to produce a real link or move
    the stage back.
"""

CALLERS = "CALLERS"      # Yuktha + Lamiya
MEETING = "MEETING"      # Ishpreet
COMMERCIAL = "COMMERCIAL"  # Shobit

OWNER_OF = {CALLERS: "Yuktha / Lamiya", MEETING: "Ishpreet", COMMERCIAL: "Shobit"}

CALLER_STAGES = {"Cold Call", "No Pickup", "Interested", "Call Attempted (retired)"}
MEETING_STAGES = {"Script Shared", "Script Results Received"}
COMMERCIAL_STAGES = {"Commercial Negotiation", "Deal Contract Signed",
                     "Data Migration Done", "Metadata Matched", "Payment Initiation"}


def has_meeting_link(props):
    """The gate. Only a populated gmeet1_link counts — not a note, not a task."""
    return bool((props.get("gmeet1_link") or "").strip())


def band_for(stage_label, props=None):
    """Return (band, reason). props is the deal's HubSpot properties dict."""
    props = props or {}
    if stage_label == "GMeet Fixed":
        if has_meeting_link(props):
            return MEETING, "meeting link present"
        return CALLERS, "NO gmeet1_link — caller must add the link or move the stage back"
    if stage_label in CALLER_STAGES:
        return CALLERS, "top of funnel"
    if stage_label in MEETING_STAGES:
        return MEETING, "meeting done, chasing output"
    if stage_label in COMMERCIAL_STAGES:
        return COMMERCIAL, "commercials"
    if str(stage_label).startswith("Dead/") or stage_label == "Closed/Won":
        return None, "closed"
    return CALLERS, "unmapped stage — defaults to callers"


REQUIRED_PROPERTIES = ["dealname", "dealstage", "hubspot_owner_id",
                       "gmeet1_link", "gmeet1_date", "gmeet1_outcome"]

if __name__ == "__main__":
    for s, p in (("Cold Call", {}), ("Interested", {}),
                 ("GMeet Fixed", {}), ("GMeet Fixed", {"gmeet1_link": "https://meet.google.com/abc"}),
                 ("Script Shared", {}), ("Commercial Negotiation", {}), ("Closed/Won", {})):
        b, r = band_for(s, p)
        print(f"{s:<26}{'link' if p.get('gmeet1_link') else '    ':<6}-> {str(OWNER_OF.get(b)):<18}({r})")
