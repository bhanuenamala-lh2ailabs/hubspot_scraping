#!/bin/bash
# Auto-resume searchByQuery once the daily quota clears.
# Quota hit 2026-08-17 14:39:55 IST -> first probe 14:45, then every 20 min for 3h.
# On success: runs searchq_enrich.py --apply (size=3, batches of 10, resumes at Lamiya).
# Sends NO email. Logs everything to searchq_auto.log.
cd /Users/bhanu/Desktop/hubspot/godown/founder_id
LOG=searchq_auto.log
TARGET_EPOCH=$(python3 -c "import datetime,time;print(int(time.mktime(datetime.datetime(2026,8,18,14,45,0).timetuple())))")
say(){ echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> $LOG; }

say "runner armed; waiting until 14:45 IST"
NOW=$(date +%s); WAIT=$((TARGET_EPOCH-NOW))
[ $WAIT -gt 0 ] && sleep $WAIT

for i in $(seq 1 10); do
  CODE=$(python3 - <<'PY'
import json,urllib.request,urllib.error
env={l.split('=',1)[0].strip().lower():l.split('=',1)[1].strip() for l in open("/Users/bhanu/Desktop/hubspot/.env",encoding='utf-8-sig') if '=' in l and not l.strip().startswith('#')}
H={"apikey":env["signal_hire"],"Content-Type":"application/json"}
b={"currentCompany":"Zealous System","currentTitle":"founder OR CEO","size":1}
try:
    r=urllib.request.Request("https://www.signalhire.com/api/v1/candidate/searchByQuery",
        data=json.dumps(b).encode(),method="POST",headers=H)
    with urllib.request.urlopen(r,timeout=45) as x: print(x.status)
except urllib.error.HTTPError as e: print(e.code)
except Exception: print("ERR")
PY
)
  say "probe $i/10 -> HTTP $CODE"
  if [ "$CODE" = "200" ]; then
    say "QUOTA CLEARED — running searchq_enrich.py --apply on remaining 85"
    python3 searchq_enrich.py --apply >> $LOG 2>&1
    say "run finished (exit $?)"
    python3 -c "
import json,collections
p=json.load(open('searchq_pushed.json'))
c=collections.Counter(v['owner'] for v in p.values())
print('  TOTALS now: Yuktha %d, Lamiya %d, pushed %d'%(c.get('Yuktha',0),c.get('Lamiya',0),len(p)))
" >> $LOG 2>&1
    exit 0
  fi
  say "still blocked; sleeping 20 min"
  sleep 1200
done
say "gave up after 10 probes (~3h) — quota did not clear"
