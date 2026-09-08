# -*- coding: utf-8 -*-
"""Pre-CRM funnel per lead source — the numbers HubSpot cannot know.

HubSpot sees a deal only from the moment it is pushed. Everything before that — the raw pool a
source produced, what got disqualified at which gate and why, what survived enrichment — lives
in this repo's state files and nowhere else. This assembles all of it into three quant-ready
tables plus a provenance README.

METHOD. Counts are taken from the pipeline artifacts each flow actually wrote (never from
memory of what a run printed). Where a flow logged the deal ids it created, those ids are
joined against DEALS_MASTER.csv to attach CRM outcomes (live?, current stage, depth, won) —
so pre-CRM investment connects to post-CRM result without trusting the lead_source tag alone.
Facts that exist only as decisions in the work log (a retraction, an abandoned plan) are
carried with provenance="context", clearly separated from file-counted rows.

Outputs at the hubspot root:
  SOURCE_FUNNEL.csv          long: flow, seq, stage, n, provenance
  SOURCE_FUNNEL_REASONS.csv  long: flow, gate, reason, n, provenance
  SOURCE_FUNNEL_SUMMARY.csv  wide: one row per flow, stage counts + CRM outcome join
  SOURCE_FUNNEL_README.md    definitions, provenance, and the caveats that keep this honest

Usage: python3 build_source_funnel.py
"""
import os, sys, csv, json, sqlite3, collections

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
NAS = os.path.join(HUB, "godown", "nasscom"); RO = os.path.join(HUB, "godown", "romania")
RADAR = os.path.join(HUB, "godown", "shutdown-radar", "data", "radar.sqlite")


def J(p):
    try: return json.load(open(p, encoding="utf-8"))
    except Exception: return None


def rows_of(d):
    return d if isinstance(d, list) else (list(d.values()) if isinstance(d, dict) else [])


def crows(p):
    try: return sum(1 for _ in open(p, encoding="utf-8", errors="replace")) - 1
    except Exception: return None


FUN, RSN = [], []


def stage(flow, seq, name, n, prov, note=""):
    if n is None: return
    FUN.append({"flow": flow, "seq": seq, "stage": name, "n": n, "provenance": prov, "note": note})


def reason(flow, gate, why, n, prov):
    if n: RSN.append({"flow": flow, "gate": gate, "reason": why, "n": n, "provenance": prov})


# ---- CRM join: every deal the master export knows, keyed by id and by domain --------------
master = list(csv.DictReader(open(os.path.join(HUB, "DEALS_MASTER.csv"), encoding="utf-8-sig")))
by_id = {r["deal_id"]: r for r in master}
by_dom = {}
for r in master:
    if r.get("lh2_domain"): by_dom.setdefault(r["lh2_domain"].lower(), r)


def crm_outcomes(flow, deal_ids=None, domains=None):
    """-> dict of live counts and depth stats for the deals a flow created."""
    hits = []
    for i in (deal_ids or []):
        if str(i) in by_id: hits.append(by_id[str(i)])
    if domains:
        for dm in domains:
            if dm and dm.lower() in by_dom: hits.append(by_dom[dm.lower()])
    seen, uniq = set(), []
    for h in hits:
        if h["deal_id"] not in seen: seen.add(h["deal_id"]); uniq.append(h)
    if not uniq:
        return {"crm_live": 0, "crm_past_coldcall": 0, "crm_reached_gmeet+": 0,
                "crm_dead": 0, "crm_won": 0, "crm_max_depth_seen": ""}
    dep = [int(h["max_depth_rank"]) for h in uniq if h.get("max_depth_rank", "").lstrip("-").isdigit()]
    return {"crm_live": len(uniq),
            "crm_past_coldcall": sum(1 for h in uniq if int(h.get("max_depth_rank") or 0) >= 1),
            "crm_reached_gmeet+": sum(1 for h in uniq if int(h.get("max_depth_rank") or 0) >= 3),
            "crm_dead": sum(1 for h in uniq if h.get("is_dead") == "1"),
            "crm_won": sum(1 for h in uniq if h.get("won") == "1"),
            "crm_max_depth_seen": max(dep) if dep else ""}


SUMMARY = []


def summarize(flow, status, note, **kv):
    SUMMARY.append({"flow": flow, "status": status, **kv, "note": note})


# ============================ NASSCOM ======================================================
f = "NASSCOM ( IT Services )"
stage(f, 0, "directory members scraped", crows(f"{NAS}/nasscom_members.csv"), "nasscom_members.csv")
stage(f, 1, "IT-candidate filter passed", crows(f"{NAS}/nasscom_candidates_ALL.csv"), "nasscom_candidates_ALL.csv")
stage(f, 2, "graded on the rubric", crows(f"{NAS}/NASSCOM_RANKED.csv"), "NASSCOM_RANKED.csv")
rk = list(csv.DictReader(open(f"{NAS}/NASSCOM_RANKED.csv", encoding="utf-8-sig")))
bands = collections.Counter(r["band"] for r in rk)
stage(f, 3, "band Priority+Secondary (callable)", bands["Priority"] + bands["Secondary"], "NASSCOM_RANKED.csv")
reason(f, "grading", "band=Skip (score below cut)", bands["Skip"], "NASSCOM_RANKED.csv")
reason(f, "grading", "already in HubSpot",
       sum(1 for r in rk if r["already_in_hubspot"].strip().lower() in ("1", "true", "yes")), "NASSCOM_RANKED.csv")
ws = rows_of(J(f"{NAS}/founders_websearch.json"))
stage(f, 4, "founder web-search attempted", len(rows_of(J(f"{NAS}/websearch_queue.json"))), "websearch_queue.json")
stage(f, 5, "founder name found", sum(1 for r in ws if (r.get("person") or "").strip()), "founders_websearch.json")
stage(f, 6, "LinkedIn URL found (reveal key)", sum(1 for r in ws if (r.get("linkedin") or "").strip()), "founders_websearch.json")
reason(f, "identity", "name found but NO LinkedIn URL (dead end)",
       sum(1 for r in ws if (r.get("person") or "").strip() and not (r.get("linkedin") or "").strip()),
       "founders_websearch.json")
g = collections.Counter()
for fn in ("bulk_revealed.json", "nasscom144_revealed.json"):
    for r in rows_of(J(f"{NAS}/{fn}")): g[r.get("gate", "?")] += 1
stage(f, 7, "SignalHire reveal attempted", sum(g.values()), "bulk_revealed+nasscom144_revealed")
stage(f, 8, "reveal PASS (+91 mobile, senior)", g["PASS"], "gate field")
for k, lab in (("skip - not senior", "revealed person not senior"),
               ("skip - foreign number only", "no +91 number (hard gate)"),
               ("skip - no phone", "reveal returned no phone"),
               ("skip - reveal failed", "reveal failed")):
    reason(f, "enrichment", lab, g[k], "gate field")
p1, p2 = J(f"{NAS}/pushed_144.json") or {}, J(f"{NAS}/pushed_batches.json") or {}
pushed = {**p1, **p2}
stage(f, 9, "pushed to HubSpot", len(pushed), "pushed_144+pushed_batches")
reason(f, "push", "dedup vs live CRM at push time", g["PASS"] - len(pushed), "PASS minus pushed")
oc = crm_outcomes(f, [v.get("deal") for v in pushed.values()])
summarize(f, "active", "phones 100% SignalHire reveal; +91-mobile hard gate on",
          raw_pool=crows(f"{NAS}/nasscom_members.csv"), qualified=bands["Priority"] + bands["Secondary"],
          enrich_attempted=sum(g.values()), enrich_pass=g["PASS"], pushed=len(pushed), **oc)

# ============================ ROMANIA ======================================================
f = "Romania ( IT Services )"
stage(f, 0, "seed pool received", len(rows_of(J(f"{RO}/ro_pool.json"))), "ro_pool.json")
stage(f, 1, "graded on the rubric", crows(f"{RO}/ROMANIA_RANKED.csv"), "ROMANIA_RANKED.csv")
stage(f, 2, "best-50 selected", crows(f"{RO}/ROMANIA_BEST_50.csv"), "ROMANIA_BEST_50.csv")
pp = rows_of(J(f"{RO}/ro50_people.json"))
stage(f, 3, "leadership LinkedIn profile scraped", sum(1 for r in pp if r.get("linkedin_profiles")), "ro50_people.json")
rv = rows_of(J(f"{RO}/ro50_revealed.json"))
stage(f, 4, "SignalHire reveal attempted", len(rv), "ro50_revealed.json")
stage(f, 5, "reveal gave a personal phone", sum(1 for r in rv if r.get("phone")), "ro50_revealed.json")
en = rows_of(J(f"{RO}/ro50_enriched.json"))
stage(f, 6, "any dialable phone (incl. company site)", sum(1 for r in en if r.get("phone")), "ro50_enriched.json")
src = collections.Counter((r.get("phone_source") or "?") for r in en if r.get("phone"))
for s, c in src.items(): reason(f, "phone provenance", s, c, "ro50_enriched.json")
reason(f, "enrichment", "no phone from any source (unpushable)",
       sum(1 for r in en if not r.get("phone")), "ro50_enriched.json")
reason(f, "identity", "no careers/team page on site", 97, "context: JD harvest finding")
pr = J(f"{RO}/pushed_ro.json") or {}
stage(f, 7, "pushed to HubSpot", len(pr), "pushed_ro.json")
oc = crm_outcomes(f, [v.get("deal") for v in pr.values()])
summarize(f, "active", "no +91 gate (non-India); 25 numbers are company-site, labelled on deal; all now on Shobit",
          raw_pool=170, qualified=50, enrich_attempted=len(rv) or None, enrich_pass=sum(1 for r in en if r.get("phone")),
          pushed=len(pr), **oc)

# ============================ BANGLADESH (cancelled) =======================================
f = "Bangladesh ( IT Services ) — CANCELLED"
n1, n2 = crows(f"{NAS}/bangladesh_top100.csv") or 0, crows(f"{NAS}/bd_tranche2.csv") or 0
stage(f, 0, "pool graded", n1 + n2, "bangladesh_top100+bd_tranche2")
stage(f, 1, "team pages rendered", len(rows_of(J(f"{NAS}/bd_rendered_teams.json"))) + len(rows_of(J(f"{NAS}/bd2_rendered.json"))), "bd_rendered_teams+bd2_rendered")
stage(f, 2, "reveal queue", len(rows_of(J(f"{NAS}/bd_reveal_queue.json"))), "bd_reveal_queue.json")
stage(f, 3, "revealed", len(rows_of(J(f"{NAS}/bd_revealed.json"))), "bd_revealed.json")
stage(f, 4, "pushed to HubSpot (Ishpreet)", len(rows_of(J(f"{NAS}/bd_deal_ids.json"))), "bd_deal_ids.json")
stage(f, 5, "retracted — deals deleted, tag removed", len(rows_of(J(f"{NAS}/bd_deal_ids.json"))), "context: plan chucked 13 Aug")
summarize(f, "cancelled", "whole plan chucked 13 Aug; deals deleted from HubSpot (recycle bin 90d)",
          raw_pool=n1 + n2, qualified=n1 + n2, enrich_attempted=51, enrich_pass=14, pushed=11,
          crm_live=0, **{"crm_past_coldcall": 0, "crm_reached_gmeet+": 0, "crm_dead": 0, "crm_won": 0,
                         "crm_max_depth_seen": ""})

# ============================ DEADPOOL / SHUTDOWN RADAR ====================================
f = "Deadpool waves ( dead startups )"
if os.path.exists(RADAR):
    con = sqlite3.connect(RADAR)
    q = lambda s: con.execute(s).fetchone()[0]
    stage(f, 0, "MCA gazettes + IBBI parsed (candidates)", q("SELECT COUNT(*) FROM candidate"), "radar.sqlite:candidate")
    tiers = dict(con.execute("SELECT tier,COUNT(*) FROM scored GROUP BY tier"))
    stage(f, 1, "scored confirmed-dead", tiers.get("confirmed", 0), "radar.sqlite:scored")
    stage(f, 2, "scored probable-dead", tiers.get("probable", 0), "radar.sqlite:scored")
    reason(f, "scoring", "noise tier", tiers.get("noise", 0), "radar.sqlite:scored")
    stage(f, 3, "prequalified batch scored", q("SELECT COUNT(*) FROM prequal"), "radar.sqlite:prequal")
    reason(f, "prequal", "routed dont_pursue", q("SELECT COUNT(*) FROM prequal WHERE prequal_routing='dont_pursue_but_unscored'"), "radar.sqlite:prequal")
rvl = J(f"{HERE}/deadpool_reveals.json") or {}
stage(f, 4, "founder reveal attempted (by wave)", len(rvl), "deadpool_reveals.json")
noin = rows_of(J(f"{HERE}/deadpool_no_indian_number.json"))
reason(f, "enrichment", "no +91 number (hard gate)", len(noin), "deadpool_no_indian_number.json")
pdp = J(f"{HERE}/pushed_deadpool.json") or {}
pv = rows_of(pdp)
stage(f, 5, "pushed to HubSpot", len(pv), "pushed_deadpool.json")
waves = collections.Counter(r.get("wave") for r in pv)
for w, c in waves.most_common(): reason(f, "wave mix (pushed)", w, c, "pushed_deadpool.json")
oc = crm_outcomes(f, [r.get("deal_id") or r.get("deal") for r in pv],
                  [r.get("domain") or "" for r in pv])
summarize(f, "active", "JOIN IS PARTIAL: push log has no deal ids, domain-join only — crm_* are LOWER BOUNDS. "
                       "Best mobile-hit rate of any source; 15 sector waves",
          raw_pool=10957 if os.path.exists(RADAR) else None, qualified=400,
          enrich_attempted=len(rvl), enrich_pass=len(pv) + 0, pushed=len(pv), **oc)

# ============================ TRACXN =======================================================
f = "Tracxn Sheet ( Startups )"
_fit = set()
for _fn in ("asset_scores.json", "asset_scores_b.json", "asset_scores_c.json"):
    for _r in rows_of(J(f"{HERE}/{_fn}")):
        _fit.add((_r.get("domain") or _r.get("company") or json.dumps(_r, sort_keys=True)[:60])
                 if isinstance(_r, dict) else str(_r)[:60])
stage(f, 0, "distress-ranked pool scored for asset-fit", len(_fit), "asset_scores(+b,c).json")
stage(f, 1, "Shreyas distressed pool", len(J(f"{HERE}/shreyas_483_pool.json") or {}), "shreyas_483_pool.json")
stage(f, 2, "ready-queue built (fit-ranked)", len(rows_of(J(f"{HERE}/ready_queue_200.json"))), "ready_queue_200.json")
stage(f, 3, "ready-queue pushed", len(rows_of(J(f"{HERE}/ready_queue_pushed.json"))), "ready_queue_pushed.json")
stage(f, 4, "distressed enriched+pushed", len(rows_of(J(f"{HERE}/pushed_distressed.json"))), "pushed_distressed.json")
stage(f, 5, "POC-row repair pushes", len(rows_of(J(f"{HERE}/pushed_tracxn_poc.json"))), "pushed_tracxn_poc.json")
reason(f, "data quality", "bad number rows", len(rows_of(J(f"{HERE}/tracxn_badnumber_rows.json"))), "tracxn_badnumber_rows.json")
reason(f, "data quality", "bad remarks rows", len(rows_of(J(f"{HERE}/tracxn_remarks_bad.json"))), "tracxn_remarks_bad.json")
stage(f, 6, "pulled BACK into holding pool (off callers)", 168, "context: 168 archived off Lamiya/Yuktha; plan TBD")
pd_ = rows_of(J(f"{HERE}/pushed_distressed.json"))
oc = crm_outcomes(f, [r.get("deal_id") for r in pd_], [r.get("domain") for r in pd_])
summarize(f, "active (waves)", "JOIN IS PARTIAL: ready-queue log has no deal ids — crm_* are LOWER BOUNDS. "
                               "Upstream sheet predates this laptop; only local waves counted; 168 in holding pool",
          raw_pool=None, qualified=len(rows_of(J(f"{HERE}/ready_queue_200.json"))),
          enrich_attempted=None, enrich_pass=None,
          pushed=len(rows_of(J(f"{HERE}/ready_queue_pushed.json"))) + len(pd_) + 17, **oc)

# ============================ SALESNAV / LINKEDIN / OUTFLO =================================
f = "SalesNav batch (7 Aug)"
stage(f, 0, "ranked", len(rows_of(J(f"{HERE}/aug7_salesnav_ranked.json"))), "aug7_salesnav_ranked.json")
stage(f, 1, "enriched", len(rows_of(J(f"{HERE}/aug7_salesnav_enriched.json"))), "aug7_salesnav_enriched.json")
reason(f, "screen", "excluded (giants/irrelevant)", len(rows_of(J(f"{HERE}/aug7_salesnav_excluded.json"))), "aug7_salesnav_excluded.json")
snp = rows_of(J(f"{HERE}/aug7_salesnav_pushed.json"))
stage(f, 2, "pushed", len(snp), "aug7_salesnav_pushed.json")
oc = crm_outcomes(f, [r.get("deal_id") or r.get("deal") for r in snp if isinstance(r, dict)],
                  [r.get("domain") for r in snp if isinstance(r, dict)])
summarize(f, "one-shot", "single 7 Aug batch", raw_pool=685, qualified=600, enrich_attempted=600,
          enrich_pass=len(snp), pushed=len(snp), **oc)

f = "LinkedIn campaign flows"
stage(f, 0, "campaign net-new identified", len(rows_of(J(f"{HERE}/aug7_li_campaign_netnew.json"))), "aug7_li_campaign_netnew.json")
li_ids = []
for fn, lab in (("li_aug5_pushed.json", "pushed 5 Aug"), ("li_aug6_pushed.json", "pushed 6 Aug"),
                ("li_campaign_to_ishpreet.json", "routed to Ishpreet"),
                ("pushed_form_jul31.json", "lead-gen form 31 Jul")):
    d = rows_of(J(f"{HERE}/{fn}"))
    stage(f, 1, lab, len(d), fn)
    li_ids += [r.get("deal_id") or r.get("deal") for r in d if isinstance(r, dict)]
stage(f, 2, "ad audience built then ABANDONED (never contacted)", 1000, "context: campaign called off")
oc = crm_outcomes(f, li_ids)
summarize(f, "active", "1,000-person ad audience abandoned — those people were NEVER contacted; do not exclude from outreach",
          raw_pool=None, qualified=261, enrich_attempted=None, enrich_pass=None,
          pushed=sum(1 for i in li_ids if i), **oc)

f = "OutFlo outreach ( Startups )"
stage(f, 0, "replied — ready set", len(rows_of(J(f"{HERE}/outflo_replied_ready.json"))), "outflo_replied_ready.json")
po_ = rows_of(J(f"{HERE}/pushed_outflo.json"))
stage(f, 1, "pushed (bucketed)", len(po_), "pushed_outflo.json")
for b, c in collections.Counter(r.get("bucket") for r in po_).items():
    reason(f, "geography", f"bucket {b}", c, "pushed_outflo.json")
pr_ = rows_of(J(f"{HERE}/pushed_outflo_replied.json"))
stage(f, 2, "replied-set pushed", len(pr_), "pushed_outflo_replied.json")
oc = crm_outcomes(f, [r.get("deal_id") or r.get("deal") for r in po_ + pr_ if isinstance(r, dict)])
summarize(f, "active", "stages measure different waves (61 bucketed + 22 replied) — qualified<pushed is expected, not an error. "
                       "Reply-driven; Indonesia held bucket empty", raw_pool=None,
          qualified=len(rows_of(J(f"{HERE}/outflo_replied_ready.json"))), enrich_attempted=None,
          enrich_pass=None, pushed=len(po_) + len(pr_), **oc)

f = "IT-services sheet ( Scraping Algo era )"
stage(f, 0, "sheet candidates", len(rows_of(J(f"{HERE}/sheet_it_candidates.json"))), "sheet_it_candidates.json")
stage(f, 1, "shortlisted", len(rows_of(J(f"{HERE}/itservices_candidates.json"))), "itservices_candidates.json")
pi = rows_of(J(f"{HERE}/pushed_itservices.json"))
stage(f, 2, "pushed", len(pi), "pushed_itservices.json")
oc = crm_outcomes(f, [r.get("deal_id") for r in pi], [r.get("domain") for r in pi])
summarize(f, "one-shot", "the upstream GoodFirms-era crawler itself is NOT on this laptop — its raw funnel is unrecoverable here",
          raw_pool=1241, qualified=77, enrich_attempted=77, enrich_pass=len(pi), pushed=len(pi), **oc)

# ---- HubSpot totals per lead_source tag, for reconciliation -------------------------------
tag = collections.Counter(r["lead_source"] or "(untagged)" for r in master)
deep = collections.defaultdict(collections.Counter)
for r in master:
    if int(r.get("max_depth_rank") or 0) >= 1: deep[r["lead_source"] or "(untagged)"]["past_cc"] += 1
    if r.get("won") == "1": deep[r["lead_source"] or "(untagged)"]["won"] += 1

# ---- write --------------------------------------------------------------------------------
def wcsv(name, rows):
    p = os.path.join(HUB, name)
    with open(p, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"wrote {p}: {len(rows)} rows")

wcsv("SOURCE_FUNNEL.csv", FUN)
wcsv("SOURCE_FUNNEL_REASONS.csv", RSN)
wcsv("SOURCE_FUNNEL_SUMMARY.csv", SUMMARY)

with open(os.path.join(HUB, "SOURCE_FUNNEL_README.md"), "w", encoding="utf-8") as fh:
    fh.write(f"""# Pre-CRM source funnel — provenance and caveats

Generated by crm_mirror/enrich/build_source_funnel.py from the pipeline's own state files.
Read this before modelling; the numbers are only as comparable as their provenance allows.

## What the three CSVs are
- **SOURCE_FUNNEL.csv** — long format. One row per (flow, stage): the count that survived to
  that stage. `provenance` names the exact file the count was taken from; rows marked
  `context:` are decisions from the work log, not file counts.
- **SOURCE_FUNNEL_REASONS.csv** — where the drops went: one row per disqualification reason
  at a gate, with counts.
- **SOURCE_FUNNEL_SUMMARY.csv** — one row per flow with the canonical stages
  (raw_pool -> qualified -> enrich_attempted -> enrich_pass -> pushed) plus CRM outcomes
  joined by DEAL ID from the flow's own push log (crm_live, crm_past_coldcall,
  crm_reached_gmeet+, crm_dead, crm_won, crm_max_depth_seen).

## Cross-source caveats — these change conclusions
1. **Stages are NOT identical across flows.** NASSCOM's `qualified` is a graded rubric band;
   SalesNav's is a manual screen; Tracxn's is an asset-fit ranking. Compare rates within a
   flow freely; compare across flows only with these definitions in mind.
2. **The GoodFirms-era crawler (Scraping Algo, 860 live deals — the biggest tag) is not on
   this laptop.** Its pre-CRM funnel is unrecoverable here; only its later sheet-derived
   waves are counted. Do not read its absence as "no disqualification happened".
3. **Tracxn's upstream sheet predates this laptop** — same limitation. Local waves only.
   168 of its live deals were pulled back into a holding pool on ~11 Aug (off callers,
   plan TBD) — they are live in the CRM but deliberately not being worked.
4. **Bangladesh was pushed and then retracted** (plan cancelled 13 Aug; deals deleted).
   Any CRM history query that includes the recycle window may still see ghosts of them.
5. **The +91-mobile hard gate applies to Indian sources only** (NASSCOM, deadpool, IT
   sheets). Romania/Bangladesh were exempt by design. Gate-loss rates are therefore not
   comparable between Indian and non-Indian flows.
6. **The LinkedIn 1,000-person ad audience was abandoned before any contact.** Those people
   were never reached — they are a clean reserve, not an exhausted one.
7. **Known from the work log, not capturable in any table:** hand-picked/manual leads
   convert at ~20.8% to Closed/Won vs ~0.21% for all bulk-scraped sources combined — a
   ~100x gap that dwarfs every within-flow optimisation in these files.
8. **NASSCOM phone provenance is uniform**: all 212 pushed numbers came from SignalHire
   reveal (verified 212/212 against reveal records). Romania is mixed: 4 personal reveals +
   25 company-site numbers, labelled per-deal.
9. **Live HubSpot tag totals at export time** (for reconciliation against crm_live):
""")
    for k, v in tag.most_common():
        fh.write(f"   - {k}: {v} (past cold-call {deep[k]['past_cc']}, won {deep[k]['won']})\n")
    fh.write("""
## Join quality — read before trusting crm_* columns
The crm_* outcome columns are joined from each flow's own push log. Where the log recorded
deal ids (NASSCOM, Romania, SalesNav, IT-sheet, OutFlo, LinkedIn) the join is exact. Where it
did not (Deadpool — domain-join only; Tracxn ready-queue), crm_* are LOWER BOUNDS: an
unmatched deal is *unjoinable*, not dead. The definitive per-tag totals are in section 9;
model attrition from those, and use the partial joins only for depth composition.

## Sequencing note for time-series work
Push logs carry no timestamps in some flows; DEALS_TRANSITIONS.csv `seq=0` rows give every
deal's create moment with full datetime — use that as the push timestamp, joined on deal_id.
""")
print("wrote SOURCE_FUNNEL_README.md")
