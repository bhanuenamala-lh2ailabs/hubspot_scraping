# -*- coding: utf-8 -*-
"""Rough-qualifies the Gujarat LinkedIn Sales Nav companies using ONLY data already in the
sheet (headline, title, company name) — no crawling, no web fetches. Uses Claude Haiku via
the Anthropic API (cheap) to judge fit against our actual ICP: small/mid Indian IT-services
or software companies that plausibly own a dormant/legacy codebase — not big tech, not NGOs,
not personal-brand-only consultants/coaches, not recruiting/staffing shops, not students.

Usage: python3 qualify.py
"""
import os, csv, json, collections, time
import anthropic

HUB = "/Users/bhanu/Desktop/hubspot"
env = {l.split('=',1)[0].strip().lower(): l.split('=',1)[1].strip()
       for l in open(os.path.join(HUB, ".env"), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
client = anthropic.Anthropic(api_key=env["anthropic_api_key"])
MODEL = "claude-haiku-4-5-20251001"

IN_CSV = os.path.join(HUB, "temporary", "Gujarat_IT_Linkedin Sales Nav.csv")
OUT_JSON = os.path.join(os.path.dirname(__file__), "scores.json")
BATCH = 25

rows = list(csv.DictReader(open(IN_CSV, encoding="utf-8-sig")))
by_company = collections.defaultdict(list)
for r in rows:
    by_company[r["Company"].strip()].append(r)

companies = list(by_company.items())
print(f"{len(companies)} distinct companies, {len(rows)} people total")

PROMPT_TMPL = """You are screening Indian companies for a very specific acquisition target:
LH2 AI Labs buys DORMANT SOFTWARE CODEBASES from small/mid Indian IT-services or software
product companies (roughly 10-250 employees) who built custom software, retained the IP, and
no longer actively maintain/monetise it fully.

GOOD fit: small/mid IT-services or software product company, agency, or dev shop. The person
listed is a real founder/owner/CTO/senior tech decision-maker there.

BAD fit (score low): big tech / MNCs / frontier AI labs, NGOs/nonprofits/foundations,
personal-brand-only coaches/consultants/trainers/speakers with no real company codebase,
recruiting/staffing/HR-only firms, students/interns, marketing/ad agencies with no software
product, hardware/manufacturing/non-software companies, generic "consulting" with no evidence
of an actual software codebase.

For each company below, using ONLY the data given (no outside knowledge), return a JSON array
with one object per company: {{"company": "<exact name as given>", "score": <0-100 integer>,
"reason": "<one short phrase>"}}. Score reflects how well it fits the GOOD profile above.

Companies:
{block}

Return ONLY the JSON array, nothing else."""

def make_block(batch):
    lines = []
    for company, people in batch:
        ppl = "; ".join(f'{p["Title"]} — "{p["Headline"][:140]}"' for p in people[:3])
        lines.append(f'- COMPANY: {company}\n  PEOPLE: {ppl}')
    return "\n".join(lines)

results = {}
batches = [companies[i:i+BATCH] for i in range(0, len(companies), BATCH)]
for bi, batch in enumerate(batches, 1):
    block = make_block(batch)
    msg = client.messages.create(
        model=MODEL, max_tokens=4000,
        messages=[{"role": "user", "content": PROMPT_TMPL.format(block=block)}],
    )
    text = msg.content[0].text.strip()
    if text.startswith("```"):
        text = text.strip("`"); 
        if text.startswith("json"): text = text[4:]
    try:
        arr = json.loads(text)
    except Exception as e:
        print(f"  batch {bi}: PARSE FAILED ({e}), skipping"); continue
    for item in arr:
        results[item["company"]] = item
    print(f"  batch {bi}/{len(batches)}: scored {len(arr)} companies", flush=True)
    json.dump(results, open(OUT_JSON, "w"), indent=1)
    time.sleep(0.3)

print(f"\ntotal scored: {len(results)}/{len(companies)}")
ranked = sorted(results.values(), key=lambda x: -x["score"])
top300 = ranked[:300]
print(f"top 300 cutoff score: {top300[-1]['score']}")
json.dump({"all": results, "top300_companies": [x["company"] for x in top300]},
          open(OUT_JSON, "w"), indent=1)
