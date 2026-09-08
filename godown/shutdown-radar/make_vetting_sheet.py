# -*- coding: utf-8 -*-
"""Turn every candidate list into one sheet a human can vet, banded by how vettable it is.

The buy list is machine output: scores, rationale strings, capture counts. A teammate
deciding "is this worth chasing" needs three things instead —

  1. A WAY TO LOOK AT IT. The single most useful column is a Wayback link that opens the
     dead product. No score substitutes for seeing the site. `live_site` is given too but
     is usually parked or sold by now, which is exactly why the archive link leads.
  2. THE EVIDENCE IN PLAIN WORDS. `app_signals` (login, pricing, dashboard...) is the real
     tell that software was running and being sold; the numeric scores are secondary.
  3. SOMEWHERE TO WRITE THE ANSWER. Empty verdict columns, so the sheet comes back as data
     rather than as prose in an email.

TIERS EXIST BECAUSE THE ROWS ARE NOT EQUALLY JUDGEABLE. Only tiers 1 and 2 carry a working
archive link. Tier 3 has no resolved domain at all, so there is nothing to open — asking
someone to "check the site" there is wasted effort, and a No from them means "I couldn't
see anything", not "not relevant". Tier 4 failed on network errors during the Wayback pass:
those are UNMEASURED, not misses, and a human verdict on them would permanently discard
candidates we simply never checked. Each tier therefore ships with its own instruction in
`how_to_judge`, written into every row so it cannot be missed in a spreadsheet.

`sector` is empty on every source row, but the NIC code was captured inside the
`why_codebase` rationale, so it is parsed back out here rather than shipping a blank column.

Within a tier, rows are ordered best-first, so a half-finished pass is still the useful half.
"""
import csv, os, re, sys, collections

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
HERE = os.path.dirname(os.path.abspath(__file__))
OUTD = os.path.join(HERE, "data", "out")
OUT  = os.path.join(OUTD, "LH2_vetting_sheet.csv")

# product_evidence -> (tier label, what the vetter should actually do)
TIER = {
 "verified_product": ("1 - product proven",
   "Open the archived site. App paths like login/pricing/dashboard were archived, so software "
   "was running and being sold. Judge: was this a real pre-2024 codebase worth buying?"),
 "probable_product": ("1 - product proven",
   "Open the archived site. App paths like login/pricing/dashboard were archived, so software "
   "was running and being sold. Judge: was this a real pre-2024 codebase worth buying?"),
 "brochure_only":    ("2 - website only",
   "Open the archived site. A website existed but we found NO app paths, so there may be no "
   "product behind it. Judge: does this look like a company that built software, or a shopfront?"),
 "domain_not_found": ("3 - no website found",
   "NOTHING TO OPEN - we never resolved a domain. Judge on name, sector and state only, or "
   "skip. A No here means 'could not see', not 'not relevant'."),
 "error":            ("4 - UNCHECKED, do not vet",
   "DO NOT VET. The archive check failed on network errors, so this is UNMEASURED, not a miss. "
   "It needs a re-run before any human looks at it."),
}
SOURCES = [("LH2_buy_list.csv", 120), ("LH2_secondary_list.csv", 995),
           ("LH2_unresolved_errors.csv", 88)]

def nic_of(why):
    m = re.match(r"NIC (\d+)\s*:\s*([^;(]+)", why or "")
    return (f"{m.group(1)} — {m.group(2).strip()}" if m else "")

def wb_stamp(d):
    """Wayback wants YYYYMMDD in the path; the CSV holds YYYY-MM-DD."""
    return (d or "").replace("-", "")

def pretty(name):
    """MADHUR NOURISHMENT PRODUCTS LLP -> Madhur Nourishment Products LLP."""
    keep = {"LLP", "PVT", "LTD", "OPC"}
    return " ".join(w if w in keep else w.capitalize() for w in " ".join((name or "").split()).split())

rows = []
for fn, _ in SOURCES:
    got = list(csv.DictReader(open(os.path.join(OUTD, fn), encoding="utf-8-sig")))
    print(f"  {fn:<32}{len(got):>5} rows")
    rows += got
print(f"  {'TOTAL':<32}{len(rows):>5} rows\n")

out = []
for r in rows:
    dom   = (r.get("wayback_domain") or "").strip()
    first = r.get("first_capture") or ""
    tier, howto = TIER.get(r.get("product_evidence") or "", ("3 - no website found", ""))
    out.append({
        "tier":           tier,
        "how_to_judge":   howto,
        "company":        pretty(r.get("company")),
        "cin":            r.get("cin") or "",
        # the vetting affordance: open these and you can see what they built. Blank, not a
        # broken URL, when no domain was ever resolved.
        "archived_site":  f"https://web.archive.org/web/{wb_stamp(first)}/http://{dom}" if (dom and first) else "",
        "all_snapshots":  f"https://web.archive.org/web/*/{dom}*" if dom else "",
        "live_site":      f"http://{dom}" if dom else "",
        "sector":         nic_of(r.get("why_codebase")),
        "state":          r.get("state") or "",
        "incorporated":   r.get("incorporated") or "",
        "site_live_for_years": r.get("capture_span_years") or "",
        "first_seen":     first,
        "last_seen":      r.get("last_capture") or "",
        "snapshots":      r.get("capture_count") or "",
        "product_proof":  r.get("product_evidence") or "",
        "app_signals":    (r.get("app_signals") or "").strip(),
        "product_score":  r.get("product_score") or "",
        "codebase_score": r.get("codebase_score") or "",
        "status_at_mca":  r.get("death_status") or "",
        # ---- the vetter fills these four; everything left of here is ours ----
        "RELEVANT? (Yes/No/Maybe)": "",
        "WHY (one line)":           "",
        "VETTED BY":                "",
        "NOTES":                    "",
        # ---- reference, for anyone who wants to argue with the call ----
        "evidence_product":  r.get("why_product") or "",
        "evidence_codebase": r.get("why_codebase") or "",
        "evidence_dead":     r.get("why_dead") or "",
        "legal_name":        r.get("legal_name") or "",
    })

RANK = {"verified_product": 0, "probable_product": 1, "brochure_only": 2,
        "domain_not_found": 3, "error": 4}
def fnum(v):
    try: return float(v or 0)
    except ValueError: return 0.0
out.sort(key=lambda x: (x["tier"], RANK.get(x["product_proof"], 9),
                        -fnum(x["product_score"]), -fnum(x["codebase_score"])))
for i, x in enumerate(out, 1): x["sr"] = i
cols = ["sr"] + [c for c in out[0] if c != "sr"]

with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(out)
print(f"wrote {OUT}\n  {len(out)} rows, {len(cols)} columns\n")

print(f"{'tier':<28}{'rows':>6}{'openable':>10}{'w/ signals':>12}{'w/ state':>10}")
print("-" * 66)
for t in sorted({x["tier"] for x in out}):
    g = [x for x in out if x["tier"] == t]
    print(f'{t:<28}{len(g):>6}{sum(1 for x in g if x["archived_site"]):>10}'
          f'{sum(1 for x in g if x["app_signals"]):>12}{sum(1 for x in g if x["state"]):>10}')
print("-" * 66)
print(f'{"TOTAL":<28}{len(out):>6}{sum(1 for x in out if x["archived_site"]):>10}'
      f'{sum(1 for x in out if x["app_signals"]):>12}{sum(1 for x in out if x["state"]):>10}')
print(f'\nactually vettable by opening a link: '
      f'{sum(1 for x in out if x["archived_site"])} of {len(out)}')
