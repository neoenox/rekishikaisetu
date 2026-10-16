"""Ask Codex (read-only) to review a video's script or finished package.  Replaces the earlier ChatGPT review step.
usage: python scripts/codex_review.py <theme_dir> script|video [slug]
  script: reads <theme_dir>/08_fact_check.md + 09_script_v1.md  -> <theme_dir>/12_codex_script_review.md
  video : reads script v2 + out/<slug>_description.md + review sheets (images) -> <theme_dir>/13_codex_video_review.md
The result is advice only: every finding must be verified against the original sources before it is applied (record in 10_review_log.md)."""
import subprocess,sys,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
COMMON="""あなたは、歴史・科学・暮らしの解説動画（YouTubeチャンネル「寄り道ラボ」、合成音声のナレーション＋図解）の査読者です。
**ファイルは変更せず、読むだけ**にしてください。結果は日本語で、重大度（高／中／低）の高い順に出してください。
チャンネルの型は「〜は本当か？ → よく言われる説明 → 実際の根拠 → 分かること／決められないこと」です。断定しすぎない、根拠より強く言わない、が方針です。
"""
SCRIPT="""対象ディレクトリ：{d}
読むファイル：
- {d}/08_fact_check.md（事実確認の記録。各主張の根拠と状態）
- {d}/09_script_v1.md（台本。番号つきの行がナレーション。〔Kn〕などは根拠の番号で、読み上げない）
- {d}/07_brief.md（企画メモ）

見てほしい点（優先順）：
1. **事実関係**：台本の記述が、08_fact_check.md の根拠と食い違っていないか。根拠より**強く断定している箇所**、根拠にない内容、年号・数値・人名・用語の誤り、計算の誤り（数字は検算してください）。
2. **誤解を招く表現**：視聴者が誤った印象を持ちうる箇所。反対の見方・例外を落としていないか。
3. **構成**：問い→説明→根拠→分かること／決められないこと、の流れ。冗長・飛躍・説明不足。
4. **音声の読み**：合成音声で誤読しやすい語（同音異義、数字・年号、固有名詞、略語）と、聞いて意味が取りにくい長文。読み仮名の指定が必要な語を挙げる。
5. **画面に出せるか**：自作の図・表・グラフで見せやすいか（図にできない箇所は、文字だけになる）。
6. **権利・ポリシー**：画像・データ・引用の扱い、YouTubeのポリシー上の懸念。

出力形式：指摘ごとに「重大度／該当箇所（引用）／問題／直し案」。問題がなければ「指摘なし」と書き、確認した範囲を示す。根拠が手元にない点は「未確認」と分けて書く（推測で断定しない）。
"""
VIDEO="""対象ディレクトリ：{d}　（動画の識別子：{slug}）
読むファイル：
- {d}/08_fact_check.md、{d}/09_script_v2.md（最終台本）
- out/{slug}_description.md（YouTube概要欄の下書き。チャプター・出典・クレジット・注意書き・投稿前チェック）
- data/{slug}_spec.json（画面の文言・図の定義）
- 添付画像：完成動画の各章の静止画（コンタクトシート）

見てほしい点（優先順）：
1. **画面の文言**：事実関係の誤り・根拠より強い断定、数字の不一致（ナレーションと画面）、誤字。
2. **画面の見やすさ**：添付画像で、文字のはみ出し・重なり・小さすぎる文字・情報過多がないか。
3. **概要欄**：チャプター、出典・クレジット（外部素材・生成画像・音声・音楽）、注意書き、YouTubeのポリシー（AIの使用の申告基準、合成音声）。
4. **台本との整合**：台本と画面・概要欄の食い違い。
5. 未確認の点は、そう書く（動画本体の音声・音量は確認できません）。

出力形式：指摘ごとに「重大度／該当箇所（引用）／問題／直し案」。問題がなければ「指摘なし」と書き、確認した範囲を示す。
"""
def main():
    d=sys.argv[1];kind=sys.argv[2];slug=sys.argv[3] if len(sys.argv)>3 else None
    rel=f'docs/themes/{d}';out=ROOT/rel/('12_codex_script_review.md' if kind=='script' else '13_codex_video_review.md')
    prompt=COMMON+(SCRIPT.format(d=rel) if kind=='script' else VIDEO.format(d=rel,slug=slug))
    cmd=['codex','exec','-s','read-only','--skip-git-repo-check','-C',str(ROOT),'-o',str(out)]
    if kind=='video':
        sheets=sorted((ROOT/'out'/f'{slug}_review').glob('sheet_*.png'))
        for s in sheets:cmd+=['-i',str(s)]
    cmd.append('-')
    log=ROOT/'out'/'codex'/f'{d}_{kind}.log';log.parent.mkdir(exist_ok=True,parents=True)
    with log.open('wb') as lf:r=subprocess.run(cmd,input=prompt.encode('utf8'),stdout=lf,stderr=subprocess.STDOUT,cwd=str(ROOT))
    print('exit',r.returncode,'->',out if out.exists() else 'NO OUTPUT (see '+str(log)+')')
if __name__=='__main__':main()
