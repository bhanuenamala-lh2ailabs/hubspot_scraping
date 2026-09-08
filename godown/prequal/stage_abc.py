# -*- coding: utf-8 -*-
"""PREQUAL Stages A-C — dedupe, acquirability gates, metadata ICP gates. No web fetches.

Implements the pre-enrichment universe filter spec (Stages A-C) over the two universes this
laptop actually holds:
  GoodFirms  lh2-pipeline/data/pipeline.sqlite  (5,369 companies; size_band, founded_year,
             segment free-text, and a people table reused later at Stage E)
  NASSCOM    godown/nasscom/nasscom_members.csv (2,775; name/city/website only — headcount
             joined from NASSCOM_RANKED where the earlier run resolved it)

Per spec: prior NASSCOM scores are UNTRUSTED and are NOT read here; only raw harvested facts
get reused, and that happens at Stage D, not in these gates. GoodFirms metadata (size band,
founded year, segment) is trusted for Stage-1 gating.

Stage-B gates fire only on POSITIVE evidence of a category, with the triggering quote stored.
Absence of dev signals is never a rejection here — that routing belongs to Stage D lanes.

Outputs under prequal_out/: survivors.csv, rejects.csv, lanes/needs_manual_lookup.csv,
lanes/tier_c_small.csv, state.json, and a printed gate-loss table.

Usage: python3 stage_abc.py
"""
import os, re, csv, json, sqlite3, collections, difflib

HERE = os.path.dirname(os.path.abspath(__file__)); HUB = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(HERE, "prequal_out"); LANES = os.path.join(OUT, "lanes")
DB = os.path.join(HUB, "lh2-pipeline", "data", "pipeline.sqlite")
NAS = os.path.join(HUB, "godown", "nasscom")
CRM = os.path.join(HUB, "DEALS_MASTER.csv")
FOUNDED_CUTOFF = 2023

SUF = re.compile(r"\b(pvt|private|limited|ltd|llp|inc|technologies|technology|tech|solutions|"
                 r"software|softwares|systems|services|consultancy|consulting|labs|infotech|"
                 r"india|global|group|corp|corporation|company|co)\b")


def norm_dom(u):
    u = (u or "").strip().lower()
    u = re.sub(r"^https?://", "", u); u = re.sub(r"^www\.", "", u)
    return u.split("/")[0].split("?")[0]


def norm_name(s):
    s = re.sub(r"[^a-z0-9 ]", " ", (s or "").lower())
    s = SUF.sub(" ", s)
    return re.sub(r"\s+", " ", s).strip()


# ---------------------------------------------------------------- Stage B category evidence
# Each gate: (reject_reason, regex over the GoodFirms segment/description text). POSITIVE
# evidence only; the matched snippet is stored as the quote. Dev-presence words act as a veto
# for the softer categories: "digital marketing AND software development" is a mixed shop, and
# mixed shops are Stage-D material, not a Stage-B kill.
DEV = re.compile(r"software development|product engineering|app development|application development|"
                 r"custom software|web development|product development|saas|erp|crm solution", re.I)
GATES = [
    ("gcc_captive",     re.compile(r"global capability cent|capability cent(er|re)|captive unit|"
                                   r"(subsidiary|india arm|indian arm) of [A-Z]|offshore development cent(er|re) of", re.I), False),
    ("bpo_core",        re.compile(r"\b(bpo|kpo)\b|business process outsourcing|call cent(er|re) services|"
                                   r"back[- ]office (services|support)|data entry services", re.I), True),
    ("training_core",   re.compile(r"training institute|placement (assistance|guarantee)|our (students|learners)|"
                                   r"courses? (offered|catalog)|certification courses|coaching (cent|class)", re.I), True),
    ("marketing_only",  re.compile(r"digital marketing (agency|company)|seo (agency|company|services)|"
                                   r"social media (marketing|agency)|branding agency|performance marketing", re.I), True),
    ("template_reseller", re.compile(r"(wordpress|shopify|wix) themes?|website templates?|theme (shop|store)|"
                                     r"ready[- ]made websites?", re.I), True),
    ("body_shop_pure",  re.compile(r"hire (dedicated )?(developers?|programmers?|coders?)|staff augmentation|"
                                   r"contract staffing|it staffing|manpower (supply|services)|bench strength", re.I), True),
]


def stage_b(text):
    """-> (reject_reason, quote) or (None, ''). Dev-veto applies where marked."""
    if not text: return None, ""
    for reason, rx, dev_vetoes in GATES:
        m = rx.search(text)
        if not m: continue
        if dev_vetoes and DEV.search(text): continue        # mixed shop -> keep for Stage D
        i = max(0, m.start() - 40)
        quote = " ".join(text[i:m.end() + 40].split())[:90]
        return reason, quote
    return None, ""


# BOTH band vocabularies, because the DB normalizes what the raw listings spell out — the
# first run keyed only the raw form and 789 '<10' companies sailed through the too_small gate
# as survivors. '250+' is unbounded, so it cannot be split whale-vs-too-big here: it routes
# to whale_candidate and Stage D resolves the actual number (>800 -> out there).
BAND = {"Freelancer": ("too_small", None), "2 - 9": ("too_small", None), "<10": ("too_small", None),
        "10 - 49": (None, "10-49"), "10-49": (None, "10-49"),
        "50 - 249": (None, "50-249"), "50-249": (None, "50-249"),
        "250 - 999": (None, "250+"), "250+": (None, "250+"),
        "1,000 - 9,999": ("too_big_not_icp", None), "10000+": ("too_big_not_icp", None)}


def main():
    os.makedirs(LANES, exist_ok=True)

    # ---- load universes -------------------------------------------------------
    uni = []
    con = sqlite3.connect(DB)
    for dom, nm, ws, city, fy, sb in con.execute(
            "SELECT domain, company_name, website, city, founded_year, size_band FROM companies"):
        uni.append({"source": "goodfirms", "name": nm or "", "city": city or "",
                    "website": ws or "", "domain": norm_dom(dom or ws),
                    "founded_year": fy, "size_band": (sb or "").strip(), "seg": ""})
    seg = {norm_dom(r[0] or ""): (r[1] or "") for r in con.execute(
        "SELECT website_raw, segment_raw FROM raw_listings")}
    segc = {}
    for r in con.execute("SELECT domain, segment FROM companies"):
        segc[norm_dom(r[0] or "")] = r[1] or ""
    for u in uni:
        u["seg"] = segc.get(u["domain"]) or seg.get(u["domain"]) or ""

    ncnt = 0
    hc = {}
    for r in csv.DictReader(open(f"{NAS}/NASSCOM_RANKED.csv", encoding="utf-8-sig")):
        if r.get("headcount", "").strip().isdigit():
            hc[norm_dom(r.get("domain") or r.get("website"))] = int(r["headcount"])
    for r in csv.DictReader(open(f"{NAS}/nasscom_members.csv", encoding="utf-8-sig")):
        d = norm_dom(r.get("website"))
        uni.append({"source": "nasscom", "name": r.get("name", ""), "city": r.get("city", ""),
                    "website": r.get("website", ""), "domain": d,
                    "founded_year": None, "size_band": "", "seg": "",
                    "headcount": hc.get(d)})
        ncnt += 1
    print(f"universe: goodfirms {len(uni)-ncnt} + nasscom {ncnt} = {len(uni)}")

    # ---- CRM keys -------------------------------------------------------------
    crm_dom, crm_name = set(), {}
    for r in csv.DictReader(open(CRM, encoding="utf-8-sig")):
        if r.get("lh2_domain"): crm_dom.add(norm_dom(r["lh2_domain"]))
        n = norm_name(r.get("dealname", ""))
        if n: crm_name.setdefault(n[:1], set()).add(n)   # blocked by first letter for fuzzy

    rejects, lanes = [], collections.defaultdict(list)
    survivors = []

    # ---- Stage A: in-universe dedupe (keep the fuller row) --------------------
    bydom = {}
    dup_a = 0
    nodomain = []
    for u in uni:
        if not u["domain"]:
            nodomain.append(u); continue
        prev = bydom.get(u["domain"])
        if prev is None:
            bydom[u["domain"]] = u
        else:
            dup_a += 1
            filled = lambda x: sum(1 for v in x.values() if v)
            keep, drop = (u, prev) if filled(u) > filled(prev) else (prev, u)
            keep["source"] = "+".join(sorted(set(keep["source"].split("+")) | set(drop["source"].split("+"))))
            if drop.get("founded_year") and not keep.get("founded_year"):
                keep["founded_year"] = drop["founded_year"]
            if drop.get("size_band") and not keep.get("size_band"): keep["size_band"] = drop["size_band"]
            bydom[u["domain"]] = keep
    for u in nodomain:
        lanes["needs_manual_lookup"].append({**u, "lane_reason": "no website/domain in source"})

    # ---- Stage A: CRM dedupe --------------------------------------------------
    pool = []
    for u in bydom.values():
        if u["domain"] in crm_dom:
            rejects.append({**u, "stage": "A", "reject_reason": "already_in_crm",
                            "evidence": f'domain {u["domain"]} on a live deal'}); continue
        nn = norm_name(u["name"])
        hit = ""
        if nn and len(nn) > 3:
            for cand in crm_name.get(nn[:1], ()):
                if cand == nn or (abs(len(cand) - len(nn)) <= 6 and
                                  difflib.SequenceMatcher(None, nn, cand).ratio() >= 0.92):
                    hit = cand; break
        if hit:
            rejects.append({**u, "stage": "A", "reject_reason": "already_in_crm",
                            "evidence": f'name ~ "{hit}" >=0.92'}); continue
        pool.append(u)

    # ---- Stage B: acquirability gates (positive evidence only) ----------------
    pool2 = []
    for u in pool:
        reason, quote = stage_b(u.get("seg", ""))
        if reason:
            rejects.append({**u, "stage": "B", "reject_reason": reason, "evidence": quote})
        else:
            u["staffing_mix"] = bool(re.search(r"staff augmentation|staffing", u.get("seg", ""), re.I)
                                     and DEV.search(u.get("seg", "")))
            pool2.append(u)

    # ---- Stage C: metadata ICP gates ------------------------------------------
    for u in pool2:
        fy = u.get("founded_year")
        if fy and int(fy) > FOUNDED_CUTOFF:
            rejects.append({**u, "stage": "C", "reject_reason": "founded_2024_plus",
                            "evidence": f"source founded_year={fy}"}); continue
        band = u.get("size_band", "")
        hcv = u.get("headcount")
        verdict, bandlab = BAND.get(band, (None, None))
        if hcv is not None:                     # a resolved number beats a band
            if hcv < 10: verdict = "too_small"
            elif hcv < 25: verdict, bandlab = "tier_c", None
            elif hcv <= 800: verdict, bandlab = None, f"resolved:{hcv}"
            else: verdict = "too_big_not_icp"
        if verdict == "too_small":
            rejects.append({**u, "stage": "C", "reject_reason": "too_small",
                            "evidence": f"band={band or hcv}"}); continue
        if verdict == "too_big_not_icp":
            rejects.append({**u, "stage": "C", "reject_reason": "too_big_not_icp",
                            "evidence": f"band={band or hcv}"}); continue
        if verdict == "tier_c":
            lanes["tier_c_small"].append({**u, "lane_reason": f"headcount {hcv} in 10-24"}); continue
        u["headcount_unknown"] = not band and hcv is None
        u["whale_candidate"] = bandlab == "250+" or (hcv or 0) > 200
        u["band_label"] = bandlab or band or ""
        survivors.append(u)

    # ---- write ----------------------------------------------------------------
    KEEP = ["source", "name", "city", "website", "domain", "founded_year", "size_band",
            "band_label", "headcount", "headcount_unknown", "whale_candidate", "staffing_mix"]
    def w(path, rows, extra=()):
        cols = KEEP + list(extra)
        with open(path, "w", newline="", encoding="utf-8-sig") as fh:
            wr = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            wr.writeheader()
            for r in rows: wr.writerow(r)
        print(f"   {os.path.relpath(path, HERE):<42}{len(rows)}")

    w(os.path.join(OUT, "survivors.csv"), survivors)
    w(os.path.join(OUT, "rejects.csv"), rejects, ("stage", "reject_reason", "evidence"))
    for ln, rows in lanes.items():
        w(os.path.join(LANES, f"{ln}.csv"), rows, ("lane_reason",))
    json.dump({"stage": "C", "survivors": len(survivors), "rejects": len(rejects),
               "lanes": {k: len(v) for k, v in lanes.items()}, "in_universe_dupes": dup_a},
              open(os.path.join(OUT, "state.json"), "w"), indent=1)

    # ---- gate-loss table ------------------------------------------------------
    print(f"\nin-universe duplicate domains merged: {dup_a}")
    print("GATE LOSSES:")
    c = collections.Counter((r["stage"], r["reject_reason"]) for r in rejects)
    for (st, why), n in sorted(c.items()):
        print(f"   {st}  {why:<22}{n:>5}")
    print(f"lanes: " + ", ".join(f"{k}={len(v)}" for k, v in lanes.items()))
    print(f"\nSURVIVORS -> Stage D: {len(survivors)} "
          f"(whale_candidates {sum(1 for s in survivors if s['whale_candidate'])}, "
          f"headcount_unknown {sum(1 for s in survivors if s['headcount_unknown'])})")
    tot = len(survivors) + len(rejects) + sum(len(v) for v in lanes.values())
    print(f"conservation: {tot} + {dup_a} merged == {len(uni)} in? {tot + dup_a == len(uni)}")


main()
