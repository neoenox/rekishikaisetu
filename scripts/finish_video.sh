#!/bin/bash
# usage: scripts/finish_video.sh <slug> <theme_dir> [from]  : build -> desc -> thumb -> pack -> Codex watch + kana
set -e
cd /e/rekishikaisetu-honnoji
export PYTHONIOENCODING=utf-8
s=$1; t=$2; from=${3:-build}
if [ "$from" = "build" ]; then python scripts/vp.py $s build > out/codex/${s}_build.txt 2>&1; fi
python scripts/vp.py $s desc >> out/codex/${s}_build.txt 2>&1
python scripts/vp.py $s thumb >> out/codex/${s}_build.txt 2>&1
python scripts/vp.py $s pack >> out/codex/${s}_build.txt 2>&1
python scripts/codex_watch.py $s $t > out/codex/${s}_watch_run.txt 2>&1 || true
python scripts/codex_kana.py $s $t > out/codex/${s}_kana_run.txt 2>&1 || true
echo done > out/codex/${s}_finished.txt
