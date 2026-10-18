#!/bin/bash
# opencode（無料のDeepSeek）で通し視聴レビュー＋読み確認。usage: oc_review_all.sh slug:theme ...
cd /e/rekishikaisetu-honnoji; export PYTHONIOENCODING=utf-8 REVIEWER=opencode MODEL=opencode/deepseek-v4.1-flash-free TAG=_oc
for p in "$@"; do s=${p%%:*}; t=${p##*:}
  python scripts/codex_watch.py $s $t > out/codex/${s}_oc_watch_run.txt 2>&1
  python scripts/codex_kana.py $s $t > out/codex/${s}_oc_kana_run.txt 2>&1
  echo "$s done $(date +%H:%M)" >> out/codex/oc_review_progress.txt
done
echo all > out/codex/oc_review_done.txt
