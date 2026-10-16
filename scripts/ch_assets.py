"""Channel art for 「寄り道ラボ」: profile icon (800x800) and banner (2560x1440, text inside the 1546x423 safe area). Own palette/fonts as in the videos."""
import sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import gm_compose as C
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'out'/'channel';OUT.mkdir(parents=True,exist_ok=True);FD='C:/Windows/Fonts/'
NAVY=(7,18,30);GOLD=(239,201,118);ORANGE=(255,150,90);BLUE=(120,190,255);WHITE=(248,246,236)
def serif(n):f=ImageFont.truetype(FD+'NotoSerifJP-VF.ttf',n);f.set_variation_by_axes([900]);return f
def sans(n,w=700):f=ImageFont.truetype(FD+'NotoSansJP-VF.ttf',n);f.set_variation_by_axes([w]);return f
def vgrad(w,h,c0,c1):
    a=np.linspace(0,1,h)[:,None,None];arr=(np.array(c0)[None,None,:]*(1-a)+np.array(c1)[None,None,:]*a)*np.ones((1,w,1));return Image.fromarray(arr.astype('uint8'),'RGB').convert('RGBA')
def winding(w,h,y0,amp,x0,x1,n=240):
    xs=np.linspace(x0,x1,n);ys=y0+amp*np.sin(np.linspace(0,2.2*np.pi,n))*np.linspace(.4,1,n);return list(zip(xs,ys))
def dashed(d,pts,col,width,on=26,off=22):
    acc=0;draw=True;prev=pts[0]
    for p in pts[1:]:
        seg=math.hypot(p[0]-prev[0],p[1]-prev[1]);
        if draw:d.line([prev,p],fill=col,width=width)
        acc+=seg
        if acc>(on if draw else off):draw=not draw;acc=0
        prev=p
def icon():
    S=800;im=vgrad(S,S,(12,30,48),(5,12,22));d=ImageDraw.Draw(im)
    pts=winding(S,S,610,60,110,690);dashed(d,pts,GOLD+(255,),9);
    for (x,y),c in ((pts[0],ORANGE),(pts[-1],BLUE)):d.ellipse((x-22,y-22,x+22,y+22),fill=c+(255,),outline=WHITE+(255,),width=4)
    f=serif(470);bb=d.textbbox((0,0),'寄',font=f);w=bb[2]-bb[0];d.text(((S-w)/2-bb[0],70-bb[1]),'寄',font=f,fill=WHITE+(255,),stroke_width=6,stroke_fill=(5,10,16,255))
    return im.convert('RGB')
def banner():
    W,H=2560,1440;im=vgrad(W,H,(11,28,44),(5,12,22));lay,_=C.draw_map({'merc':1},(0,0,W,H),{},grat=False,alpha=62);im.alpha_composite(lay,(0,0));d=ImageDraw.Draw(im)
    pts=winding(W,H,1180,70,160,2400);dashed(d,pts,GOLD+(150,),12,34,30)
    for (x,y),c in ((pts[0],ORANGE),(pts[-1],BLUE)):d.ellipse((x-26,y-26,x+26,y+26),fill=c+(230,),outline=WHITE+(255,),width=5)
    # name only, centred in the 1546x423 safe area (y 507..933)
    f1=serif(260);t='寄り道ラボ';bb=d.textbbox((0,0),t,font=f1);w=bb[2]-bb[0];h=bb[3]-bb[1];d.text(((W-w)/2-bb[0],720-h/2-bb[1]),t,font=f1,fill=WHITE+(255,),stroke_width=10,stroke_fill=(5,10,16,255))
    return im.convert('RGB')
if __name__=='__main__':
    i=icon();i.save(OUT/'ch_icon_800.png');b=banner();b.save(OUT/'ch_banner_2560x1440.png')
    # preview: banner with the safe-area frame and the icon in a circle
    pv=b.resize((1280,720)).convert('RGBA');d=ImageDraw.Draw(pv);d.rectangle((640-386,360-106,640+386,360+106),outline=(255,80,80,255),width=3)
    ic=i.resize((180,180)).convert('RGBA');m=Image.new('L',(180,180),0);ImageDraw.Draw(m).ellipse((0,0,179,179),fill=255);ic.putalpha(m);pv.alpha_composite(ic,(40,520));pv.convert('RGB').save(OUT/'preview.png');print('ok')
