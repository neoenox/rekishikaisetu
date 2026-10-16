"""Procedural flame / smoke sprites (RGBA PNG)."""
import numpy as np
from PIL import Image,ImageFilter
from pathlib import Path
out=Path(__file__).resolve().parents[1]/'assets'/'fx_hn';out.mkdir(parents=True,exist_ok=True)
rng=np.random.default_rng(7)
for k in range(4):
    W,H=256,384;y,x=np.mgrid[0:H,0:W];u=(x-W/2)/(W/2);v=1-y/H
    width=(1-v)**.8*(.55+.15*rng.random())+.03;sway=.12*np.sin(v*6+k*1.7)*v
    core=np.clip(1-((u-sway)/width)**2,0,1)*np.clip(v*4,0,1)*np.clip((1-v)*1.3,0,1)
    noise=Image.fromarray((rng.random((H//8,W//8))*255).astype(np.uint8)).resize((W,H),Image.BICUBIC);n=np.asarray(noise)/255.
    a=np.clip(core*(.75+.5*n)-.05,0,1)
    r=np.clip(1.0+0*a,0,1);g=np.clip(.25+.75*a**1.5*(1-v*.3),0,1);b=np.clip(.03+.45*a**4,0,1)
    img=np.dstack([r,g,b,a**.8]);Image.fromarray((img*255).astype(np.uint8),'RGBA').filter(ImageFilter.GaussianBlur(1.2)).save(out/f'flame_{k}.png')
W=H=256;y,x=np.mgrid[0:H,0:W];r=np.hypot(x-W/2,y-H/2)/(W/2)
n=np.asarray(Image.fromarray((rng.random((16,16))*255).astype(np.uint8)).resize((W,H),Image.BICUBIC))/255.
a=np.clip(1-r,0,1)**1.5*(.6+.6*n);Image.fromarray((np.dstack([.12+0*a,.11+0*a,.10+0*a,np.clip(a,0,1)*.85])*255).astype(np.uint8),'RGBA').save(out/'smoke.png');print('fx ok')
