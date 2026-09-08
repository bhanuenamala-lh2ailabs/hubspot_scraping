IT Firm Relevancy Scorer — Instructions
You are scoring an Indian IT-services company's website to decide whether to contact them. Goal: find firms that follow a modern, reviewed git / pull-request workflow (engineering maturity).
A website is marketing, not a git server — so score by strength of evidence, treat a public repo as near-proof, and treat everything else as a probabilistic prior. Outsourced / staff-aug firms are in scope: judge them on the engineering signals below, not on whether the work was for a client.
Step 1 — Fetch these pages (not just the homepage)
/ , /careers (or /jobs) , /blog (and any Medium/Dev.to link) , /about , /team , /tech-stack , and footer social icons — scan for github.com/<org> / gitlab.com/<org>. Most real signal lives off the homepage. Record which pages you actually reached.
Step 2 — Score: engineering-maturity / PR practice (0–100)
Add points for each signal present. Keep evidence to a short snippet (<15 words) or paraphrase + where found.

Tier GOLD — Shipped software BEFORE 2024 (pre-vibe-coding era)
The firm must have been building real software before LLM-assisted coding was widespread. A
codebase written by a team that shipped pre-2024 is human-authored, reviewed and maintained;
one started after is likely to be substantially machine-generated, which is what we are trying
to avoid buying. This is the single most important signal — a firm that cannot evidence it is
capped at 45 no matter how strong the rest of its engineering story looks.
  Verified pre-2024 build activity (any ONE of, strongest first) → +25
    * VCS org whose EARLIEST merged PR / commit history predates 2024-01-01
    * Published OSS package with a pre-2024 release date
    * Wayback snapshot from before 2024-01-01 in which the site already advertises software
      development, a product, or a portfolio of delivered projects
    * Dated case studies, client projects or blog posts written before 2024-01-01
  Weak / inferred only (do NOT award the full +25, award +10) → founding year claimed pre-2024
    with no dated artefact to corroborate it. A founding date proves the company existed, not
    that it was writing software.
  No evidence either way → 0 and cap the total at 45.
Note: a site whose earliest Wayback snapshot is 2024 or later is a red flag, not a neutral.

Tier A — Verifiable (if present, mark confidence = Verified)
PRIVATE-REPO DISCIPLINE, evidenced from job descriptions → +40
  We are buying a codebase that has NEVER been public. A public repo therefore proves the wrong
  thing: that some of their code is already given away. It is also nearly absent here — 4 firms
  in 200 had one, 2 had real merged PRs — so it was scoring almost nobody while pointing the
  wrong way. What we want is evidence of pull-request discipline applied to code we cannot see,
  and a job description is exactly that: the firm describing how its engineers work on its own
  private repositories.
  Award +40 for a JD (or careers page) naming BOTH a private-repo host AND a review gate:
    * private-repo host — Bitbucket, Azure DevOps / TFS, self-hosted GitLab, AWS CodeCommit.
      Weight these highest: nobody hosts open source on them, so their presence is near-proof of
      a private codebase under version control.
    * review gate — "raise a PR", "review pull requests", "merge request", "peer review",
      "code review", "branching strategy", "GitFlow", "trunk-based"
  Award +25 if only ONE of the two appears.
Engineering blog with posts on code review, CI/CD, branching, or PR workflow → +20
A public VCS org is now worth 0. Record it as a note if found, but do NOT score it, and never
attribute a vendor's org (twbs, newrelic, wix, wordpress, google) to the firm whose page links it.
Tier B — Strong process proxies
Careers/JD mentions Git, CI/CD or peer review but WITHOUT a named private-repo host → +25
  (if it also names Bitbucket/Azure DevOps/self-hosted GitLab, score it under Tier A instead —
   do not count the same JD twice)
Enforced quality gates named: SonarQube, coverage threshold, "definition of done" → +10
Substantive CI/CD + DevOps (IaC, pipelines, named tools) → +15
Dedicated QA / test-automation in pipeline ("shift-left") → +10
Change-control compliance: SOC 2, ISO 27001/9001, CMMI ≥3, HIPAA → +10
Tier C — Positioning proxies (only count if ≥2 co-occur; cap combined at +20)
"Product engineering" / "platform engineering" as a named capability → +5
Owns products / accelerators / platforms (long-lived codebases) → +8
Senior eng roles named (Staff/Principal/VP Eng, SRE, Architect) → +5
Enterprise / regulated clients → +5
Detailed SDLC "how we work" or tech-stack page → +5
Cap total at 100.
Step 3 — Disqualifiers / caps (apply after summing)
Generalist-agency signature — dev bundled with SEO/PPC/SMM/content marketing/IT support/networking/helpdesk/training → cap at 30
"MVP in X days guaranteed," template/portfolio/website-builder shop → −15
No careers page AND no blog AND no team page → cap at 40
BPO / managed-IT-support / data-entry core business → cap at 20
Notes: "serves many industries" is not a positive signal — body shops serve many industries too; award nothing for breadth. Do not penalize a firm merely for being outsourced / staff-aug; if they still show code review, CI/CD, or a real careers page, that signal counts.
Step 4 — Final relevancy band
Score
Relevancy
≥70
Priority — contact
50–69
Secondary — worth a look
<50
Skip

Scoring rules
JD text is now the primary evidence, so it must actually be COLLECTED. Many firms post roles via
Greenhouse, Lever or Naukri rather than on their own careers page; follow those links and read the
listing. A firm scored on an on-page careers blurb alone is being scored on marketing copy.
Confidence = Verified requires JD-level evidence of a private-repo host or an explicit review gate.
Tier GOLD is a gate, not a bonus: no pre-2024 evidence caps the total at 45, so such a firm can
never reach Priority however good its CI/CD story reads. Apply the cap AFTER summing, alongside
the Step 3 caps, and take the lowest cap that applies.
Tier C never fires on a single buzzword — require corroboration with a Tier A/B signal.
Confidence = Verified only if a Tier A signal was found; otherwise Inferred.
A VCS org only counts as the firm's own if the org name matches the company name or its domain.
Do not award points for github.com links to vendors or dependencies (twbs, newrelic, vercel…) —
those appear on a page because the site USES that library, not because the firm wrote it.
Absence of signal ≠ absence of practice → a low score means deprioritize, not exclude.
Judge substance, not keywords: decide whether "product engineering" is real or decorative.
Output  make a csv


