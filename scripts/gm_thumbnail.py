"""YouTube thumbnails for the world-map video (1280x720 JPEG). A: 'same size?' on Mercator; B: Mercator vs equal-area side by side; C: how many Greenlands fit in Africa (true-size overlay)."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageEnhance
import gm_compose as C
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'out';FD='C:/Windows/Fonts/';W,H=1280,720
NAVY=(7,18,30);GOLD=(255,214,110);ORANGE=(255,150,90);BLUE=(120,190,255);WHITE=(255,255,255)
def font(n,bold=True):
    if n>=100:f=ImageFont.truetype(FD+'NotoSerifJP-VF.ttf',n);f.set_variation_by_axes([900]);return f
    f=ImageFont.truetype(FD+'NotoSansJP-VF.ttf',n);f.set_variation_by_axes([800 if bold else 560]);return f
def st(d,xy,text,f,fill,sw=10,sc=(6,10,18)):d.text(xy,text,font=f,fill=fill,stroke_width=sw,stroke_fill=sc)
def grad(w,h,fn):
    g=Image.new('L',(w,h));px=g.load()
    for y in range(h):
        for x in range(w):px[x,y]=int(255*fn(x/w,y/h))
    return g
def base(w):
    im=Image.new('RGBA',(W,H),NAVY+(255,));return im
def A():
    im=base(W);lay,view=C.draw_map({'merc':1},(0,0,W,830),{1:ORANGE,2:BLUE},grat=False);im.alpha_composite(lay,(-170,-40))
    sh=Image.new('RGBA',(W,H),NAVY+(255,));sh.putalpha(grad(W,H,lambda x,y:min(1,max(0,(x-.5)/.25))*.93));im.alpha_composite(sh);d=ImageDraw.Draw(im)
    st(d,(700,28),'アフリカ',font(60),ORANGE,8);st(d,(950,28),'と',font(60),WHITE,8);st(d,(700,98),'グリーンランド',font(52),BLUE,8)
    st(d,(700,160),'同じ',font(210),WHITE,13);st(d,(700,370),'大きさ？',font(138),WHITE,12)
    d.rectangle((706,545,1240,557),fill=(230,50,50));st(d,(700,585),'地図を計算で検証',font(62),GOLD,8)
    return im.convert('RGB')
def B():
    im=base(W);d=ImageDraw.Draw(im)
    for k,(proj,x0,name,col) in enumerate((('merc',20,'見た目（メルカトル図法）',(255,255,255)),('ee',650,'実際の面積',GOLD))):
        lay,view=C.draw_map({proj:1},(0,0,610,370),{1:ORANGE,2:BLUE},grat=False);im.alpha_composite(lay,(x0,282))
        st(d,(x0+10,232),name,font(44),col,7)
    st(d,(40,14),'同じ大きさ？',font(112),WHITE,11);d.rectangle((44,142,660,152),fill=(230,50,50))
    st(d,(700,18),'実は',font(52),WHITE,8);st(d,(700,62),'約14倍',font(112),GOLD,11)
    st(d,(40,650),'アフリカ',font(52),ORANGE,8);st(d,(250,650),'と',font(52),WHITE,8);st(d,(300,650),'グリーンランド',font(52),BLUE,8)
    return im.convert('RGB')
def Cc():
    im=base(W);XY=C.PR['ee'];af=[(a,b) for (a,b),g in zip(C.SL,C.GROUP) if g==1];idx=[(a,b) for (a,b),g in zip(C.SL,C.GROUP) if g==2]
    apts=np.concatenate([XY[a:b] for a,b in af]);ac=(apts.min(0)+apts.max(0))/2
    cx0,cy0,s0=C.fit(XY,(0,0,W,H));s=s0*2.1;view=C.View(float(ac[0]-(850-W/2)/s),float(ac[1]+(380-H/2)/s*-1+0),s,(0,0,W,H))
    lay,_=C.draw_map({'ee':1},(0,0,W,H),{1:ORANGE,2:(70,100,115)},grat=False,view=view);im.alpha_composite(lay,(0,0))
    ov=Image.new('RGBA',(W*2,H*2),(0,0,0,0));od=ImageDraw.Draw(ov)
    for a,b in idx:
        lo=C.LON[a:b]+62.0;la=C.LAT[a:b];lo=(lo+540)%360-180;lo2,la2=C.P.move_north(lo,la,20.0,-69.0)   # rigid move of Greenland onto Africa (true shape and size)
        q=view.px(np.stack(C.P.PROJ['ee'](lo2,la2),1),2);od.polygon([tuple(p) for p in q],fill=BLUE+(240,),outline=WHITE+(255,))
    im.alpha_composite(ov.resize((W,H),Image.BOX))
    sh=Image.new('RGBA',(W,H),NAVY+(255,));sh.putalpha(grad(W,H,lambda x,y:min(1,max(0,(.46-x)/.46))*.92));im.alpha_composite(sh);d=ImageDraw.Draw(im)
    st(d,(40,30),'グリーンランドは',font(100),BLUE,12);st(d,(40,160),'アフリカに',font(140),WHITE,13);st(d,(40,330),'何個入る？',font(140),GOLD,13)
    d.rectangle((50,500,560,514),fill=(230,50,50));st(d,(46,540),'地図の「大きさ」を計算で検証',font(44),WHITE,7)
    return im.convert('RGB')
def D():
    """background: ChatGPT-generated illustration (globe peeled like an orange), text overlaid with the video fonts"""
    bg=Image.open(ROOT/'assets'/'imagen'/'gm_thumb_globe_peel.webp').convert('RGB');s=max(W/bg.width,H/bg.height);bg=bg.resize((int(bg.width*s)+1,int(bg.height*s)+1),Image.LANCZOS).crop((0,0,W,H))
    bg=ImageEnhance.Contrast(bg).enhance(1.08);im=bg.convert('RGBA');d=ImageDraw.Draw(im)
    st(d,(44,34),'アフリカ',font(54),ORANGE,8);st(d,(262,34),'と',font(54),WHITE,8);st(d,(44,98),'グリーンランド',font(48),BLUE,8)
    st(d,(40,170),'地図は',font(190),WHITE,13);st(d,(40,380),'間違い？',font(150),WHITE,12)
    d.rectangle((48,568,610,580),fill=(230,50,50));st(d,(44,598),'大きさを計算で検証',font(58),GOLD,8)
    return im.convert('RGB')
if __name__=='__main__':
    for n,f in (('A',A),('B',B),('C',Cc),('D',D)):
        im=f();p=OUT/f'gm_thumbnail_{n}.jpg';im.save(p,quality=92);print(p,round(p.stat().st_size/1e3),'KB')
