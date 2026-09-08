# -*- coding: utf-8 -*-
"""Pull the Tracxn-sourced Cold Call leads out of Lamiya's and Yuktha's books into a pool.

Scope, deliberately narrow:
  * owner is Lamiya or Yuktha
  * stage is Cold Call (a lead someone has already started working is NOT touched)
  * the deal traces to the Tracxn ranked sheet — either ready_queue_pushed.json or the
    earlier tracxn PoC push. The deadpool-wave book is explicitly excluded; those were
    just assigned and are a different source.

Deals are ARCHIVED (HubSpot recycle bin — restorable), contacts are LEFT IN PLACE so the
people stay reachable and nothing is destroyed. Every field is written to
crm_mirror/holding/ first, in the same shape as the earlier no-Indian-number pull-off, so
the pool can be re-pushed or worked another way later.

Usage: python pull_tracxn_from_newjoiners.py [--dry-run]
"""
import os, csv, sys, json, time, datetime, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
HOLD = os.path.join(HUB, "crm_mirror", "holding")
os.makedirs(HOLD, exist_ok=True)
env = {l.split('=', 1)[0].strip().lower(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
HS = env["hubspot_key"]
COLD_CALL = {"default": "3992480462", "2425754306": "4002503379"}
TARGETS = {"96574824": "Lamiya Saleem", "96573782": "Yuktha Anand"}
TODAY = datetime.date.today().isoformat()


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
            return e.code, {"raw": e.read().decode()[:200]}
        except Exception:
            if a == 4: raise
            time.sleep(2)


def norm(s):
    import re
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", str(s or "").lower())).strip()


def tracxn_origin():
    """-> (deal ids, company names) known to have come from the Tracxn ranked sheet.

    Ids alone are not enough: a few Tracxn deals were created outside the two push logs
    (Logipe, for one), so we also match on the company names in the Tracxn source rows.
    """
    ids, names = set(), set()
    for f in ("ready_queue_pushed.json", "pushed_tracxn_poc.json"):
        p = os.path.join(HERE, f)
        if not os.path.exists(p): continue
        for r in json.load(open(p, encoding="utf-8")):
            if isinstance(r, dict) and r.get("deal_id"): ids.add(str(r["deal_id"]))
    for f in ("tracxn_poc_rows.json", "tracxn_relevant_pushable.json"):
        p = os.path.join(HERE, f)
        if not os.path.exists(p): continue
        try: rows = json.load(open(p, encoding="utf-8"))
        except Exception: continue
        for r in rows if isinstance(rows, list) else []:
            if not isinstance(r, dict): continue
            n = r.get("company") or r.get("Company") or r.get("name")
            if n and len(norm(n)) > 3: names.add(norm(n))
    return ids, names


def main():
    dry = "--dry-run" in sys.argv
    keep_out = {r["deal_id"] for r in
                json.load(open(os.path.join(HERE, "pushed_deadpool.json"), encoding="utf-8"))}
    tracxn, tracxn_names = tracxn_origin()

    after, deals = None, []
    while True:
        b = {"limit": 200, "filterGroups": [], "properties":
             ["dealname", "dealstage", "hubspot_owner_id", "pipeline", "lead_source",
              "scraped_type", "createdate", "lh2_domain", "linkedin_url"]}
        if after: b["after"] = after
        _, d = hs("/crm/v3/objects/deals/search", "POST", b)
        deals += d.get("results", [])
        after = d.get("paging", {}).get("next", {}).get("after")
        if not after: break

    hit = []
    for x in deals:
        p = x["properties"]
        if p.get("hubspot_owner_id") not in TARGETS: continue
        if p.get("dealstage") != COLD_CALL.get(p.get("pipeline")): continue
        if x["id"] in keep_out: continue                     # deadpool stays
        if x["id"] not in tracxn and norm(p.get("dealname")) not in tracxn_names:
            continue                                         # only Tracxn-sourced
        hit.append(x)
    print(f"{len(deals)} deals scanned -> {len(hit)} Tracxn Cold Call deals held by Lamiya/Yuktha")
    by = {}
    for x in hit: by[TARGETS[x["properties"]["hubspot_owner_id"]]] = \
        by.get(TARGETS[x["properties"]["hubspot_owner_id"]], 0) + 1
    for k, v in sorted(by.items()): print(f"   {k:16} {v}")

    # ---- capture everything BEFORE touching anything ----
    pool = []
    for i, x in enumerate(hit, 1):
        p = x["properties"]
        _, a = hs(f"/crm/v4/objects/deals/{x['id']}/associations/contacts")
        cids = [str(y["toObjectId"]) for y in a.get("results", [])]
        contacts = []
        if cids:
            _, cr = hs("/crm/v3/objects/contacts/batch/read", "POST",
                       {"properties": ["firstname", "lastname", "email", "phone", "mobilephone",
                                       "jobtitle", "company", "linkedin_url", "city"],
                        "inputs": [{"id": c} for c in cids]})
            contacts = [c["properties"] | {"contact_id": c["id"]} for c in cr.get("results", [])]
        pool.append({
            "company": p.get("dealname"), "deal_id": x["id"],
            "owner": TARGETS[p["hubspot_owner_id"]], "stage": "Cold Call",
            "pipeline": p.get("pipeline"), "domain": p.get("lh2_domain") or "",
            "deal_linkedin": p.get("linkedin_url") or "", "created": (p.get("createdate") or "")[:10],
            "source": "Tracxn ranked sheet", "scraped_type": p.get("scraped_type") or "",
            "contacts": contacts})
        if i % 40 == 0: print(f"   ...captured {i}/{len(hit)}", flush=True)

    jp = os.path.join(HOLD, f"tracxn_pool_{TODAY}.json")
    cp = os.path.join(HOLD, f"tracxn_pool_{TODAY}.csv")
    json.dump(pool, open(jp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(cp, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["company", "domain", "contact", "title", "phone", "email", "linkedin",
                    "city", "was_owned_by", "deal_id", "contact_id", "created", "source"])
        for r in pool:
            if not r["contacts"]:
                w.writerow([r["company"], r["domain"], "", "", "", "", r["deal_linkedin"], "",
                            r["owner"], r["deal_id"], "", r["created"], r["source"]])
            for c in r["contacts"]:
                nm = f"{c.get('firstname','')} {c.get('lastname','')}".strip()
                w.writerow([r["company"], r["domain"], nm, c.get("jobtitle", ""),
                            c.get("mobilephone") or c.get("phone", ""), c.get("email", ""),
                            c.get("linkedin_url") or r["deal_linkedin"], c.get("city", ""),
                            r["owner"], r["deal_id"], c.get("contact_id", ""), r["created"],
                            r["source"]])
    ncon = sum(len(r["contacts"]) for r in pool)
    withph = sum(1 for r in pool for c in r["contacts"] if (c.get("mobilephone") or c.get("phone")))
    print(f"\npool written: {len(pool)} companies, {ncon} contacts ({withph} with a phone)")
    print(f"  {jp}\n  {cp}")

    if dry:
        print("\nDRY RUN — nothing archived."); return

    ok = 0
    for i in range(0, len(hit), 100):
        chunk = hit[i:i + 100]
        st, d = hs("/crm/v3/objects/deals/batch/archive", "POST",
                   {"inputs": [{"id": x["id"]} for x in chunk]})
        if st in (204, 200): ok += len(chunk)
        else: print(f"  archive batch failed: {st} {d}")
        time.sleep(0.4)
    print(f"\nARCHIVED {ok} deals (recycle bin — restorable). Contacts left in place.")
    print("Lamiya/Yuktha now keep only their deadpool-wave book at Cold Call.")


if __name__ == "__main__":
    main()
