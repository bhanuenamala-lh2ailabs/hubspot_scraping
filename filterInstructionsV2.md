I have a CSV file named 'bangladesh_software_companies.csv' with columns: 'name', 'website', 'description'.

Write and execute a Python script to do the following:
1. Read 'bangladesh_software_companies.csv'.
2. For each URL in the 'website' column, fetch the homepage text and attempt to fetch the '/careers' or '/about' subpage using `httpx` or `aiohttp` with a realistic browser User-Agent.
3. Pass the combined page text to the Claude API to classify the company.
4. Evaluation criteria:
   - RELEVANT (Score 7-10): Custom software development, enterprise web/mobile apps, dedicated engineering teams, explicit mentions of CI/CD, Git, Pull Requests, Agile, SaaS, cloud infrastructure, or custom backend engineering.
   - IRRELEVANT (Score 1-4): Generic WordPress/Wix agencies, basic digital marketing/SEO firms, BPO/call centers, graphic design agencies, or broken/inactive websites.
5. Append 3 new columns to the CSV:
   - 'relevance_status' (RELEVANT / IRRELEVANT)
   - 'lead_score' (1-10)
   - 'qualification_reason' (1 concise sentence explaining why)
6. Save the final results to 'bangladesh_software_companies_qualified.csv'.

Handle timeouts, missing websites, and errors gracefully without stopping the loop. Run this script now.