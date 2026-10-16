"""Natural Earth 110m countries reader (minimal .shp/.dbf parser, no external deps) + sphere area + Mercator scale checks.
usage: python scripts/gm_geo.py  -> prints the numbers used in the script (areas, ratio, Greenland latitude range, Japan lat-shift factor)"""
import struct,math,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'assets'/'naturalearth'/'ne110'
R=6371.0088  # km, mean Earth radius
def read_shp(p):
    b=Path(p).read_bytes();pos=100;out=[]
    while pos<len(b):
        rn,cl=struct.unpack('>ii',b[pos:pos+8]);pos+=8;rec=b[pos:pos+cl*2];pos+=cl*2
        st=struct.unpack('<i',rec[:4])[0]
        if st==0:out.append(None);continue
        npart,npts=struct.unpack('<ii',rec[36:44]);parts=struct.unpack('<%di'%npart,rec[44:44+4*npart]);o=44+4*npart
        pts=[struct.unpack('<dd',rec[o+16*i:o+16*i+16]) for i in range(npts)];rings=[pts[parts[i]:(parts[i+1] if i+1<npart else npts)] for i in range(npart)]
        out.append(rings)
    return out
def read_dbf(p):
    b=Path(p).read_bytes();n,hl,rl=struct.unpack('<xxxxIHH',b[:12]);fields=[];o=32
    while b[o]!=0x0D:
        fields.append((b[o:o+11].split(b'\x00')[0].decode(),b[o+16]));o+=32
    recs=[]
    for i in range(n):
        r=b[hl+i*rl:hl+(i+1)*rl];off=1;d={}
        for name,ln in fields:d[name]=r[off:off+ln].decode('utf8',errors='replace').replace(chr(0),'').strip();off+=ln
        recs.append(d)
    return recs
def ring_area(r):
    s=0.0
    for (x1,y1),(x2,y2) in zip(r[:-1],r[1:]):
        s+=math.radians(x2-x1)*(math.sin(math.radians(y1))+math.sin(math.radians(y2)))
    return s*R*R/2   # signed (clockwise outer ring -> negative with this convention)
def load():
    g=read_shp(D/'ne_110m_admin_0_countries.shp');a=read_dbf(D/'ne_110m_admin_0_countries.dbf')
    return [dict(attr=x,rings=r) for x,r in zip(a,g)]
def area_km2(rings):
    outer=sum(abs(ring_area(r)) for r in rings if ring_area(r)>0);holes=sum(abs(ring_area(r)) for r in rings if ring_area(r)<0)   # outer rings are positive in this convention
    return outer-holes
if __name__=='__main__':
    C=load();by={c['attr']['ADMIN']:c for c in C}
    gl=by['Greenland'];ja=by['Japan']
    A_gl=area_km2(gl['rings']);A_ja=area_km2(ja['rings'])
    afr=[c for c in C if c['attr'].get('CONTINENT')=='Africa'];A_af=sum(area_km2(c['rings']) for c in afr)
    print('Greenland area (sphere, 110m) km2',round(A_gl),' Japan',round(A_ja),' Africa (sum of countries, 110m)',round(A_af),' n=',len(afr))
    print('Africa/Greenland ratio',round(A_af/A_gl,2))
    lats=[p[1] for r in gl['rings'] for p in r];print('Greenland lat range',round(min(lats),1),round(max(lats),1))
    # area-weighted mean latitude of Japan, and Mercator area-factor ratio when moved to 60N
    num=0;den=0
    for r in ja['rings']:
        a=abs(ring_area(r));m=sum(p[1] for p in r)/len(r);num+=a*m;den+=a
    latj=num/den;print('Japan area-weighted mean lat',round(latj,2))
    sec2=lambda d:1/math.cos(math.radians(d))**2
    print('sec^2 at Japan',round(sec2(latj),3),' at 60:',round(sec2(60),3),' at 80:',round(sec2(80),2),' ratio 60/Japan',round(sec2(60)/sec2(latj),2))
    # Mercator drawn area of Greenland and Africa relative (numerical integration over rings, per-polygon strip method)
    def merc_area(rings):
        s=0.0
        for r in rings:
            t=0.0
            for (x1,y1),(x2,y2) in zip(r[:-1],r[1:]):
                y1c=max(min(y1,85),-85);y2c=max(min(y2,85),-85)
                m1=math.log(math.tan(math.pi/4+math.radians(y1c)/2));m2=math.log(math.tan(math.pi/4+math.radians(y2c)/2))
                t+=math.radians(x2-x1)*(m1+m2)/2
            s+=t
        return abs(s)
    sg=sum(1 for _ in [0]);mg=0
    def signed(rings):
        tot=0.0
        for r in rings:
            t=0.0
            for (x1,y1),(x2,y2) in zip(r[:-1],r[1:]):
                y1c=max(min(y1,85),-85);y2c=max(min(y2,85),-85)
                m1=math.log(math.tan(math.pi/4+math.radians(y1c)/2));m2=math.log(math.tan(math.pi/4+math.radians(y2c)/2))
                t+=math.radians(x2-x1)*(m1+m2)/2
            tot+= -t if ring_area(r)<0 else -t  # sign handled below
        return tot
    def mercator_sum(rings):
        tot=0.0
        for r in rings:
            t=0.0
            for (x1,y1),(x2,y2) in zip(r[:-1],r[1:]):
                m1=math.log(math.tan(math.pi/4+math.radians(max(min(y1,85),-85))/2));m2=math.log(math.tan(math.pi/4+math.radians(max(min(y2,85),-85))/2))
                t+=math.radians(x2-x1)*(m1+m2)/2
            tot+= abs(t) if ring_area(r)<0 else -abs(t)
        return tot
    mg=mercator_sum(gl['rings']);ma=sum(mercator_sum(c['rings']) for c in afr)
    print('Mercator drawn area (unit sphere) Greenland',round(mg,3),' Africa',round(ma,3),' Africa/Greenland drawn ratio',round(ma/mg,2))
