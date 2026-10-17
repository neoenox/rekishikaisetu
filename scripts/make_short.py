"""縦型Short（1080x1920）を作る。排水の渦の長尺から、約45秒に切り出した試作。
usage: python scripts/make_short.py drain      # 音声→画面→mp4 -> out/short_drain.mp4, _subtitles.srt, _description.md
台本・画面は SHORTS['drain'] に書く。ナレーションの数字・限定は、長尺の台本（docs/themes/20261017_drain/09_script_v2.md）と一致させる。
VOICEVOX(四国めたん)が 127.0.0.1:50021 で動いていること。"""
import json, math, re, subprocess, sys, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FD = 'C:/Windows/Fonts/'
BASE = 'http://127.0.0.1:50021'
SPEED = 0.95
W, H, FPS = 1080, 1920, 30
NAVY = (9, 22, 34); GOLD = (239, 201, 118); WHITE = (245, 243, 232); DIM = (190, 205, 208)
ORG = (255, 150, 90); BLUE = (120, 190, 255); EDGE = (176, 153, 100)
COL = dict(gold=GOLD, white=WHITE, dim=DIM, org=ORG, blue=BLUE)
_FC = {}


def font(size, serif=False):
    k = (size, serif)
    if k not in _FC:
        f = ImageFont.truetype(FD + ('NotoSerifJP-VF.ttf' if serif else 'NotoSansJP-VF.ttf'), size)
        f.set_variation_by_axes([800 if serif else 600])
        _FC[k] = f
    return _FC[k]


def wrap(d, text, f, maxw):
    lines, cur = [], ''
    for ch in text:
        if d.textlength(cur + ch, font=f) > maxw and cur and ch not in '、。」）！？':
            lines.append(cur); cur = ch
        else:
            cur += ch
    return lines + ([cur] if cur else [])


def swirl(d, c, r, ccw, col, lw=10):
    """上から見た渦の概念図（外から中心へ向かう渦巻き。矢じりで回る向きを示す）。"""
    for arm in range(3):
        pts = []
        for i in range(60):
            t = i / 59
            ang = arm * 2 * math.pi / 3 + (1 if ccw else -1) * (t * 3.2 * math.pi)
            rr = r * (1 - 0.88 * t)
            pts.append((c[0] + rr * math.cos(ang), c[1] - rr * math.sin(ang)))
        d.line(pts, fill=col, width=lw, joint='curve')
        (x0, y0), (x1, y1) = pts[-8], pts[-4]
        a = math.atan2(y1 - y0, x1 - x0)
        for s in (-0.5, 0.5):
            d.line([(x1, y1), (x1 - 34 * math.cos(a + s), y1 - 34 * math.sin(a + s))], fill=col, width=lw)


SHORTS = {
    'drain': dict(
        title='排水の渦は、逆回転する？', pack='short_drain', long_id='qjXxDENAZZE',
        pron='data/drain_pronunciations.json',
        # 台本（1文=1場面）。画面は kind と引数。
        scenes=[
            dict(text='「南半球では、排水の渦は逆回転する」。本当でしょうか。ふつうの洗面台では、半球だけで向きは決まりません。', kind='two'),
            dict(text='台風やハリケーンは、地球の自転による力で、回る向きが半球ごとに決まります。', kind='storm'),
            dict(text='でも、洗面台の排水の渦の向きには、コリオリ力は小さすぎると、NOAAは説明しています。', kind='small'),
            dict(text='他の力を除いて、コリオリ力だけで向きが変わる計算では、北緯三十五度で、一周に約二十一時間かかります。', kind='calc1'),
            dict(text='排水にかかる時間を、仮に二分とすると、約六百三十分の一です。', kind='calc2'),
            dict(text='実際の渦の回転時間ではなく、時間の規模の違いを見るための計算です。', kind='note'),
            dict(text='ふつうの洗面台では、渦の向きは、容器の形と、水の初めの動きで決まります。', kind='cause'),
            dict(text='詳しくは、長い動画で、確かめています。', kind='cta'),
        ]),
}


def panel(d, box, title, text, size=52, col=WHITE, hi=False, alpha=255):
    x0, y0, x1, y1 = box
    lns = [ln for para in text.split(chr(10)) for ln in wrap(d, para, font(size), x1 - x0 - 60)]
    need = y0 + 22 + (56 if title else 0) + int(size * 1.4) * len(lns) + 14
    y1 = max(y1, need)
    d.rounded_rectangle((x0, y0, x1, y1), 18, fill=(7, 24, 36, int(235 * alpha / 255)), outline=GOLD + (alpha,) if hi else EDGE + (alpha,), width=3)
    y = y0 + 22
    if title:
        d.text((x0 + 30, y), title, font=font(34, True), fill=GOLD + (alpha,)); y += 56
    for ln in lns:
        d.text((x0 + 30, y), ln, font=font(size), fill=col + (alpha,)); y += int(size * 1.4)


def draw_visual(d, kind, a, k):
    """a: 0..1 の出現度。k: 場面内の経過秒。"""
    A = int(255 * a)
    if kind == 'two':
        swirl(d, (290, 560), 190, True, BLUE + (A,)); swirl(d, (790, 560), 190, False, ORG + (A,))
        d.text((290, 800), '北半球', font=font(48), fill=BLUE + (A,), anchor='mm'); d.text((790, 800), '南半球', font=font(48), fill=ORG + (A,), anchor='mm')
        d.text((290, 860), '反時計回り？', font=font(40), fill=WHITE + (A,), anchor='mm'); d.text((790, 860), '時計回り？', font=font(40), fill=WHITE + (A,), anchor='mm')
        d.text((540, 1010), '原因は、地球の自転？', font=font(60), fill=GOLD + (A,), anchor='mm')
        d.text((540, 1090), '（上から見た概念図）', font=font(40), fill=DIM + (A,), anchor='mm')
    elif kind == 'storm':
        swirl(d, (290, 600), 200, True, BLUE + (A,), 12); swirl(d, (790, 600), 200, False, ORG + (A,), 12)
        d.text((290, 860), '北半球：反時計回り', font=font(40), fill=BLUE + (A,), anchor='mm'); d.text((790, 860), '南半球：時計回り', font=font(40), fill=ORG + (A,), anchor='mm')
        panel(d, (60, 960, 1020, 1090), '熱帯低気圧（NOAA）', '原因：地球の自転による、見かけの力（コリオリ力）', 38, alpha=A)
    elif kind == 'small':
        swirl(d, (540, 520), 150, True, BLUE + (A,), 9)
        panel(d, (60, 760, 1020, 1000), 'NOAA', 'コリオリ力は、排水の渦の向きに影響するには、小さすぎる', 54, hi=True, alpha=A)
        panel(d, (60, 1020, 1020, 1140), None, '洗面台・浴槽の渦の話', 44, col=GOLD, alpha=A)
    elif kind == 'calc1':
        panel(d, (60, 340, 1020, 560), '理想化した計算例（自作・北緯35度）', '水平の圧力差や摩擦などを除き、コリオリ力だけで向きが変わると仮定', 46, alpha=A)
        d.text((540, 760), '向きが1周する時間', font=font(54), fill=WHITE + (A,), anchor='mm')
        d.text((540, 900), '約21時間', font=font(130, True), fill=BLUE + (A,), anchor='mm')
    elif kind == 'calc2':
        d.text((540, 430), '向きが1周する時間', font=font(40), fill=DIM + (A,), anchor='mm')
        d.rounded_rectangle((90, 470, 990, 540), 12, fill=BLUE + (A,))
        d.text((540, 600), '約21時間（約1,250分）', font=font(44), fill=BLUE + (A,), anchor='mm')
        d.text((540, 700), '排水にかかる時間（仮に）', font=font(40), fill=DIM + (A,), anchor='mm')
        d.rounded_rectangle((90, 740, 90 + max(14, int(900 * 2 / 1252)), 810), 4, fill=ORG + (A,))
        d.text((540, 870), '約21時間に対して、2分', font=font(44), fill=ORG + (A,), anchor='mm')
        d.text((540, 1040), '約630分の1', font=font(120, True), fill=GOLD + (A,), anchor='mm')
    elif kind == 'note':
        panel(d, (60, 500, 1020, 800), '注意', '実際の渦の回転時間ではない。時間の規模の違いを見るための、理想化した計算', 58, hi=True, alpha=A)
        d.text((540, 940), '自作の計算例', font=font(36), fill=DIM + (A,), anchor='mm')
    elif kind == 'cause':
        panel(d, (60, 420, 1020, 640), 'NOAA', '排水の渦の向きを決めるのは', 48, alpha=A)
        panel(d, (60, 680, 520, 880), None, '容器の形', 62, col=GOLD, hi=True, alpha=A)
        panel(d, (560, 680, 1020, 880), None, '水の初めの動き', 50, col=GOLD, hi=True, alpha=A)
        d.text((540, 980), '同じ半球でも、向きは両方見られる', font=font(38), fill=WHITE + (A,), anchor='mm')
    elif kind == 'cta':
        panel(d, (60, 440, 1020, 780), '長い動画', '南半球では、排水の渦は逆回転する？\nNOAAと物理学の解説で確かめる', 50, hi=True, alpha=A)
        d.text((540, 900), '寄り道ラボ', font=font(80, True), fill=GOLD + (A,), anchor='mm')
        d.text((540, 990), 'ふと気になったことを、資料で調べる', font=font(36), fill=DIM + (A,), anchor='mm')


def synth(spec, work):
    import requests
    sp = requests.get(BASE + '/speakers', timeout=60).json()
    style = next(x['id'] for s in sp if s['name'] == '四国めたん' for x in s['styles'] if x['name'] == 'ノーマル')
    dic = json.loads((ROOT / spec['pron']).read_text(encoding='utf8'))
    segs, pcms, rate, t = [], [], 24000, 0.25
    for i, sc in enumerate(spec['scenes']):
        spoken = sc['text']
        for kk, v in sorted(dic.items(), key=lambda z: -len(z[0])):
            spoken = spoken.replace(kk, v)
        q = requests.post(BASE + '/audio_query', params={'text': spoken, 'speaker': style}, timeout=120).json()
        q.update(speedScale=SPEED, intonationScale=1.08, prePhonemeLength=.1, postPhonemeLength=.3, outputSamplingRate=24000)
        r = requests.post(BASE + '/synthesis', params={'speaker': style}, json=q, timeout=180); r.raise_for_status()
        p = work / f'n_{i:02}.wav'; p.write_bytes(r.content)
        with wave.open(str(p)) as w:
            pcm = np.frombuffer(w.readframes(w.getnframes()), np.int16); rate = w.getframerate()
        dur = len(pcm) / rate
        segs.append(dict(i=i, text=sc['text'], kind=sc['kind'], start=t, end=t + dur, kana=q['kana']))
        pcms.append(pcm); t += dur + 0.35
        pcms.append(np.zeros(int(0.35 * rate), np.int16))
    total = t + 0.6
    full = np.concatenate([np.zeros(int(0.25 * rate), np.int16)] + pcms + [np.zeros(int(0.6 * rate), np.int16)])
    with wave.open(str(work / 'narration.wav'), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(full.tobytes())
    return segs, total


def display(t):
    sys.path.insert(0, str(ROOT / 'scripts'))
    from hn_text import display as dsp
    return dsp(t)


def chunks(text, maxc=15, lines=2):
    """字幕を、句読点で区切って、1画面 maxc字×lines行 に収まる塊に分ける。"""
    parts = [p for p in re.split(r'(?<=[、。])', text) if p]
    out, cur = [], ''
    for p in parts:
        if len(cur) + len(p) <= maxc * lines:
            cur += p
        else:
            if cur: out.append(cur)
            cur = p
    if cur: out.append(cur)
    return out


def render(spec, segs, total, work, out_mp4):
    n = round(total * FPS)
    cache = {}
    cks = []
    for s in segs:
        cs = chunks(display(s['text']))
        ws = [len(c) for c in cs]; tot = sum(ws); t0 = s['start']; dur = s['end'] - s['start']
        for c, wgt in zip(cs, ws):
            cks.append((t0, t0 + dur * wgt / tot, c, s['i'])); t0 += dur * wgt / tot
    srt = []
    st = lambda t: (lambda ms: f'{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}')(round(t * 1000))
    for i, (a, b, c, _) in enumerate(cks):
        srt.append(f'{i + 1}\n{st(a)} --> {st(b)}\n{c}')
    (ROOT / 'out' / 'short_drain_subtitles.srt').write_text('\n\n'.join(srt) + '\n', encoding='utf8')
    proc = subprocess.Popen(['ffmpeg', '-y', '-v', 'warning', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', 'pipe:0',
                             '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', str(out_mp4)], stdin=subprocess.PIPE)
    for fi in range(n):
        t = fi / FPS
        seg = next((s for s in segs if s['start'] - 0.2 <= t < s['end'] + 0.35), segs[-1] if t >= segs[-1]['end'] else segs[0])
        ck = next((c for c in cks if c[0] <= t < c[1]), None)
        k = t - (seg['start'] - 0.2)
        a = min(1.0, max(0.0, k / 0.35)); aq = round(a * 6) / 6
        key = (seg['i'], ck[2] if ck else '', aq if aq < 1 else 1)
        if key not in cache:
            im = Image.new('RGBA', (W, H), NAVY + (255,)); d = ImageDraw.Draw(im, 'RGBA')
            # 見出し（上部。Shortsの上のUIを避けて少し下げる）
            d.text((540, 200), spec['title'], font=font(58, True), fill=WHITE + (255,), anchor='mm')
            d.line([(120, 262), (960, 262)], fill=GOLD + (255,), width=4)
            draw_visual(d, seg['kind'], aq, k)
            if ck:
                d.rounded_rectangle((50, 1290, 1030, 1540), 16, fill=(7, 24, 36, 235))
                lns = wrap(d, ck[2], font(60), 940)
                y = 1290 + (250 - len(lns) * 84) // 2
                for ln in lns:
                    d.text((540, y + 42), ln, font=font(60), fill=(255, 252, 239, 255), anchor='mm'); y += 84
            cache[key] = im.convert('RGB').tobytes()
            if len(cache) > 400: cache.pop(next(iter(cache)))
        proc.stdin.write(cache[key])
    proc.stdin.close(); proc.wait()


def mix(spec, work, total, out_mp4, final):
    bgm = ROOT / 'assets' / 'bgm_maou' / 'maou_bgm_piano12.mp3'
    fc = ('[1:a]aresample=48000,volume=0.30,afade=t=in:d=1,afade=t=out:st=%.2f:d=1.5[b];[2:a]aresample=48000,asplit=2[n1][n2];'
          '[b][n1]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[bd];[bd][n2]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=7[a]') % (total - 1.5)
    subprocess.run(['ffmpeg', '-y', '-v', 'warning', '-i', str(out_mp4), '-stream_loop', '-1', '-i', str(bgm), '-i', str(work / 'narration.wav'),
                    '-filter_complex', fc, '-map', '0:v', '-map', '[a]', '-t', f'{total:.2f}', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', str(final)], check=True)


def description(spec):
    s = spec
    return f"""{s['title']}　（約55秒）

「南半球では、排水の渦が逆回転する」。本当でしょうか。NOAAの解説と、理想化した計算例で、地球の自転の影響の大きさを確かめます。

▶ 詳しい根拠と実験の話は、長い動画で：https://youtu.be/{s['long_id']}

■ 動画で確かめたこと
・熱帯低気圧（台風・ハリケーン）の回る向きは、コリオリ力で半球ごとに決まります（NOAA）。
・ふつうの洗面台や浴槽の排水の渦の向きには、コリオリ力は影響するには小さすぎ、容器の形と水の初めの動きで決まります（NOAA）。
・「約21時間」「約630分の1」は、水平の圧力差や摩擦などを除き、コリオリ力だけで向きが変わると仮定した、北緯35度での理想化した自作の計算例です。実際の渦の回転を表す数字ではありません。

■ 参考資料
・NOAA/AOML 熱帯低気圧FAQ D3：https://www.aoml.noaa.gov/hrd/tcfaq/D3.html
・Physics Frequently Asked Questions "Which way does the water drain?"：https://math.ucr.edu/home/baez/physics/General/bathtub.html

■ 出典・クレジット
・図・計算：自作（渦の図は上から見た概念図）
・音声：VOICEVOX:四国めたん
・音楽：魔王魂（https://maou.audio/）ピアノ12（作曲：森田交一。音量調整を行っています）

■ このチャンネルについて
寄り道ラボは、ふと気になったことを、資料やデータで調べる解説チャンネルです。

#Shorts #雑学 #科学
"""


def main():
    name = sys.argv[1]; spec = SHORTS[name]
    work = ROOT / 'cache' / f'short_{name}'; work.mkdir(parents=True, exist_ok=True)
    segs, total = synth(spec, work)
    (ROOT / 'out' / f'short_{name}_kana.txt').write_text('\n'.join(f"{s['text']}\n    {s['kana']}" for s in segs), encoding='utf8')
    print('narration', round(total, 1), 's')
    raw = work / 'raw.mp4'
    render(spec, segs, total, work, raw)
    mix(spec, work, total, raw, ROOT / 'out' / f'short_{name}.mp4')
    (ROOT / 'out' / f'short_{name}_description.md').write_text(description(spec), encoding='utf8')
    print('done -> out/short_%s.mp4' % name)


if __name__ == '__main__':
    main()
