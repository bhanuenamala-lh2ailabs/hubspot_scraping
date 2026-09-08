# -*- coding: utf-8 -*-
"""Backfill the founder LinkedIn URL onto the 200 Sales-Navigator deals pushed on 7 Aug.

WHY THIS EXISTS: aug7_salesnav_enrich.py read the profile URL from the wrong place —
`profile.social[].url` on the SEARCH result, when SignalHire returns it as
`candidate.social[].link` on the REVEAL result (see push_deadpool.py, which does it right).
Wrong object and wrong key, so it silently produced "" for all 300 rows instead of failing.
Everything else landed; only the LinkedIn is missing.

Recovery route: /candidate/search accepts EMAIL addresses as items, so the profile can be
re-fetched without a single search call — which matters because the daily SEARCH quota is
exhausted, while reveals draw on credits. Re-revealing a profile already revealed today is
served from cache.

The 8 deals with no email cannot be recovered this way and are listed at the end for a
search-based pass once the quota resets.

Usage: python aug7_backfill_linkedin.py [--apply]
"""
import os, re, sys, json, time, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
HS, SH = env["hubspot_key"], env["signal_hire"]
H = {"Authorization": "Bearer " + HS, "Content-Type": "application/json"}
PUSHED = os.path.join(HERE, "aug7_salesnav_pushed.json")
OUT = os.path.join(HERE, "aug7_linkedin_backfill.json")
APPLY = "--apply" in sys.argv
BATCH = 10


def hs(path, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    for a in range(6):
        try:
            req = urllib.request.Request("https://api.hubapi.com" + path, data=data, method=method, headers=H)
            with urllib.request.urlopen(req, timeout=60) as r:
                t = r.read().decode(); return r.status, (json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and a < 5: time.sleep(2*(a+1)); continue
            return e.code, {"raw": e.read().decode()[:200]}
        except Exception:
            if a == 5: raise
            time.sleep(3*(a+1))


def credits():
    try:
        r = urllib.request.Request("https://www.signalhire.com/api/v1/credits", headers={"apikey": SH})
        return json.loads(urllib.request.urlopen(r, timeout=20).read().decode()).get("credits")
    except Exception: return None


def reveal_many(items):
    """items may be emails. -> {key_lower: linkedin_url}"""
    req = urllib.request.Request("https://www.signalhire.com/api/v1/candidate/search",
        data=json.dumps({"items": items, "withoutWaterfall": True}).encode(), method="POST",
        headers={"apikey": SH, "Content-Type": "application/json"})
    for a in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                d = json.loads(r.read().decode()); break
        except urllib.error.HTTPError as e:
            if e.code == 402: return {"__quota__": True}
            if e.code in (429, 500, 502, 503, 504) and a < 3: time.sleep(4*(a+1)); continue
            return {}
        except Exception:
            if a < 3: time.sleep(3*(a+1)); continue
            return {}
    else: return {}
    res = d if isinstance(d, list) else d.get("results", [])
    out = {}
    for it in res or []:
        if not (isinstance(it, dict) and it.get("status") == "success"): continue
        cand = it.get("candidate") or {}
        li = ""
        for s in cand.get("social") or []:
            l = str(s.get("link") or "")
            if "linkedin.com/in/" in l and not li: li = l
        key = str(it.get("item") or "").lower().strip()
        if li:
            out[key] = li
            # also key by revealed emails, so a lookup still hits when `item` is echoed oddly
            for c in cand.get("contacts") or []:
                if "email" in str(c.get("type", "")).lower() and isinstance(c.get("value"), str):
                    out.setdefault(c["value"].lower().strip(), li)
    return out


def contact_of_deal(did):
    s, d = hs(f"/crm/v4/objects/deals/{did}/associations/contacts")
    r = d.get("results") or []
    return str(r[0]["toObjectId"]) if r else None


def main():
    pushed = json.load(open(PUSHED, encoding="utf-8"))
    withmail = [r for r in pushed if str(r.get("email") or "").strip()]
    nomail = [r for r in pushed if not str(r.get("email") or "").strip()]
    c0 = credits()
    print(f"pushed {len(pushed)} | with email {len(withmail)} | no email {len(nomail)} | credits {c0}")

    found = {}
    for i in range(0, len(withmail), BATCH):
        chunk = withmail[i:i+BATCH]
        got = reveal_many([r["email"] for r in chunk])
        if got.get("__quota__"):
            print("!! reveal credits exhausted — stopping cleanly"); break
        found.update(got)
        n = sum(1 for r in chunk if found.get(r["email"].lower().strip()))
        print(f"   {i+len(chunk):>4}/{len(withmail)}  +{n} linkedin this batch "
              f"(total {len(found)})", flush=True)
        time.sleep(0.4)

    recs = []
    for r in withmail:
        li = found.get(str(r["email"]).lower().strip(), "")
        if li: recs.append({**r, "linkedin": li})
    print(f"\nrecovered LinkedIn for {len(recs)}/{len(pushed)}")
    json.dump(recs, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"credits {c0} -> {credits()}")

    if not APPLY:
        print("\nDRY RUN — nothing written to HubSpot. Re-run with --apply.")
        for r in recs[:8]:
            print(f'   {r["company"][:28]:<30}{r["founder"][:22]:<24}{r["linkedin"]}')
        return

    print("\npatching HubSpot (contact.linkedin_url + deal.linkedin_url)...", flush=True)
    ok = fail = 0
    for r in recs:
        did = r["deal_id"]
        ctid = contact_of_deal(did)
        s1, _ = hs(f"/crm/v3/objects/deals/{did}", "PATCH", {"properties": {"linkedin_url": r["linkedin"]}})
        s2 = None
        if ctid:
            s2, _ = hs(f"/crm/v3/objects/contacts/{ctid}", "PATCH",
                       {"properties": {"linkedin_url": r["linkedin"]}})
        good = s1 in (200, 201) and (ctid is None or s2 in (200, 201))
        ok += good; fail += (not good)
        if not good:
            print(f'   FAIL {r["company"][:30]:<32}deal={s1} contact={s2}', flush=True)
        elif ok % 25 == 0:
            print(f"   {ok} patched...", flush=True)
        time.sleep(0.25)
    print(f"\npatched {ok}, failed {fail}")
    if nomail:
        print(f"\n{len(nomail)} deals have NO email and cannot be recovered this way — "
              f"they need a search pass after the quota resets:")
        for r in nomail: print(f'   {r["company"][:34]:<36}{r["founder"][:24]}  deal={r["deal_id"]}')


main()
