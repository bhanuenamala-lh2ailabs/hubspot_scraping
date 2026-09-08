# -*- coding: utf-8 -*-
"""Deals Lamiya or Yuktha marked "relevant" in a note but that still have no dialable number.

They were asked to vet the no-phone queue and write the verdict as a HubSpot note rather than
reply by mail. This pulls those verdicts back out so the relevant ones can be enriched.

"not relevant" / "irrelevant" must be excluded BEFORE matching "relevant", otherwise every
rejection is read as an approval — the substring is inside its own negation.

Reports today's notes separately from older ones, because the ask was about today's pass, but
any older relevant-and-unreachable deal is the same enrichment job and should not be lost.
"""
import os, sys, re, json, time, html, datetime, collections, urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE); HUB=os.path.dirname(ROOT)
sys.path.insert(0, HERE)
from indian_number import to_e164, classify
env={l.split('=',1)[0].strip().lower():l.split('=',1)[1].strip() for l in open(os.path.join(HUB,'.env'),encoding='utf-8-sig') if '=' in l and not l.strip().startswith('#')}
H={"Authorization":"Bearer "+env["hubspot_key"],"Content-Type":"application/json"}
OW={"96574824":"Lamiya","96573782":"Yuktha"}
IST=datetime.timezone(datetime.timedelta(hours=5,minutes=30))
today=datetime.datetime.now(IST).date()

def hs(u,m="GET",b=None):
    """8 attempts, not 5 — this network has dropped TLS handshakes repeatedly today, and a
    batch read that dies two-thirds of the way through costs the whole run."""
    d=json.dumps(b).encode() if b is not None else None
    for a in range(8):
        try:
            r=urllib.request.Request("https://api.hubapi.com"+u,data=d,method=m,headers=H)
            with urllib.request.urlopen(r,timeout=60) as x:
                t=x.read().decode(); return x.status,(json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429,502,503,504) and a<7: time.sleep(2*(a+1)); continue
            return e.code,{"raw":e.read().decode()[:300]}
        except Exception as e:
            if a==7: raise
            print(f"   retry {a+1}/8 after {type(e).__name__}", file=sys.stderr)
            time.sleep(3*(a+1))

def plain(s):
    """Note bodies are HTML. Strip tags before matching, or <b>relevant</b> is missed."""
    return html.unescape(re.sub(r"<[^>]+>", " ", s or "")).strip()

NEG = re.compile(r"\b(not\s+relevant|non[-\s]?relevant|irrelevant|not\s+a\s+fit|no\s+fit)\b", re.I)
POS = re.compile(r"\brelevant\b", re.I)
def verdict(text):
    t=" ".join(text.split())
    if NEG.search(t): return "not relevant"
    if POS.search(t): return "relevant"
    return None

def ist_day(ts):
    try: return datetime.datetime.fromisoformat((ts or "").replace("Z","+00:00")).astimezone(IST).date()
    except Exception: return None

s,d=hs("/crm/v3/pipelines/deals"); LAB={x["id"]:x["label"] for p in d["results"] for x in p["stages"]}

# ---- their deals ----
deals={}; after=None
while True:
    b={"filterGroups":[{"filters":[{"propertyName":"hubspot_owner_id","operator":"IN","values":list(OW)}]}],
       "properties":["dealname","dealstage","lead_source","hubspot_owner_id"],"limit":200}
    if after: b["after"]=after
    s,dd=hs("/crm/v3/objects/deals/search","POST",b)
    for x in dd.get("results",[]): deals[x["id"]]=x["properties"]
    after=(dd.get("paging") or {}).get("next",{}).get("after")
    if not after: break
    time.sleep(0.12)
print(f"{len(deals)} deals owned by Lamiya + Yuktha")

# ---- notes on those deals ----
ids=list(deals); d2n={}
for i in range(0,len(ids),100):
    s,a=hs("/crm/v4/associations/deals/notes/batch/read","POST",{"inputs":[{"id":x} for x in ids[i:i+100]]})
    for res in (a.get("results") or []):
        d2n[str(res.get("from",{}).get("id"))]=[str(t["toObjectId"]) for t in res.get("to",[])]
    time.sleep(0.08)
nids=sorted({n for v in d2n.values() for n in v}); notes={}
for i in range(0,len(nids),100):
    s,r=hs("/crm/v3/objects/notes/batch/read","POST",
           {"properties":["hs_note_body","hs_timestamp","hubspot_owner_id","hs_createdate"],
            "inputs":[{"id":n} for n in nids[i:i+100]]})
    for x in (r.get("results") or []): notes[x["id"]]=x["properties"]
    time.sleep(0.08)
print(f"{len(notes)} notes on those deals")

# ---- contacts / phone ----
d2c={}
for i in range(0,len(ids),100):
    s,a=hs("/crm/v4/associations/deals/contacts/batch/read","POST",{"inputs":[{"id":x} for x in ids[i:i+100]]})
    for res in (a.get("results") or []):
        d2c[str(res.get("from",{}).get("id"))]=[str(t["toObjectId"]) for t in res.get("to",[])]
    time.sleep(0.08)
cids=sorted({c for v in d2c.values() for c in v}); cp={}
for i in range(0,len(cids),100):
    s,r=hs("/crm/v3/objects/contacts/batch/read","POST",
           {"properties":["firstname","lastname","email","phone","mobilephone","linkedin_url","jobtitle"],
            "inputs":[{"id":c} for c in cids[i:i+100]]})
    for x in (r.get("results") or []): cp[x["id"]]=x["properties"]
    time.sleep(0.08)

def dialable(did):
    for c in d2c.get(did,[]):
        p=cp.get(c,{})
        for v in (p.get("mobilephone"), p.get("phone")):
            e=to_e164(v)
            if e: return e
    return None

rows=[]
for did,nlist in d2n.items():
    if did not in deals: continue
    for nid in nlist:
        p=notes.get(nid)
        if not p: continue
        txt=plain(p.get("hs_note_body"))
        v=verdict(txt)
        if v != "relevant": continue
        day=ist_day(p.get("hs_timestamp") or p.get("hs_createdate"))
        rows.append({"deal":did,"name":deals[did].get("dealname") or "",
                     "who":OW.get(deals[did].get("hubspot_owner_id"),"?"),
                     "stage":LAB.get(deals[did].get("dealstage")),
                     "src":deals[did].get("lead_source") or "(untagged)",
                     "day":day,"note":" ".join(txt.split())[:150],
                     "phone":dialable(did),
                     "contacts":[cp.get(c,{}) for c in d2c.get(did,[])]})
# one row per deal, keeping the newest note
best={}
for r in rows:
    k=r["deal"]
    if k not in best or (r["day"] or datetime.date.min) > (best[k]["day"] or datetime.date.min): best[k]=r
rows=sorted(best.values(), key=lambda r:(r["day"] or datetime.date.min), reverse=True)

need=[r for r in rows if not r["phone"]]
have=[r for r in rows if r["phone"]]
print(f'\nnotes reading "relevant": {len(rows)} deals   ({len(need)} with NO number, {len(have)} already dialable)')
print("  today:", sum(1 for r in rows if r["day"]==today), " earlier:", sum(1 for r in rows if r["day"]!=today))
print("  by caller:", dict(collections.Counter(r["who"] for r in rows)))

print("\n" + "="*100)
print("NEEDS ENRICHMENT — marked relevant, no dialable +91")
print("="*100)
print(f"{'who':<8}{'day':<12}{'deal':<30}{'stage':<14}{'source':<34}contact")
for r in need:
    c=r["contacts"][0] if r["contacts"] else {}
    nm=((c.get("firstname") or "")+" "+(c.get("lastname") or "")).strip() or "(no contact)"
    li=(c.get("linkedin_url") or "").strip()
    print(f'{r["who"]:<8}{str(r["day"]):<12}{r["name"][:28]:<30}{(r["stage"] or "")[:12]:<14}{r["src"][:32]:<34}{nm[:22]}  {li[:46]}')
    print(f'{"":<8}note: {r["note"][:110]}')
json.dump([{k:v for k,v in r.items() if k!="contacts"} |
           {"contacts":[{kk:c.get(kk) for kk in ("firstname","lastname","email","linkedin_url","jobtitle")} for c in r["contacts"]]}
           for r in need],
          open(os.path.join(HERE,"relevant_needs_enrichment.json"),"w",encoding="utf-8"),
          ensure_ascii=False, indent=1, default=str)
print(f'\nwrote relevant_needs_enrichment.json — {len(need)} deals for SignalHire')
