# -*- coding: utf-8 -*-
"""Find a known founder's LinkedIn profile URL — the cheapest remaining path to a phone number.

56 firms have a founder NAME (from the earlier web-search pass) but no profile URL. A name alone
is not enough: SignalHire's reveal takes a LinkedIn URL as its key, and the searchByQuery endpoint
that could work from a company name is permanently off. So one targeted search per person turns a
dead name into a revealable lead.

Cheaper than the earlier pass because the question is narrower — we already know who we are
looking for, so one search usually settles it rather than three.

VERIFICATION MATTERS MORE THAN COVERAGE. A wrong profile URL costs a credit AND produces a wrong
person's phone number, which is worse than no number at all. The model is told to return empty
rather than a plausible-looking guess, and to reject profiles where the person's current employer
does not match.

Usage: python3 find_linkedin_websearch.py [--budget 2.5]
"""
import os, re, sys, json, time

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
env = {l.split('=', 1)[0].strip(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
os.environ["ANTHROPIC_API_KEY"] = env["ANTHROPIC_API_KEY"]
import anthropic

SRC = os.path.join(HERE, "q_needli.json")
OUT = os.path.join(HERE, "linkedin_found.json")
MODEL = "claude-haiku-4-5-20251001"
BUDGET = 2.5
for i, a in enumerate(sys.argv):
    if a == "--budget": BUDGET = float(sys.argv[i+1])
    if a == "--src": SRC = os.path.join(HERE, sys.argv[i+1])
    if a == "--out": OUT = os.path.join(HERE, sys.argv[i+1])

COST_SEARCH, COST_IN, COST_OUT = 0.010, 1.0/1_000_000, 5.0/1_000_000

PROMPT = """Find the personal LinkedIn profile URL for this person:

Name: {person}
Title: {title}
Company: {company} (an Indian IT services firm)
Company website: {site}

Search the web for their LinkedIn profile.

Rules:
- It must be THIS person at THIS company. Indian names are common; if the profile you find works
  somewhere else, it is the wrong person — return an empty url.
- Must be a personal profile (linkedin.com/in/...), NOT a company page (linkedin.com/company/...).
- If you cannot confirm it is them, return an empty url. A wrong profile is worse than none:
  it costs a lookup and produces a stranger's phone number.

Reply as strict JSON only:
{{"url": "https://www.linkedin.com/in/... or empty string",
  "confidence": "high|medium|low",
  "why": "one short phrase on how you confirmed it, or why you could not"}}"""


def main():
    rows = json.load(open(SRC, encoding="utf-8"))
    state = {}
    if os.path.exists(OUT):
        state = {r["domain"]: r for r in json.load(open(OUT, encoding="utf-8"))}
    todo = [r for r in rows if r["domain"] not in state]
    print(f"{len(rows)} people | {len(state)} done | {len(todo)} to look up | budget ${BUDGET:.2f}\n", flush=True)

    c = anthropic.Anthropic()
    spend = 0.0
    for i, r in enumerate(todo, 1):
        if spend >= BUDGET:
            print(f"\n!! budget reached (${spend:.2f}) — stopping", flush=True); break
        try:
            resp = c.messages.create(
                model=MODEL, max_tokens=350,
                tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 2}],
                messages=[{"role": "user", "content": PROMPT.format(
                    person=r["person"], title=r.get("title") or "", company=r["name"],
                    site=r.get("website", ""))}],
            )
        except Exception as e:
            print(f"  [{i}] {r['name'][:30]:<32}API ERROR {type(e).__name__}", flush=True); continue
        u = resp.usage
        ns = getattr(getattr(u, "server_tool_use", None), "web_search_requests", 0) or 0
        spend += ns * COST_SEARCH + u.input_tokens * COST_IN + u.output_tokens * COST_OUT
        txt = "".join(b.text for b in resp.content if b.type == "text").strip()
        m = re.search(r"\{.*\}", txt, re.S)
        url, conf, why = "", "", ""
        if m:
            try:
                d = json.loads(m.group(0))
                url = (d.get("url") or "").strip()
                conf, why = d.get("confidence", ""), d.get("why", "")
            except Exception:
                pass
        if "linkedin.com/in/" not in url: url = ""      # company pages and prose are not keys
        rec = dict(r); rec |= {"linkedin": url, "li_confidence": conf, "li_why": why}
        state[r["domain"]] = rec
        json.dump(list(state.values()), open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f'  [{i}/{len(todo)}] ${spend:>5.2f} {r["name"][:28]:<30}{r["person"][:22]:<24}'
              f'{"FOUND" if url else "-":<7}{conf}', flush=True)
        time.sleep(0.15)

    fin = list(state.values())
    got = [r for r in fin if r.get("linkedin")]
    print(f"\nspent ~${spend:.2f}")
    print(f"found a profile URL: {len(got)}/{len(fin)}  ({len(got)/max(len(fin),1)*100:.0f}%)")
    print(f"   high confidence : {sum(1 for r in got if r.get('li_confidence')=='high')}")


main()
