#!/usr/bin/env python3
"""
Apollo.io phone reveal via webhook — run this LOCALLY, outside any sandboxed
agent, using your real Apollo API key and a webhook.site token you control.

Usage:
    pip install requests
    export APOLLO_API_KEY="your_key_here"
    python apollo_phone_reveal.py

What it does:
    1. Loads your leads CSV (must have columns: first_name,last_name,organization_name
       — optionally source_batch, email)
    2. Dedupes by (first_name, last_name, organization_name)
    3. Fires ONE test call, waits, polls the webhook, shows you the round trip,
       and asks you to confirm before touching the rest
    4. Runs the full deduped list through /people/bulk_match in batches of 10
    5. Polls the webhook.site token periodically, merges phone numbers back in
       by Apollo's "id" field
    6. Writes results to apollo_results.csv

Edit the CONFIG block below before running.
"""

import csv
import json
import os
import sys
import time
import requests

# ---------------- CONFIG ----------------
APOLLO_API_KEY = os.environ.get("APOLLO_API_KEY", "")
WEBHOOK_TOKEN = "26fd58aa-2820-4ad3-b82d-a04db6db3205"  # from your webhook.site URL
WEBHOOK_URL = f"https://webhook.site/{WEBHOOK_TOKEN}"
WEBHOOK_API = f"https://webhook.site/token/{WEBHOOK_TOKEN}/requests?sorting=newest"

INPUT_CSV = "leads.csv"          # your cached lead data — adjust columns as needed
OUTPUT_CSV = "apollo_results.csv"

BATCH_SIZE = 10                  # bulk_match max per call
POLL_INTERVAL_SEC = 20
POLL_MAX_MINUTES = 8
BATCH_PAUSE_SEC = 3               # basic throttle between bulk_match calls
# -----------------------------------------

MATCH_URL = "https://api.apollo.io/api/v1/people/match"
BULK_MATCH_URL = "https://api.apollo.io/api/v1/people/bulk_match"


def load_leads(path):
    leads = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            leads.append({
                "first_name": row.get("first_name", "").strip(),
                "last_name": row.get("last_name", "").strip(),
                "organization_name": row.get("organization_name", "").strip(),
                "email": row.get("email", "").strip() or None,
                "source_batch": row.get("source_batch", "").strip() or None,
            })
    return leads


def dedupe(leads):
    seen = {}
    for lead in leads:
        key = (lead["first_name"].lower(), lead["last_name"].lower(),
               lead["organization_name"].lower())
        if key not in seen:
            seen[key] = lead
    return list(seen.values())


def apollo_headers():
    return {"X-Api-Key": APOLLO_API_KEY, "Content-Type": "application/json"}


def test_call(lead):
    body = {
        "first_name": lead["first_name"],
        "last_name": lead["last_name"],
        "organization_name": lead["organization_name"],
        "reveal_personal_emails": True,
        "reveal_phone_number": True,
        "webhook_url": WEBHOOK_URL,
    }
    print(f"\n[TEST] POST {MATCH_URL}")
    print(f"[TEST] Body: {json.dumps(body)}")
    r = requests.post(MATCH_URL, headers=apollo_headers(), json=body)
    print(f"[TEST] Status: {r.status_code}")
    print(f"[TEST] Response: {r.text[:2000]}")
    r.raise_for_status()
    data = r.json()
    person_id = data.get("person", {}).get("id") or data.get("id")
    print(f"[TEST] Captured Apollo id: {person_id}")
    return person_id


def poll_webhook_for_id(target_id, max_minutes=POLL_MAX_MINUTES):
    deadline = time.time() + max_minutes * 60
    print(f"\n[POLL] Watching {WEBHOOK_API} for id={target_id} (up to {max_minutes} min)...")
    while time.time() < deadline:
        r = requests.get(WEBHOOK_API)
        r.raise_for_status()
        for entry in r.json().get("data", []):
            content = entry.get("content", "")
            try:
                payload = json.loads(content)
            except (json.JSONDecodeError, TypeError):
                continue
            pid = payload.get("id") or payload.get("person", {}).get("id")
            if pid == target_id:
                print(f"[POLL] Match found: {json.dumps(payload)[:2000]}")
                return payload
        print("[POLL] Not yet — waiting...")
        time.sleep(POLL_INTERVAL_SEC)
    print("[POLL] Timed out without a matching payload.")
    return None


def run_bulk_batch(batch):
    body = {
        "reveal_personal_emails": True,
        "reveal_phone_number": True,
        "webhook_url": WEBHOOK_URL,
        "details": [
            {
                "first_name": l["first_name"],
                "last_name": l["last_name"],
                "organization_name": l["organization_name"],
                **({"email": l["email"]} if l["email"] else {}),
            }
            for l in batch
        ],
    }
    r = requests.post(BULK_MATCH_URL, headers=apollo_headers(), json=body)
    if r.status_code == 429:
        print("[BULK] Rate limited — backing off 60s")
        time.sleep(60)
        r = requests.post(BULK_MATCH_URL, headers=apollo_headers(), json=body)
    r.raise_for_status()
    data = r.json()
    matches = data.get("matches", []) or data.get("people", [])
    ids = []
    for lead, match in zip(batch, matches):
        pid = match.get("id")
        lead["apollo_id"] = pid
        ids.append(pid)
    return ids


def drain_webhook_since(collected, seen_ids):
    """Pull all currently-available webhook payloads and merge any new ones."""
    r = requests.get(WEBHOOK_API)
    r.raise_for_status()
    for entry in r.json().get("data", []):
        try:
            payload = json.loads(entry.get("content", ""))
        except (json.JSONDecodeError, TypeError):
            continue
        pid = payload.get("id") or payload.get("person", {}).get("id")
        if pid and pid not in seen_ids:
            seen_ids.add(pid)
            collected[pid] = payload


def main():
    if not APOLLO_API_KEY:
        print("ERROR: set APOLLO_API_KEY environment variable first.")
        sys.exit(1)

    leads = dedupe(load_leads(INPUT_CSV))
    print(f"Loaded {len(leads)} deduped leads from {INPUT_CSV}")

    # --- Step 1: single test call ---
    test_lead = leads[0]
    test_id = test_call(test_lead)
    payload = poll_webhook_for_id(test_id)
    if not payload:
        print("\nTest did not confirm a webhook round trip. Stopping before bulk run.")
        sys.exit(1)

    proceed = input(f"\nTest succeeded (id={test_id} got a payload). "
                     f"Proceed with all {len(leads)} leads? [y/N] ").strip().lower()
    if proceed != "y":
        print("Aborted by user.")
        sys.exit(0)

    remaining = leads[1:]  # first lead already done in the test
    all_ids_expected = {test_id}
    collected = {test_id: payload}

    # --- Step 2: bulk_match in batches ---
    for i in range(0, len(remaining), BATCH_SIZE):
        batch = remaining[i:i + BATCH_SIZE]
        print(f"\n[BULK] Batch {i // BATCH_SIZE + 1}: {len(batch)} leads")
        ids = run_bulk_batch(batch)
        all_ids_expected.update(x for x in ids if x)
        time.sleep(BATCH_PAUSE_SEC)

    print(f"\n[BULK] Done. Expecting phone data for {len(all_ids_expected)} ids.")

    # --- Step 3: drain webhook until all ids seen or timeout ---
    seen_ids = set(collected.keys())
    deadline = time.time() + POLL_MAX_MINUTES * 60
    while time.time() < deadline and not all_ids_expected.issubset(seen_ids):
        drain_webhook_since(collected, seen_ids)
        missing = len(all_ids_expected - seen_ids)
        print(f"[DRAIN] {len(seen_ids)}/{len(all_ids_expected)} received, {missing} pending...")
        if all_ids_expected.issubset(seen_ids):
            break
        time.sleep(POLL_INTERVAL_SEC)

    # --- Step 4: merge and write CSV ---
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["first_name", "last_name", "organization_name",
                          "source_batch", "apollo_id", "phone_number", "status"])
        all_leads = [test_lead] + remaining
        for lead in all_leads:
            pid = lead.get("apollo_id") or (test_id if lead is test_lead else None)
            payload = collected.get(pid)
            phone = None
            status = "no_match"
            if pid and payload:
                phones = payload.get("phone_numbers") or payload.get("phones") or []
                if phones:
                    phone = phones[0].get("sanitized_number") or phones[0].get("raw_number")
                    status = "matched_with_phone"
                else:
                    status = "matched_no_phone"
            elif pid:
                status = "pending_or_error"
            writer.writerow([lead["first_name"], lead["last_name"],
                              lead["organization_name"], lead.get("source_batch"),
                              pid, phone, status])

    print(f"\nDone. Results written to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
