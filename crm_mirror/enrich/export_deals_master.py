# -*- coding: utf-8 -*-
"""One CSV row per deal, carrying everything HubSpot knows about it — for pattern analysis.

Built for the question "what is actually working?", so beyond the raw properties every row gets
the deal's whole JOURNEY: the ordered stage path with dates, how deep it travelled, who moved
it, who wrote notes on it, and how long each leg took.

DESIGN DECISIONS, so the numbers are read correctly:

* max_depth_ever vs max_depth_human. ~42% of stage-history entries are sourceType=INTEGRATION —
  bulk API writes, including our own migrations (the 5 Aug Call Attempted -> No Pickup move, the
  Tracxn pull-back). "ever" is the deal's true furthest point regardless of who moved it;
  "human" counts only stages ENTERED by a CRM_UI click. A deal where the two disagree was
  script-touched — the `migrated` flag says so explicitly.

* Depth is by STAGE LABEL, not stage id, because the two pipelines carry identical labels with
  different ids. Dead/* labels map to the depth they imply: dying at Dead/GMeet/NoShow means a
  VC slot was spent (depth 4), while Dead/GMeet/Cancelled was called off in advance (depth 3).
  Dead/ColdCall/WrongFit is depth 0 — screened out, never dialled. Same semantics as the
  dashboard's METRICS sets.

* "Call Attempted" was retired 2026-08-05 but survives in ~100 deals' history; it counts as
  depth 1 (attempted), same as No Pickup.

* Notes are classified with dashboard/note_rules.py — imported, never copied (a hand-copy of
  KPI definitions once drifted 2.7x). Full note text rides along, capped per cell, because for
  pattern work the words matter ("no bandwidth" vs "wrong number" are different funnels).

* Every deal property that is non-empty on at least one deal gets a column. Empty-everywhere
  properties are dropped — they are schema, not data.

FOUR OUTPUTS at the hubspot root — a wide table for eyeballing plus long-format event logs
for quantitative work (survival analysis, transition matrices, per-person cadence):

  DEALS_MASTER.csv       one row per deal (wide)
  DEALS_TRANSITIONS.csv  one row per stage ENTRY: from/to stage + depth, exact dwell time in
                         the previous stage (float days), who moved it, owner at that moment,
                         weekday/hour, and the deal's final outcome denormalised onto every row
  DEALS_NOTES.csv        one row per note: author, bucket, stage the deal was in when written
  DEALS_ENGAGEMENTS.csv  one row per task/email/meeting logged on a deal

The transitions log is an event log, so the CURRENT stage's still-running dwell is censored —
it has no closing transition yet. That censored observation is in the master as
days_in_current_stage; join on deal_id.

Usage: python3 export_deals_master.py
"""
import os, re, sys, csv, json, time, datetime, collections, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HUB, "lh2-pipeline", "dashboard"))
from note_rules import classify, plain

env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
H = {"Authorization": "Bearer " + env["hubspot_key"], "Content-Type": "application/json"}
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
OUT = os.path.join(HUB, "DEALS_MASTER.csv")
TODAY = datetime.datetime.now(IST).date()


def hs(u, m="GET", b=None):
    d = json.dumps(b).encode() if b is not None else None
    for a in range(6):
        try:
            r = urllib.request.Request("https://api.hubapi.com" + u, data=d, method=m, headers=H)
            with urllib.request.urlopen(r, timeout=90) as x:
                t = x.read().decode(); return x.status, (json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and a < 5: time.sleep(2*(a+1)); continue
            return e.code, {"raw": e.read().decode()[:300]}
        except Exception:                       # URLError/SSLError killed six builds on 6 Aug
            if a == 5: raise
            time.sleep(3*(a+1))


def ist_dt(ms_or_iso):
    try:
        if str(ms_or_iso).isdigit():
            return datetime.datetime.fromtimestamp(int(ms_or_iso)/1000, IST)
        return datetime.datetime.fromisoformat(str(ms_or_iso).replace("Z", "+00:00")).astimezone(IST)
    except Exception:
        return None


def d(x):   return x.date().isoformat() if x else ""


def ts(x):  return x.strftime("%Y-%m-%d %H:%M:%S") if x else ""


def fdays(a, b):
    """b - a in float days, 3dp — dwell times below a day matter (same-day dial sequences)."""
    return round((b - a).total_seconds() / 86400, 3) if a and b else ""


# ---------------------------------------------------------------- depth ladder
# Rank of the furthest rung a stage label implies. Lowercased keys: GMeet dead labels are
# inconsistently cased in the portal ("wrong fit" vs "WrongFit").
#
# Ranks 10-12 are the post-contract operational stages that sit BETWEEN Deal Contract Signed
# and Closed/Won in the portal (displayOrder 8-10) — a deal there is further along than a
# signed contract but not yet won.
LADDER = ["Cold Call", "Attempted", "Connected", "GMeet Fixed", "VC Done", "Script Shared",
          "Results Received", "Evaluated", "Negotiation", "Contract Signed",
          "Data Migration", "Metadata Matched", "Payment Initiation", "Closed/Won"]
DEPTH = {
    "cold call": 0, "dead/coldcall/wrongfit": 0,
    "call attempted": 1, "call attempted (retired)": 1, "no pickup": 1,
    "dead/coldcall/wrongnumber": 1, "dead/coldcall/nopickup": 1,
    "interested": 2, "dead/coldcall/not interested": 2,
    "gmeet fixed": 3, "dead/gmeet/cancelled": 3,
    # Dead/Interested/NoShow ranks WITH Dead/GMeet/NoShow, not below it: the funnel SOP's own
    # open-decisions list says the two "mean the same thing" — a booked meet that no-showed.
    "dead/gmeet/noshow": 4, "dead/gmeet/wrong fit": 4, "dead/gmeet/wrongfit": 4,
    "dead/gmeet/privacy concerns": 4, "dead/interested/noshow": 4,
    "script shared": 5, "dead/scriptshared/noshow": 5,
    "script results received": 6,
    "dead/resultsreceived/wrongfit-rejected": 7,
    "commercial negotiation": 8, "dead/negotiation/pricing": 8, "dead/negotiation/contractual": 8,
    "deal contract signed": 9,
    "data migration done": 10, "metadata matched": 11, "payment initiation": 12,
    "closed/won": 13,
    # --- legacy stages, deleted in the July revamp. Labels recovered from the pipeline AUDIT
    # endpoint (/crm/v3/pipelines/deals/default/audit) — the current pipelines API no longer
    # knows these ids, but ~250 history entries on July deals still carry them. Depths are
    # judgment calls mapped onto the new semantics; the raw label rides in stage_path so the
    # mapping is checkable:
    #   Assigned            = allocated to a caller, not yet dialled       -> 0
    #   M1V1 Sent           = first outreach message sent                  -> 1 (attempted)
    #   Dead - No Response  = outreach made, silence                       -> 1
    #   Dead - Rejected     = contact made, they said no (Not Interested)  -> 2
    #   Dead - Meeting Rejected = connected, declined to meet              -> 2
    #   Awaiting Meeting    = meeting agreed                               -> 3 (gmeet fixed)
    #   GMEET1 Completed    = meeting held                                 -> 4 (vc done)
    #   Awaiting Results    = script out, waiting                          -> 5
    #   Results Under Review= results in hand                              -> 6
    #   Dead - Wrong Fit    = screened out                                 -> 0
    "assigned": 0, "m1v1 sent": 1, "dead - no response": 1, "dead - rejected": 2,
    "dead - meeting rejected": 2, "awaiting meeting": 3, "gmeet1 completed": 4,
    "awaiting results": 5, "results under review": 6, "dead - wrong fit": 0,
}
# Deleted default-pipeline stage ids -> recovered labels, so paths read as words not numbers.
RETIRED = {"3992480463": "Assigned", "3992480466": "M1V1 Sent", "3992480468": "Awaiting Meeting",
           "3992480470": "GMEET1 Completed", "3992480472": "Awaiting Results",
           "3992480474": "Results Under Review", "3992480476": "Dead - Rejected",
           "3992480477": "Dead - No Response", "3992480478": "Dead - Meeting Rejected",
           "3992480479": "Dead - Wrong Fit"}
UNMAPPED = collections.Counter()


def depth_of(label):
    k = (label or "").strip().lower()
    if k in DEPTH: return DEPTH[k]
    UNMAPPED[label] += 1
    return None


def is_dead(label):
    k = (label or "").lower()
    return k.startswith("dead/") or k.startswith("dead -") or k == "closed/lost"


def main():
    # ---- reference maps -------------------------------------------------------
    _, pp = hs("/crm/v3/pipelines/deals")
    PIPE = {p["id"]: p["label"] for p in pp["results"]}
    STG  = {s["id"]: s["label"] for p in pp["results"] for s in p["stages"]}
    OWN, UID = {}, {}
    for arch in ("false", "true"):
        _, ow = hs(f"/crm/v3/owners?limit=200&archived={arch}")
        for o in ow.get("results", []):
            OWN[o["id"]] = f'{o.get("firstName","")} {o.get("lastName","")}'.strip() or o.get("email", o["id"])
            if o.get("userId"): UID[str(o["userId"])] = OWN[o["id"]]
    _, pr = hs("/crm/v3/properties/deals")
    ALLPROPS = [p["name"] for p in pr["results"]]
    print(f"pipelines {list(PIPE.values())} | owners {len(OWN)} | deal properties {len(ALLPROPS)}", flush=True)

    # ---- enumerate every deal (list endpoint: no 10k search cap) --------------
    ids, after = [], None
    while True:
        u = "/crm/v3/objects/deals?limit=100&properties=dealname" + (f"&after={after}" if after else "")
        _, r = hs(u)
        ids += [x["id"] for x in r.get("results", [])]
        after = (r.get("paging") or {}).get("next", {}).get("after")
        if not after: break
    print(f"deals: {len(ids)}", flush=True)

    # ---- full properties + stage/owner history (batch caps at 50 WITH history) -
    deals = {}
    for i in range(0, len(ids), 50):
        s, r = hs("/crm/v3/objects/deals/batch/read", "POST",
                  {"inputs": [{"id": x} for x in ids[i:i+50]], "properties": ALLPROPS,
                   "propertiesWithHistory": ["dealstage", "hubspot_owner_id"]})
        if s != 200: sys.exit(f"batch read {s}: {str(r)[:200]}")
        for x in r["results"]: deals[x["id"]] = x
        if (i//50) % 8 == 0: print(f"   history {min(i+50,len(ids))}/{len(ids)}", flush=True)

    # ---- associated contacts --------------------------------------------------
    d2c, cids = {}, set()
    for i in range(0, len(ids), 100):
        _, r = hs("/crm/v4/associations/deals/contacts/batch/read", "POST",
                  {"inputs": [{"id": x} for x in ids[i:i+100]]})
        for row in r.get("results", []):
            cs = [str(t["toObjectId"]) for t in row.get("to", [])]      # toObjectId is an INT
            d2c[str(row["from"]["id"])] = cs; cids |= set(cs)
    CPROPS = ["firstname", "lastname", "email", "phone", "mobilephone", "jobtitle", "company",
              "city", "country", "linkedin_url", "lifecyclestage", "createdate"]
    contacts = {}
    cl = sorted(cids)
    for i in range(0, len(cl), 100):
        _, r = hs("/crm/v3/objects/contacts/batch/read", "POST",
                  {"inputs": [{"id": x} for x in cl[i:i+100]], "properties": CPROPS})
        for x in r.get("results", []): contacts[x["id"]] = x["properties"]
    print(f"contacts: {len(contacts)} on {sum(1 for v in d2c.values() if v)} deals", flush=True)

    # ---- notes ----------------------------------------------------------------
    d2n, nids = {}, set()
    for i in range(0, len(ids), 100):
        _, r = hs("/crm/v4/associations/deals/notes/batch/read", "POST",
                  {"inputs": [{"id": x} for x in ids[i:i+100]]})
        for row in r.get("results", []):
            ns = [str(t["toObjectId"]) for t in row.get("to", [])]
            d2n[str(row["from"]["id"])] = ns; nids |= set(ns)
    notes = {}
    nl = sorted(nids)
    for i in range(0, len(nl), 100):
        _, r = hs("/crm/v3/objects/notes/batch/read", "POST",
                  {"inputs": [{"id": x} for x in nl[i:i+100]],
                   "properties": ["hs_note_body", "hs_timestamp", "hubspot_owner_id", "hs_created_by_user_id"]})
        for x in r.get("results", []): notes[x["id"]] = x["properties"]
    print(f"notes: {len(notes)} on {sum(1 for v in d2n.values() if v)} deals", flush=True)

    # Deactivated users vanish from the owners API's userId linkage: Shreyas and Yash left,
    # and 698 human stage-moves (their entire July on the CRM) came back with a blank mover.
    # Their notes still carry BOTH hs_created_by_user_id and the note's hubspot_owner_id, so
    # the pairing is re-learned from evidence — majority vote across all their notes, not
    # first-seen, in case a note was ever logged on someone else's behalf.
    votes = collections.defaultdict(collections.Counter)
    for n in notes.values():
        uid, oid = str(n.get("hs_created_by_user_id") or ""), n.get("hubspot_owner_id")
        if uid and uid != "None" and oid in OWN: votes[uid][OWN[oid]] += 1
    learned = {u: c.most_common(1)[0][0] for u, c in votes.items() if u not in UID}
    UID.update(learned)
    if learned:
        print(f"   userId map: +{len(learned)} learned from note authorship "
              f"({', '.join(sorted(set(learned.values())))})", flush=True)

    # ---- other engagement types: probe before sweeping ------------------------
    # Nothing here has ever logged calls in HubSpot (calls happen on personal phones, mail
    # goes via Gmail) — but tasks WERE created by script once. Probe 200 deals per type and
    # only sweep types that actually occur, so we don't burn 80 calls proving zeros.
    ENG_PROPS = {
        "tasks":    ["hs_task_subject", "hs_task_body", "hs_task_status", "hs_timestamp",
                     "hubspot_owner_id"],
        "emails":   ["hs_email_subject", "hs_email_direction", "hs_timestamp", "hubspot_owner_id"],
        "meetings": ["hs_meeting_title", "hs_meeting_outcome", "hs_meeting_start_time",
                     "hs_timestamp", "hubspot_owner_id"],
        "calls":    ["hs_call_title", "hs_call_duration", "hs_timestamp", "hubspot_owner_id"],
        "communications": ["hs_communication_channel_type", "hs_timestamp", "hubspot_owner_id"],
    }
    d2e, eobjs = {}, {}                       # d2e[typ][deal_id] = [ids]; eobjs[typ][id] = props
    for typ in ENG_PROPS:
        _, r = hs(f"/crm/v4/associations/deals/{typ}/batch/read", "POST",
                  {"inputs": [{"id": x} for x in ids[:200]]})
        hits = sum(len(row.get("to", [])) for row in r.get("results", []))
        print(f"   probe {typ}: {hits} on first 200 deals", flush=True)
        if not hits: continue
        d2e[typ], eids = {}, set()
        for i in range(0, len(ids), 100):
            _, r = hs(f"/crm/v4/associations/deals/{typ}/batch/read", "POST",
                      {"inputs": [{"id": x} for x in ids[i:i+100]]})
            for row in r.get("results", []):
                es = [str(t["toObjectId"]) for t in row.get("to", [])]
                if es: d2e[typ][str(row["from"]["id"])] = es; eids |= set(es)
        eobjs[typ], el = {}, sorted(eids)
        for i in range(0, len(el), 100):
            _, r = hs(f"/crm/v3/objects/{typ}/batch/read", "POST",
                      {"inputs": [{"id": x} for x in el[i:i+100]], "properties": ENG_PROPS[typ]})
            for x in r.get("results", []): eobjs[typ][x["id"]] = x["properties"]
        print(f"   {typ}: {len(eobjs[typ])} objects", flush=True)

    # ---- assemble -------------------------------------------------------------
    NB = ["System note", "Script received", "Bad number", "Vetted - out", "Vetted - in",
          "Not interested", "Disqualified", "No pickup", "Callback booked", "Meeting fixed",
          "Script shared", "Chase sent", "Interested", "Other"]
    SKIP_DYN = {"dealname", "pipeline", "dealstage", "hubspot_owner_id", "createdate",
                "closedate", "hs_lastmodifieddate", "hs_object_id",
                "hs_v2_date_entered_current_stage", "description",
                "lead_source", "source_tab", "lh2_domain"}
    rows, dyn_fill = [], collections.Counter()
    trans_rows, note_rows, eng_rows = [], [], []

    for did in ids:
        x = deals.get(did)
        if not x: continue
        p = {k: v for k, v in (x.get("properties") or {}).items() if v not in (None, "")}

        # -- stage history, oldest first. Entry 0 is the create; the rest are moves.
        hist = sorted((x.get("propertiesWithHistory", {}).get("dealstage") or []),
                      key=lambda e: e.get("timestamp", ""))
        legs = []                                   # (dt, label, human, actor)
        for j, e in enumerate(hist):
            lab = STG.get(e.get("value")) or RETIRED.get(e.get("value")) or e.get("value")
            human = e.get("sourceType") == "CRM_UI"
            actor = UID.get(str(e.get("updatedByUserId") or ""), "")
            legs.append((ist_dt(e.get("timestamp")), lab, human and j > 0, actor,
                         e.get("sourceType") or ""))

        created = ist_dt(p.get("createdate"))
        cur_lab = STG.get(p.get("dealstage")) or RETIRED.get(p.get("dealstage")) or p.get("dealstage", "")
        cur_ent = ist_dt(p.get("hs_v2_date_entered_current_stage"))

        depths = [(depth_of(l), dt, l, hu) for dt, l, hu, _, _ in legs]  # (depth, dt, label, human)
        known = [t for t in depths if t[0] is not None]
        ever = max((t[0] for t in known), default=depth_of(cur_lab) or 0)
        human_known = [t for t in known if t[3]]
        hum = max((t[0] for t in human_known), default=0)
        first_at_max = next((t[1] for t in known if t[0] == ever), None)

        moves = legs[1:]
        hmoves = [m for m in moves if m[2]]
        imoves = [m for m in moves if not m[2]]
        movers = [m[3] for m in hmoves if m[3]]
        first_caller = movers[0] if movers else ""

        # -- owner history -> path of names, consecutive dupes collapsed; olist keeps the
        #    timestamps so any event below can be attributed to the owner OF THAT MOMENT
        #    (the Tracxn pull-back and the Romania handover both changed owners mid-life).
        ohist = sorted((x.get("propertiesWithHistory", {}).get("hubspot_owner_id") or []),
                       key=lambda e: e.get("timestamp", ""))
        opath, olist = [], []
        for e in ohist:
            nm = OWN.get(e.get("value"), e.get("value") or "")
            if nm:
                olist.append((ist_dt(e.get("timestamp")), nm))
                if not opath or opath[-1] != nm: opath.append(nm)

        def owner_at(t):
            best = ""
            for odt, nm in olist:
                if odt and t and odt <= t: best = nm
            return best or (olist[0][1] if olist else "")

        def stage_at(t):
            best = ""
            for ldt, lab, *_ in legs:
                if ldt and t and ldt <= t: best = lab
            return best

        # -- notes
        created0 = legs[0][0] if legs and legs[0][0] else created
        nb = collections.Counter(); ntexts, nauth, ndates = [], [], []
        for nid in d2n.get(did, []):
            n = notes.get(nid)
            if not n: continue
            body = plain(n.get("hs_note_body") or "")
            if not body: continue
            b = classify(body.lower())
            nb[b] += 1
            ndt = ist_dt(n.get("hs_timestamp"))
            who = OWN.get(n.get("hubspot_owner_id"), UID.get(str(n.get("hs_created_by_user_id") or ""), ""))
            if who: nauth.append(who)
            if ndt: ndates.append(ndt)
            ntexts.append((ndt, f'[{ndt.strftime("%m-%d") if ndt else "?"} {who or "?"}] {body}'))
            note_rows.append({
                "deal_id": did, "dealname": p.get("dealname", ""), "ts": ts(ndt),
                "date": d(ndt), "dow": ndt.strftime("%a") if ndt else "", "hour": ndt.hour if ndt else "",
                "author": who, "bucket": b,
                "stage_at_note": stage_at(ndt), "owner_at_note": owner_at(ndt),
                "days_since_create": fdays(created0, ndt),
                "chars": len(body), "text": body[:800],
                "lead_source": p.get("lead_source", ""), "pipeline": PIPE.get(p.get("pipeline"), ""),
            })
        ntexts.sort(key=lambda t: t[0] or datetime.datetime.min.replace(tzinfo=IST))
        notes_text = " || ".join(t[1] for t in ntexts)[:1800]

        acts = collections.Counter(movers) + collections.Counter(nauth)
        last_move = max((m[0] for m in moves if m[0]), default=None)
        last_touch = max([t for t in [last_move, max(ndates, default=None)] if t], default=None)

        c1 = (contacts.get(d2c.get(did, [""])[0]) if d2c.get(did) else None) or {}
        row = {
            "deal_id": did, "dealname": p.get("dealname", ""),
            "pipeline": PIPE.get(p.get("pipeline"), p.get("pipeline", "")),
            "created": d(created), "age_days": (TODAY - created.date()).days if created else "",
            "current_stage": cur_lab, "current_stage_entered": d(cur_ent),
            "days_in_current_stage": (TODAY - cur_ent.date()).days if cur_ent else "",
            "is_dead": int(is_dead(cur_lab)), "dead_reason": cur_lab if is_dead(cur_lab) else "",
            "won": int(cur_lab.lower() == "closed/won"), "closedate": d(ist_dt(p.get("closedate"))),
            "max_depth_rank": ever, "max_depth": LADDER[ever] if 0 <= ever < len(LADDER) else "",
            "max_depth_rank_human": hum, "max_depth_human": LADDER[hum] if 0 <= hum < len(LADDER) else "",
            "migrated": int(bool(imoves)),
            "stage_path": " > ".join(l for _, l, _, _, _ in legs),
            "stage_path_dated": " > ".join(f'{d(dt)} {l}{"" if hu else " [script]" if i else ""}'
                                           for i, (dt, l, hu, _, _) in enumerate(legs)),
            "n_stage_moves": len(moves), "n_human_moves": len(hmoves),
            "n_integration_moves": len(imoves),
            "first_human_move": d(min((m[0] for m in hmoves if m[0]), default=None)),
            "last_human_move": d(max((m[0] for m in hmoves if m[0]), default=None)),
            "last_any_move": d(last_move),
            "days_to_first_touch": (min((m[0] for m in hmoves if m[0]), default=None) - created).days
                                   if created and hmoves and hmoves[0][0] else "",
            "days_to_max_depth": (first_at_max - created).days if created and first_at_max else "",
            "stalled_days": (TODAY - last_touch.date()).days if last_touch else "",
            "owner": OWN.get(p.get("hubspot_owner_id"), ""), "owner_path": " > ".join(opath),
            "owner_changes": max(0, len(opath) - 1),
            "first_caller": first_caller,
            "movers": ", ".join(sorted(set(movers))),
            "primary_actor": (acts.most_common(1)[0][0] if acts else ""),
            "lead_source": p.get("lead_source", ""), "source_tab": p.get("source_tab", ""),
            "lh2_domain": p.get("lh2_domain", ""), "deal_description": p.get("description", ""),
            "contact_name": f'{c1.get("firstname","")} {c1.get("lastname","")}'.strip(),
            "contact_title": c1.get("jobtitle", ""), "contact_email": c1.get("email", ""),
            "contact_phone": c1.get("phone", ""), "contact_mobile": c1.get("mobilephone", ""),
            "contact_city": c1.get("city", ""), "contact_country": c1.get("country", ""),
            "contact_company": c1.get("company", ""), "contact_linkedin": c1.get("linkedin_url", ""),
            "n_contacts": len(d2c.get(did, [])),
            "n_notes": sum(nb.values()), "first_note": d(min(ndates, default=None)),
            "last_note": d(max(ndates, default=None)),
            "notes_by": ", ".join(sorted(set(nauth))),
            **{f'nb_{b.lower().replace(" ", "_").replace("-", "").replace("__","_")}': nb.get(b, 0) for b in NB},
            "notes_text": notes_text,
            **{f"n_{t}": len(d2e[t].get(did, [])) for t in d2e},
        }
        for k, v in p.items():
            if k not in SKIP_DYN:
                row[k] = v; dyn_fill[k] += 1
        rows.append(row)

        # -- one row per stage ENTRY -> DEALS_TRANSITIONS.csv
        for j, (dt, lab, hu, act, st_) in enumerate(legs):
            frm = legs[j-1] if j else None
            fdep = depth_of(frm[1]) if frm else None
            tdep = depth_of(lab)
            delta = (tdep - fdep) if (tdep is not None and fdep is not None) else None
            trans_rows.append({
                "deal_id": did, "dealname": p.get("dealname", ""),
                "pipeline": PIPE.get(p.get("pipeline"), ""),
                "lead_source": p.get("lead_source", ""), "source_tab": p.get("source_tab", ""),
                "seq": j, "n_moves_total": len(legs) - 1,
                "entered_at": ts(dt), "date": d(dt),
                "dow": dt.strftime("%a") if dt else "", "hour": dt.hour if dt else "",
                "from_stage": frm[1] if frm else "", "to_stage": lab,
                "from_depth": fdep if fdep is not None else "",
                "to_depth": tdep if tdep is not None else "",
                "depth_delta": delta if delta is not None else "",
                "direction": ("create" if not frm else
                              "advance" if (delta or 0) > 0 else
                              "regress" if (delta or 0) < 0 else "lateral"),
                "to_is_dead": int(is_dead(lab)),
                "revived": int(bool(frm) and is_dead(frm[1]) and not is_dead(lab)),
                "mover": act, "source_type": st_, "human": int(hu),
                "owner_at_move": owner_at(dt),
                "dwell_prev_days": fdays(frm[0], dt) if frm else "",
                "days_since_create": fdays(created0, dt),
                "final_stage": cur_lab, "final_won": int(cur_lab.lower() == "closed/won"),
                "final_max_depth": LADDER[ever] if 0 <= ever < len(LADDER) else "",
            })

        # -- one row per task/email/meeting -> DEALS_ENGAGEMENTS.csv
        for typ in d2e:
            for eid in d2e[typ].get(did, []):
                e = eobjs[typ].get(eid)
                if not e: continue
                edt = ist_dt(e.get("hs_meeting_start_time") or e.get("hs_timestamp"))
                eng_rows.append({
                    "deal_id": did, "dealname": p.get("dealname", ""), "type": typ[:-1],
                    "ts": ts(edt), "date": d(edt),
                    "dow": edt.strftime("%a") if edt else "", "hour": edt.hour if edt else "",
                    "owner": OWN.get(e.get("hubspot_owner_id"), ""),
                    "subject": (e.get("hs_task_subject") or e.get("hs_email_subject")
                                or e.get("hs_meeting_title") or e.get("hs_call_title")
                                or e.get("hs_communication_channel_type") or ""),
                    "status": (e.get("hs_task_status") or e.get("hs_email_direction")
                               or e.get("hs_meeting_outcome") or ""),
                    "detail": plain(e.get("hs_task_body") or "")[:200],
                    "stage_at": stage_at(edt), "days_since_create": fdays(created0, edt),
                    "lead_source": p.get("lead_source", ""),
                })

    # ---- columns: fixed first, then dynamics by how often they are filled -----
    fixed = [k for k in rows[0].keys() if k not in dyn_fill] if rows else []
    dyn = [k for k, _ in dyn_fill.most_common()]
    cols = fixed + [k for k in dyn if k not in fixed]
    rows.sort(key=lambda r: (-r["max_depth_rank"], r["created"]))

    with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)

    for path, data, sort in ((os.path.join(HUB, "DEALS_TRANSITIONS.csv"), trans_rows,
                              lambda r: (r["deal_id"], r["seq"])),
                             (os.path.join(HUB, "DEALS_NOTES.csv"), note_rows,
                              lambda r: (r["deal_id"], r["ts"])),
                             (os.path.join(HUB, "DEALS_ENGAGEMENTS.csv"), eng_rows,
                              lambda r: (r["deal_id"], r["ts"]))):
        data.sort(key=sort)
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            if data:
                w = csv.DictWriter(f, fieldnames=list(data[0].keys())); w.writeheader(); w.writerows(data)
        print(f"wrote {path}: {len(data)} rows")

    print(f"\nwrote {OUT}: {len(rows)} rows x {len(cols)} cols "
          f"({len(fixed)} derived + {len(cols)-len(fixed)} raw properties)")
    print("\ndepth distribution (ever / human):")
    ce, ch = collections.Counter(r["max_depth"] for r in rows), collections.Counter(r["max_depth_human"] for r in rows)
    for i, lab in enumerate(LADDER):
        if ce.get(lab) or ch.get(lab): print(f"   {i:>2} {lab:<16}{ce.get(lab,0):>5}{ch.get(lab,0):>7}")
    if UNMAPPED:
        print("\nUNMAPPED stage labels (depth ignored for these — check they are harmless):")
        for k, v in UNMAPPED.most_common(): print(f"   {v:>4}x  {k}")


main()
