# -*- coding: utf-8 -*-
"""Score the association companies on the SAME Stage-F table as the main prequal pool.

Scoring is copied verbatim from prequal/stage_efg.py so the numbers are directly comparable
to the 65-120 Tier-A range. What differs is the evidence available: these firms have no
GoodFirms metadata (no founded_year, no size band, no headcount), so the headcount bonus and
the GoodFirms corroborator can never fire. That is a real handicap, not a bug — it is stated
in the output so nobody reads a lower score as a worse company.

Usage: python3 score_assoc.py
"""
import os, re, csv, json, collections

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "prequal_out")


def load_jsonl(name):
    """Last record per domain wins — a later success supersedes an earlier failure."""
    d = {}
    p = os.path.join(OUT, name)
    if not os.path.exists(p): return d
    for line in open(p, encoding="utf-8"):
        try:
            r = json.loads(line); d[r["domain"]] = r
        except Exception: pass
    return d


def main():
    surv = {r["domain"]: r for r in csv.DictReader(open(os.path.join(OUT, "survivors.csv"), encoding="utf-8-sig"))}
    site, rdap, wb = load_jsonl("d_site.jsonl"), load_jsonl("d_rdap.jsonl"), load_jsonl("d_wayback.jsonl")
    print(f"survivors {len(surv)} | site {len(site)} | rdap {len(rdap)} | wayback {len(wb)}")
    rows, lanes = [], collections.defaultdict(list)
    for dom, s in surv.items():
        st, rd, w = site.get(dom, {}), rdap.get(dom, {}), wb.get(dom, {})
        if not st:
            lanes["not_crawled"].append({**s, "lane_reason": "site lane produced no record"}); continue
        if st.get("fetch_failed") and not st.get("final_url"):
            lanes["retry_queue"].append({**s, "lane_reason": st.get("fetch_failed", "")}); continue
        if st.get("site_dead"):
            lanes["site_dead"].append({**s, "lane_reason": str(st.get("dead_evidence", ""))[:80]}); continue
        if st.get("redirected_offsite") and not st.get("dev_wording"):
            lanes["gcc_suspect"].append({**s, "lane_reason": f'redirects to {st.get("final_url","")[:60]}'}); continue

        # ---- corroborators (same definition as stage_efg) ----
        cor, rreg = [], (rd.get("registered") or "")
        cpy = st.get("copyright_min_year") or ""
        if rreg[:4].isdigit() and int(rreg[:4]) <= 2023: cor.append("rdap")
        if str(cpy)[:4].isdigit() and int(str(cpy)[:4]) <= 2023: cor.append("copyright")
        wb_pre = bool(w.get("wb_pre2024") or (str(w.get("first_snapshot", ""))[:4].isdigit()
                                              and int(str(w.get("first_snapshot"))[:4]) <= 2023))
        if wb_pre: cor.append("wayback")
        arch = any(c in ("rdap", "wayback") for c in cor)
        if wb_pre and st.get("dev_wording"): grade = "PROVEN_EQUIV"
        elif len(cor) >= 2 and arch: grade = "EXISTED_2COR"
        elif len(cor) == 1 and arch: grade = "DOMAIN_ONLY"
        elif cor: grade = "SOURCE_ONLY"
        else: grade = "NONE"

        jd = int(st.get("jd_chars") or 0)
        hits = {k: int(st.get(k) or 0) for k in ("repo_host_hits", "review_gate_hits", "cicd_hits", "nongit_hits")}
        if grade in ("SOURCE_ONLY", "NONE") and jd < 500 and not st.get("owned_ip"):
            lanes["thin_evidence"].append({**s, "lane_reason": f"grade={grade}, jd={jd}"}); continue

        # ---- Stage F score, verbatim from stage_efg.py ----
        sc = {"PROVEN_EQUIV": 25, "EXISTED_2COR": 25, "DOMAIN_ONLY": 5, "SOURCE_ONLY": 0, "NONE": 0}[grade]
        if grade == "EXISTED_2COR" and not wb_pre: sc = 12 if len(cor) < 3 else 25
        sc += 25 * bool(st.get("owned_ip"))
        sc += 20 * (hits["review_gate_hits"] > 0)
        sc += 10 * (hits["repo_host_hits"] > 0)
        sc += 10 * (hits["cicd_hits"] > 0)
        sc += 10 if jd > 20000 else (5 if jd >= 5000 else 0)
        # headcount bonus cannot fire: associations publish no size band
        age = 2026 - int(rreg[:4]) if rreg[:4].isdigit() else 0
        sc += 10 * (age >= 8)
        sc -= 10 * bool(st.get("qa_only"))
        sc -= 10 * bool(hits["nongit_hits"])
        rows.append({**s, "score": sc, "pre2024_grade": grade, "corroborators": "+".join(cor) or "-",
                     "owned_ip": bool(st.get("owned_ip")), "ownip_quote": (st.get("ownip_quote") or "")[:90],
                     "dev_wording": bool(st.get("dev_wording")), "jd_chars": jd,
                     "repo_host_hits": hits["repo_host_hits"], "review_gate_hits": hits["review_gate_hits"],
                     "cicd_hits": hits["cicd_hits"], "years_active": age,
                     "extraction_verified": bool(st.get("extraction_verified")),
                     "final_url": st.get("final_url", "")})
    GR = {"PROVEN_EQUIV": 3, "EXISTED_2COR": 2, "DOMAIN_ONLY": 1, "SOURCE_ONLY": 0, "NONE": 0}
    rows.sort(key=lambda r: (-r["score"], -r["jd_chars"], -GR[r["pre2024_grade"]], r["domain"]))
    for i, r in enumerate(rows, 1): r["rank"] = i
    cols = ["rank", "score", "name", "domain", "source", "pre2024_grade", "corroborators", "owned_ip",
            "dev_wording", "jd_chars", "repo_host_hits", "review_gate_hits", "cicd_hits", "years_active",
            "extraction_verified", "final_url", "ownip_quote", "city"]
    with open(os.path.join(OUT, "assoc_scored.csv"), "w", newline="", encoding="utf-8") as f:
        w_ = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w_.writeheader(); w_.writerows(rows)
    for lane, items in lanes.items():
        with open(os.path.join(OUT, "lanes", f"{lane}.csv"), "w", newline="", encoding="utf-8") as f:
            if items:
                w_ = csv.DictWriter(f, fieldnames=list(items[0].keys()), extrasaction="ignore")
                w_.writeheader(); w_.writerows(items)
    print(f"\nSCORED {len(rows)}   lanes: {dict((k, len(v)) for k, v in lanes.items())}")
    if not rows: return
    b = collections.Counter()
    for r in rows:
        s = r["score"]
        b['>=65 (Tier-A range)' if s >= 65 else '50-64' if s >= 50 else '35-49' if s >= 35 else '20-34' if s >= 20 else '<20'] += 1
    print("\nscore bands:")
    for k in ('>=65 (Tier-A range)', '50-64', '35-49', '20-34', '<20'):
        if b.get(k): print(f"  {k:<24}{b[k]:>5}")
    print(f"\nowned_ip {sum(1 for r in rows if r['owned_ip'])} | "
          f"repo hits {sum(1 for r in rows if r['repo_host_hits'])} | "
          f"review gates {sum(1 for r in rows if r['review_gate_hits'])}")
    print("\ntop 20:")
    for r in rows[:20]:
        print(f"  {r['rank']:>3} [{r['score']:>3}] {r['name'][:38]:<40}{r['domain']:<28}"
              f"{r['pre2024_grade']:<14}ip={str(r['owned_ip'])[:1]} jd={r['jd_chars']}")


main()
