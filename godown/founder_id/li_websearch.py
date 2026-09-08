# -*- coding: utf-8 -*-
"""LinkedIn URL for the 349 MCA-named founders, via Anthropic web search. HARD $10 cap.

We already KNOW each person (name + title + company, MCA-registry-cited). This asks only for
their linkedin.com/in URL — a far tighter query than blind founder-finding, so yield should
beat the earlier 42%. web_search makes the model read live results rather than recall a URL;
every accepted URL is regex-checked and the person is re-verified again at reveal time
(enrich_push skips any reveal whose returned name doesn't match the MCA name), so a slightly
wrong URL costs at most one failed lookup, never a wrong-person push.

Resolved rows flip to status='full' -> enrich_push.py reveals + gates +91 + pushes 50:50.
Runs alongside any Apify URL source; dedup at push handles overlap.

Usage: python3 li_websearch.py [--budget 10] [--limit N]
"""
import os, re, sys, json, time, sqlite3

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
DBP = os.path.join(HERE, "resolver.sqlite")
env = {l.split('=', 1)[0].strip(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
os.environ["ANTHROPIC_API_KEY"] = env["ANTHROPIC_API_KEY"]
import anthropic

MODEL = "claude-haiku-4-5-20251001"
BUDGET, LIMIT = 10.0, 0
for i, a in enumerate(sys.argv):
    if a == "--budget": BUDGET = float(sys.argv[i + 1])
    if a == "--limit": LIMIT = int(sys.argv[i + 1])
COST_SEARCH, COST_IN, COST_OUT = 0.010, 1.0 / 1_000_000, 5.0 / 1_000_000
LI_RX = re.compile(r"^https?://([a-z]{2,3}\.)?linkedin\.com/in/[^/?#]+/?$")

PROMPT = """Find the personal LinkedIn profile URL of this specific person. I already know who
they are — I only need their linkedin.com/in/ profile URL, confirmed by web search.

Person: {person}
Title: {title}
Company: {company}  ({site}, {city}, India)

Search the web (LinkedIn, the company site, news). Return the URL ONLY if a search result
clearly shows THIS person at THIS company — not a namesake. If you cannot confirm it, return an
empty string. A wrong profile is worse than none.

Reply as strict JSON, nothing else:
{{"linkedin": "https://www.linkedin.com/in/... or empty string",
  "matches_company": true/false,
  "source": "the result URL that confirmed it",
  "confidence": "high|medium|low"}}"""


def tokens(s):
    return {t for t in re.sub(r"[^a-z0-9 ]", " ", (s or "").lower()).split() if len(t) > 2}


def main():
    con = sqlite3.connect(DBP)
    rows = [(dom, json.loads(data)) for dom, data in
            con.execute("SELECT domain, data FROM companies WHERE status='name_only'")]
    todo = [(d, r) for d, r in rows if not r.get("li_ws_done")]
    if LIMIT: todo = todo[:LIMIT]
    print(f"{len(rows)} named | {len(todo)} to search | budget ${BUDGET:.2f} "
          f"(~$0.02/lookup -> ~{int(BUDGET/0.02)} max)\n", flush=True)

    c = anthropic.Anthropic()
    spend = 0.0; found = 0
    for i, (dom, r) in enumerate(todo, 1):
        if spend >= BUDGET:
            print(f"\n!! ${spend:.2f} — budget reached, stopping cleanly", flush=True); break
        person, title, company = r["founder_name"], r.get("title", "Director"), r["company"]
        try:
            resp = c.messages.create(
                model=MODEL, max_tokens=500,
                tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}],
                messages=[{"role": "user", "content": PROMPT.format(
                    person=person, title=title, company=company,
                    site=dom, city=r.get("city", ""))}])
        except Exception as e:
            print(f"  [{i}] {company[:30]:<32}API ERROR {type(e).__name__}", flush=True)
            time.sleep(1); continue
        u = resp.usage
        ns = getattr(getattr(u, "server_tool_use", None), "web_search_requests", 0) or 0
        spend += ns * COST_SEARCH + u.input_tokens * COST_IN + u.output_tokens * COST_OUT
        txt = "".join(b.text for b in resp.content if b.type == "text").strip()
        m = re.search(r"\{.*\}", txt, re.S)
        url = ""; conf = ""
        if m:
            try:
                d = json.loads(m.group(0))
                cand = (d.get("linkedin") or "").split("?")[0].rstrip("/")
                conf = d.get("confidence", "")
                # Keep any /in/ URL the model confirms is THIS company's person. The slug-token
                # check was dropping real URLs (LinkedIn slugs are often initials/numbers);
                # the true person-gate is at reveal, where enrich_push compares the revealed
                # fullName to the MCA name and skips mismatches. Defence in depth, not here.
                if LI_RX.match(cand) and d.get("matches_company"):
                    url = cand; r["li_source"] = d.get("source", "anthropic web search")
            except Exception:
                pass
        r["li_ws_done"] = True
        if url:
            found += 1; r["linkedin_url"] = url; r["li_confidence"] = conf
            con.execute("UPDATE companies SET status='full', data=? WHERE domain=?", (json.dumps(r), dom))
        else:
            con.execute("UPDATE companies SET data=? WHERE domain=?", (json.dumps(r), dom))
        con.commit()
        print(f'  [{i}/{len(todo)}] ${spend:>5.2f} {company[:28]:<30}{person[:20]:<22}'
              f'{(url or "-")[:42]:<44}{conf}', flush=True)
        time.sleep(0.2)

    st = con.execute("SELECT COUNT(*) FROM companies WHERE status='full'").fetchone()[0]
    print(f"\nspent ~${spend:.2f} | found {found} URLs this run | total status=full now {st}")
    print("next: python3 enrich_push.py --apply   (reveal + +91 gate + 50:50 push)")


main()
