"""Re-run the route analysis on the road-following route (scripts/hn_route.py output). Writes data/hn_analysis.json + data/hn_places.json."""
from hn_common import *
f=interp()
raw=np.load(ROOT/'cache'/'hn_route_raw.npz');P=raw['pts']
seg=np.hypot(*np.diff(P,axis=0).T);d=np.r_[0,np.cumsum(seg)]
# resample every 30 m along the road (same sampling as the straight-line version)
s=np.arange(0,d[-1],30.0);s=np.r_[s,d[-1]]
X=np.interp(s,d,P[:,0]);Y=np.interp(s,d,P[:,1]);z=np.array([float(f([[y,x]])[0]) for x,y in zip(X,Y)])
sg=np.hypot(np.diff(X),np.diff(Y));dist=np.r_[0,np.cumsum(sg)]
asc=float(np.clip(np.diff(z),0,None).sum());desc=float(-np.clip(np.diff(z),None,0).sum());L3=float(np.hypot(sg,np.diff(z)).sum())
imax=int(np.argmax(z));INV=__import__('pyproj').Transformer.from_crs(CRS_,4326,always_xy=True)
olon,olat=INV.transform(X[imax],Y[imax])
def nearest(lon,lat):
    x,y=xy(lon,lat);i=int(np.argmin(np.hypot(X-x,Y-y)));return float(dist[i]),float(np.hypot(X[i]-x,Y[i]-y))
wp={'kameyama':0.0,'oinosaka_zone':float(dist[imax]),'katsura':nearest(135.696701,34.982559)[0],'honnoji':float(dist[-1])}
old=json.load(open(ROOT/'cache'/'hn_analysis_straight.json',encoding='utf8'))
hj=np.array(xy(135.7534,35.0055));nj=np.array(xy(135.7580,35.0116))
res=dict(route_kind='road-following (modern GSI road network), shortest path with slope penalty, forced nothing',horizontal_distance_m=float(dist[-1]),length_3d_m=L3,ascent_m=asc,descent_m=desc,max_elev_m=float(z.max()),max_elev_at_m=float(dist[imax]),start_elev_m=float(z[0]),end_elev_m=float(z[-1]),
 pass_elev_m_dem=float(z.max()),waypoint_dist_m=wp,honnoji_to_nijo_m=old['honnoji_to_nijo_m'],honnoji_old_to_now_m=old['honnoji_old_to_now_m'],
 sensitivity=[dict(assumed_speed_km_h=v,minutes=float(L3/(v*1000/60))) for v in (3,4,5)],
 profile=dict(distance_m=[float(v) for v in dist[::4]],elevation_m=[float(v) for v in z[::4]]),
 route_xy=[[float(a),float(b),float(c)] for a,b,c in zip(X,Y,z)],
 notes='route follows the modern road network (GSI vector tiles); not the 1582 road; speeds are assumptions')
(ROOT/'data'/'hn_analysis.json').write_text(json.dumps(res,ensure_ascii=False,indent=1),encoding='utf8')
pl=json.load(open(ROOT/'data'/'hn_places.json',encoding='utf8'))
pl['oinosaka'].update(lon=float(olon),lat=float(olat),x_m=float(X[imax]),y_m=float(Y[imax]),elev_m=float(z.max()),basis='道路に沿った経路上の最高標高点(DEMから算出)')
(ROOT/'data'/'hn_places.json').write_text(json.dumps(pl,ensure_ascii=False,indent=1),encoding='utf8')
print({k:(round(v,1) if isinstance(v,float) else v) for k,v in res.items() if k in('horizontal_distance_m','length_3d_m','ascent_m','descent_m','max_elev_m','max_elev_at_m','start_elev_m','end_elev_m')})
print('minutes',[(s['assumed_speed_km_h'],round(s['minutes'])) for s in res['sensitivity']],'oinosaka',round(olon,4),round(olat,4),'wp',{k:round(v) for k,v in wp.items()})
