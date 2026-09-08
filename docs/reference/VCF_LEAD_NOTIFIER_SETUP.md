# VCF lead notifier — setup

When a deal is assigned to a caller in HubSpot, they get an email with a `.vcf` holding
every contact on that deal. They open it on their phone and the whole batch is in their
contacts. Built and proven end-to-end on 2026-08-04 — **the only missing piece is an email
transport.**

| Piece | File | Status |
|---|---|---|
| Assignment detection | `crm_mirror/enrich/lead_vcf_notifier.py` | working |
| vCard 3.0 generation | same | working — verified against live deals |
| Email transport | `crm_mirror/enrich/gmail_sender.py` | **needs one of the setups below** |

Until a transport exists the notifier writes the `.vcf` and the message body to
`crm_mirror/vcf_outbox/` instead of dropping them. Nothing is lost.

---

## Can we use the Gmail API from Google Cloud? Yes — but pick the right one

### ✅ Option A — OAuth 2.0 Desktop client (no admin needed) — do this one

You consent once in a browser, a refresh token is stored, and it then sends unattended
forever. Roughly 3 minutes.

1. **console.cloud.google.com** → project **`lh2-pipeline`** (the project the existing
   service-account key belongs to).
2. **APIs & Services → Library →** search **Gmail API** → **Enable**.
3. **APIs & Services → OAuth consent screen** — if it asks, choose **Internal**
   (everyone at lh2holdings.com; no Google verification review), add the scope
   `https://www.googleapis.com/auth/gmail.send`.
4. **APIs & Services → Credentials → Create credentials → OAuth client ID**
   → Application type **Desktop app** → Create → **Download JSON**.
5. Save that file as **`gmail_oauth_client.json`** in the repo root (next to `.env`).
6. Run once:
   ```bash
   python crm_mirror/enrich/gmail_sender.py --auth
   ```
   A browser opens — sign in as **rahul.dhali@lh2holdings.com** and approve. The refresh
   token is written to `crm_mirror/enrich/gmail_token.json`.
7. Prove it:
   ```bash
   python crm_mirror/enrich/gmail_sender.py --check
   python crm_mirror/enrich/gmail_sender.py --test rahul.dhali@lh2holdings.com
   ```

Mail arrives **from Rahul's account**. Gmail's API cap is 2,000 messages/day on Workspace;
this sends a handful.

> `gmail_token.json` and `gmail_oauth_client.json` are credentials — keep them out of git,
> same as `.env` and the service-account key.

### Option B — service account + domain-wide delegation (needs a super-admin)

Only worth it if we later want to send *as* several different people unattended.

A service account has **no mailbox of its own** — it can only impersonate a real user, and
that requires a Workspace super-admin to authorise it:

> Admin console → **Security → Access and data control → API controls →
> Domain-wide delegation → Add new**
> Client ID `100170198106213149801`
> Scope `https://www.googleapis.com/auth/gmail.send`

Verified 2026-08-04: this is **not** currently enabled — the SA returns
`unauthorized_client: Client is unauthorized to retrieve access tokens using this method`.
Once an admin adds it, `gmail_sender.py` picks it up with no code change.

### Option C — SMTP app password (fallback)

Set `SMTP_HOST=smtp.gmail.com`, `SMTP_USER`, `SMTP_PASSWORD` (a Google **app password**,
not the account password) in `.env`. Works, but app passwords require 2FA and are disabled
in some Workspace configs — try A first.

---

## Running it

```bash
python crm_mirror/enrich/lead_vcf_notifier.py --init      # first run: baseline, sends nothing
python crm_mirror/enrich/lead_vcf_notifier.py --dry-run   # show what would go out
python crm_mirror/enrich/lead_vcf_notifier.py             # send
python crm_mirror/enrich/lead_vcf_notifier.py --install-task 15   # every 15 min, Windows
```

**Run `--init` first.** Without it the very first run would treat all 1,231 existing deals
as newly assigned and mail every caller their entire book.

## Why polling and not a HubSpot webhook

A HubSpot workflow webhook has to POST to a public HTTPS endpoint. We have no server. The
notifier instead diffs current deal→owner assignments against
`crm_mirror/enrich/vcf_notifier_state.json`, so it fires on a genuinely new assignment —
either a first assignment or a hand-off to a different owner — and never repeats one.
A 15-minute task is well inside HubSpot's ~625k calls/day.

## What the caller gets

```
Hi Ishpreet,

3 new leads have been assigned to you in HubSpot in the Scraped pipeline.
The attached .vcf holds 10 contacts — open it on your phone to add them all at once.

  • Rahul Harkisanka    Eatlo     +919166627878   Co-founder & CEO
  • Amit More           Finzy     +919821017398   Founder & CEO
  ...
```

Each vCard carries name, company, title, mobile, email, LinkedIn URL, and a NOTE recording
the deal, its stage, the owner and the assignment date — so a contact in someone's phone
still points back to the deal months later.
