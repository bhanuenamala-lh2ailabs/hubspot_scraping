# Next step: deploy it yourself and show it running live

Purunjay — the code on `realtime-dashboard` is strong. You read the brief closely and it
shows: the signature verification, the `changeSource` vs `sourceType` distinction, the
git-refs send-ledger, the bulk-write threshold, and the send-failure exit code are all exactly
right.

But the brief's acceptance criteria are about **showing it working**, not describing it. Right
now nothing is deployed — the Worker isn't live, the webhooks aren't on, and no report has
actually fired on schedule. So the task isn't finished; it's built and needs to be **stood up
and demonstrated.**

**Please drive the entire setup yourself, end to end.** Don't hand the deployment back to us —
do every step in your own `RELAY_SETUP.md`, and come back with proof it runs.

## What you own

1. **Cloudflare** — create your own free account, deploy the Worker, create the D1 database,
   set all three secrets (`PUBLISH_TOKEN`, `GITHUB_TOKEN`, `HUBSPOT_APP_SECRET`). This is all
   yours — no access needed from us.

2. **GitHub** — you already have repo access. Add the `RELAY_URL` / `RELAY_TOKEN` Actions
   secrets, and confirm the three workflows run.

3. **HubSpot webhooks** — this is the one screen that needs portal admin. Tell us **exactly**
   what you need: the precise webhook config (target URL, the two subscriptions, concurrency)
   written so it can be pasted in without interpretation, and what to send back to you (the
   client secret). We'll do that one screen; everything around it is yours to wire.

## What "done" looks like — demonstrate each, don't describe it

Record a short screen capture or paste the terminal/log output for each:

1. **Live update:** move a deal's stage in HubSpot → the dashboard page reflects it without a
   manual rebuild. State the lag you measured.
2. **Gap handling:** stop the Worker, move two deals, bring it back → show what happens to
   those two (recovered, or lost — and why).
3. **The 6:30 mail lands** at 18:30 IST on a day you didn't touch anything. Show the send log
   and the received mail. Then show the **Friday weekly** firing too.
4. **At-most-once:** trigger the report twice in the same window → show only one mail went, and
   the git-ref claim that blocked the second.
5. **Failure is loud:** break it on purpose (bad token / Worker down / send failure) → show
   that the run goes **red** and someone would find out. This is the one that matters most.
6. **Rollback:** show the `RELAY=''` switch takes the page back to today's behaviour instantly.

## Rules (same as the brief — don't relax them)

- Everything stays on **free tiers**. Name what you used and where it breaks at 10× volume.
- **Secrets never get committed** — you've done this right so far, keep it that way.
- The **only** automated mail is the 18:30 report. Don't add alerts or notification mail. The
  disabled VCF-notifier task stays disabled.
- Don't touch the **CEO dashboard** view or the **note-rule / metric definitions** (change a
  metric in `note_rules.py` / the imported functions once, never copy them).
- Human-move filtering (`sourceType == "CRM_UI"`) must survive everywhere it's counted.

## When it's demonstrably live

Open a PR from `realtime-dashboard` → `main` with the demo evidence in the description, and
we'll review and merge. Until it's shown working, treat it as in progress.

Good work so far — finish it by making it real.
