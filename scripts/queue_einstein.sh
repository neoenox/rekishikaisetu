#!/bin/bash
cd /e/rekishikaisetu-honnoji
export PYTHONIOENCODING=utf-8
while [ ! -f out/codex/season_rebuilt.txt ]; do sleep 20; done
s=einstein
for st in build desc pack; do python scripts/vp.py $s $st > out/codex/${s}_re_$st.txt 2>&1; done
echo done > out/codex/einstein_rebuilt.txt
