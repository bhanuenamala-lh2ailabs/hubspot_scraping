# -*- coding: utf-8 -*-
"""Re-crawl careers for queue rows that failed audit check 1.

These rows carried jd_chars>5000 with all-zero signals FROM THE OLD NASSCOM HARVEST — the
exact silent-zero failure the spec guards against. The site lane skipped their careers pages
because the prepass supplied numbers; this re-crawls them fresh so the zeros are either
replaced by real counts or verified with a logged sample. Appends to d_site.jsonl; the merge
takes last-record-per-domain, so these supersede.
"""
import os, sys, csv, json
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "prequal_out")
sys.path.insert(0, HERE)
import stage_d_crawl as C

q = list(csv.DictReader(open(os.path.join(OUT, "enrich_queue.csv"), encoding="utf-8-sig")))
sus = [r for r in q if int(r["jd_chars"] or 0) > 5000
       and not any(int(r[k] or 0) for k in ("repo_host_hits", "review_gate_hits", "cicd_hits"))]
print(f"re-crawling careers for {len(sus)} suspect rows")
with open(os.path.join(OUT, "d_site.jsonl"), "a", encoding="utf-8") as ck:
    for i, r in enumerate(sus, 1):
        res = C.do_site({"domain": r["domain"], "website": f'https://{r["domain"]}', "needs": "careers"})
        res["resurvey"] = "audit-check-1"
        ck.write(json.dumps(res, ensure_ascii=False) + "\n"); ck.flush()
        print(f'  [{i}/{len(sus)}] {r["domain"]:<30} jd={res.get("jd_chars", "?")} '
              f'hits={res.get("repo_host_hits", 0)}/{res.get("review_gate_hits", 0)}/{res.get("cicd_hits", 0)}', flush=True)
