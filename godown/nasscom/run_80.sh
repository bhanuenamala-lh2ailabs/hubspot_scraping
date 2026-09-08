#!/bin/zsh
# Unattended pipeline for the 80-lead NASSCOM goal.
#
# Everything here is FREE except the final reveal step, which spends credits (not the exhausted
# search quota) and only on people we have already identified. The expensive stage never runs on
# a firm we know nothing about.
#
# Stages, in order:
#   1. team pages + LinkedIn URLs for the top-600 by engineering signal   (plain HTTP)
#   2. render the JS-only team pages that stage 1 could not read          (chromium)
#   3. <- agent name-extraction happens in the main session, not here >
#   4. reveal by LinkedIn URL, +91 gate                                   (credits)
#   5. push in batches of 8: 5 Lamiya, 3 Yuktha
#
# Resumable throughout: every stage skips what it already has, so a kill costs only the row in
# flight. Progress lands in /tmp/run80.log.
set -u
cd /Users/bhanu/Desktop/hubspot/godown/nasscom
LOG=/tmp/run80.log
say() { echo "[$(date '+%H:%M:%S')] $*" >> $LOG; }

say "=== stage 1: team pages for top 600 (free) ==="
until [ -f top600_people.json ]; do sleep 20; done
while pgrep -f "fetch_people_pages.py --src top600_evidence" > /dev/null; do sleep 20; done
say "stage 1 done: $(python3 -c "import json;d=json.load(open('top600_people.json'));print(len(d),'rows,',sum(1 for r in d if r['linkedin_profiles']),'with linkedin')" 2>/dev/null)"

say "=== stage 2: render JS team pages for those with no linkedin (free) ==="
python3 - <<'PY' >> $LOG 2>&1
import json
rows=json.load(open("top600_people.json",encoding="utf-8"))
need=[{"name":r["name"],"domain":r["domain"],"founder":"","website":"http://"+r["domain"]}
      for r in rows if not r["linkedin_profiles"] and len(r.get("text",""))<400]
json.dump(need,open("top600_need_render.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
print(f"to render: {len(need)}")
PY
python3 bd_render_teams.py --src top600_need_render.json --out top600_rendered.json --prefix t6r >> $LOG 2>&1
say "stage 2 done"

say "=== ready for agent name-extraction in the main session ==="
say "batches waiting: $(ls bd_batches/t6r_*.json 2>/dev/null | wc -l | tr -d ' ')"
