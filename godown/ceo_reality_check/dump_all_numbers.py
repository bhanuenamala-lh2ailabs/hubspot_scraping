# -*- coding: utf-8 -*-
"""EXHAUSTIVE NUMERIC DUMP — every cut, no conclusions. For analyst hand-off.
Emits DATA_DUMP.md (the document) + PER_DEAL_TIMELINE.csv (one row per deal, full timing)."""
import csv, os, json, collections, datetime, statistics as st, math
HERE=os.path.dirname(os.path.abspath(__file__))
def rd(f):
    with open(os.path.join(HERE,f),encoding="utf-8") as fh: return list(csv.DictReader(fh))
D=rd("DEALS_FULL.csv"); T=rd("STAGE_TRANSITIONS.csv"); N=rd("NOTES_FULL.csv"); TK=rd("TASKS_FULL.csv")
# Some historical transitions point at stages that have since been DELETED from the pipelines.
# They survive only as bare numeric ids. Relabel them so they are obvious rather than looking like a bug.
DELETED=set()
for _t in T:
    for _k in ("from_stage","to_stage"):
        _v=_t[_k]
        if _v and _v.isdigit():
            DELETED.add(_v); _t[_k]=f"(deleted stage {_v})"
try: E=rd("ENGAGEMENTS_FULL.csv")
except: E=[]
try: C=rd("CONTACTS_FULL.csv")
except: C=[]
try: CO=rd("COMPANIES_FULL.csv")
except: CO=[]
OUT=[]
def P(*a): OUT.append(" ".join(str(x) for x in a))
def H1(t): P(""); P("#"*110); P("## "+t); P("#"*110)
def H2(t): P(""); P("-"*110); P(t); P("-"*110)
def num(v):
    try:
        f=float(v); return f if f==f else None
    except: return None
def d2(x,y): return (100.0*x/y) if y else 0.0
def stats(v):
    v=[x for x in v if x is not None]
    if not v: return "n=0"
    s=sorted(v)
    def q(p):
        i=(len(s)-1)*p; lo=int(i); hi=min(lo+1,len(s)-1); return s[lo]+(s[hi]-s[lo])*(i-lo)
    return (f"n={len(s)} sum={sum(s):,.0f} mean={st.mean(s):,.1f} median={st.median(s):,.1f} "
            f"p25={q(.25):,.1f} p75={q(.75):,.1f} p90={q(.90):,.1f} min={min(s):,.1f} max={max(s):,.1f} "
            f"sd={(st.stdev(s) if len(s)>1 else 0):,.1f}")

ORDER=["Cold Call","No Pickup","Interested","GMeet Fixed","Script Shared","Script Results Received",
"Commercial Negotiation","Deal Contract Signed","Data Migration Done","Metadata Matched","Payment Initiation","Closed/Won"]
RANK={s:i for i,s in enumerate(ORDER)}
RANK["Call Attempted (retired)"]=1
FLOOR={"Dead/ColdCall/WrongFit":0,"Dead/ColdCall/WrongNumber":0,"Dead/ColdCall/NoPickup":1,
"Dead/ColdCall/Not Interested":2,"Dead/Interested/NoShow":2,"Dead/GMeet/NoShow":3,"Dead/GMeet/Cancelled":3,
"Dead/GMeet/wrong fit":3,"Dead/GMeet/Privacy Concerns":3,"Dead/ScriptShared/NoShow":4,
"Dead/ResultsReceived/WrongFit-Rejected":5,"Dead/Negotiation/Pricing":6,"Dead/Negotiation/Contractual":6}
# ---- build per-deal timeline ----
tl=collections.defaultdict(list)
for t in T: tl[t["deal_id"]].append(t)
for k in tl: tl[k].sort(key=lambda e:e["ts_ist"])
notes_by=collections.defaultdict(list)
for n in N: notes_by[n["deal_id"]].append(n)
tasks_by=collections.defaultdict(list)
for t in TK: tasks_by[t["deal_id"]].append(t)
def pd_(s):
    try: return datetime.date.fromisoformat(s[:10])
    except: return None
def pdt(s):
    try: return datetime.datetime.strptime(s[:19],"%Y-%m-%d %H:%M:%S")
    except: return None
TODAY=datetime.date(2026,8,17)
for d in D:
    did=d["deal_id"]; ev=tl.get(did,[])
    depth=RANK.get(d["stage_label"],FLOOR.get(d["stage_label"],0))
    first={}
    for e in ev:
        lab=e["to_stage"]
        if lab in RANK: depth=max(depth,RANK[lab])
        if lab not in first: first[lab]=e
        if e["from_stage"] in RANK: depth=max(depth,RANK[e["from_stage"]])
    d["_depth"]=depth
    d["_depth_label"]=ORDER[depth] if depth<len(ORDER) else "?"
    d["_first"]=first
    d["_nev"]=len(ev); d["_nhuman"]=sum(1 for e in ev if e["is_human"]=="True")
    d["_loc"]=num(d["loc"]); d["_pr"]=num(d["pr_count"])
    d["_ratio"]=(d["_loc"]/d["_pr"]) if (d["_loc"] and d["_pr"]) else None
    d["_t1"]=(300<=d["_ratio"]<=2000) if d["_ratio"] else None
    d["_won"]=d["stage_label"]=="Closed/Won"
    d["_dead"]=d["stage_label"].startswith("Dead/") or d["stage_label"]=="Call Attempted (retired)"
    d["_live"]=not(d["_won"] or d["_dead"])
    cd=pd_(d["create_day"]); d["_cd"]=cd
    lastd=pd_(d["last_move_day"]) or cd
    d["_age"]=(TODAY-cd).days if cd else None
    d["_idle"]=(TODAY-lastd).days if lastd else None
    d["_nnotes"]=len(notes_by.get(did,[])); d["_ntasks"]=len(tasks_by.get(did,[]))
    # time to each milestone from create
    for m in ORDER:
        e=first.get(m)
        d["_t_"+m]=((pd_(e["day"])-cd).days if (e and cd and pd_(e["day"])) else None)

P("LH2 AI LABS — EXHAUSTIVE NUMERIC DUMP")
P("="*110)
P(f"generated              : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} IST")
P(f"source                 : HubSpot portal 246754894 (live extract)")
P(f"deals                  : {len(D):,}")
P(f"stage transitions      : {len(T):,}")
P(f"notes                  : {len(N):,}")
P(f"tasks                  : {len(TK):,}")
P(f"engagements            : {len(E):,}")
P(f"contacts               : {len(C):,}")
P(f"companies              : {len(CO):,}")
days=[d["create_day"] for d in D if d["create_day"]]
P(f"date range (createdate): {min(days)} -> {max(days)}  ({(pd_(max(days))-pd_(min(days))).days+1} days)")
P("")
P("NO CONCLUSIONS ARE DRAWN IN THIS DOCUMENT. It is a complete numeric record for independent analysis.")
P("")
P("CONTENTS")
for i,s in enumerate(["Definitions & data dictionary","Deal inventory — every dimension",
"Stage distribution — current and ever-reached","The funnel — overall and sliced",
"Depth analysis — how far leads travel","Daily time series","Weekly time series",
"Per-person activity","Lead-source deep dive","Pipeline deep dive","Timelines — time to each stage",
"Dwell time per stage","Stage transition matrix","Death analysis","Cohort analysis by creation week",
"Cumulative pipeline over time","LoC / PR economics","Live pipeline inventory","Notes analysis",
"Tasks analysis","Contacts & companies","Per-deal appendix (deals past Cold Call)"],1):
    P(f"  {i:>2}. {s}")

H1("1. DEFINITIONS & DATA DICTIONARY")
P("depth / max stage reached : highest funnel rank a deal EVER touched, rebuilt from the full")
P("                            transition history (from_stage and to_stage), plus a floor implied")
P("                            by its Dead/* label (e.g. Dead/GMeet/* implies it reached GMeet Fixed).")
P("                            Rank order: " + " < ".join(ORDER))
P("is_human                  : stage move made in the HubSpot UI (sourceType=CRM_UI) vs INTEGRATION/API.")
P("tier-1                    : LoC/PR ratio between 300 and 2000 inclusive.")
P("live                      : not Closed/Won and not Dead/*.")
P("resolved                  : Closed/Won + all Dead/* (i.e. outcome settled).")
P("age_days                  : days from createdate to 2026-08-17.")
P("idle_days                 : days since the deal's last stage move.")
P("t_<stage>                 : days from createdate to the first RECORDED ENTRY transition into that")
P("                            stage. NOTE this differs slightly from depth: depth also credits a stage")
P("                            if it appears only as a from_stage (i.e. the entry predates the history")
P("                            window) or is implied by a Dead/* floor. So 'ever reached' counts in")
P("                            section 3.2/5 are >= the t_<stage> counts in section 11. Both are given.")
P("deleted stages            : some historical transitions reference pipeline stages that have since")
P("                            been deleted; they appear as '(deleted stage <id>)'. See section 1.1.")
P("")
H2("1.1 DELETED STAGES still referenced by history")
_dc=collections.Counter()
for _t in T:
    for _k in ("from_stage","to_stage"):
        if _t[_k].startswith("(deleted"): _dc[_t[_k]]+=1
P(f"  {len(DELETED)} distinct deleted stage ids appear in {sum(_dc.values())} transition endpoints.")
P("  These are from an earlier pipeline design. They carry no rank and are excluded from funnel/depth maths.")
for _k,_v in _dc.most_common(): P(f"    {_k:<34}{_v:>6}")
P("")
P("STAGE RANK TABLE")
for s in ORDER: P(f"  rank {RANK[s]:>2}  {s}")
P("  dead-stage floors:")
for k,v in sorted(FLOOR.items(),key=lambda x:x[1]): P(f"    {k:<44} implies reached rank {v} ({ORDER[v]})")

H1("2. DEAL INVENTORY — EVERY DIMENSION")
def tab(title,keyfn,rows=None):
    H2(title)
    c=collections.Counter(keyfn(d) for d in (rows or D))
    tot=sum(c.values())
    P(f"{'value':<52}{'deals':>8}{'% ':>9}")
    for k,v in c.most_common(): P(f"{str(k)[:51]:<52}{v:>8}{d2(v,tot):>8.2f}%")
    P(f"{'TOTAL':<52}{tot:>8}{100.0:>8.2f}%")
    return c
tab("2.1 by PIPELINE",lambda d:d["pipeline_label"])
tab("2.2 by LEAD SOURCE",lambda d:d["lead_source"] or "(none)")
tab("2.3 by OWNER",lambda d:d["owner_name"] or "(unassigned)")
tab("2.4 by CURRENT STAGE",lambda d:d["stage_label"])
tab("2.5 by DEPTH REACHED",lambda d:f"{d['_depth']} {d['_depth_label']}")
tab("2.6 by OUTCOME",lambda d:"Closed/Won" if d["_won"] else ("Dead" if d["_dead"] else "Live"))
tab("2.7 by CREATE WEEK",lambda d:d["create_week"] or "(none)")
tab("2.8 by SCRAPED TYPE",lambda d:d.get("scraped_type") or "(none)")
tab("2.9 by DISTRESS TIER",lambda d:d.get("distress_tier") or "(none)")
tab("2.10 by SOURCE TAB",lambda d:d.get("source_tab") or "(none)")

H2("2.11 CROSS-TAB: lead source x pipeline")
srcs=[s for s,_ in collections.Counter(d["lead_source"] or "(none)" for d in D).most_common()]
pipes=sorted({d["pipeline_label"] for d in D})
P(f"{'source':<50}"+"".join(f"{p[:14]:>16}" for p in pipes)+f"{'TOTAL':>10}")
for s in srcs:
    ds=[d for d in D if (d["lead_source"] or "(none)")==s]
    P(f"{s[:49]:<50}"+"".join(f"{sum(1 for d in ds if d['pipeline_label']==p):>16}" for p in pipes)+f"{len(ds):>10}")

H2("2.12 CROSS-TAB: lead source x owner")
owns=[o for o,_ in collections.Counter(d["owner_name"] or "(none)" for d in D).most_common()]
P(f"{'source':<44}"+"".join(f"{o.split()[0][:11]:>13}" for o in owns)+f"{'TOTAL':>9}")
for s in srcs:
    ds=[d for d in D if (d["lead_source"] or "(none)")==s]
    P(f"{s[:43]:<44}"+"".join(f"{sum(1 for d in ds if (d['owner_name'] or '(none)')==o):>13}" for o in owns)+f"{len(ds):>9}")

H2("2.13 CROSS-TAB: owner x current stage")
stgs=[s for s,_ in collections.Counter(d["stage_label"] for d in D).most_common()]
P(f"{'stage':<42}"+"".join(f"{o.split()[0][:11]:>13}" for o in owns)+f"{'TOTAL':>9}")
for s in stgs:
    ds=[d for d in D if d["stage_label"]==s]
    P(f"{s[:41]:<42}"+"".join(f"{sum(1 for d in ds if (d['owner_name'] or '(none)')==o):>13}" for o in owns)+f"{len(ds):>9}")

H2("2.14 CROSS-TAB: depth x lead source")
P(f"{'source':<44}"+"".join(f"{('d'+str(i)):>7}" for i in range(12))+f"{'TOT':>7}")
for s in srcs:
    ds=[d for d in D if (d["lead_source"] or "(none)")==s]
    P(f"{s[:43]:<44}"+"".join(f"{sum(1 for d in ds if d['_depth']==i):>7}" for i in range(12))+f"{len(ds):>7}")

H1("3. STAGE DISTRIBUTION — CURRENT AND EVER-REACHED")
H2("3.1 CURRENT stage")
c=collections.Counter(d["stage_label"] for d in D)
P(f"{'stage':<46}{'deals':>8}{'%':>9}{'cum%':>9}")
cum=0
for k,v in c.most_common():
    cum+=v; P(f"{k[:45]:<46}{v:>8}{d2(v,len(D)):>8.2f}%{d2(cum,len(D)):>8.2f}%")
H2("3.2 EVER-REACHED (from full transition history)")
P(f"{'stage':<46}{'ever reached':>14}{'% of all':>10}")
for s in ORDER:
    n_=sum(1 for d in D if d["_depth"]>=RANK[s])
    P(f"{s[:45]:<46}{n_:>14}{d2(n_,len(D)):>9.2f}%")
H2("3.3 ENTRIES into each stage (transition count, may exceed deal count)")
ent=collections.Counter(t["to_stage"] for t in T)
enth=collections.Counter(t["to_stage"] for t in T if t["is_human"]=="True")
P(f"{'stage':<46}{'entries':>9}{'human':>8}{'system':>8}")
for k,v in ent.most_common(): P(f"{k[:45]:<46}{v:>9}{enth.get(k,0):>8}{v-enth.get(k,0):>8}")

H1("4. THE FUNNEL — OVERALL AND SLICED")
def funnel(rows,label):
    H2(f"4.x FUNNEL — {label}  (n={len(rows)})")
    P(f"{'stage':<34}{'reached':>9}{'% of top':>10}{'step conv':>11}{'lost':>8}")
    prev=None
    for s in ORDER:
        n_=sum(1 for d in rows if d["_depth"]>=RANK[s])
        if s=="Cold Call": n_=len(rows)
        step=f"{d2(n_,prev):.2f}%" if prev else "-"
        P(f"{s:<34}{n_:>9}{d2(n_,len(rows)):>9.2f}%{step:>11}{(prev-n_ if prev is not None else 0):>8}")
        prev=n_
    w=sum(1 for d in rows if d["_won"]); dd=sum(1 for d in rows if d["_dead"]); lv=sum(1 for d in rows if d["_live"])
    P(f"  outcome: won {w}  dead {dd}  live {lv}   raw win {d2(w,len(rows)):.3f}%   resolved win {d2(w,w+dd):.3f}%")
funnel(D,"ALL DEALS")
for p in pipes: funnel([d for d in D if d["pipeline_label"]==p],f"PIPELINE = {p}")
for s in srcs:
    ds=[d for d in D if (d["lead_source"] or "(none)")==s]
    if len(ds)>=20: funnel(ds,f"SOURCE = {s}")
for o in owns:
    ds=[d for d in D if (d["owner_name"] or "(none)")==o]
    if len(ds)>=20: funnel(ds,f"OWNER = {o}")

H1("5. DEPTH ANALYSIS — HOW FAR LEADS TRAVEL")
H2("5.1 depth distribution")
c=collections.Counter(d["_depth"] for d in D)
P(f"{'depth':<8}{'stage':<30}{'deals':>8}{'%':>9}{'cum% (>= this depth)':>22}")
for i in range(12):
    ge=sum(1 for d in D if d["_depth"]>=i)
    P(f"{i:<8}{(ORDER[i] if i<len(ORDER) else '?'):<30}{c.get(i,0):>8}{d2(c.get(i,0),len(D)):>8.2f}%{d2(ge,len(D)):>21.2f}%")
H2("5.2 depth stats by lead source")
P(f"{'source':<48}{'n':>6}{'mean depth':>12}{'median':>8}{'max':>6}{'%>=2':>8}{'%>=4':>8}")
for s in srcs:
    ds=[d for d in D if (d["lead_source"] or "(none)")==s]
    dep=[d["_depth"] for d in ds]
    P(f"{s[:47]:<48}{len(ds):>6}{st.mean(dep):>12.2f}{st.median(dep):>8.1f}{max(dep):>6}"
      f"{d2(sum(1 for x in dep if x>=2),len(ds)):>7.1f}%{d2(sum(1 for x in dep if x>=4),len(ds)):>7.1f}%")
H2("5.3 depth stats by owner")
P(f"{'owner':<28}{'n':>6}{'mean depth':>12}{'median':>8}{'max':>6}{'%>=2':>8}{'%>=4':>8}")
for o in owns:
    ds=[d for d in D if (d["owner_name"] or "(none)")==o]
    dep=[d["_depth"] for d in ds]
    if not dep: continue
    P(f"{o[:27]:<28}{len(ds):>6}{st.mean(dep):>12.2f}{st.median(dep):>8.1f}{max(dep):>6}"
      f"{d2(sum(1 for x in dep if x>=2),len(ds)):>7.1f}%{d2(sum(1 for x in dep if x>=4),len(ds)):>7.1f}%")
H2("5.4 number of stage moves per deal")
P("  all deals      : "+stats([d["_nev"] for d in D]))
P("  human moves    : "+stats([d["_nhuman"] for d in D]))
P("  deals past CC  : "+stats([d["_nev"] for d in D if d["_depth"]>=2]))
P("  won deals      : "+stats([d["_nev"] for d in D if d["_won"]]))

H1("6. DAILY TIME SERIES")
alldays=sorted({d["create_day"] for d in D if d["create_day"]} | {t["day"] for t in T if t["day"]} | {n["day"] for n in N if n["day"]})
cre=collections.Counter(d["create_day"] for d in D)
mv=collections.Counter(t["day"] for t in T)
mvh=collections.Counter(t["day"] for t in T if t["is_human"]=="True")
nt=collections.Counter(n["day"] for n in N)
tk=collections.Counter(t["created_day"] for t in TK)
stg_day={s:collections.Counter(t["day"] for t in T if t["to_stage"]==s and t["is_human"]=="True") for s in ORDER}
won_day=collections.Counter(d["close_day"] for d in D if d["_won"] and d["close_day"])
loc_day=collections.defaultdict(float)
for d in D:
    if d["_won"] and d["close_day"]: loc_day[d["close_day"]]+=d["_loc"] or 0
P(f"{'date':<12}{'new':>6}{'moves':>7}{'human':>7}{'notes':>7}{'tasks':>7}{'conn':>6}{'gmeet':>7}{'script':>7}{'won':>5}{'LoC':>13}")
for day in alldays:
    conn=stg_day["Interested"].get(day,0)+sum(1 for t in T if t["day"]==day and t["to_stage"]=="Dead/ColdCall/Not Interested" and t["is_human"]=="True")
    P(f"{day:<12}{cre.get(day,0):>6}{mv.get(day,0):>7}{mvh.get(day,0):>7}{nt.get(day,0):>7}{tk.get(day,0):>7}"
      f"{conn:>6}{stg_day['GMeet Fixed'].get(day,0):>7}{stg_day['Script Shared'].get(day,0):>7}"
      f"{won_day.get(day,0):>5}{loc_day.get(day,0):>13,.0f}")
P(f"{'TOTAL':<12}{sum(cre.values()):>6}{sum(mv.values()):>7}{sum(mvh.values()):>7}{sum(nt.values()):>7}{sum(tk.values()):>7}"
  f"{'':>6}{sum(stg_day['GMeet Fixed'].values()):>7}{sum(stg_day['Script Shared'].values()):>7}{sum(won_day.values()):>5}{sum(loc_day.values()):>13,.0f}")

H1("7. WEEKLY TIME SERIES")
allw=sorted({d["create_week"] for d in D if d["create_week"]} | {t["week"] for t in T if t["week"]})
crw=collections.Counter(d["create_week"] for d in D)
mvw=collections.Counter(t["week"] for t in T); mvwh=collections.Counter(t["week"] for t in T if t["is_human"]=="True")
ntw=collections.Counter(n["week"] for n in N); tkw=collections.Counter(t["created_week"] for t in TK)
stg_w={s:collections.Counter(t["week"] for t in T if t["to_stage"]==s and t["is_human"]=="True") for s in ORDER}
wonw=collections.Counter(d["close_week"] for d in D if d["_won"] and d["close_week"])
locw=collections.defaultdict(float); loct1=collections.defaultdict(float)
for d in D:
    if d["_won"] and d["close_week"]:
        locw[d["close_week"]]+=d["_loc"] or 0
        if d["_t1"] is True: loct1[d["close_week"]]+=d["_loc"] or 0
P(f"{'week':<12}{'new':>6}{'moves':>7}{'human':>7}{'notes':>7}{'tasks':>7}{'inter':>7}{'gmeet':>7}{'script':>7}{'results':>8}{'neg':>5}{'won':>5}{'raw LoC':>13}{'tier1 LoC':>13}")
for w in allw:
    P(f"{w:<12}{crw.get(w,0):>6}{mvw.get(w,0):>7}{mvwh.get(w,0):>7}{ntw.get(w,0):>7}{tkw.get(w,0):>7}"
      f"{stg_w['Interested'].get(w,0):>7}{stg_w['GMeet Fixed'].get(w,0):>7}{stg_w['Script Shared'].get(w,0):>7}"
      f"{stg_w['Script Results Received'].get(w,0):>8}{stg_w['Commercial Negotiation'].get(w,0):>5}"
      f"{wonw.get(w,0):>5}{locw.get(w,0):>13,.0f}{loct1.get(w,0):>13,.0f}")
H2("7.1 weekly new leads BY SOURCE")
P(f"{'week':<12}"+"".join(f"{s[:13]:>15}" for s in srcs[:8]))
for w in allw:
    P(f"{w:<12}"+"".join(f"{sum(1 for d in D if d['create_week']==w and (d['lead_source'] or '(none)')==s):>15}" for s in srcs[:8]))
H2("7.2 weekly HUMAN stage moves BY OWNER")
P(f"{'week':<12}"+"".join(f"{o.split()[0][:12]:>14}" for o in owns))
for w in allw:
    P(f"{w:<12}"+"".join(f"{sum(1 for t in T if t['week']==w and t['is_human']=='True' and (t['mover_name'] or '(none)')==o):>14}" for o in owns))
H2("7.3 weekly NOTES BY OWNER")
P(f"{'week':<12}"+"".join(f"{o.split()[0][:12]:>14}" for o in owns))
for w in allw:
    P(f"{w:<12}"+"".join(f"{sum(1 for n in N if n['week']==w and (n['owner_name'] or '(none)')==o):>14}" for o in owns))

H1("8. PER-PERSON ACTIVITY")
for o in owns:
    if o=="(none)": continue
    H2(f"8.x {o}")
    od=[d for d in D if (d["owner_name"] or "(none)")==o]
    om=[t for t in T if (t["mover_name"] or "")==o and t["is_human"]=="True"]
    on=[n for n in N if (n["owner_name"] or "")==o]
    ot=[t for t in TK if (t["owner_name"] or "")==o]
    P(f"  deals owned            : {len(od)}")
    P(f"  human stage moves made : {len(om)}")
    P(f"  notes written          : {len(on)}")
    P(f"  tasks created          : {len(ot)}")
    dd=collections.defaultdict(set)
    for t in om: dd[t["day"]].add(t["deal_id"])
    if dd:
        P(f"  active days            : {len(dd)}")
        P(f"  distinct deals/day     : "+stats([len(v) for v in dd.values()]))
        P(f"  moves/day              : "+stats(list(collections.Counter(t['day'] for t in om).values())))
    if on:
        P(f"  notes/day              : "+stats(list(collections.Counter(n['day'] for n in on).values())))
    P(f"  owned-deal outcomes    : won {sum(1 for d in od if d['_won'])}  dead {sum(1 for d in od if d['_dead'])}  live {sum(1 for d in od if d['_live'])}")
    P(f"  owned-deal depth       : "+stats([d["_depth"] for d in od]))
    P(f"  moves BY TARGET STAGE:")
    for k,v in collections.Counter(t["to_stage"] for t in om).most_common(): P(f"      {k:<44}{v:>6}")
    P(f"  daily detail:")
    P(f"      {'date':<12}{'deals':>7}{'moves':>7}{'notes':>7}")
    for day in sorted(set(list(dd)+[n['day'] for n in on])):
        P(f"      {day:<12}{len(dd.get(day,[])):>7}{sum(1 for t in om if t['day']==day):>7}{sum(1 for n in on if n['day']==day):>7}")

H1("9. LEAD-SOURCE DEEP DIVE")
P(f"{'source':<48}{'deals':>7}{'>=Int':>7}{'>=GM':>6}{'>=SS':>6}{'won':>5}{'t1won':>6}{'dead':>6}{'live':>6}{'rawLoC':>12}{'t1LoC':>12}{'win%':>7}{'res%':>7}")
for s in srcs:
    ds=[d for d in D if (d["lead_source"] or "(none)")==s]
    w=[d for d in ds if d["_won"]]; t1=[d for d in w if d["_t1"] is True]; de=[d for d in ds if d["_dead"]]
    P(f"{s[:47]:<48}{len(ds):>7}{sum(1 for d in ds if d['_depth']>=2):>7}{sum(1 for d in ds if d['_depth']>=3):>6}"
      f"{sum(1 for d in ds if d['_depth']>=4):>6}{len(w):>5}{len(t1):>6}{len(de):>6}{sum(1 for d in ds if d['_live']):>6}"
      f"{sum(d['_loc'] or 0 for d in w):>12,.0f}{sum(d['_loc'] or 0 for d in t1):>12,.0f}"
      f"{d2(len(w),len(ds)):>6.2f}%{d2(len(w),len(w)+len(de)):>6.2f}%")
H2("9.1 per-source: age, idle, notes")
P(f"{'source':<48}{'mean age':>10}{'mean idle':>11}{'notes/deal':>12}{'moves/deal':>12}")
for s in srcs:
    ds=[d for d in D if (d["lead_source"] or "(none)")==s]
    P(f"{s[:47]:<48}{st.mean([d['_age'] for d in ds if d['_age'] is not None]):>10.1f}"
      f"{st.mean([d['_idle'] for d in ds if d['_idle'] is not None]):>11.1f}"
      f"{st.mean([d['_nnotes'] for d in ds]):>12.2f}{st.mean([d['_nev'] for d in ds]):>12.2f}")
H2("9.2 per-source: death-reason breakdown")
deaths=[s for s,_ in collections.Counter(d["stage_label"] for d in D if d["_dead"]).most_common()]
P(f"{'source':<40}"+"".join(f"{x.replace('Dead/','')[:13]:>15}" for x in deaths[:7]))
for s in srcs:
    ds=[d for d in D if (d["lead_source"] or "(none)")==s]
    P(f"{s[:39]:<40}"+"".join(f"{sum(1 for d in ds if d['stage_label']==x):>15}" for x in deaths[:7]))

H1("10. PIPELINE DEEP DIVE")
for p in pipes:
    ds=[d for d in D if d["pipeline_label"]==p]
    H2(f"10.x {p}  (n={len(ds)})")
    P(f"  stage distribution:")
    for k,v in collections.Counter(d["stage_label"] for d in ds).most_common(): P(f"      {k:<46}{v:>6}{d2(v,len(ds)):>8.2f}%")
    P(f"  sources:")
    for k,v in collections.Counter(d["lead_source"] or "(none)" for d in ds).most_common(): P(f"      {k:<46}{v:>6}")
    P(f"  owners:")
    for k,v in collections.Counter(d["owner_name"] or "(none)" for d in ds).most_common(): P(f"      {k:<46}{v:>6}")
    w=[d for d in ds if d["_won"]]
    P(f"  won {len(w)}  LoC {sum(d['_loc'] or 0 for d in w):,.0f}   depth mean {st.mean([d['_depth'] for d in ds]):.2f}")

H1("11. TIMELINES — DAYS FROM CREATE TO EACH STAGE")
H2("11.1 all deals that reached the stage")
P(f"{'stage':<30}{'n':>6}  {'days from createdate (stats)'}")
for s in ORDER:
    v=[d["_t_"+s] for d in D if d.get("_t_"+s) is not None]
    if v: P(f"{s:<30}{len(v):>6}  {stats(v)}")
H2("11.2 same, WON deals only")
for s in ORDER:
    v=[d["_t_"+s] for d in D if d["_won"] and d.get("_t_"+s) is not None]
    if v: P(f"{s:<30}{len(v):>6}  {stats(v)}")
H2("11.3 create -> close for won deals")
P("  days_to_close (property) : "+stats([num(d["days_to_close_calc"]) for d in D if d["_won"]]))
P("  age of live deals        : "+stats([d["_age"] for d in D if d["_live"]]))
P("  age of dead deals        : "+stats([d["_age"] for d in D if d["_dead"]]))
P("  idle days, live deals    : "+stats([d["_idle"] for d in D if d["_live"]]))
P("  idle days by depth (live):")
for i in range(12):
    v=[d["_idle"] for d in D if d["_live"] and d["_depth"]==i]
    if v: P(f"      depth {i} {ORDER[i] if i<len(ORDER) else '?':<28} "+stats(v))

H1("12. DWELL TIME PER STAGE (days between consecutive moves)")
dw=collections.defaultdict(list)
for did,ev in tl.items():
    for i in range(len(ev)-1):
        a=pdt(ev[i]["ts_ist"]); b=pdt(ev[i+1]["ts_ist"])
        if a and b: dw[ev[i]["to_stage"]].append((b-a).total_seconds()/86400.0)
P(f"{'stage':<44}{'n':>6}  stats (days)")
for s in ORDER+[x for x in dw if x not in ORDER]:
    if s in dw and dw[s]: P(f"{s[:43]:<44}{len(dw[s]):>6}  {stats(dw[s])}")

H1("13. STAGE TRANSITION MATRIX (from -> to, human moves)")
mat=collections.Counter((t["from_stage"],t["to_stage"]) for t in T if t["is_human"]=="True")
P(f"{'from':<40}{'to':<44}{'count':>7}")
for (a,b),v in mat.most_common(): P(f"{(a or '(create)')[:39]:<40}{b[:43]:<44}{v:>7}")
H2("13.1 SYSTEM (INTEGRATION/API) transitions")
mats=collections.Counter((t["from_stage"],t["to_stage"]) for t in T if t["is_human"]!="True")
P(f"{'from':<40}{'to':<44}{'count':>7}")
for (a,b),v in mats.most_common(30): P(f"{(a or '(create)')[:39]:<40}{b[:43]:<44}{v:>7}")
H2("13.2 backward / regressive moves (to a LOWER rank)")
back=[t for t in T if t["from_stage"] in RANK and t["to_stage"] in RANK and RANK[t["to_stage"]]<RANK[t["from_stage"]]]
P(f"  count: {len(back)}")
for (a,b),v in collections.Counter((t["from_stage"],t["to_stage"]) for t in back).most_common(20):
    P(f"    {a[:36]:<38} -> {b[:34]:<36}{v:>6}")

H1("14. DEATH ANALYSIS")
dead=[d for d in D if d["_dead"]]
P(f"total dead: {len(dead)}  ({d2(len(dead),len(D)):.2f}% of all)")
H2("14.1 by death stage")
P(f"{'death stage':<46}{'deals':>8}{'% of dead':>11}{'% of all':>10}{'mean depth':>12}")
for k,v in collections.Counter(d["stage_label"] for d in dead).most_common():
    ds=[d for d in dead if d["stage_label"]==k]
    P(f"{k[:45]:<46}{v:>8}{d2(v,len(dead)):>10.2f}%{d2(v,len(D)):>9.2f}%{st.mean([x['_depth'] for x in ds]):>12.2f}")
H2("14.2 deaths grouped by funnel position of the death LABEL")
grp={"ColdCall":0,"Interested":0,"GMeet":0,"ScriptShared":0,"ResultsReceived":0,"Negotiation":0,"other":0}
for d in dead:
    s=d["stage_label"]; hit=False
    for k in grp:
        if k!="other" and k in s.replace("/",""): grp[k]+=1; hit=True; break
    if not hit: grp["other"]+=1
for k,v in grp.items(): P(f"  {k:<20}{v:>7}{d2(v,len(dead)):>9.2f}%")
H2("14.3 deaths where the deal had actually reached deeper than the death label implies")
mism=[d for d in dead if d["_depth"]>FLOOR.get(d["stage_label"],0)+1]
P(f"  count: {len(mism)} of {len(dead)} ({d2(len(mism),len(dead)):.1f}%)")
for k,v in collections.Counter(f"{d['stage_label']} (actually reached {d['_depth_label']})" for d in mism).most_common(25):
    P(f"    {k[:88]:<90}{v:>5}")

H1("15. COHORT ANALYSIS BY CREATION WEEK")
P(f"{'cohort':<12}{'n':>6}{'>=Int':>7}{'>=GM':>6}{'>=SS':>6}{'won':>5}{'dead':>6}{'live':>6}{'%>=Int':>8}{'%>=SS':>8}{'win%':>7}{'mean depth':>12}{'mean age':>10}")
for w in allw:
    ds=[d for d in D if d["create_week"]==w]
    if not ds: continue
    P(f"{w:<12}{len(ds):>6}{sum(1 for d in ds if d['_depth']>=2):>7}{sum(1 for d in ds if d['_depth']>=3):>6}"
      f"{sum(1 for d in ds if d['_depth']>=4):>6}{sum(1 for d in ds if d['_won']):>5}{sum(1 for d in ds if d['_dead']):>6}"
      f"{sum(1 for d in ds if d['_live']):>6}{d2(sum(1 for d in ds if d['_depth']>=2),len(ds)):>7.2f}%"
      f"{d2(sum(1 for d in ds if d['_depth']>=4),len(ds)):>7.2f}%{d2(sum(1 for d in ds if d['_won']),len(ds)):>6.2f}%"
      f"{st.mean([d['_depth'] for d in ds]):>12.2f}{st.mean([d['_age'] for d in ds if d['_age'] is not None]):>10.1f}")

H1("16. CUMULATIVE PIPELINE OVER TIME")
P(f"{'week':<12}{'cum leads':>11}{'cum moves':>11}{'cum notes':>11}{'cum won':>9}{'cum raw LoC':>15}{'cum t1 LoC':>14}{'open deals EOW':>16}")
cl=cm=cn_=cw_=0; clo=ct=0.0
for w in allw:
    cl+=crw.get(w,0); cm+=mvw.get(w,0); cn_+=ntw.get(w,0); cw_+=wonw.get(w,0)
    clo+=locw.get(w,0); ct+=loct1.get(w,0)
    we=pd_(w)+datetime.timedelta(days=6)
    openn=sum(1 for d in D if d["_cd"] and d["_cd"]<=we and not (d["close_day"] and pd_(d["close_day"]) and pd_(d["close_day"])<=we) and not d["_dead"])
    P(f"{w:<12}{cl:>11}{cm:>11}{cn_:>11}{cw_:>9}{clo:>15,.0f}{ct:>14,.0f}{openn:>16}")

H1("17. LoC / PR ECONOMICS")
locd=sorted([d for d in D if d["_loc"]],key=lambda x:-x["_loc"])
P(f"{'deal':<30}{'LoC':>13}{'PRs':>8}{'LoC/PR':>9}{'tier1':>7}{'stage':<40}{'source':<32}{'created':<12}{'closed':<12}")
for d in locd:
    P(f"{d['dealname'][:29]:<30}{d['_loc']:>13,.0f}{(d['_pr'] and f'{d[chr(95)+chr(112)+chr(114)]:,.0f}') or '-':>8}"
      f"{(d['_ratio'] and f'{d[chr(95)+chr(114)+chr(97)+chr(116)+chr(105)+chr(111)]:,.0f}') or '-':>9}{str(d['_t1']):>7}"
      f"{d['stage_label'][:39]:<40}{(d['lead_source'] or '-')[:31]:<32}{d['create_day']:<12}{d['close_day']:<12}")
P("")
P("  all LoC deals   : "+stats([d["_loc"] for d in locd]))
P("  all PR counts   : "+stats([d["_pr"] for d in locd if d["_pr"]]))
P("  all ratios      : "+stats([d["_ratio"] for d in locd if d["_ratio"]]))
won=[d for d in D if d["_won"]]
P("  WON LoC         : "+stats([d["_loc"] for d in won if d["_loc"]]))
t1w=[d for d in won if d["_t1"] is True]
P("  WON tier-1 LoC  : "+stats([d["_loc"] for d in t1w]))
P(f"  totals: all={sum(d['_loc'] for d in locd):,.0f}  won={sum(d['_loc'] or 0 for d in won):,.0f}  won-tier1={sum(d['_loc'] for d in t1w):,.0f}")
import re
def base(n_): return re.sub(r"\s*\d+$","",re.sub(r"^S\s*-\s*","",n_ or "")).strip().lower().replace("backspacce","backspace")
H2("17.1 per DISTINCT COMPANY (deals de-duplicated by name root)")
comp=collections.defaultdict(lambda:{"n":0,"loc":0.0,"t1":0.0,"deals":[]})
for d in won:
    b=base(d["dealname"]); comp[b]["n"]+=1; comp[b]["loc"]+=d["_loc"] or 0; comp[b]["deals"].append(d["dealname"])
    if d["_t1"] is True: comp[b]["t1"]+=d["_loc"] or 0
P(f"{'company':<30}{'deals':>6}{'total LoC':>14}{'tier1 LoC':>14}  deal names")
for b,v in sorted(comp.items(),key=lambda x:-x[1]["loc"]):
    P(f"{b[:29]:<30}{v['n']:>6}{v['loc']:>14,.0f}{v['t1']:>14,.0f}  {', '.join(v['deals'])}")
P(f"\n  {len(won)} won deals -> {len(comp)} distinct companies")
P("  per-company LoC  : "+stats([v["loc"] for v in comp.values()]))
P("  per-company t1   : "+stats([v["t1"] for v in comp.values() if v["t1"]>0]))
H2("17.2 LoC by lead source / pipeline / owner")
for lab,keyfn in [("lead source",lambda d:d["lead_source"] or "(none)"),("pipeline",lambda d:d["pipeline_label"]),("owner",lambda d:d["owner_name"] or "(none)")]:
    P(f"  by {lab}:")
    agg=collections.defaultdict(lambda:[0,0.0,0.0])
    for d in won:
        k=keyfn(d); agg[k][0]+=1; agg[k][1]+=d["_loc"] or 0
        if d["_t1"] is True: agg[k][2]+=d["_loc"] or 0
    for k,v in sorted(agg.items(),key=lambda x:-x[1][1]): P(f"      {k[:44]:<46}{v[0]:>4} wins{v[1]:>14,.0f}{v[2]:>14,.0f} tier1")

H1("18. LIVE PIPELINE INVENTORY")
live=[d for d in D if d["_live"]]
P(f"live deals: {len(live)}")
P(f"{'stage':<32}{'deals':>7}{'prob':>7}{'known LoC':>13}{'mean age':>10}{'mean idle':>11}")
for s in ORDER:
    ds=[d for d in live if d["stage_label"]==s]
    if not ds: continue
    pr=num(ds[0].get("stage_probability")) or 0
    P(f"{s:<32}{len(ds):>7}{pr:>7.2f}{sum(d['_loc'] or 0 for d in ds):>13,.0f}"
      f"{st.mean([d['_age'] for d in ds if d['_age'] is not None]):>10.1f}{st.mean([d['_idle'] for d in ds if d['_idle'] is not None]):>11.1f}")
H2("18.1 live deals at depth >= GMeet Fixed (the deep pipeline), full list")
deep=sorted([d for d in live if d["_depth"]>=3],key=lambda x:(-x["_depth"],x["_idle"] or 0))
P(f"{'deal':<34}{'stage':<28}{'depth':>6}{'age':>5}{'idle':>6}{'notes':>7}{'LoC':>12}{'owner':<18}{'source'}")
for d in deep:
    P(f"{d['dealname'][:33]:<34}{d['stage_label'][:27]:<28}{d['_depth']:>6}{d['_age'] or 0:>5}{d['_idle'] or 0:>6}"
      f"{d['_nnotes']:>7}{(d['_loc'] or 0):>12,.0f}{(d['owner_name'] or '-')[:17]:<18}{(d['lead_source'] or '-')[:28]}")

H1("19. NOTES ANALYSIS")
P(f"total notes: {len(N)}  |  deals with >=1 note: {len({n['deal_id'] for n in N if n['deal_id']})}")
P("  notes per deal (all deals)  : "+stats([d["_nnotes"] for d in D]))
P("  notes per deal (>=1 note)   : "+stats([d["_nnotes"] for d in D if d["_nnotes"]>0]))
H2("19.1 notes by owner")
for k,v in collections.Counter(n["owner_name"] or "(none)" for n in N).most_common(): P(f"  {k:<30}{v:>7}")
H2("19.2 notes by week")
for k,v in sorted(collections.Counter(n["week"] for n in N).items()): P(f"  {k:<14}{v:>7}")
H2("19.3 keyword frequency in note bodies")
KW=["wrong number","wrong fit","not interested","did not pick","no pickup","call back","callback","follow up","follow-up",
"whatsapp","wa ","mail","meeting","gmeet","script","shared","interested","busy","switched off","out of service",
"wrong poc","proposal","codebase","repo","pr","demo","price","pricing","budget","legal","agreement","migration","deadpool"]
low=[(n["body"] or "").lower() for n in N]
for k in KW:
    c=sum(1 for b in low if k in b)
    if c: P(f"  {k:<24}{c:>7}{d2(c,len(N)):>8.2f}%")
H2("19.4 note length")
P("  chars: "+stats([len(n["body"] or "") for n in N]))

H1("20. TASKS ANALYSIS")
P(f"total tasks: {len(TK)}")
for lab,f_ in [("owner",lambda t:t["owner_name"] or "(none)"),("status",lambda t:t["status"]),
               ("type",lambda t:t["task_type"]),("week created",lambda t:t["created_week"])]:
    P(f"  by {lab}:")
    for k,v in collections.Counter(f_(t) for t in TK).most_common(): P(f"      {str(k)[:40]:<42}{v:>6}")

H1("21. CONTACTS & COMPANIES")
P(f"contacts: {len(C)}   companies: {len(CO)}")
if C:
    P(f"  with phone    : {sum(1 for c in C if c.get('phone'))}")
    P(f"  with mobile   : {sum(1 for c in C if c.get('mobilephone'))}")
    P(f"  with email    : {sum(1 for c in C if c.get('email'))}")
    P(f"  with linkedin : {sum(1 for c in C if c.get('linkedin_url'))}")
    P("  by create week:")
    for k,v in sorted(collections.Counter(c.get("create_week","") for c in C).items()): P(f"      {k:<14}{v:>7}")
if CO:
    P("  companies by country:")
    for k,v in collections.Counter(c.get("country") or "(none)" for c in CO).most_common(12): P(f"      {str(k)[:30]:<32}{v:>7}")

H1("22. PER-DEAL APPENDIX — every deal that got past Cold Call (depth >= 1)")
P("columns: deal | source | owner | pipeline | depth | current stage | created | age | idle | moves | notes | LoC | full stage path with dates")
past=sorted([d for d in D if d["_depth"]>=1],key=lambda x:(-x["_depth"],x["dealname"]))
P(f"total: {len(past)} deals")
for d in past:
    ev=tl.get(d["deal_id"],[])
    path=" > ".join(f"{e['to_stage']}({e['day'][5:]}{'H' if e['is_human']=='True' else 'S'})" for e in ev if e["day"])
    P("")
    P(f"[{d['_depth']}] {d['dealname']}")
    P(f"     src={d['lead_source'] or '-'} | owner={d['owner_name'] or '-'} | pipe={d['pipeline_label']} | stage={d['stage_label']}")
    P(f"     created={d['create_day']} age={d['_age']}d idle={d['_idle']}d moves={d['_nev']}(h{d['_nhuman']}) notes={d['_nnotes']} tasks={d['_ntasks']} LoC={d['_loc'] or '-'} PR={d['_pr'] or '-'} ratio={f'{d[chr(95)+chr(114)+chr(97)+chr(116)+chr(105)+chr(111)]:.0f}' if d['_ratio'] else '-'}")
    P(f"     path: {path}")

open(os.path.join(HERE,"DATA_DUMP.md"),"w",encoding="utf-8").write("\n".join(OUT))
# ---- per-deal CSV ----
cols=["deal_id","dealname","lead_source","owner_name","pipeline_label","stage_label","depth","depth_label",
"is_won","is_dead","is_live","create_day","create_week","close_day","close_week","age_days","idle_days",
"n_moves","n_human_moves","n_notes","n_tasks","loc","pr_count","loc_per_pr","tier1"]+["t_"+s.replace(" ","_") for s in ORDER]
with open(os.path.join(HERE,"PER_DEAL_TIMELINE.csv"),"w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(cols)
    for d in D:
        w.writerow([d["deal_id"],d["dealname"],d["lead_source"],d["owner_name"],d["pipeline_label"],d["stage_label"],
        d["_depth"],d["_depth_label"],d["_won"],d["_dead"],d["_live"],d["create_day"],d["create_week"],
        d["close_day"],d["close_week"],d["_age"],d["_idle"],d["_nev"],d["_nhuman"],d["_nnotes"],d["_ntasks"],
        d["loc"],d["pr_count"],d["loc_per_pr"],d["_t1"]]+[d.get("_t_"+s,"") for s in ORDER])
print("wrote DATA_DUMP.md lines:",len(OUT))
print("wrote PER_DEAL_TIMELINE.csv rows:",len(D))
