# -*- coding: utf-8 -*-
"""Render the team pages plain HTTP could not read, for the Bangladesh firms still missing a name.

60 of the 100 have no founder name yet. On the NASSCOM run the identical situation turned out to
be mostly JavaScript: rendering recovered pages for 16 of 30 firms whose nav urllib could not see,
including Xebia, which has 615 merged PRs and was being rejected for "no careers page".

A name matters here beyond the CRM record: SignalHire's company search returns several profiles
per firm, and a scraped name is what lets the enrichment pick the right one instead of revealing
whoever ranks first. So each name recovered now makes a later credit spend more accurate.

Only runs on firms with no name. Rendering costs ~100x a plain GET, so it is not run wholesale.

Usage: python3 bd_render_teams.py [--limit 0]
"""
import os, re, sys, json, time, collections

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "bd_consolidated.json")
OUT = os.path.join(HERE, "bd_rendered_teams.json")
PREFIX = "bdr"
LIMIT = 0
for i, a in enumerate(sys.argv):
    if a == "--limit": LIMIT = int(sys.argv[i+1])
    if a == "--src": SRC = os.path.join(HERE, sys.argv[i+1])
    if a == "--out": OUT = os.path.join(HERE, sys.argv[i+1])
    if a == "--prefix": PREFIX = sys.argv[i+1]

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
WANT = r"(team|leadership|management|about|who-we-are|our-people|company|founder|director)"
KEY = re.compile(r"(founder|chief executive|\bceo\b|managing director|\bmd\b|chairman|"
                 r"proprietor|\bcto\b|director)", re.I)


def main():
    from playwright.sync_api import sync_playwright
    rows = json.load(open(SRC, encoding="utf-8"))
    todo = [r for r in rows if not r["founder"]]
    if LIMIT: todo = todo[:LIMIT]
    print(f"{len(rows)} firms | {len(todo)} without a name -> rendering", flush=True)

    out, t0 = [], time.time()
    with sync_playwright() as p:
        br = p.chromium.launch(headless=True)
        for i, r in enumerate(todo, 1):
            rec = {"name": r["name"], "domain": r["domain"], "pages": [],
                   "text": "", "linkedin_profiles": []}
            site = r["website"] if r["website"].startswith("http") else "http://" + r["website"]
            try:
                pg = br.new_page(user_agent=UA)
                pg.set_default_timeout(20000)
                pg.goto(site, wait_until="domcontentloaded"); pg.wait_for_timeout(2200)
                m = re.match(r"(https?://[^/]+)", pg.url); root = m.group(1) if m else site
                hrefs = pg.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
                cand, seen = [], set()
                for h in hrefs:
                    if not h.startswith(root) or h in seen: continue
                    if re.search(WANT, h, re.I): seen.add(h); cand.append(h)
                chunks = []
                for u in cand[:4]:
                    try:
                        pg.goto(u, wait_until="domcontentloaded"); pg.wait_for_timeout(1600)
                        t = re.sub(r"\s+", " ", pg.inner_text("body"))
                        if len(t) < 200: continue
                        rec["pages"].append(u)
                        # keep only the sentences that talk about people
                        keep = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n|\s{2,}", t)
                                if 8 <= len(s.strip()) <= 260]
                        hits = [s for s in keep if KEY.search(s)]
                        chunks.append(" | ".join(hits[:30] if hits else keep[:20]))
                        for a in pg.eval_on_selector_all("a[href*='linkedin.com/in/']", "els => els.map(e => e.href)"):
                            if a not in [x["url"] for x in rec["linkedin_profiles"]]:
                                rec["linkedin_profiles"].append({"url": a, "context": ""})
                    except Exception:
                        continue
                rec["text"] = " || ".join(chunks)[:3000]
                pg.close()
            except Exception as e:
                rec["error"] = type(e).__name__
                try: pg.close()
                except Exception: pass
            out.append(rec)
            json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            if i % 10 == 0:
                got = sum(1 for x in out if len(x["text"]) > 200)
                print(f"   {i}/{len(todo)}  {time.time()-t0:.0f}s  usable {got}", flush=True)
        br.close()

    usable = [r for r in out if len(r["text"]) > 200 or r["linkedin_profiles"]]
    print(f"\ndone in {time.time()-t0:.0f}s -> {os.path.basename(OUT)}")
    print(f"now have readable people-page text : {len(usable)}/{len(out)}")
    print(f"with a linkedin profile on the page: {sum(1 for r in out if r['linkedin_profiles'])}")
    os.makedirs(os.path.join(HERE, "bd_batches"), exist_ok=True)
    per, n = 22, 0
    for i in range(0, len(usable), per):
        n += 1
        json.dump(usable[i:i+per],
                  open(os.path.join(HERE, "bd_batches", f"{PREFIX}_{n}.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    print(f"wrote {n} batches -> bd_batches/bdr_*.json")


main()
