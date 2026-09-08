# -*- coding: utf-8 -*-
"""Resolve founders for NET-NEW gate-pass IT-services firms by scraping their own website
+ Claude extraction (no SignalHire, no numbers, no search quota). Build a 500-row LinkedIn CSV.
Resumable: checkpoints resolved founders to it_founders_resolved.json."""
import os, sqlite3, json, re, csv, urllib.request, urllib.error, time
HERE=os.path.dirname(os.path.abspath(__file__)); HUB=os.path.dirname(os.path.dirname(HERE))
env={l.split('=',1)[0].strip().lower():l.split('=',1)[1].strip() for l in open(os.path.join(HUB,'.env'),encoding='utf-8-sig') if '=' in l and not l.strip().startswith('#')}
ANT=env["anthropic_api_key"]; UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
def norm(n): return re.sub(r"\s+"," ",re.sub(r"[^a-z0-9 ]","",(n or "").lower())).strip()
def clean(s): return re.sub(r"\s+"," ",str(s or "").replace("\n"," ").replace("\r"," ")).strip()
def get(url,t=8):
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":UA}),timeout=t) as r: return r.read()
    except Exception: return b""
def site_text(dom):
    txt=""
    for path in ("","/about","/about-us","/team","/leadership","/company","/our-team"):
        for sch in ("https://","http://"):
            b=get(sch+dom+path)
            if b and len(b)>300:
                h=b.decode("utf-8","ignore")
                h=re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>"," ",h)
                h=re.sub(r"(?s)<[^>]+>"," ",h); h=re.sub(r"&[a-z#0-9]+;"," ",h)
                txt+=" "+re.sub(r"\s+"," ",h).strip()
                break
        if len(txt)>4000: break
    return txt[:4500]
def claude_founder(company, text):
    if not text or len(text)<80: return "",""
    prompt=(f"Company: {company}\nWebsite text:\n{text[:4000]}\n\n"
            "From this company's own website, identify its FOUNDER, Co-Founder, CEO, Owner, or Managing Director "
            "(a real person's full name). Return ONLY minified JSON: {\"name\":\"<full name or empty>\",\"title\":\"<their title>\"}. "
            "If no clear founder/leader person is named, return {\"name\":\"\",\"title\":\"\"}.")
    body=json.dumps({"model":"claude-haiku-4-5-20251001","max_tokens":120,"messages":[{"role":"user","content":prompt}]}).encode()
    req=urllib.request.Request("https://api.anthropic.com/v1/messages",data=body,method="POST",headers={"x-api-key":ANT,"anthropic-version":"2023-06-01","content-type":"application/json"})
    for a in range(3):
        try:
            with urllib.request.urlopen(req,timeout=45) as r: d=json.loads(r.read().decode())
            t="".join(c.get("text","") for c in d.get("content",[])); m=re.search(r"\{.*\}",t,re.S)
            if not m: return "",""
            j=json.loads(m.group(0)); return clean(j.get("name")), clean(j.get("title"))
        except urllib.error.HTTPError as e:
            if e.code in (429,529,503) and a<2: time.sleep(3*(a+1)); continue
            return "",""
        except Exception:
            if a<2: time.sleep(2); continue
            return "",""
    return "",""

# --- net-new gate-pass companies WITHOUT a founder yet ---
db=sqlite3.connect(os.path.join(HUB,"lh2-pipeline","data","pipeline.sqlite")); db.row_factory=sqlite3.Row
have_dom=set(p["domain"].lower() for p in db.execute("SELECT DISTINCT domain FROM people WHERE name IS NOT NULL AND name!=''") if p["domain"])
by_nm=json.load(open(os.path.join(HUB,"crm_mirror","data","index","by_name.json"),encoding="utf-8"))
by_dom=json.load(open(os.path.join(HUB,"crm_mirror","data","index","by_domain.json"),encoding="utf-8"))
pushed=set(r["domain"] for r in json.load(open(os.path.join(HERE,"pushed_itservices.json"),encoding="utf-8")))
comps=[c for c in db.execute("SELECT domain,company_name,city FROM companies WHERE gate_pass=1")
       if (c["domain"] or "").lower() not in have_dom
       and (c["domain"] or "").lower() not in by_dom and (c["domain"] or "").lower() not in pushed
       and norm(c["company_name"]) not in by_nm]
print(f"net-new gate-pass firms needing a founder: {len(comps)}", flush=True)
CK=os.path.join(HERE,"it_founders_resolved.json")
done=json.load(open(CK,encoding="utf-8")) if os.path.exists(CK) else {}
TARGET_NEW=420   # + the 113 already-have -> ~500 net-new
for i,c in enumerate(comps):
    if sum(1 for v in done.values() if v.get("name"))>=TARGET_NEW: break
    dom=(c["domain"] or "").lower()
    if dom in done: continue
    nm,title=claude_founder(clean(c["company_name"]), site_text(dom))
    done[dom]={"company":clean(c["company_name"]),"name":nm if len(nm.split())>=2 else "","title":title or "Founder"}
    if (i+1)%20==0:
        json.dump(done,open(CK,"w",encoding="utf-8"),ensure_ascii=False)
        print(f"  [{i+1}/{len(comps)}] resolved-with-name={sum(1 for v in done.values() if v.get('name'))}", flush=True)
    time.sleep(0.1)
json.dump(done,open(CK,"w",encoding="utf-8"),ensure_ascii=False)
print(f"DONE resolving. net-new founders found this pass: {sum(1 for v in done.values() if v.get('name'))}", flush=True)
