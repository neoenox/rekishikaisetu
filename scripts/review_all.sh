#!/bin/bash
# Codex で通し視聴＋読み確認。usage: review_all.sh slug:theme ...
cd /e/rekishikaisetu-honnoji; export PYTHONIOENCODING=utf-8
for p in "$@"; do s=${p%%:*}; t=${p##*:}
  python scripts/codex_watch.py $s $t > out/codex/${s}_watch_run.txt 2>&1
  python scripts/codex_kana.py $s $t > out/codex/${s}_kana_run.txt 2>&1
  echo "$s $(cat out/codex/${s}_watch_run.txt | cut -c1-60) | $(cat out/codex/${s}_kana_run.txt | cut -c1-60)" >> out/codex/review_progress.txt
done
echo all > out/codex/review_done.txt
