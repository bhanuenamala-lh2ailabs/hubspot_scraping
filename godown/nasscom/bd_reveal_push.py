# -*- coding: utf-8 -*-
"""Reveal 10 fully-enriched Bangladesh leads and push them to Ishpreet.

Uses the CREDITS pool (/candidate/search by LinkedIn URL) — the profile SEARCH pool is still
exhausted, and reveal-by-URL does not touch it. Reveal also returns the person's name and title,
so firms where we scraped a profile URL but could not pair a name still resolve.

NUMBER RULE: Bangladesh accepts ANY dialable number, unlike the +91 gate on Indian sources —
granted explicitly for this batch. bangladesh_number.py is used to LABEL what came back (BD
mobile / landline / foreign) so a caller knows what they are dialling, never to reject it.

"Fully enriched" here means a person, a title and a phone. Email and LinkedIn are recorded when
present but a lead is not held back for lacking them.

Stops the moment TARGET leads are ready — no point spending credits past the ask.

Usage: python3 bd_reveal_push.py [--target 10] [--apply]
"""
import os, re, sys, json, time, collections, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HUB, "crm_mirror", "enrich"))
from bangladesh_number import to_e164 as bd_e164, classify as bd_class

env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
SH = env["signal_hire"]
H = {"Authorization": "Bearer " + env["hubspot_key"], "Content-Type": "application/json"}

SRC = os.path.join(HERE, "bd_reveal_queue.json")
OUT = os.path.join(HERE, "bd_revealed.json")
ISHPREET = "166322228"
PIPE, COLD = "default", "3992480462"
SOURCE, TAB = "Bangladesh ( IT Services )", "bangladesh"
TARGET, APPLY = 10, "--apply" in sys.argv
for i, a in enumerate(sys.argv):
    if a == "--target": TARGET = int(sys.argv[i+1])

SENIOR = re.compile(r"\b(founder|co[- ]?founder|ceo|chief executive|managing director|\bmd\b|"
                    r"chairman|president|owner|proprietor|director|chief technology|\bcto\b|"
                    r"\bcoo\b|partner|head of)\b", re.I)


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


def credits():
    try:
        r = urllib.request.Request("https://www.signalhire.com/api/v1/credits", headers={"apikey": SH})
        return json.loads(urllib.request.urlopen(r, timeout=20).read().decode()).get("credits")
    except Exception:
        return None


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
    res = d if isinstance(d, list) else d.get("results", [])
    for it in res or []:
        if not isinstance(it, dict) or it.get("status") != "success": continue
        c = it.get("candidate") or {}
        exp = c.get("experience") or []
        cur = next((e for e in exp if e.get("current")), (exp[0] if exp else {}))
        return {"name": c.get("fullName"),
                "title": (cur.get("position") or c.get("headLine") or "").strip(),
                "company": (cur.get("company") or "").strip(),
                "staff": cur.get("staffCount") or "",
                "phones": [x.get("value") for x in (c.get("contacts") or [])
                           if "phone" in str(x.get("type", "")).lower() and isinstance(x.get("value"), str)],
                "emails": [x.get("value") for x in (c.get("contacts") or [])
                           if "email" in str(x.get("type", "")).lower() and isinstance(x.get("value"), str)],
                "linkedins": [s.get("link") for s in (c.get("social") or [])
                              if "linkedin.com/in/" in str(s.get("link") or "")]}, ""
    return None, "not_found"


def d10(s):
    d = re.sub(r"\D", "", str(s or "")); return d[-10:] if len(d) >= 10 else ""


def nm(s):
    s = (s or "").lower(); s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r"\b(pvt|private|ltd|limited|llp|inc|technologies|technology|solutions|software|"
               r"systems|labs|services|consulting|infotech|it|the|bangladesh|global|group)\b", " ", s)
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


def push(r):
    parts = (r["person"] or "").split()
    cp = {"firstname": parts[0] if parts else "", "lastname": " ".join(parts[1:]) if len(parts) > 1 else "",
          "email": r.get("email") or "", "phone": r["phone"], "mobilephone": r["phone"],
          "jobtitle": r.get("title") or "", "company": r["name"],
          "linkedin_url": r.get("linkedin") or "", "country": "Bangladesh"}
    s, d = hs("/crm/v3/objects/contacts", "POST", {"properties": {k: v for k, v in cp.items() if v}})
    if s not in (200, 201): return None, f"contact {s} {str(d)[:110]}"
    ctid = d["id"]
    dp = {"dealname": r["name"], "pipeline": PIPE, "dealstage": COLD,
          "hubspot_owner_id": ISHPREET, "poc": ISHPREET,
          "lead_source": SOURCE, "source_tab": TAB, "lh2_domain": r["domain"]}
    s, d = hs("/crm/v3/objects/deals", "POST", {"properties": dp})
    if s not in (200, 201): return None, f"deal {s} {str(d)[:110]}"
    did = d["id"]; time.sleep(0.2)
    hs(f"/crm/v4/objects/deals/{did}/associations/default/contacts/{ctid}", "PUT")
    return did, ""


def main():
    q = json.load(open(SRC, encoding="utf-8"))
    state = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else []
    seen = {r["domain"] for r in state}
    # firms where we already scraped a name first — the reveal is then a confirmation, not a guess
    q.sort(key=lambda r: not r.get("person"))
    c0 = credits()
    print(f"queue {len(q)} | already revealed {len(state)} | credits {c0} | target {TARGET}\n", flush=True)

    # NB: this seeding line must apply the SAME seniority test as the append below. It did not,
    # and a "Web Developer" already sitting in state was carried into a push as a founder lead.
    ready = [r for r in state if r.get("phone") and r.get("senior")]
    for r in q:
        if len(ready) >= TARGET: break
        if r["domain"] in seen: continue
        got, note = reveal(r["linkedin"])
        if note == "CREDITS":
            print("!! credits exhausted — stopping", flush=True); break
        rec = dict(r); rec["reveal"] = note or "ok"
        if got:
            ph = got["phones"][0] if got["phones"] else ""
            bd = bd_e164(ph)
            rec |= {"person": got["name"] or r.get("person", ""),
                    "title": got["title"] or r.get("title", ""),
                    "phone": bd or ph, "phone_kind": bd_class(bd) if bd else ("foreign/landline" if ph else ""),
                    "email": got["emails"][0] if got["emails"] else r.get("company_email", ""),
                    "linkedin": (got["linkedins"] or [r["linkedin"]])[0],
                    "staff": got["staff"], "all_phones": got["phones"]}
            rec["senior"] = bool(SENIOR.search(rec["title"] or ""))
        else:
            rec |= {"phone": "", "email": r.get("company_email", "")}
        state.append(rec); seen.add(r["domain"])
        json.dump(state, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        # a phone alone is not a lead: the profile URL on a team page can belong to any engineer,
        # and one of the first thirteen revealed as a "Web Developer". Seniority is judged on the
        # title the API returned, not on where the link sat.
        if rec.get("phone") and rec.get("senior"): ready.append(rec)
        print(f'   {r["name"][:30]:<32}{(rec.get("person") or "-")[:20]:<22}'
              f'{(rec.get("title") or "")[:20]:<22}{rec.get("phone") or "-":<17}{rec.get("phone_kind","")}',
              flush=True)
        time.sleep(0.3)

    print(f"\ncredits {c0} -> {credits()}")
    ready = ready[:TARGET]
    print(f"\nFULLY ENRICHED: {len(ready)}")
    for r in ready:
        print(f'   {r["name"][:32]:<34}{r["person"][:20]:<22}{r["title"][:22]:<24}{r["phone"]}')
    if not APPLY:
        print("\nDRY RUN — nothing pushed. Re-run with --apply.")
        return

    # live dedup right before creating
    dom, dn = set(), set()
    after = None
    while True:
        b = {"limit": 200, "properties": ["dealname", "lh2_domain"], "filterGroups": []}
        if after: b["after"] = after
        _, d = hs("/crm/v3/objects/deals/search", "POST", b)
        for x in d.get("results", []):
            p = x["properties"]
            if p.get("lh2_domain"): dom.add(p["lh2_domain"].lower())
            if p.get("dealname"): dn.add(nm(p["dealname"]))
        after = (d.get("paging") or {}).get("next", {}).get("after")
        if not after: break
    ok = fail = 0
    for r in ready:
        if r["domain"].lower() in dom or nm(r["name"]) in dn:
            print(f'   SKIP {r["name"][:30]} — already in HubSpot'); continue
        did, err = push(r)
        if did: ok += 1; print(f'   pushed {r["name"][:30]:<32}deal {did}  -> Ishpreet')
        else: fail += 1; print(f'   FAIL   {r["name"][:30]:<32}{err}')
        time.sleep(0.3)
    print(f"\npushed {ok}, failed {fail}  |  lead_source '{SOURCE}', owner Ishpreet")


main()
