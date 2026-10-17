"""Codex の画像生成で、サムネイルの背景イラストを作る（文字は入れさせない）。
usage: python scripts/codex_thumb.py <slug> "<場面の説明>"   -> assets/<slug>/thumb_art.png
生成画像は『イメージ』であり、史実・実在の再現ではない（概要欄に明記する）。"""
import subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
slug, scene = sys.argv[1], sys.argv[2]
out = ROOT / 'assets' / slug / 'thumb_art.png'
out.parent.mkdir(parents=True, exist_ok=True)
prompt = f"""画像生成ツールで、YouTube動画のサムネイル用の背景イラストを1枚作り、{out.as_posix()} にPNGで保存してください（ファイルは、その1枚だけを作る）。
条件：横長16:9（1920x1080に近い比率）。画像の中に、文字・数字・ロゴ・透かしを一切入れない。実在の人物の顔や、実在の作品・商標に似せない。
画面の左半分は、文字を重ねるため、比較的すっきり（暗めで、細かい模様を避ける）にし、見せ場は右半分に置く。落ち着いた紺・金を基調とした、解説動画向けの、やや様式化したイラスト。
場面：{scene}
保存したら、保存したパスだけを答えてください。"""
r = subprocess.run(['codex', 'exec', '-s', 'workspace-write', '--skip-git-repo-check', '-C', str(ROOT), '-'], input=prompt.encode('utf8'),
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
print(slug, 'exit', r.returncode, 'saved' if out.exists() else 'NOT SAVED', out.stat().st_size if out.exists() else '')
