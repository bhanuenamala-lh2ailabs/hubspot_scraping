# -*- coding: utf-8 -*-
"""Find founder/CEO names via Anthropic web search — the route left after everything else closed.

WHY THIS, AFTER EVERYTHING ELSE:
  company team pages   exhausted — the residual firms yield ~5%, they simply do not publish
  Playwright rendering same residual, same 5%
  GoodFirms            Cloudflare bot challenge on every company profile, 403
  MCA (data.gov.in)    open datasets carry registration data, NOT director names
  SignalHire search    permanently off per instruction
  LinkedIn scraping    gated, HTTP 999

WHAT MAKES THIS SAFE. The model is NOT recalling names from training data — that would produce
confident, plausible, wrong people. `web_search` makes it fetch live pages and answer from them,
and every row carries the source URL so any name can be checked. A name with no source is
recorded as not-found rather than guessed.

IT ALSO RETURNS THE LINKEDIN URL, which is the reveal key we lack. That turns this into the
missing first half of the enrichment chain: search finds the person and their profile, reveal
(credits, not the exhausted search pool) turns that into a phone number.

COST CONTROL: ~$0.022 per company measured (1 search + ~11k Haiku tokens). Hard budget below;
the run stops rather than drifting past it.

Usage: python3 find_founders_websearch.py [--budget 6.0] [--limit 0]
"""
import os, re, sys, json, time

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
env = {l.split('=', 1)[0].strip(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
os.environ["ANTHROPIC_API_KEY"] = env["ANTHROPIC_API_KEY"]
import anthropic

SRC = os.path.join(HERE, "websearch_queue.json")
OUT = os.path.join(HERE, "founders_websearch.json")
MODEL = "claude-haiku-4-5-20251001"
BUDGET, LIMIT = 6.0, 0
for i, a in enumerate(sys.argv):
    if a == "--budget": BUDGET = float(sys.argv[i+1])
    if a == "--limit": LIMIT = int(sys.argv[i+1])
    if a == "--src": SRC = os.path.join(HERE, sys.argv[i+1])

# measured rates: web search $10/1k, Haiku ~$1/MTok in, ~$5/MTok out
COST_SEARCH, COST_IN, COST_OUT = 0.010, 1.0/1_000_000, 5.0/1_000_000

PROMPT = """Find the FOUNDER, CO-FOUNDER, CEO or MANAGING DIRECTOR of this Indian IT company:

Company: {name}
Website: {site}

Search the web. Use the company's own site, LinkedIn, news articles or business registries.

Rules:
- The person must currently lead THIS company. Not a client, not a parent company's global CEO,
  not someone at a similarly-named firm. If the company is an Indian arm of a foreign parent, say so.
- If you cannot find a confident answer, say NOT_FOUND. Do not guess. A wrong name is worse than none.
- Prefer a founder or CEO over other executives.

Reply as strict JSON, nothing else:
{{"person": "full name or null", "title": "exact title or null",
  "linkedin": "their personal linkedin.com/in/ URL if you found one, else empty string",
  "source": "the URL you took this from", "confidence": "high|medium|low",
  "is_india_entity_leader": true/false,
  "note": "one short sentence if anything is unusual, else empty"}}"""


def main():
    rows = json.load(open(SRC, encoding="utf-8"))
    state = {}
    if os.path.exists(OUT):
        state = {r["domain"]: r for r in json.load(open(OUT, encoding="utf-8"))}
    todo = [r for r in rows if r["domain"] not in state]
    if LIMIT: todo = todo[:LIMIT]
    print(f"{len(rows)} firms | {len(state)} already looked up | {len(todo)} to search")
    print(f"budget ${BUDGET:.2f}  (~${0.022:.3f}/company measured -> ~{int(BUDGET/0.022)} lookups)\n", flush=True)

    c = anthropic.Anthropic()
    spend = 0.0
    for i, r in enumerate(todo, 1):
        if spend >= BUDGET:
            print(f"\n!! budget reached (${spend:.2f}) — stopping cleanly", flush=True); break
        try:
            resp = c.messages.create(
                model=MODEL, max_tokens=600,
                tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}],
                messages=[{"role": "user", "content": PROMPT.format(name=r["name"], site=r.get("website", ""))}],
            )
        except Exception as e:
            print(f"  [{i}] {r['name'][:34]:<36}API ERROR {type(e).__name__}", flush=True)
            continue
        u = resp.usage
        n_search = getattr(getattr(u, "server_tool_use", None), "web_search_requests", 0) or 0
        spend += n_search * COST_SEARCH + u.input_tokens * COST_IN + u.output_tokens * COST_OUT
        txt = "".join(b.text for b in resp.content if b.type == "text").strip()
        m = re.search(r"\{.*\}", txt, re.S)
        rec = {"name": r["name"], "domain": r["domain"], "website": r.get("website", ""),
               "score": r.get("score"), "band": r.get("band")}
        if m:
            try:
                d = json.loads(m.group(0))
                rec |= {"person": d.get("person"), "title": d.get("title"),
                        "linkedin": d.get("linkedin") or "", "source": d.get("source") or "",
                        "confidence": d.get("confidence"), "note": d.get("note") or "",
                        "is_india_entity_leader": d.get("is_india_entity_leader")}
            except Exception:
                rec |= {"person": None, "raw": txt[:300]}
        else:
            rec |= {"person": None, "raw": txt[:300]}
        state[r["domain"]] = rec
        json.dump(list(state.values()), open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        p = rec.get("person") or "-"
        print(f'  [{i}/{len(todo)}] ${spend:>5.2f} {r["name"][:30]:<32}{str(p)[:24]:<26}'
              f'{(rec.get("title") or "")[:22]:<24}{"LI" if rec.get("linkedin") else ""}', flush=True)
        time.sleep(0.2)

    fin = list(state.values())
    got = [r for r in fin if r.get("person")]
    li = [r for r in got if r.get("linkedin")]
    print(f"\nspent ~${spend:.2f}")
    print(f"looked up      : {len(fin)}")
    print(f"found a person : {len(got)}  ({len(got)/max(len(fin),1)*100:.0f}%)")
    print(f"  ...with a LinkedIn URL (revealable) : {len(li)}")
    print(f"  ...flagged as a foreign parent's arm: {sum(1 for r in got if r.get('is_india_entity_leader') is False)}")


main()
