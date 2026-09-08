# -*- coding: utf-8 -*-
import openpyxl, csv, json, urllib.request, urllib.error, time, os

HUB = "/Users/bhanu/Desktop/hubspot"
env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, ".env"), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
SH = env["signal_hire"]
IN_XLSX = "/tmp/company_ops_pilot.xlsx"
OUT_CSV = os.path.join(HUB, "godown", "company_ops_pilot_enriched.csv")
STATE = os.path.join(HUB, "godown", "company_ops_enrich_state.json")

def reveal_full(li_url):
    body = {"items": [li_url], "withoutWaterfall": True}
    r = urllib.request.Request("https://www.signalhire.com/api/v1/candidate/search",
                               data=json.dumps(body).encode(), method="POST",
                               headers={"apikey": SH, "Content-Type": "application/json"})
    try:
        d = json.loads(urllib.request.urlopen(r, timeout=60).read().decode())
    except Exception as e:
        return None, str(e)[:60]
    for it in (d if isinstance(d, list) else d.get("results", [])) or []:
        if isinstance(it, dict) and it.get("status") == "success":
            return (it.get("candidate") or {}).get("contacts") or [], "success"
    return [], "no_match"

wb = openpyxl.load_workbook(IN_XLSX, data_only=True)
ws = wb.active
rows = list(ws.iter_rows(min_row=2, values_only=True))
print(f"total rows: {len(rows)}")

state = json.load(open(STATE)) if os.path.exists(STATE) else {}
results = []
for i, r in enumerate(rows, 1):
    fn, ln, headline, loc, company, title, li = (list(r) + [None]*7)[:7]
    li = (li or "").strip()
    if li in state:
        s = state[li]
    else:
        contacts, status = (reveal_full(li) if li else (None, "no_url"))
        work = personal = phone = None
        if contacts:
            for c in contacts:
                if c.get("type") == "email":
                    if c.get("subType") == "work" and not work: work = c["value"]
                    elif c.get("subType") == "personal" and not personal: personal = c["value"]
                    elif not work and not personal and not c.get("subType"): personal = c["value"]
                if c.get("type") == "phone" and c.get("subType") == "mobile" and not phone:
                    phone = c["value"]
        s = {"email": work or personal or "", "is_official": bool(work), "phone": phone or "", "status": status}
        state[li] = s
        if i % 20 == 0: json.dump(state, open(STATE, "w"), indent=0)
        time.sleep(0.3)
    results.append({"First Name": fn, "Last Name": ln, "Company": company, "Title": title,
                    "LinkedIn URL": li, "Email": s["email"],
                    "Is Official": "Yes" if s["is_official"] else ("No" if s["email"] else ""),
                    "Phone": s["phone"]})
    print(f"  [{i}/{len(rows)}] {fn} {ln} ({company}) -> {s['email'] or '(none)'}", flush=True)

json.dump(state, open(STATE, "w"), indent=0)
with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["First Name","Last Name","Company","Title","LinkedIn URL","Email","Is Official","Phone"])
    w.writeheader()
    for r in results: w.writerow(r)
print(f"\nwrote {OUT_CSV}")
n_email = sum(1 for r in results if r["Email"])
n_official = sum(1 for r in results if r["Is Official"]=="Yes")
n_phone = sum(1 for r in results if r["Phone"])
print(f"emails: {n_email}/{len(results)} ({n_official} official) | phones: {n_phone}/{len(results)}")
