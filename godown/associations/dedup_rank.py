# -*- coding: utf-8 -*-
"""Dedup the association scrape against every pool we already hold, then rank what is new."""
import os, re, csv, json, collections
HERE=os.path.dirname(os.path.abspath(__file__)); HUB=os.path.dirname(os.path.dirname(HERE))
PQ=os.path.join(HUB,"godown","prequal","prequal_out")
def rd(p):
    try:
        with open(p,encoding="utf-8-sig") as f: return list(csv.DictReader(f))
    except Exception: return []
def norm_dom(d):
    d=(d or "").lower().strip().rstrip("/")
    d=re.sub(r"^www\.","",d)
    return d
def norm_name(s):
    s=(s or "").lower()
    s=re.sub(r"\b(pvt|private|limited|ltd|inc|llp|llc|co|company|technologies|technology|solutions|"
             r"services|software|systems|india|group|consulting|labs|infotech|it)\b"," ",s)
    return re.sub(r"[^a-z0-9]","",s)
raw=rd(os.path.join(HERE,"assoc_members_raw.csv"))
print(f"raw rows {len(raw)}")
# ---- 1. dedup within the scrape ----
seen={}
for r in raw:
    d=norm_dom(r["domain"]); k=d or ("name:"+norm_name(r["name"]))
    if not k or k=="name:": continue
    if k in seen:
        if r["source"] not in seen[k]["sources"]: seen[k]["sources"].append(r["source"])
        if len(r["name"])>len(seen[k]["name"]): seen[k]["name"]=r["name"]
    else:
        seen[k]={"name":r["name"],"domain":d,"sources":[r["source"]],"sector":r.get("sector",""),"city":r.get("city","")}
uniq=list(seen.values())
print(f"after intra-scrape dedup: {len(uniq)}")
# ---- 2. dedup against our existing pools ----
have_dom=set(); have_name=set()
for f in ("survivors.csv","reserve.csv","enrich_queue.csv","whales.csv","rejects.csv"):
    for r in rd(os.path.join(PQ,f)):
        have_dom.add(norm_dom(r.get("domain"))); have_name.add(norm_name(r.get("name")))
for f in ("nasscom_candidates_ALL.csv","nasscom_members.csv"):
    for r in rd(os.path.join(HUB,"godown","nasscom",f)):
        have_dom.add(norm_dom(r.get("domain") or r.get("website"))); have_name.add(norm_name(r.get("name")))
try:
    for r in rd(os.path.join(HUB,"godown","ceo_reality_check","DEALS_FULL.csv")):
        have_dom.add(norm_dom(r.get("lh2_domain"))); have_name.add(norm_name(r.get("dealname")))
except Exception: pass
have_dom.discard(""); have_name.discard("")
new=[]; dup=[]
for u in uniq:
    if (u["domain"] and u["domain"] in have_dom) or norm_name(u["name"]) in have_name: dup.append(u)
    else: new.append(u)
print(f"already in our pools : {len(dup)}")
print(f"GENUINELY NEW        : {len(new)}")
# ---- 3. ICP filter ----
GIANT=re.compile(r"\b(accenture|adobe|infosys|wipro|tcs|tata|cognizant|capgemini|deloitte|ibm|hcl|"
                 r"tech mahindra|oracle|microsoft|amazon|google|sap|dell|cisco|intel|qualcomm|"
                 r"airtel|reliance|birla|hsbc|adp|genpact|concentrix|teleperformance|hexaware|"
                 r"mphasis|ltimindtree|persistent|zensar|virtusa|ust global|nagarro|thoughtworks)\b",re.I)
NONICP=re.compile(r"\b(bank|insurance|pharma|hospital|university|college|school|institute|foundation|"
                  r"chamber|association|ministry|logistics|realty|hotel|restaurant|travel)\b",re.I)
for n in new:
    n["flag"]=("giant" if GIANT.search(n["name"]) else
               "non-icp" if NONICP.search(n["name"]) else
               "no-domain" if not n["domain"] else "ok")
icp=[n for n in new if n["flag"]=="ok"]
print(f"  giants excluded    : {sum(1 for n in new if n['flag']=='giant')}")
print(f"  non-ICP excluded   : {sum(1 for n in new if n['flag']=='non-icp')}")
print(f"  no domain          : {sum(1 for n in new if n['flag']=='no-domain')}")
print(f"  ICP-CLEAN NEW      : {len(icp)}")
# ---- 4. preliminary rank ----
# We do NOT have the prequal signals (owned_ip / pre2024 / repo hits) for these yet — those need
# the crawl. Rank on what we can see now, and mark them for the prequal pipeline.
SRCW={"GESIA":3,"HYSEA":3,"ITAAP":3,"GTECH":3,"DSCI":1}
for n in icp:
    s=0
    s+=sum(SRCW.get(x,1) for x in n["sources"])          # multi-association membership = stronger
    s+=4 if len(n["sources"])>1 else 0
    d=n["domain"]
    s+=3 if d.endswith((".in",".co.in")) else 0           # India-registered
    s+=2 if re.search(r"(soft|tech|info|data|cloud|digital|labs|code|web|app|sys)",d,re.I) else 0
    n["prelim_score"]=s
icp.sort(key=lambda x:(-x["prelim_score"],x["name"]))
for i,n in enumerate(icp,1): n["rank"]=i
with open(os.path.join(HERE,"assoc_ranked.csv"),"w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=["rank","prelim_score","name","domain","sources","sector","city","flag"])
    w.writeheader()
    for n in icp: w.writerow({**n,"sources":"+".join(n["sources"])})
with open(os.path.join(HERE,"assoc_excluded.csv"),"w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=["name","domain","sources","flag"]); w.writeheader()
    for n in new:
        if n["flag"]!="ok": w.writerow({"name":n["name"],"domain":n["domain"],"sources":"+".join(n["sources"]),"flag":n["flag"]})
print(f"\nwrote assoc_ranked.csv ({len(icp)}) and assoc_excluded.csv")
print("\nby source (new & ICP-clean):",dict(collections.Counter(s for n in icp for s in n["sources"])))
print("multi-association members:",sum(1 for n in icp if len(n["sources"])>1))
print("\ntop 15:")
for n in icp[:15]: print(f"  {n['rank']:>3} [{n['prelim_score']:>2}] {n['name'][:44]:<46}{n['domain']:<30}{'+'.join(n['sources'])}")
