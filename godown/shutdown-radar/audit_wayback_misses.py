# -*- coding: utf-8 -*-
"""Is every `domain_not_found` a REAL miss, or did some rows just hit a network error?

cdx() returns None on any network failure and check() then reports domain_not_found —
indistinguishable, in the checkpoint, from "we asked and archive.org said nothing".
Because run_wayback.py skips anything already checkpointed, such a row is poisoned
permanently.

The tell: cdx() only writes its disk cache on a SUCCESSFUL fetch. So for a genuine miss
every candidate domain has a cache file holding an empty result. For a network-error row
the cache files are absent — we never got an answer to store.
"""
import os, sys, csv, json, hashlib
sys.path.insert(0, "src")
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
from shutdown_radar import wayback as WB

CACHE = WB.CACHE
ck = json.load(open("data/out/wayback_checkpoint.json", encoding="utf-8"))
rows = {r["company"]: r for r in
        csv.DictReader(open("data/out/LH2_dead_companies_with_codebases.csv",
                            encoding="utf-8-sig"))}

def cache_url(dom):
    return (f"http://web.archive.org/cdx/search/cdx?url={dom}&matchType=domain"
            f"&output=json&fl=timestamp,original,statuscode&collapse=urlkey&limit=400")

def cached(dom):
    p = os.path.join(CACHE, hashlib.sha256(cache_url(dom).encode()).hexdigest() + ".json")
    return os.path.exists(p)

real_miss = answered = no_candidates = network_suspect = 0
suspects = []
for comp, v in ck.items():
    if v.get("product_evidence") != "domain_not_found":
        answered += 1
        continue
    r = rows.get(comp)
    if not r:
        continue
    doms = WB.candidate_domains(r["legal_name"] or r["company"])
    if not doms:
        no_candidates += 1          # blocked generic stem / unusable name — a real skip
        continue
    hit = [d for d in doms if cached(d)]
    if hit:
        real_miss += 1              # we asked, archive.org had nothing
    else:
        network_suspect += 1        # never got an answer for ANY candidate
        suspects.append(comp)

print(f"checkpointed rows            : {len(ck):,}")
print(f"  resolved to some evidence  : {answered:,}")
print(f"  domain_not_found, REAL     : {real_miss:,}   (cache holds an empty answer)")
print(f"  domain_not_found, no cands : {no_candidates:,}   (generic stem blocked / unusable name)")
print(f"  domain_not_found, SUSPECT  : {network_suspect:,}   (no cached answer for any candidate)")
if suspects:
    print("\nfirst 15 suspects:", suspects[:15])
    json.dump(suspects, open("data/out/wayback_network_suspects.json", "w"), indent=1)
    print(f"\nwrote data/out/wayback_network_suspects.json ({len(suspects)} rows to re-query)")
