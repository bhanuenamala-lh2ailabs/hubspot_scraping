# -*- coding: utf-8 -*-
"""Standalone watcher: fires a push batch the instant 10 unpushed PASS leads accumulate.

Runs independently of search_runner.py — just polls searchq_state.json / searchq_pushed.json
every POLL_S seconds and pushes whenever the unpushed-PASS count hits the threshold, using the
same batches-of-10-alternating-Yuktha/Lamiya logic as every manual push this session.

Usage: python3 auto_push.py [--threshold 10] [--poll 30]
"""
import os, sys, json, time, re, collections, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ARG = sys.argv
def opt(n, d):
    return ARG[ARG.index(n)+1] if n in ARG and ARG.index(n)+1 < len(ARG) else d
THRESHOLD = int(opt("--threshold", "10"))
POLL_S = float(opt("--poll", "30"))
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

_ns = {"__file__": os.path.join(HERE, "searchq_enrich.py")}
exec(compile(open(_ns["__file__"], encoding="utf-8").read().split("def main()")[0], "sqe", "exec"), _ns)
hs = _ns["hs"]; deals_by_domain = _ns["deals_by_domain"]; NAME = _ns["NAME"]
find_existing_deal = _ns["find_existing_deal"]
YUKTHA, LAMIYA = _ns["YUKTHA"], _ns["LAMIYA"]; PIPE, COLD, TAG = _ns["PIPE"], _ns["COLD"], _ns["TAG"]
STATE, PUSHED = _ns["STATE"], _ns["PUSHED"]


def log(msg):
    print(f"[{datetime.datetime.now(IST).strftime('%H:%M:%S')}] {msg}", flush=True)


def push_batch(ready, dmap, nmap):
    done = json.load(open(PUSHED))
    new_idx = sum(1 for v in done.values() if v.get("mode") == "new")
    new = upd = fail = 0
    for v in ready:
        parts = (v["person"] or "").split()
        existing = find_existing_deal(v["domain"], v["company"], dmap, nmap)
        if existing and existing.get("owner") in NAME:
            owner = existing["owner"]
        else:
            owner = YUKTHA if (new_idx // 10) % 2 == 0 else LAMIYA
        cp = {"firstname": parts[0] if parts else "", "lastname": " ".join(parts[1:]),
              "email": v.get("email") or "", "phone": v["phone"], "mobilephone": v["phone"],
              "jobtitle": v.get("title") or "Director", "company": v["company"],
              "linkedin_url": v.get("linkedin") or "", "country": "India",
              "website": f"https://{v['domain']}" if v.get("domain") else ""}
        s, d = hs("/crm/v3/objects/contacts", "POST", {"properties": {k: x for k, x in cp.items() if x}})
        if s not in (200, 201):
            blob = str(d.get("message") or d.get("raw") or d)
            if s == 409 and "Existing ID" in blob:
                m = re.search(r"Existing ID: (\d+)", blob); ctid = m.group(1) if m else None
            else:
                fail += 1; log(f"   FAIL contact {v['company'][:26]} http{s}"); continue
        else:
            ctid = d["id"]
        if existing:
            hs(f'/crm/v4/objects/deals/{existing["deal"]}/associations/default/contacts/{ctid}', "PUT")
            hs(f'/crm/v3/objects/deals/{existing["deal"]}', "PATCH",
               {"properties": {"description": f'FOUNDER FOUND via searchByQuery: {v["person"]} ({v.get("title","")}) {v["phone"]}'}})
            done[v["domain"]] = {"deal": existing["deal"], "owner": NAME.get(existing["owner"], "?"),
                                 "person": v["person"], "phone": v["phone"], "email": v.get("email", ""), "mode": "updated"}
            upd += 1
            log(f"   UPDATED {v['company'][:28]:<30}{v['person'][:20]} -> kept owner ({NAME.get(existing['owner'],'?')})")
        else:
            dp = {"dealname": v["company"], "pipeline": PIPE, "dealstage": COLD, "hubspot_owner_id": owner,
                  "poc": owner, "lead_source": TAG, "source_tab": "searchq", "lh2_domain": v["domain"],
                  "description": f'{v["person"]} ({v.get("title","")}) via searchByQuery; rank {v["rank"]} score {v["score"]}'}
            s2, d2 = hs("/crm/v3/objects/deals", "POST", {"properties": dp})
            if s2 not in (200, 201):
                dp.pop("description", None); s2, d2 = hs("/crm/v3/objects/deals", "POST", {"properties": dp})
                if s2 not in (200, 201): fail += 1; log(f"   FAIL deal {v['company'][:26]} http{s2}"); continue
            hs(f'/crm/v4/objects/deals/{d2["id"]}/associations/default/contacts/{ctid}', "PUT")
            new_idx += 1
            done[v["domain"]] = {"deal": d2["id"], "owner": NAME[owner], "person": v["person"],
                                 "phone": v["phone"], "email": v.get("email", ""), "mode": "new"}
            new += 1
            log(f"   NEW [{new_idx}] block{(new_idx-1)//10}={NAME[owner]:<8}{v['company'][:26]:<28}{v['person'][:18]}")
        json.dump(done, open(PUSHED, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    c2 = collections.Counter(v["owner"] for v in done.values())
    log(f"batch done: new {new}, updated {upd}, failed {fail} | totals -> Yuktha {c2['Yuktha']}, Lamiya {c2['Lamiya']}")


def main():
    log(f"auto_push armed: threshold={THRESHOLD}, poll={POLL_S}s")
    while True:
        try:
            state = json.load(open(STATE)) if os.path.exists(STATE) else {}
            done = json.load(open(PUSHED)) if os.path.exists(PUSHED) else {}
            ready = [v for v in state.values() if v.get("gate") == "PASS" and v["domain"] not in done]
            if len(ready) >= THRESHOLD:
                ready.sort(key=lambda v: int(v["rank"]))
                log(f"threshold hit: {len(ready)} unpushed PASS leads -> pushing now")
                dmap, nmap = deals_by_domain()
                push_batch(ready, dmap, nmap)
        except Exception as e:
            log(f"!! error this cycle (will retry next poll): {type(e).__name__}: {str(e)[:150]}")
        time.sleep(POLL_S)


if __name__ == "__main__":
    main()
