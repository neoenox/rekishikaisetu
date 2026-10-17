#!/bin/bash
cd /e/rekishikaisetu-honnoji
export PYTHONIOENCODING=utf-8
while [ ! -f out/codex/queue_rest_done.txt ]; do sleep 20; done
s=season
for st in audio bgm ends build desc pack; do python scripts/vp.py $s $st > out/codex/${s}_re_$st.txt 2>&1; done
python scripts/codex_kana.py $s 20261018_season > out/codex/${s}_kana_re_run.txt 2>&1 || true
echo done > out/codex/season_rebuilt.txt
