# HubSpot Personal Templates — ready to paste

No public API exists for personal/sales templates, so these have to go in via
Settings → Templates (or "Insert template → New template" from the compose window)
while logged in as Yuktha, Lamiya, or whoever has working UI access.

Tokens used are HubSpot's real personalization syntax — they'll resolve automatically
to the record you're composing from (the contact tied to the deal open in the CRM, or
the deal itself if sending from a deal record). No manual fill-in needed per send.

---

## Template 1: Script Share Email

**Subject suggestion:** Next step — running the script for {{deal.dealname}}

Hi {{contact.firstname}},

Thanks for the chat today. It was great connecting with you!

As mentioned on the call, we're currently procuring large-scale private projects on behalf of Frontier AI Labs. We're specifically looking for production-grade, manually written code (pre-2024) that hasn't been publicly hosted. This could include internal tools, past client deployments, or systems that are no longer actively commercialised.

Given you mentioned having such projects, this could be a strong fit.

For next steps you'll have to run the script we shared, which can run offline as well (attached in this mail). This is the step that moves us towards the commercial side, so we're now one step closer to getting an actual offer in front of you.

Quick note on what it does: the tool scans your code projects and generates a quality report for each one, covering how many files and tests exist, the LOC, PRs and commit spread, Git history, how healthy the development process looks, and whether CI/CD pipelines are set up.

The report itself is just these metrics and counts — your actual source code isn't part of what gets shared at this stage.

It works with GitHub, GitLab, Subversion (SVN), and local folders on your machine, so whatever you're running should be covered. I've attached a PDF with step-by-step instructions to get it going — it's fairly quick, but if there are any issues at all, just reply here or drop me a message, and I'll walk you through it.

Once you loop in the Tech POC, I'd love to get a more detailed understanding of your projects. As mentioned on the call, we look at your LOC, PRs and commits on a project level and then share commercials once qualified.

Looking forward to moving ahead with the process!

*(Attach: the script tool + the step-by-step PDF — these don't personalize per deal, so keep them as static attachments on the template if HubSpot allows attachments on personal templates; otherwise attach manually each send.)*

---

## Template 2: Intro Mail — with scheduling ask

**Subject suggestion:** Following up — {{contact.company}} codebase licensing

Hi {{contact.firstname}},

Thanks for the quick chat, it was great connecting with you!

To quickly recap, LH2 AI Labs licenses pre-2024 proprietary codebases (unlaunched bench projects, internal tools, and shelved MVPs) to supply frontier AI labs.

To be absolutely clear: we only want assets where you fully retain the IP. We do not touch your active client work.

This essentially offers a quick liquidity event for your shelved projects that are just sitting on your Git/local server and gathering dust. In just the last 2 months we have licensed over 100+ million lines of code from IT firms.

Here is a step-by-step breakdown of how our licensing process works:
1. **Local Audit** — we share a lightweight script that you run locally on your end. It only counts structural metadata (lines of code, PRs, commits, and languages). Zero source code leaves your network during this step.
2. **Evaluation** — you share the generated output report with us.
3. **Valuation & Closing** — we review the metrics and come back to you with a formal licensing offer within a day's time and proceed with closing if everything qualifies.

I would love to schedule a quick GMeet between us so I can walk you through our process in more detail. Let me know a day and time that works for a quick 10-minute chat — would love to discuss how we can monetize any of your assets.

*(Original had a hardcoded "3:00 PM today" — removed since that's dead the moment it's reused. If you want a standing scheduling link instead of asking for a time, use Template 3's Calendly line.)*

---

## Template 3: Intro Mail — with Calendly + social proof

**Subject suggestion:** {{contact.company}} — turning shelved code into cash

Hi {{contact.firstname}},

Great speaking with you earlier today.

To quickly recap, LH2 AI Labs licenses pre-2024 proprietary codebases (unlaunched bench projects, internal tools, and shelved MVPs) to supply frontier AI labs. To be clear: we only want assets where you fully retain the IP.

It's essentially a fast liquidity event for software assets that are just gathering dust. We recently licensed over 100M+ lines of code, helping founders turn unused R&D into immediate cash. We move fast — the whole process clears in under a week.

If you'd like to discuss further, please let me know a day and time that works best for you and I'll be happy to set up a call with the team. Alternatively, you can book a slot here: https://calendly.com/lh2-ai_labs/discovery-call?utm_source=linkedin&utm_medium=social&utm_campaign=linkedin_outreach&utm_content=engage

To vouch for us, check out our founder's profile: https://www.linkedin.com/in/upneet-grover-19612315/

I am attaching our proposal deck. If you have any questions, please feel free to reach out.

Looking forward to speaking with you!

*(Attach: the proposal deck — static, not deal-specific.)*

---

### Notes on the tokens
- `{{contact.firstname}}` and `{{contact.company}}` are standard HubSpot contact/company properties — they'll populate automatically once the template is inserted from a contact/deal record.
- If your portal's company name property isn't populated for a given deal (many of ours aren't — most sourced leads have `lh2_domain` but no linked Company object), `{{contact.company}}` will render blank. Worth checking before relying on it — I can pull the actual coverage number if useful.
- The subject-line suggestions aren't in the original text — added for convenience, feel free to drop or edit them.
