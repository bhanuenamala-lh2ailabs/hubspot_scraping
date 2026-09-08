#!/bin/zsh
# Unattended pipeline for the Bangladesh 100, running alongside the NASSCOM 80.
#
# State when this starts: 100 firms deduped and selected, 40 with a founder name (34 scraped,
# 6 inferred from personal email addresses), 18 with a LinkedIn URL, 0 with a lead phone.
# The 74 company switchboard numbers are held in `company_phone` and are deliberately NOT
# treated as lead phones — they reach a receptionist, not the founder.
#
# Stages:
#   1. render the JS-only team pages for the 60 with no name yet          (chromium, free)
#   2. <- agent name-extraction happens in the main session >
#   3. reveal by LinkedIn URL for a real number                           (credits, no search)
#   4. push 50/50 Yuktha/Lamiya, lead_source "Scraped ( Bangladesh )"
#
# NUMBER RULE: this batch accepts ANY dialable number, not just +880 — a deliberate exception.
# bangladesh_number.py is used to LABEL what we got, never to reject it.
#
# Waits for the other chromium job to finish first: three headless browsers at once on this
# machine just makes all three slow and raises the odds of a timeout being mistaken for a site
# genuinely having no team page.
set -u
cd /Users/bhanu/Desktop/hubspot/godown/nasscom
LOG=/tmp/runbd.log
say() { echo "[$(date '+%H:%M:%S')] $*" >> $LOG; }

say "=== waiting for the other render job to finish (avoid 3 chromiums at once) ==="
while pgrep -f "bd_render_teams.py --src above20_need_name" > /dev/null; do sleep 30; done
say "clear"

say "=== stage 1: render JS team pages for Bangladesh firms with no name ==="
python3 bd_render_teams.py --src bd_consolidated.json --out bd_rendered_teams.json --prefix bdr >> $LOG 2>&1
say "stage 1 done"

python3 - <<'PY' >> $LOG 2>&1
import json, glob
rows = json.load(open("bd_consolidated.json", encoding="utf-8"))
try:
    rend = {r["domain"]: r for r in json.load(open("bd_rendered_teams.json", encoding="utf-8"))}
except Exception:
    rend = {}
gained = sum(1 for d, r in rend.items() if r.get("linkedin_profiles"))
print(f"rendered {len(rend)} firms; {gained} now expose a LinkedIn profile URL")
have_li = sum(1 for r in rows if r.get("linkedin"))
print(f"linkedin URLs before render: {have_li}  -> revealable without any search")
print(f"batches ready for agent extraction: {len(glob.glob('bd_batches/bdr_*.json'))}")
PY
say "=== ready for agent name-extraction in the main session ==="
