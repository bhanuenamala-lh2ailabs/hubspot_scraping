# -*- coding: utf-8 -*-
"""Re-fetch careers/blog/team for firms the plain-HTTP crawler could not see them on.

WHY. The rubric caps a company at 40 when it has no careers page AND no blog AND no team page.
30 firms hit that cap having reached only "/" — and at least one of them, Xebia, has its own
GitHub org with 615 merged PRs going back to 2011. A firm like that plainly has a careers page;
what it has is a JavaScript-rendered nav that urllib cannot see, so the cap was applied to a
scraping limitation rather than to the company.

This renders the homepage in Chromium, reads the links the browser actually builds, and retries
the three page types. Anything still missing after this is much more likely to be genuinely
absent, which is what the cap is for.

Only runs on the affected firms — rendering is ~100x the cost of a GET.

Usage: python3 repair_pages.py [--limit 0]
"""
import os, re, sys, json, time, collections

HERE = os.path.dirname(os.path.abspath(__file__))
BUNDLES = os.path.join(HERE, "score_bundles.json")
EV = os.path.join(HERE, "scoring_evidence.json")
OUT = os.path.join(HERE, "pages_repaired.json")
LIMIT = 0
for i, a in enumerate(sys.argv):
    if a == "--limit": LIMIT = int(sys.argv[i+1])

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
WANT = {
  "careers":  r"(career|jobs?|join-?us|work-with-us|hiring|openings|life-at|vacanc)",
  "blog":     r"(blog|insights|articles|news|resources|engineering)",
  "team":     r"(team|leadership|our-people|management|about-us|about)",
}
SIGNALS = [
 ("pr_practice",  r"(code review|peer review|pull request|merge request|branching strateg|git ?flow|version control)"),
 ("cicd",         r"(ci/?cd|continuous integration|continuous delivery|jenkins|circleci|github actions|gitlab ci|terraform|kubernetes|docker|ansible|devops)"),
 ("qa",           r"(test automation|automated test|unit test|shift[- ]left|selenium|cypress|playwright|junit|pytest|quality engineering)"),
 ("compliance",   r"(soc ?2|iso ?27001|iso ?9001|cmmi|hipaa|gdpr)"),
 ("senior_roles", r"(staff engineer|principal engineer|vp of engineering|site reliability|\bsre\b|solution architect|technical architect|tech lead)"),
 ("prod_eng",     r"(product engineering|platform engineering)"),
]


def main():
    from playwright.sync_api import sync_playwright
    bundles = json.load(open(BUNDLES, encoding="utf-8"))
    ev = {r.get("domain"): r for r in json.load(open(EV, encoding="utf-8"))}
    todo = [b for b in bundles if not b.get("UNREACHABLE") and b.get("has_no_careers_blog_or_team")]
    if LIMIT: todo = todo[:LIMIT]
    print(f"rendering {len(todo)} firms that hit the no-careers/blog/team cap...", flush=True)

    out, t0 = [], time.time()
    with sync_playwright() as p:
        br = p.chromium.launch(headless=True)
        for i, b in enumerate(todo, 1):
            rec = {"name": b["name"], "domain": b["domain"], "new_pages": [], "new_signals": {},
                   "still_missing": True}
            site = b.get("website") or ""
            try:
                pg = br.new_page(user_agent=UA)
                pg.set_default_timeout(20000)
                pg.goto(site, wait_until="domcontentloaded")
                pg.wait_for_timeout(2500)          # let the nav render
                root = re.match(r"(https?://[^/]+)", pg.url)
                root = root.group(1) if root else site
                hrefs = pg.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
                found = {}
                for h in hrefs:
                    if not h.startswith(root): continue
                    for k, rx in WANT.items():
                        if k not in found and re.search(rx, h, re.I): found[k] = h
                text_all = []
                for k, u in found.items():
                    try:
                        pg.goto(u, wait_until="domcontentloaded"); pg.wait_for_timeout(1500)
                        t = re.sub(r"\s+", " ", pg.inner_text("body"))
                        if len(t) > 250:
                            rec["new_pages"].append(k); text_all.append(t)
                    except Exception:
                        continue
                joined = " ".join(text_all)
                for k, rx in SIGNALS:
                    n = len(re.findall(rx, joined, re.I))
                    if n: rec["new_signals"][k] = n
                rec["still_missing"] = not rec["new_pages"]
                rec["evidence"] = {}
                for k, rx in SIGNALS:
                    hits = [s.strip() for s in re.split(r"(?<=[.!?])\s+", joined)
                            if re.search(rx, s, re.I) and 25 <= len(s.strip()) <= 300]
                    if hits: rec["evidence"][k] = hits[:3]
                pg.close()
            except Exception as e:
                rec["error"] = type(e).__name__
                try: pg.close()
                except Exception: pass
            out.append(rec)
            json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print(f"  [{i}/{len(todo)}] {b['name'][:38]:<40}"
                  f"{'+'.join(rec['new_pages']) or 'still nothing':<26}{rec.get('error','')}", flush=True)
        br.close()

    fixed = [r for r in out if r["new_pages"]]
    print(f"\ndone in {time.time()-t0:.0f}s -> {os.path.basename(OUT)}")
    print(f"cap lifted (found pages after rendering): {len(fixed)}/{len(out)}")
    print(f"genuinely have none                     : {sum(1 for r in out if r['still_missing'] and not r.get('error'))}")
    print(f"errored                                 : {sum(1 for r in out if r.get('error'))}")
    sc = collections.Counter()
    for r in fixed:
        for k in r["new_signals"]: sc[k] += 1
    if sc:
        print("\nnew signals found on those pages:")
        for k, n in sc.most_common(): print(f"   {n:>4}  {k}")
    for r in fixed[:20]:
        print(f"   {r['name'][:44]:<46}{'+'.join(r['new_pages'])}")


main()
