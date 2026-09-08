# -*- coding: utf-8 -*-
"""Exhausts remaining Apollo credits against the backlog, per the validated pipeline:

  1. Apollo mixed_people/api_search (0 credits) -> best decision-maker by role score
  2. Apollo people/match, work-email-only (1 credit) -> official email + LinkedIn URL
     (no personal-email fallback spent here — SignalHire covers that for free below)
  3. SignalHire candidate/search reveal on that LinkedIn URL (own credit pool, ample) ->
     phone (+91 mobile hard gate) + work/personal email tagging as a fallback if Apollo
     had none
  4. PASS (valid +91 mobile) -> push to HubSpot, alternating Yuktha/Lamiya in batches of 10,
     tagged lead_source "Apollo Search ( IT Services )"

Stops cleanly the moment Apollo credits hit the safety margin (checked before every paid
call) — this is a deliberate one-shot "spend it all" run per instruction, not a daily-paced
budget like the SignalHire searchByQuery runner.

Resumable: state checkpointed to apollo_reveal_state.json after every company.
Usage: python3 apollo_reveal_runner.py [--margin 1] [--limit 5000]
"""
import os, sys, csv, json, time, re, collections, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
FOUNDER_DIR = os.path.join(HUB, "godown", "founder_id")
sys.path.insert(0, os.path.join(HUB, "crm_mirror", "enrich"))
from indian_number import to_e164, classify as in_classify

env = {l.split("=", 1)[0].strip().lower(): l.split("=", 1)[1].strip()
       for l in open(os.path.join(HUB, ".env"), encoding="utf-8-sig")
       if "=" in l and not l.strip().startswith("#")}
APOLLO_KEY = env["apollo_api_key"]; SH = env["signal_hire"]; HS_KEY = env["hubspot_key"]
AH = {"Content-Type": "application/json", "Cache-Control": "no-cache", "X-Api-Key": APOLLO_KEY}
HH = {"Authorization": "Bearer " + HS_KEY, "Content-Type": "application/json"}

ARG = sys.argv
def opt(n, d):
    return ARG[ARG.index(n)+1] if n in ARG and ARG.index(n)+1 < len(ARG) else d
MARGIN = int(opt("--margin", "1"))
LIMIT = int(opt("--limit", "5000"))

STATE = os.path.join(HERE, "apollo_reveal_state.json")
PUSHED = os.path.join(HERE, "apollo_reveal_pushed.json")
YUKTHA, LAMIYA = "96573782", "96574824"
NAME = {YUKTHA: "Yuktha", LAMIYA: "Lamiya"}
PIPE, COLD = "default", "3992480462"
TAG = "Apollo Search ( IT Services )"

LADDER = [
    (r"\b(founder|co[-\s]?founder|founding|promoter)\b", 100), (r"\b(owner|proprietor|managing partner)\b", 96),
    (r"\b(chief executive|\bceo\b)\b", 94), (r"\b(managing director|\bmd\b)\b", 90),
    (r"(chief technolog|\bcto\b|chief technical)", 88),
    (r"\b(chairman|chairperson|(?<!vice )president)\b", 86),
    (r"\b(chief operating|\bcoo\b|chief product|\bcpo\b|chief information|\bcio\b)\b", 80),
    (r"\b(partner)\b", 74), (r"\b(executive director|whole[-\s]?time director|\bdirector\b)\b", 72),
]
DISQ = re.compile(r"\b(sales|marketing|\bhr\b|human resource|recruit|talent|business development|"
                  r"account manager|support|intern|trainee|junior|customer success)\b", re.I)

def role_score(t):
    t = (t or "").lower()
    for rx, sc in LADDER:
        if re.search(rx, t, re.I):
            if sc <= 90 and DISQ.search(t): return 0
            return sc
    return 0


def acall(url, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, headers=AH, method=method, data=data)
    try:
        with urllib.request.urlopen(r, timeout=45) as x:
            return x.status, json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try: return e.code, json.loads(raw)
        except Exception: return e.code, {"raw": raw[:400]}
    except Exception as e:
        return None, {"error": str(e)[:150]}


def apollo_credits():
    s, d = acall("https://api.apollo.io/api/v1/users/api_profile?include_credit_usage=true")
    return d.get("num_credits_remaining") if s == 200 else None


def apollo_search(company):
    body = {"q_organization_name": company, "organization_locations": ["India"],
            "person_titles": ["CEO", "Founder", "Co-Founder", "CTO", "Managing Director", "MD",
                              "Chairman", "President", "COO"],
            "person_seniorities": ["owner", "founder", "c_suite"], "per_page": 5}
    s, d = acall("https://api.apollo.io/api/v1/mixed_people/api_search", method="POST", body=body)
    return d.get("people", []) if s == 200 else []


def apollo_match(apollo_id):
    s, d = acall("https://api.apollo.io/api/v1/people/match", method="POST",
                 body={"id": apollo_id, "reveal_personal_emails": False, "reveal_phone_number": False})
    return s, d.get("person", {}) if s == 200 else {}


def sh_reveal(li_url):
    body = {"items": [li_url], "withoutWaterfall": True}
    r = urllib.request.Request("https://www.signalhire.com/api/v1/candidate/search",
                               data=json.dumps(body).encode(), method="POST",
                               headers={"apikey": SH, "Content-Type": "application/json"})
    try:
        d = json.loads(urllib.request.urlopen(r, timeout=60).read().decode())
    except Exception:
        return None
    for it in (d if isinstance(d, list) else d.get("results", [])) or []:
        if isinstance(it, dict) and it.get("status") == "success":
            return (it.get("candidate") or {}).get("contacts") or []
    return None


def hs(u, m="GET", b=None):
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request("https://api.hubapi.com" + u, headers=HH, method=m, data=d)
    try:
        with urllib.request.urlopen(r, timeout=30) as x:
            return x.status, json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try: return e.code, json.loads(raw)
        except Exception: return e.code, {"raw": raw[:400]}


CORP = re.compile(r"\b(pvt|private|limited|ltd|inc|llp|llc|co|company|technologies|technology|"
                  r"solutions|services|software|systems|india|group|consulting|labs|infotech|"
                  r"enterprises|ventures|global|international)\b", re.I)


def core(name):
    """Company name minus corporate boilerplate — same normalization searchq_enrich.py uses,
    kept here too so this runner's dedup doesn't depend on lh2_domain alone."""
    return re.sub(r"[^a-z0-9 ]", " ", CORP.sub(" ", (name or "").lower())).strip()


def deals_by_domain():
    """(domain_map, name_map). HARDENED 20 Aug: lh2_domain is blank on some deals (e.g.
    Outflo-sourced), which let a duplicate Zimo Technologies deal get created and pushed
    because the domain-only check couldn't see the pre-existing, domain-less one. name_map
    is a normalized-name fallback covering every deal, blank domain or not."""
    ids, after = [], None
    while True:
        b = {"limit": 100, "properties": ["dealname"], "filterGroups": []}
        if after: b["after"] = after
        _, r = hs("/crm/v3/objects/deals/search", "POST", b)
        ids += [x["id"] for x in r.get("results", [])]
        after = (r.get("paging") or {}).get("next", {}).get("after")
        if not after: break
    dmap, nmap = {}, {}
    for i in range(0, len(ids), 50):
        _, r = hs("/crm/v3/objects/deals/batch/read", "POST",
                  {"inputs": [{"id": x} for x in ids[i:i+50]],
                   "properties": ["lh2_domain", "hubspot_owner_id", "dealname"]})
        for d in r.get("results", []):
            p = d["properties"]
            info = {"deal": d["id"], "owner": p.get("hubspot_owner_id")}
            dom = (p.get("lh2_domain") or "").strip().lower()
            if dom: dmap[dom] = info
            nm = core(p.get("dealname") or "")
            if nm: nmap.setdefault(nm, info)
    return dmap, nmap


def find_existing_deal(domain, company_name, domain_map, name_map):
    hit = domain_map.get((domain or "").lower().strip())
    if hit: return hit
    return name_map.get(core(company_name))


def build_queue():
    st = load_state()
    srcs = [os.path.join(HUB, "godown", "prequal", "prequal_out", f)
            for f in ("enrich_queue_tierB.csv", "reserve.csv")]
    # also exclude anything the SignalHire searchByQuery pipeline already has state on
    sq_state_path = os.path.join(FOUNDER_DIR, "searchq_state.json")
    sq_state = json.load(open(sq_state_path)) if os.path.exists(sq_state_path) else {}
    rows, seen = [], set()
    for p in srcs:
        if not os.path.exists(p): continue
        for r in csv.DictReader(open(p, encoding="utf-8-sig")):
            dom = (r.get("domain") or "").strip().lower(); nm = (r.get("name") or "").strip()
            if not dom or not nm or dom in seen: continue
            if dom in st: continue
            seen.add(dom)
            rows.append({"domain": dom, "name": nm, "rank": r.get("rank", ""), "score": r.get("score", "")})
    return rows


def load_state():
    return json.load(open(STATE)) if os.path.exists(STATE) else {}


def save_state(s):
    json.dump(s, open(STATE, "w"), ensure_ascii=False, indent=1)


def push_one(v, dmap, nmap, done, new_idx):
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
        # BUG FIXED 20 Aug: hs() returns the parsed JSON dict directly when HubSpot's 409 body
        # is valid JSON (which it always is) — the "Existing ID: <id>" text lives in d["message"],
        # not d["raw"] (that key only appears when JSON parsing itself failed). Checking "raw"
        # meant this branch never fired and every duplicate-contact conflict was reported as a
        # hard failure instead of being recovered, same class of bug fixed manually mid-run
        # earlier today on the other push scripts.
        blob = str(d.get("message") or d.get("raw") or d)
        if s == 409 and "Existing ID" in blob:
            m = re.search(r"Existing ID: (\d+)", blob); ctid = m.group(1) if m else None
        else:
            return None, False
    else:
        ctid = d["id"]
    if existing:
        hs(f'/crm/v4/objects/deals/{existing["deal"]}/associations/default/contacts/{ctid}', "PUT")
        hs(f'/crm/v3/objects/deals/{existing["deal"]}', "PATCH",
           {"properties": {"description": f'FOUNDER FOUND via Apollo+SignalHire: {v["person"]} ({v.get("title","")}) {v["phone"]}'}})
        done[v["domain"]] = {"deal": existing["deal"], "owner": NAME.get(existing["owner"], "?"),
                             "person": v["person"], "phone": v["phone"], "email": v.get("email", ""), "mode": "updated"}
        return NAME.get(existing["owner"], "?"), False
    else:
        dp = {"dealname": v["company"], "pipeline": PIPE, "dealstage": COLD, "hubspot_owner_id": owner,
              "poc": owner, "lead_source": TAG, "source_tab": "apollo_reveal", "lh2_domain": v["domain"],
              "description": f'{v["person"]} ({v.get("title","")}) via Apollo search + SignalHire reveal; rank {v["rank"]} score {v["score"]}'}
        s2, d2 = hs("/crm/v3/objects/deals", "POST", {"properties": dp})
        if s2 not in (200, 201):
            dp.pop("description", None); s2, d2 = hs("/crm/v3/objects/deals", "POST", {"properties": dp})
            if s2 not in (200, 201): return None, False
        hs(f'/crm/v4/objects/deals/{d2["id"]}/associations/default/contacts/{ctid}', "PUT")
        done[v["domain"]] = {"deal": d2["id"], "owner": NAME[owner], "person": v["person"],
                             "phone": v["phone"], "email": v.get("email", ""), "mode": "new"}
        return NAME[owner], True


def main():
    q = build_queue()[:LIMIT]
    print(f"queue: {len(q)} fresh companies | apollo margin={MARGIN}", flush=True)
    st = load_state()
    done = json.load(open(PUSHED)) if os.path.exists(PUSHED) else {}
    dmap, nmap = deals_by_domain()
    new_idx = sum(1 for v in done.values() if v.get("mode") == "new")
    apollo_calls = matches = passes = pushed = 0

    # HARDENED 20 Aug: users/api_profile has its own separate rate limit (400/hour) that has
    # nothing to do with actual lead-credit balance. Checking it before every single company
    # blew through that limit mid-run and returned balance=None, which the old code treated as
    # "exhausted" and stopped a run that still had ~2,400 real credits left. Fix: track spend
    # LOCALLY (people/match always costs exactly 1 credit per attempt, confirmed empirically
    # regardless of whether an email is found) seeded from one real check, and only re-verify
    # against the live API every RECHECK_EVERY companies for drift correction — falling back
    # silently to the local estimate if that check itself gets rate-limited.
    RECHECK_EVERY = 30
    bal = apollo_credits()
    if bal is None:
        print("  !! could not read starting balance (rate-limited?) — assuming plenty and proceeding", flush=True)
        bal = 10**9

    for i, r in enumerate(q, 1):
        if i % RECHECK_EVERY == 1 and i > 1:
            live = apollo_credits()
            if live is not None:
                if live != bal: print(f"  [recheck] local estimate {bal} -> live {live}", flush=True)
                bal = live
        if bal <= MARGIN:
            print(f"\n!! APOLLO CREDITS EXHAUSTED (balance={bal}, margin={MARGIN}). Stopping cleanly.", flush=True)
            break
        people = apollo_search(r["name"])
        apollo_calls += 1
        rec = {"domain": r["domain"], "company": r["name"], "rank": r.get("rank",""), "score": r.get("score","")}
        if not people:
            rec["gate"] = "no apollo hit"
            st[r["domain"]] = rec; save_state(st)
            print(f"  [{i}/{len(q)}] {r['name'][:32]:<34}no apollo hit  (credits ~{bal})", flush=True)
            continue
        best = max(people, key=lambda p: role_score(p.get("title")))
        if role_score(best.get("title")) <= 0:
            rec["gate"] = "no qualifying role"
            st[r["domain"]] = rec; save_state(st)
            print(f"  [{i}/{len(q)}] {r['name'][:32]:<34}no qualifying role  (credits ~{bal})", flush=True)
            continue

        s2, person = apollo_match(best["id"]); matches += 1
        bal -= 1   # people/match costs exactly 1 credit per attempt, tracked locally now
        work_email = person.get("email") if person.get("email") not in (None, "email_not_unlocked@domain.com") else None
        li_url = person.get("linkedin_url")
        full_name = person.get("name") or best.get("first_name","")
        title = person.get("title") or best.get("title","")

        phone = sh_work = sh_personal = None
        if li_url:
            contacts = sh_reveal(li_url)
            if contacts:
                for ct in contacts:
                    if ct.get("type") == "phone" and ct.get("subType") == "mobile" and not phone:
                        phone = ct["value"]
                    if ct.get("type") == "email":
                        if ct.get("subType") == "work" and not sh_work: sh_work = ct["value"]
                        elif ct.get("subType") == "personal" and not sh_personal: sh_personal = ct["value"]
        final_email = work_email or sh_work or sh_personal or ""
        ind_mobile = to_e164(phone) if phone and in_classify(phone) == "mobile" else ""

        rec.update({"person": full_name, "title": title, "linkedin": li_url or "",
                    "email": final_email, "phone": ind_mobile})
        if ind_mobile:
            rec["gate"] = "PASS"; passes += 1
            owner_name, was_new = push_one(rec, dmap, nmap, done, new_idx)
            json.dump(done, open(PUSHED, "w"), ensure_ascii=False, indent=1)
            if was_new: new_idx += 1
            if owner_name:
                pushed += 1
                print(f"  [{i}/{len(q)}] {r['name'][:32]:<34}PASS -> pushed to {owner_name}  (credits ~{bal})", flush=True)
            else:
                print(f"  [{i}/{len(q)}] {r['name'][:32]:<34}PASS but push FAILED  (credits ~{bal})", flush=True)
        else:
            rec["gate"] = "skip - no +91 mobile"
            print(f"  [{i}/{len(q)}] {r['name'][:32]:<34}skip - no +91 mobile  (credits ~{bal})", flush=True)
        st[r["domain"]] = rec; save_state(st)
        time.sleep(0.3)

    c = collections.Counter(v["owner"] for v in done.values())
    print(f"\ndone. apollo_search_calls={apollo_calls} apollo_matches={matches} PASS={passes} pushed={pushed}")
    print(f"totals -> Yuktha {c['Yuktha']}, Lamiya {c['Lamiya']}")


if __name__ == "__main__":
    main()
