# -*- coding: utf-8 -*-
"""Push the enriched Sales-Navigator IT firms: 100 to Yuktha, 100 to Lamiya.

Only rows that cleared the +91 gate are eligible — the standing rule is that nothing reaches
HubSpot without a dialable Indian number.

Enterprise/captive arms are dropped (aug7_salesnav_excluded.json): Thomson Reuters India,
Tata Motors Global Services, Danske IT, Lumen Technologies India and the like are IT-services
by LinkedIn industry but will never sell a codebase. The old GoodFirms-sourced filter never
needed this rule because a vendor directory does not list them; a raw LinkedIn industry scrape
does.

SPLIT IS INTERLEAVED BY RANK, not first-100/second-100. A straight cut would hand Yuktha every
400-person firm and Lamiya the tail, making their books unequal in quality and their numbers
incomparable. Odd ranks -> Yuktha, even -> Lamiya.

Re-checks each company against HubSpot immediately before creating it: the ranked list was
deduped hours earlier and the other two tasks have written to the CRM since.

Usage: python aug7_salesnav_push.py [--apply] [--per 100]
"""
import os, re, sys, json, time, collections, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
HS = env["hubspot_key"]
H = {"Authorization": "Bearer " + HS, "Content-Type": "application/json"}

YUKTHA = "96573782"; LAMIYA = "96574824"
PIPE = "default"; COLD = "3992480462"
SOURCE = "Scraping Algo ( IT services )"; TAG = "ITservices"
STATE = os.path.join(HERE, "aug7_salesnav_enriched.json")
EXCL  = os.path.join(HERE, "aug7_salesnav_excluded.json")
LOG   = os.path.join(HERE, "aug7_salesnav_pushed.json")

APPLY = "--apply" in sys.argv
PER = 100
for i, a in enumerate(sys.argv):
    if a == "--per": PER = int(sys.argv[i+1])


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


def nm(s):
    s = (s or "").lower(); s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r"\b(pvt|private|ltd|limited|llp|inc|technologies|technology|solutions|software|"
               r"systems|labs|services|consulting|infotech|it|the|india|global|group)\b", " ", s)
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


def crm_names():
    after, out = None, set()
    while True:
        b = {"limit": 200, "filterGroups": [], "properties": ["dealname"]}
        if after: b["after"] = after
        _, d = hs("/crm/v3/objects/deals/search", "POST", b)
        for x in d.get("results", []): out.add(nm(x["properties"].get("dealname")))
        after = (d.get("paging") or {}).get("next", {}).get("after")
        if not after: break
    out.discard("")
    return out


def nli(u):
    u = str(u or "").strip().lower()
    if not u: return ""
    u = re.sub(r"^https?://", "", u).split("?")[0].split("#")[0]
    u = re.sub(r"^([a-z]{2,3}\.)?linkedin\.com", "linkedin.com", u)
    return u.rstrip("/")


def crm_people():
    """Two independent person-level keys already in the CRM:
      phones  — last 10 digits of any contact number
      lis     — normalised LinkedIn URL on contacts AND on deals
    Both are needed. Phone alone misses a founder whose CRM record was created without one
    (common for the OutFlo book, which is LinkedIn-only until SignalHire runs); LinkedIn alone
    misses the older scraped records that were never stamped with a profile URL."""
    after, phones, lis = None, set(), set()
    while True:
        b = {"limit": 200, "filterGroups": [],
             "properties": ["phone", "mobilephone", "linkedin_url", "hs_linkedin_url"]}
        if after: b["after"] = after
        _, d = hs("/crm/v3/objects/contacts/search", "POST", b)
        for x in d.get("results", []):
            p = x["properties"]
            for k in ("phone", "mobilephone"):
                dd = re.sub(r"[^\d]", "", str(p.get(k) or ""))
                if len(dd) >= 10: phones.add(dd[-10:])
            for k in ("linkedin_url", "hs_linkedin_url"):
                if nli(p.get(k)): lis.add(nli(p[k]))
        after = (d.get("paging") or {}).get("next", {}).get("after")
        if not after: break
    after = None
    while True:
        b = {"limit": 200, "filterGroups": [], "properties": ["linkedin_url"]}
        if after: b["after"] = after
        _, d = hs("/crm/v3/objects/deals/search", "POST", b)
        for x in d.get("results", []):
            if nli(x["properties"].get("linkedin_url")): lis.add(nli(x["properties"]["linkedin_url"]))
        after = (d.get("paging") or {}).get("next", {}).get("after")
        if not after: break
    lis.discard("")
    return phones, lis


def push(rec, owner):
    comp = rec["company"]
    s, d = hs("/crm/v3/objects/companies/search", "POST", {"limit": 1, "properties": ["name"],
        "filterGroups": [{"filters": [{"propertyName": "name", "operator": "EQ", "value": comp}]}]})
    coid = d["results"][0]["id"] if d.get("results") else None
    if not coid:
        s, d = hs("/crm/v3/objects/companies", "POST",
                  {"properties": {"name": comp, "linkedin_company_page": rec.get("li_company_url") or ""}})
        coid = d.get("id")
    parts = (rec.get("founder") or "").split()
    cp = {"firstname": parts[0] if parts else comp,
          "lastname": " ".join(parts[1:]) if len(parts) > 1 else "",
          "company": comp, "phone": rec["phone"], "mobilephone": rec["phone"],
          "jobtitle": rec.get("title") or "Founder"}
    if rec.get("email"): cp["email"] = rec["email"]
    if rec.get("li"): cp["linkedin_url"] = rec["li"]
    s, d = hs("/crm/v3/objects/contacts", "POST", {"properties": {k: v for k, v in cp.items() if v}})
    if s not in (200, 201): return None, f"contact {s} {str(d)[:100]}"
    ctid = d.get("id")
    dp = {"dealname": comp, "pipeline": PIPE, "dealstage": COLD,
          "hubspot_owner_id": owner, "poc": owner,
          "lead_source": SOURCE, "scraped_type": TAG}
    if rec.get("li"): dp["linkedin_url"] = rec["li"]
    s, d = hs("/crm/v3/objects/deals", "POST", {"properties": dp})
    if s not in (200, 201): return None, f"deal {s} {str(d)[:100]}"
    did = d.get("id"); time.sleep(0.25)
    hs(f"/crm/v4/objects/deals/{did}/associations/default/companies/{coid}", "PUT")
    hs(f"/crm/v4/objects/deals/{did}/associations/default/contacts/{ctid}", "PUT")
    hs(f"/crm/v4/objects/contacts/{ctid}/associations/default/companies/{coid}", "PUT")
    return did, ""


def main():
    state = json.load(open(STATE, encoding="utf-8"))
    excl = set(json.load(open(EXCL, encoding="utf-8"))) if os.path.exists(EXCL) else set()
    callable_ = [r for r in state if r.get("phone")]
    print(f"enriched rows {len(state)} | callable (+91) {len(callable_)} | exclusion list {len(excl)}")

    elig = [r for r in callable_ if r["company"] not in excl]
    print(f"after dropping enterprise/captive arms: {len(elig)} "
          f"({len(callable_)-len(elig)} dropped)")

    print("re-checking against HubSpot (the CRM changed while this ran)...", flush=True)
    have = crm_names()
    phones, lis = crm_people()
    print(f"   CRM keys: {len(have)} deal names, {len(phones)} phones, {len(lis)} linkedin URLs")
    fresh, dnm, dph, dli, dself = [], 0, 0, 0, 0
    seen_n, seen_p, seen_l = set(), set(), set()
    for r in sorted(elig, key=lambda x: x["rank"]):
        k = nm(r["company"]); d10 = re.sub(r"[^\d]", "", r["phone"])[-10:]; li = nli(r.get("li"))
        if k in have: dnm += 1; continue
        if d10 in phones: dph += 1; continue
        if li and li in lis: dli += 1; continue
        # and inside this batch itself — the same founder can surface under two firms
        if k in seen_n or d10 in seen_p or (li and li in seen_l): dself += 1; continue
        seen_n.add(k); seen_p.add(d10)
        if li: seen_l.add(li)
        fresh.append(r)
    print(f"dropped: {dnm} name already a deal | {dph} phone already on a contact | "
          f"{dli} linkedin already known | {dself} duplicate inside this batch")
    print(f"ELIGIBLE TO PUSH: {len(fresh)}")

    need = PER * 2
    if len(fresh) < need:
        print(f"\n!! only {len(fresh)} eligible, {need} needed for {PER} each.")
        print("   Pushing what exists, split evenly — NOT topping up with excluded or "
              "un-enriched rows.")
    take = fresh[:need]
    y = [r for i, r in enumerate(take) if i % 2 == 0][:PER]
    l = [r for i, r in enumerate(take) if i % 2 == 1][:PER]
    print(f"\nsplit (interleaved by rank): Yuktha {len(y)} | Lamiya {len(l)}")
    for who, lst in (("Yuktha", y), ("Lamiya", l)):
        hc = [r["headcount"] for r in lst]
        print(f'   {who}: hc median {sorted(hc)[len(hc)//2] if hc else 0}, '
              f'pri1 {sum(1 for r in lst if r["pri"]==1)}, pri2 {sum(1 for r in lst if r["pri"]==2)}')

    if not APPLY:
        print("\nDRY RUN — nothing written. Re-run with --apply.")
        print("\nfirst 10 for each:")
        for who, lst in (("Yuktha", y), ("Lamiya", l)):
            print(f"  -- {who} --")
            for r in lst[:10]:
                print(f'     rank {r["rank"]:>4} hc={r["headcount"]:<5}{r["company"][:34]:<36}'
                      f'{(r.get("founder") or "")[:22]:<24}{r["phone"]}')
        return

    out = json.load(open(LOG, encoding="utf-8")) if os.path.exists(LOG) else []
    done = {r["company"] for r in out}
    ok = collections.Counter()
    for who, oid, lst in (("Yuktha", YUKTHA, y), ("Lamiya", LAMIYA, l)):
        print(f"\n--- pushing {len(lst)} to {who} ---", flush=True)
        for r in lst:
            if r["company"] in done: continue
            did, err = push(r, oid)
            print(f'   {"OK  " if did else "FAIL"} {r["company"][:34]:<36}{did or err}', flush=True)
            if did:
                ok[who] += 1
                out.append({**r, "owner": who, "deal_id": did})
                json.dump(out, open(LOG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            time.sleep(0.3)
    print(f"\npushed: {dict(ok)}  -> {os.path.basename(LOG)}")


main()
