# -*- coding: utf-8 -*-
"""Verify a company's real headcount from its PUBLIC LinkedIn company page (Playwright).

Why: GoodFirms' size band is wrong ~10% of the time even when it passes our 50-employee
gate (analysts found firms labelled "50 - 249" that were actually 1-26 people). This is the
independent second check — run it BEFORE pushing a lead to a caller.

Returns per company: {slug, members, band_low, band_high, verdict}
  verdict: pass (>=min) | fail (<min) | not_found

NOTE ON COMPLIANCE: this reads a page LinkedIn serves publicly without login, but automated
access is contrary to LinkedIn's User Agreement. For production volume prefer a licensed
source (Proxycurl / Coresignal / Apollo) which sells exactly this field. Keep volumes low
and rate-limited if using this.

Usage:
  python verify_headcount.py --test                 # validate against known-bad cases
  python verify_headcount.py --domains a.com,b.com  # check specific companies
"""
import re, sys, json, time, os

MIN_HEADCOUNT = 50
HERE = os.path.dirname(os.path.abspath(__file__))
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"

def slugs_for(name, domain=""):
    """Candidate LinkedIn company slugs, best guess first."""
    base = re.sub(r"[^a-z0-9 ]", " ", (name or "").lower())
    base = re.sub(r"\b(pvt|private|ltd|limited|llp|inc|the)\b", " ", base)
    toks = [t for t in base.split() if t]
    out = []
    if toks:
        out.append("-".join(toks))                      # full name
        out.append("".join(toks))                       # squashed
        if len(toks) > 1: out.append("-".join(toks[:-1]))  # drop trailing 'technologies' etc
        out.append(toks[0])
    d = (domain or "").split(".")[0]
    if d: out += [d, d.replace("-", "")]
    seen, uniq = set(), []
    for s in out:
        if s and s not in seen: seen.add(s); uniq.append(s)
    return uniq[:5]

def parse_headcount(txt):
    """-> (members, band_low, band_high) from LinkedIn page text.

    Two independent signals on a public company page:
      * "Company size 201-500 employees"  -> the firm's self-declared band
      * "245 employees"                   -> live count of members listing this employer
    Verified against Velotio: band 201-500, count 245 (ground truth 244).
    """
    lo = hi = members = None
    b = re.search(r"[Cc]ompany size\s*([\d,]+)\s*[-–]\s*([\d,]+)\s*employees", txt)
    if not b:
        b = re.search(r"([\d,]+)\s*[-–]\s*([\d,]+)\s*employees", txt)
    if b:
        lo, hi = int(b.group(1).replace(",", "")), int(b.group(2).replace(",", ""))
    else:
        b2 = re.search(r"([\d,]+)\+\s*employees", txt)
        if b2: lo = int(b2.group(1).replace(",", ""))
    # live employee count: an "N employees" that is NOT part of the band string
    for m in re.finditer(r"([\d,]{1,7})\s+employees", txt):
        v = int(m.group(1).replace(",", ""))
        if v not in (lo, hi):
            members = v; break
    return members, lo, hi

def check(pg, name, domain="", min_hc=MIN_HEADCOUNT, linkedin_url=None):
    """If a verified company LinkedIn URL is known, pass it as `linkedin_url` —
    slug-guessing is the main failure mode (404s)."""
    cands = [linkedin_url] if linkedin_url else \
            [f"https://www.linkedin.com/company/{s}/" for s in slugs_for(name, domain)]
    throttled = False
    for url in cands:
        try:
            r = pg.goto(url, timeout=35000, wait_until="domcontentloaded")
            pg.wait_for_timeout(1800)
            if r and r.status == 999:      # LinkedIn anti-bot response
                throttled = True; time.sleep(5); continue
            if not r or r.status >= 400: continue
            t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", pg.content()))
            # confirm the page is really this company (guard against wrong-slug matches)
            key = re.sub(r"[^a-z0-9]", "", (name or "").lower())[:7]
            if key and key not in re.sub(r"[^a-z0-9]", "", t.lower())[:6000]: continue
            members, lo, hi = parse_headcount(t)
            if members is None and lo is None: continue
            # conservative: fail if EITHER signal says under the floor
            sigs = [v for v in (members, hi if hi else lo) if v is not None]
            verdict = "pass" if sigs and min(sigs) >= min_hc else "fail"
            return {"url": url, "members": members, "band_low": lo, "band_high": hi, "verdict": verdict}
        except Exception:
            continue
    return {"url": None, "members": None, "band_low": None, "band_high": None,
            "verdict": "throttled" if throttled else "not_found"}

def main():
    from playwright.sync_api import sync_playwright
    args = sys.argv
    if "--test" in args:
        # ground truth from analysts' notes (GoodFirms claimed "50 - 249" for all of these)
        cases = [("DigiQAL Technologies", "", 1), ("Actiknow Consulting Pvt Ltd", "", 13),
                 ("Alphalogic Techsys Limited", "", 11), ("Aneka Labs Private Limited", "", 19),
                 ("Fibonalabs", "", 15), ("GigLabz Private Limited", "", 25),
                 ("Velotio Technologies", "velotio.com", 244)]   # known-good control
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True); pg = b.new_page(user_agent=UA)
            ok = 0
            print(f"{'company':30} {'analyst':>8} {'linkedin':>10} {'band':>12}  verdict")
            for name, dom, truth in cases:
                r = check(pg, name, dom)
                lk = r["members"] if r["members"] is not None else r["band_low"]
                band = f"{r['band_low']}-{r['band_high']}" if r["band_low"] else "-"
                agree = ""
                if r["verdict"] != "not_found":
                    caught = (r["verdict"] == "fail") == (truth < MIN_HEADCOUNT)
                    ok += caught; agree = "OK" if caught else "MISS"
                print(f"{name[:30]:30} {truth:>8} {str(lk):>10} {band:>12}  {r['verdict']:9} {agree}")
                time.sleep(1.5)
            print(f"\ncorrectly classified: {ok}/{len(cases)}")
            b.close()
        return
    doms = []
    for i, a in enumerate(args):
        if a == "--domains": doms = args[i+1].split(",")
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True); pg = b.new_page(user_agent=UA)
        out = []
        for d in doms:
            r = check(pg, d.split(".")[0], d); r["domain"] = d; out.append(r)
            print(f"{d:30} {r['verdict']:10} members={r['members']} band={r['band_low']}-{r['band_high']}")
            time.sleep(1.5)
        b.close()
        json.dump(out, open(os.path.join(HERE, "headcount_checks.json"), "w"), indent=1)

if __name__ == "__main__":
    main()
