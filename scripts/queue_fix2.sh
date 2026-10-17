#!/bin/bash
cd /e/rekishikaisetu-honnoji
export PYTHONIOENCODING=utf-8
for a in "compass 20261018_compass" "einstein 20261018_einstein"; do
  set -- $a
  for st in audio bgm ends build desc pack; do python scripts/vp.py $1 $st > out/codex/$1_re2_$st.txt 2>&1; done
  python scripts/codex_kana.py $1 $2 > out/codex/$1_kana_re2_run.txt 2>&1 || true
done
echo done > out/codex/queue_fix2_done.txt
