# -*- coding: utf-8 -*-
"""Find the RIGHT founder/CEO for the 25 wrong-SPOC companies — no Anthropic key.

Lamiya's notes say the person on the deal is the wrong one. The chain here, in cost order,
all keyless:
  0. the note itself      MEDIATRENZ's note carries a referred number — that IS the answer
  1. local corpora        GoodFirms people table (702 LinkedIn URLs), founders_websearch,
                          salesnav enriched — by domain
  2. company site         /team /about /leadership scrape for names + linkedin /in/ links
  3. DuckDuckGo HTML      html.duckduckgo.com needs no API key: site:linkedin.com/in
                          "<company>" founder — the free replacement for paid web search
Whatever produces a LinkedIn URL becomes a SignalHire reveal candidate (credits pool), but
REVEALS ARE NOT SPENT HERE — the output is a reviewed shortlist first, because reveal credits
were once burned on 48 non-senior people and that lesson stays learned.

Domains for 17/25 are unknown (older pushes carried no lh2_domain) — resolved via DDG too.
Giants (TransUnion, Holcim, Neudesic, Rightpoint, CtrlS) are marked skip_giant: "wrong SPOC"
there really meant wrong company; chasing their CEOs is not our motion.

Usage: python3 find_right_spoc.py       -> right_spoc_found.json + printed table
"""
import os, re, sys, json, time, sqlite3, urllib.request, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
DB = os.path.join(HUB, "lh2-pipeline", "data", "pipeline.sqlite")
NAS = os.path.join(HUB, "godown", "nasscom")
OUT = os.path.join(HERE, "right_spoc_found.json")
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
SENIOR = re.compile(r"founder|co[- ]?founder|ceo|cto|chief|managing director|\bmd\b|owner|"
                    r"director|president|managing partner", re.I)


def fetch(url, timeout=14):
    try:
        r = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(r, timeout=timeout) as x:
            return x.read(600_000).decode("utf-8", "replace")
    except Exception:
        return ""


def ddg(q):
    """DuckDuckGo HTML results — list of (title, url). Keyless, throttle-friendly."""
    h = fetch("https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(q))
    out = []
    for m in re.finditer(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', h, re.S):
        u = m.group(1)
        mm = re.search(r"uddg=([^&]+)", u)
        if mm: u = urllib.parse.unquote(mm.group(1))
        out.append((re.sub(r"<[^>]+>", "", m.group(2))[:80], u))
    time.sleep(2.0)          # be a polite guest — this endpoint bans the greedy
    return out


def site_people(domain):
    """-> [(name_guess, title_line, linkedin_url)] from team-ish pages."""
    found = []
    for path in ("", "/team", "/about", "/about-us", "/leadership", "/our-team"):
        h = fetch(f"https://{domain}{path}") or fetch(f"http://{domain}{path}")
        if not h: continue
        for m in re.finditer(r'href="(https?://(?:www\.)?linkedin\.com/in/[^"]+)"', h):
            found.append(("", "", m.group(1)))
        txt = re.sub(r"<[^>]+>", " ", re.sub(r"<script.*?</script>|<style.*?</style>", " ", h, flags=re.S))
        for m in re.finditer(r"([A-Z][a-z]+(?: [A-Z][a-z]+){1,2})\s*[,–-]?\s*"
                             r"((?:Co[- ]?)?Founder[^.,;|]{0,40}|CEO[^.,;|]{0,30}|Managing Director[^.,;|]{0,20}|CTO[^.,;|]{0,30})", txt):
            found.append((m.group(1), m.group(2).strip(), ""))
        if found: break
    return found[:6]


def main():
    targets = json.load(open(os.path.join(HERE, "targets.json")))
    gf = {}
    con = sqlite3.connect(DB)
    for dom, nm, role, li in con.execute("SELECT domain,name,role,linkedin_url FROM people"):
        gf.setdefault((dom or "").lower(), []).append({"name": nm, "role": role or "", "linkedin": li or ""})
    ws = {(r.get("domain") or "").lower(): r for r in
          (json.load(open(f"{NAS}/founders_websearch.json")) if os.path.exists(f"{NAS}/founders_websearch.json") else [])
          if r.get("person")}

    state = {r["deal_id"]: r for r in json.load(open(OUT))} if os.path.exists(OUT) else {}
    for t in targets:
        if t["deal_id"] in state: continue
        rec = dict(t)
        if t["name"] == "MEDIATRENZ":
            rec |= {"person": "(referred by Ashok on the call)", "phone": "+919871181711",
                    "source": "caller note — referred number", "action": "push-ready"}
            state[t["deal_id"]] = rec; continue
        if t["giant"]:
            rec |= {"source": "skipped", "action": "skip_giant — wrong company, not wrong person"}
            state[t["deal_id"]] = rec; continue

        dom = t["domain"]
        if not dom:                                   # resolve domain via DDG
            for _, u in ddg(f'{t["name"]} India official website'):
                d2 = urllib.parse.urlparse(u).netloc.lower().replace("www.", "")
                if d2 and not any(b in d2 for b in ("linkedin", "facebook", "instagram", "glassdoor",
                                                    "ambitionbox", "justdial", "crunchbase", "zaubacorp",
                                                    "indiamart", "youtube", "wikipedia", "duckduckgo")):
                    dom = d2; break
        rec["domain_resolved"] = dom

        person = title = li = src = ""
        # 1. local corpora
        for p in gf.get(dom, []):
            if SENIOR.search(p["role"]):
                person, title, li, src = p["name"], p["role"], p["linkedin"], "goodfirms people DB"; break
        if not person and dom in ws:
            w = ws[dom]
            person, title, li, src = w["person"], w.get("title", ""), w.get("linkedin", ""), "founders_websearch cache"
        # 2. company site
        if not person and dom:
            for nm, tt, lk in site_people(dom):
                if nm and SENIOR.search(tt):
                    person, title, li, src = nm, tt, lk, "company site scrape"; break
                if lk and not li: li = lk; src = src or "company site linkedin link"
        # 3. DuckDuckGo -> LinkedIn
        if not li:
            for ttl, u in ddg(f'site:linkedin.com/in "{t["name"]}" founder OR CEO OR director'):
                if "linkedin.com/in/" in u:
                    li = u.split("?")[0]
                    if not person:
                        nm = re.split(r"[-–|]", ttl)[0].strip()
                        if 4 < len(nm) < 40: person = nm
                        tm = re.search(SENIOR, ttl)
                        title = title or (tm.group(0) if tm else "")
                    src = src or "duckduckgo linkedin search"
                    break
        rec |= {"person": person, "title": title, "linkedin": li, "source": src,
                "action": ("reveal-candidate" if li else
                           "name-only — needs another key" if person else "not found")}
        state[t["deal_id"]] = rec
        json.dump(list(state.values()), open(OUT, "w"), indent=1, ensure_ascii=False)
        print(f'{t["name"][:30]:<32}{(person or "-")[:24]:<26}{(title or "")[:22]:<24}'
              f'{"LI" if li else "  "}  [{src or "nothing"}]', flush=True)

    json.dump(list(state.values()), open(OUT, "w"), indent=1, ensure_ascii=False)
    acts = {}
    for r in state.values(): acts[r["action"].split(" ")[0]] = acts.get(r["action"].split(" ")[0], 0) + 1
    print("\nsummary:", acts)


main()
