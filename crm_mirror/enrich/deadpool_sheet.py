# -*- coding: utf-8 -*-
"""Rebuild the deadpool-wave working sheet from the ACTUAL outcome of the run.

Three tabs, written as CSVs (and one .xlsx if openpyxl is available):
  1_Pushed      every contact now live in HubSpot — owner, phone, deal id
  2_Companies   all 75 researched companies + why each was targeted, held or excluded
  3_NotPushed   resolved people who failed the +91 gate, and companies with nobody found

Run after push_deadpool.py. Regenerable — never hand-edit the output.
"""
import os, sys, json, csv, re
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(HUB, "crm_mirror", "sources", "deadpool_waves")
OUT = os.path.join(HUB, "exports", "lead_batches")
os.makedirs(OUT, exist_ok=True)

q = json.load(open(os.path.join(SRC, "deadpool_queue.json"), encoding="utf-8"))
st = json.load(open(os.path.join(HERE, "deadpool_resolved.json"), encoding="utf-8"))
pushed = json.load(open(os.path.join(HERE, "pushed_deadpool.json"), encoding="utf-8"))
rej = json.load(open(os.path.join(HERE, "deadpool_no_indian_number.json"), encoding="utf-8"))

def w(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        cw = csv.writer(f); cw.writerow(header); cw.writerows(rows)
    return path

# ---- 1. pushed ----
p1 = w(os.path.join(SRC, "1_pushed_to_hubspot.csv"),
    ["owner", "company", "wave", "founder", "title_at_company", "phone", "phone_type",
     "email", "linkedin", "current_role", "location", "shutdown", "funding_raised",
     "confidence", "deal_id"],
    [[r["owner_name"], r["display"], r["wave"], r["name"], r["title"], r["phone"], r["phone_kind"],
      r.get("email", ""), r.get("linkedin", ""), r.get("current", ""), r.get("location", ""),
      r["shutdown"], r["funding"], r["confidence"], r.get("deal_id", "")]
     for r in sorted(pushed, key=lambda x: (x["owner_name"], x["display"]))])

# ---- 2. every company + verdict ----
push_co = {}
for r in pushed: push_co.setdefault(r["display"], []).append(r)
rows = []
for c in q["companies"]:
    got = push_co.get(c["display"], [])
    if got: outcome = f"PUSHED to {got[0]['owner_name']}"
    elif c["gate"] == "EXCLUDE": outcome = "not targeted"
    else: outcome = "no callable person found"
    named = [p for k, p in st["people"].items() if p["display_company"] == c["display"]]
    rows.append([" | ".join(c["waves"]), c["display"], c["gate"], c["gate_reason"], outcome,
                 len(got), ", ".join(c["founders"]) or "(none named in research)",
                 sum(1 for p in named if p["verify"] in ("verified_company", "unique_name")),
                 len(st["companies"].get(c["company"], {}).get("hits", [])),
                 c["founded"], c["shutdown"], c["funding_raised"], c["status"], c["source"]])
p2 = w(os.path.join(SRC, "2_companies_all.csv"),
    ["wave", "company", "gate", "gate_reason", "outcome", "contacts_pushed",
     "founders_in_research", "named_resolved", "founders_recovered",
     "founded", "shutdown", "funding_raised", "status", "source"], rows)

# ---- 3. not pushed ----
rows = []
for r in rej:
    rows.append([r["display"], r["name"], r.get("current", ""), r.get("location", ""),
                 "no valid +91 number", "; ".join(r.get("all_phones", [])) or "(none returned)",
                 r.get("email", "")])
for k, p in st["people"].items():
    if p["verify"] in ("verified_company", "unique_name"): continue
    rows.append([p["display_company"], p["name"], "", "",
                 {"ambiguous": "namesakes — could not confirm identity",
                  "not_found": "not in SignalHire"}[p["verify"]], "", ""])
p3 = w(os.path.join(SRC, "3_not_pushed.csv"),
    ["company", "person", "current_role", "location", "reason", "phones_seen", "email"], rows)

# ---- optional xlsx ----
xlsx = ""
try:
    from openpyxl import Workbook
    wb = Workbook(); wb.remove(wb.active)
    for name, path in (("1_Pushed", p1), ("2_Companies", p2), ("3_NotPushed", p3)):
        ws = wb.create_sheet(name[:31])
        for row in csv.reader(open(path, encoding="utf-8-sig")): ws.append(row)
        for cell in ws[1]:
            from openpyxl.styles import Font
            cell.font = Font(bold=True)
        ws.freeze_panes = "A2"
        for col in ws.columns:
            ln = max((len(str(c.value or "")) for c in col[:200]), default=10)
            ws.column_dimensions[col[0].column_letter].width = min(46, max(11, ln + 2))
    xlsx = os.path.join(OUT, "Deadpool_Waves_2026-08-04.xlsx"); wb.save(xlsx)
except ImportError:
    pass

by_owner = {}
for r in pushed: by_owner[r["owner_name"]] = by_owner.get(r["owner_name"], 0) + 1
print(f"pushed contacts {len(pushed)} across {len(push_co)} companies")
for k, v in sorted(by_owner.items()): print(f"  {k:16} {v}")
print(f"not pushed rows  {len(rows)}")
for p in (p1, p2, p3, xlsx):
    if p: print("->", p)
