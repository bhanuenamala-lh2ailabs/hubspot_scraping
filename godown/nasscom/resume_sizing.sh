#!/bin/zsh
# Resume SignalHire sizing whenever the daily search quota opens.
# headcount_sh.py is resumable: it skips domains already in headcounts_all.json, so a re-run
# never repeats a search or spends a credit twice. Exits cleanly on 402 and waits.
cd /Users/bhanu/Desktop/hubspot/godown/nasscom
for i in $(seq 1 96); do
  n=$(python3 -c "import json,os; p='headcounts_all.json'; print(len(json.load(open(p))) if os.path.exists(p) else 0)" 2>/dev/null)
  echo "[$(date '+%m-%d %H:%M')] attempt $i — $n / 1681 sized"
  python3 headcount_sh.py --src sizing_pool.json --out headcounts_all.json --all 2>&1 | tail -4
  n2=$(python3 -c "import json,os; p='headcounts_all.json'; print(len(json.load(open(p))) if os.path.exists(p) else 0)" 2>/dev/null)
  if [ "$n2" -ge 1681 ]; then echo "SIZING COMPLETE at $n2"; break; fi
  sleep 1800
done
