Subject: Approval Request: Apollo.io Basic Plan ($49–59/user/month) — Decision-Maker Identification Layer

Hi [Finance Contact],

I'm requesting approval to subscribe to Apollo.io's Basic plan ($49/user/month billed annually,
or $59/user/month billed monthly) to support our sales lead-generation pipeline. Below is the
full context, the sequence of testing that led here with real numbers, what this unlocks, and
one open risk I want to flag clearly before we commit.

## Background: the pipeline and where it was stuck

Our sales pipeline is: company -> find decision-maker -> get their phone number -> sales call.
We run this through SignalHire, which does both the search (find the person) and the reveal
(get their contact info). Our reveal credits (currently 4,540 remaining, checked today) have
never been the constraint — the search step was. We were hitting SignalHire's daily
searchByQuery quota after only 170–300 companies searched per day (297 on 17 Aug, 171 on 18
Aug), against a backlog of ~3,100 qualified companies. At that rate, just enriching the backlog
would have taken 10–18 working days before any selling could start.

## Update: SignalHire has already fixed part of this

I've attached SignalHire's reply for reference. Two separate things are happening here — one
already done, one in motion:

- **Already done, no cost:** SignalHire has already raised our daily search quota from 300 to
  700 calls/day as a courtesy. This is live now, not pending — confirmed by their support reply
  today (19 Aug) and by re-running our own search script against the new limit.
- **In motion, pending payment:** They've also offered a further upgrade to 1,200 calls/day for
  $2,000/year. I've told them to go ahead and send the payment link, so this is actively being
  set up, but not yet finalized on our side — flagging here for full visibility in case this
  needs its own separate finance sign-off for the payment itself.
- **Important nuance from their reply:** the quota actually has two independent ceilings —
  calls/day (700 now, 1,200 once the upgrade lands) AND total profiles returned/day (2,000).
  Either one triggers a 402 first, and we haven't yet confirmed with SignalHire whether the
  profile cap also increases with the paid upgrade. I've already updated our internal search
  script to track and gate on both ceilings independently, and it's running live against the
  backlog right now to confirm SignalHire's stated numbers hold up in practice, not just on paper.

Even at today's already-live 700/day, that's a 4x improvement over the 170–300/day we were stuck
at. Once the 1,200/day upgrade is finalized, the backlog could theoretically clear in ~2.6 days.
So a reasonable question is: why do we still need Apollo?

## Why we're still requesting Apollo alongside SignalHire's fix

1. **Redundancy and headroom.** Apollo's search endpoints are commonly cited at up to 50,000
   requests/day on paid plans — well above even SignalHire's upgraded tier, on a completely
   separate quota system. Caveat: we have not independently verified this figure against our own
   API calls (we've made under 50 test calls total to date), and Apollo's own documentation does
   not publish a plan-by-plan rate-limit table — this needs direct confirmation once we're on the
   plan, not taken as given.

2. **Apollo's search step is free.** Apollo's People Search endpoint (which finds the
   decision-maker's name and internal ID) consumes zero credits, no matter how many times we call
   it — confirmed empirically across two separate test rounds this week, including a 30-company
   coverage test run today (19 Aug) that made 17+ search calls with zero credit movement, verified
   by checking Apollo's credit balance before and after. Only converting that ID into a real name
   + LinkedIn URL (the Enrichment step) costs a credit, and it's a flat **1 credit per person**,
   confirmed empirically today by checking our test account's balance immediately before (101
   credits) and after (96 credits) enriching exactly 5 people — a clean -5 delta, and the API's
   own response even carries a `credits_consumed` field that matched exactly.

3. **We already validated the full combined pipeline works, end to end, with real data.** Today
   (19 Aug) we ran a controlled test: Apollo Search -> Apollo Enrichment (real LinkedIn URL) ->
   fed that LinkedIn URL into SignalHire's existing reveal endpoint. Result: **5/5 LinkedIn URLs
   matched a real SignalHire profile (100%)**, and **3/5 (60%) returned a usable phone + email**.
   This confirms Apollo can serve as a lower-cost identity-discovery layer feeding SignalHire's
   reveal step, which is the expensive, high-value part of the pipeline we most want to protect.
   (For completeness: we also tested whether Apollo could return the phone number itself,
   bypassing SignalHire entirely. It technically can — we got back one real, high-confidence
   Indian mobile number — but it cost **9 credits for that single phone number** (1 for the
   match + 8 for the direct-dial reveal). At that price it is not a SignalHire replacement; we
   are asking for Apollo strictly as an identity layer, not a phone-reveal layer.)

4. **One-time cost estimate, now corrected to reflect one decision-maker per company, not
   three.** An earlier internal estimate assumed we'd need to enrich up to 3 executives per
   company. We ran a dedicated coverage test today specifically to check whether narrowing to
   just the single best-available decision-maker per company loses real coverage. Method: 30
   fresh companies from the backlog, cascading title search (founder/CEO first, widening only if
   that returns nobody). Result: **8 of 30 companies (26.7%) had anyone at all in Apollo's index**
   — India IT-services coverage is genuinely sparse, which is a real limitation of Apollo's
   database, not a config issue on our side — and of those 8, the large majority were resolved
   by the very first, narrowest title tier. Widening to 3 titles found zero additional companies
   that the 1-title search couldn't already find. **So the right one-time estimate, using one
   decision-maker per company (which is also how our existing SignalHire pipeline already
   works), is: 3,100 companies × 26.7% ≈ 825 people to enrich, at 1 credit each ≈ 825 Apollo
   credits, one-time** — not the 1,000–1,200 in an earlier draft of this estimate, and roughly a
   third of what a 3-execs/company assumption would have required.

## What we're asking finance to approve

Apollo.io Basic plan, 1 seat, starting on **monthly billing ($59/month)** rather than committing
to annual immediately — see the caveats below for why. We can switch to annual ($49/month
effective rate) once we've confirmed real usage patterns. Third-party research on Apollo's
current pricing pages indicates Basic includes **30,000 enrichment credits/year, granted
upfront** — if accurate, that comfortably covers our ~825-credit one-time backlog cost many
times over, with room for ongoing volume. This number is not yet confirmed against Apollo's own
in-app Billing page and should be treated as directional until we can verify it there directly.

## The one risk I want to flag clearly before we commit

**We have not been able to confirm, from Apollo's own documentation, that the Basic plan
includes API access to the specific endpoints we tested** (People Search and Bulk People
Enrichment / `bulk_match`). Apollo's own API pricing docs explicitly decline to give a
plan-by-plan endpoint map and direct customers to check their account's own Billing/Plans page
instead. Several independent third-party pricing breakdowns we checked suggest that full
programmatic API access — specifically bulk/custom integrations — may be reserved for the
Professional or Organization tier ($119+/user/month), with Basic offering more limited API
access. **All of our successful testing this week was run on a test API key with broadened
("master") scope, not a freshly-provisioned standard Basic-plan key** — so there is a real
chance that subscribing to Basic does not, by itself, grant the API access this entire proposal
is built on. Recommend either (a) getting written confirmation from Apollo sales that Basic
includes `people/search` and `people/bulk_match` API access before we pay, or (b) treating this
approval as conditional on that confirmation, with Organization tier as the fallback ask if it
turns out Basic doesn't cover it.

## Other caveats we can only test after the plan is actually active

1. **Real daily rate-limit behavior at production volume.** We've only run about 45–50 test API
   calls total. The commonly-cited 50,000/day figure is third-party, not from Apollo's own
   plan-comparison docs, and we haven't stress-tested it ourselves.
2. **Actual enrichment credit allotment and refill cadence.** Third-party sources now converge on
   ~30,000 credits/year for Basic (granted upfront), which is a much tighter number than the
   900–30,000 range we had before, but we still want to confirm it directly from Apollo's in-app
   Billing page once we're on the plan, rather than budget against secondhand figures.
3. **Whether our current account's test results reflect standard Basic-tier behavior or a
   broader allowance.** Directly tied to the API-access risk above — we want to confirm our
   validated 1-credit-per-person and 100% SignalHire-match numbers hold unchanged once we're
   formally on Basic with a standard key, not a master-scoped one.
4. **Seat-based pricing implications if more than one person needs API access.** Basic is priced
   per user; right now we're requesting a single seat, but if a second person needs concurrent
   access later, cost scales linearly.
5. **Overage pricing if actual usage exceeds the plan's included credits.** Not published
   anywhere we've found — we'll need to ask Apollo sales directly once we know our real usage
   rate.
6. **Credit delivery timing.** Apollo's own documentation states annual-billing credits are
   released entirely upfront for the year, while monthly billing may work differently. This
   affects how conservatively we should plan our initial rollout, which is why we're proposing to
   start on monthly billing until we understand this better.

## Bottom line

We have working proof, generated today with real API calls and verified credit deltas, that the
pipeline concept succeeds end-to-end: Apollo finds identities for free, converts them to a
LinkedIn URL for 1 credit each, and SignalHire's existing reveal step matches 100% of those URLs
with a 60% usable-contact yield. The one-time cost to clear the segment of our backlog Apollo can
actually resolve is a modest ~825 credits, comfortably inside Basic's likely ~30,000/year
allotment if that figure holds. The one real unknown — and the reason I'd like this approval
treated as conditional — is whether Basic's API scope actually includes the endpoints we tested,
since our validation ran on a broader-scoped test key. We're requesting to start on monthly
billing specifically so we can confirm API access and validate the other caveats within the
first cycle before committing to annual.

Happy to walk through any of this in more detail, including the raw test logs if useful. Let me
know if you need anything else to approve.

Best regards,
[Your Name]
