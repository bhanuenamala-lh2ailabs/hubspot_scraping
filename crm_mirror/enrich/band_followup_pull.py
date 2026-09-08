# -*- coding: utf-8 -*-
"""Data pull for the per-band daily follow-up report (stage_ownership.py bands).

STANDARD, REUSABLE DATA LAYER. Deterministic: pulls deals, stage-entry timestamps (days in
current stage), notes (text + age), and the two hard-gate fields (gmeet1_link, metadata_link).
Buckets each deal by band + staleness tier. Outputs one JSON blob with everything a report
writer needs, per band per person.

This script does NOT write the "Issue"/"Action" prose columns — that step reads actual note
text and needs judgment (see band_followup_report.py or a human/LLM pass). Keeping the two
apart means the mechanical half here can run unattended forever; only the prose half needs a
human or an LLM call wired in later.

Usage: python3 band_followup_pull.py [--out FILE.json]
"""
import os, sys, json, re, datetime, html
import stage_ownership as SO

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, ".env"), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
H = {"Authorization": "Bearer " + env["hubspot_key"], "Content-Type": "application/json"}
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
OUT = None
for i, a in enumerate(sys.argv):
    if a == "--out": OUT = sys.argv[i+1]

import urllib.request, urllib.error, time
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

def plain(h):
    t = re.sub(r"<[^>]+>", " ", h or "")
    return html.unescape(re.sub(r"\s+", " ", t)).strip()

def days_ago(ts):
    if not ts: return None
    try:
        dt = datetime.datetime.fromisoformat(str(ts).replace("Z","+00:00")).astimezone(IST)
        return (datetime.datetime.now(IST) - dt).days
    except Exception:
        return None

def when(ts):
    try:
        return datetime.datetime.fromisoformat(str(ts).replace("Z","+00:00")).astimezone(IST).strftime("%d %b")
    except Exception:
        return ""

NAME_OF = {"96573782": "Yuktha", "96574824": "Lamiya", "166322228": "Ishpreet", "166262056": "Shobit"}
ID_OF = {v: k for k, v in NAME_OF.items()}

PROPS = ["dealname", "dealstage", "hubspot_owner_id", "gmeet1_link", "gmeet1_date",
         "gmeet1_outcome", "metadata_link", "createdate", "lead_source", "poc"]

def pull_deals():
    _, pd = hs("/crm/v3/pipelines/deals")
    STG = {s["id"]: s["label"] for p in pd["results"] for s in p["stages"]}
    ids, after = [], None
    while True:
        b = {"limit": 100, "properties": ["dealname"], "filterGroups": []}
        if after: b["after"] = after
        _, r = hs("/crm/v3/objects/deals/search", "POST", b)
        ids += [x["id"] for x in r.get("results", [])]
        after = (r.get("paging") or {}).get("next", {}).get("after")
        if not after: break
    deals = []
    for i in range(0, len(ids), 50):
        _, r = hs("/crm/v3/objects/deals/batch/read", "POST",
                  {"inputs": [{"id": x} for x in ids[i:i+50]], "properties": PROPS,
                   "propertiesWithHistory": ["dealstage"]})
        deals += r.get("results", [])
    return deals, STG

def pull_notes(ids):
    d2n, nids = {}, set()
    for i in range(0, len(ids), 100):
        _, r = hs("/crm/v4/associations/deals/notes/batch/read", "POST",
                  {"inputs": [{"id": x} for x in ids[i:i+100]]})
        for row in r.get("results", []):
            ns = [str(t["toObjectId"]) for t in row.get("to", [])]
            d2n[str(row["from"]["id"])] = ns; nids |= set(ns)
    nl = sorted(nids); nbody = {}
    for i in range(0, len(nl), 100):
        _, r = hs("/crm/v3/objects/notes/batch/read", "POST",
                  {"inputs": [{"id": x} for x in nl[i:i+100]],
                   "properties": ["hs_note_body", "hs_timestamp"]})
        for x in r.get("results", []):
            nbody[x["id"]] = {"text": plain(x["properties"].get("hs_note_body") or ""),
                              "ts": x["properties"].get("hs_timestamp")}
    return d2n, nbody

def main():
    deals, STG = pull_deals()
    ids = [d["id"] for d in deals]
    d2n, nbody = pull_notes(ids)

    result = {"CALLERS": {"Yuktha": [], "Lamiya": []}, "MEETING": {"Ishpreet": []},
              "COMMERCIAL": {"Shobit": []}, "generated_at": datetime.datetime.now(IST).isoformat()}

    for dl in deals:
        p = dl["properties"]
        lab = STG.get(p.get("dealstage"), p.get("dealstage") or "")
        if lab.startswith("Dead/") or lab == "Closed/Won": continue
        band, reason = SO.band_for(lab, p)
        if band is None: continue

        # days in current stage: last human (CRM_UI) or any transition INTO this stage
        hist = sorted((dl.get("propertiesWithHistory", {}).get("dealstage") or []),
                      key=lambda e: e.get("timestamp",""))
        entered_ts = None
        for e in reversed(hist):
            if STG.get(e.get("value")) == lab or e.get("value") == p.get("dealstage"):
                entered_ts = e.get("timestamp"); break
        if entered_ts is None and hist: entered_ts = hist[-1].get("timestamp")
        if entered_ts is None: entered_ts = p.get("createdate")
        days = days_ago(entered_ts)

        notes = []
        for nid in d2n.get(dl["id"], []):
            nb = nbody.get(nid)
            if nb and nb["text"]:
                notes.append(nb)
        notes.sort(key=lambda n: n.get("ts") or "")
        last_note = notes[-1] if notes else None

        owner_id = p.get("hubspot_owner_id")
        rec = {
            "deal_id": dl["id"], "name": p.get("dealname"), "stage": lab,
            "band_reason": reason, "days_in_stage": days,
            "entered_stage_str": when(entered_ts),
            "owner": NAME_OF.get(owner_id, "(none)"),
            "gmeet1_link": p.get("gmeet1_link") or "", "gmeet1_date": p.get("gmeet1_date") or "",
            "metadata_link": p.get("metadata_link") or "",
            "note_count": len(notes),
            "last_note_text": last_note["text"] if last_note else "",
            "last_note_days_ago": days_ago(last_note["ts"]) if last_note else None,
            "lead_source": p.get("lead_source") or "",
        }

        if band == "CALLERS":
            who = NAME_OF.get(owner_id)
            if who in ("Yuktha", "Lamiya"):
                result["CALLERS"][who].append(rec)
            else:
                result["CALLERS"].setdefault("(unassigned)", []).append(rec)
        elif band == "MEETING":
            result["MEETING"]["Ishpreet"].append(rec)
        elif band == "COMMERCIAL":
            result["COMMERCIAL"]["Shobit"].append(rec)

    out = OUT or os.path.join(HERE, "band_followup_data.json")
    json.dump(result, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"wrote {out}")
    for band, people in result.items():
        if band == "generated_at": continue
        for person, recs in people.items():
            print(f"  {band}/{person}: {len(recs)} deals")

if __name__ == "__main__":
    main()
