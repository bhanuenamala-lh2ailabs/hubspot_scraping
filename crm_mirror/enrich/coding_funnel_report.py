# -*- coding: utf-8 -*-
"""Coding Funnel Report — daily snapshot writer + Today/Yesterday/Roll7/Prev7 renderer.

Spec: docs/reference/../Coding_Funnel_Report_KPIs_and_Stages.pdf (17 Sep 2026), approved as-is.

Two counting rules, one per stage type:
  FLOW-BASED (12 active stages):  Today = deals that moved INTO the stage today (CRM_UI only).
                                   Rolling 7 = SUM of daily flow counts, today back 6 days.
  CURRENT-STATE (14 terminal stages, incl. Closed/Won): Today = deals sitting in the stage
                                   right now. Rolling 7 = the current-state count AS RECORDED
                                   7 days ago (a single point-in-time read, not a sum).

Every day this runs, it writes today's numbers to a persistent JSON snapshot
(crm_mirror/data/snapshots/coding_funnel_<date>.json) and reads Yesterday/Roll7/Prev7 back
from PAST snapshot files — never reconstructed from HubSpot after the fact, per the spec's
"why this needs a snapshot store" section. Until 14 days of snapshots exist, those columns
show "not enough history yet".

Usage: python3 coding_funnel_report.py [--send --to you@lh2.ai]
"""
import os, sys, json, datetime, time, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
SNAP_DIR = os.path.join(HUB, "crm_mirror", "data", "snapshots")
env = {l.split('=', 1)[0].strip().lower(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, ".env"), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
HH = {"Authorization": "Bearer " + env["hubspot_key"], "Content-Type": "application/json"}
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

CODING_SOURCES = [
    "Apollo Search ( IT Services )", "Founder Search ( IT Services )",
    "LinkedIn Sales Nav ( IT Services )", "Linkedin Campaign ( IT Services )",
    "Outflo Outreach ( IT Services )", "Relevant IT Services",
    "Scraping Algo ( IT services )", "Scraped ( IT Services )",
    "Private Codebase Tracker sheet ( IT services )", "NASSCOM ( IT Services )", "CAD_salesNav",
]

# label -> [stage_id in Scraped pipeline, stage_id in Campaign pipeline]
FLOW_STAGE_IDS = {
    "Cold Call":                 ["3992480462", "4002503379"],
    "No Pickup":                 ["4104051404", "4102985418"],
    "Interested":                ["3992480465", "4018854633"],
    "GMeet Fixed":               ["3992480469", "4018854634"],
    "Script Shared":             ["3992480471", "4018854635"],
    "Script Results Received":   ["3992480473", "4018854636"],
    "Commercial Negotiation":    ["4030231231", "4018854637"],
    "LOI":                       ["4173850324", "4173777601"],
    "Deal Contract Signed":      ["4029653710", "4018854638"],
    "Data Migration Done":       ["3992480475", "4018854639"],
    "Metadata Matched":          ["4036632313", "4018854640"],
    "Payment Initiation":        ["4036633274", "4018854641"],
}
TERMINAL_STAGE_IDS = {
    "Closed/Won":                              ["4036632309", "4018854642"],
    "Dead/ColdCall/Not Interested":             ["4036632310", "4018854643"],
    "Dead/ColdCall/WrongFit":                   ["4036687547", "4002503384"],
    "Dead/ColdCall/WrongNumber":                ["4099250912", "4099442394"],
    "Dead/ColdCall/NoPickup":                   ["4102985416", "4103772885"],
    "Dead/Interested/NoShow":                   ["4061963984", "4002503385"],
    "Dead/GMeet/NoShow":                        ["4102985417", "4103772886"],
    "Dead/GMeet/Cancelled":                     ["4103772884", "4103772887"],
    "Dead/GMeet/wrong fit":                     ["4036632311", "4018854644"],
    "Dead/GMeet/Privacy Concerns":              ["4036687548", "4018854645"],
    "Dead/ScriptShared/NoShow":                 ["4104051405", "4103772888"],
    "Dead/ResultsReceived/WrongFit-Rejected":   ["4036687549", "4018854646"],
    "Dead/Negotiation/Pricing":                 ["4035313388", "4068768453"],
    "Dead/Negotiation/Contractual":             ["4036632312", "4068768454"],
}
STAGE_LABEL = {sid: lab for lab, ids in {**FLOW_STAGE_IDS, **TERMINAL_STAGE_IDS}.items() for sid in ids}


def hs(path, method="GET", body=None):
    d = json.dumps(body).encode() if body else None
    req = urllib.request.Request("https://api.hubapi.com" + path, data=d, method=method, headers=HH)
    for a in range(8):
        try:
            r = urllib.request.urlopen(req, timeout=45)
            t = r.read().decode()
            return r.status, (json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503, 504) and a < 7:
                time.sleep(2 * (a + 1)); continue
            t = e.read().decode()
            try: return e.code, json.loads(t)
            except Exception: return e.code, {"raw": t[:200]}
        except (urllib.error.URLError, ConnectionResetError, TimeoutError, OSError):
            if a < 7:
                time.sleep(2 * (a + 1)); continue
            raise
    return None, {}


def ist_day(ts):
    if isinstance(ts, (int, float)) or str(ts).isdigit():
        return datetime.datetime.fromtimestamp(int(ts) / 1000, IST).date().isoformat()
    return datetime.datetime.fromisoformat(str(ts).replace("Z", "+00:00")).astimezone(IST).date().isoformat()


def today_ist():
    return datetime.datetime.now(IST).date()


CREATION_STAGE = "Cold Call"   # the one flow stage where an API-driven entry IS the real event
                                # (a lead genuinely entering the funnel) rather than integration
                                # noise — every other flow stage stays CRM_UI-only.


def compute_flow_today():
    """Deals under Coding sources that moved into a flow stage TODAY.
    CRM_UI-only for every stage except Cold Call, where ANY sourceType counts — a script push
    landing a new lead there is the real "entered the funnel" event, not noise to filter out.
    Candidate-then-history: narrow via hs_v2_date_entered_current_stage == today first
    (valid because the window ends today), then pull full history only for that small set."""
    today = today_ist().isoformat()
    start = today + "T00:00:00Z"
    counts = {lab: 0 for lab in FLOW_STAGE_IDS}
    after = None
    cand_ids = []
    while True:
        body = {"filterGroups": [{"filters": [
                    {"propertyName": "lead_source", "operator": "IN", "values": CODING_SOURCES},
                    {"propertyName": "hs_lastmodifieddate", "operator": "GTE", "value": start}]}],
                 "properties": ["dealname", "hs_v2_date_entered_current_stage"], "limit": 100}
        if after: body["after"] = after
        s, r = hs("/crm/v3/objects/deals/search", "POST", body)
        for x in r.get("results", []):
            dt = x["properties"].get("hs_v2_date_entered_current_stage")
            if dt and ist_day(dt) == today:
                cand_ids.append(x["id"])
        p = r.get("paging")
        if p and p.get("next"): after = p["next"]["after"]
        else: break
        time.sleep(0.05)
    for did in cand_ids:
        s, r = hs(f"/crm/v3/objects/deals/{did}?propertiesWithHistory=dealstage")
        hist = ((r.get("propertiesWithHistory") or {}).get("dealstage")) or []
        for e in hist:
            lab = STAGE_LABEL.get(e.get("value"))
            if lab not in counts:
                continue
            if lab != CREATION_STAGE and e.get("sourceType") != "CRM_UI":
                continue
            if ist_day(e.get("timestamp")) != today:
                continue
            counts[lab] += 1
        time.sleep(0.05)
    return counts


def compute_current_state_today():
    counts = {}
    for lab, ids in TERMINAL_STAGE_IDS.items():
        body = {"filterGroups": [{"filters": [
                    {"propertyName": "lead_source", "operator": "IN", "values": CODING_SOURCES},
                    {"propertyName": "dealstage", "operator": "IN", "values": ids}]}],
                 "properties": ["dealname"], "limit": 1, "total": True}
        s, r = hs("/crm/v3/objects/deals/search", "POST", body)
        counts[lab] = r.get("total", 0)
    return counts


def snapshot_path(d):
    return os.path.join(SNAP_DIR, f"coding_funnel_{d.isoformat()}.json")


def write_today_snapshot(flow, current_state):
    os.makedirs(SNAP_DIR, exist_ok=True)
    d = today_ist()
    payload = {"date": d.isoformat(), "flow": flow, "current_state": current_state}
    open(snapshot_path(d), "w").write(json.dumps(payload, indent=1))
    return payload


def read_snapshot(d):
    p = snapshot_path(d)
    if not os.path.exists(p):
        return None
    return json.load(open(p))


def build_report(flow_today, cs_today):
    d0 = today_ist()
    rows = []
    for lab in FLOW_STAGE_IDS:
        today_v = flow_today[lab]
        yest = read_snapshot(d0 - datetime.timedelta(days=1))
        roll7_days = [read_snapshot(d0 - datetime.timedelta(days=i)) for i in range(7)]
        prev7_days = [read_snapshot(d0 - datetime.timedelta(days=i)) for i in range(7, 14)]
        yest_v = yest["flow"][lab] if yest else None
        roll7_v = sum(s["flow"][lab] for s in roll7_days if s) if all(roll7_days) else None
        prev7_v = sum(s["flow"][lab] for s in prev7_days if s) if all(prev7_days) else None
        rows.append(("flow", lab, today_v, yest_v, roll7_v, prev7_v))
    for lab in TERMINAL_STAGE_IDS:
        today_v = cs_today[lab]
        yest = read_snapshot(d0 - datetime.timedelta(days=1))
        s7 = read_snapshot(d0 - datetime.timedelta(days=7))
        s14 = read_snapshot(d0 - datetime.timedelta(days=14))
        yest_v = yest["current_state"][lab] if yest else None
        roll7_v = s7["current_state"][lab] if s7 else None
        prev7_v = s14["current_state"][lab] if s14 else None
        rows.append(("current-state", lab, today_v, yest_v, roll7_v, prev7_v))
    return rows


def fmt(v):
    return "—" if v is None else str(v)


def render(rows):
    lines = []
    lines.append(f"CODING FUNNEL REPORT — {today_ist().isoformat()} (IST)")
    lines.append("=" * 78)
    lines.append(f"{'Stage':<42}{'Type':<14}{'Today':>6}{'Yest':>7}{'Roll7':>7}{'Prev7':>7}")
    for typ, lab, t, y, r7, p7 in rows:
        lines.append(f"{lab:<42}{typ:<14}{fmt(t):>6}{fmt(y):>7}{fmt(r7):>7}{fmt(p7):>7}")
    have_history = any(y is not None for _, _, _, y, _, _ in rows)
    if not have_history:
        lines.append("")
        lines.append("Not enough history yet — this is day 1 of the 14-day snapshot build-up.")
        lines.append("Yesterday/Roll7/Prev7 will start filling in from tomorrow's run onward.")
    return "\n".join(lines)


if __name__ == "__main__":
    print("computing today's flow counts (12 active stages)...", flush=True)
    flow = compute_flow_today()
    print("computing today's current-state counts (14 terminal stages)...", flush=True)
    cs = compute_current_state_today()
    write_today_snapshot(flow, cs)
    rows = build_report(flow, cs)
    print()
    print(render(rows))
