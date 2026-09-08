# -*- coding: utf-8 -*-
"""Stage-F pass: LinkedIn URLs for every board-cited name in state — the reveal keys.

One paced DDG query per person (site:linkedin.com/in "<name>" "<company>"). Wall -> the row
simply stays name_only and the next fpass run retries it; a real empty answer marks
li_checked so it isn't re-queried every night. Runs inside the same daily engine quota as
the resolver (shared counters table).
"""
import os, sys, json, sqlite3
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import resolver as R

c = R.db()
rows = [(r[0], json.loads(r[1])) for r in
        c.execute("SELECT domain, data FROM companies WHERE status='name_only'")]
print(f"F-pass over {len(rows)} named companies", flush=True)
done = full = 0
for dom, rec in rows:
    if rec.get("li_checked"): continue
    nm, comp = rec["founder_name"], rec["company"]
    try:
        hits = R.ddg(c, f'site:linkedin.com/in "{nm}" "{comp}"')
    except SystemExit as e:
        print(f"stopping: {e}"); break
    if hits is None: continue                    # wall — retry next run
    url = ""
    for ttl, u in hits:
        if "linkedin.com/in/" in u and R.LI_RX.match(u.split("?")[0]):
            if nm.split()[0].lower() in ttl.lower():
                url = u.split("?")[0]; break
    if not url:                                  # relax: name-only query, company match in title
        try: hits2 = R.ddg(c, f'site:linkedin.com/in "{nm}"')
        except SystemExit as e: print(f"stopping: {e}"); break
        for ttl, u in (hits2 or []):
            if "linkedin.com/in/" in u and R.LI_RX.match(u.split("?")[0]):
                t = ttl.lower()
                if nm.split()[0].lower() in t and any(w in t for w in comp.lower().split()[:2]):
                    url = u.split("?")[0]; break
    rec["li_checked"] = True
    if url:
        rec["linkedin_url"] = url; rec["identity_status"] = "full"; full += 1
        c.execute("UPDATE companies SET status='full', data=? WHERE domain=?", (json.dumps(rec), dom))
    else:
        c.execute("UPDATE companies SET data=? WHERE domain=?", (json.dumps(rec), dom))
    c.commit(); done += 1
    print(f'{comp[:30]:<32}{nm[:24]:<26}{"LI FOUND" if url else "-"}', flush=True)
print(f"\nF-pass: {done} checked, {full} upgraded to full (reveal-ready)")
