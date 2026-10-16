"""Road network from GSI vector tiles (experimental_bvmap, layer 'road'); decoded with a minimal MVT/protobuf reader.
Cached to cache/bv/. Output: data/hn_roads.npz (edges: lon/lat polylines + category)."""
from pathlib import Path
import math,json,requests,numpy as np
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parents[1];CACHE=ROOT/'cache'/'bv';CACHE.mkdir(parents=True,exist_ok=True);Z=15
def varint(b,i):
    r=0;s=0
    while True:
        c=b[i];i+=1;r|=(c&0x7f)<<s;s+=7
        if not c&0x80:return r,i
def fields(b):
    i=0;out=[]
    while i<len(b):
        k,i=varint(b,i);f,w=k>>3,k&7
        if w==0:v,i=varint(b,i)
        elif w==2:
            l,i=varint(b,i);v=b[i:i+l];i+=l
        elif w==1:v=b[i:i+8];i+=8
        elif w==5:v=b[i:i+4];i+=4
        else:raise ValueError(w)
        out.append((f,v))
    return out
def unpack(b):
    i=0;o=[]
    while i<len(b):
        v,i=varint(b,i);o.append(v)
    return o
zz=lambda n:(n>>1)^-(n&1)
def decode_road(data,x,y,z=Z):
    lines=[]
    for f,v in fields(data):
        if f!=3:continue
        fl=fields(v);name=next(vv for ff,vv in fl if ff==1).decode()
        if name!='road':continue
        keys=[vv.decode() for ff,vv in fl if ff==3];vals=[]
        for ff,vv in fl:
            if ff==4:
                for f2,v2 in fields(vv):vals.append(v2.decode() if isinstance(v2,(bytes,bytearray)) and f2==1 else v2)
        ext=next((vv for ff,vv in fl if ff==5),4096)
        for ff,vv in fl:
            if ff!=2:continue
            ft=dict(fields(vv)) if False else None;tags=[];geom=[];gtype=0
            for f3,v3 in fields(vv):
                if f3==2:tags=unpack(v3)
                elif f3==3:gtype=v3
                elif f3==4:geom=unpack(v3)
            if gtype!=2:continue
            attrs={keys[tags[k]]:vals[tags[k+1]] for k in range(0,len(tags),2)}
            cx=cy=0;i=0;cur=[]
            while i<len(geom):
                cmd=geom[i]&7;cnt=geom[i]>>3;i+=1
                for _ in range(cnt):
                    if cmd in (1,2):
                        cx+=zz(geom[i]);cy+=zz(geom[i+1]);i+=2
                        if cmd==1:
                            if len(cur)>1:lines.append((cur,attrs))
                            cur=[]
                        cur.append((cx,cy))
                    elif cmd==7:pass
            if len(cur)>1:lines.append((cur,attrs))
    out=[]
    n=2**z
    for pts,a in lines:
        ll=[((x+px/ext)/n*360-180,math.degrees(math.atan(math.sinh(math.pi*(1-2*(y+py/ext)/n))))) for px,py in pts]
        out.append((ll,a))
    return out
def fetch(xy):
    x,y=xy;p=CACHE/f'{Z}_{x}_{y}.pbf'
    if not p.exists():
        for k in range(4):
            r=requests.get(f'https://cyberjapandata.gsi.go.jp/xyz/experimental_bvmap/{Z}/{x}/{y}.pbf',timeout=60)
            if r.ok:p.write_bytes(r.content);break
            if r.status_code==404:p.write_bytes(b'');break
    return xy,p.read_bytes() if p.exists() else b''
def main(bounds=(135.56,34.96,135.78,35.04)):
    tx=lambda lon:int((lon+180)/360*2**Z);ty=lambda lat:int((1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*2**Z)
    xs=range(tx(bounds[0]),tx(bounds[2])+1);ys=range(ty(bounds[3]),ty(bounds[1])+1);jobs=[(x,y) for x in xs for y in ys]
    allw=[]
    with ThreadPoolExecutor(8) as ex:
        for (x,y),data in ex.map(fetch,jobs):
            if data:allw+=decode_road(data,x,y)
    cat={}
    for _,a in allw:cat[a.get('rdCtg')]=cat.get(a.get('rdCtg'),0)+1
    print('tiles',len(jobs),'road lines',len(allw),'rdCtg',cat)
    json.dump([dict(pts=[[round(a,6),round(b,6)] for a,b in ll],a=a) for ll,a in allw],open(ROOT/'cache'/'hn_roads.json','w'),ensure_ascii=False,default=lambda o:None)
if __name__=='__main__':main()
