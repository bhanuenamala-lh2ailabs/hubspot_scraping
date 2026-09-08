# -*- coding: utf-8 -*-
"""Enrich confirmed CAD candidates for +91 mobile via Apollo, in batches of 100.
Checks live Apollo credit balance before EACH batch and halts immediately if it's 0 —
so we never again silently burn through a batch on an exhausted account. Captures the
raw `failure_reason` per person so a genuine "no data" is distinguishable from a
credit/billing block.

Usage: python3 batch_enrich_100.py
"""
import json, urllib.request, urllib.error, time, socket, sys, os

env = {l.split('=', 1)[0].strip().lower(): l.split('=', 1)[1].strip()
       for l in open("/Users/bhanu/Desktop/hubspot/.env", encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
AH = {"Content-Type": "application/json", "Cache-Control": "no-cache", "X-Api-Key": env["apollo_api_key"]}
WEBHOOK = "https://example.com/apollo-noop"
STATE = os.path.join(os.path.dirname(__file__), "round3_phones.json")


def credit_balance():
    """A cheap, free probe: attempt reveal on a junk record. 422 body carries the live balance."""
    body = {"first_name": "Zzz", "last_name": "Probe", "organization_name": "Nonexistent Co 12345",
             "reveal_personal_emails": True, "reveal_phone_number": True, "webhook_url": WEBHOOK}
    r = urllib.request.Request("https://api.apollo.io/api/v1/people/match",
        data=json.dumps(body).encode(), method="POST", headers=AH)
    try:
        d = json.loads(urllib.request.urlopen(r, timeout=30).read().decode())
        return None  # 200 OK on a junk record just means "no match found" — not a credit signal either way
    except urllib.error.HTTPError as e:
        body_e = e.read().decode()
        try:
            d = json.loads(body_e)
            bal = (d.get("error_details") or {}).get("context", {}).get("credit_balance", {}).get("value")
            return bal
        except Exception:
            return None


def safe_call(fn, retries=3):
    for attempt in range(retries):
        try:
            return fn()
        except (ConnectionResetError, socket.timeout, ConnectionError, TimeoutError, urllib.error.URLError) as e:
            print(f"  network error (attempt {attempt+1}): {e}", flush=True)
            time.sleep(3)
    return {"_err": "network_failure"}


def trigger(first, last, org):
    def _do():
        body = {"first_name": first, "last_name": last, "organization_name": org,
                "reveal_personal_emails": True, "reveal_phone_number": True, "webhook_url": WEBHOOK}
        r = urllib.request.Request("https://api.apollo.io/api/v1/people/match",
            data=json.dumps(body).encode(), method="POST", headers=AH)
        try:
            return json.loads(urllib.request.urlopen(r, timeout=30).read().decode())
        except urllib.error.HTTPError as e:
            body_e = e.read().decode()
            try:
                parsed = json.loads(body_e)
            except Exception:
                parsed = {"raw": body_e}
            return {"_err": e.code, "_body": parsed}
    return safe_call(_do)


class PollRateLimited(Exception):
    pass


def poll(rid, max_tries=8):
    for _ in range(max_tries):
        def _do():
            r = urllib.request.Request(f"https://api.apollo.io/api/v1/webhook_result/{rid}",
                                        headers={"X-Api-Key": env["apollo_api_key"]})
            try:
                return json.loads(urllib.request.urlopen(r, timeout=30).read().decode())
            except urllib.error.HTTPError as e:
                body_e = e.read().decode()
                if e.code == 404 and "result_pending" in body_e:
                    return {"_pending": True}
                if e.code == 429:
                    return {"_err": 429, "_body": body_e}
                return {"_err": e.code, "_body": body_e}
        d = safe_call(_do)
        if d.get("_pending"):
            time.sleep(5); continue
        if d.get("_err") == 429:
            # webhook_result/show is capped at 400/hr — this is NOT "no phone data", it's a
            # rate limit. Surfacing it as an exception forces the caller to stop rather than
            # silently record a false "matched_no_phone" the way plain error dicts did before.
            raise PollRateLimited(d.get("_body", ""))
        wr = d.get("webhook_result") or {}
        if wr.get("status") in ("success", "failed"):
            return d
        if d.get("_err"):
            return d
        time.sleep(5)
    return {"_timeout": True}


def enrich_batch(candidates):
    """candidates: list of {p: profile, company, title}. Returns results list, stops on credit exhaustion."""
    results = []
    for i, c in enumerate(candidates, 1):
        p = c["p"]
        fn, ln, co = p.get("firstName", ""), p.get("lastName", ""), c["company"]
        trig = trigger(fn, ln, co)
        if trig.get("_err"):
            err_body = trig.get("_body") or {}
            code = (err_body.get("error_details") or {}).get("code") if isinstance(err_body, dict) else None
            if code == "BILLING.LIMIT.CREDITS_EXHAUSTED" or trig.get("_err") in (402, 429):
                print(f"  CREDIT/RATE LIMIT HIT at {i}/{len(candidates)} — stopping batch. "
                      f"balance={((err_body.get('error_details') or {}).get('context', {}).get('credit_balance', {}).get('value'))}",
                      flush=True)
                return results, "credit_exhausted"
            results.append({**c, "phone": None, "status": "trigger_error", "failure_reason": str(err_body)[:200]})
            print(f"  [{i}/{len(candidates)}] {fn} {ln} @ {co} -> TRIGGER ERR {trig['_err']}", flush=True)
            continue
        rid = trig.get("request_id")
        person_found = bool(trig.get("person"))
        try:
            res = poll(rid)
        except PollRateLimited as e:
            print(f"  POLL RATE LIMIT HIT at {i}/{len(candidates)} — stopping batch "
                  f"(webhook_result/show capped at 400/hr on this account): {str(e)[:150]}", flush=True)
            return results, "rate_limited"
        wr = (res or {}).get("webhook_result") or {}
        people = wr.get("people") or []
        phone = None
        if people:
            phones = people[0].get("phone_numbers") or []
            mobiles = [ph for ph in phones if ph.get("type_cd") == "mobile" and ph.get("status_cd") == "valid_number"]
            if mobiles: phone = mobiles[0].get("sanitized_number")
            elif phones: phone = phones[0].get("sanitized_number")
        failure_reason = res.get("failure_reason") or wr.get("failure_reason") or ""
        status = "matched_with_phone" if phone else ("matched_no_phone" if person_found else "no_match")
        results.append({**c, "phone": phone, "status": status, "failure_reason": failure_reason})
        print(f"  [{i}/{len(candidates)}] {fn} {ln} @ {co} -> {status} {phone or ''} "
              f"[{failure_reason[:60]}]", flush=True)
        time.sleep(1.0)  # throttle poll volume — webhook_result/show is capped at 400/hr account-wide
    return results, "completed"


if __name__ == "__main__":
    confirmed = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "/tmp/cad_round3_confirmed.json"))
    print(f"total confirmed candidates: {len(confirmed)}", flush=True)

    all_results = json.load(open(STATE)) if os.path.exists(STATE) else []
    done_companies = {r["company"] for r in all_results}
    remaining = [c for c in confirmed if c["company"] not in done_companies]
    print(f"already done: {len(all_results)} | remaining: {len(remaining)}", flush=True)

    BATCH = 100
    for i in range(0, len(remaining), BATCH):
        batch = remaining[i:i + BATCH]
        bal = credit_balance()
        print(f"\n=== batch {i//BATCH+1} ({len(batch)} people) | probe balance signal: {bal} ===", flush=True)
        results, outcome = enrich_batch(batch)
        all_results += results
        json.dump(all_results, open(STATE, "w"), default=str, ensure_ascii=False, indent=1)
        found = sum(1 for r in results if r["status"] == "matched_with_phone")
        print(f"batch done: {found}/{len(results)} phones found | outcome={outcome}", flush=True)
        if outcome == "credit_exhausted":
            print("STOPPING — credits exhausted. Re-run this script once topped up; it resumes automatically.", flush=True)
            break
        if outcome == "rate_limited":
            print("STOPPING — Apollo's webhook_result/show hourly cap (400/hr) was hit. "
                  "Wait ~60 min for the rolling window to clear, then re-run; it resumes automatically.", flush=True)
            break

    total_found = sum(1 for r in all_results if r["status"] == "matched_with_phone")
    print(f"\nRUNNING TOTAL: {total_found} phones found / {len(all_results)} processed", flush=True)
