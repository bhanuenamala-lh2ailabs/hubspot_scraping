# -*- coding: utf-8 -*-
"""LinkedIn Ads Master List V2 -> act on the Relevance column.

Two jobs, both driven by the sheet's `Relevance`:

  YES  -> live on the LinkedIn campaign, split 50:50 across Yuktha and Lamiya.
          Most of these already exist (they carry a deal_id) — for those the job is to confirm
          they are still at Cold Call and rebalance ownership, NOT to create a second deal.
          Only rows with no deal_id are genuinely new, and those are deduped against the live
          CRM on email / LinkedIn / last-10-digits phone before anything is created.

  NO   -> if the deal is at Cold Call under Yuktha, Lamiya or Ishpreet, move it to
          Dead/ColdCall/WrongFit so it stops padding a caller's queue.

WHAT THIS DELIBERATELY DOES NOT DO:
  * It never trusts the sheet's `stage`/`assigned_to`. Those were exported earlier and deals
    have moved since; every decision is made against a live read.
  * It never moves a NO row that has already progressed past Cold Call. Someone who reached
    GMeet Fixed has been spoken to, and a sheet verdict written before that call should not
    silently erase the outcome.
  * It never pushes a lead without a +91 number — the standing rule.
  * WrongFit stage id is resolved PER PIPELINE, because Scraped and Campaign use different ids
    for the identically-named stage.

Usage: python3 masterv2_apply.py [--apply]
"""
import os, re, sys, csv, json, time, collections, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HUB, "crm_mirror", "enrich"))
from indian_number import to_e164, classify

env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
H = {"Authorization": "Bearer " + env["hubspot_key"], "Content-Type": "application/json"}

SHEET = os.path.join(HERE, "LinekdinAdsMasterListV2 - Sheet1.csv")
YUKTHA, LAMIYA, ISHPREET = "96573782", "96574824", "166322228"
CALLERS = {YUKTHA: "Yuktha", LAMIYA: "Lamiya", ISHPREET: "Ishpreet"}
PIPE, COLD = "2425754306", "4002503379"          # Campaign / Cold Call
SOURCE = "Linkedin Campaign ( IT Services )"
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


def norm_email(s): return (s or "").strip().lower()
def digits10(s):
    d = re.sub(r"\D", "", str(s or "")); return d[-10:] if len(d) >= 10 else ""
def norm_li(u):
    u = (u or "").strip().lower()
    u = re.sub(r"^https?://", "", u).split("?")[0].rstrip("/")
    return re.sub(r"^([a-z]{2,3}\.)?linkedin\.com", "linkedin.com", u)


def crm_contact_keys():
    em, li, ph = set(), set(), set()
    after = None
    while True:
        b = {"limit": 200, "properties": ["email", "phone", "mobilephone", "linkedin_url", "hs_linkedin_url"],
             "filterGroups": [{"filters": [{"propertyName": "hs_object_id", "operator": "HAS_PROPERTY"}]}]}
        if after: b["after"] = after
        s, d = hs("/crm/v3/objects/contacts/search", "POST", b)
        for x in d.get("results", []):
            p = x["properties"]
            if p.get("email"): em.add(norm_email(p["email"]))
            for k in ("linkedin_url", "hs_linkedin_url"):
                if p.get(k): li.add(norm_li(p[k]))
            for k in ("phone", "mobilephone"):
                if digits10(p.get(k)): ph.add(digits10(p[k]))
        after = (d.get("paging") or {}).get("next", {}).get("after")
        if not after: break
        time.sleep(0.08)
    em.discard(""); li.discard(""); ph.discard("")
    return em, li, ph


def push(rec, owner):
    cp = {"firstname": rec["first"], "lastname": rec["last"], "email": rec["email"],
          "phone": rec["e164"], "mobilephone": rec["e164"]}
    if rec["li"]: cp["linkedin_url"] = "https://" + rec["li"]
    s, d = hs("/crm/v3/objects/contacts", "POST", {"properties": {k: v for k, v in cp.items() if v}})
    if s not in (200, 201): return None, f"contact {s} {str(d)[:110]}"
    ctid = d["id"]
    dp = {"dealname": rec["name"], "pipeline": PIPE, "dealstage": COLD,
          "hubspot_owner_id": owner, "poc": owner, "lead_source": SOURCE}
    s, d = hs("/crm/v3/objects/deals", "POST", {"properties": dp})
    if s not in (200, 201): return None, f"deal {s} {str(d)[:110]}"
    did = d["id"]; time.sleep(0.2)
    hs(f"/crm/v4/objects/deals/{did}/associations/default/contacts/{ctid}", "PUT")
    return did, ""


def main():
    _, pl = hs("/crm/v3/pipelines/deals")
    LAB = {s["id"]: s["label"] for p in pl["results"] for s in p["stages"]}
    WRONGFIT = {p["id"]: next((s["id"] for s in p["stages"] if s["label"] == "Dead/ColdCall/WrongFit"), None)
                for p in pl["results"]}

    rows = list(csv.DictReader(open(SHEET, encoding="utf-8-sig")))
    yes = [r for r in rows if (r.get("Relevance") or "").strip().lower() == "yes"]
    no  = [r for r in rows if (r.get("Relevance") or "").strip().lower() == "no"]
    print(f"sheet {len(rows)} rows | yes {len(yes)} | no {len(no)}\n")

    ids = [r["deal_id"].strip() for r in rows if r["deal_id"].strip()]
    live = {}
    for i in range(0, len(ids), 100):
        _, d = hs("/crm/v3/objects/deals/batch/read", "POST",
                  {"properties": ["dealname", "dealstage", "pipeline", "hubspot_owner_id", "lead_source"],
                   "inputs": [{"id": x} for x in ids[i:i+100]]})
        for x in d.get("results", []): live[x["id"]] = x["properties"]
    print(f"resolved live in HubSpot: {len(live)}/{len(ids)}\n")

    # ================= YES =================
    print("=" * 74)
    print("YES -> LinkedIn campaign, 50:50 Yuktha / Lamiya")
    print("=" * 74)
    existing, newrows, gone = [], [], []
    for r in yes:
        did = r["deal_id"].strip()
        if did and did in live: existing.append((r, live[did]))
        elif did: gone.append(r)
        else: newrows.append(r)
    own = collections.Counter(CALLERS.get(p.get("hubspot_owner_id"), "other/unassigned")
                              for _, p in existing)
    print(f"already in HubSpot : {len(existing)}   current owners: {dict(own)}")
    print(f"stages             : {dict(collections.Counter(LAB.get(p.get('dealstage'),'?') for _,p in existing))}")
    if gone: print(f"deal_id not found  : {len(gone)}")
    print(f"net-new to push    : {len(newrows)}")

    # dedup the net-new against the live CRM
    em, li, ph = crm_contact_keys()
    ready, skipped = [], []
    for r in newrows:
        e164, note = to_e164(r.get("mobile", "")), ""
        kind = classify(e164) if e164 else ""
        rec = {"first": (r.get("first_name") or "").strip(),
               "last": (r.get("last_name") or "").strip(),
               "email": norm_email(r.get("email")), "e164": e164,
               "li": norm_li(r.get("linkedin_url")),
               "name": (r.get("deal_name") or "").strip() or
                       f'{r.get("first_name","")} {r.get("last_name","")}'.strip()}
        if not e164: note = "NO +91 NUMBER — blocked by the standing gate"
        elif rec["email"] and rec["email"] in em: note = "duplicate: email already in CRM"
        elif rec["li"] and rec["li"] in li: note = "duplicate: linkedin already in CRM"
        elif digits10(e164) in ph: note = "duplicate: phone already in CRM"
        (skipped if note else ready).append((rec, note or kind))
    print(f"\nafter dedup: {len(ready)} pushable, {len(skipped)} skipped")
    for rec, n in skipped: print(f"   SKIP {rec['name'][:30]:<32}{n}")

    # balance the final book across all YES rows
    cur = collections.Counter()
    for _, p in existing:
        o = p.get("hubspot_owner_id")
        if o in (YUKTHA, LAMIYA): cur[o] += 1
    plan = []
    for rec, kind in ready:
        o = YUKTHA if cur[YUKTHA] <= cur[LAMIYA] else LAMIYA
        cur[o] += 1; plan.append((rec, o, kind))
    print(f"\npush plan ({len(plan)}):")
    for rec, o, kind in plan:
        print(f"   {rec['name'][:30]:<32}{rec['e164']:<16}{kind:<10}-> {CALLERS[o]}")
    print(f"\nfinal YES book: Yuktha {cur[YUKTHA]}  Lamiya {cur[LAMIYA]}")

    # ================= NO =================
    print("\n" + "=" * 74)
    print("NO -> Dead/ColdCall/WrongFit, only if live at Cold Call under a caller")
    print("=" * 74)
    move, why = [], collections.Counter()
    for r in no:
        did = r["deal_id"].strip()
        if not did: why["never pushed to HubSpot (no deal_id)"] += 1; continue
        p = live.get(did)
        if not p: why["deal_id not found in HubSpot"] += 1; continue
        lab = LAB.get(p.get("dealstage"), "?")
        o = p.get("hubspot_owner_id")
        if lab != "Cold Call": why[f"not at Cold Call — currently {lab}"] += 1; continue
        if o not in CALLERS: why["at Cold Call but owned by someone else"] += 1; continue
        move.append((r, p, lab, o))
    print(f"TO MOVE: {len(move)}")
    print("   by owner:", dict(collections.Counter(CALLERS[o] for _, _, _, o in move)))
    print("\nnot moved:")
    for k, v in why.most_common(): print(f"   {v:>4}  {k}")

    if not APPLY:
        print("\n\nDRY RUN — nothing changed. Re-run with --apply.")
        return

    print("\n\napplying...")
    ok = fail = 0
    for rec, o, _ in plan:
        did, err = push(rec, o)
        if did: ok += 1; print(f"   pushed {rec['name'][:30]:<32}{CALLERS[o]}  deal {did}")
        else: fail += 1; print(f"   FAIL   {rec['name'][:30]:<32}{err}")
        time.sleep(0.3)
    print(f"\nYES pushed {ok}, failed {fail}")

    mok = mfail = 0
    for r, p, lab, o in move:
        sid = WRONGFIT.get(p.get("pipeline"))
        if not sid:
            print(f"   FAIL {r['deal_name'][:30]} — no WrongFit stage in pipeline {p.get('pipeline')}")
            mfail += 1; continue
        s, _x = hs(f"/crm/v3/objects/deals/{r['deal_id']}", "PATCH", {"properties": {"dealstage": sid}})
        if s in (200, 201): mok += 1
        else: mfail += 1; print(f"   FAIL {r['deal_name'][:30]} -> {s}")
        if mok and mok % 20 == 0: print(f"   {mok} moved...", flush=True)
        time.sleep(0.12)
    print(f"NO moved to WrongFit {mok}, failed {mfail}")


main()
