# -*- coding: utf-8 -*-
"""EXHAUSTIVE HubSpot extraction for the 1Bn-LoC reality check.

Pulls EVERY deal (all properties + full dealstage history), every note, task, meeting,
call, contact and company, plus all object->deal associations. Emits both machine-readable
CSVs and one giant JSONL "log of everything" suitable for handing to an LLM.

Outputs (godown/ceo_reality_check/):
  DEALS_FULL.csv          one row per deal, every property
  STAGE_TRANSITIONS.csv   one row per stage change (who, when, human/system, from->to)
  NOTES_FULL.csv          every note, body + owner + deal
  TASKS_FULL.csv          every task
  ENGAGEMENTS_FULL.csv    meetings + calls
  CONTACTS_FULL.csv       every contact
  COMPANIES_FULL.csv      every company
  EVERYTHING.jsonl        one JSON object per line: {type, ...} — the full log
"""
import os, json, csv, time, datetime, urllib.request, urllib.error, collections

HERE = os.path.dirname(os.path.abspath(__file__))
HUB = os.path.dirname(os.path.dirname(HERE))
env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, ".env"), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
H = {"Authorization": "Bearer " + env["hubspot_key"], "Content-Type": "application/json"}
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))


def hs(u, m="GET", b=None, retries=5):
    for a in range(retries):
        try:
            d = json.dumps(b).encode() if b is not None else None
            r = urllib.request.Request("https://api.hubapi.com" + u, data=d, method=m, headers=H)
            with urllib.request.urlopen(r, timeout=90) as x:
                t = x.read().decode()
                return x.status, (json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503, 504) and a < retries - 1:
                time.sleep(2 * (a + 1)); continue
            raise
        except Exception:
            if a < retries - 1: time.sleep(2 * (a + 1)); continue
            raise


def ist(ts):
    if ts in (None, ""): return ""
    s = str(ts)
    try:
        dt = (datetime.datetime.fromtimestamp(int(s)/1000, IST) if s.isdigit()
              else datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(IST))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(ts)


def day(ts):
    v = ist(ts)
    return v[:10] if v else ""


def week(ts):
    d = day(ts)
    if not d: return ""
    dt = datetime.date.fromisoformat(d)
    return (dt - datetime.timedelta(days=dt.weekday())).isoformat()


def page_search(obj, props, extra=None):
    """Enumerate every object of a type via /search paging."""
    out, after = [], None
    while True:
        b = {"limit": 100 if obj != "deals" else 100, "properties": props, "filterGroups": []}
        if extra: b.update(extra)
        if after: b["after"] = after
        _, r = hs(f"/crm/v3/objects/{obj}/search", "POST", b)
        out += r.get("results", [])
        after = (r.get("paging") or {}).get("next", {}).get("after")
        if not after: break
        if len(out) % 500 == 0: print(f"    {obj}: {len(out)}", flush=True)
    return out


def assoc_map(from_obj, to_obj, ids):
    """batch association read -> {from_id: [to_id,...]}"""
    m = {}
    for i in range(0, len(ids), 100):
        try:
            _, a = hs(f"/crm/v4/associations/{from_obj}/{to_obj}/batch/read", "POST",
                      {"inputs": [{"id": x} for x in ids[i:i+100]]})
        except Exception:
            continue
        for res in a.get("results", []) or []:
            fid = str((res.get("from") or {}).get("id"))
            m[fid] = [str(t.get("toObjectId")) for t in (res.get("to") or [])]
    return m


def main():
    t0 = time.time()
    LOG = open(os.path.join(HERE, "EVERYTHING.jsonl"), "w", encoding="utf-8")
    def logline(o): LOG.write(json.dumps(o, ensure_ascii=False, default=str) + "\n")

    # ---------- reference data ----------
    _, pl = hs("/crm/v3/pipelines/deals")
    STG = {s["id"]: s["label"] for p in pl["results"] for s in p["stages"]}
    STG_ORDER = {s["id"]: s.get("displayOrder", 0) for p in pl["results"] for s in p["stages"]}
    STG_PROB = {s["id"]: (s.get("metadata") or {}).get("probability") for p in pl["results"] for s in p["stages"]}
    PIPE = {p["id"]: p["label"] for p in pl["results"]}
    _, ow = hs("/crm/v3/owners?limit=200")
    OWN = {o["id"]: f'{o.get("firstName","")} {o.get("lastName","")}'.strip() for o in ow.get("results", [])}
    U2ID = {str(o.get("userId")): o["id"] for o in ow.get("results", []) if o.get("userId")}
    logline({"type": "reference", "pipelines": PIPE, "stages": STG, "owners": OWN})
    print(f"ref: {len(STG)} stages, {len(OWN)} owners", flush=True)

    # ---------- deal property list ----------
    _, pr = hs("/crm/v3/properties/deals")
    ALLP = [x["name"] for x in pr["results"]]
    skip = {"hs_time_in_", "hs_v2_cumulative", "hs_v2_date_entered_", "hs_v2_date_exited_",
            "hs_v2_latest_time_", "hs_date_entered_", "hs_date_exited_", "hs_time_in"}
    DP = [n for n in ALLP if not any(n.startswith(s) for s in skip)]
    # always keep these
    for must in ["hs_v2_date_entered_current_stage", "hs_lastmodifieddate", "hs_object_id"]:
        if must not in DP: DP.append(must)
    print(f"deal properties requested: {len(DP)}", flush=True)

    # ---------- DEALS (ids first, then batch/read WITH history) ----------
    print("pulling deal ids...", flush=True)
    ids = [d["id"] for d in page_search("deals", ["dealname"])]
    print(f"  {len(ids)} deals", flush=True)

    deals, CH = [], 50
    for i in range(0, len(ids), CH):
        _, r = hs("/crm/v3/objects/deals/batch/read", "POST",
                  {"inputs": [{"id": x} for x in ids[i:i+CH]],
                   "properties": DP,
                   "propertiesWithHistory": ["dealstage", "hubspot_owner_id", "loc", "pr_count"]})
        deals += r.get("results", [])
        if (i//CH) % 10 == 0: print(f"  deals {len(deals)}/{len(ids)}", flush=True)
    print(f"  deals fetched: {len(deals)}", flush=True)

    # deal -> company / contacts
    d_comp = assoc_map("deals", "companies", ids)
    d_cont = assoc_map("deals", "contacts", ids)

    # ---------- write DEALS_FULL + STAGE_TRANSITIONS ----------
    dcols = ["deal_id", "dealname", "pipeline", "pipeline_label", "dealstage", "stage_label",
             "stage_order", "stage_probability", "is_closed_won", "is_dead", "owner_id", "owner_name",
             "lead_source", "loc", "pr_count", "loc_per_pr", "tier1_ratio_ok", "num_repos", "num_projects",
             "amount", "createdate_ist", "create_day", "create_week", "closedate_ist", "close_day", "close_week",
             "days_to_close_calc", "n_stage_moves", "n_human_moves", "max_stage_order_reached",
             "max_stage_label_reached", "first_human_move_day", "last_move_day",
             "n_notes", "n_tasks", "n_contacts", "n_companies"] + \
            [p for p in DP if p not in ("dealname", "pipeline", "dealstage", "hubspot_owner_id",
                                        "lead_source", "loc", "pr_count", "amount", "createdate", "closedate",
                                        "num_repos", "num_projects")]
    trows, drows = [], []
    dealmeta = {}
    for dl in deals:
        p = dl.get("properties", {}) or {}
        did = dl["id"]
        hist = sorted((dl.get("propertiesWithHistory", {}) or {}).get("dealstage", []) or [],
                      key=lambda e: e.get("timestamp", ""))
        ohist = sorted((dl.get("propertiesWithHistory", {}) or {}).get("hubspot_owner_id", []) or [],
                       key=lambda e: e.get("timestamp", ""))
        # stage transitions
        nhuman, maxord, maxlab, first_h, lastday = 0, -1, "", "", ""
        for j, e in enumerate(hist):
            frm = STG.get(hist[j-1]["value"]) if j > 0 else ""
            lab = STG.get(e.get("value"), e.get("value"))
            uid = str(e.get("updatedByUserId") or "")
            oid = U2ID.get(uid, "")
            human = e.get("sourceType") == "CRM_UI"
            if human:
                nhuman += 1
                if not first_h: first_h = day(e.get("timestamp"))
            o = STG_ORDER.get(e.get("value"), -1)
            if o > maxord: maxord, maxlab = o, lab
            lastday = day(e.get("timestamp"))
            tr = {"deal_id": did, "dealname": p.get("dealname"), "seq": j,
                  "from_stage": frm, "to_stage": lab,
                  "ts_ist": ist(e.get("timestamp")), "day": day(e.get("timestamp")),
                  "week": week(e.get("timestamp")),
                  "source_type": e.get("sourceType"), "is_human": human,
                  "updated_by_user_id": uid, "owner_id_of_mover": oid,
                  "mover_name": OWN.get(oid, ""), "stage_order": STG_ORDER.get(e.get("value"), ""),
                  "stage_probability": STG_PROB.get(e.get("value"), ""),
                  "pipeline": PIPE.get(p.get("pipeline"), p.get("pipeline")),
                  "lead_source": p.get("lead_source"), "loc": p.get("loc"), "pr_count": p.get("pr_count")}
            trows.append(tr); logline({"type": "stage_transition", **tr})
        def num(v):
            try: return float(v)
            except (TypeError, ValueError): return None
        loc, prc = num(p.get("loc")), num(p.get("pr_count"))
        ratio = (loc/prc) if (loc and prc) else None
        stage_lab = STG.get(p.get("dealstage"), p.get("dealstage"))
        cd, cl = p.get("createdate"), p.get("closedate")
        dtc = ""
        try:
            if cd and cl:
                dtc = (datetime.date.fromisoformat(day(cl)) - datetime.date.fromisoformat(day(cd))).days
        except Exception: pass
        row = {"deal_id": did, "dealname": p.get("dealname"),
               "pipeline": p.get("pipeline"), "pipeline_label": PIPE.get(p.get("pipeline"), ""),
               "dealstage": p.get("dealstage"), "stage_label": stage_lab,
               "stage_order": STG_ORDER.get(p.get("dealstage"), ""),
               "stage_probability": STG_PROB.get(p.get("dealstage"), ""),
               "is_closed_won": stage_lab == "Closed/Won",
               "is_dead": str(stage_lab).startswith("Dead/"),
               "owner_id": p.get("hubspot_owner_id"), "owner_name": OWN.get(p.get("hubspot_owner_id"), ""),
               "lead_source": p.get("lead_source"), "loc": p.get("loc"), "pr_count": p.get("pr_count"),
               "loc_per_pr": round(ratio, 1) if ratio else "",
               "tier1_ratio_ok": (300 <= ratio <= 2000) if ratio else "",
               "num_repos": p.get("num_repos"), "num_projects": p.get("num_projects"),
               "amount": p.get("amount"),
               "createdate_ist": ist(cd), "create_day": day(cd), "create_week": week(cd),
               "closedate_ist": ist(cl), "close_day": day(cl), "close_week": week(cl),
               "days_to_close_calc": dtc,
               "n_stage_moves": len(hist), "n_human_moves": nhuman,
               "max_stage_order_reached": maxord, "max_stage_label_reached": maxlab,
               "first_human_move_day": first_h, "last_move_day": lastday,
               "n_contacts": len(d_cont.get(did, [])), "n_companies": len(d_comp.get(did, [])),
               "n_notes": 0, "n_tasks": 0}
        for k in dcols:
            if k not in row: row[k] = p.get(k, "")
        drows.append(row)
        dealmeta[did] = row
        logline({"type": "deal", **row, "owner_history": [{"ts": ist(e.get("timestamp")), "owner": OWN.get(e.get("value"), e.get("value")), "src": e.get("sourceType")} for e in ohist]})
    print(f"  transitions: {len(trows)}", flush=True)

    # ---------- NOTES ----------
    print("pulling notes...", flush=True)
    notes = page_search("notes", ["hs_note_body", "hs_timestamp", "hs_createdate",
                                  "hubspot_owner_id", "hs_object_id", "hs_lastmodifieddate"])
    print(f"  {len(notes)} notes", flush=True)
    n2d = assoc_map("notes", "deals", [n["id"] for n in notes])
    import re
    nrows = []
    for n in notes:
        p = n["properties"]
        body = re.sub("<[^>]+>", " ", p.get("hs_note_body") or "")
        body = re.sub(r"&nbsp;?", " ", body); body = re.sub(r"\s+", " ", body).strip()
        for did in (n2d.get(n["id"]) or [""]):
            r = {"note_id": n["id"], "deal_id": did,
                 "dealname": dealmeta.get(did, {}).get("dealname", ""),
                 "lead_source": dealmeta.get(did, {}).get("lead_source", ""),
                 "stage_label": dealmeta.get(did, {}).get("stage_label", ""),
                 "owner_id": p.get("hubspot_owner_id"), "owner_name": OWN.get(p.get("hubspot_owner_id"), ""),
                 "ts_ist": ist(p.get("hs_timestamp")), "day": day(p.get("hs_timestamp")),
                 "week": week(p.get("hs_timestamp")), "body": body}
            nrows.append(r); logline({"type": "note", **r})
            if did in dealmeta: dealmeta[did]["n_notes"] += 1

    # ---------- TASKS ----------
    print("pulling tasks...", flush=True)
    tasks = page_search("tasks", ["hs_task_subject", "hs_task_body", "hs_task_status", "hs_task_type",
                                  "hs_task_priority", "hs_timestamp", "hs_createdate", "hubspot_owner_id",
                                  "hs_task_completion_date"])
    print(f"  {len(tasks)} tasks", flush=True)
    t2d = assoc_map("tasks", "deals", [t["id"] for t in tasks])
    tkrows = []
    for t in tasks:
        p = t["properties"]
        body = re.sub("<[^>]+>", " ", p.get("hs_task_body") or "")
        body = re.sub(r"&nbsp;?", " ", body); body = re.sub(r"\s+", " ", body).strip()
        for did in (t2d.get(t["id"]) or [""]):
            r = {"task_id": t["id"], "deal_id": did,
                 "dealname": dealmeta.get(did, {}).get("dealname", ""),
                 "owner_id": p.get("hubspot_owner_id"), "owner_name": OWN.get(p.get("hubspot_owner_id"), ""),
                 "subject": p.get("hs_task_subject"), "body": body,
                 "status": p.get("hs_task_status"), "task_type": p.get("hs_task_type"),
                 "priority": p.get("hs_task_priority"),
                 "due_ist": ist(p.get("hs_timestamp")), "created_ist": ist(p.get("hs_createdate")),
                 "created_day": day(p.get("hs_createdate")), "created_week": week(p.get("hs_createdate")),
                 "completed_ist": ist(p.get("hs_task_completion_date"))}
            tkrows.append(r); logline({"type": "task", **r})
            if did in dealmeta: dealmeta[did]["n_tasks"] += 1

    # ---------- MEETINGS + CALLS ----------
    print("pulling meetings/calls...", flush=True)
    erows = []
    for obj, props in (("meetings", ["hs_meeting_title", "hs_meeting_body", "hs_meeting_start_time",
                                     "hs_meeting_end_time", "hs_meeting_outcome", "hs_timestamp",
                                     "hubspot_owner_id", "hs_createdate"]),
                       ("calls", ["hs_call_title", "hs_call_body", "hs_call_duration", "hs_call_direction",
                                  "hs_call_disposition", "hs_timestamp", "hubspot_owner_id", "hs_createdate"])):
        try:
            objs = page_search(obj, props)
        except Exception as e:
            print(f"  {obj} skipped: {e}"); continue
        m = assoc_map(obj, "deals", [o["id"] for o in objs])
        for o in objs:
            p = o["properties"]
            for did in (m.get(o["id"]) or [""]):
                r = {"engagement_id": o["id"], "engagement_type": obj, "deal_id": did,
                     "dealname": dealmeta.get(did, {}).get("dealname", ""),
                     "owner_name": OWN.get(p.get("hubspot_owner_id"), ""),
                     "title": p.get("hs_meeting_title") or p.get("hs_call_title") or "",
                     "outcome": p.get("hs_meeting_outcome") or p.get("hs_call_disposition") or "",
                     "start_ist": ist(p.get("hs_meeting_start_time") or p.get("hs_timestamp")),
                     "day": day(p.get("hs_meeting_start_time") or p.get("hs_timestamp")),
                     "week": week(p.get("hs_meeting_start_time") or p.get("hs_timestamp")),
                     "duration": p.get("hs_call_duration", ""),
                     "body": re.sub(r"\s+", " ", re.sub("<[^>]+>", " ", (p.get("hs_meeting_body") or p.get("hs_call_body") or "")))[:2000].strip()}
                erows.append(r); logline({"type": "engagement", **r})
        print(f"  {obj}: {len(objs)}", flush=True)

    # ---------- CONTACTS + COMPANIES ----------
    print("pulling contacts...", flush=True)
    contacts = page_search("contacts", ["firstname", "lastname", "email", "phone", "mobilephone",
                                        "jobtitle", "company", "linkedin_url", "hs_object_id",
                                        "createdate", "lifecyclestage", "hs_lead_status"])
    crows = []
    for c in contacts:
        p = c["properties"]
        r = {"contact_id": c["id"], "firstname": p.get("firstname"), "lastname": p.get("lastname"),
             "email": p.get("email"), "phone": p.get("phone"), "mobilephone": p.get("mobilephone"),
             "jobtitle": p.get("jobtitle"), "company": p.get("company"),
             "linkedin_url": p.get("linkedin_url"), "created_ist": ist(p.get("createdate")),
             "create_week": week(p.get("createdate")), "lifecyclestage": p.get("lifecyclestage")}
        crows.append(r); logline({"type": "contact", **r})
    print(f"  {len(crows)} contacts", flush=True)

    print("pulling companies...", flush=True)
    comps = page_search("companies", ["name", "domain", "industry", "city", "state", "country",
                                      "numberofemployees", "annualrevenue", "website", "createdate",
                                      "linkedin_company_page", "description"])
    cmrows = []
    for c in comps:
        p = c["properties"]
        r = {"company_id": c["id"], "name": p.get("name"), "domain": p.get("domain"),
             "industry": p.get("industry"), "city": p.get("city"), "country": p.get("country"),
             "employees": p.get("numberofemployees"), "revenue": p.get("annualrevenue"),
             "website": p.get("website"), "created_ist": ist(p.get("createdate")),
             "create_week": week(p.get("createdate"))}
        cmrows.append(r); logline({"type": "company", **r})
    print(f"  {len(cmrows)} companies", flush=True)

    # ---------- WRITE CSVs ----------
    def w(name, rows, cols=None):
        path = os.path.join(HERE, name)
        if not rows:
            open(path, "w").write(""); print(f"  {name}: EMPTY"); return
        cols = cols or list(rows[0].keys())
        with open(path, "w", newline="", encoding="utf-8") as f:
            wr = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            wr.writeheader()
            for r in rows: wr.writerow(r)
        print(f"  {name}: {len(rows)} rows", flush=True)

    print("writing CSVs...", flush=True)
    w("DEALS_FULL.csv", drows, dcols)
    w("STAGE_TRANSITIONS.csv", trows)
    w("NOTES_FULL.csv", nrows)
    w("TASKS_FULL.csv", tkrows)
    w("ENGAGEMENTS_FULL.csv", erows)
    w("CONTACTS_FULL.csv", crows)
    w("COMPANIES_FULL.csv", cmrows)
    LOG.close()

    summary = {"deals": len(drows), "transitions": len(trows), "notes": len(nrows),
               "tasks": len(tkrows), "engagements": len(erows), "contacts": len(crows),
               "companies": len(cmrows), "seconds": round(time.time()-t0, 1)}
    json.dump(summary, open(os.path.join(HERE, "EXTRACT_SUMMARY.json"), "w"), indent=2)
    print("\nDONE:", json.dumps(summary), flush=True)


main()
