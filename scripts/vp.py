"""Generic explainer-video pipeline (card compositor).  Replaces the per-video copies (nj_*, gm_*): everything is driven by
  data/<slug>_spec.json   (chapters -> scene items, images, bgm plan, description/thumbnail fields)
  docs/themes/<theme_dir>/09_script_v2.md   (narration: "## 章N　title" + numbered lines)
usage:  python scripts/vp.py <slug> story|kana|audio|bgm|parts|build|qa|desc|thumb|pack
  build = render all parts in parallel -> concat -> loudnorm -> BGM remix -> out/<slug>_video.mp4 (+ qa)
Scene item types (all optional 'at' = sentence index at which the item appears, 'until' = index at which it disappears):
  stack, panel, image, timeline, chips, bars, table, cols2, big, flow
"""
from pathlib import Path
import json,subprocess,sys,math,os,re,hashlib,time,wave,shutil
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from hn_text import display
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];FD='C:/Windows/Fonts/';BASE='http://127.0.0.1:50021';SPEED=0.95
BG=(7,24,36,240);GOLD=(239,201,118);WHITE=(245,243,232);DIM=(190,205,208);EDGE=(176,153,100);NAVY=(9,22,34);ORG=(255,150,90);BLUE=(120,190,255);VIO=(170,135,255);GRN=(120,210,150);RED=(235,90,80)
COL={'gold':GOLD,'white':WHITE,'dim':DIM,'org':ORG,'blue':BLUE,'vio':VIO,'grn':GRN,'red':RED}
SPEC_F={'sans':('NotoSansJP-VF.ttf',560),'sub':('NotoSansJP-VF.ttf',640),'serif':('NotoSerifJP-VF.ttf',800)}
_FC={}
def vfont(kind,size):
    k=(kind,size)
    if k not in _FC:
        f=ImageFont.truetype(FD+SPEC_F[kind][0],size);f.set_variation_by_axes([SPEC_F[kind][1]]);_FC[k]=f
    return _FC[k]
class _Fam:
    def __init__(s,kind):s.kind=kind
    def __getitem__(s,n):return vfont(s.kind,n)
F=_Fam('sans');FB=_Fam('serif');FSUB=_Fam('sub')
SLUG=None;SPEC=None;TL=None;SEGS=None;N=0;KEYS=[]
def P(rel):return ROOT/rel
def load_spec(slug):
    global SLUG,SPEC;SLUG=slug;SPEC=json.loads(P(f'data/{slug}_spec.json').read_text(encoding='utf8'));return SPEC
def theme_dir():return P('docs/themes')/SPEC['theme_dir']
def load_runtime():
    global TL,SEGS,N,KEYS
    TL=json.loads(P(f'data/{SLUG}_timeline.json').read_text(encoding='utf8'));SEGS=json.loads(P(f'out/{SLUG}_audio_report.json').read_text(encoding='utf8'))['segments']
    N=round(TL[-1]['end']*30);KEYS=[c['key'] for c in TL]
# ---------------------------------------------------------------- text helpers
def tw(d,t,f):return d.textlength(t,font=f)
def wrap(d,text,font,maxw):
    if tw(d,text,font)<=maxw:return [text]
    best=None
    for k in range(1,len(text)):
        l1,l2=text[:k],text[k:];w1,w2=tw(d,l1,font),tw(d,l2,font)
        if w1>maxw or w2>maxw or _nobreak(text[k-1],text[k]):continue
        score=max(w1,w2)+(400 if ('゠'<=text[k-1]<='ヿ' and '゠'<=text[k]<='ヿ') else 0)+(0 if text[k-1] in '、，。' else (70 if text[k-1] in 'はがをにのでとも' and not ('\u4e00'<=text[k]<='\u9fff' and '\u4e00'<=text[k-1]<='\u9fff') else 150))
        if best is None or score<best[0]:best=(score,[l1,l2])
    if best:return best[1]
    lines=[];cur=''
    for ch in text:
        if tw(d,cur+ch,font)>maxw and cur:lines.append(cur);cur=ch
        else:cur+=ch
    lines.append(cur);return lines
_UNIT='分秒時間年月日倍％度回世紀万千円人歳'
def _nobreak(a,b):
    """True if a line break between characters a|b is not allowed (digits, units, opening/closing brackets)"""
    return (a.isdigit() and (b.isdigit() or b in _UNIT or b in '.:：点')) or (a in '.:：点' and b.isdigit()) or a in '（「『(' or b in '）」』、。,)'
def wrapn(d,text,font,maxw):
    """wrap to any number of lines: greedy, backtracking to the last allowed break position"""
    out=[];cur=''
    for ch in text:
        if tw(d,cur+ch,font)>maxw and cur:
            k=len(cur)
            while k>0 and _nobreak(cur[k-1],cur[k] if k<len(cur) else ch):k-=1
            if k==0:k=len(cur)
            out.append(cur[:k]);cur=cur[k:]+ch
        else:cur+=ch
    if cur:out.append(cur)
    return out
def ease(x):x=min(1,max(0,x));return x*x*(3-2*x)
def line_text(d,xy,text,font,fill=WHITE,a=1.0):d.text(xy,text,font=font,fill=tuple(fill[:3])+(int(255*a),))
def box_fill(d,box,a,col=EDGE,w=2,fill=BG):
    d.rounded_rectangle(box,12,fill=tuple(fill[:3])+(int(fill[3]*a) if len(fill)>3 else int(255*a),),outline=tuple(col[:3])+(int(255*a),),width=w)
def text_block(d,x,y,text,size,maxw,col=WHITE,a=1.0,fam='sans',lh=1.3):
    f=(F if fam=='sans' else FB)[size];ls=wrapn(d,text,f,maxw)
    for l in ls:line_text(d,(x,y),l,f,col,a);y+=int(size*lh)
    return y
def measure(d,text,size,maxw,fam='sans',lh=1.3):
    f=(F if fam=='sans' else FB)[size];return len(wrapn(d,text,f,maxw))*int(size*lh)
class Ctx:
    def __init__(s,ci,t):
        s.ci=ci;s.t=t;s.key=KEYS[ci];s.segl=[x for x in SEGS if x['scene']==ci];s.st=[x['start'] for x in s.segl]
    def on(s,i):return i is None or (i<len(s.st) and s.t>=s.st[i])
    def a(s,i,dur=.5):
        if i is None:return 1.0
        return 0.0 if not s.on(i) else min(1,(s.t-s.st[i])/dur)
    def idx(s):return sum(1 for x in s.st if s.t>=x)-1
    def vis(s,it):
        at=it.get('at');un=it.get('until')
        return s.on(at) and not (un is not None and s.on(un))
# ---------------------------------------------------------------- images
_IMG={}
def get_img(name,w,h):
    k=(name,w,h)
    if k not in _IMG:
        meta=SPEC['images'][name];im=Image.open(P(meta['file'])).convert('RGB');c=meta.get('crop')
        if c:im=im.crop((int(im.width*c[0]),int(im.height*c[1]),int(im.width*c[2]),int(im.height*c[3])))
        s=min(w/im.width,h/im.height);_IMG[k]=im.resize((max(1,int(im.width*s)),max(1,int(im.height*s))),Image.LANCZOS)
    return _IMG[k]
def it_image(im,d,cx,it):
    a=cx.a(it.get('at'))
    if a<=0 or not cx.vis(it):return
    x0,y0,x1,y1=it['box'];cap=it.get('cap','');capn=len(wrapn(d,cap,F[26],x1-x0-28)[:2]) if cap else 0;reserve=(capn*34+16) if cap else 8
    pic=get_img(it['name'],x1-x0-16,y1-y0-reserve-8);W_,H_=pic.size;layer=Image.new('RGBA',(x1-x0,y1-y0),(0,0,0,0));ld=ImageDraw.Draw(layer)
    ld.rounded_rectangle((0,0,x1-x0-1,y1-y0-1),12,fill=BG,outline=EDGE+(255,),width=2);layer.paste(pic,((x1-x0-W_)//2,8))
    for j,l in enumerate(wrapn(d,cap,F[26],x1-x0-28)[:2]):ld.text((14,y1-y0-reserve+8+j*34),l,font=F[26],fill=WHITE+(255,))
    if a<1:r,g,b,al=layer.split();layer=Image.merge('RGBA',(r,g,b,al.point(lambda v:int(v*a))))
    im.alpha_composite(layer,(x0,y0))
# ---------------------------------------------------------------- item renderers
def it_stack(im,d,cx,it):
    x0,x1,y=it.get('x0',60),it.get('x1',930),it.get('y0',170);size=it.get('size',34);gap=it.get('gap',14);ymax=it.get('ymax',850)
    for e in it['items']:
        if not cx.vis(e):continue
        a=cx.a(e.get('at'));col=COL.get(e.get('col','white'),WHITE);hi=e.get('hi',False);title=e.get('title')
        th=(size+16) if title else 0;bh=measure(d,e['text'],size,x1-x0-52)+30+th
        assert y+bh<=ymax,f'stack overflow in {cx.key}: {e["text"][:20]}'
        box_fill(d,(x0,y,x1,y+bh),a,col=GOLD if hi else EDGE,w=3 if hi else 2)
        yy=y+14
        if title:line_text(d,(x0+24,yy),title,FB[size-4],GOLD,a);yy+=size+16
        text_block(d,x0+26,yy,e['text'],size,x1-x0-52,GOLD if hi else col,a);y+=bh+gap
def it_panel(im,d,cx,it):
    if not cx.vis(it):return
    a=cx.a(it.get('at'));x0,y0,x1,y1=it['box'];size=it.get('size',40);col=COL.get(it.get('col','white'),WHITE);title=it.get('title');fam=it.get('fam','sans')
    box_fill(d,(x0,y0,x1,y1),a,col=GOLD if it.get('hi') else EDGE,w=3 if it.get('hi') else 2);yy=y0+14
    if title:line_text(d,(x0+22,yy),title,FB[34],GOLD,a);yy+=48
    need=measure(d,it['text'],size,x1-x0-48,fam);assert yy+need<=y1+4,f'panel overflow in {cx.key}: {it["text"][:20]} need {yy+need-y1}'
    text_block(d,x0+24,yy,it['text'],size,x1-x0-48,col,a,fam)
def it_timeline(im,d,cx,it):
    y=it.get('y',430);x0=it.get('x0',160);x1=it.get('x1',1760);w=it.get('w',400);size=it.get('size',36);ymax=it.get('ymax',850)
    if not any(cx.vis(n) for n in it['nodes']):return
    d.line([(x0,y),(x1,y)],fill=EDGE+(255,),width=5)
    for n in it['nodes']:
        if not cx.vis(n):continue
        a=cx.a(n.get('at'));x=n['x'];col=COL.get(n.get('col','org'),ORG)
        d.ellipse((x-14,y-14,x+14,y+14),fill=tuple(col)+(int(255*a),),outline=WHITE+(int(255*a),),width=3)
        line_text(d,(x-w/2,y+28),n['label'],F[40],WHITE,a);yy=y+80
        for l in wrapn(d,n.get('sub',''),F[size],w):line_text(d,(x-w/2,yy),l,F[size],(215,224,226),a);yy+=int(size*1.28)
        assert yy<=ymax,f'timeline overflow in {cx.key}: {n["label"]}'
def it_chips(im,d,cx,it):
    n=len(it['items']);w=it.get('w',480);h=it.get('h',150);y=it.get('y',230);gap=it.get('gap',60);tot=n*w+(n-1)*gap;x=(1920-tot)//2;size=it.get('size',72)
    for k,e in enumerate(it['items']):
        if cx.vis(e):
            a=cx.a(e.get('at'));xx=x+k*(w+gap);d.rounded_rectangle((xx,y,xx+w,y+h),14,outline=GOLD+(int(255*a),),width=3,fill=(12,34,50,int(255*a)))
            f=FB[size]
            while tw(d,e['text'],f)>w-30 and size>30:size-=4;f=FB[size]
            line_text(d,(xx+(w-tw(d,e['text'],f))/2,y+(h-size*1.25)/2),e['text'],f,WHITE,a)
def it_big(im,d,cx,it):
    if not cx.vis(it):return
    a=cx.a(it.get('at'));size=it.get('size',56);col=COL.get(it.get('col','white'),WHITE);x0=it.get('x0',120);x1=it.get('x1',1800);fam=it.get('fam','serif')
    text_block(d,x0,it.get('y',400),it['text'],size,x1-x0,col,a,fam)
def it_bars(im,d,cx,it):
    x0,y0,x1,y1=it['box'];title=it.get('title');unit=it.get('unit','');data=it['data'];mx=it.get('max') or max(e['value'] for e in data)
    vis_any=any(cx.vis(e) for e in data)
    if not vis_any:return
    box_fill(d,(x0,y0,x1,y1),1.0);yy=y0+12
    if title:line_text(d,(x0+22,yy),title,FB[34],GOLD,1.0);yy+=52
    rh=min(70,(y1-yy-14)//len(data));lab_w=it.get('lab_w',300);bw=x1-x0-lab_w-220
    for k,e in enumerate(data):
        if not cx.vis(e):continue
        a=cx.a(e.get('at'));ry=yy+k*rh;col=COL.get(e.get('col','org'),ORG)
        line_text(d,(x0+22,ry+4),e['label'],F[32],WHITE,a);L=int(bw*min(1,e['value']/mx)*ease(a*1.6))
        d.rounded_rectangle((x0+lab_w,ry+6,x0+lab_w+max(4,L),ry+rh-12),6,fill=tuple(col)+(int(235*a),))
        line_text(d,(x0+lab_w+L+14,ry+4),e.get('vlabel',f"{e['value']:,}{unit}"),F[32],WHITE,a)
def it_table(im,d,cx,it):
    x0,y0,x1,y1=it['box'];cols=it['cols'];rows=it['rows'];size=it.get('size',32);cw=it.get('colw') or [ (x1-x0-40)/len(cols) ]*len(cols)
    if not any(cx.vis(r) for r in rows):return
    box_fill(d,(x0,y0,x1,y1),1.0);x=x0+20
    for c,w in zip(cols,cw):line_text(d,(x,y0+12),c,F[size],GOLD,1.0);x+=w
    d.line([(x0+16,y0+12+size+14),(x1-16,y0+12+size+14)],fill=EDGE+(255,),width=2);yy=y0+12+size+26
    for r in rows:
        if not cx.vis(r):continue
        a=cx.a(r.get('at'));x=x0+20;hmax=0
        for cell,w in zip(r['cells'],cw):
            ls=wrapn(d,str(cell),F[size],w-16)
            for j,l in enumerate(ls):line_text(d,(x,yy+j*int(size*1.25)),l,F[size],COL.get(r.get('col','white'),WHITE),a)
            hmax=max(hmax,len(ls)*int(size*1.25));x+=w
        yy+=hmax+14;assert yy<=y1+4,f'table overflow in {cx.key}'
def it_cols2(im,d,cx,it):
    for side,(bx0,bx1) in (('left',(it.get('x0',60),it.get('xm',940))),('right',(it.get('xm2',980),it.get('x1',1860)))):
        sp=it.get(side)
        if not sp:continue
        e=dict(t='stack',x0=bx0,x1=bx1,y0=sp.get('y0',170),size=it.get('size',34),items=sp['items'],gap=12)
        if sp.get('title') and cx.on(sp.get('title_at')):
            box_fill(d,(bx0,170,bx1,250),cx.a(sp.get('title_at')),col=GOLD,w=3);line_text(d,(bx0+22,180),sp['title'],FB[40],GOLD,cx.a(sp.get('title_at')));e['y0']=266
        it_stack(im,d,cx,e)
def it_flow(im,d,cx,it):
    nodes=it['nodes'];n=len(nodes);y=it.get('y',400);h=it.get('h',140);gap=60;w=(1800-(n-1)*gap)//n;x=60;size=it.get('size',34)
    for k,e in enumerate(nodes):
        xx=x+k*(w+gap)
        if cx.vis(e):
            a=cx.a(e.get('at'));box_fill(d,(xx,y,xx+w,y+h),a,col=GOLD if e.get('hi') else EDGE,w=3 if e.get('hi') else 2)
            ls=wrapn(d,e['text'],F[size],w-30);yy=y+(h-len(ls)*int(size*1.25))/2
            for l in ls:line_text(d,(xx+(w-tw(d,l,F[size]))/2,yy),l,F[size],WHITE,a);yy+=int(size*1.25)
            if k<n-1:d.polygon([(xx+w+12,y+h/2-14),(xx+w+gap-12,y+h/2),(xx+w+12,y+h/2+14)],fill=GOLD+(int(255*a),))
def it_daybar(im,d,cx,it):
    """1-day bar (0-24h): day part (mk..bk minutes) split into 6, night part split into 6. rows: [{label,mk,bk,at}]"""
    x0=it.get('x0',150);x1=it.get('x1',1770);y=it.get('y',230);rh=it.get('rh',190);bh=it.get('bh',64)
    X=lambda m:x0+(x1-x0)*m/1440
    if any(cx.vis(r) for r in it['rows']):
        for h in range(0,25,3):
            xx=X(h*60);d.line([(xx,y-52),(xx,y+max(k for k,r in enumerate(it['rows']) if cx.vis(r))*rh+bh)],fill=(70,90,110,255),width=1);tl=f'{h}時';line_text(d,(xx-tw(d,tl,F[26])/2,y-88),tl,F[26],DIM,1.0)
    for k,r in enumerate(it['rows']):
        if not cx.vis(r):continue
        a=cx.a(r.get('at'));yy=y+k*rh;mk,bk=r['mk'],r['bk'];dk=(bk-mk)/6;nk=(1440-(bk-mk))/6
        line_text(d,(x0,yy-44),r['label'],F[34],WHITE,a)
        d.rectangle((X(0),yy,X(1440),yy+bh),fill=(26,54,92,int(255*a)))
        d.rectangle((X(mk),yy,X(bk),yy+bh),fill=(206,164,78,int(235*a)))
        for q in range(7):
            xx=X(mk+q*dk);d.line([(xx,yy),(xx,yy+bh)],fill=(30,24,10,int(255*a)),width=2)
        for q in range(7):
            m=(bk+q*nk)%1440;xx=X(m);d.line([(xx,yy),(xx,yy+bh)],fill=(150,185,235,int(255*a)),width=2)
        dtxt=r.get('dlabel',f'昼の一刻 {int(dk//60)}時間{int(dk%60+0.5)}分');ntxt=r.get('nlabel',f'夜の一刻 {int(nk//60)}時間{int(nk%60+0.5)}分')
        if cx.on(r.get('dat')):line_text(d,(X(mk)+(X(bk)-X(mk))/2-tw(d,dtxt,F[32])/2,yy+bh+10),dtxt,F[32],GOLD,cx.a(r.get('dat')))
        if cx.on(r.get('nat')):
            nx=X(bk)+(X(1440)-X(bk))/2;w_=tw(d,ntxt,F[32]);line_text(d,(max(X(bk)+6,min(nx-w_/2,x1-w_)),yy+bh+10),ntxt,F[32],BLUE,cx.a(r.get('nat')))
def it_line(im,d,cx,it):
    """line chart: x labels, one series; points appear one by one by sentence index. series=[{label,value,at}], y range ymin..ymax, unit"""
    x0,y0,x1,y1=it['box'];ser=it['series'];ymin=it.get('ymin',0);ymax=it.get('ymax',30);unit=it.get('unit','％');title=it.get('title')
    if not any(cx.vis(s) for s in ser):return
    box_fill(d,(x0,y0,x1,y1),1.0);yy=y0+10
    if title:line_text(d,(x0+22,yy),title,FB[32],GOLD,1.0);yy+=48
    px0,px1,py0,py1=x0+150,x1-90,yy+50,y1-70
    for g in range(0,int(ymax)+1,10):
        gy=py1-(py1-py0)*(g-ymin)/(ymax-ymin);d.line([(px0,gy),(px1,gy)],fill=(60,80,100,255),width=1);line_text(d,(x0+20,gy-16),f'{g}{unit}',F[26],DIM,1.0)
    n=len(ser);pts=[]
    for k,s in enumerate(ser):
        y0_,y1_=ser[0].get('year',0),ser[-1].get('year',n-1);yr=s.get('year',k);X=px0+(px1-px0)*(yr-y0_)/max(1,(y1_-y0_));Y=py1-(py1-py0)*(s['value']-ymin)/(ymax-ymin);pts.append((X,Y))
        line_text(d,(X-tw(d,s['label'],F[26])/2,py1+12),s['label'],F[26],DIM,1.0)
    for k,s in enumerate(ser):
        if not cx.vis(s):continue
        a=cx.a(s.get('at'));X,Y=pts[k];col=COL.get(s.get('col','org'),ORG)
        if k>0 and cx.vis(ser[k-1]):d.line([pts[k-1],(X,Y)],fill=tuple(col)+(int(255*a),),width=5)
        d.ellipse((X-9,Y-9,X+9,Y+9),fill=tuple(col)+(int(255*a),),outline=WHITE+(int(255*a),),width=2)
        if s.get('show',True):
            v=s.get('vlabel',f"{s['value']}{unit}");line_text(d,(X-tw(d,v,F[30])/2,Y-48),v,F[30],WHITE,a)
def it_swirl(im,d,cx,it):
    """concept sketch of a swirl seen from above: dir 'ccw'|'cw' (as seen on screen), centre (x,y), radius r, label under it"""
    if not cx.vis(it):return
    a=cx.a(it.get('at'));x,y=it['c'];R=it.get('r',150);ccw=it.get('dir','ccw')=='ccw';col=COL.get(it.get('col','blue'),BLUE);turns=2.2;n=160;pts=[]
    for k in range(n+1):
        u=k/n;th=(turns*2*math.pi*u)*(1 if ccw else -1)+it.get('phase',0);r=R*(1-0.88*u);pts.append((x+r*math.cos(th),y-r*math.sin(th)))
    d.line(pts,fill=tuple(col)+(int(255*a),),width=7,joint='curve')
    (x1_,y1_),(x2_,y2_)=pts[-6],pts[-1];ang=math.atan2(y2_-y1_,x2_-x1_);hl=26
    d.polygon([(x2_,y2_),(x2_-hl*math.cos(ang-0.5),y2_-hl*math.sin(ang-0.5)),(x2_-hl*math.cos(ang+0.5),y2_-hl*math.sin(ang+0.5))],fill=tuple(col)+(int(255*a),))
    d.ellipse((x-R-14,y-R-14,x+R+14,y+R+14),outline=EDGE+(int(120*a),),width=2)
    lab=it.get('label','');f=F[it.get('lsize',34)];yy=y+R+26
    for l in wrapn(d,lab,f,it.get('lw',520)):line_text(d,(x-tw(d,l,f)/2,yy),l,f,WHITE,a);yy+=int(it.get('lsize',34)*1.3)
_ART={}
def it_art(im,d,cx,it):
    """生成イラストを、箱いっぱいに敷く（ゆっくり拡大・移動）。spec: dict(t='art',name='<images のキー>',box=[...],at=N,until=M,dim=0.7)"""
    if not cx.vis(it):return
    a=cx.a(it.get('at'),.8)
    if a<=0:return
    x0,y0,x1,y1=it['box'];w,h=x1-x0,y1-y0;name=it['name']
    if name not in _ART:
        src=Image.open(P(SPEC['images'][name]['file'])).convert('RGB');sc=max(w/src.width,h/src.height)*1.14
        base=src.resize((int(src.width*sc)+1,int(src.height*sc)+1),Image.BILINEAR);_ART[name]=base
    base=_ART[name];prog=min(1.0,max(0.0,cx.t/ max(8.0,it.get('drift',30.0))))
    ox=int((base.width-w)*(0.15+0.7*prog)*it.get('dir',1)) if it.get('dir',1)>0 else int((base.width-w)*(0.85-0.7*prog))
    oy=int((base.height-h)*0.5)
    crop=base.crop((ox,oy,ox+w,oy+h)).convert('RGBA');dim=it.get('dim',0.7)
    crop=Image.blend(crop,Image.new('RGBA',crop.size,(5,16,26,255)),1-dim)
    mask=Image.new('L',(w,h),0);ImageDraw.Draw(mask).rounded_rectangle((0,0,w-1,h-1),18,fill=int(255*a))
    layer=Image.new('RGBA',(w,h),(0,0,0,0));layer.paste(crop,(0,0),mask);im.alpha_composite(layer,(x0,y0))
    if it.get('note'):
        f=F[it.get('note_size',24)];tw_=int(d.textlength(it['note'],font=f));ln=ImageDraw.Draw(im,'RGBA');nx=x1-tw_-34;ny=y1-(36+it.get('note_size',24))
        ln.rounded_rectangle((nx-12,ny-6,x1-14,ny+34),10,fill=(5,16,26,int(215*a)));ln.text((nx,ny),it['note'],font=f,fill=(215,224,226,int(255*a)))
def it_shade(im,d,cx,it):
    """暗い下地（文字を読みやすくする）。spec: dict(t='shade',box=[...],at=N,until=M,alpha=0.8)"""
    if not cx.vis(it):return
    a=cx.a(it.get('at'),.5)
    if a<=0:return
    x0,y0,x1,y1=it['box'];lay=Image.new('RGBA',(x1-x0,y1-y0),(0,0,0,0));ImageDraw.Draw(lay).rounded_rectangle((0,0,x1-x0-1,y1-y0-1),16,fill=(6,18,29,int(255*it.get('alpha',0.8)*a)));im.alpha_composite(lay,(x0,y0))
_ANIM_BOUND=[False]
def it_anim(im,d,cx,it):
    """自作アニメーション部品（scripts/vp_anim.py）。spec: dict(t='anim',name='...',box=[...],at=N,until=M,...)"""
    if not cx.vis(it):return
    a=cx.a(it.get('at'))
    if a<=0:return
    import vp_anim
    if not _ANIM_BOUND[0]:vp_anim.bind(globals());_ANIM_BOUND[0]=True
    vp_anim.DRAW[it['name']](im,d,cx,it,a)
ITEMS=dict(shade=it_shade,art=it_art,anim=it_anim,swirl=it_swirl,line=it_line,daybar=it_daybar,stack=it_stack,panel=it_panel,image=it_image,timeline=it_timeline,chips=it_chips,big=it_big,bars=it_bars,table=it_table,cols2=it_cols2,flow=it_flow)
def opener(im,d,cx):
    ch=SPEC['chapters'][cx.ci];un=ch.get('opener_until',0)
    if cx.idx()>=un:return
    a=cx.a(0,0.4) if cx.idx()>=0 else 1.0;txt=ch.get('opener',ch.get('chapter_title',''));f=FB[64];ls=wrapn(d,txt,f,1500);h=len(ls)*int(64*1.35);y=ch.get('opener_y',520)-h//2
    box_fill(d,(160,y-30,1760,y+h+22),a,col=GOLD,w=3)
    for l in ls:line_text(d,((1920-tw(d,l,f))/2,y),l,f,GOLD,a);y+=int(64*1.35)
def render_scene(im,d,cx):
    opener(im,d,cx)
    for it in SPEC['chapters'][cx.ci]['scene']:
        ITEMS[it['t']](im,d,cx,it) if it['t']!='image' else it_image(im,d,cx,it)
        d=ImageDraw.Draw(im,'RGBA')
def header(d,ci):
    d.text((48,16),SPEC['chapters'][ci].get('title',''),font=FB[60],fill=WHITE,stroke_width=5,stroke_fill=(5,10,16));d.text((48,94),SPEC['header_sub'],font=F[28],fill=(200,210,214),stroke_width=4,stroke_fill=(5,10,16))
# ---------------------------------------------------------------- subtitles / frames
_SUBP={}
def sub_lines(d,seg,f,t):
    k=seg['start']
    if k not in _SUBP:
        txt=display(seg['text']);ls=wrap(d,txt,f,1720)
        if len(ls)<=2:_SUBP[k]=[(ls,seg['start'],seg['end'])]
        else:
            allw=wrapn(d,txt,f,1720);pages=[allw[i:i+2] for i in range(0,len(allw),2)];tot=sum(len(''.join(p)) for p in pages);cum=0;out=[]
            for p in pages:
                n=len(''.join(p));out.append((p,seg['start']+(seg['end']-seg['start'])*cum/tot,seg['start']+(seg['end']-seg['start'])*(cum+n)/tot));cum+=n
            _SUBP[k]=out
    for ls,s0,s1 in _SUBP[k]:
        if t<s1:return ls
    return _SUBP[k][-1][0]
def render_frame(i):
    t=i/30;ci=next(k for k,c in enumerate(TL) if t<c['end']+1e-9);cx=Ctx(ci,t)
    im=Image.new('RGBA',(1920,1080),NAVY+(255,));d=ImageDraw.Draw(im,'RGBA')
    header(d,ci);render_scene(im,d,cx);d=ImageDraw.Draw(im,'RGBA')
    active=next((x for x in cx.segl if x['start']<=t<x['end']),None)
    if active:
        f=FSUB[46];lines=sub_lines(d,active,f,t);d.rounded_rectangle((60,860,1860,1008),12,fill=(5,18,29,242))
        for j,txt in enumerate(lines):
            w=tw(d,txt,f);assert w<1760;d.text(((1920-w)/2,872+j*62),txt,font=f,fill='#fffcef')
    d.rectangle((48,1012,48+1824*(i+1)/N,1018),fill=(201,173,112));return im
def render_part(a,b):
    stills=[int(x) for x in os.environ['STILLS'].split(',')] if os.environ.get('STILLS') else None
    out=P(f'cache/{SLUG}_part_{a}_{b}.mp4');(P('logs')).mkdir(exist_ok=True);log=P(f'logs/{SLUG}_enc_{a}.log').open('wb')
    class _P:
        class stdin:
            write=staticmethod(lambda b:None);close=staticmethod(lambda:None)
        def wait(self):pass
        returncode=0
    proc=_P() if stills else subprocess.Popen(['ffmpeg','-y','-v','warning','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','30','-i','pipe:0','-an','-c:v','h264_nvenc','-preset','p4','-cq','19','-b:v','0','-pix_fmt','yuv420p',str(out)],stdin=subprocess.PIPE,stderr=log)
    try:
        for i in (stills or range(a,min(b,N))):
            im=render_frame(i);proc.stdin.write(im.convert('RGB').tobytes())
            if stills:im.convert('RGB').save(P(f'cache/{SLUG}_still_{i}.png'))
    finally:
        proc.stdin.close();proc.wait();log.close()
    assert proc.returncode==0
# ---------------------------------------------------------------- stages
def stage_story():
    t=(theme_dir()/'09_script_v2.md').read_text(encoding='utf8');chs=re.split(r'\n## ',t)[1:];scenes=[];keys=[c['key'] for c in SPEC['chapters']]
    for c in chs:
        head=c.split('\n')[0];m=re.match(r'章(\d+)　(.*)',head)
        if not m:continue
        n=int(m.group(1));lines=[re.sub(r'〔[^〕]*〕','',re.sub(r'^\d+\. ','',l)).strip() for l in c.split('\n') if re.match(r'^\d+\. ',l)]
        scenes.append(dict(id=n-1,key=keys[n-1],title=m.group(2),narration=''.join(lines)))
    assert len(scenes)==len(keys),f'{len(scenes)} chapters in script vs {len(keys)} in spec'
    P(f'data/{SLUG}_scenes.json').write_text(json.dumps(scenes,ensure_ascii=False,indent=1),encoding='utf8')
    pr=P(f'data/{SLUG}_pronunciations.json')
    if not pr.exists():pr.write_text('{}',encoding='utf8')
    n=sum(len(s['narration']) for s in scenes);print(len(scenes),'scenes',n,'chars  est. minutes',round(n/290,1))
def _vv():
    import requests
    sp=requests.get(BASE+'/speakers',timeout=60).json();speaker=next(x for x in sp if x['name']=='四国めたん');style=next(x['id'] for x in speaker['styles'] if x['name']=='ノーマル');return requests,speaker,style
def sentences(sc):return [x.strip()+'。' for x in sc['narration'].split('。') if x.strip()]
def stage_kana():
    requests,spk,style=_vv();dic=json.loads(P(f'data/{SLUG}_pronunciations.json').read_text(encoding='utf8'));out=[]
    for s in json.loads(P(f'data/{SLUG}_scenes.json').read_text(encoding='utf8')):
        for x in sentences(s):
            sp_=x
            for k,v in sorted(dic.items(),key=lambda z:-len(z[0])):sp_=sp_.replace(k,v)
            q=requests.post(BASE+'/audio_query',params={'text':sp_,'speaker':style},timeout=60).json();out.append(f"[{s['key']}] {x}\n    {q['kana']}")
    P(f'out/{SLUG}_kana.txt').write_text('\n'.join(out),encoding='utf8');print(len(out),'sentences ->',f'out/{SLUG}_kana.txt')
def readwav(p):
    with wave.open(str(p),'rb') as w:return np.frombuffer(w.readframes(w.getnframes()),np.int16),w.getframerate()
def writewav(p,a,rate):
    with wave.open(str(p),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(a.astype(np.int16).tobytes())
def stage_audio():
    requests,speaker,style=_vv();folder=P(f'cache/{SLUG}_audio');folder.mkdir(exist_ok=True,parents=True)
    dic=json.loads(P(f'data/{SLUG}_pronunciations.json').read_text(encoding='utf8'));scenes=json.loads(P(f'data/{SLUG}_scenes.json').read_text(encoding='utf8'))
    segs=[];timeline=[];cursor=0;allpcm=[];rate=24000
    for sc in scenes:
        local=[];t=0
        for i,text in enumerate(sentences(sc)):
            spoken=text
            for k,v in sorted(dic.items(),key=lambda x:-len(x[0])):spoken=spoken.replace(k,v)
            p=folder/f'{sc["id"]:02}_{i:02}.wav';key=hashlib.sha256((spoken+f'|{SPEED}|1.08|'+str(style)).encode()).hexdigest();meta=p.with_suffix('.json')
            if not p.exists() or not meta.exists() or json.loads(meta.read_text())['key']!=key:
                q=requests.post(BASE+'/audio_query',params={'text':spoken,'speaker':style},timeout=120).json();q.update(speedScale=SPEED,intonationScale=1.08,prePhonemeLength=.15,postPhonemeLength=.35,outputSamplingRate=24000)
                r=requests.post(BASE+'/synthesis',params={'speaker':style},json=q,timeout=180);r.raise_for_status();p.write_bytes(r.content);meta.write_text(json.dumps({'key':key}),encoding='utf8')
            pcm,rate=readwav(p);dur=len(pcm)/rate;rms=float(np.sqrt(np.mean((pcm.astype(float)/32768)**2)));peak=float(np.abs(pcm).max()/32768)
            assert dur>.4 and rms>.003 and peak<.999,(sc['key'],i,dur,rms,peak)
            segs.append(dict(scene=sc['id'],text=text,spoken=spoken,start=round(cursor+t,4),end=round(cursor+t+dur,4),duration=dur,rms=rms,peak=peak));local.append(pcm);t+=dur
        sd=math.ceil((t+1.6)*30)/30;j=np.concatenate(local);j=np.pad(j,(0,round(sd*rate)-len(j)));allpcm.append(j)
        timeline.append({**sc,'start':cursor,'duration':sd,'end':cursor+sd});cursor+=sd
    writewav(P(f'out/{SLUG}_narration.wav'),np.concatenate(allpcm),rate)
    st=lambda t:(lambda ms:f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}')(round(t*1000))
    P(f'out/{SLUG}_subtitles.srt').write_text('\n\n'.join(f'{i+1}\n{st(x["start"])} --> {st(x["end"])}\n{display(x["text"])}' for i,x in enumerate(segs))+'\n',encoding='utf8')
    P(f'data/{SLUG}_timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=1),encoding='utf8')
    P(f'out/{SLUG}_audio_report.json').write_text(json.dumps(dict(engine=requests.get(BASE+'/version').json(),speaker='VOICEVOX:四国めたん',style=style,segments=segs,total_seconds=cursor,all_lines_voiced=True,semantic_asr_verified=False),ensure_ascii=False,indent=1),encoding='utf8')
    print('total',round(cursor,1),'s',int(cursor//60),'min',int(cursor%60),'s')
def stage_bgm():
    SR=48000;D=P('assets/bgm_maou');tl=json.loads(P(f'data/{SLUG}_timeline.json').read_text(encoding='utf8'));T={c['key']:c for c in tl};TOTAL=tl[-1]['end'];XF=3.0;TARGET=-24.0
    def load_(name):
        f=str(D/f'maou_bgm_{name}.mp3');raw=subprocess.run(['ffmpeg','-v','error','-i',f,'-ar',str(SR),'-ac','2','-f','f32le','-'],capture_output=True).stdout
        x=np.frombuffer(raw,np.float32).reshape(-1,2).T.astype(np.float64)
        r=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',f,'-af','ebur128','-f','null','-'],capture_output=True,text=True,encoding='utf8',errors='replace').stderr
        lufs=float(r.split('Integrated loudness:')[1].split('I:')[1].split('LUFS')[0]);return x*10**((TARGET-lufs)/20)
    fade=lambda n,k:(lambda u:np.sin(u*np.pi/2) if k=='in' else np.cos(u*np.pi/2))(np.linspace(0,1,n))
    def fill(x,length):
        xf=int(XF*SR);out=x.copy()
        while out.shape[1]<length:
            a,b=out,x;out=np.concatenate([a[:,:-xf],a[:,-xf:]*fade(xf,'out')+b[:,:xf]*fade(xf,'in'),b[:,xf:]],axis=1)
        return out[:,:length]
    n_=int(TOTAL*SR);mix=np.zeros((2,n_));cache={}
    for a,b,name in SPEC['bgm']:
        s=T[a]['start'];e=T[b]['end'];s0=max(0,s-XF/2);e0=min(TOTAL,e+XF/2);n=int((e0-s0)*SR)
        if name not in cache:cache[name]=load_(name)
        seg=fill(cache[name],n).copy();fi=int(XF*SR) if s0>0 else 0;fo=int(XF*SR) if e0<TOTAL else 0
        if fi:seg[:,:fi]*=fade(fi,'in')
        if fo:seg[:,-fo:]*=fade(fo,'out')
        i=int(s0*SR);mix[:,i:i+n]+=seg[:,:n_-i]
    fi=int(2*SR);fo=int(6*SR);env=np.ones(n_);env[:fi]=np.linspace(0,1,fi);env[-fo:]=np.minimum(env[-fo:],np.linspace(1,0,fo)**1.5);mix*=env;pk=np.abs(mix).max()
    if pk>.9:mix*=.9/pk
    with wave.open(str(P(f'out/{SLUG}_bgm.wav')),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes((mix.T*32767).astype(np.int16).tobytes())
    print('bgm ok',round(TOTAL,1),'s')
def loud_args(path):
    r=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',str(path),'-af','loudnorm=I=-15:TP=-1.5:LRA=9:print_format=json','-f','null','-'],capture_output=True,text=True)
    j=json.loads(re.search(r'\{[^{}]*"input_i"[^{}]*\}',r.stderr,re.S).group(0))
    return f"loudnorm=I=-15:TP=-1.5:LRA=9:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true",j
def stage_build(chunk=2000,bgm_db=-6.0):
    load_runtime()
    for f in P('cache').glob(f'{SLUG}_part_*.mp4'):f.unlink()
    procs=[]
    for a in range(0,N,chunk):
        procs.append(subprocess.Popen([sys.executable,str(Path(__file__)),SLUG,'part',str(a),str(a+chunk)],cwd=str(ROOT),env={**os.environ,'PYTHONIOENCODING':'utf8'}))
    rc=[p.wait() for p in procs];assert all(r==0 for r in rc),f'part render failed {rc}'
    parts=sorted(P('cache').glob(f'{SLUG}_part_*.mp4'),key=lambda p:int(p.stem.split('_')[2]));lst=P(f'cache/{SLUG}_parts.txt');lst.write_text(''.join(f"file '{p.as_posix()}'\n" for p in parts))
    wav=P(f'out/{SLUG}_narration.wav');nob=P(f'out/{SLUG}_video_nobgm.mp4');af,j=loud_args(wav)
    subprocess.run(['ffmpeg','-y','-v','warning','-f','concat','-safe','0','-i',str(lst),'-i',str(wav),'-map','0:v','-map','1:a','-c:v','h264_nvenc','-preset','p5','-cq','25','-b:v','0','-pix_fmt','yuv420p','-af',af,'-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart','-shortest',str(nob)],check=True)
    mix=P(f'cache/{SLUG}_mix.wav');bgm=P(f'out/{SLUG}_bgm.wav')
    fc=f"[0:a]aresample=48000,pan=stereo|c0=c0|c1=c0,asplit=2[n1][n2];[1:a]volume={bgm_db}dB[bg];[bg][n2]sidechaincompress=threshold=0.02:ratio=4:attack=30:release=900:makeup=1[duck];[n1][duck]amix=inputs=2:normalize=0:duration=first[m]"
    subprocess.run(['ffmpeg','-y','-v','warning','-i',str(wav),'-i',str(bgm),'-filter_complex',fc,'-map','[m]','-c:a','pcm_s16le',str(mix)],check=True)
    af2,j2=loud_args(mix);out=P(f'out/{SLUG}_video.mp4')
    subprocess.run(['ffmpeg','-y','-v','warning','-i',str(nob),'-i',str(mix),'-map','0:v','-map','1:a','-c:v','copy','-af',af2,'-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart','-shortest',str(out)],check=True)
    stage_qa()
def stage_qa():
    load_runtime();v=P(f'out/{SLUG}_video.mp4');r=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(v)],capture_output=True,text=True);dur=float(r.stdout.strip())
    assert abs(dur-TL[-1]['end'])<1.0,f'video {dur:.2f}s != timeline {TL[-1]["end"]:.2f}s'
    dec=subprocess.run(['ffmpeg','-v','error','-i',str(v),'-f','null','-'],capture_output=True,text=True);assert not dec.stderr.strip(),dec.stderr[:300]
    l=subprocess.run(['ffmpeg','-i',str(v),'-af','ebur128','-f','null','-'],capture_output=True,text=True,encoding='utf8',errors='replace').stderr
    lufs=float(l.split('Integrated loudness:')[1].split('I:')[1].split('LUFS')[0]);bd=subprocess.run(['ffmpeg','-i',str(v),'-vf','blackdetect=d=0.5:pix_th=0.04','-an','-f','null','-'],capture_output=True,text=True,encoding='utf8',errors='replace').stderr
    blk=re.findall(r'black_start:([\d.]+) black_end:([\d.]+)',bd);print(f'QA {SLUG}: {dur:.1f}s decode ok  {lufs:.1f} LUFS  black segments {blk}')
    # contact sheet: first sentence of every chapter + the last-but-one sentence
    pts=[]
    for c in TL:
        ss=[x for x in SEGS if x['scene']==c['id']];pts+= [ss[0]['start']+1.0, ss[len(ss)//2]['start']+1.0, ss[-1]['start']+1.0]
    d=P(f'out/{SLUG}_review');d.mkdir(exist_ok=True,parents=True)
    for k,t in enumerate(pts):subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{t:.2f}','-i',str(v),'-frames:v','1','-vf','scale=640:-1',str(d/f'f{k:02d}.png')])
    cols=3;rows=math.ceil(len(pts)/cols);per=12
    for s in range(0,len(pts),per):
        sub=list(range(s,min(s+per,len(pts))));W=Image.new('RGB',(1920,360*math.ceil(len(sub)/3)))
        for q,k in enumerate(sub):W.paste(Image.open(d/f'f{k:02d}.png'),((q%3)*640,(q//3)*360))
        W.save(d/f'sheet_{s//per}.png')
    print('contact sheets in',d)
def chapter_list():
    tl=json.loads(P(f'data/{SLUG}_timeline.json').read_text(encoding='utf8'));ts=lambda s:f'{int(s)//60}:{int(s)%60:02d}'
    return [f'{ts(c["start"])} {SPEC["chapters"][i].get("chapter_title",SPEC["chapters"][i].get("title",c["key"]))}' for i,c in enumerate(tl)],tl[-1]['end']
MAOU={'piano12':'ピアノ12','piano36':'ピアノ36','piano40':'ピアノ40','ethnic06':'民族06','ethnic26':'民族26','ethnic30':'民族30'}
def stage_desc():
    ds=SPEC['desc'];chapters,dur=chapter_list();used=sorted({it['name'] for ch in SPEC['chapters'] for it in ch['scene'] if it['t']=='image'})
    imglines=[f"・{SPEC['images'][n]['credit']}:{SPEC['images'][n]['source_url']}" for n in used if SPEC['images'][n].get('credit')]
    tracks=' / '.join(MAOU[x] for x in dict.fromkeys(b[2] for b in SPEC['bgm']))
    L=[f'# YouTube 投稿用ドラフト：{ds["title_main"]}\n','## タイトル案']+[f'{i+1}. {t}' for i,t in enumerate(ds['titles'])]+['','## 概要欄(そのまま貼り付け用)\n','```',ds['intro'],'','■ チャプター']+chapters+['','■ 動画で確かめたこと(要点)']+[f'・{p}' for p in ds['points']]+['','■ 参考資料(確認に使ったもの)']+[f'・{r}' for r in ds['refs']]+['','■ 出典・クレジット']+ds.get('credit_lines',[])+imglines+['・音声:VOICEVOX:四国めたん',f'・音楽:魔王魂(https://maou.audio/) {tracks}(作曲:森田交一。音量調整・場面に合わせた切り替えを行っています)','・図・表・年表:自作','','■ 注意']+[f'・{n}' for n in ds['notes']]+['・詳しい出典と素材のクレジットは、この概要欄にまとめています。','','■ このチャンネルについて','寄り道ラボは、ふと気になったことを、資料やデータで調べる解説チャンネルです。','```\n','## タグ案',ds['tags']+'\n','## 投稿前チェック(自分で確認が必要)']+[f'- [ ] {c}' for c in ds.get('checks',[])]+['- [ ] YouTubeの設問(AIの使用):完成動画の表現を公式基準と照合し、Studioの「AIの使用」を設定(サムネイル背景の生成画像・合成音声(VOICEVOX)を含めて、本物の人物・出来事と誤認させる表現がないか確認)','- [ ] **動画を通しで見る・聞く**(動き、ナレーションの読み、BGMの音量、画像の切り出しと説明の整合)','- [ ] 概要欄の外部リンクに必要な機能利用資格をStudioで確認し、公開後にリンクが開けるか確認する','- [ ] VOICEVOX:四国めたん / BGM(魔王魂)の最新規約',f'- [ ] 字幕:`out/{SLUG}_subtitles.srt` をアップロード(日本語)','- [ ] サムネイルを設定し、投稿後の表示(スマートフォンの小さな表示)を確認','']
    P(f'out/{SLUG}_description.md').write_text('\n'.join(L)+'\n',encoding='utf8');print('\n'.join(chapters),'\nduration',f'{int(dur//60)}分{int(dur%60)}秒')
def stage_thumb():
    th=SPEC['thumb'];W,H=1280,720;FDW='C:/Windows/Fonts/'
    def font(n):
        if n>=100:f=ImageFont.truetype(FDW+'NotoSerifJP-VF.ttf',n);f.set_variation_by_axes([900]);return f
        f=ImageFont.truetype(FDW+'NotoSansJP-VF.ttf',n);f.set_variation_by_axes([800]);return f
    def st(d,xy,text,f,fill,sw=10):d.text(xy,text,font=f,fill=fill,stroke_width=sw,stroke_fill=(6,10,18))
    if th.get('bg'):
        im=Image.open(P(th['bg'])).convert('RGBA');s=max(W/im.width,H/im.height);im=im.resize((int(im.width*s)+1,int(im.height*s)+1),Image.LANCZOS);x=(im.width-W)//2;y=(im.height-H)//2;im=im.crop((x,y,x+W,y+H))
        sh=Image.new('RGBA',(W,H),(4,10,20,255));g=Image.new('L',(W,1));px=g.load()
        for xx in range(W):px[xx,0]=int(235*max(0,min(1,(th.get('shade_x',760)-xx)/th.get('shade_w',560))))
        sh.putalpha(g.resize((W,H)));im.alpha_composite(sh)
    else:
        im=Image.new('RGBA',(W,H),NAVY+(255,));meta=SPEC['images'][th['image']];pic=Image.open(P(meta['file'])).convert('RGB');c=th.get('crop') or meta.get('crop')
        if c:pic=pic.crop((int(pic.width*c[0]),int(pic.height*c[1]),int(pic.width*c[2]),int(pic.height*c[3])))
        pw,ph=th.get('pic_w',560),H-80;s=max(pw/pic.width,ph/pic.height);pic=pic.resize((int(pic.width*s)+1,int(pic.height*s)+1),Image.LANCZOS);x=(pic.width-pw)//2;y=(pic.height-ph)//2;pic=pic.crop((x,y,x+pw,y+ph))
        if th.get('sepia',True):
            from PIL import ImageEnhance,ImageOps
            pic=ImageOps.colorize(ImageEnhance.Contrast(pic).enhance(1.15).convert('L'),(18,14,10),(238,226,196)).convert('RGB')
        im.alpha_composite(pic.convert('RGBA'),(W-pw-40,40));ImageDraw.Draw(im).rectangle((W-pw-40,40,W-40,H-40),outline=GOLD,width=6)
    d=ImageDraw.Draw(im);y=th.get('y0',30)
    for text,size,col in th['lines']:
        st(d,(50,y),text,font(size),WHITE if col=='white' else GOLD,12 if size>=100 else 8);y+=int(size*1.2)
    by=th.get('bar_y',520);d.rectangle((54,by,th.get('bar_w',640),by+12),fill=RED);st(d,(50,by+35),th['sub'],font(th.get('sub_size',38)),WHITE,6)
    out=P(f'out/{SLUG}_thumbnail.jpg');im.convert('RGB').save(out,quality=92);print(out,round(out.stat().st_size/1e3),'KB')
def stage_pack():
    import make_upload_pack as M
    vid=P(f'out/{SLUG}_video.mp4');srt=P(f'out/{SLUG}_subtitles.srt');assert vid.stat().st_mtime>=srt.stat().st_mtime-1,f'{vid.name} is older than the subtitles (stale build?) - rebuild before pack'
    name=SPEC['pack'];M.build(name,dict(video=f'out/{SLUG}_video.mp4',thumb=f'out/{SLUG}_thumbnail.jpg',srt=f'out/{SLUG}_subtitles.srt',desc=f'out/{SLUG}_description.md',title_no=SPEC['desc'].get('title_no',1)))
if __name__=='__main__':
    slug,cmd=sys.argv[1],sys.argv[2];load_spec(slug)
    if cmd=='part':load_runtime();render_part(int(sys.argv[3]),int(sys.argv[4]))
    elif cmd=='story':stage_story()
    elif cmd=='still':
        load_runtime();d=P(f'out/{SLUG}_review');d.mkdir(parents=True,exist_ok=True)
        for a in sys.argv[3:]:render_frame(int(float(a)*30)).convert('RGB').save(d/f'still_{a}.png')
        print('stills',sys.argv[3:])
    elif cmd=='ends':
        load_runtime()
        for c in TL:
            ss=[x for x in SEGS if x['scene']==c['id']];print(c['key'],[round(x['start']+0.8,1) for x in ss])
    elif cmd=='sents':
        for s in json.loads(P(f'data/{SLUG}_scenes.json').read_text(encoding='utf8')):
            print(f"--- {s['id']} {s['key']}")
            for i,x in enumerate(sentences(s)):print(f'  {i}: {x[:60]}')
    elif cmd=='kana':stage_kana()
    elif cmd=='audio':stage_audio()
    elif cmd=='bgm':stage_bgm()
    elif cmd=='build':stage_build()
    elif cmd=='qa':stage_qa()
    elif cmd=='desc':stage_desc()
    elif cmd=='thumb':stage_thumb()
    elif cmd=='pack':stage_pack()
    else:raise SystemExit('unknown command')
