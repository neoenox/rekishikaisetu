"""YouTube thumbnails for the ninja video (1280x720 JPEG). Pictures: National Diet Library Digital Collection (pdm). A: Hokusai Manga black-clad figure + 'did ninja really wear black?'; B: three keywords on a dark ground with the kabuki print."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageEnhance,ImageOps
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'out';FD='C:/Windows/Fonts/';W,H=1280,720
NAVY=(7,18,30);GOLD=(255,214,110);RED=(230,50,50);WHITE=(255,255,255)
def font(n,bold=True):
    if n>=100:f=ImageFont.truetype(FD+'NotoSerifJP-VF.ttf',n);f.set_variation_by_axes([900]);return f
    f=ImageFont.truetype(FD+'NotoSansJP-VF.ttf',n);f.set_variation_by_axes([800 if bold else 560]);return f
def st(d,xy,text,f,fill,sw=10,sc=(6,10,18)):d.text(xy,text,font=f,fill=fill,stroke_width=sw,stroke_fill=sc)
def crop(name,box):
    im=Image.open(ROOT/'assets'/'ndl_ninja'/f'{name}.jpg').convert('RGB');a,b,c,e=box;return im.crop((int(im.width*a),int(im.height*b),int(im.width*c),int(im.height*e)))
def fit(im,w,h):
    s=max(w/im.width,h/im.height);im=im.resize((int(im.width*s)+1,int(im.height*s)+1),Image.LANCZOS);x=(im.width-w)//2;y=(im.height-h)//2;return im.crop((x,y,x+w,y+h))
def paper(im):
    """woodblock print on the right: warm paper tone, slight contrast"""
    im=ImageEnhance.Contrast(im).enhance(1.15);return ImageOps.colorize(im.convert('L'),(18,14,10),(238,226,196))
def A():
    im=Image.new('RGBA',(W,H),NAVY+(255,));pic=paper(crop('hokusai_black_ninja',(.55,.24,.95,.62)));pic=fit(pic,560,H-80);im.alpha_composite(pic.convert('RGBA'),(W-560-40,40))
    d=ImageDraw.Draw(im);d.rectangle((W-560-40,40,W-40,H-40),outline=GOLD,width=6)
    st(d,(50,30),'忍者は',font(100),WHITE,10);st(d,(50,150),'本当に',font(150),WHITE,12);st(d,(50,330),'黒装束？',font(150),GOLD,12)
    d.rectangle((54,520,640,532),fill=RED);st(d,(50,555),'国立国会図書館の解説で確かめる',font(38),WHITE,6)
    return im.convert('RGB')
def B():
    im=Image.new('RGBA',(W,H),NAVY+(255,));pic=fit(crop('toyokuni_goemon_hisayoshi',(.09,.075,.915,.86)),520,H);im.alpha_composite(pic.convert('RGBA'),(W-520,0))
    sh=Image.new('RGBA',(W,H),NAVY+(255,));g=Image.new('L',(W,1));px=g.load()
    for x in range(W):px[x,0]=int(255*min(1,max(0,(W-520+120-x)/260))) if x>W-640 else 255
    sh.putalpha(g.resize((W,H)));base=im.copy();base.alpha_composite(sh);d=ImageDraw.Draw(base)
    for k,t_ in enumerate(('黒装束','覆面','手裏剣')):st(d,(50,40+k*175),t_,font(150),WHITE if k<2 else GOLD,12)
    d.rectangle((54,575,560,587),fill=RED);st(d,(50,610),'そのイメージは、どこから？',font(52),WHITE,8)
    return base.convert('RGB')
if __name__=='__main__':
    for n,f in (('A',A),('B',B)):
        im=f();p=OUT/f'nj_thumbnail_{n}.jpg';im.save(p,quality=92);print(p,round(p.stat().st_size/1e3),'KB')
