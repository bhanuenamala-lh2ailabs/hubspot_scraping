# -*- coding: utf-8 -*-
"""Reveal + gate + push for the prequal queue's identity-full rows — 2026-08-17 instruction:
"enrich with signalhire number, linkedin url, email; push half each to Yuktha and Lamiya,
whichever are left after the +91 gate."

Wave-based and idempotent: each run picks up every row that has a LinkedIn URL (from the
resolver state as the F-pass upgrades rows, plus the 30 pre-keyed in the queue CSV), reveals
the ones not yet revealed, gates, dedups LIVE against HubSpot, and pushes the survivors with
owners alternated to keep Yuktha/Lamiya equal ACROSS runs (split state persisted).

GATES, in order, each recorded with a reason:
  identity   revealed fullName must share first+last tokens with the MCA-cited name — a URL
             that reveals a different person is a wrong profile, not a lead (QoderLabs rule)
  +91 mobile the hard gate: no Indian mobile, no push. Landlines and foreign numbers fail.
Lead-source tag preserves origin (nasscom -> NASSCOM tag, goodfirms -> Scraping Algo tag,
both already in the cleaned dropdown); source_tab='prequal_q1' marks the cohort either way.
NO VCF mails — not asked for.

Usage: python3 enrich_push.py [--apply]      (dry-run prints the plan without creating)
"""
import os, re, sys, csv, json, time, collections, sqlite3, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HUB, "crm_mirror", "enrich"))
from indian_number import to_e164, classify as in_classify

env = {l.split('=', 1)[0].strip().lower(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
H = {"Authorization": "Bearer " + env["hubspot_key"], "Content-Type": "application/json"}
SH = env["signal_hire"]
QUEUE = os.path.join(HUB, "godown", "prequal", "prequal_out", "enrich_queue.csv")
DBP = os.path.join(HERE, "resolver.sqlite")
REV = os.path.join(HERE, "revealed.json")
PUSHED = os.path.join(HERE, "pushed_prequal.json")
APPLY = "--apply" in sys.argv
LAMIYA, YUKTHA = "96574824", "96573782"
NAME = {LAMIYA: "Lamiya", YUKTHA: "Yuktha"}
PIPE, COLD = "default", "3992480462"
TAG = {"nasscom": "NASSCOM ( IT Services )", "goodfirms": "Scraping Algo ( IT services )"}


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
                "sh_company": (cur.get("company") or "").strip(),
                "phones": [x.get("value") for x in (c.get("contacts") or [])
                           if "phone" in str(x.get("type", "")).lower() and isinstance(x.get("value"), str)],
                "emails": [x.get("value") for x in (c.get("contacts") or [])
                           if "email" in str(x.get("type", "")).lower() and isinstance(x.get("value"), str)]}, ""
    return None, "not_found"


def name_match(a, b):
    ta = {t for t in re.sub(r"[^a-z ]", "", (a or "").lower()).split() if len(t) > 2}
    tb = {t for t in re.sub(r"[^a-z ]", "", (b or "").lower()).split() if len(t) > 2}
    return len(ta & tb) >= 2 or (len(ta & tb) == 1 and (len(ta) == 1 or len(tb) == 1))


def d10(s):
    d = re.sub(r"\D", "", str(s or "")); return d[-10:] if len(d) >= 10 else ""


def nm(s):
    s = re.sub(r"\(.*?\)", "", (s or "").lower())
    s = re.sub(r"\b(pvt|private|limited|ltd|llp|technologies|technology|solutions|software|"
               r"systems|labs|services|infotech|india)\b", " ", s)
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


def crm_keys():
    dom, dn, ph = set(), set(), set()
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
    q = {r["domain"]: r for r in csv.DictReader(open(QUEUE, encoding="utf-8-sig"))}
    cands = []
    con = sqlite3.connect(DBP)
    for (dom, data) in con.execute("SELECT domain, data FROM companies WHERE status='full'"):
        r = json.loads(data)
        cands.append({"domain": dom, "name": r["company"], "person": r["founder_name"],
                      "linkedin": r["linkedin_url"], "din_src": r.get("source_1_url", "")})
    for dom, r in q.items():
        if r["identity_status"] == "identity_full" and (r["contact_linkedin"] or "").strip():
            if not any(c["domain"] == dom for c in cands):
                cands.append({"domain": dom, "name": r["name"], "person": r["contact_name"],
                              "linkedin": r["contact_linkedin"].strip(), "din_src": "goodfirms people"})
    rev = json.load(open(REV, encoding="utf-8")) if os.path.exists(REV) else {}
    print(f"identity-full candidates: {len(cands)} | already revealed: {len(rev)}", flush=True)

    for c in cands:
        if c["domain"] in rev: continue
        got, note = reveal(c["linkedin"])
        if note == "CREDITS":
            print("!! credits exhausted"); break
        rec = {**c, "reveal_note": note}
        if got:
            rec.update(got)
            if not name_match(c["person"], got["sh_name"]):
                rec["gate"] = "skip - revealed different person"
            else:
                ind = next((to_e164(x) for x in got["phones"] if in_classify(x) == "mobile"), "")
                rec["phone"] = ind
                rec["email"] = (got["emails"] or [""])[0]
                rec["gate"] = "PASS" if ind else "skip - no +91 mobile"
        else:
            rec["gate"] = f"skip - {note}"
        rev[c["domain"]] = rec
        json.dump(rev, open(REV, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f'{c["name"][:30]:<32}{(rec.get("sh_name") or "-")[:22]:<24}{rec["gate"]}', flush=True)
        time.sleep(0.4)

    g = collections.Counter(r["gate"] for r in rev.values())
    print("\nreveal gates:", dict(g))
    ready = [r for r in rev.values() if r.get("gate") == "PASS"]

    done = json.load(open(PUSHED, encoding="utf-8")) if os.path.exists(PUSHED) else {}
    ready = [r for r in ready if r["domain"] not in done]
    dom, dn, ph = crm_keys()
    plan, skip = [], []
    for r in ready:
        why = ""
        if r["domain"].lower() in dom: why = "domain already on a deal"
        elif nm(r["name"]) in dn: why = "deal name exists"
        elif d10(r["phone"]) in ph: why = "phone already in CRM"
        (skip if why else plan).append((r, why))
    for r, w in skip: print(f'   SKIP {r["name"][:32]:<34}{w}')
    cnt = collections.Counter(v["owner"] for v in done.values())
    print(f"\nPLAN: push {len(plan)} (splits continue from Lamiya {cnt['Lamiya']}, Yuktha {cnt['Yuktha']})")
    if not APPLY:
        print("DRY RUN — re-run with --apply"); return

    ok = fail = 0
    for r, _ in plan:
        o = LAMIYA if cnt["Lamiya"] <= cnt["Yuktha"] else YUKTHA
        parts = (r["person"] or "").split()
        srcrow = q.get(r["domain"], {})
        cp = {"firstname": parts[0] if parts else "", "lastname": " ".join(parts[1:]),
              "email": r.get("email") or "", "phone": r["phone"], "mobilephone": r["phone"],
              "jobtitle": r.get("sh_title") or "Director", "company": r["name"],
              "linkedin_url": r["linkedin"], "country": "India"}
        s, d = hs("/crm/v3/objects/contacts", "POST", {"properties": {k: v for k, v in cp.items() if v}})
        if s not in (200, 201): fail += 1; print(f'   FAIL contact {r["name"][:30]} {s}'); continue
        ctid = d["id"]
        dp = {"dealname": r["name"], "pipeline": PIPE, "dealstage": COLD,
              "hubspot_owner_id": o, "poc": o,
              "lead_source": TAG.get(srcrow.get("source", "").split("+")[0], TAG["goodfirms"]),
              "source_tab": "prequal_q1", "lh2_domain": r["domain"],
              "description": f'MCA-cited director; prequal rank {srcrow.get("rank","?")} '
                             f'score {srcrow.get("score","?")}; {srcrow.get("pre2024_grade","")}'}
        s, d = hs("/crm/v3/objects/deals", "POST", {"properties": dp})
        if s not in (200, 201):
            dp.pop("description", None)
            s, d = hs("/crm/v3/objects/deals", "POST", {"properties": dp})
            if s not in (200, 201): fail += 1; print(f'   FAIL deal {r["name"][:30]} {s}'); continue
        did = d["id"]; time.sleep(0.2)
        hs(f"/crm/v4/objects/deals/{did}/associations/default/contacts/{ctid}", "PUT")
        cnt[NAME[o]] += 1; ok += 1
        done[r["domain"]] = {"deal": did, "owner": NAME[o], "name": r["name"], "person": r["person"],
                             "phone": r["phone"], "email": r.get("email", ""), "linkedin": r["linkedin"]}
        json.dump(done, open(PUSHED, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f'   PUSHED {r["name"][:30]:<32}-> {NAME[o]}', flush=True)
        time.sleep(0.3)
    print(f"\npushed {ok}, failed {fail} | totals: Lamiya {cnt['Lamiya']}, Yuktha {cnt['Yuktha']}")


main()
