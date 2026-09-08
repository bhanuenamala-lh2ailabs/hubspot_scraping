# OutFlo → HubSpot Plug Rules

How OutFlo LinkedIn-campaign leads are pulled, tiered, enriched, and pushed into the HubSpot **Campaign** pipeline. This is the source-of-truth for the sync; re-run follows these rules exactly.

_Last updated: 2026-07-29_

---

## 1. Sources

| Source | What it provides |
|---|---|
| **OutFlo API** (3 campaigns) | LinkedIn URL, name, headline, company, title, location, connection/reply status, per-lead **timeline** (sent/accepted/replied timestamps + reply text + sender account) |
| **"Outflo Reachout" Google Sheet** (`Lead Tracker` tab) | Yash's manual tracker — Current Status, Remarks, Next Check Date, POC |
| **Calendly** (Ishpreet's link) | Booked discovery-call meetings — invitee name/email, meeting time + link |

**Campaigns → bucket:**
- `Private Codebase - Startup Founders_India` **+** `..._India_2` → **India**
- `Private Codebase - Startup Founders_Indonesia` → **Indonesia**

---

## 2. Which leads to pull (engagement tiers)

Pull a lead if **any** of these is true:

| Tier | Condition | Pulled? |
|---|---|---|
| Booked | Has a Calendly booking | ✅ |
| Replied | Reply Status = Replied | ✅ |
| Accepted | Connection Status = Connected (accepted the request), no reply | ✅ |
| Sent ≥ 2 days | Connection request sent **≥ 2 days ago**, not yet accepted | ✅ |
| Sent < 2 days | Request sent **< 2 days ago**, not accepted | ❌ skip (still in flight) |
| On the sheet | Present in Yash's Outflo Reachout sheet | ✅ (always) |

Final push set = **union** of the above, **deduped by normalized LinkedIn URL**.
(Untouched queued leads — connection never sent, "Checking"/"Unknown" — are **not** pulled.)

---

## 3. Stage mapping (precedence order)

For each lead, decide the Campaign-pipeline stage in this order (first match wins):

1. **Calendly booking → `GMeet Fixed`** (store meeting link + time in the note).
2. **Sheet manual status → its stage:**
   - Dead → `Dead/ColdCall/Not Interested`
   - Interested → `Interested`
   - Script shared → `Script Shared`
   - Call attempted → `Call Attempted`
   - GMeet fixed → `GMeet Fixed`
3. **OutFlo auto-tier → `Cold Call`** (see priority below).

> Rationale: a confirmed meeting beats a manual note beats an automated engagement signal. Yash's human-verified status always outranks the raw campaign state.

---

## 4. Priority (`hs_priority`)

Applied to the **Cold Call auto-tier** (increasing with engagement):

| Engagement | Priority |
|---|---|
| Replied | **High** |
| Accepted, no reply | **Medium** |
| Request sent ≥ 2 days, not accepted | **Low** |
| GMeet Fixed / any sheet-status stage | *(no auto priority — set later per SOP)* |

---

## 5. Enrichment (Signalhire, by LinkedIn URL)

- Enrich **all non-dead leads** for **phone + email** (Signalhire, cached lookup).
- GMeet-booked leads also carry the **Calendly email**.
- Dead leads are **not** enriched.
- Where Signalhire has no number, the lead is pushed without a phone (worked via LinkedIn).

> Original rule was "connected only"; widened (2026-07-29, per Rahul) to **every non-dead lead** so Yash has a number for the full cold-call list.

---

## 6. What gets written to HubSpot

**Pipeline:** Campaign (`2425754306`), on the Scraped/SOP cadence (Cold Call → … → Closed/Won + Dead/*).

**Per lead — Contact + Company + Deal, associated:**
- **Contact:** first/last name, `linkedin_url`, job title, company, city, `phone`, `email`.
- **Company:** by name (deduped).
- **Deal:**
  - `dealname` = lead name
  - `dealstage` = mapped stage (§3)
  - `hs_priority` = §4
  - `lead_source` = **"Outflo Outreach – India"** / **"Outflo Outreach – Indonesia"** (the tag)
  - `source_tab` = "OutFlo API"
  - **`hubspot_owner_id` + `poc` = Yash** (`166483631`) — always
  - `linkedin_url` (deal property — also the dedup key)
  - `outflo_request_sent`, `outflo_connected_at`, `outflo_replied_at` (datetime)

**Note (one per deal):** connection/reply status · sent/accepted/replied times · **reply text** · sender account (Ashish/Yash) · sheet status · **remarks**.

**Task (only when the sheet has a real Next Check Date):** assigned to Yash, due = Next Check Date, body = remark. (Garbage dates like phone numbers are skipped.)

---

## 7. Deduping

- **Within the pull:** union deduped by normalized LinkedIn URL (strip `www`, trailing slash, query string, force `https`).
- **Against HubSpot:** every deal is looked up by `linkedin_url`; if found → **update in place**, else **create**. Re-runs are therefore idempotent (no duplicate deals). Notes & tasks are created **only on new deals** so re-runs don't duplicate them.

---

## 8. Owner

**Everything is assigned to Yash Wani** (owner + PoC), regardless of the sheet's POC column.

---

## 9. Known caveats

- **Calendly is Ishpreet's shared link**, used across all LH2 discovery calls — a booking is only treated as an OutFlo GMeet if the invitee matches an OutFlo lead by name. (At last run, the live bookings were codebase-acquisition leads, not OutFlo.)
- OutFlo provides **no email/phone** itself — contact info comes only from Signalhire enrichment (or Calendly for booked invitees).
- The "2 days" cutoff is measured from the connection-request-sent time in the lead's OutFlo timeline.

---

## 10. Scripts (in the working scratchpad)

`outflo_pull.py` (pull) → `tier_leads.py` (tier) → `timelines_enrich.py` + `enrich_all.py` (timestamps + enrichment) → `push_outflo_v2.py` (push). Data staged in `push_set.json`.
