# -*- coding: utf-8 -*-
"""Re-verify every number we pushed from the ready-queue, using SignalHire as the source of truth.

Why: Tracxn's phone column is unreliable — the team measured a ~14% wrong rate, a sample of 15
cross-checked against SignalHire agreed 0/10, ~10% of what we pushed are company switchboards
(dead for a deadpooled company), and some are foreign numbers with no country code that our
validator wrongly stamped +91 on (e.g. Clik `6464800503` = New York 646-480-0503).

Preference order for the number we keep:
  1. SignalHire +91 MOBILE      (verified, reaches the founder)
  2. SignalHire +91 landline
  3. existing number, only if it is +91 MOBILE format
  -> otherwise the lead FAILS the hard gate and is archived off HubSpot.

Usage: python reverify_numbers.py [--dry-run] [--limit N]
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
                t = r.read().decode(); return r.status, (json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429,502,503,504) and a < 3: time.sleep(2); continue
            return e.code, {}
        except Exception:
            if a == 3: return 500, {}
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

def classify(p):
    """-> ('mobile'|'landline'|'foreign'|'bad', '+91XXXXXXXXXX')"""
    raw = str(p or "").strip(); d = re.sub(r"[^\d]", "", raw)
    if raw.startswith("+") and not raw.startswith("+91"): return "foreign", ""
    if len(d) == 11 and d.startswith("1"): return "foreign", ""
    if d.startswith("91") and len(d) == 12: d = d[-10:]
    if len(d) != 10: return "bad", ""
    if d[0] in "6789": return "mobile", "+91"+d
    if d[0] in "2345":  return "landline", "+91"+d
    return "bad", ""

def sh_phones(ident):
    if not ident: return [], "none"
    try: d = sh("/candidate/search", {"items":[ident], "withoutWaterfall": True})
    except urllib.error.HTTPError as e:
        return [], ("quota" if e.code == 402 else "err")
    except Exception: return [], "err"
    res = d if isinstance(d, list) else d.get("results", [])
    out = []
    for it in res or []:
        if isinstance(it, dict) and it.get("status") == "success":
            for c in (it.get("candidate", {}) or {}).get("contacts", []) or []:
                if "phone" in str(c.get("type","")).lower() and isinstance(c.get("value"), str):
                    out.append(c["value"])
    return out, "ok"

def find_founder(company):
    try:
        d = sh("/candidate/searchByQuery", {"currentCompany": company, "size": 6,
             "currentTitle":"Founder OR Co-Founder OR CEO OR Owner OR Managing Director OR Director"})
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
    for i,a in enumerate(sys.argv):
        if a == "--limit": limit = int(sys.argv[i+1])
    pushed = json.load(open(os.path.join(HERE,"ready_queue_pushed.json"), encoding="utf-8"))
    if limit: pushed = pushed[:limit]
    c0 = credits()
    print(f"re-verifying {len(pushed)} pushed leads | credits={c0}", flush=True)
    stats = {"upgraded":0,"kept":0,"failed_gate":0,"quota":0}
    failed = []
    for i, r in enumerate(pushed):
        did = r["deal_id"]; cur = r.get("phone","")
        curkind, curnorm = classify(cur)
        phones, status = sh_phones(r.get("ident"))
        if status == "quota":
            stats["quota"] += 1; print("  !! SignalHire quota hit — stopping", flush=True); break
        if not phones:                                  # fall back to founder discovery
            prof = find_founder(r["company"])
            if prof:
                uid = prof.get("uid") or prof.get("profileUid")
                if uid: phones, status = sh_phones(uid)
            time.sleep(0.2)
        best = ""; bestkind = ""
        for p in phones:
            k, n = classify(p)
            if k == "mobile": best, bestkind = n, "mobile"; break
            if k == "landline" and not best: best, bestkind = n, "landline"
        if best and best != curnorm:
            if not dry:
                s, a = hs(f"/crm/v4/objects/deals/{did}/associations/contacts")
                cids = [str(x["toObjectId"]) for x in a.get("results",[])]
                if cids: hs(f"/crm/v3/objects/contacts/{cids[0]}","PATCH",{"properties":{"phone":best,"mobilephone":best}})
            r["phone"] = best; r["phone_source"] = "signalhire-"+bestkind
            stats["upgraded"] += 1
            print(f"  [{i+1}] UPGRADED {r['company'][:24]:24} {cur:16} -> {best} ({bestkind})", flush=True)
        elif curkind == "mobile":
            r["phone_source"] = "tracxn-mobile-unverified"; stats["kept"] += 1
        else:
            # no SignalHire number AND the existing one is a landline/foreign/bad -> fails the gate
            r["phone_source"] = "FAILED-GATE"; stats["failed_gate"] += 1; failed.append(r)
            print(f"  [{i+1}] GATE-FAIL {r['company'][:24]:24} had {cur or '(none)'} ({curkind}), SignalHire has no +91", flush=True)
        time.sleep(0.35)
    if not dry and not limit:      # never let a dry/limited run overwrite the full record
        json.dump(pushed, open(os.path.join(HERE,"ready_queue_pushed.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(failed, open(os.path.join(HERE,"reverify_failed_gate.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
    c1 = credits()
    print(f"\n{'DRY ' if dry else ''}upgraded {stats['upgraded']} | kept (already +91 mobile) {stats['kept']} | "
          f"FAILED GATE {stats['failed_gate']} | credits {c0} -> {c1} (used {(c0 or 0)-(c1 or 0)})")
    if failed and not dry:
        print(f"\n  {len(failed)} fail the +91 hard gate -> archiving them off HubSpot")
        ids = [f["deal_id"] for f in failed]
        for j in range(0, len(ids), 100):
            hs("/crm/v3/objects/deals/batch/archive","POST",{"inputs":[{"id":x} for x in ids[j:j+100]]})
        print(f"  archived {len(ids)} (kept in reverify_failed_gate.json)")

if __name__ == "__main__":
    main()
