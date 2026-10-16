"""Map projections used by the world-map video (unit sphere, R=1) + self-test: equal-area projections must preserve area.
usage: python scripts/gm_proj.py   (self-test)"""
import math
import numpy as np
A1,A2,A3,A4=1.340264,-0.081106,0.000893,0.003796   # Equal Earth coefficients (Savric, Patterson, Jenny 2018)
def merc(lon,lat):
    lat=np.clip(lat,-85.05113,85.05113);return np.radians(lon),np.log(np.tan(np.pi/4+np.radians(lat)/2))
def gall_peters(lon,lat):
    c=math.cos(math.radians(45));return np.radians(lon)*c,np.sin(np.radians(lat))/c      # cylindrical equal-area, standard parallels 45 deg
def equal_earth(lon,lat):
    lam=np.radians(lon);ph=np.radians(lat);th=np.arcsin(np.sqrt(3)/2*np.sin(ph));t2=th*th;t6=t2**3;t8=t6*t2
    x=2*np.sqrt(3)*lam*np.cos(th)/(3*(9*A4*t8+7*A3*t6+3*A2*t2+A1));y=th*(A1+A2*t2+A3*t6+A4*t8);return x,y
def plate(lon,lat):return np.radians(lon),np.radians(lat)
def move_north(lon,lat,lon0,delta_deg):
    """rigid motion on the sphere: rotate by delta_deg about the axis perpendicular to the meridian of lon0 (points on that meridian move north by delta_deg); shape and spherical area are preserved"""
    lo,la=np.radians(lon),np.radians(lat);v=np.stack([np.cos(la)*np.cos(lo),np.cos(la)*np.sin(lo),np.sin(la)],1);k=np.array([-math.sin(math.radians(lon0)),math.cos(math.radians(lon0)),0.0]);a=-math.radians(delta_deg)
    r=v*math.cos(a)+np.cross(k,v)*math.sin(a)+np.outer(v@k,k)*(1-math.cos(a));return np.degrees(np.arctan2(r[:,1],r[:,0])),np.degrees(np.arcsin(np.clip(r[:,2],-1,1)))
PROJ={'merc':merc,'gp':gall_peters,'ee':equal_earth,'plate':plate}
def shoelace(x,y):return 0.5*abs(np.sum(x[:-1]*y[1:]-x[1:]*y[:-1]))
def dest_point(lon,lat,bearing,dist):
    """point at angular distance `dist` (rad) from (lon,lat) deg along `bearing` (rad) on the unit sphere -> (lon,lat) deg"""
    p1=np.radians(lat);l1=np.radians(lon);p2=np.arcsin(np.sin(p1)*np.cos(dist)+np.cos(p1)*np.sin(dist)*np.cos(bearing))
    l2=l1+np.arctan2(np.sin(bearing)*np.sin(dist)*np.cos(p1),np.cos(dist)-np.sin(p1)*np.sin(p2));return (np.degrees(l2)+540)%360-180,np.degrees(p2)
def great_circle(lon1,lat1,lon2,lat2,n=80):
    a=np.radians([lon1,lat1,lon2,lat2]);v=lambda lo,la:np.array([np.cos(la)*np.cos(lo),np.cos(la)*np.sin(lo),np.sin(la)])
    p,q=v(a[0],a[1]),v(a[2],a[3]);w=np.arccos(np.clip(p@q,-1,1));ts=np.linspace(0,1,n);pts=[(np.sin((1-t)*w)*p+np.sin(t*w)*q)/np.sin(w) for t in ts]
    return np.degrees(np.arctan2([q_[1] for q_ in pts],[q_[0] for q_ in pts])),np.degrees(np.arcsin([q_[2] for q_ in pts]))
if __name__=='__main__':
    import sys;sys.path.insert(0,str(__import__('pathlib').Path(__file__).resolve().parent));import gm_geo as G
    C=G.load();R=G.R;afr=[c for c in C if c['attr'].get('CONTINENT')=='Africa'];gl=[c for c in C if c['attr']['ADMIN']=='Greenland'][0]
    def proj_area(cs,f):
        tot=0.0
        for c in cs:
            for r in c['rings']:
                a=np.array(r)
                if G.ring_area(r)>0:x,y=f(a[:,0],a[:,1]);tot+=shoelace(x,y)
        return tot
    for name in ('plate','merc','gp','ee'):
        f=PROJ[name];pa,pg=proj_area(afr,f),proj_area([gl],f);print(f'{name:6s} Africa/Greenland drawn-area ratio = {pa/pg:6.2f}')
    sa=sum(G.area_km2(c['rings']) for c in afr);sg=G.area_km2(gl['rings']);print('sphere ratio',round(abs(sa/sg),2))
    # equal-area check in absolute units (unit sphere): drawn area / (sphere area / R^2)
    for name in ('gp','ee'):
        f=PROJ[name];print(name,'drawn/true (Africa) =',round(proj_area(afr,f)/(abs(sa)/R**2),3),' (Greenland) =',round(proj_area([gl],f)/(abs(sg)/R**2),3))
    print('web-mercator limit lat =',round(math.degrees(math.atan(math.sinh(math.pi))),4))
