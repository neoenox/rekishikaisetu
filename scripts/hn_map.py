"""2D location maps for the lead-up scenes: GSI hillshademap mosaics (Japan z9, Kinki z11), darkened to match the UI."""
from pathlib import Path
import io,json,math
import numpy as np,requests
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parents[1]
def tile(lon,lat,z):return (lon+180)/360*2**z,(1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*2**z
def fetch(args):
    z,x,y=args;p=ROOT/'cache'/'hn_tiles'/f'shade_{z}_{x}_{y}.png'
    if p.exists():return args,p.read_bytes()
    for k in range(4):
        r=requests.get(f'https://cyberjapandata.gsi.go.jp/xyz/hillshademap/{z}/{x}/{y}.png',timeout=60)
        if r.status_code==404:return args,None
        if r.ok:p.write_bytes(r.content);return args,r.content
    return args,None
def build(name,z,lon0,lon1,lat0,lat1):
    x0,y0=[int(v) for v in map(math.floor,tile(lon0,lat1,z))];x1,y1=[int(v) for v in map(math.floor,tile(lon1,lat0,z))]
    jobs=[(z,x,y) for y in range(y0,y1+1) for x in range(x0,x1+1)];im=Image.new('RGB',((x1-x0+1)*256,(y1-y0+1)*256),(0,0,0));got=0
    with ThreadPoolExecutor(8) as ex:
        for (zz,x,y),data in ex.map(fetch,jobs):
            if data:im.paste(Image.open(io.BytesIO(data)).convert('RGB'),((x-x0)*256,(y-y0)*256));got+=1
    a=np.asarray(im,dtype=float)/255.;g=a.mean(-1,keepdims=True)
    # darken + cool tint: land stays readable, sea sinks to near-black navy
    out=np.clip(g*np.array([.62,.78,.92])*1.15+np.where(g<.02,np.array([.02,.04,.07]),0),0,1)
    Image.fromarray((out*255).astype(np.uint8)).save(ROOT/'cache'/f'hn_map_{name}.png')
    (ROOT/'cache'/f'hn_map_{name}.json').write_text(json.dumps(dict(z=z,x0=x0,y0=y0,size=list(im.size),tiles=len(jobs),got=got)))
    print(name,im.size,got,'/',len(jobs),flush=True)
if __name__=='__main__':
    build('jp',9,132.8,139.4,33.1,36.4);build('jp8',8,129.0,142.0,31.0,38.6);build('kinki',11,133.7,136.8,34.4,35.8);build('chukyo',9,133.0,139.0,33.0,36.5);build('okayama',10,132.8,136.2,34.0,35.4);build('east',9,135.0,141.0,35.0,38.5)
