"""Codex の画像生成で、場面のイラストを作る（文字は入れさせない）。
usage: python scripts/codex_art.py <slug> <name> "<場面の説明>"   -> assets/<slug>/art_<name>.png
画風は STYLE で固定（1本の動画の中で、そろえる）。生成画像は『イメージ』であり、史実・実在の再現ではない（概要欄に明記）。"""
import subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
STYLE = "落ち着いた紺・金・生成り色を基調にした、やや様式化したデジタルイラスト（絵本・図鑑の挿絵のような柔らかい質感）。写真のようにリアルにはしない。"
slug, name, scene = sys.argv[1], sys.argv[2], sys.argv[3]
out = ROOT / 'assets' / slug / f'art_{name}.png'
out.parent.mkdir(parents=True, exist_ok=True)
prompt = f"""画像生成ツールで、解説動画の場面に使う背景イラストを1枚作り、{out.as_posix()} にPNGで保存してください（ファイルは、その1枚だけを作る）。
条件：横長16:9。画像の中に、文字・数字・ロゴ・透かし・看板の文字を一切入れない。実在の人物の顔や、実在の作品・商標に似せない。人物を描く場合は、後ろ姿かシルエットにする。
画風：{STYLE}
画面の構図：見せたい対象を画面の中央〜右に大きく置き、左上は、文字を重ねられるよう、比較的すっきり（暗めで細かい模様を避ける）にする。
場面：{scene}
保存したら、保存したパスだけを答えてください。"""
r = subprocess.run(['codex', 'exec', '-s', 'workspace-write', '--skip-git-repo-check', '-C', str(ROOT), '-'], input=prompt.encode('utf8'), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
print(slug, name, 'exit', r.returncode, 'saved' if out.exists() else 'NOT SAVED', out.stat().st_size if out.exists() else '')
