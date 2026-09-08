# -*- coding: utf-8 -*-
"""Everything in the LinkedIn-ads master sheet that is NOT marked `yes` -> Dead/ColdCall/WrongFit.

The team vetted this list in the sheet but the verdicts were never written back to HubSpot:
245 rows are marked `not` in the sheet while 228 of them still sit at Cold Call, padding
Lamiya's and Yuktha's live queues with work already judged irrelevant.

The 4 rows marked `yes` are left completely alone — they already carry +91 mobiles, are already
on the campaign tag and are already assigned.

Rows already in ANY Dead/* stage are skipped rather than re-stamped. Moving a deal that sits at
Dead/GMeet/wrong fit into Dead/ColdCall/WrongFit would erase the fact that a meeting actually
took place, and gains nothing: it is out of the calling queue either way.

Stage id is resolved PER PIPELINE from the deal's own pipeline, not hardcoded — Scraped and
Campaign have different ids for the identically-named stage.

Usage: python3 master_wrongfit.py [--apply]
"""
import os, sys, csv, json, time, collections, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(HERE)
env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
H = {"Authorization": "Bearer " + env["hubspot_key"], "Content-Type": "application/json"}
SHEET = os.path.join(HERE, "LinekdinAdsMasterList - Sheet1.csv")
APPLY = "--apply" in sys.argv


def hs(u, m="GET", b=None):
    d = json.dumps(b).encode() if b is not None else None
    for a in range(6):
        try:
            r = urllib.request.Request("https://api.hubapi.com" + u, data=d, method=m, headers=H)
            with urllib.request.urlopen(r, timeout=60) as x:
                t = x.read().decode(); return x.status, (json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and a < 5: time.sleep(2*(a+1)); continue
            return e.code, {"raw": e.read().decode()[:200]}
        except Exception:
            if a == 5: raise
            time.sleep(3*(a+1))


def main():
    _, pl = hs("/crm/v3/pipelines/deals")
    LAB = {s["id"]: s["label"] for p in pl["results"] for s in p["stages"]}
    # per-pipeline id for the target stage
    WRONGFIT = {p["id"]: next((s["id"] for s in p["stages"] if s["label"] == "Dead/ColdCall/WrongFit"), None)
                for p in pl["results"]}
    _, ow = hs("/crm/v3/owners?limit=200")
    OWN = {o["id"]: f'{o.get("firstName","")} {o.get("lastName","")}'.strip() for o in ow.get("results", [])}

    rows = list(csv.DictReader(open(SHEET, encoding="utf-8-sig")))
    targets = [r for r in rows if (r.get("Relevance") or "").strip().lower() != "yes"]
    kept = [r for r in rows if (r.get("Relevance") or "").strip().lower() == "yes"]
    print(f"sheet rows {len(rows)} | marked yes (untouched) {len(kept)} | candidates {len(targets)}")

    ids = [r["deal_id"] for r in targets]
    live = {}
    for i in range(0, len(ids), 100):
        _, d = hs("/crm/v3/objects/deals/batch/read", "POST",
                  {"properties": ["dealname", "dealstage", "pipeline", "hubspot_owner_id"],
                   "inputs": [{"id": x} for x in ids[i:i+100]]})
        for x in d.get("results", []): live[x["id"]] = x["properties"]
    print(f"resolved live in HubSpot: {len(live)}")

    todo, already, missing = [], [], []
    for r in targets:
        p = live.get(r["deal_id"])
        if not p: missing.append(r); continue
        lab = LAB.get(p.get("dealstage"), "?")
        if lab.startswith("Dead/"):
            already.append((r, lab)); continue
        todo.append((r, p, lab))

    print(f"\nTO MOVE -> Dead/ColdCall/WrongFit : {len(todo)}")
    print(f"already in a Dead/* stage, skipped : {len(already)}")
    for k, v in collections.Counter(l for _, l in already).most_common():
        print(f"      {v:>4}  {k}")
    if missing: print(f"not found in HubSpot               : {len(missing)}")

    print("\nbreakdown of what moves:")
    print("   by current stage:", dict(collections.Counter(l for _, _, l in todo)))
    print("   by owner:        ", dict(collections.Counter(OWN.get(p.get("hubspot_owner_id"), "?") for _, p, _ in todo)))
    print("   by sheet verdict:", dict(collections.Counter((r.get("Relevance") or "(blank)").strip() or "(blank)"
                                                            for r, _, _ in todo)))

    if not APPLY:
        print("\nDRY RUN — nothing changed. Re-run with --apply.")
        return

    ok = fail = 0
    for r, p, lab in todo:
        sid = WRONGFIT.get(p.get("pipeline"))
        if not sid:
            print(f"   FAIL {r['deal_name'][:30]} — no WrongFit stage in pipeline {p.get('pipeline')}")
            fail += 1; continue
        s, _x = hs(f"/crm/v3/objects/deals/{r['deal_id']}", "PATCH", {"properties": {"dealstage": sid}})
        if s in (200, 201): ok += 1
        else: fail += 1; print(f"   FAIL {r['deal_name'][:30]} -> {s}")
        if ok and ok % 50 == 0: print(f"   {ok} moved...", flush=True)
        time.sleep(0.12)
    print(f"\nmoved {ok}, failed {fail}")


main()
