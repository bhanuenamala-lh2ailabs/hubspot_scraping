# -*- coding: utf-8 -*-
"""Pull both upstream sheets and every HubSpot deal, so supply and outcome can be joined.

The question this feeds: for each source, how much is left unpushed, how much reached
HubSpot, and how far did what we pushed actually get.
"""
import os, sys, json, time, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
HUB = os.path.dirname(ROOT)
OUT = os.path.join(ROOT, "sources", "_audit"); os.makedirs(OUT, exist_ok=True)

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

KEY = os.path.join(HUB, "lh2-pipeline-9982aa4422f5.json")
SHEETS = {"private_codebase_tracker": "1B9in9qK1V3IyjoyjYSqwn0gGRyoP9qVlMBGKKheoEhM",
          "tracxn":                   "12BLV3nv1d9Is4UHN113YVhiTBNilHe-9phIMMCEKS4A"}
creds = Credentials.from_service_account_file(
    KEY, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
svc = build("sheets", "v4", credentials=creds)

for name, sid in SHEETS.items():
    meta = svc.spreadsheets().get(spreadsheetId=sid).execute()
    tabs = [s["properties"]["title"] for s in meta["sheets"]]
    print(f"\n=== {name} — {len(tabs)} tabs ===")
    book = {}
    for tab in tabs:
        try:
            v = svc.spreadsheets().values().get(
                spreadsheetId=sid, range=f"'{tab}'").execute().get("values", [])
        except Exception as e:
            print(f"   {tab[:40]:<42} ! {str(e)[:60]}"); continue
        if not v:
            print(f"   {tab[:40]:<42} empty"); continue
        hdr = [h.strip() for h in v[0]]
        rows = [dict(zip(hdr, r + [""] * (len(hdr) - len(r))))
                for r in v[1:] if any(str(c).strip() for c in r)]
        book[tab] = rows
        print(f"   {tab[:40]:<42}{len(rows):>6} rows | cols: {', '.join(hdr[:7])[:88]}")
    json.dump(book, open(os.path.join(OUT, name + ".json"), "w", encoding="utf-8"),
              ensure_ascii=False)

# ---- HubSpot: every deal, live and archived, with the fields needed to judge outcome ----
env = {l.split('=', 1)[0].strip().lower(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
H = {"Authorization": "Bearer " + env["hubspot_key"], "Content-Type": "application/json"}

def hs(path, method="GET", body=None):
    url = "https://api.hubapi.com" + path
    data = json.dumps(body).encode() if body is not None else None
    for a in range(5):
        try:
            req = urllib.request.Request(url, data=data, method=method, headers=H)
            with urllib.request.urlopen(req, timeout=45) as r:
                t = r.read().decode(); return r.status, (json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503, 504) and a < 4: time.sleep(2 * (a + 1)); continue
            return e.code, {"raw": e.read().decode()[:200]}
        except Exception:
            if a == 4: raise
            time.sleep(2)

PS = hs("/crm/v3/pipelines/deals")[1]["results"]
LAB = {s["id"]: s["label"] for p in PS for s in p["stages"]}
PROPS = ["dealname", "dealstage", "pipeline", "lead_source", "scraped_type",
         "hubspot_owner_id", "createdate", "domain", "lh2_domain", "linkedin_url",
         "loc", "pr_count", "num_repos", "cost", "deal_value_range"]

def pull(archived):
    out, after = [], None
    while True:
        if archived:
            u = f"/crm/v3/objects/deals?archived=true&limit=100&properties={','.join(PROPS)}"
            if after: u += "&after=" + after
            s, d = hs(u)
        else:
            b = {"limit": 200, "properties": PROPS}
            if after: b["after"] = after
            s, d = hs("/crm/v3/objects/deals/search", "POST", b)
        out += d.get("results", [])
        after = (d.get("paging") or {}).get("next", {}).get("after")
        if not after: break
        time.sleep(0.12)
    return out

live = pull(False); arch = pull(True)
print(f"\nHubSpot: {len(live)} live deals, {len(arch)} archived")
deals = []
for src, rs in (("live", live), ("archived", arch)):
    for r in rs:
        p = r["properties"]
        deals.append({"id": r["id"], "state": src, "name": p.get("dealname") or "",
                      "stage": LAB.get(p.get("dealstage"), p.get("dealstage")),
                      "pipeline": p.get("pipeline"), "lead_source": p.get("lead_source") or "",
                      "scraped_type": p.get("scraped_type") or "",
                      "owner": p.get("hubspot_owner_id"), "created": (p.get("createdate") or "")[:10],
                      "domain": (p.get("domain") or p.get("lh2_domain") or "").lower().strip(),
                      "linkedin": (p.get("linkedin_url") or "").lower().strip(),
                      "loc": p.get("loc"), "cost": p.get("cost")})
json.dump(deals, open(os.path.join(OUT, "hubspot_deals.json"), "w", encoding="utf-8"),
          ensure_ascii=False)
print(f"wrote {OUT}")
