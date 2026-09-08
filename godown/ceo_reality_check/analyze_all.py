# -*- coding: utf-8 -*-
"""Every number, every cut. Emits ANALYSIS_ALL_NUMBERS.txt — the complete numeric record."""
import csv, json, collections, datetime, statistics as st, os, math
HERE=os.path.dirname(os.path.abspath(__file__))
def rd(f):
    with open(os.path.join(HERE,f),encoding="utf-8") as fh: return list(csv.DictReader(fh))
D=rd("DEALS_FULL.csv"); T=rd("STAGE_TRANSITIONS.csv"); N=rd("NOTES_FULL.csv"); TK=rd("TASKS_FULL.csv")
OUT=[]
def P(*a):
    s=" ".join(str(x) for x in a); OUT.append(s); print(s)
def H(t):
    P(""); P("="*100); P(t); P("="*100)
def num(v):
    try:
        f=float(v); return f if f==f else None
    except: return None

ORDER=["Cold Call","No Pickup","Interested","GMeet Fixed","Script Shared","Script Results Received",
       "Commercial Negotiation","Deal Contract Signed","Data Migration Done","Metadata Matched",
       "Payment Initiation","Closed/Won"]
RANK={s:i+1 for i,s in enumerate(ORDER)}
DEAD={"Dead/ColdCall/WrongFit":1,"Dead/ColdCall/WrongNumber":1,"Dead/ColdCall/NoPickup":1,
"Call Attempted (retired)":1,"Dead/ColdCall/Not Interested":3,"Dead/Interested/NoShow":3,
"Dead/GMeet/NoShow":4,"Dead/GMeet/Cancelled":4,"Dead/GMeet/wrong fit":4,"Dead/GMeet/Privacy Concerns":4,
"Dead/ScriptShared/NoShow":5,"Dead/ResultsReceived/WrongFit-Rejected":6,
"Dead/Negotiation/Pricing":7,"Dead/Negotiation/Contractual":7}
def rank(s): return RANK.get(s, DEAD.get(s,0))
for d in D:
    d["_r"]=rank(d["stage_label"]); d["_mr"]=rank(d["max_stage_label_reached"]) or d["_r"]
    d["_loc"]=num(d["loc"]); d["_pr"]=num(d["pr_count"])
    d["_ratio"]=(d["_loc"]/d["_pr"]) if (d["_loc"] and d["_pr"]) else None
    d["_t1"]=(300<=d["_ratio"]<=2000) if d["_ratio"] else None
    d["_won"]=d["stage_label"]=="Closed/Won"; d["_dead"]=d["stage_label"].startswith("Dead/") or d["stage_label"]=="Call Attempted (retired)"

P("LH2 AI LABS — COMPLETE NUMERIC RECORD FOR THE 1-BILLION-LoC REALITY CHECK")
P(f"generated {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}  |  source: HubSpot portal 246754894")
P(f"deals={len(D)} transitions={len(T)} notes={len(N)} tasks={len(TK)}")

H("1. THE ENTIRE LoC EVIDENCE BASE — every deal that has ever carried a LoC number")
locd=sorted([d for d in D if d["_loc"]],key=lambda x:-x["_loc"])
P(f"{'deal':<28}{'LoC':>12}{'PRs':>8}{'LoC/PR':>9} {'tier1':<6}{'stage':<40}{'source':<32}{'closed'}")
for d in locd:
    P(f"{d['dealname'][:27]:<28}{d['_loc']:>12,.0f}{(d['_pr'] and f'{d[chr(95)+chr(112)+chr(114)]:,.0f}') or '-':>8}"
      f"{(d['_ratio'] and f'{d[chr(95)+chr(114)+chr(97)+chr(116)+chr(105)+chr(111)]:,.0f}') or '-':>9} {str(d['_t1']):<6}"
      f"{d['stage_label'][:39]:<40}{(d['lead_source'] or '-')[:31]:<32}{d['close_day']}")
tot=sum(d["_loc"] for d in locd)
t1=[d for d in locd if d["_t1"] is True]; f1=[d for d in locd if d["_t1"] is False]
P(f"\nTOTAL LoC recorded ever          {tot:>14,.0f}   across {len(locd)} deals")
P(f"TIER-1 (300<=LoC/PR<=2000)       {sum(d['_loc'] for d in t1):>14,.0f}   across {len(t1)} deals  ({100*sum(d['_loc'] for d in t1)/tot:.1f}% of raw)")
P(f"FAILS tier-1 ratio               {sum(d['_loc'] for d in f1):>14,.0f}   across {len(f1)} deals  -> {', '.join(d['dealname'] for d in f1)}")
P(f"QUALITY HAIRCUT: {100-100*sum(d['_loc'] for d in t1)/tot:.1f}% of harvested LoC fails the CEO's own ratio bar")

H("2. CLOSED/WON — per deal and per DISTINCT COMPANY")
won=[d for d in D if d["_won"]]
P(f"{'deal':<28}{'LoC':>12}{'LoC/PR':>9} {'tier1':<6}{'created':<12}{'closed':<12}{'days':>5}  source")
for d in sorted(won,key=lambda x:x["close_day"] or ""):
    P(f"{d['dealname'][:27]:<28}{(d['_loc'] or 0):>12,.0f}{(d['_ratio'] and f'{d[chr(95)+chr(114)+chr(97)+chr(116)+chr(105)+chr(111)]:,.0f}') or '-':>9} {str(d['_t1']):<6}{d['create_day']:<12}{d['close_day']:<12}{d['days_to_close_calc']:>5}  {(d['lead_source'] or '-')[:30]}")
import re
def base(n): return re.sub(r"\s*\d+$","",re.sub(r"^S\s*-\s*","",n or "")).strip().lower().replace("backspacce","backspace")
comp=collections.defaultdict(lambda:{"loc":0,"t1":0,"n":0})
for d in won:
    b=base(d["dealname"]); comp[b]["loc"]+=d["_loc"] or 0; comp[b]["n"]+=1
    if d["_t1"] is True: comp[b]["t1"]+=d["_loc"] or 0
P(f"\n{len(won)} won DEALS  ->  {len(comp)} DISTINCT COMPANIES")
P(f"{'company':<30}{'deals':>6}{'total LoC':>14}{'tier1 LoC':>14}")
for b,v in sorted(comp.items(),key=lambda x:-x[1]["loc"]):
    P(f"{b[:29]:<30}{v['n']:>6}{v['loc']:>14,.0f}{v['t1']:>14,.0f}")
cl=[v["loc"] for v in comp.values()]; ct=[v["t1"] for v in comp.values() if v["t1"]>0]
P(f"\nper-COMPANY raw LoC   mean={st.mean(cl):,.0f} median={st.median(cl):,.0f}")
P(f"per-COMPANY tier1 LoC mean={st.mean(ct):,.0f} median={st.median(ct):,.0f}  (n={len(ct)} companies with tier-1 LoC)")
wt1=[d["_loc"] for d in won if d["_t1"] is True]
P(f"\nper-DEAL tier1 won LoC: n={len(wt1)} mean={st.mean(wt1):,.0f} median={st.median(wt1):,.0f} min={min(wt1):,.0f} max={max(wt1):,.0f}")
sw=sorted(wt1); P(f"  sorted: {[f'{x:,.0f}' for x in sw]}")
ex=[x for x in wt1 if x<15e6]
P(f"  excluding Deliqt outlier: n={len(ex)} mean={st.mean(ex):,.0f} median={st.median(ex):,.0f}")
P(f"  25% trimmed mean: {st.mean(sorted(wt1)[len(wt1)//4:len(wt1)-len(wt1)//4]):,.0f}")

H("3. FULL FUNNEL — every deal by DEEPEST stage ever reached")
mr=collections.Counter(d["max_stage_label_reached"] for d in D)
P(f"{'deepest stage reached':<44}{'deals':>7}{'% of all':>10}")
for s,c in sorted(mr.items(),key=lambda x:-rank(x[0])):
    P(f"{s[:43]:<44}{c:>7}{100*c/len(D):>9.2f}%")
P("")
P(f"{'milestone':<34}{'deals':>7}{'% of top':>10}{'step conv':>11}")
prev=None
for s in ORDER:
    c=sum(1 for d in D if d["_mr"]>=rank(s))
    step=(100*c/prev) if prev else 100.0
    P(f"{s:<34}{c:>7}{100*c/len(D):>9.2f}%{step:>10.1f}%")
    prev=c if c else prev
live=[d for d in D if not d["_won"] and not d["_dead"]]
P(f"\nterminal (won+dead) = {len(D)-len(live)}  ({100*(len(D)-len(live))/len(D):.1f}%)   still live = {len(live)}")
P(f"raw win rate      = {len(won)}/{len(D)} = {100*len(won)/len(D):.3f}%")
P(f"resolved win rate = {len(won)}/{len(D)-len(live)} = {100*len(won)/(len(D)-len(live)):.3f}%")
t1w=[d for d in won if d["_t1"] is True]
P(f"TIER-1 raw win rate      = {len(t1w)}/{len(D)} = {100*len(t1w)/len(D):.3f}%")
P(f"TIER-1 resolved win rate = {len(t1w)}/{len(D)-len(live)} = {100*len(t1w)/(len(D)-len(live)):.3f}%")
ss=sum(1 for d in D if d["_mr"]>=RANK["Script Shared"])
P(f"\nreached Script Shared+ = {ss}  ->  wins {len(won)}  = {100*len(won)/ss:.1f}% late-stage conversion")
P(f"reached GMeet Fixed+   = {sum(1 for d in D if d['_mr']>=RANK['GMeet Fixed'])}")

H("4. FUNNEL BY LEAD SOURCE (the efficiency table)")
P(f"{'source':<48}{'deals':>6}{'GMeet+':>8}{'Scr+':>6}{'won':>5}{'t1won':>6}{'LoC won':>13}{'t1 LoC':>13}{'LoC/1k leads':>14}{'win%':>7}")
srcs=collections.Counter(d["lead_source"] or "(none)" for d in D)
rows=[]
for s,_ in srcs.most_common():
    ds=[d for d in D if (d["lead_source"] or "(none)")==s]
    g=sum(1 for d in ds if d["_mr"]>=RANK["GMeet Fixed"]); sc=sum(1 for d in ds if d["_mr"]>=RANK["Script Shared"])
    w=[d for d in ds if d["_won"]]; t=[d for d in w if d["_t1"] is True]
    lw=sum(d["_loc"] or 0 for d in w); lt=sum(d["_loc"] or 0 for d in t)
    per=1000*lt/len(ds)
    rows.append((s,len(ds),g,sc,len(w),len(t),lw,lt,per))
    P(f"{s[:47]:<48}{len(ds):>6}{g:>8}{sc:>6}{len(w):>5}{len(t):>6}{lw:>13,.0f}{lt:>13,.0f}{per:>14,.0f}{100*len(w)/len(ds):>6.2f}%")
P(f"\nRANKED BY TIER-1 LoC PER 1000 LEADS (true efficiency):")
for r in sorted(rows,key=lambda x:-x[8]):
    if r[1]>=20: P(f"  {r[0][:46]:<48}{r[8]:>12,.0f} tier1-LoC per 1000 leads   (n={r[1]})")
zero=[r for r in rows if r[4]==0]
P(f"\nZERO-WIN sources: {sum(r[1] for r in zero)} leads burned with 0 wins -> {', '.join(r[0][:28] for r in zero)}")

H("5. WEEKLY TIME SERIES — supply, progression, output")
cw=collections.Counter(d["create_week"] for d in D if d["create_week"])
wks=sorted(cw)
ssw=collections.Counter(); gmw=collections.Counter(); connw=collections.Counter()
for t in T:
    if t["is_human"]!="True": continue
    if t["to_stage"]=="Script Shared": ssw[t["week"]]+=1
    if t["to_stage"]=="GMeet Fixed": gmw[t["week"]]+=1
    if t["to_stage"] in ("Interested","Dead/ColdCall/Not Interested"): connw[t["week"]]+=1
locw=collections.defaultdict(float); loct1=collections.defaultdict(float); wonw=collections.Counter()
for d in won:
    k=d["close_week"]
    if not k: continue
    locw[k]+=d["_loc"] or 0; wonw[k]+=1
    if d["_t1"] is True: loct1[k]+=d["_loc"] or 0
allw=sorted(set(list(cw)+list(locw)+list(ssw)))
P(f"{'week':<13}{'leads new':>10}{'connects':>10}{'GMeets':>8}{'scripts':>9}{'wins':>6}{'raw LoC':>14}{'tier1 LoC':>14}")
for w in allw:
    P(f"{w:<13}{cw.get(w,0):>10}{connw.get(w,0):>10}{gmw.get(w,0):>8}{ssw.get(w,0):>9}{wonw.get(w,0):>6}{locw.get(w,0):>14,.0f}{loct1.get(w,0):>14,.0f}")
P(f"\nTOTALS      {sum(cw.values()):>10}{sum(connw.values()):>10}{sum(gmw.values()):>8}{sum(ssw.values()):>9}{sum(wonw.values()):>6}{sum(locw.values()):>14,.0f}{sum(loct1.values()):>14,.0f}")
days=[d["create_day"] for d in D if d["create_day"]]
span=(datetime.date.fromisoformat(max(days))-datetime.date.fromisoformat(min(days))).days+1
P(f"\nCRM span {min(days)} -> {max(days)} = {span} days = {span/7:.2f} weeks")
P(f"RAW   run-rate over CRM life : {sum(locw.values())/(span/7):>14,.0f} LoC/week")
P(f"TIER1 run-rate over CRM life : {sum(loct1.values())/(span/7):>14,.0f} LoC/week")
cwk=[k for k in sorted(locw) if locw[k]>0]
P(f"weeks with any close: {len(cwk)} of {len(allw)}  -> {', '.join(cwk)}")
P(f"TIER1 mean over CLOSING weeks only: {st.mean([loct1[k] for k in cwk]):,.0f} LoC/week")
P(f"*** ZERO closes since 2026-08-10. Current week {allw[-1]}: {cw.get(allw[-1],0)} new leads, {wonw.get(allw[-1],0)} wins ***")

H("6. HUMAN CAPACITY — what the callers actually produce")
act=collections.defaultdict(lambda: collections.defaultdict(set))
mv=collections.defaultdict(collections.Counter)
for t in T:
    if t["is_human"]!="True" or not t["mover_name"]: continue
    act[t["mover_name"]][t["day"]].add(t["deal_id"]); mv[t["mover_name"]][t["day"]]+=1
nt=collections.defaultdict(collections.Counter)
for n in N:
    if n["owner_name"]: nt[n["owner_name"]][n["day"]]+=1
P(f"{'person':<18}{'days':>6}{'deals touched':>15}{'moves':>8}{'notes':>8}{'deals/day':>11}{'max day':>9}{'notes/day':>11}")
for p in sorted(set(list(act)+list(nt))):
    dd=act.get(p,{}); tot_d=sum(len(v) for v in dd.values()); nd=len(dd)
    mvs=sum(mv[p].values()); nts=sum(nt[p].values())
    mx=max((len(v) for v in dd.values()),default=0)
    P(f"{p[:17]:<18}{nd:>6}{tot_d:>15}{mvs:>8}{nts:>8}{(tot_d/nd if nd else 0):>11.1f}{mx:>9}{(nts/len(nt[p]) if nt.get(p) else 0):>11.1f}")
CALLERS=["Yuktha Anand","Lamiya Saleem"]
cd=[len(v) for p in CALLERS for v in act.get(p,{}).values()]
P(f"\nCOLD-CALL TEAM (Yuktha+Lamiya): {len(cd)} person-days")
P(f"  deals touched/person/day  mean={st.mean(cd):.1f} median={st.median(cd):.1f} p90={sorted(cd)[int(.9*len(cd))]:.0f} max={max(cd)}")
P(f"  sustained weekly capacity/caller (5 working days x mean) = {5*st.mean(cd):,.0f} leads")
P(f"  2-caller weekly ceiling (5 days x p90)                   = {2*5*sorted(cd)[int(.9*len(cd))]:,.0f} leads")
P(f"  observed lead creation mean/week                          = {st.mean([cw[w] for w in wks]):,.0f}")
P(f"  -> BINDING CONSTRAINT: {'LEAD SUPPLY' if st.mean([cw[w] for w in wks])<2*5*st.mean(cd) else 'CALLING CAPACITY'}")

H("7. THE 1-BILLION MODEL")
UNIV=  {"prequal survivors (IT services)":5629,"NASSCOM members":2775,
        "dead startups w/ codebases":3274,"prequal reserve":3092,"whales":30}
P("KNOWN ADDRESSABLE UNIVERSE (local source pools):")
for k,v in UNIV.items(): P(f"  {k:<44}{v:>8,}")
P(f"  {'RAW SUM (with overlap)':<44}{sum(UNIV.values()):>8,}")
P(f"  {'realistic de-duplicated estimate':<44}{'9,000 - 15,000':>8}")
P("")
cands={"tier-1 median per deal":st.median(wt1),"tier-1 mean per deal":st.mean(wt1),
       "tier-1 mean ex-outlier":st.mean(ex),"tier-1 median per COMPANY":st.median(ct),
       "tier-1 mean per COMPANY":st.mean(ct)}
P(f"{'expected LoC per tier-1 win':<34}{'value':>13}{'wins for 1Bn':>14}{'@0.42% raw':>14}{'@0.72% resolved':>17}")
RAWR=len(t1w)/len(D); RESR=len(t1w)/(len(D)-len(live))
for k,v in cands.items():
    need=1e9/v
    P(f"{k:<34}{v:>13,.0f}{need:>14,.0f}{need/RAWR:>14,.0f}{need/RESR:>17,.0f}")
P(f"\n  (last two columns = LEADS that must be worked to produce that many tier-1 wins)")
P(f"  tier-1 raw win rate {100*RAWR:.3f}%   tier-1 resolved win rate {100*RESR:.3f}%")
P("")
MED=st.median(wt1)
P("SCENARIOS TO 1,000,000,000 LoC (tier-1):")
P(f"{'scenario':<40}{'LoC/week':>13}{'weeks':>8}{'years':>7}{'companies':>11}{'x universe':>12}")
per_co=st.median(ct)
for nm,rate in [("current tier-1 run-rate (8.6M)",sum(loct1.values())/(span/7)),
                ("closing-weeks mean (13.95M)",st.mean([loct1[k] for k in cwk])),
                ("target 15M/wk",15e6),("target 20M/wk",20e6),("target 30M/wk",30e6),("CEO pace 50M/wk",50e6)]:
    w_=1e9/rate; co=1e9/per_co
    P(f"{nm:<40}{rate:>13,.0f}{w_:>8,.0f}{w_/52:>7.1f}{co:>11,.0f}{co/12000:>11.1f}x")
P(f"\n*** CEILING: if we worked 100% of a 12,000-company universe at the observed")
P(f"    tier-1 resolved win rate of {100*RESR:.2f}%, we would win {12000*RESR:,.0f} companies")
P(f"    x {per_co:,.0f} median tier-1 LoC = {12000*RESR*per_co:,.0f} LoC")
P(f"    = {100*12000*RESR*per_co/1e9:.1f}% of the 1 BILLION target ***")
P(f"\n    To reach 1Bn from a 12,000-company universe you would need EITHER")
P(f"      win rate of {100*(1e9/per_co)/12000:.1f}% (vs {100*RESR:.2f}% observed = {(1e9/per_co)/12000/RESR:.0f}x better), OR")
P(f"      {1e9/(12000*RESR):,.0f} LoC per win (vs {per_co:,.0f} observed = {(1e9/(12000*RESR))/per_co:.0f}x bigger)")

H("8. WEEKLY TARGET DERIVATION (leads x conversion x LoC per win)")
P(f"{'leads worked/wk':>16}{'win rate':>11}{'LoC/win':>13}{'weekly tier-1 LoC':>20}")
for L in [357,500,700,1000,1500,2000]:
    for r,rl in [(RAWR,"raw 0.42%"),(RESR,"resolved 0.72%")]:
        P(f"{L:>16}{rl:>11}{MED:>13,.0f}{L*r*MED:>20,.0f}")
P(f"\nCurrent actual: {st.mean([cw[w] for w in wks]):.0f} leads/wk x {100*RESR:.2f}% x {MED:,.0f} = {st.mean([cw[w] for w in wks])*RESR*MED:,.0f} LoC/wk")
P(f"To hit 15M/wk you need {15e6/(RESR*MED):,.0f} leads/week worked")
P(f"To hit 20M/wk you need {20e6/(RESR*MED):,.0f} leads/week worked")
P(f"At {st.mean([cw[w] for w in wks]):.0f} leads/wk current supply, universe of 12,000 lasts {12000/st.mean([cw[w] for w in wks]):.0f} weeks = {12000/st.mean([cw[w] for w in wks])/52:.1f} years")
P(f"At 1,500 leads/wk, universe of 12,000 lasts {12000/1500:.0f} weeks = {12000/1500/52:.2f} years -> then it is GONE")

open(os.path.join(HERE,"ANALYSIS_ALL_NUMBERS.txt"),"w",encoding="utf-8").write("\n".join(OUT))
print("\n\nwrote ANALYSIS_ALL_NUMBERS.txt")
