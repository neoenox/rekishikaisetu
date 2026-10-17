"""Codex に、合成音声の「読み」を確認してもらう。
usage: python scripts/codex_kana.py <slug> [<theme_dir>]
  out/<slug>_audio_report.json の各文（読み辞書を適用した spoken）を VOICEVOX の audio_query にかけ、
  VOICEVOX が決めたアクセント付きカナを out/<slug>_kana_check.txt に書く。それを Codex（読み取り専用）に渡し、
  誤読（同音異義語、数字・単位、固有名詞、略語、区切り）を探してもらう。
  出力: <theme_dir>/16_codex_kana.md（theme_dir 省略時は out/<slug>_kana_review.md）
Codexは音を聞けない。見つけた誤読は、読み辞書（data/<slug>_pronunciations.json）に足して作り直す前に、
vp.py <slug> kana で実際の読みを確認する。VOICEVOXが 127.0.0.1:50021 で動いていること。"""
import json, subprocess, sys
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
BASE = 'http://127.0.0.1:50021'

PROMPT = """あなたは、解説動画（YouTubeチャンネル「寄り道ラボ」、合成音声VOICEVOX四国めたん）の、読みの査読者です。
ファイルは変更せず、読むだけにしてください。結果は日本語で、重大度（高／中／低）順に出してください。動画の音は聞けません。

材料：{kana}（各文と、その文の読み。「読み」は、VOICEVOXが決めたアクセント付きカナ。' はアクセント核、/ はアクセント句の区切り、_ は無声化。「トケエ」「ドオガ」のような長音の表記は発音を表す表記で、それだけでは誤読ではありません）
読み辞書：{dic}（キー→カタカナの読み。すでに指定済みの語）

探してほしいもの：
1. 明確な誤読：同音異義語の取り違え（例：「二分」を「にぶん」と読む、「人気」「大家」「後」「辛い」など）、数字・単位・年号の読み（「一刻」「四分の一」「十時間」「二〇二一年」など）、固有名詞・人名・書名・地名、略語・アルファベット（NOAA、GDP、SNAなど）、漢語の読み（「原論文」「容器」など）。
2. 区切りの不自然さ：意味の切れ目と違う位置でアクセント句が切れている、長すぎる一息。
3. 聞き取りにくい長文：一文が長く、意味が取りにくい箇所（読み上げではなく、台本の側の指摘）。

出力形式：先頭に、「明確な誤読の数」と「公開前に直すべきか」の判定。その後、指摘ごとに「重大度／該当文（引用）／問題（読みの引用）／直し案（読み辞書に足す『語→カタカナ』）」。
推測で誤読と断定せず、疑いは「疑い」と書く。誤読が見つからなければ「指摘なし」と書き、確認した文の数を示す。
"""


def main():
    slug = sys.argv[1]
    theme = sys.argv[2] if len(sys.argv) > 2 else None
    rep = json.loads((ROOT / 'out' / f'{slug}_audio_report.json').read_text(encoding='utf8'))['segments']
    sp = requests.get(BASE + '/speakers', timeout=60).json()
    style = next(x['id'] for s in sp if s['name'] == '四国めたん' for x in s['styles'] if x['name'] == 'ノーマル')
    lines = []
    for s in rep:
        q = requests.post(BASE + '/audio_query', params={'text': s['spoken'], 'speaker': style}, timeout=120).json()
        lines.append(f"{s['text']}\n    {q['kana']}")
    kana = ROOT / 'out' / f'{slug}_kana_check.txt'
    kana.write_text('\n'.join(lines), encoding='utf8')
    dic = ROOT / 'data' / f'{slug}_pronunciations.json'
    out = (ROOT / 'docs' / 'themes' / theme / '16_codex_kana.md') if theme else ROOT / 'out' / f'{slug}_kana_review.md'
    prompt = PROMPT.format(kana=kana.relative_to(ROOT).as_posix(), dic=dic.relative_to(ROOT).as_posix() if dic.exists() else '（なし）')
    cmd = ['codex', 'exec', '-s', 'read-only', '--skip-git-repo-check', '-C', str(ROOT), '-o', str(out), '-']
    log = ROOT / 'out' / 'codex' / f'{slug}_kana.log'
    log.parent.mkdir(exist_ok=True, parents=True)
    with log.open('wb') as lf:
        r = subprocess.run(cmd, input=prompt.encode('utf8'), stdout=lf, stderr=subprocess.STDOUT, cwd=str(ROOT))
    print(slug, len(rep), 'sentences exit', r.returncode, '->', out if out.exists() else 'NO OUTPUT (see ' + str(log) + ')')


if __name__ == '__main__':
    main()
