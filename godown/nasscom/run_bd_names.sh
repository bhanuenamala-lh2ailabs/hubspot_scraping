#!/bin/zsh
# Widen the Bangladesh scrape until 100 founder names exist — WITHOUT SignalHire.
#
# Standing at 40 of 100 named. Two levers, both free:
#   a) the 3 rendered batches from the first 100 have never been name-extracted
#   b) 166 more RELEVANT Bangladesh firms sit untouched below the top-100 cut
#
# This script does the SCRAPING half (plain fetch, then chromium for JS-only pages) and leaves
# ready-to-read batches on disk. The name extraction itself is an agent job and runs in the main
# session — a regex cannot do it: two attempts returned "Insights Blogs Case" and "View Full Bio"
# as founder names.
#
# Resumable: every stage skips what already exists.
set -u
cd /Users/bhanu/Desktop/hubspot/godown/nasscom
LOG=/tmp/bdnames.log
say() { echo "[$(date '+%H:%M:%S')] $*" >> $LOG; }

say "=== tranche 2: 166 more Bangladesh firms, plain crawl ==="
python3 crawl_for_scoring.py --src bd_tranche2.csv --out bd2_evidence.json --workers 10 >> $LOG 2>&1
say "crawl done"

say "=== team/about pages + LinkedIn URLs ==="
python3 fetch_people_pages.py --src bd2_evidence.json --out bd2_people.json --workers 8 >> $LOG 2>&1
say "people pages done"

say "=== render the JS-only ones ==="
python3 - <<'PY' >> $LOG 2>&1
import json
rows=json.load(open("bd2_people.json",encoding="utf-8"))
need=[{"name":r["name"],"domain":r["domain"],"founder":"","website":"http://"+r["domain"]}
      for r in rows if len(r.get("text",""))<400 and not r.get("linkedin_profiles")]
json.dump(need,open("bd2_need_render.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
print(f"to render: {len(need)}")
PY
python3 bd_render_teams.py --src bd2_need_render.json --out bd2_rendered.json --prefix bd2r >> $LOG 2>&1
say "render done"

python3 - <<'PY' >> $LOG 2>&1
import json,glob,os
os.makedirs("bd_batches",exist_ok=True)
seen=set(); pool=[]
for f in ("bd2_people.json","bd2_rendered.json"):
    try: rows=json.load(open(f,encoding="utf-8"))
    except Exception: continue
    for r in rows:
        if r["domain"] in seen: continue
        if len(r.get("text",""))>200 or r.get("linkedin_profiles"):
            seen.add(r["domain"]); pool.append(r)
per,n=22,0
for i in range(0,len(pool),per):
    n+=1
    json.dump(pool[i:i+per],open(f"bd_batches/bd2_{n}.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
print(f"tranche-2 usable: {len(pool)} firms -> {n} batches (bd_batches/bd2_*.json)")
print(f"pending extraction overall: {len(glob.glob('bd_batches/bdr_*.json'))} rendered + {n} tranche-2")
PY
say "=== SCRAPING COMPLETE — batches ready for agent name-extraction ==="
