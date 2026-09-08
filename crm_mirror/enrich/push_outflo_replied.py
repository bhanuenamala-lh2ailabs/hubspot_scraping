# -*- coding: utf-8 -*-
"""Push the net-new OutFlo responders for a RELEVANCE CHECK — deliberately un-enriched.

This intentionally bypasses the standing "+91 or it doesn't go" rule, on explicit
instruction and for a good reason: the caller's first job here is only to read the LinkedIn
profile and mark the lead relevant or irrelevant. Enriching first would burn SignalHire
credits on leads that turn out to be irrelevant. Numbers get pulled AFTER the triage, only
for the ones marked relevant.

So every deal carries the LinkedIn URL and enough profile context to make that judgement,
and NO phone. Nothing here is callable yet — it is a reading task, not a calling task.

Pipeline: Campaign (same as Yash's OutFlo book). Stage: Cold Call.
Split: alternating between Lamiya and Yuktha.
Tag: lead_source = "OutFlo Replied - Relevance Check"

Usage: python push_outflo_replied.py [--dry-run]
"""
import os, sys, json, time, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
env = {l.split('=', 1)[0].strip().lower(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
HS = env["hubspot_key"]

PIPE = "2425754306"; COLDCALL = "4002503379"
TAG = "OutFlo Replied - Relevance Check"
OWNERS = [("96574824", "Lamiya Saleem"), ("96573782", "Yuktha Anand")]


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
            return e.code, {"raw": e.read().decode()[:300]}
        except Exception:
            if a == 4: raise
            time.sleep(2)


def ensure_tag_option():
    """lead_source is a dropdown now — a value that is not an option cannot be set."""
    st, p = hs("/crm/v3/properties/deals/lead_source")
    opts = p.get("options") or []
    if any(o["value"] == TAG for o in opts):
        print(f"tag option already present: {TAG}"); return True
    opts.append({"label": TAG, "value": TAG, "displayOrder": len(opts), "hidden": False})
    st, d = hs("/crm/v3/properties/deals/lead_source", "PATCH", {"options": opts})
    print(f"added dropdown option {TAG!r} -> HTTP {st}")
    return st == 200


def note_body(r):
    return (
        f"<b>RELEVANCE CHECK — read the LinkedIn profile, then mark relevant or irrelevant.</b><br>"
        f"Do not call. There is no phone on this deal yet, on purpose: we enrich only the ones "
        f"you mark relevant, so no credits are spent on leads that turn out not to fit.<br><br>"
        f"<b>Person:</b> {r['name']}<br>"
        f"<b>Title:</b> {r['title'] or '(none given)'}<br>"
        f"<b>Company:</b> {r['company']}<br>"
        f"<b>Location:</b> {r['location'] or '-'}<br>"
        f"<b>LinkedIn:</b> <a href=\"{r['linkedin']}\">{r['linkedin']}</a><br>"
        f"<b>Headline:</b> {r['headline'] or '-'}<br><br>"
        f"<b>Source:</b> OutFlo {r['bucket']} campaign — <b>this person REPLIED</b> to our "
        f"LinkedIn outreach (sender: {r['sender'] or '-'}). Last action: {r['last_action'] or '-'}.<br><br>"
        f"<b>What makes it relevant:</b> an Indian IT-services firm or product company that "
        f"could own pre-2024 client code, with this person senior enough to decide. "
        f"<b>Irrelevant:</b> an employee at a large corporate (Accenture, PwC, Shell, Uber and "
        f"the like) who cannot sell company IP, a student, or a recruiter.<br>"
        f"Write your verdict in the deal notes — we read those to decide what to enrich next.")


def main():
    dry = "--dry-run" in sys.argv
    rows = json.load(open(os.path.join(HERE, "outflo_replied_master.json"), encoding="utf-8"))
    for i, r in enumerate(rows):
        oid, onm = OWNERS[i % 2]
        r["owner"], r["owner_name"] = oid, onm
    print(f"master list: {len(rows)}")
    for oid, onm in OWNERS:
        print(f"   {onm:16} {sum(1 for r in rows if r['owner'] == oid)}")
    if dry:
        for r in rows:
            print(f"   {r['owner_name'][:8]:10} {r['deal_name'][:30]:32} {r['bucket']:10} {r['linkedin'][:52]}")
        return
    if not ensure_tag_option():
        print("could not add the dropdown option — aborting so nothing lands untagged"); return

    done = []
    for i, r in enumerate(rows, 1):
        s, d = hs("/crm/v3/objects/companies/search", "POST", {"limit": 1, "properties": ["name"],
            "filterGroups": [{"filters": [{"propertyName": "name", "operator": "EQ", "value": r["company"]}]}]})
        coid = d["results"][0]["id"] if d.get("results") else \
            hs("/crm/v3/objects/companies", "POST", {"properties": {"name": r["company"]}})[1].get("id")
        cp = {"firstname": r["first"] or r["name"].split(" ")[0],
              "lastname": r["last"] or " ".join(r["name"].split(" ")[1:]),
              "company": r["company"], "jobtitle": (r["title"] or "")[:100],
              "linkedin_url": r["linkedin"], "city": (r["location"] or "")[:60]}
        s, d = hs("/crm/v3/objects/contacts/search", "POST", {"limit": 1, "properties": ["email"],
            "filterGroups": [{"filters": [{"propertyName": "linkedin_url", "operator": "EQ", "value": r["linkedin"]}]}]})
        ctid = d["results"][0]["id"] if d.get("results") else None
        if ctid: hs(f"/crm/v3/objects/contacts/{ctid}", "PATCH", {"properties": {k: v for k, v in cp.items() if v}})
        else:
            s, d = hs("/crm/v3/objects/contacts", "POST", {"properties": {k: v for k, v in cp.items() if v}})
            ctid = d.get("id")
        s, d = hs("/crm/v3/objects/deals", "POST", {"properties": {
            "dealname": r["deal_name"], "pipeline": PIPE, "dealstage": COLDCALL,
            "hubspot_owner_id": r["owner"], "poc": r["owner"], "lead_source": TAG,
            "linkedin_url": r["linkedin"], "hs_priority": "high"}})
        did = d.get("id")
        if not did: print(f"  ERR deal {r['deal_name']}: {d}"); continue
        time.sleep(0.3)
        if coid: hs(f"/crm/v4/objects/deals/{did}/associations/default/companies/{coid}", "PUT")
        if ctid:
            hs(f"/crm/v4/objects/deals/{did}/associations/default/contacts/{ctid}", "PUT")
            if coid: hs(f"/crm/v4/objects/contacts/{ctid}/associations/default/companies/{coid}", "PUT")
        s, n = hs("/crm/v3/objects/notes", "POST", {"properties": {
            "hs_note_body": note_body(r), "hs_timestamp": int(time.time() * 1000)}})
        if n.get("id"):
            hs(f"/crm/v4/objects/notes/{n['id']}/associations/default/deals/{did}", "PUT")
        r.update({"deal_id": did, "contact_id": ctid, "company_id": coid}); done.append(r)
        print(f"  [{i:>2}/{len(rows)}] {r['owner_name'][:8]:10} {r['deal_name'][:26]:28} "
              f"{r['bucket']:10} deal={did}", flush=True)
    json.dump(done, open(os.path.join(HERE, "pushed_outflo_replied.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\nPUSHED {len(done)} | tag: lead_source = \"{TAG}\" | NO phone numbers, by design")


if __name__ == "__main__":
    main()
