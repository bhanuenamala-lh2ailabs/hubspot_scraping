# Claude Code Task: Bulk-scrape LinkedIn company + people data via Apify actors

## Context
I have one CSV file with a list of people (CEOs/CTOs/founders/owners) that includes
their LinkedIn profile URL, plus columns like First Name, Last Name, Headline,
Location, Company (text name only, NOT a URL), and Title. I do NOT have a separate
list of company LinkedIn URLs — I only have company names as plain text, which
isn't reliable enough to feed directly into a company-data actor (names collide
across companies/regions).

So the plan is a two-stage scrape:
1. Scrape the people first using their profile URLs.
2. From the people scrape results, extract each person's CURRENT company's LinkedIn
   URL from their work history/experience data (profile scrapers typically return a
   company URL alongside each experience entry, since it's linked data on the
   LinkedIn profile page itself).
3. Deduplicate those extracted company URLs (many people will share the same
   employer) and run the company actor on that clean, deduplicated list.

This avoids needing a separate company-URL source entirely. I will later pass both
outputs through an LLM myself for filtering (that part is handled separately — just
get me clean scraped data as the output of this task).

## Inputs (fill in before running)
- Apify API token: `<PASTE_YOUR_APIFY_API_TOKEN_HERE>`
- People CSV path: `<PASTE_FULL_PATH_TO_PEOPLE_CSV_HERE>`
  - Expected columns include something like: First Name, Last Name, Headline,
    Location, Company, Title, LinkedIn URL — inspect the actual header first and
    confirm which column holds the profile URL (likely "LinkedIn URL") before
    proceeding.

## Actors to use
1. **Person data**: Apify actor `harvestapi/linkedin-profile-scraper`
2. **Company data**: Apify actor `harvestapi/linkedin-company`

## Step 1 — Environment setup
- Check for Python 3.10+ and pip/uv availability.
- Install the `apify-client` Python package (official Apify SDK) if not already
  present.
- Do NOT hardcode the API token directly into any script file that might get
  committed to git or left lying around — read it from an environment variable
  (e.g. `APIFY_API_TOKEN`) that I'll set in my shell, or from a local `.env` file
  that is explicitly gitignored if this directory has git initialized. Check for a
  `.git` folder and add `.env` to `.gitignore` if one doesn't already exist.

## Step 2 — Inspect the input CSV
- Load the people CSV and print its column headers and first 2-3 rows so I (and
  you) can confirm which column holds the actual profile URL.
- Count total rows and report the number back to me before proceeding, since this
  affects Apify cost (~$4/1,000 for people, ~$3/1,000 for companies) — if the file
  has more than 2,000 rows, pause and confirm with me before running the full
  batch, in case I want to test on a smaller sample first.
- Deduplicate profile URLs if there are obvious exact-string duplicates before
  sending to Apify.

## Step 3 — Run the people scraper
- Using the Apify Python client, call the `harvestapi/linkedin-profile-scraper`
  actor with the full list of profile URLs as input (check the actor's input
  schema via the Apify API/console documentation to confirm the exact input field
  name expected — don't guess blindly, verify it first).
- Run it synchronously if the row count is small enough to complete within a
  reasonable timeout, otherwise start the run and poll for completion, printing
  periodic progress updates rather than going silent for a long stretch.
- Once complete, fetch the resulting dataset items via the API.
- Save the raw JSON response for each profile too (not just the flattened CSV),
  since we need to inspect the experience/work-history structure in the next step.

## Step 4 — Extract current-company LinkedIn URLs from the people data
- For each scraped profile, inspect the `experience` array (or equivalently named
  field — confirm actual field name from the real response) and find the entry
  corresponding to the person's CURRENT role (typically the one with no end date,
  or an end date/text of "Present", or flagged as current some other way — inspect
  the actual data structure to determine the right signal rather than assuming).
- From that current-role entry, extract the company's LinkedIn URL if the field
  exists (look for something like `companyUrl`, `companyLinkedinUrl`, or a URL
  nested inside a company object — inspect real output to find the correct field,
  since exact naming may differ from assumptions here).
- If a meaningful portion of profiles (say, more than ~20%) don't have a usable
  company URL in their experience data, stop and tell me rather than silently
  proceeding with a partial list — we may need a different approach (e.g. deriving
  company URLs from company name + location via a search-based method instead).
- Deduplicate the extracted company URLs (many people will share the same
  employer) before moving to the next step, and keep a mapping of which person(s)
  belong to which company URL so we can rejoin the data later.

## Step 5 — Run the company scraper
- Using the deduplicated list of company URLs from Step 4, call the
  `harvestapi/linkedin-company` actor (confirm its expected input field name via
  its own documentation/input schema — don't assume it matches the people actor's
  schema).
- Poll for completion with progress updates as in Step 3.
- Fetch the resulting dataset items via the API.

## Step 6 — Save clean output
- Save the people scrape results to a CSV, flattening `experience` into a readable
  form — at minimum surface current title, current company name, current company
  LinkedIn URL, and tenure/duration at the current role as top-level columns, and
  keep the full experience history as a JSON-string column for anything needing
  deeper detail later.
- Save the company scrape results to a CSV, flattening nested fields sensibly —
  e.g. `industries` as a comma-joined string, `foundedOn.year` as its own column,
  `employeeCount`, `description`, `specialities`, `website` as their own columns.
- Also save a simple join/mapping file (or add a `company_linkedin_url` column
  directly to the people CSV) so each person row can be matched to their
  corresponding company row later — this is important since the LLM filtering
  step will likely need both a person's and their company's data together.
- Save all outputs into a clearly named local folder, e.g.
  `~/linkedin-scrape-results/people_scraped.csv`,
  `~/linkedin-scrape-results/companies_scraped.csv`.
- If any input URLs (people or derived companies) failed to return data (blocked,
  private, deleted profile/page, etc.), save those separately into a
  `failed_urls.csv` so I know what didn't come through, rather than silently
  dropping them.

## Step 7 — Final report
Give me a short summary:
- Total people URLs attempted vs. successfully scraped vs. failed
- How many unique company URLs were successfully extracted from the people data,
  and what percentage of people rows had NO extractable company URL (flag this
  clearly since it may mean some people won't have matching company data)
- Total company URLs attempted vs. successfully scraped vs. failed
- Approximate total cost incurred (based on Apify's per-1,000 pricing for each
  actor)
- File paths of the output CSVs and the failed-URLs file
- Any data quality issues noticed (e.g. many rows missing `foundedOn.year` or
  `employeeCount` on the company side — flag this since it affects my downstream
  filtering)

## Constraints
- Don't attempt the LLM filtering step — that's handled separately by me.
- Don't proceed with a full run on more than 2,000 people rows without confirming
  with me first.
- Don't hardcode or print the full API token in any log output, file, or terminal
  output beyond what's needed to authenticate — treat it as a secret.
- If the actor input schema differs from what's assumed above, adapt and tell me
  what you found rather than forcing a mismatched input format.
- If the people scraper's experience data doesn't cleanly expose a company URL at
  all (not just partially, but structurally absent), stop and report this clearly
  rather than trying to work around it with guesses (e.g. don't try to construct a
  company URL from a company name string — that's unreliable and defeats the
  purpose of using structured data).