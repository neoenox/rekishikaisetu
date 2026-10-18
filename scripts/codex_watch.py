"""Codex に「通し視聴」をしてもらう（動画を最初から最後まで、時刻つきの静止画・字幕・音声の測定値で確認）。
usage: python scripts/codex_watch.py <slug> [<theme_dir>]
  材料: out/<slug>_video.mp4 から 4秒おきの静止画（時刻入りのコンタクトシート）、字幕SRT、音声の測定値
  出力: out/<slug>_watch/（材料）、<theme_dir>/14_codex_watch.md（Codexの所見。theme_dir 省略時は out/<slug>_watch/codex_watch.md）
Codexは音を直接聞けない。音の確認は ffmpeg の測定値（ラウドネス・無音・ピーク）で代える。助言のみ。指摘は一次資料で裏取りしてから反映する。"""
import json, re, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
STEP = 4          # 秒
COLS, ROWS = 4, 4  # 1枚に16コマ（64秒分）
W, H = 480, 270


import os
VIDEO=os.environ.get('VIDEO');SRTP=os.environ.get('SRT');WIN=[float(x) for x in os.environ['WIN'].split(',')] if os.environ.get('WIN') else None;TAG=os.environ.get('TAG','')


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding='utf8', errors='replace')


def srt_cues(p):
    cues = []
    for blk in re.split(r'\n\s*\n', p.read_text(encoding='utf-8-sig').strip()):
        ln = blk.strip().splitlines()
        if len(ln) >= 3 and '-->' in ln[1]:
            a, b = [sum(float(x) * m for x, m in zip(t.replace(',', '.').split(':'), (3600, 60, 1))) for t in ln[1].split('-->')]
            cues.append((a, b, ''.join(ln[2:])))
    return cues


def frames(video, out):
    out.mkdir(parents=True, exist_ok=True)
    for f in out.glob('f_*.jpg'):
        f.unlink()
    a, b = sh(['ffprobe', '-v', 'error', '-select_streams', 'v', '-show_entries', 'stream=avg_frame_rate', '-of', 'csv=p=0', str(video)]).stdout.strip().split('/')
    n_step = round(float(a) / float(b) * STEP)  # fpsフィルタは時刻が約2秒ずれたので、フレーム番号で正確に選ぶ
    t0 = WIN[0] if WIN else 0.0
    ss = ['-ss', str(t0), '-t', str(WIN[1] - WIN[0])] if WIN else []
    sh(['ffmpeg', '-y'] + ss + ['-i', str(video), '-vf', f"select='not(mod(n,{n_step}))',scale={W}:{H}", '-fps_mode', 'vfr', '-q:v', '4', str(out / 'f_%04d.jpg')])
    fs = sorted(out.glob('f_*.jpg'))
    font = ImageFont.truetype('C:/Windows/Fonts/meiryo.ttc', 22)
    n = COLS * ROWS
    sheets = []
    for si in range(0, len(fs), n):
        sheet = Image.new('RGB', (COLS * W, ROWS * H), 'black')
        d = ImageDraw.Draw(sheet)
        for k, f in enumerate(fs[si:si + n]):
            x, y = (k % COLS) * W, (k // COLS) * H
            sheet.paste(Image.open(f), (x, y))
            t = int(t0) + (si + k) * STEP
            d.rectangle([x, y, x + 92, y + 28], fill='black')
            d.text((x + 4, y + 1), f'{t // 60}:{t % 60:02d}', fill='yellow', font=font)
        p = out / f'watch_{si // n + 1:02d}.png'
        sheet.save(p)
        sheets.append(p)
    for f in fs:
        f.unlink()
    return sheets


def audio_report(video, srt, out):
    L = []
    dur = float(sh(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(video)]).stdout.strip())
    L.append(f'動画の長さ: {dur:.1f}秒')
    ss = ['-ss', str(WIN[0]), '-t', str(WIN[1] - WIN[0])] if WIN else []
    r = sh(['ffmpeg', '-nostats'] + ss + ['-i', str(video), '-af', 'ebur128=peak=true', '-f', 'null', '-']).stderr
    m = r[r.rfind('Summary:'):]
    L.append('ラウドネス(EBU R128) 抜粋:\n' + '\n'.join(x for x in m.splitlines() if re.search(r'I:|LRA:|Peak:', x)))
    r = sh(['ffmpeg', '-nostats'] + ss + ['-i', str(video), '-af', 'silencedetect=noise=-45dB:d=1.2', '-f', 'null', '-']).stderr
    sil = re.findall(r'silence_start: ([\d.]+)|silence_end: ([\d.]+) \| silence_duration: ([\d.]+)', r)
    ss = [a for a, b, c in sil if a]
    es = [(b, c) for a, b, c in sil if b]
    L.append('1.2秒以上の無音(-45dB以下): ' + (', '.join(f'{float(s):.1f}s〜{float(e):.1f}s({float(d):.1f}s)' for s, (e, d) in zip(ss, es)) or 'なし'))
    cues = srt_cues(srt)
    if WIN:
        cues = [c for c in cues if WIN[0] <= c[0] < WIN[1]]
    L.append(f'字幕: {len(cues)}件、最後の字幕の終了 {cues[-1][1]:.1f}s')
    fast = [(a, len(t) / max(b - a, .1), t) for a, b, t in cues if len(t) / max(b - a, .1) > 9.5]
    L.append('読む速さが 9.5字/秒 を超える字幕: ' + ('; '.join(f'{a:.1f}s {v:.1f}字/秒「{t[:24]}」' for a, v, t in fast) or 'なし'))
    long_ = [(a, len(t), t) for a, b, t in cues if len(t) > 42]
    L.append('42字を超える字幕: ' + ('; '.join(f'{a:.1f}s {n}字' for a, n, t in long_) or 'なし'))
    gaps = [(cues[i][1], cues[i + 1][0] - cues[i][1]) for i in range(len(cues) - 1) if cues[i + 1][0] - cues[i][1] > 2.0]
    L.append('字幕の途切れ(2秒超): ' + ('; '.join(f'{s:.1f}s〜(+{g:.1f}s)' for s, g in gaps) or 'なし'))
    (out / 'audio_report.txt').write_text('\n\n'.join(L), encoding='utf8')
    return cues


PROMPT = """あなたは、解説動画（YouTubeチャンネル「寄り道ラボ」、合成音声のナレーション＋図解）を、公開前に**最初から最後まで通して視聴する**査読者です。
**ファイルは変更せず、読むだけ**にしてください。結果は日本語で、重大度（高／中／低）の高い順に出してください。

【材料】
- 添付画像 watch_01.png〜：動画を{step}秒おきに切り出した静止画。各コマの左上に、動画の時刻（分:秒）が入っています。左上から右へ、上から下の順に並んでいます。
- {srt}：字幕（ナレーションの読み上げと同じ文章。時刻つき）
- {audio}：音声の測定値（ラウドネス、無音区間、字幕の読む速さ）
- {script}
動画の音は聞けません。音は、測定値で判断してください（聞いて確かめられない点は「未確認」と書く）。

【見てほしい点】
1. **時刻ごとの画面とナレーションの対応**：字幕の時刻の画面が、読み上げの内容と合っているか（別の話題の図が出ている、図が出る前に話が進んでいる、など）。
2. **画面の不具合**：文字のはみ出し・欠け・重なり、小さすぎる文字、真っ黒・空白のコマ、同じ画面が長く続いて動きがない区間。
3. **ナレーションの正しさ**：事実関係、数字、年号、固有名詞。根拠より強い断定。画面の数字と字幕の数字の不一致。
4. **音声**：測定値から、音量不足・超過、不自然な無音、冒頭と末尾の余白の問題。
5. **字幕**：長すぎる・読む速さが速すぎる字幕、誤字、画面の文字との重複。
6. **公開してよいか**：上を総合して、「公開してよい／直せば公開してよい／公開不可」の3段階で判定し、直すべき点を優先順に挙げる。

出力形式：先頭に判定、その後、指摘ごとに「重大度／時刻／該当箇所（引用）／問題／直し案」。確認した範囲（何枚のシートを見たか）を最後に書く。問題がなければ「指摘なし」。
"""


def main():
    slug = sys.argv[1]
    theme = sys.argv[2] if len(sys.argv) > 2 else None
    video = Path(VIDEO) if VIDEO else ROOT / 'out' / f'{slug}_video.mp4'
    srt = Path(SRTP) if SRTP else ROOT / 'out' / f'{slug}_subtitles.srt'
    work = ROOT / 'out' / f'{slug}{TAG}_watch'
    work.mkdir(parents=True, exist_ok=True)
    sheets = frames(video, work)
    audio_report(video, srt, work)
    script = '（台本ファイルなし。字幕を台本として扱う）'
    if theme and (ROOT / 'docs' / 'themes' / theme / '09_script_v2.md').exists():
        script = f'docs/themes/{theme}/09_script_v2.md（最終台本）と docs/themes/{theme}/08_fact_check.md（事実確認の記録）'
    script += os.environ.get('EXTRA', '')
    prompt = PROMPT.format(step=STEP, srt=srt.relative_to(ROOT).as_posix(),
                           audio=(work / 'audio_report.txt').relative_to(ROOT).as_posix(), script=script)
    out = (ROOT / 'docs' / 'themes' / theme / f'14_codex_watch{TAG}.md') if theme else work / 'codex_watch.md'
    cmd = ['codex', 'exec', '-s', 'read-only', '--skip-git-repo-check', '-C', str(ROOT), '-o', str(out)]
    for s in sheets:
        cmd += ['-i', str(s)]
    cmd.append('-')
    log = ROOT / 'out' / 'codex' / f'{slug}{TAG}_watch.log'
    log.parent.mkdir(exist_ok=True, parents=True)
    with log.open('wb') as lf:
        r = subprocess.run(cmd, input=prompt.encode('utf8'), stdout=lf, stderr=subprocess.STDOUT, cwd=str(ROOT))
    print(slug, 'sheets', len(sheets), 'exit', r.returncode, '->', out if out.exists() else 'NO OUTPUT (see ' + str(log) + ')')


if __name__ == '__main__':
    main()
