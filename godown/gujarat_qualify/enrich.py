# -*- coding: utf-8 -*-
import csv, json, urllib.request, urllib.error, time, os

HUB = "/Users/bhanu/Desktop/hubspot"
env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, ".env"), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
SH = env["signal_hire"]
IN_CSV = os.path.join(HUB, "temporary", "Gujarat_IT_top300.csv")
OUT_CSV = os.path.join(HUB, "temporary", "Gujarat_IT_top300_enriched.csv")
STATE = os.path.join(os.path.dirname(__file__), "enrich_state.json")

def reveal_full(li_url):
    body = {"items": [li_url], "withoutWaterfall": True}
    r = urllib.request.Request("https://www.signalhire.com/api/v1/candidate/search",
                               data=json.dumps(body).encode(), method="POST",
                               headers={"apikey": SH, "Content-Type": "application/json"})
    try:
        d = json.loads(urllib.request.urlopen(r, timeout=60).read().decode())
    except Exception:
        return None
    for it in (d if isinstance(d, list) else d.get("results", [])) or []:
        if isinstance(it, dict) and it.get("status") == "success":
            return (it.get("candidate") or {}).get("contacts") or []
    return None

rows = list(csv.DictReader(open(IN_CSV, encoding="utf-8-sig")))
print(f"total rows: {len(rows)}")
state = json.load(open(STATE)) if os.path.exists(STATE) else {}

results = []
for i, r in enumerate(rows, 1):
    li = (r.get("LinkedIn URL") or "").strip()
    if li in state:
        s = state[li]
    else:
        contacts = reveal_full(li) if li else None
        work = personal = phone = None
        if contacts:
            for c in contacts:
                if c.get("type") == "email":
                    if c.get("subType") == "work" and not work: work = c["value"]
                    elif c.get("subType") == "personal" and not personal: personal = c["value"]
                    elif not work and not personal and not c.get("subType"): personal = c["value"]
                if c.get("type") == "phone" and c.get("subType") == "mobile" and not phone:
                    phone = c["value"]
        s = {"email": work or personal or "", "is_official": bool(work), "phone": phone or ""}
        state[li] = s
        if i % 25 == 0: json.dump(state, open(STATE, "w"), indent=0)
        time.sleep(0.3)
    r2 = dict(r)
    r2["Email"] = s["email"]; r2["Is Official"] = "Yes" if s["is_official"] else ("No" if s["email"] else "")
    r2["Phone"] = s["phone"]
    results.append(r2)
    print(f"  [{i}/{len(rows)}] {r['First Name']} {r['Last Name']} ({r['Company']}) -> {s['email'] or '(none)'} / {s['phone'] or '(no mobile)'}", flush=True)

json.dump(state, open(STATE, "w"), indent=0)
fieldnames = list(rows[0].keys()) + ["Email", "Is Official", "Phone"]
with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for r in results: w.writerow(r)

n_email = sum(1 for r in results if r["Email"])
n_official = sum(1 for r in results if r["Is Official"]=="Yes")
n_phone = sum(1 for r in results if r["Phone"])
print(f"\nwrote {OUT_CSV}")
print(f"emails: {n_email}/{len(results)} ({n_official} official) | phones: {n_phone}/{len(results)}")
