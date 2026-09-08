# -*- coding: utf-8 -*-
"""Stage 2: pull headcount AND founding year from the public LinkedIn company page.

Both of the real filters live on this one page, which is why it is worth the visit:
  * 250-600 headcount   -> "Company size 201-500 employees" plus the live "N employees" count
  * shipped software well before 2024 -> "Founded 2011"
Only 29% of company websites state a founding year (measured on a 60-site pilot), so the
website pass cannot carry that criterion on its own.

The slug-guessing and headcount parsing are IMPORTED from crm_mirror/enrich/verify_headcount.py
rather than reimplemented — that file was validated against analyst ground truth (Velotio:
band 201-500, live count 245, truth 244) and a second copy would drift away from it.

BAND vs COUNT. LinkedIn's bands are 201-500 and 501-1000; neither lines up with 250-600, so a
band alone can only ever say "possible". The live member count is what decides. Rows are
labelled accordingly and nothing is silently rounded into the target band.

COMPLIANCE. This reads a page LinkedIn serves without login, but automated access is contrary
to their User Agreement. Volume is kept to survivors of the website cull, requests are serial
with a delay, and a 999 anti-bot response backs off rather than hammering. For production
volume use a licensed source (Proxycurl / Coresignal / Apollo) which sells these exact fields.

Usage: python3 linkedin_profile.py --src site_reads.json [--limit 150] [--delay 2.5]
"""
import os, re, sys, json, time, collections

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HUB, "crm_mirror", "enrich"))
from verify_headcount import slugs_for, parse_headcount, UA   # validated, do not re-implement

SRC = os.path.join(HERE, "site_reads.json")
OUT = os.path.join(HERE, "linkedin_profiles.json")
LIMIT, DELAY = 0, 2.5
HC_LO, HC_HI, FOUNDED_BY = 250, 600, 2020
for i, a in enumerate(sys.argv):
    if a == "--src": SRC = os.path.join(HERE, sys.argv[i+1])
    if a == "--out": OUT = os.path.join(HERE, sys.argv[i+1])
    if a == "--limit": LIMIT = int(sys.argv[i+1])
    if a == "--delay": DELAY = float(sys.argv[i+1])


def founded_of(t):
    m = re.search(r"Founded\s*:?\s*((?:19|20)\d{2})", t)
    return int(m.group(1)) if m else None


def grab(pg, name, domain):
    """-> dict. Tries each candidate slug until a page that is really this company loads."""
    throttled = False
    for slug in slugs_for(name, domain):
        url = f"https://www.linkedin.com/company/{slug}/"
        try:
            r = pg.goto(url, timeout=35000, wait_until="domcontentloaded")
            pg.wait_for_timeout(1500)
            if r and r.status == 999:
                throttled = True; time.sleep(8); continue
            if not r or r.status >= 400: continue
            t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", pg.content()))
            key = re.sub(r"[^a-z0-9]", "", (name or "").lower())[:7]
            if key and key not in re.sub(r"[^a-z0-9]", "", t.lower())[:6000]: continue
            members, lo, hi = parse_headcount(t)
            fy = founded_of(t)
            if members is None and lo is None and fy is None: continue
            return {"li_url": url, "members": members, "band_low": lo, "band_high": hi,
                    "founded": fy, "status": "found"}
        except Exception:
            continue
    return {"li_url": None, "members": None, "band_low": None, "band_high": None,
            "founded": None, "status": "throttled" if throttled else "not_found"}


def verdict(r):
    """Explicit about what we actually know. A band that straddles the target is 'possible',
    never 'pass' — 201-500 contains both a 210-person firm and a 490-person one."""
    m, lo, hi, fy = r["members"], r["band_low"], r["band_high"], r["founded"]
    if r["status"] != "found": return "unknown"
    if fy is not None and fy > FOUNDED_BY: return "too_young"
    if m is not None:
        if HC_LO <= m <= HC_HI: return "pass"
        return "size_out" if (m < HC_LO or m > HC_HI) else "pass"
    if lo is None: return "unknown"
    if hi is not None and (hi < HC_LO or lo > HC_HI): return "size_out"
    return "possible"


def main():
    from playwright.sync_api import sync_playwright
    rows = json.load(open(SRC, encoding="utf-8"))
    pool = [r for r in rows if r.get("verdict") in ("software_dev", "ambiguous")
            and r.get("agent_relevant") in (None, True, "yes", "Yes")]
    if LIMIT: pool = pool[::max(1, len(pool)//LIMIT)][:LIMIT]
    print(f"source {os.path.basename(SRC)}: {len(rows)} read -> {len(pool)} to look up", flush=True)

    done = {}
    if os.path.exists(OUT):
        done = {r["domain"]: r for r in json.load(open(OUT, encoding="utf-8"))}
        print(f"resuming, {len(done)} already done", flush=True)

    out, t0 = list(done.values()), time.time()
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True); pg = b.new_page(user_agent=UA)
        for i, r in enumerate(pool, 1):
            if r["domain"] in done: continue
            g = grab(pg, r["name"], r["domain"])
            rec = {k: r.get(k) for k in ("name", "city", "domain", "website", "verdict",
                                         "prod_or_serv", "founded_year", "self_headcount")} | g
            rec["final"] = verdict(g)
            out.append(rec)
            json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            if i % 10 == 0 or rec["final"] == "pass":
                el = time.time() - t0
                print(f'  [{i}/{len(pool)}] {el:>5.0f}s {r["name"][:34]:<36}'
                      f'{rec["final"]:<10} m={rec["members"]} band={rec["band_low"]}-{rec["band_high"]} '
                      f'founded={rec["founded"]}', flush=True)
            time.sleep(DELAY)
        b.close()

    print(f"\nlooked up {len(out)} in {time.time()-t0:.0f}s -> {os.path.basename(OUT)}")
    print("\nLOOKUP STATUS:", dict(collections.Counter(r["status"] for r in out)))
    print("VERDICT:")
    for k, n in collections.Counter(r["final"] for r in out).most_common():
        print(f"   {n:>4}  {k}  ({n/len(out)*100:.0f}%)")
    got = [r for r in out if r["status"] == "found"]
    print(f"\nresolved on LinkedIn : {len(got)}/{len(out)}  ({len(got)/max(len(out),1)*100:.0f}%)")
    fy = [r for r in got if r["founded"]]
    print(f"founding year present: {len(fy)}  ({len(fy)/max(len(got),1)*100:.0f}% of resolved)"
          f"   <- website only managed 29%")
    if fy:
        print(f"   founded <={FOUNDED_BY}   : {sum(1 for r in fy if r['founded'] <= FOUNDED_BY)}")
    ex = [r for r in got if r["members"] is not None]
    print(f"exact headcount      : {len(ex)}  ({len(ex)/max(len(got),1)*100:.0f}% of resolved)")
    if ex:
        band = [r for r in ex if HC_LO <= r["members"] <= HC_HI]
        print(f"   in {HC_LO}-{HC_HI}       : {len(band)}  ({len(band)/len(ex)*100:.0f}% of those with an exact count)")
        for r in band[:20]:
            print(f"      {r['name'][:44]:<46}{r['members']:>6}  founded={r['founded']}")


if __name__ == "__main__":
    main()
