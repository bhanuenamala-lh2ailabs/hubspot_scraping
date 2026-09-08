# -*- coding: utf-8 -*-
"""
LH2 CRM mirror + upstream sources sync.

Maintains a LOCAL copy of HubSpot (deals + their contacts + companies) and the
OutFlo lead pull, plus dedup indexes, so pushes dedup against local files instead
of scanning HubSpot every time.

Usage:
  python sync.py hubspot     # refresh the HubSpot mirror (deals/contacts/companies + indexes)
  python sync.py outflo      # refresh the OutFlo lead pull
  python sync.py all         # both  (default)

Run weekly (or before a big push). Individual push scripts should ALSO write each
new/updated deal into data/deals.json + index/ as they push (see helpers at bottom).
"""
import json, os, sys, time, datetime, urllib.request, urllib.error
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data"); IDX = os.path.join(DATA, "index")
SNAP = os.path.join(DATA, "snapshots"); OUTF = os.path.join(ROOT, "outflo")
for d in (DATA, IDX, SNAP, OUTF, os.path.join(OUTF, "snapshots")): os.makedirs(d, exist_ok=True)

ENVF = os.path.join(os.path.dirname(ROOT), ".env")
env = {}
for l in open(ENVF, encoding="utf-8-sig"):
    if "=" in l and not l.strip().startswith("#"):
        k, v = l.split("=", 1); env[k.strip().lower()] = v.strip()
HS = env["hubspot_key"]; OUTFLO = env.get("outflo_api_key"); UA = "Mozilla/5.0 AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
TODAY = datetime.date.today().isoformat()   # snapshot stamp (auto)

def hcall(path, method="GET", body=None):
    url = path if path.startswith("http") else "https://api.hubapi.com" + path
    data = json.dumps(body).encode() if body is not None else None
    for a in range(6):
        try:
            req = urllib.request.Request(url, data=data, method=method,
                headers={"Authorization": "Bearer " + HS, "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=90) as r:
                t = r.read().decode(); return r.status, (json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503, 504) and a < 5: time.sleep(2*(a+1)); continue
            return e.code, {"raw": e.read().decode()[:300]}
        except Exception:
            if a == 5: raise
            time.sleep(2*(a+1))

def scan(obj, props):
    out = []; after = None
    while True:
        b = {"limit": 100, "properties": props, "filterGroups": []}
        if after: b["after"] = after
        s, d = hcall(f"/crm/v3/objects/{obj}/search", "POST", b)
        out += d.get("results", []); after = d.get("paging", {}).get("next", {}).get("after")
        if not after: break
        time.sleep(0.05)
    return out

def batch_assoc(frm, to, ids):
    m = {}
    for i in range(0, len(ids), 100):
        s, d = hcall(f"/crm/v4/associations/{frm}/{to}/batch/read", "POST", {"inputs": [{"id": x} for x in ids[i:i+100]]})
        for r in d.get("results", []):
            tos = [str(t["toObjectId"]) for t in r.get("to", [])]
            if tos: m[str(r["from"]["id"])] = tos
        time.sleep(0.04)
    return m

def norm_li(u):
    u = (u or "").strip().lower().split("?")[0].rstrip("/")
    return u.replace("http://", "https://").replace("https://www.", "https://")
def norm_name(n):
    import re; return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", (n or "").lower())).strip()

DEAL_PROPS = ["dealname","pipeline","dealstage","hubspot_owner_id","poc","scraped_type","lead_source",
    "source_tab","linkedin_url","lh2_domain","domain","hs_priority","loc","pr_count","num_projects",
    "num_repos","cost","deal_value_range","metadata_link","outflo_request_sent","outflo_connected_at",
    "outflo_replied_at","createdate","hs_lastmodifieddate"]
CONTACT_PROPS = ["firstname","lastname","email","phone","mobilephone","linkedin_url","jobtitle","company"]
COMPANY_PROPS = ["name","domain","lh2_domain","city","scraped_type"]

def sync_hubspot():
    print("HubSpot: pulling deals...", flush=True)
    deals = scan("deals", DEAL_PROPS)
    dids = [str(x["id"]) for x in deals]
    print(f"  {len(deals)} deals. associations...", flush=True)
    d2c = batch_assoc("deals", "contacts", dids)
    d2co = batch_assoc("deals", "companies", dids)
    cids = sorted({c for v in d2c.values() for c in v})
    coids = sorted({c for v in d2co.values() for c in v})
    print(f"  reading {len(cids)} contacts, {len(coids)} companies...", flush=True)
    def read(obj, ids, props):
        out = {}
        for i in range(0, len(ids), 100):
            s, d = hcall(f"/crm/v3/objects/{obj}/batch/read", "POST", {"properties": props, "inputs": [{"id": x} for x in ids[i:i+100]]})
            for r in d.get("results", []): out[str(r["id"])] = r.get("properties", {})
            time.sleep(0.04)
        return out
    contacts = read("contacts", cids, CONTACT_PROPS)
    companies = read("companies", coids, COMPANY_PROPS)
    # assemble deals with their links
    deal_recs = []
    by_li = {}; by_dom = {}; by_nm = {}
    for x in deals:
        did = str(x["id"]); p = x["properties"]
        rec = {"id": did, **{k: p.get(k) for k in DEAL_PROPS},
               "contact_ids": d2c.get(did, []), "company_ids": d2co.get(did, [])}
        deal_recs.append(rec)
        li = norm_li(p.get("linkedin_url")); dom = (p.get("lh2_domain") or p.get("domain") or "").strip().lower()
        nm = norm_name(p.get("dealname"))
        if li: by_li.setdefault(li, did)
        if dom: by_dom.setdefault(dom, did)
        if nm: by_nm.setdefault(nm, did)
    json.dump(deal_recs, open(os.path.join(DATA, "deals.json"), "w", encoding="utf-8"), ensure_ascii=False)
    json.dump([{"id": k, **v} for k, v in contacts.items()], open(os.path.join(DATA, "contacts.json"), "w", encoding="utf-8"), ensure_ascii=False)
    json.dump([{"id": k, **v} for k, v in companies.items()], open(os.path.join(DATA, "companies.json"), "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(by_li, open(os.path.join(IDX, "by_linkedin.json"), "w"), ensure_ascii=False)
    json.dump(by_dom, open(os.path.join(IDX, "by_domain.json"), "w"), ensure_ascii=False)
    json.dump(by_nm, open(os.path.join(IDX, "by_name.json"), "w"), ensure_ascii=False)
    # snapshot
    json.dump({"generated": TODAY, "deals": len(deal_recs), "contacts": len(contacts), "companies": len(companies)},
              open(os.path.join(SNAP, f"hubspot_{TODAY}.json"), "w"))
    # summary
    print(f"HubSpot mirror saved: {len(deal_recs)} deals, {len(contacts)} contacts, {len(companies)} companies")
    print("  by pipeline:", dict(Counter(r["pipeline"] for r in deal_recs)))
    print("  by scraped_type:", dict(Counter(r.get("scraped_type") or "-" for r in deal_recs)))
    print(f"  indexes: linkedin={len(by_li)} domain={len(by_dom)} name={len(by_nm)}")

def sync_outflo():
    """Pull leads from EVERY campaign OutFlo reports, not a hardcoded list.

    The old version had three campaign IDs baked in. Two of them no longer appear in
    OutFlo's campaign list at all (renamed or replaced), and meanwhile FIVE active
    campaigns were invisible to us — the four alumni codebase campaigns and Company Ops.
    That is why the replied-lead flow looked like a trickle: we were reading a fraction of
    the funnel. Enumerating from the API means a new campaign is picked up automatically.

    EXCLUDED by name: "Company Ops 1st" — that is the ops-data motion (Kartik's side), a
    different buy-mode from the codebase pipeline these leads feed.
    """
    if not OUTFLO: print("no OUTFLO_API_KEY; skipping"); return
    EXCLUDE = {"company ops 1st"}
    LEGACY = [("India", "b2bc9663-f14f-410e-a2b2-633e3c4ae907"),
              ("India", "fd8756d5-c7b5-4fb2-bacb-737df2d32139")]   # stale ids that still return leads

    def oget(u):
        for a in range(5):
            try:
                with urllib.request.urlopen(urllib.request.Request(
                        u, headers={"x-api-key": OUTFLO, "User-Agent": UA}), timeout=180) as r:
                    return json.loads(r.read().decode())
            except Exception:
                if a == 4: return None
                time.sleep(2)

    d = oget("https://live.outflo.in/api/public/campaigns") or {}
    camps = d.get("data", {}).get("campaigns") or d.get("data") or []
    if isinstance(camps, dict): camps = camps.get("campaigns", [])
    todo, skipped = [], []
    for c in camps:
        cid = c.get("campaignId") or c.get("_id") or c.get("id")
        nm = (c.get("name") or c.get("campaignName") or "").strip()
        if not cid: continue
        if nm.lower() in EXCLUDE:
            skipped.append(nm); continue
        bucket = "Indonesia" if "indonesi" in nm.lower() else "India"
        todo.append((bucket, cid, nm))
    known = {c for _, c, _ in todo}
    for b, cid in LEGACY:
        if cid not in known: todo.append((b, cid, "(legacy id)"))
    if skipped: print("  excluded by name:", skipped)

    leads, per = [], {}
    for bucket, cid, nm in todo:
        r = oget(f"https://live.outflo.in/api/public/campaigns/{cid}/leads")
        if not r: print(f"  {nm[:38]:40} FETCH FAILED"); continue
        rows = (r.get("data") or {}).get("leads", [])
        per[nm or cid] = len(rows)
        for L in rows:
            leads.append({"bucket": bucket, "campaign_id": cid, "campaign": nm,
                "linkedin": L.get("linkedinUrl") or L.get("LinkedIn URL"),
                "name": L.get("Lead"), "first": L.get("First Name"), "last": L.get("Last Name"),
                "company": L.get("Company"), "title": L.get("Title"), "headline": L.get("Headline"),
                "location": L.get("Location"), "conn": L.get("Connection Status"),
                "reply": L.get("Reply Status"), "overall": L.get("Overall Status"),
                "last_action": L.get("Last Action At"), "sender": L.get("Assigned Account"),
                "leadId": L.get("leadId")})
    json.dump(leads, open(os.path.join(OUTF, "leads.json"), "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(leads, open(os.path.join(OUTF, "snapshots", f"leads_{TODAY}.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print(f"OutFlo pull: {len(leads)} leads from {len(per)} campaigns")
    for k, v in sorted(per.items(), key=lambda x: -x[1]): print(f"   {v:>6}  {k[:52]}")
    print("  buckets:", dict(Counter(l["bucket"] for l in leads)),
          "| connected:", sum(1 for l in leads if l["conn"] == "Connected"),
          "replied:", sum(1 for l in leads if l["reply"] == "Replied"))


def sync_tracxn():
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    KEY = os.path.join(os.path.dirname(ROOT), "lh2-pipeline-9982aa4422f5.json")
    SID = "12BLV3nv1d9Is4UHN113YVhiTBNilHe-9phIMMCEKS4A"
    svc = build("sheets", "v4", credentials=Credentials.from_service_account_file(KEY, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]))
    out = os.path.join(ROOT, "sources", "tracxn"); snap = os.path.join(out, "snapshots")
    os.makedirs(snap, exist_ok=True)
    summ = {}
    for tab in ["funded", "unfunded", "LH2 Ranked Targets", "LH2 Ranked Targets Outreach Tracker"]:
        v = svc.spreadsheets().values().get(spreadsheetId=SID, range=f"'{tab}'").execute().get("values", [])
        hdr = v[0] if v else []
        rows = [dict(zip(hdr, r + [""]*(len(hdr)-len(r)))) for r in v[1:] if any(c.strip() for c in r)]
        json.dump(rows, open(os.path.join(out, tab.lower().replace(" ", "_")+".json"), "w", encoding="utf-8"), ensure_ascii=False)
        summ[tab] = len(rows)
    rt = json.load(open(os.path.join(out, "lh2_ranked_targets.json"), encoding="utf-8"))
    by_dom = {(r.get("domain") or "").strip().lower(): r.get("rank") for r in rt if (r.get("domain") or "").strip()}
    json.dump(by_dom, open(os.path.join(out, "index_by_domain.json"), "w"), ensure_ascii=False)
    json.dump({"generated": TODAY, **summ}, open(os.path.join(snap, f"tracxn_{TODAY}.json"), "w"))
    print("Tracxn local copy saved:", summ, "| domain index:", len(by_dom))

if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("hubspot", "all"): sync_hubspot()
    if what in ("outflo", "all"): sync_outflo()
    if what in ("tracxn", "all"): sync_tracxn()
