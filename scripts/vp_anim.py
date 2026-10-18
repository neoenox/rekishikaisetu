"""自作のアニメーション部品（vp.py の spec から `dict(t='anim', name='...', box=[x0,y0,x1,y1], at=N, ...)` で呼ぶ）。
外部画像は使わない。すべて Pillow で描く（2倍で描いて縮小＝なめらか）。cx.t（場面内の秒）と cx.st[i]（文 i の開始秒）で動かす。
静脈の動画（vein）で初めて使った。図は定性的な模式図で、数値・縮尺は示さない。"""
import math
from PIL import Image, ImageDraw

F = FB = None
S = 2
BRIGHT = (224, 48, 58); DARK = (122, 20, 40); SKIN = (238, 196, 165); DERMIS = (226, 160, 140); FAT = (246, 226, 150)
VEINBLUE = (92, 140, 220); WHITE = (245, 243, 232); GOLD = (239, 201, 118); DIM = (190, 205, 208); BG = (7, 24, 36)


def bind(g):
    global F, FB
    F, FB = g['F'], g['FB']


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def ease(x):
    x = min(1, max(0, x))
    return x * x * (3 - 2 * x)


def vs(box, Z):
    """仮想キャンバスの大きさ（Z倍に拡大して、boxに貼る）"""
    return (box[2] - box[0]) / Z, (box[3] - box[1]) / Z


def layer(box, Z=1.0):
    w, h = vs(box, Z)
    L = Image.new('RGBA', (int(w * S), int(h * S)), (0, 0, 0, 0))
    return L, ImageDraw.Draw(L)


def commit(im, L, box, a):
    w, h = box[2] - box[0], box[3] - box[1]
    if a < 1:
        r, g, b, al = L.split()
        L = Image.merge('RGBA', (r, g, b, al.point(lambda v: int(v * a))))
    im.alpha_composite(L.resize((w, h), Image.LANCZOS), (box[0], box[1]))


def T(cx, i):
    """文 i が始まってからの秒（まだなら負）"""
    return cx.t - cx.st[i] if (i is not None and i < len(cx.st) and cx.on(i)) else -1.0


def text(d, xy, s, size, col=WHITE, anchor='la', serif=False, alpha=255):
    f = (FB if serif else F)[size * S]
    d.text((xy[0] * S, xy[1] * S), s, font=f, fill=tuple(col[:3]) + (alpha,), anchor=anchor)


def circle(d, c, r, fill=None, outline=None, w=0):
    d.ellipse(((c[0] - r) * S, (c[1] - r) * S, (c[0] + r) * S, (c[1] + r) * S), fill=fill, outline=outline, width=int(w * S))


def poly(d, pts, col, w):
    d.line([(x * S, y * S) for x, y in pts], fill=col, width=int(w * S), joint='curve')


def arrow_head(d, p, q, col, size=16):
    a = math.atan2(q[1] - p[1], q[0] - p[0])
    pts = [(q[0], q[1]), (q[0] - size * math.cos(a - .45), q[1] - size * math.sin(a - .45)), (q[0] - size * math.cos(a + .45), q[1] - size * math.sin(a + .45))]
    d.polygon([(x * S, y * S) for x, y in pts], fill=col)


def path_len(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def path_at(pts, s):
    s = s % path_len(pts)
    for i in range(len(pts) - 1):
        l = math.dist(pts[i], pts[i + 1])
        if s <= l:
            f = s / l if l else 0
            return (pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f)
        s -= l
    return pts[-1]


def moving_dots(d, pts, col, t, n=5, r=7, speed=140):
    L = path_len(pts)
    for k in range(n):
        p = path_at(pts, t * speed + k * L / n)
        circle(d, p, r, fill=col)


# ------------------------------------------------------------------ 前腕（手首の青っぽい筋）
def forearm(im, d0, cx, it, a):
    Z = 1.5; box = it['box']; L, d = layer(box, Z); W, H = vs(box, Z)
    t = max(0, T(cx, it.get('lens_at', 99)))
    if not it.get('lens_only'):
        # 前腕（左から右へ、手首で細くなる）
        pts = [(60, 150), (560, 120), (820, 150), (820, 330), (560, 360), (60, 330)]
        d.polygon([(x * S, y * S) for x, y in pts], fill=SKIN + (255,))
        d.rounded_rectangle((760 * S, 150 * S, 900 * S, 330 * S), 40 * S, fill=SKIN + (255,))
        for sx, sy in ((520, 230), (610, 250), (700, 215)):
            pass
        # 青っぽい筋（皮膚の下の血管の見え方）
        for pts_ in ([(120, 215), (320, 205), (520, 235), (760, 225)], [(520, 235), (610, 262), (700, 292), (800, 296)], [(330, 207), (400, 180), (470, 172)]):
            poly(d, pts_, (120, 150, 200, 150), 14)
            poly(d, pts_, (96, 130, 190, 200), 6)
        text(d, (60, 36), '手首の内側などに見える、青っぽい筋', 34, DIM)
    # 拡大鏡（中身は？）
    if cx.on(it.get('lens_at', 99)):
        k = ease(t / 0.8)
        cxy = (940, 180); R = 135 * k
        circle(d, cxy, R + 10, fill=(14, 36, 52, 255), outline=GOLD + (255,), w=6)
        poly(d, [(cxy[0] - R * .7, cxy[1] + R * .72), (cxy[0] - R * .7 - 90, cxy[1] + R * .72 + 90)], GOLD + (255,), 12)
        if k > .6:
            text(d, cxy, '？', 150, GOLD, 'mm', serif=True)
            lab = '中を流れる血は、何色？'
            d.rounded_rectangle(((cxy[0] - R - 40 - 420) * S, (cxy[1] - 30) * S, (cxy[0] - R - 24) * S, (cxy[1] + 30) * S), 14 * S, fill=(8, 20, 32, 235))
            text(d, (cxy[0] - R - 40, cxy[1]), lab, 34, WHITE, 'rm')
    commit(im, L, box, a)


# ------------------------------------------------------------------ 赤血球・ヘモグロビン・酸素
def cell(d, c, R, col, fe=True, o2=0.0, label=None):
    circle(d, c, R, fill=col + (255,))
    circle(d, c, R * .56, fill=lerp(col, (0, 0, 0), .25) + (255,))
    circle(d, (c[0] - R * .35, c[1] - R * .45), R * .13, fill=lerp(col, (255, 255, 255), .35) + (200,))
    if fe:
        for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            p = (c[0] + dx * R * .22, c[1] + dy * R * .22)
            circle(d, p, R * .1, fill=(190, 195, 205, 255), outline=(235, 238, 245, 255), w=2)
    return


def o2(d, c, r=11, alpha=255):
    circle(d, (c[0] - r * .7, c[1]), r, fill=(150, 215, 255, alpha), outline=(235, 248, 255, alpha), w=2)
    circle(d, (c[0] + r * .7, c[1]), r, fill=(150, 215, 255, alpha), outline=(235, 248, 255, alpha), w=2)


def cells(im, d0, cx, it, a):
    Z = 1.25; box = it['box']; L, d = layer(box, Z)
    t1, t2, t4, t5 = T(cx, it.get('s1', 1)), T(cx, it.get('s2', 2)), T(cx, it.get('s4', 4)), T(cx, it.get('s5', 5))
    if t4 < 0:
        c = (480, 215); R = 150
        # 酸素が近づいて結びつく（文2）
        bind_p = ease((t2 - 1.0) / 2.0) if t2 >= 0 else 0.0
        col = lerp(DARK, BRIGHT, bind_p)
        if t1 >= 0:
            cell(d, c, R, col)
            text(d, (c[0], c[1] + R + 38), '赤血球', 34, WHITE, 'mm')
            text(d, (c[0] + R + 30, c[1] - 70), 'ヘモグロビン', 34, GOLD, 'la')
            poly(d, [(c[0] + R * .25, c[1] - R * .25), (c[0] + R + 22, c[1] - 52)], GOLD + (255,), 3)
            text(d, (c[0] + R + 30, c[1] + 10), '鉄（Fe）', 30, DIM, 'la')
        if t2 >= 0:
            for k in range(4):
                ang = k * math.pi / 2 + .6
                sx, sy = c[0] + math.cos(ang) * 360, c[1] + math.sin(ang) * 200
                tx, ty = c[0] + (-1 if k % 2 == 0 else 1) * R * .22, c[1] + (-1 if k < 2 else 1) * R * .22
                f = ease((t2 - 0.3) / 2.2)
                o2(d, (sx + (tx - sx) * f, sy + (ty - sy) * f), 12, int(255 * min(1, t2 / .5)))
            text(d, (c[0] + R + 30, c[1] + 70), '酸素（O2）が結びつく', 30, (150, 215, 255), 'la')
        if cx.on(it.get('s3', 3)):
            text(d, (box[2] - box[0] - 60, 60), 'この鉄が、血液を\n赤く見せている', 38, GOLD, 'ra')
    else:
        for c, col, n, lab, sub in (((380, 215), BRIGHT, 4, '酸素が多い → 明るい赤', '動脈の血（全身へ向かう）'), ((1060, 215), DARK, 1, '酸素が少ない → 暗い赤', '静脈の血（全身から戻る）')):
            k = ease(t4 / 0.8)
            cell(d, c, 120 * k, col)
            for j in range(n):
                ang = j * math.pi / 2 + .6
                o2(d, (c[0] + math.cos(ang) * 165, c[1] + math.sin(ang) * 100), 10, int(255 * k))
            text(d, (c[0], c[1] + 165), lab, 34, WHITE, 'mm', alpha=int(255 * k))
            if t5 >= 0:
                text(d, (c[0], c[1] + 210), sub, 30, GOLD, 'mm', alpha=int(255 * min(1, t5 / .6)))
        text(d, (720, 215), '⇄', 64, DIM, 'mm')
    commit(im, L, box, a)


# ------------------------------------------------------------------ 循環（心臓・組織・肺）
def heart(d, c, r):
    for dx in (-1, 1):
        circle(d, (c[0] + dx * r * .45, c[1] - r * .25), r * .55, fill=BRIGHT + (255,))
    d.polygon([((c[0] - r) * S, (c[1] - r * .05) * S), ((c[0] + r) * S, (c[1] - r * .05) * S), (c[0] * S, (c[1] + r * 1.15) * S)], fill=BRIGHT + (255,))


def loop_paths(ox, oy, k):
    P = lambda pts: [(ox + x * k, oy + y * k) for x, y in pts]
    return dict(
        art=P([(100, -40), (290, -150), (470, -90)]),     # 心臓 → 組織（動脈）
        vein=P([(470, 100), (290, 150), (100, 40)]),      # 組織 → 心臓（静脈）
        lung_out=P([(-100, 40), (-290, 150), (-470, 100)]),  # 心臓 → 肺
        pulm=P([(-470, -90), (-290, -150), (-100, -40)]),  # 肺 → 心臓（肺静脈）
    )


def loop_draw(d, ox, oy, k, mode, t, show_pulm=False, hl=False, labels=True, small=False, lungs=True):
    p = loop_paths(ox, oy, k)
    col_art = BRIGHT if mode == 'real' else (230, 70, 70)
    col_vein = DARK if mode == 'real' else VEINBLUE
    col_lo = DARK if mode == 'real' else VEINBLUE
    col_pu = BRIGHT if mode == 'real' else (230, 70, 70)
    for key, col in ((('art', col_art), ('vein', col_vein), ('lung_out', col_lo), ('pulm', col_pu)) if lungs else (('art', col_art), ('vein', col_vein))):
        w = 18 * k
        if key == 'pulm' and hl:
            poly(d, p[key], GOLD + (255,), w + 10 * k)
        poly(d, p[key], col + (255,), w)
        moving_dots(d, p[key], (255, 255, 255, 230), t, n=4, r=max(4, 6 * k), speed=150 * k)
    heart(d, (ox, oy), 70 * k)
    d.rounded_rectangle(((ox + 470 * k - 70 * k) * S, (oy - 60 * k) * S, (ox + 470 * k + 70 * k) * S, (oy + 90 * k) * S), 16 * S, fill=(40, 70, 95, 255), outline=(150, 175, 200, 255), width=3 * S)
    if lungs:
        circle(d, (ox - 470 * k, oy + 0), 78 * k, fill=(40, 70, 95, 255), outline=(150, 175, 200, 255), w=3)
    if labels:
        fs = 28 if not small else 22
        text(d, (ox + 470 * k, oy + 15 * k), '組織', fs, WHITE, 'mm')
        if lungs:
            text(d, (ox - 470 * k, oy + 0), '肺', fs, WHITE, 'mm')
        text(d, (ox, oy + 95 * k), '心臓', fs, WHITE, 'mm')


def loop(im, d0, cx, it, a):
    Z = 1.3; box = it['box']; L, d = layer(box, Z); t = cx.t
    VW, VH = vs(box, Z); ox, oy, k = VW / 2, VH / 2 + 10, 0.95
    ps = T(cx, it.get('s_pulm', 3))
    loop_draw(d, ox, oy, k, 'real', t, show_pulm=ps >= 0, hl=(ps >= 0 and ps < 40))
    p = loop_paths(ox, oy, k)
    text(d, p['art'][1], '動脈（全身へ）', 30, WHITE, 'ms') if False else None
    text(d, (ox + 290 * k, oy - 175 * k), '動脈：全身へ', 30, WHITE, 'mm')
    text(d, (ox + 290 * k, oy + 178 * k), '静脈：全身から戻る', 30, WHITE, 'mm')
    text(d, (ox - 290 * k, oy + 178 * k), '肺へ', 30, WHITE, 'mm')
    c = GOLD if ps >= 0 else WHITE
    text(d, (ox - 290 * k, oy - 175 * k), '肺静脈：肺から戻る', 30, c, 'mm')
    if ps >= 0:
        text(d, (ox - 290 * k, oy - 215 * k), '酸素が多い（明るい赤）', 28, GOLD, 'mm')
    commit(im, L, box, a)


# ------------------------------------------------------------------ 皮膚の断面と光（模式図）
def skin(im, d0, cx, it, a):
    Z = 1.25; box = it['box']; L, d = layer(box, Z); W, H = vs(box, Z)
    t_red = T(cx, it.get('s_red', 4)); t_blue = T(cx, it.get('s_blue', 5)); t_view = T(cx, it.get('s_view', 6))
    x0, x1 = 100, W - 100
    ys = 120
    d.rectangle((x0 * S, ys * S, x1 * S, (ys + 30) * S), fill=SKIN + (255,))                 # 表皮
    d.rectangle((x0 * S, (ys + 30) * S, x1 * S, (ys + 160) * S), fill=DERMIS + (255,))         # 真皮
    d.rectangle((x0 * S, (ys + 160) * S, x1 * S, (ys + 300) * S), fill=FAT + (255,))           # 脂肪
    text(d, (x0 + 10, ys + 36), '皮膚', 28, (90, 40, 30), 'la'); text(d, (x0 + 10, ys + 166), '脂肪', 28, (110, 90, 20), 'la')
    vc = (W * 0.66, ys + 232); vr = 46
    circle(d, vc, vr, fill=DARK + (255,), outline=(60, 10, 20, 255), w=3)
    text(d, (vc[0], vc[1]), '血', 32, (255, 220, 220), 'mm', serif=True)
    text(d, (vc[0] + vr + 18, vc[1]), '静脈（中の血は暗い赤）', 30, (90, 60, 10), 'lm')
    ex, ey = W * 0.05, 66
    circle(d, (ex, ey), 26, fill=(245, 245, 245, 255), outline=(200, 200, 200, 255), w=3); circle(d, (ex, ey), 11, fill=(40, 40, 60, 255))
    text(d, (ex + 38, ey + 4), '見る人', 26, DIM, 'lm')
    if t_red >= 0:   # 赤い光：深くまで届く
        for i in range(4):
            xs = W * (0.46 + i * 0.07)
            f = ease((t_red - i * .15) / 2.0)
            ytop = 34; ydown = ys + 270
            yy = ytop + (ydown - ytop) * f
            pts = [(xs, ytop)]
            for yk in range(int(ytop) + 26, int(yy), 26):
                pts.append((xs + (7 if (yk // 26) % 2 else -7), yk))
            pts.append((xs, yy))
            poly(d, pts, (255, 110, 110, 255), 5)
        text(d, (W * 0.52, 6), '赤い光：深くまで届く', 28, (255, 140, 140), 'la')
    if t_blue >= 0:  # 青い光：浅いところで多くが戻る
        for i in range(4):
            xs = W * (0.18 + i * 0.05)
            f = ease((t_blue - i * .15) / 1.0)
            ytop = 34; yhit = ys + 16
            yy = ytop + (yhit - ytop) * min(1, f * 2)
            poly(d, [(xs, ytop), (xs + 16 * min(1, f * 2), yy)], (110, 170, 255, 255), 5)
            if f > .5:
                r = (f - .5) * 2
                poly(d, [(xs + 16, yhit), (xs + 16 + 50 * r, yhit - (yhit - 70) * r * 0.9)], (110, 170, 255, 255), 5)
        text(d, (W * 0.16, 6), '青い光：浅く入り、多くが戻る', 28, (130, 180, 255), 'la')
    if t_view >= 0:
        text(d, (W / 2, ys + 322), '光の入り方の違いで、明るい肌では静脈が青っぽく見える（と説明されている）', 30, GOLD, 'mm')
    text(d, (W - 10, H - 4), '※光の入り方の深さの違いを示す模式図（実際の光の経路ではありません）', 26, DIM, 'rs')
    commit(im, L, box, a)


# ------------------------------------------------------------------ 肌の色と見え方
def skintone(im, d0, cx, it, a):
    Z = 1.2; box = it['box']; L, d = layer(box, Z); W, H = vs(box, Z)
    t = T(cx, it.get('at', 0))
    for i, (tone, lab, vis) in enumerate(((SKIN, '明るい肌', 1.0), ((140, 92, 66), '濃い肌', 0.35))):
        cx0 = W * (0.25 + 0.5 * i); cy0 = 210
        d.rounded_rectangle(((cx0 - 220) * S, (cy0 - 130) * S, (cx0 + 220) * S, (cy0 + 130) * S), 30 * S, fill=tone + (255,))
        vcol = (120, 150, 200) if i == 0 else lerp((140, 92, 66), (110, 120, 150), .35)
        poly(d, [(cx0 - 180, cy0 + 10), (cx0 - 60, cy0 - 20), (cx0 + 60, cy0 + 20), (cx0 + 180, cy0 - 10)], vcol + (int(255 * ease(t / .8) * 1),), 14)
        text(d, (cx0, cy0 + 170), lab, 34, WHITE, 'mm')
        text(d, (cx0, cy0 + 215), '静脈が見えやすい' if i == 0 else '静脈が目立ちにくい', 28, GOLD if i == 0 else DIM, 'mm')
    commit(im, L, box, a)


def contrast(im, d0, cx, it, a):
    """同じ色の帯でも、周りの色で見え方が変わる（定性的な例）"""
    Z = 1.2; box = it['box']; L, d = layer(box, Z); W, H = vs(box, Z)
    t = T(cx, it.get('at', 0)); k = ease(t / .8)
    bar = (130, 110, 150)
    for i, (bg, lab) in enumerate(((SKIN, '明るい背景'), ((70, 45, 35), '暗い背景'))):
        x = 60 + i * (W / 2)
        d.rounded_rectangle((x * S, 20 * S, (x + W / 2 - 80) * S, 230 * S), 24 * S, fill=lerp(BG, bg, k) + (255,))
        d.rounded_rectangle(((x + 60) * S, 105 * S, (x + W / 2 - 140) * S, 145 * S), 20 * S, fill=bar + (255,))
        text(d, (x + (W / 2 - 80) / 2, 262), lab, 30, WHITE, 'mm')
    text(d, (W / 2, 320), '同じ色の帯でも、周りの色で見え方が変わる（例）', 30, GOLD, 'mm')
    commit(im, L, box, a)


# ------------------------------------------------------------------ 教科書の図と実際の色
def textbook(im, d0, cx, it, a):
    Z = 1.3; box = it['box']; L, d = layer(box, Z); W, H = vs(box, Z)
    t = cx.t
    k = 0.55
    s_legend, s_real = T(cx, it.get('s_legend', 1)), T(cx, it.get('s_real', 2))
    loop_draw(d, W * 0.27, 215, k, 'book', t, labels=True, small=True, lungs=False)
    text(d, (W * 0.27, 20), '教科書の図（全身の循環。色は区別のため）', 30, WHITE, 'mm')
    if s_legend >= 0:
        d.rounded_rectangle((W * 0.06 * S, 350 * S, W * 0.47 * S, 420 * S), 14 * S, fill=(12, 34, 50, 255), outline=GOLD + (255,), width=3 * S)
        circle(d, (W * 0.09, 385), 12, fill=VEINBLUE + (255,)); text(d, (W * 0.11, 385), '青＝静脈（動脈と区別する色）', 28, WHITE, 'lm')
    if s_real >= 0:
        kk = ease(s_real / .8)
        loop_draw(d, W * 0.73, 215, k, 'real', t, labels=True, small=True, lungs=False)
        text(d, (W * 0.73, 20), '実際の血の色', 32, GOLD, 'mm')
        d.rounded_rectangle((W * 0.53 * S, 350 * S, W * 0.94 * S, 420 * S), 14 * S, fill=(12, 34, 50, 255), outline=GOLD + (255,), width=3 * S)
        circle(d, (W * 0.56, 385), 12, fill=DARK + (255,)); text(d, (W * 0.58, 385), '全身から戻る静脈の血：暗い赤', 28, WHITE, 'lm')
    commit(im, L, box, a)


# ------------------------------------------------------------------ 偏角（真北と磁北のなす角）
def _arrow(d, o, ang_deg, length, col, w=8, k=1.0):
    """上向きを0度、西（左）へ正の角度で傾ける"""
    a = math.radians(ang_deg)
    e = (o[0] - math.sin(a) * length * k, o[1] - math.cos(a) * length * k)
    poly(d, [o, e], col, w)
    if k > .98:
        arrow_head(d, o, e, col, 26)
    return e


def decl_one(d, o, L, theta, k_true, k_mag, k_arc, lab_theta, big=True, tsize=30):
    if k_true > 0:
        e = _arrow(d, o, 0, L, GOLD + (255,), 8, k_true)
        if k_true > .9:
            text(d, (e[0], e[1] - 16), '真北', tsize, GOLD, 'mb')
    if k_mag > 0:
        e = _arrow(d, o, theta, L, (150, 215, 255, 255), 8, k_mag)
        if k_mag > .9:
            text(d, (e[0] - 10, e[1] - 16), '磁北', tsize, (150, 215, 255), 'rb')
    if k_arc > 0:
        r = L * 0.55
        n = 30
        pts = [(o[0] - math.sin(math.radians(theta * i / n)) * r, o[1] - math.cos(math.radians(theta * i / n)) * r) for i in range(int(n * k_arc) + 1)]
        if len(pts) > 1:
            poly(d, pts, (255, 255, 255, 255), 5)
        if k_arc > .9:
            text(d, (o[0] - r * 0.95, o[1] - r * 1.12), lab_theta, tsize, WHITE, 'rb')
    circle(d, o, 9, fill=WHITE + (255,))


def declination(im, d0, cx, it, a):
    Z = 1.25; box = it['box']; L, d = layer(box, Z); W, H = vs(box, Z)
    kt = ease(T(cx, it.get('s_true', 2)) / 0.9) if T(cx, it.get('s_true', 2)) >= 0 else 0
    km = ease(T(cx, it.get('s_mag', 3)) / 0.9) if T(cx, it.get('s_mag', 3)) >= 0 else 0
    ka = ease(T(cx, it.get('s_arc', 4)) / 0.9) if T(cx, it.get('s_arc', 4)) >= 0 else 0
    decl_one(d, (W * 0.5, H - 70), H - 170, 26, kt, km, ka, '偏角', tsize=34)
    text(d, (W * 0.5, H - 28), '※角度は強調した模式図（西へずれる例）', 24, DIM, 'mm')
    commit(im, L, box, a)


def declination2(im, d0, cx, it, a):
    Z = 1.25; box = it['box']; L, d = layer(box, Z); W, H = vs(box, Z)
    t = max(0.0, T(cx, it.get('at', 3)))
    k = ease(t / 0.9)
    for i, (name, ang) in enumerate((('札幌', 10), ('那覇', 6))):
        o = (W * (0.27 + 0.46 * i), H - 90)
        decl_one(d, o, H - 190, ang, 1.0 * k, 1.0 * k, k if t > 0.9 else 0, f'約{ang}度', tsize=30)
        text(d, (o[0], H - 40), f'{name}：西へ約{ang}度', 34, WHITE, 'mm')
    text(d, (W / 2, H - 6), '※2020年の磁気図（国土地理院）。角度は実際の大きさ', 22, DIM, 'ms')
    commit(im, L, box, a)


# ------------------------------------------------------------------ 北極側から見た、北極点と磁極の位置（模式図）
def polar(im, d0, cx, it, a):
    Z = 1.0; box = it['box']; L, d = layer(box, Z); W, H = vs(box, Z)
    c = (W / 2, H / 2 + 6); kdeg = (min(W, H) / 2 - 50) / 10.5
    for colat, lab in ((5, '北緯85度'), (10, '北緯80度')):
        circle(d, c, colat * kdeg, outline=(120, 150, 175, 255), w=2)
        text(d, (c[0] + 6, c[1] - colat * kdeg - 4), lab, 22, DIM, 'ls')
    for ang in range(0, 360, 45):
        r = 10.5 * kdeg
        poly(d, [c, (c[0] + r * math.sin(math.radians(ang)), c[1] - r * math.cos(math.radians(ang)))], (70, 95, 115, 255), 1)
    for lon, lab in ((139.298, '東経139度'), (-72.76, '西経73度')):
        r = 10.5 * kdeg
        e = (c[0] + r * math.sin(math.radians(lon)), c[1] - r * math.cos(math.radians(lon)))
        poly(d, [c, e], (110, 140, 165, 255), 2)
        text(d, (e[0], e[1] + (18 if lon > 0 else -18)), lab, 22, DIM, 'mm')
    t_c, t_m, t_l, t_g = T(cx, it.get('s_center', 2)), T(cx, it.get('s_mag', 1)), T(cx, it.get('s_line', 3)), T(cx, it.get('s_geo', 6))
    mp = (c[0] + 4.238 * kdeg * math.sin(math.radians(139.298)), c[1] - 4.238 * kdeg * math.cos(math.radians(139.298)))
    gp = (c[0] + 9.15 * kdeg * math.sin(math.radians(-72.76)), c[1] - 9.15 * kdeg * math.cos(math.radians(-72.76)))
    if t_c >= 0:
        circle(d, c, 9, fill=GOLD + (255,)); text(d, (c[0], c[1] - 24), '北極点（北緯90度）', 28, GOLD, 'mb')
    if t_m >= 0:
        k = ease(t_m / 0.6)
        circle(d, mp, 14 * k, fill=(150, 215, 255, 255), outline=WHITE + (255,), w=2)
        text(d, (mp[0] + 20, mp[1] + 4), '北の磁極' + chr(10) + '（2025年のモデル）', 28, (150, 215, 255), 'la')
    if t_l >= 0:
        poly(d, [c, mp], (255, 255, 255, 255), 3)
        text(d, ((c[0] + mp[0]) / 2 - 22, (c[1] + mp[1]) / 2 + 30), '約470 km', 28, WHITE, 'rm')
    if t_g >= 0:
        k = ease(t_g / 0.6)
        circle(d, gp, 14 * k, fill=(255, 170, 120, 255), outline=WHITE + (255,), w=2)
        text(d, (gp[0] + 20, gp[1] - 44), '地磁気極' + chr(10) + '（双極子モデル）', 28, (255, 170, 120), 'la')
    text(d, (W / 2, H - 14), '※北極側から見た模式図（位置関係は概略）', 22, DIM, 'ms')
    commit(im, L, box, a)


# ------------------------------------------------------------------ 公転と地軸の傾き（地球が太陽の周りを回る）
def orbit(im, d0, cx, it, a):
    Z = 0.95; box = it['box']; L, d = layer(box, Z); W, H = vs(box, Z)
    show_axis = it.get('axis', False); show_dist = it.get('dist', False); show_hemi = it.get('hemi', False)
    R = min(W, H) / 2 - 92
    c0 = (W / 2, H / 2 + 8)
    sun = (c0[0] + R * 0.03, c0[1])      # 軌道はほぼ円（太陽が、わずかに右へずれる）
    circle(d, c0, R, outline=(120, 150, 180, 255), w=3)
    for r_, al in ((70, 60), (56, 110), (44, 255)):
        circle(d, sun, r_, fill=(255, 190, 60, al))
    circle(d, sun, 40, fill=(255, 215, 90, 255))
    text(d, (sun[0], sun[1] + 66), '太陽', 26, WHITE, 'mm')
    # 4つの位置（左＝6月ごろ、右＝12月ごろ、下＝3月、上＝9月）
    spots = {'6月ごろ': (c0[0] - R, c0[1]), '12月ごろ': (c0[0] + R, c0[1]), '3月ごろ': (c0[0], c0[1] + R), '9月ごろ': (c0[0], c0[1] - R)}
    tilt = math.radians(23.4)
    for name, p in spots.items():
        lit = (255, 255, 255, 255)
        circle(d, p, 26, fill=(70, 130, 200, 255), outline=(200, 225, 255, 255), w=2)
        if show_axis:
            # 地軸：どの位置でも同じ向き（右へ傾く）。北極側を黄色で示す
            ax = (math.sin(tilt) * 52, -math.cos(tilt) * 52)
            poly(d, [(p[0] - ax[0], p[1] - ax[1]), (p[0] + ax[0], p[1] + ax[1])], (255, 255, 255, 255), 4)
            circle(d, (p[0] + ax[0], p[1] + ax[1]), 7, fill=GOLD + (255,))
        pos = (p[0], p[1] + 56) if name in ('3月ごろ',) else ((p[0], p[1] - 62) if name == '9月ごろ' else (p[0], p[1] + 58))
        text(d, pos, name, 26, WHITE, 'mm')
    if show_hemi:
        text(d, (c0[0] - R, c0[1] - 76), '北半球：夏', 28, (255, 170, 90), 'mm')
        text(d, (c0[0] + R, c0[1] - 76), '北半球：冬', 28, (150, 200, 255), 'mm')
        text(d, (c0[0] - R, c0[1] + 96), '南半球：冬', 28, (150, 200, 255), 'mm')
        text(d, (c0[0] + R, c0[1] + 96), '南半球：夏', 28, (255, 170, 90), 'mm')
    if show_dist:
        text(d, (c0[0] - R, c0[1] + 96), '遠日点（7月）', 28, (150, 215, 255), 'mm')
        text(d, (c0[0] + R, c0[1] + 96), '近日点（1月）', 28, (255, 170, 90), 'mm')
        text(d, (W / 2, 10), '※軌道はほぼ円（図は、距離の差をわずかに誇張）', 24, DIM, 'mt')
    commit(im, L, box, a)


# ------------------------------------------------------------------ 太陽の高さと、同じ幅の光が当たる面積
def sunangle(im, d0, cx, it, a):
    Z = 1.0; box = it['box']; L, d = layer(box, Z); W, H = vs(box, Z)
    t = cx.t
    for i, (ang, title, col) in enumerate(((78, '夏至のころ：高さ 約78度', (255, 170, 90)), (32, '冬至のころ：高さ 約32度', (150, 200, 255)))):
        ox = W * (0.25 + 0.5 * i); gy = H - 110
        d.rectangle(((ox - 230) * S, gy * S, (ox + 230) * S, (gy + 16) * S), fill=(110, 90, 70, 255))
        text(d, (ox, 22), title, 30, col, 'mm')
        a_ = math.radians(ang); dx, dy = -math.cos(a_), math.sin(a_)   # 光の進む向き（下向き）
        bw = 120.0
        # 同じ幅(bw)の光の束を、地面に垂直な幅で描く：地面上の幅は bw / sin(高度)
        foot = bw / math.sin(a_)
        hx = ox; hy = gy
        for k in range(5):
            off = (k - 2) * bw / 4
            # 光線（地面の点 (hx + off', gy) へ向かう）
            px = (k - 2) * foot / 4
            end = (hx + px, gy)
            start = (end[0] - dx * 380, end[1] - dy * 380)
            poly(d, [start, end], (255, 235, 150, 230), 4)
            for m in range(4):
                s_ = ((t * 150 + m * 95) % 380)
                q = (start[0] + dx * s_, start[1] + dy * s_)
                circle(d, q, 7, fill=(255, 250, 200, 255))
        poly(d, [(hx - foot / 2, gy - 4), (hx + foot / 2, gy - 4)], col + (255,), 10)
        text(d, (ox, gy + 50), f'地面で、光が広がる幅：{foot / bw:.1f}倍', 28, col, 'mm')
    text(d, (W / 2, H - 10), '※同じ幅の光の束（光の量は同じ）。大気は無視した模式図', 24, DIM, 'ms')
    commit(im, L, box, a)


# ------------------------------------------------------------------ 月の満ち欠けと、閏月（旧暦）
def moon(d, c, r, p, col=(235, 228, 190)):
    """p: 0=新月, 0.25=上弦, 0.5=満月, 0.75=下弦。簡単な描き分け"""
    circle(d, c, r, fill=(40, 52, 75, 255), outline=(120, 135, 160, 255), w=2)
    q = p if p <= 0.5 else 1 - p
    k = math.cos(2 * math.pi * q)
    pts = [(c[0] + r * math.cos(math.radians(f)), c[1] + r * math.sin(math.radians(f))) for f in range(-90, 91, 6)]
    pts += [(c[0] + k * r * math.cos(math.radians(f)), c[1] + r * math.sin(math.radians(f))) for f in range(90, -91, -6)]
    if p > 0.5:
        pts = [(2 * c[0] - x, y) for x, y in pts]
    if q > 0.001:
        d.polygon([(x * S, y * S) for x, y in pts], fill=col + (255,))


def lunar(im, d0, cx, it, a):
    """12か月＋閏月の帯。月の満ち欠け（約29.5日）が12回で約354日、季節の1年（約365日）とずれるので、閏月を足す"""
    Z = 1.1; box = it['box']; L, d = layer(box, Z); W, H = vs(box, Z)
    t12, t13 = T(cx, it.get('s_cycle', 1)), T(cx, it.get('s_leap', 3))
    n = 13 if t13 >= 0 else 12
    gap = (W - 120) / 13.0; r = min(gap * 0.38, 46)
    y = H * 0.42
    for i in range(12):
        k = ease((t12 - i * 0.12) / 0.5) if t12 >= 0 else 0
        if k <= 0:
            continue
        c = (60 + gap * (i + 0.5), y)
        moon(d, c, r * k, 0.5)
        text(d, (c[0], y + r + 26), f'{i + 1}', 24, DIM, 'mm')
    if t13 >= 0:
        k = ease(t13 / 0.8)
        c = (60 + gap * 12.5, y)
        circle(d, c, r * 1.25 * k, outline=GOLD + (255,), w=4)
        moon(d, c, r * k, 0.5)
        text(d, (c[0], y + r + 26), '閏月', 26, GOLD, 'mm')
    if t12 >= 0:
        text(d, (60 + gap * 6, H * 0.14), '月の満ち欠け（約29.5日）× 12か月 ＝ 約354日', 32, WHITE, 'mm')
        text(d, (60 + gap * 6, H * 0.78), '季節の1年は約365日 → 2〜3年に1度、閏月を入れて13か月の年に', 30, GOLD if t13 >= 0 else DIM, 'mm')
    commit(im, L, box, a)


# ------------------------------------------------------------------ 日付タイル（明治5年12月の日付と、西暦の対応）
def caltiles(im, d0, cx, it, a):
    Z = 1.0; box = it['box']; L, d = layer(box, Z); W, H = vs(box, Z)
    s1, s2, s3, s4 = T(cx, it.get('s_a', 4)), T(cx, it.get('s_b', 5)), T(cx, it.get('s_c', 6)), T(cx, it.get('s_skip', 7))
    tw_, th_ = 270, 270
    gap = 60
    x0 = (W - (4 * tw_ + 3 * gap)) / 2
    tiles = [('明治5年', '12月1日', '1872年12月30日', s1, False), ('明治5年', '12月2日', '1872年12月31日', s2, False),
             ('（旧暦のままなら）', '12月3日', '使われなかった日付', s4, True), ('明治6年', '1月1日', '1873年1月1日', s3, False)]
    for i, (era, jp, west, t, skip) in enumerate(tiles):
        if t < 0:
            continue
        k = ease(t / 0.6)
        x = x0 + i * (tw_ + gap); y = 30 + (1 - k) * 40
        fill = (245, 240, 225, int(255 * k)) if not skip else (60, 70, 90, int(255 * k))
        d.rounded_rectangle((x * S, y * S, (x + tw_) * S, (y + th_) * S), 22 * S, fill=fill, outline=(GOLD if not skip else DIM) + (int(255 * k),), width=4 * S)
        d.rectangle((x * S, y * S, (x + tw_) * S, (y + 70) * S), fill=((200, 70, 70, int(255 * k)) if not skip else (90, 100, 120, int(255 * k))))
        text(d, (x + tw_ / 2, y + 36), era, 26, WHITE, 'mm', alpha=int(255 * k))
        text(d, (x + tw_ / 2, y + 160), jp, 52 if not skip else 44, (50, 40, 40) if not skip else DIM, 'mm', serif=True, alpha=int(255 * k))
        text(d, (x + tw_ / 2, y + 225), west, 24, (70, 60, 60) if not skip else DIM, 'mm', alpha=int(255 * k))
        if skip:
            poly(d, [(x + 20, y + th_ - 20), (x + tw_ - 20, y + 90)], (230, 100, 100, int(255 * k)), 6)
    if s4 >= 0:
        text(d, (W / 2, H - 36), '日が消えたのではなく、日付の数え方が切り替わった', 34, GOLD, 'mm')
    commit(im, L, box, a)


DRAW = dict(lunar=lunar, caltiles=caltiles, orbit=orbit, sunangle=sunangle, declination=declination, declination2=declination2, polar=polar, forearm=forearm, cells=cells, loop=loop, skin=skin, skintone=skintone, contrast=contrast, textbook=textbook)
