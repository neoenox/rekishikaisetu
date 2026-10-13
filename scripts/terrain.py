from pathlib import Path
import io,json,math,hashlib
import numpy as np
import requests
from PIL import Image
from pyproj import Transformer,CRS
from scipy.ndimage import map_coordinates
ROOT=Path(__file__).resolve().parents[1]
def decode(rgb):
    a=np.asarray(rgb,dtype=np.int32);n=a[...,0]*65536+a[...,1]*256+a[...,2]
    return np.where(n==8388608,np.nan,np.where(n>8388608,n-16777216,n)*.01)
def tile(lon,lat,z=14):
    return (lon+180)/360*2**z,(1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*2**z
def make():
    # 6.4 x 5.4 km, containing Sasao, Matsuo, Momokubari.
    bounds=[136.437,35.322,136.507,35.388];z=14
    x0,y0=map(math.floor,tile(bounds[0],bounds[3],z));x1,y1=map(math.floor,tile(bounds[2],bounds[1],z))
    mosaic=np.full(((y1-y0+1)*256,(x1-x0+1)*256),np.nan);manifest=[]
    folder=ROOT/'cache'/'dem';folder.mkdir(parents=True,exist_ok=True)
    for y in range(y0,y1+1):
        for x in range(x0,x1+1):
            url=f'https://cyberjapandata.gsi.go.jp/xyz/dem_png/{z}/{x}/{y}.png';p=folder/f'{z}_{x}_{y}.png'
            if not p.exists():
                r=requests.get(url,timeout=60);r.raise_for_status();p.write_bytes(r.content)
            raw=p.read_bytes();a=decode(Image.open(io.BytesIO(raw)).convert('RGB'))
            mosaic[(y-y0)*256:(y-y0+1)*256,(x-x0)*256:(x-x0+1)*256]=a
            manifest.append({'url':url,'sha256':hashlib.sha256(raw).hexdigest(),'nodata':int(np.isnan(a).sum())})
    assert np.isfinite(mosaic).all(),'DEM missing values: do not silently fill'
    crs=CRS.from_proj4('+proj=aeqd +lat_0=35.355 +lon_0=136.472 +datum=WGS84 +units=m')
    forward=Transformer.from_crs(4326,crs,always_xy=True);inverse=Transformer.from_crs(crs,4326,always_xy=True)
    # Square metric grid; north increases along row index. 25 m sampling.
    xs=np.arange(-3100,3101,25.);ys=np.arange(-3200,3701,25.)
    xx,yy=np.meshgrid(xs,ys);lon,lat=inverse.transform(xx,yy)
    tx=(lon+180)/360*2**z;ty=(1-np.arcsinh(np.tan(np.radians(lat)))/np.pi)/2*2**z
    px=(tx-x0)*256-.5;py=(ty-y0)*256-.5
    assert px.min()>=0 and py.min()>=0 and px.max()<mosaic.shape[1]-1 and py.max()<mosaic.shape[0]-1
    h=map_coordinates(mosaic,[py,px],order=1)
    np.savez(ROOT/'data'/'terrain.npz',xs=xs,ys=ys,h=h)
    info={'source':'GSI_DEM','layer':'dem_png','zoom':z,'tiles':manifest,'crs':crs.to_string(),'origin':[136.472,35.355],'step_m':25,'vertical_scale':1,'nodata':0,'height_min_m':float(h.min()),'height_max_m':float(h.max()),'resampling':'bilinear from native z14 pixel centers; 25m metric mesh; no hole filling','bounds_wgs84':[float(lon.min()),float(lat.min()),float(lon.max()),float(lat.max())],'acquired':'2026-10-13','native_pixel_m_approx':7.79,'notice':'Modern DEM; 1600 terrain changes unmodeled'}
    (ROOT/'data'/'terrain_manifest.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in info.items() if k!='tiles'},ensure_ascii=False))
if __name__=='__main__':make()
