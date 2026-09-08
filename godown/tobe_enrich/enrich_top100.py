# -*- coding: utf-8 -*-
import csv, json, urllib.request, urllib.error, time, os

HUB = "/Users/bhanu/Desktop/hubspot"
HERE = os.path.dirname(os.path.abspath(__file__))
env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, ".env"), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
SH = env["signal_hire"]
IN_CSV = os.path.join(HUB, "tobe.csv")
OUT_CSV = os.path.join(HUB, "tobe_top100_enriched.csv")

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

rows = list(csv.DictReader(open(IN_CSV, encoding="utf-8-sig"), delimiter="\t"))
print("fieldnames:", list(rows[0].keys()))
top100 = rows[:100]
print(f"processing top {len(top100)} rows")

results = []
for i, r in enumerate(top100, 1):
    li = r.get("LinkedIn URL", "").strip()
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
    final_email = work or personal or ""
    results.append({"First Name": r.get("First Name",""), "Last Name": r.get("Last Name",""),
                    "Company": r.get("Company",""), "LinkedIn URL": li,
                    "Email": final_email, "Is Official": "Yes" if work else ("No" if final_email else ""),
                    "Phone": phone or ""})
    print(f"  [{i}/100] {r.get('First Name','')} {r.get('Last Name','')} -> {final_email or '(none)'}", flush=True)
    time.sleep(0.3)

with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["First Name","Last Name","Company","LinkedIn URL","Email","Is Official","Phone"])
    w.writeheader()
    for r in results: w.writerow(r)
print(f"\nwrote {OUT_CSV}")

n_email = sum(1 for r in results if r["Email"])
n_official = sum(1 for r in results if r["Is Official"]=="Yes")
print(f"emails found: {n_email}/100 ({n_official} official)")
