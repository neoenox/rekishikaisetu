#!/bin/bash
# wait for the first batch (compass/season/einstein) to finish, then: vein finish, then rebuild calendar & compass after reading fixes
cd /e/rekishikaisetu-honnoji
export PYTHONIOENCODING=utf-8
while [ ! -f out/codex/einstein_finished.txt ]; do sleep 20; done
bash scripts/finish_video.sh vein 20261018_vein
for a in "calendar 20261018_calendar" "compass 20261018_compass"; do
  set -- $a
  for st in audio bgm ends build desc pack; do python scripts/vp.py $1 $st > out/codex/$1_re_$st.txt 2>&1; done
  python scripts/codex_kana.py $1 $2 > out/codex/$1_kana_re_run.txt 2>&1 || true
  echo done > out/codex/$1_rebuilt.txt
done
echo done > out/codex/queue_rest_done.txt
