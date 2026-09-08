# -*- coding: utf-8 -*-
"""Strip CSS-derived phantom signals out of the harvested JD evidence.

FontAwesome ships an icon class for every brand, including `.fa-bitbucket`, `.fa-github` and
`.fa-gitlab`. When a stylesheet survives tag-stripping, the harvester reads

    .fa-bitbucket:before { content: "\\f171"; }

as prose and records a `private_repo_host` hit. Four firms in one batch of twenty surfaced as
Tier A candidates on exactly that — a firm whose only "Bitbucket evidence" is an icon font has
told us nothing about how it manages code.

This re-judges every stored quote and drops the CSS ones, then recomputes the signal counts and
the Tier A flag from what survives. Cheap: it re-reads the saved evidence rather than re-crawling
1,742 sites.

A quote is treated as CSS/markup, not prose, when it shows any of: a declaration block, a
pseudo-element, a `content:` rule, an icon-class prefix, a font or url() rule, or simply more
punctuation than words.

Usage: python3 fix_css_false_positives.py
"""
import os, re, json, collections

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "jd_evidence.json")

CSSY = re.compile(
    r"(\{[^}]*\}|:before\b|:after\b|content\s*:|\.fa-|\bfa[bsrl]?\s+fa-|font-family\s*:|"
    r"url\(|@media\b|!important|\bclass=|\bsvg\b|viewBox|xmlns|\\f[0-9a-f]{3}|"
    r"[;{}]\s*[.#][a-z-]+\s*[{,])", re.I)


def is_css(s):
    if CSSY.search(s): return True
    words = re.findall(r"[A-Za-z]{2,}", s)
    punct = len(re.findall(r"[{}:;.#\\/()\[\]]", s))
    # a real JD sentence is mostly words; a rule is mostly punctuation
    return len(words) < 5 or punct > max(len(words), 4)


def main():
    rows = json.load(open(SRC, encoding="utf-8"))
    changed, zeroed = 0, collections.Counter()
    for r in rows:
        q = r.get("quotes") or {}
        s = r.get("signals") or {}
        before_a = bool(s.get("private_repo_host") and s.get("review_gate"))
        for k in list(q.keys()):
            clean = [x for x in q[k] if not is_css(x)]
            if len(clean) != len(q[k]):
                dropped = len(q[k]) - len(clean)
                # the stored quotes are a sample of the matches; if EVERY sampled quote for a
                # signal was CSS, the signal itself is not credible — zero it rather than scale it
                if not clean:
                    s.pop(k, None); q.pop(k, None); zeroed[k] += 1
                else:
                    q[k] = clean
                    s[k] = max(1, (s.get(k, 0) * len(clean)) // (len(clean) + dropped))
                changed += 1
        r["quotes"], r["signals"] = q, s
        r["meets_tier_a_clean"] = bool(s.get("private_repo_host") and s.get("review_gate"))
        if before_a and not r["meets_tier_a_clean"]:
            r["tier_a_revoked_reason"] = "only evidence was icon-font CSS, not job-description prose"

    json.dump(rows, open(SRC, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ta = sum(1 for r in rows if r.get("meets_tier_a_clean"))
    rev = [r for r in rows if r.get("tier_a_revoked_reason")]
    print(f"quotes cleaned on {changed} signal entries")
    print("signals zeroed entirely (all sampled quotes were CSS):")
    for k, v in zeroed.most_common(): print(f"   {v:>4}  {k}")
    print(f"\nTier A after cleaning : {ta}   (was 21)")
    print(f"Tier A revoked        : {len(rev)}")
    for r in rev[:15]: print(f"   {r['name'][:46]}")


main()
