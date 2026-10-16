from hn_common import *
f=interp()
def hz(x,y):return float(f([[y,x]])[0])
# find pass: highest point on corridor between ouji and kutsukake (straight chord), search within +-250m laterally
a=np.array(xy(135.61731,34.993305));b=np.array(xy(135.646042,34.9842));d=b-a;L=np.linalg.norm(d);u=d/L;n=np.array([-u[1],u[0]])
best=None
# pass = saddle: along the chord, for each lateral offset take the max over s of ... use min over lateral of the ridge crossing: highest elevation of the lowest crossing
cross=[]
for off in np.arange(-600,601,30):
    zs=[hz(*(a+u*s+n*off)) for s in np.arange(0,L,30)]
    cross.append((max(zs),off,int(np.argmax(zs))))
low=min(cross);off=low[1];s=low[2]*30;px,py=a+u*s+n*off
lon,lat=__import__('pyproj').Transformer.from_crs(CRS_,4326,always_xy=True).transform(px,py)
print('saddle',low,lon,lat)
PLACES['oinosaka'].update(lon=float(lon),lat=float(lat),elev_m=low[0])
wps=[]
for k,lo,la in ROUTE_WP:
    if k=='oinosaka_zone':lo,la=lon,lat
    wps.append((k,*xy(lo,la)))
pts=[];prev=None
for k,x,y in wps:
    if prev is None:pts.append((x,y))
    else:
        n_=max(2,int(math.hypot(x-prev[0],y-prev[1])/30))
        for t in np.linspace(0,1,n_+1)[1:]:pts.append((prev[0]+(x-prev[0])*t,prev[1]+(y-prev[1])*t))
    prev=(x,y)
pts=np.array(pts);z=np.array([hz(x,y) for x,y in pts])
seg=np.hypot(*np.diff(pts,axis=0).T);dist=np.concatenate([[0],np.cumsum(seg)])
# light smoothing of DEM noise before ascent calc is NOT applied; raw values
asc=float(np.clip(np.diff(z),0,None).sum());desc=float(-np.clip(np.diff(z),None,0).sum())
length3d=float(np.hypot(seg,np.diff(z)).sum())
wp_dist={}
for k,x,y in wps:
    i=int(np.argmin(np.hypot(pts[:,0]-x,pts[:,1]-y)));wp_dist[k]=float(dist[i])
nj=np.array(xy(PLACES['nijo']['lon'],PLACES['nijo']['lat']));hj=np.array(xy(PLACES['honnoji']['lon'],PLACES['honnoji']['lat']))
res=dict(horizontal_distance_m=float(dist[-1]),length_3d_m=length3d,ascent_m=asc,descent_m=desc,max_elev_m=float(z.max()),max_elev_at_m=float(dist[int(np.argmax(z))]),start_elev_m=float(z[0]),end_elev_m=float(z[-1]),
 pass_elev_m_dem=low[0],waypoint_dist_m=wp_dist,honnoji_to_nijo_m=float(np.linalg.norm(nj-hj)),honnoji_old_to_now_m=float(np.linalg.norm(np.array(xy(135.768306,35.01028))-hj)),
 sensitivity=[dict(assumed_speed_km_h=v,minutes=float(length3d/(v*1000/60))) for v in (3,4,5)],
 profile=dict(distance_m=[float(v) for v in dist[::4]],elevation_m=[float(v) for v in z[::4]]),
 route_xy=[[float(a),float(b),float(c)] for (a,b),c in zip(pts,z)],
 notes='straight chords between waypoints; modern DEM; not a historical road; speeds are assumptions')
(ROOT/'data'/'hn_analysis.json').write_text(json.dumps(res,ensure_ascii=False,indent=1),encoding='utf8')
(ROOT/'data'/'hn_places.json').write_text(json.dumps({k:{**v,'x_m':xy(v['lon'],v['lat'])[0],'y_m':xy(v['lon'],v['lat'])[1]} for k,v in PLACES.items()},ensure_ascii=False,indent=1),encoding='utf8')
print({k:v for k,v in res.items() if k not in('profile','route_xy')})
