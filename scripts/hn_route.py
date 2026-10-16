"""Road-following route Kameyama castle -> old Honnoji site on the modern road network (GSI vector tiles).
Not a historical road: the modern network is used as the best available proxy; the route is forced through the Oinosaka pass area."""
from pathlib import Path
import json,math,sys
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree
from hn_common import ROOT,xy,interp,CRS_
from pyproj import Transformer
INV=Transformer.from_crs(CRS_,4326,always_xy=True)
def build():
    R=json.load(open(ROOT/'cache'/'hn_roads.json',encoding='utf8'))
    nodes={};coords=[];E=[]
    def nid(x,y):
        k=(round(x/4),round(y/4))   # 4 m snap grid in local metres
        if k not in nodes:nodes[k]=len(coords);coords.append((x,y))
        return nodes[k]
    for r in R:
        a=r['a'];cat=a.get('rdCtg');mw=a.get('motorway')
        if cat in (3,5) or mw==0:continue          # skip expressways / non-vehicle
        w=a.get('rnkWidth',1) or 0;f={0:.8,1:.9}.get(cat,1.0)*(1.35 if w==0 else 1.0)
        P=[xy(lo,la) for lo,la in r['pts']]
        for (x0,y0),(x1,y1) in zip(P[:-1],P[1:]):
            u,v=nid(x0,y0),nid(x1,y1)
            if u!=v:E.append((u,v,math.hypot(x1-x0,y1-y0),f))
    C=np.array(coords);return C,E
def graph(C,E,f_dem):
    z=np.array([f_dem([[y,x]])[0] if True else 0 for x,y in C]) if False else None
    I=[e[0] for e in E];J=[e[1] for e in E];L=np.array([e[2] for e in E]);F=np.array([e[3] for e in E])
    return I,J,L,F
def main():
    import numpy as np
    f=interp();C,E=build();print('nodes',len(C),'edges',len(E),flush=True)
    xs=C[:,0];ys=C[:,1]
    # elevation per node (DEM, metres)
    from hn_common import grid
    from scipy.interpolate import RegularGridInterpolator as RGI
    gx,gy,gh=grid();fz=RGI((gy,gx),gh,bounds_error=False,fill_value=np.nan);z=fz(np.column_stack([C[:,1],C[:,0]]))
    I=np.array([e[0] for e in E]);J=np.array([e[1] for e in E]);L=np.array([e[2] for e in E]);F=np.array([e[3] for e in E])
    ok=np.isfinite(z[I])&np.isfinite(z[J]);I,J,L,F=I[ok],J[ok],L[ok],F[ok]
    # drop tunnel-like edges: the terrain above the segment is clearly higher than both ends (road runs under it)
    mid=fz(np.column_stack([(C[I,1]+C[J,1])/2,(C[I,0]+C[J,0])/2]));q1=fz(np.column_stack([C[I,1]*.75+C[J,1]*.25,C[I,0]*.75+C[J,0]*.25]));q3=fz(np.column_stack([C[I,1]*.25+C[J,1]*.75,C[I,0]*.25+C[J,0]*.75]))
    bump=np.nanmax(np.vstack([mid,q1,q3]),axis=0)-np.maximum(z[I],z[J]);keep=(bump<12)|(L<45)
    print('tunnel-like edges removed',int((~keep).sum()),'of',len(L),flush=True)
    I,J,L,F=I[keep],J[keep],L[keep],F[keep]
    dz=np.abs(z[I]-z[J]);grade=dz/np.maximum(L,1);cost=L*F*(1+6*np.clip(grade-.06,0,None))
    n=len(C);A=coo_matrix((np.r_[cost,cost],(np.r_[I,J],np.r_[J,I])),shape=(n,n)).tocsr()
    tree=cKDTree(C)
    def near(lon,lat,r=400):
        p=xy(lon,lat);d,i=tree.query(p);return int(i),float(d)
    s,ds=near(135.5812,35.0136);t,dt=near(135.7534,35.0055)
    print('start snap m',round(ds),'end snap m',round(dt))
    dist,pred=dijkstra(A,indices=s,return_predecessors=True)
    def path(src_pred,tgt):
        p=[tgt]
        while p[-1]!=s and src_pred[p[-1]]>=0:p.append(int(src_pred[p[-1]]))
        return p[::-1]
    P=path(pred,t);pts=C[P];zz=z[P]
    seg=np.hypot(*np.diff(pts,axis=0).T);d=np.r_[0,np.cumsum(seg)]
    print('route nodes',len(P),'length m',round(d[-1]),'max elev',round(zz.max()),'at km',round(d[int(np.argmax(zz))]/1000,1))
    lonlat=[INV.transform(x,y) for x,y in pts[::max(1,len(pts)//60)]]
    print('sample lonlat',[(round(a,4),round(b,4)) for a,b in lonlat[::6]])
    np.savez(ROOT/'cache'/'hn_route_raw.npz',pts=pts,z=zz)
if __name__=='__main__':main()
