# -*- coding: utf-8 -*-
"""Turn the deadpool-wave research table into (a) a working sheet and (b) a person-level
enrichment queue for SignalHire.

Selection logic — three gates, applied in order and recorded per row:
  1. ALIVE          -> the company still trades; never target it.
  2. IP_HELD        -> a large acquirer owns the code (Google/Amazon/BYJU'S/Snapdeal/Future).
                       The founder cannot sell what they no longer own.
  3. NO_FOUNDER     -> the research row says "various"/corporate; nobody to call yet.
Everything else is TARGET: the company is dead or dormant, and a named founder still
personally controls (or can release) the pre-2024 codebase.

Outputs (crm_mirror/sources/deadpool_waves/):
  deadpool_waves_companies.csv   one row per company + gate verdict
  deadpool_waves_people.csv      one row per named founder (the call list)
  deadpool_queue.json            the enrichment queue consumed by push_deadpool.py
"""
import os, re, csv, json

HERE = os.path.dirname(os.path.abspath(__file__))
HUB = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(HUB, "crm_mirror", "sources", "deadpool_waves")
TSV = os.path.join(SRC, "deadpool_waves.tsv")

def norm(n): return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", (n or "").lower())).strip()

# acquirers big enough that the IP is theirs, not the founder's
IP_HOLDERS = ("byju", "amazon", "google", "youtube", "snapdeal", "future group")

def base_name(c):
    """'Baxi (74 BC Technologies)' -> 'Baxi'; 'Doormint (laundry pivot)' -> 'Doormint'."""
    return re.sub(r"\s*\([^)]*\)\s*$", "", c).strip()

def split_founders(s):
    s = (s or "").strip()
    if not s or s == "-": return []
    if s.lower().startswith("various"): return []
    if s.startswith("("): return []                        # "(Amazon corporate)", "(Snapdeal)"
    s = re.sub(r"\+\s*\d+.*$", "", s)                      # "Xitij Kothi + 4"
    s = re.sub(r"\+\s*$", "", s)                           # "Sachin Bhatia +"
    s = re.sub(r"\s*\([^)]*\)", "", s)                     # "Rutvik Doshi (CEO)"
    out = []
    for p in re.split(r",| and ", s):
        p = p.strip(" .")
        if len(p.split()) >= 2 and len(p) > 4: out.append(p)
        elif p and len(p) > 4: out.append(p)               # single-token names e.g. "Raghunandan G"
    return out

rows = list(csv.DictReader(open(TSV, encoding="utf-8"), delimiter="\t"))

companies, seen = [], {}
for r in rows:
    disp = r["company"].strip()
    key = norm(base_name(disp))
    status = r["status"]; shutdown = r["shutdown"]
    founders = split_founders(r["founders"])

    if key in seen:                                        # Doormint / Townrush appear twice
        prev = seen[key]
        prev["waves"].append(r["wave"])
        for f in founders:
            if norm(f) not in {norm(x) for x in prev["founders"]}: prev["founders"].append(f)
        continue

    if "ALIVE" in shutdown.upper() or "alive" in status.lower() and "Acquired-alive" in status:
        gate, why = "EXCLUDE", "ALIVE — still trading"
    elif any(h in status.lower() for h in IP_HOLDERS):
        gate, why = "EXCLUDE", "IP_HELD — acquirer owns the codebase"
    elif not founders:
        gate, why = "HOLD", "NO_FOUNDER — research row has no named person"
    else:
        gate, why = "TARGET", "dead/dormant + named founder"

    rec = {"waves": [r["wave"]], "company": base_name(disp), "display": disp,
           "founders": founders, "founded": r["founded"], "shutdown": r["shutdown"],
           "funding_raised": r["funding_raised"], "status": status,
           "founder_notes": r["founder_notes"], "source": r["source"],
           "gate": gate, "gate_reason": why}
    seen[key] = rec; companies.append(rec)

# ---- company sheet ----
os.makedirs(SRC, exist_ok=True)
cpath = os.path.join(SRC, "deadpool_waves_companies.csv")
with open(cpath, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["wave", "company", "founders", "founded", "shutdown", "funding_raised",
                "status", "founder_notes", "source", "gate", "gate_reason"])
    for c in companies:
        w.writerow([" | ".join(c["waves"]), c["display"], ", ".join(c["founders"]), c["founded"],
                    c["shutdown"], c["funding_raised"], c["status"], c["founder_notes"],
                    c["source"], c["gate"], c["gate_reason"]])

# ---- person sheet + queue ----
people = []
for c in companies:
    if c["gate"] != "TARGET": continue
    for i, f in enumerate(c["founders"]):
        people.append({"name": f, "company": c["company"], "display_company": c["display"],
                       "wave": c["waves"][0].split(" (")[0], "founded": c["founded"],
                       "shutdown": c["shutdown"], "funding_raised": c["funding_raised"],
                       "status": c["status"], "notes": c["founder_notes"],
                       "is_primary": i == 0, "source": c["source"]})

ppath = os.path.join(SRC, "deadpool_waves_people.csv")
with open(ppath, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["founder", "company", "wave", "founded", "shutdown", "funding_raised",
                "status", "primary_contact", "notes"])
    for p in people:
        w.writerow([p["name"], p["display_company"], p["wave"], p["founded"], p["shutdown"],
                    p["funding_raised"], p["status"], "Y" if p["is_primary"] else "", p["notes"]])

json.dump({"companies": companies, "people": people},
          open(os.path.join(SRC, "deadpool_queue.json"), "w", encoding="utf-8"), indent=1)

g = {}
for c in companies: g[c["gate"]] = g.get(c["gate"], 0) + 1
print(f"rows in table      : {len(rows)}")
print(f"unique companies   : {len(companies)}")
for k in ("TARGET", "HOLD", "EXCLUDE"): print(f"  {k:8} {g.get(k,0)}")
print(f"named founders     : {len(people)}  ({sum(1 for p in people if p['is_primary'])} primary)")
print("\nEXCLUDED / HELD:")
for c in companies:
    if c["gate"] != "TARGET": print(f"  {c['gate']:8} {c['display']:34} {c['gate_reason']}")
print(f"\n-> {cpath}\n-> {ppath}")
