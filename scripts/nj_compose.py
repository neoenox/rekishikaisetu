"""World-map video compositor: Pillow 2D (Natural Earth 110m, own projections) + narration timeline -> FFmpeg NVENC.
usage: gm_compose.py part A B | gm_compose.py final | gm_compose.py remix DB BGM.wav     (STILLS=f1,f2 env -> png stills, no encode)"""
from pathlib import Path
import json,subprocess,sys,math,glob,os,re
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from hn_text import display
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];FD='C:/Windows/Fonts/';_FC={}
SPEC_F={'sans':('NotoSansJP-VF.ttf',560),'sub':('NotoSansJP-VF.ttf',640),'serif':('NotoSerifJP-VF.ttf',800)}
def vfont(kind,size):
    k=(kind,size)
    if k not in _FC:
        f=ImageFont.truetype(FD+SPEC_F[kind][0],size);f.set_variation_by_axes([SPEC_F[kind][1]]);_FC[k]=f
    return _FC[k]
class _Fam:
    def __init__(s,kind):s.kind=kind
    def __getitem__(s,n):return vfont(s.kind,n)
F=_Fam('sans');FB=_Fam('serif');FSUB=_Fam('sub');SS=2
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
timeline=load('data/nj_timeline.json');audio=load('out/nj_audio_report.json');segs=audio['segments']
N=round(timeline[-1]['end']*30);KEYS=[c['key'] for c in timeline]
BG=(7,24,36,240);GOLD=(239,201,118);WHITE=(245,243,232);DIM=(190,205,208);EDGE=(176,153,100);NAVY=(9,22,34)
C_AFR=(255,150,90);C_GRL=(120,190,255);C_JPN=(170,135,255);LAND=(66,98,112);LINE=(150,178,188)
TITLES={'intro':'忍者は、黒装束で手裏剣を投げていたのか','shinobi':'「忍び」とは、何をした人たちか','books':'忍術書には、何が書かれているか','black':'黒装束と覆面は、どこから来たのか','shuriken':'手裏剣は、使われていたのか','image':'いまのイメージ','end':'分かること、決められないこと'}
# ---------------- text helpers
def tw(d,t,f):return d.textlength(t,font=f)
def wrap(d,text,font,maxw):
    if tw(d,text,font)<=maxw:return [text]
    best=None
    for k in range(1,len(text)):
        l1,l2=text[:k],text[k:];w1,w2=tw(d,l1,font),tw(d,l2,font)
        if w1>maxw or w2>maxw or text[k-1] in '（「『' or text[k] in '）」』、':continue
        score=max(w1,w2)+(400 if ('゠'<=text[k-1]<='ヿ' and '゠'<=text[k]<='ヿ') else 0)+(0 if text[k-1] in '、，。' else (70 if text[k-1] in 'はがをにのでとも' and not ('\u4e00'<=text[k]<='\u9fff' and '\u4e00'<=text[k-1]<='\u9fff') else 160))
        if best is None or score<best[0]:best=(score,[l1,l2])
    if best:return best[1]
    lines=[];cur=''
    for ch in text:
        if tw(d,cur+ch,font)>maxw and cur:lines.append(cur);cur=ch
        else:cur+=ch
    lines.append(cur);return lines
def panel(d,box,title=None):
    d.rounded_rectangle(box,12,fill=BG,outline=EDGE,width=2)
    if title:d.text((box[0]+22,box[1]+12),title,font=FB[36],fill=GOLD)
def line_text(d,xy,text,font=F[40],fill=WHITE,a=1.0,stroke=False):
    kw=dict(stroke_width=4,stroke_fill=(5,10,16,int(255*a))) if stroke else {}
    d.text(xy,text,font=font,fill=tuple(fill[:3])+(int(255*a),),**kw)
def ptext(d,x,y,text,font,maxw,fill=WHITE,a=1.0,stroke=False):
    lh=int(font.size*1.32)
    for l in wrap(d,text,font,maxw):line_text(d,(x,y),l,font,fill,a,stroke=stroke);y+=lh
    return y
def ease(x):x=min(1,max(0,x));return x*x*(3-2*x)
class Ctx:
    def __init__(s,ci,t):
        s.ci=ci;s.t=t;s.key=KEYS[ci];ch=timeline[ci];s.local=min(1,max(0,(t-ch['start'])/ch['duration']));s.segl=[x for x in segs if x['scene']==ci];s.st=[x['start'] for x in s.segl]
    def on(s,i):return i<len(s.st) and s.t>=s.st[i]
    def a(s,i,dur=.5):return 0.0 if not s.on(i) else min(1,(s.t-s.st[i])/dur)
    def idx(s):return sum(1 for x in s.st if s.t>=x)-1
    def prog(s,i,j,dur=None):
        """0..1 progress from start of sentence i to start (or end) of sentence j"""
        t0=s.st[min(i,len(s.st)-1)];t1=s.segl[min(j,len(s.segl)-1)]['end'] if dur is None else t0+dur;return min(1,max(0,(s.t-t0)/max(t1-t0,1e-6)))
def header(d,key):
    d.text((48,16),TITLES[key],font=FB[60],fill=WHITE,stroke_width=5,stroke_fill=(5,10,16));d.text((48,94),'忍者の通説を検証する',font=F[28],fill=(200,210,214),stroke_width=4,stroke_fill=(5,10,16))
# ---------------- ninja scenes (images: National Diet Library Digital Collection, pdm; see docs/themes/20261016_ninja/05_images_rights.md)
IMG_DIR=ROOT/'assets'/'ndl_ninja';_NJI={}
CROPS={'hokusai_black_ninja':(.55,.24,.95,.90),'hokusai_bar_shuriken':(.50,.22,.97,.90),'ehon_taikoki_kimura':(.49,.08,.97,.88),'honcho_nijushiko_yamamoto':(.08,.05,.50,.93),
       'toyokuni_goemon_hisayoshi':(.09,.075,.915,.86),'shoninki_ten_p1':(.02,.03,.52,.93),'shoninki_chi_p12':(.07,.07,.93,.93),'shoninki_jin_p21':(.05,.03,.95,.93),'fujita_flat_shuriken':(.10,.10,.48,.47)}
def nji(name,w,h):
    k=(name,w,h)
    if k not in _NJI:
        im=Image.open(IMG_DIR/f'{name}.jpg').convert('RGB');a,b,c,e=CROPS[name];im=im.crop((int(im.width*a),int(im.height*b),int(im.width*c),int(im.height*e)))
        s=min(w/im.width,h/im.height);_NJI[k]=im.resize((max(1,int(im.width*s)),max(1,int(im.height*s))),Image.LANCZOS)
    return _NJI[k]
def show_img(im,d,name,box,cap,a=1.0):
    """image fitted in box=(x0,y0,x1,y1) with a caption strip underneath; fades in with alpha a"""
    x0,y0,x1,y1=box;pic=nji(name,x1-x0-16,y1-y0-92);W_,H_=pic.size;cx_=x0+(x1-x0-W_)//2;cy_=y0+8
    layer=Image.new('RGBA',(x1-x0,y1-y0),(0,0,0,0));ld=ImageDraw.Draw(layer);ld.rounded_rectangle((0,0,x1-x0-1,y1-y0-1),12,fill=BG,outline=EDGE+(255,),width=2)
    layer.paste(pic,(cx_-x0,cy_-y0))
    for j,l in enumerate(wrap(d,cap,F[28],x1-x0-28)[:2]):ld.text((14,y1-y0-84+j*38),l,font=F[28],fill=WHITE+(255,))
    if a<1:r,g,b,al=layer.split();layer=Image.merge('RGBA',(r,g,b,al.point(lambda v:int(v*a))))
    im.alpha_composite(layer,(x0,y0))
def chip(d,x,y,w,h,text,font,col=GOLD,a=1.0,fill=None):
    d.rounded_rectangle((x,y,x+w,y+h),14,outline=col+(int(255*a),),width=3,fill=(fill or (12,34,50))+(int(255*a),));tw_=tw(d,text,font);line_text(d,(x+(w-tw_)/2,y+(h-font.size*1.25)/2),text,font,WHITE,a)
def sc_intro(im,d,cx):
    for k,t_ in enumerate(('黒装束','覆面','手裏剣')):
        if cx.on(0):chip(d,120+k*540,230,480,150,t_,FB[72],GOLD,cx.a(0)*(1 if True else 0))
    if cx.on(2):panel(d,(120,430,1800,590));ptext(d,160,456,'そのイメージは、いつ、どこから来たのか',FB[64],1600,WHITE,cx.a(2))
    if cx.on(3):panel(d,(120,620,1800,780),'この動画で見る資料');line_text(d,(160,690),'国立国会図書館の解説　／　研究者の説明',F[44],WHITE,cx.a(3))
    if cx.on(4):
        line_text(d,(160,796),'分かること',F[38],GOLD,cx.a(4));line_text(d,(480,796),'と',F[38],WHITE,cx.a(4));line_text(d,(540,796),'決められないこと',F[38],GOLD,cx.a(4));line_text(d,(920,796),'を分けて考える',F[38],WHITE,cx.a(4))
def tl_node(d,x,y,label,sub,col,a,w=380):
    d.ellipse((x-14,y-14,x+14,y+14),fill=col+(int(255*a),),outline=WHITE+(int(255*a),),width=3);line_text(d,(x-w/2+0,y+28),label,F[40],WHITE,a)
    for j,l in enumerate(wrap(d,sub,F[36],w)):line_text(d,(x-w/2,y+80+j*46),l,F[36],(215,224,226),a)
def sc_shinobi(im,d,cx):
    if cx.on(1):panel(d,(60,160,1860,260));line_text(d,(90,184),'間諜（スパイ）の記述は、古くから世界中の文献にある',F[40],WHITE,cx.a(1))
    d.line([(160,430),(1760,430)],fill=EDGE+(255,),width=5)
    nodes=[(2,260,'『太平記』の執筆時期','14世紀後半ごろ。忍びの具体的な活動の、国内最古の記録（石清水八幡宮への放火が書かれている）',C_AFR_),(4,700,'戦国時代','「草」：情報収集や夜道の案内など',C_AFR_),(7,1140,'1856年刊','『武用弁略』（原本の自序は1684年）に「忍者」の語。読みは「しのびのもの」',C_AFR_),(6,1580,'昭和30年代','「忍者」の呼び名が定着（研究者の山田雄司さんの説明）',C_AFR_)]
    for at,x,lab,sub,col in nodes:
        if cx.on(at):tl_node(d,x,430,lab,sub,col,cx.a(at),w=400)
    if cx.on(5):
        panel(d,(60,760,1860,850),'呼び名');line_text(d,(260,790),'忍び　／　忍びの者　／　草　／　乱波（らっぱ）　／　透波（すっぱ）',F[36],WHITE,cx.a(5))
C_AFR_=(255,150,90)
def sc_books(im,d,cx):
    cards=[(2,'『万川集海』','1676年　藤林保武　全22巻'),(3,'『正忍記』','1681年　全3巻'),(4,'『忍秘伝』','1655年とされる（真偽ははっきりしない）')]
    for k,(at,t_,s_) in enumerate(cards):
        if cx.on(at):
            a=cx.a(at);y=170+k*180;d.rounded_rectangle((60,y,980,y+160),14,fill=BG,outline=GOLD+(int(255*a),),width=3);line_text(d,(90,y+16),t_,FB[48],GOLD,a);ptext(d,90,y+86,s_,F[36],860,WHITE,a)
    if cx.on(5):panel(d,(60,720,980,840));ptext(d,90,740,'『正忍記』：七方出＝七つの変装の姿',F[36],880,WHITE,cx.a(5))
    if cx.on(6) and not cx.on(7):
        d.rounded_rectangle((1010,170,1860,320),14,fill=BG,outline=EDGE+(255,),width=2);ptext(d,1034,186,'服装は、目立たず、人に近づきやすいものが、ふさわしい',F[34],800,WHITE,cx.a(6))
    if cx.on(7):
        d.rounded_rectangle((1010,170,1860,320),14,fill=BG,outline=GOLD+(255,),width=3);ptext(d,1034,186,'書かれた教え　と　実際の行動は、分けて考える',F[36],800,GOLD,cx.a(7))
    pic=('shoninki_ten_p1','『正忍記』の写本（寛保3年＝1743年の写し）') if cx.idx()<4 else (('shoninki_chi_p12','『正忍記』の本文の一部') if cx.idx()<7 else ('shoninki_jin_p21','『正忍記』の奥書（写された年が書かれている）'))
    if cx.on(3) or cx.idx()>=3:show_img(im,d,pic[0],(1010,340,1860,850) if cx.on(6) else (1010,170,1860,850),pic[1],cx.a(3) if cx.idx()<4 else 1.0)
def sc_black(im,d,cx):
    i=cx.idx()
    if i<5:
        if cx.on(1):panel(d,(60,170,930,330),'国立国会図書館の解説');ptext(d,90,230,'もともと、特徴的な黒装束ではなかった',F[40],800,WHITE,cx.a(1))
        if cx.on(2):
            cols=[('茶色',(120,80,50)),('柿色',(205,110,45)),('黒色',(22,22,26)),('紺色',(26,40,96))]
            d.rounded_rectangle((60,350,930,560),14,fill=BG,outline=EDGE+(255,),width=2);line_text(d,(86,360),'『正忍記』が挙げる色（色見本はイメージ）',F[32],GOLD,cx.a(2))
            for k,(n_,c_) in enumerate(cols):
                x=90+k*205;d.rounded_rectangle((x,410,x+180,500),10,fill=c_+(int(255*cx.a(2)),),outline=WHITE+(int(255*cx.a(2)),),width=3);line_text(d,(x+44,508),n_,F[30],WHITE,cx.a(2))
        if cx.on(3):panel(d,(60,590,930,670));line_text(d,(90,606),'黒も、服装の選択肢として挙げられている',F[34],GOLD,cx.a(3))
        if cx.on(4):panel(d,(60,690,930,840));ptext(d,90,708,'問題は、黒装束と覆面を「忍者の決まった姿」として描く表現',F[34],820,WHITE,cx.a(4))
        if cx.on(0):show_img(im,d,'hokusai_black_ninja',(960,170,1860,850),'『北斎漫画』に描かれた黒装束の忍者（1878年刊）',cx.a(0))
        if i==0:panel(d,(60,170,930,330),'この章の問い');ptext(d,90,230,'黒装束と覆面は、どこから来たのか',F[40],800,WHITE,cx.a(0))
        return
    items=[(5,'演劇（歌舞伎・浄瑠璃）から、広まったと考えられている',GOLD),(6,'三重大学が掲載した記事で、吉丸雄哉さんは「18世紀中ごろの演劇から発生・定着」と説明',WHITE),(7,'演劇では、「この人は忍者です」と、文字で説明できない',WHITE),(8,'見ただけで分かる黒装束が、演出上の工夫として使われた（と考えられている）',GOLD)]
    y=170
    for at,t_,col in items:
        if cx.on(at):
            ls=wrap(d,t_,F[34],820);h=len(ls)*44+40;d.rounded_rectangle((60,y,930,y+h),14,fill=BG,outline=(GOLD if col==GOLD else EDGE)+(255,),width=2)
            for j,l in enumerate(ls):line_text(d,(86,y+18+j*44),l,F[34],col,cx.a(at))
            y+=h+16
    show_img(im,d,'ehon_taikoki_kimura',(960,170,1400,850),'『絵本太閤記』（1884年刊）',cx.a(5))
    show_img(im,d,'honcho_nijushiko_yamamoto',(1420,170,1860,850),'『本朝廿四孝』（明治期）',cx.a(5))
def sc_shuriken(im,d,cx):
    i=cx.idx()
    items=[(1,'手裏剣術は、武芸として実在（流派ごとに伝わる）',WHITE),(2,'これまでに見つかっている忍術書には、手裏剣の記述がない。使った記録も、見当たらない（国立国会図書館の解説）',WHITE),(3,'通常の忍者の道具とは考えられていなかったことがうかがえる',WHITE),(4,'使った可能性は、否定できない',GOLD)]
    y=170
    if i==0:panel(d,(60,170,930,330),'この章の問い');ptext(d,90,230,'手裏剣は、実際に使われていたのか',F[40],800,WHITE,cx.a(0))
    for at,t_,col in items:
        if cx.on(at):
            ls=wrap(d,t_,F[34],820);h=len(ls)*44+40;d.rounded_rectangle((60,y,930,y+h),14,fill=BG,outline=(GOLD if col==GOLD else EDGE)+(255,),width=2)
            for j,l in enumerate(ls):line_text(d,(86,y+18+j*44),l,F[34],col,cx.a(at))
            y+=h+14
    if cx.on(5) and not cx.on(6):show_img(im,d,'toyokuni_goemon_hisayoshi',(960,170,1860,850),'『楼門五三桐』手裏剣を投げる五右衛門',cx.a(5))
    if cx.on(6):
        show_img(im,d,'hokusai_bar_shuriken',(960,170,1860,850),'『北斎漫画』棒状の手裏剣（1878年刊）',cx.a(6))
    if cx.on(7):panel(d,(60,700,930,840));ptext(d,90,716,'手裏剣を使う忍者の姿は、歌舞伎など娯楽の世界から定着したと考えられる',F[34],820,GOLD,cx.a(7))
def sc_image(im,d,cx):
    d.line([(160,420),(1760,420)],fill=EDGE+(255,),width=5)
    if cx.on(0):tl_node(d,520,420,'江戸時代','演劇で広まったとされる、黒装束・覆面・手裏剣の忍者の姿',C_AFR_,cx.a(0),w=560)
    if cx.on(1):tl_node(d,1400,420,'昭和30年代','「忍者」という呼び名が定着（研究者の説明）',C_AFR_,cx.a(1),w=560)
    if cx.on(1):panel(d,(260,640,1660,760));ptext(d,300,662,'呼び名が定着した時期と、姿が作られた時期は、同じではない',F[44],1340,GOLD,cx.a(1))
    if cx.on(2):line_text(d,(380,790),'いまの忍者像は、長い時間をかけて重ねられてきた像',F[40],WHITE,cx.a(2))
def sc_end(im,d,cx):
    d.rounded_rectangle((50,170,1010,760),14,fill=BG,outline=GOLD+(255,),width=3);line_text(d,(80,184),'分かること',FB[48],GOLD,1.0)
    it=[(2,'黒装束と覆面を「決まった姿」とする表現は、江戸時代の演劇から広まったと説明されている'),(4,'『正忍記』には、茶・柿・黒・紺色が挙げられている（国立国会図書館の解説）'),(6,'これまでに見つかっている忍術書に、手裏剣の記述はなく、使った記録も見当たらない（同）')]
    y=270
    for at,t_ in it:
        if cx.on(at):
            ls=wrap(d,t_,F[38],860);line_text(d,(80,y),'・',F[38],GOLD,cx.a(at))
            for j,l in enumerate(ls):line_text(d,(116,y+j*50),l,F[38],WHITE,cx.a(at))
            y+=len(ls)*50+30
    if cx.on(7):
        d.rounded_rectangle((1040,170,1870,760),14,fill=BG,outline=EDGE+(255,),width=3);line_text(d,(1070,184),'一つに決められないこと',FB[44],GOLD,cx.a(7))
        if cx.on(8):ptext(d,1070,290,'個々の忍びが、どんな服を着て、何を使ったのかは、これらの資料だけでは、決められない',F[40],740,WHITE,cx.a(8))
SCENES={'intro':sc_intro,'shinobi':sc_shinobi,'books':sc_books,'black':sc_black,'shuriken':sc_shuriken,'image':sc_image,'end':sc_end}
# ---------------- subtitles (46px, max 2 lines, long sentences are paged instead of shrunk)
_SUBP={}
def sub_lines(d,seg,f,t):
    k=seg['start']
    if k not in _SUBP:
        txt=display(seg['text']);ls=wrap(d,txt,f,1720)
        if len(ls)<=2:_SUBP[k]=[(ls,seg['start'],seg['end'])]
        else:
            allw=[];cur=''
            for ch in txt:
                if tw(d,cur+ch,f)>1720 and cur:allw.append(cur);cur=ch
                else:cur+=ch
            allw.append(cur);pages=[allw[i:i+2] for i in range(0,len(allw),2)];tot=sum(len(''.join(p)) for p in pages);cum=0;out=[]
            for p in pages:
                n=len(''.join(p));out.append((p,seg['start']+(seg['end']-seg['start'])*cum/tot,seg['start']+(seg['end']-seg['start'])*(cum+n)/tot));cum+=n
            _SUBP[k]=out
    for ls,s0,s1 in _SUBP[k]:
        if t<s1:return ls
    return _SUBP[k][-1][0]
def render_frame(i):
    t=i/30;ci=next(k for k,c in enumerate(timeline) if t<c['end']+1e-9);cx=Ctx(ci,t)
    im=Image.new('RGBA',(1920,1080),NAVY+(255,));d=ImageDraw.Draw(im,'RGBA')
    header(d,cx.key);SCENES[cx.key](im,d,cx);d=ImageDraw.Draw(im,'RGBA')
    active=next((x for x in cx.segl if x['start']<=t<x['end']),None)
    if active:
        f=FSUB[46];lines=sub_lines(d,active,f,t);sub=(60,860,1860,1008);d.rounded_rectangle(sub,12,fill=(5,18,29,242))
        for j,txt in enumerate(lines):
            w=tw(d,txt,f);assert w<1760;d.text(((1920-w)/2,872+j*62),txt,font=f,fill='#fffcef')
    d.rectangle((48,1012,48+1824*(i+1)/N,1018),fill=(201,173,112));return im
def render(a,b):
    stills=[int(x) for x in os.environ['STILLS'].split(',')] if os.environ.get('STILLS') else None
    out=ROOT/'cache'/f'nj_part_{a}_{b}.mp4';log=(ROOT/'logs'/f'nj_enc_{a}.log').open('wb')
    class _P:
        class stdin:
            write=staticmethod(lambda b:None);close=staticmethod(lambda:None)
        def wait(self):pass
        returncode=0
    proc=_P() if stills else subprocess.Popen(['ffmpeg','-y','-v','warning','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','30','-i','pipe:0','-an','-c:v','h264_nvenc','-preset','p4','-cq','19','-b:v','0','-pix_fmt','yuv420p',str(out)],stdin=subprocess.PIPE,stderr=log)
    try:
        for i in (stills or range(a,min(b,N))):
            im=render_frame(i);proc.stdin.write(im.convert('RGB').tobytes())
            if stills:im.convert('RGB').save(ROOT/'cache'/f'gmstill_{i}.png')
            if i%600==0:print(a,i,flush=True)
    finally:
        proc.stdin.close();proc.wait();log.close()
    assert proc.returncode==0
    if not stills:(ROOT/'cache'/f'nj_part_{a}_{b}.json').write_text(json.dumps(dict(range=[a,b])),encoding='utf8')
def chk_duration():
    r=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(ROOT/'out'/'nj_video.mp4')],capture_output=True,text=True);dur=float(r.stdout.strip())
    assert abs(dur-timeline[-1]['end'])<1.0,f'video {dur:.2f}s != timeline end {timeline[-1]["end"]:.2f}s (truncated parts?)'
def final():
    parts=sorted(ROOT.glob('cache/nj_part_*.mp4'),key=lambda p:int(p.stem.split('_')[2]))
    lst=ROOT/'cache'/'nj_parts.txt';lst.write_text(''.join(f"file '{p.as_posix()}'\n" for p in parts));wav=str(ROOT/'out'/'nj_narration.wav')
    r=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',wav,'-af','loudnorm=I=-15:TP=-1.5:LRA=9:print_format=json','-f','null','-'],capture_output=True,text=True)
    j=json.loads(re.search(r'\{[^{}]*"input_i"[^{}]*\}',r.stderr,re.S).group(0))
    af=f"loudnorm=I=-15:TP=-1.5:LRA=9:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true"
    subprocess.run(['ffmpeg','-y','-v','warning','-f','concat','-safe','0','-i',str(lst),'-i',wav,'-map','0:v','-map','1:a','-c:v','h264_nvenc','-preset','p5','-cq','25','-b:v','0','-pix_fmt','yuv420p','-af',af,'-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart','-shortest',str(ROOT/'out'/'nj_video.mp4')],check=True)
    chk_duration();print('loudnorm input',j['input_i'],'LUFS')
def remix(bgm_db=-16.0,bgm_file='nj_bgm.wav'):
    nar=str(ROOT/'out'/'nj_narration.wav');bgm=str(ROOT/'out'/bgm_file);mix=str(ROOT/'cache'/'nj_mix.wav')
    fc=f"[0:a]aresample=48000,pan=stereo|c0=c0|c1=c0,asplit=2[n1][n2];[1:a]volume={bgm_db}dB[bg];[bg][n2]sidechaincompress=threshold=0.02:ratio=4:attack=30:release=900:makeup=1[duck];[n1][duck]amix=inputs=2:normalize=0:duration=first[m]"
    subprocess.run(['ffmpeg','-y','-v','warning','-i',nar,'-i',bgm,'-filter_complex',fc,'-map','[m]','-c:a','pcm_s16le',mix],check=True)
    r=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',mix,'-af','loudnorm=I=-15:TP=-1.5:LRA=9:print_format=json','-f','null','-'],capture_output=True,text=True)
    j=json.loads(re.search(r'\{[^{}]*"input_i"[^{}]*\}',r.stderr,re.S).group(0))
    af=f"loudnorm=I=-15:TP=-1.5:LRA=9:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true"
    subprocess.run(['ffmpeg','-y','-v','warning','-i',str(ROOT/'out'/'nj_video_nobgm.mp4'),'-i',mix,'-map','0:v','-map','1:a','-c:v','copy','-af',af,'-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart','-shortest',str(ROOT/'out'/'nj_video.mp4')],check=True)
    print('mix input',j['input_i'])
if __name__=='__main__':
    if sys.argv[1]=='part':render(int(sys.argv[2]),int(sys.argv[3]))
    elif sys.argv[1]=='final':final()
    elif sys.argv[1]=='remix':remix(float(sys.argv[2]) if len(sys.argv)>2 else -16.0,sys.argv[3] if len(sys.argv)>3 else 'nj_bgm.wav')
