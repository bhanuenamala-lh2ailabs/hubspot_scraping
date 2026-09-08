# -*- coding: utf-8 -*-
"""Hand the deadpool-wave book from Ishpreet/Shobit to Lamiya/Yuktha, and tag it.

Tag: lead_source = "Deadpool Waves 2026-08-04".
`scraped_type` stays "Distressed startups" — it is a radio enum with only two options and
these genuinely are distressed startups; adding an option would change the schema for every
deal. lead_source is free text and is already how we mark provenance (OutFlo, LinkedIn
lead-gen form), so one filter on it isolates exactly this batch.

Each deal also gets a note. These callers are new and the pitch here is NOT the IT-services
pitch: the company is DEAD, the founder has moved on, and the ask is for code they wrote off
years ago. Without that context on the deal, a caller opens "TaxiForSure" and rings a founder
about a company that shut in 2016.

Whole companies move together so two callers never ring the same dead startup.

Usage: python reassign_deadpool.py [--dry-run]
"""
import os, sys, json, time, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
LOG = os.path.join(HERE, "pushed_deadpool.json")
env = {l.split('=', 1)[0].strip().lower(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
HS = env["hubspot_key"]

TAG = "Deadpool Waves 2026-08-04"
NEW_OWNERS = [("96574824", "Lamiya Saleem"), ("96573782", "Yuktha Anand")]


def hs(path, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    for a in range(5):
        try:
            req = urllib.request.Request("https://api.hubapi.com" + path, data=data, method=method,
                headers={"Authorization": "Bearer " + HS, "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=45) as r:
                t = r.read().decode(); return r.status, (json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503, 504) and a < 4: time.sleep(2 * (a + 1)); continue
            return e.code, {"raw": e.read().decode()[:250]}
        except Exception:
            if a == 4: raise
            time.sleep(2)


def note_body(rs):
    r = rs[0]
    who = "; ".join(f"{x['name']} ({x['title'][:34]})" for x in rs)
    return (
        f"DEADPOOL WAVE LEAD — this company is DEAD. Do not pitch it as a live business.<br><br>"
        f"<b>Company:</b> {r['display']}<br>"
        f"<b>Sector wave:</b> {r['wave']}<br>"
        f"<b>Shut down:</b> {r['shutdown']}<br>"
        f"<b>Raised:</b> {r['funding']}<br>"
        f"<b>Status:</b> {r['status']}<br>"
        f"<b>Founder(s) on this deal:</b> {who}<br><br>"
        f"<b>How to open the call:</b> they founded {r['display']}, which shut down. "
        f"They have moved on and almost certainly consider the code worthless. That is the "
        f"opening — we pay for a pre-2024 codebase they have already written off. There is no "
        f"board, no customers and no ongoing business to protect, so the decision is theirs "
        f"alone. Be respectful about the shutdown; it is often a sore subject.<br><br>"
        f"<b>Contact source:</b> SignalHire-verified mobile (this batch was 100% mobile, "
        f"no switchboards). Numbers came from SignalHire only, never a spreadsheet.")


def main():
    dry = "--dry-run" in sys.argv
    rows = json.load(open(LOG, encoding="utf-8"))
    by_co = {}
    for r in rows: by_co.setdefault(r["display"], []).append(r)
    order = sorted(by_co)
    for i, co in enumerate(order):
        oid, onm = NEW_OWNERS[i % 2]
        for r in by_co[co]: r["new_owner"], r["new_owner_name"] = oid, onm

    print(f"{len(rows)} contacts across {len(order)} companies")
    for oid, onm in NEW_OWNERS:
        cs = [c for c in order if by_co[c][0]["new_owner"] == oid]
        print(f"  -> {onm:16} {len(cs):>2} companies, "
              f"{sum(len(by_co[c]) for c in cs):>3} contacts")
    if dry:
        for co in order:
            print(f"   {by_co[co][0]['new_owner_name'][:8]:10} {co}")
        return

    ok = fail = 0
    for i, co in enumerate(order, 1):
        rs = by_co[co]; did = rs[0]["deal_id"]
        st, d = hs(f"/crm/v3/objects/deals/{did}", "PATCH", {"properties": {
            "hubspot_owner_id": rs[0]["new_owner"], "poc": rs[0]["new_owner"],
            "lead_source": TAG}})
        if st != 200:
            print(f"  ERR deal {co}: {st} {d}"); fail += 1; continue
        # contact ownership follows the deal, so the caller sees them in their own views
        for r in rs:
            if r.get("contact_id"):
                hs(f"/crm/v3/objects/contacts/{r['contact_id']}", "PATCH",
                   {"properties": {"hubspot_owner_id": r["new_owner"]}})
        s2, n = hs("/crm/v3/objects/notes", "POST", {"properties": {
            "hs_note_body": note_body(rs), "hs_timestamp": int(time.time() * 1000)}})
        if n.get("id"):
            hs(f"/crm/v4/objects/notes/{n['id']}/associations/default/deals/{did}", "PUT")
        ok += 1
        print(f"  [{i:>2}/{len(order)}] {rs[0]['new_owner_name'][:8]:10} {co[:28]:30} "
              f"deal={did} contacts={len(rs)} tagged+noted", flush=True)
        time.sleep(0.2)

    json.dump(rows, open(LOG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\nreassigned {ok} companies ({fail} failed), tagged lead_source='{TAG}'")


if __name__ == "__main__":
    main()
