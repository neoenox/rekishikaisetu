import json,re,numpy as np
from pathlib import Path
from pyproj import Transformer
from scipy.optimize import least_squares
samples=json.loads(Path('assets/earth/calibration_samples.json').read_text())
tf=Transformer.from_crs(4979,4978,always_xy=True)
lat0,lon0=35.359,136.466
la,lo=np.radians([lat0,lon0]);east=np.array([-np.sin(lo),np.cos(lo),0]);north=np.array([-np.sin(la)*np.cos(lo),-np.sin(la)*np.sin(lo),np.cos(la)]);up=np.array([np.cos(la)*np.cos(lo),np.cos(la)*np.sin(lo),np.sin(la)])
origin=np.array(tf.transform(lon0,lat0,0))
records=[]
for s in samples:
 nums=re.search(r'Cursor latitude and longitude (\d+)°(\d+)\x27([\d.]+).*?N (\d+)°(\d+)\x27([\d.]+).*?E Cursor elevation relative to sea level (\d+) m',s['state'])
 assert nums,s
 n=list(map(float,nums.groups()));lat=n[0]+n[1]/60+n[2]/3600;lon=n[3]+n[4]/60+n[5]/3600;h=n[6];p=np.array(tf.transform(lon,lat,h))-origin
 records.append({**{k:s[k] for k in ['x','y']},'lat':lat,'lon':lon,'height':h,'enu':[float(p@east),float(p@north),float(p@up)]})
a=np.array([r['enu'] for r in records]);target=np.array([[r['x'],r['y']] for r in records])
def project(par,a):
 cx,cy,f,alt=par;return np.array([cx+f*a[:,0]/(alt-a[:,2]),cy-f*a[:,1]/(alt-a[:,2])]).T
train=[0,1,2,3,5,6];valid=[4,7,8]
res=least_squares(lambda par:(project(par,a[train])-target[train]).ravel(),[960,540,1712,9700],bounds=([950,530,1500,9000],[970,550,2000,10500]))
err=np.linalg.norm(project(res.x,a)-target,axis=1)
print('camera',res.x,'error',err,'holdout',err[valid]);assert err.max()<2
r={'method':'nadir pinhole camera fitted from Google Earth UI cursor coordinates and elevations; WGS84 ECEF to ENU; 6 fit points + 3 held out','parameters':res.x.tolist(),'origin_lat':lat0,'origin_lon':lon0,'samples':records,'train_indices':train,'holdout_indices':valid,'max_error_px':float(err.max()),'holdout_max_error_px':float(err[valid].max()),'limits':'Fit residual is rendering registration, not historic position accuracy; DEM heights may differ from Google Earth.'}
Path('data/earth_registration.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
