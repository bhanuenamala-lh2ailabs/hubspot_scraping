# -*- coding: utf-8 -*-
"""Apply the wrong-fit engine's verdicts to real HubSpot deals:
  Group A (apollo_reveal + searchq Cold Call deals): move WRONG_FIT to Dead/ColdCall/WrongFit,
           with a note logging the engine's reason for audit/revert purposes.
  Group B (Coimbatore Cold Call deals): leave stage untouched, just add a note flagging the
           concern for the caller to confirm before any action.

Usage: python3 apply_wrongfit_actions.py [--apply]
"""
import os, sys, json, time, urllib.request, urllib.error

HUB = "/Users/bhanu/Desktop/hubspot"
env = {l.split('=', 1)[0].strip().lower(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, ".env"), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
HH = {"Authorization": "Bearer " + env["hubspot_key"], "Content-Type": "application/json"}
DEAD_WRONGFIT_STAGE = "4036687547"
APPLY = "--apply" in sys.argv


def hs(path, method="GET", body=None):
    d = json.dumps(body).encode() if body else None
    req = urllib.request.Request("https://api.hubapi.com" + path, data=d, method=method, headers=HH)
    for a in range(5):
        try:
            r = urllib.request.urlopen(req, timeout=45); t = r.read().decode()
            return r.status, (json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503, 504) and a < 4: time.sleep(2 * (a + 1)); continue
            t = e.read().decode(); return e.code, (json.loads(t) if t else {"raw": t})
        except Exception:
            if a == 4: raise
            time.sleep(2)


def add_note(deal_id, text):
    s, d = hs("/crm/v3/objects/notes", "POST", {
        "properties": {"hs_note_body": text, "hs_timestamp": None},
    })
    # hs_timestamp None isn't valid; HubSpot requires a timestamp — use current via a second call pattern
    return s, d


group_a = json.load(open("/tmp/group_a_wrongfit.json"))
group_b = json.load(open("/tmp/group_b_wrongfit.json"))
print(f"Group A (move to Dead/WrongFit): {len(group_a)}")
print(f"Group B (Coimbatore, note only): {len(group_b)}")

if not APPLY:
    print("\nDRY RUN — nothing written. Re-run with --apply")
    for x in group_a[:5]: print("  A:", x["dealname"][:40], "|", x["reason"][:60])
    for x in group_b[:5]: print("  B:", x["dealname"][:40], "|", x["reason"][:60])
    sys.exit()

moved = fail_a = 0
for x in group_a:
    did = x["deal_id"]
    note_text = (f"[Apify wrong-fit engine] Auto-moved to Dead/ColdCall/WrongFit — "
                 f"{x['reason']}. Flag if this looks wrong; engine has ~13-19% false-positive "
                 f"rate on this rule set, revert if the company is actually a good fit.")
    ts = int(time.time() * 1000)
    s1, d1 = hs("/crm/v3/objects/notes", "POST", {
        "properties": {"hs_note_body": note_text, "hs_timestamp": ts},
        "associations": [{"to": {"id": did}, "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 214}]}]})
    s2, d2 = hs(f"/crm/v3/objects/deals/{did}", "PATCH", {"properties": {"dealstage": DEAD_WRONGFIT_STAGE}})
    if s2 in (200, 201):
        moved += 1
        print(f"  MOVED [{moved}] {x['dealname'][:40]}", flush=True)
    else:
        fail_a += 1
        print(f"  ! FAIL {x['dealname'][:40]}: {s2} {d2}")
    time.sleep(0.15)

flagged = fail_b = 0
for x in group_b:
    did = x["deal_id"]
    note_text = (f"[Apify wrong-fit engine — NEEDS CALLER CONFIRMATION] Possible wrong fit: "
                 f"{x['reason']}. Stage left unchanged — please verify on the call before treating "
                 f"as wrong fit.")
    ts = int(time.time() * 1000)
    s1, d1 = hs("/crm/v3/objects/notes", "POST", {
        "properties": {"hs_note_body": note_text, "hs_timestamp": ts},
        "associations": [{"to": {"id": did}, "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 214}]}]})
    if s1 in (200, 201):
        flagged += 1
        print(f"  FLAGGED [{flagged}] {x['dealname'][:40]}", flush=True)
    else:
        fail_b += 1
        print(f"  ! FAIL {x['dealname'][:40]}: {s1} {d1}")
    time.sleep(0.15)

print(f"\nGroup A: {moved} moved to Dead/WrongFit" + (f", {fail_a} failed" if fail_a else ""))
print(f"Group B: {flagged} flagged with a note" + (f", {fail_b} failed" if fail_b else ""))
