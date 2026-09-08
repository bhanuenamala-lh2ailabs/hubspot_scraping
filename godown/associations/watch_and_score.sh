#!/bin/bash
cd /Users/bhanu/Desktop/hubspot/godown/associations
# wait for the site lane to finish (it is the one that carries owned_ip / dev signals)
until [ "$(wc -l < prequal_out/d_site.jsonl 2>/dev/null || echo 0)" -ge 672 ] || ! pgrep -f "lane site" >/dev/null; do
  sleep 20
done
sleep 5
echo "[$(date '+%H:%M:%S')] site lane done -> scoring" >> score_run.log
python3 score_assoc.py >> score_run.log 2>&1
echo "[$(date '+%H:%M:%S')] scored" >> score_run.log
