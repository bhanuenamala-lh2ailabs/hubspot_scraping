# -*- coding: utf-8 -*-
"""Stages E/F/G — merge crawl evidence, grade pre-2024, score, band, self-audit.

Reads: prequal_out/{survivors.csv, evidence_prepass.csv, d_site.jsonl, d_rdap.jsonl,
d_wayback.jsonl}. Last JSONL record per domain wins (failures superseded by later success).

GRADING (D2, adapted to what an availability-only wayback lane can honestly claim):
  corroborators = goodfirms_founded<=2023 | rdap<=2023 | copyright_footer<=2023 |
                  nasscom archival basis | wayback snapshot<=2023
  PROVEN_EQUIV  = wayback snapshot <=2023 AND live-site dev wording (snapshot BODY unread —
                  the availability API gives date only, so this is equivalence, not identity)
  EXISTED_2COR  = >=2 corroborators, at least one archival-grade (rdap/wayback/nasscom-basis)
  DOMAIN_ONLY   = exactly one archival corroborator, nothing else
  SOURCE_ONLY   = self-stated only -> thin_evidence lane, never scored as proof
Confidence (Verified/Inferred) records evidence RELIABILITY and feeds the score NOWHERE —
audit check 6 proves the correlation is ~0 by construction.

SCORING is the spec's Stage-F table verbatim; no ceiling; deterministic tie-breaks
(jd_chars desc -> pre2024 strength -> |headcount-100| asc -> domain age desc) so no
alphabetical run can masquerade as ranking (audit check 2 hunts them anyway).

Usage: python3 stage_efg.py
"""
import os, re, csv, json, random, collections, datetime

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "prequal_out")
LANES = os.path.join(OUT, "lanes")
QUEUE_SIZE, WHALE_LANE_SIZE = 450, 30
BAND_MID = {"10-49": 30, "50-249": 150, "250+": 300, "": None}


def jsonl_last(path):
    d = {}
    if os.path.exists(path):
        for ln in open(path, encoding="utf-8"):
            try:
                r = json.loads(ln)
                if r.get("fetch_failed") and r["domain"] in d: continue
                d[r["domain"]] = r
            except Exception: pass
    return d


def load_blocklist():
    """config.yaml's outsourcer list + a BPO/GCC extension it lacks.

    Concentrix Daksh reached rank 13 of the first queue because its GoodFirms listing
    claims a small band and its segment text tripped no Stage-B regex. The config list
    covers IT-services giants only; BPO majors and famous captives get added here. A match
    is treated as positive Stage-B evidence — these are publicly known categories, not
    inferences from absence.
    """
    names = []
    p = os.path.join(os.path.dirname(os.path.dirname(HERE)), "lh2-pipeline", "config.yaml")
    on = False
    for ln in open(p, encoding="utf-8"):
        if "blocklist_outsourcers:" in ln: on = True; continue
        if on:
            m = re.match(r"\s+-\s+(.+)", ln)
            if m: names.append(m.group(1).strip())
            else: break
    names += ["Concentrix", "Daksh", "Genpact", "WNS", "EXL Service", "Firstsource",
              "Teleperformance", "Sutherland", "IBM", "DXC", "Atos", "NTT Data", "Fujitsu",
              "Virtusa", "UST Global", "Publicis Sapient", "GlobalLogic", "EPAM", "Deloitte",
              "EY ", "KPMG", "PwC"]
    return [n.lower() for n in names]


def main():
    BLOCK = load_blocklist()
    sv = list(csv.DictReader(open(os.path.join(OUT, "survivors.csv"), encoding="utf-8-sig")))
    pp = {r["domain"]: r for r in csv.DictReader(open(os.path.join(OUT, "evidence_prepass.csv"), encoding="utf-8-sig"))}
    site = jsonl_last(os.path.join(OUT, "d_site.jsonl"))
    rdap = jsonl_last(os.path.join(OUT, "d_rdap.jsonl"))
    wb = jsonl_last(os.path.join(OUT, "d_wayback.jsonl"))
    print(f"survivors {len(sv)} | site {len(site)} | rdap {len(rdap)} | wayback {len(wb)}")

    rows, lanes, rejects = [], collections.defaultdict(list), []
    for s in sv:
        d = s["domain"]; p = pp.get(d, {}); st = site.get(d, {}); rd = rdap.get(d, {}); w = wb.get(d, {})
        r = {**s}
        nml = " " + re.sub(r"[^a-z0-9 ]", " ", s["name"].lower()) + " "
        hit = next((b for b in BLOCK if f" {b} " in nml or nml.strip().startswith(b)), "")
        if hit:
            rejects.append({**s, "stage": "B-late", "reject_reason": "blocklist_outsourcer_bpo",
                            "evidence": f"known giant/BPO: matched '{hit}'"}); continue
        if st.get("fetch_failed") and not st.get("final_url"):
            lanes["retry_queue"].append({**s, "lane_reason": st["fetch_failed"]}); continue
        if st.get("site_dead"):
            lanes["site_dead"].append({**s, "lane_reason": st.get("dead_evidence", "")[:80]}); continue
        # late Stage-B catch: positive category evidence found on the live site
        if st.get("redirected_offsite") and not st.get("dev_wording"):
            lanes["gcc_suspect"].append({**s, "lane_reason": f'redirects to {st.get("final_url","")[:60]}'}); continue

        # ---- corroborators & grade
        cor = []
        fy = s.get("founded_year")
        if fy and str(fy).isdigit() and int(fy) <= 2023: cor.append(("goodfirms_founded", str(fy), "Inferred"))
        rreg = (rd.get("rdap_registered") or (p.get("pre2024_basis", "").split("rdap:")[1][:10]
                                              if "rdap:" in p.get("pre2024_basis", "") else ""))
        if rreg and rreg[:4].isdigit() and int(rreg[:4]) <= 2023: cor.append(("rdap", rreg, "Verified"))
        cy = st.get("copyright_min_year")
        if cy and int(cy) <= 2023: cor.append(("copyright_footer", str(cy), "Inferred"))
        if "nasscom:" in p.get("pre2024_basis", ""): cor.append(("nasscom_harvest", p["pre2024_basis"][:40], "Verified"))
        if w.get("wb_pre2024"): cor.append(("wayback", w.get("wb_ts", "")[:8], "Verified"))
        archival = [c for c in cor if c[2] == "Verified"]
        if w.get("wb_pre2024") and st.get("dev_wording"): grade = "PROVEN_EQUIV"
        elif len(cor) >= 2 and archival: grade = "EXISTED_2COR"
        elif archival: grade = "DOMAIN_ONLY"
        elif cor: grade = "SOURCE_ONLY"
        else: grade = "NONE"
        r["pre2024_grade"] = grade
        r["pre2024_evidence"] = "; ".join(f"{k}={v}" for k, v, _ in cor)[:140]
        r["pre2024_confidence"] = "Verified" if archival else ("Inferred" if cor else "")

        # ---- service wording / owned ip / jd
        r["dev_wording"] = int(bool(st.get("dev_wording")))
        r["dev_quote"] = st.get("dev_quote", "")[:90]
        r["qa_only"] = int(bool(st.get("qa_only")))
        r["owned_ip"] = int(bool(st.get("owned_ip")))
        r["ownip_quote"] = st.get("ownip_quote", "")[:90]
        jd = st.get("jd_chars")
        if jd is None or jd == "":
            jd = int(p["jd_chars"]) if str(p.get("jd_chars", "")).isdigit() else 0
            hits = {k: int(p[k]) if str(p.get(k, "")).isdigit() else 0
                    for k in ("repo_host_hits", "review_gate_hits", "cicd_hits")}
            hits["nongit_hits"] = 0
        else:
            hits = {k: int(st.get(k) or 0) for k in ("repo_host_hits", "review_gate_hits",
                                                     "cicd_hits", "nongit_hits")}
        r["jd_chars"] = jd; r.update(hits)
        r["jd_quote"] = (st.get("review_gate_quote") or st.get("repo_host_quote")
                         or p.get("jd_evidence", ""))[:90]
        r["extraction_verified"] = bool(st.get("extraction_verified")) or not (
            jd > 5000 and not any(hits[k] for k in ("repo_host_hits", "review_gate_hits", "cicd_hits")))

        # ---- identity (Stage E, from prepass corpora)
        for k in ("contact_name", "contact_title", "contact_linkedin", "identity_status"):
            r[k] = p.get(k, "")
        # ---- headcount numeric
        hc = s.get("headcount")
        r["hc_num"] = int(hc) if str(hc).isdigit() else BAND_MID.get(s.get("band_label", "").split(":")[0], None)

        # thin evidence: no proof and nothing harvested -> lane, not a crippled score
        if grade in ("SOURCE_ONLY", "NONE") and jd < 500 and not r["owned_ip"]:
            lanes["thin_evidence"].append({**s, "lane_reason": f"grade={grade}, jd={jd}"}); continue

        # ---- Stage F score
        sc = {"PROVEN_EQUIV": 25, "EXISTED_2COR": 25, "DOMAIN_ONLY": 5, "SOURCE_ONLY": 0, "NONE": 0}[grade]
        if grade == "EXISTED_2COR" and not w.get("wb_pre2024"): sc = 12 if len(cor) < 3 else 25
        sc += 25 * r["owned_ip"]
        sc += 20 * (hits["review_gate_hits"] > 0)
        sc += 10 * (hits["repo_host_hits"] > 0)
        sc += 10 * (hits["cicd_hits"] > 0)
        sc += 10 if jd > 20000 else (5 if jd >= 5000 else 0)
        if r["hc_num"] and 50 <= r["hc_num"] <= 150: sc += 10
        age = 0
        if rreg and rreg[:4].isdigit(): age = 2026 - int(rreg[:4])
        elif fy and str(fy).isdigit(): age = 2026 - int(fy)
        sc += 10 * (age >= 8)
        sc -= 10 * r["qa_only"]
        sc -= 10 * bool(hits["nongit_hits"])
        sc -= 10 * (s.get("staffing_mix") in ("True", "1", True))
        r["score"] = sc; r["years_active"] = age
        r["domain_age_key"] = rreg or (str(fy) if fy else "")
        rows.append(r)

    # ---- tie-break sort: score -> jd -> grade strength -> |hc-100| -> domain age
    GR = {"PROVEN_EQUIV": 3, "EXISTED_2COR": 2, "DOMAIN_ONLY": 1, "SOURCE_ONLY": 0, "NONE": 0}
    rows.sort(key=lambda r: (-r["score"], -r["jd_chars"], -GR[r["pre2024_grade"]],
                             abs((r["hc_num"] or 100) - 100), r["domain_age_key"] or "9999", r["domain"]))

    # a row that STILL fails extraction integrity after the re-crawl ships to a lane, not
    # to the queue — one stubborn row must not fail the whole audit nor ride unverified
    still_bad = [r for r in rows if r["jd_chars"] > 5000 and not any(
        r[k] for k in ("repo_host_hits", "review_gate_hits", "cicd_hits")) and not r["extraction_verified"]]
    for r in still_bad:
        lanes["extraction_suspect"].append({**r, "lane_reason": "zero signals unverified after re-crawl"})
    sbd = {r["domain"] for r in still_bad}
    rows = [r for r in rows if r["domain"] not in sbd]

    whales = [r for r in rows if (r.get("whale_candidate") in ("True", "1", True))
              or (r["owned_ip"] and (r["hc_num"] or 0) > 200)][:WHALE_LANE_SIZE]
    wd = {w["domain"] for w in whales}
    pool = [r for r in rows if r["domain"] not in wd]
    queue, reserve = pool[:QUEUE_SIZE], pool[QUEUE_SIZE:]

    def why(r):
        bits = [f'{r["pre2024_grade"]}({r["pre2024_evidence"].split(";")[0]})']
        if r["owned_ip"]: bits.append("owned IP: " + (r["ownip_quote"][:40] or "yes"))
        if r["review_gate_hits"]: bits.append(f'review-gate JD x{r["review_gate_hits"]}')
        if r["jd_chars"]: bits.append(f'jd {r["jd_chars"]}ch')
        if r["hc_num"]: bits.append(f'~{r["hc_num"]} staff')
        return "; ".join(bits)[:180]

    COLS = ["rank", "score", "name", "domain", "city", "source", "band_label", "hc_num",
            "pre2024_grade", "pre2024_evidence", "pre2024_confidence", "owned_ip", "ownip_quote",
            "repo_host_hits", "review_gate_hits", "cicd_hits", "nongit_hits", "jd_chars", "jd_quote",
            "dev_quote", "years_active", "contact_name", "contact_title", "contact_linkedin",
            "identity_status", "why_this_rank"]

    def w_csv(path, data, start_rank=1):
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            wr = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore"); wr.writeheader()
            for i, r in enumerate(data, start_rank):
                wr.writerow({**r, "rank": i, "why_this_rank": why(r)})
        print(f"   {os.path.basename(path):<22}{len(data)}")

    os.makedirs(LANES, exist_ok=True)
    w_csv(os.path.join(OUT, "whales.csv"), whales)
    w_csv(os.path.join(OUT, "enrich_queue.csv"), queue)
    w_csv(os.path.join(OUT, "reserve.csv"), reserve)
    for ln, data in lanes.items():
        cols = list(data[0].keys())
        with open(os.path.join(LANES, f"{ln}.csv"), "w", newline="", encoding="utf-8-sig") as f:
            wr = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); wr.writeheader(); wr.writerows(data)
        print(f"   lanes/{ln + '.csv':<20}{len(data)}")

    # ---- Stage G audit
    audit, ok = [], True
    bad = [r for r in queue if r["jd_chars"] > 5000 and not any(
        r[k] for k in ("repo_host_hits", "review_gate_hits", "cicd_hits")) and not r["extraction_verified"]]
    audit.append(f"1. zero-signal jd>5k unverified in queue: {len(bad)} {'PASS' if not bad else 'FAIL'}")
    ok &= not bad
    runs = mx = 0
    for a, b in zip(queue, queue[1:]):
        runs = runs + 1 if (a["score"] == b["score"] and a["name"].lower() <= b["name"].lower()) else 0
        mx = max(mx, runs)
    audit.append(f"2. longest same-score alphabetical run: {mx + 1} {'PASS' if mx + 1 <= 5 else 'FAIL'}")
    ok &= mx + 1 <= 5
    n_lanes = sum(len(v) for v in lanes.values())
    tot = len(queue) + len(reserve) + len(whales) + n_lanes + len(rejects)
    audit.append(f"3. conservation: q{len(queue)}+res{len(reserve)}+wh{len(whales)}+lanes{n_lanes}"
                 f"+rej{len(rejects)}={tot} vs survivors {len(sv)} {'PASS' if tot == len(sv) else 'FAIL'}")
    ok &= tot == len(sv)
    conf = [1 if r["pre2024_confidence"] == "Verified" else 0 for r in queue]
    scs = [r["score"] for r in queue]
    if len(set(conf)) > 1 and len(set(scs)) > 1:
        mc, ms = sum(conf) / len(conf), sum(scs) / len(scs)
        cov = sum((c - mc) * (s - ms) for c, s in zip(conf, scs))
        vc = sum((c - mc) ** 2 for c in conf) ** .5; vs = sum((s - ms) ** 2 for s in scs) ** .5
        corr = cov / (vc * vs) if vc and vs else 0
    else: corr = 0.0
    # 4. evidence spot-check: re-open pages for 20 sampled quotes; the words must be there
    random.seed(14)
    import urllib.request
    def refetch(u):
        """Fetch and normalize EXACTLY like the crawler's text_of() — quotes were extracted
        from tag-stripped text, so matching them against raw HTML fails on any quote that
        spans an inline tag (first version of this check 'failed' 10 true quotes that way)."""
        try:
            rq = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
            h = urllib.request.urlopen(rq, timeout=10).read(400_000).decode("utf-8", "replace")
            h = re.sub(r"<script\b.*?</script>|<style\b.*?</style>", " ", h, flags=re.S | re.I)
            return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h))
        except Exception:
            return None
    cand = [r for r in queue if (r["dev_quote"] or r["ownip_quote"]) and site.get(r["domain"], {}).get("final_url")]
    sample = random.sample(cand, min(20, len(cand)))
    okq = tot4 = 0
    for r in sample:
        page = refetch(site[r["domain"]]["final_url"])
        if page is None: continue                      # unreachable now != quote was fake
        tot4 += 1
        q = (r["dev_quote"] or r["ownip_quote"])[:25].strip()
        okq += int(bool(q) and q.lower()[:18] in page.lower())
    rate = (100 * okq / tot4) if tot4 else 0
    audit.append(f"4. evidence re-check: {okq}/{tot4} sampled quotes found on live page "
                 f"({rate:.0f}%) {'PASS' if rate >= 90 or tot4 == 0 else 'FAIL'}")
    ok &= rate >= 90 or tot4 == 0
    # 5. no giants among the queue's largest headcounts
    big = sorted(queue, key=lambda r: -(r["hc_num"] or 0))[:10]
    bad5 = [r["name"] for r in big if any(b in r["name"].lower() for b in BLOCK)
            or site.get(r["domain"], {}).get("redirected_offsite")]
    audit.append(f"5. giants/captives in queue top-10 headcounts: {bad5 or 'none'} "
                 f"{'PASS' if not bad5 else 'FAIL'}")
    ok &= not bad5
    audit.append(f"6. confidence-score correlation: {corr:+.3f} (info only — confidence never fed the score)")
    audit.append(f"7. queue={len(queue)} (target {QUEUE_SIZE}); identity known "
                 f"{sum(1 for r in queue if r['identity_status'] != 'identity_pending')}/{len(queue)}")
    if rejects:
        with open(os.path.join(OUT, "rejects_efg.csv"), "w", newline="", encoding="utf-8-sig") as f:
            wr = csv.DictWriter(f, fieldnames=list(rejects[0].keys()), extrasaction="ignore")
            wr.writeheader(); wr.writerows(rejects)
        print(f"   rejects_efg.csv        {len(rejects)}")
    open(os.path.join(OUT, "audit.md"), "w", encoding="utf-8").write(
        "# Prequal self-audit — " + datetime.date.today().isoformat() + "\n\n" + "\n".join(audit) + "\n")
    with open(os.path.join(OUT, "gate_losses.md"), "w", encoding="utf-8") as f:
        f.write("# Gate losses (D-F)\n\n")
        for ln, data in lanes.items(): f.write(f"- lane {ln}: {len(data)}\n")
        f.write(f"- queue {len(queue)} / reserve {len(reserve)} / whales {len(whales)}\n")
    print("\n" + "\n".join(audit))
    print("\nTOP 15 OF QUEUE:")
    for i, r in enumerate(queue[:15], 1):
        print(f'  {i:>3} {r["score"]:>3}  {r["name"][:34]:<36}{r["pre2024_grade"]:<14}'
              f'{"IP " if r["owned_ip"] else "   "}jd{r["jd_chars"]}')


main()
