# -*- coding: utf-8 -*-
"""Set up the Company Ops-Data acquisition portal (key: hubspot_kartik).

Creates the LinkedIn-led deal pipeline (stages per docs/sop/COmpanyOpsDataFlow.md) + every custom
property the flow needs. Idempotent: existing pipeline/properties are updated, not duplicated.

Usage:
  python setup_opsdata_account.py --dry-run     # preview everything, write nothing
  python setup_opsdata_account.py               # create for real
"""
import os, sys, json, time, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
env = {}
for l in open(os.path.join(HUB, ".env"), encoding="utf-8-sig"):
    if "=" in l and not l.strip().startswith("#"):
        k, v = l.split("=", 1); env[k.strip().lower()] = v.strip()
KEY = env.get("hubspot_kartik")
DRY = "--dry-run" in sys.argv
if not KEY and not DRY:
    sys.exit("hubspot_kartik not found in .env — add the new portal's private-app token first.")

PIPELINE_LABEL = "Company Ops Data"

# ---------------- stages (order matters) ----------------
# (label, kind)  kind: open | won | lost
STAGES = [
    ("Begin Here",                                   "open"),
    ("Profile PreScreen",                            "open"),
    ("Cold LinkedIn Sent",                           "open"),
    ("Message Back (Email + 2nd Msg)",               "open"),
    ("Replied",                                      "open"),
    ("Ghost Follow-Up",                              "open"),
    ("GMeet Fixed",                                  "open"),
    ("One Pager + Deck Shared",                      "open"),
    ("Internal Evaluation (Sample)",                 "open"),
    ("Samples Requested",                            "open"),
    ("Sample Follow-Up",                             "open"),
    ("Sample Received + Interest Gauge",             "open"),
    ("Token Amount Paid",                            "open"),
    ("Commercial Negotiations",                      "open"),
    ("Deal Contract Signed",                         "open"),
    ("Data Migration Done",                          "open"),
    ("Payment Initiation",                           "open"),
    ("Closed/Won",                                   "won"),
    # --- dead ends (from the flow doc) ---
    ("Dead/Cold/WrongFit",                           "lost"),
    ("Dead/Cold/Not Interested",                     "lost"),
    ("Dead/Cold/No Reply",                           "lost"),
    ("Dead/Interested/No Show",                      "lost"),
    ("Dead/Sample Not Collected/Wrong Fit-Rejected", "lost"),
    ("Dead/Sample Not Received/Company No Show",     "lost"),
    ("Dead/No Interest from Demand/Wrong Fit-Rejected", "lost"),
    ("Dead/Negotiations/Pricing",                    "lost"),
    ("Dead/Negotiations/Contractual",                "lost"),
    # --- ADDED (not in the doc, but this line needs them) ---
    ("Dead/GMeet/Privacy Concerns",                  "lost"),   # ops data = PII-sensitive; track separately
    ("Dead/Migration/Failed",                        "lost"),   # post-contract delivery failure
]

def stage_body(label, kind, order):
    md = {"isClosed": "true" if kind in ("won", "lost") else "false",
          "probability": "1.0" if kind == "won" else ("0.0" if kind == "lost" else "0.5")}
    return {"label": label, "displayOrder": order, "metadata": md}

# ---------------- custom properties ----------------
def P(name, label, type_, field, group, options=None, description=""):
    d = {"name": name, "label": label, "type": type_, "fieldType": field,
         "groupName": group, "description": description}
    if options: d["options"] = [{"label": o, "value": o, "displayOrder": i} for i, o in enumerate(options)]
    elif type_ == "bool":   # HubSpot requires booleans to carry explicit true/false options
        d["options"] = [{"label": "Yes", "value": "true", "displayOrder": 0},
                        {"label": "No",  "value": "false", "displayOrder": 1}]
    return d

DG = "dealinformation"
DEAL_PROPS = [
    # identity / routing (mirrors the main account so scripts port over)
    P("lh2_domain", "LH2 Domain (unique key)", "string", "text", DG),
    P("linkedin_url", "LinkedIn URL", "string", "text", DG),
    P("lead_source", "Lead Source", "string", "text", DG),
    P("poc", "PoC", "string", "text", DG),
    P("deal_value_range", "Deal Value Range ($)", "string", "text", DG),
    P("cost", "Deal Cost (USD)", "number", "number", DG),
    P("metadata_link", "Metadata / Results Link", "string", "text", DG),
    # LinkedIn-led outreach tracking (this flow starts on LinkedIn, not the phone)
    P("li_msg1_sent_at", "LinkedIn Msg 1 Sent", "datetime", "date", DG),
    P("li_msg2_sent_at", "LinkedIn Msg 2 Sent", "datetime", "date", DG),
    P("cold_email_sent_at", "Cold Email Sent", "datetime", "date", DG),
    P("replied_at", "Replied At", "datetime", "date", DG),
    P("prescreen_result", "PreScreen Result", "enumeration", "select", DG,
      ["Good Fit", "Wrong Fit", "Not Screened"]),
    P("followup_count", "Follow-Up Count", "number", "number", DG),
    # meeting
    P("gmeet_link", "GMeet Link", "string", "text", DG),
    P("gmeet_date", "GMeet Date", "datetime", "date", DG),
    P("gmeet_outcome", "GMeet Outcome", "enumeration", "select", DG,
      ["Proceeds", "Wrong Fit", "Privacy Concerns", "No Show"]),
    # one-pager / evaluation
    P("onepager_sent_at", "One Pager Sent", "datetime", "date", DG),
    P("onepager_received_at", "One Pager Received", "datetime", "date", DG),
    P("internal_eval_result", "Internal Evaluation Result", "enumeration", "select", DG,
      ["Good Fit", "Wrong Fit - Rejected", "Pending"]),
    # sample
    P("sample_requested_at", "Sample Requested", "datetime", "date", DG),
    P("sample_received_at", "Sample Received", "datetime", "date", DG),
    P("sample_format", "Sample Format", "enumeration", "select", DG,
      ["CSV", "SQL dump", "API export", "Excel", "PDF / Docs", "Mixed"]),
    P("sample_quality_score", "Sample Quality Score (0-100)", "number", "number", DG),
    P("interest_gauge", "Demand Interest Gauge", "enumeration", "select", DG,
      ["Strong", "Moderate", "Weak", "Wrong Fit - Rejected"]),
    # token + close
    P("token_amount", "Token Amount Paid (USD)", "number", "number", DG),
    P("token_paid_at", "Token Paid At", "datetime", "date", DG),
    P("data_migration_done_at", "Data Migration Done At", "datetime", "date", DG),
    P("payment_initiated_at", "Payment Initiated At", "datetime", "date", DG),
    # --- what we're actually buying: internal operating know-how / ops data ---
    P("ops_data_types", "Ops Data Types", "enumeration", "checkbox", DG,
      ["SOPs & playbooks", "Process docs", "Internal tooling / workflows", "CRM records",
       "Support tickets", "Transactions", "Logistics / delivery", "Inventory",
       "HR / org structure", "Vendor / supplier", "Financial ops"]),
    P("systems_of_record", "Systems of Record", "string", "text", DG,
      description="Salesforce / Zoho / Tally / SAP / custom-built ..."),
    P("record_count", "Record Count", "number", "number", DG),
    P("data_volume_gb", "Data Volume (GB)", "number", "number", DG),
    P("data_date_range_start", "Data Covers From", "date", "date", DG),
    P("data_date_range_end", "Data Covers To", "date", "date", DG),
    P("data_format", "Data Format", "enumeration", "select", DG,
      ["CSV", "SQL dump", "API export", "Excel", "PDF / Docs", "Mixed"]),
    P("sop_docs_available", "SOP Docs Available", "bool", "booleancheckbox", DG),
    P("internal_tools_count", "Internal Tools Documented", "number", "number", DG),
    P("completeness_pct", "Completeness %", "number", "number", DG),
    # privacy / compliance (ops data is PII-sensitive — the codebase line doesn't need this)
    P("pii_present", "PII Present", "bool", "booleancheckbox", DG),
    P("pii_scrub_required", "PII Scrub Required", "bool", "booleancheckbox", DG),
    P("compliance_notes", "Compliance / DPA Notes", "string", "textarea", DG),
    # targeting scores (from our asset-fit vetting)
    P("opsdata_fit", "Ops-Data Fit (0-100)", "number", "number", DG),
    P("ops_intensive", "Ops-Intensive Business", "bool", "booleancheckbox", DG),
    P("peak_employees", "Peak Employees", "number", "number", DG),
    P("years_operating", "Years Operating", "number", "number", DG),
    P("distress_score", "Distress Score", "number", "number", DG),
    P("distress_tier", "Distress Tier", "string", "text", DG),
]
CG = "contactinformation"
CONTACT_PROPS = [
    P("linkedin_url", "LinkedIn URL (LH2)", "string", "text", CG),
    P("contact_role", "Contact Role", "string", "text", CG),
    P("spoc_type", "SPOC Type", "enumeration", "select", CG, ["Primary", "Secondary"]),
    P("next_step", "Next Step", "string", "text", CG),
    P("outreach_status", "Outreach Status", "enumeration", "select", CG,
      ["Not Contacted", "LinkedIn Sent", "Followed Up", "Replied", "Meeting Booked", "Not Interested"]),
]
OG = "companyinformation"
COMPANY_PROPS = [
    P("lh2_domain", "LH2 Domain (unique key)", "string", "text", OG),
    P("opsdata_fit", "Ops-Data Fit (0-100)", "number", "number", OG),
    P("ops_intensive", "Ops-Intensive Business", "bool", "booleancheckbox", OG),
    P("peak_employees", "Peak Employees", "number", "number", OG),
    P("years_operating", "Years Operating", "number", "number", OG),
    P("segment", "Segment", "string", "text", OG),
    P("incorp_year", "Incorp. Year", "number", "number", OG),
    P("pipeline_source", "Pipeline Source", "string", "text", OG),
]

def call(path, method="GET", body=None):
    url = "https://api.hubapi.com" + path
    data = json.dumps(body).encode() if body is not None else None
    for a in range(5):
        try:
            req = urllib.request.Request(url, data=data, method=method,
                headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=40) as r:
                t = r.read().decode(); return r.status, (json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503, 504) and a < 4: time.sleep(2 * (a + 1)); continue
            return e.code, {"raw": e.read().decode()[:300]}
        except Exception:
            if a == 4: raise
            time.sleep(2)

def main():
    print(f"{'DRY-RUN — nothing will be written' if DRY else 'CREATING in the hubspot_kartik portal'}\n")
    print(f"Pipeline: {PIPELINE_LABEL}  ({len(STAGES)} stages: "
          f"{sum(1 for _,k in STAGES if k=='open')} open, 1 won, {sum(1 for _,k in STAGES if k=='lost')} dead)")
    for i, (lab, kind) in enumerate(STAGES):
        print(f"   {i:2}. {lab:48} [{kind}]")
    print(f"\nProperties: deals={len(DEAL_PROPS)} contacts={len(CONTACT_PROPS)} companies={len(COMPANY_PROPS)}")
    if DRY:
        for p in DEAL_PROPS: print(f"   deal.{p['name']:26} {p['type']:10} {p['fieldType']}")
        return

    # --- pipeline (reuse if the label already exists) ---
    s, d = call("/crm/v3/pipelines/deals")
    existing = next((p for p in d.get("results", []) if p["label"] == PIPELINE_LABEL), None)
    body = {"label": PIPELINE_LABEL, "displayOrder": 2,
            "stages": [stage_body(l, k, i) for i, (l, k) in enumerate(STAGES)]}
    if existing:
        s, d = call(f"/crm/v3/pipelines/deals/{existing['id']}", "PUT", body)
        print(f"\npipeline UPDATED ({s}) id={existing['id']}")
        pid = existing["id"]
    else:
        s, d = call("/crm/v3/pipelines/deals", "POST", body)
        pid = d.get("id"); print(f"\npipeline CREATED ({s}) id={pid}")
        if s >= 400: print("  ", d)
    if pid:
        s, d = call(f"/crm/v3/pipelines/deals/{pid}")
        ids = {x["label"]: x["id"] for x in d.get("stages", [])}
        json.dump({"pipeline_id": pid, "stages": ids},
                  open(os.path.join(HERE, "opsdata_pipeline_ids.json"), "w"), indent=1)
        print(f"  saved stage ids -> opsdata_pipeline_ids.json ({len(ids)} stages)")

    # --- properties ---
    for obj, props in (("deals", DEAL_PROPS), ("contacts", CONTACT_PROPS), ("companies", COMPANY_PROPS)):
        s, d = call(f"/crm/v3/properties/{obj}")
        have = {p["name"] for p in d.get("results", [])}
        made = skip = err = 0
        for p in props:
            if p["name"] in have: skip += 1; continue
            s, r = call(f"/crm/v3/properties/{obj}", "POST", p)
            if s in (200, 201): made += 1
            else: err += 1; print(f"   ERR {obj}.{p['name']}: {str(r)[:140]}")
            time.sleep(0.08)
        print(f"{obj}: created={made} already-existed={skip} errors={err}")
    print("\nDONE.")

if __name__ == "__main__":
    main()
