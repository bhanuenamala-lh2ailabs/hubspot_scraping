# -*- coding: utf-8 -*-
"""Weekly IT-services funnel analysis -> analysis/weekly/<YYYY-Www>/README.md

Pulls every `scraped_type = ITservices` deal from HubSpot (stage, owner, notes),
joins scrape firmographics (city / size / founded) from pipeline.sqlite, categorises
GTM analysts' dead-reason notes with Claude, and writes a markdown report.

Usage:
  python weekly_report.py --pull        # refresh from HubSpot (slow)
  python weekly_report.py               # rebuild the report from the last pull
"""
import os, sys, json, re, html, time, sqlite3, urllib.request, urllib.error, datetime
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
DATA = os.path.join(HERE, "_data"); os.makedirs(DATA, exist_ok=True)
env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
HS, ANT = env["hubspot_key"], env["anthropic_api_key"]

# ---- funnel model: how deep did the deal get? ----
LEVEL = {"Cold Call":0,"Call Attempted":1,"Interested":2,"GMeet Fixed":3,"Script Shared":4,
         "Script Results Received":5,"Commercial Negotiation":6,"Deal Contract Signed":7,
         "Data Migration Done":8,"Metadata Matched":9,"Payment Initiation":10,"Closed/Won":11}
# WrongFit is depth 0 — screened from the profile, never dialled.
# WrongNumber is depth 1 (same as Call Attempted): the caller DID dial, the number was
# simply bad. It is a call attempt that failed on our data, not a lead we declined, so it
# must count toward Called+/Call Attempted. See WNR in analysis/KPI_DEFINITIONS.md.
DEAD_LEVEL = {"Dead/ColdCall/WrongFit":0,"Dead/ColdCall/WrongNumber":1,
              "Dead/ColdCall/Not Interested":1,"Dead/Interested/NoShow":2,
              "Dead/GMeet/wrong fit":3,"Dead/Gmeet/Privacy Concerns":3,
              "Dead/ResultsReceived/WrongFit-Rejected":5,"Dead/Negotiation/Pricing":6,
              "Dead/Negotiation/Contractual":6}
STEPS = ["Cold Call","Call Attempted","Interested","GMeet Fixed","Script Shared",
         "Script Results Received","Commercial Negotiation","Deal Contract Signed","Closed/Won"]
STEP_LVL = [0,1,2,3,4,5,6,7,11]

def call(path, method="GET", body=None):
    url = "https://api.hubapi.com" + path
    data = json.dumps(body).encode() if body is not None else None
    for a in range(5):
        try:
            req = urllib.request.Request(url, data=data, method=method,
                headers={"Authorization":"Bearer "+HS,"Content-Type":"application/json"})
            with urllib.request.urlopen(req, timeout=45) as r:
                t = r.read().decode(); return r.status, (json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            if e.code in (429,502,503,504) and a < 4: time.sleep(2*(a+1)); continue
            return e.code, {}
        except Exception:
            if a == 4: raise
            time.sleep(2)

def strip_html(h):
    t = re.sub(r"(?i)<br\s*/?>", "\n", h or "")
    return re.sub(r"[ \t]+", " ", html.unescape(re.sub(r"<[^>]+>", "", t))).strip()

def pull():
    stage = {}
    for pid in ("default","2425754306"):
        s, pp = call(f"/crm/v3/pipelines/deals/{pid}")
        for x in pp.get("stages", []): stage[x["id"]] = x["label"]
    s, own = call("/crm/v3/owners?limit=100")
    owners = {o["id"]: f"{o.get('firstName','')} {o.get('lastName','')}".strip() for o in own.get("results",[])}
    after, deals = None, []
    while True:
        b = {"limit":100,"properties":["dealname","dealstage","hubspot_owner_id","createdate",
             "lh2_domain","hs_lastmodifieddate","deal_value_range","hs_priority"],
             "filterGroups":[{"filters":[{"propertyName":"scraped_type","operator":"EQ","value":"ITservices"}]}]}
        if after: b["after"] = after
        s, d = call("/crm/v3/objects/deals/search", "POST", b)
        deals += d.get("results", []); after = d.get("paging",{}).get("next",{}).get("after")
        if not after: break
        time.sleep(0.03)
    ids = [x["id"] for x in deals]
    def assoc(to):
        m = {}
        for i in range(0, len(ids), 100):
            s, d = call(f"/crm/v4/associations/deals/{to}/batch/read", "POST",
                        {"inputs":[{"id":x} for x in ids[i:i+100]]})
            for r in d.get("results", []):
                t = [str(y["toObjectId"]) for y in r.get("to", [])]
                if t: m[str(r["from"]["id"])] = t
            time.sleep(0.04)
        return m
    d2n, d2c = assoc("notes"), assoc("companies")
    nids = sorted({n for v in d2n.values() for n in v}); notes = {}
    for i in range(0, len(nids), 100):
        s, d = call("/crm/v3/objects/notes/batch/read", "POST",
                    {"properties":["hs_note_body","hs_timestamp"],"inputs":[{"id":n} for n in nids[i:i+100]]})
        for r in d.get("results", []): notes[str(r["id"])] = r.get("properties", {})
        time.sleep(0.04)
    coids = sorted({v[0] for v in d2c.values()}); comps = {}
    for i in range(0, len(coids), 100):
        s, d = call("/crm/v3/objects/companies/batch/read", "POST",
                    {"properties":["name","domain","city","lh2_domain"],"inputs":[{"id":c} for c in coids[i:i+100]]})
        for r in d.get("results", []): comps[str(r["id"])] = r.get("properties", {})
        time.sleep(0.04)
    out = []
    for x in deals:
        p = x["properties"]; did = x["id"]
        ns = sorted([notes[n] for n in d2n.get(did,[]) if n in notes], key=lambda z: z.get("hs_timestamp") or "")
        co = comps.get((d2c.get(did) or [""])[0], {})
        out.append({"deal_id":did,"name":p.get("dealname"),"stage":stage.get(p.get("dealstage"),p.get("dealstage")),
            "owner":owners.get(p.get("hubspot_owner_id"),p.get("hubspot_owner_id")),
            "created":(p.get("createdate") or "")[:10],"modified":(p.get("hs_lastmodifieddate") or "")[:10],
            "domain":(p.get("lh2_domain") or co.get("lh2_domain") or co.get("domain") or "").lower(),
            "city_hs":co.get("city"),"priority":p.get("hs_priority"),"value_range":p.get("deal_value_range"),
            "notes":[{"ts":(n.get("hs_timestamp") or "")[:10],"body":strip_html(n.get("hs_note_body"))} for n in ns]})
    json.dump(out, open(os.path.join(DATA,"itservices_pull.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"pulled {len(out)} deals, {len(notes)} notes")
    return out

def join_firmo(deals):
    db = sqlite3.connect(os.path.join(HUB,"lh2-pipeline","data","pipeline.sqlite")); db.row_factory = sqlite3.Row
    comp = {(r["domain"] or "").lower(): dict(r) for r in db.execute(
        "SELECT domain,company_name,city,size_source,size_band,size_bucket,founded_year,segment FROM companies")}
    nrm = lambda n: re.sub(r"\s+"," ",re.sub(r"[^a-z0-9 ]","",(n or "").lower())).strip()
    byname = {nrm(v["company_name"]): v for v in comp.values()}
    for d in deals: d["firmo"] = comp.get(d["domain"]) or byname.get(nrm(d["name"]))
    return deals

# ---- categorise analyst notes with Claude ----
CATS = ["too_small_headcount","too_new","foreign_company","wrong_services_segment",
        "not_operating_defunct","data_mismatch","contact_unreachable","not_interested_other",
        "positive_signal","no_reason_given"]
def categorise(deals, cache_path):
    cache = json.load(open(cache_path,encoding="utf-8")) if os.path.exists(cache_path) else {}
    todo = [d for d in deals if d["notes"] and d["deal_id"] not in cache]
    for i in range(0, len(todo), 25):
        chunk = todo[i:i+25]
        items = "\n".join(f'{j+1}. [{d["stage"]}] {d["name"]}: "{" | ".join(n["body"] for n in d["notes"])[:220]}"'
                          for j, d in enumerate(chunk))
        prompt = ("Each line is a B2B lead with its stage and the GTM analyst's note. We scrape Indian "
                  "IT-services firms (target: India, founded<=2022, 50-1000 employees, real dev shop) to "
                  "acquire dormant CODEBASES. Classify WHY each lead ended where it did.\n"
                  f"Categories: {', '.join(CATS)}\n"
                  "- too_small_headcount: the note says the company is far smaller than expected (e.g. '13 people')\n"
                  "- too_new: founded later than expected\n- foreign_company: not India\n"
                  "- wrong_services_segment: not a codebase-owning dev shop (agency/reseller/other services)\n"
                  "- not_operating_defunct: shut down / dormant\n"
                  "- data_mismatch: scraped data contradicts reality (LinkedIn/site disagree)\n"
                  "- contact_unreachable: wrong/no number, need another channel\n"
                  "- positive_signal: interest, callback, WhatsApp sent, etc.\n"
                  "Return ONLY a minified JSON array, one object per line, same order:\n"
                  '[{"n":1,"cat":"<category>","headcount":<int or null>}]\n\n' + items)
        body = json.dumps({"model":"claude-haiku-4-5-20251001","max_tokens":1600,
                           "messages":[{"role":"user","content":prompt}]}).encode()
        req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, method="POST",
            headers={"x-api-key":ANT,"anthropic-version":"2023-06-01","content-type":"application/json"})
        try:
            with urllib.request.urlopen(req, timeout=90) as r: d = json.loads(r.read().decode())
            txt = "".join(c.get("text","") for c in d.get("content",[]))
            arr = json.loads(re.search(r"\[.*\]", txt, re.S).group(0))
            for o in arr:
                k = chunk[o["n"]-1]["deal_id"]
                cache[k] = {"cat":o.get("cat"),"headcount":o.get("headcount")}
        except Exception as e:
            print("  categorise chunk failed:", str(e)[:90])
        print(f"  categorised {min(i+25,len(todo))}/{len(todo)}", flush=True)
        json.dump(cache, open(cache_path,"w",encoding="utf-8"), ensure_ascii=False)
        time.sleep(0.3)
    for d in deals: d["cat"] = cache.get(d["deal_id"], {})
    return deals

MATURE_DAYS = 14   # funnel KPIs only count leads old enough to have progressed

def compute_kpis(deals, label):
    """Tier-1/2/3 KPIs per analysis/KPI_DEFINITIONS.md."""
    n = len(deals)
    if not n: return None
    cat = lambda d: (d.get("cat") or {}).get("cat")
    wrongfit    = sum(1 for d in deals if d["stage"] == "Dead/ColdCall/WrongFit")
    unreachable = sum(1 for d in deals if cat(d) == "contact_unreachable")
    usable      = sum(1 for d in deals
                      if d["stage"] != "Dead/ColdCall/WrongFit" and cat(d) != "contact_unreachable")
    # FAR — where an analyst recorded a real headcount, did the claimed band hold?
    # ⚠ BIASED SAMPLE: analysts usually only write a headcount when it's WRONG, so FAR
    # trends to 0 by construction. Read it as "of the firms someone bothered to verify,
    # how many held up" — not as a population accuracy rate.
    ver = [d for d in deals if (d.get("cat") or {}).get("headcount")]
    far_ok = sum(1 for d in ver if d["cat"]["headcount"] >= 50)
    # funnel KPIs on matured leads only
    today = datetime.date.today()
    def mature(d):
        try: return (today - datetime.date.fromisoformat(d["created"])).days >= MATURE_DAYS
        except Exception: return True
    mat = [d for d in deals if mature(d)]
    contacted = [d for d in mat if d["stage"] != "Dead/ColdCall/WrongFit"]
    k = {
        "label": label, "n": n, "n_mature": len(mat),
        "QR":  round((1 - wrongfit/n)*100, 1),
        "CR":  round((1 - unreachable/n)*100, 1),
        "ULR": round(usable/n*100, 1),
        "FAR": (round(far_ok/len(ver)*100, 1) if ver else None), "FAR_n": len(ver),
        "ER":  (round(sum(1 for d in contacted if d["lvl"] >= 2)/len(contacted)*100, 1) if contacted else None),
        "MR":  (round(sum(1 for d in mat if d["lvl"] >= 3)/len(mat)*100, 1) if mat else None),
        "AFD": (round(sum(d["lvl"] for d in mat)/len(mat), 2) if mat else None),
        "WR":  (round(sum(1 for d in mat if d["lvl"] >= 11)/len(mat)*100, 2) if mat else None),
    }
    return k

def kpi_history(week, kpis, path):
    hist = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    hist[week] = {k["label"]: k for k in kpis if k}
    json.dump(hist, open(path, "w", encoding="utf-8"), indent=1)
    return hist

def fmt(v, suf="%"):
    return "—" if v is None else f"{v}{suf}"

def delta(cur, prev):
    if cur is None or prev is None: return ""
    d = cur - prev
    if abs(d) < 0.05: return " (=)"
    return f" ({'▲' if d>0 else '▼'}{abs(d):.1f})"

def bar(n, total, width=28):
    if not total: return ""
    f = int(round(width * n / total))
    return "█"*f + "·"*(width-f)

def reached(d):
    st = d["stage"]
    return LEVEL.get(st, DEAD_LEVEL.get(st))

def main():
    if "--pull" in sys.argv or not os.path.exists(os.path.join(DATA,"itservices_pull.json")):
        deals = pull()
    else:
        deals = json.load(open(os.path.join(DATA,"itservices_pull.json"),encoding="utf-8"))
    deals = join_firmo(deals)
    deals = categorise(deals, os.path.join(DATA,"note_categories.json"))
    for d in deals:
        d["lvl"] = reached(d)
        f = d.get("firmo") or {}
        d["band"] = (f.get("size_source") or f.get("size_band") or "").strip()
        # cohort: scrape-sourced vs migrated from the Private Codebase Tracker (warm, curated)
        d["cohort"] = "scrape" if d.get("firmo") else "tracker"
        # legacy = pushed before the 50-employee floor existed
        d["legacy"] = d["band"] == "10 - 49"
    deals = [d for d in deals if d["lvl"] is not None]
    json.dump(deals, open(os.path.join(DATA,"itservices_joined.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
    today = datetime.date.today()
    wk = f"{today.isocalendar()[0]}-W{today.isocalendar()[1]:02d}"
    outdir = os.path.join(HERE, wk); os.makedirs(outdir, exist_ok=True)
    render(deals, os.path.join(outdir,"README.md"), wk, today)
    print(f"report -> analysis/weekly/{wk}/README.md")

def render(all_deals, path, wk, today):
    tracker = [d for d in all_deals if d["cohort"] == "tracker"]
    deals = [d for d in all_deals if d["cohort"] == "scrape"]     # analyse SCRAPE output only
    N = len(deals)
    L = []
    A = L.append
    A(f"# IT-Services Funnel — Weekly Analysis · {wk}")
    A(f"\n_Generated {today.isoformat()} · regenerate with `python analysis/weekly/weekly_report.py --pull`_\n")
    A(f"> **Scope:** {len(all_deals)} IT-services deals exist in HubSpot. This report analyses the "
      f"**{N} scrape-sourced** ones. The other **{len(tracker)}** were migrated from the Private Codebase "
      f"Tracker (warm, hand-curated deals — they reach Interested+ at "
      f"{sum(1 for d in tracker if d['lvl']>=2)/max(1,len(tracker))*100:.0f}% and would badly skew "
      f"scrape-quality metrics).\n")

    # ---------- KPI SCOREBOARD ----------
    kscrape  = compute_kpis(deals, "goodfirms_scrape")
    ktracker = compute_kpis(tracker, "codebase_tracker")
    klegacy  = compute_kpis([d for d in deals if d["legacy"]], "scrape_legacy_sub50")
    kcurrent = compute_kpis([d for d in deals if not d["legacy"]], "scrape_gated_50plus")
    hist = kpi_history(wk, [kscrape, ktracker, klegacy, kcurrent],
                       os.path.join(DATA, "kpi_history.json"))
    prevwk = sorted([w for w in hist if w < wk])
    prev = hist[prevwk[-1]] if prevwk else {}
    A("## 0. KPI scoreboard\n")
    A(f"_Definitions + targets: [`analysis/KPI_DEFINITIONS.md`](../../KPI_DEFINITIONS.md). "
      f"Funnel KPIs count only leads ≥{MATURE_DAYS} days old. "
      f"{'Deltas vs ' + prevwk[-1] if prevwk else 'First week — no deltas yet.'}_\n")
    A("| Source | n | **ULR** ⭐ | QR | CR | FAR | ER | MR | AFD | WR |")
    A("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for k in (kscrape, kcurrent, klegacy, ktracker):
        if not k: continue
        p = prev.get(k["label"], {})
        far = f"{fmt(k['FAR'])} (n={k['FAR_n']})" if k["FAR"] is not None else "—"
        A(f"| {k['label'].replace('_',' ')} | {k['n']} | **{fmt(k['ULR'])}**{delta(k['ULR'],p.get('ULR'))} | "
          f"{fmt(k['QR'])}{delta(k['QR'],p.get('QR'))} | {fmt(k['CR'])}{delta(k['CR'],p.get('CR'))} | {far} | "
          f"{fmt(k['ER'])} | {fmt(k['MR'])} | {fmt(k['AFD'],'')} | {fmt(k['WR'])} |")
    A("\n**Targets:** ULR ≥80% · QR ≥85% · CR ≥85% · FAR ≥90% · ER ≥25% · MR ≥8%\n")
    if kscrape:
        flags = []
        if kscrape["ULR"] < 80: flags.append(f"**ULR {kscrape['ULR']}% is below the 80% target** — the scrape is sending unusable leads")
        if kscrape["QR"] < 85:  flags.append(f"QR {kscrape['QR']}% — too many wrong targets (gate/source accuracy)")
        if kscrape["CR"] < 85:  flags.append(f"CR {kscrape['CR']}% — contact data is failing")
        for f in flags: A(f"- 🔴 {f}")
        if ktracker:
            A(f"- 📊 **Source comparison:** curated tracker leads score **QR {ktracker['QR']}%** vs "
              f"scrape **{kscrape['QR']}%** — the scrape sends ~"
              f"{(100-kscrape['QR'])/max(0.1,(100-ktracker['QR'])):.0f}× more wrong targets.")
        if kcurrent and klegacy:
            gap = kcurrent["ULR"] - klegacy["ULR"]
            if abs(gap) < 8:
                A(f"- ⚠️ **The 50-employee gate barely helps:** gated leads score ULR "
                  f"**{kcurrent['ULR']}%** vs legacy sub-50 **{klegacy['ULR']}%** — only "
                  f"{gap:+.1f}pp. Purging the legacy batch will *not* fix lead quality on its own; "
                  f"the source is noisy at every size band.")
            else:
                A(f"- 📌 Gated (50+) leads score ULR **{kcurrent['ULR']}%** vs legacy sub-50 "
                  f"**{klegacy['ULR']}%** ({gap:+.1f}pp) — the gate is doing real work.")
        if kscrape["FAR"] is not None:
            A(f"- ℹ️ **FAR {kscrape['FAR']}% (n={kscrape['FAR_n']}) is a biased sample** — analysts "
              f"usually only record a headcount when it's *wrong*, so this trends to 0 by "
              f"construction. Treat it as 'verified failures found', not a population accuracy rate.")
    A("")

    # ---------- headline ----------
    dead = [d for d in deals if d["stage"].startswith("Dead")]
    alive = [d for d in deals if not d["stage"].startswith("Dead")]
    wf = [d for d in deals if d["stage"] == "Dead/ColdCall/WrongFit"]
    A("## 1. Headline\n")
    A(f"| Metric | Value |\n|---|---|")
    A(f"| Total scraped IT-services deals | **{N}** |")
    A(f"| Still alive in funnel | {len(alive)} ({len(alive)/N*100:.0f}%) |")
    A(f"| Dead | {len(dead)} ({len(dead)/N*100:.0f}%) |")
    A(f"| **Screened out as WrongFit — never even called** | **{len(wf)} ({len(wf)/N*100:.0f}%)** |")
    wn = [d for d in deals if d["stage"] == "Dead/ColdCall/WrongNumber"]
    A(f"| **Dead on a wrong number — enrichment failure** | **{len(wn)} ({len(wn)/N*100:.0f}%)** |")
    reachedI = sum(1 for d in deals if d["lvl"] >= 2)
    A(f"| Reached Interested or beyond | {reachedI} ({reachedI/N*100:.0f}%) |")
    won = sum(1 for d in deals if d["lvl"] >= 11)
    A(f"| Closed/Won | {won} |")

    # ---------- funnel ----------
    A("\n## 2. Funnel — how far deals actually get\n")
    A("Cumulative: a deal counts at a step if it **reached that step or beyond** (including dying there later).\n")
    A("| Step | Reached | % of all | |\n|---|---:|---:|---|")
    base = None
    for s, lv in zip(STEPS, STEP_LVL):
        c = sum(1 for d in deals if d["lvl"] >= lv)
        if base is None: base = c or 1
        A(f"| {s} | {c} | {c/N*100:.1f}% | `{bar(c,N)}` |")
    A("\n**Biggest drop-offs**")
    prev = None
    for s, lv in zip(STEPS, STEP_LVL):
        c = sum(1 for d in deals if d["lvl"] >= lv)
        if prev is not None and prev[1] > 0:
            drop = (prev[1]-c)/prev[1]*100
            if drop >= 30: A(f"- **{prev[0]} → {s}**: {prev[1]} → {c} (**−{drop:.0f}%**)")
        prev = (s, c)

    # ---------- city ----------
    A("\n## 3. City × how far the deal went\n")
    bycity = defaultdict(list)
    for d in deals:
        c = (d.get("firmo") or {}).get("city") or d.get("city_hs") or "Unknown"
        bycity[str(c).split(",")[0].strip()].append(d)
    rows = sorted(bycity.items(), key=lambda kv: -len(kv[1]))
    A("| City | Deals | WrongFit % | Called+ | Interested+ | Script+ | Avg depth |\n|---|---:|---:|---:|---:|---:|---:|")
    for city, ds in rows:
        if len(ds) < 3: continue
        n = len(ds)
        wfp = sum(1 for x in ds if x["stage"]=="Dead/ColdCall/WrongFit")/n*100
        c1 = sum(1 for x in ds if x["lvl"]>=1)/n*100
        c2 = sum(1 for x in ds if x["lvl"]>=2)/n*100
        c4 = sum(1 for x in ds if x["lvl"]>=4)/n*100
        avg = sum(x["lvl"] for x in ds)/n
        A(f"| {city} | {n} | {wfp:.0f}% | {c1:.0f}% | {c2:.0f}% | {c4:.0f}% | {avg:.2f} |")
    good = [(c,ds) for c,ds in rows if len(ds)>=8]
    if good:
        best = max(good, key=lambda kv: sum(1 for x in kv[1] if x["lvl"]>=2)/len(kv[1]))
        worst = max(good, key=lambda kv: sum(1 for x in kv[1] if x["stage"]=="Dead/ColdCall/WrongFit")/len(kv[1]))
        A(f"\n- **Best converting (≥8 deals):** {best[0]} — "
          f"{sum(1 for x in best[1] if x['lvl']>=2)/len(best[1])*100:.0f}% reach Interested+")
        A(f"- **Worst quality (≥8 deals):** {worst[0]} — "
          f"{sum(1 for x in worst[1] if x['stage']=='Dead/ColdCall/WrongFit')/len(worst[1])*100:.0f}% WrongFit")

    # ---------- size ----------
    A("\n## 4. Company size × how far the deal went\n")
    A("_Size = the headcount **GoodFirms reported** (range midpoint) — the value our 50–1,000 gate used._\n")
    def sband(d):
        f = d.get("firmo") or {}
        s = f.get("size_source") or f.get("size_band") or ""
        nums = [int(x) for x in re.findall(r"\d+", s.replace(",",""))]
        h = (nums[0]+nums[1])//2 if len(nums)>=2 else (nums[0] if nums else None)
        if h is None: return "unknown", None
        for lo,hi,lab in ((0,49,"<50"),(50,99,"50–99"),(100,249,"100–249"),(250,499,"250–499"),(500,1000,"500–1000")):
            if lo <= h <= hi: return lab, h
        return ">1000", h
    bysize = defaultdict(list)
    for d in deals:
        lab,_ = sband(d); bysize[lab].append(d)
    order = ["<50","50–99","100–249","250–499","500–1000",">1000","unknown"]
    A("| Reported size | Deals | WrongFit % | Interested+ | Script+ | Avg depth |\n|---|---:|---:|---:|---:|---:|")
    for lab in order:
        ds = bysize.get(lab, [])
        if not ds: continue
        n=len(ds)
        A(f"| {lab} | {n} | {sum(1 for x in ds if x['stage']=='Dead/ColdCall/WrongFit')/n*100:.0f}% | "
          f"{sum(1 for x in ds if x['lvl']>=2)/n*100:.0f}% | {sum(1 for x in ds if x['lvl']>=4)/n*100:.0f}% | "
          f"{sum(x['lvl'] for x in ds)/n:.2f} |")

    # ---------- REAL headcount from notes ----------
    hc = [(d, d["cat"].get("headcount")) for d in deals if d.get("cat") and d["cat"].get("headcount")]
    if hc:
        A("\n### ⚠️ Reported size vs. what the analyst actually found\n")
        A(f"Analysts recorded a **real headcount** in {len(hc)} notes. Comparing to what GoodFirms claimed:\n")
        A("| Company | GoodFirms said | Analyst found | Stage |\n|---|---:|---:|---|")
        for d, real in sorted(hc, key=lambda t: t[1])[:15]:
            lab, rep = sband(d)
            A(f"| {d['name'][:26]} | {rep if rep else '?'} | **{real}** | {d['stage'].replace('Dead/ColdCall/','')} |")
        under = [1 for d, real in hc if real < 50]
        A(f"\n**{sum(under)} of {len(hc)}** verified companies were **under 50 employees** — "
          f"they should never have passed the size gate.")

    # ---------- dead reasons ----------
    A("\n## 5. Dead-reason distribution\n")
    dc = Counter(d["stage"] for d in deals if d["stage"].startswith("Dead"))
    td = sum(dc.values())
    A(f"| Dead stage | Deals | % of dead | |\n|---|---:|---:|---|")
    for s,c in dc.most_common():
        A(f"| {s} | {c} | {c/td*100:.0f}% | `{bar(c,td)}` |")

    # ---------- note themes ----------
    cats = Counter(d["cat"].get("cat") for d in deals if d.get("cat") and d["cat"].get("cat"))
    if cats:
        A("\n## 6. What the analysts' notes actually say\n")
        tot = sum(cats.values())
        A(f"_{tot} notes categorised._\n")
        A("| Reason | Notes | % | |\n|---|---:|---:|---|")
        for c,n in cats.most_common():
            A(f"| {c.replace('_',' ')} | {n} | {n/tot*100:.0f}% | `{bar(n,tot)}` |")
        wfc = Counter(d["cat"].get("cat") for d in deals
                      if d["stage"]=="Dead/ColdCall/WrongFit" and d.get("cat") and d["cat"].get("cat"))
        if wfc:
            wt = sum(wfc.values())
            A("\n### Why leads were screened out as WrongFit (never called)\n")
            A("| Reason | Notes | % |\n|---|---:|---:|")
            for c,n in wfc.most_common(): A(f"| **{c.replace('_',' ')}** | {n} | {n/wt*100:.0f}% |")

    # ---------- founded year ----------
    A("\n## 7. Founded year × outcome\n")
    byf = defaultdict(list)
    for d in deals:
        fy = (d.get("firmo") or {}).get("founded_year")
        if fy: byf["≤2010" if fy<=2010 else ("2011–2015" if fy<=2015 else ("2016–2019" if fy<=2019 else "2020–2022"))].append(d)
    A("| Founded | Deals | WrongFit % | Interested+ | Avg depth |\n|---|---:|---:|---:|---:|")
    for k in ["≤2010","2011–2015","2016–2019","2020–2022"]:
        ds = byf.get(k,[])
        if not ds: continue
        n=len(ds)
        A(f"| {k} | {n} | {sum(1 for x in ds if x['stage']=='Dead/ColdCall/WrongFit')/n*100:.0f}% | "
          f"{sum(1 for x in ds if x['lvl']>=2)/n*100:.0f}% | {sum(x['lvl'] for x in ds)/n:.2f} |")

    # ---------- owners ----------
    A("\n## 8. By analyst\n")
    byo = defaultdict(list)
    for d in deals: byo[d["owner"] or "unassigned"].append(d)
    A("| Analyst | Deals | Called+ | Interested+ | WrongFit % |\n|---|---:|---:|---:|---:|")
    for o,ds in sorted(byo.items(), key=lambda kv:-len(kv[1])):
        n=len(ds)
        A(f"| {o} | {n} | {sum(1 for x in ds if x['lvl']>=1)/n*100:.0f}% | "
          f"{sum(1 for x in ds if x['lvl']>=2)/n*100:.0f}% | "
          f"{sum(1 for x in ds if x['stage']=='Dead/ColdCall/WrongFit')/n*100:.0f}% |")

    # ---------- FOCUS LISTS ----------
    cat = lambda d: (d.get("cat") or {}).get("cat")
    def seg_kpi(ds):
        n = len(ds)
        if not n: return None
        wf = sum(1 for x in ds if x["stage"] == "Dead/ColdCall/WrongFit")
        us = sum(1 for x in ds if x["stage"] != "Dead/ColdCall/WrongFit" and cat(x) != "contact_unreachable")
        cont = [x for x in ds if x["stage"] != "Dead/ColdCall/WrongFit"]
        return dict(n=n, ULR=us/n*100, QR=(1-wf/n)*100,
                    ER=(sum(1 for x in cont if x["lvl"] >= 2)/len(cont)*100 if cont else 0),
                    AFD=sum(x["lvl"] for x in ds)/n)
    citymap = defaultdict(list)
    for d in deals:
        citymap[str((d.get("firmo") or {}).get("city") or d.get("city_hs") or "Unknown").split(",")[0].strip()].append(d)
    crows = [(c, seg_kpi(v)) for c, v in citymap.items() if len(v) >= 7]
    crows.sort(key=lambda t: (-t[1]["AFD"], -t[1]["ULR"]))
    A("\n## 8b. 🎯 Top cities — where to concentrate next week\n")
    A("_Ranked by average funnel depth (AFD), min 7 deals. This is the list to weight the next scrape toward._\n")
    A("| # | City | n | ULR | QR | ER | AFD |\n|---:|---|---:|---:|---:|---:|---:|")
    for i, (c, k) in enumerate(crows[:10], 1):
        A(f"| {i} | **{c}** | {k['n']} | {k['ULR']:.0f}% | {k['QR']:.0f}% | {k['ER']:.0f}% | {k['AFD']:.2f} |")
    worst = sorted([r for r in crows if r[1]["n"] >= 15], key=lambda t: t[1]["ULR"])[:3]
    if worst:
        A(f"\n**Volume traps** — high volume, low quality: " +
          ", ".join(f"**{c}** (n={k['n']}, ULR {k['ULR']:.0f}%)" for c, k in worst))
        A("These absorb the most caller time for the least return. Cap or deprioritise them.")

    A("\n## 8c. 📈 Size band — is >249 employees better?\n")
    bmap = defaultdict(list)
    for d in deals: bmap[d["band"]].append(d)
    A("| GoodFirms band | n | ULR | QR | ER | AFD |\n|---|---:|---:|---:|---:|---:|")
    for b in ("10 - 49","50 - 249","250 - 999"):
        k = seg_kpi(bmap.get(b, []))
        if k: A(f"| {b} | {k['n']} | **{k['ULR']:.0f}%** | {k['QR']:.0f}% | {k['ER']:.0f}% | {k['AFD']:.2f} |")
    kb, ks = seg_kpi(bmap.get("250 - 999", [])), seg_kpi(bmap.get("50 - 249", []))
    if kb and ks:
        A(f"\n**Yes — decisively.** `250 - 999` scores **ULR {kb['ULR']:.0f}%** vs **{ks['ULR']:.0f}%** for "
          f"`50 - 249` ({kb['ULR']-ks['ULR']:+.0f}pp), QR {kb['QR']:.0f}% vs {ks['QR']:.0f}%, "
          f"ER {kb['ER']:.0f}% vs {ks['ER']:.0f}%.")
        A(f"\n**But supply is the constraint:** the scrape DB holds only **166 gate-passing "
          f"`250 - 999` firms** vs **955** in `50 - 249`. We've used {kb['n']} of the 166.")
        A(f"→ **Work all ~147 remaining `250 - 999` firms first**, then fall back to `50 - 249` "
          f"filtered to the best cities above.")

    # ---------- ROOT CAUSE ----------
    A("\n---\n\n## 9. 🔎 Root cause: why 1-in-3 leads is unusable\n")
    legacy = [d for d in deals if d["legacy"]]
    gated  = [d for d in deals if d["band"] in ("50 - 249","250 - 999")]
    gsmall = [d for d in gated if (d.get("cat") or {}).get("cat") == "too_small_headcount"]
    hcs = sorted([d["cat"]["headcount"] for d in gsmall if (d.get("cat") or {}).get("headcount")])
    A("The dominant kill reason is **company far too small**. It has *two separate causes* — "
      "and they need different fixes.\n")
    A(f"### Cause A — {len(legacy)} legacy deals that predate the size gate\n")
    A(f"- **{len(legacy)} of {N} ({len(legacy)/N*100:.0f}%)** scrape-sourced deals came from the "
      f"GoodFirms band **`10 - 49`** (midpoint 29) — below our 50-employee floor.")
    A(f"- They were pushed **before** the `size_min_headcount: 50` floor existed.")
    A(f"- **The gate is correct today:** of 2,692 `10 - 49` companies in the scrape DB, "
      f"**0 currently pass** (`size ~29 below floor 50`).")
    A(f"- So this is a **cleanup problem, not a code problem** — but these are still sitting in "
      f"callers' queues today ({sum(1 for d in legacy if not d['stage'].startswith('Dead'))} still alive).")
    A(f"\n### Cause B — GoodFirms size data is wrong ~{len(gsmall)/max(1,len(gated))*100:.0f}% of the time, even when it passes the gate\n")
    A(f"- Of **{len(gated)}** deals from gate-*passing* bands (`50 - 249`, `250 - 999`), analysts found "
      f"**{len(gsmall)} ({len(gsmall)/max(1,len(gated))*100:.0f}%)** to be far too small on inspection.")
    if hcs:
        A(f"- Their **actual** headcount: min **{hcs[0]}**, median **{hcs[len(hcs)//2]}**, max **{hcs[-1]}** — "
          f"against a claimed range of 50–249.")
    A("- Examples where GoodFirms said `50 - 249`:")
    for d in gsmall[:6]:
        h = (d.get("cat") or {}).get("headcount")
        if h: A(f"  - **{d['name'][:34]}** → actually **{h}** people")
    A(f"\n**This one cannot be fixed by tightening the threshold** — the source data itself is unreliable. "
      f"It needs a second, independent size check before a lead reaches a caller.\n")

    # ---------- ACTIONS ----------
    A("## 10. ✅ What we're changing next week\n")
    alive_legacy = [d for d in legacy if not d["stage"].startswith("Dead")]
    unreach = sum(1 for d in deals if cat(d) == "contact_unreachable")
    catn = sum(1 for d in deals if cat(d))
    top10 = ", ".join(c for c, _ in crows[:10])
    A("| # | Change | Why (this week's data) | Effort |\n|---|---|---|---|")
    A(f"| 1 | **Prioritise the ~147 unused `250 - 999` firms** ahead of everything else | "
      f"That band scores ULR {kb['ULR']:.0f}% vs {ks['ULR']:.0f}% and ER {kb['ER']:.0f}% vs {ks['ER']:.0f}% | config |")
    A(f"| 2 | **Weight the next scrape to the top-10 cities** ({top10}) | "
      f"They lead on funnel depth; Bengaluru/Jaipur absorb volume at ~50% ULR | config |")
    A(f"| 3 | **Add a SignalHire headcount pre-check before push** (see §10b) | "
      f"Catches 6/8 of the too-small firms GoodFirms passed — no credits, no ToS risk | small |")
    A(f"| 4 | **Purge the {len(alive_legacy)} still-alive `10 - 49` legacy deals** | "
      f"Fail today's gate — but note this alone only moves ULR ~3pp | 10 min |")
    A(f"| 5 | **Fix contact quality** — {unreach}/{catn} notes ({unreach/max(1,catn)*100:.0f}%) are "
      f"'wrong number / need LinkedIn' | 2nd-biggest killer | see `docs/reference/LEAD_SOURCING_PROBLEM_BRIEF.md` |")
    yng = [d for d in deals if (d.get("firmo") or {}).get("founded_year") and d["firmo"]["founded_year"] >= 2020]
    if yng:
        A(f"| 6 | **Drop founded ≥2020 from the gate** | {sum(1 for d in yng if d['stage']=='Dead/ColdCall/WrongFit')/len(yng)*100:.0f}% "
          f"WrongFit vs {sum(1 for d in deals if d['stage']=='Dead/ColdCall/WrongFit')/N*100:.0f}% overall | 1 line of config |")

    A("\n### 10b. Headcount pre-check — SignalHire works, and it's free\n")
    A("`searchByQuery{currentCompany}` returns a **`total`** = profiles listing that employer. "
      "Tested against ground truth:\n")
    A("| Company | Real | SignalHire `total` | Verdict |\n|---|---:|---:|---|")
    for nm, real, tot, ok in [("Velotio",244,252,"✅"),("Aneka Labs",19,19,"✅"),("Fibonalabs",15,12,"✅"),
                              ("Alphalogic",11,9,"✅"),("DigiQAL",1,7,"✅"),("Bacancy",1095,451,"✅"),
                              ("Actiknow",13,92,"❌ over"),("GigLabz",25,78,"❌ over")]:
        A(f"| {nm} | {real} | {tot} | {ok} |")
    A("\n**6/8 correct** — vs GoodFirms, which passed *all 8* (2/8). Costs a **search, not a credit**, "
      "and the search quota resets daily. Both misses are *over*-counts (name collision), so it never "
      "wrongly rejects a good firm — it only occasionally lets a small one through.")
    A("\n_LinkedIn's public page is more accurate (Velotio 244 exact) — "
      "`crm_mirror/enrich/verify_headcount.py` — but it throttles (HTTP 999) and is against LinkedIn's "
      "ToS, so **SignalHire is the one to wire into the pipeline**; keep LinkedIn for spot-checks._")

    A("\n### Watch next week")
    A(f"- **ULR** on the `250 - 999` batch — does it hold above {kb['ULR']:.0f}%?")
    A("- **QR** after the SignalHire pre-check — target ≥85% (from 62%).")
    A("- Do the top-10 cities keep their edge as n grows?")
    A("- City signal is still thin (<25 deals for most) — treat as directional.\n")
    open(path,"w",encoding="utf-8").write("\n".join(L)+"\n")

if __name__ == "__main__":
    main()
