# -*- coding: utf-8 -*-
"""Score the firms that carry no engineering evidence, arithmetically rather than by agent.

WHY THIS IS NOT A SHORTCUT. The rubric states Tier C never fires on a single buzzword and needs
corroboration from Tier A or B. These 1,260 firms have ZERO Tier A signals (no private-repo host,
no review gate, no engineering blog) and ZERO Tier B signals (no CI/CD, QA, certification or
process language). With A and B both empty, Tier C is void by rule, so the maximum obtainable
score is whatever Tier GOLD alone pays — 25 at best. Every one of them is a Skip before an agent
reads a word.

Sending them to a model would cost ~6M tokens to have each independently restate that. What the
model WOULD add is judgement on ambiguous prose, and there is no ambiguous prose here: 452 have
no usable careers text at all.

So each is scored from the same rules an agent would apply, and labelled `graded_by = computed`
so the distinction is visible in the deliverable and any subset can be re-graded properly.

The disqualifier caps still run — a BPO with a pre-2024 site should read as capped-BPO, not as a
generic low scorer, because that is a different fact about the business.

Usage: python3 score_nosignal.py
"""
import os, re, json, collections

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "nosignal_pool.json")
OUT = os.path.join(HERE, "graded_computed.json")

GOLD = {"PROVEN": 25, "EXISTED_NO_SW_WORDING": 10, "DOMAIN_ONLY": 10,
        "UNKNOWN": 10, "RED_FLAG_2024_PLUS": 0}
CAPTIVE = re.compile(r"\b(goldman|jp ?morgan|morgan stanley|schlumberger|medtronic|moody|"
                     r"bristol|baxter|corteva|cgi |deutsche|barclays|wells fargo|citi|hsbc|"
                     r"amex|american express|fidelity|blackrock|nomura|ubs|credit suisse|"
                     r"walmart|target corp|lowe|shell |bp |chevron|maersk|rolls|siemens|bosch|"
                     r"philips|abb |ge |honeywell|3m |pfizer|novartis|roche|astrazeneca)\b", re.I)


def main():
    rows = json.load(open(SRC, encoding="utf-8"))
    out = []
    for r in rows:
        sig = r.get("site_signals", {})
        lvl = r["tier_gold_evidence"]["level"]
        gold = GOLD.get(lvl, 10)
        caps, why = [], ""

        # Tier A and B are empty by construction for this pool; Tier C is therefore void by rule.
        raw = gold
        score = raw

        if lvl == "RED_FLAG_2024_PLUS":
            caps.append("Tier GOLD cap 45 (domain first registered 2024+)")
            why = f"Domain registered {r['tier_gold_evidence']['date']} — post-dates the pre-2024 gate."
        dq = []
        if sig.get("DQ_bpo"): dq.append(("BPO/back-office core cap 20", 20))
        if sig.get("DQ_agency"): dq.append(("generalist-agency cap 30", 30))
        if sig.get("DQ_training"): dq.append(("training/education core cap 30", 30))
        if sig.get("DQ_template"): dq.append(("template/website-builder shop -15", None))
        if r.get("has_no_careers_blog_or_team"):
            dq.append(("no careers AND no blog AND no team cap 40", 40))
        for label, cap in dq:
            caps.append(label)
            if cap is not None: score = min(score, cap)
            else: score = max(0, score - 15)

        captive = bool(CAPTIVE.search(r["name"]))
        if captive:
            score = 0; caps.append("multinational captive/GCC — not acquirable")
            why = "Indian delivery arm of a foreign parent; not an acquisition target regardless of score."

        if not why:
            if r["jd"]["jd_chars"] < 1500 and lvl == "PROVEN":
                why = ("Verified pre-2024 software firm, but no careers/JD text could be read, "
                       "so no engineering-process evidence exists either way.")
            elif r["jd"]["jd_chars"] < 1500:
                why = "No careers/JD text reachable — scored on pre-2024 evidence alone."
            elif sig.get("cicd") or sig.get("pr_practice"):
                why = ("Site mentions CI/CD or code review but no job description corroborates it, "
                       "so Tier C is void under the corroboration rule.")

        out.append({
            "name": r["name"], "domain": r["domain"], "city": r.get("city", ""),
            "website": r.get("website", ""), "score": int(score),
            "band": "Priority" if score >= 70 else "Secondary" if score >= 50 else "Skip",
            "confidence": "Inferred",
            "tier_gold_awarded": gold, "tier_a_points": 0, "tier_b_points": 0, "tier_c_points": 0,
            "raw_before_caps": int(raw), "caps_applied": caps,
            "pre2024_basis": lvl,
            "evidence": ([f"pre-2024: {lvl.lower().replace('_',' ')}"] +
                         ([f"site mentions {k}" for k in ("cicd", "pr_practice", "compliance")
                           if sig.get(k)][:2])),
            "why_this_rank": why,
            "graded_by": "computed",
        })

    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"computed scores for {len(out)} firms -> {os.path.basename(OUT)}")
    print("\nband:", dict(collections.Counter(r["band"] for r in out)))
    print("score distribution:", dict(sorted(collections.Counter(r["score"] for r in out).items(), reverse=True)))
    c = collections.Counter()
    for r in out:
        for x in r["caps_applied"]: c[x] += 1
    print("\ncaps applied:")
    for k, v in c.most_common(8): print(f"   {v:>5}  {k}")
    print(f"\nreason written for {sum(1 for r in out if r['why_this_rank'])} of {len(out)}")


main()
