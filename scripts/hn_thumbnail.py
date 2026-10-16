"""YouTube thumbnails (1280x720 JPEG, < 2MB). Variant A: print + numbers; variant B: two portraits."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageEnhance
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'out'
B='C:/Windows/Fonts/YuGothB.ttc';M='C:/Windows/Fonts/YuGothM.ttc'
FD='C:/Windows/Fonts/'
def font(n,bold=True):
    """same families as the video: Noto Serif JP for the big headline (size>=140), Noto Sans JP elsewhere (numbers stay in the sans face)"""
    if n>=140:f=ImageFont.truetype(FD+'NotoSerifJP-VF.ttf',n);f.set_variation_by_axes([900]);return f
    f=ImageFont.truetype(FD+'NotoSansJP-VF.ttf',n);f.set_variation_by_axes([800 if bold else 560]);return f
W,H=1280,720
def stroke_text(d,xy,text,f,fill,sw=10,sc=(8,8,12)):d.text(xy,text,font=f,fill=fill,stroke_width=sw,stroke_fill=sc)
def cover(im,w,h,fx=.5,fy=.5):
    s=max(w/im.width,h/im.height);im=im.resize((int(im.width*s)+1,int(im.height*s)+1),Image.LANCZOS);x=int((im.width-w)*fx);y=int((im.height-h)*fy);return im.crop((x,y,x+w,y+h))
def crop_portrait(pid,x0,top,wf,w,h):
    im=Image.open(ROOT/'assets'/'portraits'/f'{pid}.jpg').convert('RGB');cw=im.width*wf;ch=cw*h/w;cx=im.width*(x0+wf/2);cy=im.height*top+ch/2
    return im.crop((int(cx-cw/2),int(cy-ch/2),int(cx+cw/2),int(cy+ch/2))).resize((w,h),Image.LANCZOS)
def A():
    bg=cover(Image.open(ROOT/'assets'/'portraits'/'print.jpg').convert('RGB'),W,H,.62,.5);bg=ImageEnhance.Color(bg).enhance(1.25);bg=ImageEnhance.Contrast(bg).enhance(1.12)
    im=bg.convert('RGBA');g=Image.new('L',(W,1));gd=g.load()
    for x in range(W):gd[x,0]=int(235*max(0,1-x/(W*.82))**1.25)
    sh=Image.new('RGBA',(W,H),(6,10,18,255));sh.putalpha(g.resize((W,H)));im.alpha_composite(sh)
    bt=Image.new('L',(1,H));bd=bt.load()
    for y in range(H):bd[0,y]=int(190*max(0,(y-H*.55)/(H*.45))**1.5)
    b2=Image.new('RGBA',(W,H),(6,10,18,255));b2.putalpha(bt.resize((W,H)));im.alpha_composite(b2);d=ImageDraw.Draw(im)
    stroke_text(d,(54,34),'天正10年6月2日',font(52),(245,205,110),8)
    stroke_text(d,(46,92),'本能寺の変',font(205),(255,255,255),14)
    # red brush underline
    d.rectangle((58,350,930,364),fill=(220,40,40))
    # numbers
    d.rounded_rectangle((52,384,560,596),18,fill=(10,20,32,235),outline=(255,105,90),width=5)
    d.text((82,392),'信長の側近',font=font(46),fill=(255,255,255));stroke_text(d,(78,436),'20〜30人',font(104),(255,120,100),6);d.text((84,556),'多い説では150〜160人（諸説）',font=font(26,False),fill=(215,222,226))
    d.rounded_rectangle((610,384,1230,596),18,fill=(10,20,32,235),outline=(160,125,255),width=5)
    d.text((640,392),'光秀の軍勢',font=font(46),fill=(255,255,255));stroke_text(d,(634,436),'約1万3千',font(104),(190,165,255),6);d.text((640,556),'（一説・史料により異なる）',font=font(26,False),fill=(215,222,226))
    stroke_text(d,(54,624),'その大軍は、どこから来たのか？',font(60),(255,255,255),8)
    return im.convert('RGB')
def Bv():
    im=Image.new('RGB',(W,H),(14,22,34));d=ImageDraw.Draw(im)
    for y in range(H):d.line([(0,y),(W,y)],fill=(int(18+30*y/H),int(26+20*y/H),int(40+14*y/H)))
    n=crop_portrait('nobunaga',.12,.07,.76,470,560);m=crop_portrait('mitsuhide',.27,.40,.65,470,560)
    for p,x,col in ((n,40,(255,95,80)),(m,770,(150,110,255))):
        im.paste(p,(x,150));d.rectangle((x-6,144,x+476,716),outline=col,width=8)
    d=ImageDraw.Draw(im)
    stroke_text(d,(40,10),'本能寺の変',font(120),(255,255,255),10)
    d.rounded_rectangle((60,610,490,700),12,fill=(8,14,22),outline=(255,95,80),width=4);d.text((90,626),'織田信長',font=font(54),fill=(255,255,255))
    d.rounded_rectangle((790,610,1220,700),12,fill=(8,14,22),outline=(150,110,255),width=4);d.text((820,626),'明智光秀',font=font(54),fill=(255,255,255))
    stroke_text(d,(500,230),'なぜ',font(150),(245,205,110),12);stroke_text(d,(500,400),'？',font(190),(255,255,255),12)
    stroke_text(d,(820,40),'経緯から丁寧に',font(52),(245,205,110),8)
    return im
if __name__=='__main__':
    for name,fn in (('thumbnail_A',A),('thumbnail_B',Bv)):
        im=fn();p=OUT/f'{name}.jpg';im.save(p,quality=93,optimize=True);print(name,p.stat().st_size//1024,'KB')

# ---------------- v2: higher-tension variants (still hedged: 諸説 stays on the numbers)
def glow_poly(im,poly,color,blur=30,alpha=200):
    layer=Image.new('RGBA',im.size,(0,0,0,0));ImageDraw.Draw(layer).polygon(poly,fill=color+(alpha,));layer=layer.filter(ImageFilter.GaussianBlur(blur));im.alpha_composite(layer)
def C():
    im=Image.new('RGBA',(W,H),(10,12,20,255));d=ImageDraw.Draw(im)
    left=[(0,0),(790,0),(560,720),(0,720)];right=[(830,0),(1280,0),(1280,720),(600,720)]
    def fill_side(poly,pid,crop,col,x,w):
        mask=Image.new('L',(W,H),0);ImageDraw.Draw(mask).polygon(poly,fill=255)
        p=crop_portrait(pid,*crop,w,H);base=Image.new('RGBA',(W,H),(0,0,0,255));base.paste(p,(x,0))
        base=ImageEnhance.Contrast(ImageEnhance.Brightness(base.convert('RGB')).enhance(1.25)).enhance(1.25).convert('RGBA');tint=Image.new('RGBA',(W,H),col+(38,));base.alpha_composite(tint);im.paste(base,(0,0),mask)
    fill_side(left,'nobunaga',(.10,.04,.80),(255,60,40),-20,780);fill_side(right,'mitsuhide',(.22,.34,.70),(130,80,255),620,700)
    glow_poly(im,[(790,0),(830,0),(600,720),(560,720)],(255,255,255),14,230)
    # darken lower third for text
    bt=Image.new('L',(1,H));bd=bt.load()
    for y in range(H):bd[0,y]=int(215*max(0,(y-H*.38)/(H*.62))**1.2)
    sh=Image.new('RGBA',(W,H),(4,6,12,255));sh.putalpha(bt.resize((W,H)));im.alpha_composite(sh);d=ImageDraw.Draw(im)
    stroke_text(d,(40,8),'本能寺の変',font(150),(255,255,255),12)
    stroke_text(d,(46,300),'信長の側近',font(46),(255,255,255),7);stroke_text(d,(40,352),'20〜30人',font(122),(255,110,90),9)
    stroke_text(d,(742,300),'光秀の軍勢',font(46),(255,255,255),7);stroke_text(d,(716,352),'約1万3千',font(122),(195,170,255),9)
    stroke_text(d,(548,470),'VS',font(104),(255,225,120),10)
    d.text((46,478),'多い説は150〜160人',font=font(28),fill=(255,230,225),stroke_width=4,stroke_fill=(5,5,10));d.text((760,478),'一説・史料により異なる',font=font(28),fill=(235,225,255),stroke_width=4,stroke_fill=(5,5,10))
    d.rounded_rectangle((26,590,1254,700),16,fill=(215,40,40,245));stroke_text(d,(56,600),'大軍は、どこから来たのか？',font(84),(255,255,255),6,(90,0,0))
    return im.convert('RGB')
def D():
    bg=cover(Image.open(ROOT/'assets'/'portraits'/'print.jpg').convert('RGB'),W,H,.68,.5);bg=ImageEnhance.Brightness(bg).enhance(.62);bg=ImageEnhance.Color(bg).enhance(1.4)
    im=bg.convert('RGBA')
    red=Image.new('RGBA',(W,H),(0,0,0,0));rd=ImageDraw.Draw(red);rd.ellipse((660,260,1500,980),fill=(255,70,20,150));red=red.filter(ImageFilter.GaussianBlur(120));im.alpha_composite(red)
    v=Image.new('L',(W,H),0);vd=ImageDraw.Draw(v);vd.ellipse((-260,-200,1540,900),fill=255);v=ImageEnhance.Brightness(v.filter(ImageFilter.GaussianBlur(160))).enhance(1);dark=Image.new('RGBA',(W,H),(0,0,0,255));dark.putalpha(v.point(lambda a:int(200*(1-a/255))));im.alpha_composite(dark);d=ImageDraw.Draw(im)
    stroke_text(d,(48,26),'天正10年6月2日 未明',font(56),(255,215,120),9)
    stroke_text(d,(40,90),'信長、',font(150),(255,255,255),12);stroke_text(d,(40,222),'最期の夜',font(190),(255,60,50),14)
    d.rounded_rectangle((44,458,640,618),16,fill=(8,14,24,238),outline=(255,105,90),width=5);d.text((70,466),'側近',font=font(40),fill=(255,255,255));stroke_text(d,(70,508),'20〜30人',font(84),(255,125,105),6)
    d.rounded_rectangle((668,458,1236,618),16,fill=(8,14,24,238),outline=(160,125,255),width=5);d.text((694,466),'光秀の軍勢',font=font(40),fill=(255,255,255));stroke_text(d,(694,508),'約1万3千',font(84),(195,170,255),6)
    d.text((300,470),'諸説あり',font=font(26,False),fill=(210,215,220))
    stroke_text(d,(46,632),'光秀は、どこから来たのか？',font(62),(255,255,255),8)
    return im.convert('RGB')
if __name__=='__main__':
    for name,fn in (('thumbnail_C',C),('thumbnail_D',D)):
        im=fn();p=OUT/f'{name}.jpg';im.save(p,quality=93,optimize=True);print(name,p.stat().st_size//1024,'KB')
