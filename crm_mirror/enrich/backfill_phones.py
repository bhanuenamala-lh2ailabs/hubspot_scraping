# -*- coding: utf-8 -*-
"""Backfill +91 mobiles on Cold Call deals that don't have one.

Policy (2026-08-03): nothing lives in HubSpot's call queue without a valid Indian
mobile. This finds every Cold Call deal whose contact lacks one and tries, in order:
  1. reveal from the contact's LinkedIn URL   (cached = free)
  2. reveal from the contact's email
  3. SignalHire founder title-search on the company, then reveal that profile

Indonesian OutFlo leads are skipped (they cannot have +91 numbers).
Usage: python backfill_phones.py [--dry-run] [--limit N]
"""
import os, sys, json, re, time, urllib.request, urllib.error
HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB,'.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
HS, SH = env["hubspot_key"], env["signal_hire"]
try: from rapidfuzz import fuzz
except Exception: fuzz = None

def hs(p, m="GET", b=None):
    d = json.dumps(b).encode() if b is not None else None
    for a in range(4):
        try:
            req = urllib.request.Request("https://api.hubapi.com"+p, data=d, method=m,
                headers={"Authorization":"Bearer "+HS,"Content-Type":"application/json"})
            with urllib.request.urlopen(req, timeout=45) as r:
                t = r.read().decode(); return json.loads(t) if t else {}
        except Exception:
            if a == 3: return {}
            time.sleep(2)

def sh(p, b):
    req = urllib.request.Request("https://www.signalhire.com/api/v1"+p, data=json.dumps(b).encode(),
        method="POST", headers={"apikey":SH,"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=60) as r: return json.loads(r.read().decode())

def credits():
    try:
        req = urllib.request.Request("https://www.signalhire.com/api/v1/credits", headers={"apikey":SH})
        return json.loads(urllib.request.urlopen(req, timeout=20).read().decode())["credits"]
    except Exception: return None

def india(p):
    raw = str(p or "").strip(); d = re.sub(r"[^\d]", "", raw)
    if raw.startswith("+1") or (len(d) == 11 and d.startswith("1")): return ""
    if raw.startswith("+91") or (d.startswith("91") and len(d) == 12):
        d = d[-10:]; return "+91"+d if len(d) == 10 and d[0] in "23456789" else ""
    if len(d) == 10 and d[0] in "23456789": return "+91"+d
    return ""

def reveal(ident):
    if not ident: return "", ""
    try: d = sh("/candidate/search", {"items":[ident], "withoutWaterfall": True})
    except Exception: return "", ""
    res = d if isinstance(d, list) else d.get("results", [])
    ph, em = [], []
    for it in res or []:
        if isinstance(it, dict) and it.get("status") == "success":
            for c in (it.get("candidate", {}) or {}).get("contacts", []) or []:
                t = str(c.get("type","")).lower(); v = c.get("value")
                if not isinstance(v, str): continue
                if "phone" in t: ph.append(v)
                elif "email" in t and "@" in v: em.append(v)
    return next((india(x) for x in ph if india(x)), ""), next((x for x in em if "@" in x), "")

def find_founder(company):
    try:
        d = sh("/candidate/searchByQuery", {"currentCompany": company, "size": 6,
             "currentTitle": "Founder OR Co-Founder OR CEO OR Owner OR Managing Director OR Director"})
    except Exception: return None
    cl = (company or "").lower(); best = None; bs = 0
    for p in (d.get("profiles") or []):
        if not isinstance(p, dict): continue
        cs = 0
        for e in (p.get("experience") or []):
            c = str(e.get("company") or "").lower()
            cs = max(cs, fuzz.token_set_ratio(cl, c) if fuzz else (90 if (cl in c or c in cl) else 0))
        if cs >= 80 and cs > bs: bs = cs; best = p
    return best

def main():
    dry = "--dry-run" in sys.argv; limit = None
    for i, a in enumerate(sys.argv):
        if a == "--limit": limit = int(sys.argv[i+1])
    own = {o["id"]: f"{o.get('firstName','')} {o.get('lastName','')}".strip()
           for o in hs("/crm/v3/owners?limit=100").get("results", [])}
    COLD = [x["id"] for pid in ("default","2425754306")
            for x in hs(f"/crm/v3/pipelines/deals/{pid}").get("stages", []) if x["label"] == "Cold Call"]
    after, deals = None, []
    while True:
        b = {"limit":100,"properties":["dealname","hubspot_owner_id","lead_source","linkedin_url"],
             "filterGroups":[{"filters":[{"propertyName":"dealstage","operator":"IN","values":COLD}]}]}
        if after: b["after"] = after
        d = hs("/crm/v3/objects/deals/search","POST",b); deals += d.get("results", [])
        after = d.get("paging",{}).get("next",{}).get("after")
        if not after: break
    ids = [x["id"] for x in deals]; d2c = {}
    for i in range(0, len(ids), 100):
        d = hs("/crm/v4/associations/deals/contacts/batch/read","POST",{"inputs":[{"id":x} for x in ids[i:i+100]]})
        for r in d.get("results", []):
            t = [str(y["toObjectId"]) for y in r.get("to", [])]
            if t: d2c[str(r["from"]["id"])] = t[0]
        time.sleep(0.04)
    cids = sorted(set(d2c.values())); cons = {}
    for i in range(0, len(cids), 100):
        d = hs("/crm/v3/objects/contacts/batch/read","POST",
               {"properties":["phone","mobilephone","email","linkedin_url","firstname","lastname"],
                "inputs":[{"id":c} for c in cids[i:i+100]]})
        for r in d.get("results", []): cons[str(r["id"])] = r.get("properties", {})
        time.sleep(0.04)
    todo = []
    for x in deals:
        p = x["properties"]
        if "Indonesia" in (p.get("lead_source") or ""): continue      # cannot have +91
        cid = d2c.get(x["id"]); c = cons.get(cid, {}) if cid else {}
        # SAFETY (2026-08-03): a deal with NO contact association is NOT proof of "no phone" —
        # HubSpot's association index lags behind creation. Archiving on that basis wrongly
        # removed 6 freshly-created deals. Skip them; they need review, not deletion.
        if not cid: continue
        if any(india(v) for v in (c.get("mobilephone"), c.get("phone"))): continue
        todo.append({"deal_id":x["id"],"name":p.get("dealname"),
                     "owner":own.get(p.get("hubspot_owner_id"),"?"),"cid":cid,
                     "li":(c.get("linkedin_url") or p.get("linkedin_url") or ""),
                     "email":c.get("email") or "", "src":p.get("lead_source") or ""})
    if limit: todo = todo[:limit]
    c0 = credits()
    print(f"Cold Call deals missing a +91 mobile (excl. Indonesia): {len(todo)} | credits={c0}", flush=True)
    fixed = failed = 0
    for r in todo:
        ph = em = ""
        for ident in (r["li"], r["email"]):
            if ident and not ph:
                ph, em2 = reveal(ident); em = em or em2
        if not ph:
            prof = find_founder(r["name"])
            if prof:
                uid = prof.get("uid") or prof.get("profileUid")
                if uid:
                    ph2, em2 = reveal(uid); ph = ph or ph2; em = em or em2
        if ph and not dry and r["cid"]:
            hs(f"/crm/v3/objects/contacts/{r['cid']}","PATCH",
               {"properties":{"phone":ph,"mobilephone":ph, **({"email":em} if (em and not r["email"]) else {})}})
        if ph: fixed += 1; print(f"  OK   {r['owner'][:12]:12} {str(r['name'])[:26]:26} -> {ph}", flush=True)
        else:  failed += 1; print(f"  --   {r['owner'][:12]:12} {str(r['name'])[:26]:26} no number found", flush=True)
        time.sleep(0.4)
    c1 = credits()
    print(f"\n{'DRY ' if dry else ''}fixed {fixed} | still missing {failed} | credits {c0} -> {c1} (used {(c0 or 0)-(c1 or 0)})")

if __name__ == "__main__":
    main()
