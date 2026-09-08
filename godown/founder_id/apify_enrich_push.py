# -*- coding: utf-8 -*-
"""Reveal + push ONLY the Apify-found URLs. Batches of 10; alternate owner STARTING YUKTHA.

Per instruction 2026-08-17: enrich the successful Apify URLs in batches and push them
alternately, first lead to Yuktha. This cohort keeps its OWN alternating counter (persisted
in apify_cohort.json) so the Yuktha-first sequence is continuous across re-runs as Apify
keeps yielding URLs — independent of the earlier Lamiya-balanced prequal pushes.

Reuses the same revealed.json / pushed_prequal.json state, so no reveal is repeated and CRM
dedup still holds. +91-mobile hard gate + revealed-name match unchanged. No VCF mail.

Usage: python3 apify_enrich_push.py [--apply] [--batch 10]
"""
import os, re, sys, json, time, sqlite3, collections, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HUB, "crm_mirror", "enrich"))
from indian_number import to_e164, classify as in_classify
env = {l.split('=', 1)[0].strip().lower(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
H = {"Authorization": "Bearer " + env["hubspot_key"], "Content-Type": "application/json"}
SH = env["signal_hire"]
DBP = os.path.join(HERE, "resolver.sqlite")
QUEUE = os.path.join(HUB, "godown", "prequal", "prequal_out", "enrich_queue.csv")
REV = os.path.join(HERE, "revealed.json"); PUSHED = os.path.join(HERE, "pushed_prequal.json")
COHORT = os.path.join(HERE, "apify_cohort.json")   # persisted Yuktha-first index for this cohort
YUKTHA, LAMIYA = "96573782", "96574824"            # index 0 -> YUKTHA first
NAME = {YUKTHA: "Yuktha", LAMIYA: "Lamiya"}
PIPE, COLD = "default", "3992480462"
TAG = {"nasscom": "NASSCOM ( IT Services )", "goodfirms": "Scraping Algo ( IT services )"}
APPLY = "--apply" in sys.argv
BATCH = 10
for i, a in enumerate(sys.argv):
    if a == "--batch": BATCH = int(sys.argv[i + 1])


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


def reveal(url):
    body = {"items": [url], "withoutWaterfall": True}
    r = urllib.request.Request("https://www.signalhire.com/api/v1/candidate/search",
                               data=json.dumps(body).encode(), method="POST",
                               headers={"apikey": SH, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(r, timeout=60) as x:
            d = json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        return None, ("CREDITS" if e.code == 402 else f"http{e.code}")
    except Exception as e:
        return None, type(e).__name__
    for it in (d if isinstance(d, list) else d.get("results", [])) or []:
        if not isinstance(it, dict) or it.get("status") != "success": continue
        c = it.get("candidate") or {}
        exp = c.get("experience") or []
        cur = next((e for e in exp if e.get("current")), (exp[0] if exp else {}))
        return {"sh_name": c.get("fullName") or "",
                "sh_title": (cur.get("position") or c.get("headLine") or "").strip(),
                "phones": [x.get("value") for x in (c.get("contacts") or [])
                           if "phone" in str(x.get("type", "")).lower() and isinstance(x.get("value"), str)],
                "emails": [x.get("value") for x in (c.get("contacts") or [])
                           if "email" in str(x.get("type", "")).lower() and isinstance(x.get("value"), str)]}, ""
    return None, "not_found"


def name_match(a, b):
    ta = {t for t in re.sub(r"[^a-z ]", "", (a or "").lower()).split() if len(t) > 2}
    tb = {t for t in re.sub(r"[^a-z ]", "", (b or "").lower()).split() if len(t) > 2}
    return len(ta & tb) >= 2 or (len(ta & tb) == 1 and (len(ta) == 1 or len(tb) == 1))


def d10(s): d = re.sub(r"\D", "", str(s or "")); return d[-10:] if len(d) >= 10 else ""
def nm(s):
    s = re.sub(r"\(.*?\)", "", (s or "").lower())
    s = re.sub(r"\b(pvt|private|limited|ltd|llp|technologies|technology|solutions|software|"
               r"systems|labs|services|infotech|india)\b", " ", s)
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


def crm_keys():
    dom, dn, ph = set(), set(), set()
    for obj, props, sink in (("deals", ["dealname", "lh2_domain"], None),):
        pass
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
    after = None
    while True:
        b = {"limit": 200, "properties": ["phone", "mobilephone"],
             "filterGroups": [{"filters": [{"propertyName": "hs_object_id", "operator": "HAS_PROPERTY"}]}]}
        if after: b["after"] = after
        _, d = hs("/crm/v3/objects/contacts/search", "POST", b)
        for x in d.get("results", []):
            for k in ("phone", "mobilephone"):
                if d10(x["properties"].get(k)): ph.add(d10(x["properties"][k]))
        after = (d.get("paging") or {}).get("next", {}).get("after")
        if not after: break
    for s in (dom, dn, ph): s.discard("")
    return dom, dn, ph


def main():
    import csv
    q = {r["domain"]: r for r in csv.DictReader(open(QUEUE, encoding="utf-8-sig"))}
    con = sqlite3.connect(DBP)
    apify = [json.loads(d) for _, d in con.execute("SELECT domain, data FROM companies WHERE status='full'")
             if json.loads(d).get("li_source") == "apify harvestapi"]
    rev = json.load(open(REV, encoding="utf-8")) if os.path.exists(REV) else {}
    print(f"Apify URLs: {len(apify)} | revealing {sum(1 for r in apify if r['domain'] not in rev)} new", flush=True)

    # ---- reveal (batches of BATCH) -------------------------------------------
    todo = [r for r in apify if r["domain"] not in rev]
    for bi in range(0, len(todo), BATCH):
        for r in todo[bi:bi + BATCH]:
            got, note = reveal(r["linkedin_url"])
            rec = {"domain": r["domain"], "name": r["company"], "person": r["founder_name"],
                   "linkedin": r["linkedin_url"], "cohort": "apify", "reveal_note": note}
            if note == "CREDITS": print("!! credits exhausted"); break
            if got:
                rec.update(got)
                if not name_match(r["founder_name"], got["sh_name"]):
                    rec["gate"] = "skip - revealed different person"
                else:
                    ind = next((to_e164(x) for x in got["phones"] if in_classify(x) == "mobile"), "")
                    rec["phone"] = ind; rec["email"] = (got["emails"] or [""])[0]
                    rec["gate"] = "PASS" if ind else "skip - no +91 mobile"
            else:
                rec["gate"] = f"skip - {note}"
            rev[r["domain"]] = rec
            json.dump(rev, open(REV, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            time.sleep(0.4)
        print(f"  revealed batch {bi // BATCH + 1}/{(len(todo)+BATCH-1)//BATCH}", flush=True)

    g = collections.Counter(r["gate"] for r in rev.values() if r.get("cohort") == "apify")
    print("apify reveal gates:", dict(g))

    # ---- push PASS rows, alternating YUKTHA-first, continuous across re-runs ---
    done = json.load(open(PUSHED, encoding="utf-8")) if os.path.exists(PUSHED) else {}
    ready = [rev[d] for d in rev if rev[d].get("cohort") == "apify"
             and rev[d].get("gate") == "PASS" and d not in done]
    dom, dn, ph = crm_keys()
    plan, skip = [], []
    for r in ready:
        why = ("domain already on a deal" if r["domain"].lower() in dom else
               "deal name exists" if nm(r["name"]) in dn else
               "phone already in CRM" if d10(r["phone"]) in ph else "")
        (skip if why else plan).append(r)
    for r in skip: print(f'   SKIP {r["name"][:32]:<34}dedup')
    coh = json.load(open(COHORT)) if os.path.exists(COHORT) else {"idx": 0}
    print(f"\nPLAN: push {len(plan)} | cohort index {coh['idx']} (even=Yuktha, odd=Lamiya)")
    if not APPLY:
        print("DRY RUN — re-run with --apply"); return

    ok = fail = 0
    for r in plan:
        o = YUKTHA if coh["idx"] % 2 == 0 else LAMIYA
        parts = (r["person"] or "").split()
        srcrow = q.get(r["domain"], {})
        cp = {"firstname": parts[0] if parts else "", "lastname": " ".join(parts[1:]),
              "email": r.get("email") or "", "phone": r["phone"], "mobilephone": r["phone"],
              "jobtitle": r.get("sh_title") or "Director", "company": r["name"],
              "linkedin_url": r["linkedin"], "country": "India"}
        s, d = hs("/crm/v3/objects/contacts", "POST", {"properties": {k: v for k, v in cp.items() if v}})
        if s not in (200, 201): fail += 1; print(f'   FAIL contact {r["name"][:28]} {s}'); continue
        ctid = d["id"]
        dp = {"dealname": r["name"], "pipeline": PIPE, "dealstage": COLD,
              "hubspot_owner_id": o, "poc": o,
              "lead_source": TAG.get(srcrow.get("source", "").split("+")[0], TAG["goodfirms"]),
              "source_tab": "prequal_q1", "lh2_domain": r["domain"],
              "description": f'MCA director via Apify; prequal rank {srcrow.get("rank","?")} '
                             f'score {srcrow.get("score","?")}'}
        s, d = hs("/crm/v3/objects/deals", "POST", {"properties": dp})
        if s not in (200, 201):
            dp.pop("description", None)
            s, d = hs("/crm/v3/objects/deals", "POST", {"properties": dp})
            if s not in (200, 201): fail += 1; print(f'   FAIL deal {r["name"][:28]} {s}'); continue
        did = d["id"]; time.sleep(0.2)
        hs(f"/crm/v4/objects/deals/{did}/associations/default/contacts/{ctid}", "PUT")
        done[r["domain"]] = {"deal": did, "owner": NAME[o], "name": r["name"], "person": r["person"],
                             "phone": r["phone"], "email": r.get("email", ""), "linkedin": r["linkedin"],
                             "cohort": "apify"}
        json.dump(done, open(PUSHED, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        coh["idx"] += 1; json.dump(coh, open(COHORT, "w"))
        ok += 1
        print(f'   PUSHED {r["name"][:30]:<32}-> {NAME[o]}', flush=True)
        time.sleep(0.3)
    c2 = collections.Counter(v["owner"] for v in done.values() if v.get("cohort") == "apify")
    print(f"\npushed {ok}, failed {fail} | Apify cohort so far: Yuktha {c2['Yuktha']}, Lamiya {c2['Lamiya']}")


main()
