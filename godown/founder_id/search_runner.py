# -*- coding: utf-8 -*-
"""Resumable searchByQuery runner with CLIENT-SIDE quota accounting.

The API tells us nothing about quota: no remaining-count endpoint, no counter in the 402 body,
no limit header, no Retry-After. So we keep our own ledger of every call and gate ourselves
BEFORE calling, rather than discovering the wall by hitting it and losing the run.

What we established empirically (18 Aug 2026) and this runner is built on:
  * The meter counts CALLS, not profiles. 86 calls returned 160 profiles; 24 of those calls
    returned zero profiles and still cost quota. => `size` is FREE, so we raise it 3 -> 10.
  * Reset arrived ~24h03m after exhaustion, not at a calendar boundary.
  * Volume before 402 was inconsistent (297 one cycle, 171 the next), which is what a ROLLING
    24h window looks like: calls age out individually, so a cycle beginning against a
    partly-full window recovers only part of the allowance.

CONFIRMED BY SIGNALHIRE SUPPORT (19 Aug 2026, in reply to SIGNALHIRE_QUOTA_PROBLEM.md):
  * 297/171 were against the OLD 300-calls/day cap (now explains the anomaly cleanly).
  * They raised us to 700 calls/day for free, as a courtesy.
  * There are TWO independent caps, either can trigger the 402:
      - 700 calls/day  (every call counts, even zero-result ones)
      - 2,000 profiles/day  (total candidates returned, tracked separately)
  * Confirmed rolling 24h window, per-call expiry (not a shared reset clock).
  * A $2,000/year upgrade exists for 1,200 calls/day — a commercial decision, not applied here.
  This runner now gates on BOTH caps and is calibrated to trust these numbers until a real 402
  proves otherwise (see on_402(), which only lowers whichever cap actually looks breached).

The reveal leg is NOT touched. reveal()/pick()/role_score() are loaded from searchq_enrich.py
verbatim so its credit accounting and behaviour are literally the same code.

Usage
  python3 search_runner.py --report
  python3 search_runner.py --limit 50 [--pace even|burst|asap] [--apply]
  python3 search_runner.py --experiment
"""
import os, re, sys, csv, json, time, math, sqlite3, datetime, collections
import requests

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))

# ----------------------------------------------------------------- 1. CONFIG
SEARCH_SIZE          = 5         # raised 19 Aug (2nd test, against the ACTUAL live queue segment
                                  # this runner draws from — Tier-B/reserve, not the earlier mixed
                                  # sample): size=3 averaged only 1.88 profiles/call live, size=5
                                  # averaged 2.72 (1.45x), projecting ~1,714 profiles/day at the full
                                  # 630 calls/day — still within the 1,800/day gated cap (~95%
                                  # utilization, tighter margin than size=3 but not exceeding it).
                                  # size=10 was re-confirmed unsafe on this same live sample: 3.72
                                  # avg -> 2,344/day, exceeding both the gated and hard profile caps.
ASSUMED_WINDOW_HOURS = 24.0
ASSUMED_CALL_BUDGET  = 700       # SignalHire support, 19 Aug 2026: raised from 300 -> 700/day, free courtesy
ASSUMED_PROFILE_BUDGET = 2000    # SignalHire support, 19 Aug 2026: independent cap, total profiles/day
SAFETY_MARGIN        = 0.9       # stop at 90% of assumed budget
MIN_INTERVAL_S       = 0.35
LEDGER   = os.path.join(HERE, "search_ledger.db")
CALIB    = os.path.join(HERE, "search_calibration.json")
RAW_LOG  = os.path.join(HERE, "searchq_raw_log.json")
STATE    = os.path.join(HERE, "searchq_state.json")
API      = "https://www.signalhire.com/api/v1/candidate/searchByQuery"

ARG = sys.argv
def flag(n): return n in ARG
def opt(n, d=None):
    return ARG[ARG.index(n) + 1] if n in ARG and ARG.index(n) + 1 < len(ARG) else d
PACE  = opt("--pace", "even")
LIMIT = int(opt("--limit", "0") or 0)
APPLY = flag("--apply")
RUN_ID = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S")

env = {l.split("=", 1)[0].strip().lower(): l.split("=", 1)[1].strip()
       for l in open(os.path.join(HUB, ".env"), encoding="utf-8-sig")
       if "=" in l and not l.strip().startswith("#")}
SH = env["signal_hire"]
HDR = {"apikey": SH, "Content-Type": "application/json"}

# reuse the reveal leg + role ladder verbatim (module runs main() at import, so exec the top half)
_ns = {"__file__": os.path.join(HERE, "searchq_enrich.py")}
exec(compile(open(_ns["__file__"], encoding="utf-8").read().split("def main()")[0], "sqe", "exec"), _ns)
reveal, pick, role_score = _ns["reveal"], _ns["pick"], _ns["role_score"]
to_e164, in_classify, TITLE_Q = _ns["to_e164"], _ns["in_classify"], _ns["TITLE_Q"]


# ----------------------------------------------------------------- 2. LEDGER
def led():
    c = sqlite3.connect(LEDGER)
    c.execute("""CREATE TABLE IF NOT EXISTS calls(
        id INTEGER PRIMARY KEY AUTOINCREMENT, ts_utc REAL, company TEXT, http_status INTEGER,
        profiles_returned INTEGER, size_used INTEGER, total_reported INTEGER, run_id TEXT)""")
    c.execute("CREATE TABLE IF NOT EXISTS events(ts_utc REAL, kind TEXT, note TEXT)")
    c.execute("CREATE INDEX IF NOT EXISTS ix_calls_ts ON calls(ts_utc)")
    c.commit(); return c


DB = led()


def ev(kind, note=""):
    DB.execute("INSERT INTO events VALUES(?,?,?)", (time.time(), kind, note)); DB.commit()
    print(f"    [event] {kind}: {note}", flush=True)


def log_call(company, status, profiles, total, size):
    DB.execute("INSERT INTO calls(ts_utc,company,http_status,profiles_returned,size_used,total_reported,run_id)"
               " VALUES(?,?,?,?,?,?,?)", (time.time(), company, status, profiles, size, total, RUN_ID))
    DB.commit()


def backfill():
    """Seed the ledger from the raw log so day-one accounting is not blind."""
    if DB.execute("SELECT COUNT(*) FROM calls").fetchone()[0]: return
    if not os.path.exists(RAW_LOG): print("  ledger empty and no raw log to backfill from"); return
    rows = json.load(open(RAW_LOG))
    # raw log has no timestamps; attribute them to the file mtime working backwards at MIN_INTERVAL
    t_end = os.path.getmtime(RAW_LOG)
    for i, r in enumerate(rows):
        ts = t_end - (len(rows) - i) * 1.0
        DB.execute("INSERT INTO calls(ts_utc,company,http_status,profiles_returned,size_used,total_reported,run_id)"
                   " VALUES(?,?,?,?,?,?,?)",
                   (ts, r.get("company", ""), 402 if r.get("err") == 402 else 200,
                    r.get("returned", 0), 3, r.get("total") or 0, "backfill"))
    DB.commit()
    ev("run_start", f"backfilled {len(rows)} calls from searchq_raw_log.json")
    print(f"  backfilled {len(rows)} historical calls into the ledger")


def calib():
    try:
        c = json.load(open(CALIB))
        c.setdefault("profile_budget", ASSUMED_PROFILE_BUDGET)   # older calibration files predate this cap
        return c
    except Exception:
        return {"call_budget": ASSUMED_CALL_BUDGET, "profile_budget": ASSUMED_PROFILE_BUDGET,
                "window_hours": ASSUMED_WINDOW_HOURS, "observations": []}


def save_calib(c): json.dump(c, open(CALIB, "w"), indent=1)


def window_calls(hours=None):
    h = hours or calib()["window_hours"]
    cut = time.time() - h * 3600
    return DB.execute("SELECT ts_utc FROM calls WHERE ts_utc>? AND http_status=200 ORDER BY ts_utc",
                      (cut,)).fetchall()


def window_profiles(hours=None):
    """(ts, profiles_returned) rows in the trailing window — the second, independent cap."""
    h = hours or calib()["window_hours"]
    cut = time.time() - h * 3600
    return DB.execute("SELECT ts_utc, profiles_returned FROM calls WHERE ts_utc>? AND http_status=200"
                      " ORDER BY ts_utc", (cut,)).fetchall()


# ----------------------------------------------------------------- 3. PRE-FLIGHT GATE
def gate(verbose=True):
    """Return (ok, seconds_to_wait). Never let the caller discover the wall by hitting it.

    Two independent caps per SignalHire support (19 Aug 2026): calls/day AND profiles/day.
    Either one can trigger a 402, so we gate on whichever is tighter right now."""
    c = calib(); h = c["window_hours"]
    call_budget = int(c["call_budget"] * SAFETY_MARGIN)
    prof_budget = int(c["profile_budget"] * SAFETY_MARGIN)

    calls = [r[0] for r in window_calls(h)]
    profs = window_profiles(h)
    prof_sum = sum(r[1] or 0 for r in profs)

    waits = []
    if len(calls) >= call_budget:
        idx = len(calls) - call_budget
        waits.append(("calls", calls[max(0, idx - 1)] + h * 3600))
    if prof_sum >= prof_budget:
        # walk the window forward until enough profile-volume has aged out to fit under budget
        running = prof_sum
        for ts, p in profs:
            running -= (p or 0)
            if running < prof_budget:
                waits.append(("profiles", ts + h * 3600)); break

    if not waits: return True, 0.0
    reason, next_slot = max(waits, key=lambda w: w[1])   # whichever cap frees up LAST is binding
    wait = max(0.0, next_slot - time.time())
    if verbose:
        print(f"    GATE[{reason}]: {len(calls)}/{call_budget} calls, {prof_sum}/{prof_budget} profiles "
              f"in trailing {h}h — waiting {wait/60:.1f} min "
              f"for a slot (until {datetime.datetime.fromtimestamp(next_slot).strftime('%H:%M:%S')})", flush=True)
    return False, wait


def interval():
    c = calib()
    if PACE == "asap":  return MIN_INTERVAL_S
    if PACE == "burst": return MIN_INTERVAL_S
    return max(MIN_INTERVAL_S, c["window_hours"] * 3600 / max(1, c["call_budget"]))   # even


# ----------------------------------------------------------------- 4/5. CALL + 402 HANDLING
class QuotaWall(Exception): pass


def search(company):
    """One searchByQuery call, gated and ledgered. Raises QuotaWall on 402."""
    while True:
        ok, wait = gate()
        if ok: break
        if wait <= 0: break
        time.sleep(min(wait, 900))          # re-evaluate at least every 15 min
    body = {"currentCompany": company, "location": "India", "size": SEARCH_SIZE, "currentTitle": TITLE_Q}
    try:
        r = requests.post(API, headers=HDR, json=body, timeout=45)
    except Exception as e:
        log_call(company, 0, 0, 0, SEARCH_SIZE); return [], 0, 0
    if r.status_code == 402:
        log_call(company, 402, 0, 0, SEARCH_SIZE)
        on_402(); raise QuotaWall("402")
    if r.status_code != 200:
        log_call(company, r.status_code, 0, 0, SEARCH_SIZE); return [], 0, r.status_code
    d = r.json(); profs = d.get("profiles") or []
    log_call(company, 200, len(profs), d.get("total") or 0, SEARCH_SIZE)
    return profs, d.get("total") or 0, 200


def on_402():
    """Record the wall and ALWAYS ratchet both budgets down to what was actually observed.

    FIXED 20 Aug: the previous version only adjusted whichever cap looked "near" its assumed
    threshold, and left both alone if neither was close — on the theory that a 402 far below
    both assumed caps was unexplained and shouldn't be blamed on either. In practice this let
    us hit a genuine live 402 twice in under a minute at 570-571 calls / ~1461 profiles, well
    under the 700/2000 SignalHire quoted, with the calibration never adapting because neither
    number was "near" 630/1800. A live 402 is definitive proof the true ceiling is AT MOST what
    we'd sent in the trailing window — that's true unconditionally, whether or not it matches
    our prior guess. So now both call_budget and profile_budget always ratchet down to
    min(prior, observed) on every wall, with no threshold gate. This is also how we catch
    SignalHire's stated numbers being unreliable: if the real ceiling is consistently below
    700/2000, both fields will visibly and permanently drop below those defaults over time."""
    c = calib(); h = c["window_hours"]
    calls_spent = len(window_calls(h))
    prof_spent = sum(r[1] or 0 for r in window_profiles(h))
    obs = c.get("observations", [])
    obs.append({"at": datetime.datetime.now().isoformat(timespec="seconds"),
                "calls_in_window_at_402": calls_spent, "profiles_in_window_at_402": prof_spent,
                "window_hours": h})

    prior_calls, prior_prof = c["call_budget"], c["profile_budget"]
    note = []
    new_calls = max(20, min(prior_calls, calls_spent))
    if new_calls != prior_calls:
        c["call_budget"] = new_calls
        note.append(f"call_budget {prior_calls} -> {new_calls}")
    new_prof = max(50, min(prior_prof, prof_spent))
    if new_prof != prior_prof:
        c["profile_budget"] = new_prof
        note.append(f"profile_budget {prior_prof} -> {new_prof}")
    if not note:
        note.append(f"observed (calls={calls_spent}, profiles={prof_spent}) already >= "
                    f"current budgets — no further tightening needed")

    c["observations"] = obs[-20:]
    save_calib(c)
    ev("402", f"hit wall with {calls_spent} calls / {prof_spent} profiles in trailing {h}h — " + "; ".join(note))
    ts = [r[0] for r in window_calls(h)]
    if ts:
        nxt = ts[0] + h * 3600
        ev("402", f"earliest slot frees at {datetime.datetime.fromtimestamp(nxt).strftime('%d %b %H:%M:%S')} "
                  f"({(nxt-time.time())/3600:.2f}h away)")


def note_recovery():
    """Called on the first 200 after a 402 — measures the real gap and logs it."""
    row = DB.execute("SELECT ts_utc FROM events WHERE kind='402' ORDER BY ts_utc DESC LIMIT 1").fetchone()
    if not row: return
    gap = (time.time() - row[0]) / 3600
    ev("recovery", f"first 200 after 402 — measured gap {gap:.2f}h")
    c = calib(); c.setdefault("recoveries", []).append(round(gap, 2)); save_calib(c)


# ----------------------------------------------------------------- 7. QUEUE
def load_state():
    try: return json.load(open(STATE))
    except Exception: return {}


def done_domains():
    """A company is done when a 200 is logged for it, profiles or not."""
    d = {r[0] for r in DB.execute("SELECT company FROM calls WHERE http_status=200").fetchall()}
    return d


def build_queue():
    st = load_state()
    done_names = done_domains()
    # HARDENED 20 Aug: apollo_reveal_runner.py draws from the same queue files and runs
    # independently (Apollo search+match -> SignalHire reveal, no direct-dial fallback for
    # now). Without this exclusion the two pipelines could both spend a call on the same
    # company — cheap for Apollo, but this runner's SignalHire searchByQuery calls are the
    # scarcest resource in the whole system, so a company Apollo already resolved must never
    # also burn a searchByQuery call here.
    apollo_state_path = os.path.join(HUB, "godown", "apollo_reveal", "apollo_reveal_state.json")
    apollo_done = set(json.load(open(apollo_state_path)).keys()) if os.path.exists(apollo_state_path) else set()
    rows, seen = [], set()
    srcs = [os.path.join(HUB, "godown", "prequal", "prequal_out", f)
            for f in ("enrich_queue_tierB.csv", "reserve.csv")]
    for p in srcs:
        if not os.path.exists(p): continue
        for r in csv.DictReader(open(p, encoding="utf-8-sig")):
            dom = (r.get("domain") or "").strip().lower(); nm = (r.get("name") or "").strip()
            if not dom or not nm or dom in seen: continue
            if dom in st: continue                       # already searched in the old pipeline
            if nm in done_names: continue                # already searched by this runner
            if dom in apollo_done: continue               # already attempted by the Apollo pipeline
            seen.add(dom)
            rows.append({"domain": dom, "name": nm, "rank": r.get("rank", ""), "score": r.get("score", "")})
    return rows


# ----------------------------------------------------------------- 8. REPORT
def report():
    c = calib(); h = c["window_hours"]; budget = c["call_budget"]; pbudget = c["profile_budget"]
    ts = [r[0] for r in window_calls(h)]
    prof_window = sum(r[1] or 0 for r in window_profiles(h))
    tot = DB.execute("SELECT COUNT(*),SUM(profiles_returned) FROM calls WHERE http_status=200").fetchone()
    n200, profs = tot[0] or 0, tot[1] or 0
    zero = DB.execute("SELECT COUNT(*) FROM calls WHERE http_status=200 AND profiles_returned=0").fetchone()[0]
    n402 = DB.execute("SELECT COUNT(*) FROM calls WHERE http_status=402").fetchone()[0]
    q = build_queue()
    st = load_state()
    gates = collections.Counter(v.get("gate") for v in st.values())
    print("=" * 78); print("SEARCH RUNNER — REPORT"); print("=" * 78)
    print(f"  ledger                     {LEDGER}")
    print(f"  calls logged (200)         {n200}")
    print(f"  calls logged (402)         {n402}")
    print(f"  profiles returned          {profs}   ({profs/max(1,n200):.2f} per call)")
    print(f"  zero-result rate           {100*zero/max(1,n200):.1f}%  ({zero}/{n200})")
    print()
    print(f"  ASSUMED window             {h} h")
    print(f"  calibrated call budget     {budget}   (safety-gated at {int(budget*SAFETY_MARGIN)})")
    print(f"  calibrated profile budget  {pbudget}   (safety-gated at {int(pbudget*SAFETY_MARGIN)})")
    print(f"  calls in trailing {h}h     {len(ts)}")
    print(f"  profiles in trailing {h}h  {prof_window}")
    print(f"  REMAINING (calls)          {max(0, int(budget*SAFETY_MARGIN) - len(ts))}")
    print(f"  REMAINING (profiles)       {max(0, int(pbudget*SAFETY_MARGIN) - prof_window)}")
    if c.get("recoveries"): print(f"  measured recovery gaps     {c['recoveries']}")
    if c.get("observations"):
        print("  402 observations:")
        for o in c["observations"][-5:]:
            if "calls_in_window_at_402" in o:
                print(f"     {o['at']}  {o['calls_in_window_at_402']} calls in window")
            else:
                print(f"     {o.get('at','?')}  {o.get('note', o)}")
    print()
    print(f"  companies remaining        {len(q)}")
    print(f"  dial-ready so far (state)  {gates.get('PASS',0)} PASS / {sum(gates.values())} searched")
    if gates.get("PASS"):
        yld = gates["PASS"] / max(1, sum(gates.values()))
        print(f"  observed PASS rate         {100*yld:.1f}%")
        per_day = budget * SAFETY_MARGIN
        print(f"  projected leads/day        {per_day*yld:.0f}   at {int(per_day)} calls/day")
        if per_day: print(f"  DAYS TO CLEAR BACKLOG      {len(q)/per_day:.1f}")
    print(f"  pacing mode                {PACE}  (interval {interval():.1f}s)")
    print("=" * 78)


# ----------------------------------------------------------------- 6. EXPERIMENT
def experiment():
    """Distinguish a rolling window from a fixed daily cap. Bursts of 50, 6h apart, until 402."""
    print("EXPERIMENT: rolling-window vs calendar-cap")
    print("  plan: fire 50 calls as fast as MIN_INTERVAL allows, stop, wait 6h, repeat until 402.")
    print("  then wait for recovery and compare the gap against the EARLIEST burst.\n")
    q = build_queue()
    if not q: print("  no queue — nothing to test with"); return
    bursts, i = [], 0
    try:
        while i < len(q):
            b0 = time.time(); made = 0
            while made < 50 and i < len(q):
                nm = q[i]["name"]; i += 1
                try:
                    profs, total, code = search(nm)
                except QuotaWall:
                    bursts.append({"start": b0, "end": time.time(), "calls": made})
                    raise
                made += 1
                print(f"    burst{len(bursts)+1} {made}/50 {nm[:34]:<36}{len(profs)} profiles", flush=True)
                time.sleep(MIN_INTERVAL_S)
            bursts.append({"start": b0, "end": time.time(), "calls": made})
            ev("run_end", f"burst of {made} complete; sleeping 6h")
            print(f"  burst {len(bursts)} done ({made} calls). sleeping 6h...", flush=True)
            time.sleep(6 * 3600)
    except QuotaWall:
        print("\n  402 reached. now polling for recovery every 15 min...", flush=True)
        first = bursts[0]["start"]; hit = time.time()
        while True:
            time.sleep(900)
            try:
                requests.post(API, headers=HDR, json={"currentCompany": "Zealous System",
                              "currentTitle": "founder", "size": 1}, timeout=30).raise_for_status()
            except Exception:
                continue
            break
        rec = time.time()
        note_recovery()
        g_first = (rec - first) / 3600; g_hit = (rec - hit) / 3600
        print("\n" + "=" * 78); print("EXPERIMENT VERDICT"); print("=" * 78)
        print(f"  first call of burst 1 : {datetime.datetime.fromtimestamp(first)}")
        print(f"  402 hit               : {datetime.datetime.fromtimestamp(hit)}")
        print(f"  recovered             : {datetime.datetime.fromtimestamp(rec)}")
        print(f"  gap from FIRST call   : {g_first:.2f} h")
        print(f"  gap from the 402      : {g_hit:.2f} h")
        print()
        if abs(g_first - 24) < 1.5:
            print("  VERDICT: ROLLING WINDOW. Recovery tracked ~24h from the EARLIEST calls, not")
            print("  from the moment we were blocked. Spread calls evenly; bursting wastes the window.")
        elif abs(g_hit - 24) < 1.5:
            print("  VERDICT: PENALTY-STYLE RESET — the clock starts when you hit the wall, so")
            print("  hitting 402 is expensive and must be avoided by the pre-flight gate.")
        else:
            print(f"  VERDICT: NEITHER cleanly. Recovery at {datetime.datetime.fromtimestamp(rec).strftime('%H:%M')} local")
            print("  suggests a fixed wall-clock boundary. Compare across two more cycles.")
        print("=" * 78)


# ----------------------------------------------------------------- MAIN
def run():
    q = build_queue()
    if LIMIT: q = q[:LIMIT]
    c0 = calib()
    print(f"queue: {len(q)} companies | size={SEARCH_SIZE} | pace={PACE} ({interval():.1f}s) "
          f"| call_budget={c0['call_budget']} (gated {int(c0['call_budget']*SAFETY_MARGIN)})"
          f" | profile_budget={c0['profile_budget']} (gated {int(c0['profile_budget']*SAFETY_MARGIN)})")
    ev("run_start", f"{len(q)} queued, size={SEARCH_SIZE}, pace={PACE}")
    st = load_state(); ok = pas = 0
    last_402 = DB.execute("SELECT COUNT(*) FROM events WHERE kind='402'").fetchone()[0]
    try:
        for i, r in enumerate(q, 1):
            try:
                profs, total, code = search(r["name"])
            except QuotaWall:
                print("\n  !! 402 — gate will hold until a slot frees. checkpointed."); break
            if code == 200 and last_402:
                note_recovery(); last_402 = 0
            ok += 1
            best = pick(profs, r["name"]) if profs else None
            rec = {"domain": r["domain"], "company": r["name"], "rank": r.get("rank", ""),
                   "score": r.get("score", "")}
            if not best:
                rec["gate"] = "no decision-maker found"
            else:
                uid, person, title, sc = best
                got = reveal(uid)                                  # reveal leg untouched
                if got:
                    ind = next((to_e164(x) for x in got["phones"] if in_classify(x) == "mobile"), "")
                    rec.update({"person": person, "title": title, "role_score": sc, "uid": uid,
                                "phone": ind, "email": (got["emails"] or [""])[0],
                                "linkedin": got.get("linkedin", "")})
                    rec["gate"] = "PASS" if ind else "skip - no +91 mobile"
                    pas += 1 if ind else 0
                else:
                    rec.update({"person": person, "title": title, "gate": "reveal failed"})
            st[r["domain"]] = rec; json.dump(st, open(STATE, "w"), ensure_ascii=False, indent=1)
            print(f"  [{i}/{len(q)}] {r['name'][:32]:<34}{len(profs)}p  {rec['gate']}", flush=True)
            time.sleep(interval())
    finally:
        ev("run_end", f"{ok} calls made, {pas} PASS this run")
        print(f"\ncalls {ok} | PASS {pas}")
        if APPLY:
            print("\n--apply: hand off to the existing push step:")
            print("  python3 searchq_enrich.py --apply   (pushes any PASS rows not yet in searchq_pushed.json)")


if __name__ == "__main__":
    backfill()
    if flag("--report"): report()
    elif flag("--experiment"): experiment()
    else: run()
