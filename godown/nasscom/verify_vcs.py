# -*- coding: utf-8 -*-
"""Turn "a github link exists in the footer" into the Tier A fact the rubric actually asks for.

filterInstructions.md Tier A is "Public VCS org with VISIBLE MERGED PRs / MULTIPLE CONTRIBUTORS
-> +40", and marks confidence = Verified only when a Tier A signal is found. A link alone does
not meet that bar: Zensar's org page loads fine and has ZERO merged PRs.

One GitHub search call per org answers all three parts at once:
    /search/issues?q=org:<org>+is:pr+is:merged&per_page=100
      total_count            -> how many merged PRs exist
      items[].user.login     -> distinct authors, i.e. multiple contributors
      items[].closed_at      -> recency, so a org last touched in 2019 is not sold as live

BOTS ARE EXCLUDED. dependabot[bot] was the single largest "contributor" on a test org with 63
merged PRs. Counting it would award +40 for automated dependency bumps, which is the opposite
of evidence that humans review each other's code.

Second Tier A path for firms with no org: published OSS packages (rubric +10). npm is matched
on the package's repository/homepage URL containing the company's own domain — searching by
brand name alone would award points to any firm sharing a word with a popular package.

Unauthenticated limits: search 10/min, core 60/hr. Paced accordingly; on exhaustion the run
stops cleanly and records what it has rather than guessing.

Usage: python3 verify_vcs.py [--src scoring_evidence.json]
"""
import os, re, sys, json, time, collections, urllib.request, urllib.error, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "scoring_evidence.json")
OUT = os.path.join(HERE, "vcs_verified.json")
GH_DELAY = 7.0            # search API is 10/min unauthenticated
for i, a in enumerate(sys.argv):
    if a == "--src": SRC = os.path.join(HERE, sys.argv[i+1])
    if a == "--out": OUT = os.path.join(HERE, sys.argv[i+1])

UA = "Mozilla/5.0 (compatible; lh2-lead-research/1.0)"
BOT = re.compile(r"\[bot\]$|^(dependabot|renovate|github-actions|snyk-bot|greenkeeper|imgbot)\b", re.I)


def jget(u, accept="application/json", t=30):
    r = urllib.request.Request(u, headers={"User-Agent": UA, "Accept": accept})
    with urllib.request.urlopen(r, timeout=t) as x:
        return json.loads(x.read().decode())


def owns(org, domain, name):
    """Is this org plausibly the COMPANY'S own, or just a library the site happens to use?

    An unfiltered scrape of github.com links attributes Bootstrap's 12,528 merged PRs (twbs) and
    New Relic's 77,878 to whichever Indian IT firm embeds them. Those links exist because the
    site USES the library. Require the org to echo the domain root or a distinctive word of the
    company name before any of its activity counts toward Tier A.
    """
    o = re.sub(r"[^a-z0-9]", "", org.lower())
    root = re.sub(r"[^a-z0-9]", "", (domain or "").split(".")[0].lower())
    if root and len(root) >= 4 and (o in root or root in o): return True
    toks = [re.sub(r"[^a-z0-9]", "", t.lower()) for t in re.split(r"\s+", name or "")]
    for t in toks:
        if len(t) >= 5 and t not in ("private", "limited", "solutions", "technologies",
                                     "software", "systems", "services", "india", "global"):
            if t in o or o in t: return True
    return False


def gh_earliest(org):
    """Oldest merged PR — the Tier GOLD test. Same endpoint, ascending."""
    u = (f"https://api.github.com/search/issues?q=org:{org}+is:pr+is:merged"
         f"&per_page=1&sort=created&order=asc")
    try:
        d = jget(u, "application/vnd.github+json")
        it = (d.get("items") or [{}])[0]
        return (it.get("created_at") or "")[:10] or None
    except Exception:
        return None


def gh_org(org):
    """-> dict. One search call: merged PRs, distinct human authors, recency."""
    u = (f"https://api.github.com/search/issues?q=org:{org}+is:pr+is:merged"
         f"&per_page=100&sort=updated&order=desc")
    try:
        d = jget(u, "application/vnd.github+json")
    except urllib.error.HTTPError as e:
        return {"org": org, "status": f"http{e.code}",
                "note": "rate limited" if e.code in (403, 429) else e.reason}
    except Exception as e:
        return {"org": org, "status": type(e).__name__}
    items = d.get("items") or []
    humans = collections.Counter()
    for i in items:
        lg = ((i.get("user") or {}).get("login") or "")
        if lg and not BOT.search(lg): humans[lg] += 1
    dates = sorted([i.get("closed_at") for i in items if i.get("closed_at")], reverse=True)
    bots = len(items) - sum(humans.values())
    return {"org": org, "status": "ok", "merged_prs": d.get("total_count", 0),
            "sampled": len(items), "bot_prs_in_sample": bots,
            "human_authors": len(humans), "top_authors": humans.most_common(5),
            "last_merge": dates[0] if dates else None,
            # the rubric's own wording: merged PRs AND multiple contributors
            "tier_a_vcs": bool(d.get("total_count", 0) >= 3 and len(humans) >= 2)}


def npm_for(domain, name):
    """Published packages whose repo/homepage points back at this company's own domain."""
    if not domain: return []
    root = domain.split(".")[0]
    if len(root) < 4: return []
    try:
        d = jget(f"https://registry.npmjs.org/-/v1/search?text={urllib.parse.quote(root)}&size=20")
    except Exception:
        return []
    out = []
    for o in d.get("objects", []):
        p = o.get("package", {})
        links = " ".join(str(v) for v in (p.get("links") or {}).values())
        blob = f'{links} {p.get("homepage","")}'.lower()
        if domain.lower() in blob:
            out.append({"name": p.get("name"), "link": (p.get("links") or {}).get("npm", ""),
                        "date": p.get("date", "")[:10]})
        if len(out) >= 5: break
    return out


def main():
    rows = json.load(open(SRC, encoding="utf-8"))
    state = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}

    orgs, rejected = {}, []
    for r in rows:
        for u in r.get("vcs", []):
            m = re.match(r"https://(github|gitlab|bitbucket)[^/]*/([A-Za-z0-9._-]+)", u)
            if not m or m.group(1) != "github": continue
            org = m.group(2).lower()
            if owns(org, r.get("domain"), r.get("name")):
                orgs.setdefault(org, []).append(r["domain"])
            else:
                rejected.append((org, r.get("domain")))
    todo = [o for o in orgs if o not in state.get("gh", {})]
    print(f"companies crawled: {len(rows)}")
    if rejected:
        print(f"github links REJECTED as vendor/dependency, not the firm's own: {len(rejected)}")
        for o, d in rejected: print(f"     {o:<20} found on {d}")
    print(f"distinct GitHub orgs found: {len(orgs)} | to verify: {len(todo)}", flush=True)
    print(f"pacing at {GH_DELAY}s (search API is 10/min unauthenticated)\n", flush=True)

    state.setdefault("gh", {}); state.setdefault("npm", {})
    for i, o in enumerate(todo, 1):
        g = gh_org(o)
        if g.get("status") == "ok" and g.get("merged_prs"):
            time.sleep(GH_DELAY)
            g["first_merge"] = gh_earliest(o)
            g["tier_gold_vcs"] = bool(g["first_merge"] and g["first_merge"] < "2024-01-01")
        state["gh"][o] = g
        json.dump(state, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        if g.get("status") != "ok":
            print(f"  [{i}/{len(todo)}] {o:<28} {g.get('status')} {g.get('note','')}", flush=True)
            if g.get("note") == "rate limited":
                print("  !! GitHub rate limit — stopping cleanly, re-run later to resume", flush=True)
                break
        else:
            print(f"  [{i}/{len(todo)}] {o:<28} PRs={g['merged_prs']:<6} humans={g['human_authors']:<3} "
                  f"first={str(g.get('first_merge'))[:10]:<11} last={str(g['last_merge'])[:10]:<11} "
                  f"tierA={g['tier_a_vcs']} GOLD={g.get('tier_gold_vcs')}", flush=True)
        time.sleep(GH_DELAY)

    print("\nnpm check (free, no auth)...", flush=True)
    n = 0
    for r in rows:
        d = r.get("domain")
        if not d or d in state["npm"]: continue
        pk = npm_for(d, r["name"])
        state["npm"][d] = pk
        if pk:
            n += 1
            print(f"   {r['name'][:38]:<40}{len(pk)} package(s): {', '.join(p['name'] for p in pk[:3])}", flush=True)
        time.sleep(0.25)
    json.dump(state, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    ok = [g for g in state["gh"].values() if g.get("status") == "ok"]
    ta = [g for g in ok if g.get("tier_a_vcs")]
    print(f"\n--- TIER A VERIFICATION ---")
    print(f"orgs checked            : {len(ok)}")
    print(f"orgs with 0 merged PRs  : {sum(1 for g in ok if not g.get('merged_prs'))}")
    print(f"PASS tier A (>=3 PRs, >=2 human authors): {len(ta)}")
    for g in sorted(ta, key=lambda x: -x["merged_prs"]):
        print(f"   {g['org']:<26}{g['merged_prs']:>6} PRs  {g['human_authors']:>3} humans  "
              f"last {str(g['last_merge'])[:10]}")
    print(f"\ncompanies with npm packages tied to their domain: {n}")


main()
