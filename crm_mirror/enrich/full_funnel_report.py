# -*- coding: utf-8 -*-
"""Full-HubSpot Funnel Report — every deal in the portal (both pipelines: Scraped + Campaign),
no lead_source filter. Same flow/current-state split and snapshot-store logic as
coding_funnel_report.py (see that file's docstring + the approved Coding_Funnel_Report_KPIs_
and_Stages.pdf spec) — this is the vertical-agnostic, whole-portal version.

Usage: python3 full_funnel_report.py
"""
import os, sys, json, datetime, time, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
SNAP_DIR = os.path.join(HUB, "crm_mirror", "data", "snapshots")
env = {l.split('=', 1)[0].strip().lower(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, ".env"), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
HH = {"Authorization": "Bearer " + env["hubspot_key"], "Content-Type": "application/json"}
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

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
CREATION_STAGE = "Cold Call"   # only flow stage where any sourceType counts (see coding_funnel_report.py)
SNAP_PREFIX = "full_funnel"

# Dashboard-format rows (full_funnel_dashboard_mail.py): (row_label, stage_labels_in_row, any_source)
DEAD_STAGE_LABELS = [lab for lab in TERMINAL_STAGE_IDS if lab != "Closed/Won"]
DASHBOARD_ROWS = [
    ("Leads Assigned", ["Cold Call"], True),
    ("No Pickup", ["No Pickup"], False),
    ("Interested", ["Interested"], False),
    ("GMeet Fixed", ["GMeet Fixed"], False),
    ("Script Shared", ["Script Shared"], False),
    ("Script Results Received", ["Script Results Received"], False),
    ("Commercial Negotiation", ["Commercial Negotiation"], False),
    ("LOI", ["LOI"], False),
    ("Deal Contract Signed", ["Deal Contract Signed"], False),
    ("Closed/Won", ["Closed/Won"], False),
    ("Dead", DEAD_STAGE_LABELS, False),
]


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


def compute_flow_today():
    today = today_ist().isoformat()
    start = today + "T00:00:00Z"
    counts = {lab: 0 for lab in FLOW_STAGE_IDS}
    after = None
    cand_ids = []
    while True:
        body = {"filterGroups": [{"filters": [
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


def compute_dashboard_and_engaged_today():
    """One candidate-then-history pass, used by full_funnel_dashboard_mail.py, that produces both:
      - dashboard flow counts (the 11 DASHBOARD_ROWS, today only)
      - the set of distinct deal IDs with >=1 CRM_UI stage-move today (for "Leads Engaged")
    Kept separate from compute_flow_today() (the 12/14-stage table version) so neither report's
    candidate pull depends on the other, even though the underlying HubSpot data is the same."""
    today = today_ist().isoformat()
    start = today + "T00:00:00Z"
    dash_counts = {lab: 0 for lab, _, _ in DASHBOARD_ROWS}
    after = None
    cand_ids = []
    while True:
        body = {"filterGroups": [{"filters": [
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
    engaged = []
    for did in cand_ids:
        s, r = hs(f"/crm/v3/objects/deals/{did}?propertiesWithHistory=dealstage")
        hist = ((r.get("propertiesWithHistory") or {}).get("dealstage")) or []
        touched = False
        for e in hist:
            if ist_day(e.get("timestamp")) != today:
                continue
            lab = STAGE_LABEL.get(e.get("value"))
            src = e.get("sourceType")
            if src == "CRM_UI":
                touched = True
            for row_lab, stage_labels, any_source in DASHBOARD_ROWS:
                if lab in stage_labels and (any_source or src == "CRM_UI"):
                    dash_counts[row_lab] += 1
        if touched:
            engaged.append(did)
        time.sleep(0.05)
    return dash_counts, engaged


def compute_current_state_today():
    counts = {}
    for lab, ids in TERMINAL_STAGE_IDS.items():
        body = {"filterGroups": [{"filters": [{"propertyName": "dealstage", "operator": "IN", "values": ids}]}],
                 "properties": ["dealname"], "limit": 1, "total": True}
        s, r = hs("/crm/v3/objects/deals/search", "POST", body)
        counts[lab] = r.get("total", 0)
    return counts


def snapshot_path(d):
    return os.path.join(SNAP_DIR, f"{SNAP_PREFIX}_{d.isoformat()}.json")


def write_today_snapshot(flow, current_state, dashboard_flow=None, engaged_ids=None):
    """dashboard_flow/engaged_ids are optional — pass them (from
    compute_dashboard_and_engaged_today()) to also persist 'cumulative' (each DASHBOARD_ROWS
    label's running inception-to-date total, built incrementally from yesterday's snapshot — no
    full-history re-pull needed after the one-time seed backfill) and 'engaged_deal_ids' (for a
    correct multi-day dedup when a future Roll7/Prev7 "Leads Engaged" needs a real union, not a
    naive sum of daily counts)."""
    os.makedirs(SNAP_DIR, exist_ok=True)
    d = today_ist()
    payload = {"date": d.isoformat(), "flow": flow, "current_state": current_state}
    if dashboard_flow is not None:
        yest = read_snapshot(d - datetime.timedelta(days=1))
        prior_cumulative = yest["cumulative"] if yest and "cumulative" in yest else {lab: 0 for lab, _, _ in DASHBOARD_ROWS}
        payload["cumulative"] = {lab: prior_cumulative.get(lab, 0) + dashboard_flow.get(lab, 0) for lab, _, _ in DASHBOARD_ROWS}
        payload["dashboard_flow"] = dashboard_flow
    if engaged_ids is not None:
        payload["engaged_deal_ids"] = engaged_ids
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
    lines.append(f"FULL HUBSPOT FUNNEL REPORT — {today_ist().isoformat()} (IST)")
    lines.append("=" * 78)
    lines.append(f"{'Stage':<42}{'Type':<14}{'Today':>6}{'Yest':>7}{'Roll7':>7}{'Prev7':>7}")
    for typ, lab, t, y, r7, p7 in rows:
        lines.append(f"{lab:<42}{typ:<14}{fmt(t):>6}{fmt(y):>7}{fmt(r7):>7}{fmt(p7):>7}")
    return "\n".join(lines)


if __name__ == "__main__":
    print("computing today's flow counts (12 active stages, whole portal)...", flush=True)
    flow = compute_flow_today()
    print("computing today's current-state counts (14 terminal stages, whole portal)...", flush=True)
    cs = compute_current_state_today()
    print("computing today's dashboard-row flow + engaged deals...", flush=True)
    dash_flow, engaged = compute_dashboard_and_engaged_today()
    write_today_snapshot(flow, cs, dashboard_flow=dash_flow, engaged_ids=engaged)
    rows = build_report(flow, cs)
    print()
    print(render(rows))
