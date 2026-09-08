# -*- coding: utf-8 -*-
"""Full-funnel activity per person per day — Plan B (notes as the activity log).

Everyone now works the whole funnel, so this reports EVERY KPI for EVERY person. No roles, no
per-role quotas: the old split is what made a day of script-chasing read as a bad day.

TWO INDEPENDENT SOURCES, deliberately kept apart so nothing is double counted:

  STAGE KPIs   — dealstage transitions, sourceType=CRM_UI only, credited to whoever clicked.
                 Same definition the dashboard uses, so the two can never disagree.
                 Only counts work that MOVED a deal.

  NOTE BUCKETS — what people wrote down. This is the work stages cannot see: a dial that got
                 no answer, a vetting verdict, a callback booked, a chase message sent.

Note buckets were derived by reading the actual 106 notes written on 6-7 Aug, not invented.
Classification is ORDERED and first-match-wins: negations and disqualifiers are tested before
the positive words they contain, because "Irrelevant" contains "relevant" and "no response to
call" contains "call". Getting that order wrong silently turns every rejection into an approval
— which is exactly how a regex misread "Not fully relevant" as an approval earlier this week.

Usage: python daily_activity_report.py [--days 2026-08-06,2026-08-07] [--md out.md]
"""
import os, re, sys, json, time, html, datetime, collections, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
H = {"Authorization": "Bearer " + env["hubspot_key"], "Content-Type": "application/json"}
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

DAYS = ["2026-08-06", "2026-08-07"]
MD = None
for i, a in enumerate(sys.argv):
    if a == "--days": DAYS = sys.argv[i+1].split(",")
    if a == "--md":   MD = sys.argv[i+1]


def hs(u, m="GET", b=None):
    d = json.dumps(b).encode() if b is not None else None
    for a in range(6):
        try:
            r = urllib.request.Request("https://api.hubapi.com" + u, data=d, method=m, headers=H)
            with urllib.request.urlopen(r, timeout=60) as x:
                t = x.read().decode(); return x.status, (json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and a < 5: time.sleep(2*(a+1)); continue
            return e.code, {}
        except Exception:
            if a == 5: raise
            time.sleep(3*(a+1))


def ist_day(ts):
    try:
        if isinstance(ts, (int, float)) or str(ts).isdigit():
            return datetime.datetime.fromtimestamp(int(ts)/1000, IST).date().isoformat()
        return datetime.datetime.fromisoformat(str(ts).replace("Z", "+00:00")).astimezone(IST).date().isoformat()
    except Exception:
        return None


# ---------------------------------------------------------------- stage KPIs
# label -> KPI keys. Mirrors dashboard/build_dashboard.py metrics_for().
KPI = [("att", "Call attempted"), ("conn", "Connected"), ("gm", "GMeet fixed"),
       ("vc", "VC done"), ("ss", "Script shared"), ("rr", "Result recvd"),
       ("ev", "Evaluation"), ("cn", "Negotiation"), ("neg", "Neg. calls"),
       ("dcs", "Contract"), ("won", "Closed/Won")]


# COPIED VERBATIM from lh2-pipeline/dashboard/build_dashboard.py METRICS. Do not "improve" it.
# It is explicit set membership and deliberately NOT cascading — an earlier draft of this file
# assumed reaching a late stage implied the earlier ones and inflated Lamiya's 6 Aug attempts
# from 18 to 54. Two exclusions carry real meaning:
#   * Dead/ColdCall/WrongFit is absent from `att` — screened out, never dialled.
#   * Dead/GMeet/Cancelled is absent from `vc`  — called off in advance, no time spent in it.
# If a quota or stage changes, change it there first and re-copy.
METRICS = {
    "att":  {"No Pickup", "Dead/ColdCall/WrongNumber", "Dead/ColdCall/Not Interested",
             "Dead/ColdCall/NoPickup", "Interested"},
    "conn": {"Dead/ColdCall/Not Interested", "Interested"},
    "gm":   {"GMeet Fixed"},
    "vc":   {"Dead/GMeet/NoShow", "Dead/GMeet/wrong fit", "Dead/GMeet/Privacy Concerns",
             "Script Shared"},
    "ss":   {"Script Shared"},
    "rr":   {"Script Results Received"},
    "ev":   {"Dead/ResultsReceived/WrongFit-Rejected", "Commercial Negotiation"},
    "cn":   {"Commercial Negotiation"},
    "neg":  {"Dead/Negotiation/Pricing", "Dead/Negotiation/Contractual", "Deal Contract Signed"},
    "dcs":  {"Deal Contract Signed"},
    "won":  {"Closed/Won"},
}


def metrics_for(lab):
    return [k for k, s in METRICS.items() if lab in s]


# ---------------------------------------------------------------- note buckets
# MOVED to lh2-pipeline/dashboard/note_rules.py on 2026-08-14 and imported back from there.
# The dashboard build needs these same classifiers, and it runs on GitHub Actions where only
# the lh2-pipeline repo exists — this file is local-only, so a build importing FROM here found
# nothing in CI. The definition now lives in the repo that deploys and this script borrows it.
# Copying was not an option: an earlier hand-copy of the KPI definitions drifted and inflated
# dial counts 2.7x. Edit the rules there, once.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "lh2-pipeline", "dashboard"))
from note_rules import NOTE_RULES, BUCKETS, classify, plain  # noqa: E402


def main():
    s, d = hs("/crm/v3/pipelines/deals")
    LAB = {x["id"]: x["label"] for p in d["results"] for x in p["stages"]}
    _, ow = hs("/crm/v3/owners?limit=200")
    OWN = {o["id"]: f'{o.get("firstName","")} {o.get("lastName","")}'.strip() for o in ow.get("results", [])}
    UID2OWN = {str(o.get("userId")): OWN[o["id"]] for o in ow.get("results", []) if o.get("userId")}

    lo = min(DAYS) + "T00:00:00Z"
    # `hs_lastmodifieddate` is far too broad: today's own pushes and a linkedin backfill touched
    # 1,176 deals without changing a single stage, and one history call each is ~16 minutes.
    # `hs_date_entered_<stage>` is a readable property, so one batched search tells us which
    # deals actually entered a stage inside the window. History is then fetched only for those.
    # This portal has no per-stage `hs_date_entered_<id>` properties — only
    # `hs_v2_date_entered_current_stage`. That is still a sound filter while the window ends
    # NOW: if a deal's most recent stage change predates the window it changed nothing inside
    # it. (It would under-count for a window that ends in the past, because a later move
    # overwrites the field — so this filter is only valid for a report run up to today.)
    ENTERED = "hs_v2_date_entered_current_stage"
    after, cand = None, []
    while True:
        b = {"limit": 100, "properties": ["dealname", "hubspot_owner_id", "dealstage", ENTERED],
             "filterGroups": [{"filters": [{"propertyName": "hs_lastmodifieddate",
                                            "operator": "GTE", "value": lo}]}]}
        if after: b["after"] = after
        _, r = hs("/crm/v3/objects/deals/search", "POST", b)
        cand += r.get("results", [])
        after = (r.get("paging") or {}).get("next", {}).get("after")
        if not after: break
    if max(DAYS) < datetime.datetime.now(IST).date().isoformat():
        sys.exit("This filter is only valid for a window ending today — see comment above.")
    deals = [x for x in cand if ist_day(x["properties"].get(ENTERED)) in DAYS]
    print(f"deals modified since {min(DAYS)}: {len(cand)} | actually changed stage in window: "
          f"{len(deals)} — pulling history for those only", flush=True)

    stage = collections.defaultdict(collections.Counter)   # (day,person) -> Counter(kpi)
    touched = collections.defaultdict(set)                 # (day,person) -> {deal ids}
    for i, x in enumerate(deals):
        did = x["id"]
        _, h = hs(f"/crm/v3/objects/deals/{did}?propertiesWithHistory=dealstage")
        for e in (h.get("propertiesWithHistory", {}) or {}).get("dealstage", []) or []:
            if e.get("sourceType") != "CRM_UI":      # 42% is integration noise; never count it
                continue
            day = ist_day(e.get("timestamp"))
            if day not in DAYS: continue
            lab = LAB.get(e.get("value"))
            if not lab: continue
            who = UID2OWN.get(str(e.get("updatedByUserId")), "(unknown)")
            for k in metrics_for(lab): stage[(day, who)][k] += 1
            touched[(day, who)].add(did)
        if (i+1) % 100 == 0: print(f"   {i+1}/{len(deals)}", flush=True)

    # ---------------- notes ----------------
    after, notes = None, []
    while True:
        b = {"limit": 100, "properties": ["hs_note_body", "hs_timestamp", "hubspot_owner_id"],
             "filterGroups": [{"filters": [{"propertyName": "hs_timestamp", "operator": "GTE", "value": lo}]}]}
        if after: b["after"] = after
        _, r = hs("/crm/v3/objects/notes/search", "POST", b)
        notes += r.get("results", [])
        after = (r.get("paging") or {}).get("next", {}).get("after")
        if not after: break
    nb = collections.defaultdict(collections.Counter)
    other = []
    for n in notes:
        p = n["properties"]; day = ist_day(p.get("hs_timestamp"))
        if day not in DAYS: continue
        who = OWN.get(p.get("hubspot_owner_id"), "(unowned)")
        t = plain(p.get("hs_note_body"))
        if not t: continue
        b_ = classify(t); nb[(day, who)][b_] += 1
        if b_ == "Other": other.append((day, who, t[:120]))

    # ---------------- tasks completed ----------------
    after, tasks = None, []
    while True:
        b = {"limit": 100, "properties": ["hs_task_status", "hs_timestamp", "hubspot_owner_id"],
             "filterGroups": [{"filters": [
                 {"propertyName": "hs_timestamp", "operator": "GTE", "value": lo},
                 {"propertyName": "hs_task_status", "operator": "EQ", "value": "COMPLETED"}]}]}
        if after: b["after"] = after
        _, r = hs("/crm/v3/objects/tasks/search", "POST", b)
        tasks += r.get("results", [])
        after = (r.get("paging") or {}).get("next", {}).get("after")
        if not after: break
    tk = collections.Counter()
    for t in tasks:
        p = t["properties"]; day = ist_day(p.get("hs_timestamp"))
        if day in DAYS: tk[(day, OWN.get(p.get("hubspot_owner_id"), "(unowned)"))] += 1

    people = sorted({w for (_, w) in list(stage) + list(nb)} | {w for (_, w) in tk})
    out = []
    A = out.append
    A(f"# Full-funnel activity by person\n")
    A(f"Pulled live from HubSpot at {datetime.datetime.now(IST):%Y-%m-%d %H:%M} IST. "
      f"Days: {', '.join(DAYS)}. Everyone measured on every KPI — no roles.\n")

    for day in DAYS:
        A(f"\n## {day}\n")
        A("### Stage KPIs — work that moved a deal\n")
        A("| Person | " + " | ".join(l for _, l in KPI) + " | Deals touched |")
        A("|---|" + "---|"*(len(KPI)+1))
        for w in people:
            c = stage.get((day, w))
            if not c and not touched.get((day, w)): continue
            A(f"| {w} | " + " | ".join(str(c[k] if c else 0) for k, _ in KPI) +
              f" | {len(touched.get((day,w), ()))} |")
        A("\n### Note buckets — work stages cannot see\n")
        A("| Person | " + " | ".join(BUCKETS) + " | Notes | Tasks done |")
        A("|---|" + "---|"*(len(BUCKETS)+2))
        any_ = False
        for w in people:
            c = nb.get((day, w)); t = tk.get((day, w), 0)
            if not c and not t: continue
            any_ = True
            tot = sum(c.values()) if c else 0
            A(f"| {w} | " + " | ".join(str(c[b] if c else 0) for b in BUCKETS) + f" | {tot} | {t} |")
        if not any_: A("| _no notes or completed tasks_ | " + " | ".join("" for _ in BUCKETS) + " | | |")

    A("\n## Coverage check\n")
    A(f"- notes classified: {sum(sum(c.values()) for c in nb.values())}, "
      f"of which unmatched (`Other`): {sum(c['Other'] for c in nb.values())}")
    A(f"- call objects in HubSpot: **0** — dial counts below come from notes, not call logs")
    if other:
        A("\nUnmatched notes (these are what the bucket rules miss — review and add rules):\n")
        for d_, w, t in other[:20]: A(f"- `{d_}` **{w}** — {t}")

    text = "\n".join(out)
    print("\n" + text)
    if MD:
        open(os.path.join(HUB, MD), "w", encoding="utf-8").write(text)
        print(f"\nwrote {MD}")


if __name__ == "__main__":
    main()
