# -*- coding: utf-8 -*-
"""Push 100 best company-only deals for MANUAL founder-finding, 50 Lamiya / 50 Yuktha.

Per instruction 2026-08-17: give the two GTM people the best companies we have (no contact
yet); they find the founder/CEO, user enriches after. DELIBERATE exception to the +91 gate —
these carry NO phone by design; they are research assignments, not dial-ready leads.

Each deal carries everything a caller needs to start: website, city, prequal score/rank, and
where we have it, the MCA-registry director name as a verify-this HINT (74 of 100). Lead source
is a distinct new tag so this batch is filterable and never confused with dial-ready leads.

Split: alternate by rank so both get an equal quality mix. Owner + poc both set.

Usage: python3 push_founder_hunt.py [--apply]
"""
import os, re, sys, json, time, collections, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
env = {l.split('=', 1)[0].strip().lower(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
H = {"Authorization": "Bearer " + env["hubspot_key"], "Content-Type": "application/json"}
SRC = os.path.join(HERE, "founder_hunt_100.json")
DONE = os.path.join(HERE, "pushed_founder_hunt.json")
LAMIYA, YUKTHA = "96574824", "96573782"
NAME = {LAMIYA: "Lamiya", YUKTHA: "Yuktha"}
PIPE, COLD = "default", "3992480462"
TAG = "Founder Search ( IT Services )"        # NEW lead_source, under the Scraped pipeline
APPLY = "--apply" in sys.argv


def hs(u, m="GET", b=None):
    d = json.dumps(b).encode() if b is not None else None
    for a in range(6):
        try:
            r = urllib.request.Request("https://api.hubapi.com" + u, data=d, method=m, headers=H)
            with urllib.request.urlopen(r, timeout=60) as x:
                t = x.read().decode(); return x.status, (json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and a < 5: time.sleep(2 * (a + 1)); continue
            return e.code, {"raw": e.read().decode()[:200]}
        except Exception:
            if a == 5: raise
            time.sleep(3 * (a + 1))


def d10(s): d = re.sub(r"\D", "", str(s or "")); return d[-10:] if len(d) >= 10 else ""
def nm(s):
    s = re.sub(r"\(.*?\)", "", (s or "").lower())
    s = re.sub(r"\b(pvt|private|limited|ltd|llp|technologies|technology|solutions|software|"
               r"systems|labs|services|infotech|india)\b", " ", s)
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


def ensure_tag():
    """Add TAG to the deals lead_source dropdown if missing (keeps existing options)."""
    _, p = hs("/crm/v3/properties/deals/lead_source")
    opts = p.get("options", [])
    if any(o["value"] == TAG for o in opts): return
    new = [{"label": o["label"], "value": o["value"], "displayOrder": i, "hidden": False}
           for i, o in enumerate(opts)] + [{"label": TAG, "value": TAG, "displayOrder": len(opts), "hidden": False}]
    hs("/crm/v3/properties/deals/lead_source", "PATCH", {"options": new})
    print(f"added lead_source option: {TAG}")


def crm_keys():
    dom, dn = set(), set()
    after = None
    while True:
        b = {"limit": 200, "properties": ["dealname", "lh2_domain"], "filterGroups": []}
        if after: b["after"] = after
        _, d = hs("/crm/v3/objects/deals/search", "POST", b)
        for x in d.get("results", []):
            p = x["properties"]
            if p.get("lh2_domain"): dom.add(p["lh2_domain"].lower().strip())
            if p.get("dealname"): dn.add(nm(p["dealname"]))
        after = (d.get("paging") or {}).get("next", {}).get("after")
        if not after: break
    dom.discard(""); dn.discard("")
    return dom, dn


def main():
    firms = json.load(open(SRC, encoding="utf-8"))
    done = json.load(open(DONE, encoding="utf-8")) if os.path.exists(DONE) else {}
    firms = [f for f in firms if f["domain"] not in done]
    dom, dn = crm_keys()
    plan, skip = [], []
    for f in firms:
        why = "domain already on a deal" if f["domain"].lower() in dom else \
              "deal name exists" if nm(f["name"]) in dn else ""
        (skip if why else plan).append((f, why))
    for f, w in skip: print(f'   SKIP {f["name"][:34]:<36}{w}')
    # alternate by rank: Lamiya even index, Yuktha odd
    plan.sort(key=lambda x: int(x[0]["rank"]))
    print(f"\nPLAN: push {len(plan)} (skipped {len(skip)}) | 50:50 alternating by rank")
    print(f"lead_source tag: {TAG}\n")
    for i, (f, _) in enumerate(plan[:6]):
        o = LAMIYA if i % 2 == 0 else YUKTHA
        print(f'   rank{f["rank"]:<4}{f["name"][:30]:<32}hint={f.get("mca_hint","-")[:18]:<20}-> {NAME[o]}')
    if not APPLY:
        print("   ...\nDRY RUN — re-run with --apply."); return

    ensure_tag()
    cnt = collections.Counter(); ok = fail = 0
    for i, (f, _) in enumerate(plan):
        o = LAMIYA if i % 2 == 0 else YUKTHA
        hint = f.get("mca_hint", "")
        desc = (f'FIND THE FOUNDER/CEO. Website: https://{f["domain"]} | City: {f.get("city","")} | '
                f'prequal rank {f["rank"]} score {f["score"]}'
                + (f' | MCA director (verify on LinkedIn): {hint}' if hint else ' | no registry name — research from scratch'))
        dp = {"dealname": f["name"], "pipeline": PIPE, "dealstage": COLD,
              "hubspot_owner_id": o, "poc": o, "lead_source": TAG,
              "source_tab": "founder_hunt", "lh2_domain": f["domain"], "description": desc}
        s, d = hs("/crm/v3/objects/deals", "POST", {"properties": dp})
        if s not in (200, 201):
            dp.pop("description", None)
            s, d = hs("/crm/v3/objects/deals", "POST", {"properties": dp})
            if s not in (200, 201): fail += 1; print(f'   FAIL {f["name"][:30]} {s} {str(d)[:80]}'); continue
        cnt[NAME[o]] += 1; ok += 1
        done[f["domain"]] = {"deal": d["id"], "owner": NAME[o], "name": f["name"], "rank": f["rank"], "hint": hint}
        json.dump(done, open(DONE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        time.sleep(0.25)
    print(f"\npushed {ok}, failed {fail} | Lamiya {cnt['Lamiya']}, Yuktha {cnt['Yuktha']}")


main()
