# -*- coding: utf-8 -*-
"""Judge whether the Google Maps scrape is actually a good codebase-acquisition source.

Maps tells us name/phone/website/rating and nothing else — no headcount, no founded year,
no idea whether the firm builds software or just resells websites. Our real gates need
exactly those. So: take a random sample, read each firm's own website, and have Claude
score it against the gates we actually use.

Judged per firm:
  builds_software  does it build custom software FOR CLIENTS (the thing that leaves a
                   dormant codebase behind), vs marketing/design/staffing/reselling
  employees        best estimate from the site
  founded_year     pre-2024 codebases need a firm that existed before then
  codebase_odds    0-100: would this firm plausibly hold sellable dormant client code

Usage: python gmaps_vet_sample.py [--n 45] [--seed 7]
"""
import os, re, sys, csv, json, time, random, argparse, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(HERE)
CSV = os.path.join(HUB, "exports", "gmaps", "gmaps_tier2_leads.csv")
OUT = os.path.join(HUB, "exports", "gmaps", "gmaps_vet_sample.json")
env = {l.split('=', 1)[0].strip().lower(): l.split('=', 1)[1].strip()
       for l in open(os.path.join(HUB, '.env'), encoding='utf-8-sig')
       if '=' in l and not l.strip().startswith('#')}
ANT = env["anthropic_api_key"]
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def get(url, t=9):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=t) as r:
            return r.read()
    except Exception:
        return b""


def site_text(dom):
    txt = ""
    for path in ("", "/about", "/about-us", "/services", "/company"):
        for sch in ("https://", "http://"):
            b = get(sch + dom + path)
            if b and len(b) > 300:
                h = b.decode("utf-8", "ignore")
                h = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", h)
                h = re.sub(r"(?s)<[^>]+>", " ", h); h = re.sub(r"&[a-z#0-9]+;", " ", h)
                txt += " " + re.sub(r"\s+", " ", h).strip()
                break
        if len(txt) > 3500: break
    return txt[:4000]


SCHEMA = ('{"builds_software":true|false,"what_they_do":"<6 words>",'
          '"employees":<int or 0 if unclear>,"founded_year":<int or 0>,'
          '"codebase_odds":<0-100>,"why":"<12 words>"}')


def judge(name, dom, text):
    if not text or len(text) < 120:
        return {"error": "no_site_text"}
    prompt = (
        f"Company: {name}\nWebsite ({dom}) text:\n{text[:3600]}\n\n"
        "You are assessing this company as a potential SELLER of dormant software assets.\n"
        "We buy pre-2024 source code that a company built for clients and has since written "
        "off — abandoned MVPs, retired internal tools, completed client projects.\n\n"
        "Judge THIS company only:\n"
        "- builds_software: true only if they WRITE custom software/apps for clients. "
        "False for digital-marketing, SEO, graphic design, staffing/recruitment, IT support, "
        "hardware resale, or website-template shops.\n"
        "- employees: their headcount if stated or clearly implied, else 0.\n"
        "- founded_year: if stated, else 0.\n"
        "- codebase_odds: 0-100, how likely they hold dormant pre-2024 client code they could "
        "sell. A 5-person web shop scores low; a 100-person firm with a decade of client "
        "projects scores high.\n\n"
        f"Return ONLY minified JSON: {SCHEMA}")
    body = json.dumps({"model": "claude-haiku-4-5-20251001", "max_tokens": 220,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, method="POST",
        headers={"x-api-key": ANT, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    for a in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                d = json.loads(r.read().decode())
            t = "".join(c.get("text", "") for c in d.get("content", []))
            m = re.search(r"\{.*\}", t, re.S)
            return json.loads(m.group(0)) if m else {"error": "unparsed"}
        except urllib.error.HTTPError as e:
            if e.code in (429, 529, 503) and a < 2: time.sleep(3 * (a + 1)); continue
            return {"error": f"http{e.code}"}
        except Exception:
            if a < 2: time.sleep(2); continue
            return {"error": "net"}
    return {"error": "retries"}


def one(r):
    txt = site_text(r["domain"])
    v = judge(r["company_name"], r["domain"], txt)
    return {**r, "site_chars": len(txt), **v}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=45); ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    rows = list(csv.DictReader(open(CSV, encoding="utf-8-sig")))
    random.seed(a.seed)
    sample = random.sample(rows, min(a.n, len(rows)))
    print(f"vetting a random {len(sample)} of {len(rows)} Maps firms (seed {a.seed})\n")
    out = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        for i, res in enumerate(ex.map(one, sample), 1):
            out.append(res)
            if i % 10 == 0: print(f"  ...{i}/{len(sample)}", flush=True)
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    ok = [r for r in out if not r.get("error")]
    dead = [r for r in out if r.get("error") == "no_site_text"]
    builds = [r for r in ok if r.get("builds_software")]
    emp = [r["employees"] for r in builds if r.get("employees")]
    fy = [r["founded_year"] for r in builds if r.get("founded_year")]
    odds = [r["codebase_odds"] for r in ok if r.get("codebase_odds") is not None]

    print(f"\n=== VERDICT on {len(out)} sampled ===")
    print(f"site unreachable / no text : {len(dead)}  ({100*len(dead)//len(out)}%)")
    print(f"judged                     : {len(ok)}")
    print(f"  BUILD custom software    : {len(builds)}  ({100*len(builds)//max(1,len(ok))}% of judged)")
    print(f"  do NOT (marketing/etc)   : {len(ok)-len(builds)}")
    if emp:
        emp.sort()
        print(f"\nheadcount (where stated, n={len(emp)}): median {emp[len(emp)//2]}, "
              f"min {emp[0]}, max {emp[-1]}")
        for lo, hi in ((1, 9), (10, 49), (50, 249), (250, 999), (1000, 10**6)):
            n = sum(1 for e in emp if lo <= e <= hi)
            print(f"    {lo}-{hi if hi < 10**6 else '+'}: {n}")
        print(f"  >=50 employees (our gate): {sum(1 for e in emp if e >= 50)}/{len(emp)}")
    if fy:
        fy.sort()
        print(f"\nfounded (where stated, n={len(fy)}): median {fy[len(fy)//2]}, "
              f"<=2022: {sum(1 for y in fy if y <= 2022)}/{len(fy)}")
    if odds:
        odds.sort()
        print(f"\ncodebase_odds: median {odds[len(odds)//2]}, "
              f">=60: {sum(1 for o in odds if o >= 60)}/{len(odds)}, "
              f">=40: {sum(1 for o in odds if o >= 40)}/{len(odds)}")
    print("\ntop by codebase_odds:")
    for r in sorted(ok, key=lambda x: -(x.get("codebase_odds") or 0))[:10]:
        print(f"  {r.get('codebase_odds', 0):>3}  {r['company_name'][:30]:32} "
              f"emp={r.get('employees', 0):<5} {r.get('what_they_do', '')[:38]}")
    print("\nworst:")
    for r in sorted(ok, key=lambda x: (x.get("codebase_odds") or 0))[:6]:
        print(f"  {r.get('codebase_odds', 0):>3}  {r['company_name'][:30]:32} {r.get('what_they_do', '')[:40]}")
    print(f"\n-> {OUT}")


if __name__ == "__main__":
    main()
